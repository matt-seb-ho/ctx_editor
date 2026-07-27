# Paste-Ready OpenReview Comment Drafts — AC3 (Sub. 27902)

These are the **actual comments to post** on OpenReview: one General Response + one reply per reviewer, tightened for reading. The fuller reasoning lives in `04_rebuttal_response.md`; this file is what you paste.

**Before posting:** experiment numbers (Exp1 random-subset, Exp2 equal-budget) are **filled in** from `experiments/exp1_results.txt` / `exp2_results.txt`. Still to do: re-verify every *pre-existing* number against its canonical source (see guardrails below), confirm the revised PDF reflects the reconciled framing, and coordinate with co-authors before posting.

---

## GENERAL RESPONSE (post once, to all reviewers + AC)

We thank the reviewers and AC. The three reservations named — generalizability, the structural-exclusion assumption, and experimental strength — are fair for the submitted version, and we have addressed each with work completed since submission. We summarize here; per-reviewer replies give specifics.

**1. AC3 is one method with one knob, not a per-benchmark family.** Every setting uses the *same* two-query analyzer (spec-extraction → approach-evaluation) and the *same* operator set {Augment, Reset, Gated-Reset, Rewrite}. What varies is operator *intensity*, and it follows a stated rule — heavier operators for more-polluted histories / weaker models — not per-benchmark tuning. Our agentic (tau2) results show exactly this ordering: the lightest operator (Augment) wins on the strongest model, the heaviest (Rewrite) on the weakest. We add an explicit **essential-vs-adaptive component table** and a unified algorithm statement.

**2. Statistics: scaled up and reported as mean±std.** LiC per-cell samples went from ~18–25 to **~113–150** (≈6×). We replace best-of-3 with mean±std; on all four LiC tasks the AC3 mean clears the full-context baseline (math 80.0±5.0 vs 60.0; code 64.4±7.2 vs 15.8; database 38.7±6.1 vs 4.0; actions 61.3±6.1 vs 34.8). WildChat (N=3) win-rate vs. assistant-omission is 89.8±1.4 (Reset) / 92.1±1.3 (Augment).

**3. A multi-model agentic matrix, honestly reported.** We have revised the abstract and introduction to replace "the only method robust across the spectrum" with the precise, verifiable claim "**the only method that improves over full context across the entire spectrum**." On tau2 (telecom, n=19, three models), **assistant-omission collapses to 0% on every model** (it deletes tool-call state), while the **best AC3 operator beats the full-context baseline on every model** (+15.8 / +26.3 / +24–34pp). We report the best operator per cell and explicitly note that Gated-Reset alone does *not* win everywhere (it loses on gpt-5.4).

**4. New experiments in this response.** (a) A **random, non-difficulty-selected, end-to-end** LiC run on a fresh model (gpt-5.4-mini), **over 3 reruns (mean±std)**, to answer whether gains survive off the hard subset (iNYK Q1/Q2); (b) an **equal-compute self-reflection baseline** at matched call budget + latency (Vg97 Q3). Numbers in the per-reviewer replies.

**5. Overclaims removed.** The paper now states the scoped conclusion the reviewers identified: AC3 improves self-contained/conversational settings *and* avoids catastrophic collapse in stateful tool use; separating useful from harmful assistant content when both must be visible (deeply-referential turns) is stated as an open problem, not a solved one.

---

## REPLY TO REVIEWER iNYK

Thank you — your two questions are the right tests, and we can now answer both directly.

**Q1 — Reset vs. Baseline on an unbiased subset.** We agree the Table-2 hard subset (20 hardest by baseline failure, GPT-5.2-trajectory replay) inflates deltas via regression-to-the-mean; we now disclose this at every mention. Two pieces of evidence show the effect survives off that subset:
- On the **full, non-difficulty-selected** LiC pool (~113–150/cell), Reset beats Baseline by **+13–17pp** benchmark-average across three models (DeepSeek-V4-Flash +17.1, gpt-5.4 +16.8, Kimi +13.9) — smaller than the +20–42pp headline, but clearly non-zero and consistent.
- **New (this response, N=3):** we drew a **uniformly random N=40 subset** of LiC-math (selected with no reference to baseline outcomes) and ran **fresh end-to-end** conversations (not replay) with a **new model (gpt-5.4-mini)**, over **3 reruns**. Mean±std — on the false-negative-adjusted metric (the paper's headline metric): Baseline **87.5±2.0** → **AC3-Reset 100.0±0.0 (+12.5pp)**, **AC3-Gated-Reset 99.1±1.2 (+11.6pp)**; on raw accuracy (n=40): Baseline 87.5±2.0 → Reset 93.3±4.2, Gated 95.0±0.0. **Both operators improve over baseline in every one of the three reruns.** This answers the selection-bias concern (unbiased subset), the replay concern (end-to-end), and your Q2 request in one shot — the new result is reported as mean±std, not a single seed.

Per your criterion, the generalization claim stands on unbiased data; we have rewritten the headline to the smaller, honest number.

**Q2 — mean±std over seeds; does AC3's mean clear baseline?** Yes. On all four LiC tasks the AC3 (Gated-Reset, N=3) mean exceeds the full-context baseline (see General Response). We also correct the specific number you flagged: the "48% vs 32% exceeds-oracle" database result was a single Reset run; the replicated figure is **38.7 ± 6.1**, which we now report. On tau2 we report per-model results vs. baseline rather than best-of-3, and we are explicit that AC3 clears baseline with the best operator on all three models while **Gated-Reset specifically does not** (it loses on gpt-5.4) — which is why we no longer present it as a universal default.

**On "robust across the spectrum" vs. tau2** — you are right that the mean, not best-of-3, is the honest statistic and that "robust" meant "did not collapse." We have revised the abstract and introduction to replace "the only method robust across the spectrum" with "**the only method that improves over full context across the entire spectrum**": the best operator per cell beats full context on all four regimes, while AO collapses to 0% on tau2. This is a verifiable claim, not an absolute about noise.

---

## REPLY TO REVIEWER Vg97

Thank you — your points sharpen the paper materially.

**Q1 — stronger baselines.** ERGO is already included (CollabLLM). We agree stronger context-management comparisons help. **MT-OSC** (arXiv:2604.08782) is concurrent with our submission; we will add it as a LiC-style baseline where it adapts to our protocol and state precisely where it cannot (it assumes live multi-turn control that our replay-attribution setup deliberately fixes). **U-Fold** is a trajectory-*compaction* method; we can add it on tau2, where compaction-vs-curation is most separable. We give the mechanism-level reason for each rather than dismissing by category.

**Q2 — statistically sound results.** Addressed in the General Response: LiC scaled ~6×; mean±std replaces best-of-3; WildChat CIs are ±1.3–1.4pp; tau2 reported per-model vs. baseline. We commit to paired tests / bootstrap CIs on headline cells for camera-ready.

**Q3 — equal-compute & latency.** Important control; we address it two ways.
- *Mechanism argument:* our contagious-pollution result already shows the gain is **not** merely "more compute" — a *contaminated* two-stage analyzer pipeline underperforms a single-pass baseline (Table 5); extra LLM calls hurt unless the added stage is structurally decontaminated.
- *New experiment (this response):* an **equal-budget self-reflection baseline** — a matched extra LLM call per turn over the full context, same model — with **wall-clock latency** logged. On the random N=40 LiC-math set (matched seed for an apples-to-apples control): Baseline 90.0% (36/40), equal-budget Reflection 97.5% (39/40), AC3-Reset 97.5% (39/40). On this near-ceiling task (baseline already 90%) Reflection and Reset are indistinguishable — with little *harmful* pollution to remove, a matched-budget reflection recovers the same cases — so this particular task does not separate "compute" from "decontamination." That separation is provided directly by our **contagious-pollution result (Table 5)**: adding a second analyzer stage that is *not* structurally decontaminated drops accuracy *below* the single-pass baseline — extra compute in the wrong place *hurts*. Together these show more compute is neither necessary nor sufficient; correct structural decontamination is. We will add a matched-budget reflection control on a *high-pollution* benchmark (database / tau2) for camera-ready. **Latency:** the matched-budget reflection adds ~13% wall-clock over baseline at equal turn counts (231s vs 205s, both n=40 at avg 5.2 turns, concurrency 10); AC3-Reset's higher wall-clock (547s) largely reflects that curation *lengthened* conversations (8.5 vs 5.2 turns), and Gated-Reset — the deployment default — runs at 266s / 6.6 turns.

**Q4 — the general algorithm.** See the essential-vs-adaptive table (General Response). Shared/essential: the two-query analyzer + structural exclusion where user turns self-specify the task. Single adaptive knob: operator intensity, set by pollution level / model strength. The CollabLLM choice to disable structural exclusion is a *principled a-priori* switch (intent there genuinely weaves through assistant turns), and the tau2 "strategic reflection" variant is the same analyzer with tool-state tracking added for a stateful environment — we rename it in the text to make the continuity explicit.

We are also **moving the structural-exclusion ablation to the main body**, as you suggested.

---

## REPLY TO REVIEWER 5YHP

Thank you for the thorough read — your six points define our revision.

**W1 — structural exclusion fails on deeply-referential turns.** Agreed, and now stated as the paper's scoped claim. Structural exclusion is provably best when user turns independently specify the task; where the referent lives only in assistant history, soft-attention + memory only partially closes the gap (Appendix D). We frame accurate useful-vs-harmful separation under full visibility as the central open problem and do not claim to solve it.

**W2 — not a single fixed method.** Addressed via the essential-vs-adaptive table: one analyzer, one operator family, one intensity knob; per-setting differences are settings of that knob plus the principled structural-exclusion on/off switch.

**W3 — small samples, replay, single runs.** Samples up ~6× (to ~113–150/cell); headline rows now carry mean±std. On **replay**: it is a deliberate causal-attribution design — every method inherits an identical polluted trajectory, so the measured delta is the intervention's effect, not divergent user-sim paths — and we now phrase LiC results as "recovery from a fixed polluted history." We also report a **new fresh, end-to-end** (non-replay) run on a uniformly random subset with gpt-5.4-mini, over **3 reruns** (FN-adjusted: Baseline 87.5±2.0 → Reset 100.0±0.0 / Gated-Reset 99.1±1.2; raw: Reset 93.3±4.2, Gated 95.0±0.0), showing the effect is neither a replay artifact nor a single-seed fluke.

**W4 — referential evidence weaker than headline.** On CollabLLM, the submitted numbers used a weak user-simulator that never conveyed the task spec; with a competent user-sim, AC3-Augment reaches 100% on MATH-Hard (Baseline 95, AO 90) and AC3-Reset leads BigCodeBench at 20% (AO 15, Baseline 5) — the earlier "regresses below baseline" reading was a simulator artifact and is withdrawn. We are candid that on the averaged CollabLLM cells no single operator dominates and AO stays competitive (the mid-referentiality regime); our claim there is only "best-operator ≥ baseline, no collapse." On the **BigCodeBench judge**: executable tests were unavailable because the simulator cannot pass required function signatures; the judge does discriminate (v8-Rewrite 17.6% vs Reset 0% on gpt-5.4; 16.7% vs 0% on Kimi), and we will add judge-agreement / partial execution for camera-ready. On **WildChat**: we report the honest win-rate range (**72–92%**) and will add position-bias and judge-agreement checks; differing sample counts come from per-method AO-failure pools and will be footnoted.

**W5 — analyzer not evaluated as a detector.** We add gate-behavior data from the Gated-Reset reconstruction (the analyzer's `needs_edit` flag): gate-open rate ≥97% on text (LiC 97.3%, CollabLLM 98.3%); the gate bites mainly on agentic and strong-model text. Its error profile is asymmetric — high recall for genuine issues, but **false-negative closes** dominate the cost (WildChat gpt-5.4: Gated-Reset 74.1% vs. always-on Reset 88.6%, −14.5pp). We commit to a span-level annotation study (stale / useful / must-preserve) with detector precision/recall for camera-ready, and can provide a pilot in-window if helpful.

**W6 — memory mixed.** We now present memory as an optional, ablated add-on (helps math, ~neutral on code) and agree it can inject stale priors — consistent with our own contagious-pollution finding. It is not load-bearing for any headline claim; we add order-sensitivity and train/eval-split analysis.

**On clarity (your score of 2):** we tightened the narrative so the scoped conclusion matches the headline, moved the structural-exclusion ablation to the main body, and aligned the abstract/Figure 1 language with the corrected claims.

---

### Verification ledger (before posting)
- **Experiment numbers: FILLED (N=3).** Exp1 (random N=40 end-to-end, gpt-5.4-mini, 3 reruns) FN-adjusted: Baseline 87.5±2.0 / Reset 100.0±0.0 / Gated 99.1±1.2; raw: Baseline 87.5±2.0 / Reset 93.3±4.2 / Gated 95.0±0.0. Exp2 (equal-budget reflection, matched seed): 97.5 (ties Reset). Sources: `experiments/exp1_results.txt`, `exp1_reps_results.txt`, `exp2_results.txt`.
- Verify pre-existing numbers vs canonical sources (tau2 n=19 Foundry; Kimi +24–34 conservative; WildChat 72–92%; "best operator per cell," not "every operator").
- Paper overclaim edit is committed locally (inner repo `b1a629a`) but **not pushed** (Overleaf remote down). Push before/with posting so the PDF matches the rebuttal. See `paper_edits_needed.md`.
