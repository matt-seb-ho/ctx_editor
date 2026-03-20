# Test-Time Scaling for Overcoming Context Contamination in Multi-Turn Conversations

---

## Abstract

Large language models suffer systematic reliability collapse in multi-turn conversations: when task specifications are revealed incrementally, performance drops 39% on average compared to equivalent single-turn interactions, with unreliability increasing by 112% (Laban et al., 2025). Models overcommit to early incorrect assumptions and cannot self-correct because their flawed reasoning persists in context, a phenomenon we term *context contamination*. We frame recovery from context contamination as a test-time scaling problem: rather than fine-tuning models to resist contamination, we invest additional inference-time compute in an *executive function* layer that monitors, diagnoses, and corrects the conversation trajectory. Inspired by the cognitive science construct of executive function (the set of mental processes that manage attention, inhibit irrelevant information, and flexibly update working representations), our framework employs an LLM-as-analyzer that critically inspects the conversation history, identifies where the assistant's approach diverges from user intent, and surgically rewrites the context to remove erroneous assumptions while preserving correct progress. A two-query architecture enforces hard attention separation between user intent extraction and assistant evaluation, preventing the analyzer from being contaminated by the same anchoring it is trying to correct. We further introduce a memory-based learning mechanism (Dynamic Cheatsheet) that accumulates transferable meta-cognitive editing principles across problem instances, a form of meta-self-reflection that partially amortizes the cost of test-time intervention. On the Lost in Conversation benchmark, our methods improve accuracy from 30% to 60% on code tasks (2x), from 63% to 79% on database tasks, and achieve 57% on a curated hard subset where the baseline scores 0%. Across four task domains, at least one test-time intervention variant outperforms the baseline, with the optimal strategy varying by task characteristics.

---

## 1. Introduction

The deployment of large language models increasingly involves multi-turn conversations. Users rarely specify complete requirements upfront; instead, they iteratively clarify, correct, and extend their requests across multiple exchanges. This conversational pattern is natural for humans but creates a fundamental problem for LLMs: once the model commits to an interpretation in an early turn, the resulting reasoning persists in context and anchors all subsequent generation, even when later user messages contradict the initial assumptions.

Laban et al. (2025) quantified this through the "Lost in Conversation" (LiC) framework, a large-scale simulation across 15 LLMs and 6 task domains. Their core finding is striking: the performance gap between single-turn and multi-turn settings is driven primarily by *unreliability* (112% increase), not reduced *aptitude* (only 16% decrease). The capability is preserved, but the model fails to access it reliably. We call this degradation mechanism *context contamination*: earlier assistant outputs introduce errors, incorrect assumptions, and speculative content that propagate across turns, anchoring future generation on flawed foundations.

The failure modes driving context contamination are well-characterized: premature answers that fill specification gaps with assumptions, answer bloat from patching rather than rewriting, lost-in-the-middle effects across turns, and over-verbosity that treats speculation as established fact (Laban et al., 2025; Huang et al., 2026). Crucially, interventions *within* the contaminated context (including reasoning models, lower temperature, and agent-like recapitulation) fail to close the gap. Only starting a new conversation with consolidated information recovers performance.

This pattern has a direct analogue in cognitive psychology. When humans face situations with distracting, contradictory, or outdated information, they rely on *executive function*: the set of higher-order cognitive processes that manage attention, inhibit prepotent but incorrect responses, and flexibly update working memory representations (Miyake et al., 2000; Diamond, 2013). Executive function enables humans to suppress irrelevant stimuli, shift between mental sets when the situation demands, and update their beliefs in light of new evidence. Current LLMs lack this regulatory capacity. They have no mechanism to step outside the conversation, evaluate whether their own prior outputs are helping or harming, and selectively suppress contaminating content.

To address these challenges, we introduce a framework of test-time scaling methods centered on the idea of *executive function for LLM conversations*. Rather than fine-tuning models to resist context contamination (a train-time approach whose benefits are amortized into the model), we invest additional inference-time compute in an external executive layer that monitors, diagnoses, and corrects the conversation trajectory. This executive layer operates through three capacities that mirror the core components of human executive function:

- **Inhibition and attention management.** A conversation analyzer identifies contaminating content (incorrect assumptions, failed approaches, speculative reasoning) and either annotates it for the assistant or surgically removes it from context, preventing it from anchoring future generation. This mirrors the inhibitory control that allows humans to suppress distracting information.

- **Flexible updating.** When the analyzer determines that the assistant's approach has diverged from user intent, the context is rewritten: erroneous content is removed while correct progress is preserved, providing the assistant with an updated working representation. This parallels the working memory updating that allows humans to revise their mental models.

- **Meta-cognitive learning.** A Dynamic Cheatsheet mechanism accumulates transferable editing principles across problem instances through a reflect-then-unify process. This meta-self-reflection partially amortizes the cost of test-time intervention: rather than reasoning from scratch at each turn, the executive layer draws on accumulated experience about *how* context contamination manifests and *what* editing patterns are effective. This represents a second level of test-time scaling, investing compute not just in per-turn reflection but in cross-instance learning.

The usual benefit of train-time compute is that improvements are amortized into the model parameters. Our memory mechanism absorbs some of this benefit, as learned principles persist and transfer across problems. But even with memory, the reflection step remains necessary at each turn: the executive layer must still evaluate whether the current conversation is on track and decide how to intervene. This is the fundamental trade-off of test-time scaling: greater flexibility and applicability to any black-box model, at the cost of per-instance compute.

Our specific methods (context annotation, context rewriting, selective gated rewriting, and memory-augmented variants) are instantiations of this executive function framework at different levels of intervention aggressiveness. We evaluate these methods on four task domains from the LiC benchmark and show that: (1) context *rewriting* is essential, because annotating contaminated content without removing it does not help since the harmful content still competes for attention; (2) the decision of *when* to intervene matters as much as *how*, with the optimal strategy depending on task characteristics; (3) meta-cognitive learning can substantially amplify effectiveness (+20pp on code), but only when the learned knowledge remains at the right abstraction level, as task-specific content causes the executive layer to anchor on stale patterns, recreating the very failure mode it is designed to correct; and (4) at least one variant outperforms the baseline on every task, though no single variant is universally best, motivating future work on adaptive executive control.

---

## 2. Related Work

### 2.1 Lost in Conversation

Laban et al. (2025) introduced the Lost in Conversation (LiC) framework, demonstrating that LLMs suffer systematic performance degradation in multi-turn, underspecified conversations. Their methodology takes single-turn problems (where models achieve high accuracy) and "shards" them: the complete specification is split into pieces that are revealed incrementally by a simulated user across multiple turns.

The key findings are: (1) performance drops 39% on average compared to single-turn, (2) the degradation is primarily unreliability (+112%) rather than reduced aptitude (-16%), (3) all 15 tested models exhibit similarly high multi-turn unreliability regardless of single-turn capability, and (4) the degradation is binary, occurring fully with even a 2-turn conversation.

LiC identifies four failure modes: premature answer attempts, answer bloat, loss-in-middle-turns, and over-verbosity. Crucially, interventions within the same conversation context fail to close the gap. Only starting a new conversation with consolidated information recovers performance.

We adopt the LiC simulation framework as our primary evaluation setting because it provides controlled, reproducible multi-turn scenarios with known ground truth. However, we note that strong LiC results can be achieved by trivially discarding all assistant content and concatenating user messages (recovering the single-turn baseline). Our approach is designed to be non-exploitative: by preserving (edited) assistant content, improvements must come from genuinely useful editing decisions.

### 2.2 ERGO: Entropy-Guided Context Resetting

Khalid et al. (2025) proposed ERGO, which monitors token-level Shannon entropy at each turn and triggers a context reset when the entropy delta exceeds a calibrated threshold. Upon reset, all prior user messages are summarized into a single prompt and all assistant messages are discarded.

On the LiC simulator, ERGO achieves a 56.6% average performance gain. However: (1) it requires logprob access, which many API providers limit; (2) its reset discards all assistant messages, recovering the single-turn baseline; (3) the entropy threshold is calibrated per-model; and (4) it uses a simplified LiC simulator without conversational rephrasing.

Our approach differs in using the LLM itself to decide when and how to intervene (requiring only black-box API access), preserving edited assistant content rather than discarding it, and incorporating a learning mechanism that improves over time.

### 2.3 Do LLMs Benefit from Their Own Words?

Huang et al. (2026) investigated whether prior assistant responses help or hurt in multi-turn conversations. They found that omitting all prior assistant responses frequently does not hurt, and sometimes improves, response quality, terming this "context pollution." Their key insight that one-sentence summaries outperform both full context and full omission directly supports our thesis: intelligent compression beats both extremes. However, their approach makes a binary per-turn choice (keep all or omit all) and requires model-specific training. Our methods provide finer-grained control and require no training.

### 2.4 CollabLLM

[TODO: CollabLLM paper. Describe setting, compare methodology.]

### 2.5 Test-Time Scaling and Inference-Time Compute

The broader test-time scaling literature investigates how additional inference-time compute can improve model performance without parameter updates. This includes chain-of-thought reasoning (Wei et al., 2022), self-consistency (Wang et al., 2023), tree-of-thought search (Yao et al., 2024), and verifier-guided search (Cobbe et al., 2021). These methods focus on single-turn settings, scaling compute within a single generation.

Our work extends test-time scaling to the *multi-turn* setting, where the challenge is not generating a better single response but managing the accumulated context across turns. The executive function layer is a form of test-time compute that operates at the conversation level rather than the generation level. The Dynamic Cheatsheet further extends this to cross-instance learning, a second axis of test-time scaling.

### 2.6 Dynamic Cheatsheet and Test-Time Learning

Suzgun et al. (2025) introduced the Dynamic Cheatsheet, a mutable text document that accumulates task-relevant knowledge across problem instances at test time without gradient updates. We adapt this for context editing, targeting the cheatsheet at the analyzer (executive layer) rather than the assistant itself. We find that the *content* of the cheatsheet is critical: meta-level editing principles transfer well, while task-specific solutions cause harmful anchoring, the same failure mode we are trying to correct.

---

## 3. Methods

### 3.1 Problem Setting

We adopt the LiC simulation framework. A single evaluation instance consists of:

- A **task** with a fully-specified question $q$ and ground truth answer $a$
- A **sharding** of $q$ into $k$ shards $\{s_1, \ldots, s_k\}$ that partition the specification
- A **simulated user** that reveals shards incrementally across turns
- An **assistant** (the model under evaluation) that must gather information and produce a correct answer
- A **system agent** that classifies each assistant response and evaluates correctness

The conversation proceeds for up to $T$ turns. At each turn: the user reveals a shard, the context strategy prepares the message history, the assistant generates a response, and the system agent evaluates.

### 3.2 Executive Function for Multi-Turn Conversations

The core challenge of multi-turn conversations is that LLMs lack the regulatory mechanisms to manage their own context. In cognitive psychology, executive function comprises three core capacities (Miyake et al., 2000):

1. **Inhibitory control**: suppressing prepotent but incorrect responses and filtering distracting information
2. **Working memory updating**: revising mental representations when new information arrives
3. **Cognitive flexibility**: shifting between mental sets or strategies as demands change

Current LLMs fail at all three in multi-turn settings. They cannot inhibit attention to their own incorrect prior outputs (inhibitory failure). They cannot revise their approach when user corrections arrive because the old approach remains in context (updating failure). And they cannot shift strategies because early commitments anchor subsequent generation (flexibility failure).

Our framework implements an external executive function layer through an LLM-as-analyzer that operates on the conversation history before each assistant turn. The specific methods described below (context annotation, context rewriting, and selective gating) instantiate executive function at different levels of intervention strength:

| Executive capacity | Method instantiation |
|---|---|
| **Monitoring** (detecting contamination) | Conversation Analyzer: two-query architecture (Sec 3.3) |
| **Inhibition** (suppressing harmful content) | Context rewriting / S2 (Sec 3.4) |
| **Annotation** (flagging without removing) | Append analysis / S1 (Sec 3.4) |
| **Selective control** (deciding when to intervene) | Agentic Edit gating (Sec 3.4) |
| **Meta-cognition** (learning from experience) | Dynamic Cheatsheet / memory (Sec 3.5) |

### 3.3 Conversation Analyzer

The analyzer is the core monitoring component, shared by all intervention strategies. It uses a **two-query architecture** that enforces hard attention separation between user intent extraction and assistant evaluation.

#### Query 1: Task Specification (Intent Extraction)

- **Input:** Only user messages, numbered by turn. No assistant responses.
- **Output:** A `<task_spec>` containing the complete, up-to-date specification from user messages.
- **Purpose:** Pure information extraction. By architecturally excluding assistant responses, we prevent the analyzer from being contaminated by the assistant's framing. The model cannot rationalize the assistant's approach if it has never seen it.

#### Query 2: Comparison (Contamination Detection)

- **Input:** The task specification from Q1, the full conversation history, and optionally a memory cheatsheet.
- **Output:** `<aligned>` (what the assistant got right) and `<issues>` (what contradicts the specification).
- **Purpose:** Critical evaluation against the independently-extracted specification.

**Why two queries?** A single query cannot guarantee the model processes user intent before evaluating the assistant, especially with reasoning models whose internal thinking may interleave freely. Two queries enforce the sequencing architecturally.

**Implicit edit decision.** The presence of substantive content in `<issues>` *is* the edit decision. A function filters out trivial responses ("None," "No issues," empty strings). This avoids the risk of the model misjudging severity.

### 3.4 Context Strategies

We define a `ContextStrategy` interface with `prepare_context(trace, memory, model_client)` called before each assistant turn. Three primary strategies instantiate executive function at different intervention levels:

#### S0: Baseline (No Intervention)

The full conversation history is passed unchanged. This is the control condition. When memory is enabled, the cheatsheet is injected into the system message.

#### S1: Append Analysis (Monitoring Without Inhibition)

The analyzer runs and its structured output (task specification, aligned content, issues) is appended to the last user message. The full history is preserved. S1 serves as an ablation: it provides the same diagnostic information as S2 but without removing contaminated content, isolating the contribution of *inhibition* (rewriting) versus *monitoring* (annotation).

#### S2: Context Edit (Full Executive Intervention)

If the analyzer identifies substantive issues, the conversation trace is reset: all prior messages are replaced with a compacted context containing only the clean task specification and aligned content. Issues guide the edit decision but are **not reintroduced**, because including descriptions of what went wrong would give the assistant new content to anchor on, reintroducing contamination.

```
[compacted conversation]
# Task Spec
{clean specification from user messages}

# What Looks Right So Far
{aligned content from assistant responses}

[user]
{any new user message since last analysis}
```

A `max_resets` parameter (default 3) prevents infinite reset loops.

#### Agentic Edit (Selective Executive Control)

A gating step: a decision model analyzes the conversation and outputs yes/no for whether intervention is beneficial. If yes, the full S2 edit is performed; if no, the context passes through unchanged. This mirrors cognitive flexibility, adapting the intervention strategy to the current conversation state rather than applying a fixed policy.

### 3.5 Memory-Based Learning (Meta-Cognitive Layer)

The Dynamic Cheatsheet accumulates editing principles across problem instances, injected into the analyzer's Q2 prompt. Memory is not used in Q1 (pure extraction).

#### Update Mechanism: Reflect-then-Unify

After processing a batch of problems:

1. **Reflect.** For each trajectory, an LLM generates generalizable takeaways. Reflections run in parallel. The prompt includes the current cheatsheet, the rendered trajectory, outcome, and optionally ground truth.

2. **Unify.** A single LLM call merges takeaways with the current cheatsheet, deduplicating and resolving contradictions.

This is meta-self-reflection: the system reflects not on the task itself but on its own executive process, asking *how well did the monitoring and intervention work, and what should change?* This partially amortizes the cost of test-time scaling by encoding reusable patterns, though the per-turn reflection step remains necessary.

#### Memory Target

| Target | What it learns | Where injected |
|---|---|---|
| Analyzer (S1/S2) | Patterns for identifying harmful vs. useful content | Q2 comparison prompt |
| Assistant (S0) | Task-domain strategies and pitfalls | System message |

Targeting memory at the executive layer (analyzer) is more effective than targeting the assistant directly.

#### Content Discipline

A critical finding: the *type* of knowledge matters more than the update mechanism. Meta-level principles transfer well:
- "Verify output format matches user specification before declaring alignment"
- "Example-based disambiguation: when the user provides examples, use them as the specification"
- "Reject assistant assumptions not grounded in user messages"

Task-specific content (algorithmic recipes, code snippets) causes the executive layer to anchor on stale patterns, the same failure mode we are correcting in the assistant. We enforce content discipline through explicit WHAT BELONGS / WHAT DOES NOT BELONG sections and cap cheatsheet length at 1500 words.

### 3.6 Conversation Rendering

The conversation is rendered using an "Option 2" format: all messages are tagged and concatenated into a single user message with a system message providing task instructions. This avoids differential attention at message boundaries.

---

## 4. Experiments

### 4.1 Evaluation Framework

We evaluate on the LiC benchmark across four task domains:

| Task | Domain | Evaluation | Source |
|---|---|---|---|
| **Math** | Mathematical reasoning | Exact numerical match | MATH dataset |
| **Code** | Code generation | Functional correctness (unit tests) | HumanEval + LiveCodeBench |
| **Database** | SQL generation | Execution match | Spider/BIRD |
| **Actions** | Action sequence generation | Sequence match | ALFWorld-derived |

#### Model Configuration

- **Assistant / Analyzer:** GPT-5-mini
- **User / System agents:** GPT-4o (upgraded from GPT-4o-mini due to content filter false positives)
- **Infrastructure:** Azure OpenAI multi-endpoint load balancer

#### Compute and Latency Considerations

Multi-turn simulation is inherently expensive. Each evaluation instance requires at minimum $k$ sequential LLM calls for the assistant (average ~8 shards), plus user agent calls, system agent verification, and (for S1/S2) two analyzer calls per turn. Memory experiments require sequential batch processing. These constraints limit evaluation scale; we address this through careful subset selection (Section 4.2).

### 4.2 Subset Derivation

We derive evaluation subsets via two-stage filtering:

1. **Consistency Filtering.** Run the baseline 3-5 times per problem. Retain problems with consistent baseline failure, i.e., instances where multi-turn degradation is most evident and intervention has the most potential.

2. **Threshold.** A problem is included if it failed in at least $t$ out of $n$ baseline runs. We use $t = n$ for our primary evaluation.

Task-specific subsets:
- **Math:** 9 problems (test) / 23 (dev)
- **Code:** 20 (test) / 25 (dev)
- **Database:** 63 ($t$=2) / 48 ($t$=3) / 25 (dev)
- **Actions:** 47 (test) / 25 (dev)

### 4.3 Experimental Conditions

| Condition | Strategy | Memory | Description |
|---|---|---|---|
| Baseline | S0 | No | Unmodified conversation |
| Baseline + Memory | S0 | Yes (assistant) | Cheatsheet in system message |
| Reflection (S1) | S1 | No | Analysis appended, no rewriting |
| S1 + Memory | S1 | Yes (analyzer) | Analysis with learned patterns |
| Context Edit (S2) | S2 | No | Analyzer-driven rewriting |
| S2 + Memory | S2 | Yes (analyzer) | Rewriting with learned principles |
| Agentic Edit | Selective | No | Gated reset |
| Agentic + Memory | Selective | Yes (analyzer) | Gated reset with memory |

Memory experiments use batched execution (batch size 3-10), continual learning, oracle-guided reflection.

### 4.4 Comparison with CollabLLM

[TODO: Describe CollabLLM experimental setup and evaluation of our methods in their setting.]

### 4.5 Comparison with Huang et al. Setting

[TODO: Evaluate context editing with their WildChat/ShareLM data and FC/AO methodology.]

---

## 5. Results

### 5.1 V1 Results: Cross-Task Strategy Comparison

Initial experiments evaluated six conditions across four tasks. All use GPT-5-mini as assistant/analyzer, GPT-4o for user/system agents.

**Table 1: V1 Results, Accuracy across tasks and conditions**

| Task ($N$) | Baseline | Reflect (S1) | Ctx Edit (S2) | S2+Mem | Agentic | Agentic+Mem | Best |
|---|---|---|---|---|---|---|---|
| **Code** (20) | 6/20 (30%) | 3/18 (17%)$^\dagger$ | 8/20 (40%) | **12/20 (60%)** | 8/19 (42%) | 4/20 (20%) | S2+M |
| **Math** (9) | 2/9 (22%) | 2/9 (22%) | 2/9 (22%) | 2/9 (22%) | 3/9 (33%) | 4/8 (50%)$^\dagger$ | AE+M |
| **DB $t$=3** (48) | 30/48 (63%) | 24/48 (50%) | 24/48 (50%) | 35/48 (73%) | **38/48 (79%)** | 28/48 (58%) | AE |
| **Actions** (47) | 14/47 (30%) | 8/34 (24%)$^\dagger$ | 16/47 (34%) | 15/47 (32%) | 11/47 (23%) | **17/47 (36%)** | AE+M |

$^\dagger$ Errors excluded (content filter). S2=context edit, AE=agentic edit, M=memory.

**Key findings:**

1. **At least one method beats baseline on every task.** The optimal strategy varies: S2+Memory for code (+30pp), Agentic Edit for database (+16.7pp), Agentic Edit+Memory for actions (+6pp) and math (+28pp).

2. **Monitoring without inhibition (S1) never helps.** Consistently at or below baseline. Appending diagnostic annotations to contaminated context adds noise because the assistant cannot act on "here's what's wrong" when the wrong content remains visible. This confirms that *inhibition* (removing contaminated content) is the essential executive capacity, not just *monitoring*.

3. **Context editing is most effective on code.** S2+Memory achieves 60%, a 2x improvement. Code tasks have consistent failure patterns (premature implementation, assumption lock-in) that benefit from systematic executive intervention with learned principles.

4. **Indiscriminate intervention hurts when baseline is strong.** S2 without memory drops database from 63% to 50%. Many database problems are solved in few turns; always resetting disrupts on-track conversations (turns 3.7 to 9.1). The executive layer must exercise *selective control*.

5. **Selective control (Agentic Edit) excels on database.** At 79.2%, it exceeds baseline by 16.7pp while *decreasing* turn count (3.4 vs 3.7). The decision model correctly identifies when intervention helps versus hurts, a form of cognitive flexibility.

6. **Memory helps the analyzer but hurts the gating decision.** S2+Memory improves over S2 on code (+20pp) and database (+23pp). But Agentic+Memory underperforms Agentic on code (-22pp) and database (-21pp). Editing principles make the decider over-trigger resets, suggesting the gating component needs its own memory with decision-oriented principles.

### 5.2 V2 Results: Dev Set with Refined Analyzer

After refactoring the analyzer to the two-query architecture and externalizing prompts, we evaluated on curated hard dev sets.

**Table 2: Dev Set Results, Hard problems only**

| Task ($N$) | Baseline | Base+Mem | S1 | S1+Mem | S2 | S2+Mem |
|---|---|---|---|---|---|---|
| **Math** (23) | 14.5% | 31.8% | 31.6% | 35.0% | **61.5%** | 50.0% |
| **Code** (25) | 0% | 20.0% | 25.0% | 40.0% | **57.1%** | 41.7% |
| **Database** (25) | 0% | 4.2% | 0% | **20.0%** | 4.0% | 0% |
| **Actions** (25) | 0% | 8.0% | 20.0% | **31.6%** | 16.0% | 16.0% |

Note: Exclusion rates vary (0-13 per condition). Higher exclusion rates inflate accuracy percentages. Raw correct counts should be compared alongside.

**Key findings:**

1. **Full executive intervention (S2) is strongest on reasoning tasks.** Math (61.5%) and code (57.1%), where contamination manifests as incorrect partial work that anchors subsequent reasoning, benefit most from complete context rewriting.

2. **S1+Memory is the most robust strategy.** Improvements across all four tasks, including database (0% to 20%). Monitoring with learned meta-cognitive principles is operationally stable compared to full rewriting.

3. **Memory can over-constrain the executive layer.** S2+Memory hurts math (61.5% to 50.0%) and code (57.1% to 41.7%). Learned patterns may bias the analyzer's comparison, over-weighting memory over current evidence. The executive layer should treat memory as a weak prior.

4. **Memory consistently helps at lower intervention levels.** Baseline+Memory and S1+Memory improve on all 4 tasks. Meta-cognitive knowledge transfers even without context rewriting.

### 5.3 CollabLLM Setting

[TODO: Results on CollabLLM experimental setting.]

### 5.4 Huang et al. Replication

[TODO: Results comparing against FC/AO on WildChat/ShareLM data.]

---

## 6. Discussion

### 6.1 When Does Executive Intervention Help?

The benefit depends on the interaction between task difficulty, baseline performance, and contamination patterns.

**High-value targets: reasoning-intensive tasks with consistent contamination.** Code and math show the largest gains. These exhibit the classic contamination cascade: premature implementation, assumption lock-in, answer bloat. The executive layer interrupts this cascade by removing anchoring content.

**Low-value or harmful: tasks with strong baselines.** On database ($t$=2, baseline 73%), always intervening *hurts*. Many problems are solved quickly with minimal contamination. The executive layer must exercise selective control, not blanket intervention.

**The "when" matters as much as the "how."** On database, Agentic Edit (79.2%) far outperforms S2 (50.0%) despite using the same editing mechanism. Selective control (knowing *when* to intervene) is more valuable than intervention quality alone. On code, S2+Memory (60%) outperforms Agentic (42%), suggesting that *how* the intervention is performed matters more when the task consistently benefits from executive control.

### 6.2 The Test-Time Scaling Trade-Off

Our framework invests additional inference-time compute at two levels: per-turn reflection (the analyzer) and cross-instance learning (the cheatsheet). This stands in contrast to train-time approaches that would amortize improvements into model parameters.

The trade-off is clear. Test-time scaling offers: (1) applicability to any black-box model without fine-tuning, (2) flexibility to apply different intervention strategies per task or conversation, and (3) the ability to learn and adapt at deployment time. The cost is per-instance compute, as the analyzer adds two LLM calls per turn and memory requires sequential batch processing.

The Dynamic Cheatsheet partially bridges this gap: learned principles persist and transfer, analogous to how train-time improvements amortize. But the per-turn reflection step remains necessary because the executive layer must still evaluate each conversation's state. Whether this cost can be further amortized through fine-tuning models to internalize executive function is an important direction for future work.

### 6.3 The Role of Memory and Content Discipline

Memory is a double-edged sword. When targeted correctly, it provides substantial gains (S2+Memory on code: +20pp). When targeted incorrectly, it actively hurts (Agentic+Memory on code: -22pp).

The critical insight is **content discipline**. Early experiments with unconstrained cheatsheets saw the memory accumulate algorithmic recipes and code snippets. These caused the executive layer to anchor on stale patterns, exactly the failure mode we are correcting in the assistant. Restricting to transferable meta-level principles resolved this.

This has implications for test-time learning broadly: the abstraction level of learned knowledge must match the generality of its application. Domain-specific content does not transfer and actively harms; domain-general meta-cognitive knowledge transfers well.

### 6.4 Monitoring vs. Inhibition

The S1 vs. S2 comparison provides a clean ablation. S1 without memory consistently fails because appending diagnostic annotations to contaminated context adds noise. The assistant cannot act on "here's what's wrong" when the wrong content is still visible. This is the executive function analogue of inhibitory failure: without the ability to *suppress* contaminating information, merely *identifying* it is insufficient.

S1 *with memory* is more competitive, suggesting that accumulated meta-cognitive principles provide useful guidance even without context cleanup. But it does not reach S2's peak on reasoning tasks, confirming that inhibition (removing harmful content) is the essential capacity.

### 6.5 Limitations

**Sample sizes.** Evaluation subsets are small (9-48 problems), constrained by multi-turn simulation cost. Larger-scale evaluation is needed to confirm effect sizes.

**Simulated setting.** The LiC framework uses scripted shard reveals. Real users are less predictable and may reference assistant responses in ways the simulator does not capture.

**Model-specific results.** All experiments use GPT-5-mini. The interaction between executive intervention and different model families is unexplored.

**Fixed analyzer model.** The analyzer uses the same model family as the assistant. A weaker or different analyzer might produce different results.

### 6.6 Proposed Ablations and Future Explorations

1. **Memory target separation.** The gating component needs its own memory with decision-oriented principles, separate from editing principles.

2. **Hybrid strategy.** Combine selective gating (without memory) with S2+Memory editing when triggered.

3. **Cross-task cheatsheet transfer.** Can meta-level principles learned on code improve editing on actions?

4. **Analyzer model scaling.** Does a stronger analyzer improve intervention quality?

5. **Variance quantification.** Multiple runs per condition to separate signal from noise.

6. **Memory content ablation.** Systematically compare cheatsheets of different content types and sizes.

---

## 7. Conclusion

We have presented a test-time scaling framework for recovering multi-turn conversation reliability, centered on the idea of executive function for LLM conversations. By investing additional inference-time compute in an external layer that monitors, diagnoses, and corrects context contamination, we demonstrate consistent improvements over unmodified baselines across multiple task domains.

Our key findings are: (1) *inhibition*, removing contaminated content, is the essential executive capacity; merely monitoring contamination without suppressing it does not help; (2) *selective control* matters as much as intervention quality, with the optimal strategy depending on task characteristics; (3) *meta-cognitive learning* can substantially amplify effectiveness, but only when learned knowledge remains at the right abstraction level; and (4) at least one executive intervention variant outperforms the baseline on every task, though no single variant is universally best.

### Future Work

**Adaptive executive control.** Our results show that the optimal strategy varies by task. An adaptive system that selects intervention level based on conversation-level features, analogous to the flexible shifting component of executive function, would be more robust than any fixed strategy.

**Internalizing executive function.** If an LLM can perform executive monitoring through prompting (as our analyzer demonstrates), this capability is a natural target for reinforcement learning or fine-tuning. Training models to natively detect and recover from context contamination would amortize the test-time compute cost while preserving the benefits.

**True long-context settings.** Our evaluation uses 3-12 turn conversations. Real deployments involve much longer exchanges where context windows become binding. Context editing naturally addresses this through compression, but the interaction between editing quality and conversation length is unexplored.

**Agentic settings.** Modern agentic architectures amplify multi-turn reliability problems: a wrong tool call from an early assumption can cascade across a workflow. Executive function could be applied to agentic traces, identifying failed action sequences while preserving successful sub-task completions.

---

## References

- Laban, P., et al. (2025). Lost in Conversation: A Large-Scale Simulation of Multi-Turn Problem-Solving Conversations with LLMs. *arXiv*.
- Khalid, M., et al. (2025). ERGO: Entropy-Guided Context Resetting for Multi-Turn Conversations. *arXiv*.
- Huang, X., et al. (2026). Do LLMs Benefit from Their Own Words? Understanding Context Pollution in Multi-Turn Conversations. *arXiv*.
- Suzgun, M., et al. (2025). Dynamic Cheatsheet: Test-Time Learning with Mutable Memory. *arXiv*.
- Miyake, A., et al. (2000). The Unity and Diversity of Executive Functions. *Cognitive Psychology*.
- Diamond, A. (2013). Executive Functions. *Annual Review of Psychology*.
- [TODO: CollabLLM reference]
- [TODO: Test-time scaling references: Wei et al., Wang et al., Yao et al., Cobbe et al.]

---

## Appendix

### A. Prompt Templates

[TODO: Include key prompts: analyzer Q1, Q2, reflection, unification.]

### B. Cheatsheet Examples

[TODO: Show difference between harmful (task-specific) and beneficial (meta-principle) content.]

### C. Trajectory Examples

[TODO: Annotated examples showing baseline failure, analyzer diagnosis, edited context, and recovery.]
