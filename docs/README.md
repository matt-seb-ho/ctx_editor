# ctx_editor Documentation

Project documentation for the Context Editor evaluation system.

**See [`index.md`](index.md) for the full list of docs**, organized topically and chronologically. This README covers only the starter docs for new readers.

## Starter docs

| File | Covers |
|------|--------|
| [index.md](index.md) | Full doc index (every `.md` file under `docs/`, topical + chronological) |
| [benchmarks_index.md](benchmarks_index.md) | One-stop reference for LiC / CollabLLM / WildChat / Tau2 entry points |
| [simulation.md](simulation.md) | `ConversationSimulator`, `ConversationTrace`, core types |
| [context_strategies.md](context_strategies.md) | Strategy protocol, AC3 lineup, ConversationAnalyzer integration |
| [strategy_name_history.md](strategy_name_history.md) | Old class names ↔ AC3 names + S0/S1/S2/S3 decoder for older notes |
| [memory_learning.md](memory_learning.md) | Memory-based learning (Dynamic Cheatsheet) |
| [project_motivation.md](project_motivation.md) | Research background, comparisons with ERGO and Huang et al. |
| [paper_experiments_provenance.md](paper_experiments_provenance.md) | Which strategy + prompt version produced each paper result |
| [experiment_organization_audit.md](experiment_organization_audit.md) | May-2026 code-organization audit and phased refactor plan |

## Quick Start

```bash
pip install -e ".[all]"

# Run with default config
ctx-editor

# Common overrides
ctx-editor experiment=baseline model=gpt4o task=math
ctx-editor experiment=context_edit_v2 execution.max_concurrent=10
ctx-editor experiment=append_analysis memory.enabled=true memory.source=continual execution.mode=sequential

# Offline memory learning from saved trajectories (no new simulations)
ctx-editor memory.enabled=true memory.source=offline \
  memory.offline_trajectories=outputs/baseline_run/results.json \
  memory.target=context_editor memory.save_path=memories/editor_v1.json
```

## Key Source Paths

```
src/ctx_editor/
  run_experiment.py          # Main entry point (Hydra)
  core/
    simulator.py             # ConversationSimulator (Option 2 rendering)
    trace.py                 # ConversationTrace
    types.py                 # Shared dataclasses
  strategies/
    baseline.py              # No-op (pass-through)
    append_analysis.py       # AC3-Augment (alias: AppendAnalysisStrategy)
    context_edit_v2.py       # AC3-Reset / AC3-Gated-Reset (alias: ContextEditV2Strategy)
    context_compaction.py    # AC3-Rewrite (alias: ContextCompactionStrategy)
    analyzer.py              # ConversationAnalyzer (dispatches via analyzer_prompts registry)
    analyzer_prompts.py      # Versioned registry for analyzer prompt sets (v4–v11, v8_soft, s1, …)
    prompts/                 # Externalized analyzer prompt template files
    legacy/                  # Superseded: AgenticEditStrategy, ContextEditStrategy (v1), ReflectionStrategy
  agents/
    user_agent.py            # Standard UserAgent
    natural_user_agent.py    # Budget-based shard revelation
    length_constrained_user_agent.py
    system_agent.py          # Verification + answer extraction
  memory/
    base.py                  # MemoryModule, MemoryUpdater ABCs
    cheatsheet.py            # CheatsheetMemory, CheatsheetUpdater
    renderers.py             # Target-specific trajectory rendering
    prompts/                 # Per-target reflection prompt templates
  execution/
    parallel.py              # ParallelRunner
    batched.py               # BatchedRunner (batched learning)
    offline.py               # OfflineMemoryLearner (learn from saved trajectories)
  identify_false_negatives.py  # Post-hoc error analysis (per-run)
  build_test_subset.py         # Aggregate across runs → test subset
  config/                    # Hydra YAML configs
```
