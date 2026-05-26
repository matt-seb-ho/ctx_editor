"""Reconstruct Gated-Reset cells from existing Reset + Baseline traces.

Gated-Reset semantics:
  - Same upstream analyzer as Reset.
  - If analyzer.needs_edit == True → use Reset's prediction (the reset fired).
  - If analyzer.needs_edit == False → use Baseline's prediction (gate held; no edit).

Since Reset's analyzer output (and its needs_edit flag) is logged in every
Reset trace (`trace.logs[type=conversation_analysis].data.needs_edit`),
we can rebuild Gated-Reset's per-sample accuracy without firing any new
LLM calls — just match (sample_id, task, conv) between the Reset cell and
the matching Baseline cell and pick the appropriate is_correct flag.

Output: a JSONL file with per-cell reconstructed numbers + a markdown table.

Usage:
  python scripts/reconstruct_gated_reset.py --root outputs/post_neurips_ac3_phase1

Currently scopes to LiC last-turn-replay outputs (R3 cells under
post_neurips_ac3_phase1/). CollabLLM and WildChat reconstructions can be
added by extending the cell-matching regexes if needed.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

# Regexes pull (task, conv) out of cell names so we can pair Reset ↔ Baseline.
# LiC Phase-1 cells (last-turn replay; exact reconstruction):
RESET_PATTERNS_LIC = [
    re.compile(r"^context_edit_v2_no_gate(?:_accumulate)?_(?P<task>[a-z_]+)_v2_conv(?P<conv>\d+)_\d+$"),
]
BASELINE_PATTERNS_LIC = [
    re.compile(r"^baseline_(?P<task>[a-z_]+)_v2_conv(?P<conv>\d+)_\d+$"),
]
# CollabLLM Phase-3 cells (multi-turn; reconstruction is approximate —
# documented in the output table):
RESET_PATTERNS_COLLAB = [
    re.compile(r"^collabllm_ac3_reset_v8_(?P<task>[a-z_-]+)_rep(?P<conv>\d+)_\d+$"),
]
BASELINE_PATTERNS_COLLAB = [
    re.compile(r"^collabllm_baseline_(?P<task>[a-z_-]+)_rep(?P<conv>\d+)_\d+$"),
]


def collect(root: Path, patterns: list[re.Pattern]) -> dict[tuple[str, str], Path]:
    out: dict[tuple[str, str], Path] = {}
    for d in sorted(root.iterdir()) if root.exists() else []:
        if not d.is_dir():
            continue
        for pat in patterns:
            m = pat.match(d.name)
            if m:
                out[(m.group("task"), m.group("conv"))] = d
                break
    return out


def extract_needs_edit(trace_dir: Path, task: str, sample_id: str) -> bool | None:
    """Return True if ANY turn's analyzer fired needs_edit (Gated-Reset would have
    opened at that turn). Returns False only if every turn's analyzer said
    needs_edit=False. None if no analyzer log was found.

    For LiC last-turn replay (one analyzer fire per sample) this is exact.
    For multi-turn benchmarks this is an approximation: "would Gated-Reset
    have opened the gate at least once?". The exact dynamics — Gated-Reset's
    trajectory after the first opening — can't be reconstructed without
    re-running the agent.
    """
    # Find the trace file by walking traces/ — different benchmarks use
    # different sub-directory layouts (LiC: traces/<task>/<strategy>/<sid>.json;
    # CollabLLM: traces/collabllm_<lang>/<strategy>/<sid>.json).
    candidates: list[Path] = []
    traces_root = trace_dir / "traces"
    if not traces_root.exists():
        return None
    for sid in (sample_id, sample_id.replace("/", "_")):
        candidates.extend(traces_root.rglob(f"{sid}.json"))
    if not candidates:
        return None
    trace = json.load(open(candidates[0]))
    logs = (trace.get("trace") or {}).get("logs", []) or []
    saw_any_analyzer = False
    for log in logs:
        if log.get("type") == "conversation_analysis":
            saw_any_analyzer = True
            ne = log.get("data", {}).get("needs_edit")
            if ne:
                return True
    return False if saw_any_analyzer else None


def load_results(cell_dir: Path) -> dict[str, dict] | None:
    p = cell_dir / "results.json"
    if not p.exists():
        return None
    return {r["sample_id"]: r for r in json.load(open(p))}


def reconstruct_cell(reset_dir: Path, baseline_dir: Path, task: str) -> dict:
    """Return per-sample reconstruction + summary for one (task, conv) cell."""
    reset_results = load_results(reset_dir)
    baseline_results = load_results(baseline_dir)
    if reset_results is None or baseline_results is None:
        return {"error": "missing results.json"}

    shared = sorted(set(reset_results) & set(baseline_results))
    gated_correct = 0
    n_eval = 0
    n_gated_open = 0
    n_gated_passthrough = 0
    n_unknown_gate = 0
    per_sample: list[dict] = []
    for sid in shared:
        rs = reset_results[sid]
        bl = baseline_results[sid]
        # Skip cells where either side errored (num_turns == 0)
        if rs.get("num_turns", 0) == 0 or bl.get("num_turns", 0) == 0:
            continue
        n_eval += 1
        ne = extract_needs_edit(reset_dir, task, sid)
        if ne is None:
            # No analyzer log found; fall back to Reset's call.
            n_unknown_gate += 1
            chosen_correct = bool(rs.get("is_correct"))
            chosen_src = "reset_fallback"
        elif ne:
            chosen_correct = bool(rs.get("is_correct"))
            chosen_src = "reset"
            n_gated_open += 1
        else:
            chosen_correct = bool(bl.get("is_correct"))
            chosen_src = "baseline"
            n_gated_passthrough += 1
        gated_correct += int(chosen_correct)
        per_sample.append({"sample_id": sid, "needs_edit": ne, "source": chosen_src, "gated_correct": chosen_correct})
    return {
        "n": n_eval,
        "gated_correct": gated_correct,
        "gated_acc": (gated_correct / n_eval * 100) if n_eval else 0.0,
        "reset_correct": sum(int(reset_results[r["sample_id"]].get("is_correct", False)) for r in per_sample),
        "baseline_correct": sum(int(baseline_results[r["sample_id"]].get("is_correct", False)) for r in per_sample),
        "n_reset_chosen": n_gated_open,
        "n_baseline_chosen": n_gated_passthrough,
        "n_unknown_gate": n_unknown_gate,
        "per_sample": per_sample,
    }


BENCHMARK_PATTERNS = {
    "lic": (RESET_PATTERNS_LIC, BASELINE_PATTERNS_LIC),
    "collabllm": (RESET_PATTERNS_COLLAB, BASELINE_PATTERNS_COLLAB),
}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True,
                   help="Output dir holding both Reset and Baseline cells.")
    p.add_argument("--benchmark", default="lic", choices=list(BENCHMARK_PATTERNS),
                   help="Benchmark family — chooses pattern set.")
    p.add_argument("--out", default="scripts/analysis_rewrite_v_reset/data/gated_reset_reconstructed.md",
                   help="Markdown summary path.")
    args = p.parse_args()

    reset_patterns, baseline_patterns = BENCHMARK_PATTERNS[args.benchmark]
    root = Path(args.root)
    reset_cells = collect(root, reset_patterns)
    baseline_cells = collect(root, baseline_patterns)
    print(f"Found {len(reset_cells)} Reset cells, {len(baseline_cells)} Baseline cells under {root}")

    rows = []
    for key in sorted(reset_cells):
        if key not in baseline_cells:
            print(f"  SKIP {key}: no matching Baseline")
            continue
        task, conv = key
        r = reconstruct_cell(reset_cells[key], baseline_cells[key], task)
        if "error" in r:
            print(f"  SKIP {key}: {r['error']}")
            continue
        n = r["n"]
        if n == 0:
            continue
        rows.append({"task": task, "conv": conv, **{k: r[k] for k in r if k != "per_sample"}})

    # Markdown summary
    lines = [
        "# Gated-Reset reconstruction (LiC last-turn replay, DSV4F)",
        "",
        "Reconstructed from existing Reset analyzer logs + Baseline traces. No new LLM calls.",
        "Per-sample rule: Reset if `needs_edit=True`, else Baseline.",
        "",
        "| task | conv | n | reset acc | baseline acc | **gated acc** | n_reset_chosen | n_baseline_chosen |",
        "|---|---|---|---|---|---|---|---|",
    ]
    by_task = defaultdict(list)
    for r in rows:
        reset_acc = r["reset_correct"] / r["n"] * 100 if r["n"] else 0
        baseline_acc = r["baseline_correct"] / r["n"] * 100 if r["n"] else 0
        lines.append(
            f"| {r['task']} | {r['conv']} | {r['n']} | "
            f"{reset_acc:.1f}% | {baseline_acc:.1f}% | "
            f"**{r['gated_acc']:.1f}%** | "
            f"{r['n_reset_chosen']} | {r['n_baseline_chosen']} |"
        )
        by_task[r["task"]].append(r)

    lines.append("")
    lines.append("## Per-task aggregates")
    lines.append("")
    lines.append("| task | total n | reset acc | baseline acc | **gated acc** | %samples gated-open |")
    lines.append("|---|---|---|---|---|---|")
    for task in sorted(by_task):
        cells = by_task[task]
        total_n = sum(c["n"] for c in cells)
        total_reset = sum(c["reset_correct"] for c in cells)
        total_base = sum(c["baseline_correct"] for c in cells)
        total_gated = sum(c["gated_correct"] for c in cells)
        total_open = sum(c["n_reset_chosen"] for c in cells)
        lines.append(
            f"| {task} | {total_n} | "
            f"{total_reset/total_n*100:.1f}% | {total_base/total_n*100:.1f}% | "
            f"**{total_gated/total_n*100:.1f}%** | "
            f"{total_open/total_n*100:.1f}% |"
        )

    # Overall
    total_n = sum(r["n"] for r in rows)
    total_reset = sum(r["reset_correct"] for r in rows)
    total_base = sum(r["baseline_correct"] for r in rows)
    total_gated = sum(r["gated_correct"] for r in rows)
    total_open = sum(r["n_reset_chosen"] for r in rows)
    lines.append("")
    lines.append("## Overall")
    lines.append("")
    lines.append(f"- Total n: {total_n}")
    lines.append(f"- Reset accuracy: **{total_reset/total_n*100:.2f}%**")
    lines.append(f"- Baseline accuracy: {total_base/total_n*100:.2f}%")
    lines.append(f"- **Gated-Reset (reconstructed): {total_gated/total_n*100:.2f}%**")
    lines.append(f"- Samples where gate opened (Reset chosen): {total_open}/{total_n} ({total_open/total_n*100:.1f}%)")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n")
    print(f"\nWrote summary to {out_path}")
    print("\n".join(lines[-10:]))


if __name__ == "__main__":
    main()
