"""Aggregate accuracy across rewrite versions (v1, v2, v3_no_conv,
v3_conv_first, v4_strict) and compare against Baseline + Reset on
the same model/task/conv keys.

Reads:
  outputs/post_neurips_ac3_phase1/ — v1 Rewrite + Baseline + Reset
  outputs/post_neurips_r2_rewrite_v2/ — v2 Rewrite
  outputs/post_may18_r3_rewrite_v3_v4/ — v3_no_conv + v4_strict (throttled re-run)

Writes a markdown summary table.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

OUTPUTS = Path("/home/v-homatthew/ctx_editor/outputs")
OUT_PATH = Path(__file__).resolve().parent / "data" / "rewrite_versions_compared.md"

# Map directory name → (variant_label, regex of task/conv extraction)
DIRS = {
    "post_neurips_ac3_phase1": [
        (re.compile(r"^baseline_(?P<task>[a-z_]+)_v2_conv(?P<conv>\d+)_\d+$"), "Baseline"),
        (re.compile(r"^context_edit_v2_no_gate(?:_accumulate)?_(?P<task>[a-z_]+)_v2_conv(?P<conv>\d+)_\d+$"), "Reset"),
        (re.compile(r"^ac3_rewrite_lic_(?P<task>[a-z_]+)_v2_conv(?P<conv>\d+)_\d+$"), "Rewrite-v1"),
        (re.compile(r"^omit_assistant_(?P<task>[a-z_]+)_v2_conv(?P<conv>\d+)_\d+$"), "AO"),
    ],
    "post_neurips_r2_rewrite_v2": [
        (re.compile(r"^ac3_rewrite_v2_lic_(?P<task>[a-z_]+)_v2_conv(?P<conv>\d+)_\d+$"), "Rewrite-v2"),
    ],
    "post_may18_r3_rewrite_v3_v4": [
        (re.compile(r"^ac3_rewrite_v3_no_conv_lic_(?P<task>[a-z_]+)_v2_conv(?P<conv>\d+)_\d+$"), "Rewrite-v3-no-conv"),
        (re.compile(r"^ac3_rewrite_v3_conv_first_lic_(?P<task>[a-z_]+)_v2_conv(?P<conv>\d+)_\d+$"), "Rewrite-v3-conv-first"),
        (re.compile(r"^ac3_rewrite_v4_strict_lic_(?P<task>[a-z_]+)_v2_conv(?P<conv>\d+)_\d+$"), "Rewrite-v4-strict"),
    ],
}

TASKS_ORDER = ["math", "code", "database", "actions"]


def collect() -> dict:
    """Returns: variant -> task -> conv -> (n_correct, n_total, errors)."""
    out: dict[str, dict[str, dict[str, tuple[int, int, int]]]] = defaultdict(lambda: defaultdict(dict))
    for run_root, patterns in DIRS.items():
        root = OUTPUTS / run_root
        if not root.exists():
            continue
        for d in sorted(root.iterdir()):
            if not d.is_dir():
                continue
            for pat, variant in patterns:
                m = pat.match(d.name)
                if not m:
                    continue
                rfile = d / "results.json"
                if not rfile.exists():
                    continue
                rows = json.load(open(rfile))
                n = len(rows)
                correct = sum(1 for r in rows if r.get("is_correct"))
                errors = sum(1 for r in rows if r.get("num_turns") == 0)
                out[variant][m.group("task")][m.group("conv")] = (correct, n, errors)
                break
    return out


def main() -> None:
    data = collect()
    variants_order = ["Baseline", "AO", "Reset", "Rewrite-v1", "Rewrite-v2",
                      "Rewrite-v3-no-conv", "Rewrite-v3-conv-first", "Rewrite-v4-strict"]
    variants = [v for v in variants_order if v in data]

    md = ["# Rewrite versions vs Baseline / Reset on LiC (DeepSeek-V4-Flash, last-turn replay, htn50_52)\n"]
    md.append("Per-task averages across 3 prefix replicates. Each cell shows accuracy% and total n.\n")

    # Header
    header = "| Variant | " + " | ".join(TASKS_ORDER) + " | avg |"
    md.append(header)
    md.append("|" + "---|" * (len(TASKS_ORDER) + 2))

    for v in variants:
        per_task_str = []
        per_task_means = []
        for task in TASKS_ORDER:
            convs = data[v].get(task, {})
            if not convs:
                per_task_str.append("—")
                continue
            # Aggregate across convs: weight by n
            total_correct = sum(c for c, n, _ in convs.values())
            total_n = sum(n for c, n, _ in convs.values())
            errs = sum(e for c, n, e in convs.values())
            if total_n == 0:
                per_task_str.append("—")
                continue
            acc = total_correct / total_n * 100
            per_task_str.append(f"{acc:.1f}% (n={total_n}, e={errs})")
            per_task_means.append(acc)
        avg = sum(per_task_means) / len(per_task_means) if per_task_means else 0
        md.append(f"| {v} | " + " | ".join(per_task_str) + f" | {avg:.1f}% |")
    md.append("")

    # Δ vs Baseline / Reset
    if "Baseline" in data and len(variants) > 1:
        md.append("\n## Δ vs Baseline (positive = rewrite better)\n")
        md.append("| Variant | " + " | ".join(TASKS_ORDER) + " | avg |")
        md.append("|" + "---|" * (len(TASKS_ORDER) + 2))
        bl_means = {}
        for task in TASKS_ORDER:
            convs = data["Baseline"].get(task, {})
            if convs:
                tc = sum(c for c, n, _ in convs.values())
                tn = sum(n for c, n, _ in convs.values())
                bl_means[task] = (tc / tn * 100) if tn else 0
        for v in variants:
            if v == "Baseline":
                continue
            diffs = []
            cells = []
            for task in TASKS_ORDER:
                convs = data[v].get(task, {})
                if not convs:
                    cells.append("—")
                    continue
                tc = sum(c for c, n, _ in convs.values())
                tn = sum(n for c, n, _ in convs.values())
                if tn == 0:
                    cells.append("—")
                    continue
                acc = tc / tn * 100
                d = acc - bl_means.get(task, 0)
                diffs.append(d)
                sign = "+" if d >= 0 else ""
                cells.append(f"{sign}{d:.1f}pp")
            avg = sum(diffs) / len(diffs) if diffs else 0
            md.append(f"| {v} | " + " | ".join(cells) + f" | {'+' if avg>=0 else ''}{avg:.1f}pp |")
        md.append("")

    text = "\n".join(md)
    print(text)
    OUT_PATH.write_text(text)
    print(f"\nWrote {OUT_PATH}")


if __name__ == "__main__":
    main()
