"""Aggregate Rewrite failure-mode labels into a coherent report.

Reads `data/rewrite_failure_labels.jsonl` (produced by
`categorize_failures.py`) and computes:

  - Primary-category distribution per task and overall
  - Most common secondary categories
  - A few illustrative quotes (rationale strings) per category
  - Co-occurrence: which categories tend to fire together

Writes a markdown report to `data/rewrite_failure_summary.md` plus prints
to stdout.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"

LABELS = ["F1_LOST_META_STRUCTURE", "F2_ANCHORED_ON_PARTIAL_WRONG_WORK",
          "F3_COMPACTION_INTERPRETIVE_BIAS", "F4_OVERFIT_REQUIREMENTS",
          "F5_SCHEMA_DETAIL_LOST", "F6_TONE_OR_FORMAT_MISMATCH", "F7_OTHER",
          "ERROR"]


def shorten(cat: str) -> str:
    return cat.split("_", 1)[0] if cat and "_" in cat else cat


def main() -> None:
    p = DATA_DIR / "rewrite_failure_labels.jsonl"
    rows = [json.loads(l) for l in p.open()]
    print(f"Loaded {len(rows)} labels")

    by_task_prim: dict[str, Counter] = defaultdict(Counter)
    overall_prim: Counter = Counter()
    secondary: Counter = Counter()
    by_task_secondary: dict[str, Counter] = defaultdict(Counter)
    co_occur: Counter = Counter()
    rationales: dict[str, list[tuple[str, str, str]]] = defaultdict(list)

    for r in rows:
        prim = (r.get("primary_category") or "F7").upper().split("_", 1)[0]
        prim_full = (r.get("primary_category") or "F7").upper()
        # Sometimes the labeler returns just "F1" or "F1_LOST_META_STRUCTURE"
        if len(prim_full) <= 4:
            prim_full = next((L for L in LABELS if L.startswith(prim)), prim_full)
        by_task_prim[r["task"]][prim] += 1
        overall_prim[prim] += 1
        rationales[prim].append((r["task"], r["sample_id"], (r.get("rationale") or "")[:180]))

        for s in (r.get("secondary_categories") or []):
            scode = s.upper().split("_", 1)[0]
            secondary[scode] += 1
            by_task_secondary[r["task"]][scode] += 1
            co_occur[tuple(sorted([prim, scode]))] += 1

    # Output
    out_lines: list[str] = []
    out_lines.append("# Rewrite failure-mode aggregation")
    out_lines.append(f"\nTotal labeled cases: {len(rows)}")
    out_lines.append("\n## Primary-category distribution\n")
    out_lines.append("| Task | F1 | F2 | F3 | F4 | F5 | F6 | F7 | ERR | Total |")
    out_lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for task in sorted(by_task_prim):
        c = by_task_prim[task]
        total = sum(c.values())
        out_lines.append(f"| {task} | " + " | ".join(str(c.get(f'F{i}', 0)) for i in range(1, 8)) + f" | {c.get('ERROR', 0)} | {total} |")
    # Overall row
    total_all = sum(overall_prim.values())
    out_lines.append("| **All** | " + " | ".join(str(overall_prim.get(f'F{i}', 0)) for i in range(1, 8)) + f" | {overall_prim.get('ERROR', 0)} | {total_all} |")

    out_lines.append("\n## Secondary-category counts (per failure case can list multiple)\n")
    out_lines.append("| Code | Count |")
    out_lines.append("|---|---|")
    for code, n in secondary.most_common():
        out_lines.append(f"| {code} | {n} |")

    out_lines.append("\n## Top co-occurrences (primary + secondary)\n")
    for pair, n in co_occur.most_common(8):
        out_lines.append(f"- {pair[0]} ⨯ {pair[1]}: {n}")

    out_lines.append("\n## Illustrative rationales by category\n")
    for cat in [f"F{i}" for i in range(1, 8)] + ["ERROR"]:
        if cat not in rationales:
            continue
        out_lines.append(f"### {cat}")
        for task, sid, rationale in rationales[cat][:3]:
            out_lines.append(f"- [{task} / {sid[:32]}] {rationale}")
        out_lines.append("")

    text = "\n".join(out_lines)
    print(text)
    (DATA_DIR / "rewrite_failure_summary.md").write_text(text)
    print(f"\nSaved to {DATA_DIR / 'rewrite_failure_summary.md'}")


if __name__ == "__main__":
    main()
