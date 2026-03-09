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
  renderers.py    # Target-specific trajectory rendering functions
  prompts/
    assistant_reflection.txt       # Reflection prompt for assistant target
    context_editor_reflection.txt  # Reflection prompt for context_editor target
    edit_decision_reflection.txt   # Reflection prompt for edit_decision target
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
        target: str = "assistant",          # NEW: "assistant" | "context_editor" | "edit_decision"
        reflection_prompt: Optional[str] = None,
        reflection_prompt_file: Optional[str] = None,
        model: str = "gpt-4o-mini",
        update_on_success: bool = True,
        update_on_failure: bool = True,
        include_full_spec_q: bool = False,
        include_ground_truth_a: bool = False,
    )
```

### `target` parameter

Controls two things automatically:
1. **Which reflection prompt to use** — loaded from `memory/prompts/{target}_reflection.txt`
2. **How the trajectory is rendered** — via `memory/renderers.py`

| Target | Prompt focus | Rendering |
|--------|-------------|-----------|
| `assistant` | Response strategy, pitfalls, clarification patterns | Active messages only |
| `context_editor` | What to preserve/remove, edit quality | All messages (visible + archived) with edit markers |
| `edit_decision` | When to edit, false positives/negatives | Decision events + full active conversation |

A custom `reflection_prompt` or `reflection_prompt_file` overrides the target default entirely.

**Grounding options** — optional oracle context provided during reflection:
- `include_full_spec_q`: inject the fully-specified single-turn question
- `include_ground_truth_a`: inject the ground truth answer

### `update_from_trajectory(memory, trajectory, model_client)`

Per-trajectory update:

1. Skip if `update_on_success`/`update_on_failure` filters apply
2. Render trajectory via `self.renderer(trajectory)` (target-specific)
3. Format the reflection prompt with: current memory content, task name, sample ID, outcome, turn count, rendered conversation, optional grounding info
4. Call the LLM (temperature 0.3)
5. Call `memory.update(new_content)` with the response

### `batch_update(memory, trajectories, model_client)`

Synthesizes insights from multiple trajectories in a **single LLM call**. All trajectories are concatenated into one prompt using the target-specific renderer. This is used by `BatchedRunner` after each batch.

> **Note**: `batch_update` is the current default in `BatchedRunner` but is considered suboptimal. The planned replacement (Change 2 in `plans/memory_features_plan.md`) is a Reflect-then-Unify algorithm: parallel per-trajectory reflections → single unify call.

## `renderers.py` — Trajectory Rendering

Three rendering functions, registered in `RENDERERS: dict[str, Callable]`:

- **`render_for_assistant`** — active messages only (role/content), omits edit internals
- **`render_for_context_editor`** — all messages including archived ones, with `--- CONTEXT EDIT ---` markers at reset boundaries showing the editor's condensed output
- **`render_for_edit_decision`** — lists each `edit_decision` log entry (should_edit + reasoning), then appends the full active conversation for context

Source data: `trajectory.trace["messages"]` (full list with `visible` flags) and `trajectory.trace["logs"]` (typed event log).

---

## Deployment in the Experiment Pipeline

### Configuration

Memory behavior is controlled under the `memory:` key in `config.yaml`:

```yaml
memory:
  enabled: false
  source: null          # null | path to frozen .json | "continual"
  target: assistant     # assistant | context_editor | edit_decision
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

All reflection prompts share the same template variables:
`{current_cheatsheet}`, `{task_name}`, `{sample_id}`, `{outcome}`, `{score}`, `{num_turns}`, `{conversation}`, `{grounding_info}`

### `prompts/assistant_reflection.txt`

Default for `target="assistant"`. Asks the model to reflect on: response strategies, information extraction from the user, premature assumptions, effective clarifying questions, and task-specific pitfalls.

### `prompts/context_editor_reflection.txt`

Default for `target="context_editor"`. Asks the model to reflect on: what information was essential to preserve, what wrong reasoning should have been removed, whether the edit helped the assistant recover, signals that an edit was overdue, and what structure works best for the edited context.

### `prompts/edit_decision_reflection.txt`

Default for `target="edit_decision"`. Asks the model to reflect on: whether edit decisions were correct in hindsight, conversation signals that predicted benefit, false positives/negatives, optimal timing for edits, and patterns of context pollution that reliably indicate an edit is needed.
