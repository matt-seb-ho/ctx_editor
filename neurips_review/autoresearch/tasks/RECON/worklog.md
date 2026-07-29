# RECON — Experiment Infrastructure Map

**Task:** map every harness + operator name so downstream agents (T6/T8/T9/T11–13) can launch runs without re-deriving anything.
**Date:** 2026-07-29. **No experiments run** — only config dry-runs (`--cfg job`) and 5 single-token endpoint auth probes.
**Status:** complete.

---

## 0. TL;DR — the five things that will bite you

1. **`seed=` is a no-op on the LiC harness and on CollabLLM.** `cfg.seed` is read *only* by `huang_eval/run_phase{1,2}.py` (WildChat). `grep -rn "cfg.seed" src/` returns 4 hits, all in `huang_eval/`. The T4 "N=3 seeds" runs (`seed=43,44`) and every `seed=$((42+rep))` in the launcher scripts were inert — reps varied only through `temperature: 1.0` sampling. **WildChat N=3 is real; LiC and CollabLLM "N=3" are sampling reps on a fixed subset.** Say "3 reps", not "3 seeds", in the rebuttal.
2. **`fxdata-shared` is dead under the current `az` identity (401 PermissionDenied)**, and `multi_endpoint_foundry.yaml` routes `gpt-4o-mini` *only* there (it is deliberately excluded from `dl-openai-3`, see comment at `config/load_balancer/multi_endpoint_foundry.yaml:42-44`). `gpt-4o-mini` is the `system:` (judge/extractor) role in `deepseek_v4_flash_user_deepseek.yaml`. **T8 will fail at the judge step unless you patch the load balancer** — see §B.1 for the one-line fix.
3. **`mgalley-foundry2` and `dl-openai-3` both work** under the current identity. DeepSeek-V4-Flash and Kimi-K2.6 verified live. So T8's exact competent-user-sim config *is* reproducible (after fix #2), and the tau2 Foundry sweep is not blocked on credentials.
4. **All prior CollabLLM / WildChat / tau2 output dirs are gone from disk** — but the CollabLLM and WildChat ones **are inside `~/ac3/blob_staging/snapshot.tar.gz`** (2.2 GB, ctx_editor-rooted, 2026-06-12). tau2 outputs are not; tau2 lives in GitHub `matt-seb-ho/tau2_ctxe` (verified reachable, HEAD `8e5fd3c`).
5. **`docs/paper_experiments_provenance.md` names two configs that do not exist**: `experiment=assistant_omit` and `experiment=concat_baseline`. The real names are `omit_assistant` and `concatenate_user`. Also `reflection_only` must be addressed as `experiment=legacy/reflection_only`.

---

## A. LiC harness (`ctx-editor`)

Entry point: `pyproject.toml:47` → `ctx_editor.run_experiment:main`. Root config `src/ctx_editor/config/config.yaml`.
Config groups: `experiment/`, `model/`, `task/`, `user_mode/`, `load_balancer/`.

### A.1 Paper-name → config-name operator mapping

Source of truth: `docs/paper_experiments_provenance.md` (cheat sheet at the top) + `src/ctx_editor/strategies/__init__.py:1-33` + per-config headers. The paper (`writing/overleaf_repo/neurips/neurips_2026_conference.tex:28`) uses `\method` = **AC3**; older drafts wrote "ACC"/"ACE" — same thing.

| Paper operator | Strategy class (canonical / legacy alias) | LiC config (`experiment=`) | Key params | Notes |
|---|---|---|---|---|
| **Baseline / Full context (S0, FC)** | `BaselineStrategy` | `baseline` | — | |
| Baseline + memory | `BaselineStrategy` + cheatsheet | `baseline_memory` | — | needs CLI `memory.*` too |
| **AO — Assistant Omission** (Huang et al.) | `OmitAssistantStrategy` | `omit_assistant` | `min_turns: 1` | ⚠ provenance doc says `assistant_omit` — **wrong**. `AssistantOmitStrategy` (a near-identical second impl) has **no LiC config**; only `collabllm_assistant_omit` uses it. |
| **Concat User** (LiC paper baseline) | `ConcatenateUserStrategy` | `concatenate_user` | `numbered: true` | ⚠ provenance doc says `concat_baseline` — **wrong**. |
| **ERGO** (Khalid et al.) | `ERGORestartStrategy` | `ergo` | `min_turns: 1` | LLM rewrite of user side |
| **AC3-Augment** (S1) | `AC3AugmentStrategy` ≡ `AppendAnalysisStrategy` | `append_analysis` | `min_turns: 3`, analyzer v8 (default) | `append_analysis_v9` = v9 prompt |
| **AC3-Reset** (always-on; S1.5 in Huang logs) | `AC3ResetStrategy` ≡ `ContextEditV2Strategy` | **`context_edit_v2_no_gate`** | `min_turns: 1`, `max_resets: 100`, v8 | This is what the rebuttal calls "always-on Reset" / "Reset" (+15.9pp, 33/36) |
| **AC3-Gated-Reset** (S2; paper default) | same class, gated | **`context_edit_v2_gated`** | `min_turns: 3`, `max_resets: 3`, v8 | |
| AC3-Reset, paper-era generic | same class | `context_edit_v2` | `min_turns: 3`, `max_resets: 3`, no explicit prompt version | Older Table-1 rows used this for both Reset and Gated-Reset rows |
| **AC3-Rewrite** (S3) | `AC3RewriteStrategy` ≡ `ContextCompactionStrategy` | `ac3_rewrite_v8_lic` (headline), `ac3_rewrite_lic` (v1) | `min_turns: 1` | Ten `ac3_rewrite_*_lic.yaml` prompt variants exist: v2, v3_conv_first, v3_no_conv, v4_strict, v5_resetlike, v6_gepa, v8, v9_no_conv, v10_gepa |
| **Compaction / S3 in older notes** | same as AC3-Rewrite | ↑ | | There is **no** config literally named `compaction` for LiC; only `collabllm_compaction`. |
| **Reflection (equal-budget control, T5)** | `ReflectionStrategy` | **`legacy/reflection_only`** | `min_turns_for_reflection: 3` | must include the `legacy/` prefix |
| Actions-task variants | `AC3ResetStrategy` + accumulate flag | `context_edit_v2_gated_accumulate`, `context_edit_v2_no_gate_accumulate`, `context_edit_v2_accumulate` | `accumulate_instruction: true` | BFCL needs the full function-call set repeated in the final turn |
| Soft-attention ablations (paper Table 3) | `AC3AugmentStrategy`, alt prompts | `append_analysis_soft` (v8_soft), `append_analysis_soft_cot` (v8_soft_cot), `append_analysis_single` (v8_single) | | |
| Memory arms | +cheatsheet | `append_analysis_memory`, `context_edit_v2_memory`, `append_analysis_spec_mem`, `append_analysis_single_memory`, `context_edit_cheatsheet`, `legacy/agentic_edit_memory` | | `experiment=` alone does **not** enable memory; pass `memory.enabled=true memory.source=...` on the CLI (comment at `baseline_memory.yaml:2-3`) |
| Legacy, not in the AC3 lineup | `ContextEditStrategy`, `AgenticEditStrategy` | `context_edit`, `context_edit_v7`, `legacy/agentic_edit` | | kept for reproducibility only |
| CollabLLM ports | see §B.1 | `collabllm_*` (9 configs) | | run via `run_collabllm`, not `ctx-editor` |

Rename decoder for old logs: `AppendAnalysisStrategy`→Augment, `ContextEditV2Strategy`→Reset/Gated-Reset, `ContextCompactionStrategy`→Rewrite; `S0/FC`=Baseline, `S1`=Augment, `S1.5`=Reset, `S2`=Gated-Reset, `S3`=Rewrite. Analyzer prompt versions: `v8` production two-query (LiC + Huang S1.5/S3), `v9` adds `<corrective_direction>`, `v11` mid-task-reflection (Huang S2), `v10` **tau2-only, lives in the tau2 repo**, `s1` single-query content-filter-safe (CollabLLM legacy).

### A.2 Sample count and data file

- **Data file:** `task.data_file=<path relative to repo root>` — read at `run_experiment.py:89-95`.
- **Sample count:** `task.limit=<N>` — read at `run_experiment.py:106-108` (`samples[:limit]`, i.e. a **prefix slice, not a random sample**). `null` = all.
- **Task filter:** `task.filter=math|code|database|actions` selects rows within a multi-task data file.
- **Turn cap:** `task.max_turns` (default 20).
- Available data files: `data/lic_eval_subset.json` (default for `*_v2` tasks), `data/rebuttal_random_math40.json` (T4's uniform-random N=40), `data/math_full_subset.json` (103, non-baseline-selected pool), `data/htn50_52_*_subset.json` (baseline-failure-selected "hard" subsets), `data/dev_*_subset.json`, `data/test_*_subset.json`, `data/lic_mem_learn_set.json`.
- **Always use the `_v2` task configs** (`math_v2`, `code_v2`, `database_v2`, `actions_v2`) — they set `task_version_map` to the fixed evaluators.

### A.3 Replay mode

Doc: `docs/replay_mode.md`. Key: `execution.replay_source=<path>` (activates replay regardless of `execution.mode`); `execution.replay_turns` (default 1 = final turn only).

`replay_source` may be:
- a traces subdir — `data/baseline_traces_v2/math/`
- a whole output dir — `outputs/2026-03-06/02-22-02/`
- a `results.json` with embedded traces

It loads saved traces, strips the last **visible assistant** message plus its trailing `verification` / `answer_evaluation` log entries, applies the strategy, regenerates one turn, re-verifies. Traces are matched to samples by `task_id`; unmatched samples are dropped. Provenance is recorded on `trace.provenance` and `metadata.replay_mode: true`.

**Replay sources present on disk:**

| Path | Tasks | Notes |
|---|---|---|
| `data/baseline_traces_v2/` | `code/`, `database/`, `math/` | the paper's canonical Table-1 replay source; also has `*_false_negatives.json` per task |
| `data/baseline_traces_htn50_52/` | `actions/`, `code/`, `database/`, `math/` | hard (baseline-failure-selected) subset |
| `data/baseline_traces/` | `actions/` only | |
| `data/valid_prefixes_htn50_52/` | — | curated prefix pool (`scripts/curate_valid_prefixes.py`) |
| `outputs/rebuttal_random/{full,rep2,rep3}_baseline/traces/math/` | math | fresh 2026-07-27 gpt-5.4-mini end-to-end traces, N=40 — usable as a replay source for T2/T9 |

`outputs/2026-03-16/19-26-46` (actions replay source named in the provenance doc) is **not on this machine**.

### A.4 Analyzer / context-editor model override

Strategies read `analyzer_model: ${model.ctx_editor.model}` (e.g. `context_edit_v2_gated.yaml:9`); Rewrite reads `compaction_model`, ERGO reads `rewrite_model` — all from the same `model.ctx_editor.model` node. The `model/*.yaml` files each define a `ctx_editor:` block (`gpt5_4_mini_trapi.yaml:25-30`).

**Override string (verified via `ctx-editor --cfg job`):**

```
model.ctx_editor.model=<deployment-name>
```

Also overridable: `model.ctx_editor.reasoning_effort=null|low|medium|high`, `model.ctx_editor.temperature`, `model.ctx_editor.timeout`, `model.ctx_editor.max_tokens`.

**⚠ Two gotchas for T9:**
1. The load balancer hard-fails on unlisted models: `load_balancer.py:286` raises `ValueError("No endpoints configured for model '<m>'")`. `load_balancer/trapi.yaml:22-24` lists **only** `gpt-5.4-mini_2026-03-17` and `gpt-4o_2024-11-20`. To swap the analyzer to a third model you must either add it to `supported_models` in the load-balancer YAML, or use `load_balancer=multi_endpoint_foundry` (DeepSeek-V4-Flash, Kimi-K2.6, gpt-oss-120b, gpt-5.5, grok, Phi-4, Mistral — see §B.1 for which endpoints actually authenticate today).
2. Non-reasoning models (gpt-4o) inherit `reasoning_effort: medium` from the model config unless you also pass `model.ctx_editor.reasoning_effort=null`. `openai_model.py:203-204` forwards it verbatim.

### A.5 Where results land, and how to get the headline number

`logging.output_dir` (default `outputs/${now:%Y-%m-%d}/${now:%H-%M-%S}`; every rebuttal script overrides it to a stable name). Each run dir contains:

| File | Contents |
|---|---|
| `metrics.json` | `accuracy`, `correct`, `total_samples`, per-task breakdown, cost, avg turns |
| `run_summary.json` | metrics + `strategy`, `model`, `task`, `user_mode`, `samples`, `adjusted_accuracy`, `user_sim_induced`, `non_answer_attempts` |
| `summary.txt` | human-readable; the line the launcher scripts grep |
| `results.json` | per-sample results |
| `traces/<task>/` | full conversation traces (replay-able) |
| `false_negatives.json` | user-sim-induced-failure classification |
| `config.yaml` | resolved Hydra config |
| `verbose.log`, `experiment.log` | |

Plus an append-only ledger at **`outputs/runs.yaml`** (one row per run: path, strategy, model, task, samples, accuracy, cost, avg turns, data_file).

**Canonical headline number = `adjusted_accuracy`** in `run_summary.json` (false-negative-adjusted; excludes user-sim-induced failures). This is what the rebuttal quotes: `exp1_reps_results.txt` shows raw 95.00% → adjusted 100.00% for reset rep2. `false_negative_analysis.enabled: true` by default; on TRAPI set `false_negative_analysis.model=gpt-4o_2024-11-20`.

Quick reads:
```bash
jq -r '[.strategy,.task,.samples,.metrics.accuracy,.metrics.adjusted_accuracy]|@tsv' outputs/**/run_summary.json
grep -E 'Accuracy:|Adjusted Accuracy:' <run_dir>/summary.txt
```

**Existing analysis scripts:**

| Script | What it does |
|---|---|
| `scripts/aggregate_results.py` | Multi-dir scanner → table/CSV. `python scripts/aggregate_results.py outputs/rebuttal_random --csv out.csv`. Handles LiC, CollabLLM, and legacy tau2 dirs (`_tau2_summary_from_legacy` at `:92-137`). |
| `neurips_review/experiments/paired_analysis.py` | Paired delta vs Baseline + exact sign test. **Does not read output dirs** — it regexes the markdown tables in `docs/reports/post_neurips_ac3_phase{1,2}.md`. Zero API cost. Output: `paired_analysis_results.txt`. |
| `scripts/build_mega_table.py`, `scripts/aggregate_ac3_phase.py` | Paper-table builders |
| `src/ctx_editor/identify_false_negatives.py`, `scripts/lic_false_negative_analysis*.py` | FN adjustment |

---

## How to launch X — literal, copy-pasteable

All assume:
```bash
cd /home/t-matthewho/ac3/ctx_editor && . .venv/bin/activate
```
(`.env` is auto-loaded. `uv pip install -e ".[all]" azure-identity python-dotenv sqlparse` — the last two are missing from `[all]`; a silent `sqlparse` ImportError masks the task registry and shows up as "Task math_v2 not found".)

### 1. LiC **Baseline** (full context), TRAPI, N=40 random math, end-to-end
```bash
ctx-editor \
  experiment=baseline \
  model=gpt5_4_mini_trapi \
  load_balancer=trapi \
  task=math_v2 \
  task.data_file=data/rebuttal_random_math40.json \
  user_mode=sharded \
  execution.max_concurrent=5 \
  false_negative_analysis.model=gpt-4o_2024-11-20 \
  experiment_name=T9_baseline_rep1 \
  logging.output_dir=outputs/T9/baseline_rep1
```

### 2. LiC **Reset** (always-on)
```bash
ctx-editor \
  experiment=context_edit_v2_no_gate \
  model=gpt5_4_mini_trapi \
  load_balancer=trapi \
  task=math_v2 \
  task.data_file=data/rebuttal_random_math40.json \
  user_mode=sharded \
  execution.max_concurrent=5 \
  false_negative_analysis.model=gpt-4o_2024-11-20 \
  experiment_name=T9_reset_rep1 \
  logging.output_dir=outputs/T9/reset_rep1
```

### 3. LiC **Gated-Reset** (paper default)
```bash
ctx-editor \
  experiment=context_edit_v2_gated \
  model=gpt5_4_mini_trapi \
  load_balancer=trapi \
  task=math_v2 \
  task.data_file=data/rebuttal_random_math40.json \
  user_mode=sharded \
  execution.max_concurrent=5 \
  false_negative_analysis.model=gpt-4o_2024-11-20 \
  experiment_name=T9_gated_rep1 \
  logging.output_dir=outputs/T9/gated_rep1
```

### 4. Swapped analyzer model (T9) — assistant fixed, analyzer varied

Weaker analyzer, same endpoint (works out of the box; note the `reasoning_effort=null`):
```bash
ctx-editor \
  experiment=context_edit_v2_gated \
  model=gpt5_4_mini_trapi \
  load_balancer=trapi \
  model.ctx_editor.model=gpt-4o_2024-11-20 \
  model.ctx_editor.reasoning_effort=null \
  task=math_v2 task.data_file=data/rebuttal_random_math40.json \
  execution.max_concurrent=5 \
  false_negative_analysis.model=gpt-4o_2024-11-20 \
  experiment_name=T9_gated_analyzer-gpt4o \
  logging.output_dir=outputs/T9/gated_analyzer_gpt4o
```

Cross-family analyzer (DeepSeek-V4-Flash / Kimi-K2.6) — requires the Foundry balancer, and the assistant must then also be a Foundry-served model, or you add the TRAPI deployment to a merged balancer file:
```bash
ctx-editor \
  experiment=context_edit_v2_gated \
  model=deepseek_v4_flash_foundry \
  load_balancer=multi_endpoint_foundry \
  model.ctx_editor.model=Kimi-K2.6 \
  task=math_v2 task.data_file=data/rebuttal_random_math40.json \
  execution.max_concurrent=5 \
  experiment_name=T9_gated_analyzer-kimi \
  logging.output_dir=outputs/T9/gated_analyzer_kimi
```
⚠ Before running the second form, apply the `gpt-4o-mini` load-balancer fix in §B.1 — the `system:` role in the Foundry model configs is `gpt-4o-mini`.

### 5. Replay run (last-turn regeneration on a fixed prefix)
```bash
ctx-editor \
  experiment=context_edit_v2_gated \
  model=gpt5_4_mini_trapi \
  load_balancer=trapi \
  task=math_v2 \
  execution.replay_source=data/baseline_traces_v2/math/ \
  execution.replay_turns=1 \
  execution.max_concurrent=5 \
  false_negative_analysis.model=gpt-4o_2024-11-20 \
  experiment_name=replay_gated_math \
  logging.output_dir=outputs/replay/gated_math
```

### 6. Config dry-run (free, no API calls) — always do this first
```bash
ctx-editor --cfg job experiment=<X> model=gpt5_4_mini_trapi task=math_v2 load_balancer=trapi <overrides>
```

### 7. N=3 reps

Copy `neurips_review/experiments/run_exp1_reps.sh` — it is the working template (loop over reps, distinct `logging.output_dir`, grep `summary.txt`). **Drop the `seed=` override**; it does nothing (§0.1). Variation comes from `temperature: 1.0`.

---

## B. Non-LiC harnesses

### B.0 Endpoint reachability, verified 2026-07-29 (single-token probes)

Identity: `sc-hy6197645@microsoft.com`.

| Endpoint | Status | Models probed |
|---|---|---|
| TRAPI `redmond/interactive` | ✅ 200 | `gpt-5.4-mini_2026-03-17`, `gpt-4o_2024-11-20` (per WORKLOG) |
| `mgalley-foundry2` (Foundry) | ✅ 200 | `DeepSeek-V4-Flash`, `Kimi-K2.6` |
| `dl-openai-3` (Azure OAI) | ✅ 200 | `gpt-4o-mini`, `gpt-4o`, `gpt-5-mini` |
| `fxdata-shared` (Azure OAI) | ❌ **401 PermissionDenied** | all (gpt-4o-mini, gpt-4o, gpt-5-mini) |

**Actionable fix (blocks T8, and any Foundry-based T9):** `config/load_balancer/multi_endpoint_foundry.yaml` routes `gpt-4o-mini` exclusively to `fxdata-shared` (line 67), deliberately excluding it from `dl-openai-3` (comment lines 42-44 — a quota decision made when `fxdata-shared` still worked). Add to the `dl-openai-3` block (after line 55):
```yaml
      gpt-4o-mini: 150
```
Or override per run: `model.system.model=gpt-4o` (verified working on `dl-openai-3`). Do not silently substitute the *judge* model without recording it — it changes the CollabLLM accuracy metric.

Same issue affects `multi_endpoint_full.yaml` / `multi_endpoint.yaml` — check before use.

### B.1 CollabLLM (T8)

| | |
|---|---|
| **Location** | In-repo. Entry `src/ctx_editor/run_collabllm.py` (`@hydra.main` at `:350`); root config `src/ctx_editor/config/collabllm.yaml`; console script `ctx-editor-collabllm`. User sim `agents/collabllm_user_agent.py`; loader `data/collabllm_loader.py` (`COLLABLLM_DATASETS` at `:181`); judge `evaluation/collabllm_metrics.py`; prompts `src/ctx_editor/prompts/collabllm/`. No `collabllm` pip package, no external clone — it is a full reimplementation. |
| **Task config** | **Inline in `collabllm.yaml:11-16`, not a config group.** `task.name` is a free-text label; `task.dataset_name` is the real switch. `math-hard` → `task.name=collabllm_math`; `bigcodebench` → `task.name=collabllm_code`. `task.limit=20`, `task.max_turns=14`. There is no `config/task/collabllm_*.yaml`. |
| **"Competent user simulator"** | Not a flag — a **model-config swap**: `model=deepseek_v4_flash_user_deepseek` (`user.model: DeepSeek-V4-Flash` at `:12`). The weak sim is any config with `user.model: gpt-4o-mini` (`deepseek_v4_flash_foundry.yaml`, `gpt5_mini_low.yaml:7`). Zero code hits for "competent" — it exists only in prose. |
| **Strategy configs** | `collabllm_baseline` (Baseline), `collabllm_assistant_omit` (AO), `collabllm_ac3_reset_v8` (Reset, always-on, v8), `collabllm_ac3_augment_v8` (Augment, v8, `min_turns:4`), `collabllm_compaction` (Rewrite), `collabllm_ergo`, plus legacy `collabllm_append_analysis` / `collabllm_context_edit_v2` (both `s1` prompt). |
| **Prior output dir** | `outputs/post_neurips_r2_collabllm_user_deepseek/` — **not on disk**, but present in `~/ac3/blob_staging/snapshot.tar.gz` with 8 cells: `collabllm_{baseline,assistant_omit,ac3_reset_v8,ac3_augment_v8}_{math-hard,bigcodebench}_rep1_*`. |
| **N seeds** | **N=1** (`REPS=(1)` at `run_post_neurips_r2_collabllm.sh:33`). This is the T8 exposure. Phase 3a (weak sim) was N=3. |
| **Report** | `docs/reports/post_neurips_r2_collabllm.md` — the source of MATH-Hard 95/90/**100** and BigCodeBench 5/15/**20**. |
| **⚠ Seed** | `cfg.seed` is never read by `run_collabllm.py`. Loaders hardcode `seed: int = 42` (`collabllm_loader.py:10,53`) and subsample with `random.Random(42)`. All reps hit the **same 20 problems**. Confirmed empirically: Phase 3a Baseline math-hard was 30.0/30.0/30.0 across "seeds" 43/44/45. So T8 N=3 = 3 sampling reps. Threading a real seed through is a ~3-line change to `load_collabllm_dataset` but would break comparability with the asserted N=1 numbers. |

**Launch (one cell, reproduces the claim):**
```bash
cd /home/t-matthewho/ac3/ctx_editor && . .venv/bin/activate
[[ -f .env ]] && { set -a; source .env; set +a; }

python -m ctx_editor.run_collabllm \
  experiment=collabllm_ac3_augment_v8 \
  model=deepseek_v4_flash_user_deepseek \
  load_balancer=multi_endpoint_foundry \
  task.name=collabllm_math \
  task.dataset_name=math-hard \
  task.limit=20 \
  execution.max_concurrent=10 \
  experiment_name=T8_augment_math-hard_rep1 \
  logging.output_dir=outputs/T8/augment_math-hard_rep1 \
  metadata.branch=T8_collabllm_n3
```
Cells for T8: 4 strategies × 2 datasets × 3 reps = 24. Full sweep template: `scripts/run_post_neurips_r2_collabllm.sh` (+ `_augment.sh` for the 4th strategy). Apply the §B.0 `gpt-4o-mini` fix first.

### B.2 tau2 / τ²-bench (T6)

| | |
|---|---|
| **Location** | **Not on this machine.** GitHub `matt-seb-ho/tau2_ctxe` (fork of `sierra-research/tau2-bench`) — **verified reachable over https**, HEAD `8e5fd3ca5eea0b4547f46ba03156cac57adfe451`. Our code is 6 files in `ctx_edit/`: `agents.py`, `analyzer.py`, `run_parallel.py`, `run_experiment.py`, `run_diagnostic.py`, `build_cheatsheet.py`. Dead historical paths in docs: `/home/agent/tau2-bench/`, `/home/v-homatthew/tau2_ctxe/`. |
| **Invocation** | argparse, not Hydra: `python ctx_edit/run_parallel.py --strategy {s0,ao,s1,s2,s3} --agent-llm <m> --analyzer-model <m> --max-steps 50 --min-turns 2 --max-resets 3 --workers 10 --seed 42`. Args dumped to `config.json` per run. Foundry models take the `foundry/<MODEL>` prefix. |
| **Strategy labels** | `s0`=Baseline, `ao`=Assistant Omission, `s1`=AC3-Augment, `s2`=AC3-Gated-Reset (v10), `s3`=AC3-Rewrite (`--rewrite-prompt-version=v10|v11`, default v11). |
| **Seed** | CLI `--seed 42`. **This is a real seed** (unlike LiC/CollabLLM). |
| **n=19 vs 20** | Benchmark `telecom_small` has **20** tasks; the paper reports n=19 because `[service_issue]break_apn_settings[PERSONA:None]` is dropped (resolved in 1/20 cells; user sim emits `###STOP###` early). See `docs/reports/post_may18_progress_update_v4_bandaid_tau2.html:470,535`. |
| **Prior output dirs** | All in the fork, off-machine: `ctx_edit/outputs/post_may18_tau2_foundry/{gpt5_4_*,dsv4f_foundry_*}/`, `.../post_may18_tau2_foundry_kimi_retry/kimi_k2_6_foundry_w4_*/` (canonical); `post_may18_tau2_sweep/`, `post_may18_tau2_retry/` (OpenRouter substitutes, deprecated); paper-era `exp*/` (gpt-5-mini, `--num-trials 3`, seeds 42–44). |
| **N seeds** | **N=1, seed 42** for the 3-model Foundry sweep quoted in the General Response. (The older paper-era gpt-5-mini cell *was* 3 trials, reported best-of-3 — the thing iNYK attacked.) |
| **Setup cost** | `git clone` + py3.12 venv + `pip install -e` both repos + 734 MB tracked `data/`. Known gotchas: a `pyaudio`/`audioop` import shim via `.pth` (`docs/post_may18_tau2_followups.md:18`); Kimi needs `--workers 4` and a `ToolCall.arguments` JSON-string `field_validator`. Estimate ≥ half a day before the first run. |
| **Shared contract** | tau2's analyzer imports `AGENTIC_PROMPT_REGISTRY["tau2_v10"]` from `src/ctx_editor/strategies/analyzer_prompts.py:197-202` (with inline fallback). `scripts/aggregate_results.py:92-137` can parse legacy tau2 result dirs. |

### B.3 WildChat / Huang eval (T11)

| | |
|---|---|
| **Location** | In-repo: `src/ctx_editor/huang_eval/` — `run_phase1.py`, `run_phase2.py`, `pairwise_judge.py`, `replay.py`, `strategies.py`, `data_loader.py` (streams `allenai/WildChat-1M`). Hydra configs `config/huang_phase{1,2}.yaml`. Console scripts `ctx-editor-huang-phase1` / `-phase2`. |
| **Judge prompt** | `src/ctx_editor/huang_eval/prompts/pairwise_judge.txt` (46 lines; emits `quality_winner`, `ontopic_winner`, `confidence`; A/B order randomized by the caller's `rng`). AO system message: `prompts/ao_system_message.txt`. |
| **Two phases** | Phase 1 selects the "AO-failure turns" (30 conversations); Phase 2 runs the AC3 variants on that subset and judges pairwise vs AO. **Phase 2 requires a Phase 1 dir.** |
| **Variant slots** | `variants.s15` = AC3-Reset (v8), `variants.s2` = AC3-Gated-Reset (v11), `variants.s3` = AC3-Rewrite (v8), `variants.augment` = AC3-Augment (added post-paper). |
| **Prior output dirs** | `outputs/huang_eval/phase1/2026-03-24/02-22-57` (canonical Phase 1), `outputs/huang_eval/phase2/{2026-03-24/02-54-36, 2026-03-29/21-43-34}`, `outputs/post_neurips_ac3_phase3_huang/{s15,augment}_seed{42,43,44}_*`, `outputs/post_may26_wildchat_gpt54/`, `outputs/post_may18_r6_b3_wildchat/`, `outputs/post_may18_r3_wildchat_fills/`. **None on disk**; all present in `snapshot.tar.gz` under `ctx_editor/outputs/`. |
| **N seeds** | **N=3, real seeds 42/43/44** (`scripts/run_phase3_huang_redo.sh:36`). This is the one genuinely multi-seed result in the paper. Source of Reset 89.8 ± 1.4, Augment 92.1 ± 1.3. Report: `docs/reports/post_neurips_ac3_phase3_huang.md`. The gpt-5.4 cells (`post_may26_wildchat_gpt54`, incl. the Reset 88.6 vs Gated-Reset 74.1 comparison) are **seed 42 only, N=1**. |
| **⚠** | Non-Azure-OAI respondents (DeepSeek/Kimi) **need** `load_balancer=multi_endpoint_foundry`; without it Phase 2 silently reports "0 turns evaluated" (`post_neurips_ac3_phase3_huang.md:36`). |

**Launch (N=3 sweep):**
```bash
ctx-editor-huang-phase1 \
  num_conversations=30 respondent_model=gpt-5-mini \
  judge_model=gpt-5-mini classifier_model=gpt-5-mini \
  max_concurrent=5 max_scan=10000 seed=42

ctx-editor-huang-phase2 --multirun \
  phase1_dir=outputs/huang_eval/phase1/<DATE>/<TIME> \
  respondent_model=gpt-5-mini judge_model=gpt-5-mini analyzer_model=gpt-5-mini \
  variants.s15=true variants.augment=true \
  analyzer_prompt_versions.s15=v8 analyzer_prompt_versions.augment=v8 \
  max_concurrent=4 seed=42,43,44
```

### B.4 Memory / cheatsheet learning (T12/T13)

| | |
|---|---|
| **Location** | `src/ctx_editor/memory/` (`cheatsheet.py` = Reflect-then-Unify; `renderers.py:221-227` = 5 targets); offline driver `src/ctx_editor/execution/offline.py`; dispatch `run_experiment.py:189-198` (setup) and `:363-400` (offline early-return). Prompts `src/ctx_editor/memory/prompts/` (11 files). Doc `docs/memory_learning.md`. |
| **Hydra keys** | `memory.enabled`, `memory.source` (`null` \| `continual` \| `offline` \| `<path/to/snapshot.json>`), `memory.target` (`assistant`\|`context_editor`\|`edit_decision`\|`analyzer`\|`spec_curation`), `memory.save_path`, `memory.offline_trajectories`, `memory.offline_batch_size`, `memory.include_full_spec_q`, `memory.include_ground_truth_a`, `memory.include_oracle_spec`, `memory.oracle_spec_path`. **`memory.mode` and `memory.snapshot_path` do NOT exist** (the doc is stale). Update cadence = `execution.mode` (`batched`/`sequential` → continual updates; `parallel` → frozen). |
| **Configs** | `baseline_memory`, `append_analysis_memory`, `append_analysis_single_memory`, `append_analysis_spec_mem`, `append_analysis_mem_compliant`, `append_analysis_soft_cot_spec_mem{,_after}`, `context_edit_v2_memory`, `context_edit_memory`, `context_edit_cheatsheet`, `legacy/agentic_edit_memory`. |
| **WildChat×memory bridge** | `scripts/run_wildchat_memory.py` (argparse, 459 lines): train S1.5 no-memory → reflect+unify → eval held-out turns twice (no-mem vs frozen mem) with identical judge seed. Flags: `--phase2-dir` (req), `--phase1-dir` (req), `--model`, `--judge-model`, `--train-split`, `--seed`, `--memory-path`. Output hardcoded to `outputs/huang_eval/memory/{DATE}/{TIME}/`. |
| **Prior output dirs** | `outputs/huang_eval/memory/2026-03-30/04-00-10` (gpt-5-mini online, no improvement — ceiling), `outputs/huang_eval/memory/2026-03-30/13-57-16` (DeepSeek V3.2, train/eval split, **+13.8pp vs AO**, 1026-word cheatsheet from 25 train turns). Results in `docs/reports/multi_model_generalization.md:331-400`. **Not on disk**; in `snapshot.tar.gz`. |
| **N seeds** | N=1 per memory cell. |
| **⚠** | **No memory snapshot files exist anywhere on the machine** — no `*cheatsheet*.json`, no `memory_trained.json`, no `memories/`, no `outputs/replay_memories/`. Every cheatsheet must be re-learned or extracted from the snapshot tarball. Also: `experiment=<X>_memory` alone does not enable memory — pass `memory.enabled=true memory.source=...` on the CLI. |

**Launch (offline learning from saved trajectories):**
```bash
ctx-editor memory.enabled=true memory.source=offline \
  memory.offline_trajectories=outputs/rebuttal_random/full_baseline/results.json \
  memory.offline_batch_size=5 \
  memory.target=analyzer \
  memory.save_path=outputs/T12/mem_math.json
```

**Launch (frozen snapshot eval):**
```bash
ctx-editor experiment=append_analysis_memory task=dev_math_test model=gpt5_mini \
  execution.mode=parallel execution.max_concurrent=8 \
  memory.enabled=true memory.source=outputs/T12/mem_math.json memory.target=analyzer
```

Cleanest end-to-end template: `scripts/run_spec_curation_memory_experiment.sh` (train phase `:40-53`, three-condition eval `:66-89`).

---

## C. Prior-results inventory — where the v4-quoted numbers came from

| Claim in `replies/v4/` | Source | N | On disk? |
|---|---|---|---|
| CollabLLM MATH-Hard 95 / 90 / **100**; BigCodeBench 5 / 15 / **20** | `docs/reports/post_neurips_r2_collabllm.md`; dir `outputs/post_neurips_r2_collabllm_user_deepseek/` | **N=1** ⚠ | ❌ disk; ✅ in `snapshot.tar.gz` |
| tau2 3-model reward: FC 68.4/31.6/26.3, AO 0/0/0, best AC3 84.2/57.9/73.7 (n=19) | `docs/reports/post_may26_megatable_round_summary.md:33-41` (n=20 raw, 19 after dropping `break_apn_settings`); dirs `tau2_ctxe/ctx_edit/outputs/post_may18_tau2_foundry*/` | **N=1, seed 42** ⚠ | ❌ (in the GitHub fork) |
| tau2 paper-era Baseline 53.3 / Gated-Reset 48.3 (iNYK's quote) | `docs/paper_experiments_provenance.md:117-127`; gpt-5-mini, `--num-trials 3`, seeds 42–44 | N=3 trials, best-of-3 headlined | ❌ |
| WildChat Reset **89.8 ± 1.4**, Augment **92.1 ± 1.3** | `docs/reports/post_neurips_ac3_phase3_huang.md`; `outputs/post_neurips_ac3_phase3_huang/*_seed{42,43,44}_*` | **N=3, real seeds** ✅ | ❌ disk; ✅ in snapshot |
| WildChat gpt-5.4: Reset 88.6 vs Gated-Reset 74.1 (+14.5pp) | `outputs/post_may26_wildchat_gpt54/` | **N=1, seed 42** ⚠ | ❌ disk; ✅ in snapshot |
| WildChat range 72–92% | across all cells above | mixed | |
| LiC paired: Reset +15.9pp, 33/36 wins, sign-test p<0.0001 | `neurips_review/experiments/paired_analysis.py` over `docs/reports/post_neurips_ac3_phase{1,2}.md` | N/A (paired over 36 cells) | ✅ script + `paired_analysis_results.txt` |
| Random subset end-to-end: FC 87.5±2.0, Reset 100.0±0.0, Gated 99.1±1.2 | `outputs/rebuttal_random/{full,rep2,rep3}_*`; `neurips_review/experiments/exp1{,_reps}_results.txt` | **N=3 reps (seed override inert)** | ✅ **on disk** |
| Equal-budget reflection control: Reflection 97.5 / Reset 97.5 / FC 90.0 | `outputs/rebuttal_random/full_reflection`; `exp2_results.txt` | N=1 | ✅ on disk |
| Gate open rates 97.3% LiC (n=554), 98.3% CollabLLM (n=119) | not re-derived this session | — | ⚠ unverified — see Unknowns |
| Memory +13.8pp vs AO (DeepSeek V3.2, WildChat) | `docs/reports/multi_model_generalization.md:331-400`; `outputs/huang_eval/memory/2026-03-30/13-57-16` | N=1 | ❌ disk; ✅ in snapshot |

### Recovering the missing output dirs

`~/ac3/blob_staging/snapshot.tar.gz` (2.2 GB, root = `ctx_editor/`, dated 2026-06-12) contains the full `outputs/` tree — 56 186 entries, including `post_neurips_r2_collabllm_user_deepseek/`, `huang_eval/{phase1,phase2,phase2_full,phase2_s15_full,phase2_s2_full,memory,rejudge,rejudge_memory}/`, `post_neurips_ac3_phase3_{collabllm,huang}/`, `post_may26_wildchat_gpt54/`, `post_may18_r6_b3_{collabllm,wildchat}/`, all the dated `2026-0X-XX/` trees, and `runs.yaml`. Full listing cached at `/tmp/snap_list.txt`.

Selective extraction (do not extract the whole thing — it will land on top of the live repo):
```bash
mkdir -p ~/ac3/recovered
tar -xzf ~/ac3/blob_staging/snapshot.tar.gz -C ~/ac3/recovered \
  ctx_editor/outputs/post_neurips_r2_collabllm_user_deepseek \
  ctx_editor/outputs/post_neurips_ac3_phase3_huang \
  ctx_editor/outputs/huang_eval/phase1 \
  ctx_editor/outputs/huang_eval/phase2 \
  ctx_editor/outputs/huang_eval/memory \
  ctx_editor/outputs/post_may26_wildchat_gpt54
```
`supplementary.tar.gz` (289 MB) does **not** help — it is the sibling repos (`collabmem`, `lic`, `l3_dir`, …) and `collabmem/outputs` (14 GB) was deliberately excluded (`preservation_stage/MANIFEST.md`).

`ctx_editor/data/spider` appears in the snapshot as a **single entry** (the directory itself, empty) — Spider DBs are not recoverable from it. (`MANIFEST.md` says `testsuitedatabases.zip` was excluded as re-downloadable.)

---

## Unknowns / not found — do not guess

1. **Where the 97.3% / 98.3% gate-open rates came from.** Quoted in `replies/v4/03_reviewer_5YHP.md:67` and `README.md:82` with n=554 / n=119. No script found that computes them; no analysis artifact located. Would need to be recomputed from `edit_decision` fields in traces.
2. **Whether the exact 3 respondent models in the tau2 Foundry sweep are still servable.** DeepSeek-V4-Flash and Kimi-K2.6 are reachable on `mgalley-foundry2`; `gpt-5.4` on the Azure OAI side was **not** probed (the tau2 sweep used an Azure gpt-5.4, not TRAPI gpt-5.4-mini). Unverified.
3. **The `dl-openai-1` endpoint** named as the gpt-5.2 escalation route in `task_spec.md` — no config file in `config/load_balancer/` references it. Not probed. Unknown whether reachable.
4. **`outputs/2026-03-16/19-26-46`** — the actions replay source in `paper_experiments_provenance.md`. Present in the snapshot's `2026-03-16` tree (unverified at that timestamp), not on disk.
5. **Whether the tau2 fork's `ctx_edit/outputs/` was committed** to `matt-seb-ho/tau2_ctxe`. Repo is reachable but was not cloned. If outputs are gitignored there too, the tau2 N=1 numbers exist only in `docs/reports/*.md` on this machine.
6. **Reason `fxdata-shared` returns 401.** Could be a per-principal RBAC gap (fixable by asking for `Cognitive Services OpenAI User`) or a decommissioned resource. Not investigated.
7. **BigCodeBench execution-based scoring (T10).** No execution harness found in-repo; the judge is LLM-based (`evaluation/collabllm_metrics.py`). Whether upstream CollabLLM's executable tests can be wired in was not assessed.
8. **`docs/multi_run_variance_2026-05-07.md`** — linked twice from `paper_experiments_provenance.md` as the source of the appendix variance table. **The file does not exist** under `docs/`. The N=3 per-cell stds (5–7pp) it supposedly holds could not be verified.
9. **Whether the `analysis_cache` (242 shards, `outputs/analysis_cache/`) matches the models we will use.** It was built with gpt-5-mini v8/v11; passing `analysis_cache_dir=outputs/analysis_cache` with a gpt-5.4-mini analyzer may or may not key on the model name. Cache-key logic in `strategies/analysis_cache.py` was **not** read. Assume it is unsafe for T9 (analyzer-swap) runs until checked — a stale hit would silently invalidate the whole experiment.

---

## Files worth reading before dispatch

- `docs/paper_experiments_provenance.md` — the operator↔config↔prompt-version cheat sheet (with the two wrong config names noted above)
- `docs/strategy_name_history.md` — rename map
- `docs/ac3_variants_per_benchmark.md` — cross-benchmark coverage matrix (which variants exist where)
- `docs/replay_mode.md` — replay semantics + provenance
- `docs/benchmarks_index.md` — per-benchmark invocation index
- `neurips_review/experiments/run_exp1.sh`, `run_exp1_reps.sh`, `run_exp2.sh` — working launch templates on TRAPI
- `scripts/run_post_neurips_r2_collabllm{,_augment}.sh` — CollabLLM competent-sim templates
- `scripts/run_phase3_huang_redo.sh` — the WildChat N=3 template
- `scripts/run_spec_curation_memory_experiment.sh` — memory train→freeze→eval template
