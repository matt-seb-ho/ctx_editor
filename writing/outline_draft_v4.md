# Recovering from Context Contamination in Multi-Turn LLM Conversations

---

## Abstract

Large language models suffer systematic performance degradation in multi-turn conversations: when task specifications are revealed incrementally, models overcommit to early incorrect assumptions and cannot self-correct because flawed reasoning persists in context. We term this *context contamination* and show it operates through two mechanisms: (1) user intent becomes fragmented across turns, and (2) the assistant's prior incorrect reasoning anchors future generation. We introduce an *executive function* framework that addresses both: an LLM-as-analyzer extracts a clean task specification from user messages alone (addressing intent fragmentation) and identifies correct versus harmful content in the assistant's responses (addressing reasoning contamination). A key architectural insight is *hard attention*: the analyzer must be physically prevented from seeing the assistant's prior responses when extracting user intent, because even an external analyzer model is susceptible to the same anchoring it is trying to correct. On the Lost in Conversation benchmark, our methods improve accuracy from 60% to 90% on math, 16% to 72% on code, 4% to 44% on database, and 9% to 30% on actions. Ablation studies confirm that hard attention is load-bearing (removing it collapses gains to zero) and that context removal provides additional benefit beyond analysis alone, particularly on multi-output tasks.

---

## 1. Introduction

[Same motivational framing as v3: multi-turn degradation, LiC findings, executive function analogy. Updated to reflect two-problem decomposition.]

We identify two distinct mechanisms driving context contamination:

1. **User intent fragmentation.** In multi-turn conversations, the user's actual request is scattered across turns — paraphrased, revised, and buried in conversational noise. The model must reconstruct what the user wants from incomplete, non-linear input, and frequently fails.

2. **Reasoning contamination.** The assistant's prior (often incorrect) reasoning remains in context and anchors future responses. Even when later user messages contradict earlier assumptions, the model cannot un-see its own mistakes.

These two problems require different solutions. Intent fragmentation is addressed by *task specification reconstruction*: an independent extraction of what the user wants from their messages alone, free from the assistant's interpretive lens. Reasoning contamination is addressed by *context editing*: surgically removing harmful content while preserving correct progress.

Both solutions depend on a shared architectural principle we call *hard attention*: physically excluding the assistant's prior responses from the analysis stage that extracts user intent. We show that this separation is load-bearing — without it, even an external analyzer model falls prey to the same anchoring phenomenon, producing analysis that reflects the assistant's errors rather than correcting them.

[Executive function framing: monitoring, inhibition, flexible updating, meta-cognition. Same structure as v3 but updated with two-problem language.]

---

## 2. Related Work

[Same structure as v3. Add CollabLLM description when available.]

---

## 3. Methods

### 3.1 Problem Setting

[Same as v3: LiC simulation framework, sharding, agents.]

### 3.2 Conversation Analyzer: Two-Query Architecture

The analyzer is the core component, shared by all intervention strategies. It uses a two-query architecture that enforces hard attention separation.

**Query 1 (Task Specification).** Sees the system message and all user messages. No assistant responses. Produces a consolidated task specification — a clean restatement of what the user is asking for. The system message grounds the specification in the correct output format (e.g., SQL against a specific schema, function calls with specific signatures), preventing over-elaboration.

**Query 2 (Comparison).** Sees the task specification from Query 1 plus the full conversation history, and optionally a memory cheatsheet. Produces an assessment of what the assistant got right (`aligned`) and what contradicts the specification (`issues`).

The critical design choice is that Query 1 never sees assistant messages. This enforces a clean separation: user intent is extracted without contamination, then used as an independent reference point to evaluate the full conversation. We show in Section 5.2 that relaxing this separation collapses the system's effectiveness.

### 3.3 Context Strategies

Four strategies use the analyzer's output differently:

**Baseline (no intervention).** The full conversation history passes unchanged to the assistant.

**Append Analysis.** The analyzer runs and its output (task specification + aligned + issues) is appended to the conversation before the assistant's next turn. The full history is preserved — the analysis provides corrective signal but contaminating content remains visible.

**Always-Reset.** The analyzer runs and its output is used to *replace* the conversation: all prior messages are removed and replaced with a compacted context containing the task specification and aligned content. Issues guide the edit but are not reintroduced. This removes contaminating content entirely but loses any useful context not captured in the analysis.

**Gated Reset.** Like Always-Reset, but the context is only replaced when the analyzer detects substantive issues. When no issues are found, the conversation passes through unchanged.

### 3.4 Memory-Based Learning

[Same as v3 Section 3.5: Dynamic Cheatsheet, reflect-then-unify, content discipline. Updated to note memory targets Query 2 only.]

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

**Table 1: Accuracy across tasks and intervention strategies (replay-last-turn, v8 prompts)**

| Strategy | Math | Code | Database | Actions |
|----------|:----:|:----:|:--------:|:-------:|
| Baseline | 60% | 16% | 4% | 9% |
| Baseline + Memory | 55% | 21% | 4% | 9% |
| Append Analysis | 80% | 56% | 32% | 22% |
| Append Analysis + Memory | **90%** | **68%** | **44%** | 9% |
| Always-Reset | 80% | 69% | 40% | **30%** |
| Always-Reset + Memory | 85% | 68% | **44%** | **30%** |
| Gated Reset | 75% | 72% | **44%** | 13% |

Note: Code Append Analysis and Gated Reset had 1 timeout error each; Always-Reset had 9 timeout errors reducing its effective sample size. See Appendix for per-condition sample counts.

#### The task specification is the primary mechanism

The largest jump is from Baseline to Append Analysis: +20pp on math, +40pp on code, +28pp on database, +13pp on actions. This gain comes primarily from the task specification — a clean, consolidated restatement of user intent extracted from user messages alone. Further evidence comes from the spec-only ablation (Section 5.2), which shows the task specification alone captures most of the improvement.

#### Context removal provides additional benefit

Always-Reset outperforms Append Analysis on database (+8pp), actions (+8pp), and code (+13pp). Both strategies use identical analysis; the only difference is whether the assistant sees the full conversation history or a compacted version. The improvement demonstrates that reasoning contamination — the assistant anchoring on its prior incorrect responses — is a real and measurable problem beyond intent fragmentation.

The gap is largest on actions, the most structurally complex task (requiring multiple simultaneous function calls). This suggests context removal matters most when the assistant must coordinate multiple outputs, where prior partial/incorrect attempts create stronger anchoring.

#### Memory amplifies analysis quality

Append Analysis + Memory is the strongest overall configuration, achieving the best results on math (90%), code (68%), and database (44%). Sample-level comparison shows +8 new correct answers and zero regressions across these three tasks. Memory helps the analyzer produce more decisive task specifications and more concrete error identification.

Memory cannot overcome structural barriers: on actions, where the primary failure mode is the user simulator revealing function calls one at a time (an accumulation problem, not an analysis problem), memory provides no benefit.

#### Gated Reset underperforms Always-Reset

Gated Reset is worse than Always-Reset on math (-5pp) and actions (-17pp). The gate's false negatives are costly: when the analyzer decides no edit is needed but the assistant is actually wrong, the assistant receives no corrective signal at all. Always-Reset avoids this by always providing the clean task specification.

### 5.2 Hard Attention Ablation

The two-query architecture enforces *hard attention*: the task specification query never sees assistant messages. Is this separation necessary?

We test four configurations varying two axes: (1) whether the task specification query sees only user messages (hard attention) or the full conversation (soft attention), and (2) whether the system uses one query or two.

**Table 2: Hard attention ablation (Append Analysis, no memory)**

| Configuration | Math | Code | Database |
|---------------|:----:|:----:|:--------:|
| Hard attention, spec only (1 query) | 70% | 63% | 40% |
| Hard attention, full analysis (2 queries) | **80%** | 56% | 32% |
| Soft attention, combined (1 query) | 55% | 21% | 4% |
| Soft attention, full analysis (2 queries) | 40% | 11% | 8% |
| Baseline (no analysis) | 60% | 16% | 4% |

#### Hard attention is load-bearing

Removing hard attention collapses the system to baseline or worse. Both soft-attention variants — where the analyzer sees assistant messages when building the task specification — produce analysis that is not just unhelpful but *actively harmful*. The soft two-query variant performs below baseline on math (40% vs 60%) and code (11% vs 16%).

This result extends the anchoring phenomenon documented by Laban et al. (2025). They showed that the conversational assistant cannot un-anchor from its own prior reasoning. We show that even an *external* model tasked with analyzing the conversation is susceptible to the same contamination when it reads the assistant's messages during intent extraction.

#### Contamination amplifies through chained queries

The soft two-query variant (40% math, 11% code) underperforms the soft single-query variant (55% math, 21% code). When Query 1 produces a contaminated task specification and passes it to Query 2 as authoritative ground truth, the contamination compounds. Each pipeline stage inherits and amplifies errors from the prior stage. This contamination amplification is a failure mode specific to chained LLM calls and suggests caution when designing multi-stage inference pipelines.

#### The task specification alone is surprisingly effective

The hard-attention spec-only variant (one query, no comparison) matches or exceeds the full two-query system on code (63% vs 56%) and database (40% vs 32%) at half the LLM cost. The comparison query adds value on math (+10pp) but introduces noise on structured-output tasks. This suggests a task-adaptive approach: spec-only for tasks with well-defined output formats, full analysis for tasks requiring nuanced error identification.

### 5.3 Can Context Editing Rescue Contaminated Analysis?

If the analysis is contaminated (soft attention), can we still extract value by removing the bad conversation context? We test Always-Reset and an LLM-based compaction variant on top of the soft-attention analysis from Section 5.2.

**Table 3: Context editing with contaminated analysis**

| Strategy | Math | Code | Database |
|----------|:----:|:----:|:--------:|
| Baseline | 60% | 16% | 4% |
| Soft analysis, appended | 55% | 21% | 4% |
| Soft analysis, always-reset | 55% | 26% | 4% |
| Soft analysis, LLM compaction | 55% | 22% | 12% |
| Hard analysis, appended | **80%** | **56%** | **32%** |
| Hard analysis, always-reset | **80%** | **69%** | **40%** |

Context editing cannot rescue contaminated analysis. The bottleneck is analysis quality, not delivery mechanism. Context editing is a *force multiplier* on analysis quality: with clean analysis it provides +8–13pp over appending; with contaminated analysis it provides nothing. This confirms that hard attention is the foundational architectural requirement, not an optional optimization.

### 5.4 CollabLLM Setting

[TODO: Results showing context editing effectiveness in the collaborative LLM setting, where the user iteratively refines requirements. Early results show positive improvement on math and code.]

---

## 6. Discussion

### 6.1 Two Problems, Two Solutions

Our results reveal that multi-turn performance degradation operates through two distinct mechanisms that are separable in our framework.

**User intent fragmentation** is the dominant factor on the LiC benchmark. The task specification alone — a clean extraction of user intent from user messages — recovers most of the single-turn performance. This is because LiC tasks are single-answer problems where rederivation is trivial: once the model knows what to compute, it can produce the answer without reference to its prior attempts.

**Reasoning contamination** is secondary but present. Always-Reset consistently outperforms Append Analysis on database (+8pp) and actions (+8pp), demonstrating that the assistant's prior incorrect reasoning does anchor its final response even when corrective analysis is available. The gap is largest on actions, the most complex task requiring coordination of multiple outputs — the closest LiC comes to stateful, multi-artifact work.

This decomposition has implications for benchmark design. LiC was constructed around simple, single-answer tasks to isolate the anchoring phenomenon. Our results suggest that more complex benchmarks — requiring multi-step reasoning, iterative artifact construction, or coordination across outputs — would show a larger role for context editing relative to task specification, because rederivation becomes expensive or impossible.

### 6.2 Hard Attention as an Architectural Principle

The hard attention finding is our most practically consequential result. It implies that multi-stage LLM pipelines must carefully control information flow between stages: allowing a downstream model to see content it is supposed to evaluate objectively will contaminate its judgment.

This has implications beyond our setting. Any system that uses an LLM to evaluate, critique, or improve another LLM's output faces the same risk: the evaluator model will be influenced by the content it evaluates, even when instructed to be critical. Architectural separation — physically controlling what each stage sees — is more reliable than prompting the model to "ignore" certain content.

The limitation of our hard attention approach is that it exploits a property specific to LiC: user messages alone fully specify the task. In realistic multi-turn settings (iterative design, multi-step reasoning, tool-use agents), the task specification may depend on prior assistant work. Extending hard attention to these settings — perhaps through hybrid approaches that separate user-specified constraints from assistant-generated state — is an important direction.

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

1. **Task specification reconstruction is the primary mechanism** for LiC-style benchmarks where rederivation is cheap. A clean, hard-attention extraction of user intent from user messages alone recovers most of the single-turn performance.

2. **Hard attention is the load-bearing architectural principle.** Without physically separating user intent extraction from the assistant's prior reasoning, even an external analyzer is contaminated by the same anchoring it tries to correct. This is a general caution for multi-stage LLM pipelines.

3. **Context removal provides measurable additional benefit,** particularly on complex multi-output tasks. This motivates context editing for settings where tasks are stateful and rederivation is expensive.

4. **Memory-based learning amplifies analysis quality** when applied to the append-analysis strategy, but the benefit is sensitive to how the analysis is consumed downstream.

These results suggest a progression: for simple tasks, a clean task specification suffices; for moderately complex tasks, context removal adds value; for truly stateful long-horizon tasks, surgical context editing — preserving correct work while removing harmful content — should be essential. Future work on harder, more realistic benchmarks will test this progression.

---

## References

[Same as v3, plus any new references.]

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
