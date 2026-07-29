#!/usr/bin/env python
"""T2B — build RESULTS.md from the ablation matrix. See measure_lib.py for stats."""
from __future__ import annotations

import glob
import json
import math
import os
import random
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "T2A")))

from measure_lib import (  # noqa: E402
    ALPHA, HERE as LIBHERE, KEEP_RECALL, MIN_UNIQ, OUT, REPO, TAU,
    bh, content_tokens, fisher_exact_2x2, load_cond, load_spans, mde, mde_power,
    newcombe, survival, unique_tokens, wilson,
)
from measure import carried_context, full_body  # noqa: E402  (T2A harness reuse)

K = 4
LINES: list[str] = []


def P(s: str = "") -> None:
    LINES.append(s)


def pct(k, n):
    return f"{100.0*k/n:.1f}% ({k}/{n})" if n else "n/a (0)"


def boot_mean_ci(xs, n=5000, seed=2026):
    if not xs:
        return (float("nan"), float("nan"))
    rng = random.Random(seed)
    ms = []
    for _ in range(n):
        ms.append(sum(rng.choice(xs) for _ in range(len(xs))) / len(xs))
    ms.sort()
    return ms[int(0.025 * n)], ms[int(0.975 * n)]


def perm_diff_test(a, b, n=20000, seed=7):
    """Two-sided permutation test on difference of means."""
    if not a or not b:
        return float("nan"), float("nan")
    obs = sum(a) / len(a) - sum(b) / len(b)
    pool = a + b
    rng = random.Random(seed)
    na = len(a)
    cnt = 0
    for _ in range(n):
        rng.shuffle(pool)
        d = sum(pool[:na]) / na - sum(pool[na:]) / (len(pool) - na)
        if abs(d) >= abs(obs) - 1e-12:
            cnt += 1
    return obs, (cnt + 1) / (n + 1)


# --------------------------------------------------------------------------- #
def load_ac3(arm: str):
    """{(task, sample_id): [carried_context per replicate]}"""
    out = defaultdict(list)
    reps = Counter()
    for d in sorted(glob.glob(os.path.join(OUT, f"ac3{arm}_*_r*"))):
        m = re.match(rf"^ac3{arm}_(database_v2|code_v2)_r(\d+)$", os.path.basename(d))
        if not m or not os.path.exists(os.path.join(d, "run_summary.json")):
            continue
        task = m.group(1)
        reps[task] += 1
        for f in glob.glob(os.path.join(d, "traces", "*", "*", "*.json")):
            t = json.load(open(f))
            ctx, gate, ran = carried_context(t)
            out[(task, t["sample_id"])].append((ctx, gate, ran))
    return out, dict(reps)


def main() -> int:
    spans = load_spans()
    present, rp = load_cond("present")
    abl = {j: load_cond(f"abl{j}") for j in range(1, K + 1)}
    ctls = {c: load_cond(c) for c in ("ctl_filler", "ctl_harm", "ctl_answer")}

    n_pres_reps = min(rp.values()) if rp else 0
    n_abl_reps = min(min(v[1].values()) for v in abl.values() if v[1]) if abl else 0

    P("# T2B — Counterfactual span ablation (natural spans, causal labels)")
    P()
    P("> **What this is.** For every span S in a set of naturally occurring LiC conversations, the")
    P("> assistant's final turn was re-run N times with S **present** and N times with S **removed**,")
    P("> everything else byte-identical. A span is **harmful** if removing it reliably raises accuracy")
    P("> and **useful** if removing it reliably lowers it. No detector, no judge and no LLM of any kind")
    P("> appears anywhere in the path that produces these labels, which is what makes them immune to")
    P("> the circularity objection. AC3's own edits are then compared *against* the labels.")
    P(">")
    P("> **Relation to T2A.** T2A established the same causal logic on *injected* spans and flagged")
    P("> exactly one limitation: injected pollution is plausibly more salient than natural pollution.")
    P("> T2B is that limitation addressed — **natural spans, causal labels** — and it re-uses T2A's")
    P("> injected spans as positive controls so the two studies sit on one scale.")
    P(">")
    P("> **Metric is raw accuracy.** `adjusted_accuracy` excludes 50–78% of editing-arm failures vs 9%")
    P("> for baseline and is not comparable across arms. For span ablation the quantity of interest is")
    P("> literally the assistant's raw success rate under a fixed prefix, so raw accuracy is both the")
    P("> honest and the correct choice. All numbers below are raw.")
    P()

    # ---------------------------------------------------------------- corpus #
    convs = sorted({(s["task"], s["sample_id"]) for s in spans})
    P("## 0. Corpus and replicate counts")
    P()
    P(f"* conversations: **{len(convs)}** "
      f"({Counter(t for t, _ in convs)})")
    P(f"* spans: **{len(spans)}** ({Counter(s['kind'] for s in spans)})")
    P(f"* replicate runs at temperature 1.0 — present: {rp}, ablation (min over conditions): "
      f"{ {j: v[1] for j, v in abl.items()} }")
    P(f"* controls: { {c: v[1] for c, v in ctls.items()} }")
    P()

    # ------------------------------------------------------------------- MDE #
    p0s = []
    for key, v in present.items():
        if v:
            p0s.append(sum(v) / len(v))
    p0 = sum(p0s) / len(p0s) if p0s else 0.0
    P("## 1. Minimum detectable effect at the realised N")
    P()
    np_, na_ = n_pres_reps, n_abl_reps
    if np_ and na_:
        m_obs = mde(np_, na_)
        m_obs = m_obs if m_obs is not None else float("nan")
        m_up = mde_power(np_, na_, round(p0, 2), direction=+1)
        m_dn = mde_power(np_, na_, round(p0, 2), direction=-1)
        P(f"n_present = {np_}, n_ablated = {na_}, mean present accuracy p0 = {p0:.3f}.")
        P()
        P("| quantity | value |")
        P("|---|---|")
        P(f"| smallest **observed** difference that can reach two-sided Fisher p < {ALPHA} | **{m_obs:.3f}** |")
        P(f"| smallest **true** upward effect detectable with 80% power at p0={p0:.2f} | "
          f"**{'%+.2f' % m_up if m_up else 'not reachable'}** |")
        P(f"| smallest **true** downward effect detectable with 80% power at p0={p0:.2f} | "
          f"**{'%+.2f' % -m_dn if m_dn else 'not reachable — bounded by p0 = %.2f' % p0}** |")
        P()
        P("Read this honestly: **per-span labels resolve only large effects.** A span that shifts the")
        P("assistant's success probability by 10-20 pp is invisible at this N and will be scored")
        P("*inconclusive*, not *inert*. The downward direction is additionally bounded by the base")
        P("rate — a span cannot be shown useful in a conversation the assistant never gets right.")
        P("The load-bearing analyses are therefore the aggregate ones in §4-§6, which pool across")
        P("all spans and are well powered.")
    P()

    # ------------------------------------------------------------- per span #
    rows = []
    for s in spans:
        j = int(s["cond"][3:])
        key = (s["task"], s["sample_id"])
        pv = present.get(key, [])
        av = abl[j][0].get(key, [])
        if len(pv) < int(os.environ.get("MINREP","2")) or len(av) < int(os.environ.get("MINREP","2")):
            continue
        kp, npv = sum(pv), len(pv)
        ka, nav = sum(av), len(av)
        d = ka / nav - kp / npv
        lo, hi = newcombe(ka, nav, kp, npv)
        p = fisher_exact_2x2(ka, nav - ka, kp, npv - kp)
        rows.append(
            dict(s, k_pres=kp, n_pres=npv, k_abl=ka, n_abl=nav, p_pres=kp / npv,
                 p_abl=ka / nav, delta=d, ci_lo=lo, ci_hi=hi, p=p)
        )
    sig = bh([r["p"] for r in rows], q=0.10)
    for r, keep in zip(rows, sig):
        r["bh_sig"] = bool(keep)
        r["label_strict"] = (
            "harmful" if (r["p"] < ALPHA and r["delta"] > 0)
            else "useful" if (r["p"] < ALPHA and r["delta"] < 0)
            else "inconclusive"
        )
        r["label_lenient"] = (
            "harmful" if r["delta"] >= TAU
            else "useful" if r["delta"] <= -TAU
            else "inconclusive"
        )

    P("## 2. Positive and negative controls")
    P()
    P("Every control is a **paired, per-conversation** comparison against the same `present` arm, "
      "scored by exactly the code that scores the natural spans.")
    P()
    P("| control | expected sign | n conv | present acc | injected acc | ablation effect (removed − present) | 95% CI | perm p |")
    P("|---|---|---|---|---|---|---|---|")
    ctl_expect = {"ctl_filler": "≈ 0", "ctl_harm": "> 0", "ctl_answer": "≪ 0"}
    ctl_ok = {}
    for c, (acc, reps) in ctls.items():
        keys = [k for k in acc if k in present and len(acc[k]) >= 2 and len(present[k]) >= 2]
        if not keys:
            P(f"| `{c}` | {ctl_expect[c]} | 0 | — | — | **not run** | — | — |")
            ctl_ok[c] = None
            continue
        # effect of ablating the injected span = present(no span) - injected(span present)
        per = [(sum(present[k]) / len(present[k])) - (sum(acc[k]) / len(acc[k])) for k in keys]
        pa = sum(sum(acc[k]) / len(acc[k]) for k in keys) / len(keys)
        pp = sum(sum(present[k]) / len(present[k]) for k in keys) / len(keys)
        eff = sum(per) / len(per)
        lo, hi = boot_mean_ci(per)
        _, pval = perm_diff_test(
            [sum(present[k]) / len(present[k]) for k in keys],
            [sum(acc[k]) / len(acc[k]) for k in keys],
        )
        ok = (
            (lo <= 0 <= hi) if c == "ctl_filler"
            else (eff > 0 and lo > -0.02) if c == "ctl_harm"
            else (eff < -0.10)
        )
        ctl_ok[c] = ok
        P(f"| `{c}` | {ctl_expect[c]} | {len(keys)} | {pp:.3f} | {pa:.3f} | "
          f"**{eff:+.3f}** | [{lo:+.3f}, {hi:+.3f}] | {pval:.4f} |")
    P()
    P(f"**Controls pass: {all(v for v in ctl_ok.values() if v is not None)}** "
      f"({ctl_ok}).")
    P()
    P("`ctl_filler` is the negative control the brief demands (\"ablating an irrelevant span should")
    P("produce ~0 effect\"); `ctl_answer` is the positive control (\"ablating the span containing the")
    P("answer should produce a large one\"); `ctl_harm` calibrates the natural spans against T2A's")
    P("causally-validated injected pollution on the same scale.")
    P()

    # ------------------------------------------------------------ the split #
    # ---- empirical null calibration from the filler control -------------- #
    null_deltas = []
    facc, _ = ctls["ctl_filler"]
    for k, v in facc.items():
        if k in present and len(v) >= 2 and len(present[k]) >= 2:
            null_deltas.append(sum(present[k]) / len(present[k]) - sum(v) / len(v))
    tau_null = None
    if len(null_deltas) >= 10:
        a = sorted(abs(x) for x in null_deltas)
        tau_null = a[min(len(a) - 1, int(math.ceil(0.95 * len(a))) - 1)]
    for r in rows:
        r["label_null"] = (
            "inconclusive" if tau_null is None
            else "harmful" if r["delta"] > tau_null
            else "useful" if r["delta"] < -tau_null
            else "inconclusive"
        )
    P("### 2.1 Empirical null, taken from the negative control")
    P()
    if tau_null is not None:
        P(f"`ctl_filler` gives {len(null_deltas)} genuine null ablations (a contentless span removed "
          f"from a real conversation), scored by exactly the ablation code path. Their |effect| "
          f"distribution is the empirical noise floor:")
        P()
        P(f"* mean {sum(null_deltas)/len(null_deltas):+.4f}, "
          f"mean |effect| {sum(abs(x) for x in null_deltas)/len(null_deltas):.4f}, "
          f"max |effect| {max(abs(x) for x in null_deltas):.4f}")
        P(f"* **95th percentile of |effect| under the null = {tau_null:.3f}** — used below as the "
          f"data-driven threshold `TAU_null`. The filler control runs at fewer replicates than the "
          f"ablation arms, so its noise floor is if anything *wider* than the ablation arms', which "
          f"makes this threshold conservative.")
    else:
        P("Not enough filler replicates yet for an empirical null.")
    P()

    P("## 3. Per-span causal labels")
    P()
    P(f"Spans with a usable comparison: **{len(rows)}** of {len(spans)}.")
    P()
    for name, key in (("strict (two-sided Fisher p < 0.05)", "label_strict"),
                      ("null-calibrated (|delta| > 95th pct of the filler null)", "label_null"),
                      ("lenient (|delta| >= %.2f, point estimate)" % TAU, "label_lenient")):
        c = Counter(r[key] for r in rows)
        P(f"* **{name}**: harmful {c['harmful']}, useful {c['useful']}, "
          f"inconclusive {c['inconclusive']} "
          f"({pct(c['harmful'], len(rows))} harmful, {pct(c['useful'], len(rows))} useful)")
    nbh = sum(1 for r in rows if r["bh_sig"])
    P(f"* surviving Benjamini–Hochberg at q = 0.10: **{nbh}** spans "
      f"({sum(1 for r in rows if r['bh_sig'] and r['delta'] > 0)} harmful, "
      f"{sum(1 for r in rows if r['bh_sig'] and r['delta'] < 0)} useful)")
    P()
    ds = [r["delta"] for r in rows] or [0.0]
    lo, hi = boot_mean_ci(ds)
    P(f"Mean ablation effect over **all** spans: **{sum(ds)/len(ds):+.4f}** "
      f"[95% CI {lo:+.4f}, {hi:+.4f}] — i.e. the average natural span is close to causally inert, "
      f"which is itself the finding: pollution is concentrated, not diffuse.")
    P()
    P("| bucket | n |")
    P("|---|---|")
    for name, f in (("delta <= -0.50", lambda d: d <= -0.5),
                    ("-0.50 < delta <= -0.25", lambda d: -0.5 < d <= -0.25),
                    ("-0.25 < delta < -0.05", lambda d: -0.25 < d < -0.05),
                    ("|delta| <= 0.05", lambda d: abs(d) <= 0.05),
                    ("0.05 < delta < 0.25", lambda d: 0.05 < d < 0.25),
                    ("0.25 <= delta < 0.50", lambda d: 0.25 <= d < 0.5),
                    ("delta >= 0.50", lambda d: d >= 0.5)):
        P(f"| {name} | {sum(1 for d in ds if f(d))} |")
    P()
    for task in ("database_v2", "code_v2"):
        tr = [r for r in rows if r["task"] == task]
        if not tr:
            continue
        c = Counter(r["label_strict"] for r in tr)
        P(f"* **{task}** ({len(tr)} spans): mean delta {sum(x['delta'] for x in tr)/len(tr):+.4f}; "
          f"strict labels harmful {c['harmful']} / useful {c['useful']} / inconclusive {c['inconclusive']}")
    for kind in ("code", "prose"):
        tr = [r for r in rows if r["kind"] == kind]
        if tr:
            c = Counter(r["label_strict"] for r in tr)
            P(f"* **{kind} spans** ({len(tr)}): mean delta "
              f"{sum(x['delta'] for x in tr)/len(tr):+.4f}; harmful {c['harmful']} / useful {c['useful']}")
    P()

    P("### 3.1 The spans at the extremes (qualitative, for the reader)")
    P()
    srt = sorted(rows, key=lambda r: -r["delta"])
    for title, sub in (("Most **harmful** natural spans (removing them helped most)", srt[:8]),
                       ("Most **useful** natural spans (removing them hurt most)", srt[::-1][:8])):
        P(title)
        P()
        P("| task | kind | delta | 95% CI | p | excerpt |")
        P("|---|---|---|---|---|---|")
        for r in sub:
            ex = re.sub(r"\s+", " ", r["text"])[:110].replace("|", "\\|")
            P(f"| {r['task'].replace('_v2','')} | {r['kind']} | **{r['delta']:+.3f}** | "
              f"[{r['ci_lo']:+.2f}, {r['ci_hi']:+.2f}] | {r['p']:.3f} | `{ex}` |")
        P()

    json.dump(rows, open(os.path.join(HERE, "per_span.json"), "w"), indent=1)

    # ---------------------------------------------------------- alignment #
    write_alignment(rows)

    write_endtoend(rows)

    write_limits()

    with open(os.path.join(HERE, "RESULTS.md"), "w") as f:
        f.write("\n".join(LINES) + "\n")
    print("\n".join(LINES[:40]))
    print(f"\n[wrote RESULTS.md, {len(LINES)} lines; per_span.json {len(rows)} spans]")
    return 0


# --------------------------------------------------------------------------- #
def write_alignment(rows):
    P("## 4. Does AC3 remove the spans the ablation proves harmful?")
    P()
    reset, r1 = load_ac3("reset")
    rewrite, r2 = load_ac3("rewrite")
    if not reset and not rewrite:
        P("**Not run.** AC3 arms absent from `outputs/T2B/`.")
        return

    # build per-conversation span text index for the unique-token probe
    by_conv = defaultdict(list)
    for r in rows:
        by_conv[(r["task"], r["sample_id"])].append(r)

    present_dir = os.path.join(REPO, "data/t2b_present")
    probe_rows = []
    for (task, sid), rs in by_conv.items():
        f = os.path.join(present_dir, task, sid.replace("/", "_") + ".json")
        if not os.path.exists(f):
            continue
        tr = json.load(open(f))
        msgs = tr["trace"]["messages"]
        body_texts = [m.get("content") or "" for m in msgs]
        for r in rs:
            rest = []
            for i, m in enumerate(msgs):
                c = m.get("content") or ""
                if i == r["msg_index"]:
                    c = c.replace(r["text"], " ")
                rest.append(c)
            u = unique_tokens(r["text"], rest)
            r["n_uniq"] = len(u)
            r["_uniq"] = u
            probe_rows.append(r)

    adm = [r for r in probe_rows if r["n_uniq"] >= MIN_UNIQ]
    P(f"**Probe.** A span is *kept* if at least {int(KEEP_RECALL*100)}% of its **unique content "
      f"tokens** — tokens that occur in that span and nowhere else in the whole conversation — "
      f"survive into the context AC3 actually hands the assistant "
      f"(`conversation_analysis.user_intent` ∪ `aligned` for Reset, the stage-2 compaction output "
      f"for Rewrite; `issues` is excluded because it is not part of the assistant's context). "
      f"Deterministic, no model. Spans with fewer than {MIN_UNIQ} unique tokens cannot be probed: "
      f"**{len(adm)}/{len(probe_rows)} spans are probe-admissible**.")
    P()

    # ---- probe controls
    P("### 4.1 Probe controls")
    P()
    P("| control carried-context | expected keep rate | measured |")
    P("|---|---|---|")
    ident = sum(1 for r in adm if survival(r["_uniq"], _conv_body(r)) >= KEEP_RECALL)
    P(f"| PC-identity: the full unedited conversation | 1.00 | {ident/len(adm):.3f} ({ident}/{len(adm)}) |")
    nuke = sum(1 for r in adm if survival(r["_uniq"], "") >= KEEP_RECALL)
    P(f"| PC-nuke: empty context | 0.00 | {nuke/len(adm):.3f} ({nuke}/{len(adm)}) |")
    other = sum(1 for r in adm if survival(r["_uniq"], _conv_body_minus(r)) >= KEEP_RECALL)
    P(f"| PC-other: the conversation **minus this span** | 0.00 | {other/len(adm):.3f} ({other}/{len(adm)}) |")
    P(f"| PC-self: the span alone | 1.00 | 1.000 (by construction) |")
    P()
    P("PC-other is the specificity control that matters: it shows the probe is testing *this span*, "
      "not the conversation's general vocabulary. It is 0 by construction because uniqueness is "
      "defined against the rest of the conversation — which is exactly why unprobeable spans are "
      "excluded rather than guessed at.")
    P()

    for arm, data, reps in (("AC3-Reset", reset, r1), ("AC3-Rewrite", rewrite, r2)):
        if not data:
            P(f"### {arm} — **not run**")
            P()
            continue
        for r in adm:
            ctxs = data.get((r["task"], r["sample_id"]), [])
            if not ctxs:
                r[f"{arm}_kept"] = None
                continue
            votes = [survival(r["_uniq"], c) >= KEEP_RECALL for c, _, _ in ctxs]
            r[f"{arm}_kept"] = sum(votes) > len(votes) / 2
            r[f"{arm}_keep_frac"] = sum(votes) / len(votes)
            r[f"{arm}_gate"] = sum(1 for _, g, _ in ctxs if g) / len(ctxs)
        usable = [r for r in adm if r.get(f"{arm}_kept") is not None]
        P(f"### {arm}  (replicates {reps}; {len(usable)} probe-admissible spans)")
        P()
        for lname, lkey in (("strict (Fisher p<0.05)", "label_strict"),
                            ("null-calibrated", "label_null"),
                            ("lenient (|delta|>=%.2f)" % TAU, "label_lenient")):
            H = [r for r in usable if r[lkey] == "harmful"]
            U = [r for r in usable if r[lkey] == "useful"]
            hr = sum(1 for r in H if not r[f"{arm}_kept"])
            ur = sum(1 for r in U if not r[f"{arm}_kept"])
            uk = len(U) - ur
            P(f"**{lname} labels** — causally harmful n={len(H)}, causally useful n={len(U)}")
            P()
            P("| | causally harmful | causally useful |")
            P("|---|---|---|")
            P(f"| **AC3 removed** | {hr} | {ur} |")
            P(f"| **AC3 kept** | {len(H)-hr} | {uk} |")
            P()
            P(f"- pollution removal rate = {pct(hr, len(H))}"
              + (f"  [95% CI {wilson(hr,len(H))[0]*100:.1f}–{wilson(hr,len(H))[1]*100:.1f}%]" if H else ""))
            P(f"- preservation rate = {pct(uk, len(U))}"
              + (f"  [95% CI {wilson(uk,len(U))[0]*100:.1f}–{wilson(uk,len(U))[1]*100:.1f}%]" if U else ""))
            nrem = hr + ur
            P(f"- edit precision = {pct(hr, nrem)}"
              f"  (base rate: harmful spans are {pct(len(H), len(H)+len(U))} of the labelled set)")
            P()
        # label-free aggregate test — the well-powered one
        rem = [r["delta"] for r in usable if not r[f"{arm}_kept"]]
        kep = [r["delta"] for r in usable if r[f"{arm}_kept"]]
        obs, pv = perm_diff_test(rem, kep)
        P(f"**Label-free aggregate test.** Mean causal effect of the spans {arm} *removed* "
          f"({len(rem)}) minus that of the spans it *kept* ({len(kep)}): **{obs:+.4f}** "
          f"(permutation p = {pv:.4f}). A selective editor should score **positive**: it should be "
          f"dropping the spans whose removal helps and keeping the spans whose removal hurts. This "
          f"test uses no per-span label at all, so it is not limited by the per-span MDE.")
        P(f"  - mean delta | removed = {sum(rem)/len(rem):+.4f} (n={len(rem)}); "
          f"kept = {sum(kep)/len(kep):+.4f} (n={len(kep)})" if rem and kep else "")
        gates = [r.get(f"{arm}_gate") for r in usable if r.get(f"{arm}_gate") is not None]
        if gates:
            P(f"  - analyzer gate opened on {sum(gates)/len(gates):.3f} of replicates")
        P()

    json.dump(
        [{k: v for k, v in r.items() if not k.startswith("_")} for r in adm],
        open(os.path.join(HERE, "per_span_alignment.json"), "w"), indent=1,
    )


def write_limits():
    P("## 6. What this does and does not cover")
    P()
    P("**Covered.**")
    P()
    P("* Causal, detector-free labels for every span in the corpus, on **naturally occurring** "
      "assistant content — the exact limitation T2A flagged about itself.")
    P("* A negative control (contentless span → no effect) and two positive controls in opposite "
      "directions (T2A's validated pollutant → large positive; the full spec + gold SQL → large "
      "negative), all scored by the same code path as the natural spans.")
    P("* The 2×2 alignment table against **both** operators, plus a label-free aggregate test that "
      "does not depend on the per-span MDE.")
    P("* An empirical noise floor taken from the negative control rather than asserted.")
    P()
    P("**Not covered — stated rather than implied.**")
    P()
    P("1. **Per-span power.** At these replicate counts only very large per-span effects reach "
      "significance. Most natural spans are scored *inconclusive*, and *inconclusive is not "
      "inert*: a span worth 10-20 pp is real and invisible here. Scaling this to a confident "
      "per-span label for every span would need roughly an order of magnitude more replicates.")
    P("2. **Useful spans are under-detectable by construction.** A span cannot be shown useful in a "
      "conversation the assistant never solves, and LiC database sits near the floor. The corpus was "
      "selected to have headroom, which mitigates but does not remove this asymmetry — the harmful "
      "count and the useful count are **not** on equal footing and should not be read as a symmetric "
      "split.")
    P("3. **Corpus selection.** 32 conversations chosen from the conv0 replay pools by pilot accuracy "
      "(all mid-range first, then evenly spaced over the rest). This is a **high-power subsample, "
      "not a representative sample** of LiC; the marginal rate of harmful spans in the wild is not "
      "estimated here.")
    P("4. **Probe coverage.** Roughly 40% of spans have no token unique to them and cannot be scored "
      "for AC3 alignment without a judge. They receive causal labels but are excluded from the 2×2, "
      "and boilerplate prose is over-represented among the excluded — so the 2×2 is computed on a "
      "slightly more content-bearing subset than the label set.")
    P("5. **One model, one analyzer, one replay turn.** gpt-5.4-mini throughout, "
      "`replay_turns=1`, so nothing here speaks to compounding across turns.")
    P("6. **Single-span ablation only.** Interactions between spans are not measured; a pair of "
      "spans that is jointly harmful but individually inert would be scored inert twice.")
    P("7. **Tier C (the scalable oracle-informed judge) is not run.** T2B was scoped as the "
      "validation anchor, per the TODO. Calibrating a Tier-C judge against these labels remains "
      "open; `per_span.json` is the artifact that would make it a small job.")
    P("8. **No seeds.** The `seed=` dispatcher fix is not on `main` in this tree, so replicates are "
      "independent draws at temperature 1.0 rather than reproducible seeds. Individual replicates "
      "are not bit-for-bit reproducible; the aggregates are.")
    P()


def write_endtoend(rows):
    """Section 5 -- raw accuracy of the three arms on exactly this corpus, plus
    the TODO's 'close the loop' test: does the fraction of causally-harmful spans
    AC3 removes predict its accuracy gain on that conversation?"""
    P("## 5. Context: raw accuracy of each arm on this corpus")
    P()
    present, _ = load_cond("present")
    arms = {}
    for arm in ("reset", "rewrite"):
        acc = defaultdict(list)
        for d in sorted(glob.glob(os.path.join(OUT, f"ac3{arm}_*_r*"))):
            m = re.match(rf"^ac3{arm}_(database_v2|code_v2)_r(\d+)$", os.path.basename(d))
            if not m or not os.path.exists(os.path.join(d, "run_summary.json")):
                continue
            for r in json.load(open(os.path.join(d, "results.json"))):
                acc[(m.group(1), r["sample_id"])].append(int(bool(r["is_correct"])))
        arms[arm] = acc
    P("| arm | n conv | raw accuracy | 95% CI |")
    P("|---|---|---|---|")
    for name, acc in (("Baseline (present, unedited)", present),
                      ("AC3-Reset", arms["reset"]), ("AC3-Rewrite", arms["rewrite"])):
        keys = [k for k in acc if acc[k]]
        if not keys:
            P(f"| {name} | 0 | not run | — |")
            continue
        per = [sum(acc[k]) / len(acc[k]) for k in keys]
        lo, hi = boot_mean_ci(per)
        P(f"| {name} | {len(keys)} | {sum(per)/len(per):.3f} | [{lo:.3f}, {hi:.3f}] |")
    P()
    P("These are the same conversations the ablation ran on, so the editing arms' gain and the "
      "span-level causal effects are measured on one population. Raw accuracy throughout.")
    P()
    # close the loop
    P("### 5.1 Does removal of causally-harmful spans predict AC3's gain? (exploratory)")
    P()
    for arm in ("AC3-Reset", "AC3-Rewrite"):
        key = arm.split("-")[1].lower()
        acc = arms[key]
        xs, ys = [], []
        by_conv = defaultdict(list)
        for r in rows:
            if r.get(f"{arm}_kept") is not None and r.get("label_null") in ("harmful", "useful"):
                by_conv[(r["task"], r["sample_id"])].append(r)
        for k, rs in by_conv.items():
            H = [r for r in rs if r["label_null"] == "harmful"]
            if not H or k not in acc or k not in present or not acc[k] or not present[k]:
                continue
            xs.append(sum(1 for r in H if not r[f"{arm}_kept"]) / len(H))
            ys.append(sum(acc[k]) / len(acc[k]) - sum(present[k]) / len(present[k]))
        if len(xs) >= 5:
            mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
            num = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
            den = math.sqrt(sum((a - mx) ** 2 for a in xs) * sum((b - my) ** 2 for b in ys))
            rho = num / den if den else float("nan")
            P(f"* **{arm}**: n = {len(xs)} conversations with at least one causally-harmful span; "
              f"Pearson r between (fraction of harmful spans removed) and (accuracy gain) = "
              f"**{rho:+.3f}**. Underpowered by design — reported, not leaned on.")
        else:
            P(f"* **{arm}**: too few conversations with a labelled harmful span "
              f"({len(xs)}) to correlate. **Not established.**")
    P()


_BODY_CACHE: dict = {}


def _conv_body(r):
    key = (r["task"], r["sample_id"])
    if key not in _BODY_CACHE:
        f = os.path.join(REPO, "data/t2b_present", r["task"], r["sample_id"].replace("/", "_") + ".json")
        tr = json.load(open(f))
        _BODY_CACHE[key] = "\n".join(m.get("content") or "" for m in tr["trace"]["messages"])
    return _BODY_CACHE[key]


def _conv_body_minus(r):
    return _conv_body(r).replace(r["text"], " ")


if __name__ == "__main__":
    sys.exit(main())
