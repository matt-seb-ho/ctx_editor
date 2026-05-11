# AC3 Variants by Benchmark

The "AC3" method is the family of context-editing operations the analyzer can apply at each turn. On LiC we have four named variants (Augment, Reset, Rewrite, Gated-Reset). This doc maps those variants to what is actually implemented for each non-LiC benchmark, so we can see at a glance what's missing.

## Canonical AC3 variants (from LiC)

| Variant | What the analyzer does at each turn | LiC class |
|---|---|---|
| **AC3-Augment** | Append analyzer output as a system note. Trace is untouched. | `AppendAnalysisStrategy` (`strategies/append_analysis.py`) |
| **AC3-Reset** | If analyzer flags issues, reset the trace and replay with a clean user message + analysis. | `ContextEditV2Strategy` w/o gating cap |
| **AC3-Rewrite** | LLM rewrites the conversation history into a compacted briefing before each assistant call. | `ContextCompactionStrategy` (and the legacy `ContextEditStrategy`) |
| **AC3-Gated-Reset** | Like Reset, but gated by analyzer severity + a hard `max_resets` cap so we don't thrash. Current production setting. | `ContextEditV2Strategy` (`max_resets=3`, `min_turns=3`) — `strategies/context_edit_v2.py` |

A few legacy strategies (`AgenticEditStrategy`, `ReflectionStrategy`, `ContextEditStrategy` v1) are still present but are not part of the AC3 lineup and are kept only for backwards comparability — they should be marked deprecated in a cleanup pass.

## Cross-benchmark coverage

| Variant | LiC | CollabLLM | WildChat (Huang) | Tau2 |
|---|---|---|---|---|
| **Augment** | ✅ `AppendAnalysisStrategy` | ✅ `collabllm_append_analysis.yaml` → same class | ❌ Not implemented | ⚠️ Tried as "hint-injection" (v10.4), regressed, abandoned |
| **Reset** | ✅ `ContextEditV2Strategy` (no cap) | ✅ via same class, different params | ✅ "S1.5" inline in `huang_eval/replay.py` (template-based programmatic reset, v8 analyzer) | ✅ "S2" — `ContextEditAgent` in `tau2-bench/ctx_edit/agents.py` (programmatic template, v10 analyzer) |
| **Rewrite** | ✅ `ContextCompactionStrategy` | ✅ `collabllm_compaction.yaml` → same class. Also `collabllm_ergo.yaml` → `ERGORestartStrategy` (related but rewrites the *user side*) | ✅ "S3" inline in `huang_eval/replay.py` (LLM compaction, v8 analyzer) | ✅ "S3" — `ContextRewriteAgent` (Q1+Q2 → LLM Q3 briefing). Currently **net-negative** vs S2; loses tool result fidelity. |
| **Gated-Reset** | ✅ `ContextEditV2Strategy` with `min_turns`/`max_resets` (current production) | ⚠️ The same class is used, but no benchmark-specific evaluation sweeps over gating params | ⚠️ "S2" in Huang eval uses the **v11 analyzer with gating**, so it occupies this slot. Not a separate config. | ❌ Not implemented as a distinct strategy (S2 always emits "strategic direction", never an "augment only" mode) |
| **AC3 + memory** | ✅ Memory built in via `CheatsheetMemory` + `OfflineMemoryLearner` | ❌ `setup_memory()` exists but is never exercised in any `collabllm_*.yaml` | ⚠️ Bolt-on via `scripts/run_wildchat_memory.py` — post-hoc, not integrated into Phase 1/2 | ⚠️ Bolt-on via `tau2-bench/ctx_edit/build_cheatsheet.py` (offline cheatsheet, exp12). Net-zero so far. |

## Per-benchmark notes

### CollabLLM (`src/ctx_editor/run_collabllm.py`)
- The **cleanest port**: every variant is just a Hydra config that instantiates the same LiC strategy class via `_target_`. No reimplementation. Adding a new AC3 variant to CollabLLM is a one-line config change.
- Gaps: no gated-reset sweep, no memory variant tested, fixed `n=20` and `seed=42` everywhere — variance dominates the headline numbers (e.g. math swings 40–60% across runs per `docs/reports/collabllm_baseline_comparison.md`).

### WildChat / Huang eval (`src/ctx_editor/huang_eval/`)
- The **most divergent port**. S1.5 / S2 / S3 are implemented as **inline functions inside `huang_eval/replay.py`** rather than `ContextStrategy` subclasses. They reuse `ConversationAnalyzer` from the shared strategies package, but the actual context-edit operation is duplicated logic.
- Phase 1 produces "AO failure turns" (where full-context beats assistant-omit); Phase 2 then evaluates S1.5/S2/S3 on that subset against AO. No `Augment` slot — the experiment frames the question as "given AO failures, which AC3-style rewrite recovers best?", so AC3-Augment was never plumbed in.
- Memory is a separate script (`scripts/run_wildchat_memory.py`) that reuses Phase 2 outputs and learns a frozen cheatsheet — disconnected from the main pipeline.
- All knobs are argparse flags + hardcoded constants (temperatures, timeouts, analyzer version per strategy). No Hydra.

### Tau2 (`/home/agent/tau2-bench/ctx_edit/`, **separate repo**)
- **Fully parallel codebase**: no imports from `ctx_editor`. The analyzer (`ctx_edit/analyzer.py`) is a synchronous rewrite of LiC's two-query pattern, with prompts redesigned for tool-calling and backend state (`TASK_SPEC_PROMPT_V10`, `COMPARE_PROMPT_V10_S2`, etc.).
- Agents inherit from `tau2.HalfDuplexAgent` rather than LiC abstractions (the AC3 op happens inside `_get_response`).
- S0/AO/S2/S3 exist; no separate Gated-Reset; v10.4 attempted Augment-style hint injection and regressed. S3 (Rewrite) is net-negative because Q3 LLM rewrite loses tool result fidelity — fixable in principle, not investigated since.
- Configuration is argparse → `config.json` saved per run (reasonable reproducibility once you know the flags).

## Implications for scaling experiments

To run "AC3 × {Augment, Reset, Rewrite, Gated-Reset} × seeds × n_samples" symmetrically across all four benchmarks today, you would need:

1. **CollabLLM**: enable the missing memory configs and add multi-seed support in the runner. No new strategy code.
2. **WildChat/Huang**: lift S1.5/S2/S3 out of `replay.py` into the shared `ContextStrategy` interface so adding Augment/Gated-Reset is a config change, not a code change. Plumb the memory pipeline back into Phase 2.
3. **Tau2**: either (a) port the LiC strategy classes into the tau2-bench repo, or (b) accept the parallel codebase and add Augment/Gated-Reset agents alongside S2/S3. Decide whether to fix S3 (Rewrite) before scaling — currently it would just produce a larger losing run.

The path-of-least-resistance refactor is covered in [experiment_organization_audit.md](experiment_organization_audit.md).
