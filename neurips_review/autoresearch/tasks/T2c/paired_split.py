#!/usr/bin/env python
"""T2c step 3 — paired AC3-vs-baseline accuracy, split by leakage label.

Pairing follows neurips_review/experiments/paired_analysis.py in spirit (every
strategy is evaluated on the SAME (task, prefix) cells, so the comparison must
be paired) but at SAMPLE granularity: the pair key is
(task, conv_prefix, sample_id), which is exactly what the replay design
guarantees is matched across arms.

Statistic: McNemar exact (two-sided binomial on discordant pairs), plus a
Wilson interval on the paired accuracy difference via the discordant counts.
"""
import json
import math
import re
import sys
from pathlib import Path
from collections import defaultdict

PHASE1 = Path("/home/t-matthewho/ac3/recovered_t2c/ctx_editor/outputs/post_neurips_ac3_phase1")
HERE = Path(__file__).parent


def conv_of(name):
    m = re.search(r"_conv(\d)_", name)
    return int(m.group(1)) if m else -1


def task_of(name):
    m = re.search(r"_(math|code|database|actions)_v2_", name)
    return m.group(1) if m else "?"


def load_arm(prefix):
    """(task, conv, sample_id) -> is_correct for every run dir starting with prefix."""
    out = {}
    for rd in sorted(PHASE1.glob(prefix + "_*")):
        if not rd.is_dir() or not (rd / "results.json").exists():
            continue
        # guard against prefix collisions (no_gate vs no_gate_accumulate)
        rest = rd.name[len(prefix) + 1:]
        if not re.match(r"^(math|code|database|actions)_v2_conv\d_\d+$", rest):
            continue
        t, c = task_of(rd.name), conv_of(rd.name)
        for r in json.load(open(rd / "results.json")):
            out[(t, c, r["sample_id"])] = bool(r["is_correct"])
    return out


def binom_two_sided(k, n):
    """Exact two-sided binomial test, p=0.5."""
    if n == 0:
        return 1.0
    k = min(k, n - k)
    tail = sum(math.comb(n, i) for i in range(0, k + 1)) / (2 ** n)
    return min(1.0, 2 * tail)


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def report(name, keys, ac3, base):
    keys = [k for k in keys if k in ac3 and k in base]
    n = len(keys)
    if n == 0:
        print(f"{name:34s} n=0")
        return None
    a = sum(ac3[k] for k in keys)
    b = sum(base[k] for k in keys)
    win = sum(1 for k in keys if ac3[k] and not base[k])
    loss = sum(1 for k in keys if base[k] and not ac3[k])
    disc = win + loss
    p = binom_two_sided(min(win, loss), disc)
    # CI on the paired difference: difference = (win-loss)/n; use Wilson on
    # win/(win+loss) rescaled by disc/n.
    lo, hi = wilson(win, disc) if disc else (float("nan"), float("nan"))
    dlo, dhi = (2 * lo - 1) * disc / n, (2 * hi - 1) * disc / n
    print(
        f"{name:34s} n={n:4d}  base={b/n:6.1%}  AC3={a/n:6.1%}  "
        f"delta={100*(a-b)/n:+6.1f}pp  [{100*dlo:+6.1f},{100*dhi:+6.1f}]  "
        f"W/L={win}/{loss}  p={p:.4f}"
    )
    return dict(name=name, n=n, base=b / n, ac3=a / n, delta=(a - b) / n,
                ci=(dlo, dhi), win=win, loss=loss, p=p)


def main(label_file, label_key="label", arm="context_edit_v2_no_gate",
         tasks=None):
    labels = {}
    for l in open(label_file):
        r = json.loads(l)
        if r.get("strategy") != arm:
            continue
        if tasks and r["task"] not in tasks:
            continue
        labels[(r["task"], r["conv"], r["sample_id"])] = r[label_key]

    ac3 = load_arm(arm)
    base = load_arm("baseline")

    print(f"\narm = {arm};  label = {label_key};  labelled samples = {len(labels)}")
    print("-" * 110)
    groups = defaultdict(list)
    for k, v in labels.items():
        groups[v].append(k)
    rows = []
    rows.append(report("ALL (labelled)", list(labels), ac3, base))
    for g in sorted(groups):
        rows.append(report(f"  {g}", groups[g], ac3, base))
    return rows


if __name__ == "__main__":
    lf = sys.argv[1]
    key = sys.argv[2] if len(sys.argv) > 2 else "label"
    arms = sys.argv[3].split(",") if len(sys.argv) > 3 else ["context_edit_v2_no_gate"]
    tasks = sys.argv[4].split(",") if len(sys.argv) > 4 else None
    for a in arms:
        main(lf, key, a, tasks)
