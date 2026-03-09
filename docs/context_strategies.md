# Context Strategies

This document covers the four context management strategies investigated in the ctx_editor framework, how they work mechanically, and how they relate to the core research problem.

---

## Background: Context Pollution

The LiC (Lost in Conversation) benchmark showed that multi-turn performance degrades significantly relative to single-turn. Two failure modes drive this:

1. **Premature answers** — the assistant guesses before all information is revealed, then future turns build on that wrong attempt.
2. **Invalid assumptions** — early assumptions get contradicted by later shards, but the prior reasoning remains in context and distracts the model.

We call this accumulated wrong reasoning *context pollution*. The strategies in this framework are treatments for it:

| Strategy | Mechanism | History preserved? |
|---|---|---|
| `BaselineStrategy` | No-op — full history passes through | Yes, always |
| `ContextEditStrategy` | Compress history before every turn | No — replaced by edited summary |
| `AgenticEditStrategy` | Model decides whether to compress | Conditional |
| `ReflectionStrategy` | Append a state summary; keep full history | Yes, plus annotation |

---

## The `ContextStrategy` Protocol

`strategies/base.py`

All strategies implement a single method:

```python
async def prepare_context(
    trace: ConversationTrace,
    memory: Optional[MemoryModule],
    model_client: ModelClient,
) -> list[Message]
```

**Contract:** `prepare_context()` **mutates** the trace (e.g., resets the conversation, appends reflections) and returns the active messages to use for the next assistant call. The simulator calls this once per turn before the assistant generates a response.

### `BaseStrategy` (shared utilities)

The concrete base class provides two utilities used by all strategies:

- `_inject_memory_to_trace(trace, memory, target)` — appends memory content to either the system message or the last user message. Idempotent: only injects once per trace (guards via `memory_injected` log entry).
- `_is_memory_injected(trace)` — checks the trace log for prior injection.

---

## Strategies

### 1. BaselineStrategy

`strategies/baseline.py`

**What it does:** Returns the full conversation history unchanged. This is the control condition.

**Trace mutations:** Only the optional one-time memory injection.

**Key parameters:**

| Parameter | Default | Description |
|---|---|---|
| `use_memory` | `False` | Whether to inject the memory module |
| `memory_target` | `"system"` | Where to inject: `"system"` or `"user"` |

**Flow:**
```
if use_memory and memory not yet injected:
    inject memory to system (or user) message
return trace.get_active_messages()
```

**Hydra config:** `experiment=baseline`

---

### 2. ContextEditStrategy

`strategies/context_edit.py`

**What it does:** Before every assistant turn (after the first), calls a separate editor model to compress the full conversation into a concise summary. The trace is then *reset* to just three messages: `[system, "[Prior conversation context, condensed]" (user), edited_context (assistant)]` plus the current user message. All prior turns are dropped from the active context.

This is the primary intervention: replacing polluted history with a clean, dense summary.

**Trace mutations:** Calls `trace.reset_conversation(new_messages, label="context_edit")`. Future turns build off the edited context, not the original history.

**Editor prompt (default):** Asks the editor to preserve valid requirements, constraints, and progress while removing wrong answer attempts, invalidated assumptions, and outdated intermediate work.

**Key parameters:**

| Parameter | Default | Description |
|---|---|---|
| `editor_model` | `"gpt-4o-mini"` | Model used for compression |
| `editor_prompt` | `DEFAULT_EDITOR_PROMPT` | Custom prompt string |
| `editor_prompt_file` | `None` | Path to a prompt file (overrides `editor_prompt`) |
| `use_memory` | `False` | Whether to include memory in editor input |
| `memory_target` | `"context_editor"` | `"context_editor"` = feed to editor; `"assistant"` = inject into system message |

**Flow:**
```
if turn == 0:
    return trace.get_active_messages()  # nothing to compress yet

build editor_input from conversation_str + optional memory section
edited_context = editor_model.generate(editor_input)
log "context_edit_output"
reset trace to: [system, user:"[Prior context, condensed]", assistant:edited_context, user:last_message]
return trace.get_active_messages()
```

**Hydra configs:**
- `experiment=context_edit` — no memory
- `experiment=context_edit_cheatsheet` — memory fed to the editor, with continual learning enabled

---

### 3. AgenticEditStrategy

`strategies/agentic_edit.py`

**What it does:** Adds a gating step before editing. A decision model first analyzes the conversation and outputs `yes/no` for whether compression is beneficial. If yes, it performs an edit (like `ContextEditStrategy`) with the decision analysis injected into the editor prompt. If no, it falls back to `BaselineStrategy`.

The decision analysis is passed to the editor so the editor doesn't have to re-analyze the conversation from scratch.

**Trace mutations:** Same as `ContextEditStrategy` when editing; same as `BaselineStrategy` otherwise. Decision is always logged (`"edit_decision"` log entry).

**Decision prompt:** Lists five failure modes (premature answers, invalid assumptions, outdated work, redundant exchanges, scattered information) and asks for structured `<notes>` + `<edit_decision>yes/no</edit_decision>`.

**Key parameters:**

| Parameter | Default | Description |
|---|---|---|
| `decision_model` | `"gpt-4o-mini"` | Model for the edit/no-edit decision |
| `editor_model` | `"gpt-4o-mini"` | Model for compression (when editing) |
| `edit_threshold_turns` | `3` | Skip decision entirely if fewer than this many user turns |
| `use_memory` | `False` | Whether to use memory |
| `memory_target` | `"context_editor"` | Same semantics as `ContextEditStrategy` |

**Flow:**
```
decision = _should_edit(trace)   # → {should_edit, reasoning, notes}
log "edit_decision" (always)

if decision.should_edit:
    build editor_input with decision.notes injected as <decision_analysis>
    perform edit (same reset logic as ContextEditStrategy)
else:
    return baseline_strategy.prepare_context(trace, ...)
```

**Hydra config:** `experiment=agentic_edit`

---

### 4. ReflectionStrategy

`strategies/reflection.py`

**What it does:** Generates a brief 2–4 sentence summary of the conversation state and appends it to the last user message inside `<conversation_state_reflection>` tags. The full conversation history is preserved — this is append-only. The system message receives a one-time addendum explaining these tags so the assistant doesn't treat them as user text.

This is an **ablation** of context editing: it provides similar diagnostic information (what went wrong, what to focus on) but without the rewrite. The key difference is that the polluted history remains visible.

**Trace mutations:**
1. First call: appends `REFLECTION_SYSTEM_ADDENDUM` to system message (once).
2. Every qualifying call: appends `<conversation_state_reflection>...</conversation_state_reflection>` block to the last user message (persists in trace).

**Reflection prompt (default):** Asks the model to summarize the user's core goal, key revealed information, constraints, progress made, and — critically — to explicitly flag any wrong answer attempts or invalidated assumptions.

**Key parameters:**

| Parameter | Default | Description |
|---|---|---|
| `reflection_model` | `"gpt-4o-mini"` | Model for reflection generation |
| `reflection_prompt` | `DEFAULT_REFLECTION_PROMPT` | Custom prompt string |
| `reflection_prompt_file` | `None` | Path to a prompt file |
| `use_memory` | `False` | Whether to include memory in reflection prompt |
| `min_turns_for_reflection` | `2` | Minimum user turns before reflecting (skips early turns) |

**Flow:**
```
if num_user_turns < min_turns_for_reflection:
    return trace.get_active_messages()

if system addendum not yet added:
    append REFLECTION_SYSTEM_ADDENDUM to system message

reflection = reflection_model.generate(conversation_str)
log "reflection_generated"
append <conversation_state_reflection>reflection</...> to last user message
return trace.get_active_messages()
```

**Hydra config:** `experiment=reflection_only`

---

## Memory Integration

All strategies optionally accept a `MemoryModule` object. Memory contains learned takeaways from prior trajectories (see `memory_learning.md`). How it's used depends on the strategy:

| Strategy | `memory_target` options | Effect |
|---|---|---|
| `BaselineStrategy` | `"system"`, `"user"` | Injected once into system or last user message |
| `ContextEditStrategy` | `"context_editor"`, `"assistant"` | Fed to editor in prompt, or injected into assistant's system message |
| `AgenticEditStrategy` | `"context_editor"`, `"assistant"` | Same as `ContextEditStrategy` |
| `ReflectionStrategy` | (implicit) | Included in the reflection generation prompt |

Memory injection is always **idempotent** — once injected to a trace, subsequent calls are no-ops.

---

## Design Notes

**Why reset the trace (not just truncate)?**
Resetting the trace means the edited context persists across turns — the next turn's edit starts from the already-cleaned state, not the full original history. Truncation would still accumulate pollution across edits.

**Why pass decision notes to the editor?**
In `AgenticEditStrategy`, the decision model already identifies what's wrong. Reusing those notes avoids a second analysis pass and keeps the editor focused on the specific issues identified.

**Reflection as ablation:**
`ReflectionStrategy` isolates the signal from diagnosis alone, without the rewrite. Comparing it against `ContextEditStrategy` reveals how much benefit comes from the annotation vs. the removal of polluted history.

**First-turn skip in editing strategies:**
`ContextEditStrategy` and `AgenticEditStrategy` both skip editing on turn 0 (`num_assistant_turns == 0`). There is no prior history to compress, so editing would be a no-op at best.
