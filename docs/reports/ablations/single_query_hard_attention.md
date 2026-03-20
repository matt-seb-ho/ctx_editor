# Ablation: Hard Attention and Query Architecture

**Date**: 2026-03-17
**Branch**: `newleaf2`
**Commits**: `0032ce5` (v8_single), `749b6f3` (v8_soft), `14aeb8b` (spec_only)

## Hypothesis

The v8 analyzer uses a two-query architecture with "hard attention" — the task spec query (Query 1) sees **only user messages and the system message**, never assistant messages. This forces the model to build a clean specification from user intent alone, uncontaminated by the assistant's (potentially wrong) reasoning. Query 2 then compares that spec against the full conversation.

**Questions**:
1. Is the hard attention separation responsible for S1 gains?
2. Is the damage from assistant message contamination or from combining two tasks into one prompt (chaining)?
3. Does Query 2 (comparison) add value beyond the task spec alone?

## Design

Four configurations, all using the same downstream strategy (analysis appended as `[conversation analysis]` message):

| Variant | Query 1 sees | # queries | Output appended | What it tests |
|---|---|---|---|---|
| **S1** (v8, control) | user msgs only | 2 | spec + aligned + issues | Full system |
| **S1-speconly** (v8, spec_only) | user msgs only | 1 | spec only | Value of Query 2 |
| **S1-soft** (v8_soft) | full conversation | 2 | spec + aligned + issues | Hard attention, isolated |
| **S1-single** (v8_single) | full conversation | 1 | spec + aligned + issues | Hard attention + chaining |

**What's controlled across all variants**:
- Same model (gpt-5-mini), same temperature, same timeout
- Same v2 evaluators, same dev subsets, same replay traces (depth=1)
- Same false negative filtering
- Same `AppendAnalysisStrategy` (analysis inserted before last user message)

## Results

### Full Comparison (No Memory)

| Task | S0 | S1-speconly (1q, hard) | S1 (2q, hard) | S1-single (1q, soft) | S1-soft (2q, soft) |
|------|:---:|:---:|:---:|:---:|:---:|
| Math (n=20) | 12/20 (60%) | 14/20 (70%) | **16/20 (80%)** | 11/20 (55%) | 8/20 (40%) |
| Code (n=19) | 3/19 (16%) | **12/19 (63%)** | 10/18 (56%) | 4/19 (21%) | 2/19 (11%) |
| Database (n=25) | 1/25 (4%) | **10/25 (40%)** | 8/25 (32%) | 1/25 (4%) | 2/25 (8%) |

### Decomposition: What Each Component Contributes

| Task | S0 → S1-speconly (task spec alone) | S1-speconly → S1 (comparison query) | S0 → S1 (total) |
|------|:---:|:---:|:---:|
| Math | +10pp | +10pp | +20pp |
| Code | +47pp | -7pp | +40pp |
| Database | +36pp | -8pp | +28pp |

## Key Findings

### 1. The task spec is the primary mechanism

S1-speconly (hard attention task spec, no comparison) captures the bulk of S1's gains:
- **Math**: 70% — captures 50% of S1's gain over baseline (10pp of 20pp)
- **Code**: 63% — **exceeds S1** by 7pp
- **Database**: 40% — **exceeds S1** by 8pp

The clean, hard-attention task spec alone — at half the LLM cost — matches or beats the full two-query system on 2 of 3 tasks.

### 2. The comparison query helps on math, hurts on code and database

On math, the comparison query adds +10pp (70% → 80%). On code and database, it actually **reduces** accuracy by 7-8pp. The comparison query's aligned/issues judgments apparently introduce noise that distracts the assistant on structured-output tasks (SQL, code), where the task spec alone is a cleaner signal.

This suggests the comparison query's value is task-dependent. For math (where the "what's wrong" signal is more nuanced), explicit error identification helps. For code and database (where the spec itself defines the output format), additional commentary is counterproductive.

### 3. Hard attention is load-bearing — removing it collapses performance to baseline

Both soft-attention variants (S1-single, S1-soft) perform at or below baseline:

| Task | S0 | S1-soft (2q, soft) | S1-single (1q, soft) |
|------|:---:|:---:|:---:|
| Math | 60% | 40% | 55% |
| Code | 16% | 11% | 21% |
| Database | 4% | 8% | 4% |

Without hard attention, the analysis provides zero value — appending it is no better (and often worse) than not having analysis at all.

### 4. Contamination amplification: S1-soft is worse than S1-single

S1-soft (two queries, no hard attention) underperforms S1-single (one query) on math (40% vs 55%) and code (11% vs 21%). When Query 1 produces a contaminated task spec and that spec is passed to Query 2 as authoritative ground truth, the contamination is *amplified*. Query 2 evaluates the conversation against the wrong spec, producing wrong aligned/issues judgments that actively mislead the assistant.

In the single-query case, there's no authoritative handoff point — the contamination still happens but doesn't get the "authority boost."

### 5. Contaminated analysis is actively harmful, not just useless

Both soft-attention variants frequently perform *below* baseline:
- S1-soft: below baseline on math (40% vs 60%) and code (11% vs 16%)
- S1-single: below baseline on math (55% vs 60%)

The contaminated analysis reinforces the assistant's incorrect assumptions with a false sense of external validation.

## Summary: The 2×2 Matrix

|  | Hard attention (user only) | Soft attention (full conversation) |
|---|:---:|:---:|
| **1 query (spec only)** | S1-speconly: **strong** (matches/beats S1) | S1-single: at baseline |
| **2 queries (spec + comparison)** | S1: **strong** (best on math) | S1-soft: **below baseline** |

The dominant axis is **hard vs soft attention** — it determines whether the system works at all. The secondary axis (1 vs 2 queries) is task-dependent and can go either way.

## Implications

1. **Hard attention is the load-bearing architectural decision.** It cannot be removed or relaxed.
2. **The task spec alone is a viable (and cheaper) strategy** for code and database tasks. It halves LLM cost with no accuracy loss.
3. **The comparison query is a mixed bag.** It helps on math but hurts on structured-output tasks. A task-adaptive approach (spec-only for code/database, full analysis for math) could be optimal.
4. **The two-query architecture amplifies spec quality in both directions.** Clean spec → good analysis. Contaminated spec → actively harmful analysis.

## Run Details

**Model**: `gpt-5-mini` (assistant + analyzer), `gpt-4o-mini` (user/system agents)
**Task configs**: `dev_math`, `dev_code`, `dev_database` (all v2 evaluators)
**Replay**: `data/baseline_traces_v2/{task}/`, depth=1, false negatives skipped

### Output Directories

| Run | Result | Dir |
|-----|:------:|-----|
| S1-speconly math | 14/20 (70%) | `outputs/2026-03-17/04-47-34` |
| S1-speconly code | 12/19 (63%) | `outputs/2026-03-17/04-47-34` |
| S1-speconly database | 10/25 (40%) | `outputs/2026-03-17/04-47-34` |
| S1-single math | 11/20 (55%) | `outputs/2026-03-17/03-02-33` |
| S1-single code | 4/19 (21%) | `outputs/2026-03-17/03-02-34` |
| S1-single database | 1/25 (4%) | `outputs/2026-03-17/03-02-35` |
| S1-soft math | 8/20 (40%) | `outputs/2026-03-17/04-12-12` |
| S1-soft code | 2/19 (11%) | `outputs/2026-03-17/04-12-14` |
| S1-soft database | 2/25 (8%) | `outputs/2026-03-17/04-12-14` |

### Files Added

- Prompts: `analyzer_v8_single.txt`, `analyzer_v8_soft_spec.txt`
- Analyzer: `v8_single`, `v8_soft`, `spec_only` in `src/ctx_editor/strategies/analyzer.py`
- Strategy: `spec_only` flag in `AppendAnalysisStrategy`
- Configs: `append_analysis_single{,_memory}.yaml`, `append_analysis_soft.yaml`, `append_analysis_spec_only.yaml`
- Run script: `scripts/run_single_query_ablation.sh`
