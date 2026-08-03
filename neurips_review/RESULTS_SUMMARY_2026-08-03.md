# New Results Since Submission — Neutral Summary
**As of 2026-08-03.** Descriptive only: what was run, what was measured, what it does and does not show. No response strategy — that is in `PLAN_2026-08-03.md`.

Scope: the two areas of new work. **(A)** stronger / matched-compute baselines. **(B)** direct evaluation of pollution removal, measured separately from downstream task accuracy.

Every number below traces to an artifact under `neurips_review/autoresearch/` (abbreviated `AR/`). Findings are cited as F-numbers in `AR/WORKLOG.md`.

---

# A. Baselines

## A1. Generic LLM condensation, at matched call budget

**Design.** Per-turn condenser: an LLM compresses the conversation history, the assistant proceeds from the condensed context. The condenser is instructed to compress **faithfully** and is *not* told to find errors, judge correctness, or remove invalidated reasoning — that instruction difference is the experimental variable. Two budgets: 1 call/turn and 2 calls/turn. Venue: LiC database and code (chosen for headroom). Assistant: gpt-5.4-mini. N=1 per cell.

| Arm | database | code |
|---|---|---|
| Baseline (full context) | 56.1% (60/107) | 83.0% (83/100) |
| Summarisation, 1 call/turn | 53.3% (57/107), −2.8pp, p=0.678 | 79.0%, −4.0pp, p=0.481 |
| Summarisation, 2 calls/turn | 47.7% (51/107), −8.4pp, p=0.078 | 80.0%, −3.0pp, p=0.581 |
| AC3-Reset | 75.7% (81/107), +19.6pp, p=0.0005 | 92.0%, +9.0pp, p=0.023 |
| AC3-Gated-Reset | 73.8% (79/107), +17.8pp, p=0.0013 | not run |

Head-to-head paired, AC3-Reset − summarisation: +22.4 / +28.0pp (database), +13.0 / +12.0pp (code), all p<0.01. Artifact: `AR/tasks/T1/RESULTS.md`, `outputs/T1/`.

**Budget, measured rather than asserted.** Instrumented per component (`src/ctx_editor/utils/call_meter.py`). The 2-call summariser **exceeded** AC3-Reset's consumption: **1.02–1.19× strategy calls, 1.62–2.14× strategy tokens**. Gated-Reset obtains +17.8pp at **0.41×** Reset's calls.

**Prompt-sensitivity control.** A second, neutral-phrasing condenser (faithfulness instruction only) scores **51.4%** on database — between the two replicates of the original prompt (53.3 / 47.7). Both prompts verbatim in `AR/tasks/T1/worklog.md`. Artifact: `AR/tasks/T27/`.

**Mechanism probe.** With the "find errors" clause removed, the condenser flags an assistant error in **0 of 340** summaries — the same rate as with the clause present. Probe validated at 26.4% detection on AC3 analyzer output and 0% on baseline turns.

**Limitations.** N=1 per cell (`seed=` is inert on LiC; replicates vary by temperature only). Two tasks. One assistant model. A one-call-vs-two-call *ordering* was initially read as budget-dependent degradation; on replication the 1-call arm scored 47.7% — identical to the 2-call value — and the two 1-call runs differ by more (p=0.29) than 1-call differs from 2-call (p=0.26). The honest description is **neutral-to-negative at both budgets**, not monotone degradation (F74).

## A2. MT-OSC (arXiv:2604.08782), reimplemented

**Provenance.** No code release — the paper has no code/data availability statement and no repository link. Reimplemented from the paper text; source and a written faithfulness audit in `src/ctx_editor/strategies/mtosc.py`.

*Taken verbatim:* condenser prompt (App. B.1), the three few-shot exemplars (transcribed from Fig. 2, a rasterised image), JSON output contract, recursion `C_j = Condense({C_{j−1}} ∪ new pairs)`, decider hyperparameters (γ=0.2, τ=1000), decoder settings.
*Generalised and checked:* the schedule is specified only for w=4; we derived `T_j = (w−1)j + 2` with the paper's one-turn lag, and verified that substituting w=4 reproduces the paper's turn-by-turn walkthrough exactly.
*Underdetermined by the paper (4 items, recorded):* most notably the Decider's polarity is **self-contradictory** between §3's prose and the Combined-Operation equation. We implemented the prose. The choice is **inert on LiC** (τ=1000 user tokens is never reached by short sharded messages) and this is logged per run, not assumed. Condenser LLM is gpt-5.4-mini rather than the paper's Llama-3.3-70B, to match every other arm's operator model; the paper's §5.3 reports insensitivity to condenser model.

| Arm | database | Δ vs baseline |
|---|---|---|
| MT-OSC, w=4 (published setting) | 60.7% (65/107) | +4.7pp, p=0.383 |
| MT-OSC, w=2 (conversation-scaled) | 47.7% | −13.1pp vs w=4, p=0.016 |

**Engagement.** At w=4, MT-OSC performs **30 condensations across 107 conversations (0.3/conv)** and cannot modify context before turn 6; LiC conversations average 4.1 turns. Only **6 of those 30** ever reached a context (one-turn application lag). At w=2 it performs 237 (2.2/conv), a **7.9×** increase, and scores worse. Counting note: a composite over three heterogeneous log record types gives 0.62 and 5.67, i.e. 9.2× — that composite is not an engagement rate and should not be quoted (F87).

**Interpretation available from this.** At its published setting MT-OSC is close to a no-op on LiC-length conversations; increasing its engagement does not help. This is evidence about *length-triggered compaction schedules on short conversations*, not a general refutation of MT-OSC on the workloads it targets.

## A3. What is **not** covered

- **U-Fold: not run.** Declined 2026-07-29 on cost and because the tau2 fork was in use (`AR/tasks/T27/`).
- **Self-reflection at high pollution: not run.** The only reflection data is a session-1 equal-budget run on **near-ceiling math** (N=40), where all arms compressed to ~97.5% and the comparison was non-discriminating (`neurips_review/experiments/exp2_results.txt`). It was intended to fold into the T1 work; T1 ran summarisation and MT-OSC arms instead. **A reflection arm on database/code has not been executed.**
- Code-task coverage is partial: MT-OSC and Gated-Reset were run on database only.
- No condensation baseline on tau2, WildChat, or CollabLLM.

---

# B. Evaluating pollution removal independently of task accuracy

Three instruments, in increasing rigour and decreasing scale. The design problem being addressed: producing pollution labels is the task the analyzer performs, so an LLM judge is a peer detector, not an oracle.

## B1. Tier A — constructed pollution (no judge in the label path)

**Design.** Into 145 LiC database+code replay prefixes, inject **two** spans per conversation — one known-false, one known-**true** — in an identical surface frame, each anchored on a rare token verified absent from the conversation. Labels are ground truth by construction. 126 conversations pass a mechanical admissibility check. The two-span design is what makes preservation measurable: with only false spans injected, an editor that deletes everything scores perfectly.

**Results (AC3-Reset, n=126).** Pollution removal **97.6%** (123/126) CI [93.2, 99.2] · Preservation **4.0%** (5/126) CI [1.7, 9.0] · Edit precision **50.4%** (123/244), where **chance is 50%** · Gate sensitivity 98.4%.
Independent of the edit: the analyzer **names the injected pollutant in its `issues` output 78.6%** of the time (89.7% on the causally-harmful subset).
AC3-Rewrite on the same instrument: removal 27.0%, preservation 38.9%.

**Causal check, detector-free.** A factorial over the unedited baseline (clean / harmful-only / useful-only / both): the harmful span costs **−11.1pp**; the true span is worth **+15.1pp**. On the causally-validated subset: baseline clean 24.7% → with pollutant 9.3% → AC3-Reset with pollutant present 59.8%.

**Controls.** Identity editor 0.000/1.000, oracle 1.000/1.000, nuke 1.000/0.000, delete-both 1.000/0.000. One control caught a substring-vs-word-boundary bug that would have overstated removal.

**Stated limitation (in the writeup's first paragraph).** Injected pollution is plausibly more salient than natural pollution, so these are an **upper bound / sanity check**, not a field estimate. Two of four injected types are causally inert; N=1 per cell; single model. Artifact: `AR/tasks/T2A/`.

## B2. Tier B — counterfactual span ablation on naturally occurring spans

**Design.** For each span, re-run the assistant **14× with the span present and 12× with it removed**, everything else fixed. Pollution is defined by **causal effect**; no detector, judge or LLM appears anywhere in label generation. 111 natural spans across 30 LiC database+code conversations; 3,357 assistant turns; 0 errors.

**Controls, both directions.** Contentless span +0.033 (n.s.) · Tier-A's validated pollutant **+0.368** (p=1e-4) · full-spec + gold-SQL span **−0.447** (p<1e-4). Probe controls identity 1.000 / nuke 0.000. MDE 0.333 as an observed difference.

**Is natural pollution real?** Point labels (|δ|≥0.25): 11 harmful, 5 useful, 95 inconclusive — per-span identification is weak. In aggregate, against a replicate-matched parametric null: effect SD **0.155 vs 0.125** (p=0.0085), and 16 large-effect spans where the null predicts 9.3 (p=0.017). Mean effect +0.020 [−0.010, +0.048].
→ **Natural spans carry real causal effects, concentrated in a ~6% excess minority; the typical span is inert.**

**Does AC3 remove the harmful ones selectively?** Removal on causally harmful spans **100%** (7/7). Preservation on causally useful spans **0%** (0/4). **Edit precision is exactly at the base rate (63.6%) for both operators.** AC3-Reset keeps 5/66 probe-admissible spans; **AC3-Rewrite keeps 0/66**. A label-free aggregate test agrees (Reset removed−kept = −0.014, p=0.85).

**Relation to Tier A.** Rewrite appeared selective on Tier A (27.0/38.9) and is not on natural spans. Explanation: a compactor can copy a short *injected* sentence verbatim, but paraphrases the model's own verbose prose and code, so nothing distinctive survives. Tier A's own salience caveat proved load-bearing.

**Limitations (8, stated by the study).** Most spans are *inconclusive*, and inconclusive ≠ inert. Useful spans are structurally under-detectable at LiC's low base rates. The 30 conversations are a headroom-selected high-power subsample, not representative. ~40% of spans lack a unique token and are excluded from the 2×2, so the probe measures *lexical* survival and prose preservation is a lower bound. One model, one analyzer, `replay_turns=1`. Single-span ablation only — no interactions. Tier C (oracle-informed judge at scale) not run. The pre-registered "does removal rate predict accuracy gain" correlation has a **zero-variance predictor** — both operators removed 100% of harmful spans in all 6 qualifying conversations. Cost $62.80. Artifact: `AR/tasks/T2B/`.

## B3. Auditing vs. re-solving

**Design.** For each analyzer output in the LiC replay matrix, determine whether it contains or entails the verified correct answer; then re-measure the paired AC3-vs-baseline gain restricted to the non-leaking subset. Strict detector = answer-verification pass ∪ math-only numeric probe.

| Task | Leak rate | Paired gain on no-leak subset |
|---|---|---|
| code | **0%** (0/106) | **+30.2pp**, n=106, p<0.0001 |
| database | 1% (1/147) | **+26.0pp**, n=146, p<0.0001 |
| actions | 2% (3/150) | +6.8pp, n=147, p=0.099 |
| **math** | **47%** (67/144) | **−2.6pp**, n=77, p=0.815 |
| math+code+database pooled | 17% | **+20.7pp** [+14.8, +25.3], n=329, p<0.0001 |

A model-free numeric probe on math independently returns ~40% against the LLM detector's rate. Gated-Reset reproduces the pooled effect (+19.6pp, n=311).

**Limitations.** Conditions on a post-treatment variable: baseline accuracy is 36.5% on the no-leak subset vs 75.0% on the leaking one, so the *between*-stratum contrast is not causal (the within-stratum paired test is). A 3-way classifier failed validation and was replaced by the strict union detector; the reported hand-validation (29/32) was drawn from the *judge's* partition, not the primary one, and is reattributed accordingly. Single model, one run per cell. Artifact: `AR/tasks/T2c/`.

## B4. Analyzer-model sensitivity

Assistant pinned to DeepSeek-V4-Flash; only the analyzer varies. LiC code+database, n=178 matched pairs, exact McNemar, 2 replicates.

| Analyzer | Family | AC3-Reset | Δ | p |
|---|---|---|---|---|
| Kimi-K2.6 | Moonshot | 61.2 ± 2.4 | +39.9 | 2e-17 |
| DeepSeek-V4-Flash | DeepSeek | 50.0 ± 2.4 | +28.7 | 3e-09 |
| gpt-5.4-mini | OpenAI | 48.3 ± 1.6 | +27.0 | 1e-08 |
| Llama-3.3-70B | Meta | 39.3 ± 0.0 | +18.0 | 6e-06 |
| gpt-4o-mini | OpenAI | 34.3 ± 0.8 | +12.9 | 8e-04 |

All positive and individually significant; none falls below baseline in either replicate. Failure mode of weak analyzers is measured: gpt-4o-mini declares `needs_edit` on 74.4% of turns vs ~97% for strong analyzers and writes 2.7× shorter issue lists, while `user_intent` parses on 100% of calls and `edited_context` is non-empty on 100% of applied edits — it **under-detects rather than mis-detects**. The cache-key confound was checked and excluded three ways. Limitations: n=40+49 per replicate; adjacent rungs are not individually separated; ± is spread over N=2, not a variance estimate. Artifact: `AR/tasks/T9/`.

---

# C. What these results do and do not establish

**Supported by the above:**
- A faithful, non-analyzer condenser at equal-or-greater measured budget does not close the LiC multi-turn gap on database or code; AC3 does. The result is not an artifact of the condenser prompt's wording.
- The analyzer's benefit does not depend on answer leakage on code or database; it does on math, where auditing and solving are not separable.
- Natural pollution is causally real and concentrated in a small minority of spans; AC3 removes 100% of the causally harmful ones.
- The gain is not specific to one analyzer model or family; it degrades gracefully with analyzer strength.

**Not supported, and revised by this work:**
- **"We preserve what's correct and remove what's harmful"** does not hold for either operator on natural spans: edit precision is at the base rate and preservation is 0–4%. The supported mechanism is **detect, discard the assistant side, and re-derive the task from the user side.**
- The pollution-detection numbers are an upper bound (Tier A) or drawn from a headroom-selected subsample (Tier B); neither is a field estimate.
- The reported detection rate is a *firing* rate: 29% (LiC) / 73% (CollabLLM) of gate-open records have the analyzer writing `issues: "None"` while still setting `needs_edit=true`.

**Not addressed:** U-Fold; self-reflection at high pollution; Tier C at scale; condensation baselines outside LiC; interactions between spans; human agreement on any label set.
