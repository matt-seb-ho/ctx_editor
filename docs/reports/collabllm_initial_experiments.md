# CollabLLM Initial Experiments Report

**Date**: 2026-03-18
**Branch**: `collabllm_eval`
**Commits**: `19cb719` (implementation), `8a53c26` (turn-cap bugfix)

## Overview

Initial experiments evaluating our context compaction strategy against the CollabLLM evaluation framework. We implemented a new `ContextCompactionStrategy` (S3) and ran it against a baseline (no context editing) on two CollabLLM benchmark tasks: MATH-Hard (question answering) and BigCodeBench (code generation).

## Setup

### Models
- **Assistant**: gpt-5-mini with `reasoning_effort: low` (to approximate 8B-class model capability, matching CollabLLM's original Llama-3-8B evaluation)
- **User simulator**: gpt-4o-mini (CollabLLM's standard user simulator)
- **Evaluator/Judge**: gpt-4o-mini (for answer extraction, accuracy judging, interactivity judging)
- **Context editor (S3 only)**: gpt-5-mini with `reasoning_effort: low`

### Load balancing
All experiments used `multi_endpoint_full` with 4 Azure endpoints (dl-openai-1, dl-openai-3, fxdata-eastus2, fxdata-shared) for round-robin load balancing.

### Strategy: Context Compaction (S3)
New strategy (`ContextCompactionStrategy`) that activates after user turn 4 and runs **every turn** (unconditional, unlike S2 which is conditional on issues found):

1. **Single-query analysis**: An "independent reviewer" prompt reads the conversation history and produces three sections:
   - User task specification
   - What about the assistant's approach is good and should be kept
   - What about the assistant's approach is bad and should be changed or removed

2. **Context compaction**: The analysis + full conversation are fed into the existing `context_compaction.txt` prompt to generate compacted context (task spec + work completed so far).

3. **Trace reset**: The conversation trace is reset with the compacted context, removing all previous messages from the assistant's view.

Key difference from S2: S3 always compacts after the threshold (not conditional on `needs_edit`), and uses a single-query analysis (not the two-query hard attention separation of v8).

### Datasets
- **MATH-Hard**: 20 problems randomly subsampled (seed=42) from `lighteval/MATH-Hard` test split (1,324 total)
- **BigCodeBench**: 20 problems randomly subsampled (seed=42) from `bigcode/bigcodebench` v0.1.2 split (1,140 total)

### Configuration
- `max_turns: 14` (CollabLLM default)
- `execution.max_concurrent: 4`
- CollabLLM's original system prompt (interactive, asks for clarification) and user simulator prompt (vague, gradually reveals intent)
- No LiC-specific guardrails (no compliance rules, no anti-clarification constraints)

## Results

### Final Results (with turn-cap fix)

| | **Math-Hard** | | **BigCodeBench** | |
|---|---|---|---|---|
| **Metric** | **Baseline** | **Compaction** | **Baseline** | **Compaction** |
| Accuracy (LLM judge) | 40.0% (8/20) | **45.0% (9/20)** | 0.0% (0/20) | 0.0% (0/20) |
| Interactivity | 0.965 | 0.885 | - | 0.990 |
| Avg Turns | 9.1 | 10.4 | 13.3 | 11.9 |
| Avg Asst Tokens | 2,796 | 725 | - | 1,311 |
| Cost | $0.44 | $0.43 | $1.00 | $0.62 |
| Errors | 0 | 0 | 0 | 0 |

### Output Directories
- Baseline Math: `outputs/2026-03-17/04-16-54/`
- Baseline Code: `outputs/2026-03-17/04-16-55/`
- Compaction Math: `outputs/2026-03-18/20-49-55/`
- Compaction Code: `outputs/2026-03-18/20-49-56/`

## Analysis

### Math-Hard: +5pp improvement

Context compaction improved accuracy from 40.0% to 45.0% on MATH-Hard. While modest on 20 samples, the direction is consistent with our core hypothesis: removing failed reasoning and bad assumptions from context helps the model self-correct on subsequent turns.

Notable observations:
- **Token reduction**: Assistant tokens dropped from 2,796 to 725 (74% reduction). Compaction forces more concise responses by removing accumulated context bloat.
- **Interactivity slightly lower** (0.885 vs 0.965): Expected, since compacted context shifts the model toward solving rather than asking clarifying questions.
- **Cost-neutral**: $0.43 vs $0.44. The extra analysis+compaction LLM calls are offset by shorter conversations with less context.

### BigCodeBench: 0% for both (evaluation methodology issue)

Both baseline and compaction scored 0% on BigCodeBench. Investigation revealed this is **not** due to API errors or implementation bugs, but a fundamental mismatch between our evaluation method and the CollabLLM paper's approach.

**Our implementation**: LLM-as-judge compares extracted code against ground truth solution text.

**CollabLLM paper**: Executes extracted code against test cases (pass rate).

#### Why LLM-as-judge fails for code

The ground truth for BigCodeBench problems specifies exact function signatures:
```python
# Ground truth expects:
def task_func(s1, s2):
    high_sales_categories = s1.index[(s1 > 200) & (s2 > 200)]
    ...
```

But the CollabLLM user simulator is deliberately vague (per the paper's design). In our traces, the user **never** mentions `task_func`, `s1`, or `s2`. The assistant builds a reasonable but structurally different function:
```python
# Assistant produces:
def compare_store_sales(store_a, store_b, categories=None, threshold=200, ...):
    ...
```

The LLM accuracy judge compares these textually and scores 0, even though the function may be functionally correct. Test-case execution would be far more forgiving -- if the code produces correct output, it passes regardless of naming.

#### Example conversation (BigCodeBench/1034)

The ground truth asks for a function `task_func(s1, s2)` that compares store sales, generates a bar plot, and computes Euclidean distance. The multi-turn conversation:

- **Turn 1 (user)**: "Can you show me how that function will look? I want to make sure it checks for thresholds and generates the plot correctly."
- **Turn 1 (assistant)**: Asks for clarification about language, data format, what "thresholds" means.
- **Turn 2 (user)**: "Can you modify the function to compare sales data from two stores for specific categories? I want it to check against the threshold of 200..."
- **Turn 2 (assistant)**: Produces `compare_store_sales()` with full implementation.
- **Turns 3-14**: User asks about CSV formatting, testing, error handling. Conversation drifts to practical usage rather than spec refinement.

The extracted code is a working function that does what the user asked for, but with different naming, extra parameters, and a more elaborate API. The LLM judge scores it 0.

### Bug found and fixed: turn counter bypass

During the initial (pre-fix) compaction runs, we discovered that `collabllm_simulator.py` used `trace.num_user_turns` (active/visible turns only) for the max_turns check. Since context compaction resets the trace and hides all previous messages, `num_user_turns` would drop back to ~1 after each compaction, and conversations ran to 50-200+ turns instead of the configured 14.

**Fix** (commit `8a53c26`): Changed to `trace.total_user_turns` which counts across all resets.

Pre-fix compaction results (for reference, not valid):
- Math: 52.6% accuracy, 27.8 avg turns, $1.22 cost
- Code: 5.6% accuracy, 73.3 avg turns, $3.55 cost

## Next Steps

1. **Implement test-case execution for BigCodeBench**: The CollabLLM paper uses pass rate (code execution against test cases), not LLM-as-judge. We need to extract the code, wrap it with the expected function signature if needed, and run against BigCodeBench's test suite. This is required to get comparable numbers.

2. **Scale up sample size**: 20 samples per task is a pilot. Need 100+ for statistically meaningful comparisons.

3. **Compare against CollabLLM paper baselines**: The paper reports results with Llama-3-8B. Our gpt-5-mini (low) results should be compared against those.

## Files Created/Modified

### New files
- `src/ctx_editor/strategies/context_compaction.py` -- ContextCompactionStrategy (S3)
- `src/ctx_editor/strategies/prompts/compaction_analysis.txt` -- Single-query analysis prompt
- `src/ctx_editor/config/model/gpt5_mini_low.yaml` -- gpt-5-mini with reasoning_effort: low
- `src/ctx_editor/config/experiment/collabllm_compaction.yaml` -- Experiment config for S3

### Modified files
- `src/ctx_editor/data/collabllm_loader.py` -- Added BigCodeBench loader, random subsampling, dataset-specific default splits
- `src/ctx_editor/config/collabllm.yaml` -- Updated defaults to gpt5_mini_low + multi_endpoint_full
- `src/ctx_editor/strategies/__init__.py` -- Export ContextCompactionStrategy
- `src/ctx_editor/run_collabllm.py` -- Fixed split handling for non-standard datasets
- `src/ctx_editor/core/collabllm_simulator.py` -- Fixed turn counter to use total_user_turns
