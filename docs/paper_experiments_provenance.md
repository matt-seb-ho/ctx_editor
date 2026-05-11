# Paper Experiments → Code Provenance

Durable record of which code paths produced each result in the COLM/NeurIPS 2026 paper. Read this if you need to:

- Reproduce a published number.
- Decode an older project-memory entry that uses the pre-rename names (`AppendAnalysisStrategy`, `ContextEditV2Strategy`, etc.).
- Map paper terminology (AC3-Augment / Reset / Rewrite / Gated-Reset) to a concrete `(strategy class, analyzer prompt version, config file)` tuple.

The active draft is `writing/overleaf_repo/neurips/neurips_2026_conference.tex`. See [strategy_name_history.md](strategy_name_history.md) for the rename map and [ac3_variants_per_benchmark.md](ac3_variants_per_benchmark.md) for the cross-benchmark coverage matrix.

## Strategy → AC3 → paper-label cheat sheet

| Paper label | AC3 variant | Canonical class (post-rename) | Pre-rename class name (older logs/configs use this) |
|---|---|---|---|
| Baseline / FC / "full context" | — | `BaselineStrategy` | (unchanged) |
| AO (Huang et al. baseline) | — | `AssistantOmitStrategy` | (unchanged) |
| Concat User (LiC baseline) | — | `ConcatenateUserStrategy` | (unchanged) |
| ERGO (Khalid et al. baseline) | — | `ERGORestartStrategy` | (unchanged) |
| **ACC-Augment** | AC3-Augment | `AC3AugmentStrategy` | `AppendAnalysisStrategy` |
| **ACC-Reset** | AC3-Reset | `AC3ResetStrategy` (gating disabled) | `ContextEditV2Strategy` |
| **ACC-Gated-Reset** | AC3-Gated-Reset | `AC3ResetStrategy` with `min_turns` + `max_resets` set | `ContextEditV2Strategy` w/ gating |
| **ACC-Rewrite** | AC3-Rewrite | `AC3RewriteStrategy` | `ContextCompactionStrategy` |

The paper uses "ACC" / "ACE" / "\method" depending on the draft revision; the code prefix is uniformly "AC3" post-rename.

## Table 1 (a) — LiC

GSM8K math / HumanEval code / Spider database / BFCL actions. Replay mode (last-turn regeneration with fixed user-sim trajectory). Model: `gpt-5-mini` (assistant + analyzer) at temperature 1.0. Sample sizes: math n=20, code n=18, database n=25, actions n=23.

| Paper row | Class instantiated | Hydra experiment config | Analyzer prompt version | Notes |
|---|---|---|---|---|
| Baseline (full context) | `BaselineStrategy` | `experiment=baseline` | n/a | |
| Baseline + Memory | `BaselineStrategy` + memory | `experiment=baseline_memory` | n/a | Sanity check that memory alone doesn't help |
| AO | `AssistantOmitStrategy` | `experiment=assistant_omit` | n/a | Huang et al. 2026 baseline |
| Concat User | `ConcatenateUserStrategy` | `experiment=concat_baseline` (also `prior_work_baselines.OmitAssistantStrategy`) | n/a | LiC paper baseline |
| ERGO | `ERGORestartStrategy` | `experiment=ergo` | n/a | Khalid et al. 2025 |
| **ACC-Augment** | `AC3AugmentStrategy` (`AppendAnalysisStrategy`) | `experiment=append_analysis` | **v8** (and `v9` for the `_v9` variant cell) | |
| ACC-Augment + Memory | `AC3AugmentStrategy` + cheatsheet | `experiment=append_analysis_memory` | **v8** | Online memory regime |
| **ACC-Reset** | `AC3ResetStrategy` (`ContextEditV2Strategy`), gating disabled or wide | `experiment=context_edit_v2` w/ permissive `max_resets` | **v8** | |
| ACC-Reset + Memory | `AC3ResetStrategy` + cheatsheet | `experiment=context_edit_v2_memory` | **v8** | |
| **ACC-Gated-Reset** (N=3 multi-run row) | `AC3ResetStrategy` with `min_turns=3, max_resets=3` | `experiment=context_edit_v2` (math/code/database) and `experiment=context_edit_v2_accumulate` (actions) | **v8** | Mean over 3 replay runs. Replay sources: `data/baseline_traces_v2/{task}` for math/code/database; `outputs/2026-03-16/19-26-46` for actions. See [`multi_run_variance_2026-05-07.md`](multi_run_variance_2026-05-07.md). |

Caveat for the **actions** column: actions uses `context_edit_v2_accumulate.yaml` which adds the explicit instruction "repeat all function calls in the final turn" on top of `context_edit_v2`. This is documented in the paper appendix (§A.2) and is necessary because BFCL evaluation expects the full function-call set in the final response. See project memory `project_actions_accumulate_gotcha.md`.

The Gated-Reset row's N=3 spread is captured in [`docs/multi_run_variance_2026-05-07.md`](multi_run_variance_2026-05-07.md). Per-cell stds are 5–7pp.

## Table 1 (b) — CollabLLM

MATH-Hard / BigCodeBench. GPT-5 judge correctness. n=20 per task, seed=42. Run via `python -m ctx_editor.run_collabllm experiment=<config>`.

| Paper row | Class | Config | Analyzer prompt | Notes |
|---|---|---|---|---|
| Baseline (full context) | `BaselineStrategy` | `experiment=collabllm_baseline` | n/a | |
| AO | `AssistantOmitStrategy` | `experiment=collabllm_assistant_omit` | n/a | |
| **ACC-Rewrite** | `AC3RewriteStrategy` (`ContextCompactionStrategy`) | `experiment=collabllm_compaction` | **s1** (simplified single-query, content-filter safe) | "Rewrite uses single-pass full-conversation analysis (no structural exclusion)" — `s1` analyzer is the single-query format. |

Not in headline Table 1 but present in `config/experiment/`:
- `collabllm_append_analysis.yaml` → AC3-Augment with `s1` analyzer
- `collabllm_context_edit_v2.yaml` → AC3-Gated-Reset with `s1` analyzer
- `collabllm_ergo.yaml` → ERGO baseline

These were run as comparison conditions during the COLM sprint (see `docs/reports/collabllm_baseline_comparison.md`) but only the three rows above made the headline table.

## Table 1 (c) — WildChat / Huang eval

Pairwise win rates over 30 WildChat conversations (n=173–178 turns per row). All models: `gpt-5-mini` (respondent, analyzer, judge, classifier). Generation temp 0.7; analysis temp 0.0.

| Paper row | Function in `huang_eval/replay.py` | Post-Phase-2 strategy class | Analyzer prompt version | Notes |
|---|---|---|---|---|
| **ACC-Reset** | `generate_s15(...)` | `HuangAC3ResetStrategy` (in `huang_eval/strategies.py`) | **v8** | Programmatic reset, no LLM rewrite. Always edits (100% edit rate row in the paper). |
| **ACC-Rewrite** | `generate_s3(...)` | `HuangAC3RewriteStrategy` | **v8** | Analyzer + LLM compaction step. 84.3% edit rate (the analyzer gates whether to rewrite). |
| **ACC-Gated-Reset** | `generate_s2(...)` | `HuangAC3GatedResetStrategy` | **v11** | v11 prompt is "mid-task reflection" framing generalized from tau2 v10. Gates on `min_turns=2` and `needs_edit`. 72.3% edit rate. |

Phase 2 of the refactor (this commit) replaced the inline `generate_*` implementations with `ContextStrategy` subclasses in `huang_eval/strategies.py`. The `generate_*` functions are now thin wrappers that preserve the original message layout bit-for-bit (the paper's pairwise judges were scored against the original layout — changing it would invalidate stored judgments). New in Phase 2 (not in the paper): `HuangAC3AugmentStrategy` / `generate_augment` provides AC3-Augment for Huang eval — available for future runs but not used in the published numbers.

Reproduction (post-Phase-3 Hydra CLI):

```bash
ctx-editor-huang-phase1 \
    num_conversations=30 respondent_model=gpt-5-mini \
    judge_model=gpt-5-mini classifier_model=gpt-5-mini \
    max_concurrent=5 max_scan=10000 seed=42

ctx-editor-huang-phase2 \
    phase1_dir=outputs/huang_eval/phase1/<DATE>/<TIME> \
    respondent_model=gpt-5-mini judge_model=gpt-5-mini \
    analyzer_model=gpt-5-mini max_concurrent=5 \
    variants.s15=true variants.s2=true seed=42
```

Pre-Phase-3 (argparse) form, for decoding older project memory / docs:

```bash
python -m ctx_editor.huang_eval.run_phase1 \
    --num-conversations 30 --respondent-model gpt-5-mini \
    --judge-model gpt-5-mini --classifier-model gpt-5-mini \
    --max-concurrent 5 --max-scan 10000 --seed 42

python -m ctx_editor.huang_eval.run_phase2 \
    --phase1-dir outputs/huang_eval/phase1/<DATE>/<TIME> \
    --respondent-model gpt-5-mini --judge-model gpt-5-mini \
    --analyzer-model gpt-5-mini --max-concurrent 5 \
    --run-s15 --run-s2 --seed 42
```

The WildChat memory ablation (Appendix table) used:

```bash
python scripts/run_wildchat_memory.py \
    --phase1-dir <p1> --phase2-dir <p2> \
    --model gpt-5-mini --judge-model gpt-5-mini \
    --train-split 0.33 --seed 42
```

## Table 1 (d) — Tau2-bench (telecom_small)

Per-trial success rates across seeds 42–44. Model: `gpt-5-mini` (agent + analyzer). Code lives in the **separate repo** `/home/agent/tau2-bench/ctx_edit/`.

| Paper row | Class (in `tau2-bench/ctx_edit/agents.py`) | Run command | Analyzer prompt version |
|---|---|---|---|
| Baseline | `LLMAgent` (tau2 upstream) | `python run_parallel.py --strategy s0 --num-trials 3 --agent-llm openai/gpt-5-mini` | n/a |
| AO | `AssistantOmitAgent` | `python run_parallel.py --strategy ao --num-trials 1 --agent-llm openai/gpt-5-mini` | n/a (Huang baseline) |
| **ACC-Gated-Reset** | `ContextEditAgent` | `python run_parallel.py --strategy s2 --num-trials 3 --agent-llm openai/gpt-5-mini --analyzer-model openai/gpt-5-mini` | **v10** (tau2-specific, inline in `ctx_edit/analyzer.py`) |

Per-trial breakdown (paper §A.3): Baseline {45.0, 55.0, 60.0}%, ACC-Gated-Reset {40.0, 65.0, 40.0}%, AO {0.0}% (seed-invariant). Table 1 reports the best-of-3 for Baseline and ACC-Gated-Reset.

ACC-Rewrite for tau2 exists in code (`ContextRewriteAgent`, v10 + Q3 LLM rewrite) but is **not** in the headline table because it is net-negative vs S2 due to LLM-rewrite-induced tool-result fidelity loss. See `/home/agent/tau2-bench/ctx_edit/EXPERIMENT_LOG.md` exp11 onwards.

**Tau2's `v10` analyzer prompts are NOT in this repo's registry** (`strategies/analyzer_prompts.py`); they live inline in the tau2-bench repo. Aligning them is deferred (Phase 4) per user decision.

## Other paper figures/tables

| Table / Figure | Notes |
|---|---|
| Table 2 (multi-model LiC) | Same as Table 1(a) but swaps the assistant model across {GPT-5-mini, GPT-5, Claude Sonnet 4.5, DeepSeek V3.2, Qwen3 80B}. Strategy = ACC-Reset (`AC3ResetStrategy`), analyzer = `gpt-5-mini` v8, hard subset selected by baseline failure rate via GPT-5.2. See `scripts/run_replay_*.sh`. |
| Table 3 (cognitive hazard / soft attention) | Ablates the analyzer's hard-attention structure. Configs: `append_analysis_soft.yaml` (v8_soft), `append_analysis_soft_cot.yaml` (v8_soft_cot), `append_analysis_single.yaml` (v8_single combined-prompt). All instantiate `AC3AugmentStrategy` with different analyzer prompt versions. |
| Appendix WildChat memory table | DeepSeek V3.2 added as second respondent model. Uses `scripts/run_wildchat_memory.py` (offline regime, train_split=0.33). |
| Appendix variance table | N=3 replay-mode reruns of ACC-Gated-Reset across all 4 LiC tasks. Captured in [`multi_run_variance_2026-05-07.md`](multi_run_variance_2026-05-07.md). |

## Output directories

Where the actual run outputs sit, for spot-checking. Note the timestamp tree under `outputs/` is on the *other* machine for CollabLLM and WildChat — this machine has Tau2 outputs (`/home/agent/tau2-bench/ctx_edit/outputs/`) and a subset of LiC outputs (`outputs/`).

| Benchmark | Output location | Run-config saved? |
|---|---|---|
| LiC | `outputs/{YYYY-MM-DD}/{HH-MM-SS}/.hydra/` | Yes (Hydra `overrides.yaml` + `config.yaml`) |
| CollabLLM | `outputs/{YYYY-MM-DD}/{HH-MM-SS}/.hydra/` (other machine) | Yes (Hydra) |
| WildChat / Huang | `outputs/huang_eval/phase{1,2}/{DATE}/{TIME}/config.json` (other machine) | Yes (CLI args dumped to `config.json`) |
| Tau2 | `/home/agent/tau2-bench/ctx_edit/outputs/exp*/{config,results}.json` | Yes (CLI args dumped to `config.json`) |

## Post-rename diff for old configs / logs / project memory

When you read older artifacts and see one of these strings, here's what it maps to today. (Same content as [strategy_name_history.md](strategy_name_history.md) but with the experiment context for quick lookup.)

| Found in old artifact | Read it as |
|---|---|
| `AppendAnalysisStrategy` in code/Hydra | `AC3AugmentStrategy` |
| `ContextEditV2Strategy` | `AC3ResetStrategy` (and gated config = ACC-Gated-Reset) |
| `ContextCompactionStrategy` | `AC3RewriteStrategy` |
| `S1` in Huang or paper drafts | ACC-Augment |
| `S1.5` in Huang | ACC-Reset (programmatic, v8) — see Table 1(c) row 1 |
| `S2` in Huang | ACC-Gated-Reset (v11) — see Table 1(c) row 3 |
| `S2` in tau2 | ACC-Gated-Reset (v10) — Table 1(d) ACC row |
| `S3` in Huang | ACC-Rewrite (v8 + LLM compaction) — Table 1(c) row 2 |
| `S3` in tau2 | ACC-Rewrite (v10 + Q3) — exists in code, not in Table 1 |
| `S0`, `FC` | Baseline (full context) |
| `AO` | `AssistantOmitStrategy` (Huang baseline) |
| `v8` analyzer | Current production two-query, hard attention. Default for LiC and Huang S1.5/S3. |
| `v9` analyzer | v8 spec + v9 compare prompt (adds `<corrective_direction>`). Used by `append_analysis_v9.yaml`. |
| `v11` analyzer | v8 spec + mid-task reflection compare prompt. Used by Huang S2. Generalized from tau2's v10. |
| `v10` analyzer | **Tau2-specific**, lives inline in `/home/agent/tau2-bench/ctx_edit/analyzer.py`. NOT in the LiC registry. |
| `v10.4` (Tau2 only) | Failed hint-injection experiment, not in the paper. |
| Pre-rename project memory using "S1", "S2", "S3" | Apply the table above; flavor depends on which benchmark the memory describes. |
