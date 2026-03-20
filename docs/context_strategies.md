# Context Strategies

This document covers the context management strategies in the ctx_editor framework.

---

## Background: Context Pollution

The LiC benchmark showed that multi-turn performance degrades significantly relative to single-turn. LLMs overcommit to early incorrect assumptions and cannot self-correct because the bad reasoning remains in context. We call this accumulated wrong reasoning *context pollution*. The strategies below are treatments for it.

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

**Contract:** `prepare_context()` **mutates** the trace (e.g., resets the conversation, appends analysis) and returns the active messages to use for the next assistant call. The simulator calls this once per turn before the assistant generates a response.

### `BaseStrategy` (shared utilities)

The concrete base class provides two utilities used by all strategies:

- `_inject_memory_to_trace(trace, memory, target)` — appends memory content to either the system message or the last user message. Idempotent: only injects once per trace (guards via `memory_injected` log entry).
- `_is_memory_injected(trace)` — checks the trace log for prior injection.

---

## Current Strategies (S0, S1, S2)

### S0: BaselineStrategy

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

### S1: AppendAnalysisStrategy

`strategies/append_analysis.py`

**What it does:** Runs the `ConversationAnalyzer` (see below) and appends structured analysis to the last user message. The full conversation history is preserved — this is append-only, no rewriting. The system message receives a one-time addendum explaining the analysis tags.

This serves as an ablation of S2: it provides the same diagnostic information but without removing polluted history from context.

**Analysis format appended to the user message:**
```
# Task Spec
{user_intent from analyzer Q1}

# What Looks Right So Far
{aligned from analyzer Q2}

# What Needs to Change
{issues from analyzer Q2 — only present when substantive}
```

The "What Needs to Change" section is omitted entirely when there are no substantive issues. The "What Looks Right So Far" label is deliberately tentative — strong language like "What's Correct" would over-commit.

**Hydra configs:**
- `experiment=append_analysis` — no memory
- `experiment=append_analysis_memory` — with memory

---

### S2: ContextEditV2Strategy

`strategies/context_edit_v2.py`

**What it does:** Runs the same `ConversationAnalyzer`. If substantive issues are found, rewrites the context — the trace is reset to contain only the analysis output plus any unprocessed user messages. If no issues, passes through like S0.

**Key design decisions:**

- **Issues are NOT reintroduced into context.** The `<issues>` section guides the *decision* to edit but does not survive into the edited context. Only the task spec and aligned content are preserved. Reintroducing descriptions of what's wrong would give the assistant something to anchor on — the very problem we're solving.
- **Single rendering path.** The edited context uses a `[compacted conversation]` role tag that flows through the Option 2 renderer naturally:

```
Here is the current conversation:

[compacted conversation]
# Task Spec
Write a Python function that sorts a list in descending order.
Handle empty lists by returning [].

# What Looks Right So Far
Using sorted() with a key function is the right approach.
Input validation for empty lists is correct.

[user]
Also make sure it works with strings

Please respond to the user. Do not include [user] or [assistant] tags in your response.
```

**Trace mutations:** Calls `trace.reset_conversation()` when editing. Future turns build off the edited context, not the original history.

**Hydra configs:**
- `experiment=context_edit_v2` — no memory
- `experiment=context_edit_v2_memory` — with memory

---

## ConversationAnalyzer

`strategies/analyzer.py`

Central analysis component used by both S1 and S2. Uses a two-query architecture (v6) that enforces hard attention separation.

### The problem with single-query analysis

In earlier versions (v3/v4), the analyzer saw the full conversation linearly. This risked the analyzer retracing the conversation's logic and finding each step locally reasonable, even when the assistant's approach had diverged from user intent. The analyzer needs the privilege of hindsight: consider all user messages as a complete picture, *then* evaluate the assistant against that picture.

### Two-query design

**Query 1 — Task Spec** (`prompts/analyzer_v6_task_spec.txt`):
- Input: only user messages (via `trace.get_user_messages_string()`, numbered by turn)
- Output: `<task_spec>` — the complete, up-to-date specification
- Pure extraction. No judgment, no assistant contamination. Architecturally enforced: assistant responses are not in the prompt at all.

**Query 2 — Comparison** (`prompts/analyzer_v6_compare.txt`):
- Input: task spec from Q1 + full conversation + optional memory cheatsheet
- Output: `<aligned>` (what looks right) and `<issues>` (what contradicts the spec)
- The model is instructed to be critical and identify content that would cause the assistant to anchor on mistakes if left in context.

**Why two queries instead of one?** A single query can't guarantee the model processes user intent before evaluating the assistant — especially with reasoning models whose internal thinking may interleave freely. Two queries enforce the sequencing architecturally.

### Implicit edit decision

Previous versions had explicit `<pivot_decision>` or `<edit_action>` tags. Now the presence of substantive content in `<issues>` *is* the edit decision. `AnalysisResult.needs_edit` exposes this as a boolean. This avoids redundant metadata and the risk of the model saying "minor" for something major.

### AnalysisResult

```python
@dataclass
class AnalysisResult:
    user_intent: str       # Clean task spec (from Q1)
    aligned: str           # What the assistant got right (from Q2)
    issues: str            # What contradicts the spec (from Q2)
    raw_output: str        # Full output from both queries
    needs_edit: bool       # Derived: substantive issues present?
```

Backward-compatible properties (`approach_evaluation`, `pivot_needed`, `edit_action`) ensure legacy strategies still work.

### Prompts

Externalized to `strategies/prompts/` for version control:
- `analyzer_v6_task_spec.txt` — Q1 prompt
- `analyzer_v6_compare.txt` — Q2 prompt
- `analyzer_v4.txt`, `analyzer_v5.txt` — preserved for reference

The analyzer accepts a `prompt_version` parameter (default `"v6"`) and loads the corresponding files.

**Memory injection:** The `{memory_section}` placeholder in the compare prompt (Q2) allows learned patterns to guide the comparison. Memory is not used in Q1 (pure extraction — nothing to learn).

---

## Legacy Strategies

Kept for backward compatibility and comparison with earlier experimental results.

### ContextEditStrategy

`strategies/context_edit.py`

Calls a separate editor model to compress the full conversation into a summary before every turn. The trace is reset to the edited context. Superseded by S2 which uses the analyzer for more structured editing decisions.

### AgenticEditStrategy

`strategies/agentic_edit.py`

Adds a gating step: a decision model analyzes the conversation and outputs yes/no for whether compression is beneficial. If yes, performs an edit. Superseded by S2's implicit edit decision via the analyzer.

### ReflectionStrategy

`strategies/reflection.py`

Generates a brief summary and appends it to the last user message. Append-only, no rewriting. Superseded by S1 which uses the structured analyzer output instead.

---

## Memory Integration

All strategies optionally accept a `MemoryModule` object. Memory contains learned takeaways from prior trajectories (see `memory_learning.md`).

| Strategy | Memory behavior |
|---|---|
| S0 (`BaselineStrategy`) | Injected once into system or last user message |
| S1 (`AppendAnalysisStrategy`) | Fed to analyzer Q2 (comparison) via `{memory_section}` placeholder |
| S2 (`ContextEditV2Strategy`) | Same as S1 — memory targets the analyzer's comparison query |

Memory injection is always **idempotent** — once injected to a trace, subsequent calls are no-ops.

---

## Design Notes

**Why reset the trace (not just truncate)?**
Resetting the trace means the edited context persists across turns — the next turn's edit starts from the already-cleaned state, not the full original history.

**Reflection (S1) as ablation:**
S1 isolates the signal from diagnosis alone, without the rewrite. Comparing it against S2 reveals how much benefit comes from the annotation vs. the removal of polluted history.

**First-turn skip:**
S1 and S2 both skip analysis on turn 0 — there's no prior history to analyze.
