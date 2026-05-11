# Strategy Name History

The `strategies/` package was renamed in May 2026 to match the paper's "AC3-{Augment,Reset,Rewrite,Gated-Reset}" terminology. The old class names are kept as **module-level aliases** (literally `OldName = NewName`) so:

- All existing Hydra `_target_:` strings keep resolving.
- All existing pickled traces, log filenames, and config dumps remain readable.
- All older docs and project memories referring to the old names still make sense.

This document is the durable record of what was renamed when, so future-you reading a 2026-Q1 experiment log can decode it.

## Rename map (May 2026)

| Old class name | Paper-era label | Canonical class name | AC3 variant |
|---|---|---|---|
| `AppendAnalysisStrategy` | "S1" | `AC3AugmentStrategy` | AC3-Augment |
| `ContextEditV2Strategy` | "S2" | `AC3ResetStrategy` | AC3-Reset / AC3-Gated-Reset (same class, gating is a config knob: `min_turns`, `max_resets`) |
| `ContextCompactionStrategy` | "S3" | `AC3RewriteStrategy` | AC3-Rewrite |

Unchanged (prior-work baselines, not AC3):

- `BaselineStrategy` — S0, no editing
- `AssistantOmitStrategy` — drops all assistant messages (Huang et al.)
- `ERGORestartStrategy` — ERGO-style user-side rewrite
- `OmitAssistantStrategy`, `ConcatenateUserStrategy` — older prior-work variants in `prior_work_baselines.py`
- `ConversationAnalyzer` — shared two-query analyzer used by all AC3 variants

## Demoted to `strategies/legacy/`

These were experimental/superseded and no longer part of the AC3 family. They remain importable from `ctx_editor.strategies` for backwards compatibility but new work should not use them.

| Class | Reason for demotion |
|---|---|
| `AgenticEditStrategy` | Separate decision prompt for gating. Superseded by `AC3ResetStrategy` where gating is folded into the analyzer's structured output. |
| `ContextEditStrategy` (v1) | Always-rewrite. Superseded by `AC3RewriteStrategy` (cleaner two-step analyze → compact pipeline). |
| `ReflectionStrategy` | Reflection-style append. Superseded by `AC3AugmentStrategy` which produces a structured analysis. |

## Per-benchmark naming, for cross-referencing logs

The same operation goes by different short labels in different benchmarks' experiment logs. Cross-reference:

| AC3 variant | LiC log label | CollabLLM config | Huang eval label | Tau2 label |
|---|---|---|---|---|
| AC3-Augment | "S1" / "append_analysis" | `collabllm_append_analysis` | — (not implemented in huang_eval) | — (v10.4 hint-injection attempt, abandoned) |
| AC3-Reset | "S2" / "context_edit_v2" | `collabllm_context_edit_v2` | "S1.5" (programmatic) / "S2" (v11 gated) | "S2" (`ContextEditAgent`) |
| AC3-Rewrite | "S3" / "compaction" | `collabllm_compaction` (also `collabllm_ergo` is related) | "S3" (LLM compaction) | "S3" (`ContextRewriteAgent`) |
| AC3-Gated-Reset | "AC3-Gated-Reset" / "context_edit_v2 (gated)" | (same as Reset, config-controlled) | "S2" with v11 gating analyzer | (no separate variant; S2 always emits direction) |

## Pre-rename references to expect in older artifacts

If you grep older notes, expect to find these strings — they all refer to one of the canonical classes above:

- `S0`, `S1`, `S1.5`, `S2`, `S3`, `AO`, `FC`
- `AppendAnalysis*`, `ContextEditV2*`, `ContextCompaction*`
- `context_edit_v2_*.yaml`, `append_analysis_*.yaml`, `*_compaction.yaml`
- v8 / v9 / v10 / v11 prompts (analyzer prompt versions, orthogonal to strategy class)
- Tau2: v10 / v10.4 (also orthogonal — v10.4 was an unsuccessful hint-injection attempt, not a strategy class change)

## What is NOT renamed (yet)

- Config YAML filenames in `config/experiment/` still use the old labels (`append_analysis.yaml`, `context_edit_v2.yaml`, etc.). Renaming these would break every recorded experiment command in our docs and project memory, so we keep them. New configs can be named with AC3 prefix if desired.
- Output directory layout (`outputs/{date}/{time}/`) is unchanged.
- Project memory files (`MEMORY.md` etc.) still reference old names; that's intentional — they are point-in-time snapshots.
