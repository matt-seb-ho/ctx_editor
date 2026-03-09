# Memory-Based Learning (Dynamic Cheatsheet)

This document describes the `memory/` module and how it integrates into the experiment pipeline to implement memory-based learning.

---

## Motivation

Memory-based learning lets the system accumulate knowledge across problem instances and apply it to future ones — without any gradient updates. The simplest instantiation is the **Dynamic Cheatsheet** (following Suzgun et al., 2025): a mutable text document that grows more informative as the system processes more trajectories.

Memory is a general mechanism. It can be targeted at different components:

| Target | What it learns |
|--------|---------------|
| **Baseline assistant** | Strategies and pitfalls for the task domain |
| **Context editor** | Which information to preserve vs. compress |
| **Agentic decision-maker** | When to trigger a context edit |

---

## Module: `memory/`

```
src/ctx_editor/memory/
  base.py         # MemoryModule, MemoryUpdater ABCs
  cheatsheet.py   # CheatsheetMemory, CheatsheetUpdater (concrete implementation)
  prompts/
    reflection.txt    # Default prompt for per-trajectory reflection
    context_editor.txt  # Prompt template for context editor use
```

---

## `MemoryModule` ABC (`memory/base.py`)

Abstract interface for all memory implementations:

```python
class MemoryModule(ABC):
    @property
    def content(self) -> str: ...
    @property
    def version(self) -> int: ...
    def update(self, new_content: str) -> None: ...
    def clone(self) -> "MemoryModule": ...
    def save(self, filepath: str) -> None: ...
    @classmethod
    def load(cls, filepath: str) -> "MemoryModule": ...
```

---

## `CheatsheetMemory` (`memory/cheatsheet.py`)

The current concrete implementation. A versioned, mutable text container with full version history.

```python
class CheatsheetMemory(MemoryModule):
    content: str        # current text
    version: int        # monotonically increasing
    history: list[str]  # all prior versions
    metadata: dict      # per-version update info
```

**Key methods:**

| Method | Behavior |
|--------|----------|
| `update(new_content)` | Replace content (saves old version to history, increments version) |
| `append(additional_content)` | Append to existing content (also versioned) |
| `rollback()` | Revert to previous version; returns False if no history |
| `get_version(n)` | Retrieve content at version `n` |
| `save(filepath)` | Serialize to JSON |
| `load(filepath)` | Deserialize from JSON (classmethod) |
| `clone()` | Deep copy — used by `BatchedRunner` to freeze memory state per batch |

Each call to `update()` or `append()` also stores a metadata entry keyed by the new version number, recording which trajectory triggered the update.

---

## `CheatsheetUpdater` (`memory/cheatsheet.py`)

Reflects on completed trajectories and rewrites the memory with an LLM call.

```python
class CheatsheetUpdater(MemoryUpdater):
    def __init__(
        self,
        reflection_prompt: Optional[str] = None,
        reflection_prompt_file: Optional[str] = None,
        model: str = "gpt-4o-mini",
        update_on_success: bool = True,
        update_on_failure: bool = True,
        include_full_spec_q: bool = False,
        include_ground_truth_a: bool = False,
    )
```

**Grounding options** — optional oracle context provided during reflection to help the model understand what the correct behavior should have been:
- `include_full_spec_q`: inject the fully-specified single-turn question
- `include_ground_truth_a`: inject the ground truth answer

### `update_from_trajectory(memory, trajectory, model_client)`

The correct per-trajectory update path:

1. Skip if `update_on_success`/`update_on_failure` filters apply
2. Format the reflection prompt with: current memory content, task name, sample ID, outcome, turn count, full conversation, optional grounding info
3. Call the LLM (temperature 0.3)
4. Call `memory.update(new_content)` with the response

The default reflection prompt (`prompts/reflection.txt`) asks the model to consider: patterns/strategies, critical information to preserve, effective questions, task-specific insights, and what could have been safely compressed.

### `batch_update(memory, trajectories, model_client)`

Synthesizes insights from multiple trajectories in a **single LLM call**. All trajectories are concatenated into one prompt. This is a rougher update used by `BatchedRunner` after each batch.

> **Note**: `batch_update` is the current default in `BatchedRunner` but is considered suboptimal. The planned replacement is sequential `update_from_trajectory` calls followed by a unification step.

---

## Deployment in the Experiment Pipeline

### Configuration

Memory behavior is controlled under the `memory:` key in `config.yaml`:

```yaml
memory:
  enabled: false
  source: null          # null | path to frozen .json | "continual"
  target: assistant     # assistant | context_editor
  save_path: null       # checkpoint path
  include_full_spec_q: false
  include_ground_truth_a: false
```

- `source: null` — memory disabled
- `source: "continual"` — start empty, update after each batch/problem
- `source: "/path/to/file.json"` — load a frozen memory snapshot (no updates)

A pre-built experiment config exists for the continual-learning case:

```yaml
# experiment/context_edit_cheatsheet.yaml
strategy:
  _target_: ctx_editor.strategies.ContextEditStrategy
  use_memory: true
  memory_target: context_editor

memory:
  enabled: true
  source: continual
  target: context_editor
```

### Initialization (`run_experiment.py: setup_memory`)

```
enabled=false  →  return None
source="continual" or source=None  →  return CheatsheetMemory(content="")
source=<path>  →  return CheatsheetMemory.load(source)
```

### Injection into context (`strategies/base.py: BaseStrategy`)

`BaseStrategy._inject_memory_to_trace()` appends the memory content into the live conversation trace inside `<cheatsheet>` tags. Injection is one-shot per trace — subsequent calls are no-ops (guarded by `memory_injected` log entry).

**Injection targets:**
- `"system"` — appended to the system message (assistant sees it every turn)
- `"user"` — appended to the last user message

### Per-strategy memory behavior

| Strategy | `use_memory` effect |
|----------|------------------------|
| `BaselineStrategy` | Injects into system or user message once at turn 1 |
| `ContextEditStrategy` | Provides memory to the context editor LLM in its prompt (as `{memory_section}`); or injects into the assistant's system message |
| `AgenticEditStrategy` | Passes memory to both the decision-maker and the editor |
| `ReflectionStrategy` | Includes memory content in the reflection generation prompt |

### Execution modes and update cadence

The `execution.mode` config key controls how updates happen:

| Mode | Runner | Update cadence |
|------|--------|---------------|
| `parallel` | `ParallelRunner` | No updates — memory is frozen (or None) |
| `batched` | `BatchedRunner.run()` | `batch_update` after every batch of `batch_size` problems; within a batch the memory is frozen |
| `sequential` | `BatchedRunner.run_sequential()` | `update_from_trajectory` after every individual problem |

In batched mode, `BatchedRunner` saves a checkpoint to `{save_path}.batch{N}` after each batch and the final memory to `save_path` at the end.

In sequential mode, each simulator receives a `.clone()` of the current memory — the running memory is updated after the result returns, so problems within a batch don't interfere.

### Data flow summary

```
load_samples()
    │
    ▼
setup_memory()  →  CheatsheetMemory (empty or loaded)
    │
    ├─[parallel]─────────────────────────────────────────┐
    │                                                     │
    ├─[batched]──► BatchedRunner.run()                   │
    │                 for each batch:                     │
    │                   ParallelRunner (frozen memory)    │
    │                   batch_update()  ◄── CheatsheetUpdater
    │                   save checkpoint                   │
    │                                                     │
    └─[sequential]─► BatchedRunner.run_sequential()       │
                        for each problem:                 │
                          simulator.run()                 │
                          update_from_trajectory()        │
                                                          │
    All paths ───────────────────────────────────────────►│
                                                          ▼
                                                   list[SimulationResult]
                                                   + final memory saved
```

---

## Prompts

### `prompts/reflection.txt`

Used by `CheatsheetUpdater` when reflecting on a single trajectory. Template variables: `{current_cheatsheet}`, `{task_name}`, `{sample_id}`, `{outcome}`, `{score}`, `{num_turns}`, `{conversation}`.

Asks the model to produce a 200–400 word, categorized memory covering: patterns, critical information, effective questions, task insights, and context management heuristics (what to preserve vs. compress).

### `prompts/context_editor.txt`

Injected into `ContextEditStrategy`'s editor prompt as `{memory_section}`. Instructs the editor to use the memory to identify which information is most important to preserve during compression.
