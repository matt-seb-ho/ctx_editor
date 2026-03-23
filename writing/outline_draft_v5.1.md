# Can LLMs Curate Their Own Context? Investigating Self-Reflective Mitigation of Multi-Turn Performance Degradation

---

## Abstract

Large language models suffer systematic performance degradation in multi-turn conversations when task specifications are revealed incrementally — a phenomenon documented as "Lost in Conversation" (Laban et al., 2025). Prior work has identified context pollution (Huang et al., 2026) and proposed resetting strategies (ERGO; Khalid et al., 2025), but these approaches discard all prior assistant work, which is only viable when rederivation is cheap. We investigate whether LLMs can instead *self-reflectively curate* their own conversational context: explicitly re-reading the conversation to identify where they have gone off course, then selectively preserving what is correct and removing what is harmful. We decompose the analysis into subtasks — extracting a clean task specification from user messages, then comparing it against the assistant's work — to manually implement the executive function that current LLMs lack. A striking finding is that prior assistant messages act as a *cognitive hazard*: even a model prompted as an independent reviewer, with no obligation to maintain consistency with the assistant's prior reasoning, produces degraded analysis when exposed to those messages. This anchoring effect means that the analyzer cannot simply be told to ignore bad context — it must be structurally prevented from seeing it. While this structural exclusion is effective on the LiC benchmark (improving accuracy from 60% to 90% on math, 16% to 72% on code, 4% to 44% on database), it is not a general solution: realistic multi-turn settings involve stateful tasks where assistant messages contain essential progress. We present initial investigations into memory-based learning that teaches the analyzer to resist this anchoring when it must read the full conversation, closing up to 65% of the gap on structured tasks, and demonstrate positive preliminary results in the CollabLLM collaborative setting. As a secondary contribution, we introduce methodological improvements to multi-turn simulation evaluation — user simulator quality control, replay-based isolation, and conversation-aware judging — that yield more reliable performance estimates.

---

## 1. Introduction

The deployment of large language models increasingly involves multi-turn conversations. Users rarely specify complete requirements upfront; instead, they iteratively clarify, correct, and extend their requests across multiple exchanges. This conversational pattern is natural for humans but creates a fundamental problem for LLMs: once the model commits to an interpretation in an early turn, the resulting reasoning persists in context and anchors all subsequent generation, even when later user messages contradict the initial assumptions.

Laban et al. (2025) quantified this through the "Lost in Conversation" (LiC) framework, a large-scale simulation across 15 LLMs and 6 task domains. Their core finding is striking: the performance gap between single-turn and multi-turn settings is driven primarily by *unreliability* (112% increase), not reduced *aptitude* (only 16% decrease). The capability is preserved, but the model fails to access it reliably. Subsequent work has attributed this degradation to what Huang et al. (2026) term *context pollution*: the assistant's prior outputs introduce errors, incorrect assumptions, and speculative content that accumulate across turns, anchoring future generation on flawed foundations.

We observe two distinct mechanisms driving this pollution:

1. **User intent fragmentation.** In multi-turn conversations, the user's actual request is scattered across turns — paraphrased, revised, and buried in conversational noise. The model must reconstruct what the user wants from incomplete, non-linear input, and frequently fails.

2. **Reasoning anchoring.** The assistant's prior (often incorrect) reasoning remains in context and anchors future responses. Even when later user messages contradict earlier assumptions, the model cannot un-see its own mistakes.

Existing mitigation strategies — omitting all assistant messages (Huang et al., 2026), entropy-triggered context resets (ERGO; Khalid et al., 2025) — address both problems at once by discarding everything the assistant has said and effectively starting over. On the LiC benchmark, where rederivation is cheap and user messages fully specify the task, this works well. But these approaches cannot generalize to realistic settings where the assistant's prior work is essential: multi-step coding, iterative design, tool-use agents. In such settings, the challenge is not to discard context but to *curate* it — preserving what is correct while removing what is harmful.

This paper investigates whether LLMs can perform this self-curation. The core idea is straightforward: have the model re-read its own conversation, identify where it has gone off course, and intervene in the context before its next response. This is a form of self-reflective reasoning — reasoning about one's own prior reasoning to identify and correct failures. In cognitive psychology, this capacity is called *executive function*: the higher-order processes that manage attention, inhibit prepotent but incorrect responses, and flexibly update working memory (Miyake et al., 2000; Diamond, 2013). Current LLMs lack this regulatory capacity intrinsically, so we implement it externally: an agent that schedules additional LLM queries with carefully curated context windows, decomposing the self-reflection task into subtasks that accommodate the model's limitations.

Our approach decomposes the analysis into two subtasks rather than asking a single model to simultaneously extract user intent and evaluate prior work:

- **Task specification extraction.** A separate LLM call extracts a clean, consolidated task specification from user messages alone, reconstructing fragmented intent without the assistant's interpretive lens.

- **Approach evaluation.** A second call compares this clean specification against the full conversation to identify what the assistant got right and where it diverged.

- **Meta-cognitive learning.** A Dynamic Cheatsheet (Suzgun et al., 2025) accumulates transferable self-reflection principles across problem instances.

The reason for decomposing the analysis — rather than having a single call assess the full conversation — is our most striking finding: prior assistant messages act as a *cognitive hazard* for the analyzer. Even when prompted as an independent reviewer with no role obligation to the assistant, the model's analysis is severely degraded by exposure to the assistant's messages. The mechanism is not fully understood — it may be attention-based anchoring, implicit role consistency, or some other property of how LLMs process multi-party conversation — but the effect is unambiguous: analysis quality collapses to baseline or worse when the analyzer sees assistant messages during intent extraction (Section 5.2). This is not a prompting failure that more careful instructions could fix; we tried.

This means the problem is recursive: we want the model to identify what is bad in its own context, but the bad context impairs the model's ability to identify it. Structurally excluding assistant messages from the intent extraction step breaks this recursion on LiC, where user messages alone fully specify the task. But this structural exclusion is benchmark-specific — it works precisely because LiC tasks are self-contained and rederivation is cheap. For realistic multi-turn settings where the task specification depends on prior assistant work, we need the model to maintain analytical clarity *while looking at potentially contaminating content*.

We present initial investigations into this harder problem through two avenues:

1. **Memory-based decontamination learning.** We train the analyzer to resist anchoring by learning generalizable decontamination principles from oracle comparisons, closing up to 65% of the performance gap on structured tasks (Section 5.4).

2. **CollabLLM evaluation.** We test context compaction in a genuinely collaborative setting where assistant contributions are integral, finding positive preliminary results (+5pp math, +20pp code; Section 5.5).

These are early results on a hard problem. The gap between structural exclusion and learned resistance remains large (20-25pp), and our sample sizes are small. But the executive function framing — an agent that schedules LLM queries with custom context windows to implement the self-reflective capacity that models lack natively — is general, and the findings about cognitive hazards from assistant messages have immediate practical implications for anyone building multi-stage LLM systems.

---

## 2. Related Work

### 2.1 Lost in Conversation

Laban et al. (2025) introduced the Lost in Conversation (LiC) framework, demonstrating that LLMs suffer systematic performance degradation in multi-turn, underspecified conversations. Their methodology takes single-turn problems (where models achieve high accuracy) and "shards" them: the complete specification is split into pieces that are revealed incrementally by a simulated user across multiple turns. The key findings are: (1) performance drops 39% on average compared to single-turn, (2) the degradation is primarily unreliability (+112%) rather than reduced aptitude (-16%), (3) all 15 tested models exhibit similarly high multi-turn unreliability, and (4) interventions within the same conversation context fail to close the gap — only starting a new conversation with consolidated information recovers performance.

We adopt the LiC simulation framework as our primary evaluation setting because it provides controlled, reproducible multi-turn scenarios with known ground truth. We also introduce methodological improvements to the evaluation pipeline (Section 4.3) that yield more reliable performance estimates.

### 2.2 ERGO: Entropy-Guided Context Resetting

Khalid et al. (2025) proposed ERGO, which monitors token-level Shannon entropy at each turn and triggers a context reset when the entropy delta exceeds a calibrated threshold. Upon reset, all prior user messages are summarized into a single prompt and all assistant messages are discarded. ERGO achieves a 56.6% average performance gain on LiC. However, it requires logprob access (which many API providers limit), its reset discards all assistant messages entirely (recovering the single-turn baseline), and the entropy threshold is calibrated per-model. Our approach differs in using the LLM itself to decide when and how to intervene (requiring only black-box API access) and in attempting to preserve useful assistant work rather than discarding it wholesale.

### 2.3 Context Pollution (Huang et al.)

Huang et al. (2026) investigated whether prior assistant responses help or hurt in multi-turn conversations, coining the term *context pollution*. They found that omitting all prior assistant responses frequently does not hurt, and sometimes improves, response quality. Their key insight that one-sentence summaries outperform both full context and full omission directly supports our thesis: intelligent context curation beats both extremes. However, their approach makes a binary per-turn choice (keep all or omit all) and requires model-specific training. We adopt their terminology and build on their finding that assistant messages are the primary source of degradation.

### 2.4 CollabLLM

CollabLLM (citation TBD) proposes a framework for training LLMs to be more effective collaborators in multi-turn conversations, where the user iteratively refines requirements through natural dialogue. Unlike LiC's scripted shard reveals, CollabLLM uses an LLM-based user simulator that is instructed to be initially vague and gradually reveal intent — creating more naturalistic collaborative dynamics. CollabLLM evaluates on MATH-Hard and BigCodeBench, measuring both task accuracy and interactivity. We use CollabLLM as a second evaluation setting to test whether our methods transfer to more realistic, explicitly collaborative interactions.

### 2.5 Test-Time Scaling and Inference-Time Compute

The broader test-time scaling literature investigates how additional inference-time compute can improve model performance without parameter updates, including chain-of-thought reasoning (Wei et al., 2022), self-consistency (Wang et al., 2023), tree-of-thought search (Yao et al., 2024), and verifier-guided search (Cobbe et al., 2021). These methods focus on single-turn settings, scaling compute within a single generation. Our work extends test-time scaling to the *multi-turn* setting, where the challenge is not generating a better single response but managing accumulated context across turns. The key mechanism is different: rather than searching over possible outputs, we curate the *input context* presented to the model.

### 2.6 Dynamic Cheatsheet

Suzgun et al. (2025) introduced the Dynamic Cheatsheet, a mutable text document that accumulates task-relevant knowledge across problem instances at test time without gradient updates. We adapt this for context curation, targeting the cheatsheet at the analyzer rather than the assistant itself.

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

### 3.2 Conversation Analysis via Subtask Decomposition

The central challenge is getting an LLM to accurately assess what has gone right and wrong in a conversation. Rather than asking a single model to perform this analysis in one pass over the full conversation, we decompose it into two subtasks with different context windows — manually implementing the executive function (selective attention, distractor inhibition) that current LLMs lack.

**Subtask 1: Task Specification Extraction.** The model sees only the system message and all user messages — no assistant responses. It produces a consolidated task specification: a clean restatement of what the user is asking for. The system message grounds the specification in the correct output format (e.g., SQL against a specific schema, function calls with specific signatures), preventing over-elaboration.

**Subtask 2: Approach Evaluation.** The model sees the task specification from Subtask 1 plus the full conversation history, and optionally a memory cheatsheet. It produces an assessment of what the assistant got right (`aligned`) and what contradicts the specification (`issues`).

The reason for this decomposition is empirical, not aesthetic. The model cannot reliably extract user intent when assistant messages are present — it anchors on the assistant's framing even when instructed to focus on user messages. By physically excluding assistant messages from Subtask 1, we design around this limitation rather than attempting to prompt through it. We show in Section 5.2 that including assistant messages in Subtask 1 collapses the system's effectiveness to baseline or worse. This decomposition is our way of manually scheduling the model's attention: one query where it can only see user intent, then a second query where it compares that clean intent against the messy reality.

### 3.3 Context Strategies

Four strategies use the analysis output differently:

**Baseline (no intervention).** The full conversation history passes unchanged to the assistant.

**Append Analysis.** The analysis output (task specification + aligned + issues) is appended to the conversation before the assistant's next turn. The full history is preserved — the analysis provides corrective signal but polluting content remains visible.

**Always-Reset.** The analysis output is used to *replace* the conversation: all prior messages are removed and replaced with a compacted context containing the task specification and aligned content. Issues guide the edit but are not reintroduced. This removes polluting content entirely but loses any useful context not captured in the analysis.

**Gated Reset.** Like Always-Reset, but the context is only replaced when the analyzer detects substantive issues. When no issues are found, the conversation passes through unchanged.

### 3.4 Toward Realistic Settings: Full-Conversation Analysis

The hard-attention design (excluding assistant messages from Subtask 1) exploits a property of LiC: user messages alone fully specify the task. In realistic multi-turn settings — iterative design, collaborative coding, tool-use agents — the task specification may depend on prior assistant work. We investigate whether the model can learn to perform accurate self-reflection even when it must see the full conversation, including the contaminating assistant messages.

**Chain-of-thought decontamination.** We introduce a soft-attention variant that explicitly reasons through source attribution: (1) list every concrete requirement stated by the user, with message-level provenance, (2) identify assistant-originated interpretations and flag them as hypotheses rather than facts, (3) note user overrides, (4) write the spec using only user-grounded requirements. This makes the separation between user intent and assistant interpretation an explicit reasoning step rather than a structural guarantee.

**Memory-based decontamination learning.** We use hard-attention task specs as oracle training targets: the reflector compares soft-attention specs against hard-attention oracles to learn generalizable decontamination principles. These principles are injected into the soft-attention spec query via the Dynamic Cheatsheet mechanism (Section 3.5). The goal is to teach the model to perform the cognitive hazard resistance that the structural exclusion provides for free.

**Context reset with soft-attention analysis (S1.5).** A hybrid strategy that uses full-conversation analysis (the analyzer sees assistant messages) but resets the conversation context, removing polluted history before the assistant's next turn. This separates two effects: spec quality (soft vs. hard attention) and context pollution (full history vs. reset).

### 3.5 Memory-Based Learning

The Dynamic Cheatsheet accumulates self-reflection principles across problem instances, injected into the analyzer's prompt. For the primary hard-attention system, memory targets the approach evaluation subtask. For the soft-attention experiments, memory targets the spec extraction subtask, where it can directly improve resistance to the cognitive hazard.

**Update Mechanism: Reflect-then-Unify.** After processing a batch of problems: (1) *Reflect* — for each trajectory, an LLM generates generalizable takeaways from the outcome, with access to the current cheatsheet, the rendered trajectory, and optionally ground truth; (2) *Unify* — a single LLM call merges new takeaways with the current cheatsheet, deduplicating and resolving contradictions.

**Content Discipline.** The *type* of knowledge matters more than the update mechanism. Meta-level principles transfer well ("verify output format matches user specification," "reject assistant assumptions not grounded in user messages"). Task-specific content (algorithmic recipes, code snippets) causes the analyzer to anchor on stale patterns — recreating the failure mode we are correcting. We cap cheatsheet length at 1500 words.

### 3.6 CollabLLM Adaptation: Context Compaction

To test our methods in a more naturalistic collaborative setting, we adapt the framework for the CollabLLM evaluation pipeline. The key adaptation is a **Context Compaction Strategy** that activates after user turn 4 and runs unconditionally every turn:

1. **Single-pass analysis**: An "independent reviewer" prompt reads the full conversation and produces a task specification, what is good about the assistant's approach, and what should be changed.

2. **Context compaction**: The analysis plus full conversation are fed into a compaction prompt that generates a clean summary (task spec + work completed so far).

3. **Context reset**: The conversation is replaced with the compacted context, removing all previous messages from the assistant's view.

This uses a single-pass analysis (no subtask decomposition), since CollabLLM conversations are genuinely collaborative and the task specification may depend on assistant contributions. It represents the realistic end of our spectrum — full-conversation analysis without the structural exclusion that works on LiC.

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

**Replay mode (LiC).** To isolate the effect of our interventions from conversational variance, we use a replay methodology: all strategies share the same baseline conversation prefix (from an unmodified baseline run) and only the final assistant turn is regenerated with the intervention applied. This ensures identical conversational context across conditions.

### 4.2 Experimental Conditions

**LiC — Primary conditions:**

| Condition | Analysis | Context | Memory |
|-----------|:--------:|:-------:|:------:|
| Baseline | — | Full | — |
| Baseline + Memory | — | Full | Assistant |
| Omit Assistant (Huang) | — | User msgs only | — |
| Concatenate User (ERGO-style) | — | Reset, concat user | — |
| Append Analysis | Decomposed | Full + appended | — |
| Append Analysis + Memory | Decomposed | Full + appended | Analyzer |
| Always-Reset | Decomposed | Replaced | — |
| Always-Reset + Memory | Decomposed | Replaced | Analyzer |
| Gated Reset | Decomposed | Conditional | — |

**LiC — Soft-attention conditions (dev test splits):**

| Condition | Spec source | Context | Memory |
|-----------|:--------:|:-------:|:------:|
| S1-soft-cot | Full conv. (CoT) | Full + appended | — |
| S1-soft-cot + Memory | Full conv. (CoT) | Full + appended | Spec query |
| S1.5-soft-cot | Full conv. (CoT) | Reset | — |
| S1.5-soft-cot + Memory | Full conv. (CoT) | Reset | Spec query |
| S1-speconly (hard attention) | User msgs only | Full + appended | — |

**CollabLLM conditions:**

| Condition | Analysis | Context |
|-----------|:--------:|:-------:|
| Baseline | — | Full |
| Context Compaction | Single-pass | Reset (after turn 4) |

Memory experiments use batched execution (batch size 5) with continual learning and oracle-guided reflection (ground truth available during cheatsheet updates).

### 4.3 User Simulator Quality Control (LiC)

The sharded disclosure format occasionally produces user messages that distort the original problem, making the task unsolvable regardless of the assistant's capability. We pre-screen baseline traces using an LLM judge that compares the union of user simulator messages against the original single-turn question and flags cases where critical details are absent or materially changed. Flagged samples are excluded from all conditions (3 math, 6 code, 0 database, 2 actions). This ensures accuracy denominators reflect problems the assistant could reasonably solve.

This quality control step is itself a contribution: without it, evaluation conflates assistant failure with user simulator failure, inflating variance and understating intervention effects. We recommend this screening as standard practice for simulation-based multi-turn evaluation.

### 4.4 CollabLLM Evaluation Methodology

CollabLLM's standard BigCodeBench evaluation uses test-case execution (pass_rate), which requires exact function signatures. In the multi-turn setting, the user simulator never conveys exact function specs (it is instructed to be vague), making pass_rate systematically zero for all conditions — a ceiling imposed by the evaluation harness, not by code quality. We develop a **conversation-aware LLM judge** that evaluates the assistant's code against what the user actually asked for, rather than against a hidden test harness the assistant never saw. Using GPT-5 as judge (which is stricter and more discriminating than GPT-4o), this provides a fairer metric for the collaborative setting.

---

## 5. Results

### 5.1 Main Results (LiC)

**Table 1: Effect of intervention strategy (no memory)**

| Strategy | Math | Code | Database | Actions |
|----------|:----:|:----:|:--------:|:-------:|
| Baseline | 60% | 16% | 4% | 9% |
| Omit Assistant (Huang) | 85% | 78% | 32% | 83% |
| Concatenate User (ERGO-style) | 84% | 68% | 32% | 87% |
| Append Analysis (ours) | 80% | 56% | 32% | 22% |
| Always-Reset (ours) | 80% | 69% | 40% | 30% |
| Gated Reset (ours) | 75% | 72% | 44% | 13% |

**Table 2: Effect of adding memory (our methods only)**

| Strategy | Math | Code | Database | Actions |
|----------|:----:|:----:|:--------:|:-------:|
| Baseline | 60% | 16% | 4% | 9% |
| Baseline + Memory | 55% | 21% | 4% | 9% |
| Append Analysis | 80% | 56% | 32% | 22% |
| Append Analysis + Memory | **90%** | 68% | **44%** | 9% |
| Always-Reset | 80% | 69% | 40% | 30% |
| Always-Reset + Memory | 85% | 68% | **44%** | 30% |

Note: Some conditions had timeout errors reducing effective sample sizes. See Appendix B for per-condition sample counts.

#### Simple baselines are strong when rederivation is cheap

The most important comparison in Table 1 is between our analysis-based methods and the simpler prior-work baselines. On math, code, and actions, simply omitting assistant messages or concatenating user messages matches or exceeds our analysis pipeline. The prior-work baselines are particularly dominant on actions (+53-57pp over our best), where the structured function-call output format is degraded by natural-language analysis intermediaries.

This confirms a key insight: on the LiC benchmark, the problem is primarily that the assistant's prior messages are harmful, and removing them is sufficient. The model can solve these tasks from scratch given clean user messages.

#### Analysis adds value through intelligent consolidation

Our methods outperform the simple baselines on **database** (44% vs 32%), the most schema-dependent task where raw fragmented user messages are insufficient. The task specification extraction — which consolidates scattered user requirements into a structured spec grounded in the system message's schema — provides value beyond simple message filtering. On **math with memory**, our Append Analysis + Memory (90%) also outperforms omit-assistant (85%), showing that learned analysis principles can exceed what raw user messages provide.

#### Context removal provides additional benefit over analysis alone

Always-Reset outperforms Append Analysis on code (+13pp), database (+8pp), and actions (+8pp). Both use identical analysis; the difference is whether the assistant sees the full polluted history or a clean compacted context. This confirms that context pollution — the assistant anchoring on its prior incorrect responses — is a real and measurable problem separable from intent fragmentation.

#### Memory amplifies analysis quality

Append Analysis + Memory achieves the best results on math (90%) and ties for best on database (44%). Memory helps the analyzer produce more decisive task specifications and more concrete error identification. On single-output tasks, better analysis quality can substitute for context removal.

### 5.2 The Cognitive Hazard: Why the Analyzer Must Be Shielded

Our subtask decomposition omits assistant messages from the spec extraction step. Is this structural exclusion necessary, or can the analyzer extract user intent reliably from the full conversation?

We test four configurations varying two axes: (1) whether the spec extraction sees only user messages (*hard attention*) or the full conversation (*soft attention*), and (2) whether the system uses one subtask (spec only) or two (spec + evaluation).

**Table 3: Analyzer input ablation (Append Analysis, no memory)**

| Configuration | Math | Code | Database |
|---------------|:----:|:----:|:--------:|
| Hard attention, spec only | 70% | 63% | 40% |
| Hard attention, spec + eval | **80%** | 56% | 32% |
| Soft attention, single pass | 55% | 21% | 4% |
| Soft attention, spec + eval | 40% | 11% | 8% |
| Baseline (no analysis) | 60% | 16% | 4% |

#### Assistant messages are a cognitive hazard for the analyzer

When the analyzer sees assistant messages during spec extraction, performance collapses to baseline or worse. Both soft-attention variants produce analysis that is not just unhelpful but *actively harmful*: the soft-attention decomposed variant performs below baseline on math (40% vs 60%) and code (11% vs 16%).

This is evidence that context pollution is not specific to the conversational assistant role — it is a general property of how LLMs process multi-party conversation context. Even a model explicitly tasked with critical analysis, prompted as an independent reviewer, anchors on the assistant's reasoning when exposed to it. The exact mechanism is unclear — it may be attention-based anchoring on the most recent or most detailed content, implicit role consistency, or some other property — but the effect is robust across tasks.

#### The recursive problem: contamination amplifies through chained calls

The soft-attention decomposed variant (40% math, 11% code) underperforms the soft-attention single-pass variant (55% math, 21% code). When Subtask 1 produces a contaminated specification and passes it to Subtask 2 as authoritative ground truth, the contamination compounds. Each stage inherits and amplifies errors from the prior stage. This contamination amplification is a cautionary finding for anyone designing multi-stage LLM pipelines — chaining calls can amplify rather than correct errors when earlier stages are contaminated.

#### The task specification alone is surprisingly effective

The hard-attention spec-only variant (one subtask, no approach evaluation) matches or exceeds the full decomposed system on code (63% vs 56%) and database (40% vs 32%) at half the LLM cost. The approach evaluation adds value on math (+10pp) but introduces noise on structured-output tasks. This suggests a task-adaptive approach: spec-only for tasks with well-defined output formats, full decomposition for tasks requiring nuanced error identification.

### 5.3 Can Context Editing Rescue Contaminated Analysis?

If the analysis is contaminated (built from the full conversation), can we still extract value by removing the bad conversation context and presenting only the (contaminated) analysis?

**Table 4: Context editing with contaminated vs. clean analysis**

| Strategy | Math | Code | Database |
|----------|:----:|:----:|:--------:|
| Baseline | 60% | 16% | 4% |
| Soft-attention analysis, appended | 55% | 21% | 4% |
| Soft-attention analysis, context edit | 55% | 26% | 4% |
| Hard-attention analysis, appended | **80%** | **56%** | **32%** |
| Hard-attention analysis, context edit | **80%** | **69%** | **40%** |

Context editing cannot rescue contaminated analysis. The bottleneck is analysis quality, not delivery mechanism. Context editing is a *force multiplier* on analysis quality: with clean analysis it provides +8–13pp over appending; with contaminated analysis it provides nothing. This underscores that the cognitive hazard is the fundamental problem — the delivery mechanism is secondary.

### 5.4 Learning to Resist the Cognitive Hazard

The structural exclusion of assistant messages is effective but LiC-specific. Can the analyzer learn to produce clean specs even when it must see the full conversation? We evaluate on held-out test splits (Math n=12, Code n=13, Database n=13) using the chain-of-thought soft-attention variant with and without memory-trained decontamination.

**Table 5: Soft-attention spec quality — S1 (full conversation visible)**

| Condition | Math | Code | Database |
|-----------|:----:|:----:|:--------:|
| Soft-cot (no memory) | 40% | 13% | 31% |
| Soft-cot + memory | 56% | 14% | **46%** |
| Hard attention (oracle) | **80%** | **40%** | 54% |

**Table 6: Soft-attention spec quality — S1.5 (conversation reset)**

| Condition | Math | Code | Database |
|-----------|:----:|:----:|:--------:|
| Soft-cot (no memory) | 42% | 23% | 31% |
| Soft-cot + memory | 42% | 25% | **46%** |
| Hard attention (oracle) | **67%** | **46%** | 54% |

#### Context reset helps even with contaminated specs

S1.5 (reset) outperforms S1 (full conversation) across tasks for soft-attention analysis: code improves from 13% to 23% (no memory) and 14% to 25% (with memory). Even when the spec itself is contaminated, removing the polluted conversation history from the assistant's view reduces anchoring. Context pollution and spec contamination are separable problems.

#### Memory teaches partial resistance to the cognitive hazard

Memory-based decontamination shows its strongest effect on database: +15pp in both S1 and S1.5, closing 65% of the gap to hard attention. The learned cheatsheet converged on structured decontamination principles — "build a user-only spec first, then overlay assistant suggestions as hypotheses" and "anchor to schema for column/table names rather than accepting the assistant's SQL choices." These principles transfer to held-out test samples.

Code remains resistant to memory improvement (+1-2pp), suggesting that code spec contamination is more structurally diverse and resists generic decontamination principles. The structural guarantee of never seeing assistant messages provides something that learned heuristics cannot fully replicate — but in settings where that guarantee is unavailable, memory-trained soft attention with context reset offers a meaningful improvement over naive full-conversation analysis.

### 5.5 CollabLLM Setting

We evaluate context compaction in the CollabLLM collaborative setting, where the user simulator is instructed to be initially vague and gradually reveal intent through natural dialogue.

**Table 7: CollabLLM results**

| Task | Baseline | Compaction | Delta |
|------|:--------:|:----------:|:-----:|
| MATH-Hard (LLM judge) | 40.0% (8/20) | **45.0% (9/20)** | +5.0pp |
| BigCodeBench (GPT-5 conv. judge) | 62.5% | **82.5%** | **+20.0pp** |
| BigCodeBench (matched subset, n=12) | 58.3% | **75.0%** | +16.7pp |

Despite using single-pass full-conversation analysis (no structural exclusion), context compaction improves accuracy on both tasks. The BigCodeBench improvement is particularly notable: +20pp overall. Compaction helps by removing accumulated confusion from vague early exchanges, distilling the user's requirements, and preserving correct work while discarding dead ends. This suggests that even imperfect self-reflection provides value when it replaces a long, confused conversation history — the bar for "useful analysis" is lower in collaborative settings where context naturally accumulates noise.

Context compaction also reduces average assistant tokens by 74% on math (2,796 to 725) with no increase in cost, as the analysis LLM calls are offset by shorter downstream contexts.

---

## 6. Discussion

### 6.1 What LiC Tells Us (and What It Doesn't)

Our results, together with the prior-work baselines, paint a clear picture of the LiC benchmark: it is a setting where rederivation is cheap. Simply removing assistant messages and giving the model clean user messages is a very strong baseline — matching or exceeding our analysis pipeline on 3 of 4 tasks. Our analysis-based methods outperform on database (where schema-grounded consolidation matters) and math with memory (where learned principles improve spec quality), but the marginal benefit of intelligent analysis over brute-force removal is modest on LiC.

This is not a limitation of our approach — it is a characterization of the benchmark. LiC was designed to isolate the anchoring phenomenon with single-answer tasks. The real test of context curation methods lies in settings where you *cannot* simply start over: multi-step coding where the assistant has built up a codebase, iterative design where prior artifacts inform future work, tool-use agents where actions have been taken. Our CollabLLM results (Section 5.5) offer a preliminary step in this direction, and the soft-attention decontamination experiments (Section 5.4) address the prerequisite capability.

### 6.2 The Cognitive Hazard and Its Implications

The finding that assistant messages degrade analysis quality — even for a model prompted as an independent reviewer — has implications beyond our specific setting. Any system that uses an LLM to evaluate, critique, or improve another LLM's output faces this risk. The cognitive hazard means that multi-stage LLM pipelines cannot rely on prompting to achieve selective attention. Structural data flow design — controlling what each stage sees — is the reliable approach.

The exact mechanism behind this cognitive hazard remains unclear. Possible explanations include: (1) attention-based anchoring on the most detailed or recent content, (2) implicit role consistency where the model resists contradicting "assistant" outputs even when not in the assistant role, (3) information integration where the model treats all context as equally authoritative regardless of source. Understanding this mechanism is an important direction for future work, as it would inform whether the hazard can be mitigated through training or whether architectural solutions are fundamentally necessary.

### 6.3 Executive Function as an Agent Design Pattern

Our approach can be understood as a general design pattern: implementing executive function through an agent that schedules LLM queries with custom context windows. The key insight is that different subtasks of self-reflection require different context. Intent extraction needs to be shielded from contaminating content. Approach evaluation needs to see both the clean intent and the messy reality. Memory accumulation needs access to outcomes.

This pattern generalizes beyond our specific decomposition. Any setting where an LLM needs to reason about potentially misleading context — code review where the existing code anchors the reviewer, fact-checking where the claim anchors the checker, debate where the opponent's argument anchors the judge — could benefit from careful context scheduling. The executive function framing provides a vocabulary for this: what information should each reasoning step attend to, and what should it be inhibited from seeing?

Our implementation is an initial, manually-designed version of this pattern. A natural extension is learning the decomposition itself — using outcomes to discover which context windows enable the best self-reflection for a given task structure.

### 6.4 Memory: What Transfers and What Doesn't

Memory provides consistent benefit when applied to Append Analysis (+10pp math, +12pp code, +12pp database). In the soft-attention setting, memory teaches partial resistance to the cognitive hazard, with the strongest effect on structured tasks (database +15pp). The learned cheatsheets converge on meta-level decontamination principles — provenance tracking, schema anchoring, treating assistant outputs as hypotheses.

Memory cannot overcome structural barriers: on actions (an accumulation problem, not an analysis problem) and on code in the soft-attention setting (where contamination patterns are too diverse for generic principles). This task-dependence suggests that memory-based decontamination complements but cannot replace architectural solutions.

### 6.5 Evaluation Methodology as Contribution

Our experience with both LiC and CollabLLM highlights the importance of evaluation methodology in multi-turn settings:

**User simulator quality control.** Without screening for user simulator failures, evaluation conflates assistant capability with simulator quality. Our LLM-based screening identifies cases where the simulated user distorts the original problem, enabling cleaner measurement of intervention effects.

**Replay-based isolation.** By sharing baseline conversation prefixes across conditions and only regenerating the final turn, we isolate intervention effects from conversational variance. This is critical for small sample sizes where turn-by-turn divergence can dominate treatment effects.

**Conversation-aware evaluation.** CollabLLM's BigCodeBench pass_rate metric is systematically zero because the user simulator never conveys exact function signatures. Our conversation-aware judge evaluates against what the user actually requested — revealing meaningful performance differences that the standard metric misses entirely.

### 6.6 Limitations

**Sample sizes.** Our evaluation subsets are small (19-25 for LiC, 20 for CollabLLM), constrained by multi-turn simulation cost. The soft-attention experiments use even smaller test splits (12-13 samples). Effect sizes should be interpreted with appropriate caution.

**Simulated setting.** Both LiC and CollabLLM use simulated users. Real conversations involve more diverse user behavior, including references to prior assistant responses and non-linear requirement evolution.

**Task simplicity.** LiC's single-answer tasks favor brute-force context removal over intelligent curation. CollabLLM provides a step toward more realistic interactions but still evaluates on self-contained problems. Long-horizon tasks (multi-file coding, iterative design) would provide a stronger test of context curation's value.

**Single model family.** All experiments use GPT-5-mini. The interaction between our methods and different model architectures is unexplored.

**CollabLLM preliminary.** CollabLLM results are on 20 samples per task without memory or ablation studies. These are directional findings that require scaling to confirm.

**Cognitive hazard mechanism.** We document the hazard but do not explain its mechanism. Understanding *why* assistant messages degrade analysis — and whether it can be mitigated through training — is an important open question.

---

## 7. Conclusion

We investigate whether LLMs can self-reflectively curate their conversational context to mitigate multi-turn performance degradation. Our key findings:

1. **Self-reflective context curation works, but simple baselines are strong on LiC.** On the LiC benchmark, where rederivation is cheap, simply omitting assistant messages often suffices. Our analysis-based methods add value primarily through intelligent consolidation (database, math with memory) and point toward settings where brute-force removal is insufficient.

2. **Assistant messages are a cognitive hazard for the analyzer.** Even a model prompted as an independent reviewer produces severely degraded analysis when exposed to the assistant's prior messages. This hazard is not addressable through prompting — it requires structural exclusion or learned resistance. Any multi-stage LLM system should consider this when designing data flows.

3. **Memory-based learning teaches partial resistance** to the cognitive hazard. On structured tasks, learned decontamination principles close up to 65% of the performance gap when the analyzer must see the full conversation. This is an initial step toward the harder problem of maintaining analytical clarity in the presence of contaminating context.

4. **The framework transfers to collaborative settings.** Preliminary CollabLLM results show context compaction improves accuracy in a genuinely collaborative paradigm, even using full-conversation analysis without structural exclusion.

5. **Evaluation methodology matters.** User simulator quality control, replay-based isolation, and conversation-aware evaluation are necessary for reliable measurement in multi-turn simulation settings.

This work is an initial investigation into a fundamental challenge: enabling LLMs to reason about their own reasoning in the presence of misleading context. The executive function framing — an agent scheduling LLM queries with custom context windows — provides a general pattern for implementing the self-reflective capacity that models lack natively. Scaling to harder, more stateful tasks where context curation (rather than context removal) is essential remains the central open problem.

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

[Key prompts: task spec extraction, approach evaluation, soft-attention CoT, compaction analysis.]

### D. Cheatsheet Examples

[Beneficial vs harmful content, sanitization. Include learned decontamination principles from spec-curation experiments.]

### E. Trajectory Examples

[Annotated examples showing baseline failure → analysis → recovery for each task.]

### F. CollabLLM Evaluation Details

[Conversation-aware judge design, pass_rate analysis, implementation differences from CollabLLM paper pipeline.]
