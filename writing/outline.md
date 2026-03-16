# Context Editing for Multi-Turn Conversations: Closing the Reliability Gap Through Surgical History Rewriting

---

## Abstract

Large language models suffer a systematic reliability collapse in multi-turn conversations. When task specifications are revealed incrementally — as in natural human communication — performance drops by 39% on average compared to equivalent single-turn interactions, with unreliability increasing by 112% (Laban et al., 2025). Models overcommit to early incorrect assumptions and cannot self-correct because their flawed reasoning persists in context, anchoring future generation. Prior interventions either discard all assistant-generated content (recovering the trivial single-turn baseline) or rely on signals unavailable from black-box APIs. We propose *context editing*: an LLM-driven system that analyzes the conversation history to identify where the assistant's approach diverges from user intent, then surgically rewrites the context to remove erroneous assumptions while preserving correct progress. Our two-query analyzer architecture enforces hard attention separation — extracting user intent independently of assistant contamination before evaluating alignment. We further introduce a memory-based learning mechanism (Dynamic Cheatsheet) that accumulates transferable editing principles across problem instances without gradient updates. On the Lost in Conversation benchmark, context editing improves accuracy from 30% to 40% on code tasks, and adding learned memory raises it to 60% — a 2x improvement over the unmodified baseline. Across four task domains, at least one context editing variant outperforms the baseline, with the optimal strategy varying by task: full context rewriting with memory for code (+30pp), selective reset for database (+16.7pp), and memory-augmented selective reset for actions (+6pp). We further validate these results on a curated dev set of hard problems, where context editing with memory achieves 57.14% on code tasks where the baseline scores 0%. Our results demonstrate that multi-turn reliability is recoverable through intelligent context management, and that the decision of *what* to remove matters as much as *when* to intervene.

---

## 1. Introduction

The deployment of large language models increasingly involves multi-turn conversations. Users rarely specify complete requirements upfront — instead, they iteratively clarify, correct, and extend their requests across multiple exchanges. This conversational pattern is natural and efficient for humans but creates a fundamental problem for LLMs: once the model commits to an interpretation in an early turn, the resulting reasoning persists in context and anchors all subsequent generation, even when later user messages contradict the initial assumptions.

Laban et al. (2025) quantified this phenomenon through the "Lost in Conversation" (LiC) framework, a large-scale simulation of 200,000+ conversations across 15 LLMs and 6 task domains. Their core finding is striking: the performance gap between single-turn and multi-turn settings is driven primarily by *unreliability* (112% increase), not by reduced *aptitude* (only 16% decrease). In the best 10% of multi-turn runs, models perform nearly as well as in single-turn — the capability is preserved, but the model fails to access it reliably. Moreover, the degradation is binary: even splitting a task specification into just two messages triggers the full reliability collapse.

Four interlocking failure modes drive this collapse. Models generate premature answers before sufficient information is available, filling gaps with assumptions. These assumptions anchor subsequent reasoning, and when corrected, models patch rather than rewrite — causing answer bloat. Information from middle turns is disproportionately neglected (lost-in-the-middle across turns), and verbose responses introduce speculative content that gets treated as established fact. Once lost, models do not recover within the same conversation.

The only reliable mitigation identified by Laban et al. is manual: notice the model is lost, ask it to consolidate, and start a *new* conversation. Restating information within the same context is insufficient because the bad reasoning remains visible and continues to attract attention.

This points to a clear opportunity. If the problem is that bad content persists in context and anchors generation, the solution should remove that content — not by discarding everything and restarting (which is what the manual mitigation does), but by surgically identifying and removing the harmful portions while preserving useful progress. We call this *context editing*.

### Contributions

We make the following contributions:

1. **LLM-driven context editing.** We propose a system where an LLM analyzer inspects the conversation history and produces a structured assessment of user intent versus assistant divergence. When substantive issues are identified, the context is rewritten to remove polluted reasoning while preserving aligned work. Unlike prior approaches that use entropy thresholds (Khalid et al., 2025) or shallow classifiers (Huang et al., 2026), our approach requires only black-box API access and can reason about *why* the model is lost, not just *that* it is lost.

2. **Two-query hard attention architecture.** We introduce a two-query analyzer that enforces an architectural separation between user intent extraction and assistant evaluation. The first query sees *only* user messages and extracts a clean task specification; the second compares this specification against the full conversation. This prevents the analyzer from being contaminated by the assistant's framing — the same anchoring problem we are trying to solve.

3. **Memory-based learning for context editing.** We introduce a Dynamic Cheatsheet mechanism that accumulates transferable editing principles across problem instances. The cheatsheet learns meta-level patterns (e.g., "output format verification prevents false negatives," "reject assistant assumptions not grounded in user messages") rather than task-specific solutions. This is the first application of test-time learning to context management in multi-turn settings.

4. **Systematic evaluation across task domains.** We evaluate context editing on four task domains from the LiC benchmark (math, code, database, actions), comparing multiple strategy variants (baseline, append-only analysis, full context rewriting, selective reset) with and without memory. We show that at least one context editing variant outperforms the baseline on every task, but the optimal strategy is task-dependent — motivating future work on adaptive strategy selection.

---

## 2. Related Work

### 2.1 Lost in Conversation

Laban et al. (2025) introduced the Lost in Conversation (LiC) framework, demonstrating that LLMs suffer systematic performance degradation in multi-turn, underspecified conversations. Their methodology takes single-turn problems — where models achieve high accuracy — and "shards" them: the complete specification is split into pieces that are revealed incrementally by a simulated user across multiple turns.

The key findings are: (1) performance drops 39% on average compared to single-turn, (2) the degradation is primarily unreliability (+112%) rather than reduced aptitude (-16%), (3) all 15 tested models — from Llama3.1-8B to Gemini 2.5 Pro — exhibit similarly high multi-turn unreliability regardless of their single-turn capability, and (4) the degradation is binary, occurring fully with even a 2-turn conversation.

LiC identifies four failure modes: premature answer attempts (answers in the first 20% of turns score 30.9 vs 64.4 when waiting), answer bloat (20-300% longer final answers), loss-in-middle-turns (8% citation rate for turns 2-3 vs 20% for the final turn), and over-verbosity (shortest-response conversations outperform longest by 10-50%). Crucially, interventions within the same conversation context — including reasoning models, lower temperature, and agent-like recapitulation — fail to close the gap. Only starting a new conversation with consolidated information recovers performance.

We adopt the LiC simulation framework as our primary evaluation setting because it provides controlled, reproducible multi-turn scenarios with known ground truth. However, we note that strong LiC results can be achieved by trivially discarding all assistant content and concatenating user messages (recovering the single-turn baseline), which limits its value as a standalone benchmark. Our approach is designed to be non-exploitative: by preserving (edited) assistant content, improvements must come from genuinely useful editing decisions.

### 2.2 ERGO: Entropy-Guided Context Resetting

Khalid et al. (2025) proposed ERGO, which monitors the model's average token-level Shannon entropy at each turn and triggers a context reset when the entropy delta exceeds a calibrated threshold. Upon reset, all prior user messages are summarized into a single prompt, all assistant messages are discarded, and generation continues in a fresh context.

On the LiC simulator, ERGO achieves a 56.6% average performance gain over the sharded baseline, increases aptitude by 24.7%, and reduces unreliability by 35.3%. However, the approach has several limitations: (1) it requires logprob access, which many API providers limit (e.g., OpenAI provides only top-20 logprobs, degrading entropy estimates); (2) its reset operation discards all assistant messages, effectively recovering the Concat/single-turn baseline; (3) the entropy threshold is calibrated per-model and does not adapt; and (4) it uses a simplified LiC simulator variant that feeds shards directly as user messages without conversational rephrasing.

Our approach differs in three ways: we use the LLM itself to decide when and how to intervene (requiring only black-box API access), we preserve edited assistant content rather than discarding it entirely, and we incorporate a learning mechanism that improves intervention quality over time.

### 2.3 Do LLMs Benefit from Their Own Words?

Huang et al. (2026) investigated whether prior assistant responses help or hurt in multi-turn conversations. Testing on real-world datasets (WildChat, ShareLM) and LiC, they found that omitting all prior assistant responses frequently does not hurt — and sometimes improves — response quality. They term this "context pollution": earlier assistant outputs introduce errors, hallucinations, or stylistic artifacts that propagate across turns.

Their key findings include: (1) 36.4% of turns in real conversations are self-contained "new asks" that don't depend on prior assistant output; (2) one-sentence summaries of assistant responses beat both full context and full omission on LiC and WildChat; (3) an adaptive classifier (L1-regularized logistic regression on metadata, prompt category, and PCA-reduced embeddings) retains >95% of full-context performance at 70% of context consumption.

Huang et al.'s finding that one-sentence summaries outperform both extremes (full context and full omission) directly supports our thesis: the right answer is neither keeping everything nor discarding everything, but intelligent compression. However, their approach makes a binary per-turn choice (keep all or omit all) and requires model-specific training data from an LLM judge. Our context editing provides finer-grained control — surgically removing harmful content within responses while preserving useful portions — and requires no model-specific training.

### 2.4 CollabLLM

[TODO: CollabLLM paper — collaborative multi-turn LLM interaction. Describe setting, compare methodology.]

### 2.5 Dynamic Cheatsheet and Test-Time Learning

Suzgun et al. (2025) introduced the Dynamic Cheatsheet, a mutable text document that accumulates task-relevant knowledge across problem instances at test time without gradient updates. The cheatsheet is updated after each problem through LLM-driven reflection, enabling the system to learn from its own successes and failures.

We adapt this mechanism for context editing, targeting the cheatsheet at the analyzer component rather than the assistant itself. Our implementation uses a Reflect-then-Unify algorithm: per-trajectory takeaways are generated in parallel, then a single unification call merges them with the existing cheatsheet. We find that the *content* of the cheatsheet is critical — meta-level editing principles (output format verification, intent separation) transfer well, while task-specific solutions (algorithmic recipes, code snippets) cause harmful anchoring in the editor, the same failure mode we are trying to correct in the assistant.

---

## 3. Methods

### 3.1 Problem Setting

We adopt the LiC simulation framework. A single evaluation instance consists of:

- A **task** with a fully-specified question $q$ and ground truth answer $a$
- A **sharding** of $q$ into $k$ shards $\{s_1, \ldots, s_k\}$ that partition the specification
- A **simulated user** that reveals shards incrementally across turns
- An **assistant** (the model under evaluation) that must gather information and produce a correct answer
- A **system agent** that classifies each assistant response (answer attempt, clarification, etc.) and evaluates correctness

The conversation proceeds for up to $T$ turns. At each turn: the user reveals a shard (or responds to a clarification), the context strategy prepares the message history, the assistant generates a response, and the system agent evaluates. The simulation ends when the assistant produces a correct answer or all shards are exhausted.

### 3.2 Context Strategies

We define a `ContextStrategy` interface with a single method `prepare_context(trace, memory, model_client)` that is called before each assistant turn. The strategy may inspect, annotate, or rewrite the conversation history. We evaluate three primary strategies:

#### S0: Baseline (No Modification)

The full conversation history is passed to the assistant unchanged. This is the control condition. When memory is enabled, the cheatsheet is injected once into the system message.

#### S1: Append Analysis (Diagnosis Without Rewriting)

The `ConversationAnalyzer` (Section 3.3) runs on the conversation history. Its structured output — task specification, aligned content, and identified issues — is appended to the last user message. The full conversation history is preserved; this is append-only. A one-time system message addendum explains the analysis tags.

S1 serves as an ablation of S2: it provides the same diagnostic information but without removing polluted history from context. Comparing S1 against S2 isolates the contribution of context *rewriting* versus context *annotation*.

#### S2: Context Edit (Analyzer-Driven Rewriting)

Uses the same `ConversationAnalyzer` as S1. If substantive issues are identified (i.e., `AnalysisResult.needs_edit` is true), the conversation trace is reset: all prior messages are replaced with a compacted context containing only the clean task specification and aligned content. Any unprocessed user messages (shards revealed after the last analysis) are preserved.

A critical design decision: the *issues* identified by the analyzer guide the decision to edit but are **not reintroduced into the edited context**. Including descriptions of what went wrong would give the assistant new content to anchor on — reintroducing the very problem we are solving. Only the task specification and what the assistant got right survive into the edited context.

The edited context uses a `[compacted conversation]` role tag that integrates cleanly with the message rendering pipeline:

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

#### Agentic Edit (Selective Reset)

A variant that adds a gating step: a decision model analyzes the conversation and outputs yes/no for whether context editing is beneficial. If yes, the full S2 edit is performed; if no, the context passes through unchanged. This is motivated by the observation that on some tasks (e.g., database), always resetting disrupts conversations that are already on track.

### 3.3 Conversation Analyzer

The analyzer is the core analytical component, shared by S1 and S2. It uses a **two-query architecture** that enforces hard attention separation between user intent extraction and assistant evaluation.

#### Query 1: Task Specification

- **Input:** Only user messages, numbered by turn. No assistant responses are included.
- **Output:** A `<task_spec>` containing the complete, up-to-date specification as understood from the user's messages.
- **Purpose:** Pure information extraction. By architecturally excluding assistant responses from the input, we prevent the analyzer from being contaminated by the assistant's framing or assumptions. The model cannot rationalize the assistant's approach if it has never seen it.

#### Query 2: Comparison

- **Input:** The task specification from Q1, the full conversation history (including assistant responses), and optionally a memory cheatsheet.
- **Output:** `<aligned>` (what the assistant got right) and `<issues>` (what contradicts the specification).
- **Purpose:** Critical evaluation. The model compares the assistant's work against the independently-extracted specification, identifying content that would cause anchoring if left in context.

**Why two queries?** A single query cannot guarantee the model processes user intent before evaluating the assistant — especially with reasoning models whose internal thinking may interleave freely. Two queries enforce the sequencing architecturally. We considered restructuring input within a single prompt (showing user messages first, then the full conversation), but this provides no guarantee about processing order.

**Implicit edit decision.** Rather than an explicit yes/no pivot decision, the presence of substantive content in `<issues>` *is* the edit decision. A function filters out trivial responses ("None," "No issues," empty strings). This avoids the risk of the model saying "minor" for something major, or vice versa.

### 3.4 Memory-Based Learning (Dynamic Cheatsheet)

We implement a Dynamic Cheatsheet that accumulates editing principles across problem instances. The cheatsheet is a mutable text document, injected into the analyzer's Q2 (comparison) prompt via a `{memory_section}` placeholder. Memory is not used in Q1 (pure extraction — nothing to learn).

#### Update Mechanism: Reflect-then-Unify

After processing a batch of problems, the cheatsheet is updated in two steps:

1. **Reflect.** For each completed trajectory, an LLM generates a bullet list of generalizable takeaways. All reflections run in parallel. The reflection prompt includes the current cheatsheet, the rendered trajectory (including any edit markers), outcome (success/failure), and optionally the ground truth answer for oracle-guided learning.

2. **Unify.** A single LLM call merges all per-trajectory takeaways with the current cheatsheet, deduplicating, resolving contradictions (preferring newer evidence), and keeping the result concise.

#### Memory Target

Memory can be targeted at different components:

| Target | What it learns | Where it's injected |
|---|---|---|
| Analyzer (S1/S2) | Patterns for identifying harmful vs. useful assistant content | Q2 comparison prompt |
| Assistant (S0) | Task-domain strategies and pitfalls | System message |

We find that targeting memory at the *analyzer* (the component making editing decisions) is more effective than targeting the assistant directly.

#### Content Discipline

A critical finding: the *type* of knowledge in the cheatsheet matters more than the update mechanism. Meta-level editing principles transfer well across problems:
- "Verify output format matches user specification before declaring alignment"
- "Example-based disambiguation: when the user provides examples, use them as the specification"
- "Reject assistant assumptions not grounded in user messages"

Task-specific content (algorithmic recipes, code snippets, function signatures) causes the editor to anchor on stale patterns — the same failure mode we are correcting in the assistant. We enforce content discipline through explicit WHAT BELONGS / WHAT DOES NOT BELONG sections in the reflection and unification prompts, and cap cheatsheet length at 1500 words.

### 3.5 Conversation Rendering

The conversation is rendered for the assistant using an "Option 2" format: all messages (user, assistant, compacted conversation) are tagged and concatenated into a single user message, with a system message providing task instructions. This avoids multi-message API calls where the model might differentially attend to message boundaries.

---

## 4. Experiments

### 4.1 Evaluation Framework

We evaluate on the Lost in Conversation (LiC) benchmark across four task domains:

| Task | Domain | Evaluation | Source |
|---|---|---|---|
| **Math** | Mathematical reasoning | Exact numerical match | MATH dataset |
| **Code** | Code generation | Functional correctness (unit tests) | HumanEval + LiveCodeBench |
| **Database** | SQL generation | Execution match | Spider/BIRD |
| **Actions** | Action sequence generation | Sequence match | ALFWorld-derived |

#### Model Configuration

- **Assistant / Editor:** GPT-5-mini
- **User / System agents:** GPT-4o (upgraded from GPT-4o-mini due to content filter false positives on meta-instructions)
- **Infrastructure:** Azure OpenAI multi-endpoint load balancer

#### Compute and Latency Considerations

Multi-turn conversation simulation is inherently expensive. If a problem has $k$ shards (average ~8), each evaluation instance requires at minimum $k$ sequential LLM calls for the assistant alone, plus user agent calls, system agent verification, and (for S1/S2) two analyzer calls per turn. A single problem evaluation takes 8-16x longer than a single-turn evaluation.

This cost is further amplified for memory-based learning. The batched execution mode requires sequential processing across batches because each batch's cheatsheet update depends on the results of all prior batches. Within a batch, problems can be parallelized, but across batches, there is a strict sequential dependency. This means memory experiments cannot be fully parallelized — a run of $N$ problems with batch size $B$ requires $\lceil N/B \rceil$ sequential rounds.

These constraints limit the scale of our evaluation relative to single-turn benchmarks. We address this through careful subset selection (Section 4.2) and report results on curated subsets where each problem has been verified for consistent baseline behavior.

### 4.2 Subset Derivation

The full LiC benchmark contains hundreds of problems per task. Evaluating all problems across multiple strategy variants with the latency constraints described above is infeasible. We derive evaluation subsets using a two-stage filtering process:

1. **True/False Filtering.** We run the baseline (S0) configuration 3-5 times per problem. Problems that are always correct (indicating they are not affected by multi-turn degradation) or always incorrect across *all* configurations (indicating they may be fundamentally too hard or poorly sharded) are candidates for filtering. We retain problems with consistent baseline failure (always incorrect under S0) — these represent the "hard" or "problematic" instances where multi-turn degradation is most evident and context editing has the most potential to help.

2. **Consistency Threshold.** We apply a consistency threshold $t$: a problem is included in the dev set if it failed in at least $t$ out of $n$ baseline runs. Higher thresholds produce harder subsets. We use $t = n$ (failed in all runs) for our primary evaluation, ensuring every problem in the subset is one where the baseline reliably fails.

This process produces task-specific subsets:
- **Math:** 9 problems (test set) / 23 problems (dev set)
- **Code:** 20 problems (test set) / 25 problems (dev set)
- **Database:** 63 problems ($t=2$) / 48 problems ($t=3$) / 25 problems (dev set)
- **Actions:** 47 problems (test set) / 25 problems (dev set)

### 4.3 Experimental Conditions

We evaluate the following conditions on each task subset:

| Condition | Strategy | Memory | Description |
|---|---|---|---|
| Baseline | S0 | No | Unmodified conversation |
| Baseline + Memory | S0 | Yes (assistant) | Cheatsheet injected into system message |
| Reflection (S1) | S1 | No | Analysis appended, no rewriting |
| S1 + Memory | S1 | Yes (analyzer) | Analysis with learned comparison patterns |
| Context Edit (S2) | S2 | No | Analyzer-driven rewriting |
| S2 + Memory | S2 | Yes (analyzer) | Rewriting with learned editing principles |
| Agentic Edit | Selective | No | Gated reset (decision model) |
| Agentic + Memory | Selective | Yes (analyzer) | Gated reset with memory |

Memory experiments use batched execution (batch size 3-10 depending on task), continual learning mode, with ground truth answers available during reflection (oracle-guided learning).

### 4.4 Comparison with CollabLLM

[TODO: Describe CollabLLM experimental setup. Evaluate context editing in their setting — collaborative multi-turn interaction with different task structure.]

### 4.5 Comparison with Huang et al. Setting

[TODO: Describe replication of Huang et al.'s experimental setup. Evaluate context editing with their WildChat/ShareLM data and their FC/AO comparison methodology. Test whether surgical editing outperforms their binary keep-all/omit-all approach.]

---

## 5. Results

### 5.1 V1 Results: Cross-Task Strategy Comparison

Our initial experiments (v1 approach) evaluated six conditions across four task domains. All experiments use GPT-5-mini as the assistant and editor, GPT-4o for user/system agents.

**Table 1: V1 Results — Accuracy across tasks and conditions**

| Task ($N$) | Baseline | Reflect (S1) | Ctx Edit (S2) | S2+Mem | Agentic | Agentic+Mem | Best |
|---|---|---|---|---|---|---|---|
| **Code** (20) | 6/20 (30%) | 3/18 (17%)$^\dagger$ | 8/20 (40%) | **12/20 (60%)** | 8/19 (42%) | 4/20 (20%) | S2+M |
| **Math** (9) | 2/9 (22%) | 2/9 (22%) | 2/9 (22%) | 2/9 (22%) | 3/9 (33%) | 4/8 (50%)$^\dagger$ | AE+M |
| **DB $t$=3** (48) | 30/48 (63%) | 24/48 (50%) | 24/48 (50%) | 35/48 (73%) | **38/48 (79%)** | 28/48 (58%) | AE |
| **Actions** (47) | 14/47 (30%) | 8/34 (24%)$^\dagger$ | 16/47 (34%) | 15/47 (32%) | 11/47 (23%) | **17/47 (36%)** | AE+M |

$^\dagger$ Errors excluded (content filter). S2=context edit, AE=agentic edit, M=memory.

**Key findings:**

1. **At least one method beats baseline on every task.** The optimal strategy varies: S2+Memory for code (+30pp), Agentic Edit for database (+16.7pp), Agentic Edit+Memory for actions (+6pp) and math (+28pp).

2. **Reflection-only (S1 without memory) never helps.** It is consistently at or below baseline across all tasks, dropping to 17% on code (vs 30% baseline). This confirms that the value comes from context *rewriting* — removing polluted reasoning — not from generating diagnostic annotations. Append-only reflection adds noise to an already polluted context.

3. **Context editing is most effective on code.** S2+Memory achieves 60% on code, a 2x improvement over the 30% baseline. Code problems have consistent failure patterns (premature implementation, assumption lock-in on function signatures) that benefit from systematic editing with learned principles.

4. **Always-resetting hurts on database.** S2 without memory drops from 63% to 50% on database ($t$=3). The baseline is already strong on database (many problems solved in few turns), and always resetting disrupts conversations that are on track (average turns 3.7 to 9.1).

5. **Selective resetting (Agentic Edit) is best on database.** At 79.2%, it exceeds the baseline by 16.7pp while actually *decreasing* average turn count (3.4 vs 3.7). The decision model correctly identifies when resetting helps vs. hurts.

6. **Memory helps the editor but hurts the agentic decider.** S2+Memory improves over S2 on code (+20pp) and database (+23pp). But Agentic+Memory consistently underperforms Agentic alone on code (-22pp) and database (-21pp). The cheatsheet, trained on editing principles, makes the decider over-trigger resets. This suggests the decider needs its own memory target with decision-oriented principles.

### 5.2 V2 Results: Dev Set with Refined Analyzer

After refactoring the analyzer to the two-query architecture (v6) and externalizing prompts, we evaluated on curated dev sets of hard problems using GPT-5-mini (assistant) with GPT-4o-mini (user/system).

**Table 2: Dev Set Results — Hard problems only**

| Task ($N$) | Baseline | Base+Mem | S1 | S1+Mem | S2 | S2+Mem |
|---|---|---|---|---|---|---|
| **Math** (23) | 14.5% | 31.8% | 31.6% | 35.0% | **61.5%** | 50.0% |
| **Code** (25) | 0% | 20.0% | 25.0% | 40.0% | **57.1%** | 41.7% |
| **Database** (25) | 0% | 4.2% | 0% | **20.0%** | 4.0% | 0% |
| **Actions** (25) | 0% | 8.0% | 20.0% | **31.6%** | 16.0% | 16.0% |

Note: Exclusion rates vary significantly (0-13 per condition). Higher exclusion rates inflate accuracy percentages. Raw correct counts should be compared alongside percentages.

**Key findings:**

1. **S2 without memory is strongest on reasoning tasks.** On math (61.5%) and code (57.1%), full context rewriting provides the largest gains. These reasoning-intensive tasks benefit most from discarding incorrect partial work and restarting with a clean analysis.

2. **S1+Memory is the most robust strategy.** It shows improvements across all four tasks, including the challenging database task (0% to 20%). Unlike S2, it does not suffer from high exclusion rates. The append-only approach is more operationally stable while memory provides the learning signal.

3. **Memory helps S0 and S1 but can hurt S2.** Adding memory to S2 hurts math (61.5% to 50.0%) and code (57.1% to 41.7%). The memory content may bias the analyzer's comparison, causing it to over-weight learned patterns over current evidence. This suggests the analyzer prompt should treat memory as a weak prior rather than strong guidance.

4. **Memory consistently helps at every level.** Baseline to Baseline+Memory improves on all 4 tasks. S1 to S1+Memory improves on all 4 tasks. The cheatsheet provides transferable knowledge even without context rewriting.

### 5.3 CollabLLM Setting

[TODO: Results on CollabLLM experimental setting.]

### 5.4 Huang et al. Replication

[TODO: Results comparing context editing against FC/AO on WildChat/ShareLM data.]

---

## 6. Discussion

### 6.1 When Does Context Editing Help?

Our results reveal a clear pattern: the benefit of context editing depends on the interaction between task difficulty, baseline performance, and the nature of multi-turn failure modes.

**High-value targets: reasoning-intensive tasks with consistent failure patterns.** Code and math tasks show the largest gains. These tasks exhibit the classic LiC failure cascade: premature implementation, assumption lock-in, and answer bloat. Context editing interrupts this cascade by removing the anchoring content. The consistency of failure patterns also makes memory effective — learned editing principles transfer across problems of similar structure.

**Low-value or harmful: tasks with strong baselines.** On database ($t$=2, baseline 73%), always-resetting *hurts* performance. Many database problems are solved in few turns with minimal multi-turn degradation. Resetting disrupts these on-track conversations, increasing turn count from 3.7 to 9.1 and decreasing accuracy by 12.5pp. The lesson: context editing should be applied selectively, not universally.

**The "when" matters as much as the "how."** On database, Agentic Edit (79.2%) far outperforms S2 (50.0%), despite using the same editing mechanism. The difference is the gating decision — knowing *when* to edit is more valuable than the edit quality itself. Conversely, on code, S2+Memory (60%) outperforms Agentic Edit (42%), suggesting that *how* the edit is performed (and what the editor has learned) matters more when the task consistently benefits from intervention.

### 6.2 The Role of Memory

Memory is a double-edged sword. When targeted correctly, it provides substantial gains (S2+Memory on code: +20pp over S2). When targeted incorrectly, it actively hurts (Agentic+Memory on code: -22pp vs. Agentic).

The critical insight is **content discipline**. Early experiments with unconstrained cheatsheets saw the memory accumulate algorithmic recipes, specific function templates, and problem-specific code snippets. These caused the editor to anchor on stale patterns for new problems — exactly the failure mode we are trying to correct in the assistant. Restricting the cheatsheet to transferable meta-level editing principles resolved this.

This has implications for test-time learning more broadly: the abstraction level of learned knowledge must match the generality of its application. Domain-specific knowledge (which DP recurrence to use) does not transfer and actively harms; domain-general knowledge (verify output format, use examples as specification) transfers well.

### 6.3 Reflection vs. Rewriting

The S1 (append-only analysis) vs. S2 (rewriting) comparison provides a clean ablation of the rewriting mechanism. S1 without memory is consistently at or below baseline — generating diagnostic annotations and appending them to an already-polluted context adds noise rather than signal. The assistant cannot reliably act on "here's what's wrong" instructions when the wrong content is still visible and competing for attention.

S1 *with memory* is more competitive, suggesting that accumulated editing principles provide useful guidance even without context cleanup. However, this does not reach S2's peak performance on reasoning tasks, confirming that *removing* harmful content (hard attention) is more effective than *annotating* it.

### 6.4 Limitations

**Sample sizes.** Our evaluation subsets are small (9-48 problems per task), constrained by the computational cost of multi-turn simulation. While we observe consistent patterns across tasks, individual results may be affected by variance. Larger-scale evaluation is needed to confirm effect sizes.

**LiC simulator limitations.** The LiC framework uses simulated users with scripted shard reveals. Real users are less predictable, may provide contradictory information, and may reference assistant responses in ways that the simulated user does not. Our approach is designed for deployment realism (preserving edited assistant content), but has only been evaluated in the simulated setting.

**Model-specific results.** All experiments use GPT-5-mini as the assistant. The interaction between context editing and different model families (Claude, open-source models) is unexplored.

**Fixed analyzer model.** The analyzer uses the same model family as the assistant. A weaker or different analyzer might produce different results. The interaction between analyzer and assistant capability is not explored.

### 6.5 Proposed Ablations and Future Explorations

Based on our preliminary results, we identify several ablations and explorations:

1. **Memory target separation.** The agentic decider needs its own memory with decision-oriented principles (when to reset vs. continue), separate from the editing principles that help the analyzer. Current memory hurts the decider because editing principles don't translate to good reset decisions.

2. **Hybrid strategy.** Combine Agentic Edit's selective gating with S2+Memory's learned editing. Use the decision model (without memory) to gate, then S2+Memory to edit when triggered.

3. **Cross-task cheatsheet transfer.** Can a cheatsheet learned on code improve editing on actions? The meta-level nature of editing principles suggests potential for transfer.

4. **Analyzer model scaling.** Does a stronger analyzer (GPT-4o, Claude) improve editing quality, or is the two-query architecture sufficient to extract useful signals even from smaller models?

5. **Variance quantification.** Multiple runs per condition to separate signal from temperature noise, particularly for small subsets.

6. **Memory content ablation.** Systematically compare cheatsheets of different content types (meta-principles only, task-specific, mixed) and sizes to identify the optimal content discipline.

---

## 7. Conclusion

We have presented context editing, an LLM-driven approach to recovering multi-turn conversation reliability. By using a two-query analyzer to identify where the assistant's approach diverges from user intent — and surgically rewriting the context to remove erroneous content while preserving correct progress — we demonstrate consistent improvements over unmodified baselines across multiple task domains.

Our key findings are: (1) context *rewriting* is essential — append-only analysis does not help and can hurt; (2) the decision of *when* to edit matters as much as *how* to edit, with the optimal strategy depending on task characteristics; (3) memory-based learning can substantially amplify editing effectiveness (+20pp on code), but only when the cheatsheet is disciplined to store transferable meta-level principles rather than task-specific solutions; and (4) at least one context editing variant outperforms the baseline on every task evaluated, though no single variant is universally best.

### Future Work

Several directions extend this work:

**Improving conversational simulation.** The LiC simulator uses scripted shard reveals and does not model realistic user behaviors like referencing prior assistant responses, providing contradictory corrections, or expressing preferences implicitly. A higher-fidelity user simulator — potentially using a strong LLM prompted with realistic user personas — would better evaluate context editing's robustness to messy, real-world interactions.

**True long-context settings.** Our evaluation uses conversations of 3-12 turns. Real-world deployments involve much longer conversations where context window limits become binding. Context editing naturally addresses this by compressing the history, but the interaction between editing quality and conversation length is unexplored. Long conversations may benefit from periodic editing even when the assistant is on track, as a form of context window management.

**Agentic settings.** Modern LLM deployments increasingly use agentic architectures where the model takes actions, uses tools, and manages multi-step workflows. These settings amplify the multi-turn reliability problem: a wrong tool call based on an early assumption can create cascading failures across the workflow. Context editing could be applied to agentic traces — identifying and removing failed action sequences while preserving successful sub-task completions.

**Adaptive strategy selection.** Our results show that the optimal editing strategy varies by task. An adaptive system that selects the intervention level (no edit, append-only, full rewrite, selective reset) based on conversation-level features would be more robust than any fixed strategy. This could be learned from data or driven by the analyzer's assessment of conversation state.

**Native model capabilities.** If an LLM can recognize when it is confused through prompting (as our analyzer demonstrates), this capability is a natural target for reinforcement learning or fine-tuning. Training models to natively detect and recover from multi-turn anchoring — without external intervention — is the ultimate goal.

---

## References

- Laban, P., et al. (2025). Lost in Conversation: A Large-Scale Simulation of Multi-Turn Problem-Solving Conversations with LLMs. *arXiv*.
- Khalid, M., et al. (2025). ERGO: Entropy-Guided Context Resetting for Multi-Turn Conversations. *arXiv*.
- Huang, X., et al. (2026). Do LLMs Benefit from Their Own Words? Understanding Context Pollution in Multi-Turn Conversations. *arXiv*.
- Suzgun, M., et al. (2025). Dynamic Cheatsheet: Test-Time Learning with Mutable Memory. *arXiv*.
- [TODO: CollabLLM reference]

---

## Appendix

### A. Prompt Templates

[TODO: Include key prompts — analyzer Q1 (task spec), Q2 (comparison), reflection, unification.]

### B. Cheatsheet Examples

[TODO: Include example cheatsheets showing the difference between harmful (task-specific) and beneficial (meta-principle) content.]

### C. Trajectory Examples

[TODO: Include annotated examples showing the full conversation flow: baseline failure, analyzer diagnosis, edited context, and successful recovery.]
