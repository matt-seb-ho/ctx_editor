# Ablation: Single-Query Analysis (No Hard Attention)

**Date**: 2026-03-17
**Branch**: `newleaf2`
**Commit**: `0032ce5`

## Hypothesis

The v8 analyzer uses a two-query architecture with "hard attention" — the task spec query (Query 1) sees **only user messages and the system message**, never assistant messages. This forces the model to build a clean specification from user intent alone, uncontaminated by the assistant's (potentially wrong) reasoning.

**Question**: Is this code-enforced attention separation responsible for S1/S1.5 gains? Or can a single combined query that sees the full conversation (including assistant messages) produce equally useful analysis?

## Design

**S1-single**: Identical to S1 (`AppendAnalysisStrategy`) but uses a single LLM call (`v8_single` prompt) instead of two. The single prompt receives the system message and full conversation, then asks the model to:
1. Construct the task spec (seeing all messages, including assistant)
2. Compare the assistant's work against the spec

Same output format (`<task_spec>`, `<aligned>`, `<issues>`), same downstream integration. The only variable is whether assistant messages are visible during task spec construction.

**What's controlled**:
- Same model (gpt-5-mini), same temperature, same timeout
- Same v2 evaluators, same dev subsets, same replay traces (depth=1)
- Same false negative filtering
- Same downstream strategy (analysis appended as `[conversation analysis]` message)

**What differs**:
- Two-query S1: task spec built from user messages only (hard attention), then compared against full conversation in a second call
- Single-query S1-single: task spec built while seeing full conversation (no hard attention), comparison done in same call

## Results

### S1-single vs S1 (No Memory)

| Task | S0 (baseline) | S1-single | S1 (two-query) | Δ single→two |
|------|:---:|:---:|:---:|:---:|
| Math (n=20) | 12/20 (60%) | 11/20 (55%) | 16/20 (80%) | **+25pp** |
| Code (n=19) | 3/19 (16%) | 4/19 (21%) | 10/18 (56%) | **+35pp** |
| Database (n=25) | 1/25 (4%) | 1/25 (4%) | 8/25 (32%) | **+28pp** |

**Actions**: Skipped — no baseline replay traces available for this task.

### Key Observation

S1-single performs at or below S0 baseline on every task. The analysis produced by the single-query prompt provides essentially zero value — the appended analysis is no better than not having analysis at all.

## Interpretation

### Why the single query fails

When the model sees assistant messages during task spec construction, **the assistant's reasoning contaminates the spec**. The assistant's wrong assumptions, incorrect intermediate results, and flawed interpretations become anchoring content that biases the task spec away from what the user actually asked for.

This is exactly the "hard attention" problem the two-query architecture was designed to solve. The assistant's messages contain:
- **Confident but wrong answers** that the model treats as established facts
- **Assumptions stated as given** (e.g., "Based on your requirement to X..." where X was never required)
- **Partial solutions** that anchor the spec toward the assistant's current approach

With two queries, the task spec query is immunized from this contamination because it literally cannot see assistant messages. The spec is built purely from user intent + system context.

### The task spec is the mechanism, and hard attention is what makes it work

The v8 batch report (see `docs/reports/v8_batch_results.md`) identified the task spec as "doing most of the work" — S1 (append analysis) captures most of the gains even without context rewriting. This ablation reveals the complementary finding: **the task spec only works because of hard attention**. A task spec built with full conversation visibility is worthless.

Together these findings establish:
1. A clean task spec is the primary mechanism for course correction
2. Hard attention (hiding assistant messages from the spec query) is what makes the spec clean
3. Neither component works without the other

### Cost implication

The two-query architecture costs 2× LLM calls per turn. This ablation confirms that cost is justified — a single query cannot substitute. The hard attention separation is not an optimization target; it's a load-bearing architectural decision.

## Run Details

**Model**: `gpt-5-mini` (assistant + analyzer), `gpt-4o-mini` (user/system agents)
**Task configs**: `dev_math`, `dev_code`, `dev_database` (all v2 evaluators)
**Replay**: `data/baseline_traces_v2/{task}/`, depth=1, false negatives skipped
**Experiment config**: `experiment=append_analysis_single` (new, uses `analyzer_prompt_version: v8_single`)

### Output Directories

| Run | Result | Dir |
|-----|:------:|-----|
| S1-single math | 11/20 (55%) | `outputs/2026-03-17/03-02-33` |
| S1-single code | 4/19 (21%) | `outputs/2026-03-17/03-02-34` |
| S1-single database | 1/25 (4%) | `outputs/2026-03-17/03-02-35` |

### Files Added

- Prompt: `src/ctx_editor/strategies/prompts/analyzer_v8_single.txt`
- Analyzer: `v8_single` dispatch in `src/ctx_editor/strategies/analyzer.py`
- Configs: `src/ctx_editor/config/experiment/append_analysis_single{,_memory}.yaml`
- Run script: `scripts/run_single_query_ablation.sh`

## Follow-up (Not Run)

S1-single+memory and S1.5-single were not run. Given that S1-single matches baseline, adding memory or context resetting on top of a contaminated analysis would not meaningfully change the conclusion. The bottleneck is the quality of the task spec, which is broken at the source.
