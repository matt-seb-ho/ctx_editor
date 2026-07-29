#!/usr/bin/env python
"""T27 / M3 — the `95.0 +/- 0.0` cells.

Two questions:
  (a) Are the three replicates independent draws, or is a cache / determinism
      making them byte-identical?  Test: do the three runs FAIL on the same
      problems, and do the assistant's turn counts / answers differ?
  (b) Give a bootstrap CI over problems (Vg97 asked for CIs; a +/- 0.0 over
      three replicates is a decoder-variance statement, not a sampling one).

Zero API calls.  Item-level data from outputs/rebuttal_random/*/results.json.
"""
import json, random, statistics as st
from pathlib import Path

ROOT = Path("/home/t-matthewho/ac3/ctx_editor")
OUT = ROOT / "outputs/rebuttal_random"

ARMS = {
    "baseline": ["full_baseline", "rep2_baseline", "rep3_baseline"],
    "AC3-Reset": ["full_reset", "rep2_reset", "rep3_reset"],
    "AC3-Gated-Reset": ["full_gated", "rep2_gated", "rep3_gated"],
}


def load(d):
    rs = json.loads((OUT / d / "results.json").read_text())
    return {r["sample_id"]: r for r in rs}


data = {arm: [load(d) for d in dirs] for arm, dirs in ARMS.items()}

# ---------------------------------------------------------------- sanity
ids = None
for arm, runs in data.items():
    for d, run in zip(ARMS[arm], runs):
        assert len(run) == 40, (d, len(run))
        if ids is None:
            ids = set(run)
        assert set(run) == ids, f"{d} draws different problems"
print(f"POSITIVE CONTROL: all 9 runs cover the identical 40 problems.  n={len(ids)}")
ids = sorted(ids)

print("\n=== raw accuracy per run (must reproduce v5's printed cells) ===")
for arm, runs in data.items():
    cnt = [sum(r[i]["is_correct"] for i in ids) for r in runs]
    accs = [100.0 * c / 40 for c in cnt]
    sd = st.stdev(accs)
    print(f"  {arm:18s} {'/'.join(f'{c}/40' for c in cnt):>22s}  "
          f"= {'/'.join(f'{a:.1f}' for a in accs):>20s}  mean {st.mean(accs):5.1f} sd {sd:.1f}")

# ------------------------------------------------- (a) independence probes
print("\n=== (a) are the replicates independent draws? ===")
for arm, runs in data.items():
    fails = [set(i for i in ids if not r[i]["is_correct"]) for r in runs]
    union = set().union(*fails)
    inter = set.intersection(*fails)
    turns = [[r[i]["num_turns"] for i in ids] for r in runs]
    n_turn_diff = sum(1 for k, i in enumerate(ids)
                      if len({t[k] for t in turns}) > 1)
    ans = [[r[i].get("extracted_answer") for i in ids] for r in runs]
    n_ans_diff = sum(1 for k, i in enumerate(ids)
                     if len({a[k] for a in ans}) > 1)
    print(f"  {arm:18s} failing sets {[sorted(f) for f in fails]}")
    print(f"  {'':18s} |union of failures| = {len(union)}, "
          f"|always-fails| = {len(inter)}; "
          f"problems whose turn-count differs across runs: {n_turn_diff}/40; "
          f"whose extracted answer differs: {n_ans_diff}/40")

# ----------------------------------------------------- (b) bootstrap CIs
# Cluster on the PROBLEM (the sampling unit reviewers care about).  Resample
# problems with replacement; within a resampled problem keep all 3 replicates
# and take that problem's mean success rate.  This propagates both sampling
# variance over problems and decoder variance over replicates.
random.seed(20260729)
B = 20000
print(f"\n=== (b) problem-clustered bootstrap over the N=3 replicates (B={B}) ===")
boot_by_arm = {}
for arm, runs in data.items():
    per_problem = {i: st.mean(float(r[i]["is_correct"]) for r in runs) for i in ids}
    draws = []
    for _ in range(B):
        samp = [per_problem[random.choice(ids)] for _ in ids]
        draws.append(100.0 * st.mean(samp))
    draws.sort()
    boot_by_arm[arm] = draws
    point = 100.0 * st.mean(per_problem.values())
    lo, hi = draws[int(0.025 * B)], draws[int(0.975 * B)]
    print(f"  {arm:18s} {point:5.1f}  95% CI [{lo:.1f}, {hi:.1f}]")

# paired bootstrap of the deltas vs baseline (same resampled problems)
print("\n=== (b2) PAIRED problem-clustered bootstrap, delta vs full context ===")
pp = {arm: {i: st.mean(float(r[i]["is_correct"]) for r in runs) for i in ids}
      for arm, runs in data.items()}
for arm in ("AC3-Reset", "AC3-Gated-Reset"):
    random.seed(20260729)
    draws = []
    for _ in range(B):
        samp = [random.choice(ids) for _ in ids]
        d = st.mean(pp[arm][i] - pp["baseline"][i] for i in samp)
        draws.append(100.0 * d)
    draws.sort()
    point = 100.0 * st.mean(pp[arm][i] - pp["baseline"][i] for i in ids)
    lo, hi = draws[int(0.025 * B)], draws[int(0.975 * B)]
    frac_pos = sum(1 for d in draws if d > 0) / B
    print(f"  {arm:18s} {point:+5.1f}pp  95% CI [{lo:+.1f}, {hi:+.1f}]  "
          f"P(delta>0)={frac_pos:.3f}")

# pooled-run exact McNemar (item-level), replicate-pooled 120 vs 120
print("\n=== (b3) item-level exact McNemar, replicates pooled (120 pairs) ===")
from math import comb
def mcnemar(b, c):
    n = b + c
    if n == 0:
        return 1.0
    p = sum(comb(n, k) for k in range(0, min(b, c) + 1)) / 2 ** n
    return min(1.0, 2 * p)
for arm in ("AC3-Reset", "AC3-Gated-Reset"):
    b = c = 0
    for k in range(3):
        for i in ids:
            x = data[arm][k][i]["is_correct"]; y = data["baseline"][k][i]["is_correct"]
            b += x and not y
            c += y and not x
    print(f"  {arm:18s} wins {b} / losses {c} over 120 replicate-item pairs, "
          f"exact McNemar p = {mcnemar(b, c):.4f}")
