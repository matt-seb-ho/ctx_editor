# Post-NeurIPS LiC Vanilla Baseline Runs

**Started**: 2026-05-16T06:36:23-07:00
**Strategy**: baseline (no context modification)
**User simulator**: gpt-4o-mini
**Subset**: htn50_52 (50/44/50/50 problems for math/code/database/actions)
**Runs per (model, domain)**: 3 sequential ctx-editor invocations
**User mode**: sharded (LiC-identical)
**Task evaluators**: math_v2, code_v2, database_v2, actions_v2 (new, includes 'accumulate' instruction)

## Models

| Model | Config | Endpoint pool | Per-model RPM cap |
|---|---|---|---|
| gpt-5.4 | `gpt5_4` | OpenAI (dl-openai-1/3) | 10000 / 2500 |
| DeepSeek-V4-Flash | `deepseek_v4_flash_foundry` | Foundry (mgalley-foundry2) | 250 |
| Kimi-K2.6 | `kimi_k2_6_foundry` | Foundry (mgalley-foundry2) | 100 |
| gpt-5.5 | `gpt5_5_foundry` | Foundry (mgalley-foundry2) | 250 |

Phi-4 was excluded — its Foundry quota is 1 RPM, making the matrix infeasible.

## Run commands

The full matrix was launched by `scripts/run_post_neurips_lic_vanilla.sh all`,
which runs four parallel pipelines (one per model). Each pipeline issues 12
sequential `ctx-editor` invocations (4 domains × 3 runs). The bare-bones form
of a single invocation is:

```bash
ctx-editor experiment=baseline \
    model={gpt5_4|deepseek_v4_flash_foundry|kimi_k2_6_foundry|gpt5_5_foundry} \
    task={math_v2|code_v2|database_v2|actions_v2} \
    task.data_file=data/htn50_52_{math|code|database|actions}_subset.json \
    user_mode=sharded \
    load_balancer={multi_endpoint|multi_endpoint_foundry} \
    execution.max_concurrent={30|20} \
    experiment_name=baseline_sharded_{model}_{task}_run{i} \
    logging.output_dir=outputs/post_neurips_lic_vanilla_redo/{exp_name}_{epoch}
```

The `logging.output_dir` override is **important**: without it, multiple
parallel pipelines that start in the same second collide on the default
Hydra path (see `## Caveats` below).

Re-runs (for code data-bug fixes and the math run-1 collision) live in
`scripts/run_post_neurips_lic_vanilla_code_redo.sh` and `/tmp/redo_math_run1.sh`.

## Caveats and audit trail

Two correctness issues affected portions of the original matrix; both were
identified and resolved via re-runs.

1. **Code & database subsets were missing task-execution fields** (e.g.
   `function`/`reference_answer` for actions, `public_test_cases`/`metadata`
   for HumanEval, `db_id`/`schema_sql` for SQL). The htn50_52 subsets had
   been built for replay-mode experiments and dropped fields that fresh
   sharded simulations need. Fixed by enriching from
   `data/sharded_instructions_600.json` (commits `534a44b`, `7de964e`,
   `10cd44d`). Code runs launched before the fix are marked
   `(tainted, replaced)` in the per-cell table and replaced by `redo*`
   counterparts (commit-fix timestamp ≈ 06:53–06:58 PT).

2. **Math run-1 output-directory collision.** All four model pipelines were
   launched in the same second (06:40:46), so Hydra's default
   `outputs/{date}/{HH-MM-SS}/` resolved to the same path for every run.
   The trace files and `metrics.json` in `outputs/2026-05-16/06-40-47/`
   were sequentially overwritten; only the last finisher (Kimi-K2.6)
   survives in that directory. Per-run accuracy values for the three other
   models were captured by the launcher *before* the overwrite, so the
   numbers reported here are correct (sourced from the captured stdout in
   `outputs/post_neurips_lic_vanilla/logs/*__math_v2__run1.log`), but the
   trace files for gpt-5.4 / DeepSeek-V4-Flash / gpt-5.5 in 06-40-47 cannot
   be inspected. Math run-1 for the three affected models was re-issued
   into unique output directories under
   `outputs/post_neurips_lic_vanilla_redo/`. Future runs of
   `run_post_neurips_lic_vanilla.sh` should pass `logging.output_dir` per
   invocation to prevent this class of collision.

## Per-run table

Each row = one ctx-editor invocation. Same (model, domain) appears 3× with different run_idx.
Aggregate "(model, domain) means over the N runs" lives below.

| Started | Model | Task | Run | rc | Wall | Accuracy | Cost | Avg Turns | Output Dir | Log |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-05-16T06:40:46-07:00 | deepseek_v4_flash_foundry | math_v2 | 1 | 0 | 178s | 66.00% (33/50) | $0.0714 | 5.5 | `outputs/2026-05-16/06-40-47` | `deepseek_v4_flash_foundry__math_v2__run1.log` |
| 2026-05-16T06:40:46-07:00 | gpt5_4 | math_v2 | 1 | 0 | 224s | 80.00% (40/50) | $0.8610 | 5.4 | `outputs/2026-05-16/06-40-47` | `gpt5_4__math_v2__run1.log` |
| 2026-05-16T06:43:44-07:00 | deepseek_v4_flash_foundry | math_v2 | 2 | 0 | 114s | 73.47% (36/49)  (1 errors excluded) | $0.0650 | 5.3 | `outputs/2026-05-16/06-43-45` | `deepseek_v4_flash_foundry__math_v2__run2.log` |
| 2026-05-16T06:40:46-07:00 | gpt5_5_foundry | math_v2 | 1 | 0 | 401s | 82.00% (41/50) | $0.6284 | 5.3 | `outputs/2026-05-16/06-40-47` | `gpt5_5_foundry__math_v2__run1.log` |
| 2026-05-16T06:45:38-07:00 | deepseek_v4_flash_foundry | math_v2 | 3 | 0 | 146s | 76.00% (38/50) | $0.0716 | 5.5 | `outputs/2026-05-16/06-45-39` | `deepseek_v4_flash_foundry__math_v2__run3.log` |
| 2026-05-16T06:44:30-07:00 | gpt5_4 | math_v2 | 2 | 0 | 222s | 74.00% (37/50) | $0.8910 | 5.5 | `outputs/2026-05-16/06-44-31` | `gpt5_4__math_v2__run2.log` |
| 2026-05-16T06:47:27-07:00 | gpt5_5_foundry | math_v2 | 2 | 0 | 148s | 81.63% (40/49)  (1 errors excluded) | $0.7000 | 5.5 | `outputs/2026-05-16/06-47-28` | `gpt5_5_foundry__math_v2__run2.log` |
| 2026-05-16T06:40:46-07:00 | kimi_k2_6_foundry | math_v2 | 1 | 0 | 604s | 73.47% (36/49)  (1 errors excluded) | $0.0716 | 5.5 | `outputs/2026-05-16/06-40-47` | `kimi_k2_6_foundry__math_v2__run1.log` |
| 2026-05-16T06:48:04-07:00 | deepseek_v4_flash_foundry | code_v2 | 1 | 0 | 192s | 31.58% (6/19)  (25 errors excluded) | $0.0386 | 6.2 | `outputs/2026-05-16/06-48-05` | `deepseek_v4_flash_foundry__code_v2__run1.log` |
| 2026-05-16T06:48:12-07:00 | gpt5_4 | math_v2 | 3 | 0 | 210s | 76.00% (38/50) | $0.9209 | 5.4 | `outputs/2026-05-16/06-48-13` | `gpt5_4__math_v2__run3.log` |
| 2026-05-16T06:49:55-07:00 | gpt5_5_foundry | math_v2 | 3 | 0 | 171s | 72.34% (34/47)  (3 errors excluded) | $0.6619 | 5.5 | `outputs/2026-05-16/06-49-55` | `gpt5_5_foundry__math_v2__run3.log` |
| 2026-05-16T06:51:17-07:00 | deepseek_v4_flash_foundry | code_v2 | 2 | 0 | 161s | 33.33% (6/18)  (26 errors excluded) | $0.0407 | 6.6 | `outputs/2026-05-16/06-51-17` | `deepseek_v4_flash_foundry__code_v2__run2.log` |
| 2026-05-16T06:51:42-07:00 | gpt5_4 | code_v2 | 1 | 0 | 206s | 52.38% (11/21)  (23 errors excluded) | $0.5845 | 4.7 | `outputs/2026-05-16/06-51-43` | `gpt5_4__code_v2__run1.log` |
| 2026-05-16T06:52:46-07:00 | gpt5_5_foundry | code_v2 | 1 | 0 | 169s | 70.59% (12/17)  (27 errors excluded) | $0.3394 | 3.8 | `outputs/2026-05-16/06-52-47` | `gpt5_5_foundry__code_v2__run1.log` |
| 2026-05-16T06:53:58-07:00 | deepseek_v4_flash_foundry | code_v2 | 3 | 0 | 260s | 38.71% (12/31)  (13 errors excluded) | $0.0501 | 5.2 | `outputs/2026-05-16/06-53-58` | `deepseek_v4_flash_foundry__code_v2__run3.log` |
| 2026-05-16T06:55:08-07:00 | gpt5_4 | code_v2 | 2 | 0 | 221s | 64.52% (20/31)  (13 errors excluded) | $0.8192 | 4.3 | `outputs/2026-05-16/06-55-09` | `gpt5_4__code_v2__run2.log` |
| 2026-05-16T06:55:35-07:00 | gpt5_5_foundry | code_v2 | 2 | 0 | 201s | 63.33% (19/30)  (14 errors excluded) | $0.4800 | 3.9 | `outputs/2026-05-16/06-55-35` | `gpt5_5_foundry__code_v2__run2.log` |
| 2026-05-16T06:50:50-07:00 | kimi_k2_6_foundry | math_v2 | 2 | 0 | 622s | 76.00% (38/50) | $0.0717 | 5.4 | `outputs/2026-05-16/06-50-51` | `kimi_k2_6_foundry__math_v2__run2.log` |
| 2026-05-16T06:58:56-07:00 | gpt5_5_foundry | code_v2 | 3 | 0 | 149s | 79.55% (35/44) | $0.7444 | 3.3 | `outputs/2026-05-16/06-58-57` | `gpt5_5_foundry__code_v2__run3.log` |
| 2026-05-16T06:58:18-07:00 | deepseek_v4_flash_foundry | database_v2 | 1 | 0 | 234s | 22.00% (11/50) | $0.0489 | 4.3 | `outputs/2026-05-16/06-58-19` | `deepseek_v4_flash_foundry__database_v2__run1.log` |
| 2026-05-16T06:58:49-07:00 | gpt5_4 | code_v2 | 3 | 0 | 325s | 61.36% (27/44) | $0.9741 | 3.8 | `outputs/2026-05-16/06-58-49` | `gpt5_4__code_v2__run3.log` |
| 2026-05-16T07:02:12-07:00 | deepseek_v4_flash_foundry | database_v2 | 2 | 0 | 189s | 34.00% (17/50) | $0.0483 | 4.2 | `outputs/2026-05-16/07-02-13` | `deepseek_v4_flash_foundry__database_v2__run2.log` |
| 2026-05-16T07:04:14-07:00 | gpt5_4 | database_v2 | 1 | 0 | 238s | 20.41% (10/49)  (1 errors excluded) | $0.6914 | 4.2 | `outputs/2026-05-16/07-04-15` | `gpt5_4__database_v2__run1.log` |
| 2026-05-16T07:05:21-07:00 | deepseek_v4_flash_foundry | database_v2 | 3 | 0 | 210s | 18.00% (9/50) | $0.0478 | 4.2 | `outputs/2026-05-16/07-05-22` | `deepseek_v4_flash_foundry__database_v2__run3.log` |
| 2026-05-16T07:01:25-07:00 | gpt5_5_foundry | database_v2 | 1 | 0 | 498s | 16.00% (8/50) | $0.6204 | 4.2 | `outputs/2026-05-16/07-01-26` | `gpt5_5_foundry__database_v2__run1.log` |
| 2026-05-16T07:08:52-07:00 | deepseek_v4_flash_foundry | actions_v2 | 1 | 0 | 94s | 81.63% (40/49)  (1 errors excluded) | $0.0539 | 5.1 | `outputs/2026-05-16/07-08-52` | `deepseek_v4_flash_foundry__actions_v2__run1.log` |
| 2026-05-16T07:08:12-07:00 | gpt5_4 | database_v2 | 2 | 0 | 228s | 20.00% (10/50) | $0.6859 | 4.3 | `outputs/2026-05-16/07-08-13` | `gpt5_4__database_v2__run2.log` |
| 2026-05-16T07:09:43-07:00 | gpt5_5_foundry | database_v2 | 2 | 0 | 258s | 14.00% (7/50) | $0.6639 | 4.3 | `outputs/2026-05-16/07-09-44` | `gpt5_5_foundry__database_v2__run2.log` |
| 2026-05-16T07:10:26-07:00 | deepseek_v4_flash_foundry | actions_v2 | 2 | 0 | 235s | 74.00% (37/50) | $0.0595 | 5.5 | `outputs/2026-05-16/07-10-27` | `deepseek_v4_flash_foundry__actions_v2__run2.log` |
| 2026-05-16T07:12:00-07:00 | gpt5_4 | database_v2 | 3 | 0 | 227s | 20.00% (10/50) | $0.7325 | 4.3 | `outputs/2026-05-16/07-12-01` | `gpt5_4__database_v2__run3.log` |
| 2026-05-16T07:14:21-07:00 | deepseek_v4_flash_foundry | actions_v2 | 3 | 0 | 128s | 70.00% (35/50) | $0.0552 | 5.1 | `outputs/2026-05-16/07-14-22` | `deepseek_v4_flash_foundry__actions_v2__run3.log` |
| 2026-05-16T07:15:47-07:00 | gpt5_4 | actions_v2 | 1 | 0 | 103s | 87.76% (43/49)  (1 errors excluded) | $0.6416 | 5.2 | `outputs/2026-05-16/07-15-48` | `gpt5_4__actions_v2__run1.log` |
| 2026-05-16T07:14:01-07:00 | gpt5_5_foundry | database_v2 | 3 | 0 | 270s | 10.00% (5/50) | $0.7014 | 4.4 | `outputs/2026-05-16/07-14-02` | `gpt5_5_foundry__database_v2__run3.log` |
| 2026-05-16T07:17:30-07:00 | gpt5_4 | actions_v2 | 2 | 0 | 104s | 85.42% (41/48)  (2 errors excluded) | $0.6386 | 5.2 | `outputs/2026-05-16/07-17-31` | `gpt5_4__actions_v2__run2.log` |
| 2026-05-16T07:19:14-07:00 | gpt5_4 | actions_v2 | 3 | 0 | 103s | 90.00% (45/50) | $0.6727 | 5.2 | `outputs/2026-05-16/07-19-15` | `gpt5_4__actions_v2__run3.log` |
| 2026-05-16T07:18:31-07:00 | gpt5_5_foundry | actions_v2 | 1 | 0 | 346s | 90.00% (45/50) | $0.5737 | 5.1 | `outputs/2026-05-16/07-18-32` | `gpt5_5_foundry__actions_v2__run1.log` |
| 2026-05-16T07:01:12-07:00 | kimi_k2_6_foundry | math_v2 | 3 | 0 | 1447s | 66.00% (33/50) | $0.0803 | 5.8 | `outputs/2026-05-16/07-01-12` | `kimi_k2_6_foundry__math_v2__run3.log` |
| 2026-05-16T07:24:17-07:00 | gpt5_5_foundry | actions_v2 | 2 | 0 | 125s | 85.42% (41/48)  (2 errors excluded) | $0.5565 | 5.3 | `outputs/2026-05-16/07-24-18` | `gpt5_5_foundry__actions_v2__run2.log` |
| 2026-05-16T07:26:22-07:00 | gpt5_5_foundry | actions_v2 | 3 | 0 | 376s | 89.58% (43/48)  (2 errors excluded) | $0.5513 | 5.2 | `outputs/2026-05-16/07-26-23` | `gpt5_5_foundry__actions_v2__run3.log` |
| 2026-05-16T07:25:19-07:00 | kimi_k2_6_foundry | code_v2 | 1 | 0 | 941s | 68.18% (30/44) | $0.0451 | 3.9 | `outputs/2026-05-16/07-25-20` | `kimi_k2_6_foundry__code_v2__run1.log` |
| 2026-05-16T07:41:00-07:00 | kimi_k2_6_foundry | code_v2 | 2 | 0 | 535s | 77.27% (34/44) | $0.0403 | 3.6 | `outputs/2026-05-16/07-41-01` | `kimi_k2_6_foundry__code_v2__run2.log` |
| 2026-05-16T07:49:55-07:00 | kimi_k2_6_foundry | code_v2 | 3 | 0 | 725s | 61.36% (27/44) | $0.0437 | 3.8 | `outputs/2026-05-16/07-49-56` | `kimi_k2_6_foundry__code_v2__run3.log` |
| 2026-05-16T08:02:00-07:00 | kimi_k2_6_foundry | database_v2 | 1 | 0 | 306s | 24.00% (12/50) | $0.0493 | 4.3 | `outputs/2026-05-16/08-02-01` | `kimi_k2_6_foundry__database_v2__run1.log` |
| 2026-05-16T08:07:06-07:00 | kimi_k2_6_foundry | database_v2 | 2 | 0 | 298s | 20.00% (10/50) | $0.0505 | 4.3 | `outputs/2026-05-16/08-07-06` | `kimi_k2_6_foundry__database_v2__run2.log` |
| 2026-05-16T08:12:04-07:00 | kimi_k2_6_foundry | database_v2 | 3 | 0 | 351s | 18.00% (9/50) | $0.0496 | 4.3 | `outputs/2026-05-16/08-12-04` | `kimi_k2_6_foundry__database_v2__run3.log` |
| 2026-05-16T08:17:55-07:00 | kimi_k2_6_foundry | actions_v2 | 1 | 0 | 319s | 83.67% (41/49)  (1 errors excluded) | $0.0598 | 5.5 | `outputs/2026-05-16/08-17-55` | `kimi_k2_6_foundry__actions_v2__run1.log` |
| 2026-05-16T08:23:14-07:00 | kimi_k2_6_foundry | actions_v2 | 2 | 0 | 216s | 90.00% (45/50) | $0.0572 | 5.2 | `outputs/2026-05-16/08-23-14` | `kimi_k2_6_foundry__actions_v2__run2.log` |
| 2026-05-16T08:26:50-07:00 | kimi_k2_6_foundry | actions_v2 | 3 | 0 | 242s | 92.00% (46/50) | $0.0601 | 5.4 | `outputs/2026-05-16/08-26-51` | `kimi_k2_6_foundry__actions_v2__run3.log` |

## Summary — Mean accuracy across 3 runs (best clean set)

| Model | math_v2 | code_v2 | database_v2 | actions_v2 |
|---|---|---|---|---|
| gpt-5.4 | 76.5% ± 2.8pp (n=3) | 66.7% ± 4.7pp (n=3) | 20.1% ± 0.2pp (n=3) | 87.7% ± 2.3pp (n=3) |
| DeepSeek-V4-Flash | 73.2% ± 3.0pp (n=3) | 40.2% ± 4.7pp (n=3) | 24.7% ± 8.3pp (n=3) | 75.2% ± 5.9pp (n=3) |
| Kimi-K2.6 | 71.8% ± 5.2pp (n=3) | 68.9% ± 8.0pp (n=3) | 20.7% ± 3.1pp (n=3) | 88.6% ± 4.3pp (n=3) |
| gpt-5.5 | 78.0% ± 5.0pp (n=3) | 80.3% ± 1.3pp (n=3) | 13.3% ± 3.1pp (n=3) | 88.3% ± 2.5pp (n=3) |

## Per-(model, task) detail

| Model | Task | Run | Accuracy | Errors | Avg Turns | Cost (USD) | Output Dir |
|---|---|---|---|---|---|---|---|
| gpt-5.4 | math_v2 | 1 (extra) | 80.0% (40/50) | 0 | 5.4 | $0.86 | `outputs/2026-05-16/06-40-47 (overwritten — stats from launcher log)` |
| gpt-5.4 | math_v2 | 2 | 74.0% (37/50) | 0 | 5.5 | $0.89 | `outputs/2026-05-16/06-44-31` |
| gpt-5.4 | math_v2 | 3 | 76.0% (38/50) | 0 | 5.4 | $0.92 | `outputs/2026-05-16/06-48-13` |
| gpt-5.4 | math_v2 | redo1 (redo, used) | 79.6% (39/49) | 1 | 5.3 | $0.84 | `outputs/post_neurips_lic_vanilla_redo/baseline_sharded_gpt5_4_math_v2_redo1_1778946595` |
| gpt-5.4 | code_v2 | 1 (tainted, replaced) | 52.4% (11/21) | 23 | 4.7 | $0.58 | `outputs/2026-05-16/06-51-43` |
| gpt-5.4 | code_v2 | 2 (tainted, replaced) | 64.5% (20/31) | 13 | 4.3 | $0.82 | `outputs/2026-05-16/06-55-09` |
| gpt-5.4 | code_v2 | 3 | 61.4% (27/44) | 0 | 3.8 | $0.97 | `outputs/2026-05-16/06-58-49` |
| gpt-5.4 | code_v2 | redo1 (redo, used) | 68.2% (30/44) | 0 | 3.6 | $0.98 | `outputs/post_neurips_lic_vanilla_redo/baseline_sharded_gpt5_4_code_v2_redo1_1778945672` |
| gpt-5.4 | code_v2 | redo2 (redo, used) | 70.5% (31/44) | 0 | 3.7 | $1.01 | `outputs/post_neurips_lic_vanilla_redo/baseline_sharded_gpt5_4_code_v2_redo2_1778945913` |
| gpt-5.4 | database_v2 | 1 | 20.4% (10/49) | 1 | 4.2 | $0.69 | `outputs/2026-05-16/07-04-15` |
| gpt-5.4 | database_v2 | 2 | 20.0% (10/50) | 0 | 4.3 | $0.69 | `outputs/2026-05-16/07-08-13` |
| gpt-5.4 | database_v2 | 3 | 20.0% (10/50) | 0 | 4.3 | $0.73 | `outputs/2026-05-16/07-12-01` |
| gpt-5.4 | actions_v2 | 1 | 87.8% (43/49) | 1 | 5.2 | $0.64 | `outputs/2026-05-16/07-15-48` |
| gpt-5.4 | actions_v2 | 2 | 85.4% (41/48) | 2 | 5.2 | $0.64 | `outputs/2026-05-16/07-17-31` |
| gpt-5.4 | actions_v2 | 3 | 90.0% (45/50) | 0 | 5.2 | $0.67 | `outputs/2026-05-16/07-19-15` |
| DeepSeek-V4-Flash | math_v2 | 1 (extra) | 66.0% (33/50) | 0 | 5.5 | $0.07 | `outputs/2026-05-16/06-40-47 (overwritten — stats from launcher log)` |
| DeepSeek-V4-Flash | math_v2 | 2 | 73.5% (36/49) | 1 | 5.3 | $0.06 | `outputs/2026-05-16/06-43-45` |
| DeepSeek-V4-Flash | math_v2 | 3 | 76.0% (38/50) | 0 | 5.5 | $0.07 | `outputs/2026-05-16/06-45-39` |
| DeepSeek-V4-Flash | math_v2 | redo1 (redo, used) | 70.0% (35/50) | 0 | 5.4 | $0.07 | `outputs/post_neurips_lic_vanilla_redo/baseline_sharded_deepseek_v4_flash_foundry_math_v2_redo1_1778946595` |
| DeepSeek-V4-Flash | code_v2 | 1 (tainted, replaced) | 31.6% (6/19) | 25 | 6.2 | $0.04 | `outputs/2026-05-16/06-48-05` |
| DeepSeek-V4-Flash | code_v2 | 2 (tainted, replaced) | 33.3% (6/18) | 26 | 6.6 | $0.04 | `outputs/2026-05-16/06-51-17` |
| DeepSeek-V4-Flash | code_v2 | 3 (tainted, replaced) | 38.7% (12/31) | 13 | 5.2 | $0.05 | `outputs/2026-05-16/06-53-58` |
| DeepSeek-V4-Flash | code_v2 | redo1 (redo, used) | 38.6% (17/44) | 0 | 4.8 | $0.06 | `outputs/post_neurips_lic_vanilla_redo/baseline_sharded_deepseek_v4_flash_foundry_code_v2_redo1_1778945672` |
| DeepSeek-V4-Flash | code_v2 | redo2 (redo, used) | 45.5% (20/44) | 0 | 4.4 | $0.06 | `outputs/post_neurips_lic_vanilla_redo/baseline_sharded_deepseek_v4_flash_foundry_code_v2_redo2_1778945960` |
| DeepSeek-V4-Flash | code_v2 | redo3 (redo, used) | 36.4% (16/44) | 0 | 5.0 | $0.07 | `outputs/post_neurips_lic_vanilla_redo/baseline_sharded_deepseek_v4_flash_foundry_code_v2_redo3_1778946216` |
| DeepSeek-V4-Flash | database_v2 | 1 | 22.0% (11/50) | 0 | 4.3 | $0.05 | `outputs/2026-05-16/06-58-19` |
| DeepSeek-V4-Flash | database_v2 | 2 | 34.0% (17/50) | 0 | 4.2 | $0.05 | `outputs/2026-05-16/07-02-13` |
| DeepSeek-V4-Flash | database_v2 | 3 | 18.0% (9/50) | 0 | 4.2 | $0.05 | `outputs/2026-05-16/07-05-22` |
| DeepSeek-V4-Flash | actions_v2 | 1 | 81.6% (40/49) | 1 | 5.1 | $0.05 | `outputs/2026-05-16/07-08-52` |
| DeepSeek-V4-Flash | actions_v2 | 2 | 74.0% (37/50) | 0 | 5.5 | $0.06 | `outputs/2026-05-16/07-10-27` |
| DeepSeek-V4-Flash | actions_v2 | 3 | 70.0% (35/50) | 0 | 5.1 | $0.06 | `outputs/2026-05-16/07-14-22` |
| Kimi-K2.6 | math_v2 | 1 | 73.5% (36/49) | 1 | 5.5 | $0.07 | `outputs/2026-05-16/06-40-47` |
| Kimi-K2.6 | math_v2 | 2 | 76.0% (38/50) | 0 | 5.4 | $0.07 | `outputs/2026-05-16/06-50-51` |
| Kimi-K2.6 | math_v2 | 3 | 66.0% (33/50) | 0 | 5.8 | $0.08 | `outputs/2026-05-16/07-01-12` |
| Kimi-K2.6 | code_v2 | 1 | 68.2% (30/44) | 0 | 3.9 | $0.05 | `outputs/2026-05-16/07-25-20` |
| Kimi-K2.6 | code_v2 | 2 | 77.3% (34/44) | 0 | 3.6 | $0.04 | `outputs/2026-05-16/07-41-01` |
| Kimi-K2.6 | code_v2 | 3 | 61.4% (27/44) | 0 | 3.8 | $0.04 | `outputs/2026-05-16/07-49-56` |
| Kimi-K2.6 | database_v2 | 1 | 24.0% (12/50) | 0 | 4.3 | $0.05 | `outputs/2026-05-16/08-02-01` |
| Kimi-K2.6 | database_v2 | 2 | 20.0% (10/50) | 0 | 4.3 | $0.05 | `outputs/2026-05-16/08-07-06` |
| Kimi-K2.6 | database_v2 | 3 | 18.0% (9/50) | 0 | 4.3 | $0.05 | `outputs/2026-05-16/08-12-04` |
| Kimi-K2.6 | actions_v2 | 1 | 83.7% (41/49) | 1 | 5.5 | $0.06 | `outputs/2026-05-16/08-17-55` |
| Kimi-K2.6 | actions_v2 | 2 | 90.0% (45/50) | 0 | 5.2 | $0.06 | `outputs/2026-05-16/08-23-14` |
| Kimi-K2.6 | actions_v2 | 3 | 92.0% (46/50) | 0 | 5.4 | $0.06 | `outputs/2026-05-16/08-26-51` |
| gpt-5.5 | math_v2 | 1 (extra) | 82.0% (41/50) | 0 | 5.3 | $0.63 | `outputs/2026-05-16/06-40-47 (overwritten — stats from launcher log)` |
| gpt-5.5 | math_v2 | 2 | 81.6% (40/49) | 1 | 5.5 | $0.70 | `outputs/2026-05-16/06-47-28` |
| gpt-5.5 | math_v2 | 3 | 72.3% (34/47) | 3 | 5.5 | $0.66 | `outputs/2026-05-16/06-49-55` |
| gpt-5.5 | math_v2 | redo1 (redo, used) | 80.0% (40/50) | 0 | 5.3 | $0.66 | `outputs/post_neurips_lic_vanilla_redo/baseline_sharded_gpt5_5_foundry_math_v2_redo1_1778946595` |
| gpt-5.5 | code_v2 | 1 (tainted, replaced) | 70.6% (12/17) | 27 | 3.8 | $0.34 | `outputs/2026-05-16/06-52-47` |
| gpt-5.5 | code_v2 | 2 (tainted, replaced) | 63.3% (19/30) | 14 | 3.9 | $0.48 | `outputs/2026-05-16/06-55-35` |
| gpt-5.5 | code_v2 | 3 | 79.5% (35/44) | 0 | 3.3 | $0.74 | `outputs/2026-05-16/06-58-57` |
| gpt-5.5 | code_v2 | redo1 (redo, used) | 81.8% (36/44) | 0 | 3.1 | $0.69 | `outputs/post_neurips_lic_vanilla_redo/baseline_sharded_gpt5_5_foundry_code_v2_redo1_1778945672` |
| gpt-5.5 | code_v2 | redo2 (redo, used) | 79.5% (35/44) | 0 | 3.4 | $0.96 | `outputs/post_neurips_lic_vanilla_redo/baseline_sharded_gpt5_5_foundry_code_v2_redo2_1778945816` |
| gpt-5.5 | database_v2 | 1 | 16.0% (8/50) | 0 | 4.2 | $0.62 | `outputs/2026-05-16/07-01-26` |
| gpt-5.5 | database_v2 | 2 | 14.0% (7/50) | 0 | 4.3 | $0.66 | `outputs/2026-05-16/07-09-44` |
| gpt-5.5 | database_v2 | 3 | 10.0% (5/50) | 0 | 4.4 | $0.70 | `outputs/2026-05-16/07-14-02` |
| gpt-5.5 | actions_v2 | 1 | 90.0% (45/50) | 0 | 5.1 | $0.57 | `outputs/2026-05-16/07-18-32` |
| gpt-5.5 | actions_v2 | 2 | 85.4% (41/48) | 2 | 5.3 | $0.56 | `outputs/2026-05-16/07-24-18` |
| gpt-5.5 | actions_v2 | 3 | 89.6% (43/48) | 2 | 5.2 | $0.55 | `outputs/2026-05-16/07-26-23` |

## Totals

- Total ctx-editor invocations: **58** (includes tainted and redo runs)
- Total cost across all runs: **$23.06**

## Single-Turn (STQ) Upper Bound

Each cell sends the original unsharded `full_spec_q` prompt as ONE user message,
extracts the answer with the same task evaluator, scores it. N=3 runs per cell.
Cost = $0 for foundry-side models because the Foundry endpoint does not surface
OpenAI-style token usage; treat foundry STQ cost as `unreported` rather than zero.

| Model | math_v2 | code_v2 | database_v2 | actions_v2 |
|---|---|---|---|---|
| gpt-5.4 | 100.0% ± 0.0pp (n=3) | 99.2% ± 1.3pp (n=3) | 91.3% ± 3.1pp (n=3) | 97.3% ± 1.2pp (n=3) |
| DeepSeek-V4-Flash | 98.0% ± 2.0pp (n=3) | 92.4% ± 1.3pp (n=3) | 94.7% ± 2.3pp (n=3) | 96.7% ± 2.3pp (n=3) |
| Kimi-K2.6 | 93.3% ± 2.3pp (n=3) | 85.6% ± 1.3pp (n=3) | 90.0% ± 3.5pp (n=3) | 98.0% ± 2.0pp (n=3) |
| gpt-5.5 | 100.0% ± 0.0pp (n=3) | 99.2% ± 1.3pp (n=3) | 93.3% ± 1.2pp (n=3) | 98.7% ± 1.2pp (n=3) |

Per-run detail:

| Model | Task | Run | Accuracy | Wall | Cost |
|---|---|---|---|---|---|
| gpt-5.4 | math_v2 | 1 | 100.0% (50/50) | 10s | $0.11 |
| gpt-5.4 | math_v2 | 2 | 100.0% (50/50) | 9s | $0.11 |
| gpt-5.4 | math_v2 | 3 | 100.0% (50/50) | 9s | $0.11 |
| gpt-5.4 | code_v2 | 1 | 100.0% (44/44) | 41s | $0.21 |
| gpt-5.4 | code_v2 | 2 | 100.0% (44/44) | 29s | $0.20 |
| gpt-5.4 | code_v2 | 3 | 97.7% (43/44) | 53s | $0.19 |
| gpt-5.4 | database_v2 | 1 | 88.0% (44/50) | 11s | $0.14 |
| gpt-5.4 | database_v2 | 2 | 92.0% (46/50) | 8s | $0.13 |
| gpt-5.4 | database_v2 | 3 | 94.0% (47/50) | 10s | $0.13 |
| gpt-5.4 | actions_v2 | 1 | 98.0% (49/50) | 10s | $0.09 |
| gpt-5.4 | actions_v2 | 2 | 98.0% (49/50) | 8s | $0.08 |
| gpt-5.4 | actions_v2 | 3 | 96.0% (48/50) | 21s | $0.10 |
| DeepSeek-V4-Flash | math_v2 | 1 | 100.0% (50/50) | 28s | $0.00 |
| DeepSeek-V4-Flash | math_v2 | 2 | 98.0% (49/50) | 23s | $0.00 |
| DeepSeek-V4-Flash | math_v2 | 3 | 96.0% (48/50) | 24s | $0.00 |
| DeepSeek-V4-Flash | code_v2 | 1 | 90.9% (40/44) | 32s | $0.00 |
| DeepSeek-V4-Flash | code_v2 | 2 | 93.2% (41/44) | 26s | $0.00 |
| DeepSeek-V4-Flash | code_v2 | 3 | 93.2% (41/44) | 27s | $0.00 |
| DeepSeek-V4-Flash | database_v2 | 1 | 92.0% (46/50) | 21s | $0.00 |
| DeepSeek-V4-Flash | database_v2 | 2 | 96.0% (48/50) | 15s | $0.00 |
| DeepSeek-V4-Flash | database_v2 | 3 | 96.0% (48/50) | 13s | $0.00 |
| DeepSeek-V4-Flash | actions_v2 | 1 | 94.0% (47/50) | 13s | $0.00 |
| DeepSeek-V4-Flash | actions_v2 | 2 | 98.0% (49/50) | 14s | $0.00 |
| DeepSeek-V4-Flash | actions_v2 | 3 | 98.0% (49/50) | 18s | $0.00 |
| Kimi-K2.6 | math_v2 | 1 | 92.0% (46/50) | 109s | $0.00 |
| Kimi-K2.6 | math_v2 | 2 | 92.0% (46/50) | 83s | $0.00 |
| Kimi-K2.6 | math_v2 | 3 | 96.0% (48/50) | 83s | $0.00 |
| Kimi-K2.6 | code_v2 | 1 | 84.1% (37/44) | 287s | $0.00 |
| Kimi-K2.6 | code_v2 | 2 | 86.4% (38/44) | 350s | $0.00 |
| Kimi-K2.6 | code_v2 | 3 | 86.4% (38/44) | 337s | $0.00 |
| Kimi-K2.6 | database_v2 | 1 | 86.0% (43/50) | 252s | $0.00 |
| Kimi-K2.6 | database_v2 | 2 | 92.0% (46/50) | 225s | $0.00 |
| Kimi-K2.6 | database_v2 | 3 | 92.0% (46/50) | 307s | $0.00 |
| Kimi-K2.6 | actions_v2 | 1 | 100.0% (50/50) | 46s | $0.00 |
| Kimi-K2.6 | actions_v2 | 2 | 98.0% (49/50) | 67s | $0.00 |
| Kimi-K2.6 | actions_v2 | 3 | 96.0% (48/50) | 59s | $0.00 |
| gpt-5.5 | math_v2 | 1 | 100.0% (50/50) | 55s | $0.09 |
| gpt-5.5 | math_v2 | 2 | 100.0% (50/50) | 55s | $0.09 |
| gpt-5.5 | math_v2 | 3 | 100.0% (50/50) | 52s | $0.09 |
| gpt-5.5 | code_v2 | 1 | 100.0% (44/44) | 96s | $0.18 |
| gpt-5.5 | code_v2 | 2 | 100.0% (44/44) | 93s | $0.18 |
| gpt-5.5 | code_v2 | 3 | 97.7% (43/44) | 86s | $0.17 |
| gpt-5.5 | database_v2 | 1 | 94.0% (47/50) | 119s | $0.22 |
| gpt-5.5 | database_v2 | 2 | 92.0% (46/50) | 113s | $0.22 |
| gpt-5.5 | database_v2 | 3 | 94.0% (47/50) | 106s | $0.21 |
| gpt-5.5 | actions_v2 | 1 | 98.0% (49/50) | 33s | $0.07 |
| gpt-5.5 | actions_v2 | 2 | 100.0% (50/50) | 31s | $0.07 |
| gpt-5.5 | actions_v2 | 3 | 98.0% (49/50) | 32s | $0.07 |

## v1 vs v2 Task Evaluators — DeepSeek-V4-Flash, sharded

Same model, same data, same sharded protocol — only the *task evaluator and
system prompt* change between rows. v2 = math_v2/code_v2/database_v2/actions_v2
(the active task configs); v1 = math/code/database/actions (the pre-v2 evaluators
without the system-prompt and extraction tweaks). N=3 runs each.

| Task | v1 mean | v1 per-run | v2 mean | Δ (v2−v1) |
|---|---|---|---|---|
| math | 65.0% ± 6.0pp | 66.7% / 58.3% / 70.0% | 73.2% ± 3.0pp | +8.2pp |
| code | 30.3% ± 1.3pp | 29.5% / 31.8% / 29.5% | 40.2% ± 4.7pp | +9.9pp |
| database | 98.7% ± 1.2pp | 98.0% / 100.0% / 98.0% | 24.7% ± 8.3pp | -74.0pp |
| actions | 44.0% ± 10.6pp | 48.0% / 52.1% / 32.0% | 75.2% ± 5.9pp | +31.2pp |

### Caveats on this comparison

- **Conversation length differs systematically.** Eyeballing matched traces, v1
  conversations tend to be shorter (fewer user turns) than v2 conversations on the
  same problem. The difference is not coming from the user agent or shard list — the
  user-sim, shards, and `max_turns` cap are the same — but from the system agent's
  answer-attempt detection. v2's stricter answer-format expectations (e.g. requiring
  `\boxed{}` or `\`\`\`sql` fences) seem to delay the answer_attempt classification
  for longer, so the user-sim reveals more shards. v1's looser format is satisfied
  earlier, the simulation terminates, and the model is graded on a partial-shard
  conversation. Net effect: v1 is graded on *easier* conversational state but with a
  *less reliable* extraction.
- **Database in particular swings the wrong direction (v1 ~98% vs v2 ~25%).** This
  is dominated by the conversation-length effect above. The model's intuition often
  produces a correct query from just the first 1–2 shards; v2's longer protocol gives
  the model more chances to be misdirected by later shards.
- **Actions swings strongly in v2's favor (+31pp).** This is the `accumulate`
  instruction in the v2 system prompt: BFCL grades the final assistant turn, and v1's
  prompt does not tell the model to re-emit the full consolidated function-call list.
  This was a known gap; we documented it in `docs/mar21_bug_discovery.md`.
- **Math and code show modest v2 gains (~8–10pp).** Driven by extraction fixes
  (v2's `\*\*ANSWER: N\*\*` plus integer coercion for math; v2's import/def split
  fix for code).

Net read: v2 is the right default for forward experiments. The headline-grabbing
v1 database number is a measurement artifact (premature termination), not the model
being better.
