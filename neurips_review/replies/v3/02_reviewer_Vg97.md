# Response to Reviewer Vg97

We thank the reviewer for a thorough and constructive review, and for the specific pointer to MT-OSC. We address each weakness and question below.

## Response to Weaknesses

> **W1:** The central weakness is the set of baselines in the experiment... the paper should compare against recent stronger context-condensation/context-management methods such as MT-OSC.

**Response to W1:** Please see **Common Weakness 5** in the General Response, and Q1 below.

---

> **W2:** Another concern is the statistical reliability. Many of the headline LiC cells use small sample sizes, with only the Gated-Reset row repeated three times... The tau2-bench result is also not very persuasive as currently presented.

**Response to W2:** Please see **Common Weakness 2** (scaled evaluation and paired tests) and **Common Weakness 4** (multi-model tau2 results replacing best-of-3).

---

> **W3:** A third concern is that the method changes substantially across settings... it is not obvious whether the paper is validating a single method, a family of prompt-engineering patterns, or several task-specific context-management variants.

**Response to W3:** Please see **Common Weakness 1**, where we now demonstrate that the same four operators run across 3 models x 4 LiC tasks plus CollabLLM, WildChat, and tau2 with no per-benchmark tuning. Q4 below gives the component-level breakdown you requested.

## Response to Questions

> **Q1:** Can the authors compare against stronger context-management baselines as described in the weakness section? Otherwise, the authors should be able to clearly justify why the stronger baselines cannot be adapted.

**Response to Q1:** We appreciate this and should have made our reasoning explicit in the paper. Our baselines were chosen because they attack **the same problem we study**: deciding what remains in context so that harmful prior content stops influencing generation. Assistant omission is the strongest published intervention for context pollution and is a design-oracle on LiC by construction, ERGO resets via LLM rewriting of user turns, and Concatenate-User provides the single-turn upper bound.

Compaction and folding methods (MT-OSC, U-Fold, Context-Folding, MemoBrain) target a **different failure mode**: context-length pressure. They compress history to fit a budget without adjudicating whether the retained content remains valid. A method can compress a conversation perfectly and still preserve every invalidated assumption in condensed form, leaving pollution fully intact. This is why we treated them as a boundary rather than a competing solution.

We agree the boundary is better tested than argued. **We are adding a condensation baseline at matched compute** on our highest-pollution tasks, and will report the result either way. MT-OSC is concurrent with our submission (2026); we will cite and discuss it in the revision.

---

> **Q2:** Can the authors report statistically sound results for the main claims? Please provide confidence intervals, paired tests, or bootstrap analyses for LiC and WildChat, and report mean ± variance rather than best-of-3 on tau2.

**Response to Q2:** Yes. Since every method is evaluated on the same (model, task, prefix) triples, we report **paired tests**, which is the statistically appropriate choice here:

| Method | Mean paired gain vs. full context | Wins / Losses / Ties | Sign-test p |
|---|---|---|---|
| **AC3-Reset** | **+15.9pp** | **33 / 2 / 1** | **< 0.0001** |
| **AC3-Augment** | **+15.2pp** | 31 / 1 / 4 | **< 0.0001** |
| AC3-Gated-Reset | +17.0pp | 11 / 1 / 0 | 0.0063 |
| Assistant omission | +13.3pp | 31 / 4 / 1 | < 0.0001 |

Sample size on LiC grew from 18-25 per cell to **50 problems per task across 3 prefixes** (up to 150 conversations per cell) on **3 models**. **WildChat** is reported over 3 seeds with tight intervals (Reset **89.8 +/- 1.4**, Augment **92.1 +/- 1.3** against assistant omission). On **tau2** we now report per-model results against baseline rather than best-of-3 (**Common Weakness 4**).

---

> **Q3:** How sensitive are the results to the analyzer model and compute budget?... A fair comparison should include equal-budget baselines, such as repeated generation, self-reflection, or a strong summarizer/condensor using the same model and number of calls. Please also report latency implications, not just API cost.

**Response to Q3:** This is an important control, and we would note that our **strongest evidence on it is already in the paper**.

The contagious-pollution result (Table 5) is a direct test of the extra-compute hypothesis and refutes it. Adding a second analyzer stage that is **not** structurally decontaminated makes accuracy drop **below** the single-pass baseline. Additional LLM calls in the wrong information-flow configuration actively hurt, so compute alone is not sufficient, and the mechanism doing the work is the structural constraint rather than the extra call.

We have also run an explicit **matched-call-budget self-reflection control**, which sees the full conversation and produces guidance without structural decontamination. On a near-ceiling random math subset it reaches 97.5, against AC3-Reset at 97.5 and full context at 90.0. When the baseline is already at 90%, both interventions recover the same small number of polluted cases, so that particular task cannot discriminate between the two hypotheses. We are re-running the same control on high-pollution tasks, where baseline accuracy is near 20% and there is real headroom to separate them.

On **latency**, the matched-budget control adds roughly **13% wall-clock** over the baseline at equal turn counts (231s vs. 205s for the same 40 conversations at equal concurrency). For AC3, Gated-Reset is the deployment-relevant configuration because gating skips the intervention entirely when the analyzer finds no issue.

---

> **Q4:** Please clarify what exactly is the general AC3 algorithm across benchmarks? ... Please clarify which components are essential and which are task-specific adaptations.

**Response to Q4:** One analyzer, one operator family, one knob:

| Component | Status |
|---|---|
| Two-query analyzer (spec extraction, then approach evaluation) | **Essential.** Identical across all four benchmarks |
| Structural exclusion during spec extraction | **Essential where user turns self-specify the task.** Off by design where they do not |
| Operator (Augment / Reset / Gated-Reset / Rewrite) | **The single knob.** Intensity scales with pollution level and model weakness |
| Gating | Optional |
| Memory (cheatsheet) | Optional, ablated, not load-bearing for any headline claim |

The two cases you flag are the stated theory applied, not departures from it. **CollabLLM** turns structural exclusion off because our claim is that it applies when user turns independently specify the task, and CollabLLM is exactly the regime where intent is co-constructed across assistant turns; applying it there would contradict our own analysis. The **tau2** variant is the same analyzer with environment-state tracking added because the environment is stateful.

**Revision:** We will add this table and a unified algorithm statement to Section 3, and rename the tau2 variant so the continuity is explicit.

---

Finally, we thank the reviewer for the suggestion to **move the hard-attention ablation into the main body**. We agree and are doing so. Your reading of it as a general lesson for multi-stage LLM pipelines is exactly the framing we will adopt.
