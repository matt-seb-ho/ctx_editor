# Paper Framing — Context Editing for Multi-Turn LLM Conversations

## Core Thesis

Multi-turn conversations degrade LLM performance through two distinct mechanisms:

1. **User intent fragmentation** — the user's actual request is scattered across turns, paraphrased, revised, and buried in conversational noise. The model must reconstruct what the user *really* wants from incomplete, non-linear input.

2. **Reasoning contamination** — the assistant's prior (often incorrect) reasoning remains in context and anchors future responses. The model cannot un-see its own mistakes.

We show that these two problems require different solutions, that both solutions depend on a shared architectural principle (hard attention), and that LiC's evaluation framework primarily tests problem 1 while providing evidence that problem 2 matters and warrants further investigation on more complex benchmarks.

## The Two-Query Architecture

Our analyzer uses a two-query design:

- **Query 1 (task spec)**: Sees *only* the system message and user messages. Produces a consolidated task specification — a clean restatement of what the user is asking for.
- **Query 2 (comparison)**: Sees the task spec from Query 1 *plus* the full conversation. Produces an assessment of what the assistant got right (aligned) and wrong (issues).

Query 1 addresses user intent fragmentation. Query 2 addresses reasoning contamination by identifying specifically what's correct and what's harmful in the assistant's prior work.

The critical architectural choice is **hard attention**: Query 1 never sees assistant messages. This prevents the analyzer from being contaminated by the same bad reasoning it's trying to correct.

## Strategies

Three strategies use the analyzer's output differently:

- **S1 (append analysis)**: Appends the analysis (spec + aligned + issues) to the conversation. The assistant sees everything — the bad context *and* the corrective analysis. This addresses problem 1 (task spec clarifies intent) and partially addresses problem 2 (issues highlight what's wrong, but bad context is still visible).

- **S1.5 (always reset)**: Replaces the conversation with compacted context built from the analysis (spec + aligned). Removes all prior assistant reasoning. Addresses both problems — clean spec for intent, and context removal for contamination.

- **S2 (gated reset)**: Like S1.5 but only resets when the analyzer detects issues. When it decides not to reset, the assistant gets no analysis at all. This proved worse than S1.5 due to false negatives in the gate.

## Main Results (V8, Replay-Last-Turn)

Baseline is S0 (no intervention). All results use user-sim-induced sample filtering.

| Strategy | Math (n=20) | Code (n=19) | Database (n=25) | Actions (n=23) |
|----------|:-----------:|:-----------:|:---------------:|:--------------:|
| **S0** (baseline) | 60% | 16% | 4% | 9% |
| **S1** (append) | 80% | 56% | 32% | 22% |
| **S1+mem** | **90%** | **68%** | **44%** | 9% |
| **S1.5** (always reset) | 80% | 69%† | 40% | **30%** |
| **S1.5+mem** | 85% | 68% | **44%** | **30%** |
| **S2** (gated reset) | 75% | 72% | **44%** | 13% |

†Code S1.5 had timeout errors reducing denominator.

### Key observations

**S1 captures most gains via task spec (problem 1).** The jump from S0 to S1 is large across all tasks: +20pp math, +40pp code, +28pp database, +13pp actions. This is primarily the task spec at work — giving the assistant a clean restatement of user intent.

**S1.5 > S1 on database and actions, showing context removal helps (problem 2).** Database: 40% vs 32% (+8pp). Actions: 30% vs 22% (+8pp). On these tasks, the assistant's prior bad reasoning (wrong SQL structure, incomplete function calls) anchors the final response even when corrective analysis is appended. Removing it helps.

**The gap is largest on multi-artifact tasks.** Actions requires producing multiple simultaneous function calls — the most "stateful" task in LiC. It's the only task where S1.5 substantially outperforms S1+mem, suggesting that context removal matters most when the assistant must coordinate across multiple outputs.

**Memory closes the S1 → S1.5 gap on single-output tasks.** S1+mem matches S1.5 on math (90% vs 80%) and database (44% vs 40%), surpassing the context-removal approach through better analysis quality alone. But memory cannot overcome the structural accumulation problem on actions (S1+mem: 9% vs S1.5: 30%).

## Hard Attention Ablation

The critical architectural question: does the hard attention separation (hiding assistant messages from Query 1) actually matter?

| Variant | Query 1 sees | Math | Code | Database |
|---------|:------------:|:----:|:----:|:--------:|
| **S1** (hard, 2q) | user only | **80%** | 56% | 32% |
| **S1-speconly** (hard, 1q) | user only | 70% | **63%** | **40%** |
| **S1-single** (soft, 1q) | full conv | 55% | 21% | 4% |
| **S1-soft** (soft, 2q) | full conv | 40% | 11% | 8% |
| **S0** (baseline) | — | 60% | 16% | 4% |

### Findings

**Hard attention is load-bearing.** Removing it (soft variants) collapses performance to baseline or worse. The analyzer, when exposed to assistant messages during task spec construction, produces contaminated analysis that reflects the assistant's errors rather than correcting them. This is the same anchoring phenomenon LiC documents in the assistant, now demonstrated in an *external analyzer model*.

**Contamination is not just useless — it's actively harmful.** Both soft variants frequently perform *below* baseline. The contaminated analysis reinforces incorrect reasoning with a false sense of external validation. S1-soft math (40%) is 20pp below the unmodified baseline (60%).

**Two-query chaining amplifies contamination.** S1-soft (two queries, soft) underperforms S1-single (one query, soft) on math (40% vs 55%) and code (11% vs 21%). When Query 1 produces a contaminated task spec and passes it to Query 2 as authoritative ground truth, the contamination compounds. Each pipeline stage inherits and amplifies errors from the prior stage — a failure mode specific to LLM cascades.

**The task spec alone is surprisingly effective.** S1-speconly (hard attention, spec only, no comparison query) matches or exceeds full S1 on code (+7pp) and database (+8pp) at half the LLM cost. The comparison query helps on math (+10pp) but hurts on structured-output tasks. This suggests a task-adaptive approach may be optimal.

## Soft Attention + Context Editing Ablation

If soft-attention analysis is contaminated, can context editing rescue it? If removing bad context helps (as S1.5 > S1 showed), maybe removing bad context *and* replacing it with even imperfect analysis would help?

| Setting | Math | Code | Database |
|---------|:----:|:----:|:--------:|
| **S0** (baseline) | 60% | 16% | 4% |
| S1-single (soft, append) | 55% | 21% | 4% |
| S1.5-single (soft, reset) | 55% | 26% | 4% |
| S1-soft (soft 2q, append) | 40% | 11% | 8% |
| S1.5-soft (soft 2q, reset) | 44% | 12% | 8% |
| **S1** (hard, append) | **80%** | **56%** | **32%** |
| **S1.5** (hard, reset) | **80%** | **69%** | **40%** |

**Context editing cannot rescue contaminated analysis.** Neither resetting nor LLM-rewriting improves soft-attention results meaningfully. The bottleneck is analysis quality, not delivery mechanism. Context editing is a force multiplier on analysis quality — with clean analysis it provides substantial lift; with contaminated analysis there is nothing to multiply.

## Narrative Arc

### What LiC tests

LiC was designed to isolate multi-turn performance degradation on simple, single-answer tasks. The sharded disclosure format creates user intent fragmentation (the problem is revealed piece by piece) and reasoning contamination (the assistant commits to interpretations early and anchors on them).

Because the tasks are simple (one math answer, one function, one SQL query), the correct response is fully determined by the user's messages alone. This makes "hard reset + clean spec" a viable and powerful strategy — you don't need to preserve any prior assistant work because rederivation is trivial.

### What our results show

1. **Task spec reconstruction (solving intent fragmentation) is the primary mechanism in LiC.** S1's task spec alone recovers most of the single-turn performance. S1-speconly (hard attention, spec only) matches or beats full S1 on code and database at half the cost.

2. **Hard attention is the architectural principle that makes it work.** The same analysis produced with soft attention (analyzer sees assistant messages) is worthless or harmful. This extends LiC's finding — anchoring affects not just the conversational assistant but any model processing the conversation, including an external analyzer.

3. **Context removal provides incremental but real benefit (S1.5 > S1).** This is secondary to the task spec but present, especially on structured/multi-artifact tasks. It demonstrates that reasoning contamination is a real problem even when a clean spec is available.

4. **The S1.5 > S1 gap is largest on the most complex task (actions).** Actions requires coordinating multiple function calls — the closest LiC gets to stateful, multi-artifact work. This is where context removal matters most, and where neither memory nor better analysis can substitute for actually removing the contaminating context.

5. **Memory learning amplifies analysis quality and closes the S1→S1.5 gap on simple tasks,** but cannot overcome structural barriers (actions accumulation). This suggests that for simple tasks, better analysis is sufficient; for complex tasks, architectural solutions (context editing) are necessary.

### What this implies for harder settings

LiC's simple tasks are the *easy case* for context editing — the regime where a clean spec alone nearly solves the problem. In more realistic settings:

- **Long-horizon coding**: The assistant has built correct infrastructure across many turns. You can't reset to a spec — you'd lose the working code. Surgical editing (keep correct work, remove bad reasoning) is essential.
- **Multi-artifact tasks**: Multiple outputs must be coordinated. The spec can describe what's needed, but the comparison (aligned/issues) identifies which outputs are correct and which need revision.
- **Stateful agent interactions**: Tool call results, environment state, and accumulated findings can't be re-derived from user messages. Editing must preserve useful state while removing dead ends.

In these regimes, the full context editing machinery — not just the task spec but the aligned/issues comparison and surgical context reset — should show its value over the simpler "spec + reset" approach.

### The hard attention limitation

Hard attention (hiding assistant messages from the analyzer) works in LiC because user messages alone fully specify the task. In realistic settings where the task spec depends on prior assistant work (iterative refinement, multi-step reasoning, tool use results), pure hard attention isn't applicable. Future work should explore:

- Hybrid attention: hard attention for task spec, soft attention for aligned/issues
- More capable analyzer models that resist anchoring
- Structured separation within a single query (chain-of-thought that explicitly separates "user said" from "assistant did")
- Training-based approaches that teach the analyzer to decontaminate

## Paper Structure Sketch

1. **Introduction**: Multi-turn LLM conversations degrade performance. LiC quantified this. We address it.

2. **Background**: LiC framework, the anchoring problem, prior approaches (ERGO's full reset vs our surgical approach).

3. **Method**: Two-query architecture with hard attention. Three strategies (S1 append, S1.5 always-reset, S2 gated-reset). Memory learning for cross-problem knowledge transfer.

4. **Results**:
   - V8 main results across 4 tasks showing S1/S1.5 effectiveness
   - Memory providing consistent uplift for S1
   - S1.5 > S1 as evidence that context removal matters beyond spec

5. **Analysis — Hard Attention**:
   - The 2×2 ablation (hard/soft × 1q/2q) showing hard attention is load-bearing
   - Soft attention context editing ablation showing contaminated analysis can't be rescued
   - Contamination amplification in chained LLM calls

6. **Discussion**:
   - Task spec reconstruction vs context editing as solving two distinct problems
   - LiC primarily tests intent fragmentation; context editing shows incremental benefit
   - Harder benchmarks needed to fully demonstrate context editing's value
   - Hard attention as an architectural principle with limitations in realistic settings

7. **Conclusion**: Hard-attention task spec reconstruction is a simple, effective intervention for multi-turn degradation. Context editing provides additional gains, especially for complex/multi-artifact tasks, and should be essential in harder settings where rederivation is expensive.
