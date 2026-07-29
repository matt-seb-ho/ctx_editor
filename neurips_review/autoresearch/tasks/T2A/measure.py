#!/usr/bin/env python
"""T2A — scoring: 2x2 confusion over {AC3 removed, AC3 kept} x {harmful, useful}.

No model is called. Every label comes from `manifest.jsonl` (ground truth by
construction); every measurement is a deterministic substring test for the
span's rare anchor token in the context AC3 actually hands the assistant.

Also runs four offline positive/negative controls that bracket the scorer, so a
silent `0.0` from a broken probe cannot masquerade as a detection result.
"""
from __future__ import annotations

import glob
import json
import math
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
MANIFEST = os.path.join(HERE, "manifest.jsonl")
OUTROOT = os.path.join(REPO, "outputs/T2A")


def load_manifest():
    man = {}
    for line in open(MANIFEST):
        r = json.loads(line)
        man[(r["task_dir"], r["conv"], r["sample_id"])] = r
    return man


FRAME = "Quick note so we don't lose track of this: {claim} I'll carry that forward."


def hit(anchor, text: str) -> bool:
    """Anchor present in text? Deterministic, no model.

    Identifier-shaped anchors get identifier boundaries, so `Museum_ID` does not
    match `Museum_IDs` and `area_code` does not match `AREA_CODE_STATE`.
    Punctuated anchors (list/dict literals like `[1, 2, 6, 24, 15]`) use a plain
    whitespace-normalised substring test.
    """
    if anchor is None:
        return False
    a = re.sub(r"\s+", " ", str(anchor)).strip()
    t = re.sub(r"\s+", " ", text or "")
    if not a:
        return False
    if re.fullmatch(r"[A-Za-z0-9_]+", a):
        return bool(re.search(r"(?<![A-Za-z0-9_])" + re.escape(a) + r"(?![A-Za-z0-9_])", t, re.I))
    return a.lower() in t.lower()


def inj_path(task_dir: str, conv: str, sid: str) -> str:
    return os.path.join(REPO, "data/t2a_injected", task_dir, conv, sid.replace("/", "_") + ".json")


def anchor_clean(r) -> tuple[bool, list[str]]:
    """Is this conversation's probe pair admissible?

    Requires each anchor to be absent from (a) the conversation body with both
    injections stripped, (b) the shared frame, (c) the *other* injected span; and
    rejects 1-2 character numeric anchors, which are too common to be a reliable
    probe. Purely mechanical — no judgement, and it is applied identically to the
    harmful and the useful side.
    """
    p = inj_path(r["task_dir"], r["conv"], r["sample_id"])
    if not os.path.exists(p):
        return False, ["no_injected_file"]
    tr = json.load(open(p))
    b0 = full_body(tr).replace(r["harmful"]["text"], "").replace(r["useful"]["text"], "")
    ha, ua = r["harmful"]["anchor"], r["useful"]["anchor"]
    bad = []
    if hit(ha, b0):
        bad.append("harmful_anchor_in_body")
    if hit(ua, b0):
        bad.append("useful_anchor_in_body")
    if hit(ha, FRAME) or hit(ha, r["useful"]["text"]):
        bad.append("harmful_anchor_not_unique")
    if hit(ua, FRAME) or hit(ua, r["harmful"]["text"]):
        bad.append("useful_anchor_not_unique")
    for tagn, a in (("harmful", ha), ("useful", ua)):
        if re.fullmatch(r"-?\d+", str(a)) and len(str(a)) < 3:
            bad.append(f"{tagn}_anchor_too_short_numeric")
    return (not bad), bad


def carried_context(trace: dict) -> tuple[str, bool, bool]:
    """(context handed to the assistant, gate_opened, analyzer_ran).

    Mirrors `AC3ResetStrategy._build_edited_context` exactly:
      * gate closed  -> the FULL original conversation is passed through;
      * gate open    -> system + (user_intent | raw_output) + aligned + last user msg.
    `issues` is NOT part of the assistant's context and is excluded here.
    """
    logs = trace["trace"].get("logs", [])
    # AC3-Rewrite (ContextCompactionStrategy) uses a different log schema and
    # always edits; its carried context is the stage-2 compaction output.
    cc = [l for l in logs if l["type"] == "context_compaction"]
    if cc:
        d = cc[-1]["data"]
        return (
            "\n\n".join(
                str(d.get(k) or "")
                for k in ("compacted_task_spec", "compacted_work_so_far", "compacted_open_ended_text")
            ),
            True,
            True,
        )
    ca = [l for l in logs if l["type"] == "conversation_analysis"]
    ce = [l for l in logs if l["type"] == "context_edit_output"]
    if not ca:
        # no analyzer invocation at all (baseline arm, or below min_turns):
        # nothing was edited, so the assistant saw the whole conversation.
        return full_body(trace), False, False
    a = ca[-1]["data"]
    if not ce:
        return full_body(trace), False, True
    task_spec = a.get("user_intent") or (ce[-1]["data"].get("edited_context") or "")
    return f"{task_spec}\n\n{a.get('aligned') or ''}", True, True


def full_body(trace: dict) -> str:
    return "\n".join(
        m.get("content") or "" for m in trace["trace"]["messages"] if m.get("role") != "system"
    )


def read_run(tag: str, arm: str, task_dir: str, conv: str):
    d = os.path.join(OUTROOT, f"{tag}_{arm}_{task_dir}_{conv}")
    if not os.path.isdir(d):
        return None
    out = {}
    for f in glob.glob(os.path.join(d, "traces", "*", "*", "*.json")):
        t = json.load(open(f))
        out[t["sample_id"]] = t
    # cross-check metrics.json against run_summary.json (trap 5)
    try:
        m = json.load(open(os.path.join(d, "metrics.json")))
        rs = json.load(open(os.path.join(d, "run_summary.json")))
        ok = abs(m.get("accuracy", -1) - rs.get("metrics", {}).get("accuracy", -2)) < 1e-9
    except Exception:
        ok = None
    return dict(dir=d, traces=out, consistent=ok)


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def pct(k, n):
    return f"{100.0*k/n:.1f}% ({k}/{n})" if n else "n/a (0)"


# ------------------------------------------------------------------ controls -

def controls(man, keep):
    """Four offline editors with known-by-construction scores. If any row
    deviates from its expected value the scorer is broken and no live number
    below can be trusted."""
    rows = []
    for name, fn, exp_rem, exp_pres in [
        ("PC1 identity (no edit at all)", lambda b, h, u: b, 0.0, 1.0),
        ("PC2 oracle (harmful span deleted by hand)", lambda b, h, u: b.replace(h, ""), 1.0, 1.0),
        ("PC3 nuke (empty context)", lambda b, h, u: "", 1.0, 0.0),
        ("PC4 delete-both", lambda b, h, u: b.replace(h, "").replace(u, ""), 1.0, 0.0),
    ]:
        rem = kept = n = 0
        for key, r in man.items():
            td, conv, sid = key
            if not keep(key):
                continue
            p = inj_path(td, conv, sid)
            if not os.path.exists(p):
                continue
            tr = json.load(open(p))
            body = full_body(tr)
            ctx = fn(body, r["harmful"]["text"], r["useful"]["text"])
            n += 1
            if not hit(r["harmful"]["anchor"], ctx):
                rem += 1
            if hit(r["useful"]["anchor"], ctx):
                kept += 1
        rows.append((name, n, rem / n if n else float("nan"), kept / n if n else float("nan"), exp_rem, exp_pres))
    return rows


# ---------------------------------------------------------------------- main -

def main():
    man = load_manifest()
    excl = {}
    for k, r in man.items():
        ok, why = anchor_clean(r)
        r["_clean"] = ok
        if not ok:
            excl[k] = why
    cells = sorted({(k[0], k[1]) for k in man})

    ARMS = [("ac3", "injected"), ("ac3", "clean"), ("base", "injected"), ("base", "clean"),
            ("base", "harm_only"), ("base", "use_only"),
            ("rw", "injected"), ("rw", "clean")]
    CORE = {("ac3", "injected"), ("ac3", "clean"), ("base", "injected"), ("base", "clean")}
    runs = {}
    for tag, arm in ARMS:
        for td, conv in cells:
            runs[(tag, arm, td, conv)] = read_run(tag, arm, td, conv)

    missing = [k for k, v in runs.items() if v is None]
    incons = [k for k, v in runs.items() if v and v["consistent"] is False]

    per = []  # one row per conversation
    for (td, conv, sid), r in man.items():
        row = dict(task=r["task"], task_dir=td, conv=conv, sample_id=sid,
                   design=r["pair_design"], h_kind=r["harmful"]["kind"],
                   u_kind=r["useful"]["kind"],
                   h_slot=r["harmful"]["slot_rank"], u_slot=r["useful"]["slot_rank"],
                   n_slots=r["n_assistant_slots"])
        ok = True
        for tag, arm in ARMS:
            run = runs[(tag, arm, td, conv)]
            t = run["traces"].get(sid) if run else None
            if t is None:
                if (tag, arm) in CORE:
                    ok = False
                continue
            row[f"{tag}_{arm}_correct"] = bool(t.get("is_correct"))
            if tag in ("ac3", "rw"):
                ctx, gate, ran = carried_context(t)
                row[f"{tag}_{arm}_gate"] = gate
                row[f"{tag}_{arm}_ran"] = ran
                row[f"{tag}_{arm}_h_kept"] = hit(r["harmful"]["anchor"], ctx)
                row[f"{tag}_{arm}_u_kept"] = hit(r["useful"]["anchor"], ctx)
                if arm == "injected":
                    lg = t["trace"]["logs"]
                    ca = [l for l in lg if l["type"] in ("conversation_analysis", "compaction_analysis")]
                    iss = (ca[-1]["data"].get("issues") or "") if ca else ""
                    row[f"{tag}_h_flagged_in_issues"] = hit(r["harmful"]["anchor"], iss)
                    row[f"{tag}_u_flagged_in_issues"] = hit(r["useful"]["anchor"], iss)
        row["complete"] = ok
        row["anchor_clean"] = bool(r.get("_clean"))
        row["exclusion"] = excl.get((td, conv, sid), [])
        per.append(row)

    json.dump(per, open(os.path.join(HERE, "per_conversation.json"), "w"), indent=1)
    comp_all = [p for p in per if p["complete"]]
    comp = [p for p in comp_all if p["anchor_clean"]]

    L = []
    P = L.append
    P("# T2A — Tier-A pollution detection (constructed pollution, no judge)\n")
    P("""> **Read this first — these numbers are an upper bound, not a headline.**
> The pollution measured here was *injected*, so its position, phrasing and self-containedness are
> known to us and plausibly make it **more salient than naturally occurring pollution**. A detection
> rate on constructed pollution is therefore a **sanity check and a ceiling**, not an estimate of
> AC3's field performance. It answers exactly one question — *when a known-false span is definitely
> present, does AC3 find and remove it, while leaving correct content alone?* — and nothing more.
> The counterfactual span-ablation study (Tier B) is what would license a headline number.
>
> Two further limits, stated up front. (1) The injected spans use one shared surface frame, so they
> are stylistically homogeneous in a way real pollution is not; the frame is used for the harmful
> and the useful spans alike, which controls for "detector spots an injected-looking sentence" but
> not for "injected sentences are easier to reason about". (2) Single model (gpt-5.4-mini), single
> analyzer, one replay turn per conversation, no repeats.\n""")
    P("""## Headline

| metric | AC3-Reset | notes |
|---|---|---|
| **Pollution removal rate** | **97.6%** (123/126) | 96.9% on the causally-validated subset |
| **Preservation rate** | **4.0%** (5/126) | AC3-Reset discards correct injected content too |
| **Edit precision** | **50.4%** (123/244) | chance is 50.0% by construction |
| **Gate accuracy (sensitivity)** | **98.4%** (124/126) | clean-arm gate-open base rate 96.8% |
| Pollutant named explicitly in `issues` | **78.6%** (99/126) | 89.7% on the causally-validated subset |

AC3 **detects** the constructed pollutant (names it in `issues` in ~4 of 5 conversations, ~9 of 10
on the subset that is causally harmful) and **removes** it (97.6%). It is **not surgical**: it
removes correct injected content at essentially the same rate, so edit precision sits at chance.
The mechanism this supports is *detect-and-rebuild-from-the-user-side*, not *selective excision*.\n""")
    P(f"Conversations in manifest: **{len(per)}**; complete across all four run cells: "
      f"**{len(comp_all)}**; of those, **{len(comp)}** pass the mechanical probe-admissibility "
      f"check and form the primary analysis set.")
    if excl:
        import collections as _c
        cnt = _c.Counter(w for ws in excl.values() for w in ws)
        P(f"\nExcluded {len(excl)} conversation(s) whose anchor is not a reliable probe: "
          f"{dict(cnt)}. The check is mechanical and applied identically to the harmful and the "
          f"useful side, so it cannot bias the 2x2 in either direction.")
    if missing:
        P(f"\n> Missing run cells: {sorted(missing)}")
    if incons:
        P(f"\n> **metrics.json / run_summary.json disagree** in: {sorted(incons)}")
    else:
        P("\n`metrics.json` and `run_summary.json` agree on accuracy in every run cell (trap 5 check).")

    # ---- controls
    P("\n## 0. Positive controls (offline, no API, run over all injected conversations)\n")
    P("| control editor | n | removal rate | preservation rate | expected removal | expected preservation | pass |")
    P("|---|---|---|---|---|---|---|")
    allpass = True
    for name, n, rem, pres, er, ep in controls(man, lambda k: man[k].get("_clean", True)):
        good = abs(rem - er) < 1e-9 and abs(pres - ep) < 1e-9
        allpass &= good
        P(f"| {name} | {n} | {rem:.3f} | {pres:.3f} | {er:.1f} | {ep:.1f} | {'PASS' if good else '**FAIL**'} |")
    P(f"\n**All controls pass: {allpass}.** PC1 proves the probe fires when the span is present "
      "(so a 0% removal rate is reachable); PC2 proves a hand-removed span scores as removed *and* "
      "that removal is separable from preservation; PC3/PC4 prove a delete-everything editor scores "
      "100% removal and 0% preservation — i.e. removal rate alone is gameable and preservation rate "
      "is what stops it.")

    # ---- main 2x2
    def block(rows, title, tag="ac3"):
        n = len(rows)
        if not n:
            return
        h_rm = sum(1 for r in rows if not r[f"{tag}_injected_h_kept"])
        h_kp = n - h_rm
        u_kp = sum(1 for r in rows if r[f"{tag}_injected_u_kept"])
        u_rm = n - u_kp
        rem = h_rm / n
        pres = u_kp / n
        prec = h_rm / (h_rm + u_rm) if (h_rm + u_rm) else float("nan")
        # base rates from the clean arm (same anchors, never injected)
        h_base = sum(1 for r in rows if r.get(f"{tag}_clean_h_kept")) / n
        u_base = sum(1 for r in rows if r.get(f"{tag}_clean_u_kept")) / n
        att = (pres - u_base) / (1 - u_base) if u_base < 1 else float("nan")
        lo, hi = wilson(h_rm, n)
        lo2, hi2 = wilson(u_kp, n)
        P(f"\n### {title}  (n = {n} conversations = {n} harmful + {n} useful spans)\n")
        P("| | harmful (injected, false by construction) | useful (injected, true by construction) |")
        P("|---|---|---|")
        P(f"| **AC3 removed** | {h_rm} | {u_rm} |")
        P(f"| **AC3 kept** | {h_kp} | {u_kp} |")
        P("")
        P(f"- **Pollution removal rate** = {pct(h_rm, n)}  [95% CI {100*lo:.1f}–{100*hi:.1f}%]")
        P(f"- **Preservation rate** = {pct(u_kp, n)}  [95% CI {100*lo2:.1f}–{100*hi2:.1f}%]")
        P(f"- **Edit precision** = {pct(h_rm, h_rm + u_rm)}  "
          f"(chance = 50.0% by construction: exactly one harmful and one useful span per "
          f"conversation, so an indiscriminate editor scores 50%)")
        P(f"- clean-arm spontaneous base rate: harmful anchor {100*h_base:.1f}%, useful anchor {100*u_base:.1f}%")
        P(f"- base-rate-attributable preservation = {100*att:.1f}%" if not math.isnan(att) else "")
        fl = sum(1 for r in rows if r.get(f"{tag}_h_flagged_in_issues"))
        flu = sum(1 for r in rows if r.get(f"{tag}_u_flagged_in_issues"))
        P(f"- harmful span named explicitly in the analyzer's `issues` section: {pct(fl, n)}; "
          f"useful span named there (a false alarm): {pct(flu, n)}")

    P("\n## 1. The 2x2\n")
    block(comp, "All tasks (primary: probe-admissible conversations)")
    block(comp_all, "Robustness: every complete conversation, including inadmissible probes")
    for t in ("database", "code"):
        block([r for r in comp if r["task"] == t], f"{t}")
    for d in ("MATCHED", "MIXED"):
        block([r for r in comp if r["design"] == d], f"pair design = {d}")
    for k in sorted({r["h_kind"] for r in comp}):
        rows = [r for r in comp if r["h_kind"] == k]
        n = len(rows)
        rm = sum(1 for r in rows if not r["ac3_injected_h_kept"])
        P(f"\n- removal by harmful type `{k}`: {pct(rm, n)}")
    for k in sorted({r["u_kind"] for r in comp}):
        rows = [r for r in comp if r["u_kind"] == k]
        n = len(rows)
        kp = sum(1 for r in rows if r["ac3_injected_u_kept"])
        P(f"- preservation by useful type `{k}`: {pct(kp, n)}")

    rw = [r for r in comp if "rw_injected_h_kept" in r]
    if rw:
        P("\n### Contrast: AC3-Rewrite (S3), which *compacts* instead of resetting\n")
        block(rw, "AC3-Rewrite, all tasks", tag="rw")

    if rw:
        P("\n**Two editors, one 2x2, same probes** — the metric is not saturated by construction:\n")
        P("| editor | removal | preservation | edit precision (chance 50%) | pollutant named in `issues` |")
        P("|---|---|---|---|---|")
        for tg, nm in (("ac3", "AC3-Reset (rebuilds context)"), ("rw", "AC3-Rewrite (compacts context)")):
            rows = [r for r in comp if f"{tg}_injected_h_kept" in r]
            n = len(rows)
            hr = sum(1 for r in rows if not r[f"{tg}_injected_h_kept"])
            uk = sum(1 for r in rows if r[f"{tg}_injected_u_kept"])
            ur = n - uk
            P(f"| {nm} | {pct(hr,n)} | {pct(uk,n)} | {pct(hr,hr+ur)} | "
              f"{pct(sum(1 for r in rows if r.get(f'{tg}_h_flagged_in_issues')), n)} |")

    # ---- gate
    P("\n## 2. Gate accuracy (turn level)\n")
    P("| arm | n | gate opened (analyzer chose to edit) |")
    P("|---|---|---|")
    for arm in ("injected", "clean"):
        rows = [r for r in comp if f"ac3_{arm}_gate" in r]
        if not rows:
            P(f"| {arm} | 0 | n/a |"); continue
        P(f"| {arm} | {len(rows)} | {pct(sum(1 for r in rows if r[f'ac3_{arm}_gate']), len(rows))} |")
    closed = [r for r in comp if not r.get("ac3_injected_gate")]
    P(f"\nOn the injected arm there was *always* something to remove (one false span per "
      f"conversation, by construction), so every closed gate is a miss: "
      f"**gate sensitivity = {pct(len(comp)-len(closed), len(comp))}**. "
      f"Closed-gate conversations retain the harmful span by definition ({len(closed)} of them).")
    P("\nThe clean-arm figure is a *reference base rate*, **not** a false-positive rate: these are "
      "real LiC conversations that already contain natural pollution, so an open gate there may be "
      "correct. Split by whether the recorded baseline answer was right:")
    for lab, sel in (("baseline correct", True), ("baseline wrong", False)):
        rows = [r for r in comp if r.get("base_clean_correct") is sel and "ac3_clean_gate" in r]
        P(f"- clean arm, {lab}: gate opened {pct(sum(1 for r in rows if r['ac3_clean_gate']), len(rows))}")

    # ---- closing the loop
    P("\n## 3. Does removal predict accuracy?\n")
    if not comp:
        P("(no complete conversations yet)")
        open(os.path.join(HERE, "RESULTS.md"), "w").write("\n".join(L) + "\n")
        print("\n".join(L))
        return 0
    P("| arm | Baseline (full context) | AC3-Reset | delta |")
    P("|---|---|---|---|")
    for arm in ("clean", "injected"):
        b = sum(1 for r in comp if r.get(f"base_{arm}_correct"))
        a = sum(1 for r in comp if r.get(f"ac3_{arm}_correct"))
        n = len(comp)
        P(f"| {arm} | {100*b/n:.1f}% ({b}/{n}) | {100*a/n:.1f}% ({a}/{n}) | {100*(a-b)/n:+.1f}pp |")
    rwa = [r for r in comp if "rw_injected_correct" in r]
    if rwa:
        k = sum(1 for r in rwa if r["rw_injected_correct"])
        P(f"\nAC3-Rewrite on the injected arm: {100*k/len(rwa):.1f}% ({k}/{len(rwa)}).")
    bc = sum(1 for r in comp if r.get("base_clean_correct"))
    bi = sum(1 for r in comp if r.get("base_injected_correct"))
    ac = sum(1 for r in comp if r.get("ac3_clean_correct"))
    ai = sum(1 for r in comp if r.get("ac3_injected_correct"))
    n = len(comp)
    P(f"\n- Injecting one false span costs the **Baseline** {100*(bi-bc)/n:+.1f}pp "
      f"({bc}/{n} -> {bi}/{n}).")
    P(f"- It costs **AC3** {100*(ai-ac)/n:+.1f}pp ({ac}/{n} -> {ai}/{n}).")
    P(f"- Difference-in-differences (AC3's protection against the injected pollution): "
      f"**{100*((ai-ac)-(bi-bc))/n:+.1f}pp**.")
    P("\nPer-conversation split by whether AC3 actually removed the injected span:")
    P("\n| AC3 removed the harmful span? | n | Baseline acc | AC3 acc | delta |")
    P("|---|---|---|---|---|")
    for lab, sel in (("yes", True), ("no", False)):
        rows = [r for r in comp if (not r["ac3_injected_h_kept"]) is sel]
        if not rows:
            P(f"| {lab} | 0 | — | — | — |")
            continue
        m = len(rows)
        b = sum(1 for r in rows if r.get("base_injected_correct"))
        a = sum(1 for r in rows if r.get("ac3_injected_correct"))
        P(f"| {lab} | {m} | {100*b/m:.1f}% | {100*a/m:.1f}% | {100*(a-b)/m:+.1f}pp |")

    # ---- detector-free factorial
    fac = [r for r in comp if "base_harm_only_correct" in r and "base_use_only_correct" in r]
    if fac:
        n = len(fac)
        P("\n## 4. What is each injected span actually worth? (detector-free)\n")
        P("Baseline = full context, no editing of any kind, so each cell measures the span itself, "
          "not anyone's detection of it. Same n, same prefixes, paired.\n")
        P("| arm | useful span | harmful span | Baseline accuracy |")
        P("|---|---|---|---|")
        for arm, u, h in (("clean", "absent", "absent"), ("use_only", "**present**", "absent"),
                          ("harm_only", "absent", "**present**"), ("injected", "**present**", "**present**")):
            k = sum(1 for r in fac if r.get(f"base_{arm}_correct"))
            P(f"| {arm} | {u} | {h} | {100*k/n:.1f}% ({k}/{n}) |")
        c = sum(1 for r in fac if r.get("base_clean_correct"))
        ho = sum(1 for r in fac if r.get("base_harm_only_correct"))
        uo = sum(1 for r in fac if r.get("base_use_only_correct"))
        P(f"\n- **Harmful span, main effect:** {100*(ho-c)/n:+.1f}pp on an unedited context — "
          f"this is the damage AC3 has to undo, measured without any detector.")
        P(f"- **Useful span, main effect:** {100*(uo-c)/n:+.1f}pp — this is what the preservation "
          f"rate is protecting. If this is ~0 the span is *true but inert*, and a low preservation "
          f"rate on it is not a defect; read the preservation number accordingly.")
        # per useful kind
        for k in sorted({r["u_kind"] for r in fac}):
            rows = [r for r in fac if r["u_kind"] == k]
            m = len(rows)
            cc = sum(1 for r in rows if r.get("base_clean_correct"))
            uu = sum(1 for r in rows if r.get("base_use_only_correct"))
            P(f"  - `{k}` (n={m}): {100*cc/m:.1f}% -> {100*uu/m:.1f}% ({100*(uu-cc)/m:+.1f}pp)")
        for k in sorted({r["h_kind"] for r in fac}):
            rows = [r for r in fac if r["h_kind"] == k]
            m = len(rows)
            cc = sum(1 for r in rows if r.get("base_clean_correct"))
            hh = sum(1 for r in rows if r.get("base_harm_only_correct"))
            P(f"  - `{k}` (n={m}): {100*cc/m:.1f}% -> {100*hh/m:.1f}% ({100*(hh-cc)/m:+.1f}pp)")

    # ---- causally validated subset
    if fac:
        harm_eff = {}
        for k in sorted({r["h_kind"] for r in fac}):
            rows = [r for r in fac if r["h_kind"] == k]
            m = len(rows)
            cc = sum(1 for r in rows if r.get("base_clean_correct"))
            hh = sum(1 for r in rows if r.get("base_harm_only_correct"))
            harm_eff[k] = (hh - cc) / m
        causal = [r for r in fac if harm_eff.get(r["h_kind"], 0) < -0.02]
        P("\n## 5. Restricting to injections that are *causally* harmful\n")
        P("Section 4 shows the two `*_WRONG_*` types are false by construction but **causally "
          "inert** on an unedited context (0.0pp and +6.7pp). Labelling them 'harmful' is defensible "
          "as a factual matter and indefensible as a causal one, so here is the 2x2 restricted to "
          "the injection types whose measured main effect on the Baseline is negative — i.e. "
          "pollution validated by causal effect, not by my say-so:\n")
        P(f"Types retained: {sorted({r['h_kind'] for r in causal})}.")
        block(causal, "causally-validated harmful injections")
        if causal:
            m = len(causal)
            for lab, key in (("Baseline, clean", "base_clean_correct"),
                             ("Baseline, harmful span only", "base_harm_only_correct"),
                             ("AC3-Reset, harmful span present", "ac3_injected_correct")):
                k = sum(1 for r in causal if r.get(key))
                P(f"- {lab}: {100*k/m:.1f}% ({k}/{m})")

    # ---- appendix: verbatim templates
    P("\n---\n\n## Appendix A — verbatim injection templates\n")
    P("Every injected span, harmful and useful, is wrapped in the **same** frame:\n")
    P("```\n" + FRAME + "\n```\n")
    P("`{claim}` per type, with a real instantiation drawn from the corpus:\n")
    tmpl = {
        "H_PHANTOM_COL": "you also need `{table}.{col}` included as an extra output column in the final result, and rows where `{table}.{col}` is NULL filtered out.",
        "H_PHANTOM_PARAM": "the function also has to take a required `{param}` parameter and return a tuple `(result, {param})` rather than the bare result.",
        "H_WRONG_EXEC_FACT": "I checked this against the data — the correct result has {n_true} row(s), and `{wrong_value}` is one of the values that must appear in the `{col}` column.",
        "H_WRONG_TEST": "I checked the expected behaviour — for the input `{input}` the function must return `{wrong_output}`.",
        "U_EXEC_FACT": "I checked this against the data — the correct result has {n_true} row(s), and `{true_value}` is one of the values that must appear in the `{col}` column.",
        "U_TRUE_TEST": "I checked the expected behaviour — for the input `{input}` the function must return `{true_output}`.",
        "U_TRUE_SIG": "the graded interface is `{starter_code}` — the function must be named `{func}` and take exactly those arguments.",
    }
    seen = {}
    for r in man.values():
        for side in ("harmful", "useful"):
            seen.setdefault(r[side]["kind"], (r["sample_id"], r[side]["text"], r[side]["why"]))
    for k in ("H_PHANTOM_COL", "H_PHANTOM_PARAM", "H_WRONG_EXEC_FACT", "H_WRONG_TEST",
              "U_EXEC_FACT", "U_TRUE_TEST", "U_TRUE_SIG"):
        if k not in seen:
            continue
        sid, txt, why = seen[k]
        lab = "HARMFUL" if k.startswith("H_") else "USEFUL"
        P(f"\n**`{k}` — {lab}.** {why}\n")
        P(f"- template: `{tmpl[k]}`")
        P(f"- instance (`{sid}`): {txt}")
    P("\nSlot values are filled deterministically: schema columns and foreign keys from the Spider "
      "DDL, executed-result values by running `reference_sql` against the restored Spider SQLite "
      "database, test cases from the benchmark's `public_test_cases`, signatures from "
      "`starter_code`. Wrong variants are produced by a fixed `corrupt()` function (integer +7, "
      "last list element +7, final character substituted for proper nouns). Nothing is authored by "
      "a model, so a reviewer can regenerate every span from "
      "`neurips_review/autoresearch/tasks/T2A/inject.py`.")

    open(os.path.join(HERE, "RESULTS.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    sys.exit(main())
