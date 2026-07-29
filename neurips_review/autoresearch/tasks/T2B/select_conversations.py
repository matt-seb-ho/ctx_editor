#!/usr/bin/env python
"""T2B — conversation selection from the pilot.

Rationale (worklog §2). Raw baseline accuracy on these prefixes is ~10-30%.
A conversation that is at the floor (never solved) or the ceiling (always
solved) under the *present* context cannot express a causal span effect in one
direction, so including it only adds noise and dilutes power. Selection is
therefore made on the **present arm only**, before any ablation exists, and the
pilot data is then **discarded**: the analysis uses fresh present replicates.
That ordering is what prevents regression-to-the-mean from manufacturing an
apparent effect.

Selection rule (declared before looking at the numbers):
  1. Rank conversations by |pilot_rate - 0.5| ascending (most headroom first).
  2. Keep at most N_PER_TASK per task.
  3. Never keep a conversation with pilot_rate exactly 0 or 1 unless there are
     not enough others, in which case top up with rate-0 conversations (they
     retain upward headroom, which is the direction that detects *harmful*
     spans) and record how many were topped up.

The consequence is stated in RESULTS: effect sizes are conditional on
conversations that have headroom, i.e. this is a high-power subsample, not a
representative sample of LiC conversations.
"""
from __future__ import annotations

import glob
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
N_PER_TASK = int(os.environ.get("N_PER_TASK", "25"))


def main() -> int:
    rates = {}
    for task in ("database_v2", "code_v2"):
        counts = defaultdict(lambda: [0, 0])
        runs = sorted(glob.glob(os.path.join(REPO, f"outputs/T2B/pilot_{task}_r*/results.json")))
        for f in runs:
            for r in json.load(open(f)):
                c = counts[r["sample_id"]]
                c[0] += int(bool(r["is_correct"]))
                c[1] += 1
        rates[task] = {k: (v[0], v[1], v[0] / v[1]) for k, v in counts.items()}
        print(f"{task}: {len(runs)} pilot runs, {len(counts)} conversations")

    sel, report = {}, {}
    for task, rr in rates.items():
        mid = [k for k, v in rr.items() if 0 < v[2] < 1]
        mid.sort(key=lambda k: (abs(rr[k][2] - 0.5), k))
        chosen = mid[:N_PER_TASK]
        topped = 0
        if len(chosen) < N_PER_TASK:
            zeros = sorted([k for k, v in rr.items() if v[2] == 0])
            extra = zeros[: N_PER_TASK - len(chosen)]
            topped = len(extra)
            chosen += extra
        sel[task] = sorted(chosen)
        report[task] = {
            "n_candidates": len(rr),
            "n_with_headroom": len(mid),
            "n_selected": len(chosen),
            "n_topped_up_from_rate0": topped,
            "pilot_rate_hist": {
                str(round(v[2], 3)): sum(1 for x in rr.values() if abs(x[2] - v[2]) < 1e-9)
                for v in rr.values()
            },
            "selected_pilot_rates": {k: rr[k][2] for k in chosen},
        }

    json.dump(sel, open(os.path.join(HERE, "selection.json"), "w"), indent=1)
    json.dump(report, open(os.path.join(HERE, "selection_report.json"), "w"), indent=1)
    for t, r in report.items():
        print(t, {k: v for k, v in r.items() if k != "selected_pilot_rates"})
    return 0


if __name__ == "__main__":
    sys.exit(main())
