# Response to Reviewer Vg97

We thank the reviewer for a thorough and constructive review, and for the specific pointer to MT-OSC. Both halves of Q3 — analyzer sensitivity and compute budget — are now answered with completed experiments rather than with promises, and Q1's baseline is now run. We address each weakness and question below.

## Response to Weaknesses

> **W1:** The central weakness is the set of baselines in the experiment... the paper should compare against recent stronger context-condensation/context-management methods such as MT-OSC.

**Response to W1:** We have now run the condensation baseline rather than argued for its exclusion. Please see **Common Weakness 5** in the General Response, and Q1 below.

Since baselines are your central concern, we should also flag a correction we found in how one of our *existing* baselines was scored, because it runs against that baseline rather than for it. **ERGO — and only ERGO — was evaluated on unfiltered conversation pools** in our main LiC table, so it was charged with items no other method was asked to attempt. On the corrected pools **ERGO/math moves from 69.6 to 80.0, above AC3-Reset (75.0) and level with AC3-Gated-Reset (80.0)**; code is essentially unchanged at ≈44.0 and database is untouched at 12.0. Paired exact sign tests on the same items then show that **no ERGO-vs-AC3 difference in that table is significant at n ≈ 20 in either direction** (code p = 0.375, math p = 1.00) — which is also, we think, the correct reading of your W2. The full disclosure, including what the correction does not touch, is in **Common Weakness 5**.

---

> **W2:** Another concern is the statistical reliability. Many of the headline LiC cells use small sample sizes, with only the Gated-Reset row repeated three times... The tau2-bench result is also not very persuasive as currently presented.

**Response to W2:** Please see **Common Weakness 2** (scaled evaluation, paired tests, and the problem-clustered confidence intervals you asked for) and **Common Weakness 4** (tau2).

On tau2 in particular, you were more right than we realised, and the answer is a withdrawal rather than a re-report. We re-ran the entire published tau2 matrix at N=3 (3 models x 5 arms x 3 replicate runs x 19 tasks, 855 scored rollouts) and **two of our three published baselines do not replicate** — DeepSeek-V4-Flash 31.6 → **70.2 ± 11.0**, Kimi-K2.6 26.3 → **78.9 ± 0.0**. On all three models the re-measured full-context baseline is at or above every AC3 arm, so **we withdraw the tau2 improvement claim**: we had compared a clean treatment against a control our own logs show was rate-limit-clipped. Your instinct about the noise floor was also correct and we can now put a number on it — at n=19 tasks a single cell has a binomial standard deviation of about **10.7pp**, and our N=3 baseline re-measurement returns **±13.9pp**, so any tau2 difference below roughly 15pp measured at N=1 was never resolvable. The one tau2 result that survives, and reproduces exactly, is structural: **assistant omission is 0.0% in all nine cells / 171 rollouts**, because omission destroys tool-call results that exist only in assistant turns. Full accounting, including a gpt-5.4 AC3 collapse we could not explain, is in **Common Weakness 4**.

---

> **W3:** A third concern is that the method changes substantially across settings... it is not obvious whether the paper is validating a single method, a family of prompt-engineering patterns, or several task-specific context-management variants.

**Response to W3:** Please see **Common Weakness 1**, where we now demonstrate that the same four operators run across 3 models x 4 LiC tasks plus CollabLLM, WildChat, and tau2 with no per-benchmark tuning. Q3 and Q4 below add the component-level and analyzer-level breakdowns you requested.

## Response to Questions

> **Q1:** Can the authors compare against stronger context-management baselines as described in the weakness section? Otherwise, the authors should be able to clearly justify why the stronger baselines cannot be adapted.

**Response to Q1:** We have run it. The result is in **Common Weakness 5**; we summarise the three things we think you will most want to check.

**Summarisation does not close the gap — it moves accuracy down.** On our two highest-pollution LiC tasks, run on the **complete, unselected** LiC pool (n=107 database / 100 code, full end-to-end simulation rather than replay) and paired against identical conversations: on database, summarisation at 1 call/turn is **−2.8pp** and at 2 calls/turn is **−8.4pp** against full context, while AC3-Reset is **+19.6pp** (p = 0.0005); on code, summarisation is **−4.0 / −3.0pp** while AC3-Reset is **+9.0pp** (p = 0.023). Head-to-head and paired, AC3-Reset beats summarisation by +22.4 / +28.0pp on database and +13.0 / +12.0pp on code, all p < 0.01. This is the mechanism prediction we made in Related Work behaving as predicted: a good-faith condenser preserves invalidated reasoning in compressed form.

**The budget comparison came out better than parity.** We instrumented every LLM call and token per component. The budget-matched summariser **over-consumed** AC3-Reset — 1.02–1.19x its strategy calls and 1.62–2.14x its strategy tokens — and still lost by 12 to 28 points.

**On MT-OSC we decline to claim a win, and we ran the follow-up you would be entitled to ask for.** Our reimplementation at the published window (w=4) improves database by +4.7pp (p = 0.383), but it fired only **30 times across 107 conversations, 0.3 per conversation**, because it cannot compact before turn 6 and LiC conversations average 4.1 turns. That is not a fair test of MT-OSC's idea — and the obvious reply is "then scale the window to the conversation length and re-report". **We did.** At w = 2, the smallest window in MT-OSC's own published sweep, it engages properly (**5.7 compaction events per conversation against 0.6 at w = 4**) and accuracy goes **down**: 47.7% against full context's 56.1% and against its own w=4 run's 60.7%, a paired **−13.1pp** (22 losses to 8, p = 0.016); AC3-Reset leads the engaged configuration by **+28.0pp** (37/7, p < 0.0001). So the scoping claim does not rest on a hyperparameter that happened to disable the competitor: when length-triggered compaction actually engages with a short, polluted conversation, it compresses the invalidated reasoning rather than removing it — the same mechanism the summariser arms show — and at w=4 it looks mildly positive precisely because it is nearly a no-op. We will report it in exactly those terms, cite MT-OSC as concurrent work (2026), and release both condenser prompts verbatim. These are single runs of our own reimplementation of a method with no code release, and we label them as such.

**On the second baseline you named, U-Fold on tau2, we should be direct: we did not manage an adaptation within the window, and we would rather say so than let the omission pass.** Our reason for expecting it to behave like the compaction family is the engagement argument above, which we can now *measure* for MT-OSC rather than assert — a folding schedule keyed to context length engages late, and when we force it to engage early it compresses pollution rather than removing it. We do not claim that settles U-Fold. If you consider it decisive we will run it during the discussion period and report it whichever way it comes out; we are asking which you would prefer given the remaining time.

**On the condenser prompt, which we wrote ourselves, we ran the fairness control and it comes out against our own prompt having mattered.** Our prompt contains the clause *"your job is compression, not evaluation — preserve the assistant's current approach and conclusions as they stand"*, which could reasonably be read as forbidding the baseline from doing the useful thing. We therefore ran a **neutral-prompt variant with that clause deleted** — a bare "summarize the conversation so far". On LiC-database (n = 107 paired, raw) it scores **51.4% against full context's 56.1%** (−4.7pp, p = 0.44), which lands **between two replicate runs of our own prompt** (53.3% and 47.7%); the two prompts differ by less than two runs of the same prompt differ from each other (−1.9pp, p = 0.83 and +3.7pp, p = 0.54). AC3's margin is unchanged: **+24.3pp for AC3-Reset and +22.4pp for AC3-Gated-Reset** against the neutral prompt (31/5 and 30/6, p ≤ 0.0001). We can also say *why* the phrasing does not matter: across all 1,017 condenser summaries in these runs, the condenser flags an error in the assistant's work **zero times out of 340 under the neutral prompt** — exactly as often as under our prohibition (0/336 and 0/341). Removing the clause does not make a summariser start auditing; it only makes its summaries shorter (1,068 characters against 1,945). It is a lexical probe, so we state its limit: it would miss a purely paraphrastic critique, and as a check on the probe the same pattern fires on 26.4% of AC3's analyzer outputs and 0% of baseline assistant turns.

One further note, because the ordering in the two budget rows is tempting to read as a mechanism and we do not think it survives. The condenser scores −2.8pp at one call per turn and −8.4pp at two; a second run of the **one-call** arm scores **−8.4pp, exactly the two-call value**, and the two one-call replicates differ by more than one call differs from two (p = 0.29, p = 0.26). At n = 107 this cell carries roughly **±6pp** of run-to-run variation, so we claim only that **summarisation is neutral-to-negative at either budget, not catastrophic** — and note that AC3's +22 to +28pp advantage is four to five times that noise floor.

One comparability note, since this experiment's absolute accuracies are far above Table 1's: it runs on the complete unselected pool with a newer respondent and end-to-end rather than replay, so the absolute levels are not comparable to Table 1 and the paired Δ is the quantity to read. That does not make it an easy setting — the measured single-turn ceiling on this pool is 94.4% (database) and 98.0% (code), so the multi-turn gap is still 38.3pp and 15.0pp, and AC3-Reset closes 51% and 60% of it, the same fraction it closes on Table 1's much harder subset. Full accounting in **Common Weakness 5**.

Limits we state ourselves: one respondent model, two tasks, and one run per cell except the 1-call condenser, which we ran twice — that replicate is where the ±6pp noise floor above comes from.

---

> **Q2:** Can the authors report statistically sound results for the main claims? Please provide confidence intervals, paired tests, or bootstrap analyses for LiC and WildChat, and report mean ± variance rather than best-of-3 on tau2.

**Response to Q2:** Yes. Since every method is evaluated on the same (model, task, prefix) triples, we report **paired tests** on raw accuracy, which is the statistically appropriate choice here:

| Method | Mean paired gain vs. full context | Wins / Losses / Ties | Sign-test p |
|---|---|---|---|
| **AC3-Reset** | **+15.9pp** | **33 / 2 / 1** | **< 0.0001** |
| **AC3-Augment** | **+15.2pp** | 31 / 1 / 4 | **< 0.0001** |
| AC3-Gated-Reset† | +17.0pp | 11 / 1 / 0 | 0.0063 |
| AC3-Rewrite† | −0.3pp | 6 / 6 / 0 | 1.00 |
| Assistant omission | +13.3pp | 31 / 4 / 1 | < 0.0001 |

† These two rows cover 12 of the 36 triples, on one respondent model, which is why their counts do not sum to 36. We print the AC3-Rewrite row for completeness even though it is our worst — its cells predate the analyzer-parity fix and we do not claim Rewrite improves LiC accuracy; its evidence is on referential settings. See Common Weakness 2 for the full footnote and for where AC3 does and does not separate from assistant omission.

You asked for confidence intervals and bootstrap analyses specifically, and the table above supplies neither: a sign test over cells is assumption-light but it discards effect size and treats 36 correlated cells as independent. We therefore also report the same comparisons at the level of **individual problems**, on n = **1,668** paired items (after dropping conversations that errored in any arm, so every arm is scored on identical items):

| Method | Item-level exact McNemar | Problem-clustered bootstrap, mean paired gain |
|---|---|---|
| **AC3-Reset** | 350 wins / 93 losses, **p < 1e−30** | **+15.4pp, 95% CI [+11.5, +19.4]** |
| **AC3-Augment** | 323 / 79, p < 1e−30 | +14.6pp, [+10.8, +18.6] |
| AC3-Gated-Reset† | 126 / 33, p = 5e−14 | +16.8pp, [+11.6, +22.0] |
| AC3-Rewrite† | 42 / 42, p = 1.00 | **+0.0pp, [−3.8, +3.8]** |
| Assistant omission | 297 / 87, p < 1e−28 | +12.6pp, [+9.2, +16.1] |

The bootstrap resamples whole **problems** (191 of them, each contributing up to 3 prefixes x 3 models), which is the correlation structure the sign test ignores; we treat it as the primary interval and keep the sign test as the assumption-light cross-check. All three statistics agree. It also sharpens the row we like least: at the item level AC3-Rewrite is not mildly negative but **exactly neutral on LiC, bounded within ±4pp**, which is the honest version of the −0.3pp above. We apply the same interval to the comparison against assistant omission and report the answer it gives rather than the one we would prefer — matrix-wide AC3-Reset is **+2.8pp, 95% CI [−0.3, +5.9]**, not distinguishable from zero, while on LiC-database alone it is **+18.6pp, 95% CI [+10.7, +26.6]**. We do not claim the former.

The same treatment is applied to the end-to-end n=40 experiment in **Common Weakness 3**, whose `95.0 +/- 0.0` cell would otherwise invite the obvious question: a problem-clustered bootstrap there gives AC3-Gated-Reset **+7.5pp [+1.7, +15.0]** (p = 0.023) and AC3-Reset **+5.8pp [+0.0, +12.5]** (p = 0.119) against full context, and we report both, including the one that does not reach significance.

Sample size on LiC grew from 18-25 per cell to **up to 50 problems per task across 3 prefixes** (up to 150 conversations per cell) on **3 models**. On **tau2** we now report mean +/- std over three replicate runs per cell rather than best-of-3 — and, as **Common Weakness 4** sets out, that re-measurement made us **withdraw the tau2 improvement claim** rather than restate it.

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

**Latency.** You asked for AC3's latency, and our earlier answer gave the control's. Here is ours. On the LiC-database runs behind the table in **Common Weakness 5** — the same 107 conversations, the same machine, arms run back-to-back at identical concurrency — end-to-end wall-clock is:

| Arm | Wall-clock (107 conversations) | vs. full context | Avg. turns | Seconds per turn |
|---|---|---|---|---|
| Full context | 578 s | — | 4.1 | 1.30 |
| MT-OSC (w=4) | 587 s | +2% | 4.3 | 1.27 |
| **AC3-Gated-Reset** | **781 s** | **+35%** | 5.3 | **1.38** |
| Summarisation, 1 call/turn | 835 s | +44% | 7.3 | 1.07 |
| **AC3-Reset** | **1,051 s** | **+82%** | 6.9 | **1.43** |
| Summarisation, 2 calls/turn (budget-matched) | 1,214 s | +110% | 7.3 | 1.55 |

We should not present the +82% as smaller than it is: end-to-end, always-on Reset takes nearly twice as long as full context on this benchmark, and that is a real deployment cost. But the decomposition matters, so we give it. Most of the difference is **turn inflation** rather than per-turn slowdown — a decontaminated assistant asks the clarifying questions the polluted one skipped, so conversations run 6.9 turns instead of 4.1. **Per turn**, AC3-Reset adds **9%** over full context and AC3-Gated-Reset **5%**, while the budget-matched summariser adds **19%** per turn and scores 28 points lower. Gating is the lever: **+17.8pp of the +19.6pp at 0.41× the strategy calls and less than half the added wall-clock**, which is why we recommend always-on Reset only where an intervention is cheap and Gated-Reset where it is not. On the earlier n=40 LiC-math control, the same picture at a near-ceiling task: full context 205 s, matched-budget self-reflection 231 s (+13%), AC3-Gated-Reset 266 s (+30%), AC3-Reset 547 s (+167%) — again driven by turns (8.5 vs. 5.2). These are single runs and the timings include process start-up and offline scoring, so we quote them to two significant figures and would re-measure with per-call timing for the camera-ready. Per conversation, AC3-Reset issues 6.2 strategy calls and AC3-Gated-Reset 2.6, against 3.1 and 6.3 for the two summariser budgets.

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

We should also correct an operator-level description that our own new measurements force, because it bears directly on your question about what is shared and what is not. We had been describing AC3 as *preserving what is correct and removing what is harmful* — a selective-editing claim. We ran two studies to test it, and neither supports it.

* On **constructed** pollution (one known-false and one known-true span injected per conversation), AC3-Reset removes 97.6% of the false span but preserves only 4.0% of the true one, an edit precision of 50.4% against a 50% chance baseline. AC3-Rewrite looked like the exception at that stage (27.0% removal, 38.9% preservation).
* On **naturally occurring** spans, measured causally with no detector and no judge anywhere in the label path — 111 spans in 30 conversations, each re-run 14× present and 12× removed — **neither operator is selective**. Reset keeps 5 of 66 probe-admissible spans, Rewrite keeps **0 of 66**; preservation on causally useful spans is 0% for both; edit precision is 63.6% for both, exactly the base rate. Rewrite's apparent selectivity on the constructed spans was an artifact of their form: a short, self-contained injected sentence can be carried across verbatim by a compacting operator, whereas the model's own verbose prose and code get paraphrased and nothing distinctive survives.

So the honest mechanism statement is the **same** for Reset and Rewrite, and it is not the one in the paper: AC3 **detects, discards the assistant side, and rebuilds the specification from the user side** — Reset by dropping that side, Rewrite by recompacting it — rather than excising harmful content span by span. The two operators differ in *how much* they rebuild, not in whether they are selective, which keeps the operator a knob rather than a second method. We are removing the "preserve what is correct" framing from the paper rather than re-attributing it. What the same studies *do* support is that the analyzer detects (it names the injected pollutant in 78.6% of conversations) and that AC3 removes **100%** of the natural spans a counterfactual ablation proves causally harmful. Details in our reply to **5YHP (W5)**.

The two cases you flag are the stated theory applied, not departures from it. **CollabLLM** turns structural exclusion off because our claim is that it applies when user turns independently specify the task, and CollabLLM is exactly the regime where intent is co-constructed across assistant turns; applying it there would contradict our own analysis. The **tau2** variant is the same analyzer with environment-state tracking added because the environment is stateful.

**Revision:** We will add this table, a unified algorithm statement, and the corrected per-operator mechanism statement to Section 3, remove the "preserve what is correct" framing from the abstract and introduction, and rename the tau2 variant so the continuity is explicit.

---

Finally, we thank the reviewer for the suggestion to **move the hard-attention ablation into the main body**. We agree and are doing so. Your reading of it as a general lesson for multi-stage LLM pipelines is exactly the framing we will adopt.
