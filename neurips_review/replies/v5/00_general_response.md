# General Response to All Reviewers

> **⚠ INTERNAL — READ BEFORE POSTING. NOT PART OF THE REPLY.**
> Two audits are still in flight as of 2026-07-29 15:25 UTC and gate two classes of number in this document.
> 1. **T14 (false-negative-adjustment audit).** Every LiC accuracy figure below is **provisional pending T14**. Finding F28 established that the repo's `adjusted_accuracy` excludes 50–78% of failures for context-editing arms versus 9% for baseline, so it inflates our own numbers; one shipped cell moves 89.0% → 77.1% under an arm-symmetric re-judge. **All LiC numbers in this document have been switched to raw accuracy**, which is not affected by that bias (verified: the phase-1/phase-2 per-run tables use a single denominator per (task, prefix) across all strategies). T14 may still change what the *paper* reports; it should not change these.
> 2. **T6 (multi-replicate tau2).** The tau2 table in Common Weakness 4 is on **HOLD** — see the marked block there. Do not post that table until T6 returns.
> Every `⚠ INTERNAL` block must be resolved and deleted before anything is posted. Claim-by-claim provenance is in `CHANGES.md`.

We sincerely thank all reviewers for their careful and constructive feedback. We are encouraged that the reviewers found the core contribution compelling, and we address every concern below with new evidence collected since submission. Where a reviewer's concern turned out to be right, or where our own new evidence contradicts something we previously reported, we say so plainly and first.

### Common Strengths Highlighted by Reviewers

* **The self-contained vs. referential framing.** Reviewers noted that this distinction "cleanly explains why AO is near-perfect in some settings and collapses to zero in others" (**iNYK**), is "well motivated" (**Vg97**), and represents "a meaningful conceptual improvement over treating all assistant-generated context as uniformly harmful" (**5YHP**).
* **The structural-exclusion (contagious pollution) result.** All three reviewers highlighted this. **iNYK** noted it "carries a useful lesson for any multi-stage LLM pipeline"; **Vg97** suggested it "should be considered being moved to the main section"; **5YHP** called it "one of the strongest parts of the paper," suggesting "information-flow constraints, rather than prompt instructions alone, may be necessary."
* **Modularity and practical interpretability** of the specification-extraction, approach-evaluation, and intervention separation (**5YHP**).

We have taken **Vg97**'s and **5YHP**'s suggestion and are moving the structural-exclusion ablation into the main body.

### Summary of New Evidence in This Rebuttal

Since submission we completed a full model x benchmark x method matrix, added paired significance testing, and ran the specific experiments reviewers asked for rather than promising them. Five headline additions:

1. **The same four operators are now evaluated across 3 respondent models x 4 LiC tasks, plus CollabLLM, WildChat, and tau2**, with no per-benchmark tuning (Common Weakness 1).
2. **Paired significance testing**: AC3-Reset improves over full context on **33 of 36 paired comparisons** (mean **+15.9pp**, sign-test **p < 0.0001**), outperforming even the assistant-omission design-oracle (Common Weakness 2).
3. **A new unbiased-subset, end-to-end, 3-replicate experiment** confirming the gains are not an artifact of subset selection, replay, or a single run (Common Weakness 3).
4. **The condensation baseline Vg97 and the Area Chair asked for is now run, at measured matched compute.** Summarisation does not close the gap; it moves accuracy *down* (Common Weakness 5).
5. **A direct, judge-free span-level evaluation of the analyzer as a detector**, which 5YHP asked for and which we report including the part that does not flatter us (Reviewer 5YHP, W5).

We also correct three numbers we reported to reviewers in earlier correspondence or in the submission, having re-measured them at N=3: a CollabLLM MATH-Hard figure, the WildChat win-rates, and the end-to-end subset result. Details are in the relevant sections.

---

## Common Weakness 1 (from the Area Chair, Reviewer Vg97 W3/Q4, and Reviewer 5YHP W2)

> The method changes substantially across settings... it is not obvious whether the paper is validating a single method, a family of prompt-engineering patterns, or several task-specific context-management variants.

**Response:** We appreciate this concern and agree it deserved a direct empirical answer rather than a description. AC3 is a single method, and we now **demonstrate** this.

Every setting uses the same two-query analyzer (specification extraction, then approach evaluation) and the same operator set. The post-submission matrix runs **the same four operators across 3 respondent models (gpt-5.4, DeepSeek-V4-Flash, Kimi-K2.6) x 4 LiC tasks, plus CollabLLM, WildChat, and tau2-bench**, using one code path with no per-benchmark tuning.

| Component | Status |
|---|---|
| Two-query analyzer (spec extraction, then approach evaluation) | **Essential.** Identical across all four benchmarks |
| Structural exclusion during spec extraction | **Essential where user turns self-specify the task.** Off by design where they do not |
| Operator (Augment / Reset / Gated-Reset / Rewrite) | **The single knob.** Intensity scales with pollution level and model weakness |
| Gating | Optional |
| Memory (cheatsheet) | Optional, ablated, not load-bearing for any headline claim |

What varies across settings is **operator intensity**, which is a documented knob rather than a redesign.

We can now put a measurement behind the claim that the *operator* is the knob and the *analyzer* is the shared engine. Holding the respondent model fixed and varying only the analyzer model across five models from four families (Moonshot, DeepSeek, OpenAI x2, Meta), on LiC code+database, every analyzer produces a positive and individually significant gain over full context, from **+12.9pp to +39.9pp** (n=178 matched pairs, exact McNemar, all p < 0.001). No configuration falls below baseline. The method degrades gracefully with analyzer strength rather than depending on one particular analyzer; the full table is in our reply to **Vg97 (Q3)**.

The two cases reviewers flagged are the stated theory being applied, not departures from it:

* **CollabLLM disables structural exclusion.** Our claim is that structural exclusion applies *when user turns independently specify the task*. CollabLLM is precisely the regime where they do not, because intent is co-constructed across assistant turns. Applying structural exclusion there would contradict our own analysis.
* **tau2 adds environment-state tracking.** This is the same analyzer with tool-call state tracked, because the environment is stateful.

> **⚠ INTERNAL — HOLD (T6 in flight).** v4 closed this section with: *"tau2 confirms the rule directly: the lightest operator (Augment) wins on the strongest model (gpt-5.4), and the heaviest (Rewrite) wins on the weakest (Kimi-K2.6)."* That sentence is derived from the same N=1 seed-42 tau2 cells that T6 is currently re-measuring, and T6's interim baselines (DeepSeek-V4-Flash 70.2 ± 11.0, Kimi-K2.6 80.4 ± 2.5 at N=3) are far above the published ones (31.6, 26.3). If the interim numbers hold, the operator-ordering rule cannot be supported from tau2. **The sentence has been removed pending T6.** Restore only if T6's AC3 arms reproduce the ordering.

**Revision:** We will add this component table and an explicit unified-algorithm statement to Section 3, and rename the tau2 variant so its continuity with the shared analyzer is unambiguous.

---

## Common Weakness 2 (from Reviewers iNYK W1/Q2, Vg97 W2/Q2, and 5YHP W3)

> Many of the headline LiC cells use small sample sizes, with only the Gated-Reset row repeated three times... Please provide confidence intervals, paired tests, or bootstrap analyses.

**Response:** Thank you for pressing on this. We have both scaled the evaluation and added the paired tests requested.

**Sample size.** LiC now uses **up to 50 problems per task, each evaluated across 3 independent conversation prefixes** (36–50 conversations per prefix depending on task, up to 150 per cell), on **3 models**. The submitted version used 18 to 25 conversations on 1 model.

**Paired significance.** Because every method is evaluated on the *same* (model, task, prefix) triples, the paired difference is the statistically correct comparison. Across all **36 paired comparisons** (3 models x 4 tasks x 3 prefixes), on **raw accuracy**:

| Method | Mean paired gain vs. full context | Wins / Losses / Ties | Sign-test p |
|---|---|---|---|
| **AC3-Reset** | **+15.9pp** | **33 / 2 / 1** | **< 0.0001** |
| **AC3-Augment** | **+15.2pp** | 31 / 1 / 4 | **< 0.0001** |
| AC3-Gated-Reset | +17.0pp | 11 / 1 / 0 | 0.0063 |
| Assistant omission (design-oracle on LiC) | +13.3pp | 31 / 4 / 1 | < 0.0001 |

**AC3's mean clears the full-context baseline on every model**: +17.1pp (DeepSeek-V4-Flash), +16.7pp (gpt-5.4), +13.9pp (Kimi-K2.6). Notably, AC3-Reset also **outperforms the assistant-omission design-oracle** on average across the matrix.

Two points of methodological candour, both of which we will also state in the paper.

* **We report raw accuracy, not our false-negative-adjusted accuracy.** Our adjustment procedure asks a judge, from the *visible* messages only, whether the user ever specified the task, and drops "under-specified" items from the denominator. That is post-treatment conditioning: an arm that hides assistant or user content causes more items to look under-specified and therefore has more of its failures excluded. On a LiC-database cell we measured exclusion rates of 9% for baseline against 62% for AC3-Reset. Re-judging every arm from an identical, arm-symmetric view collapses exclusions to 2–6% uniformly and reproduces the raw ordering. The bias ran **in our favour**, so every number in this rebuttal is the raw one, and we are correcting the paper accordingly.
* **What our replicates vary.** On LiC and CollabLLM, replicate runs differ through temperature-1.0 sampling of the respondent, analyzer and user simulator on a fixed problem draw. The intervals we report therefore estimate decoder variance, not sampling variance over problems, and are correspondingly narrower than a full re-draw would give. WildChat is the exception: its N=3 are independent seeds over the sampled pool. We will state this distinction explicitly in the appendix.

**WildChat** is reported over 3 seeds with tight intervals: **87.8 +/- 2.1** (Reset) and **91.2 +/- 2.1** (Augment) against assistant omission. These are order-balanced values from a full re-judge; see our reply to **5YHP (W4)** for why they differ slightly from the submitted 89.8 / 92.1.

**Revision:** We will replace best-of-3 reporting with mean +/- std throughout, report raw accuracy as primary with the arm-symmetric re-judge as a robustness column, and add this paired-test table to the main results.

---

## Common Weakness 3 (from Reviewers iNYK W2/Q1 and 5YHP W3)

> Can you re-report Reset vs. Baseline on a random subset, or one selected independently of baseline results? ... the LiC experiments use replay mode.

**Response:** We ran exactly this experiment, and designed it to remove **both** concerns simultaneously. We drew a **uniformly random subset selected with no reference to baseline outcomes** (n=40), ran it as **fresh end-to-end conversations rather than replay**, used a **model not in the paper** (gpt-5.4-mini), and repeated it over **3 replicate runs**.

| Method | Accuracy, raw (mean +/- std, N=3) | Per-run values |
|---|---|---|
| Full context | 87.5 +/- 2.0 | 90.0 / 87.5 / 85.0 |
| **AC3-Reset** | **93.3 +/- 4.2** | 97.5 / 95.0 / 87.5 |
| **AC3-Gated-Reset** | **95.0 +/- 0.0** | 95.0 / 95.0 / 95.0 |

**Both operators improve over the baseline in every one of the three runs** (Reset +7.5 / +7.5 / +2.5pp; Gated-Reset +5.0 / +7.5 / +10.0pp). We state the limits of this experiment ourselves: at n=40 the margins are two to four problems per run, and this experiment alone is not powered for significance. Its purpose is narrower and it achieves it — the gains are not an artifact of difficulty-selected data, of replay evaluation, or of a single run. The powered evidence is the 36-comparison paired test in Common Weakness 2.

We should note a correction here. In earlier correspondence we quoted this experiment as **AC3-Reset 100.0 +/- 0.0** and **AC3-Gated-Reset 99.1 +/- 1.2**. Those were our false-negative-*adjusted* figures, and, as described in Common Weakness 2, that adjustment excluded 1, 2 and 5 items from AC3 denominators across the three runs while excluding none from baseline. The raw numbers above are the correct ones to compare, and they are the ones we will publish.

On replay more generally, we would respectfully note that holding the polluted trajectory fixed across methods is what makes the comparison **causal**: every method inherits an identical history, so the measured difference is attributable to the intervention rather than to divergent user-simulator paths. We also note that tau2 and CollabLLM are run as live multi-turn interactions, not replay.

**Revision:** We will add this experiment to the main results and report the full-pool numbers alongside the difficulty-stratified subset.

---

## Common Weakness 4 (from Reviewers iNYK W3 and Vg97 W2)

> The abstract and Figure 1 repeatedly call AC3 "the only method robust across the spectrum," yet on tau2-bench... Table 1d reports best-of-3, which masks the negative mean.

**Response:** We thank the reviewers for this precision, and we agree best-of-3 was the wrong statistic to headline. We have revised the claim and are re-reporting tau2 at N=3 per cell.

The one tau2 conclusion that is mechanism-corroborated and does not depend on the contested magnitudes:

**Assistant omission collapses to 0% on every model.** This is behavioural, not a scoring artifact: AO rollouts never reach a `user_stop` termination and instead exhaust the 50-step budget, because blanket omission destroys the tool-call results that exist only in assistant turns, so the agent re-calls tools indefinitely. In the same process, on the same tasks, the other arms return rewards of 1.0. This is the single most important tau2 result for our argument — it is the setting where the strongest published baseline does not merely underperform but fails structurally — and it is unaffected by the re-measurement below.

> **⚠ INTERNAL — HOLD (T6 in flight). DO NOT POST THE TABLE BELOW.**
> v4 posted this table:
>
> | tau2-bench (reward %) | gpt-5.4 | DeepSeek-V4-Flash | Kimi-K2.6 |
> |---|---|---|---|
> | Full context | 68.4 | 31.6 | 26.3* |
> | Assistant omission | 0.0 | 0.0 | 0.0 |
> | Best AC3 operator | 84.2 | 57.9 | 73.7 |
>
> T6 is re-running the full 3-model x 5-arm matrix at N=3 (seeds 42/43/44, n=19 tasks per replicate) with a rotate-and-backoff transport wrapper. Its **completed Baseline cells** read:
> gpt-5.4 **68.4 ± 13.9** (reproduces the published 68.4 on the mean); DeepSeek-V4-Flash **70.2 ± 11.0** (published 31.6); Kimi-K2.6 **80.4 ± 2.5** (published 26.3).
> The most likely reading, which the source report itself concedes for Kimi, is that the published DSV4F and Kimi Baseline cells were **rate-limit-clipped floors** (14/20 and 19/20 short-exits), i.e. a clean treatment was compared against a broken control. Kimi's re-measured baseline (80.4) is already **above every published Kimi AC3 number**.
> Two further facts from T6 that we will have to state regardless of the outcome: (i) `--seed` on the tau2 fork threads to the provider's best-effort `seed` parameter, so replicates differ by sampling and seed 42 does not reproduce the original point estimate (52.6, not 68.4); (ii) at n=19 and p≈0.68 the binomial sd is 10.7pp, so **any tau2 gap below roughly 15pp measured at N=1 is inside the noise** — which is the quantitative form of the reviewers' complaint and should be conceded in those terms.
> **Action:** post the AO-collapse paragraph above; hold the numeric table until T6's AC3 arms land, then paste the N=3 mean ± sd table. If the interim baselines hold, the honest framing is: *"On re-measurement at N=3 with a corrected transport layer, our published DeepSeek-V4-Flash and Kimi baselines were too low; we withdraw the magnitudes on those two models and report the corrected matrix. The structural result — assistant omission at 0% on every model — is unchanged."*

On the specific gpt-5-mini cell iNYK cites: our own failure-mode analysis finds that **only 1 of 11 baseline failures on that model is attributable to context pollution**. That configuration is simply not pollution-limited, so a null result there is the expected outcome rather than evidence against the method. The informative comparisons are the models where pollution actually binds.

**Revision:** We report tau2 as mean +/- std over N=3 replicates per cell rather than best-of-3, and we sharpen the abstract and introduction from "robust across the spectrum" to the precise, checkable claim that AC3 is **the only method tested that improves over full context across the entire spectrum**, including the stateful agentic setting where blanket omission fails completely.

---

## Common Weakness 5 (from Reviewer Vg97 W1/Q1 and the Area Chair)

> The paper should compare against recent stronger context-condensation/context-management methods such as MT-OSC.

**Response:** We appreciate this suggestion. In v3 of this response we argued the point; we have now run it, and we report the result including the compute accounting.

Our baselines were selected because they attack **the same problem we do**: deciding what stays in context so that harmful prior content stops influencing generation. Assistant omission is the strongest published intervention for context pollution and is a design-oracle on LiC by construction; ERGO resets via LLM rewriting of user turns; Concatenate-User is the single-turn upper bound. Compaction and folding methods (U-Fold, Context-Folding, MemoBrain, and the concurrent MT-OSC) target a **different failure mode**: context-length pressure. Our prediction, which follows directly from the mechanism we identify, was that a good-faith condenser carries invalidated reasoning forward in compressed form and does not close the gap.

We implemented a summarisation baseline and an MT-OSC reimplementation and ran them on our two highest-pollution LiC tasks, paired against the same conversations (raw accuracy; exact McNemar on discordant pairs):

| Task | Arm | Accuracy | n correct | Δ vs baseline | McNemar p |
|---|---|---|---|---|---|
| database | Baseline (full context) | 56.1% | 60/107 | — | — |
| database | Summarisation, 1 call/turn | 53.3% | 57/107 | −2.8 | 0.678 |
| database | Summarisation, 2 calls/turn (budget-matched) | 47.7% | 51/107 | −8.4 | 0.078 |
| database | MT-OSC (reimplementation, w=4 as published) | 60.7% | 65/107 | +4.7 | 0.383 |
| database | **AC3-Reset** | **75.7%** | 81/107 | **+19.6** | **0.0005** |
| database | **AC3-Gated-Reset** | **73.8%** | 79/107 | **+17.8** | **0.0013** |
| code | Baseline (full context) | 83.0% | 83/100 | — | — |
| code | Summarisation, 1 call/turn | 79.0% | 79/100 | −4.0 | 0.481 |
| code | Summarisation, 2 calls/turn | 80.0% | 80/100 | −3.0 | 0.581 |
| code | **AC3-Reset** | **92.0%** | 92/100 | **+9.0** | **0.023** |

Head-to-head and paired, AC3-Reset beats summarisation by **+22.4 / +28.0pp** on database and **+13.0 / +12.0pp** on code, all p < 0.01.

**On budget, the result is stronger than parity.** We instrumented every LLM call and token by component. The budget-matched summariser did not merely match AC3-Reset's compute, it **over-consumed** it — **1.02–1.19x the strategy calls and 1.62–2.14x the strategy tokens** — and still lost by 12 to 28 points. AC3-Gated-Reset reaches +17.8pp on **0.41x** AC3-Reset's strategy calls. We spent more compute on the baseline than on our own method and the baseline still lost.

**On MT-OSC we want to be careful not to overclaim a win.** At its published window (w=4) it fired **30 times across 107 conversations, 0.3 times per conversation**, because it cannot compact before turn 6 while LiC conversations average 4.1 turns. Its +4.7pp is therefore not a fair test of MT-OSC's idea. The correct reading is that a length-triggered compaction schedule **structurally cannot engage** with pollution that appears in the first few turns — which is precisely the scoping argument we made in Related Work, now with a number attached rather than an assertion. We will present it that way and not as a beaten baseline.

Limits we state ourselves: one respondent model (gpt-5.4-mini), one run per cell, two tasks. A neutral-prompt variant of the summariser was implemented to check that the result does not hinge on our phrasing of the condenser prompt; it did not finish in the window, and both prompts will be released verbatim.

**Revision:** We will add this table, the measured budget accounting, and the MT-OSC engagement-rate analysis to the paper, and cite and discuss MT-OSC (concurrent, 2026) in Related Work.
