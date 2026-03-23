# CollabLLM Baseline Comparison: ERGO & Huang et al. vs Context Compaction

**Date**: 2026-03-23
**Branch**: `collabllm_eval` (commits through `786d103`)

## Motivation

Prior work on context editing for multi-turn LLM conversations (ERGO, Huang et al.) has shown strong results on the LiC benchmark by essentially discarding all assistant messages and restarting from concatenated user messages. This works well on LiC because the user messages alone contain all the information needed to reconstruct a correct single-turn prompt.

We hypothesize that in *collaborative* multi-turn settings (like CollabLLM), where the assistant builds up useful work product across turns, discarding all assistant progress is more costly. Our context compaction strategy (S3) preserves correct work while removing harmful content, which should be advantageous when assistant contributions have value.

## Methods

### Baseline (no editing)
Full conversation passed through unmodified. The assistant sees all prior user + assistant messages.

### Context Compaction (ours, S3)
After user turn 4, every turn:
1. Single-query analysis identifies task spec, good work, and bad work
2. Context compaction produces clean task spec + preserved correct work
3. Trace resets with compacted context

Preserves correct assistant work; removes harmful/wrong content.

### ERGO Restart (Khalid et al., adapted)
After user turn 4, every turn:
1. Collects all user messages (across resets)
2. LLM rewrites them into a single consolidated prompt
3. Trace resets with **only** system message + rewritten prompt

Discards ALL assistant work. Uses same LLM (gpt-5-mini low) for rewriting.

Note: Original ERGO uses entropy-based triggering; we use the same turn-count threshold as compaction for fair comparison. The rewrite prompt is adapted from ERGO's few-shot task-specific templates into a single general-purpose consolidation prompt.

### Assistant-Omit (Huang et al., AO)
On every turn (from the start), strips all assistant messages from context. The assistant only sees system + user messages, never its own prior outputs.

No LLM calls, no threshold. This is the simplest baseline.

## Setup

| Parameter | Value |
|-----------|-------|
| Assistant | gpt-5-mini, reasoning_effort=low |
| User sim (math) | gpt-4o-mini |
| User sim (code) | gpt-4o |
| Eval model (math) | gpt-4o-mini (LLM-as-judge) |
| Eval model (code) | gpt-5 (conversation-aware judge) |
| Context editor | gpt-5-mini, reasoning_effort=low |
| max_turns | 14 |
| Samples | 20 per task (seed=42) |
| Load balancer | multi_endpoint_full (4 Azure endpoints) |

### Datasets
- **MATH-Hard**: 20 from lighteval/MATH-Hard test split
- **BigCodeBench**: 20 from bigcode/bigcodebench v0.1.2
- **MediumDocEdit**: 20 from Kamaljp/medium_articles (<=512 token articles)

### Evaluation
- **Math**: LLM-as-judge (gpt-4o-mini) comparing extracted answer vs ground truth
- **Code**: gpt-5 conversation-aware judge (scores against user's actual requests, not test cases)
- **Doc edit**: gpt-5 conversation-aware document judge (scores against user's editing requests)

BigCodeBench pass_rate (test execution) is 0% for all methods due to `task_func` naming mismatch (see initial experiments report).

## Results

### Single replicate (run 1)

| Method | Math-Hard | BigCodeBench | MediumDocEdit | Math Turns | Code Turns | Doc Turns |
|--------|-----------|-------------|---------------|------------|------------|-----------|
| **Baseline** | 40.0% | 62.5% | 95.0% | 9.1 | 5.5 | 5.0 |
| **Compaction (ours)** | 45.0% | **82.5%** | 97.5% | 10.4 | 6.8 | 4.5 |
| **AO (Huang)** | 50.0% | 82.5% | 97.5% | 10.0 | 5.3 | 4.7 |
| **ERGO** | 50.0% | 77.5% | 97.5% | 8.9 | 5.2 | 5.1 |

### Averaged across 2 replicates (math and code only)

| Method | Math-Hard (avg) | BigCodeBench (avg) |
|--------|-----------------|--------------------|
| **Baseline** | 50.0% | 67.5% |
| **Compaction (ours)** | 45.0% | 71.2% |
| **AO (Huang)** | 50.0% | **85.0%** |
| **ERGO** | 50.0% | 75.0% |

Run 2 individual results: Baseline math 60%, Compaction math 45%, AO math 50%, ERGO math 50%. Baseline code 72.5%, Compaction code 60%, AO code 87.5%, ERGO code 72.5%.

### Interactivity scores (run 1)

| Method | Math | Code | Doc |
|--------|------|------|-----|
| Baseline | 0.965 | 1.000 | 0.955 |
| Compaction | 0.885 | 0.935 | 0.950 |
| AO (Huang) | **1.000** | **1.000** | **1.000** |
| ERGO | 0.875 | 0.974 | 0.950 |

AO consistently achieves perfect or near-perfect interactivity. This is because the assistant never sees its own prior responses, so it naturally asks more clarifying questions on every turn.

### Output directories
- Run 1: `outputs/2026-03-17/04-16-54/` (baseline math), `outputs/2026-03-20/10-22-05/` (baseline code), etc.
- Run 2: `outputs/2026-03-23/r2_*/`
- Doc edit: `outputs/2026-03-23/*_doc/`
- Code re-evals: `reeval_gpt-5_conversation_judge/` subdirs
## Discussion

### Math-Hard: All methods cluster at ~50%, high variance

Averaged across 2 replicates, all methods land at 45-50% on math. The baseline itself swung from 40% to 60% between replicates, showing the variance floor at n=20. There is no statistically meaningful difference between methods on math.

This is consistent with prior findings on LiC: for math problems, discarding assistant work is low-cost because the user messages contain all the necessary information.

### BigCodeBench: Context interventions help, AO leads

On code (averaged across 2 replicates, gpt-5 conversation judge):
- **AO (85.0%)** leads -- stripping assistant messages consistently helps
- **ERGO (75.0%)** and **Compaction (71.2%)** are similar
- **Baseline (67.5%)** worst -- accumulated bad code in context hurts

All interventions beat baseline by 4-18pp, but there's high variance (compaction scored 82.5% in run 1, 60% in run 2).

### MediumDocEdit: At ceiling for gpt-5-mini

All methods score 95-97.5% on doc edit with the gpt-5 judge. The task is at ceiling: Medium articles are short (<=512 tokens), conversations are brief (4-5 turns), and gpt-5-mini handles document editing easily regardless of context strategy.

This is consistent with CollabLLM paper's observation that their base model (Llama-3-8B) scores much lower on doc edit -- a weaker model would show more differentiation. With gpt-5-mini, the task is simply too easy.

### Interactivity: AO achieves perfect scores

AO consistently scores 1.0 on interactivity across all tasks. This is because without seeing its own prior responses, the assistant naturally asks more clarifying questions on every turn (it doesn't know what it has already addressed). This artificially inflates interactivity for AO.

Our interactivity scores (0.87-1.0) are much higher than CollabLLM paper's reported range (20-50% for code, 40-60% for math) because gpt-5-mini is inherently more interactive than Llama-3-8B.

### Why we don't see compaction's advantage

Several factors work against demonstrating compaction's value in this setting:

1. **Short conversations**: 4-10 turns average. Limited assistant work product accumulates, so there's little to preserve vs discard.
2. **Strong assistant model**: gpt-5-mini (even at low reasoning) can regenerate solutions from scratch easily, reducing the value of preserved context.
3. **Small sample size**: n=20 with high variance makes methods statistically indistinguishable.
4. **Tasks at ceiling**: Doc edit is trivially easy for this model. Math is inherently lossy (all-or-nothing). Code is the most promising but still shows high replicate variance.
5. **CollabLLM's conversation protocol**: The user simulator terminates quickly with strong models, limiting conversation depth.

For compaction to show clear advantages, we likely need: (a) longer conversations with accumulated assistant work product, (b) a weaker assistant model where regeneration from scratch is costly, or (c) more complex stateful tasks where context continuity matters (e.g., multi-file coding, long document editing with many revision cycles).

### Implementation notes

**ERGO content filter**: The original "prompt rewriter" framing triggered Azure's jailbreak filter (75% failure rate). Rephrased as "helpful assistant that consolidates information" (commit `786d103`).

**AO on Option 2**: With our Option 2 rendering, AO conversations have only `[user]` blocks in the rendered prompt. The assistant never sees prior responses but still receives the full user message history.

**Replicate variance**: Baseline math swung from 40% to 60% between runs. Compaction code swung from 82.5% to 60%. At n=20, these are 1-4 sample differences that flip the ranking.

## Files Created

- `src/ctx_editor/strategies/ergo_restart.py` -- ERGORestartStrategy
- `src/ctx_editor/strategies/assistant_omit.py` -- AssistantOmitStrategy
- `src/ctx_editor/strategies/prompts/ergo_rewrite.txt` -- ERGO consolidation prompt
- `src/ctx_editor/prompts/collabllm/document_judge.txt` -- Document quality judge prompt
- `src/ctx_editor/config/experiment/collabllm_ergo.yaml`
- `src/ctx_editor/config/experiment/collabllm_assistant_omit.yaml`
- `src/ctx_editor/data/collabllm_loader.py` -- Added Medium doc edit dataset loader
