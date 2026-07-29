#!/usr/bin/env python
"""T9 — cross-replicate summary: mean +/- std of raw accuracy and of the paired
delta vs Baseline, over sampling replicates (temperature 1.0; `seed=` is inert on
the LiC harness, so these are replicates, not seeds).

Also emits the pooled-over-replicates paired McNemar (every replicate contributes
its own matched (task, sample_id) pairs).
"""
import json
import math
import statistics as st
import sys
from pathlib import Path

ROOT = Path("/home/t-matthewho/ac3/ctx_editor/outputs/T9")

ARMS = [
    ("baseline", "— (no analyzer)", "—"),
    ("kimi_k26", "Kimi-K2.6", "Moonshot"),
    ("ds_v4_flash", "DeepSeek-V4-Flash", "DeepSeek"),
    ("gpt54mini", "gpt-5.4-mini_2026-03-17", "OpenAI"),
    ("llama70b", "Llama-3.3-70B-Instruct", "Meta"),
    ("gpt4o_mini", "gpt-4o-mini", "OpenAI"),
]
TASKS = ["code", "database"]


def binom_two_sided(k, n):
    if n == 0:
        return 1.0
    k = min(k, n - k)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(0, k + 1)) / (2 ** n))


def load(rep, task, arm):
    f = ROOT / rep / f"{task}_{arm}" / "results.json"
    if not f.exists():
        return None
    return {r["sample_id"]: bool(r["is_correct"]) for r in json.load(open(f))}


def main(reps):
    reps = [r for r in reps if any((ROOT / r).glob("*/results.json"))]
    print(f"replicates found: {reps}\n")

    # ---- per-arm accuracy, mean +/- std across replicates ----
    for scope in TASKS + ["POOLED"]:
        tl = TASKS if scope == "POOLED" else [scope]
        print(f"\n### {scope} — accuracy per replicate\n")
        print("| analyzer | family | " + " | ".join(reps) + " | mean | std | Δ vs Baseline (mean pp) |")
        print("|---|---|" + "---|" * (len(reps) + 3))
        base_means = None
        rows = []
        for arm, label, fam in ARMS:
            accs = []
            for rep in reps:
                tot = cor = 0
                for t in tl:
                    d = load(rep, t, arm)
                    if d is None:
                        tot = -1
                        break
                    tot += len(d)
                    cor += sum(d.values())
                accs.append(100 * cor / tot if tot > 0 else None)
            ok = [a for a in accs if a is not None]
            if not ok:
                continue
            m = st.mean(ok)
            s = st.stdev(ok) if len(ok) > 1 else 0.0
            rows.append((arm, label, fam, accs, m, s))
            if arm == "baseline":
                base_means = m
        for arm, label, fam, accs, m, s in rows:
            cells = " | ".join("—" if a is None else f"{a:.1f}" for a in accs)
            dv = "—" if arm == "baseline" or base_means is None else f"**{m-base_means:+.1f}**"
            print(f"| `{label}` | {fam} | {cells} | **{m:.1f}** | {s:.1f} | {dv} |")

    # ---- pooled-over-replicates paired McNemar vs baseline ----
    print("\n### Paired vs Baseline, pooled over replicates AND tasks "
          "(each replicate contributes its own matched pairs)\n")
    print("| analyzer | family | n pairs | Baseline | AC3-Reset | Δ (pp) | W/L | McNemar p |")
    print("|---|---|---|---|---|---|---|---|")
    for arm, label, fam in ARMS[1:]:
        pairs = []
        for rep in reps:
            for t in TASKS:
                b = load(rep, t, "baseline")
                a = load(rep, t, arm)
                if not b or not a:
                    continue
                for k in sorted(set(b) & set(a)):
                    pairs.append((b[k], a[k]))
        if not pairs:
            continue
        n = len(pairs)
        w = sum(1 for x, y in pairs if y and not x)
        l = sum(1 for x, y in pairs if x and not y)
        p = binom_two_sided(min(w, l), w + l)
        ba = 100 * sum(x for x, _ in pairs) / n
        aa = 100 * sum(y for _, y in pairs) / n
        print(f"| `{label}` | {fam} | {n} | {ba:.1f}% | {aa:.1f}% | **{aa-ba:+.1f}** | "
              f"{w}/{l} | {p:.4g} |")


if __name__ == "__main__":
    main(sys.argv[1:] or ["rep1", "rep2"])
