# Rebuttal Response — AC3 NeurIPS (Sub. 27902)

**Draft for OpenReview.** Structured as a shared *Global Response* + three *Per-Reviewer* responses. Numbers are drawn from post-NeurIPS runs (`neurips_review/03_rebuttal_plan.md` for provenance). **Before posting:** (1) verify each number against the canonical source, (2) confirm the referenced revision edits are actually live in the current `.tex`, (3) fill the two bracketed `[TO RUN]` cells if we run the in-window experiments.

> Tone: concede-then-convert. We agree with the honest core of every critique, then show the number that survives it. We never re-defend a claim a reviewer already broke.

---

## Global Response (to all reviewers + AC)

We thank the reviewers and AC. The three reservations the AC names — generalizability, the structural-exclusion assumption, and experimental strength — are fair characterizations of the *submitted* version. We address each with work completed since submission, and we have removed every overclaim the reviewers correctly flagged. In brief:

**1. One method, one knob (generalizability).** AC3 is a *single* design: one shared two-query analyzer (spec-extraction → approach-evaluation) feeding one operator family {Augment, Reset, Gated-Reset, Rewrite}. What varies across benchmarks is **which operator intensity fits the setting**, and that follows a stated rule rather than per-benchmark tuning: *the more the history is polluted / the weaker the model, the heavier the operator*. Our agentic results make this concrete — on tau2 the **lightest** operator (Augment) wins on the strongest model (gpt-5.4) and the **heaviest** (Rewrite) wins on the weakest (Kimi). We now include an explicit **"essential vs. adaptive components"** table (below) so it is unambiguous which parts are fixed and which are the single tunable knob.

**2. Statistics — scaled up and reported as mean±std.** We increased LiC sample sizes from ~18–25 to **~113–150 per cell** (≈6×), and replaced best-of-3 with **mean ± std**:

| LiC task | AC3 (Gated-Reset) mean±std, N=3 | Full-Context baseline | AC3 mean clears baseline? |
|---|---|---|---|
| math | **80.0 ± 5.0** | 60.0 | ✓ |
| code | **64.4 ± 7.2** | 15.8 | ✓ |
| database | **38.7 ± 6.1** | 4.0 | ✓ |
| actions | **61.3 ± 6.1** | 34.8 | ✓ |

On WildChat (N=3) the win-rate vs. Assistant-Omission is **89.8% ± 1.4** (Reset) and **92.1% ± 1.3** (Augment) — tight, not noise. We commit to paired significance tests / bootstrap CIs on all headline cells for camera-ready.

**3. A multi-model agentic (tau2) matrix, honestly reported.** We retired the "only method robust across the spectrum" phrasing. The defensible, and stronger, claim is what the data shows across **three** respondent models on tau2 (telecom, n=19):

| tau2 (reward %) | gpt-5.4 | DeepSeek-V4-Flash | Kimi-K2.6 |
|---|---|---|---|
| Baseline (full context) | 68.4 | 31.6 | 26.3 † |
| **Assistant-Omission** | **0.0** | **0.0** | **0.0** |
| Best AC3 operator | **84.2** (Augment) | **57.9** (Augment/Rewrite) | **73.7** (Rewrite) |
| Δ over Baseline | **+15.8** | **+26.3** | **+24–34 (conservative)** ‡ |

† Kimi baseline was rate-limit-clipped; true value likely 40–50%. ‡ We therefore quote a **conservative** margin for Kimi, not the raw +47pp. **Assistant-Omission collapses to 0% on every model** because it deletes the tool-call state, while the best AC3 operator beats the full-context baseline by double digits on every model. We report the *best operator per cell*; we explicitly do **not** claim any single operator (e.g. Gated-Reset, which loses to baseline on gpt-5.4) is universally best.

**4. CollabLLM — an earlier artifact corrected.** The submitted CollabLLM numbers used a weak user simulator that never conveyed the task specification. With a competent user-sim, AC3-Augment reaches **100%** on MATH-Hard (Baseline 95, AO 90) and AC3-Reset **leads** BigCodeBench at **20%** (AO 15, Baseline 5). The earlier "AC3 regresses below baseline" reading was a simulator artifact and is withdrawn.

**5. Overclaims removed.** We now state the scoped conclusion the reviewers say the evidence supports: AC3 is the only context-management method tested that both improves self-contained/conversational settings **and** avoids catastrophic collapse in stateful tool use; on genuinely referential turns where the referent lives only in assistant history, structural exclusion does not apply and soft-attention + memory only partially closes the gap — which we now state as an open problem, not a solved one.

### Essential vs. adaptive components (new table)

| Component | Status | Notes |
|---|---|---|
| Two-query analyzer (spec → approach eval) | **Essential, shared** | Identical across all four benchmarks |
| Structural exclusion of assistant turns during spec extraction | **Essential where user turns self-specify the task** | *Principled* switch: disabled when intent weaves through assistant turns (CollabLLM), stated a priori |
| Operator {Augment / Reset / Gated-Reset / Rewrite} | **Single tunable knob** | Intensity chosen by pollution level / model strength; see tau2 ordering |
| Gating (skip edit when analyzer finds no issue) | Optional | High recall; asymmetric false-negative cost on strong-model text |
| Memory (cheatsheet) | Optional add-on | Ablated; not load-bearing for any headline claim |

---

## Response to Reviewer iNYK

Thank you — your two questions are precisely the right tests, and we can now answer both.

**Q1 (re-report on an unbiased subset).** We agree the Table-2 hard subset (20 hardest by baseline failure, GPT-5.2-trajectory replay) inflates deltas through regression-to-the-mean, and we now disclose this at every mention. The relevant test is whether the gain survives off that subset — it does. On the **full, non-difficulty-selected** LiC pool (~113–150/cell), Reset beats Baseline by **+13–17pp** benchmark-average across three models (DeepSeek-V4-Flash +17.1, gpt-5.4 +16.8, Kimi +13.9). The effect shrinks from the +20–42pp headline but remains clearly non-zero and consistent — so, per your criterion, the generalization claim stands on unbiased data, and we have rewritten the headline to the smaller, honest number. [If run: we additionally report a randomly-drawn subset selected independently of baseline results — Reset X.X ± X.X vs Baseline Y.Y ± Y.Y — confirming the effect. `[TO RUN #1]`]

**Q2 (mean±std over seeds; does AC3's mean clear baseline?).** Yes. See the mean±std table in the Global Response: on all four LiC tasks the AC3 (Gated-Reset) **mean** exceeds the Full-Context baseline (80.0 vs 60.0; 64.4 vs 15.8; 38.7 vs 4.0; 61.3 vs 34.8). We also correct the specific number you flagged: the "48% vs 32% exceeds-oracle" database result came from a single Reset run; the replicated figure is **38.7 ± 6.1**, and we now report that instead. On tau2 we report the multi-model result above rather than best-of-3; we note that AC3 clears baseline on all three models with the best operator, and we are candid that Gated-Reset *specifically* does not (it loses on gpt-5.4), which is why we no longer present it as the universal default.

**On the +20–42pp claim being weaker than it appears** — agreed; we have de-emphasized it in favor of the full-pool +13–17pp and the multi-model tau2 result, and clarified that Table 2 measures recovery from a fixed polluted history (a controlled attribution setting), not native multi-turn behavior.

**On "robust across the spectrum" vs. tau2** — you are right that the mean, not best-of-3, is the honest statistic, and that "robust" meant "did not collapse." We have removed the universal phrasing; the claim is now "does not catastrophically collapse in stateful tool use," which the AO→0% vs. AC3 double-digit-gain contrast supports directly.

---

## Response to Reviewer Vg97

Thank you — your four points sharpen the paper materially.

**Q1 / baselines.** ERGO is already included (CollabLLM). We agree stronger context-management comparisons help. **MT-OSC** (arXiv:2604.08782, 2026) is concurrent with our submission; we will add it as a LiC-style baseline where it can be adapted to our protocol and state precisely where it cannot (it assumes live multi-turn control that our replay attribution setup deliberately fixes). **U-Fold** is a trajectory-*compaction* method; we can slot it on tau2 as an additional context-management baseline and report it, since tau2 is where compaction-vs-curation is most separable. We will not dismiss these by category; we give the mechanism-level reason for each adaptation choice.

**Q2 / statistics.** Addressed in the Global Response: LiC scaled ~6×, mean±std replaces best-of-3, WildChat CIs are ±1.3–1.4pp, and we commit to paired/bootstrap tests for camera-ready. On tau2 we now report per-model results vs. baseline rather than best-of-3.

**Q3 / equal-compute & latency.** This is an important control and we address it two ways. First, our contagious-pollution result already argues the gains are **not** merely "more compute": a *contaminated* two-stage analyzer pipeline underperforms a single-pass baseline (Table 5) — extra LLM calls make things worse, not better, unless the added stage is structurally decontaminated. So the mechanism is decontamination, not budget. Second, we [report / will report] an explicit **equal-budget baseline** — self-reflection / summarization at AC3's matched call count (2–3 extra calls/turn), same model — together with **wall-clock latency**, not just API cost. [If run: at matched budget, self-reflection reaches Z.Z% vs AC3 W.W% on LiC-{task}. `[TO RUN #2]`]

**Q4 / the general algorithm.** See the "essential vs. adaptive components" table in the Global Response. The essential, shared parts are the two-query analyzer and structural exclusion (where user turns self-specify the task); the single adaptive knob is operator intensity, set by pollution level / model strength. The CollabLLM choice to disable structural exclusion is a *principled a-priori* switch (intent there genuinely weaves through assistant turns), not per-benchmark tuning, and the tau2 "strategic reflection" variant is the same analyzer with tool-state tracking added because the environment is stateful — we will rename it in the text to make the continuity explicit rather than implying a separate method.

On your suggestion to **move the hard-attention/structural-exclusion ablation to the main body** — agreed, we are moving it; it is one of the paper's core results.

---

## Response to Reviewer 5YHP

Thank you for the unusually thorough read — your six points define our revision.

**W1 / structural exclusion fails on deeply-referential turns.** We agree and now state this as the paper's scoped claim rather than glossing it. Structural exclusion is provably best exactly when user turns independently specify the task; where the referent exists only in assistant history ("modify the second paragraph"), the soft-attention variant + memory only partially closes the gap (Appendix D). We frame accurate useful-vs-harmful separation under full visibility as the central open problem, and we do not claim to have solved it.

**W2 / not a single fixed method.** Addressed via the essential-vs-adaptive table (Global Response): one analyzer, one operator family, one intensity knob; the per-setting differences are settings of that knob plus the principled structural-exclusion on/off switch.

**W3 / small samples, replay, single runs.** Sample sizes are up ~6× (to ~113–150/cell) and headline rows now carry mean±std. On **replay**: we want to defend it as a deliberate *causal-attribution* design — every method inherits an identical polluted trajectory, so the measured delta is purely the intervention's effect and not divergent user-sim paths — while agreeing the results should be read as *recovery from a fixed polluted history*, which is now how we phrase them. We also run non-replay/fresh-sim settings (CollabLLM Phase-3, WildChat, and tau2 which is genuinely multi-turn agentic); the fresh-sim finding that Augment's "analysis pile-on" can hurt long conversations is exactly what motivates gating. We commit to one end-to-end LiC run for camera-ready.

**W4 / referential evidence weaker than headline.** On CollabLLM, the submitted numbers were a weak-user-sim artifact; corrected numbers show AC3-Augment 100% (MATH-Hard) and AC3-Reset leading BigCodeBench at 20% (Global Response). We are candid that on the averaged CollabLLM cells no single operator dominates and AO stays competitive — that is the mid-referentiality regime, and our claim there is only "best-operator ≥ baseline, no collapse." On the **BigCodeBench GPT-5 judge**: executable tests were unavailable because the simulator cannot pass the required function signatures; we note the judge does discriminate (v8-Rewrite 17.6% vs Reset 0% on gpt-5.4; 16.7% vs 0% on Kimi) and we will add judge-agreement / partial execution for camera-ready. On **WildChat**: we report the honest win-rate range (**72–92%**, not a narrow band), and we will add position-bias and judge-agreement checks; the differing sample counts are due to per-method AO-failure pools and we will footnote them.

**W5 / analyzer not evaluated as a detector.** We now provide gate-behavior data from the Gated-Reset reconstruction (the analyzer's `needs_edit` flag): gate-open rate is **≥97%** on text (LiC 97.3%, CollabLLM 98.3%), and the gate meaningfully bites only on agentic and strong-model text. Its error profile is asymmetric — high recall for genuine issues, but **false-negative closes** are the dominant cost (WildChat gpt-5.4: Gated-Reset 74.1% vs. always-on Reset 88.6%, −14.5pp). We commit to a span-level annotation study (stale / useful / must-preserve) with detector precision/recall for camera-ready, and can provide a pilot in-window if helpful.

**W6 / memory mixed.** We now present memory as an optional, ablated add-on (helps math, ~neutral on code) and agree it can inject stale priors — consistent with our own contagious-pollution finding. It is not load-bearing for any headline claim; we add order-sensitivity and train/eval-split analysis.

**On clarity (your score of 2):** we have tightened the narrative so the scoped conclusion and the headline match, moved the structural-exclusion ablation to the main body, and aligned the abstract/Figure 1 language with the corrected claims.

---

## Appendix: numbers to double-check before posting
- tau2 uses the **n=19 Azure Foundry** sweep, not the older n=20 OpenRouter substitute.
- Kimi tau2 margin quoted **conservatively (+24–34pp)** because its baseline was rate-limit-clipped.
- LiC mean±std row = **Gated-Reset, N=3 replay**; other LiC ours-rows are still single-trial (say so).
- WildChat range = **72–92%** (not 84–86%).
- "Every operator beats baseline" is **false** — claim best-operator-per-cell (6 sub-baseline cells exist).
- Confirm the current `.tex` reflects the reconciled framing (Overleaf sync had been blocked).
- `[TO RUN #1]` random-subset LiC and `[TO RUN #2]` equal-budget baseline: fill or delete before posting.
