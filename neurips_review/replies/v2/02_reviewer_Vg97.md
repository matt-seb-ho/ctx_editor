# Reply to Reviewer Vg97

Thank you for the detailed and constructive review. We address each question in order.

## Q1. Stronger context-management baselines

Our baseline selection was deliberate, and we should have made the reasoning explicit in the paper.

We compare against assistant omission, Concatenate-User, and ERGO because all three attack **the same problem we do**: deciding what stays in context so that harmful prior content stops influencing generation. Assistant omission is the strongest published intervention for context pollution and is a design-oracle on LiC by construction. ERGO resets via LLM rewriting of user turns. These are the competing answers to our question.

MT-OSC, U-Fold, Context-Folding, and MemoBrain address a **different failure mode**: context-length pressure. They compress history to fit a budget. They do not adjudicate whether retained content is valid. A method can compress a conversation perfectly and preserve every invalidated assumption in condensed form, which leaves pollution fully intact. So these are not competing solutions to our problem, and treating them as our primary comparison would mis-frame both lines of work.

That said, the boundary between the two is worth testing empirically rather than by argument, and we are doing so. We are adding a **condensation baseline at matched compute** on our highest-pollution text tasks. The prediction that follows from our mechanism is that summarisation carries invalidated reasoning forward in compressed form and does not close the gap that AC3 closes. If it does close the gap, that is a genuinely interesting negative result and we will report it. MT-OSC is concurrent with our submission (2026), and we will cite and discuss it in the revision.

## Q2. Statistically sound results

We agree, and we have gone further than error bars by adding paired tests.

Since every method is evaluated on the same (model, task, prefix) triples, the paired difference is the right statistic. Across all 36 paired comparisons in the post-submission matrix (3 models x 4 LiC tasks x 3 prefixes):

| Method | Mean paired gain vs full context | Wins / losses / ties | Sign-test p |
|---|---|---|---|
| **AC3-Reset** | **+15.9pp** | 33 / 2 / 1 | < 0.0001 |
| **AC3-Augment** | **+15.2pp** | 31 / 1 / 4 | < 0.0001 |
| AC3-Gated-Reset | +17.0pp | 11 / 1 / 0 | 0.0063 |
| Assistant omission | +13.3pp | 31 / 4 / 1 | < 0.0001 |

Sample size on the main benchmark also grew from 18-25 per cell to 50 problems per task across 3 prefixes, giving up to 150 conversations per cell, now on 3 models rather than 1. WildChat is reported over 3 seeds with tight intervals (Reset 89.8 +/- 1.4, Augment 92.1 +/- 1.3 against assistant omission). On tau2 we report per-model results against baseline rather than best-of-3.

## Q3. Equal compute, and latency

This is an important control, and our strongest evidence on it is already in the paper.

The contagious-pollution result (Table 5) is a direct test of the "extra compute" hypothesis, and it refutes it. Adding a second analyzer stage that is **not** structurally decontaminated makes accuracy drop **below** the single-pass baseline. More LLM calls in the wrong information-flow configuration actively hurt. Compute is therefore not sufficient, and the mechanism doing the work is the structural constraint, not the additional call.

We have also run a matched-call-budget self-reflection control, which sees the full conversation and produces guidance without structural decontamination. On a near-ceiling random math subset it reaches 97.5 against AC3-Reset at 97.5 and full context at 90.0. Both interventions recover the same small number of polluted cases when the baseline is already at 90%, so that task does not discriminate between the two hypotheses. We are re-running the same control on high-pollution tasks, where baseline accuracy is near 20% and there is real headroom to separate them.

On latency, the matched-budget control adds about 13% wall-clock over the baseline at equal turn counts (231s vs 205s for the same 40 conversations at equal concurrency). For AC3, Gated-Reset is the deployment-relevant configuration, since gating skips the intervention when the analyzer finds no issue.

## Q4. What exactly is the general AC3 algorithm

One analyzer, one operator family, one knob.

| Component | Status |
|---|---|
| Two-query analyzer (spec extraction, then approach evaluation) | Essential. Identical across all four benchmarks |
| Structural exclusion during spec extraction | Essential where user turns self-specify the task. Off by design where they do not |
| Operator (Augment / Reset / Gated-Reset / Rewrite) | The single knob. Intensity scales with pollution level and model weakness |
| Gating | Optional |
| Memory (cheatsheet) | Optional, ablated, not load-bearing for any headline claim |

The post-submission matrix now demonstrates this rather than asserting it: the same four operators run across 3 models x 4 LiC tasks, plus CollabLLM, WildChat, and tau2, with no per-benchmark tuning.

The two cases you flag are the stated theory applied, not departures from it. CollabLLM turns structural exclusion off because our claim is that it applies when user turns independently specify the task, and CollabLLM is the regime where intent is co-constructed across assistant turns. Applying it there would contradict our own analysis. The tau2 variant is the same analyzer with environment-state tracking added because the environment is stateful; we are renaming it in the text so this continuity is not obscured.

## On moving the hard-attention ablation to the main body

We agree and are doing this. It is one of the paper's central results, and your reading of it as a general lesson for multi-stage LLM pipelines is exactly the framing we will adopt.
