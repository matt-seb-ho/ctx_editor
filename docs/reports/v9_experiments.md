# V9 LiC Experiments + Actions Accumulate Fairness

**Date**: 2026-03-26
**Branch**: `main`

## Overview

Two workstreams:
1. **Actions accumulate fairness (v8)**: Re-ran baseline, S1, S3 for actions with accumulate instruction to ensure fair comparison across all strategies.
2. **V9 LiC experiments**: New v9 analyzer prompt with expanded issue types, tested S1/S1.5/S2/S3 across all tasks.
3. **V8 S3 for LiC**: First time testing S3 (LLM-driven context rewrite) with hard-attention analysis on LiC.

## V9 Prompt Changes

**Q1 (task spec)**: Unchanged from v8 — same hard-attention, user-messages-only architecture.

**Q2 (compare)**: Expanded from v8. Key changes:
- Added explicit three-dimension analysis framework:
  1. **Task spec contradictions** (what v8 already covered)
  2. **Errors independent of spec** — wrong calculations, buggy code, incorrect SQL (NEW)
  3. **Bloat** — overcomplication from patching earlier wrong attempts (NEW)
- Added `<corrective_direction>` section — specific guidance on what to do differently
- Emphasized concrete, data-rich output (exact values, formulas, code snippets)
- Added framing: "Your analysis will be used to improve the assistant's context"

**File**: `src/ctx_editor/strategies/prompts/analyzer_v9_compare.txt`

## Results

### Comparison: V8 vs V9

| Strategy | | Math | Code | Database | Actions |
|---|---|:---:|:---:|:---:|:---:|
| **S1** | v8 | 80% (16/20) | 56% (10/18) | 32% (8/25) | 48%† (11/23) |
| | v9 | 78% (18/23) | **68%** (17/25) | **44%** (11/25) | 52%† (13/25) |
| | Δ | -2pp | **+12pp** | **+12pp** | +4pp |
| **S1.5** | v8 | 75% (15/20) | 61% (11/18) | **48%** (12/25) | 52%† (12/23) |
| | v9 | **87%** (20/23) | 64% (16/25) | 44% (11/25) | **76%**† (19/25) |
| | Δ | **+12pp** | +3pp | -4pp | **+24pp** |
| **S2** | v8 | 75% (15/20) | **72%** (13/18) | 44% (11/25) | 74%† (17/23) |
| | v9 | 74% (17/23) | 50% (11/22) | **52%** (13/25) | 68%† (17/25) |
| | Δ | -1pp | -22pp* | **+8pp** | -6pp |
| **S3** | v8 | 80% (16/20) | 56% (10/18) | 40% (10/25) | 35% (8/23) |
| | v9 | **83%** (19/23) | **64%** (16/25) | 40% (10/25) | 36% (9/25) |
| | Δ | +3pp | **+8pp** | 0pp | +1pp |

†With accumulate instruction
*V8 S2 code used full simulation; v9 S2 code used replay — not directly comparable

**Caveats on denominators**: V8 excluded user-sim-induced samples upfront (smaller denominators). V9 includes all samples. Direct % comparison is approximate; sample-level matching would be more precise.

### Key Findings

1. **V9 S1.5 is the standout**: Math 87% (+12pp), Actions 76% (+24pp). The expanded issue types in v9 Q2 are producing better analysis, which S1.5 translates directly into better compacted context.

2. **V9 S1 code improves significantly**: 68% vs 56% (+12pp). The explicit error and bloat dimensions help the analyzer identify code issues that aren't strictly spec contradictions.

3. **V9 S2 has mixed results**: Database improves (+8pp to 52%), but code drops significantly. The S2 code drop may be a replay vs. full-sim artifact — S2 benefits from gating decisions at every turn, which replay can't provide.

4. **V9 S3 improves on code**: 64% vs 56% (+8pp). The richer analysis (with corrective direction) gives the S3 compaction step better raw material.

5. **Database is mixed**: S1 and S2 improve, S1.5 regresses slightly. The expanded issue types may introduce noise on database tasks where the spec-contradiction axis was already sufficient.

### Actions Accumulate Fairness (v8)

| Strategy | Without Accum | With Accum | Δ |
|---|:---:|:---:|:---:|
| Baseline (S0) | 9% (2/23) | **35%** (8/23) | +26pp |
| Append Analysis (S1) | 22% (5/23) | **48%** (11/23) | +26pp |
| Always-Reset (S1.5) | — | 52% (12/23) | already had |
| Gated Reset (S2) | 13% (3/23) | **74%** (17/23) | +61pp |
| S3 (LLM rewrite) | — | 35% (8/23) | no accum‡ |

‡S3 rewrite doesn't include accumulate instruction; the LLM compaction prompt would need modification.

**Conclusion**: Accumulate is critical for ALL strategies on actions, not just context-reset methods. Even the raw baseline jumps +26pp. This is because BFCL evaluation checks only the final message — without accumulate, the model doesn't consolidate all parallel function calls.

**Paper implications**: S1 actions should be reported as 48% (with accumulate) for fair comparison with S1.5 (52%) and S2 (74%).

### V8 S3 for LiC (First Time, Hard Attention)

| Task | S0 | S1 | S1.5 | S2 | S3 |
|---|:---:|:---:|:---:|:---:|:---:|
| Math | 60% | 80% | 75% | 75% | **80%** |
| Code | 16% | 56% | 61% | 72% | **56%** |
| Database | 4% | 32% | 48% | 44% | **40%** |
| Actions | 9% | 48% | 52% | 74% | **35%** |

S3 with hard attention matches S1 (analysis quality is the same, just different context delivery). On math and code, S3 = S1. On database, S3 is between S1 and S1.5. S3 doesn't outperform S1.5 on any task, suggesting that LLM-driven context rewriting doesn't add value beyond programmatic compaction when the analysis is already clean.

## Run Details

### Actions Accumulate Fairness

| Run | Result | Dir |
|-----|:------:|-----|
| S0+accum actions | 8/23 (35%) | `outputs/2026-03-26/04-10-01` |
| S1+accum actions | 11/23 (48%) | `outputs/2026-03-26/04-10-31` |

### V8 S3 (Hard Attention)

| Run | Result | Dir |
|-----|:------:|-----|
| S3 math | 16/20 (80%) | `outputs/2026-03-26/04-10-44` |
| S3 code | 10/18 (56%) | `outputs/2026-03-26/04-12-09` |
| S3 database | 10/25 (40%) | `outputs/2026-03-26/04-12-09` |
| S3 actions | 8/23 (35%) | `outputs/2026-03-26/04-12-09` |

### V9 S1 (Full Simulation)

| Run | Result | Dir |
|-----|:------:|-----|
| S1 math | 18/23 (78%) | `outputs/2026-03-26/04-13-57` |
| S1 code | 17/25 (68%) | `outputs/2026-03-26/04-47-32` |
| S1 database | 11/25 (44%) | `outputs/2026-03-26/04-36-46` |
| S1 actions | 11/25 (44%) | `outputs/2026-03-26/05-07-17` |
| S1+accum actions | 13/25 (52%) | `outputs/2026-03-26/05-18-32` |

### V9 S1.5 (Replay from V9 S1)

| Run | Result | Dir |
|-----|:------:|-----|
| S1.5 math | 20/23 (87%) | `outputs/2026-03-26/05-13-25` |
| S1.5 code | 16/25 (64%) | `outputs/2026-03-26/05-13-52` |
| S1.5 database | 11/25 (44%) | `outputs/2026-03-26/05-14-32` |
| S1.5 actions (+accum) | 19/25 (76%) | `outputs/2026-03-26/05-15-03` |

### V9 S2 (Replay from Baseline)

| Run | Result | Dir |
|-----|:------:|-----|
| S2 math | 17/23 (74%) | `outputs/2026-03-26/04-23-57` |
| S2 code | 11/22 (50%) | `outputs/2026-03-26/04-27-57` |
| S2 database | 13/25 (52%) | `outputs/2026-03-26/04-33-43` |
| S2 actions | 8/25 (32%) | `outputs/2026-03-26/04-27-56` |
| S2+accum actions | 17/25 (68%) | `outputs/2026-03-26/05-19-28` |

### V9 S3 (Replay from V9 S1)

| Run | Result | Dir |
|-----|:------:|-----|
| S3 math | 19/23 (83%) | `outputs/2026-03-26/05-15-31` |
| S3 code | 16/25 (64%) | `outputs/2026-03-26/05-16-15` |
| S3 database | 10/25 (40%) | `outputs/2026-03-26/05-17-11` |
| S3 actions | 9/25 (36%) | `outputs/2026-03-26/05-17-58` |

## Code Changes

- `src/ctx_editor/strategies/prompts/analyzer_v9_compare.txt`: New v9 Q2 prompt
- `src/ctx_editor/strategies/analyzer.py`: Added v9 dispatch, corrective_direction field
- `src/ctx_editor/config/experiment/append_analysis_v9.yaml`: S1 v9 config
- `src/ctx_editor/config/experiment/context_edit_v2_v9.yaml`: S2 v9 config
- `src/ctx_editor/config/experiment/context_edit_v2_v9_accumulate.yaml`: S2 v9 + accumulate
- `scripts/run_s15_experiment.py`: Added s0-accum and s1-accum modes for accumulate fairness

## Commands Used

```bash
# Accumulate fairness
python scripts/run_s15_experiment.py --s1-dir <baseline-dir> --task actions --mode s0-accum --accumulate --no-clarification
python scripts/run_s15_experiment.py --s1-dir <s1-dir> --task actions --mode s1-accum --accumulate --no-clarification

# V9 S1 (full sim)
ctx-editor experiment=append_analysis_v9 task=dev_<task> model=gpt5_mini execution.max_concurrent=20

# V9 S1.5 (replay from v9 S1)
python scripts/run_s15_experiment.py --s1-dir <v9-s1-dir> --task <task> --mode s15 --no-notes --sanitize --no-clarification [--accumulate for actions]

# V9 S2 (replay from baseline)
ctx-editor experiment=context_edit_v2_v9 task=dev_<task> model=gpt5_mini execution.max_concurrent=20 execution.replay_source=<baseline-dir>

# V9 S3 (replay from v9 S1)
python scripts/run_s15_experiment.py --s1-dir <v9-s1-dir> --task <task> --mode s3
```
