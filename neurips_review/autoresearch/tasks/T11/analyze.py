#!/usr/bin/env python3
"""T11 analysis: position bias, swap consistency, order-balanced win rates,
cross-judge agreement (Cohen's kappa), self-consistency, positive controls."""

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

OUT = Path("/home/t-matthewho/ac3/ctx_editor/neurips_review/autoresearch/tasks/T11/out")


def load(name):
    p = OUT / name
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


def mean_std(xs):
    n = len(xs)
    if n == 0:
        return 0.0, 0.0
    m = sum(xs) / n
    if n < 2:
        return m, 0.0
    v = sum((x - m) ** 2 for x in xs) / (n - 1)
    return m, v ** 0.5


def kappa(pairs):
    """Cohen's kappa over a list of (label_a, label_b)."""
    n = len(pairs)
    if n == 0:
        return float("nan"), float("nan")
    labels = sorted({x for p in pairs for x in p})
    po = sum(1 for a, b in pairs if a == b) / n
    ca = Counter(a for a, _ in pairs)
    cb = Counter(b for _, b in pairs)
    pe = sum((ca[l] / n) * (cb[l] / n) for l in labels)
    k = (po - pe) / (1 - pe) if pe < 1 else float("nan")
    return po, k


def agreement_stats(pairs):
    """raw agreement, Cohen's kappa, PABAK, Gwet's AC1 (kappa-paradox robust)."""
    n = len(pairs)
    if n == 0:
        return dict(n=0, po=float("nan"), kappa=float("nan"),
                    pabak=float("nan"), ac1=float("nan"))
    labels = sorted({x for p in pairs for x in p})
    q = len(labels)
    po, k = kappa(pairs)
    pabak = (q * po - 1) / (q - 1) if q > 1 else float("nan")
    ca = Counter(a for a, _ in pairs)
    cb = Counter(b for _, b in pairs)
    pi = {l: (ca[l] / n + cb[l] / n) / 2 for l in labels}
    pe_g = sum(p * (1 - p) for p in pi.values()) / (q - 1) if q > 1 else 0.0
    ac1 = (po - pe_g) / (1 - pe_g) if pe_g < 1 else float("nan")
    return dict(n=n, po=po, kappa=k, pabak=pabak, ac1=ac1)


def fmt_ag(tag, pairs):
    s = agreement_stats(pairs)
    return (f"{tag} n={s['n']:4d}  raw={s['po']*100:.1f}%  kappa={s['kappa']:.3f}  "
            f"PABAK={s['pabak']:.3f}  AC1={s['ac1']:.3f}")


def index_by_order(rows, dim="quality"):
    """{(pair_id, order): label}, ok-only."""
    d = {}
    for r in rows:
        if not r.get("ok"):
            continue
        d[(r["pair_id"], r["order"])] = r[f"{dim}_winner"]
    return d


def fail_count(rows):
    return sum(1 for r in rows if not r.get("ok"))


# --------------------------------------------------------------------- position bias
def position_bias(rows, dim="quality", label=""):
    idx = index_by_order(rows, dim)
    meta = {r["pair_id"]: r for r in rows}
    pids = sorted({pid for pid, _ in idx})
    both = [p for p in pids if (p, "ao_first") in idx and (p, "var_first") in idx]

    def wr(order, subset=None):
        sub = subset if subset is not None else both
        v = [idx[(p, order)] for p in sub]
        return (sum(1 for x in v if x == "var") / len(v) * 100) if v else float("nan"), len(v)

    wr_ao_first, n1 = wr("ao_first")   # variant presented SECOND (position B)
    wr_var_first, n2 = wr("var_first")  # variant presented FIRST  (position A)
    balanced = (wr_ao_first + wr_var_first) / 2

    consistent = sum(1 for p in both if idx[(p, "ao_first")] == idx[(p, "var_first")])
    swapcons = consistent / len(both) * 100 if both else float("nan")

    # first-position preference over all 2N judgements
    picksA = picksB = ties = 0
    for p in both:
        for o in ("ao_first", "var_first"):
            lab = idx[(p, o)]
            if lab == "tie":
                ties += 1
            elif (o == "ao_first" and lab == "ao") or (o == "var_first" and lab == "var"):
                picksA += 1
            else:
                picksB += 1
    tot = picksA + picksB + ties

    # inconsistent-pair breakdown
    inc = [p for p in both if idx[(p, "ao_first")] != idx[(p, "var_first")]]
    inc_firstpos = sum(1 for p in inc
                       if idx[(p, "ao_first")] == "ao" and idx[(p, "var_first")] == "var")
    inc_secondpos = sum(1 for p in inc
                        if idx[(p, "ao_first")] == "var" and idx[(p, "var_first")] == "ao")
    inc_tie = len(inc) - inc_firstpos - inc_secondpos

    # per-seed / per-variant
    per = defaultdict(lambda: defaultdict(list))
    for p in both:
        m = meta[p]
        for o in ("ao_first", "var_first"):
            per[(m["variant"], m["seed"])][o].append(idx[(p, o)])

    cells = {}
    for (var, seed), od in sorted(per.items()):
        r1 = sum(1 for x in od["ao_first"] if x == "var") / len(od["ao_first"]) * 100
        r2 = sum(1 for x in od["var_first"] if x == "var") / len(od["var_first"]) * 100
        cells[(var, seed)] = {"n": len(od["ao_first"]), "ao_first": r1, "var_first": r2,
                              "balanced": (r1 + r2) / 2}

    return {
        "label": label, "dim": dim, "n_pairs": len(both),
        "wr_variant_second": wr_ao_first, "wr_variant_first": wr_var_first,
        "balanced": balanced, "delta_first_minus_second": wr_var_first - wr_ao_first,
        "swap_consistency": swapcons,
        "picksA": picksA, "picksB": picksB, "ties": ties, "total_judgements": tot,
        "pA": picksA / tot * 100 if tot else 0, "pB": picksB / tot * 100 if tot else 0,
        "pTie": ties / tot * 100 if tot else 0,
        "n_inconsistent": len(inc), "inc_first_pos": inc_firstpos,
        "inc_second_pos": inc_secondpos, "inc_tie_flip": inc_tie,
        "cells": cells, "failures": fail_count(rows),
    }


def balanced_label(idx, pid):
    """Order-balanced consensus label for a pair: agreement across both orders,
    else 'tie' (i.e. order-sensitive pairs count as no decision)."""
    a = idx.get((pid, "ao_first"))
    b = idx.get((pid, "var_first"))
    if a is None or b is None:
        return None
    return a if a == b else "tie"


def main():
    report = []
    A = load("order_gpt5mini.jsonl")
    B = load("order_deepseek.jsonl")
    C = load("order_kimi.jsonl")
    REP = load("repeat_gpt5mini.jsonl")
    ctrls = {n: load(f"control_{n}.jsonl") for n in ("gpt5mini", "deepseek", "kimi")}

    print("=" * 78)
    print("LOADED:", {"A_gpt5mini": len(A), "B_deepseek": len(B), "C_kimi": len(C),
                      "repeat": len(REP), **{k: len(v) for k, v in ctrls.items()}})

    # ---- positive controls
    print("\n### Positive controls (good vs degraded copy of itself)")
    for name, rows in ctrls.items():
        if not rows:
            continue
        ok = [r for r in rows if r.get("ok")]
        good = sum(1 for r in ok if r["quality_winner"] == "good")
        deg = sum(1 for r in ok if r["quality_winner"] == "degraded")
        tie = sum(1 for r in ok if r["quality_winner"] == "tie")
        bo = defaultdict(lambda: [0, 0])
        for r in ok:
            bo[r["order"]][0] += 1 if r["quality_winner"] == "good" else 0
            bo[r["order"]][1] += 1
        print(f"  {name:10s} n={len(ok)} good={good} degraded={deg} tie={tie} "
              f"fail={fail_count(rows)}  by-order=" +
              " ".join(f"{o}:{g}/{t}" for o, (g, t) in sorted(bo.items())))

    # ---- position bias
    print("\n### Position bias (quality dimension)")
    pbs = {}
    for name, rows in (("gpt-5-mini (headline judge)", A), ("DeepSeek-V4-Flash", B),
                       ("Kimi-K2.6", C)):
        if not rows:
            continue
        pb = position_bias(rows, "quality", name)
        pbs[name] = pb
        print(f"\n  -- {name}: n={pb['n_pairs']} pairs, {pb['total_judgements']} judgements, "
              f"{pb['failures']} hard failures")
        print(f"     variant presented SECOND: {pb['wr_variant_second']:.1f}%")
        print(f"     variant presented FIRST : {pb['wr_variant_first']:.1f}%")
        print(f"     order-balanced          : {pb['balanced']:.1f}%   "
              f"(delta first-second = {pb['delta_first_minus_second']:+.1f}pp)")
        print(f"     swap consistency        : {pb['swap_consistency']:.1f}%")
        print(f"     P(pick A)={pb['pA']:.1f}%  P(pick B)={pb['pB']:.1f}%  tie={pb['pTie']:.1f}%")
        print(f"     inconsistent pairs n={pb['n_inconsistent']}: "
              f"always-first={pb['inc_first_pos']} always-second={pb['inc_second_pos']} "
              f"tie-flip={pb['inc_tie_flip']}")
        for (var, seed), c in pb["cells"].items():
            print(f"       {var:8s} seed{seed}: n={c['n']:3d}  "
                  f"var2nd={c['ao_first']:5.1f}  var1st={c['var_first']:5.1f}  "
                  f"bal={c['balanced']:5.1f}")
        # seed-level mean +/- sd, matching headline format
        for var in ("s15", "augment"):
            xs = [c["balanced"] for (v, s), c in pb["cells"].items() if v == var]
            x2 = [c["ao_first"] for (v, s), c in pb["cells"].items() if v == var]
            x3 = [c["var_first"] for (v, s), c in pb["cells"].items() if v == var]
            if xs:
                m, sd = mean_std(xs)
                m2, sd2 = mean_std(x2)
                m3, sd3 = mean_std(x3)
                print(f"     >>> {var}: balanced {m:.1f} +/- {sd:.1f} | "
                      f"var-2nd {m2:.1f} +/- {sd2:.1f} | var-1st {m3:.1f} +/- {sd3:.1f}")

    # ---- on-topic dimension, headline judge
    if A:
        pbo = position_bias(A, "ontopic", "gpt-5-mini ontopic")
        print(f"\n  -- gpt-5-mini, ON-TOPIC dim: var2nd={pbo['wr_variant_second']:.1f} "
              f"var1st={pbo['wr_variant_first']:.1f} bal={pbo['balanced']:.1f} "
              f"swapcons={pbo['swap_consistency']:.1f}")

    # ---- agreement vs the original May-2026 stored verdicts
    if A:
        idxA = index_by_order(A, "quality")
        orig = {r["pair_id"]: r["orig_quality_winner"] for r in A}
        norm = {"s15": "var", "augment": "var", "ao": "ao", "tie": "tie"}
        prs = []
        for pid in {p for p, _ in idxA}:
            bl = balanced_label(idxA, pid)
            o = norm.get(orig.get(pid))
            if bl and o:
                prs.append((bl, o))
        po, k = kappa(prs)
        print(f"\n### Re-judge vs ORIGINAL stored verdicts (gpt-5-mini, n={len(prs)}): "
              f"raw={po*100:.1f}%  kappa={k:.3f}")
        print("    " + fmt_ag("orig-vs-rejudge", prs))

    # ---- self-consistency (repeat run, fixed order ao_first)
    if REP and A:
        idxA = index_by_order(A, "quality")
        idxR = index_by_order(REP, "quality")
        prs = [(idxA[(p, "ao_first")], idxR[(p, "ao_first")])
               for p, o in idxR if o == "ao_first" and (p, "ao_first") in idxA]
        po, k = kappa(prs)
        print(f"\n### Self-consistency, gpt-5-mini, identical prompt & order, n={len(prs)}: "
              f"raw={po*100:.1f}%  kappa={k:.3f}  (fail={fail_count(REP)})")
        print("    " + fmt_ag("self-consistency", prs))

    # ---- cross-family agreement on the shared subset
    if A and (B or C):
        idxA = index_by_order(A, "quality")
        for nm, rows in (("DeepSeek-V4-Flash", B), ("Kimi-K2.6", C)):
            if not rows:
                continue
            idxB = index_by_order(rows, "quality")
            print(f"\n### Cross-family agreement: gpt-5-mini vs {nm}")
            for order in ("ao_first", "var_first"):
                prs = [(idxA[k_], idxB[k_]) for k_ in idxB if k_[1] == order and k_ in idxA]
                print("   " + fmt_ag(f"order={order:9s}", prs))
            prs = [(idxA[k_], idxB[k_]) for k_ in idxB if k_ in idxA]
            print("   " + fmt_ag("pooled          ", prs))
            # order-balanced labels
            pidsB = {p for p, _ in idxB}
            prs = []
            for pid in pidsB:
                a, b = balanced_label(idxA, pid), balanced_label(idxB, pid)
                if a and b:
                    prs.append((a, b))
            print("   " + fmt_ag("order-balanced  ", prs))
            # binary collapse (variant-wins vs not)
            prs2 = [(("var" if a == "var" else "not"), ("var" if b == "var" else "not"))
                    for a, b in prs]
            print("   " + fmt_ag("binary var-wins ", prs2))
            # second judge's own win rate on the subset
            pb = position_bias(rows, "quality", nm)
            print(f"   {nm} own order-balanced win-rate on subset: {pb['balanced']:.1f}% "
                  f"(var2nd {pb['wr_variant_second']:.1f}, var1st {pb['wr_variant_first']:.1f})")
            sub = {p for p, _ in idxB}
            pbA = position_bias([r for r in A if r["pair_id"] in sub], "quality", "A|subset")
            print(f"   gpt-5-mini order-balanced win-rate on SAME subset: {pbA['balanced']:.1f}%")


if __name__ == "__main__":
    main()
