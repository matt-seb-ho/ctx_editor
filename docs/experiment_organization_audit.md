# Experiment Organization Audit

How are LiC, CollabLLM, WildChat/Huang, and Tau2 experiments organized in this repo today, and how should we restructure to scale up cleanly? Companion to [ac3_variants_per_benchmark.md](ac3_variants_per_benchmark.md).

## Current state — at a glance

| | LiC | CollabLLM | WildChat (Huang) | Tau2 |
|---|---|---|---|---|
| **Location** | `src/ctx_editor/` | `src/ctx_editor/` | `src/ctx_editor/huang_eval/` | **`/home/agent/tau2-bench/`** (separate repo) |
| **Entry point** | `ctx-editor` CLI (Hydra) → `run_experiment.py` | `python -m ctx_editor.run_collabllm` (Hydra) | `python -m ctx_editor.huang_eval.run_phase1 / run_phase2` (argparse) | `python ctx_edit/run_parallel.py` (argparse) |
| **Config system** | Hydra (`experiment/`, `task/`, `model/`) | Hydra, shares `model/` configs, has own `experiment/collabllm_*.yaml` | argparse + hardcoded constants | argparse + `config.json` dumped per run |
| **Strategy abstraction** | `ContextStrategy` protocol in `strategies/base.py` | Reuses same `ContextStrategy` classes | **Inline functions in `replay.py`** (does not implement the protocol) | **Custom agent classes** in `ctx_edit/agents.py` (inherit tau2's `HalfDuplexAgent`, not LiC) |
| **Analyzer** | `ConversationAnalyzer` (async) | Reuses same | Reuses same | **Reimplemented**, synchronous (`ctx_edit/analyzer.py`) |
| **Simulator** | `ConversationSimulator` | `CollabLLMSimulator` (parallel implementation, shares `ConversationTrace`) | None — replay.py is per-turn | tau2's `Orchestrator` |
| **Output dir** | `outputs/{date}/{time}/` | `outputs/{date}/{time}/` | `outputs/huang_eval/phase{1,2}/{date}/{time}/` | `/home/agent/tau2-bench/ctx_edit/outputs/exp*` |
| **Multi-seed support** | Yes (via `seed` in config) | No (hardcoded seed=42) | Seed flag exists but each invocation = one run | Yes (`--num-trials`, seeds 42,43,44…) |
| **Memory** | First-class (`memory/`) | Plumbed but unused | Separate script | Separate offline builder |

## Where the divergence comes from

LiC was built deliberately; the other three were stood up in a sprint before the COLM 2026 deadline to show generalization. The pattern is consistent:

- **CollabLLM** is the *good* fast port: it threaded itself through LiC's Hydra/strategy abstractions, so it inherits everything LiC has. It just hasn't been exercised yet (no memory configs run, no seed sweep).
- **Huang eval** is a *partial* fast port: it reuses the model client and the analyzer, but reimplemented the context-edit step inline because the AO-failure-turn structure doesn't map onto LiC's per-turn simulator loop.
- **Tau2** is a *full reimplementation*: tau2-bench's `Orchestrator` already owns the conversation loop, so the LiC simulator is irrelevant. The analyzer was rewritten synchronously to fit tau2's call style and reshape prompts for tool-calling.

None of this was wrong for a sprint. The problem now is that **the same AC3 operation lives in four different shapes** (LiC class hierarchy, inline functions in replay.py, custom tau2 agent classes, and config-level variants in CollabLLM), so adding "AC3-Gated-Reset everywhere" or "AC3-Rewrite with new v12 prompts everywhere" requires touching four code paths and remembering which knobs are flags vs YAML vs hardcoded constants.

## Concrete pain points (what blocks scaling today)

1. **No common AC3 contract across benchmarks.** A new variant has to be implemented as: a strategy class for LiC/CollabLLM, an inline function for Huang, and an agent subclass for Tau2. Three different places. Easy to drift.
2. **Knob locations vary.** Analyzer prompt version is a strategy arg in LiC, a hardcoded constant in `huang_eval/replay.py:189`, and inline prompt text in `tau2-bench/ctx_edit/analyzer.py`. Swapping in a v12 prompt is three edits.
3. **No multi-seed / multi-run wrapper.** Only LiC and Tau2 have it. CollabLLM hardcodes seed=42 + n=20 — the variance documented in `docs/reports/collabllm_baseline_comparison.md` (math swings 40–60% across runs) means we have no statistically meaningful signal yet.
4. **Experiment configs sprawl.** `config/experiment/` has 50+ YAMLs with overlapping `append_analysis_*.yaml` variants and no registry — discoverability is poor.
5. **Legacy strategies still in `strategies/__init__.py`** (`ContextEditStrategy` v1, `AgenticEditStrategy`, `ReflectionStrategy`). Per `CLAUDE.md` they're kept "for comparison" but no scripts actively reference them. Easy cleanup.
6. **Output layouts differ.** Hard to write one analysis/replay script that works across all four. The Huang and Tau2 outputs have richer per-trace metadata; LiC and CollabLLM output the bare hydra-style flat trees.
7. **Tau2 is in a separate repo with no pinned reference.** The boundary is reasonable (tau2-bench has its own upstream), but right now there's no documented contract between the two — only the memory note pointing to `/home/agent/tau2-bench/ctx_edit/`.

## Proposal — phased refactor

The goal is **one AC3 contract, four benchmark adapters**. Concretely:

### Phase 0 — Safe cleanups (do these immediately, near-zero risk)

- [ ] Add a top-level **`docs/benchmarks_index.md`** mapping each benchmark to its entry point, config dir, current best result, and "what we'd run next."
- [ ] Add this audit + the AC3 variant doc to the top-level docs (already done).
- [ ] Move the legacy strategies (`ContextEditStrategy` v1, `AgenticEditStrategy`, `ReflectionStrategy`) into `strategies/legacy/` and re-export them so existing scripts keep working. Mark `__deprecated__`.
- [ ] In `config/experiment/`, separate `_archive/` for one-off ablation configs no longer in active use. Keep the active set small and named consistently (`<benchmark>_<variant>.yaml`).
- [ ] Rename the canonical AC3 classes (or add aliases) so the code matches the paper terminology — `AppendAnalysisStrategy → AC3AugmentStrategy`, `ContextEditV2Strategy → AC3GatedResetStrategy`, etc. Keep old names as aliases for one release.

### Phase 1 — Unify the analyzer (the most reused piece)

- [ ] Lift the analyzer prompt set into a versioned registry (`strategies/analyzer_prompts/{v8,v9,v10,v11}.py`) instead of having them embedded inline across `huang_eval/replay.py` and `tau2-bench/ctx_edit/analyzer.py`.
- [ ] Provide a sync wrapper for the analyzer so Tau2 can use it without rewriting the async signature. (Or make Tau2's loop async-compatible — likely smaller change.)
- [ ] Single source of truth: when we say "v12 prompts", every benchmark uses the same v12.

### Phase 2 — Define one AC3 contract

- [ ] Promote `ContextStrategy` to a benchmark-neutral interface with explicit hooks: `prepare_context(trace, memory) -> messages` is already most of it. Add `on_turn_start`/`on_run_end` if benchmarks need it.
- [ ] Make `huang_eval/replay.py` route its S1.5/S2/S3 paths through real `ContextStrategy` classes. The "replay" framing becomes: load AO failures, instantiate strategy, run it. Adds AC3-Augment to Huang for free.
- [ ] In Tau2, write thin `Strategy` → `HalfDuplexAgent` adapters so the LiC strategy objects can be dropped in. Tau2 still owns the loop; LiC owns the context-edit op.

### Phase 3 — Unify experiment driving

- [ ] One **multi-seed/multi-config runner** (`scripts/run_sweep.py`) that takes `benchmark × variant × seeds × n` and dispatches. Each benchmark exposes a thin "runner adapter" that knows how to invoke its own pipeline; the sweep harness handles parallelism, retries, and result aggregation.
- [ ] Standardize output layout: every run writes `config.json` + `results.json` + optional `traces/` regardless of benchmark. The Tau2 layout is the best template here.
- [ ] One results-loader / aggregator that produces the Table 1 rows for all four benchmarks from a single command.

### Phase 4 — Tau2 boundary

Decide one of:
- (a) Move `tau2-bench/ctx_edit/` into a `bench/tau2/` subdirectory of this repo and depend on tau2-bench as a library, OR
- (b) Keep the separate repo but add a pinned commit + a checked-in `docs/benchmarks_index.md` entry that documents the contract.

(a) is cleaner long-term but means a one-time migration of the tau2 outputs and scripts. (b) is what's effectively in place; just needs documentation.

## What I'd start with

If you want to start landing changes now, **Phase 0** is all reversible and high-value. It:
- Documents the current state for collaborators / future you.
- Cleans up legacy code without changing behavior.
- Renames strategies to match the paper, which is a paper-readiness step anyway.

Phase 1 (analyzer prompt registry) is the highest-leverage real refactor — every benchmark will use the same v12 prompts the moment they're added — and it touches only prompt files, not control flow.

Phases 2–4 are bigger surface area and warrant explicit alignment before starting. In particular, Phase 4(a) involves moving real working code between repos and shouldn't happen mid-experiment.

## Phase 0 — completed in this pass

- ✅ Legacy strategies moved to `src/ctx_editor/strategies/legacy/` (`AgenticEditStrategy`, `ContextEditStrategy` v1, `ReflectionStrategy`). Re-exported from `ctx_editor.strategies` for backwards compatibility — every existing Hydra `_target_:` string still resolves.
- ✅ Legacy experiment configs moved to `src/ctx_editor/config/experiment/legacy/`.
- ✅ Canonical AC3 class names introduced with aliases preserving the old names:
  - `AppendAnalysisStrategy` → `AC3AugmentStrategy`
  - `ContextEditV2Strategy` → `AC3ResetStrategy` (gating is a config knob, not a separate class)
  - `ContextCompactionStrategy` → `AC3RewriteStrategy`
- ✅ Rename history documented in [strategy_name_history.md](strategy_name_history.md) — durable record of old names so 2026-Q1 logs and notes remain decodable.
- ✅ This audit doc + [ac3_variants_per_benchmark.md](ac3_variants_per_benchmark.md) checked in.

User decisions taken (May 2026):
- Legacy → archive to `strategies/legacy/`, not deleted.
- Naming → rename with aliases + historical-name doc.
- Tau2 boundary → defer.

## Pre-existing bugs surfaced during the audit

Not introduced by Phase 0, but worth flagging since they block running anything on this machine:

- `src/ctx_editor/huang_eval/run_phase2.py:69` — `SyntaxError`: keyword arg `memory=None` (with default) precedes positional `run_s2: bool` (no default) in `process_failure_turn()`. Introduced in commit `22b2f3b` ("feat: add WildChat memory learning for S1.5 analyzer"). The file imports cleanly nowhere; Huang eval must have been run on the other machine before this regression, or the entrypoint isn't actually used (the memory script in `scripts/run_wildchat_memory.py` is). Either way, this needs fixing before any new Huang runs from this machine.

## Open questions still pending

- Phase 1 timing: ready to lift the analyzer prompts into a versioned registry now, or hold until the next paper round?
- Phase 2/3: when we decide to unify the runner & strategy contract, do you want this to happen before or after the next experiment batch? Doing it before means a few-day refactor; doing it after means the next batch reuses the current sprawl.
