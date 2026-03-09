# ctx_editor Documentation

Project documentation for the Context Editor evaluation system.

## Documents

| File | Covers |
|------|--------|
| [simulation.md](simulation.md) | `ConversationSimulator`, `ConversationTrace`, core types |
| [context_strategies.md](context_strategies.md) | All four strategies — mechanics, parameters, memory integration, design notes |
| [memory_learning.md](memory_learning.md) | Memory-based learning: `CheatsheetMemory`, `CheatsheetUpdater`, `renderers.py`, pipeline integration |

## Quick Start

```bash
pip install -e ".[all]"

# Run with default config
ctx-editor

# Common overrides
ctx-editor experiment=baseline model=gpt4o task=math
ctx-editor experiment=context_edit execution.max_concurrent=10
ctx-editor experiment=baseline memory.enabled=true memory.source=continual execution.mode=sequential
```

## Key Source Paths

```
src/ctx_editor/
  run_experiment.py          # Main entry point (Hydra)
  core/
    simulator.py             # ConversationSimulator
    trace.py                 # ConversationTrace
    types.py                 # Shared dataclasses
  strategies/
    baseline.py              # No-op (pass-through)
    context_edit.py          # Always-edit
    agentic_edit.py          # Model decides whether to edit
    reflection.py            # Append-only reflection
  agents/
    user_agent.py            # Standard UserAgent
    natural_user_agent.py    # Budget-based shard revelation
    length_constrained_user_agent.py
    system_agent.py          # Verification + answer extraction
  memory/
    base.py                  # MemoryModule, MemoryUpdater ABCs
    cheatsheet.py            # CheatsheetMemory, CheatsheetUpdater
    renderers.py             # Target-specific trajectory rendering (assistant/context_editor/edit_decision)
    prompts/                 # Per-target reflection prompt templates
  execution/
    parallel.py              # ParallelRunner
    batched.py               # BatchedRunner (batched learning)
  identify_false_negatives.py  # Post-hoc error analysis
  config/                    # Hydra YAML configs
```
