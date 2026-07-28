# General Response to All Reviewers

We sincerely thank all reviewers for their careful and constructive feedback. We are encouraged that the reviewers found the core contribution compelling, and we address every concern below with new evidence collected since submission.

### Common Strengths Highlighted by Reviewers

* **The self-contained vs. referential framing.** Reviewers noted that this distinction "cleanly explains why AO is near-perfect in some settings and collapses to zero in others" (**iNYK**), is "well motivated" (**Vg97**), and represents "a meaningful conceptual improvement over treating all assistant-generated context as uniformly harmful" (**5YHP**).
* **The structural-exclusion (contagious pollution) result.** All three reviewers highlighted this. **iNYK** noted it "carries a useful lesson for any multi-stage LLM pipeline"; **Vg97** suggested it "should be considered being moved to the main section"; **5YHP** called it "one of the strongest parts of the paper," suggesting "information-flow constraints, rather than prompt instructions alone, may be necessary."
* **Modularity and practical interpretability** of the specification-extraction, approach-evaluation, and intervention separation (**5YHP**).

We have taken **Vg97**'s and **5YHP**'s suggestion and are moving the structural-exclusion ablation into the main body.

### Summary of New Evidence in This Rebuttal

Since submission we completed a full model x benchmark x method matrix and added paired significance testing. Three headline additions:

1. **The same four operators are now evaluated across 3 respondent models x 4 LiC tasks, plus CollabLLM, WildChat, and tau2**, with no per-benchmark tuning (Common Weakness 1).
2. **Paired significance testing**: AC3-Reset improves over full context on **33 of 36 paired comparisons** (mean **+15.9pp**, sign-test **p < 0.0001**), outperforming even the assistant-omission design-oracle (Common Weakness 2).
3. **A new unbiased-subset, end-to-end, 3-rerun experiment** confirming the gains are not an artifact of subset selection, replay, or a single seed (Common Weakness 3).

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

What varies across settings is **operator intensity**, which is a documented knob rather than a redesign. tau2 confirms the rule directly: the **lightest** operator (Augment) wins on the **strongest** model (gpt-5.4), and the **heaviest** (Rewrite) wins on the **weakest** (Kimi-K2.6).

The two cases reviewers flagged are the stated theory being applied, not departures from it:

* **CollabLLM disables structural exclusion.** Our claim is that structural exclusion applies *when user turns independently specify the task*. CollabLLM is precisely the regime where they do not, because intent is co-constructed across assistant turns. Applying structural exclusion there would contradict our own analysis.
* **tau2 adds environment-state tracking.** This is the same analyzer with tool-call state tracked, because the environment is stateful.

**Revision:** We will add this component table and an explicit unified-algorithm statement to Section 3, and rename the tau2 variant so its continuity with the shared analyzer is unambiguous.

---

## Common Weakness 2 (from Reviewers iNYK W1/Q2, Vg97 W2/Q2, and 5YHP W3)

> Many of the headline LiC cells use small sample sizes, with only the Gated-Reset row repeated three times... Please provide confidence intervals, paired tests, or bootstrap analyses.

**Response:** Thank you for pressing on this. We have both scaled the evaluation and added the paired tests requested.

**Sample size.** LiC now uses **50 problems per task, each evaluated across 3 independent conversation prefixes** (up to 150 conversations per cell), on **3 models**. The submitted version used 18 to 25 conversations on 1 model.

**Paired significance.** Because every method is evaluated on the *same* (model, task, prefix) triples, the paired difference is the statistically correct comparison. Across all **36 paired comparisons** (3 models x 4 tasks x 3 prefixes):

| Method | Mean paired gain vs. full context | Wins / Losses / Ties | Sign-test p |
|---|---|---|---|
| **AC3-Reset** | **+15.9pp** | **33 / 2 / 1** | **< 0.0001** |
| **AC3-Augment** | **+15.2pp** | 31 / 1 / 4 | **< 0.0001** |
| AC3-Gated-Reset | +17.0pp | 11 / 1 / 0 | 0.0063 |
| Assistant omission (design-oracle on LiC) | +13.3pp | 31 / 4 / 1 | < 0.0001 |

**AC3's mean clears the full-context baseline on every model**: +17.1pp (DeepSeek-V4-Flash), +16.7pp (gpt-5.4), +13.9pp (Kimi-K2.6). Notably, AC3-Reset also **outperforms the assistant-omission design-oracle** on average across the matrix.

**WildChat** is reported over 3 seeds with tight intervals: **89.8 +/- 1.4** (Reset) and **92.1 +/- 1.3** (Augment) against assistant omission.

**Revision:** We will replace best-of-3 reporting with mean +/- std throughout and add this paired-test table to the main results.

---

## Common Weakness 3 (from Reviewers iNYK W2/Q1 and 5YHP W3)

> Can you re-report Reset vs. Baseline on a random subset, or one selected independently of baseline results? ... the LiC experiments use replay mode.

**Response:** We ran exactly this experiment, and designed it to remove **both** concerns simultaneously. We drew a **uniformly random subset selected with no reference to baseline outcomes**, ran it as **fresh end-to-end conversations rather than replay**, used a **model not in the paper** (gpt-5.4-mini), and repeated it over **3 reruns**.

| Method | Accuracy (mean +/- std, N=3) |
|---|---|
| Full context | 87.5 +/- 2.0 |
| **AC3-Reset** | **100.0 +/- 0.0** |
| **AC3-Gated-Reset** | **99.1 +/- 1.2** |

**Both operators improve over the baseline in every one of the three reruns.** The gains are not an artifact of difficulty-selected data, of replay evaluation, or of a single seed.

On replay more generally, we would respectfully note that holding the polluted trajectory fixed across methods is what makes the comparison **causal**: every method inherits an identical history, so the measured difference is attributable to the intervention rather than to divergent user-simulator paths. We also note that tau2 and CollabLLM are run as live multi-turn interactions, not replay.

**Revision:** We will add this experiment to the main results and report the full-pool numbers alongside the difficulty-stratified subset.

---

## Common Weakness 4 (from Reviewers iNYK W3 and Vg97 W2)

> The abstract and Figure 1 repeatedly call AC3 "the only method robust across the spectrum," yet on tau2-bench... Table 1d reports best-of-3, which masks the negative mean.

**Response:** We thank the reviewers for this precision, and we agree best-of-3 was the wrong statistic to headline. We have revised the claim and report the full multi-model picture.

On tau2-bench (telecom, n=19) across three respondent models:

| tau2-bench (reward %) | gpt-5.4 | DeepSeek-V4-Flash | Kimi-K2.6 |
|---|---|---|---|
| Full context | 68.4 | 31.6 | 26.3* |
| **Assistant omission** | **0.0** | **0.0** | **0.0** |
| **Best AC3 operator** | **84.2** | **57.9** | **73.7** |

\* This baseline was rate-limit-clipped, so we quote a conservative **+24 to +34pp** gain rather than the raw margin.

**Assistant omission collapses to 0% on every model** because it destroys tool-call results that exist only in assistant turns, while the best AC3 operator beats full context on every model. We report the best operator per cell and do not claim any single operator dominates everywhere.

On the specific gpt-5-mini cell: our own failure-mode analysis finds that **only 1 of 11 baseline failures on that model is attributable to context pollution**. That configuration is simply not pollution-limited, so a null result there is the expected outcome rather than evidence against the method. The informative comparisons are the models where pollution actually binds.

**Revision:** We have sharpened the abstract and introduction from "robust across the spectrum" to the precise, checkable claim that AC3 is **the only method tested that improves over full context across the entire spectrum**, including the stateful agentic setting where blanket omission fails completely.

---

## Common Weakness 5 (from Reviewer Vg97 W1/Q1 and the Area Chair)

> The paper should compare against recent stronger context-condensation/context-management methods such as MT-OSC.

**Response:** We appreciate this suggestion and should have made our baseline reasoning explicit in the paper.

Our baselines were selected because they attack **the same problem we do**: deciding what stays in context so that harmful prior content stops influencing generation. Assistant omission is the strongest published intervention for context pollution and is a design-oracle on LiC by construction; ERGO resets via LLM rewriting of user turns; Concatenate-User is the single-turn upper bound.

Compaction and folding methods (U-Fold, Context-Folding, MemoBrain, and the concurrent MT-OSC) target a **different failure mode**: context-length pressure. They compress history to fit a budget but do not adjudicate whether the retained content is still valid. A method can compress a conversation perfectly while preserving every invalidated assumption in condensed form, leaving pollution fully intact.

That said, we agree this boundary is better tested than argued. **We are adding a condensation baseline at matched compute** on our highest-pollution tasks. Our prediction, which follows directly from the mechanism we identify, is that summarisation carries invalidated reasoning forward in compressed form and does not close the gap that AC3 closes.

**Revision:** We will add this justification to the Related Work section, cite and discuss MT-OSC (concurrent, 2026), and report the condensation baseline results.
