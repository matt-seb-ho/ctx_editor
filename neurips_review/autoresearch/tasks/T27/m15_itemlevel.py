#!/usr/bin/env python
"""T27 / M15 — replace the sign test over 36 cells with item-level statistics.

The headline paired result in `replies/v5` is a sign test over 36 (model, task,
prefix) cells.  That statistic (a) discards effect size, (b) treats 36
correlated cells as independent, and (c) is weaker than the item-level exact
McNemar used elsewhere in the same document.  Vg97 Q2 asked for "confidence
intervals, paired tests, or bootstrap"; only the middle one was supplied.

This script recovers the per-sample data behind those 36 cells from the
snapshot, reproduces `paired_analysis_results.txt` as a positive control, and
then computes:
  * item-level exact McNemar pooled across the matrix
  * a problem-clustered bootstrap CI on the mean paired gain

Zero API calls.
"""
import json, re, random, statistics as st
from math import comb
from pathlib import Path
from collections import defaultdict

ROOT = Path("/home/t-matthewho/ac3/ctx_editor")
SNAP = Path("/tmp/t27_phase/ctx_editor")
REPORTS = [
    (ROOT / "docs/reports/post_neurips_ac3_phase1.md", "DeepSeek-V4-Flash"),
    (ROOT / "docs/reports/post_neurips_ac3_phase2.md", None),
]
ROW = re.compile(
    r"^\|\s*(?P<strategy>[A-Za-z0-9 \-+]+?)\s*\|\s*(?P<task>math_v2|code_v2|database_v2|actions_v2)\s*"
    r"\|\s*(?P<conv>\d+)\s*\|\s*(?P<acc>[\d.]+)%[^|]*\|[^|]*\|[^|]*\|[^|]*\|\s*`?(?P<dir>[^`|]*)`?\s*\|?"
)


def model_from_dir(d, default):
    for k, v in (("gpt5_4", "gpt-5.4"), ("kimi", "Kimi-K2.6"),
                 ("gpt5_5", "gpt-5.5"), ("deepseek", "DeepSeek-V4-Flash")):
        if k in d:
            return v
    return default or "unknown"


# ---- parse the same rows paired_analysis.py parses, but keep the dir --------
cells = defaultdict(dict)          # (model, task, conv) -> {strategy: (acc, dir)}
for path, default_model in REPORTS:
    for line in path.read_text().splitlines():
        m = ROW.match(line)
        if not m:
            continue
        strat = m.group("strategy").strip()
        if strat in {"Strategy", ""}:
            continue
        d = m.group("dir").strip()
        cells[(model_from_dir(d, default_model), m.group("task"), int(m.group("conv")))][strat] = (
            float(m.group("acc")), d)

triples = [k for k, v in cells.items() if "Baseline" in v]
print(f"triples with a Baseline row: {len(triples)}  (paired_analysis.py reports 36)")

# ---- load item-level, verifying each cell against its printed accuracy ------
items = defaultdict(dict)          # (model, task, conv) -> {strategy: {sid: bool}}
missing, mismatch = [], []
for key in triples:
    for strat, (acc, d) in cells[key].items():
        p = SNAP / Path(d).relative_to("outputs") / "results.json" if d.startswith("outputs/") \
            else SNAP / "outputs" / Path(d).name / "results.json"
        # dirs are recorded as outputs/<batch>/<cell>
        p = SNAP / d / "results.json" if not p.exists() else p
        if not p.exists():
            missing.append(d)
            continue
        rs = json.loads(p.read_text())
        # `num_turns == 0` is a harness/API error: the conversation never ran.
        # The published tables exclude these from the denominator (e.g. Kimi
        # math conv0 prints 34/39 with "9 errors" against 48 rows on disk), so
        # the item-level analysis must exclude them too, or an arm that errored
        # more would be scored as having failed those items.
        per = {r["sample_id"]: bool(r["is_correct"]) for r in rs if r["num_turns"] > 0}
        got = 100.0 * sum(per.values()) / len(per)
        if abs(got - acc) > 0.06:
            mismatch.append((d, acc, got, len(rs), len(per)))
            continue
        items[key][strat] = per

print(f"POSITIVE CONTROL 1 — per-cell accuracy recomputed from item data "
      f"(errors dropped): {sum(len(v) for v in items.values())} of 168 cells "
      f"reproduce their printed value; {len(mismatch)} mismatch; "
      f"{len(missing)} dirs missing from the snapshot.")
if mismatch[:5]:
    print("   mismatches:", mismatch[:5])
if missing[:5]:
    print("   missing:", missing[:5])

# Arm-symmetric intersection: within each triple keep only samples that ran in
# EVERY arm of that triple.  Anything else lets a differential error rate leak
# into the paired delta.
for key in triples:
    if not items[key]:
        continue
    common = set.intersection(*(set(v) for v in items[key].values()))
    for strat in items[key]:
        items[key][strat] = {s: v for s, v in items[key][strat].items() if s in common}
print("Arm-symmetric intersection applied within each triple; "
      f"pooled n over all triples = {sum(len(next(iter(v.values()))) for v in items.values() if v)}")


def sign_p(w, l):
    n = w + l
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(comb(n, k) for k in range(0, min(w, l) + 1)) / 2 ** n)


mcnemar_p = sign_p   # identical exact binomial form

STRATS = ["Reset", "Augment", "Gated-Reset", "Rewrite", "AO"]
LABEL = {"Reset": "AC3-Reset", "Augment": "AC3-Augment",
         "Gated-Reset": "AC3-Gated-Reset", "Rewrite": "AC3-Rewrite",
         "AO": "Assistant omission"}

print("\n=== POSITIVE CONTROL 2 — cell-level sign test (must match "
      "paired_analysis_results.txt) ===")
print(f"{'strategy':16s} {'n':>3s} {'mean delta':>11s} {'W/L/T':>10s} {'sign p':>9s}")
cell_deltas = {}
for s in STRATS:
    ds, w, l, t = [], 0, 0, 0
    for key in triples:
        if s not in cells[key]:
            continue
        d = cells[key][s][0] - cells[key]["Baseline"][0]
        ds.append(d)
        w, l, t = w + (d > 0), l + (d < 0), t + (d == 0)
    cell_deltas[s] = ds
    print(f"{LABEL[s]:16s} {len(ds):3d} {st.mean(ds):+10.1f}pp "
          f"{f'{w}/{l}/{t}':>10s} {sign_p(w, l):9.4f}")

print("\n=== NEW: item-level exact McNemar, pooled over the matrix ===")
print(f"{'strategy':20s} {'pairs':>6s} {'gain':>8s} {'wins':>6s} {'losses':>7s} {'p':>10s}")
item_rows = {}
for s in STRATS:
    b = c = n = ncorr_s = ncorr_base = 0
    for key in triples:
        if s not in items[key] or "Baseline" not in items[key]:
            continue
        a, z = items[key][s], items[key]["Baseline"]
        for sid in set(a) & set(z):
            n += 1
            ncorr_s += a[sid]; ncorr_base += z[sid]
            b += a[sid] and not z[sid]
            c += z[sid] and not a[sid]
    gain = 100.0 * (ncorr_s - ncorr_base) / n
    item_rows[s] = (n, gain, b, c, mcnemar_p(b, c))
    print(f"{LABEL[s]:20s} {n:6d} {gain:+7.1f}pp {b:6d} {c:7d} {mcnemar_p(b,c):10.2e}")

# ---- problem-clustered bootstrap ------------------------------------------
# Cluster = the underlying problem (task, sample_id).  One problem contributes
# up to 3 prefixes x 3 models of paired observations; resampling whole problems
# respects that correlation, which the sign test over cells does not.
print("\n=== NEW: problem-clustered bootstrap on the mean paired gain (B=10000) ===")
B = 10000
for s in STRATS:
    byprob = defaultdict(list)
    for key in triples:
        if s not in items[key] or "Baseline" not in items[key]:
            continue
        model, task, conv = key
        a, z = items[key][s], items[key]["Baseline"]
        for sid in set(a) & set(z):
            byprob[(task, sid)].append(float(a[sid]) - float(z[sid]))
    probs = list(byprob)
    point = 100.0 * sum(sum(v) for v in byprob.values()) / sum(len(v) for v in byprob.values())
    random.seed(20260729)
    draws = []
    for _ in range(B):
        num = den = 0.0
        for _ in range(len(probs)):
            v = byprob[probs[random.randrange(len(probs))]]
            num += sum(v); den += len(v)
        draws.append(100.0 * num / den)
    draws.sort()
    lo, hi = draws[int(0.025 * B)], draws[int(0.975 * B)]
    print(f"{LABEL[s]:20s} {point:+6.1f}pp  95% CI [{lo:+.1f}, {hi:+.1f}]  "
          f"clusters={len(probs)}")

# ---- head-to-head AC3-Reset vs assistant omission, item level --------------
print("\n=== NEW: AC3-Reset vs assistant omission, item level (the H4/T25 claim) ===")
for scope in ("all", "database_v2"):
    b = c = n = d = 0
    byprob = defaultdict(list)
    for key in triples:
        model, task, conv = key
        if scope != "all" and task != scope:
            continue
        if "Reset" not in items[key] or "AO" not in items[key]:
            continue
        a, z = items[key]["Reset"], items[key]["AO"]
        for sid in set(a) & set(z):
            n += 1; d += a[sid] - z[sid]
            b += a[sid] and not z[sid]; c += z[sid] and not a[sid]
            byprob[(task, sid)].append(float(a[sid]) - float(z[sid]))
    probs = list(byprob)
    random.seed(20260729)
    draws = []
    for _ in range(B):
        num = den = 0.0
        for _ in range(len(probs)):
            v = byprob[probs[random.randrange(len(probs))]]
            num += sum(v); den += len(v)
        draws.append(100.0 * num / den)
    draws.sort()
    print(f"  {scope:12s} n={n:5d}  gain {100.0*d/n:+.1f}pp  "
          f"95% CI [{draws[int(.025*B)]:+.1f}, {draws[int(.975*B)]:+.1f}]  "
          f"wins {b} / losses {c}  exact McNemar p = {mcnemar_p(b,c):.2e}")
