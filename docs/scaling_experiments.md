# Scaling Experiments — How-To

Short reference for running new experiments and sweeps with the post-Phase-3 setup. Companion to [`benchmarks_index.md`](benchmarks_index.md) (entry points) and [`paper_experiments_provenance.md`](paper_experiments_provenance.md) (what we already ran).

## Mental model

Four moving parts:

1. **Hydra configs** under `src/ctx_editor/config/` define every knob — task, model, strategy, analyzer prompt version, seed, sample budget, etc.
2. **Console scripts** (`ctx-editor`, `ctx-editor-collabllm`, `ctx-editor-huang-phase1`, `ctx-editor-huang-phase2`) are the single way to launch a benchmark. All four take Hydra-style `key=value` overrides.
3. **`run_summary.json`** is the standardized per-run summary every benchmark writes. Same shape across LiC / CollabLLM / Huang.
4. **`scripts/aggregate_results.py`** crawls run directories, reads `run_summary.json` (with metrics.json fallback for legacy runs), and produces a single table or CSV.

You should rarely need to touch Python to run a new experiment. If you do, the new thing probably belongs in the Hydra config tree.

## Single run

```bash
# LiC (default task, default model, baseline strategy)
ctx-editor

# Override anything
ctx-editor experiment=context_edit_v2 model=gpt5_mini task=code
ctx-editor experiment=append_analysis_v9 task=dev_math execution.max_concurrent=10

# CollabLLM
ctx-editor-collabllm experiment=collabllm_compaction task.dataset_name=math-hard

# Huang phase 1 (build the AO-failure-turn set)
ctx-editor-huang-phase1 num_conversations=30 seed=42

# Huang phase 2 (run AC3 variants against those failures)
ctx-editor-huang-phase2 \
    phase1_dir=outputs/huang_eval/phase1/2026-05-11/12-34-56 \
    variants.s3=true variants.s15=true variants.s2=true variants.augment=true
```

Outputs go to `outputs/{YYYY-MM-DD}/{HH-MM-SS}/` (or `outputs/huang_eval/phase{1,2}/…` for Huang). Hydra always writes `.hydra/{config.yaml,overrides.yaml,hydra.yaml}` for reproducibility, plus the benchmark's own `run_summary.json`.

## Multi-seed sweep

Use Hydra's `--multirun` (alias `-m`) flag. No bash loop needed.

```bash
# LiC across 3 seeds on a single task
ctx-editor --multirun \
    experiment=context_edit_v2 task=math seed=42,43,44

# CollabLLM across 3 seeds on both datasets
ctx-editor-collabllm --multirun \
    experiment=collabllm_compaction task.dataset_name=math-hard,bigcodebench seed=42,43,44

# Huang phase 2 across 3 seeds with all four AC3 variants on
ctx-editor-huang-phase2 --multirun \
    phase1_dir=outputs/huang_eval/phase1/<DATE>/<TIME> \
    variants.s15=true variants.s2=true variants.augment=true \
    seed=42,43,44
```

Each combination gets its own timestamped output dir. By default Hydra runs them sequentially; for parallelism install one of the launcher plugins (`hydra-joblib-launcher`, `hydra-submitit-launcher`) and set `hydra/launcher=joblib`.

## Multi-config sweep

`key=a,b,c` is a sweep dimension. Multiple `--multirun` keys form a Cartesian product.

```bash
# AC3 variants × 4 tasks × 3 seeds = 36 runs
ctx-editor --multirun \
    experiment=baseline,append_analysis,context_edit_v2 \
    task=math,code,database,actions \
    seed=42,43,44
```

If you want a subset of the product rather than the full cross, use Hydra range syntax or list it out in a script. For repeated complex sweeps, write a YAML in `config/sweep/` and load it via `+sweep=…`.

## Aggregating results

Once one or more sweeps complete, point the aggregator at the output trees:

```bash
# Pretty-printed table across LiC + Huang runs
python scripts/aggregate_results.py outputs/2026-05-12/ outputs/huang_eval/

# CSV for downstream analysis
python scripts/aggregate_results.py --csv runs.csv outputs/

# Filter by benchmark
python scripts/aggregate_results.py --filter benchmark=huang_phase2 outputs/

# Filter by experiment_name (e.g. one specific sweep)
python scripts/aggregate_results.py --filter benchmark=lic outputs/2026-05-12/
```

For older LiC/CollabLLM runs that pre-date the `run_summary.json` standard, the aggregator falls back to `metrics.json` + Hydra's saved overrides. New runs land cleanly in the table.

## Extending

### Add a new analyzer prompt version (e.g. `v12`)

1. Drop the prompt text files into `src/ctx_editor/strategies/prompts/` (e.g. `analyzer_v12_task_spec.txt` and `analyzer_v12_compare.txt`).
2. Register the version in `src/ctx_editor/strategies/analyzer_prompts.py`:

   ```python
   "v12": AnalyzerPromptVersion(
       name="v12",
       flow="two_query",
       task_spec_template="analyzer_v12_task_spec",
       compare_template="analyzer_v12_compare",
       description="…",
   ),
   ```
3. Use it from any benchmark:

   ```bash
   ctx-editor experiment=context_edit_v2 strategy.analyzer_prompt_version=v12
   ctx-editor-huang-phase2 phase1_dir=... analyzer_prompt_versions.s3=v12
   ```

That's it. No analyzer code changes, no per-benchmark plumbing.

### Add a new AC3 variant

1. Implement a `ContextStrategy` subclass in `src/ctx_editor/strategies/` (LiC-style multi-turn) or `src/ctx_editor/huang_eval/strategies.py` (Huang one-shot).
2. Export it from the relevant `__init__.py`.
3. Add a Hydra experiment config under `src/ctx_editor/config/experiment/` with `_target_:` pointing at the new class.
4. For Huang, also add a wrapper in `huang_eval/replay.py` + slot it into `variants:` in `config/huang_phase2.yaml` and the dispatcher in `process_failure_turn`.

### Add a new task (LiC)

1. Drop a task config in `src/ctx_editor/config/task/<name>.yaml` (look at existing ones for shape).
2. Make sure `get_task()` in `run_experiment.py` knows about it (it dispatches by name).
3. Use it: `ctx-editor task=<name>`.

### Add a new dataset (CollabLLM)

1. Register the dataset in `src/ctx_editor/data/collabllm_loader.py:COLLABLLM_DATASETS`.
2. Use it: `ctx-editor-collabllm task.dataset_name=<key>`.

### Add a new benchmark

The pattern:

1. Hydra config at `src/ctx_editor/config/<benchmark>.yaml` (root config) with `defaults:` listing strategy/task/model groups it uses.
2. A `@hydra.main`-decorated entry point that:
   - Builds whatever benchmark-specific simulator/loader it needs.
   - Calls `strategy.prepare_context(trace, memory, model_client)` to invoke the AC3 op.
   - Writes `run_summary.json` with `{benchmark, experiment_name, metrics, output_dir, timestamp, …}`.
3. A `ctx-editor-<benchmark>` console script in `pyproject.toml`.
4. After `pip install -e .`, the aggregator picks the new benchmark up for free.

Tau2 is the open case (see [`tau2_absorption_decision.md`](tau2_absorption_decision.md)).

## Common pitfalls

- **`seed=` on its own does not change task selection.** Sample order is deterministic per seed; if you want different *samples*, you need to vary `task.limit` or use a different `data_file`.
- **gpt-5-family models force `temperature=1.0`.** Multi-seed sweeps are how you measure variance for these models; don't expect `temperature=0` to give you determinism.
- **Don't pass `reasoning_effort` to analyzer/editor calls** (per project memory) — degrades quality severely. The analyzer registry doesn't pass it by default; if you add it manually, you'll see the regression.
- **Hydra `--multirun` runs sequentially by default.** For real parallelism install a launcher plugin (`hydra-joblib-launcher`).
- **`experiment_name` interpolation can collide across sweep cells.** Output dirs are timestamped, so they don't actually collide on disk, but result-tree names in `ledger.csv` can look identical. Add `seed=${seed}` into your `experiment_name` template if you need them distinguishable at a glance.
