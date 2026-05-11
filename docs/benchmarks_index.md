# Benchmarks Index

One-stop reference for the four benchmarks the paper reports on. Keep this short — link out to the deeper docs.

## LiC (Lost in Conversation)

- **Where**: this repo, `src/ctx_editor/`
- **Entry point**: `ctx-editor` (Hydra CLI) → `src/ctx_editor/run_experiment.py`
- **Configs**: `src/ctx_editor/config/{experiment,task,model}/*.yaml`
- **Outputs**: `outputs/{YYYY-MM-DD}/{HH-MM-SS}/`
- **Quick run**: `ctx-editor experiment=context_edit_v2 model=gpt5_mini task=math`
- **AC3 coverage**: all four variants (Augment, Reset, Rewrite, Gated-Reset), memory variants too
- **Deep docs**: [`context_strategies.md`](context_strategies.md), [`newer_leaf_refactor.md`](newer_leaf_refactor.md), [`memory_learning.md`](memory_learning.md)

## CollabLLM

- **Where**: this repo, `src/ctx_editor/run_collabllm.py` + Hydra
- **Configs**: `src/ctx_editor/config/collabllm.yaml`, `src/ctx_editor/config/experiment/collabllm_*.yaml`
- **Outputs**: same root layout as LiC
- **Quick run**: `python -m ctx_editor.run_collabllm experiment=collabllm_context_edit_v2`
- **AC3 coverage**: Augment, Reset, Rewrite via shared LiC strategy classes. No memory variant exercised. Fixed seed=42 and n=20 → high run-to-run variance.
- **Deep docs**: [`collabllm.md`](collabllm.md), [`collabllm_eval_loop.md`](collabllm_eval_loop.md), [`reports/collabllm_*.md`](reports/)

## WildChat (Huang eval reproduction)

- **Where**: this repo, `src/ctx_editor/huang_eval/`
- **Entry points** (argparse, not Hydra):
  - `python -m ctx_editor.huang_eval.run_phase1 …` — produces AO-failure-turn list
  - `python -m ctx_editor.huang_eval.run_phase2 …` — runs S1.5/S2/S3 on those failures *(currently has a syntax error from commit `22b2f3b`; needs fix before re-running on this machine)*
  - `python scripts/run_wildchat_memory.py …` — post-hoc memory variant on phase2 outputs
- **Outputs**: `outputs/huang_eval/phase{1,2}/{date}/{time}/`
- **AC3 coverage**: Reset (S1.5), Gated-Reset (S2, v11), Rewrite (S3), and **Augment** (new in Phase 2 — `generate_augment` / `HuangAC3AugmentStrategy`). Not yet exposed via a `run_phase2.py` CLI flag, but callable from Python.
- **Implementation**: AC3 ops now live in `huang_eval/strategies.py` as `ContextStrategy` subclasses. The `generate_*` functions in `replay.py` are thin wrappers preserving the paper-era message layout.
- **Deep docs**: [`reports/huang_eval_*.md`](reports/)

## Tau2 (telecom_small)

- **Where**: **separate repo** at `/home/agent/tau2-bench/ctx_edit/`
- **Why separate**: tau2-bench has its own upstream (sierra-research). We forked the test harness in `ctx_edit/` rather than absorbing the whole repo.
- **Entry points** (argparse):
  - `python /home/agent/tau2-bench/ctx_edit/run_parallel.py --strategy s2 --num-trials 3 …`
  - `python /home/agent/tau2-bench/ctx_edit/run_experiment.py …` (single-shot variant)
- **Configs**: per-run `config.json` saved alongside `results.json` in each output dir
- **Outputs**: `/home/agent/tau2-bench/ctx_edit/outputs/exp*` and `traces/`
- **AC3 coverage**: S0/AO/S2(Reset)/S3(Rewrite). **No Augment, no separate Gated-Reset.** S3 is currently net-negative due to LLM rewrite losing tool result fidelity.
- **Caveats**: fully parallel codebase — does not import `ctx_editor`. Custom synchronous analyzer in `ctx_edit/analyzer.py`, custom agent classes in `ctx_edit/agents.py`. Memory via offline cheatsheet builder `build_cheatsheet.py`.
- **Deep docs**: [`tau2.md`](tau2.md), `/home/agent/tau2-bench/ctx_edit/EXPERIMENT_LOG.md`

## Cross-cutting

- [`paper_experiments_provenance.md`](paper_experiments_provenance.md) — which `(strategy, prompt version, config)` produced each paper result
- [`ac3_variants_per_benchmark.md`](ac3_variants_per_benchmark.md) — which AC3 variants each benchmark actually implements
- [`experiment_organization_audit.md`](experiment_organization_audit.md) — code-organization audit + proposed refactor phases
- [`strategy_name_history.md`](strategy_name_history.md) — rename map and historical name decoder
