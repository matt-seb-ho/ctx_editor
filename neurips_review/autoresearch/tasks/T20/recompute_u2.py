#!/usr/bin/env python3
"""T20 / U2 — recompute the WildChat gpt-5.4 Reset-vs-Gated-Reset comparison
from the recovered Phase-2 turn results. Zero API calls.

Positive control: reproduce the four published Table 3 (tab:wildchat) gpt-5.4
"vs AO" cells from the same files before drawing any new conclusion.
"""
import ast
import json
import os
from itertools import combinations

BASE = os.path.expanduser(
    "~/ac3/recovered/ctx_editor/outputs/post_may26_wildchat_gpt54"
)
ARMS = {  # dir prefix -> (published vs-AO cell, judgment key)
    "s15": (88.6, "ao_vs_s15"),
    "s2": (74.1, "ao_vs_s2"),
    "augment": (84.2, "ao_vs_augment"),
    "s3": (83.3, "ao_vs_s3"),
}


def load(prefix):
    d = [x for x in os.listdir(BASE) if x.startswith(prefix + "_gpt5_4")][0]
    rows = [json.loads(l) for l in open(os.path.join(BASE, d, "turn_results.jsonl"))]
    out = {}
    for r in rows:
        j = r["judgments"]
        if isinstance(j, str):
            j = ast.literal_eval(j)
        out[(r["conversation_id"], str(r["turn_index"]))] = j
    return out


def winrate(judg, key, keys=None):
    ks = keys if keys is not None else list(judg)
    w = t = l = 0
    for k in ks:
        v = judg[k].get(key)
        if v is None:
            # fall back: single judgment dict per row
            v = list(judg[k].values())[0]
        q = v["quality_winner"]
        if q == "ao":
            l += 1
        elif q == "tie":
            t += 1
        else:
            w += 1
    n = len(ks)
    return w, t, l, n, 100.0 * w / n if n else float("nan")


data = {a: load(a) for a in ARMS}

print("=== POSITIVE CONTROL: reproduce published Table 3 (gpt-5.4, vs AO) ===")
print(f"{'arm':10} {'n':>4} {'win':>4} {'tie':>4} {'loss':>4} {'recomputed':>11} {'published':>10} {'ok':>4}")
for a, (pub, key) in ARMS.items():
    # judgment key name varies; discover it
    any_j = next(iter(data[a].values()))
    k = key if key in any_j else [x for x in any_j if x.startswith("ao_vs_")][0]
    w, t, l, n, r = winrate(data[a], k)
    print(f"{a:10} {n:>4} {w:>4} {t:>4} {l:>4} {r:>10.1f}% {pub:>9.1f}% {'YES' if abs(r-pub)<0.1 else 'NO':>4}")

print()
print("=== POOL OVERLAP: are the arms evaluated on the same prefixes? ===")
for a in ARMS:
    print(f"  {a:10} n={len(data[a]):>3}")
for a, b in combinations(ARMS, 2):
    A, B = set(data[a]), set(data[b])
    print(f"  {a:>8} vs {b:<8} |A|={len(A):>3} |B|={len(B):>3} "
          f"|A&B|={len(A & B):>3} |A-B|={len(A - B):>3} |B-A|={len(B - A):>3}")

print()
print("=== MATCHED-POOL Reset (s15) vs Gated-Reset (s2) ===")
A, B = set(data["s15"]), set(data["s2"])
inter = sorted(A & B)
ka = [x for x in next(iter(data["s15"].values())) if x.startswith("ao_vs_")][0]
kb = [x for x in next(iter(data["s2"].values())) if x.startswith("ao_vs_")][0]
wa, ta, la, na, ra = winrate(data["s15"], ka, inter)
wb, tb, lb, nb, rb = winrate(data["s2"], kb, inter)
print(f"  matched n = {len(inter)}")
print(f"  Reset (s15)      {wa}/{na} = {ra:.1f}%   (published, unmatched: 88.6% on n=44)")
print(f"  Gated-Reset (s2) {wb}/{nb} = {rb:.1f}%   (published, unmatched: 74.1% on n=58)")
print(f"  matched delta = {ra - rb:+.1f}pp   (published delta = +14.5pp)")

# paired McNemar on the matched pool
b_ = sum(1 for k in inter
         if (data["s15"][k][ka]["quality_winner"] not in ("ao", "tie"))
         and (data["s2"][k][kb]["quality_winner"] in ("ao", "tie")))
c_ = sum(1 for k in inter
         if (data["s15"][k][ka]["quality_winner"] in ("ao", "tie"))
         and (data["s2"][k][kb]["quality_winner"] not in ("ao", "tie")))
print(f"  discordant pairs: Reset-only-win={b_}, Gated-only-win={c_}")
try:
    from scipy.stats import binomtest
    if b_ + c_:
        p = binomtest(b_, b_ + c_, 0.5).pvalue
        print(f"  exact McNemar p = {p:.4f}")
except Exception as e:  # pragma: no cover
    print("  (scipy unavailable:", e, ")")

print()
print("=== Gate behaviour on the s2 pool ===")
d = [x for x in os.listdir(BASE) if x.startswith("s2_gpt5_4")][0]
rows = [json.loads(l) for l in open(os.path.join(BASE, d, "turn_results.jsonl"))]
edited = 0
for r in rows:
    a = r.get("s2_analysis")
    if isinstance(a, str):
        a = ast.literal_eval(a)
    if a and a.get("edited"):
        edited += 1
print(f"  s2 edited (gate open) on {edited}/{len(rows)} = {100*edited/len(rows):.1f}% of Phase-2 turns")
