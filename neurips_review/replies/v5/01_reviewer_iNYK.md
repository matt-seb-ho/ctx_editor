# Response to Reviewer iNYK

We thank the reviewer for a precise and constructive review, and especially for identifying the two exact tests that would settle the generalization question. We ran both, and we address each point below.

## Response to Weaknesses

> **W1:** LiC has only 18–25 samples per cell, and only Gated-Reset was replicated three times (std 5–7pp), so several-point gaps sit within noise. The "exceeds the oracle on database" result (48% vs. 32%) comes from a single Reset run, whereas the replicated Gated-Reset averages only 38.7%.

**Response to W1:** Thank you for pressing on this. Please see **Common Weakness 2** in the General Response for the scaled evaluation (up to 50 problems per task x 3 prefixes, up to 150 conversations per cell, on 3 models) and the paired significance tests.

On the database result specifically, you were right that a single run was carrying too much weight. That result now **replicates across all three models** at 147 conversations per cell (raw accuracy):

| LiC-database | Full context | Assistant omission (oracle) | **AC3-Reset** |
|---|---|---|---|
| DeepSeek-V4-Flash | 22.4 | 45.6 | **49.0** |
| gpt-5.4 | 19.0 | 27.9 | **56.2** |
| Kimi-K2.6 | 19.0 | 30.6 | **55.1** |

(n = 147 per cell: 49 instances × 3 conversation prefixes, drawn from the 50 highest-failure-rate database instances in the GPT-5.2 LiC logs; last-turn replay. Every arm is scored on the same 147 conversations, so the column-to-column differences are paired. The **absolute** level is a floor set by that selection and is **not** comparable to Table 1's 4.0% or to Common Weakness 5's 56.1%, which come from a *harder* subset and an *unselected* pool respectively — see the comparability note in Common Weakness 5.)

AC3-Reset **exceeds the design-oracle on all three models**, by 28.3pp on gpt-5.4 and 24.5pp on Kimi-K2.6. The mechanism is the one described in the paper: when shards must be assembled against a schema, consolidation outperforms deletion, because removing assistant turns discards partially-correct assembly work. This is now among the better-supported results in the paper rather than a single-run observation.

**On the operator you actually named.** Your point was about **Gated-Reset**, whose replicated average you correctly quoted as 38.7%, so we should give you that operator rather than substitute the one that wins. On DeepSeek-V4-Flash — the model for which we have Gated-Reset at scale — the new database figure is **49.7%** across 147 conversations (73/147; three prefixes at 44.9 / 49.0 / 55.1), against full context at **22.4%** and assistant omission at 45.6%. It beats full context on all three prefixes and clears the design-oracle by 4.1pp. The 38.7% you cite was a three-run mean on 25 conversations; at 147 conversations the number moves up rather than down, which is the outcome your concern was testing for. We have not run Gated-Reset on the other two respondents, and we do not claim it there.

We should also be explicit about a pattern you would be entitled to suspect, since we report a best operator per cell in several tables: **the 33-of-36 result is a single fixed configuration, AC3-Reset, not a per-cell maximum.** Where a per-cell best is printed we will label it as such, and the deployment rule we recommend is stated in advance — always-on Reset where an intervention is cheap, Gated-Reset where an unnecessary edit carries state-disruption cost.

We can also now show that the database gain is not the analyzer quietly solving the task. On this task the analyzer's output contains a verified-correct answer in **1 of 147 conversations**; restricted to the 146 conversations with no verified leak, AC3-Reset still gains **+26.0pp** over full context (22.6% → 48.6%, exact McNemar p < 0.0001). The full leakage analysis, including the task where we concede the opposite, is in our reply to **5YHP**.

One further consequence of taking your noise concern seriously, and it goes against us. Re-auditing the main table's denominators for this response, we found that **ERGO — and only ERGO — had been scored on unfiltered conversation pools**, so it was charged with items no other method was asked to attempt. Correcting that moves **ERGO/math from 69.6 to 80.0, above AC3-Reset's 75.0 and level with AC3-Gated-Reset's 80.0**; code is essentially unchanged (≈44.0) and database is untouched (12.0). We then ran the paired test your review implies, and it makes your point for you: **no ERGO-vs-AC3 difference in that table is statistically distinguishable at n ≈ 20 in either direction** (code p = 0.375, math p = 1.00), which is true of the published table as well as the corrected one. We will print n per cell, disclose the original scoring in the caption, and stop presenting that ordering as settled. The full disclosure is in **Common Weakness 5**.

---

> **W2:** The Table 2 hard subset is the 20 hardest items chosen by baseline failure rate, and the runs replay GPT-5.2 trajectories rather than each model's own generations... making the +20–42pp claim weaker than it appears.

**Response to W2:** Please see **Common Weakness 3** in the General Response, where we report a new experiment on a uniformly random subset, run end-to-end rather than as replay, on a new model, over 3 replicate runs (full context 87.5 +/- 2.0 vs. **AC3-Reset 93.3 +/- 4.2**, with Reset ahead in every run).

We would add that difficulty stratification does what it is designed to do: it concentrates evaluation where the failure mode under study actually occurs, since problems the baseline already solves cannot exhibit recovery. That is also why we should be explicit about which of our experiments are stratified and which are not, since your W2 turns on exactly this. **The 36-comparison paired matrix *is* on a difficulty-selected pool** — the 50 highest-failure-rate instances per task from the GPT-5.2 LiC logs, with replay prefixes additionally weighted toward baseline failures. Its purpose is statistical power in the regime where pollution binds, and every arm sees identical items, so its **+15.9pp on 33 of 36 paired comparisons (p < 0.0001)** is a valid paired effect but **not a population estimate**, and we will describe it that way. The unbiased evidence is separate and we report it as such: the uniformly random n=40 subset in **Q1** below, and the condensation-baseline experiment in **Common Weakness 5**, which runs on the **complete, unselected LiC pool** (n=107 database, n=100 code, end-to-end rather than replay) and where AC3-Reset still gains **+19.6pp** on database (p = 0.0005) and **+9.0pp** on code (p = 0.023) over full context.

---

> **W3:** The abstract and Figure 1 repeatedly call AC3 "the only method robust across the spectrum," yet on tau2-bench the per-trial numbers in Appendix B.6 give Baseline a mean of 53.3% and Gated-Reset 48.3%... Table 1d reports best-of-3 (60 vs 65), which masks the negative mean.

**Response to W3:** You were right that best-of-3 was the wrong statistic to headline, and you were right about the underlying problem in a way that turned out to cost us more than the statistic. We re-ran the **entire published tau2 matrix** at N=3 — 3 models x 5 arms x 3 replicate runs (seeds 42/43/44) x 19 tasks, 855 scored rollouts — and **two of our three published baselines do not replicate**: DeepSeek-V4-Flash moves from 31.6 to **70.2 ± 11.0** and Kimi-K2.6 from 26.3 to **78.9 ± 0.0**. **On all three models the re-measured full-context baseline is at or above every AC3 arm, so we withdraw the tau2 improvement claim.** We had compared a clean treatment against a control that our own logs show was rate-limit-clipped (14/20 and 19/20 short-exits). The positive controls make this a statement about our published numbers rather than about comparability: gpt-5.4's baseline reproduces at **68.4** against a published 68.4, assistant omission reproduces at **0.0 in all nine cells**, the invocation strings are byte-identical to our committed sweep scripts and no model was substituted. The full table and accounting are in **Common Weakness 4**.

**The specific comparison you quoted reproduces in direction.** You cited Baseline 53.3 against Gated-Reset 48.3 from our appendix; on gpt-5.4 at N=3 the corresponding pair is Baseline **68.4 ± 13.9** against Gated-Reset **57.9 ± 21.1** — paired **−10.5pp, exact p = 0.238** over 57 pairs (6 arm wins, 12 baseline wins, 39 ties). We keep that negative rather than dropping it, and we do not upgrade it either: a 19-task benchmark cannot resolve a 10pp effect, which is the quantitative form of your objection. On the noise floor you were pointing at: at n=19 tasks and a baseline near 0.68 the binomial standard deviation of a single cell is **10.7pp**, and our N=3 re-measurement of a Baseline cell returns a spread of **±13.9pp**, so several of the cell-to-cell differences we reported at N=1 were never resolvable.

We should also disclose something we could not explain. On gpt-5.4 the baseline reproduced exactly while every AC3 arm fell 10 to 37 points against our published values (Augment 84.2 → 47.4). We ruled out model substitution, the operator not firing, degenerate termination and rate-limit contamination, and we found a real defect in our tau2 fork — 53% of analyzer calls fall back to splicing a raw completion into the agent briefing — but fixing it moved accuracy by only +2.3pp. We report the collapse as unexplained rather than attribute it to the bug.

The one tau2 result that survives is the one that matters for our claim, and it reproduces exactly: **assistant omission scores 0% on every model** — nine cells, 171 rollouts, not a single non-zero reward. This is behavioural rather than a scoring artifact — AO rollouts never terminate naturally, they exhaust the step budget, because blanket omission destroys tool-call results that exist only in assistant turns — and it does not depend on the baseline's level, which is why the correction above leaves it standing. Please see **Common Weakness 4**.

Two further points on the specific cell you cite. First, we should be straightforward with you: **we do not have a defensible failure taxonomy for that gpt-5-mini configuration.** Our qualitative reading at the time suggested its baseline failures were dominated by missing domain knowledge and by step-budget exhaustion under the hard personas rather than by pollution, which would make it a low-headroom setting for any pollution-removal method — but that was one author's reading of a single trial's traces, with no rubric and no second annotator, so we would rather offer it as a hypothesis than as evidence. That configuration was also outside the three-model re-run above. For the camera-ready we will annotate all trials against a published rubric with a second annotator and report the taxonomy whichever way it comes out. Second, we have corrected the abstract and introduction to the precise claim that AC3 is **the only method tested that improves over full context on every self-contained and referential benchmark, and the only method that remains viable in the stateful agentic setting**, where blanket omission fails structurally (0% on every respondent). The stronger version of that sentence, which we had sharpened it to before the re-measurement, is not supportable and we are not printing it.

On the ~20% per-turn cost, we can now give measured figures rather than an estimate. Instrumenting every call and token on LiC-database: AC3-Reset uses 6.2 strategy calls per conversation and AC3-Gated-Reset 2.6, that is **0.41x** Reset's strategy calls for +17.8pp versus Reset's +19.6pp. For comparison, a budget-matched summarisation baseline consumed **1.02–1.19x** AC3-Reset's strategy calls and **1.62–2.14x** its strategy tokens while scoring **below** full context. To state our deployment rule once, since it appears in several of these replies: **always-on Reset where an intervention is cheap, and Gated-Reset where an unnecessary edit carries state-disruption cost**, because gating skips the intervention entirely when the analyzer finds no issue. That is the paper's own recommendation and we keep it. We should also note for the record that Gated-Reset's paired row covers 12 of the 36 triples, on one respondent model; we report it separately rather than pooling it, and we do not present it as the best-evidenced arm.

## Response to Questions

> **Q1:** Can you re-report Reset vs. Baseline on a random subset, or one selected independently of baseline results? If the gains survive on an unbiased subset, this will better support the argument; if they largely vanish, the generalization claim should be removed.

**Response to Q1:** We ran this, and designed it to also remove the replay concern from W2. On a **uniformly random subset selected without reference to baseline outcomes** (n=40), run as **fresh end-to-end conversations**, on a **model not used in the paper** (gpt-5.4-mini), over **3 replicate runs**:

| Method | Accuracy, raw (mean +/- std, N=3) | Per-run values |
|---|---|---|
| Full context | 87.5 +/- 2.0 | 90.0 / 87.5 / 85.0 |
| **AC3-Reset** | **93.3 +/- 4.2** | 97.5 / 95.0 / 87.5 |
| **AC3-Gated-Reset** | **95.0 +/- 0.0** | 95.0 / 95.0 / 95.0 |

Two notes on that table, since a `95.0 +/- 0.0` at temperature 1.0 invites the question. First, the three Gated-Reset runs are **independent end-to-end conversations that happen to land on the same count**, not a cached replay: they fail on *different* problems each time (the failing pairs are disjoint across the three runs, union 5 and intersection 0), the analyzer's output differs on **39 of 39** comparable conversations across the three runs, and turn counts and extracted answers differ on 7 and 5 of the 40 problems respectively. Second, these `+/-` are spreads over three replicates and so describe decoder variance, not sampling variance over problems. A problem-clustered bootstrap over the 40 problems gives full context **87.5% [79.2, 95.0]**, AC3-Reset **93.3% [87.5, 98.3]** and AC3-Gated-Reset **95.0% [90.0, 99.2]**; paired against full context, AC3-Gated-Reset is **+7.5pp [+1.7, +15.0]** (item-level exact McNemar over the three replicates, p = 0.023) and AC3-Reset is **+5.8pp [+0.0, +12.5]** (p = 0.119). We report both, including the one that does not reach significance.

Both operators improve in **every** run (Reset +7.5 / +7.5 / +2.5pp; Gated-Reset +5.0 / +7.5 / +10.0pp). The gains survive selection independent of baseline performance, they survive end-to-end deployment, and they survive on a new model. By your stated criterion, the generalization claim stands.

We want to be precise about what this experiment can and cannot carry, because you asked the question in a form that deserves a precise answer. At n=40 the per-run margins are two to four problems, and a near-ceiling math subset is not where the effect is largest, so we do not rest our headline significance on it. It rules out the three specific confounds you raised and nothing more. The powered evidence remains the 36-comparison paired test (**Q2** below) and the leak-free-subset analysis reported to **5YHP**.

We should also flag a correction. We had previously reported this experiment as **AC3-Reset 100.0 +/- 0.0**. That figure came from our false-negative-adjusted metric, which asks a judge — from the *visible* messages only — whether the user ever specified the task, and drops "under-specified" items from the denominator. Because AC3 hides content, more of its items look under-specified: across the three runs, 1, 2 and 5 items were excluded from AC3-Reset's denominator and **zero** from baseline's. The adjustment therefore inflated our own arm. The raw numbers above are the ones we will publish, and we are correcting this metric throughout the paper.

---

> **Q2:** Please report Baseline and Gated-Reset as the mean ± std over the three seeds rather than best-of-3, and state explicitly whether AC3's mean clears baseline.

**Response to Q2:** Yes on both counts, and we go further by reporting paired tests, since all methods share the same (model, task, prefix) triples:

| Method | Mean paired gain vs. full context | Wins / Losses / Ties | Sign-test p |
|---|---|---|---|
| **AC3-Reset** | **+15.9pp** | **33 / 2 / 1** | **< 0.0001** |
| **AC3-Augment** | **+15.2pp** | 31 / 1 / 4 | **< 0.0001** |
| AC3-Gated-Reset† | +17.0pp | 11 / 1 / 0 | 0.0063 |
| AC3-Rewrite† | −0.3pp | 6 / 6 / 0 | 1.00 |
| Assistant omission | +13.3pp | 31 / 4 / 1 | < 0.0001 |

† These two rows cover 12 of the 36 triples, on one respondent model, which is why their counts do not sum to 36. We print the AC3-Rewrite row for completeness even though it is our worst — its cells predate the analyzer-parity fix and we do not claim Rewrite improves LiC accuracy; its evidence is on referential settings. See Common Weakness 2 for the full footnote and for where AC3 does and does not separate from assistant omission.

Because the sign test above discards effect size and treats 36 correlated cells as independent, we also report the same comparison at the level of individual problems, with an interval: AC3-Reset is **+15.4pp, 95% CI [+11.5, +19.4]** by a problem-clustered bootstrap over 191 problems, on **350 problem-wins against 93** of 1,668 paired items (exact McNemar p < 1e−30). The full five-row version is in **Common Weakness 2**; all three statistics agree.

To state it explicitly, as requested: **AC3's mean clears the full-context baseline on every model** (+17.1pp DeepSeek-V4-Flash, +16.7pp gpt-5.4, +13.9pp Kimi-K2.6). Against the assistant-omission design-oracle, AC3-Reset's mean is higher (+15.9 vs +13.3), but we would not want that read as a general win: head to head over the same 36 triples the margin is **+2.6pp on 15 wins, 17 losses and 4 ties**, and it is concentrated on LiC-database (+18.7pp, 8 of 9) rather than spread across the matrix. We set out where AC3 does and does not separate from assistant omission, and why our framework predicts the pattern, in **Common Weakness 2**.

One clarification on what our replicates measure, which we will also add to the appendix. On LiC and CollabLLM, repeated runs vary through temperature-1.0 sampling of the respondent, analyzer and user simulator over a fixed problem draw; they therefore estimate decoder variance rather than sampling variance over problems, and our intervals are narrower than a full re-draw would give. WildChat's N=3 are independent seeds over the sampled pool. We will label the two cases distinctly rather than describing both as "seeds".

We are grateful for these two questions in particular. They prompted the experiments that we believe now form the strongest empirical evidence in the paper.
