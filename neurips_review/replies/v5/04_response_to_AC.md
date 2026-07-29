# Response to the Area Chair

We thank the Area Chair for coordinating the review process and for the candid meta-review. We are grateful for the explicit invitation to rebut, and we have used the discussion period to address each of the three reservations with new experiments rather than with argument alone. We summarise our response here and point to where the evidence appears.

## On the validity of theoretical assumptions

We want to make sure we address this reservation correctly, and we would welcome clarification if we have misread it, since no reviewer raised an objection framed in formal or theoretical terms.

Our best reading is that this refers to Reviewer 5YHP's W1, which concerns the **scope condition for structural exclusion**: that a task specification can be recovered from user turns alone when those turns independently specify the task. If so, we would make two observations.

First, this is an **empirical and falsifiable condition rather than a formal assumption**, and the paper tests it directly and adversarially rather than assuming it. Table 5 shows that prompt-level instructions to ignore assistant turns are insufficient and that the structural constraint is what carries the effect, a prediction that could have failed and did not. Appendix D reports what happens when the condition does not hold, using the soft-attention variant that must see the full conversation. Testing a method past the boundary of its own stated scope is, we would suggest, the opposite of leaving an assumption unexamined.

Since the meta-review we have also tested the mechanism assumption that sits underneath it — whether the analyzer is auditing the conversation or simply re-solving the task — and reported the result including where it goes against us. Restricted to conversations where the analyzer verifiably never states the correct answer, AC3 gains **+30.2pp on code (0% leakage across 106 conversations)** and **+26.0pp on database**, pooling to **+20.7pp [+14.8, +25.3], p < 0.0001** on 329 conversations. On **math** the same test comes out at **−2.6pp**, and we concede it explicitly: on grade-school arithmetic, auditing and solving are not separable. We would rather present a mechanism claim that holds on two of three tasks and say so, than a blanket one.

Second, we would note that **context pollution is a phenomenon characterised empirically rather than formally**, and that our contribution is comparable in kind to the work it builds on, for example Laban et al. (2025) on multi-turn degradation and Huang et al. (2026) on assistant omission. Our contribution is in the same register: falsifiable predictions tested against controlled experiments. We do not claim a formal result, and we would be glad to state the scope condition more explicitly in Section 3 so that its empirical status is unambiguous.

If the Area Chair had a different concern in mind, we would very much appreciate the opportunity to address it specifically during the discussion period.

## On generalizability

The concern that the method changes for each setting was the reservation listed first, and we agree it deserved a direct empirical answer rather than a description. We now provide two.

The same two-query analyzer and the same four operators are evaluated across **3 respondent models x 4 LiC tasks, plus CollabLLM, WildChat, and tau2-bench**, using a single code path with no per-benchmark tuning. What varies is operator intensity, which is a documented knob.

We also tested generalizability at the component level, which we think is the sharper version of the question. Holding the respondent model fixed and swapping only the analyzer across **five models from four families**, every analyzer produces a positive and individually significant gain over full context, from **+12.9pp to +39.9pp** (n=178 matched pairs, exact McNemar, all p < 0.001), and none falls below baseline. Weak analyzers **under-detect rather than mis-detect**, which is why the degradation is graceful. The best analyzer is Kimi-K2.6 and the weakest is an OpenAI model; since the respondent is also non-OpenAI, the best configuration contains no OpenAI model anywhere. Details in **Common Weakness 1** and our reply to **Vg97 (Q3)**.

The two configurations reviewers flagged, CollabLLM and tau2, are the stated theory being applied rather than departures from it, and a component-level table separating the essential parts from the single tunable knob is in **Common Weakness 1**.

## On experimental evidence

We have scaled the evaluation, added the statistical testing reviewers requested, run the baseline the meta-review asked for, and corrected our own numbers where the new measurements required it.

| Addition | Result |
|---|---|
| Paired significance testing across the LiC matrix | AC3-Reset improves over full context on **33 of 36 paired comparisons**, mean **+15.9pp**, sign-test **p < 0.0001** |
| Scale on the main benchmark | **up to 50 problems per task x 3 conversation prefixes** on **3 models**, up from 18 to 25 on 1 model |
| **Condensation baseline at measured matched compute** (the "limited baselines" reservation) | Summarisation **−2.8 / −8.4pp** (database) and **−4.0 / −3.0pp** (code) vs. full context, while **AC3-Reset is +19.6 / +9.0pp**. The budget-matched summariser used **1.02–1.19x** AC3's strategy calls and **1.62–2.14x** its tokens and still lost by 12–28 points |
| MT-OSC reimplementation | At its published window it engages **0.3 times per conversation** on 4.1-turn conversations, i.e. length-triggered compaction structurally cannot reach early pollution. Reported as a scoping result, not as a beaten baseline |
| Analyzer-model sensitivity | **5 analyzers, 4 families, all positive and individually significant**, +12.9 to +39.9pp; none below baseline |
| Direct detector evaluation (judge-free, constructed ground truth) | Analyzer **names** the injected pollutant in 78.6% of conversations; removal 97.6%; **selectivity is operator-dependent** and we correct a paper claim accordingly (see below) |
| New unbiased, end-to-end, 3-replicate experiment | Raw accuracy: full context 87.5 +/- 2.0, **AC3-Reset 93.3 +/- 4.2**, **AC3-Gated-Reset 95.0 +/- 0.0**, both ahead in every run |
| Replication of the contested database result | AC3-Reset exceeds the design-oracle on **all three models** (49.0 / 56.2 / 55.1 vs. 45.6 / 27.9 / 30.6) |
| WildChat judge audit (1,824 judgements, 3 judges, both orders) | Order-balanced **87.8 +/- 2.1** (Reset) / **91.2 +/- 2.1** (Augment); cross-family PABAK 0.79–0.83, AC1 0.84–0.87; punitive 2-of-3-both-orders rule still 82.5% |

We also want to put four corrections in front of the Area Chair directly, because we think how a submission handles its own disconfirming measurements is relevant to the tractability question.

1. **A CollabLLM figure we quoted did not replicate.** At N=3, AC3-Augment on MATH-Hard **ties** full context (91.7 vs 91.7; identical 55/60 per-problem totals) rather than reaching the 100 we reported from a single run on a near-ceiling benchmark. It still answers the regression Reviewer 5YHP identified — no arm degrades — but we withdraw the improvement claim. On BigCodeBench the same re-run came out *stronger*: **+15pp in 3 of 3 replicates**, reproducing on a fully disjoint problem draw.
2. **Our false-negative-adjusted accuracy metric is biased in our own favour** and we are removing it from headline reporting. It excludes items a judge deems under-specified using only the *visible* messages, so arms that hide content have more of their failures excluded — 62% for AC3-Reset against 9% for baseline on one cell. An arm-symmetric re-judge reproduces the raw ordering but shrinks magnitudes (one cell 89.0% → 77.1%). Every number in this rebuttal is raw.
3. **One sentence in the paper is wrong as attributed.** "We preserve what is correct and remove what is harmful" holds for AC3-**Rewrite** (removal 27.0%, preservation 38.9%), not for AC3-**Reset**, whose edit precision on constructed pollution sits at chance. Reset's real mechanism — detect, discard the assistant side, re-derive from the user side — is defensible and is what we will describe.
4. **WildChat's headline moves down slightly** under a full order-balanced re-judge, from 89.8 / 92.1 to 87.8 / 91.2.

> **⚠ INTERNAL — HOLD (T6 in flight). NOT PART OF THE REPLY.**
> A fifth correction is likely and is not yet stated above because the re-measurement is incomplete. T6's completed tau2 Baseline cells at N=3 read gpt-5.4 68.4 ± 13.9 (reproducing the published 68.4), DeepSeek-V4-Flash **70.2 ± 11.0** (published 31.6) and Kimi-K2.6 **80.4 ± 2.5** (published 26.3); the published DSV4F and Kimi baselines appear to have been rate-limit-clipped floors. If this holds, the tau2 gains on those two models shrink or invert and must be withdrawn, and this letter should say so explicitly in the numbered list above — a fifth self-reported correction strengthens rather than weakens the tractability argument, but only if we state it before a reviewer finds it. The structural tau2 result (assistant omission at 0% on every model, mechanism-corroborated) is unaffected. **Do not post per-model tau2 magnitudes until T6 returns.**

## Closing

The meta-review suggested that, if the reservations were correct, they might be too large to resolve within the rebuttal process. We hope the evidence above suggests a more favourable reading. Each of the three reservations proved answerable within the discussion window: the generalizability question now has a component-level answer, the baseline question has a run baseline with measured compute, and the evidence question has paired tests, a detector evaluation, and an end-to-end replication.

We would also note that the corrections listed above are the discussion period working as intended. Every one of them was found by us, in experiments the reviews prompted, and every one of them is reported here before it could be found by anyone else. The reservations were reasonable; what they turned out to be is tractable.

We are grateful for the reviewers' precision, which made these improvements concrete, and we remain happy to run further analyses during the discussion period.
