#!/usr/bin/env python
"""T2B — conversation selection from the pilot.

The pilot showed the present-arm accuracy distribution is strongly **bimodal**:
most conversations are either never solved or always solved, with few in
between. That matters for what a span ablation can possibly reveal:

  * a **floor** conversation (never solved) has only *upward* headroom, so it
    can reveal a **harmful** span (removing it rescues the turn) and can never
    reveal a useful one;
  * a **ceiling** conversation (always solved) has only *downward* headroom, so
    it can reveal a **useful** span and never a harmful one;
  * mid-range conversations can reveal either.

Selecting only mid-range conversations would maximise power but produce a set
that is unrepresentative *and* incapable of the two extreme cases. So the rule
is: **sort by pilot accuracy and take an evenly spaced sample across the whole
sorted order**, which spans floor, middle and ceiling in proportion.

Selection uses the *present arm only*, and only the pilot's copy of it; the
analysis then uses **fresh present replicates**, so selection cannot induce
regression-to-the-mean in the measured effect.
"""
from __future__ import annotations

import glob
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
N_SEL = {"database_v2": int(os.environ.get("N_DB", "17")),
         "code_v2": int(os.environ.get("N_CODE", "15"))}


def spread(items, k):
    if len(items) <= k:
        return list(items)
    idx = sorted({round(t * (len(items) - 1) / (k - 1)) for t in range(k)})
    while len(idx) < k:  # fill any collision gaps
        for i in range(len(items)):
            if i not in idx:
                idx.append(i)
                break
        idx = sorted(set(idx))
    return [items[i] for i in idx]


def main() -> int:
    sel, report = {}, {}
    for task in ("database_v2", "code_v2"):
        counts = defaultdict(lambda: [0, 0])
        runs = sorted(glob.glob(os.path.join(REPO, f"outputs/T2B/pilot_{task}_r*/results.json")))
        for f in runs:
            for r in json.load(open(f)):
                c = counts[r["sample_id"]]
                c[0] += int(bool(r["is_correct"]))
                c[1] += 1
        rr = {k: v[0] / v[1] for k, v in counts.items()}
        # T2A manifest coverage is required for the ctl_harm control; prefer
        # covered conversations, but only as a tie-break inside the sort.
        t2a = set()
        for line in open(os.path.join(HERE, "..", "T2A", "manifest.jsonl")):
            r = json.loads(line)
            if r["conv"] == "conv0" and r["harmful"]["kind"] in ("H_PHANTOM_COL", "H_PHANTOM_PARAM"):
                t2a.add((r["task_dir"], r["sample_id"]))
        order = sorted(rr, key=lambda k: (rr[k], (task, k) not in t2a, k))
        # Mid-range conversations (0 < rate < 1) can express an effect in EITHER
        # direction and are scarce, so take all of them first; then fill the
        # remainder by even spacing over the sorted rest, which keeps floor and
        # ceiling conversations represented in proportion.
        mid = [k for k in order if 0 < rr[k] < 1]
        rest = [k for k in order if k not in set(mid)]
        chosen = mid[: N_SEL[task]]
        if len(chosen) < N_SEL[task]:
            chosen = chosen + spread(rest, N_SEL[task] - len(chosen))
        sel[task] = sorted(chosen)
        report[task] = {
            "n_pilot_runs": len(runs),
            "n_candidates": len(rr),
            "n_selected": len(chosen),
            "pilot_rate_distribution": {
                "floor(0)": sum(1 for v in rr.values() if v == 0),
                "mid": sum(1 for v in rr.values() if 0 < v < 1),
                "ceiling(1)": sum(1 for v in rr.values() if v == 1),
            },
            "selected_pilot_rates": {k: rr[k] for k in sorted(chosen)},
            "selected_mean_pilot_rate": sum(rr[k] for k in chosen) / len(chosen),
            "selected_with_t2a_harm_control": sum(1 for k in chosen if (task, k) in t2a),
        }
    json.dump(sel, open(os.path.join(HERE, "selection.json"), "w"), indent=1)
    json.dump(report, open(os.path.join(HERE, "selection_report.json"), "w"), indent=1)
    for t, r in report.items():
        print(t, {k: v for k, v in r.items() if k != "selected_pilot_rates"})
    return 0


if __name__ == "__main__":
    sys.exit(main())
