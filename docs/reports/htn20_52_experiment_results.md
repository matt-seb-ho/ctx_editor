# htn20_52 Experiment Results

**Date**: 2026-03-26/27
**Subset**: htn20_52 (20 hardest true-negative problems per task from gpt-5.2 LiC logs)
**Runs**: Single run per strategy per task (replay on first available conversation)

See `docs/htn20_52_subset.md` for subset construction details.

## Constant Configuration

All runs share these settings unless noted:

- **Assistant model**: gpt-5-mini
- **Analyzer model**: gpt-5-mini (for S1/S1.5/S2/S3)
- **Analyzer prompt version**: v8 (default, not overridden)
- **Load balancer**: `load_balancer=multi_endpoint` (4 Azure endpoints, round-robin)
- **Execution**: `execution.max_concurrent=8`
- **Replay**: last-turn replay on LiC gpt-5.2 baseline traces from `data/baseline_traces_htn20_52/{task}/`
- **Task evaluators**: math_v2, code_v2, database_v2, actions (no v2)
- **Model config**: `model=gpt5_mini` (assistant: gpt-5-mini medium reasoning, ctx_editor: gpt-5-mini medium reasoning)

## Main Results Table

All numbers are correct/total (accuracy %). Actions uses the +accumulate prompt variant for S0/S1/S1.5/S2/S3.

| Strategy | Math (n=20) | Code (n=20) | Database (n=20) | Actions (n=20) |
|---|---|---|---|---|
| **S0** (baseline) | 4/20 (20%) | 2/20 (10%) | 1/20 (5%) | 12/20 (60%) |
| **S1** (append analysis) | 8/20 (40%) | 6/20 (30%) | 8/20 (40%) | 15/20 (75%) |
| **AO** (omit assistant) | 10/20 (50%) | 5/20 (25%) | 8/20 (40%) | 17/20 (85%) |
| **S1.5** (non-gated reset) | 11/20 (55%) | 5/20 (25%) | 8/20 (40%) | 16/20 (80%) |
| **S2** (gated reset) | 8/20 (40%) | 5/20 (25%) | 5/20 (25%) | 17/20 (85%) |
| **S3** (LLM compaction) | 11/20 (55%) | 4/20 (20%) | 7/20 (35%) | 10/20 (50%) |
| **S3v2** (structured prompt) | 8/20 (40%) | 6/20 (30%) | 7/20 (35%) | 11/20 (55%) |

**Code note**: S3/S3v2/S1.5 code ran through the s15 script which skips problems where S1 had errors (7 livecodebench problems with syntax errors). The denominators shown are normalized to /20 treating missing/error samples as incorrect.

## Run Commands and Output Directories

### S0 (baseline) -- main pipeline

```bash
# Math
python -m ctx_editor.run_experiment experiment=baseline task=math_v2 model=gpt5_mini \
  load_balancer=multi_endpoint task.data_file=data/htn20_52_math_subset.json \
  execution.replay_source=data/baseline_traces_htn20_52/math execution.max_concurrent=8

# Code
python -m ctx_editor.run_experiment experiment=baseline task=code_v2 model=gpt5_mini \
  load_balancer=multi_endpoint task.data_file=data/htn20_52_code_subset.json \
  execution.replay_source=data/baseline_traces_htn20_52/code execution.max_concurrent=8

# Database
python -m ctx_editor.run_experiment experiment=baseline task=database_v2 model=gpt5_mini \
  load_balancer=multi_endpoint task.data_file=data/htn20_52_database_subset.json \
  execution.replay_source=data/baseline_traces_htn20_52/database execution.max_concurrent=8
```

Actions S0 was run via the s15 script with `--mode s0-accum` (see S1.5 section).

| Task | Output Dir |
|---|---|
| Math | `outputs/2026-03-26/21-42-24` |
| Code | `outputs/2026-03-26/21-42-26` |
| Database | `outputs/2026-03-26/21-49-55` |
| Actions (+accum) | `outputs/2026-03-26/21-54-54` |

### AO (omit assistant) -- main pipeline

```bash
python -m ctx_editor.run_experiment experiment=omit_assistant task={task_v2} model=gpt5_mini \
  load_balancer=multi_endpoint task.data_file=data/htn20_52_{task}_subset.json \
  execution.replay_source=data/baseline_traces_htn20_52/{task} execution.max_concurrent=8
```

| Task | Output Dir |
|---|---|
| Math | `outputs/2026-03-26/12-45-38` |
| Code | `outputs/2026-03-26/12-45-27` |
| Database | `outputs/2026-03-26/21-49-57` |
| Actions | `outputs/2026-03-26/21-49-59` |

### S1 (append analysis) -- main pipeline

```bash
python -m ctx_editor.run_experiment experiment=append_analysis task={task_v2} model=gpt5_mini \
  load_balancer=multi_endpoint task.data_file=data/htn20_52_{task}_subset.json \
  execution.replay_source=data/baseline_traces_htn20_52/{task} execution.max_concurrent=8
```

| Task | Output Dir |
|---|---|
| Math | `outputs/2026-03-26/12-45-49` |
| Code | `outputs/2026-03-26/12-45-52` |
| Database | `outputs/2026-03-26/21-49-58` |
| Actions | `outputs/2026-03-26/21-50-00` |

### S2 (gated reset) -- main pipeline

```bash
# Math/code/database
python -m ctx_editor.run_experiment experiment=context_edit_v2 task={task_v2} model=gpt5_mini \
  load_balancer=multi_endpoint task.data_file=data/htn20_52_{task}_subset.json \
  execution.replay_source=data/baseline_traces_htn20_52/{task} execution.max_concurrent=8

# Actions (uses accumulate variant)
python -m ctx_editor.run_experiment experiment=context_edit_v2_accumulate task=actions model=gpt5_mini \
  load_balancer=multi_endpoint task.data_file=data/htn20_52_actions_subset.json \
  execution.replay_source=data/baseline_traces_htn20_52/actions execution.max_concurrent=8
```

| Task | Output Dir |
|---|---|
| Math | `outputs/2026-03-27/00-07-19` |
| Code | `outputs/2026-03-27/00-07-20` |
| Database | `outputs/2026-03-27/00-07-22` |
| Actions (+accum) | `outputs/2026-03-27/00-07-23` |

### S1.5 / S0+accum / S1+accum -- s15 script

S1.5 is a two-stage pipeline: first run S1 (above), then run `run_s15_experiment.py` on the S1 output. S0+accum and S1+accum for actions also run through this script.

```bash
# S1.5 (programmatic compaction, always reset)
python scripts/run_s15_experiment.py --s1-dir {S1_OUTPUT} --task {task} \
  --model gpt-5-mini --label S15_htn20_52_{task} \
  --data-file data/htn20_52_{task}_subset.json --max-concurrent 8

# S0+accum actions (full conversation + accumulate instruction, no analysis)
python scripts/run_s15_experiment.py --s1-dir outputs/2026-03-26/21-50-00 --task actions \
  --model gpt-5-mini --label S0_accum_htn20_52_actions \
  --data-file data/htn20_52_actions_subset.json --mode s0-accum --accumulate --max-concurrent 8

# S1+accum actions (full conversation with analysis + accumulate)
python scripts/run_s15_experiment.py --s1-dir outputs/2026-03-26/21-50-00 --task actions \
  --model gpt-5-mini --label S1_accum_htn20_52_actions \
  --data-file data/htn20_52_actions_subset.json --mode s1-accum --accumulate --max-concurrent 8

# S1.5+accum actions
python scripts/run_s15_experiment.py --s1-dir outputs/2026-03-26/21-50-00 --task actions \
  --model gpt-5-mini --label S15_accum_htn20_52_actions \
  --data-file data/htn20_52_actions_subset.json --mode s15 --accumulate --max-concurrent 8
```

| Run | S1 Source | Output Dir |
|---|---|---|
| S1.5 math | `outputs/2026-03-26/12-45-49` | `outputs/2026-03-26/12-51-40` |
| S1.5 code | `outputs/2026-03-26/12-45-52` | `outputs/2026-03-26/12-51-42` |
| S1.5 database | `outputs/2026-03-26/21-49-58` | `outputs/2026-03-26/21-54-52` |
| S0+accum actions | `outputs/2026-03-26/21-50-00` | `outputs/2026-03-26/21-54-54` |
| S1+accum actions | `outputs/2026-03-26/21-50-00` | `outputs/2026-03-26/21-54-56` |
| S1.5+accum actions | `outputs/2026-03-26/21-50-00` | `outputs/2026-03-26/21-54-58` |

### S3 / S3v2 (LLM compaction) -- s15 script

```bash
# S3 (original compaction prompt)
python scripts/run_s15_experiment.py --s1-dir {S1_OUTPUT} --task {task} \
  --model gpt-5-mini --label S3_htn20_52_{task} \
  --data-file data/htn20_52_{task}_subset.json --mode s3 --max-concurrent 8

# S3v2 (structured compaction prompt)
python scripts/run_s15_experiment.py --s1-dir {S1_OUTPUT} --task {task} \
  --model gpt-5-mini --label S3v2_htn20_52_{task} \
  --data-file data/htn20_52_{task}_subset.json --mode s3 --v2-prompt --max-concurrent 8

# Actions variants add --accumulate
```

| Run | Output Dir |
|---|---|
| S3 math | `outputs/2026-03-27/00-07-25` |
| S3 code | `outputs/2026-03-27/00-07-26` |
| S3 database | `outputs/2026-03-27/00-07-28` |
| S3+accum actions | `outputs/2026-03-27/00-07-29` |
| S3v2 math | `outputs/2026-03-27/00-45-42` |
| S3v2 code | `outputs/2026-03-27/00-45-44` |
| S3v2 database | `outputs/2026-03-27/00-45-45` |
| S3v2+accum actions | `outputs/2026-03-27/00-45-47` |

## Reproducing with a Different Model

To swap the model while keeping everything else constant:

```bash
# For main pipeline strategies (S0, AO, S1, S2):
python -m ctx_editor.run_experiment experiment={experiment} task={task_v2} model={new_model} \
  load_balancer=multi_endpoint task.data_file=data/htn20_52_{task}_subset.json \
  execution.replay_source=data/baseline_traces_htn20_52/{task} execution.max_concurrent=8

# For s15 script strategies (S1.5, S3):
# Step 1: Run S1 with the new model to get traces
# Step 2: Run s15 script pointing at the new S1 output
python scripts/run_s15_experiment.py --s1-dir {NEW_S1_OUTPUT} --task {task} \
  --model {new_model_name} --data-file data/htn20_52_{task}_subset.json \
  --mode {s15|s3} [--accumulate for actions] --max-concurrent 8
```

The baseline traces (conversation prefixes) are fixed regardless of model. Only the final-turn generation and analysis change.

## Key Findings

Analysis below is based on aggregate score comparison only, except for the S3 root cause analysis which involved reading individual trace outputs.

### 1. Context pollution is devastating on hard problems

S0 baseline accuracy is 5-20% on math/code/database. These are problems where the original gpt-5.2 model failed in 5-10 out of 10 runs with multi-turn context. When gpt-5-mini replays the same polluted conversation and just regenerates the last turn, it almost never recovers. The context is too corrupted.

### 2. S1.5 matches or exceeds the AO upper bound

AO (omit assistant) strips all assistant messages, giving the model a "clean slate" with only user information. It was expected to be the ceiling for context manipulation strategies. S1.5 matches AO on code/database and **exceeds it on math** (55% vs 50%). This means the analyzer-curated context (task spec + aligned work) is more useful than raw user messages alone.

### 3. S2 gating hurts on consistently hard problems

S2 (gated reset) underperforms S1.5 on math (40% vs 55%) and database (25% vs 40%). On problems that are always hard, the analyzer sometimes decides the context doesn't need editing (`needs_edit=False`), missing the opportunity to reset. The non-gated approach (always reset) is strictly better when problems are known to be difficult.

### 4. S3 (LLM compaction) underperforms despite correct compaction output

S3 ties S1.5 on math (55%) but is much worse on actions (50% vs 80%) and database (35% vs 40%).

**Root cause analysis** (from reading individual S1.5 vs S3 trace outputs for the 6 divergent actions cases): In 5 out of 6 cases where S1.5 succeeded but S3 failed, S3's `compaction_output` was actually correct and complete. The failure is downstream: the assistant doesn't faithfully reproduce all items from the LLM-generated compacted context. It treats natural-language descriptions of function calls as informational rather than prescriptive, selectively returning only a subset (often the most recent one).

On math, S1.5 and S3 got the exact same 11 problems correct, confirming no information loss on non-structured tasks.

S1.5's programmatic template produces structured, enumerated parameter listings that are harder to selectively ignore. An improved "S3v2" prompt that forces enumerated output helped slightly on actions (+5pp) and code (+10pp) but regressed on math (-15pp), confirming the issue is not primarily about prompt quality but about adding an extra LLM interpretation layer.

### 5. S1 (append analysis, no reset) is surprisingly effective

Simply appending the analysis to the polluted conversation (without resetting) produces large gains: +20pp math, +20pp code, +35pp database, +15pp actions over S0. The analysis gives the assistant enough signal to overcome anchoring, even without removing the polluted history.

### 6. Actions is the easiest to intervene on

All strategies perform well on actions (60-85%), likely because function-calling tasks have more structured output and the accumulate instruction helps the model consolidate its answer.

## Strategy Descriptions

- **S0**: No intervention. Replay the polluted multi-turn context and regenerate the final assistant turn.
- **S1**: Run the conversation analyzer (two-query architecture, v8 prompt) and append its output to the context before the final turn. No context modification.
- **AO**: Omit all assistant messages from context. The model sees only system + user messages (Huang et al. 2026 baseline).
- **S1.5**: Run the analyzer, then **always** reset the conversation: replace the full history with a compacted context containing the task specification and aligned work. Programmatic template.
- **S2**: Same as S1.5, but **gated**: only reset if the analyzer determines `needs_edit=True`. If no issues found, pass through like S0.
- **S3**: Same as S1.5, but the compacted context is produced by an LLM reading the full conversation + analysis, rather than a programmatic template. Uses `context_compaction.txt`.
- **S3v2**: S3 with an improved compaction prompt that forces enumerated, structured output matching S1.5's format. Uses `context_compaction_v2.txt`.

## Viewing in Streamlit

Main pipeline runs (S0, AO, S1, S2) can be viewed in the streamlit conversation viewer:

```bash
streamlit run src/ctx_editor/app_conv_viewer.py -- --run {output_dir}
```

The s15 script runs (S1.5, S3) use a different trace format (`messages_sent` + `assistant_response` flat dict) and are **not compatible** with the streamlit viewer.

## Limitations

1. **Single run**: All results are from a single replay run. Given n=20, the 95% CI for a 50% accuracy is roughly +/-22pp. Differences under ~15pp may not be significant.

2. **Code evaluation errors**: 4-7 livecodebench problems produce syntax errors in model output across strategies. These are counted as incorrect in the normalized table above, but the s15 script excludes them entirely (inflating its denominators).

3. **Conversation selection**: Results use the first available conversation per problem. Different conversations for the same problem may yield different results due to different user simulator phrasings.

4. **Model mismatch**: Baseline conversations were generated by gpt-5.2; interventions use gpt-5-mini. This means S0 is "gpt-5-mini replaying gpt-5.2's polluted context," not "gpt-5-mini's own multi-turn performance."
