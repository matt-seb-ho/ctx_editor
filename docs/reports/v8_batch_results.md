# V8 Batch Results — 2026-03-17

## Overview

This report covers the v8 prompt batch: replay-last-turn experiments across all 4 tasks with S0/S1/S2 × {no-mem, mem}, plus an S1.5 ablation and actions evaluator fix. This serves as the starting point for two parallel branches: (1) improving memory gains and (2) single-query analysis ablation.

## What Changed in V8

1. **System message in task spec query**: The analyzer now sees the system message (schema, function signatures, output format constraints) when building the task spec. This was the single biggest improvement — it grounded the spec in the correct task format instead of producing generic consulting-style specs.

2. **Consolidation-friendly prompt**: Task spec prompt encourages rewording/consolidation of meandering user messages while preserving crucial details. Less verbatim transcription, more clean distillation.

3. **All user messages across resets**: Task spec query now sees all unique user messages from the entire conversation (not just post-reset), rebuilt from scratch each time without the previous compacted task spec.

4. **Default prompt version**: v8 is now the default in `ConversationAnalyzer`, `AppendAnalysisStrategy`, and `ContextEditV2Strategy`. No CLI override needed.

5. **v8 dispatch fix**: v8 was loading two-query templates but falling through to single-query dispatch. Fixed to route through `_analyze_v6` (two-query flow).

6. **Actions boolean fix**: `eval_bfcl.py` now normalizes JavaScript-style `true`/`false`/`null` to Python `True`/`False`/`None` in AST parsing.

7. **False negative filtering in replay**: Pre-computed `false_negatives.json` files skip user-sim-induced samples during replay, saving cost and cleaning up denominators.

## Results

### Main Grid: S0/S1/S2 × {no-mem, mem}

| Config | Math (n=20) | Code (n=19*) | Database (n=25) | Actions (n=23) |
|--------|:-----------:|:------------:|:---------------:|:--------------:|
| **S0** | 12/20 (60%) | 3/19 (16%) | 1/25 (4%) | 2/23 (9%) |
| **S0+mem** | 11/20 (55%) | 4/19 (21%) | 1/25 (4%) | 2/23 (9%) |
| **S1** | 16/20 (80%) | 10/18 (56%) | 8/25 (32%) | 5/23 (22%) |
| **S1+mem** | **18/20 (90%)** | **13/19 (68%)** | **11/25 (44%)** | 2/23 (9%) |
| **S2** | 15/20 (75%) | 13/18 (72%) | **11/25 (44%)** | 3/23 (13%) |
| **S2+mem** | 15/20 (75%) | 13/19 (68%) | 9/25 (36%) | 3/23 (13%) |

*Code S1/S2 runs had 1 timeout error reducing denominator to 18.

### S1.5 Ablation: Always-Reset (No Gate)

S1.5 takes S1's pre-computed analysis and always does a context reset (like S2), bypassing S2's binary edit/no-edit gate. Tests whether context removal helps beyond appended analysis.

| Config | Math (n=20) | Code | Database (n=25) | Actions (n=23) |
|--------|:-----------:|:----:|:---------------:|:--------------:|
| **S1** | 16/20 (80%) | 10/18 (56%) | 8/25 (32%) | 5/23 (22%) |
| **S1.5** | 16/20 (80%) | 11/16† (69%) | 10/25 (40%) | 7/23 (30%) |
| **S2** | 15/20 (75%) | 13/18 (72%) | 11/25 (44%) | 3/23 (13%) |
| | | | | |
| **S1+mem** | **18/20 (90%)** | **13/19 (68%)** | **11/25 (44%)** | 2/23 (9%) |
| **S1.5+mem** | 17/20 (85%) | 12/17† (71%) | 9/25 (36%) | 7/23 (30%) |
| **S2+mem** | 15/20 (75%) | 13/19 (68%) | 9/25 (36%) | 3/23 (13%) |

†Code S1.5 had 9 timeout errors (denominator 16); S1.5+mem had 8 (denominator 17). Percentages are inflated relative to S1/S2 denominators.

### V8 vs V6 Comparison (Best Per Task)

| Task | V6 Best | V8 Best | Δ |
|------|:-------:|:-------:|:-:|
| Math | 15/20 (75%) | **18/20 (90%)** | +15pp |
| Code | 6/18 (33%) | **13/18 (72%)** | +39pp |
| Database | 4/25 (16%) | **11/25 (44%)** | +28pp |
| Actions | 5/23 (22%) | **7/23 (30%)** | +8pp |

## Key Findings

### 1. The Task Spec Is Doing Most of the Work

Including the system message in the task spec query was transformative. The analyzer now produces SQL-aware specs for database, function-call-aware specs for actions, and format-aware specs for code. This single change accounts for most of the v6→v8 improvement.

S1 (append analysis only, no context removal) captures most of the gains. This suggests the task spec itself — a clean, consolidated restatement of what the user wants — is the primary mechanism. The assistant reads it, understands the actual task, and course-corrects.

### 2. S2's Gate Is the Problem, Not Context Editing

S2 underperforms S1 on math (75% vs 80%) because of false negatives: the analyzer returns `needs_edit: false` when the assistant is wrong, so no analysis is provided at all. S1 always provides analysis, so even imperfect analysis helps.

S1.5 (always reset, no gate) performs between S1 and S2 on most tasks, confirming that context removal provides modest incremental benefit but the gate's false negatives are costly.

### 3. Memory Helps S1 But Hurts S2

S1+mem is the best configuration on math (90%) and code (68%). Memory learning works well when it's additive — the cheatsheet helps the analyzer produce better analysis on later batches.

S2+mem consistently underperforms S2 no-mem. The ~1000-word cheatsheet dilutes the analyzer's attention, causing it to miss issues that the no-memory analyzer catches. In 3/4 analyzed regressions, the memory-equipped analyzer returned empty issues where the no-memory analyzer found clear problems.

### 4. Actions Has Two Independent Failure Modes

- **Accumulation** (structural): The sharded format reveals function calls one at a time, but evaluation expects all calls in the last message. Only works when the last shard explicitly says "also" to trigger accumulation. This affects 11/18 failures.
- **Boolean casing** (evaluator bug, now fixed): `true`/`false` → `True`/`False` normalization recovered ~2-5 samples. S1.5 actions jumped from S1's 22% to 30%.

## Architecture & Code State

### Prompt Files
- Task spec: `src/ctx_editor/strategies/prompts/analyzer_v8_task_spec.txt`
- Comparison: `src/ctx_editor/strategies/prompts/analyzer_v8_compare.txt`

### Two-Query Architecture (v6/v7/v8)
1. **Query 1 (task spec)**: System message + all unique user messages → consolidated task specification
2. **Query 2 (comparison)**: Task spec + full conversation (+ optional memory) → aligned/issues assessment

The task spec query now uses `trace.get_user_messages_string(all_unique=True)` to get all user messages across resets (deduplicated). System message is extracted via `trace.system_message`.

### Strategies
- **S0** (`BaselineStrategy`): No intervention
- **S1** (`AppendAnalysisStrategy`): Always append analysis to user message
- **S2** (`ContextEditV2Strategy`): Run analysis, gate on `needs_edit`, reset context if issues found
- **S1.5** (script only, `scripts/run_s15_experiment.py`): Always reset context using pre-computed S1 analysis

### Default Prompt Version
v8 is now the default in `ConversationAnalyzer.__init__`, `AppendAnalysisStrategy.__init__`, and `ContextEditV2Strategy.__init__`. No CLI override needed.

### False Negative Analysis
- Module: `src/ctx_editor/identify_false_negatives.py`
- Two checks: user sim sufficiency (LLM) + answer attempt classification (programmatic)
- Pre-computed files: `data/baseline_traces_v2/{task}_false_negatives.json`
- Replay automatically skips user-sim-induced samples

### Evaluator Fix
- `src/lic/tasks/actions/eval_bfcl.py` line 143: `ast.Name` nodes for `true`/`false`/`null` now map to Python booleans/None

## Run Configuration Reference

**Model**: `model=gpt5_mini` — gpt-5-mini for assistant/analyzer, gpt-4o-mini for user/system agents.

**Task configs**: `task=dev_{task}` with v2 evaluators:
- `dev_math` → 23 samples, 20 after user-sim skip, v2 evaluator
- `dev_code` → 25 samples, 19 after skip, v2 evaluator
- `dev_database` → 25 samples, 0 skipped, v2 evaluator
- `dev_actions` → 25 samples, 23 after skip (2 skipped), no v2 available

**Replay traces**: `data/baseline_traces_v2/{task}/` (gitignored), with `{task}_false_negatives.json` alongside.

**Replay commands** (same as pre_sunday_update.md but no v8 override needed):
```bash
# No memory
ctx-editor experiment={strategy} task=dev_{task} model=gpt5_mini \
  execution.replay_source=data/baseline_traces_v2/{task} \
  execution.max_concurrent=8 logging.verbose=true

# With memory
ctx-editor experiment={strategy}_memory task=dev_{task} model=gpt5_mini \
  execution.replay_source=data/baseline_traces_v2/{task} \
  execution.mode=batched execution.batch_size=5 \
  memory.enabled=true memory.source=continual memory.target=analyzer \
  memory.save_path={path} memory.include_full_spec_q=true \
  memory.include_ground_truth_a=true
```

**S1.5 experiment** (uses pre-computed S1 traces):
```bash
python scripts/run_s15_experiment.py \
  --s1-dir {S1_output_dir} \
  --task {task} \
  --model gpt-5-mini \
  --label {label}
```

## Output Directories (V8 Batch)

**Logs**: `outputs/replay_logs/2026-03-16_19-13-12/`
**S1.5 logs**: `outputs/replay_logs/s15_2026-03-17_01-21-20/`
**Memory checkpoints**: `outputs/replay_memories/2026-03-16_19-13-12/`

| Run | Result | Dir |
|-----|:------:|-----|
| S0 math | 12/20 (60%) | `outputs/2026-03-16/19-13-13` |
| S0 code | 3/19 (16%) | `outputs/2026-03-16/19-16-03` |
| S0 database | 1/25 (4%) | `outputs/2026-03-16/19-23-00` |
| S0 actions | 2/23 (9%) | `outputs/2026-03-16/19-26-46` |
| S0+mem math | 11/20 (55%) | `outputs/2026-03-16/19-29-11` |
| S0+mem code | 4/19 (21%) | `outputs/2026-03-16/19-38-53` |
| S0+mem database | 1/25 (4%) | `outputs/2026-03-16/19-52-09` |
| S0+mem actions | 2/23 (9%) | `outputs/2026-03-16/20-01-16` |
| S1 math | 16/20 (80%) | `outputs/2026-03-16/20-08-42` |
| S1 code | 10/18 (56%) | `outputs/2026-03-16/20-12-21` |
| S1 database | 8/25 (32%) | `outputs/2026-03-16/20-25-10` |
| S1 actions | 5/23 (22%) | `outputs/2026-03-16/20-29-27` |
| S1+mem math | **18/20 (90%)** | `outputs/2026-03-16/20-33-21` |
| S1+mem code | **13/19 (68%)** | `outputs/2026-03-16/20-42-35` |
| S1+mem database | **11/25 (44%)** | `outputs/2026-03-16/20-52-21` |
| S1+mem actions | 2/23 (9%) | `outputs/2026-03-16/21-02-17` |
| S2 math | 15/20 (75%) | `outputs/2026-03-16/21-13-55` |
| S2 code | 13/18 (72%) | `outputs/2026-03-16/21-18-03` |
| S2 database | **11/25 (44%)** | `outputs/2026-03-16/21-30-50` |
| S2 actions | 3/23 (13%) | `outputs/2026-03-16/21-35-58` |
| S2+mem math | 15/20 (75%) | `outputs/2026-03-16/21-41-45` |
| S2+mem code | 13/19 (68%) | `outputs/2026-03-16/21-51-32` |
| S2+mem database | 9/25 (36%) | `outputs/2026-03-16/22-02-35` |
| S2+mem actions | 3/23 (13%) | `outputs/2026-03-16/22-14-40` |
| S1.5 math | 16/20 (80%) | `outputs/2026-03-17/01-21-21` |
| S1.5 code | 11/16† (69%) | `outputs/2026-03-17/01-22-15` |
| S1.5 database | 10/25 (40%) | `outputs/2026-03-17/01-27-14` |
| S1.5 actions | 7/23 (30%) | `outputs/2026-03-17/01-28-09` |
| S1.5+mem math | 17/20 (85%) | `outputs/2026-03-17/01-28-32` |
| S1.5+mem code | 12/17† (71%) | `outputs/2026-03-17/01-29-56` |
| S1.5+mem database | 9/25 (36%) | `outputs/2026-03-17/01-34-55` |
| S1.5+mem actions | 7/23 (30%) | `outputs/2026-03-17/01-35-29` |

## Open Questions for Parallel Branches

### Branch 1: Improve Memory Gains
- Memory helps S1 (80→90% math, 56→68% code, 32→44% database) but hurts S2 and is inconsistent with S1.5
- The cheatsheet (~1000 words) dilutes analyzer attention in S2/S1.5 where the analysis drives a binary decision
- Potential directions: cap at ~500 words, restructure to be more concise, separate memory targets for task spec vs comparison queries, or only apply memory to the task spec query (not comparison)

### Branch 2: Single-Query Analysis Ablation
- Current v8 uses two queries: (1) task spec from user messages + system message, (2) comparison of task spec against conversation
- Question: can a single query that combines both steps match or exceed two-query performance?
- The two-query approach costs 2x LLM calls per turn — if a single query matches, it halves the cost
- The task spec is clearly the highest-leverage component; does the comparison query add enough value to justify the second call?

## Git State

Branch: `newleaf2`
Latest commit: `5c04385` (S1.5 evaluation fixes)
All experimental changes committed.
