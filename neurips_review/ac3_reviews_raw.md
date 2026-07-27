#### Meta Review of Submission27902 by Area Chair PfEt

Meta Reviewby Area Chair PfEt21 Jul 2026, 22:09 (modified: 23 Jul 2026, 11:24)Senior Area Chairs, Area Chairs, Authors, Reviewers Submitted, Program Chairs, Area Chair PfEt[Revisions](https://openreview.net/revisions?id=Gyg84dbDYS)

**Metareview:**

The reviewers have serious reservations related to generalizability (method changes for each setting), validity of theoretical assumptions, and weaknesses in experimental evidence (including limited benchmarks, lack of statistical reporting, and mixed results) that seem to preclude a path toward publication at NeurIPS. The authors should absolutely feel free to rebut if the reservations have been made in error, but if the reservations are correct, then the concerns are too large to be dealt with in the rebuttal process and the authors are encouraged to submit the revised work elsewhere.

Add:

#### Official Review of Submission27902 by Reviewer iNYK

Official Reviewby Reviewer iNYK26 Jun 2026, 04:12 (modified: 23 Jul 2026, 09:29)Program Chairs, Senior Area Chairs, Area Chairs, Reviewers Submitted, Authors, Reviewer iNYK[Revisions](https://openreview.net/revisions?id=R78UYCzkMp)

**Summary:**

The paper tackles context pollution in multi-turn LLM use: the model's own earlier outputs accumulate in context and anchor later turns, so an early misinterpretation persists even after the user corrects it. Prior work uses Assistant Omission (AO), dropping all assistant messages, but the authors show this only works for self-contained turns and fails on referential ones, where partial work or tool-call state lives only in assistant turns.

They propose AC3, a training-free, inference-time method: a separate analyzer (1) extracts a clean task spec from user messages alone, with assistant turns structurally excluded, then (2) compares the assistant's history against that spec and edits the context (Augment/Reset/Rewrite, optionally gated) to keep verified work and remove invalidated reasoning. A lightweight memory ("cheatsheet") accumulates transferable analysis principles.

A key finding: pollution is contagious: if the spec extractor sees assistant messages, accuracy drops below baseline, so structural exclusion (not just prompting) is essential.

**Contribution Type:** General: Most submissions will fall into this type.

**Strengths And Weaknesses:**

Strengths

The self-contained vs. referential distinction cleanly explains why AO is near-perfect in some settings and collapses to zero in others, and the four benchmarks are ordered along exactly this referentiality axis.

Backed by the Table 5 ablation (prompt-level instructions to ignore assistant turns are insufficient; structural exclusion is required), the direction is convincing—and the observation that a contaminated two-stage pipeline underperforms a contaminated single-pass one carries a useful lesson for any multi-stage LLM pipeline.

Weaknesses LiC has only 18–25 samples per cell, and only Gated-Reset was replicated three times (std 5–7pp), so several-point gaps sit within noise. The "exceeds the oracle on database" result (48% vs. 32%) comes from a single Reset run, whereas the replicated Gated-Reset averages only 38.7%.

The Table 2 hard subset is the 20 hardest items chosen by baseline failure rate, and the runs replay GPT-5.2 trajectories rather than each model's own generations. Selection on the trajectory, compounded by regression to the mean, will make almost any reasonable intervention look strong on such a subset; the setup therefore measures "how much can be recovered from a fixed polluted history," not native multi-turn behavior, making the +20–42pp claim weaker than it appears.

The abstract and Figure 1 repeatedly call AC3 "the only method robust across the spectrum," yet on tau2-bench the per-trial numbers in Appendix B.6 give Baseline a mean of 53.3% and Gated-Reset 48.3%, roughly 5 points below baseline on the mean. Table 1d reports best-of-3 (60 vs. 65), which masks the negative mean. "Robust" here means "did not collapse," not "better," and it still adds up to ~20% cost per turn.

**Quality:** 2: not good

**Clarity:** 3: good

**Significance:** 3: good

**Originality:** 2: not good

**Questions:**

Can you re-report Reset vs. Baseline on a random subset, or one selected independently of baseline results? If the gains survive on an unbiased subset, this will better support the argument; if they largely vanish, the generalization claim should be removed.

Please report Baseline and Gated-Reset as the mean ± std over the three seeds rather than best-of-3, and state explicitly whether AC3's mean clears baseline.

**Limitations:**

yes

**Rating:** 3: Borderline reject: Technically solid paper where reasons to reject, e.g., limited evaluation, outweigh reasons to accept, e.g., good evaluation. Please use sparingly.

**Confidence:** 3: You are fairly confident in your assessment. It is possible that you did not understand some parts of the submission or that you are unfamiliar with some pieces of related work. Math/other details were not carefully checked.

**Ethical Concerns:** NO or VERY MINOR ethics concerns only

**Paper Formatting Concerns:**

No obvious violations observed.

**Code Of Conduct Acknowledgement:** Yes

**Responsible Reviewing Acknowledgement:** Yes

Add:

#### Official Review of Submission27902 by Reviewer Vg97

Official Reviewby Reviewer Vg9725 Jun 2026, 23:00 (modified: 23 Jul 2026, 09:29)Program Chairs, Senior Area Chairs, Area Chairs, Reviewers Submitted, Authors, Reviewer Vg97[Revisions](https://openreview.net/revisions?id=mm3AKaKO0J)

**Summary:**

The paper studies multi-turn LLM degradation caused by “context pollution”. To address this, the paper proposes Agentic Conversation Context Curation (AC3), a training-free inference-time framework that uses an analyzer subroutine to extract a clean task specification from user turns, evaluate prior assistant outputs against that specification, and then edit the conversation context through strategies like augmentation, reset, or rewrite. The paper evaluates AC3 across Lost in Conversation, CollabLLM, WildChat, and tau2-bench, and reports that AC3 improves over full-context baselines on several self-contained and conversational settings. The authors also show that AC3 wins pairwise comparisons on WildChat, and avoids the catastrophic failure of assistant omission in stateful tool-use settings.

**Contribution Type:** General: Most submissions will fall into this type.

**Strengths And Weaknesses:**

Strengths:

- The paper addresses an important problem: how to manage LLM conversation history when prior assistant messages are neither uniformly useful nor harmful.
- The distinction between self-contained turns and referential/stateful turns is well motivated.
- The paper correctly points out that assistant omission is not a general-purpose fix once users refer back to assistant-produced artifacts or once tool-call results live in assistant turns.
- The hard-attention ablation shows that an analyzer can itself be contaminated by assistant messages; this is a useful empirical observation and supports the structural-exclusion design proposed in the paper. Maybe this should be considered being moved to the main section instead of the appendix section.

Weakness:

- The central weakness is the set of baselines in the experiment. The main comparisons are full context, assistant omission, concatenated user messages, and ERGO. These are useful diagnostic baselines, but they are not sufficiently strong or comprehensive for a paper making claims about robust context management across multi-turn conversations. In particular, the paper should compare against recent stronger context-condensation/context-management methods such as MT-OSC [1]. Also, the related-work section discusses U-Fold, Context-Folding, and MemoBrain, and argues that they mainly address compaction rather than pollution. I find this distinction make sense, but not sufficient to rule them out as empirical baselines. Since AC3 claims robustness across self-contained, referential, and stateful regimes, the evaluation should include at least one strong recent context-condensation baseline for multi-turn chat, such as MT-OSC on the overlapping LiC-style benchmarks, and one strong user-centric agent context-folding baseline, such as U-Fold on tau2-bench. Either way, the authors should include them where feasible or clearly justify why they cannot be adapted.
- Another concern is the statistical reliability. Many of the headline LiC cells use small sample sizes, with only the Gated-Reset row repeated three times. The authors are appropriately transparent that they do not report error bars on every cell, but this substantially weakens the strength of the claims, especially because the method introduces additional stochastic LLM calls. The tau2-bench result is also not very persuasive as currently presented: the main table reports best-of-3 for Baseline and AC3-Gated-Reset, while the appendix shows high variance and indicates that AC3 is statistically within trial noise of the baseline.
- A third concern is that the method changes substantially across settings. For example, on LiC, the central AC3 design relies on hard-attention extraction from user messages only. On CollabLLM, the paper uses Rewrite without structural exclusion because intent may weave across assistant turns. On tau2-bench, the analyzer is reframed as “strategic reflection,” tracks environment state, and caps resets. These adaptations may be reasonable, but they make the overall contribution less clear: it is not obvious whether the paper is validating a single method, a family of prompt-engineering patterns, or several task-specific context-management variants.

References: [1] Singh, J., Tu, F., Ballesteros, M., Sun, W., Ghoshal, S., Yuan, M., Benajiba, Y., Ravi, S. and Roth, D., 2026. Mt-osc: Path for llms that get lost in multi-turn conversation. arXiv preprint arXiv:2604.08782.

**Quality:** 2: not good

**Clarity:** 3: good

**Significance:** 3: good

**Originality:** 3: good

**Questions:**

1. Can the authors compare against stronger context-management baselines as described in the weakness section? Otherwise, the authors should be able to clearly justify why the stronger baselines cannot be adapted in the experiments.
2. Can the authors report statistically sound results for the main claims? Please provide confidence intervals, paired tests, or bootstrap analyses for LiC and WildChat, and report mean ± variance rather than best-of-3 on tau2-bench.
3. How sensitive are the results to the analyzer model and compute budget? In the paper, it shows that AC3 uses additional LLM calls per turn. A fair comparison should include equal-budget baselines, such as repeated generation, self-reflection, or a strong summarizer/condensor using the same model and number of calls. Please also report latency implications, not just API cost.
4. Please clarify what exactly is the general AC3 algorithm across benchmarks? The LiC setting uses hard attention, CollabLLM uses single-pass Rewrite without structural exclusion, and tau2-bench uses a strategic-reflection variant. Please clarify which components are essential and which are task-specific adaptations.

**Limitations:**

Please refer to the comments from the previous sections (e.g. weakness and questions).

**Rating:** 3: Borderline reject: Technically solid paper where reasons to reject, e.g., limited evaluation, outweigh reasons to accept, e.g., good evaluation. Please use sparingly.

**Confidence:** 4: You are confident in your assessment, but not absolutely certain. It is unlikely, but not impossible, that you did not understand some parts of the submission or that you are unfamiliar with some pieces of related work.

**Ethical Concerns:** NO or VERY MINOR ethics concerns only

**Paper Formatting Concerns:**

No paper formatting concerns.

**Code Of Conduct Acknowledgement:** Yes

**Responsible Reviewing Acknowledgement:** Yes

Add:

#### Official Review of Submission27902 by Reviewer 5YHP

Official Reviewby Reviewer 5YHP21 Jun 2026, 18:40 (modified: 23 Jul 2026, 09:29)Program Chairs, Senior Area Chairs, Area Chairs, Reviewers Submitted, Authors, Reviewer 5YHP[Revisions](https://openreview.net/revisions?id=P4udIHICyg)

**Summary:**

This paper studies context pollution in multi-turn language-model interactions: incorrect assumptions introduced in an assistant’s early responses may remain in the conversation history and continue to bias later responses, even after the user provides corrective information.

The paper proposes Agentic Conversation Context Curation (AC3), a training-free inference-time framework that uses an auxiliary analyzer before each assistant turn. AC3 first constructs a consolidated task specification, then evaluates the assistant’s previous work against that specification, and finally modifies the context using one of three operators: Augment, Reset, or Rewrite. A gating mechanism can avoid intervention when no issue is detected. The paper also explores a lightweight memory mechanism that accumulates reusable context-curation heuristics across instances.

The method is evaluated on four settings with increasing dependence on assistant history: Lost in Conversation (LiC), CollabLLM, WildChat, and the telecom subset of tau2-bench. The results show substantial improvements over full-context baselines on LiC, strong pairwise preferences over both full context and assistant omission on WildChat, and that selective context management remains operational in stateful tool use where assistant omission destroys necessary tool history.

**Contribution Type:** General: Most submissions will fall into this type.

**Strengths And Weaknesses:**

Strengths

1. Strong and useful problem framing. The paper clearly identifies the central tension in multi-turn context management: previous assistant messages can contain both invalidated reasoning and indispensable task state. This is a meaningful conceptual improvement over treating all assistant-generated context as uniformly harmful. The framing is likely to be relevant to conversational assistants, coding agents, and tool-using systems.
2. The structural-exclusion result is compelling. The hard-attention ablation is one of the strongest parts of the paper. When the specification extractor is allowed to see assistant messages, performance drops substantially and can fall below the full-context baseline. The observation that decomposition can amplify errors when an upstream stage produces a biased specification is important beyond this particular implementation. It suggests that information-flow constraints, rather than prompt instructions alone, may be necessary when using LLMs to audit potentially misleading context.
3. The paper studies multiple levels of referentiality. Evaluating LiC, CollabLLM, WildChat, and tau2-bench is a reasonable attempt to test the method beyond a single benchmark. In particular, the tau2-bench experiment illustrates a real limitation of assistant omission: removing assistant messages also removes tool observations and causes the agent to lose environmental state. The WildChat results also suggest that selective editing can be preferable to either retaining or deleting the full history.
4. The method is modular and practically interpretable. The separation between specification extraction, approach evaluation, and intervention is easy to understand. The Augment, Reset, Rewrite, and gating variants expose meaningful engineering tradeoffs. The paper is also generally well written, and the appendices disclose several important protocol details, including replay evaluation, variance, prompt configurations, and the limited scope of the agentic experiments.

Weaknesses

1. The strongest mechanism relies on an assumption that does not hold in the most important referential settings. AC3’s strongest LiC results rely on extracting a task specification from user messages while structurally excluding all assistant messages. This works because LiC is constructed from an originally self-contained single-turn problem. However, in genuinely referential interactions, the user may say “modify the second paragraph” or “extend the previous query,” where the referent exists only in the assistant history. Appendix D confirms this: the more realistic soft-attention variant, which must see the full conversation, performs substantially worse than hard attention across math, code, and database tasks. Memory only partially closes this gap and provides very limited improvement on code. Consequently, the paper convincingly demonstrates that structural exclusion works when user messages independently specify the task, but it does not yet solve the harder problem of accurately separating useful and harmful assistant content when both must be visible to the analyzer. This limits the main claim that AC3 provides a robust solution across referentiality regimes.
    
2. The evaluated system is not a single fixed method across benchmarks. The paper adapts the analysis and intervention pipeline to each setting. LiC uses two-stage user-only specification extraction and Reset/Gated Reset; CollabLLM uses a full-transcript, single-pass Rewrite because structural exclusion is inappropriate; WildChat evaluates several different operators; and tau2-bench modifies the analyzer toward strategic reflection and state tracking.
    
3. The LiC evidence is limited by small samples, replay evaluation, and mostly single-run results. Per-task sample sizes are modest, so several reported differences correspond to only a few examples. Only Gated Reset is evaluated over three reruns; most other AC3 and memory rows are single-trial point estimates. No paired significance tests or confidence intervals are reported in the main table. In addition, the LiC experiments use replay mode: all methods receive the same pre-generated conversation trajectory and only regenerate the final response. This isolates recovery from a fixed polluted context, but it does not evaluate the effect of deploying AC3 throughout an interaction. Early rewrites could change subsequent assistant behavior, user-simulator responses, and the accumulation of state. The results should therefore be interpreted as final-turn recovery experiments rather than end-to-end multi-turn improvements.
    
4. The evidence in the more referential settings is less conclusive than the headline presentation suggests. On CollabLLM, AC3 Rewrite is below assistant omission on MATH-Hard and tied with assistant omission on BigCodeBench. Therefore, this experiment supports improvement over full context but not an advantage over blanket omission. Moreover, BigCodeBench cannot be evaluated with its normal executable tests because the simulator does not communicate the required function signatures; the paper replaces execution with a GPT-5 correctness judge. This substantially changes the interpretation of the benchmark and introduces model-judge uncertainty. The WildChat results are strong in terms of pairwise win rate, but they measure static continuation quality on fixed transcripts rather than end-to-end human interaction. They also rely on an LLM judge instead of direct task success or a new human evaluation. Reset and Rewrite naturally produce more consolidated and explicit responses, which may be favored by a pairwise judge even when factual or task-level improvements are less clear. The paper does not report judge agreement, position-bias checks, or human validation specifically for the evaluated outputs. The compared methods also have slightly different sample counts.
    
5. The analyzer is not directly evaluated as a pollution detector or preservation mechanism. The method is motivated as identifying invalidated reasoning while preserving useful work, but the paper evaluates only downstream answer quality. It does not measure whether the analyzer correctly identifies polluted spans, preserves necessary state, or triggers gating at the appropriate times. In WildChat, Gated Reset edits approximately 72% of turns, but there is no precision/recall analysis of the issue detector or breakdown of harmful false-positive edits and missed pollution. Direct annotations of which historical statements are stale, which are useful, and which must be preserved would make the mechanism substantially more interpretable. Such annotations would also help distinguish genuine context auditing from the analyzer simply re-solving the task.
    
6. The memory results are mixed and not yet well characterized. Memory provides substantial gains in some settings but is neutral or harmful in others. This suggests that the cheatsheet can introduce stale or overly general priors, which is itself a form of context pollution at the analyzer level. More analysis of memory order sensitivity, train/evaluation separation, and failure cases would be useful before presenting memory as a generally beneficial extension.
    

Overall, the paper is clearly written, with an important architectural insight regarding structural context exclusion. However, the empirical evidence currently supports a narrower conclusion than the paper’s main narrative: AC3 is effective for recovering from fixed polluted histories in self-contained tasks, and selective editing is more compatible with referential state than blanket omission. It is not yet convincingly demonstrated that AC3 provides a unified, reliable improvement for genuinely referential and stateful long-horizon interaction.

**Quality:** 3: good

**Clarity:** 2: not good

**Significance:** 3: good

**Originality:** 3: good

**Questions:**

I've addressed all of my questions in the previous section.

**Limitations:**

yes.

**Rating:** 3: Borderline reject: Technically solid paper where reasons to reject, e.g., limited evaluation, outweigh reasons to accept, e.g., good evaluation. Please use sparingly.

**Confidence:** 3: You are fairly confident in your assessment. It is possible that you did not understand some parts of the submission or that you are unfamiliar with some pieces of related work. Math/other details were not carefully checked.

**Ethical Concerns:** NO or VERY MINOR ethics concerns only

**Paper Formatting Concerns:**

None

**Code Of Conduct Acknowledgement:** Yes

**Responsible Reviewing Acknowledgement:** Yes