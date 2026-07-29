#!/usr/bin/env python
"""T14 — build the side-by-side corrected matrix from the re-judge output.

Emits, per (arm, task): shipped adjusted accuracy, raw accuracy, arm-symmetric
corrected accuracy, and the exclusion rates under both judging regimes.

Controls printed first:
  C1  On arms that never reset (baseline / append_analysis / omit_assistant) the
      symmetric input IS the shipped input, so shipped-vs-symmetric disagreement
      is pure judge-model drift (gpt-5-mini -> gpt-5.4-mini). Must be small.
  C2  `mean_user_turns_seen` under `visible` mode must be ~1 for reset arms and
      ~= total for non-reset arms. This is the mechanism, measured.
  C3  raw accuracy is identical across all three columns' numerators.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent

ARM = {
    "baseline": ("Baseline (full context)", False),
    "append_analysis": ("AC3-Augment (S1)", False),
    "omit_assistant": ("AO / Omit-Assistant", False),
    "context_edit_v2_no_gate": ("AC3-Reset", True),
    "context_edit_v2_no_gate_accumulate": ("AC3-Reset", True),
    "context_edit_v2_gated": ("AC3-Gated-Reset", True),
    "context_edit_v2_gated_accumulate": ("AC3-Gated-Reset", True),
    "ac3_rewrite_lic": ("AC3-Rewrite", True),
}


def parse(cell: str):
    """`context_edit_v2_no_gate_accumulate_actions_v2_conv0_1779010325` -> arm, task."""
    for key in sorted(ARM, key=len, reverse=True):
        if cell.startswith(key + "_"):
            rest = cell[len(key) + 1:]
            task = rest.split("_v2_conv")[0]
            return ARM[key][0], task, ARM[key][1]
    return None, None, None


def load(mode):
    p = HERE / f"rejudge_post_neurips_ac3_phase1_{mode}.json"
    return json.load(open(p)) if p.exists() else []


sym = {r["cell"]: r for r in load("symmetric")}
vis = {r["cell"]: r for r in load("visible")}

print(f"loaded symmetric={len(sym)} visible={len(vis)}\n")

# ---------------------------------------------------------------- controls
print("=" * 100)
print("CONTROLS")
print("=" * 100)

drift_nores, drift_res = [], []
for c, r in sym.items():
    arm, task, resets = parse(c)
    if arm is None:
        continue
    d = (r["excluded"] or 0) - (r["shipped_excluded"] or 0)
    (drift_res if resets else drift_nores).append((c, d, r["n_judged"]))

def summ(rows, label):
    if not rows:
        print(f"  {label}: no data")
        return
    tot = sum(abs(d) for _, d, _ in rows)
    n = sum(j for _, _, j in rows)
    print(f"  {label}: {len(rows)} cells, sum|shipped-excl - symmetric-excl| = {tot} "
          f"over {n} judged samples ({tot/n:.1%} of judged)")

print("C1  shipped(gpt-5-mini, visible-only) vs symmetric(gpt-5.4-mini, all-visible)")
summ(drift_nores, "    non-reset arms (inputs identical -> pure judge drift)")
summ(drift_res, "    reset arms      (inputs differ    -> visibility effect)")

print("\nC2  user turns the judge actually saw (mean per sample)")
byarm = defaultdict(lambda: [0.0, 0.0, 0])
for c, r in sym.items():
    arm, task, resets = parse(c)
    if arm is None or r["mean_user_turns_seen"] is None:
        continue
    a = byarm[(arm, resets)]
    a[0] += r["mean_user_turns_seen"] * r["n_judged"]
    a[1] += r["mean_user_turns_total"] * r["n_judged"]
    a[2] += r["n_judged"]
for (arm, resets), (s, t, n) in sorted(byarm.items(), key=lambda x: (x[0][1], x[0][0])):
    tag = "RESETS" if resets else "no reset"
    print(f"    {arm:26s} [{tag:8s}]  symmetric view: {s/n:.2f} unique user turns/sample (n={n})")
for c, r in list(vis.items())[:0]:
    pass
if vis:
    byarm2 = defaultdict(lambda: [0.0, 0])
    for c, r in vis.items():
        arm, task, resets = parse(c)
        if arm is None or r["mean_user_turns_seen"] is None:
            continue
        a = byarm2[(arm, resets)]
        a[0] += r["mean_user_turns_seen"] * r["n_judged"]
        a[1] += r["n_judged"]
    print()
    for (arm, resets), (s, n) in sorted(byarm2.items(), key=lambda x: (x[0][1], x[0][0])):
        tag = "RESETS" if resets else "no reset"
        print(f"    {arm:26s} [{tag:8s}]  SHIPPED view:   {s/n:.2f} user turns/sample (n={n})")

# ---------------------------------------------------------------- matrix
print("\n" + "=" * 100)
print("CORRECTED MATRIX — post_neurips_ac3_phase1 (deepseek-v4-flash, 3 replicate runs/cell)")
print("=" * 100)

agg = defaultdict(lambda: dict(n=0, correct=0, judged=0, ship_ex=0, sym_ex=0, vis_ex=0, vis_judged=0, runs=0))
for c, r in sym.items():
    arm, task, resets = parse(c)
    if arm is None:
        continue
    a = agg[(arm, task)]
    a["n"] += r["raw_total"]
    a["correct"] += r["raw_correct"]
    a["judged"] += r["n_judged"]
    a["ship_ex"] += r["shipped_excluded"] or 0
    a["sym_ex"] += r["excluded"]
    a["runs"] += 1
    a["resets"] = resets
    if c in vis:
        a["vis_ex"] += vis[c]["excluded"]
        a["vis_judged"] += vis[c]["n_judged"]

hdr = (f"{'arm':26s} {'task':10s} {'n':>5s} {'ok':>5s} | {'RAW':>7s} | "
       f"{'ship-ex':>8s} {'SHIPPED-ADJ':>11s} | {'sym-ex':>7s} {'SYM-ADJ':>8s} | {'ship-raw':>8s} {'sym-raw':>7s}")
print(hdr)
print("-" * len(hdr))
order = ["Baseline (full context)", "AO / Omit-Assistant", "AC3-Augment (S1)",
         "AC3-Reset", "AC3-Gated-Reset", "AC3-Rewrite"]
rows_out = []
for arm in order:
    for task in ["math", "code", "database", "actions"]:
        a = agg.get((arm, task))
        if not a:
            continue
        n, ok, j = a["n"], a["correct"], a["judged"]
        raw = ok / n
        sadj = ok / (n - a["ship_ex"]) if n - a["ship_ex"] > 0 else 0
        yadj = ok / (n - a["sym_ex"]) if n - a["sym_ex"] > 0 else 0
        print(f"{arm:26s} {task:10s} {n:5d} {ok:5d} | {raw*100:6.1f}% | "
              f"{a['ship_ex']:3d}/{j:<4d} {sadj*100:10.1f}% | "
              f"{a['sym_ex']:3d}/{j:<3d} {yadj*100:7.1f}% | "
              f"{(sadj-raw)*100:+7.1f} {(yadj-raw)*100:+6.1f}")
        rows_out.append(dict(arm=arm, task=task, n=n, correct=ok, judged=j,
                             raw=raw, shipped_excluded=a["ship_ex"], shipped_adj=sadj,
                             symmetric_excluded=a["sym_ex"], symmetric_adj=yadj,
                             resets=a["resets"], runs=a["runs"]))
json.dump(rows_out, open(HERE / "corrected_matrix.json", "w"), indent=2)

# ---------------------------------------------------------------- flips
print("\n" + "=" * 100)
print("DOES ANY QUALITATIVE CONCLUSION FLIP?  (arm vs Baseline, per task)")
print("=" * 100)
by = {(r["arm"], r["task"]): r for r in rows_out}
print(f"{'arm':26s} {'task':10s} {'Δ raw':>8s} {'Δ shipped-adj':>14s} {'Δ sym-adj':>10s}  {'flip?':>6s}")
flips = []
for arm in order[1:]:
    for task in ["math", "code", "database", "actions"]:
        r = by.get((arm, task)); b = by.get(("Baseline (full context)", task))
        if not r or not b:
            continue
        dr = (r["raw"] - b["raw"]) * 100
        ds = (r["shipped_adj"] - b["shipped_adj"]) * 100
        dy = (r["symmetric_adj"] - b["symmetric_adj"]) * 100
        flip = "FLIP" if (ds > 0) != (dy > 0) else ""
        if flip:
            flips.append((arm, task, ds, dy))
        print(f"{arm:26s} {task:10s} {dr:+7.1f} {ds:+13.1f} {dy:+9.1f}  {flip:>6s}")
print()
if flips:
    print("!!! SIGN FLIPS between shipped-adjusted and arm-symmetric-corrected:")
    for arm, task, ds, dy in flips:
        print(f"    {arm} on {task}: shipped {ds:+.1f}pp -> corrected {dy:+.1f}pp")
else:
    print("No sign flips: every arm that beats baseline under the shipped metric also")
    print("beats it under the arm-symmetric correction, and vice versa.")
