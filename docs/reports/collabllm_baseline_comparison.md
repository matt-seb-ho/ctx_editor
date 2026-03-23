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

### Code evaluation
BigCodeBench pass_rate (test execution) is 0% for all methods due to `task_func` naming mismatch (see initial experiments report). We use a **conversation-aware LLM judge** (gpt-5) that evaluates whether the extracted code fulfills what the user actually asked for, scoring 1.0 (full), 0.5 (partial), or 0.0 (fail).

## Results

| Method | Math-Hard | BigCodeBench | Math Turns | Code Turns |
|--------|-----------|-------------|------------|------------|
| **Baseline** | 40.0% (8/20) | 62.5% (n=20) | 9.1 | 5.5 |
| **Compaction (ours)** | **45.0%** (9/20) | **82.5%** (n=20) | 10.4 | 6.8 |
| **AO (Huang)** | 50.0% (10/20) | 82.5% (n=20) | 10.0 | 5.3 |
| **ERGO** | 50.0% (10/20) | 77.5% (n=20) | 8.9 | 5.2 |

### Output directories
- Baseline Math: `outputs/2026-03-17/04-16-54/`
- Baseline Code: `outputs/2026-03-20/10-22-05/`
- Compaction Math: `outputs/2026-03-18/20-49-55/`
- Compaction Code: `outputs/2026-03-20/10-22-06/`
- AO Math: `outputs/2026-03-23/ao_math/`
- AO Code: `outputs/2026-03-23/ao_code/`
- ERGO Math: `outputs/2026-03-23/ergo_math/`
- ERGO Code: `outputs/2026-03-23/ergo_code/`
- Code re-evals: `reeval_gpt-5_conversation_judge/` subdirs

## Discussion

### Math-Hard: Reset baselines match or beat compaction

On math, both ERGO (50%) and AO (50%) outperform compaction (45%) and baseline (40%). This is consistent with prior findings on LiC: for math problems, discarding assistant work is low-cost because the user messages contain all the necessary information. The assistant's failed reasoning attempts are more harmful than helpful, and a clean restart lets the model try fresh.

The 5pp gap between compaction and the reset baselines suggests that compaction's preserved "correct work" is sometimes contaminated or misleading for math, where correctness is all-or-nothing.

### BigCodeBench: Compaction matches AO, beats ERGO

On code (conversation-aware judge), the picture is different:
- **Compaction (82.5%) = AO (82.5%)**: Both preserve user intent equally well
- **ERGO (77.5%)**: Slightly lower -- the rewrite step may be losing nuance from the user's incremental requirements
- **Baseline (62.5%)**: Significantly worse -- accumulated bad code in context hurts

The code results show that context interventions help across the board (+15-20pp over baseline), but the specific mechanism matters less than simply removing bad content. Compaction and AO achieve the same accuracy despite very different approaches: compaction preserves good work, AO discards everything.

### Why AO performs well on CollabLLM

Contrary to our hypothesis, AO performs as well as compaction even on the collaborative coding task. This may be because:

1. **Short conversations**: With gpt-4o user sim, code conversations average only 5-7 turns. There's limited assistant work product to preserve.
2. **Option 2 rendering**: Our framework packs all messages into a single user prompt for the assistant. Removing assistant messages from this format still leaves a coherent (if sparse) conversation for the model to work with.
3. **gpt-5-mini capability**: A strong enough assistant may not need prior work preserved in context; it can regenerate solutions from user messages alone.

### Limitations

- **n=20 per task**: All differences are within noise at this sample size. Math: 40-50% range (2 correct answers between methods). Code: 77.5-82.5% (1 sample difference).
- **Math uses gpt-4o-mini user sim, code uses gpt-4o**: Not directly comparable across tasks.
- **No complexity stratification**: CollabLLM's 14-turn conversations may not be complex/stateful enough to show compaction's advantage over simpler baselines. Longer, more complex tasks (e.g., multi-file coding, iterative document editing) would better test our hypothesis.
- **ERGO had 1 error on code** (content filter): 19/20 evaluated vs 20/20 for others.

### Implementation notes

**ERGO content filter issue**: The original ERGO-style "prompt rewriter" framing triggered Azure's jailbreak detection filter, causing 75% of samples to fail. We rephrased the prompt as a "helpful assistant that consolidates information" which resolved the issue (commit `786d103`).

**AO on Option 2**: In our framework, the assistant sees conversation via Option 2 rendering (`[user]\n...\n\n[assistant]\n...`). With AO, the rendered conversation only has `[user]` blocks. This is a valid representation but differs from standard message-list AO where assistant messages simply aren't in the `messages` array.

## Files Created

- `src/ctx_editor/strategies/ergo_restart.py` -- ERGORestartStrategy
- `src/ctx_editor/strategies/assistant_omit.py` -- AssistantOmitStrategy
- `src/ctx_editor/strategies/prompts/ergo_rewrite.txt` -- ERGO consolidation prompt
- `src/ctx_editor/config/experiment/collabllm_ergo.yaml`
- `src/ctx_editor/config/experiment/collabllm_assistant_omit.yaml`
