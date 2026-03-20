# ctx_editor Documentation

Project documentation for the Context Editor evaluation system.

## Documents

| File | Covers |
|------|--------|
| [simulation.md](simulation.md) | `ConversationSimulator`, `ConversationTrace`, core types |
| [context_strategies.md](context_strategies.md) | S0/S1/S2 strategies, ConversationAnalyzer, legacy strategies, memory integration |
| [memory_learning.md](memory_learning.md) | Memory-based learning: `CheatsheetMemory`, `CheatsheetUpdater`, `renderers.py`, pipeline integration |
| [project_motivation.md](project_motivation.md) | Research background, LiC failure modes, comparisons with ERGO and Huang et al. |
| [newleaf_refactor.md](newleaf_refactor.md) | Option 2 rendering, S0/S1/S2 introduction, error attribution |
| [newer_leaf_refactor.md](newer_leaf_refactor.md) | Two-query analyzer (v6), AnalysisResult redesign, edited context format |
| [false_negatives_and_test_subset.md](false_negatives_and_test_subset.md) | User-sim error classification, false negative identification, test subset construction |
| [code_experiment_analysis.md](code_experiment_analysis.md) | Why context editing hurts code, trace analysis, reflection advantage, cheatsheet comparison |

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
    baseline.py              # S0: No-op (pass-through)
    append_analysis.py       # S1: Append analysis, no rewriting
    context_edit_v2.py       # S2: Analysis-driven context rewriting
    analyzer.py              # ConversationAnalyzer (two-query, used by S1 & S2)
    prompts/                 # Externalized analyzer prompts (v4, v5, v6)
    context_edit.py          # [Legacy] Always-edit
    agentic_edit.py          # [Legacy] Model decides whether to edit
    reflection.py            # [Legacy] Append-only reflection
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
