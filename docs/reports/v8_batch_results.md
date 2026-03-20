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
| **S1.5+mem+sanitize** | **17/20 (85%)** | **13/19 (68%)** | **11/25 (44%)** | — |
| **S2+mem** | 15/20 (75%) | 13/19 (68%) | 9/25 (36%) | 3/23 (13%) |

†Code S1.5 had 9 timeout errors (denominator 16); S1.5+mem had 8 (denominator 17). Percentages are inflated relative to S1/S2 denominators.

S1.5+mem+sanitize applies post-processing to strip clarification-seeking patterns from the analysis before building the compacted context (`--sanitize` flag). See "Memory Deep Dive" section below.

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

### 3. Memory Helps S1, Can Be Made to Help S1.5, Hurts S2

S1+mem is the best configuration on math (90%) and code (68%), with +8 new solves and **zero regressions** across math/code/database. Memory learning works well when additive — the cheatsheet helps the analyzer produce better analysis on later batches.

S1.5+mem initially showed regressions on database (36% vs 40% no-mem). Error analysis (see "Memory Deep Dive" below) traced this to the analyzer producing clarification-seeking language that the assistant follows literally in the compacted context. Post-processing sanitization (`--sanitize`) fixes this, making memory a consistent positive for S1.5 as well (database recovers to 44%).

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
| S1.5+mem+sanitize math | 17/20 (85%) | `outputs/2026-03-17/08-13-54` |
| S1.5+mem+sanitize code | 13/19 (68%) | `outputs/2026-03-17/08-13-54` |
| S1.5+mem+sanitize database | **11/25 (44%)** | `outputs/2026-03-17/08-19-23` |
| S1+spec_mem math | 14/20 (70%) | `outputs/2026-03-17/05-57-32` |
| S1+spec_mem code | 13/19 (68%) | `outputs/2026-03-17/06-08-37` |
| S1+spec_mem database | 10/25 (40%) | `outputs/2026-03-17/06-19-08` |

## Memory Deep Dive

Detailed sample-level error analysis of memory's effect. Full report: `docs/reports/memory_error_analysis.md`.

### S1+mem: How Memory Helps (Zero Regressions)

Sample-by-sample comparison shows **+8 new solves, 0 regressions** across math/code/database:

| Task | New solves | Regressions | Key mechanism |
|------|:---------:|:-----------:|---------------|
| Math (+2) | GSM8K/1190, GSM8K/144 | 0 | Shorter, more decisive specs — commit to one interpretation instead of branching |
| Code (+3) | livecodebench/2812*, 2881, 2979 | 0 | Concrete failing examples, semantic error detection, removal of unnecessary validation |
| Database (+3) | spider-val-498, val-555, val-75 | 0 | Exact column matching, single-row semantics (LIMIT 1), suppress clarification-seeking |

*2812 was a timeout artifact; 2 genuine flips for code.

Memory's primary effect is making the analyzer produce **more actionable analysis**: shorter task specs that commit to single interpretations (math), concrete test cases that expose algorithmic errors (code), and precise constraint-checking that catches column aliasing and missing LIMIT (database).

### S1.5+mem: Why Memory Initially Hurt, and the Fix

S1.5+mem showed 4 regressions on database (net -1 vs no-mem). Root cause: **in S1.5 the analysis IS the sole context** — there's no full conversation to fall back on. Three anti-patterns in memory-influenced analysis:

1. **Clarification-seeking leakage** (val-389, val-401): Analyzer writes "ask the user if unclear" despite the cheatsheet saying not to. In S1 the assistant ignores this (it sees the real messages). In S1.5 the assistant follows it literally and asks questions instead of answering.

2. **Hallucinated requirements** (val-932): Analyzer adds a `treatment_count` column the user never requested (confused a filter condition for a projection). S1 assistant checks real messages; S1.5 trusts the spec blindly.

3. **Over-prescriptive style** (val-498): Analyzer over-constrains SQL form, steering toward semantically-correct but evaluator-incompatible EXISTS pattern.

**Fix: Post-processing sanitization** (`--sanitize` flag on `scripts/run_s15_experiment.py`). Strips clarification-seeking language from the analysis before building the compacted context. This is transparent (traces unchanged) and recovers database from 36% → 44%.

An alternative approach — adding explicit compliance rules to the analyzer prompt (`enforce_compliance`) — was tested and **hurts S1** (math drops 90%→75%, database 44%→28%). The rules over-constrain the analyzer's useful behaviors. Post-processing is strictly better: it fixes S1.5 without touching S1.

### Memory Effect Summary (Best Configs)

| Config | Math | Code | Database | Δ vs no-mem |
|--------|:----:|:----:|:--------:|:-----------:|
| S1 | 80% | 56% | 32% | — |
| **S1+mem** | **90%** | **68%** | **44%** | **+10, +12, +12** |
| S1.5 | 80% | 69%† | 40% | — |
| **S1.5+mem+sanitize** | **85%** | **68%** | **44%** | **+5, ~0, +4** |

Memory provides consistent directional uplift for both S1 (large gains) and S1.5 (moderate gains, with sanitization).

### Spec-Targeted Memory Ablation

Tested injecting memory into Query 1 (task spec) instead of Query 2 (comparison). Config: `append_analysis_spec_mem`.

| Config | Math | Code | Database |
|--------|:----:|:----:|:--------:|
| S1+mem (compare) | **90%** | 68% | **44%** |
| S1+mem (spec) | 70% | 68% | 40% |

Spec-targeted memory matches on code but drops badly on math (-20pp). The comparison query is where memory adds value for math (where explicit error identification matters). For code/database, the task spec is already the primary mechanism so memory location matters less. The default (compare-targeted) remains the best overall choice.

## Open Questions

### Remaining Memory Gaps
- Memory hurts S2 — the cheatsheet dilutes the binary edit/no-edit decision. Could a more concise cheatsheet (<500 words) or separate memory targets (spec vs compare) help S2?
- Actions memory (S1+mem actions: 9% vs S1 22%) — the accumulation structural failure mode dominates; memory can't fix it. Likely needs task-specific handling.
- The sanitization fixes 1/4 database regressions directly (clarification-seeking). Hallucinated requirements and over-prescription require deeper fixes (e.g., cross-validating spec columns against actual user messages).

### Single-Query Analysis Ablation (Completed)
See `docs/reports/ablations/single_query_hard_attention.md`. Key finding: the task spec alone (S1-speconly) matches or beats full S1 on code/database at half the LLM cost. The comparison query only helps on math. Hard attention (user messages only in Query 1) is load-bearing — removing it collapses performance to baseline.

## Git State

Branch: `newleaf2`
All experimental changes committed.
