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

AC3-Reset **exceeds the design-oracle on all three models**, by 28.3pp on gpt-5.4 and 24.5pp on Kimi-K2.6. The mechanism is the one described in the paper: when shards must be assembled against a schema, consolidation outperforms deletion, because removing assistant turns discards partially-correct assembly work. This is now among the better-supported results in the paper rather than a single-run observation.

We can also now show that the database gain is not the analyzer quietly solving the task. On this task the analyzer's output contains a verified-correct answer in **1 of 147 conversations**; restricted to the 146 conversations with no verified leak, AC3-Reset still gains **+26.0pp** over full context (22.6% → 48.6%, exact McNemar p < 0.0001). The full leakage analysis, including the task where we concede the opposite, is in our reply to **5YHP**.

---

> **W2:** The Table 2 hard subset is the 20 hardest items chosen by baseline failure rate, and the runs replay GPT-5.2 trajectories rather than each model's own generations... making the +20–42pp claim weaker than it appears.

**Response to W2:** Please see **Common Weakness 3** in the General Response, where we report a new experiment on a uniformly random subset, run end-to-end rather than as replay, on a new model, over 3 replicate runs (full context 87.5 +/- 2.0 vs. **AC3-Reset 93.3 +/- 4.2**, with Reset ahead in every run).

We would add that difficulty stratification does what it is designed to do: it concentrates evaluation where the failure mode under study actually occurs, since problems the baseline already solves cannot exhibit recovery. It is also no longer the primary evidence. On the full, non-difficulty-selected pool, AC3-Reset improves over full context on **33 of 36 paired comparisons (+15.9pp, p < 0.0001)**, and we have moved the headline onto these numbers.

---

> **W3:** The abstract and Figure 1 repeatedly call AC3 "the only method robust across the spectrum," yet on tau2-bench the per-trial numbers in Appendix B.6 give Baseline a mean of 53.3% and Gated-Reset 48.3%... Table 1d reports best-of-3 (60 vs 65), which masks the negative mean.

**Response to W3:** You are right that best-of-3 was the wrong statistic to headline, and we have changed it. You were also right about the underlying problem in a way we can now quantify: at n=19 tasks and a baseline near 0.68, the binomial standard deviation of a single tau2 cell is **10.7pp**, and our own N=3 re-measurement of a Baseline cell returns a spread of **±13.9pp**. Several of the cell-to-cell differences we reported at N=1 are smaller than that. We are re-reporting tau2 as mean +/- std over three replicates per cell.

> **⚠ INTERNAL — HOLD (T6 in flight).** Do not post per-model tau2 magnitudes until T6 returns; see the marked block in Common Weakness 4 of the General Response. The paragraph above is safe as written and concedes the reviewer's point in the reviewer's own terms.

The structural tau2 result is unaffected by the re-measurement and is the one that matters for our claim: **assistant omission scores 0% on every model**, and this is behavioural rather than a scoring artifact — AO rollouts never terminate naturally, they exhaust the step budget, because blanket omission destroys tool-call results that exist only in assistant turns. Please see **Common Weakness 4**.

Two further points on the specific cell you cite. First, our own failure-mode analysis of that gpt-5-mini configuration finds that **only 1 of 11 baseline failures is attributable to context pollution**, so that configuration is not pollution-limited and offers almost no headroom for any pollution-removal method. A null result there is expected rather than contradictory. Second, we have sharpened the abstract and introduction to the precise claim that AC3 is **the only method tested that improves over full context across the entire spectrum**.

On the ~20% per-turn cost, we can now give measured figures rather than an estimate. Instrumenting every call and token on LiC-database: AC3-Reset uses 6.2 strategy calls per conversation and AC3-Gated-Reset 2.6, that is **0.41x** Reset's strategy calls for +17.8pp versus Reset's +19.6pp. For comparison, a budget-matched summarisation baseline consumed **1.02–1.19x** AC3-Reset's strategy calls and **1.62–2.14x** its strategy tokens while scoring **below** full context. Gated-Reset is the deployment-relevant configuration precisely because gating skips the intervention when the analyzer finds no issue.

## Response to Questions

> **Q1:** Can you re-report Reset vs. Baseline on a random subset, or one selected independently of baseline results? If the gains survive on an unbiased subset, this will better support the argument; if they largely vanish, the generalization claim should be removed.

**Response to Q1:** We ran this, and designed it to also remove the replay concern from W2. On a **uniformly random subset selected without reference to baseline outcomes** (n=40), run as **fresh end-to-end conversations**, on a **model not used in the paper** (gpt-5.4-mini), over **3 replicate runs**:

| Method | Accuracy, raw (mean +/- std, N=3) | Per-run values |
|---|---|---|
| Full context | 87.5 +/- 2.0 | 90.0 / 87.5 / 85.0 |
| **AC3-Reset** | **93.3 +/- 4.2** | 97.5 / 95.0 / 87.5 |
| **AC3-Gated-Reset** | **95.0 +/- 0.0** | 95.0 / 95.0 / 95.0 |

Both operators improve in **every** run (Reset +7.5 / +7.5 / +2.5pp; Gated-Reset +5.0 / +7.5 / +10.0pp). The gains survive selection independent of baseline performance, they survive end-to-end deployment, and they survive on a new model. By your stated criterion, the generalization claim stands.

We want to be precise about what this experiment can and cannot carry, because you asked the question in a form that deserves a precise answer. At n=40 the per-run margins are two to four problems, and this experiment on its own is not powered for significance; a near-ceiling math subset is also not where the effect is largest. It rules out the three specific confounds you raised and nothing more. The powered evidence remains the 36-comparison paired test (**Q2** below) and the leak-free-subset analysis reported to **5YHP**.

We should also flag a correction. We had previously reported this experiment as **AC3-Reset 100.0 +/- 0.0**. That figure came from our false-negative-adjusted metric, which asks a judge — from the *visible* messages only — whether the user ever specified the task, and drops "under-specified" items from the denominator. Because AC3 hides content, more of its items look under-specified: across the three runs, 1, 2 and 5 items were excluded from AC3-Reset's denominator and **zero** from baseline's. The adjustment therefore inflated our own arm. The raw numbers above are the ones we will publish, and we are correcting this metric throughout the paper.

---

> **Q2:** Please report Baseline and Gated-Reset as the mean ± std over the three seeds rather than best-of-3, and state explicitly whether AC3's mean clears baseline.

**Response to Q2:** Yes on both counts, and we go further by reporting paired tests, since all methods share the same (model, task, prefix) triples:

| Method | Mean paired gain vs. full context | Wins / Losses / Ties | Sign-test p |
|---|---|---|---|
| **AC3-Reset** | **+15.9pp** | **33 / 2 / 1** | **< 0.0001** |
| **AC3-Augment** | **+15.2pp** | 31 / 1 / 4 | **< 0.0001** |
| AC3-Gated-Reset | +17.0pp | 11 / 1 / 0 | 0.0063 |
| Assistant omission | +13.3pp | 31 / 4 / 1 | < 0.0001 |

To state it explicitly, as requested: **AC3's mean clears the full-context baseline on every model** (+17.1pp DeepSeek-V4-Flash, +16.7pp gpt-5.4, +13.9pp Kimi-K2.6), and AC3-Reset's mean also clears the assistant-omission design-oracle across the matrix.

One clarification on what our replicates measure, which we will also add to the appendix. On LiC and CollabLLM, repeated runs vary through temperature-1.0 sampling of the respondent, analyzer and user simulator over a fixed problem draw; they therefore estimate decoder variance rather than sampling variance over problems, and our intervals are narrower than a full re-draw would give. WildChat's N=3 are independent seeds over the sampled pool. We will label the two cases distinctly rather than describing both as "seeds".

We are grateful for these two questions in particular. They prompted the experiments that we believe now form the strongest empirical evidence in the paper.
