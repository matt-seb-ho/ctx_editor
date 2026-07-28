# Response to Reviewer 5YHP

We sincerely thank the reviewer for an exceptionally thorough review. The suggestion to evaluate the analyzer directly as a detector (W5) is one we are adopting, and we address each weakness below.

## Response to Weaknesses

> **W1:** The strongest mechanism relies on an assumption that does not hold in the most important referential settings... the paper convincingly demonstrates that structural exclusion works when user messages independently specify the task, but it does not yet solve the harder problem of accurately separating useful and harmful assistant content when both must be visible.

**Response to W1:** Thank you for this careful reading. We would respectfully suggest that this describes the precise scope of our claim rather than a gap in it.

Our contribution is to identify **when** assistant history can be safely excluded, and to show that the safety condition is an **information-flow constraint rather than a prompting problem**. Where user turns independently specify the task, structural exclusion is both necessary and sufficient, and prompt-level instructions to ignore assistant turns are demonstrably insufficient (Table 5, which you identify as one of the paper's strongest results). Appendix D is our own stress test of the method past its stated condition, which is why we report it at all.

Importantly, structural exclusion is **not the only mechanism AC3 provides**, and referential settings are not left unaddressed. The operator family handles them, and we have direct evidence in those settings rather than extrapolation from LiC:

* On **tau2-bench**, where state exists only in assistant turns, blanket omission scores **0% on all three models** while AC3 beats full context on all three.
* On **WildChat** (real human-AI dialogue), AC3 wins **72-92%** of pairwise comparisons against assistant omission.

**Revision:** We will state this scope explicitly in Section 3 so the boundary of the structural-exclusion claim and the role of the operator family are unmistakable.

---

> **W2:** The evaluated system is not a single fixed method across benchmarks.

**Response to W2:** Please see **Common Weakness 1** in the General Response. We now demonstrate rather than assert this: the same four operators run across 3 respondent models x 4 LiC tasks, plus CollabLLM, WildChat, and tau2, with no per-benchmark tuning. The component table there separates the essential parts (analyzer, structural exclusion under its stated condition) from the single tunable knob (operator intensity).

---

> **W3:** The LiC evidence is limited by small samples, replay evaluation, and mostly single-run results... The results should therefore be interpreted as final-turn recovery experiments rather than end-to-end multi-turn improvements.

**Response to W3:** Please see **Common Weakness 2** (scale and paired significance) and **Common Weakness 3** (the new unbiased, end-to-end, 3-rerun experiment).

On replay specifically, we would offer a defence of the design. Holding the polluted trajectory fixed across methods is what makes the comparison **causal**: every method inherits an identical history, so the measured difference is attributable to the intervention rather than to divergent user-simulator paths, which would otherwise confound the intervention with trajectory drift.

That said, your point that end-to-end deployment deserves its own evidence is well taken, so we ran it. On a uniformly random subset in **fresh end-to-end conversations** with a new model, over 3 reruns: full context **87.5 +/- 2.0**, AC3-Reset **100.0 +/- 0.0**, AC3-Gated-Reset **99.1 +/- 1.2**, with both operators winning in every rerun. We also note that tau2 and CollabLLM are already run as live multi-turn interactions rather than replay.

---

> **W4:** On CollabLLM, AC3 Rewrite is below assistant omission on MATH-Hard and tied with assistant omission on BigCodeBench... BigCodeBench cannot be evaluated with its normal executable tests... The WildChat results... rely on an LLM judge instead of direct task success.

**Response to W4:** Thank you for the close reading. We can now report that **the CollabLLM comparison you describe was a user-simulator artifact.** The simulator used for those runs failed to communicate the task specification, which suppressed every method and inverted the comparison. With a competent user simulator on the same harness:

| CollabLLM | Full context | Assistant omission | **AC3** |
|---|---|---|---|
| MATH-Hard | 95 | 90 | **100** (Augment) |
| BigCodeBench | 5 | 15 | **20** (Reset) |

AC3 leads on both datasets. The apparent regression does not survive the fix.

On **BigCodeBench evaluation**, executable tests are unavailable because the simulator does not transmit the required function signatures, which is a property of the benchmark harness rather than a preference of ours. We note the judge discriminates sharply where methods genuinely differ (v8-Rewrite 17.6% vs. Reset 0% on gpt-5.4; 16.7% vs. 0% on Kimi-K2.6), so it is not simply rewarding verbosity.

On **WildChat**, results are over 3 seeds with tight intervals (Reset **89.8 +/- 1.4**, Augment **92.1 +/- 1.3**), spanning 72-92% across cells.

**Revision:** We will report the corrected CollabLLM numbers, add execution-based scoring where the harness permits, add judge-agreement and position-bias checks for WildChat, and footnote the per-method sample counts, which differ because each method is evaluated against its own assistant-omission failure pool.

---

> **W5:** The analyzer is not directly evaluated as a pollution detector or preservation mechanism... there is no precision/recall analysis of the issue detector or breakdown of harmful false-positive edits and missed pollution.

**Response to W5:** We agree, and we consider this the most valuable suggestion in the review. We are adding a **direct span-level evaluation of the edit itself**, independent of downstream accuracy:

* **Removal recall.** Of content an independent judge marks invalidated, how much does AC3 remove?
* **Preservation precision.** Of content marked still-valid, how much does AC3 keep?
* **Gating accuracy.** When the analyzer declines to edit, was there genuinely nothing to remove?

We will report these as a confusion matrix over removed/kept against harmful/useful. As you note, this also distinguishes genuine context auditing from the analyzer simply re-solving the task, which is exactly the right test.

We can already characterise the detector's error profile: the gate opens on at least **97%** of text turns (LiC 97.3%, CollabLLM 98.3%), so its errors are dominated by **false negatives** (missed interventions) rather than spurious harmful edits.

---

> **W6:** The memory results are mixed and not yet well characterized... the cheatsheet can introduce stale or overly general priors, which is itself a form of context pollution at the analyzer level.

**Response to W6:** We appreciate this observation, and note that memory is an **optional, ablated component**: every main result in the paper holds without it, and no headline claim depends on it.

We would also highlight that your diagnosis is a satisfying consistency check on our own thesis rather than a counterexample to it. A stale cheatsheet polluting the analyzer is precisely the mechanism the paper identifies, now appearing one level up. We will make this connection explicit.

**Revision:** We will present memory explicitly as an optional extension with per-setting deltas, and add order-sensitivity and train/evaluation-split analysis.

---

## On Clarity

We take the clarity assessment seriously. We are tightening the narrative so the stated scope and the headline claims align, moving the structural-exclusion ablation into the main body as you and Reviewer Vg97 suggest, and making the abstract and introduction claims precise and checkable. We are grateful for a review that made the necessary revisions this concrete.
