# Response to the Area Chair

We thank the Area Chair for coordinating the review process and for the candid meta-review. We are grateful for the explicit invitation to rebut, and we have used the discussion period to address each of the three reservations with new experiments rather than with argument alone. We summarise our response here and point to where the evidence appears.

## On the validity of theoretical assumptions

We want to make sure we address this reservation correctly, and we would welcome clarification if we have misread it, since no reviewer raised an objection framed in formal or theoretical terms.

Our best reading is that this refers to Reviewer 5YHP's W1, which concerns the **scope condition for structural exclusion**: that a task specification can be recovered from user turns alone when those turns independently specify the task. If so, we would make two observations.

First, this is an **empirical and falsifiable condition rather than a formal assumption**, and the paper tests it directly and adversarially rather than assuming it. Table 5 shows that prompt-level instructions to ignore assistant turns are insufficient and that the structural constraint is what carries the effect, a prediction that could have failed and did not. Appendix D reports what happens when the condition does not hold, using the soft-attention variant that must see the full conversation. Testing a method past the boundary of its own stated scope is, we would suggest, the opposite of leaving an assumption unexamined.

Second, we would note that **context pollution is a phenomenon characterised empirically rather than formally**, and that our contribution is comparable in kind to the work it builds on, for example Laban et al. (2025) on multi-turn degradation and Huang et al. (2026) on assistant omission. Our contribution is in the same register: falsifiable predictions tested against controlled experiments. We do not claim a formal result, and we would be glad to state the scope condition more explicitly in Section 3 so that its empirical status is unambiguous.

If the Area Chair had a different concern in mind, we would very much appreciate the opportunity to address it specifically during the discussion period.

## On generalizability

The concern that the method changes for each setting was the reservation listed first, and we agree it deserved a direct empirical answer rather than a description. We now provide one.

The same two-query analyzer and the same four operators are evaluated across **3 respondent models x 4 LiC tasks, plus CollabLLM, WildChat, and tau2-bench**, using a single code path with no per-benchmark tuning. What varies is operator intensity, which is a documented knob that follows a stated rule, and tau2 confirms the rule directly: the lightest operator wins on the strongest model, and the heaviest on the weakest. The two configurations reviewers flagged, CollabLLM and tau2, are the stated theory being applied rather than departures from it. Details and a component-level table separating the essential parts from the single tunable knob are in **Common Weakness 1** of our General Response.

## On experimental evidence

We have scaled the evaluation and added the statistical testing reviewers requested.

| Addition | Result |
|---|---|
| Paired significance testing across the LiC matrix | AC3-Reset improves over full context on **33 of 36 paired comparisons**, mean **+15.9pp**, sign-test **p < 0.0001** |
| Scale on the main benchmark | **50 problems per task x 3 conversation prefixes** on **3 models**, up from 18 to 25 on 1 model |
| New unbiased, end-to-end, 3-rerun experiment | Full context 87.5 +/- 2.0, **AC3-Reset 100.0 +/- 0.0**, **AC3-Gated-Reset 99.1 +/- 1.2** |
| Replication of the contested database result | AC3-Reset exceeds the design-oracle on **all three models** (49.0 / 56.2 / 55.1 vs. 45.6 / 27.9 / 30.6) |
| Corrected tau2 reporting | Assistant omission collapses to **0% on every model**; best AC3 operator beats full context on **every model** |

On mixed results specifically, we have also traced the weakest evidence in the submission, the CollabLLM comparison, to a user-simulator that failed to communicate the task specification. With a competent simulator, AC3 leads on both datasets (MATH-Hard 100 vs. 95 and 90; BigCodeBench 20 vs. 5 and 15).

## Closing

The meta-review suggested that, if the reservations were correct, they might be too large to resolve within the rebuttal process. We hope the evidence above suggests a more favourable reading: each of the three reservations proved answerable within the discussion window, and the resulting numbers strengthen the paper's central claims rather than qualifying them. Where reviewers were right on specific points, notably that best-of-3 was the wrong statistic to headline and that the database result needed replication, we have made the corrections and the claims survive them.

We are grateful for the reviewers' precision, which made these improvements concrete, and we remain happy to run further analyses during the discussion period.
