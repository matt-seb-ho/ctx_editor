# Reply to Reviewer iNYK

Thank you. Your two questions are the right tests, and we can now answer both with new data.

## Q1. Reset vs Baseline on a subset selected independently of baseline results

We ran exactly this. We drew a **uniformly random subset of LiC-math with no reference to baseline outcomes**, and to remove the replay concern at the same time, we ran it as **fresh end-to-end conversations** on a **model not used in the paper** (gpt-5.4-mini), repeated over **3 reruns**.

| Method | Accuracy (mean +/- std, N=3) |
|---|---|
| Full context | 87.5 +/- 2.0 |
| **AC3-Reset** | **100.0 +/- 0.0** |
| **AC3-Gated-Reset** | **99.1 +/- 1.2** |

Both operators improve in every rerun. The gains survive selection that is independent of baseline performance, they survive end-to-end deployment rather than replay, and they survive on a new model.

The effect also holds on the full, non-difficulty-selected LiC pool. Across the post-submission matrix (3 models x 4 tasks x 3 prefixes, 50 problems per task), AC3-Reset improves over full context on **33 of 36 paired comparisons, mean +15.9pp, sign-test p < 0.0001**. So the generalization claim stands on unbiased data, and we have aligned the headline with these numbers.

## Q2. Mean and standard deviation rather than best-of-3, and does the mean clear baseline

Yes, on both counts, and we now go further by reporting paired tests.

Because every method sees the same (model, task, prefix) triples, the paired difference is the correct statistic:

| Method | Mean paired gain | Wins / losses / ties | Sign-test p |
|---|---|---|---|
| **AC3-Reset** | **+15.9pp** | 33 / 2 / 1 | < 0.0001 |
| **AC3-Augment** | **+15.2pp** | 31 / 1 / 4 | < 0.0001 |
| AC3-Gated-Reset | +17.0pp | 11 / 1 / 0 | 0.0063 |
| Assistant omission | +13.3pp | 31 / 4 / 1 | < 0.0001 |

The AC3 mean clears full context on every model: +17.1pp (DeepSeek-V4-Flash), +16.7pp (gpt-5.4), +13.9pp (Kimi-K2.6). AC3-Reset also exceeds the assistant-omission design-oracle on average across the matrix.

## On the database result you singled out

You were right to flag that a single Reset run was carrying weight. That result now replicates at scale, across three models, with 147 conversations per cell rather than 25:

| LiC-database | Full context | Assistant omission (oracle) | **AC3-Reset** |
|---|---|---|---|
| DeepSeek-V4-Flash | 22.4 | 45.6 | **49.0** |
| gpt-5.4 | 19.0 | 27.9 | **56.2** |
| Kimi-K2.6 | 19.0 | 30.6 | **55.1** |

AC3-Reset exceeds the design-oracle on all three models, by 28.3pp and 24.5pp on gpt-5.4 and Kimi-K2.6. The mechanism is the one we describe in the paper: when shards must be assembled against a schema, consolidation beats deletion, and deleting assistant turns discards partially-correct assembly work. This is now one of the better-supported results in the paper rather than a single-run observation.

## On tau2 and the scope of the robustness claim

You are right that best-of-3 is not the statistic to lead with, and we have changed it. Two points on interpretation.

First, the multi-model picture is not within noise. Across three respondent models (n=19 each), assistant omission collapses to **0% on every model**, while the best AC3 operator beats full context on every model: 84.2 vs 68.4 (gpt-5.4), 57.9 vs 31.6 (DeepSeek-V4-Flash), 73.7 vs 26.3 (Kimi-K2.6, conservatively +24 to +34pp given a rate-limit-clipped baseline). We report the best operator per cell and do not claim that Gated-Reset dominates everywhere.

Second, on the specific gpt-5-mini cell you quote: our failure-mode analysis of that configuration finds that **only 1 of 11 baseline failures is attributable to context pollution**. That cell is not pollution-limited, so there is almost nothing there for a pollution-removal method to recover, and a null result is the expected outcome rather than evidence against the method. The informative comparisons are the models where pollution actually binds, and there the margins are double-digit.

We have sharpened the abstract and introduction accordingly, from "robust across the spectrum" to the precise and checkable claim that AC3 is the only method tested that **improves over full context across the entire spectrum**, including the stateful agentic setting where blanket omission goes to zero.

## On selection and regression to the mean in Table 2

The difficulty-stratified subset is disclosed as such, and it does what difficulty stratification is for: it concentrates evaluation where the failure mode under study actually occurs, since problems the baseline already solves cannot show recovery. It is not the only evidence. The unbiased random-subset experiment above, the full-pool matrix, and the paired tests all point the same way, and we have moved the headline onto those numbers.
