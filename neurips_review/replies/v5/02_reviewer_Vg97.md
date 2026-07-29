# Response to Reviewer Vg97

We thank the reviewer for a thorough and constructive review, and for the specific pointer to MT-OSC. Both halves of Q3 — analyzer sensitivity and compute budget — are now answered with completed experiments rather than with promises, and Q1's baseline is now run. We address each weakness and question below.

## Response to Weaknesses

> **W1:** The central weakness is the set of baselines in the experiment... the paper should compare against recent stronger context-condensation/context-management methods such as MT-OSC.

**Response to W1:** We have now run the condensation baseline rather than argued for its exclusion. Please see **Common Weakness 5** in the General Response, and Q1 below.

---

> **W2:** Another concern is the statistical reliability. Many of the headline LiC cells use small sample sizes, with only the Gated-Reset row repeated three times... The tau2-bench result is also not very persuasive as currently presented.

**Response to W2:** Please see **Common Weakness 2** (scaled evaluation and paired tests) and **Common Weakness 4** (tau2 re-reported at N=3 per cell rather than best-of-3).

On tau2 in particular, we now agree with you more strongly than we did, and can quantify it: at n=19 tasks a single tau2 cell has a binomial standard deviation of about **10.7pp**, and our N=3 re-measurement of a Baseline cell returns **±13.9pp**. Any tau2 difference below roughly 15pp measured at N=1 is inside the noise, which includes several differences we reported. We are re-reporting that benchmark at N=3 and will not headline any tau2 gap that does not clear its own noise floor.

---

> **W3:** A third concern is that the method changes substantially across settings... it is not obvious whether the paper is validating a single method, a family of prompt-engineering patterns, or several task-specific context-management variants.

**Response to W3:** Please see **Common Weakness 1**, where we now demonstrate that the same four operators run across 3 models x 4 LiC tasks plus CollabLLM, WildChat, and tau2 with no per-benchmark tuning. Q3 and Q4 below add the component-level and analyzer-level breakdowns you requested.

## Response to Questions

> **Q1:** Can the authors compare against stronger context-management baselines as described in the weakness section? Otherwise, the authors should be able to clearly justify why the stronger baselines cannot be adapted.

**Response to Q1:** We have run it. The result is in **Common Weakness 5**; we summarise the three things we think you will most want to check.

**Summarisation does not close the gap — it moves accuracy down.** On our two highest-pollution LiC tasks, paired against identical conversations: on database, summarisation at 1 call/turn is **−2.8pp** and at 2 calls/turn is **−8.4pp** against full context, while AC3-Reset is **+19.6pp** (p = 0.0005); on code, summarisation is **−4.0 / −3.0pp** while AC3-Reset is **+9.0pp** (p = 0.023). Head-to-head and paired, AC3-Reset beats summarisation by +22.4 / +28.0pp on database and +13.0 / +12.0pp on code, all p < 0.01. This is the mechanism prediction we made in Related Work behaving as predicted: a good-faith condenser preserves invalidated reasoning in compressed form.

**The budget comparison came out better than parity.** We instrumented every LLM call and token per component. The budget-matched summariser **over-consumed** AC3-Reset — 1.02–1.19x its strategy calls and 1.62–2.14x its strategy tokens — and still lost by 12 to 28 points.

**On MT-OSC we decline to claim a win.** Our reimplementation at the published window (w=4) improves database by +4.7pp (p = 0.383), but it fired only **30 times across 107 conversations, 0.3 per conversation**, because it cannot compact before turn 6 and LiC conversations average 4.1 turns. That is not a fair test of MT-OSC's idea. What it does establish is a scoping claim about the whole family: a length-triggered compaction schedule **structurally cannot engage** with pollution that arrives in the first few turns. We will report it in exactly those terms, cite MT-OSC as concurrent work (2026), and release both condenser prompts verbatim.

Limits we state ourselves: one respondent model, one run per cell, two tasks; the neutral-prompt robustness variant of the summariser was implemented but did not finish in the discussion window.

---

> **Q2:** Can the authors report statistically sound results for the main claims? Please provide confidence intervals, paired tests, or bootstrap analyses for LiC and WildChat, and report mean ± variance rather than best-of-3 on tau2.

**Response to Q2:** Yes. Since every method is evaluated on the same (model, task, prefix) triples, we report **paired tests** on raw accuracy, which is the statistically appropriate choice here:

| Method | Mean paired gain vs. full context | Wins / Losses / Ties | Sign-test p |
|---|---|---|---|
| **AC3-Reset** | **+15.9pp** | **33 / 2 / 1** | **< 0.0001** |
| **AC3-Augment** | **+15.2pp** | 31 / 1 / 4 | **< 0.0001** |
| AC3-Gated-Reset | +17.0pp | 11 / 1 / 0 | 0.0063 |
| Assistant omission | +13.3pp | 31 / 4 / 1 | < 0.0001 |

Sample size on LiC grew from 18-25 per cell to **up to 50 problems per task across 3 prefixes** (up to 150 conversations per cell) on **3 models**. On **tau2** we now report mean +/- std over three replicates per cell rather than best-of-3 (**Common Weakness 4**).

On **WildChat**, we re-judged the entire comparison to check the judge itself, and report corrected, order-balanced figures: AC3-Reset **87.8 +/- 2.1** and AC3-Augment **91.2 +/- 2.1** over 3 seeds, against the submitted 89.8 / 92.1. The judge-agreement and position-bias analysis behind that correction is in our reply to **5YHP (W4)**; briefly, cross-family agreement is 85.9–88.8% raw (PABAK 0.79–0.83, Gwet's AC1 0.84–0.87), each of three independent judges places AC3 within 3.5pp of the others, and under a deliberately punitive "2 of 3 judges in both presentation orders" rule the win-rate is still 82.5%.

We also want to correct a metric rather than wait to be asked. Our false-negative-adjusted accuracy asks a judge, from the *visible* messages only, whether the user ever specified the task, and drops "under-specified" items from the denominator. Because context-editing arms hide content, they get more of their failures excluded — 62% for AC3-Reset against 9% for baseline on one LiC-database cell. Re-judging every arm from an identical, arm-symmetric view collapses exclusions to 2–6% uniformly and reproduces the raw ordering, but the magnitudes shrink (one cell moves from 89.0% to 77.1%). Every number in this rebuttal is therefore the **raw** one, and we are correcting the paper accordingly.

---

> **Q3:** How sensitive are the results to the analyzer model and compute budget?... A fair comparison should include equal-budget baselines, such as repeated generation, self-reflection, or a strong summarizer/condensor using the same model and number of calls. Please also report latency implications, not just API cost.

**Response to Q3:** This question had two halves and our previous response only answered one of them. We have now run both.

**Analyzer-model sensitivity.** We held the respondent model fixed (DeepSeek-V4-Flash) and varied **only** the analyzer, across five models from four families, on LiC code+database with AC3-Reset always on so the analyzer fires on every sample. Two replicate runs; n=178 matched pairs; exact McNemar against the same full-context baseline (21.3% pooled):

| Analyzer | Family | AC3-Reset | Δ vs. full context | p |
|---|---|---|---|---|
| Kimi-K2.6 | Moonshot | 61.2 +/- 2.4 | **+39.9** | 2e-17 |
| DeepSeek-V4-Flash (the paper's default) | DeepSeek | 50.0 +/- 2.4 | **+28.7** | 3e-09 |
| gpt-5.4-mini | OpenAI | 48.3 +/- 1.6 | **+27.0** | 1e-08 |
| Llama-3.3-70B-Instruct | Meta | 39.3 +/- 0.0 | **+18.0** | 6e-06 |
| gpt-4o-mini | OpenAI | 34.3 +/- 0.8 | **+12.9** | 8e-04 |

The degradation is **graceful rather than brittle**. Every analyzer is positive and individually significant; the weakest retains 32% of the reference gain and still beats full context by 12.9pp; and **no configuration falls below baseline** on either task in either replicate.

We also measured *why* it degrades gracefully, rather than assuming it. Weak analyzers **under-detect rather than mis-detect**: gpt-4o-mini declares `needs_edit` on 74.4% of turns against roughly 97% for the strong analyzers and writes issue lists 2.7x shorter, yet it parsed a `user_intent` on 100% of calls and produced a non-empty edited context on 100% of applied edits. It notices less; it does not hallucinate issues that corrupt the context. That is the property that makes a weak analyzer safe to deploy.

Two further observations we think are relevant to the generality question you raise in W3. Three of the five analyzers are non-OpenAI and they occupy the top, middle and lower rungs, interleaving with the OpenAI models; the **best** analyzer is Kimi-K2.6, 12.9pp above the paper's own default, and the **weakest** is an OpenAI model. Since the respondent here is also non-OpenAI, the best-performing configuration contains no OpenAI model anywhere. AC3 is not a gpt-specific artifact.

Limits we state ourselves: n = 40 + 49 per replicate and the intervals are a spread over N=2, not a variance estimate; adjacent rungs are not individually separated, so we defend the shape of the curve and its endpoints rather than the exact ordering; one respondent, one operator.

**Compute budget.** Our strongest evidence here remains the contagious-pollution result (Table 5), which is a direct test of the extra-compute hypothesis and refutes it: adding a second analyzer stage that is *not* structurally decontaminated drives accuracy **below** the single-pass baseline, so additional calls in the wrong information-flow configuration actively hurt.

We previously reported a matched-call-budget self-reflection control on a random math subset, where reflection reached 97.5 against AC3-Reset 97.5 and full context 90.0. We were explicit at the time that a near-ceiling task cannot discriminate between the two hypotheses, and we have now re-run the control where there is headroom. On LiC database and code, with per-component call and token metering, the budget-matched condenser **used more compute than AC3-Reset** (1.02–1.19x strategy calls, 1.62–2.14x strategy tokens) and scored **12 to 28 points below it**, and below full context in three of four cells. AC3-Gated-Reset reaches +17.8pp on **0.41x** AC3-Reset's strategy calls. Full table in **Common Weakness 5**.

**Latency.** At equal turn counts and equal concurrency, the matched-budget control adds roughly **13% wall-clock** over baseline (231s vs. 205s for the same 40 conversations). Measured per-conversation on LiC-database, AC3-Reset issues 6.2 strategy calls and AC3-Gated-Reset 2.6, against 3.1 and 6.3 for the two summariser budgets. Gated-Reset is the deployment-relevant configuration because gating skips the intervention entirely when the analyzer finds no issue.

---

> **Q4:** Please clarify what exactly is the general AC3 algorithm across benchmarks? ... Please clarify which components are essential and which are task-specific adaptations.

**Response to Q4:** One analyzer, one operator family, one knob:

| Component | Status |
|---|---|
| Two-query analyzer (spec extraction, then approach evaluation) | **Essential.** Identical across all four benchmarks |
| Structural exclusion during spec extraction | **Essential where user turns self-specify the task.** Off by design where they do not |
| Operator (Augment / Reset / Gated-Reset / Rewrite) | **The single knob.** Intensity scales with pollution level and model weakness |
| Gating | Optional |
| Memory (cheatsheet) | Optional, ablated, not load-bearing for any headline claim |

The analyzer-sensitivity sweep in Q3 is the empirical form of the "Essential" label on row 1: the same analyzer interface, swapped across four model families, produces the same qualitative behaviour and a monotone-in-strength quantitative one.

We should also make an operator-level distinction that our own new measurements force, because it bears directly on your question about what is shared and what is not. **Reset and Rewrite do genuinely different things to the context**, and we had been describing them with a single sentence. On constructed pollution, Reset removes 97.6% of an injected false span but preserves only 4.0% of an injected true span — it detects, discards the assistant side, and re-derives the specification from the user side. Rewrite sits at the opposite corner (27.0% removal, 38.9% preservation) — it is the selective operator. Both are the same analyzer with a different intervention; but "we preserve what is correct and remove what is harmful" is a claim about **Rewrite**, not about Reset, and we are correcting the paper's phrasing to attribute it. Details in our reply to **5YHP (W5)**.

The two cases you flag are the stated theory applied, not departures from it. **CollabLLM** turns structural exclusion off because our claim is that it applies when user turns independently specify the task, and CollabLLM is exactly the regime where intent is co-constructed across assistant turns; applying it there would contradict our own analysis. The **tau2** variant is the same analyzer with environment-state tracking added because the environment is stateful.

**Revision:** We will add this table, a unified algorithm statement, and the operator-level mechanism distinction to Section 3, and rename the tau2 variant so the continuity is explicit.

---

Finally, we thank the reviewer for the suggestion to **move the hard-attention ablation into the main body**. We agree and are doing so. Your reading of it as a general lesson for multi-stage LLM pipelines is exactly the framing we will adopt.
