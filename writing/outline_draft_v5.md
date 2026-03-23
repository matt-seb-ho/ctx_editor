# Self-Aware Reasoning: Teaching LLMs to Monitor and Correct Their Own Context

---

## Abstract

Large language models suffer systematic performance degradation in multi-turn conversations: when task specifications are revealed incrementally, models overcommit to early incorrect assumptions and cannot self-correct because flawed reasoning persists in context. We term this *context contamination* and show it operates through two mechanisms: (1) user intent becomes fragmented across turns, and (2) the assistant's prior incorrect reasoning anchors future generation. We introduce a *self-aware reasoning* framework — an external executive layer that reasons about the model's own reasoning process, diagnosing where prior outputs help or harm and surgically intervening in the conversation context. A key finding is that this meta-reasoning capacity does not emerge from prompting alone: even an external analyzer model anchors on the assistant's errors when exposed to them, so the system must be architecturally designed to separate intent extraction from contaminated context. On the Lost in Conversation benchmark, our methods improve accuracy from 60% to 90% on math, 16% to 72% on code, 4% to 44% on database, and 9% to 30% on actions. We further show that memory-based learning can partially recover self-aware reasoning quality even when the analyzer must process the full conversation (closing up to 65% of the gap on structured tasks), and demonstrate initial positive results in the CollabLLM collaborative setting (+5pp math, +20pp code). As a secondary contribution, we introduce methodological improvements to the LiC evaluation framework — including user simulator quality control and replay-based isolation — that yield more reliable estimates of assistant performance.

---

## 1. Introduction

The deployment of large language models increasingly involves multi-turn conversations. Users rarely specify complete requirements upfront; instead, they iteratively clarify, correct, and extend their requests across multiple exchanges. This conversational pattern is natural for humans but creates a fundamental problem for LLMs: once the model commits to an interpretation in an early turn, the resulting reasoning persists in context and anchors all subsequent generation, even when later user messages contradict the initial assumptions.

Laban et al. (2025) quantified this through the "Lost in Conversation" (LiC) framework, a large-scale simulation across 15 LLMs and 6 task domains. Their core finding is striking: the performance gap between single-turn and multi-turn settings is driven primarily by *unreliability* (112% increase), not reduced *aptitude* (only 16% decrease). The capability is preserved, but the model fails to access it reliably. We call this degradation mechanism *context contamination*: earlier assistant outputs introduce errors, incorrect assumptions, and speculative content that propagate across turns, anchoring future generation on flawed foundations.

We identify two distinct mechanisms driving context contamination:

1. **User intent fragmentation.** In multi-turn conversations, the user's actual request is scattered across turns — paraphrased, revised, and buried in conversational noise. The model must reconstruct what the user wants from incomplete, non-linear input, and frequently fails.

2. **Reasoning contamination.** The assistant's prior (often incorrect) reasoning remains in context and anchors future responses. Even when later user messages contradict earlier assumptions, the model cannot un-see its own mistakes.

These two problems require different solutions. Intent fragmentation is addressed by *task specification reconstruction*: an independent extraction of what the user wants from their messages alone, free from the assistant's interpretive lens. Reasoning contamination is addressed by *context editing*: surgically removing harmful content while preserving correct progress.

Both solutions require what we term *self-aware reasoning*: the capacity to step outside the conversational flow, evaluate the model's own prior outputs as objects of analysis rather than authoritative context, and selectively intervene. Current LLMs lack this regulatory capacity intrinsically — they have no mechanism to distinguish between their own helpful prior reasoning and their own harmful prior reasoning within the same context window.

This pattern has a direct analogue in cognitive psychology. When humans face situations with distracting, contradictory, or outdated information, they rely on *executive function*: the set of higher-order cognitive processes that manage attention, inhibit prepotent but incorrect responses, and flexibly update working memory representations (Miyake et al., 2000; Diamond, 2013). Self-aware reasoning is the computational instantiation of this capacity: reasoning about one's own reasoning process to identify and correct failures.

We introduce a framework of test-time methods centered on this idea. Rather than fine-tuning models to resist context contamination, we invest additional inference-time compute in an external executive layer that monitors, diagnoses, and corrects the conversation trajectory. This executive layer operates through three capacities:

- **Self-monitoring and intent extraction.** A conversation analyzer extracts a clean task specification from user messages alone, reconstructing fragmented user intent without contamination from the assistant's prior reasoning.

- **Self-correction via context editing.** When the analyzer identifies harmful content in the assistant's responses, the context is surgically rewritten: erroneous content is removed while correct progress is preserved. This prevents contaminating content from anchoring future generation.

- **Meta-cognitive learning.** A Dynamic Cheatsheet mechanism accumulates transferable self-correction principles across problem instances, partially amortizing the cost of test-time intervention through cross-instance learning.

A critical finding is that self-aware reasoning is architecturally demanding: even an external analyzer model is susceptible to the same anchoring when exposed to assistant messages, so the data flow must be designed to physically exclude them during intent extraction. However, this exclusion exploits a property specific to LiC — that user messages alone fully specify the task. In realistic multi-turn settings, the task specification may depend on prior assistant work. We investigate two paths toward more realistic applicability: (1) memory-based learning that teaches a full-conversation analyzer to resist contamination, closing up to 65% of the gap on structured tasks; and (2) evaluation on the CollabLLM benchmark, which features genuinely collaborative conversations with iterative requirement refinement, where our context compaction strategy shows positive initial results.

---

## 2. Related Work

### 2.1 Lost in Conversation

Laban et al. (2025) introduced the Lost in Conversation (LiC) framework, demonstrating that LLMs suffer systematic performance degradation in multi-turn, underspecified conversations. Their methodology takes single-turn problems (where models achieve high accuracy) and "shards" them: the complete specification is split into pieces that are revealed incrementally by a simulated user across multiple turns. The key findings are: (1) performance drops 39% on average compared to single-turn, (2) the degradation is primarily unreliability (+112%) rather than reduced aptitude (-16%), (3) all 15 tested models exhibit similarly high multi-turn unreliability, and (4) interventions within the same conversation context fail to close the gap — only starting a new conversation with consolidated information recovers performance.

We adopt the LiC simulation framework as our primary evaluation setting because it provides controlled, reproducible multi-turn scenarios with known ground truth. We also introduce methodological improvements to the evaluation pipeline (Section 4.3) that yield more reliable performance estimates.

### 2.2 ERGO: Entropy-Guided Context Resetting

Khalid et al. (2025) proposed ERGO, which monitors token-level Shannon entropy at each turn and triggers a context reset when the entropy delta exceeds a calibrated threshold. Upon reset, all prior user messages are summarized into a single prompt and all assistant messages are discarded. ERGO achieves a 56.6% average performance gain on LiC. However, it requires logprob access (which many API providers limit), its reset discards all assistant messages entirely (recovering the single-turn baseline), and the entropy threshold is calibrated per-model. Our approach differs in using the LLM itself to decide when and how to intervene (requiring only black-box API access) and preserving edited assistant content rather than discarding it.

### 2.3 Do LLMs Benefit from Their Own Words?

Huang et al. (2026) investigated whether prior assistant responses help or hurt in multi-turn conversations. They found that omitting all prior assistant responses frequently does not hurt, and sometimes improves, response quality — terming this "context pollution." Their key insight that one-sentence summaries outperform both full context and full omission directly supports our thesis: intelligent compression beats both extremes. However, their approach makes a binary per-turn choice (keep all or omit all) and requires model-specific training.

### 2.4 CollabLLM

CollabLLM (citation TBD) proposes a framework for training LLMs to be more effective collaborators in multi-turn conversations, where the user iteratively refines requirements through natural dialogue. Unlike LiC's scripted shard reveals, CollabLLM uses an LLM-based user simulator that is instructed to be initially vague and gradually reveal intent — creating more naturalistic collaborative dynamics. CollabLLM evaluates on MATH-Hard and BigCodeBench, measuring both task accuracy and interactivity (how well the assistant engages collaboratively). We use CollabLLM as a second evaluation setting to test whether our methods transfer to more realistic, explicitly collaborative interactions.

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

### 3.4 Soft-Attention Analysis: Toward Realistic Settings

The hard-attention design (excluding assistant messages from Query 1) exploits a property of LiC: user messages alone fully specify the task. In realistic multi-turn settings — iterative design, collaborative coding, tool-use agents — the task specification may depend on prior assistant work. We investigate whether the analyzer can learn to resist contamination even when it sees the full conversation.

**Chain-of-thought decontamination.** We introduce a soft-attention variant (v8_soft_cot) that explicitly reasons through decontamination: (1) list every concrete requirement stated by the user with source attribution, (2) identify assistant-originated interpretations and flag them, (3) note user overrides, (4) write the spec using only user-grounded requirements. This makes the separation between user intent and assistant interpretation an explicit reasoning step rather than an architectural guarantee.

**Memory-based decontamination learning.** We use hard-attention task specs as oracle training targets: the reflector compares soft-attention specs against hard-attention oracles to learn generalizable decontamination principles. These principles are injected into the soft-attention spec query via the Dynamic Cheatsheet mechanism (Section 3.5).

**S1.5: Context reset with soft-attention analysis.** A hybrid strategy that uses soft-attention analysis (the analyzer sees the full conversation) but resets the conversation context, removing polluted history before the assistant's next turn. This separates two effects: spec quality (soft vs. hard attention) and context pollution (full history vs. reset).

### 3.5 Memory-Based Learning (Meta-Cognitive Layer)

The Dynamic Cheatsheet accumulates editing principles across problem instances, injected into the analyzer's prompt. For the primary hard-attention system, memory targets Query 2 (comparison). For the soft-attention decontamination experiments, memory targets Query 1 (task specification), where it can directly improve spec quality.

**Update Mechanism: Reflect-then-Unify.** After processing a batch of problems: (1) *Reflect* — for each trajectory, an LLM generates generalizable takeaways from the outcome, with access to the current cheatsheet, the rendered trajectory, and optionally ground truth; (2) *Unify* — a single LLM call merges new takeaways with the current cheatsheet, deduplicating and resolving contradictions.

**Memory Target.** For strategies with an analyzer (Append Analysis, Context Edit), memory is targeted at the analyzer's comparison query. For the baseline, memory is injected into the assistant's system message. Targeting the executive layer is more effective than targeting the assistant directly.

**Content Discipline.** The *type* of knowledge matters more than the update mechanism. Meta-level principles transfer well ("verify output format matches user specification," "reject assistant assumptions not grounded in user messages"). Task-specific content (algorithmic recipes, code snippets) causes the executive layer to anchor on stale patterns — recreating the failure mode we are correcting. We cap cheatsheet length at 1500 words.

### 3.6 CollabLLM Adaptation: Context Compaction

To test our methods in a more naturalistic collaborative setting, we adapt the framework for the CollabLLM evaluation pipeline. The key adaptation is a **Context Compaction Strategy (S3)** that activates after user turn 4 and runs unconditionally every turn:

1. **Single-query analysis**: An "independent reviewer" prompt reads the full conversation and produces a task specification, what is good about the assistant's approach, and what should be changed.

2. **Context compaction**: The analysis plus full conversation are fed into a compaction prompt that generates a clean summary (task spec + work completed so far).

3. **Trace reset**: The conversation is replaced with the compacted context, removing all previous messages from the assistant's view.

S3 differs from the LiC strategies in two ways: it always compacts (not conditional on issues found) and uses a single-query analysis (not the two-query hard-attention separation), since CollabLLM conversations are genuinely collaborative and the task specification may depend on assistant contributions.

---

## 4. Experiments

### 4.1 Evaluation Frameworks

**Lost in Conversation.** We evaluate on four task domains:

| Task | Domain | Evaluation | Samples |
|------|--------|------------|:-------:|
| **Math** | Word problems | Exact numerical match | 20 |
| **Code** | Function implementation | Functional correctness | 19 |
| **Database** | SQL generation | Execution match | 25 |
| **Actions** | Parallel function calls | AST match | 23 |

Sample counts reflect filtering of user-simulator-induced errors (see Section 4.3).

**CollabLLM.** We evaluate on two tasks from the CollabLLM benchmark:

| Task | Domain | Evaluation | Samples |
|------|--------|------------|:-------:|
| **MATH-Hard** | Competition math | LLM-as-judge | 20 |
| **BigCodeBench** | Code generation | Conversation-aware LLM judge | 20 |

CollabLLM samples are randomly subsampled (seed=42) from the full benchmark splits (1,324 math, 1,140 code).

**Models.** LiC: GPT-5-mini for assistant and analyzer; GPT-4o-mini for simulated user and system agents. CollabLLM: GPT-5-mini (reasoning_effort: low) for assistant and context editor; GPT-4o for user simulator; GPT-5 for conversation-aware judge.

**Replay mode (LiC).** To isolate the effect of our interventions from conversational variance, we use a replay methodology: all strategies share the same baseline conversation prefix (from an unmodified S0 run) and only the final assistant turn is regenerated with the intervention applied. This ensures identical conversational context across conditions.

### 4.2 Experimental Conditions

**LiC — Primary conditions:**

| Condition | Analysis | Context | Memory |
|-----------|:--------:|:-------:|:------:|
| Baseline | — | Full | — |
| Baseline + Memory | — | Full | Assistant |
| Append Analysis | Two-query | Full + appended | — |
| Append Analysis + Memory | Two-query | Full + appended | Analyzer |
| Always-Reset | Two-query | Replaced | — |
| Always-Reset + Memory | Two-query | Replaced | Analyzer |
| Gated Reset | Two-query | Conditional | — |

**LiC — Soft-attention conditions (dev test splits):**

| Condition | Spec source | Context | Memory |
|-----------|:--------:|:-------:|:------:|
| S1-soft-cot | v8_soft_cot (full conv.) | Full + appended | — |
| S1-soft-cot + Memory | v8_soft_cot (full conv.) | Full + appended | Spec query |
| S1.5-soft-cot | v8_soft_cot (full conv.) | Reset | — |
| S1.5-soft-cot + Memory | v8_soft_cot (full conv.) | Reset | Spec query |
| S1-speconly (hard attention) | v8 (user msgs only) | Full + appended | — |

**CollabLLM conditions:**

| Condition | Analysis | Context |
|-----------|:--------:|:-------:|
| Baseline | — | Full |
| Context Compaction | Single-query | Reset (after turn 4) |

Memory experiments use batched execution (batch size 5) with continual learning and oracle-guided reflection (ground truth available during cheatsheet updates).

### 4.3 User Simulator Quality Control (LiC)

The sharded disclosure format occasionally produces user messages that distort the original problem, making the task unsolvable regardless of the assistant's capability. We pre-screen baseline traces using an LLM judge that compares the union of user simulator messages against the original single-turn question and flags cases where critical details are absent or materially changed. Flagged samples are excluded from all conditions (3 math, 6 code, 0 database, 2 actions). This ensures accuracy denominators reflect problems the assistant could reasonably solve.

This quality control step is itself a contribution: without it, evaluation conflates assistant failure with user simulator failure, inflating variance and understating intervention effects. We recommend this screening as standard practice for simulation-based multi-turn evaluation.

### 4.4 CollabLLM Evaluation Methodology

CollabLLM's standard BigCodeBench evaluation uses test-case execution (pass_rate), which requires exact function signatures. In the multi-turn setting, the user simulator never conveys exact function specs (it is instructed to be vague), making pass_rate systematically zero for all conditions — a ceiling imposed by the evaluation harness, not by code quality. We develop a **conversation-aware LLM judge** that evaluates the assistant's code against what the user actually asked for, rather than against a hidden test harness the assistant never saw. Using GPT-5 as judge (which is stricter and more discriminating than GPT-4o), this provides a fairer metric for the collaborative setting.

---

## 5. Results

### 5.1 Main Results (LiC)

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

### 5.4 Soft-Attention Decontamination: Toward Realistic Settings

The hard-attention design exploits a LiC-specific property. Can the analyzer learn to produce clean specs even when it sees the full conversation? We evaluate on held-out test splits (Math n=12, Code n=13, Database n=13) using the chain-of-thought soft-attention variant with and without memory-trained decontamination.

**Table 5: Soft-attention spec quality — S1 (full conversation visible to assistant)**

| Condition | Math | Code | Database |
|-----------|:----:|:----:|:--------:|
| S1-soft-cot (no memory) | 40% | 13% | 31% |
| S1-soft-cot + memory | 56% | 14% | **46%** |
| S1-speconly (hard attention) | **80%** | **40%** | 54% |

**Table 6: Soft-attention spec quality — S1.5 (conversation reset, spec only)**

| Condition | Math | Code | Database |
|-----------|:----:|:----:|:--------:|
| S1.5-soft-cot (no memory) | 42% | 23% | 31% |
| S1.5-soft-cot + memory | 42% | 25% | **46%** |
| S1.5-speconly (hard attention) | **67%** | **46%** | 54% |

#### Context reset consistently helps soft-attention analysis

S1.5 (reset) outperforms S1 (full conversation) across tasks when using soft-attention analysis: code improves from 13% to 23% (no memory) and 14% to 25% (with memory). Even when the *spec itself* is contaminated, removing the polluted conversation history from the assistant's view reduces anchoring on prior incorrect reasoning. This confirms that context pollution and spec contamination are separable problems.

#### Memory closes the gap on structured tasks

Memory-based decontamination shows its strongest effect on database: +15pp in both S1 and S1.5, closing 65% of the gap to hard attention. The learned cheatsheet converged on structured decontamination principles — "build a user-only spec first, then overlay assistant suggestions as hypotheses" and "anchor to schema for column/table names rather than accepting the assistant's SQL choices." These principles transfer to held-out test samples.

Math shows +16pp in S1 (where the contaminated context benefits from better analysis to override prior reasoning) but 0pp in S1.5 (where the context is already reset, removing the marginal value of improved analysis). Code remains resistant to memory improvement (+1-2pp), suggesting that code spec contamination is more structurally complex and resists generic decontamination principles.

#### Hard attention remains dominant but the gap narrows

The soft-to-hard gap is 20-25pp across tasks even in the best memory condition. Memory-based decontamination is a partial solution: it works best when contamination patterns are predictable and domain-specific (database), and least when they are structurally diverse (code). The structural guarantee of never seeing assistant messages provides something that learned heuristics cannot fully replicate — but in settings where that guarantee is unavailable, memory-trained soft attention with context reset (S1.5 + memory) offers a meaningful improvement over naive full-conversation analysis.

### 5.5 CollabLLM Setting

We evaluate context compaction in the CollabLLM collaborative setting, where the user simulator is instructed to be initially vague and gradually reveal intent through natural dialogue — a more realistic interaction pattern than LiC's scripted shard reveals.

**Table 7: CollabLLM results**

| Task | Baseline | Compaction | Delta |
|------|:--------:|:----------:|:-----:|
| MATH-Hard (LLM judge) | 40.0% (8/20) | **45.0% (9/20)** | +5.0pp |
| BigCodeBench (GPT-5 conv. judge) | 62.5% | **82.5%** | **+20.0pp** |
| BigCodeBench (matched subset, n=12) | 58.3% | **75.0%** | +16.7pp |

Note: 8/20 BigCodeBench compaction samples had zero resets (conversation ended before the turn-4 activation threshold), making them effectively baseline. The matched subset restricts to the 12 samples where compaction actually triggered.

#### Context compaction transfers to collaborative settings

Despite using a simpler single-query analysis (no hard-attention separation), context compaction improves accuracy on both tasks. The BigCodeBench improvement is particularly notable: +20pp overall, +16.7pp on the matched subset where compaction actually activated. Compaction helps by removing accumulated confusion from vague early exchanges, distilling the user's requirements into a clean task spec, and preserving correct work while discarding dead ends.

#### Efficiency gains are a side benefit

Context compaction reduces average assistant tokens by 74% on math (2,796 → 725) with no increase in cost ($0.43 vs $0.44). The compaction and analysis LLM calls are offset by shorter downstream contexts.

#### Evaluation methodology matters

BigCodeBench's standard pass_rate metric (test-case execution) scored 0% for all conditions — both baseline and compaction — because the user simulator never conveys exact function signatures required by the test harness. This is a limitation of the evaluation, not the assistant: the conversation-aware judge confirms that the assistant produces correct code for what the user actually requested. This highlights the importance of evaluation metrics that match the interaction setting.

---

## 6. Discussion

### 6.1 Two Problems, Two Solutions

Our results reveal that multi-turn performance degradation operates through two distinct mechanisms that are separable in our framework.

**User intent fragmentation** is the dominant factor on the LiC benchmark. The task specification alone — a clean extraction of user intent from user messages — recovers most of the single-turn performance. This is because LiC tasks are single-answer problems where rederivation is trivial: once the model knows what to compute, it can produce the answer without reference to its prior attempts.

**Reasoning contamination** is secondary but present. Always-Reset consistently outperforms Append Analysis on database (+8pp) and actions (+8pp), demonstrating that the assistant's prior incorrect reasoning does anchor its final response even when corrective analysis is available. The gap is largest on actions, the most complex task requiring coordination of multiple outputs — the closest LiC comes to stateful, multi-artifact work.

This decomposition has implications for benchmark design. LiC was constructed around simple, single-answer tasks to isolate the anchoring phenomenon. Our results suggest that more complex benchmarks — requiring multi-step reasoning, iterative artifact construction, or coordination across outputs — would show a larger role for context editing relative to task specification, because rederivation becomes expensive or impossible.

### 6.2 Self-Aware Reasoning Is Architecturally Demanding

The assistant-omission finding has implications beyond our specific setting. LiC demonstrated that the conversational assistant cannot un-anchor from its own prior reasoning. We show that this executive dysfunction is not specific to the assistant role — it is a general property of how LLMs process multi-party conversation context. An external model tasked with *analyzing* the conversation exhibits the same anchoring when exposed to the assistant's responses, even when explicitly instructed to focus on user messages.

This means that multi-stage LLM pipelines cannot rely on prompting to achieve selective attention. Designing the data flow to exclude contaminating content — rather than instructing the model to ignore it — is the reliable approach. Any system that uses an LLM to evaluate, critique, or improve another LLM's output faces this risk.

The soft-attention decontamination experiments (Section 5.4) offer a partial path forward: explicit chain-of-thought reasoning about provenance, combined with memory-trained decontamination principles, can recover some of the hard-attention advantage. But the gap remains substantial (20-25pp), and the benefit is task-dependent — working best on structured domains (database) where contamination patterns are predictable. True self-aware reasoning — the ability to reliably distinguish between one's own helpful and harmful prior outputs — remains an open challenge for current LLMs.

### 6.3 Toward Realistic Multi-Turn Intervention

A core limitation of the hard-attention approach is that it exploits a LiC-specific property: user messages alone fully specify the task. Real multi-turn interactions involve genuinely collaborative dynamics where the task specification depends on assistant contributions. Our two extensions address this:

**Soft-attention decontamination** (Section 5.4) shows that when the analyzer must see the full conversation, memory-based learning can teach it to partially resist contamination. The S1.5 strategy (soft-attention analysis + context reset) combined with memory represents the best available approach when hard attention is impossible: it closes 65% of the gap on database and provides consistent improvement via context reset across all tasks.

**CollabLLM evaluation** (Section 5.5) demonstrates that context compaction — using a simpler, single-query analysis without hard-attention separation — produces meaningful improvements in a genuinely collaborative setting. The +20pp on BigCodeBench suggests that even imperfect analysis provides value when it replaces an accumulated, confused conversation history. In collaborative settings where the user is gradually clarifying rather than revealing shards of a fixed spec, the distinction between user intent and assistant interpretation is less sharp, and the simpler approach may suffice.

Together, these results suggest a practical progression: hard-attention analysis when the setting allows it (scripted evaluations, structured tasks), soft-attention with memory-trained decontamination for semi-structured settings, and unconditional context compaction as a lightweight intervention for fully collaborative interactions.

### 6.4 The Role of Memory

Memory provides consistent benefit when applied to Append Analysis (+10pp math, +12pp code, +12pp database) but is inconsistent with context editing strategies. The cheatsheet helps the analyzer produce better analysis, but its ~1000 words of procedural guidance can dilute the analyzer's natural reasoning when the analysis drives a binary decision (edit or not).

For Append Analysis, analysis quality matters but imperfect analysis is still useful — the assistant sees both the analysis and the original conversation and can integrate them. For context editing, the analysis *is* the sole context — errors in analysis become errors in the assistant's input with no fallback.

In the soft-attention decontamination setting, memory shows a different pattern: it targets the spec query directly and teaches the analyzer to resist contamination rather than improving downstream comparison. Here, memory's benefit is concentrated on structured tasks (database +15pp) where contamination patterns are regular and learnable. This task-dependence suggests that memory-based decontamination is a complement to, not a replacement for, architectural solutions.

### 6.5 Evaluation Methodology as Contribution

Our experience with both LiC and CollabLLM highlights the importance of evaluation methodology in multi-turn settings:

**User simulator quality control.** Without screening for user simulator failures, evaluation conflates assistant capability with simulator quality. Our LLM-based screening identifies cases where the simulated user distorts the original problem, enabling cleaner measurement of intervention effects.

**Replay-based isolation.** By sharing baseline conversation prefixes across conditions and only regenerating the final turn, we isolate intervention effects from conversational variance. This is critical for small sample sizes where turn-by-turn divergence can dominate treatment effects.

**Conversation-aware evaluation.** CollabLLM's BigCodeBench pass_rate metric is systematically zero because the user simulator never conveys exact function signatures. Our conversation-aware judge evaluates against what the user actually requested, not a hidden test harness — revealing meaningful performance differences that the standard metric misses entirely.

These methodological improvements are applicable beyond our specific interventions and address systematic sources of noise in simulation-based multi-turn evaluation.

### 6.6 Limitations

**Sample sizes.** Our evaluation subsets are small (19–25 for LiC, 20 for CollabLLM), constrained by multi-turn simulation cost. Effect sizes should be interpreted with appropriate caution; the soft-attention experiments use even smaller test splits (12-13 samples).

**Simulated setting.** Both LiC and CollabLLM use simulated users. Real conversations involve more diverse user behavior, including references to prior assistant responses and non-linear requirement evolution.

**Task simplicity.** LiC's single-answer tasks favor task specification over context editing. CollabLLM provides a step toward more realistic interactions but still evaluates on self-contained problems. Long-horizon tasks (multi-file coding, iterative design) would provide a stronger test of context editing's value.

**Single model family.** All experiments use GPT-5-mini. The interaction between our methods and different model architectures is unexplored.

**CollabLLM preliminary.** CollabLLM results are on 20 samples per task without memory or ablation studies. These are directional findings that require scaling to confirm.

---

## 7. Conclusion

We present a self-aware reasoning framework for recovering from context contamination in multi-turn LLM conversations. Our key findings:

1. **Task specification reconstruction is the primary mechanism** for benchmarks where rederivation is cheap. Extracting user intent from user messages alone — without the assistant's prior responses — recovers most of the single-turn performance.

2. **Self-aware reasoning is architecturally demanding.** Without physically excluding assistant messages from the intent extraction step, even an external analyzer is contaminated by the same anchoring it tries to correct. Designing data flows around this limitation — rather than prompting through it — is essential.

3. **Context removal provides measurable additional benefit,** particularly on complex multi-output tasks. This motivates context editing for settings where tasks are stateful and rederivation is expensive.

4. **Memory-based learning partially bridges the gap** when hard attention is unavailable. On structured tasks, learned decontamination principles close up to 65% of the performance gap, and context reset (S1.5) consistently outperforms full-context presentation for soft-attention analysis. This points toward practical deployment in realistic settings where user intent cannot be extracted from user messages alone.

5. **The framework transfers to collaborative settings.** Initial CollabLLM results show context compaction improves accuracy on both math (+5pp) and code (+20pp) in a genuinely collaborative interaction paradigm, even using a simpler single-query analysis.

6. **Evaluation methodology matters.** User simulator quality control, replay-based isolation, and conversation-aware evaluation are necessary for reliable measurement in multi-turn simulation settings, and constitute a secondary contribution applicable beyond our specific interventions.

These results suggest a progression: for simple tasks, a clean task specification suffices; for moderately complex tasks, context removal adds value; for truly stateful long-horizon tasks, surgical context editing — preserving correct work while removing harmful content — should be essential. The soft-attention and CollabLLM experiments demonstrate initial viability for settings where hard attention is impossible, while highlighting that robust self-aware reasoning — the ability to reliably distinguish between helpful and harmful prior outputs within the same context — remains a fundamental open challenge for LLMs.

---

## References

- Laban, P., et al. (2025). Lost in Conversation: A Large-Scale Simulation of Multi-Turn Problem-Solving Conversations with LLMs. *arXiv*.
- Khalid, M., et al. (2025). ERGO: Entropy-Guided Context Resetting for Multi-Turn Conversations. *arXiv*.
- Huang, X., et al. (2026). Do LLMs Benefit from Their Own Words? Understanding Context Pollution in Multi-Turn Conversations. *arXiv*.
- Suzgun, M., et al. (2025). Dynamic Cheatsheet: Test-Time Learning with Mutable Memory. *arXiv*.
- [TODO: CollabLLM reference]
- Miyake, A., et al. (2000). The Unity and Diversity of Executive Functions. *Cognitive Psychology*.
- Diamond, A. (2013). Executive Functions. *Annual Review of Psychology*.
- Wei, J., et al. (2022). Chain-of-thought Prompting Elicits Reasoning in Large Language Models. *NeurIPS*.
- Wang, X., et al. (2023). Self-Consistency Improves Chain of Thought Reasoning in Language Models. *ICLR*.
- Yao, S., et al. (2024). Tree of Thoughts: Deliberate Problem Solving with Large Language Models. *NeurIPS*.
- Cobbe, K., et al. (2021). Training Verifiers to Solve Math Word Problems. *arXiv*.

---

## Appendix

### A. User Simulator Quality Control

[Detail the false negative analysis: user sim sufficiency check, samples excluded per task, methodology.]

### B. Per-Condition Sample Counts

[Table with raw numerator/denominator for each condition, for transparency. Explains timeout errors and exclusions.]

### C. Prompt Templates

[Key prompts: v8 task spec query, comparison query, v8_soft_cot, compaction analysis.]

### D. Cheatsheet Examples

[Beneficial vs harmful content, sanitization. Include learned decontamination principles from spec-curation experiments.]

### E. Trajectory Examples

[Annotated examples showing baseline failure → analysis → recovery for each task.]

### F. CollabLLM Evaluation Details

[Conversation-aware judge design, pass_rate analysis, implementation differences from CollabLLM paper pipeline.]
