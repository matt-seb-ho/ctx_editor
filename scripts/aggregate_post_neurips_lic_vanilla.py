"""Aggregate post-NeurIPS LiC vanilla baseline results into a summary table.

Scans each run's outputs/{date}/{time}/run_summary.json and produces:
  - Per-(model, task) mean/std accuracy across the 3 runs
  - Total cost, wall time, token counts
  - A clean Markdown report appended to docs/reports/post_neurips_lic_vanilla.md

Tainted code runs (from the pre-fix window) are detected by the 'errors'
count in metrics.json (> a few) and replaced with their _redo counterparts
when present.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RUN_TAG = "post_neurips_lic_vanilla"
LOG_DIR = PROJECT_ROOT / "outputs" / RUN_TAG / "logs"
MD_PATH = PROJECT_ROOT / "docs" / "reports" / f"{RUN_TAG}.md"


def _parse_log_fallback(text: str, log_path: Path) -> dict:
    """Pull numbers from the launcher log's captured stdout.

    Used when metrics.json is unreliable (e.g. its output_dir collided with a
    different model's run and got overwritten). The launcher captured the
    experiment's stdout immediately as it completed, so the accuracy / cost /
    turn lines printed by run_experiment.py at the very end of the run are
    the run's actual numbers.
    """
    acc_m = re.search(r"^Accuracy:\s+([\d.]+)%\s+\((\d+)/(\d+)\)(.*)$", text, re.MULTILINE)
    cost_m = re.search(r"^Total Cost:\s+\$([\d.]+)", text, re.MULTILINE)
    turns_m = re.search(r"^Average Turns:\s+([\d.]+)", text, re.MULTILINE)
    if not acc_m:
        return {}
    correct = int(acc_m.group(2)); total = int(acc_m.group(3))
    extra = acc_m.group(4)
    errors = 0
    em = re.search(r"\((\d+)\s+errors? excluded\)", extra)
    if em:
        errors = int(em.group(1))
    return {
        "accuracy": correct / total if total else 0.0,
        "correct": correct,
        "total": total,
        "errors": errors,
        "user_sim_skipped": 0,
        "average_score": 0.0,
        "total_cost_usd": float(cost_m.group(1)) if cost_m else 0.0,
        "average_turns": float(turns_m.group(1)) if turns_m else 0.0,
        "average_user_tokens": 0.0,
        "adjusted_accuracy": None,
        "log_basename": log_path.name,
        "_from_log_fallback": True,
    }


def parse_log(log_path: Path) -> Optional[dict]:
    """Pull the canonical fields out of a launcher log file.

    Prefer metrics.json. If the run's output_dir was overwritten by a
    concurrent run (detected via run_summary.json model mismatch), fall back
    to parsing the captured stdout in the launcher log itself.
    """
    if not log_path.exists():
        return None
    text = log_path.read_text(errors="replace")
    out_dir_m = re.search(r"outputs/\d{4}-\d{2}-\d{2}/\d{2}-\d{2}-\d{2}",  text)
    out_dir = None
    if out_dir_m:
        out_dir = PROJECT_ROOT / out_dir_m.group(0)

    # The redo runs use a non-date output dir (outputs/post_neurips_lic_vanilla*_redo/...).
    if out_dir is None or not out_dir.exists():
        out_dir_m2 = re.search(r"outputs/post_neurips_lic_vanilla[^/\s]*/[^\s'\"]+", text)
        if out_dir_m2:
            out_dir = PROJECT_ROOT / out_dir_m2.group(0)

    if out_dir is None:
        return None

    metrics_path = out_dir / "metrics.json"
    run_summary_path = out_dir / "run_summary.json"

    # Try the canonical path.
    if metrics_path.exists():
        with metrics_path.open() as f:
            metrics = json.load(f)
        # Detect collision: run_summary.json's model field vs. the experiment
        # name encoded in the LOG filename.
        log_model = log_path.name.split("__")[0]
        rs_model = None
        if run_summary_path.exists():
            with run_summary_path.open() as f:
                rs = json.load(f)
            rs_model = rs.get("experiment_name", "")
        # If experiment_name in run_summary doesn't contain log_model, the dir
        # was overwritten by a different run. Use log-fallback in that case.
        if rs_model and log_model not in rs_model:
            fb = _parse_log_fallback(text, log_path)
            if fb:
                fb["out_dir"] = str(out_dir.relative_to(PROJECT_ROOT)) + " (overwritten — stats from launcher log)"
                return fb
        return {
            "out_dir": str(out_dir.relative_to(PROJECT_ROOT)),
            "accuracy": metrics.get("accuracy", 0.0),
            "correct": metrics.get("correct", 0),
            "total": metrics.get("total_samples", 0),
            "errors": metrics.get("errors", 0),
            "user_sim_skipped": metrics.get("user_sim_skipped", 0),
            "average_score": metrics.get("average_score", 0.0),
            "total_cost_usd": metrics.get("total_cost_usd", 0.0),
            "average_turns": metrics.get("average_turns", 0.0),
            "average_user_tokens": metrics.get("average_user_tokens", 0.0),
            "adjusted_accuracy": metrics.get("adjusted_accuracy"),
            "log_basename": log_path.name,
        }

    # No metrics.json — try the log fallback.
    fb = _parse_log_fallback(text, log_path)
    if fb:
        fb["out_dir"] = str(out_dir.relative_to(PROJECT_ROOT)) + " (no metrics.json — stats from launcher log)"
        return fb
    return None


def gather() -> dict:
    """Return {(model, task, run_label): record}.

    run_label is "1", "2", "3" for original runs and "redo1" etc. for re-runs.
    """
    out = {}
    for log in sorted(LOG_DIR.glob("*.log")):
        name = log.name
        if name.startswith("_"):
            continue
        m = re.match(r"^(?P<model>[^_].+?)__(?P<task>[a-z_]+_v2)__(run|redo|smoke)(?P<idx>\d+)\.log$", name)
        if not m:
            continue
        kind = m.group(3)
        if kind == "smoke":
            continue
        model = m.group("model")
        task = m.group("task")
        idx = m.group("idx")
        label = f"redo{idx}" if kind == "redo" else idx
        rec = parse_log(log)
        if rec is None:
            continue
        rec["model"] = model
        rec["task"] = task
        rec["run_label"] = label
        out[(model, task, label)] = rec
    return out


def resolve_runs(records: dict) -> dict:
    """For each (model, task), pick the 3 cleanest runs.

    Strategy: prefer redo runs over original tainted runs (errors > 5). If a
    model has 3 redo runs available for a task, use those. Otherwise use clean
    originals; fall back to tainted originals only if nothing else exists.
    """
    by_mt = defaultdict(list)
    for (model, task, _), rec in records.items():
        by_mt[(model, task)].append(rec)

    resolved = {}
    for (model, task), runs in by_mt.items():
        runs_by_label = {r["run_label"]: r for r in runs}
        def is_tainted(r):
            # data-bug tainted (excess errors) OR overwritten by collision
            return (r["errors"] > 5) or " (overwritten" in r["out_dir"]

        # Classify
        clean_originals = [r for lbl, r in runs_by_label.items()
                           if not lbl.startswith("redo") and not is_tainted(r)]
        tainted_originals = [r for lbl, r in runs_by_label.items()
                             if not lbl.startswith("redo") and is_tainted(r)]
        redos = [r for lbl, r in runs_by_label.items() if lbl.startswith("redo")]

        # Build the kept-3 set: prefer redos to replace tainted originals.
        kept = []
        used_idxs = set()
        for r in clean_originals:
            kept.append(r); used_idxs.add(r["run_label"])
        # Redos fill in for missing/tainted slots
        for r in redos:
            kept.append(r)
        # If we still don't have 3, fall back to tainted originals
        if len(kept) < 3:
            for r in tainted_originals:
                if len(kept) >= 3: break
                kept.append(r)

        # Cap to 3 (favor cleaner ones — redos already in; if extras, drop tainted)
        kept = kept[:3]
        resolved[(model, task)] = {"kept": kept, "all": runs}
    return resolved


def fmt_pct(x: float) -> str:
    return f"{x*100:.1f}%"


def fmt_money(x: float) -> str:
    return f"${x:.2f}"


def render_summary(resolved: dict) -> str:
    """Render the summary tables and per-cell stats."""
    # Order models and tasks for readability
    model_order = ["gpt5_4", "deepseek_v4_flash_foundry", "kimi_k2_6_foundry", "gpt5_5_foundry"]
    model_label = {
        "gpt5_4": "gpt-5.4",
        "deepseek_v4_flash_foundry": "DeepSeek-V4-Flash",
        "kimi_k2_6_foundry": "Kimi-K2.6",
        "gpt5_5_foundry": "gpt-5.5",
    }
    task_order = ["math_v2", "code_v2", "database_v2", "actions_v2"]

    lines = []
    lines.append("\n## Summary — Mean accuracy across 3 runs (best clean set)\n")
    lines.append("| Model | math_v2 | code_v2 | database_v2 | actions_v2 |")
    lines.append("|---|---|---|---|---|")

    for model in model_order:
        cells = [model_label.get(model, model)]
        for task in task_order:
            entry = resolved.get((model, task))
            if not entry or not entry["kept"]:
                cells.append("—")
                continue
            kept = entry["kept"]
            accs = [r["accuracy"] for r in kept]
            mean = statistics.mean(accs)
            if len(accs) >= 2:
                std = statistics.stdev(accs)
                cells.append(f"{fmt_pct(mean)} ± {std*100:.1f}pp (n={len(accs)})")
            else:
                cells.append(f"{fmt_pct(mean)} (n={len(accs)})")
        lines.append("| " + " | ".join(cells) + " |")

    # Detailed per-cell table
    lines.append("\n## Per-(model, task) detail\n")
    lines.append("| Model | Task | Run | Accuracy | Errors | Avg Turns | Cost (USD) | Output Dir |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for model in model_order:
        for task in task_order:
            entry = resolved.get((model, task))
            if not entry:
                continue
            # Show all runs (kept + tainted) sorted; mark tainted/redo
            all_runs = entry["all"]
            all_runs_sorted = sorted(all_runs, key=lambda r: r["run_label"])
            for r in all_runs_sorted:
                marker = ""
                if r["run_label"].startswith("redo"):
                    marker = " (redo, used)"
                elif r["errors"] > 5:
                    marker = " (tainted, replaced)"
                elif r in entry["kept"]:
                    marker = ""
                else:
                    marker = " (extra)"
                lines.append(
                    f"| {model_label.get(model, model)} | {task} | {r['run_label']}{marker} | "
                    f"{fmt_pct(r['accuracy'])} ({r['correct']}/{r['total']}) | "
                    f"{r['errors']} | {r['average_turns']:.1f} | "
                    f"{fmt_money(r['total_cost_usd'])} | `{r['out_dir']}` |"
                )

    # Totals
    lines.append("\n## Totals\n")
    total_cost = 0.0
    total_runs = 0
    for entry in resolved.values():
        for r in entry["all"]:
            total_cost += r["total_cost_usd"]
            total_runs += 1
    lines.append(f"- Total ctx-editor invocations: **{total_runs}** (includes tainted and redo runs)")
    lines.append(f"- Total cost across all runs: **{fmt_money(total_cost)}**")

    return "\n".join(lines) + "\n"


def update_md(summary_md: str) -> None:
    """Append/replace a 'Summary' section in the results MD."""
    if not MD_PATH.exists():
        MD_PATH.write_text(summary_md)
        return
    existing = MD_PATH.read_text()
    marker = "\n## Summary — Mean accuracy across 3 runs (best clean set)"
    if marker in existing:
        # Truncate after the prior summary marker
        existing = existing.split(marker, 1)[0]
    MD_PATH.write_text(existing.rstrip() + "\n" + summary_md)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Print summary, don't update MD")
    args = parser.parse_args()

    records = gather()
    resolved = resolve_runs(records)
    summary = render_summary(resolved)

    if args.dry_run:
        print(summary)
    else:
        update_md(summary)
        print(f"Updated {MD_PATH}")


if __name__ == "__main__":
    main()
