#!/usr/bin/env python
"""T9 — analyzer-model sensitivity: paired analysis.

Reuses T2c's statistical core (exact two-sided McNemar on discordant pairs +
Wilson interval on the discordant proportion rescaled to the accuracy
difference) and its pairing philosophy: the replay design guarantees every arm
sees the SAME (task, conv_prefix, sample_id) triples, so all comparisons are
paired at sample granularity.

Here conv is fixed at 0, so the pair key is (task, sample_id).

Every arm holds the assistant fixed (DeepSeek-V4-Flash) and varies only
model.ctx_editor.model.
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path("/home/t-matthewho/ac3/ctx_editor")

ARMS = [
    ("baseline", "— (no analyzer)"),
    ("ds_v4_flash", "DeepSeek-V4-Flash"),
    ("gpt54mini", "gpt-5.4-mini_2026-03-17"),
    ("kimi_k26", "Kimi-K2.6"),
    ("gpt4o_mini", "gpt-4o-mini"),
    ("llama70b", "Llama-3.3-70B-Instruct"),
]
TASKS = ["code", "database"]


def binom_two_sided(k, n):
    if n == 0:
        return 1.0
    k = min(k, n - k)
    tail = sum(math.comb(n, i) for i in range(0, k + 1)) / (2 ** n)
    return min(1.0, 2 * tail)


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def mcnemar(pairs):
    """pairs: list of (a_correct, b_correct). Returns dict."""
    n = len(pairs)
    b = sum(1 for a, c in pairs if c and not a)   # B wins
    c = sum(1 for a, cc in pairs if a and not cc)  # A wins
    d = b + c
    p = binom_two_sided(min(b, c), d)
    lo, hi = wilson(b, d) if d else (0, 0)
    # rescale discordant proportion to accuracy difference
    dlo = (2 * lo - 1) * d / n if n and d else 0.0
    dhi = (2 * hi - 1) * d / n if n and d else 0.0
    return dict(n=n, wins=b, losses=c, p=p, ci=(dlo * 100, dhi * 100))


def load(rep, task, arm):
    rd = ROOT / "outputs" / "T9" / rep / f"{task}_{arm}"
    rf = rd / "results.json"
    if not rf.exists():
        return None, None
    res = {r["sample_id"]: bool(r["is_correct"]) for r in json.load(open(rf))}
    summ = json.load(open(rd / "run_summary.json")) if (rd / "run_summary.json").exists() else {}
    return res, summ


def adj(summ):
    for k in ("adjusted_accuracy",):
        if k in summ and summ[k] is not None:
            return summ[k]
    m = summ.get("metrics", {})
    return m.get("adjusted_accuracy")


def main(rep="rep1"):
    data = {}
    summaries = {}
    for t in TASKS:
        for arm, _ in ARMS:
            r, s = load(rep, t, arm)
            if r is not None:
                data[(t, arm)] = r
                summaries[(t, arm)] = s

    print(f"\n## T9 rep={rep} — raw per-arm accuracies\n")
    hdr = "| task | arm | analyzer | n | correct | acc | adj acc |"
    print(hdr)
    print("|---|---|---|---|---|---|---|")
    for t in TASKS:
        for arm, label in ARMS:
            if (t, arm) not in data:
                continue
            r = data[(t, arm)]
            s = summaries[(t, arm)]
            a = adj(s)
            print(f"| {t} | {arm} | `{label}` | {len(r)} | {sum(r.values())} | "
                  f"{100*sum(r.values())/max(1,len(r)):.1f}% | "
                  f"{'—' if a is None else f'{100*a:.1f}%'} |")

    # paired vs baseline, per task and pooled
    print(f"\n## T9 rep={rep} — paired vs Baseline (same samples, assistant fixed)\n")
    print("| task | analyzer | n | Baseline | AC3-Reset | Δ (pp) | 95% CI | W/L | McNemar p |")
    print("|---|---|---|---|---|---|---|---|---|")
    for t in TASKS + ["POOLED"]:
        tlist = TASKS if t == "POOLED" else [t]
        base = {}
        for tt in tlist:
            for k, v in data.get((tt, "baseline"), {}).items():
                base[(tt, k)] = v
        if not base:
            continue
        for arm, label in ARMS[1:]:
            arm_d = {}
            for tt in tlist:
                for k, v in data.get((tt, arm), {}).items():
                    arm_d[(tt, k)] = v
            keys = sorted(set(base) & set(arm_d))
            if not keys:
                continue
            pairs = [(base[k], arm_d[k]) for k in keys]
            st = mcnemar(pairs)
            ba = 100 * sum(p[0] for p in pairs) / len(pairs)
            aa = 100 * sum(p[1] for p in pairs) / len(pairs)
            print(f"| {t} | `{label}` | {st['n']} | {ba:.1f}% | {aa:.1f}% | "
                  f"**{aa-ba:+.1f}** | [{st['ci'][0]:+.1f}, {st['ci'][1]:+.1f}] | "
                  f"{st['wins']}/{st['losses']} | {st['p']:.4f} |")

    # head-to-head vs the reference analyzer
    print(f"\n## T9 rep={rep} — paired vs reference analyzer (DeepSeek-V4-Flash)\n")
    print("| task | analyzer | n | ref acc | this acc | Δ (pp) | W/L | McNemar p |")
    print("|---|---|---|---|---|---|---|---|")
    for t in TASKS + ["POOLED"]:
        tlist = TASKS if t == "POOLED" else [t]
        ref = {}
        for tt in tlist:
            for k, v in data.get((tt, "ds_v4_flash"), {}).items():
                ref[(tt, k)] = v
        if not ref:
            continue
        for arm, label in ARMS[2:]:
            arm_d = {}
            for tt in tlist:
                for k, v in data.get((tt, arm), {}).items():
                    arm_d[(tt, k)] = v
            keys = sorted(set(ref) & set(arm_d))
            if not keys:
                continue
            pairs = [(ref[k], arm_d[k]) for k in keys]
            st = mcnemar(pairs)
            ra = 100 * sum(p[0] for p in pairs) / len(pairs)
            aa = 100 * sum(p[1] for p in pairs) / len(pairs)
            print(f"| {t} | `{label}` | {st['n']} | {ra:.1f}% | {aa:.1f}% | "
                  f"**{aa-ra:+.1f}** | {st['wins']}/{st['losses']} | {st['p']:.4f} |")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "rep1")
