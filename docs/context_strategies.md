# Context Strategies

This document covers the context management strategies in the ctx_editor framework.

> **Naming note (May 2026):** the canonical class names are now the `AC3-*` family — `AC3AugmentStrategy`, `AC3ResetStrategy`, `AC3RewriteStrategy`. The earlier names `AppendAnalysisStrategy`, `ContextEditV2Strategy`, `ContextCompactionStrategy` remain as backwards-compatible aliases (so older Hydra `_target_` strings and project memory entries still resolve). See [`strategy_name_history.md`](strategy_name_history.md) for the full rename map and [`ac3_variants_per_benchmark.md`](ac3_variants_per_benchmark.md) for how the same AC3 lineup is realized across LiC / CollabLLM / WildChat / Tau2.

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

## Current AC3 Strategies

The AC3 family captures three different "intensities" of context intervention plus a no-op baseline:

| AC3 variant | Class | What the analyzer's output does |
|---|---|---|
| (none) | `BaselineStrategy` | No editing |
| AC3-Augment | `AC3AugmentStrategy` | Appended as a system note. Trace untouched. |
| AC3-Reset / AC3-Gated-Reset | `AC3ResetStrategy` | Programmatic context reset when the analyzer flags issues. "Gated-Reset" is this class with `min_turns` / `max_resets` set — production default. |
| AC3-Rewrite | `AC3RewriteStrategy` | LLM rewrites the conversation into a compacted briefing every turn after `min_turns`. Unconditional. |

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

### AC3-Augment: AC3AugmentStrategy

`strategies/append_analysis.py` (alias: `AppendAnalysisStrategy`; paper-era label "S1")

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

### AC3-Reset / AC3-Gated-Reset: AC3ResetStrategy

`strategies/context_edit_v2.py` (alias: `ContextEditV2Strategy`; paper-era label "S2")

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

### AC3-Rewrite: AC3RewriteStrategy

`strategies/context_compaction.py` (alias: `ContextCompactionStrategy`; paper-era label "S3")

**What it does:** Two-step process applied unconditionally every turn after `min_turns`:

1. Single-query analysis (independent reviewer framing) producing `task_spec`, `aligned`, `issues`.
2. Context compaction: an LLM rewrites the conversation + analysis into a compacted briefing.

Unlike AC3-Reset (which only rewrites when the analyzer flags issues), AC3-Rewrite always compacts past the threshold. This is the operator the paper uses on CollabLLM, where intent may weave across user and assistant turns (no structural exclusion).

**Hydra configs:**
- `experiment=collabllm_compaction` (CollabLLM use)
- Used inside Huang eval as the S3 variant (`HuangAC3RewriteStrategy` in `huang_eval/strategies.py`)

---

## ConversationAnalyzer

`strategies/analyzer.py`

Central analysis component used by all AC3 variants. Two-query architecture for hard attention separation.

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

### Prompt versions and the registry

Available prompt versions live in **`strategies/analyzer_prompts.py`** as the `ANALYZER_PROMPT_REGISTRY`. The default is `v8` (production two-query, hard attention). Each entry records the flow (`two_query`, `two_query_soft`, `single_query_combined`, `single_query_s1`, `single_query_legacy`) plus the template filenames it pulls from `strategies/prompts/`. Adding a new version (e.g. `v12`) is a one-line registry entry plus the template files — no analyzer code changes needed if it reuses an existing flow. Listed versions today: `v4`, `v5`, `v6`, `v7`, `v8`, `v9`, `v11`, `v8_soft`, `v8_soft_cot`, `v8_single`, `s1`.

A parallel **`AGENTIC_PROMPT_REGISTRY`** holds prompts for tool-using agentic benchmarks (currently Tau2's `tau2_v10` set), with different placeholder shapes (`{system_message}`, `{tool_names}`, `{environment_state}`). External code reads them via `load_agentic_prompt(version, slot)` — used by Tau2's `ctx_edit/analyzer.py`.

The analyzer accepts a `prompt_version` parameter (default `"v8"`); strategies expose it as `analyzer_prompt_version` in their Hydra configs.

**Memory injection:** The `{memory_section}` placeholder in the compare prompt (Q2) allows learned patterns to guide the comparison. Memory is not used in Q1 (pure extraction — nothing to learn).

---

## Per-benchmark realization

The same AC3 lineup is instantiated three different ways depending on the benchmark loop:

| Benchmark | Where AC3 strategies live | Notes |
|---|---|---|
| LiC | `strategies/{baseline,append_analysis,context_edit_v2,context_compaction}.py` | The classes documented above. Driven by `ctx-editor` (Hydra). |
| CollabLLM | Reuses LiC's strategy classes via Hydra `_target_:` in `config/experiment/collabllm_*.yaml`. | Driven by `ctx-editor-collabllm`. |
| WildChat / Huang | `huang_eval/strategies.py` defines Huang-specific `HuangAC3{Augment,Reset,GatedReset,Rewrite}Strategy` subclasses — same `ContextStrategy` protocol, but with the message layout the paper's pairwise judges scored against. | Driven by `ctx-editor-huang-phase{1,2}`. |
| Tau2 | Separate code in `tau2-bench/ctx_edit/`; sources its v10 analyzer prompts from `AGENTIC_PROMPT_REGISTRY` when ctx_editor is pip-installed. | See [`tau2_absorption_decision.md`](tau2_absorption_decision.md). |

For more detail on which AC3 variant is supported by which benchmark today, see [`ac3_variants_per_benchmark.md`](ac3_variants_per_benchmark.md).

---

## Legacy strategies

Kept under `strategies/legacy/` for historical comparison and reproducibility of older experiments. Not part of the current AC3 lineup; new work should not use them.

### ContextEditStrategy

`strategies/legacy/context_edit.py`

Original always-rewrite editor. Superseded by `AC3RewriteStrategy` which uses a cleaner two-step analyze → compact pipeline.

### AgenticEditStrategy

`strategies/legacy/agentic_edit.py`

Separate decision-prompt for gating. Superseded by `AC3ResetStrategy` where the gate is folded into the analyzer's structured output.

### ReflectionStrategy

`strategies/legacy/reflection.py`

Free-form reflection appended to the last user message. Superseded by `AC3AugmentStrategy` which appends structured analyzer output instead.

All three remain importable from `ctx_editor.strategies` (the package re-exports them) so older Hydra configs still resolve. The corresponding legacy YAMLs live in `config/experiment/legacy/`.

---

## Memory Integration

All strategies optionally accept a `MemoryModule` object. Memory contains learned takeaways from prior trajectories (see `memory_learning.md`).

| Strategy | Memory behavior |
|---|---|
| Baseline (`BaselineStrategy`) | Injected once into system or last user message |
| AC3-Augment (`AC3AugmentStrategy`) | Fed to analyzer Q2 (comparison) via `{memory_section}` placeholder |
| AC3-Reset / Gated-Reset (`AC3ResetStrategy`) | Same as AC3-Augment — memory targets the analyzer's comparison query |
| AC3-Rewrite (`AC3RewriteStrategy`) | Memory available to both the single-query analyzer and the LLM compaction step |

Memory injection is always **idempotent** — once injected to a trace, subsequent calls are no-ops.

---

## Design Notes

**Why reset the trace (not just truncate)?**
Resetting the trace means the edited context persists across turns — the next turn's edit starts from the already-cleaned state, not the full original history.

**Augment as ablation:**
AC3-Augment isolates the signal from diagnosis alone, without the rewrite. Comparing it against AC3-Reset reveals how much benefit comes from the annotation vs. the removal of polluted history.

**First-turn skip:**
AC3-Augment and AC3-Reset both skip analysis on turn 0 — there's no prior history to analyze.
