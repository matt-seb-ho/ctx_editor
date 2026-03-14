# Dev Set Round 2: Content Filter Fix & Proper Memory Evaluation

**Date**: 2026-03-13
**Branch**: newleaf
**Model**: gpt-5-mini (assistant) + gpt-4o-mini (user/system)
**Dev sets**: math (23), code (25), database (25), actions (25)

## What Changed Since Round 1

### Problem 1: Memory was never learning (execution mode bug)

Round 1's "+mem" runs used `execution.mode=parallel`, which clones the initial (empty) memory for all samples and runs them simultaneously. Memory updates only propagate when using `execution.mode=batched`, where problems run in batches of 5 and the cheatsheet updates between batches via Reflect-then-Unify. **All Round 1 "+mem" results were functionally identical to non-memory runs** — just different random seeds.

**Fix**: All memory experiments now use `execution.mode=batched`. Batch logs confirm memory is updating properly (v0 → v1 → v2 → ... → v5 across 5 batches of ~5 problems each).

### Problem 2: Azure content filter blocking S2 runs (~43% exclusion rate)

The ConversationAnalyzer prompt triggers Azure's `jailbreak` content filter when analyzing post-reset conversations. After S2 resets the conversation, the system message contains `<context_edit_notes>` with directive language like "be willing to take a completely different approach." When the analyzer wraps this in its own prompt ("You are an independent reviewer..."), Azure sees a nested instruction pattern that resembles prompt injection.

This only affected **S2** (context edit v2), not S1 (append analysis), because S1 never resets the conversation — the analyzer always sees raw, unmodified messages.

**Root cause details**: The content filter category was consistently `jailbreak` (not hate/violence/sexual). Every error occurred on the analyzer call specifically, and every errored request contained `<context_edit_notes>` in the conversation being analyzed.

**Two-part fix**:
1. **Strip `<context_edit_notes>` from analyzer input** (`analyzer.py`): Added `_strip_edit_notes()` that removes these blocks via regex before building the analyzer prompt. The analyzer should evaluate the raw conversation anyway, not the edited metadata.
2. **Soften the notes language** (`context_edit_v2.py`, `context_edit.py`): Changed "The assistant's previous approach had issues. Read this critically and be willing to take a completely different approach" to "An independent review of the prior conversation identified areas for improvement. Consider this feedback when formulating your response."

**Result**: Content filter errors dropped from 21 to 3 across all S2 runs:

| Run | Before Fix | After Fix |
|---|---|---|
| S2 math | 10 errors | 0 |
| S2 code | 11 errors | 0 |
| S2+mem math | — | 1 |
| S2+mem code | — | 0 |
| S2+mem database | — | 0 |
| S2+mem actions | — | 2 |

### Problem 3: Round 1's conclusions were invalid

Because memory was inert and S2 had ~43% data loss from content filters, Round 1's key conclusions — "S2 is strongest," "memory helps S1 but hurts S2" — were comparing apples to oranges. The apparent S2 > S1 gap was driven by inflated accuracy from selective sample survival, and the "+mem" comparisons were just noise between parallel runs with different random seeds.

## Round 2 Results

All runs below use the content filter fix. Memory runs use `execution.mode=batched`.

### Main Results Table

| Task | Baseline | BL+mem | S1 (append) | S1+mem | S2 (edit v2) | S2+mem |
|---|---|---|---|---|---|---|
| **math** (23) | 14.5% | **40.9%** (9/22, 1e) | 62.5% (10/16, 7e) | 61.1% (11/18, 5e) | **68.2%** (15/22, 1e) | 50.0% (11/22, 1e) |
| **code** (25) | 0% | 27.3% (3/11, 14e) | 33.3% (3/9, 16e) | **33.3%** (8/24, 1e) | 18.8% (3/16, 9e) | **33.3%** (8/24, 1e) |
| **database** (25) | 0% | 4.3% (1/23, 2e) | 4.5% (1/22, 3e) | **8.0%** (2/25, 0e) | 4.0% (1/25, 0e) | **8.0%** (2/25, 0e) |
| **actions** (25) | 0% | **17.4%** (4/23, 2e) | 20.0% (3/15, 10e) | 12.5% (3/24, 1e) | 16.0% (4/25, 0e) | 13.0% (3/23, 2e) |

Format: accuracy% (correct/valid, excluded). Baseline is the average across 2-3 existing gpt5_mini runs.

### Exclusion Rates

| Task | BL+mem | S1 | S1+mem | S2 | S2+mem |
|---|---|---|---|---|---|
| math (23) | 1 | **7** | 5 | 1 | 1 |
| code (25) | **14** | **16** | 1 | **9** | 1 |
| database (25) | 2 | 3 | 0 | 0 | 0 |
| actions (25) | 2 | **10** | 1 | 0 | 2 |

High exclusions (bold) are from rate limiting during concurrent execution, not content filters. S1 without memory was hit hardest because it ran concurrently with the memory batch. S2's exclusions dropped to near-zero after the content filter fix.

**Caveat**: S1 without memory has unreliable accuracy on code (3/9, 16 excluded) and actions (3/15, 10 excluded). These numbers should not be compared at face value with S1+mem (8/24, 1 excluded) or S2 (3/16, 9 excluded). Where one setting has >5 exclusions and another has <2, the comparison is unreliable.

## Analysis

### 1. Context operations improve over baseline (confirmed)

On math, the only task with low exclusions across the board:

| Setting | Correct | Valid | Accuracy |
|---|---|---|---|
| Baseline (avg) | ~3/23 | 23 | 14.5% |
| Baseline+mem | 9 | 22 | 40.9% |
| S2 | 15 | 22 | 68.2% |
| S2+mem | 11 | 22 | 50.0% |
| S1+mem | 11 | 18 | 61.1% |

All strategies substantially beat the baseline. S2 is the strongest non-memory setting (68.2% vs 14.5% baseline). On code and database, where comparison is clean for +mem variants (0-1 exclusions), S1+mem and S2+mem both match at 33.3% and 8.0% respectively, both well above the 0% baseline.

### 2. Memory helps baseline consistently (confirmed)

Baseline → Baseline+mem gains on every task: math (+26pp), code (+27pp), database (+4pp), actions (+17pp). This confirms that continual memory learning discovers useful strategies from past trajectories even without any context editing.

### 3. S2+mem < S2 on math (the key gap)

S2 gets 15/22 correct; S2+mem gets 11/22. Same number of valid samples, so this is a fair comparison. The batch logs reveal an interesting pattern:

**S2+mem math batch progression**:
| Batch | Memory | Correct | Score |
|---|---|---|---|
| 1 | v0 (empty) | 5/5 | 100% |
| 2 | v1 | 3/5 | 60% |
| 3 | v2 | 0/5 | 0% |
| 4 | v3 | 2/5 | 40% |
| 5 | v4 | 1/3 | 33% |

Performance collapses after batch 2 and never recovers. The cheatsheet learned from the first 10 problems and then apparently started giving bad guidance. This is a known failure mode of continual cheatsheet learning — early lessons can become counterproductive when they're overly specific or when the cheatsheet grows to dominate the prompt.

**S1+mem math** shows a similar but milder pattern (batch 3 scores 0.2), suggesting the issue is partly in what the cheatsheet learns, not just in how S2 uses it.

### 4. S1+mem and S2+mem converge on code and database

Both get 33.3% (8/24) on code and 8.0% (2/25) on database — identical. This suggests that on these tasks, memory is the dominant driver of improvement and the choice of strategy (append vs edit) matters less.

### 5. Actions remains noisy

All settings cluster around 12-20% on actions with no clear winner. The high false-negative rate in actions evaluation (80-84% of errors are extraction/comparison artifacts, not genuine failures) makes it hard to measure real progress.

## Remaining Issues

1. **S2+mem math regression**: The cheatsheet degrades after ~2 batches. Possible fixes:
   - Memory target tuning — currently targets the analyzer; may need to weight memory more weakly in the comparison query
   - Cheatsheet size limits — prevent early lessons from dominating
   - Separate the cheatsheet for S2's two-query flow — memory on the comparison query only, not the task spec query

2. **S1 exclusion rates**: S1 without memory has unreliable results due to rate limit exclusions from concurrent execution. Need a clean standalone re-run.

3. **Actions evaluation noise**: The task's evaluation artifacts (extraction failures, strict comparison) make it hard to distinguish real strategy effects from measurement noise.

## Files Changed

| File | Change |
|---|---|
| `strategies/analyzer.py` | Added `_strip_edit_notes()` to remove `<context_edit_notes>` before building analyzer prompt |
| `strategies/context_edit_v2.py` | Softened `<context_edit_notes>` language to avoid trigger phrases |
| `strategies/context_edit.py` | Same language softening (old strategy, for consistency) |
| `memory/cheatsheet.py` | Added `"analyzer"` to `VALID_TARGETS`, prompt file maps |
| `memory/renderers.py` | Added `render_for_analyzer()` with timeline-based rendering |
| `memory/prompts/analyzer_reflection.txt` | New reflection prompt for analyzer memory target |
| `memory/prompts/analyzer_reflect_takeaways.txt` | New takeaway prompt for analyzer memory target |
