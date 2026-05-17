"""Aggregate AC3 phase results into a summary table per (model, strategy, task).

Walks all outputs/{run_tag}/*/run_summary.json, joins with metrics.json,
groups by (model, strategy, task) and computes mean ± std across the
prefix replicates.

Usage:
    python scripts/aggregate_ac3_phase.py outputs/post_neurips_ac3_phase1 \
        --model deepseek_v4_flash_foundry \
        --md-out docs/reports/post_neurips_ac3_phase1.md

The script also detects which Reset-family variant (no_gate / gated /
rewrite) wins on average and writes a winners.json sidecar that the
Phase 2 launcher consumes.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# Map experiment_name → strategy_key (the families we want to group by).
EXP_TO_STRAT = {
    "baseline": "Baseline",
    "omit_assistant": "AO",
    "append_analysis": "Augment",
    "context_edit_v2_no_gate": "Reset",
    "context_edit_v2_no_gate_accumulate": "Reset",
    "context_edit_v2_gated": "Gated-Reset",
    "context_edit_v2_gated_accumulate": "Gated-Reset",
    "ac3_rewrite_lic": "Rewrite",
    "context_edit_v2_accumulate": "Reset",  # historical (paper's row)
    "collabllm_compaction": "Rewrite",
}


def cell_run_summary(run_summary_path: Path) -> dict | None:
    """Return a dict describing one cell, or None if it's incomplete."""
    d = run_summary_path.parent
    try:
        rs = json.loads(run_summary_path.read_text())
    except Exception:
        return None
    metrics_path = d / "metrics.json"
    if not metrics_path.exists():
        return None
    metrics = json.loads(metrics_path.read_text())
    exp = rs.get("experiment_name", "")
    # exp shape: {exp_config}_{task}_conv{c}_{ts}
    m = re.match(r"^(?P<exp>.+?)_(?P<task>math_v2|code_v2|database_v2|actions_v2)_conv(?P<conv>\d+)_(?P<ts>\d+)$", exp)
    if not m:
        return None
    exp_key = m.group("exp")
    strat = EXP_TO_STRAT.get(exp_key, exp_key)
    return {
        "exp_config": exp_key,
        "strategy": strat,
        "task": m.group("task"),
        "conv": int(m.group("conv")),
        "model": rs.get("model"),
        "accuracy": metrics.get("accuracy", 0.0),
        "correct": metrics.get("correct", 0),
        "total": metrics.get("total_samples", 0),
        "errors": metrics.get("errors", 0),
        "total_cost_usd": metrics.get("total_cost_usd", 0.0),
        "average_turns": metrics.get("average_turns", 0.0),
        "out_dir": str(d.relative_to(PROJECT_ROOT)) if str(d).startswith(str(PROJECT_ROOT)) else str(d),
    }


def fmt_pct(x):
    return f"{x*100:.1f}%"


def gather(run_tag_dir: Path, only_model: str | None = None) -> list[dict]:
    cells = []
    for rs_path in sorted(run_tag_dir.rglob("run_summary.json")):
        c = cell_run_summary(rs_path)
        if c is None:
            continue
        if only_model and c["model"] != only_model:
            continue
        cells.append(c)
    return cells


def render(cells: list[dict], title: str) -> str:
    by_key: dict = defaultdict(list)  # (strategy, task) -> [cell]
    for c in cells:
        by_key[(c["strategy"], c["task"])].append(c)

    strategies = sorted({c["strategy"] for c in cells},
                        key=lambda s: ["Baseline", "AO", "Augment", "Reset", "Gated-Reset", "Rewrite"].index(s)
                                       if s in ["Baseline","AO","Augment","Reset","Gated-Reset","Rewrite"]
                                       else 99)
    tasks = ["math_v2", "code_v2", "database_v2", "actions_v2"]

    lines = [f"## {title}\n", "Mean accuracy across prefix replicates (typically n=3). For each cell the table shows mean ± std (pp).\n"]
    lines.append("| Strategy | " + " | ".join(tasks) + " | Δ vs Baseline (avg pp) |")
    lines.append("|---|" + "---|" * (len(tasks) + 1))

    baseline_means = {}
    for t in tasks:
        baseline_cells = by_key.get(("Baseline", t), [])
        baseline_means[t] = (
            statistics.mean(c["accuracy"] for c in baseline_cells)
            if baseline_cells else None
        )

    for s in strategies:
        row = [s]
        deltas = []
        for t in tasks:
            cs = by_key.get((s, t), [])
            if not cs:
                row.append("—"); continue
            accs = [c["accuracy"] for c in cs]
            mean = statistics.mean(accs)
            std = statistics.stdev(accs) if len(accs) >= 2 else 0
            row.append(f"{fmt_pct(mean)} ± {std*100:.1f}pp (n={len(accs)})")
            if baseline_means.get(t) is not None:
                deltas.append((mean - baseline_means[t]) * 100)
        if deltas:
            row.append(f"{statistics.mean(deltas):+.1f}pp")
        else:
            row.append("—")
        lines.append("| " + " | ".join(row) + " |")

    # Per-cell detail
    lines.append("\n### Per-cell detail\n")
    lines.append("| Strategy | Task | Conv | Accuracy | Errors | Cost | Avg Turns | Output Dir |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for c in sorted(cells, key=lambda c: (c["strategy"], c["task"], c["conv"])):
        lines.append(
            f"| {c['strategy']} | {c['task']} | {c['conv']} | "
            f"{fmt_pct(c['accuracy'])} ({c['correct']}/{c['total']}) | {c['errors']} | "
            f"${c['total_cost_usd']:.2f} | {c['average_turns']:.1f} | `{c['out_dir']}` |"
        )
    return "\n".join(lines) + "\n"


def pick_winner(cells: list[dict]) -> dict:
    """Pick the best Reset-family variant from {Reset, Gated-Reset, Rewrite}.

    Decision rule (per the plan rev.3):
      - mean accuracy across all tasks, weighted equally
      - 3pp tiebreak in favor of Reset, then Rewrite (Gated-Reset hardest to win)
    Returns: {"winner": str, "ranking": [(strategy, mean_acc), ...]}
    """
    by_strategy: dict = defaultdict(list)
    for c in cells:
        if c["strategy"] in {"Reset", "Gated-Reset", "Rewrite"}:
            by_strategy[c["strategy"]].append(c["accuracy"])
    ranking = sorted(
        [(s, statistics.mean(accs)) for s, accs in by_strategy.items()],
        key=lambda x: -x[1],
    )
    if not ranking:
        return {"winner": None, "ranking": []}
    top_strat, top_acc = ranking[0]
    if len(ranking) > 1:
        runner_strat, runner_acc = ranking[1]
        if abs(top_acc - runner_acc) < 0.03:
            # 3pp tiebreak: prefer Reset > Rewrite > Gated-Reset (simpler/cheaper)
            pref_order = {"Reset": 0, "Rewrite": 1, "Gated-Reset": 2}
            tied = [(s, a) for s, a in ranking if abs(a - top_acc) < 0.03]
            tied.sort(key=lambda x: pref_order.get(x[0], 99))
            top_strat = tied[0][0]
    return {"winner": top_strat, "ranking": ranking}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_tag_dir")
    parser.add_argument("--model", default=None)
    parser.add_argument("--md-out", default=None)
    parser.add_argument("--winners-out", default=None)
    parser.add_argument("--title", default=None)
    args = parser.parse_args()

    run_tag_dir = Path(args.run_tag_dir)
    cells = gather(run_tag_dir, only_model=args.model)
    title = args.title or f"AC3 phase results — {run_tag_dir.name}"
    md = render(cells, title)
    winners = pick_winner(cells)

    print(f"Discovered {len(cells)} cells.")
    print(md)
    print("\n=== winner ===")
    print(json.dumps(winners, indent=2))

    if args.md_out:
        Path(args.md_out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.md_out).write_text(md)
        print(f"\nWrote {args.md_out}")

    if args.winners_out:
        Path(args.winners_out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.winners_out).write_text(json.dumps(winners, indent=2))
        print(f"Wrote {args.winners_out}")


if __name__ == "__main__":
    main()
