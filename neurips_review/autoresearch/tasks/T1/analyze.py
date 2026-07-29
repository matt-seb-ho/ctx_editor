#!/usr/bin/env python
"""T1 — paired arm-vs-baseline analysis + measured call/token budgets.

Pairing follows T2c's `paired_split.py`: every arm is run on the SAME sample
set, so the comparison is paired at (task, sample_id) granularity. Statistic is
McNemar exact (two-sided binomial on discordant pairs); the CI on the paired
difference is derived from a Wilson interval on win/(win+loss) rescaled by
disc/n. Those three functions are copied verbatim from
`neurips_review/autoresearch/tasks/T2c/paired_split.py` rather than rewritten.

Budgets come from `<run_dir>/call_meter.json` (see src/ctx_editor/utils/call_meter.py),
which is snapshotted before false-negative analysis.

Usage:  .venv/bin/python neurips_review/autoresearch/tasks/T1/analyze.py
"""
import json
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path("/home/t-matthewho/ac3/ctx_editor")
T1 = ROOT / "outputs" / "T1" / "main"
HERE = Path(__file__).parent

# tag -> (pretty arm name, run-dir suffix)
ARMS = [
    ("baseline", "Baseline (full context)"),
    ("summarize1", "Summarisation (1 call/turn)"),
    ("summarize2", "Summarisation (2 calls/turn, budget-matched)"),
    ("summarize_neutral", "Summarisation (neutral prompt, 1 call/turn)"),
    ("mtosc_w2", "MT-OSC (reimpl., w=2)"),
    ("mtosc_w4", "MT-OSC (reimpl., w=4, as published)"),
    ("reset", "AC3-Reset"),
    ("gated", "AC3-Gated-Reset"),
]
TASKS = [("database", "LiC-database"), ("code", "LiC-code")]


# --- statistics (verbatim from T2c/paired_split.py) -------------------------
def binom_two_sided(k, n):
    if n == 0:
        return 1.0
    k = min(k, n - k)
    tail = sum(math.comb(n, i) for i in range(0, k + 1)) / (2**n)
    return min(1.0, 2 * tail)


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def paired(arm, base):
    keys = [k for k in arm if k in base]
    n = len(keys)
    if n == 0:
        return None
    a = sum(arm[k] for k in keys)
    b = sum(base[k] for k in keys)
    win = sum(1 for k in keys if arm[k] and not base[k])
    loss = sum(1 for k in keys if base[k] and not arm[k])
    disc = win + loss
    p = binom_two_sided(min(win, loss), disc)
    lo, hi = wilson(win, disc) if disc else (float("nan"), float("nan"))
    dlo, dhi = (2 * lo - 1) * disc / n, (2 * hi - 1) * disc / n
    return dict(n=n, arm_correct=a, base_correct=b, arm_acc=a / n, base_acc=b / n,
                delta=(a - b) / n, ci=(dlo, dhi), win=win, loss=loss, p=p)


# --- loading ----------------------------------------------------------------
def rundir(task, tag):
    return T1 / f"{task[:4] if task=='code' else 'db'}_{tag}"


def dirname(task, tag):
    return T1 / (("db_" if task == "database" else "code_") + tag)


def load_results(d):
    """(sample_id) -> is_correct, plus a consistency cross-check."""
    res = json.load(open(d / "results.json"))
    m = json.load(open(d / "metrics.json"))
    rs = json.load(open(d / "run_summary.json"))
    correct = sum(1 for r in res if r["is_correct"])
    assert correct == m["correct"], f"{d}: results.json {correct} != metrics.json {m['correct']}"
    assert m["accuracy"] == rs["metrics"]["accuracy"], f"{d}: metrics/run_summary disagree"
    return ({r["sample_id"]: bool(r["is_correct"]) for r in res}, m, rs)


def load_meter(d):
    p = d / "call_meter.json"
    return json.load(open(p)) if p.exists() else None


def main():
    data = {}
    for task, _ in TASKS:
        for tag, _ in ARMS:
            d = dirname(task, tag)
            if not (d / "run_summary.json").exists():
                continue
            corr, m, rs = load_results(d)
            data[(task, tag)] = dict(dir=d, correct=corr, metrics=m, summary=rs,
                                     meter=load_meter(d))

    lines = []
    P = lines.append
    P("# T1 — Summarisation baseline vs AC3, LiC database + code")
    P("")
    P("gpt-5.4-mini (TRAPI), sharded user sim, full LiC pool "
      "(`data/sharded_instructions_600.json`): n=107 database, n=100 code. 1 run per cell.")
    P("Pairing: same samples in every arm; McNemar exact on discordant pairs.")
    P("Budgets measured from `call_meter.json` (pre-false-negative-analysis snapshot).")
    P("")

    # --- main table
    P("## Accuracy")
    P("")
    P("| Task | Arm | Acc (raw) | n correct | Δ vs baseline | 95% CI | W/L | McNemar p | Adj. acc | Artifact |")
    P("|---|---|---|---|---|---|---|---|---|---|")
    for task, tname in TASKS:
        base = data.get((task, "baseline"))
        for tag, aname in ARMS:
            cell = data.get((task, tag))
            if cell is None:
                continue
            m = cell["metrics"]
            # adjusted_accuracy is computed after save_metrics(), so it only
            # lands in run_summary.json — not metrics.json.
            adj = cell["summary"]["metrics"].get("adjusted_accuracy")
            adj_s = f"{adj:.1%}" if adj is not None else "—"
            if tag == "baseline" or base is None:
                P(f"| {tname} | {aname} | {m['accuracy']:.1%} | {m['correct']}/{m['total_samples']} "
                  f"| — | — | — | — | {adj_s} | `{cell['dir'].relative_to(ROOT)}` |")
            else:
                s = paired(cell["correct"], base["correct"])
                P(f"| {tname} | {aname} | {m['accuracy']:.1%} | {m['correct']}/{m['total_samples']} "
                  f"| {100*s['delta']:+.1f}pp | [{100*s['ci'][0]:+.1f}, {100*s['ci'][1]:+.1f}] "
                  f"| {s['win']}/{s['loss']} | {s['p']:.4f} | {adj_s} "
                  f"| `{cell['dir'].relative_to(ROOT)}` |")
    P("")

    # --- pooled
    P("## Pooled over both tasks (paired)")
    P("")
    P("| Arm | Acc | Δ vs baseline | 95% CI | W/L | McNemar p |")
    P("|---|---|---|---|---|---|")
    for tag, aname in ARMS:
        arm_all, base_all = {}, {}
        for task, _ in TASKS:
            c, b = data.get((task, tag)), data.get((task, "baseline"))
            if c is None or b is None:
                continue
            for k, v in c["correct"].items():
                arm_all[(task, k)] = v
            for k, v in b["correct"].items():
                base_all[(task, k)] = v
        if not arm_all:
            continue
        s = paired(arm_all, base_all)
        if tag == "baseline":
            P(f"| {aname} | {s['base_acc']:.1%} | — | — | — | — |")
        else:
            P(f"| {aname} | {s['arm_acc']:.1%} | {100*s['delta']:+.1f}pp "
              f"| [{100*s['ci'][0]:+.1f}, {100*s['ci'][1]:+.1f}] | {s['win']}/{s['loss']} | {s['p']:.4f} |")
    P("")

    # --- head-to-head: summarisation vs AC3
    P("## Head-to-head: summarisation vs AC3-Reset (paired)")
    P("")
    P("| Task | Comparison | Δ | W/L | McNemar p |")
    P("|---|---|---|---|---|")
    for task, tname in TASKS:
        for tag in ("summarize1", "summarize2", "summarize_neutral", "mtosc_w2", "mtosc_w4"):
            a, b = data.get((task, "reset")), data.get((task, tag))
            if a is None or b is None:
                continue
            s = paired(a["correct"], b["correct"])
            P(f"| {tname} | AC3-Reset − {tag} | {100*s['delta']:+.1f}pp | {s['win']}/{s['loss']} | {s['p']:.4f} |")
    P("")

    # --- budgets
    P("## Measured budget (per arm, whole run)")
    P("")
    P("| Task | Arm | LLM calls total | strategy calls | assistant | user sim | system judge "
      "| total tokens | strategy tokens | calls/conv | strategy calls/conv | avg turns |")
    P("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for task, tname in TASKS:
        for tag, aname in ARMS:
            cell = data.get((task, tag))
            if cell is None or cell["meter"] is None:
                continue
            mt = cell["meter"]
            t = mt["total"]
            g = lambda k, f="calls": mt["by_tag"].get(k, {}).get(f, 0)  # noqa: E731
            n = cell["metrics"]["total_samples"]
            P(f"| {tname} | {aname} | {t['calls']} | {g('strategy')} | {g('assistant')} "
              f"| {g('user')} | {g('system')} | {t['total_tokens']:,} "
              f"| {g('strategy','total_tokens'):,} | {t['calls']/n:.1f} | {g('strategy')/n:.1f} "
              f"| {cell['metrics'].get('average_turns', float('nan')):.1f} |")
    P("")

    out = HERE / "RESULTS.md"
    out.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\n[written] {out}")


if __name__ == "__main__":
    main()
