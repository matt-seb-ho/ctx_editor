#!/usr/bin/env python
"""T2B — analysis of the counterfactual span-ablation matrix.

Produces, into RESULTS.md:
  0. positive/negative controls (harness + probe)
  1. minimum detectable effect at the realised replicate counts
  2. per-span causal labels with effect sizes and CIs
  3. the harmful/useful/inconclusive split
  4. the 2x2 alignment table against AC3-Reset and AC3-Rewrite
  5. an aggregate, label-free test: does AC3's remove/keep decision predict the
     measured causal effect?

No model is involved anywhere in producing a causal label. The only place a
model output is read at all is the *alignment* section, where AC3's own edited
context is probed for span survival with a deterministic unique-token test.
"""
from __future__ import annotations

import glob
import json
import math
import os
import random
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
OUT = os.path.join(REPO, "outputs/T2B")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "T2A"))

TAU = 0.25          # lenient point-estimate threshold for a span label
ALPHA = 0.05        # two-sided Fisher exact
MIN_UNIQ = 2        # unique tokens required for the alignment probe
KEEP_RECALL = 0.5   # fraction of unique tokens that must survive to count as KEPT

# --------------------------------------------------------------------------- #
# stats helpers (no scipy dependency assumptions -- all exact/closed form)
# --------------------------------------------------------------------------- #
def _lchoose(n, k):
    return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)


def fisher_exact_2x2(a, b, c, d):
    """Two-sided Fisher exact p for [[a,b],[c,d]] (point-probability method)."""
    n = a + b + c + d
    r1, c1 = a + b, a + c
    lo, hi = max(0, r1 + c1 - n), min(r1, c1)

    def lp(x):
        return (_lchoose(r1, x) + _lchoose(n - r1, c1 - x) - _lchoose(n, c1))

    obs = lp(a)
    tot = 0.0
    for x in range(lo, hi + 1):
        p = math.exp(lp(x))
        if lp(x) <= obs + 1e-9:
            tot += p
    return min(1.0, tot)


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def newcombe(k1, n1, k2, n2):
    """Newcombe hybrid-score CI for p1 - p2 (here p_abl - p_pres)."""
    l1, u1 = wilson(k1, n1)
    l2, u2 = wilson(k2, n2)
    p1, p2 = k1 / n1, k2 / n2
    lo = (p1 - p2) - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2)
    hi = (p1 - p2) + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)
    return max(-1.0, lo), min(1.0, hi)


def bh(pvals, q=0.10):
    idx = sorted(range(len(pvals)), key=lambda i: pvals[i])
    m = len(pvals)
    keep = [False] * m
    thresh = 0
    for rank, i in enumerate(idx, start=1):
        if pvals[i] <= q * rank / m:
            thresh = rank
    for rank, i in enumerate(idx, start=1):
        if rank <= thresh:
            keep[i] = True
    return keep


def mde(n_pres, n_abl, alpha=ALPHA):
    """Smallest |p_abl - p_pres| that can reach two-sided Fisher p < alpha."""
    best = None
    for kp in range(n_pres + 1):
        for ka in range(n_abl + 1):
            p = fisher_exact_2x2(ka, n_abl - ka, kp, n_pres - kp)
            if p < alpha:
                d = abs(ka / n_abl - kp / n_pres)
                if best is None or d < best:
                    best = d
    return best


# --------------------------------------------------------------------------- #
# data loading
# --------------------------------------------------------------------------- #
def load_cond(cond: str):
    """{(task, sample_id): [is_correct per replicate]} for one condition."""
    acc = defaultdict(list)
    reps = defaultdict(int)
    for d in sorted(glob.glob(os.path.join(OUT, f"{cond}_*_r*"))):
        name = os.path.basename(d)
        m = re.match(rf"^{re.escape(cond)}_(database_v2|code_v2)_r(\d+)$", name)
        if not m:
            continue
        task = m.group(1)
        f = os.path.join(d, "results.json")
        if not os.path.exists(f):
            continue
        # trap 5: metrics.json must agree with run_summary.json
        try:
            mt = json.load(open(os.path.join(d, "metrics.json")))
            rs = json.load(open(os.path.join(d, "run_summary.json")))
            a1 = mt.get("accuracy")
            a2 = (rs.get("metrics") or {}).get("accuracy", rs.get("accuracy"))
            if a1 is not None and a2 is not None and abs(a1 - a2) > 1e-9:
                print(f"  !! metrics/run_summary DISAGREE in {name}: {a1} vs {a2}")
        except FileNotFoundError:
            continue
        reps[task] += 1
        for r in json.load(open(f)):
            acc[(task, r["sample_id"])].append(int(bool(r["is_correct"])))
    return acc, dict(reps)


def load_spans():
    return [json.loads(l) for l in open(os.path.join(HERE, "spans.jsonl"))]


# --------------------------------------------------------------------------- #
# alignment probe: unique-token survival
# --------------------------------------------------------------------------- #
TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]{2,}|\d{3,}")
STOP = set(
    """the and for you your that this with from have has are was were will would can could
    query table column result rows row select where group order join inner outer left right
    need want use using based here there what which when please confirm sure like just also
    should does did not but all any one two more than then them they its it's into out about
    example following note make made get gets give given see look looks let lets now still
    first second third final only same other another each per some such very much many few
    return returns returned function code python sql data value values name names list
    if else while true false none null yes noo""".split()
)


def content_tokens(text: str) -> set[str]:
    return {t.lower() for t in TOKEN_RE.findall(text or "") if t.lower() not in STOP}


def unique_tokens(span_text: str, rest_texts: list[str]) -> set[str]:
    rest = set()
    for t in rest_texts:
        rest |= content_tokens(t)
    return content_tokens(span_text) - rest


def survival(uniq: set[str], carried: str) -> float:
    if not uniq:
        return float("nan")
    c = content_tokens(carried)
    return sum(1 for t in uniq if t in c) / len(uniq)


def mde_power(n_pres, n_abl, p0, power=0.80, alpha=ALPHA, direction=+1):
    """Smallest true |delta| detectable with `power` at the realised base rate p0.

    Exact: enumerates the joint binomial distribution of (k_pres, k_abl) and
    computes P(Fisher p < alpha) under the alternative p_abl = p0 + direction*delta.
    """
    from math import comb

    cache = {}

    def pv(ka, kp):
        key = (ka, kp)
        if key not in cache:
            cache[key] = fisher_exact_2x2(ka, n_abl - ka, kp, n_pres - kp)
        return cache[key]

    def binom(n, k, p):
        return comb(n, k) * (p ** k) * ((1 - p) ** (n - k))

    best = None
    for step in range(1, 101):
        d = step / 100
        p1 = p0 + direction * d
        if not (0.0 <= p1 <= 1.0):
            break
        pw = 0.0
        for kp in range(n_pres + 1):
            wp = binom(n_pres, kp, p0)
            if wp < 1e-12:
                continue
            for ka in range(n_abl + 1):
                if pv(ka, kp) < alpha:
                    pw += wp * binom(n_abl, ka, p1)
        if pw >= power:
            best = d
            break
    return best
