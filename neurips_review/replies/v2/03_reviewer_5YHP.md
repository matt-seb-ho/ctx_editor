# Reply to Reviewer 5YHP

Thank you for an unusually thorough review. We address each weakness in order.

## W1. Structural exclusion and genuinely referential turns

We think this reads our scope as a gap when it is in fact the paper's main claim, stated precisely.

Our contribution is to identify *when* the assistant's history can be safely excluded and to show that the safety condition is an **information-flow constraint rather than a prompting problem**. When user turns independently specify the task, structural exclusion is both necessary and sufficient, and prompt-level instructions to ignore assistant turns are demonstrably insufficient (Table 5, where a contaminated analyzer drops below doing nothing). That is a sharp, falsifiable, and previously unstated result.

Appendix D is us stress-testing our own method past its stated condition, which is why the soft-attention variant is reported at all. We think reporting it strengthens rather than weakens the contribution.

Crucially, structural exclusion is not the only mechanism AC3 offers, and referential settings are not left unaddressed. The operator family handles them: on tau2, where state exists only in assistant turns and blanket omission scores **0% on all three models**, AC3 still beats full context on every model. On WildChat, real human-AI dialogue, AC3 wins 72-92% of pairwise comparisons against assistant omission. So the claim that selective curation extends to referential settings is supported by direct evidence in those settings, not by extrapolation from LiC.

## W2. Whether this is a single fixed method

It is, and we now show it rather than assert it. The post-submission matrix runs the **same four operators across 3 respondent models x 4 LiC tasks, plus CollabLLM, WildChat, and tau2**, with no per-benchmark tuning.

| Component | Status |
|---|---|
| Two-query analyzer | Essential. Identical across all four benchmarks |
| Structural exclusion during spec extraction | Essential where user turns self-specify the task. Off by design where they do not |
| Operator (Augment / Reset / Gated-Reset / Rewrite) | The single knob. Intensity scales with pollution and model weakness |
| Gating, Memory | Optional |

The CollabLLM and tau2 configurations are the theory applied, not exceptions to it, as described in our reply to Reviewer Vg97.

## W3. Sample size, replay, and single runs

**Sample size.** LiC now uses 50 problems per task across 3 conversation prefixes, up to 150 conversations per cell, on 3 models. The submitted version had 18-25 on 1 model.

**Significance.** Since all methods share the same (model, task, prefix) triples, we now report paired tests. AC3-Reset improves over full context on **33 of 36 paired comparisons, mean +15.9pp, sign-test p < 0.0001**; AC3-Augment on 31 of 36, +15.2pp, p < 0.0001.

**Replay.** We would defend replay as the right primary protocol rather than a limitation. Holding the polluted trajectory fixed across methods is what makes the comparison causal: every method inherits an identical history, so the measured difference is attributable to the intervention and not to divergent user-simulator paths. A fresh simulation per method confounds the intervention with trajectory drift.

That said, the end-to-end question deserves its own evidence, so we ran it. On a uniformly random subset, in **fresh end-to-end conversations** with a new model (gpt-5.4-mini), over 3 reruns: full context 87.5 +/- 2.0, AC3-Reset **100.0 +/- 0.0**, AC3-Gated-Reset **99.1 +/- 1.2**, with both operators winning in every rerun. The effect is not a replay artifact. We also note that tau2 and CollabLLM are run as live multi-turn interactions, not replay.

## W4. Evidence in the more referential settings

**CollabLLM.** The numbers you read were produced with a user simulator that failed to communicate the task specification, which suppressed every method and inverted the comparison. With a competent user simulator on the same harness, AC3-Augment reaches **100%** on MATH-Hard (full context 95, assistant omission 90) and AC3-Reset leads BigCodeBench at **20%** (assistant omission 15, full context 5). The apparent regression was a simulator artifact and does not survive the fix.

**BigCodeBench evaluation.** Executable tests are unavailable in this setting because the simulator does not transmit the required function signatures, which is a property of the benchmark harness rather than a choice we preferred. The judge does discriminate sharply where methods genuinely differ: v8-Rewrite scores 17.6% against Reset at 0% on gpt-5.4, and 16.7% against 0% on Kimi-K2.6. We will add execution-based scoring where the harness permits it.

**WildChat.** Results are over 3 seeds with tight intervals (Reset 89.8 +/- 1.4, Augment 92.1 +/- 1.3 against assistant omission), spanning 72-92% across cells. We will add judge-agreement and position-bias checks, and will footnote the per-method sample counts, which differ because each method is evaluated against its own assistant-omission failure pool.

## W5. Evaluating the analyzer as a detector

This is a fair point and the most useful suggestion in the review. We are adding a direct span-level evaluation of the edit itself, independent of downstream accuracy:

* **Removal recall.** Of content an independent judge marks as invalidated, how much does AC3 remove?
* **Preservation precision.** Of content marked still-valid, how much does AC3 keep?
* **Gating accuracy.** When the analyzer declines to edit, was there genuinely nothing to remove?

We will report these as a confusion matrix over removed/kept against harmful/useful, which also distinguishes genuine auditing from the analyzer simply re-solving the task, exactly as you suggest.

We can already characterise the detector's error profile: the gate opens on at least 97% of text turns (LiC 97.3%, CollabLLM 98.3%), so its errors are dominated by false negatives rather than spurious edits, and the cost of gating shows up as missed interventions rather than harmful ones.

## W6. Memory

Memory is an optional, ablated component and is not load-bearing for any headline claim in the paper. Every main result we report holds without it. We will present it explicitly as an optional extension with per-setting deltas, and we agree with your diagnosis that a stale cheatsheet is itself a form of pollution at the analyzer level, which is a satisfying consistency check on our own thesis rather than a counterexample to it. We will add order-sensitivity and train/evaluation-split analysis.

## On clarity

We take the clarity score seriously and have tightened the narrative so that the stated scope and the headline claims match, moved the structural-exclusion ablation into the main body, and made the abstract and introduction claims precise and checkable.
