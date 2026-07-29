#!/usr/bin/env python
"""T27 — analyse the new database cells against T1's existing arms.

Cross-checks metrics.json against run_summary.json and results.json for every
cell before using any number (trap 7 / the double-write corruption incident).
Raw accuracy only; `adjusted_accuracy` is not comparable across editing arms.
"""
import json
from math import comb
from pathlib import Path

ROOT = Path("/home/t-matthewho/ac3/ctx_editor")
CELLS = [
    ("Baseline (full context)",              "outputs/T1/main/db_baseline"),
    ("Summarisation 1-call (T1, published)", "outputs/T1/main/db_summarize1"),
    ("Summarisation 1-call (T27 replicate)", "outputs/T27/db_summarize1_rep2"),
    ("Summarisation NEUTRAL prompt (new)",   "outputs/T27/db_summarize_neutral"),
    ("Summarisation 2-call (T1)",            "outputs/T1/main/db_summarize2"),
    ("MT-OSC w=4 (T1, as published)",        "outputs/T1/main/db_mtosc_w4"),
    ("MT-OSC w=2 (new, post-fix)",           "outputs/T27/db_mtosc_w2"),
    ("AC3-Gated-Reset (T1)",                 "outputs/T1/main/db_gated"),
    ("AC3-Reset (T1)",                       "outputs/T1/main/db_reset"),
]


def load(d):
    p = ROOT / d
    if not (p / "run_summary.json").exists():
        return None
    rs = json.loads((p / "results.json").read_text())
    per = {r["sample_id"]: bool(r["is_correct"]) for r in rs if r["num_turns"] > 0}
    n_err = len(rs) - len(per)
    met = json.loads((p / "metrics.json").read_text())
    summ = json.loads((p / "run_summary.json").read_text())
    correct = sum(per.values())
    # cross-file consistency (the check that caught the double-write corruption)
    m_corr = met.get("correct", met.get("num_correct"))
    s_acc = (summ.get("metrics") or {}).get("accuracy", summ.get("accuracy"))
    ok = (m_corr == correct) and (s_acc is None or abs(s_acc * (100 if s_acc <= 1 else 1)
                                                       - 100.0 * correct / len(per)) < 0.2)
    return dict(per=per, n=len(per), correct=correct, errors=n_err,
                acc=100.0 * correct / len(per), consistent=ok,
                m_corr=m_corr, s_acc=s_acc)


def mcnemar(b, c):
    n = b + c
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(comb(n, k) for k in range(0, min(b, c) + 1)) / 2 ** n)


data = {}
print("=== cells and cross-file consistency ===")
for name, d in CELLS:
    r = load(d)
    if r is None:
        print(f"  {name:40s} NOT PRESENT ({d})")
        continue
    data[name] = r
    flag = "OK " if r["consistent"] else "*** MISMATCH ***"
    print(f"  {name:40s} {r['correct']:3d}/{r['n']:3d} = {r['acc']:5.1f}%  "
          f"errors={r['errors']}  cross-file {flag}")

base = "Baseline (full context)"
if base in data:
    print("\n=== paired vs full context (McNemar exact, common samples only) ===")
    for name, r in data.items():
        if name == base:
            continue
        common = set(r["per"]) & set(data[base]["per"])
        b = sum(1 for s in common if r["per"][s] and not data[base]["per"][s])
        c = sum(1 for s in common if data[base]["per"][s] and not r["per"][s])
        d_pp = 100.0 * sum(r["per"][s] - data[base]["per"][s] for s in common) / len(common)
        print(f"  {name:40s} n={len(common):3d}  {d_pp:+6.1f}pp  "
              f"W/L {b}/{c}  p={mcnemar(b,c):.4f}")

print("\n=== head-to-head pairs that matter ===")
PAIRS = [
    ("Summarisation NEUTRAL prompt (new)", "Summarisation 1-call (T27 replicate)"),
    ("Summarisation NEUTRAL prompt (new)", "Summarisation 1-call (T1, published)"),
    ("AC3-Reset (T1)",                     "Summarisation NEUTRAL prompt (new)"),
    ("AC3-Gated-Reset (T1)",               "Summarisation NEUTRAL prompt (new)"),
    ("MT-OSC w=2 (new, post-fix)",         "MT-OSC w=4 (T1, as published)"),
    ("AC3-Reset (T1)",                     "MT-OSC w=2 (new, post-fix)"),
]
for a, z in PAIRS:
    if a not in data or z not in data:
        print(f"  {a} - {z}: one side missing")
        continue
    common = set(data[a]["per"]) & set(data[z]["per"])
    b = sum(1 for s in common if data[a]["per"][s] and not data[z]["per"][s])
    c = sum(1 for s in common if data[z]["per"][s] and not data[a]["per"][s])
    d_pp = 100.0 * sum(data[a]["per"][s] - data[z]["per"][s] for s in common) / len(common)
    print(f"  {a[:34]:34s} - {z[:34]:34s}  n={len(common):3d}  {d_pp:+6.1f}pp  "
          f"W/L {b}/{c}  p={mcnemar(b,c):.4f}")
