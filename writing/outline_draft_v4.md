# Recovering from Context Contamination in Multi-Turn LLM Conversations

---

## Abstract

Large language models suffer systematic performance degradation in multi-turn conversations: when task specifications are revealed incrementally, models overcommit to early incorrect assumptions and cannot self-correct because flawed reasoning persists in context. We term this *context contamination* and show it operates through two mechanisms: (1) user intent becomes fragmented across turns, and (2) the assistant's prior incorrect reasoning anchors future generation. We introduce an *executive function* framework that addresses both: an LLM-as-analyzer extracts a clean task specification from user messages alone (addressing intent fragmentation) and identifies correct versus harmful content in the assistant's responses (addressing reasoning contamination). A key finding is that executive dysfunction is pervasive: even an external analyzer model is susceptible to the same anchoring when exposed to assistant messages, so the data flow must be designed to physically exclude them during intent extraction. On the Lost in Conversation benchmark, our methods improve accuracy from 60% to 90% on math, 16% to 72% on code, 4% to 44% on database, and 9% to 30% on actions. Ablation studies confirm that shielding the analyzer from assistant messages is load-bearing (removing it collapses gains to zero) and that context removal provides additional benefit beyond analysis alone, particularly on multi-output tasks.

---

## 1. Introduction

The deployment of large language models increasingly involves multi-turn conversations. Users rarely specify complete requirements upfront; instead, they iteratively clarify, correct, and extend their requests across multiple exchanges. This conversational pattern is natural for humans but creates a fundamental problem for LLMs: once the model commits to an interpretation in an early turn, the resulting reasoning persists in context and anchors all subsequent generation, even when later user messages contradict the initial assumptions.

Laban et al. (2025) quantified this through the "Lost in Conversation" (LiC) framework, a large-scale simulation across 15 LLMs and 6 task domains. Their core finding is striking: the performance gap between single-turn and multi-turn settings is driven primarily by *unreliability* (112% increase), not reduced *aptitude* (only 16% decrease). The capability is preserved, but the model fails to access it reliably. We call this degradation mechanism *context contamination*: earlier assistant outputs introduce errors, incorrect assumptions, and speculative content that propagate across turns, anchoring future generation on flawed foundations.

We identify two distinct mechanisms driving context contamination:

1. **User intent fragmentation.** In multi-turn conversations, the user's actual request is scattered across turns — paraphrased, revised, and buried in conversational noise. The model must reconstruct what the user wants from incomplete, non-linear input, and frequently fails.

2. **Reasoning contamination.** The assistant's prior (often incorrect) reasoning remains in context and anchors future responses. Even when later user messages contradict earlier assumptions, the model cannot un-see its own mistakes.

These two problems require different solutions. Intent fragmentation is addressed by *task specification reconstruction*: an independent extraction of what the user wants from their messages alone, free from the assistant's interpretive lens. Reasoning contamination is addressed by *context editing*: surgically removing harmful content while preserving correct progress.

Both solutions require designing the data flow around executive dysfunction: the analyzer model itself cannot reliably ignore assistant messages even when instructed to, so we physically exclude them from the stage that extracts user intent. We show that this separation is load-bearing — without it, even an external analyzer model falls prey to the same anchoring phenomenon, producing analysis that reflects the assistant's errors rather than correcting them.

This pattern has a direct analogue in cognitive psychology. When humans face situations with distracting, contradictory, or outdated information, they rely on *executive function*: the set of higher-order cognitive processes that manage attention, inhibit prepotent but incorrect responses, and flexibly update working memory representations (Miyake et al., 2000; Diamond, 2013). Current LLMs lack this regulatory capacity — they have no mechanism to step outside the conversation, evaluate whether their own prior outputs are helping or harming, and selectively suppress contaminating content.

We introduce a framework of test-time methods centered on the idea of *executive function for LLM conversations*. Rather than fine-tuning models to resist context contamination, we invest additional inference-time compute in an external executive layer that monitors, diagnoses, and corrects the conversation trajectory. This executive layer operates through three capacities that mirror the core components of human executive function:

- **Monitoring and intent extraction.** A conversation analyzer extracts a clean task specification from user messages alone, reconstructing fragmented user intent without contamination from the assistant's prior reasoning.

- **Inhibition and context editing.** When the analyzer identifies harmful content in the assistant's responses, the context is surgically rewritten: erroneous content is removed while correct progress is preserved. This prevents contaminating content from anchoring future generation.

- **Meta-cognitive learning.** A Dynamic Cheatsheet mechanism accumulates transferable editing principles across problem instances, partially amortizing the cost of test-time intervention through cross-instance learning.

---

## 2. Related Work

### 2.1 Lost in Conversation

Laban et al. (2025) introduced the Lost in Conversation (LiC) framework, demonstrating that LLMs suffer systematic performance degradation in multi-turn, underspecified conversations. Their methodology takes single-turn problems (where models achieve high accuracy) and "shards" them: the complete specification is split into pieces that are revealed incrementally by a simulated user across multiple turns. The key findings are: (1) performance drops 39% on average compared to single-turn, (2) the degradation is primarily unreliability (+112%) rather than reduced aptitude (-16%), (3) all 15 tested models exhibit similarly high multi-turn unreliability, and (4) interventions within the same conversation context fail to close the gap — only starting a new conversation with consolidated information recovers performance.

We adopt the LiC simulation framework as our primary evaluation setting because it provides controlled, reproducible multi-turn scenarios with known ground truth.

### 2.2 ERGO: Entropy-Guided Context Resetting

Khalid et al. (2025) proposed ERGO, which monitors token-level Shannon entropy at each turn and triggers a context reset when the entropy delta exceeds a calibrated threshold. Upon reset, all prior user messages are summarized into a single prompt and all assistant messages are discarded. ERGO achieves a 56.6% average performance gain on LiC. However, it requires logprob access (which many API providers limit), its reset discards all assistant messages entirely (recovering the single-turn baseline), and the entropy threshold is calibrated per-model. Our approach differs in using the LLM itself to decide when and how to intervene (requiring only black-box API access) and preserving edited assistant content rather than discarding it.

### 2.3 Do LLMs Benefit from Their Own Words?

Huang et al. (2026) investigated whether prior assistant responses help or hurt in multi-turn conversations. They found that omitting all prior assistant responses frequently does not hurt, and sometimes improves, response quality — terming this "context pollution." Their key insight that one-sentence summaries outperform both full context and full omission directly supports our thesis: intelligent compression beats both extremes. However, their approach makes a binary per-turn choice (keep all or omit all) and requires model-specific training.

### 2.4 CollabLLM

[TODO: CollabLLM paper description.]

### 2.5 Test-Time Scaling and Inference-Time Compute

The broader test-time scaling literature investigates how additional inference-time compute can improve model performance without parameter updates, including chain-of-thought reasoning (Wei et al., 2022), self-consistency (Wang et al., 2023), tree-of-thought search (Yao et al., 2024), and verifier-guided search (Cobbe et al., 2021). These methods focus on single-turn settings, scaling compute within a single generation. Our work extends test-time scaling to the *multi-turn* setting, where the challenge is not generating a better single response but managing accumulated context across turns.

### 2.6 Dynamic Cheatsheet

Suzgun et al. (2025) introduced the Dynamic Cheatsheet, a mutable text document that accumulates task-relevant knowledge across problem instances at test time without gradient updates. We adapt this for context editing, targeting the cheatsheet at the analyzer rather than the assistant itself.

---

## 3. Methods

### 3.1 Problem Setting

We adopt the LiC simulation framework. A single evaluation instance consists of:

- A **task** with a fully-specified question $q$ and ground truth answer $a$
- A **sharding** of $q$ into $k$ shards $\{s_1, \ldots, s_k\}$ that partition the specification
- A **simulated user** that reveals shards incrementally across turns, paraphrasing and reordering
- An **assistant** (the model under evaluation) that must gather information and produce a correct answer
- A **system agent** that classifies each assistant response and evaluates correctness

The conversation proceeds for up to $T$ turns. At each turn: the user reveals a shard, the context strategy prepares the message history, the assistant generates a response, and the system agent evaluates.

### 3.2 Conversation Analyzer: Two-Query Architecture

The analyzer is the core component, shared by all intervention strategies. It uses a two-query design that accommodates executive dysfunction by controlling what the model sees at each step.

**Query 1 (Task Specification).** Sees the system message and all user messages. No assistant responses. Produces a consolidated task specification — a clean restatement of what the user is asking for. The system message grounds the specification in the correct output format (e.g., SQL against a specific schema, function calls with specific signatures), preventing over-elaboration.

**Query 2 (Comparison).** Sees the task specification from Query 1 plus the full conversation history, and optionally a memory cheatsheet. Produces an assessment of what the assistant got right (`aligned`) and what contradicts the specification (`issues`).

The reason for splitting the analysis into two queries is that the model cannot reliably extract user intent when assistant messages are present — it anchors on the assistant's framing even when instructed to focus on user messages. By physically excluding assistant messages from Query 1, we design around this limitation rather than attempting to prompt through it. We show in Section 5.2 that including assistant messages in Query 1 collapses the system's effectiveness to baseline or worse.

### 3.3 Context Strategies

Four strategies use the analyzer's output differently:

**Baseline (no intervention).** The full conversation history passes unchanged to the assistant.

**Append Analysis.** The analyzer runs and its output (task specification + aligned + issues) is appended to the conversation before the assistant's next turn. The full history is preserved — the analysis provides corrective signal but contaminating content remains visible.

**Always-Reset.** The analyzer runs and its output is used to *replace* the conversation: all prior messages are removed and replaced with a compacted context containing the task specification and aligned content. Issues guide the edit but are not reintroduced. This removes contaminating content entirely but loses any useful context not captured in the analysis.

**Gated Reset.** Like Always-Reset, but the context is only replaced when the analyzer detects substantive issues. When no issues are found, the conversation passes through unchanged.

### 3.4 Memory-Based Learning (Meta-Cognitive Layer)

The Dynamic Cheatsheet accumulates editing principles across problem instances, injected into the analyzer's Query 2 prompt. Memory is not used in Query 1 (task specification extraction must remain uncontaminated).

**Update Mechanism: Reflect-then-Unify.** After processing a batch of problems: (1) *Reflect* — for each trajectory, an LLM generates generalizable takeaways from the outcome, with access to the current cheatsheet, the rendered trajectory, and optionally ground truth; (2) *Unify* — a single LLM call merges new takeaways with the current cheatsheet, deduplicating and resolving contradictions.

**Memory Target.** For strategies with an analyzer (Append Analysis, Context Edit), memory is targeted at the analyzer's comparison query. For the baseline, memory is injected into the assistant's system message. Targeting the executive layer is more effective than targeting the assistant directly.

**Content Discipline.** The *type* of knowledge matters more than the update mechanism. Meta-level principles transfer well ("verify output format matches user specification," "reject assistant assumptions not grounded in user messages"). Task-specific content (algorithmic recipes, code snippets) causes the executive layer to anchor on stale patterns — recreating the failure mode we are correcting. We cap cheatsheet length at 1500 words.

---

## 4. Experiments

### 4.1 Evaluation Framework

We evaluate on the Lost in Conversation benchmark across four task domains:

| Task | Domain | Evaluation | Samples |
|------|--------|------------|:-------:|
| **Math** | Word problems | Exact numerical match | 20 |
| **Code** | Function implementation | Functional correctness | 19 |
| **Database** | SQL generation | Execution match | 25 |
| **Actions** | Parallel function calls | AST match | 23 |

Sample counts reflect filtering of user-simulator-induced errors (see Section 4.3).

**Models.** GPT-5-mini for assistant and analyzer. GPT-4o-mini for simulated user and system agents.

**Replay mode.** To isolate the effect of our interventions from conversational variance, we use a replay methodology: all strategies share the same baseline conversation prefix (from an unmodified S0 run) and only the final assistant turn is regenerated with the intervention applied. This ensures identical conversational context across conditions.

### 4.2 Experimental Conditions

| Condition | Analysis | Context | Memory |
|-----------|:--------:|:-------:|:------:|
| Baseline | — | Full | — |
| Baseline + Memory | — | Full | Assistant |
| Append Analysis | Two-query | Full + appended | — |
| Append Analysis + Memory | Two-query | Full + appended | Analyzer |
| Always-Reset | Two-query | Replaced | — |
| Always-Reset + Memory | Two-query | Replaced | Analyzer |
| Gated Reset | Two-query | Conditional | — |

Memory experiments use batched execution (batch size 5) with continual learning and oracle-guided reflection (ground truth available during cheatsheet updates).

### 4.3 User Simulator Quality Control

The sharded disclosure format occasionally produces user messages that distort the original problem, making the task unsolvable regardless of the assistant's capability. We pre-screen baseline traces using an LLM judge that compares the union of user simulator messages against the original single-turn question and flags cases where critical details are absent or materially changed. Flagged samples are excluded from all conditions (3 math, 6 code, 0 database, 2 actions). This ensures accuracy denominators reflect problems the assistant could reasonably solve.

### 4.4 CollabLLM Setting

[TODO: Describe CollabLLM experimental setup.]

---

## 5. Results

### 5.1 Main Results

We present the main results in two parts: the effect of intervention strategy (Table 1), and the effect of adding memory (Table 2).

**Table 1: Effect of intervention strategy (no memory)**

| Strategy | Math | Code | Database | Actions |
|----------|:----:|:----:|:--------:|:-------:|
| Baseline | 60% | 16% | 4% | 9% |
| Append Analysis | 80% | 56% | 32% | 22% |
| Context Edit | 80% | 69% | 40% | **30%** |
| Gated Context Edit | 75% | **72%** | **44%** | 13% |

**Table 2: Effect of adding memory**

| Strategy | Math | Code | Database | Actions |
|----------|:----:|:----:|:--------:|:-------:|
| Baseline | 60% | 16% | 4% | 9% |
| Baseline + Memory | 55% | 21% | 4% | 9% |
| Append Analysis | 80% | 56% | 32% | 22% |
| Append Analysis + Memory | **90%** | **68%** | **44%** | 9% |
| Context Edit | 80% | 69% | 40% | 30% |
| Context Edit + Memory | 85% | 68% | **44%** | **30%** |

Note: Some conditions had timeout errors reducing effective sample sizes. See Appendix B for per-condition sample counts.

#### Analysis alone captures the majority of gains (Table 1)

The largest jump is from Baseline to Append Analysis: +20pp on math, +40pp on code, +28pp on database, +13pp on actions. This gain comes primarily from the task specification — a clean, consolidated restatement of user intent extracted from user messages alone, without the assistant's prior responses. Further evidence comes from the spec-only ablation (Section 5.2), which shows the task specification alone captures most of the improvement.

#### Context editing provides additional benefit on complex tasks (Table 1)

Context Edit outperforms Append Analysis on database (+8pp), actions (+8pp), and code (+13pp). Both strategies use identical analysis; the only difference is whether the assistant sees the full conversation history or a compacted version. The improvement demonstrates that reasoning contamination — the assistant anchoring on its prior incorrect responses — is a real and measurable problem beyond intent fragmentation.

The gap is largest on actions, the most structurally complex task (requiring multiple simultaneous function calls). This suggests context removal matters most when the assistant must coordinate multiple outputs, where prior partial/incorrect attempts create stronger anchoring.

#### Gated Context Edit is unreliable

Gated Context Edit adds a decision step: only edit when the analyzer detects issues, otherwise pass the conversation through unchanged. This is worse than always editing on math (-5pp) and actions (-17pp). The gate's false negatives are costly: when the analyzer decides no edit is needed but the assistant is actually wrong, the assistant receives no corrective signal at all. Always editing avoids this by consistently providing the clean task specification.

#### Memory amplifies analysis quality (Table 2)

Append Analysis + Memory is the strongest overall configuration, achieving the best results on math (90%), code (68%), and database (44%). Sample-level comparison shows +8 new correct answers and zero regressions across these three tasks. Memory helps the analyzer produce more decisive task specifications and more concrete error identification.

On single-output tasks, memory closes the gap between Append Analysis and Context Edit: Append Analysis + Memory matches or exceeds Context Edit on math (90% vs 80%), code (68% vs 69%), and database (44% vs 40%). This suggests that for tasks where rederivation is cheap, better analysis quality can substitute for context removal.

Memory cannot overcome structural barriers: on actions, where the primary failure mode is the user simulator revealing function calls one at a time (an accumulation problem, not an analysis problem), memory provides no benefit. Context Edit remains the only strategy that improves on actions beyond the no-memory Append Analysis baseline.

### 5.2 Ablation: Does the Analyzer Need to Be Shielded from Assistant Messages?

The two-query architecture omits assistant messages from the task specification query. Is this separation necessary, or can the analyzer extract user intent reliably from the full conversation?

We test four configurations varying two axes: (1) whether the task specification query sees only user messages (*assistant-omitted*) or the full conversation (*full-conversation*), and (2) whether the system uses one query (spec only) or two (spec + comparison).

**Table 3: Analyzer input ablation (Append Analysis, no memory)**

| Configuration | Math | Code | Database |
|---------------|:----:|:----:|:--------:|
| Assistant-omitted, spec only (1 query) | 70% | 63% | 40% |
| Assistant-omitted, spec + comparison (2 queries) | **80%** | 56% | 32% |
| Full-conversation, combined (1 query) | 55% | 21% | 4% |
| Full-conversation, spec + comparison (2 queries) | 40% | 11% | 8% |
| Baseline (no analysis) | 60% | 16% | 4% |

#### Shielding the analyzer from assistant messages is load-bearing

When the analyzer sees assistant messages during task specification construction, the resulting analysis collapses to baseline or worse. Both full-conversation variants produce analysis that is not just unhelpful but *actively harmful*: the full-conversation two-query variant performs below baseline on math (40% vs 60%) and code (11% vs 16%).

This is evidence that executive dysfunction is pervasive: it extends beyond the conversational assistant to any model processing the conversation. Even an external model explicitly tasked with critical analysis anchors on the assistant's reasoning when exposed to it. The two-query design is not an arbitrary architectural choice — it is the minimal accommodation for a demonstrated cognitive limitation of current LLMs.

#### Contamination amplifies through chained queries

The full-conversation two-query variant (40% math, 11% code) underperforms the full-conversation single-query variant (55% math, 21% code). When Query 1 produces a contaminated task specification and passes it to Query 2 as authoritative ground truth, the contamination compounds. Each pipeline stage inherits and amplifies errors from the prior stage. This contamination amplification is a failure mode specific to chained LLM calls and suggests caution when designing multi-stage inference pipelines.

#### The task specification alone is surprisingly effective

The assistant-omitted spec-only variant (one query, no comparison) matches or exceeds the full two-query system on code (63% vs 56%) and database (40% vs 32%) at half the LLM cost. The comparison query adds value on math (+10pp) but introduces noise on structured-output tasks. This suggests a task-adaptive approach: spec-only for tasks with well-defined output formats, full analysis for tasks requiring nuanced error identification.

### 5.3 Ablation: Can Context Editing Rescue Contaminated Analysis?

If the analysis is contaminated (built from the full conversation including assistant messages), can we still extract value by removing the bad conversation context and presenting only the analysis? We test Context Edit and an LLM-based compaction variant on top of the full-conversation analysis from Section 5.2.

**Table 4: Context editing with contaminated vs. clean analysis**

| Strategy | Math | Code | Database |
|----------|:----:|:----:|:--------:|
| Baseline | 60% | 16% | 4% |
| Full-conversation analysis, appended | 55% | 21% | 4% |
| Full-conversation analysis, context edit | 55% | 26% | 4% |
| Full-conversation analysis, LLM compaction | 55% | 22% | 12% |
| Assistant-omitted analysis, appended | **80%** | **56%** | **32%** |
| Assistant-omitted analysis, context edit | **80%** | **69%** | **40%** |

Context editing cannot rescue contaminated analysis. The bottleneck is analysis quality, not delivery mechanism. Context editing is a *force multiplier* on analysis quality: with clean analysis it provides +8–13pp over appending; with contaminated analysis it provides nothing. This confirms that omitting assistant messages from the analyzer is the foundational architectural requirement, not an optional optimization.

### 5.4 CollabLLM Setting

[TODO: Results showing context editing effectiveness in the collaborative LLM setting, where the user iteratively refines requirements. Early results show positive improvement on math and code.]

---

## 6. Discussion

### 6.1 Two Problems, Two Solutions

Our results reveal that multi-turn performance degradation operates through two distinct mechanisms that are separable in our framework.

**User intent fragmentation** is the dominant factor on the LiC benchmark. The task specification alone — a clean extraction of user intent from user messages — recovers most of the single-turn performance. This is because LiC tasks are single-answer problems where rederivation is trivial: once the model knows what to compute, it can produce the answer without reference to its prior attempts.

**Reasoning contamination** is secondary but present. Always-Reset consistently outperforms Append Analysis on database (+8pp) and actions (+8pp), demonstrating that the assistant's prior incorrect reasoning does anchor its final response even when corrective analysis is available. The gap is largest on actions, the most complex task requiring coordination of multiple outputs — the closest LiC comes to stateful, multi-artifact work.

This decomposition has implications for benchmark design. LiC was constructed around simple, single-answer tasks to isolate the anchoring phenomenon. Our results suggest that more complex benchmarks — requiring multi-step reasoning, iterative artifact construction, or coordination across outputs — would show a larger role for context editing relative to task specification, because rederivation becomes expensive or impossible.

### 6.2 Executive Dysfunction Extends to External Analyzers

The assistant-omission finding has implications beyond our specific setting. LiC demonstrated that the conversational assistant cannot un-anchor from its own prior reasoning. We show that this executive dysfunction is not specific to the assistant role — it is a general property of how LLMs process multi-party conversation context. An external model tasked with *analyzing* the conversation exhibits the same anchoring when exposed to the assistant's responses, even when explicitly instructed to focus on user messages.

This means that multi-stage LLM pipelines cannot rely on prompting to achieve selective attention. Designing the data flow to exclude contaminating content — rather than instructing the model to ignore it — is the reliable approach. Any system that uses an LLM to evaluate, critique, or improve another LLM's output faces this risk.

The limitation of our approach is that it exploits a property specific to LiC: user messages alone fully specify the task. In realistic multi-turn settings (iterative design, multi-step reasoning, tool-use agents), the task specification may depend on prior assistant work. Extending assistant-omission to these settings — perhaps through hybrid approaches that separate user-specified constraints from assistant-generated state — is an important direction.

### 6.3 The Role of Memory

Memory provides consistent benefit when applied to Append Analysis (+10pp math, +12pp code, +12pp database) but is inconsistent with context editing strategies. The cheatsheet helps the analyzer produce better analysis, but its ~1000 words of procedural guidance can dilute the analyzer's natural reasoning when the analysis drives a binary decision (edit or not).

For Append Analysis, analysis quality matters but imperfect analysis is still useful — the assistant sees both the analysis and the original conversation and can integrate them. For context editing, the analysis *is* the sole context — errors in analysis become errors in the assistant's input with no fallback.

### 6.4 Limitations

**Sample sizes.** Our evaluation subsets are small (19–25 samples), constrained by multi-turn simulation cost. Effect sizes should be interpreted with appropriate caution.

**Simulated setting.** The LiC framework uses scripted shard reveals. Real conversations involve more diverse user behavior, including references to prior assistant responses.

**Task simplicity.** LiC's single-answer tasks favor task specification over context editing. More complex tasks (long-horizon coding, multi-artifact construction) would provide a stronger test of context editing's value.

**Single model family.** All experiments use GPT-5-mini. The interaction between our methods and different model architectures is unexplored.

---

## 7. Conclusion

We present an executive function framework for recovering from context contamination in multi-turn LLM conversations. Our key findings:

1. **Task specification reconstruction is the primary mechanism** for LiC-style benchmarks where rederivation is cheap. Extracting user intent from user messages alone — without the assistant's prior responses — recovers most of the single-turn performance.

2. **Executive dysfunction extends to external analyzers.** Without physically excluding assistant messages from the intent extraction step, even an external analyzer is contaminated by the same anchoring it tries to correct. Designing data flows around this limitation — rather than prompting through it — is essential.

3. **Context removal provides measurable additional benefit,** particularly on complex multi-output tasks. This motivates context editing for settings where tasks are stateful and rederivation is expensive.

4. **Memory-based learning amplifies analysis quality** when applied to the append-analysis strategy, but the benefit is sensitive to how the analysis is consumed downstream.

These results suggest a progression: for simple tasks, a clean task specification suffices; for moderately complex tasks, context removal adds value; for truly stateful long-horizon tasks, surgical context editing — preserving correct work while removing harmful content — should be essential. Future work on harder, more realistic benchmarks will test this progression.

---

## References

- Laban, P., et al. (2025). Lost in Conversation: A Large-Scale Simulation of Multi-Turn Problem-Solving Conversations with LLMs. *arXiv*.
- Khalid, M., et al. (2025). ERGO: Entropy-Guided Context Resetting for Multi-Turn Conversations. *arXiv*.
- Huang, X., et al. (2026). Do LLMs Benefit from Their Own Words? Understanding Context Pollution in Multi-Turn Conversations. *arXiv*.
- Suzgun, M., et al. (2025). Dynamic Cheatsheet: Test-Time Learning with Mutable Memory. *arXiv*.
- Miyake, A., et al. (2000). The Unity and Diversity of Executive Functions. *Cognitive Psychology*.
- Diamond, A. (2013). Executive Functions. *Annual Review of Psychology*.
- Wei, J., et al. (2022). Chain-of-Thought Prompting Elicits Reasoning in Large Language Models. *NeurIPS*.
- Wang, X., et al. (2023). Self-Consistency Improves Chain of Thought Reasoning in Language Models. *ICLR*.
- Yao, S., et al. (2024). Tree of Thoughts: Deliberate Problem Solving with Large Language Models. *NeurIPS*.
- Cobbe, K., et al. (2021). Training Verifiers to Solve Math Word Problems. *arXiv*.
- [TODO: CollabLLM reference]

---

## Appendix

### A. User Simulator Quality Control

[Detail the false negative analysis: user sim sufficiency check, samples excluded per task, methodology.]

### B. Per-Condition Sample Counts

[Table with raw numerator/denominator for each condition, for transparency. Explains timeout errors and exclusions.]

### C. Prompt Templates

[Key prompts: v8 task spec query, comparison query.]

### D. Cheatsheet Examples

[Beneficial vs harmful content, sanitization.]

### E. Trajectory Examples

[Annotated examples showing baseline failure → analysis → recovery for each task.]
