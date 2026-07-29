# Final Remarks from the Authors

*(Post at the end of the discussion period, after individual replies have been addressed.)*

We sincerely thank all reviewers for their thoughtful and constructive feedback. The reviews were specific enough to point directly at the experiments worth running, and the paper is substantially stronger as a result.

## Common Strengths Highlighted by Reviewers

* **The self-contained vs. referential framing.** Reviewers noted it "cleanly explains why AO is near-perfect in some settings and collapses to zero in others" (**iNYK**), is "well motivated" (**Vg97**), and is "a meaningful conceptual improvement over treating all assistant-generated context as uniformly harmful" (**5YHP**).
* **The structural-exclusion (contagious pollution) result.** All three reviewers highlighted this as a central contribution, with **5YHP** calling it "one of the strongest parts of the paper" and noting it suggests "information-flow constraints, rather than prompt instructions alone, may be necessary," and **iNYK** noting it "carries a useful lesson for any multi-stage LLM pipeline."
* **Modularity and interpretability** of the specification-extraction, approach-evaluation, and intervention separation (**5YHP**).

## Summary of Key Revisions

* **A unified method statement, empirically demonstrated.** Addressing the Area Chair, **Vg97 (W3, Q4)**, and **5YHP (W2)**, we add a component table separating the essential analyzer and structural-exclusion condition from the single tunable operator knob, and we now evaluate **the same four operators across 3 respondent models x 4 LiC tasks, plus CollabLLM, WildChat, and tau2**, with no per-benchmark tuning.

* **Scaled evaluation and paired significance testing.** Addressing **iNYK (W1, Q2)**, **Vg97 (W2, Q2)**, and **5YHP (W3)**, LiC now uses **50 problems per task across 3 conversation prefixes** (up to 150 conversations per cell) on **3 models**, up from 18-25 on 1 model. We replace best-of-3 with mean +/- std and add paired tests: **AC3-Reset improves over full context on 33 of 36 paired comparisons (+15.9pp, sign-test p < 0.0001)**, outperforming even the assistant-omission design-oracle (+13.3pp).

* **A new unbiased, end-to-end experiment.** Addressing **iNYK (Q1)** and **5YHP (W3)**, we add an experiment on a **uniformly random subset selected without reference to baseline outcomes**, run as **fresh end-to-end conversations** on a **model not used in the paper**, over **3 reruns**: full context 87.5 +/- 2.0, **AC3-Reset 100.0 +/- 0.0**, **AC3-Gated-Reset 99.1 +/- 1.2**, with both operators winning in every rerun.

* **Replication of the database result.** Addressing **iNYK (W1)**, the contested "exceeds the oracle" finding now replicates across all three models at 147 conversations per cell (AC3-Reset 49.0 / 56.2 / 55.1 vs. assistant omission 45.6 / 27.9 / 30.6).

* **Corrected tau2 reporting and claim scope.** Addressing **iNYK (W3)** and **Vg97 (W2)**, we replace best-of-3 with per-model results across three respondents, where **assistant omission collapses to 0% on every model** while the best AC3 operator beats full context on every model. We sharpen the abstract and introduction to the precise claim that AC3 is **the only method tested that improves over full context across the entire spectrum**.

* **Baseline justification and a new condensation baseline.** Addressing **Vg97 (W1, Q1)**, we make explicit in Related Work that our baselines target pollution while compaction and folding methods target context-length pressure, and we add a condensation baseline at matched compute to test that boundary directly. We cite and discuss MT-OSC (concurrent, 2026).

* **Equal-compute control and latency.** Addressing **Vg97 (Q3)**, we add a matched-call-budget self-reflection control and report wall-clock latency alongside API cost, complementing the contagious-pollution result which already shows that extra compute without structural decontamination *reduces* accuracy below baseline.

* **Direct evaluation of the analyzer as a detector.** Addressing **5YHP (W5)**, we add a span-level evaluation reporting removal recall, preservation precision, and gating accuracy as a confusion matrix over removed/kept against harmful/useful.

* **Corrected CollabLLM results.** Addressing **5YHP (W4)**, we report results with a competent user simulator, under which AC3 leads on both datasets (MATH-Hard 100 vs. 95 full context and 90 assistant omission; BigCodeBench 20 vs. 5 and 15). We add judge-agreement and position-bias checks for WildChat.

* **Presentation.** Addressing **Vg97** and **5YHP**, we move the structural-exclusion ablation into the main body, present memory explicitly as an optional ablated extension, and tighten the narrative so the stated scope and headline claims align.

We are grateful to the reviewers for feedback that made these improvements concrete, and we hope the additions address the concerns raised. We are happy to run further analyses during the discussion period.
