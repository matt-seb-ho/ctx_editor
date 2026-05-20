"""Aggregate the per-pair diagnoses (Rewrite vs Reset) into a coherent
report. Writes data/diagnosis_summary.md and prints a stdout summary.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"


def main() -> None:
    rows = [json.loads(l) for l in (DATA_DIR / "diagnoses.jsonl").open()]
    valid = [r for r in rows if "_error" not in r and "_parse_error" not in r]
    print(f"n diagnoses: {len(rows)} ({len(valid)} valid)")

    spec_kind = Counter()
    spec_kind_by_task: dict[str, Counter] = defaultdict(Counter)
    work_inlines_code = Counter()
    work_inlines_spec_num = Counter()
    work_omits_caveat = Counter()
    primary_cause = Counter()
    primary_cause_by_task: dict[str, Counter] = defaultdict(Counter)
    attribution = Counter()
    confidences = []

    for r in valid:
        task = r.get("task", "?")
        sd = r.get("spec_divergence", {}) or {}
        wd = r.get("work_so_far_divergence", {}) or {}
        fc = r.get("failure_chain", {}) or {}
        ria = r.get("rewrite_input_attribution", {}) or {}

        kind = sd.get("kind", "?")
        spec_kind[kind] += 1
        spec_kind_by_task[task][kind] += 1

        if wd.get("rewrite_inlines_verbatim_code"):
            work_inlines_code[task] += 1
        if wd.get("rewrite_inlines_numerical_speculation"):
            work_inlines_spec_num[task] += 1
        if wd.get("rewrite_omits_important_caveat"):
            work_omits_caveat[task] += 1

        primary_cause[fc.get("primary_cause", "?")] += 1
        primary_cause_by_task[task][fc.get("primary_cause", "?")] += 1

        if isinstance(ria, dict):
            for k in ria:
                attribution[k] += 1

        c = r.get("confidence")
        if isinstance(c, (int, float)):
            confidences.append(c)

    md = ["# Rewrite vs Reset — diagnosed failure attribution\n"]
    md.append(f"**Sample**: {len(valid)} pairs, balanced across tasks.")
    md.append("")
    md.append("## Spec-divergence distribution (Rewrite vs Reset)\n")
    md.append("| Kind | n |\n|---|---|")
    for k, n in spec_kind.most_common():
        md.append(f"| {k} | {n} |")
    md.append("")

    md.append("## Spec-divergence by task\n")
    md.append("| Task | vaguer | more_specific | phantom_added | phantom_dropped | format_lost | equivalent |\n|---|---|---|---|---|---|---|")
    for task, c in sorted(spec_kind_by_task.items()):
        md.append(
            f"| {task} | {c.get('vaguer',0)} | {c.get('more_specific',0)} | "
            f"{c.get('phantom_added',0)} | {c.get('phantom_dropped',0)} | "
            f"{c.get('format_lost',0)} | {c.get('equivalent',0)} |"
        )
    md.append("")

    md.append("## Work-so-far divergence flags\n")
    md.append("| Task | inlines_verbatim_code | inlines_numerical_speculation | omits_important_caveat |\n|---|---|---|---|")
    tasks = sorted(spec_kind_by_task.keys())
    for task in tasks:
        md.append(
            f"| {task} | {work_inlines_code.get(task,0)} | "
            f"{work_inlines_spec_num.get(task,0)} | {work_omits_caveat.get(task,0)} |"
        )
    md.append("")

    md.append("## Primary failure cause\n")
    md.append("| Cause | n |\n|---|---|")
    for k, n in primary_cause.most_common():
        md.append(f"| {k} | {n} |")
    md.append("")

    md.append("## Primary cause by task\n")
    md.append("| Task | spec_divergence | work_so_far_divergence | both | other |\n|---|---|---|---|---|")
    for task, c in sorted(primary_cause_by_task.items()):
        md.append(
            f"| {task} | {c.get('spec_divergence',0)} | "
            f"{c.get('work_so_far_divergence',0)} | "
            f"{c.get('both',0)} | {c.get('other',0)} |"
        )
    md.append("")

    md.append("## Rewrite-input attribution (which input to the rewrite operation drove the error)\n")
    md.append("| Attribution | n |\n|---|---|")
    for k, n in attribution.most_common():
        md.append(f"| {k} | {n} |")
    md.append("")

    if confidences:
        md.append(f"Mean labeler confidence: {sum(confidences)/len(confidences):.2f}, "
                  f"min {min(confidences):.2f}, max {max(confidences):.2f}")
        md.append("")

    text = "\n".join(md)
    print(text)
    (DATA_DIR / "diagnosis_summary.md").write_text(text)
    print(f"\nWrote {DATA_DIR/'diagnosis_summary.md'}")


if __name__ == "__main__":
    main()
