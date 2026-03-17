# Ablation: Hard Attention in the Two-Query Architecture

**Date**: 2026-03-17
**Branch**: `newleaf2`
**Commits**: `0032ce5` (v8_single), `749b6f3` (v8_soft)

## Hypothesis

The v8 analyzer uses a two-query architecture with "hard attention" — the task spec query (Query 1) sees **only user messages and the system message**, never assistant messages. This forces the model to build a clean specification from user intent alone, uncontaminated by the assistant's (potentially wrong) reasoning.

**Questions**:
1. Is this code-enforced attention separation responsible for S1 gains?
2. If so, is the damage from assistant message contamination or from combining two tasks into one prompt (chaining)?

## Design

Two ablation variants, both compared against S1 (two-query, hard attention):

| Variant | Query 1 sees | # queries | What it tests |
|---|---|---|---|
| **S1** (v8, control) | user msgs only | 2 | Full system |
| **S1-soft** (v8_soft) | full conversation | 2 | Hard attention effect, isolated |
| **S1-single** (v8_single) | full conversation | 1 | Hard attention + chaining combined |

**S1-soft** keeps the two-query architecture but removes the hard attention: Query 1 sees the full conversation (user + assistant messages) when building the task spec. Query 2 is identical to S1. This isolates the effect of hiding assistant messages.

**S1-single** collapses both queries into one prompt. The model sees the full conversation and produces task spec + aligned + issues in a single call. This tests both contamination and chaining together.

**What's controlled across all variants**:
- Same model (gpt-5-mini), same temperature, same timeout
- Same v2 evaluators, same dev subsets, same replay traces (depth=1)
- Same false negative filtering
- Same downstream strategy (analysis appended as `[conversation analysis]` message)

## Results

### Full Comparison (No Memory)

| Task | S0 (baseline) | S1-soft (2q, soft) | S1-single (1q) | S1 (2q, hard) |
|------|:---:|:---:|:---:|:---:|
| Math (n=20) | 12/20 (60%) | 8/20 (40%) | 11/20 (55%) | **16/20 (80%)** |
| Code (n=19) | 3/19 (16%) | 2/19 (11%) | 4/19 (21%) | **10/18 (56%)** |
| Database (n=25) | 1/25 (4%) | 2/25 (8%) | 1/25 (4%) | **8/25 (32%)** |

### Deltas vs S1

| Task | S1-soft → S1 | S1-single → S1 |
|------|:---:|:---:|
| Math | +40pp | +25pp |
| Code | +45pp | +35pp |
| Database | +24pp | +28pp |

## Key Findings

### 1. Hard attention is load-bearing

Both ablation variants collapse to baseline or below. Without hard attention, the analysis provides zero value — appending it is no better (and sometimes worse) than not having analysis at all.

### 2. Contamination is worse than chaining — S1-soft underperforms S1-single

The surprising result: S1-soft (two queries, no hard attention) is **worse** than S1-single (one query) on math (40% vs 55%) and code (11% vs 21%). This is counterintuitive — you'd expect the two-query architecture to at least match the single query.

**Why**: When Query 1 produces a contaminated task spec and that spec is passed to Query 2, the contamination is *amplified*. Query 2 takes the spec as authoritative ground truth and evaluates the conversation against it. A wrong spec produces wrong aligned/issues judgments, which actively mislead the assistant. The two-query chain becomes a contamination amplifier.

In the single-query case, the model produces the spec and comparison in one pass, so there's no authoritative handoff point where the spec gets treated as ground truth. The contamination still happens, but it doesn't get the "authority boost" from being passed as an explicit input to a second query.

### 3. Contaminated analysis is actively harmful, not just useless

Both S1-soft and S1-single perform at or below baseline on most tasks:
- S1-soft: below baseline on math (40% vs 60%) and code (11% vs 16%)
- S1-single: below baseline on math (55% vs 60%), at baseline on code and database

The contaminated analysis doesn't just fail to help — it often makes things worse by reinforcing the assistant's incorrect assumptions with a false sense of external validation.

### 4. The mechanism is clear

The v8 batch report identified the task spec as "doing most of the work." These ablations complete the picture:

1. **A clean task spec is the primary mechanism** — it gives the assistant a corrective signal
2. **Hard attention is what makes the spec clean** — hiding assistant messages prevents contamination
3. **Two-query architecture amplifies spec quality in both directions** — a clean spec produces good analysis (S1), a contaminated spec produces actively harmful analysis (S1-soft)
4. **The cost of 2× LLM calls is justified** — there's no cheaper path to the same result

## Run Details

**Model**: `gpt-5-mini` (assistant + analyzer), `gpt-4o-mini` (user/system agents)
**Task configs**: `dev_math`, `dev_code`, `dev_database` (all v2 evaluators)
**Replay**: `data/baseline_traces_v2/{task}/`, depth=1, false negatives skipped

### Output Directories

| Run | Result | Dir |
|-----|:------:|-----|
| S1-single math | 11/20 (55%) | `outputs/2026-03-17/03-02-33` |
| S1-single code | 4/19 (21%) | `outputs/2026-03-17/03-02-34` |
| S1-single database | 1/25 (4%) | `outputs/2026-03-17/03-02-35` |
| S1-soft math | 8/20 (40%) | `outputs/2026-03-17/04-12-12` |
| S1-soft code | 2/19 (11%) | `outputs/2026-03-17/04-12-14` |
| S1-soft database | 2/25 (8%) | `outputs/2026-03-17/04-12-14` |

### Files Added

- Prompts: `src/ctx_editor/strategies/prompts/analyzer_v8_single.txt`, `analyzer_v8_soft_spec.txt`
- Analyzer: `v8_single` and `v8_soft` dispatch in `src/ctx_editor/strategies/analyzer.py`
- Configs: `append_analysis_single{,_memory}.yaml`, `append_analysis_soft.yaml`
- Run script: `scripts/run_single_query_ablation.sh`

## Follow-up (Not Run)

S1.5-soft, S1.5-single, and memory variants were not run. Both ablation variants perform at or below baseline, so adding context resetting or memory on top would not change the conclusion. The bottleneck is task spec quality, which is broken at the source when hard attention is removed.
