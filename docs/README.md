# ctx_editor Documentation

Project documentation for the Context Editor evaluation system.

## Documents

| File | Covers |
|------|--------|
| [architecture.md](architecture.md) | System overview, data flow, key concepts |
| [run_experiment.md](run_experiment.md) | `run_experiment.py` entry point walkthrough |
| [simulation.md](simulation.md) | `ConversationSimulator`, `ConversationTrace`, core types |
| [strategies.md](strategies.md) | All four context strategies |
| [context_strategies.md](context_strategies.md) | Deep-dive: strategy mechanics, parameters, memory integration, design notes |
| [memory_learning.md](memory_learning.md) | Memory-based learning: `CheatsheetMemory` + `CheatsheetUpdater`, deployment in pipeline |
| [agents.md](agents.md) | `UserAgent`, `SystemAgent`, variant user agents |
| [evaluation.md](evaluation.md) | `identify_false_negatives.py` — post-hoc analysis |

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
  execution/
    parallel.py              # ParallelRunner
    batched.py               # BatchedRunner (batched learning)
  identify_false_negatives.py  # Post-hoc error analysis
  config/                    # Hydra YAML configs
```
