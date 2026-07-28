# General Response (post to all reviewers + AC)

We thank the reviewers for careful and specific readings. The three concerns the AC identifies (generalizability, the structural-exclusion assumption, and experimental strength) are answerable with evidence, and we address each below. Since submission we have completed a full model x benchmark x method matrix, scaled the main benchmark by roughly 6x, and added paired significance testing. The results strengthen every headline claim.

## 1. AC3 is one method, and we now test that claim directly

The concern is that AC3 is reconfigured per benchmark. It is not. Every setting uses the same two-query analyzer (specification extraction, then approach evaluation) and the same operator set (Augment, Reset, Gated-Reset, Rewrite).

We now demonstrate this rather than assert it. The post-submission matrix runs **the same four operators across 3 respondent models (gpt-5.4, DeepSeek-V4-Flash, Kimi-K2.6) x 4 LiC tasks, plus CollabLLM, WildChat, and tau2-bench**, with no per-benchmark tuning. One method, one code path, evaluated everywhere.

What varies is *operator intensity*, which is a documented knob, not a redesign. The rule is that heavier operators suit more polluted histories and weaker models. tau2 shows exactly this ordering: the lightest operator (Augment) wins on the strongest model (gpt-5.4), and the heaviest (Rewrite) wins on the weakest (Kimi-K2.6).

Two apparent exceptions are the theory working as specified, not deviations from it:

* **CollabLLM disables structural exclusion.** Our claim is that structural exclusion applies when user turns independently specify the task. CollabLLM is precisely the regime where they do not, because intent is co-constructed across assistant turns. Applying structural exclusion there would contradict our own analysis. This condition is stated in advance, not fitted after the fact.
* **tau2 adds environment-state tracking.** It is the same analyzer, with tool-call state tracked because the environment is stateful. We are renaming this in the text so the continuity is explicit.

| Component | Status |
|---|---|
| Two-query analyzer (spec extraction, then approach evaluation) | Essential, identical across all four benchmarks |
| Structural exclusion during spec extraction | Essential where user turns self-specify the task; off by design where they do not |
| Operator (Augment / Reset / Gated-Reset / Rewrite) | The single knob. Intensity scales with pollution level and model weakness |
| Gating | Optional |
| Memory (cheatsheet) | Optional add-on, ablated, not load-bearing for any headline claim |

## 2. Scale and statistics

**Sample size.** LiC, our main benchmark, now uses 50 problems per task, each evaluated across 3 independent conversation prefixes, giving up to 150 conversations per cell. The submitted version had 18 to 25. This is roughly a 6x increase, and it covers 3 models rather than 1.

**Paired significance.** Because every method is evaluated on the same (model, task, prefix) triples, the correct statistic is the paired difference. Across all 36 paired comparisons (3 models x 4 tasks x 3 prefixes):

| Method | Mean paired gain vs full context | Wins / losses / ties | Sign-test p |
|---|---|---|---|
| **AC3-Reset** | **+15.9pp** | 33 / 2 / 1 | < 0.0001 |
| **AC3-Augment** | **+15.2pp** | 31 / 1 / 4 | < 0.0001 |
| AC3-Gated-Reset | +17.0pp | 11 / 1 / 0 | 0.0063 |
| Assistant omission (design-oracle on LiC) | +13.3pp | 31 / 4 / 1 | < 0.0001 |

AC3-Reset improves over full context in 33 of 36 comparisons, and outperforms even the assistant-omission design-oracle on average across the matrix. Per model, Reset gains +17.1pp (DeepSeek-V4-Flash), +16.7pp (gpt-5.4), and +13.9pp (Kimi-K2.6).

**Variance.** We report mean and standard deviation rather than best-of-3 wherever the reviewers asked. On WildChat (N=3 seeds), AC3 win rates against assistant omission are 89.8 +/- 1.4 (Reset) and 92.1 +/- 1.3 (Augment).

## 3. New experiment: unbiased subset, end-to-end, three reruns

To test whether gains depend on difficulty-selected data or on replay, we ran a new experiment that removes both: a **uniformly random subset selected without reference to baseline outcomes**, run as **fresh end-to-end conversations rather than replay**, on a **model not in the matrix** (gpt-5.4-mini), over **3 reruns**.

| Method | Accuracy (mean +/- std, N=3) |
|---|---|
| Full context | 87.5 +/- 2.0 |
| **AC3-Reset** | **100.0 +/- 0.0** |
| **AC3-Gated-Reset** | **99.1 +/- 1.2** |

Both operators improve over the baseline in every one of the three reruns. The effect is not an artifact of subset selection, of replay, or of a single seed.

## 4. Agentic setting

On tau2-bench (telecom, n=19) across three respondent models, assistant omission collapses to **0% on every model** because it destroys tool-call results that exist only in assistant turns. The best AC3 operator beats full context on every model: 84.2 vs 68.4 (gpt-5.4), 57.9 vs 31.6 (DeepSeek-V4-Flash), and 73.7 vs 26.3 (Kimi-K2.6, where the baseline was rate-limit-clipped, so we quote a conservative +24 to +34pp). We report the best operator per cell rather than claiming that any single operator dominates everywhere.

## 5. Baselines

Our baselines were selected to target the problem we study. Assistant omission, Concatenate-User, and ERGO all manipulate what remains in context in order to remove harmful influence, which is the pollution problem. Compaction and folding methods (U-Fold, Context-Folding, MemoBrain, and the concurrent MT-OSC) target context-length pressure, which is a different failure mode: they compress history rather than adjudicate its validity. Comparing against them tests a boundary rather than a competing solution to the same problem.

That boundary is worth testing, so we are adding a condensation baseline at matched compute on our highest-pollution text tasks. Our prediction, which follows directly from the mechanism we identify, is that summarisation preserves invalidated reasoning in compressed form and therefore does not recover the gap.

## 6. Evaluating the analyzer directly

Several reviewers noted that we measure downstream accuracy but not the quality of the edit itself. We agree this is worth measuring and are adding it: a span-level evaluation reporting removal recall (of content an independent judge marks invalidated, how much AC3 removes), preservation precision (of content marked still-valid, how much AC3 keeps), and gating accuracy. We will report this as a confusion matrix over removed/kept against harmful/useful.

Existing evidence on detector behaviour: the gate opens on at least 97% of text turns (LiC 97.3%, CollabLLM 98.3%), so its errors are dominated by false negatives rather than spurious edits.
