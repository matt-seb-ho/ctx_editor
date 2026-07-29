#!/usr/bin/env python3
"""T20 / U3 — reconstruct every populated cell of the paper's Table 3 (tab:wildchat)
from recovered Phase-2 turn results, to establish what the "72-92%" honest range was
derived from and whether it reproduces. Zero API calls.

Positive control: the four gpt-5.4 cells were already reproduced exactly by
recompute_u2.py; this script re-derives them alongside the rest and compares every
cell against the published value.
"""
import ast
import json
import os

ROOTS = [
    os.path.expanduser("~/ac3/recovered/ctx_editor/outputs"),
    os.path.expanduser("~/ac3/recovered_t20/ctx_editor/outputs"),
]

# published Table 3 (tab:wildchat) values, from
# writing/overleaf_repo/neurips/neurips_2026_conference.tex L308-312
PUBLISHED = {
    ("gpt-5-mini", "Augment"): (None, None),
    ("gpt-5-mini", "Reset"): (83.0, 83.5),
    ("gpt-5-mini", "Gated-Reset"): (86.1, 83.8),
    ("gpt-5-mini", "Rewrite"): (82.6, 80.3),
    ("gpt-5.4", "Augment"): (84.2, 77.2),
    ("gpt-5.4", "Reset"): (88.6, 77.3),
    ("gpt-5.4", "Gated-Reset"): (74.1, 72.4),
    ("gpt-5.4", "Rewrite"): (83.3, 72.9),
    ("DSV4F", "Augment"): (84.2, None),
    ("DSV4F", "Reset"): (75.0, None),
    ("DSV4F", "Rewrite"): (79.2, 73.6),
    ("Kimi", "Augment"): (85.7, None),
    ("Kimi", "Reset"): (71.6, None),
    ("Kimi", "Rewrite"): (91.5, 76.3),
}

ARM = {"s15": "Reset", "s2": "Gated-Reset", "s3": "Rewrite", "augment": "Augment"}


def model_of(name):
    n = name.lower()
    if "gpt5_4" in n or "gpt_5_4" in n:
        return "gpt-5.4"
    if "dsv4f" in n or "deepseek" in n:
        return "DSV4F"
    if "kimi" in n:
        return "Kimi"
    return "gpt-5-mini"


def arm_of(name):
    b = os.path.basename(name)
    for k in ("s15", "s2", "s3", "augment"):
        if b.startswith(k + "_"):
            return ARM[k]
    return None


def rates(path):
    rows = [json.loads(l) for l in open(path)]
    if not rows:
        return None
    j0 = rows[0]["judgments"]
    if isinstance(j0, str):
        j0 = ast.literal_eval(j0)
    ao_key = next((k for k in j0 if k.startswith("ao_vs_")), None)
    fc_key = next((k for k in j0 if k.startswith("fc_vs_")), None)
    out = {}
    for label, key in (("vs AO", ao_key), ("vs FC", fc_key)):
        if key is None:
            out[label] = None
            continue
        w = n = 0
        for r in rows:
            j = r["judgments"]
            if isinstance(j, str):
                j = ast.literal_eval(j)
            if key not in j:
                continue
            n += 1
            if j[key]["quality_winner"] not in ("ao", "fc", "tie"):
                w += 1
        out[label] = (w, n, 100.0 * w / n if n else float("nan"))
    return out


cells = {}
for root in ROOTS:
    for dirpath, dirnames, filenames in os.walk(root):
        if "turn_results.jsonl" not in filenames:
            continue
        base = os.path.basename(dirpath)
        arm = arm_of(base)
        if arm is None:
            continue  # phase1 / phase2 timestamped dirs handled below
        m = model_of(base)
        r = rates(os.path.join(dirpath, "turn_results.jsonl"))
        if r:
            cells.setdefault((m, arm), []).append((dirpath, r))

# gpt-5-mini Phase-2 cells live in timestamped huang_eval/phase2 dirs; identify by config
for root in ROOTS:
    p2 = os.path.join(root, "huang_eval", "phase2")
    for dirpath, dirnames, filenames in os.walk(p2):
        if "turn_results.jsonl" not in filenames:
            continue
        cfg = {}
        cp = os.path.join(dirpath, "config.json")
        if os.path.exists(cp):
            cfg = json.load(open(cp))
        r = rates(os.path.join(dirpath, "turn_results.jsonl"))
        cells.setdefault(("gpt-5-mini", "phase2:" + os.path.basename(dirpath)), []).append(
            (dirpath, r, cfg.get("strategy") or cfg.get("phase2_strategy") or "?")
        )

print(f"{'model':10} {'arm':14} {'vs AO':>18} {'pub':>7} {'vs FC':>18} {'pub':>7}  dir")
allrates = []
for (m, arm), lst in sorted(cells.items()):
    for entry in lst:
        dirpath, r = entry[0], entry[1]
        extra = entry[2] if len(entry) > 2 else ""
        pub = PUBLISHED.get((m, arm), (None, None))
        s = []
        for i, label in enumerate(("vs AO", "vs FC")):
            v = r.get(label) if r else None
            if v:
                s.append(f"{v[0]:>3}/{v[1]:<3} {v[2]:>6.1f}%")
                allrates.append(((m, arm, label), v[2]))
            else:
                s.append(" " * 18)
        pubs = [f"{p:.1f}" if p is not None else "-" for p in pub]
        print(f"{m:10} {str(arm):14} {s[0]:>18} {pubs[0]:>7} {s[1]:>18} {pubs[1]:>7}  "
              f"{os.path.basename(dirpath)} {extra}")

print()
vals = [v for _, v in allrates]
if vals:
    lo = min(allrates, key=lambda x: x[1])
    hi = max(allrates, key=lambda x: x[1])
    print(f"recomputed min = {lo[1]:.1f}% {lo[0]}")
    print(f"recomputed max = {hi[1]:.1f}% {hi[0]}")

pubvals = [v for k, t in PUBLISHED.items() for v in t if v is not None]
print(f"published Table 3 populated cells: n={len(pubvals)}, "
      f"min={min(pubvals):.1f}, max={max(pubvals):.1f}  -> rounded envelope "
      f"{round(min(pubvals)):.0f}-{round(max(pubvals)):.0f}%")
