# Newer Leaf Refactor

Branch: `newleaf2`

> **Historical doc.** This is a point-in-time snapshot of the v6 two-query analyzer refactor; class names and file paths are as they were at that time. For current names see [`strategy_name_history.md`](strategy_name_history.md); for the active analyzer architecture (now driven by [`analyzer_prompts.py`](../src/ctx_editor/strategies/analyzer_prompts.py) registry, default `v8`), see [`context_strategies.md`](context_strategies.md).

Builds on the newleaf refactor. This round redesigns the analyzer prompt and architecture based on a first-principles review of the LiC failure modes and comparison with related work (ERGO, Huang et al.).

## 1. Two-Query Analyzer Architecture (v6)

**Files**: `src/ctx_editor/strategies/analyzer.py`, `src/ctx_editor/strategies/prompts/analyzer_v6_*.txt`

The analyzer was redesigned from a single LLM call to a two-query architecture that enforces hard attention separation.

### The problem with single-query analysis

In the original (v3/v4) prompt, the analyzer saw the full conversation linearly — user, assistant, user, assistant. This risks the analyzer retracing the conversation's logic and finding each step locally reasonable, even when the assistant's approach has diverged from what the user actually wants. The analyzer needs the privilege of hindsight: consider all user messages as a complete picture, *then* evaluate the assistant against that picture.

### Design

**Query 1 — Task Spec** (`analyzer_v6_task_spec.txt`):
- Input: only user messages (numbered, no assistant responses)
- Output: `<task_spec>` — the complete, up-to-date specification
- This is pure extraction. No judgment, no assistant contamination. Architecturally enforced: the assistant's responses are not in the prompt at all.

**Query 2 — Comparison** (`analyzer_v6_compare.txt`):
- Input: task spec from Q1 + full conversation + optional memory cheatsheet
- Output: `<aligned>` (what looks right so far) and `<issues>` (what contradicts the spec)
- The model is instructed to be critical and to identify content that would cause the assistant to anchor on mistakes if left in context.

**Why two queries instead of one with restructured input?** We considered showing user messages first then the full conversation in a single prompt (this was v5). But a single query can't guarantee the model processes user intent before evaluating the assistant — especially with reasoning models whose internal thinking may interleave freely. Two queries enforce the sequencing architecturally.

**Why not put memory on Q1?** Q1 is pure extraction from user messages — there's nothing to learn. Memory targets Q2 (the comparison), where learned patterns about what kinds of assistant content are harmful vs. useful can improve the analysis.

### Implicit edit decision

Previous versions had an explicit `<pivot_decision>` (yes/no) or `<edit_action>` (none/minor/major) tag. This was removed. The presence of substantive content in `<issues>` *is* the edit decision. This is cleaner because:
- No redundant metadata to extract and interpret
- No risk of the model saying "minor" for something that's actually major, or vice versa
- The `_has_substantive_issues()` function filters out trivial responses ("None", "No issues", etc.)
- `AnalysisResult.needs_edit` exposes this as a boolean for downstream consumers

## 2. Prompts Externalized to Files

**Directory**: `src/ctx_editor/strategies/prompts/`

Analyzer prompts moved from inline Python strings to text files for version control and easy iteration. The analyzer accepts a `prompt_version` parameter (default `"v6"`) and loads the corresponding files.

Prompt history preserved in the directory:
- `analyzer_v4.txt` — single query, enumerated subsections (ERRORS, ASSUMPTIONS, etc.)
- `analyzer_v5.txt` — single query, restructured input (user messages shown first)
- `analyzer_v6_task_spec.txt` — Q1: user messages → task spec
- `analyzer_v6_compare.txt` — Q2: task spec vs. conversation

## 3. AnalysisResult Redesign

**File**: `src/ctx_editor/strategies/analyzer.py`

The dataclass was redesigned to reflect the two-query output:

```python
@dataclass
class AnalysisResult:
    user_intent: str   # Clean task spec (from Q1)
    aligned: str       # What the assistant got right (from Q2)
    issues: str        # What contradicts the spec (from Q2)
    raw_output: str    # Full output from both queries

    needs_edit: bool        # Derived: substantive issues present?
    context_assessment: str # Derived: combined aligned + issues for S1
    approach_evaluation: str  # Alias for context_assessment (backward compat)
    pivot_needed: bool        # Alias for needs_edit (backward compat)
    edit_action: str          # Derived: "major" if needs_edit else "none" (backward compat)
```

Backward-compatible properties ensure S1 and S2 strategies work without changes to their control flow.

## 4. Edited Context Format (S2)

**File**: `src/ctx_editor/strategies/context_edit_v2.py`

The `_build_edited_context` method was redesigned based on two key decisions:

### Issues are not reintroduced into context

Previous versions put the full analysis (including "what's wrong") into `<context_edit_notes>` in the system message. This reintroduced the very content we were trying to purge — descriptions of wrong assumptions, incorrect approaches, etc. Even rephrased, this gives the assistant something to anchor on.

Now: the `<issues>` section guides the *decision* to edit but does not survive into the edited context. Only the task spec and aligned content are preserved.

### Single rendering path via Option 2

Previous versions spread the edited context across a modified system message + fake user messages. This was inconsistent with the Option 2 rendering established in the newleaf refactor, where everything goes through `_render_for_assistant()` as tagged sections in a single user message.

Now: the edited context uses a `[compacted conversation]` role tag that flows through the renderer naturally:

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

The system message passes through unmodified.

### Deliberation: do we need an LLM rewrite step?

We considered adding a third LLM call to surgically rewrite the assistant's actual responses (keeping correct code, removing wrong parts). We decided against it because:

- For LiC tasks (math, code, database, actions), the "good stuff" is typically approach-level ("using sorted() is right") not artifact-level (a 200-line file that's mostly correct). Regenerating from a good task spec + notes is sufficient.
- The hard attention mechanism — purging bad content — works either way. The bad stuff is gone regardless of whether the new context contains a rewritten version or a clean summary.
- The novelty lives in the analysis (two-query hard attention, implicit edit decision, memory-targetable comparison), not in the mechanical rewrite.
- Adding it now without evidence it helps is premature complexity — exactly the patching-on-top behavior we're trying to solve.

If we later find tasks where large correct artifacts are expensive to regenerate, an LLM rewrite step is a clean extension — the analysis output already provides exactly what a rewriter would need.

## 5. S1 Append Format

**File**: `src/ctx_editor/strategies/append_analysis.py`

The analysis block appended to the user message now uses structured markdown sections:

```
# Task Spec
{user_intent from Q1}

# What Looks Right So Far
{aligned from Q2}

# What Needs to Change
{issues from Q2 — only present when substantive}
```

The "What Needs to Change" section is omitted entirely when there are no substantive issues, rather than showing an empty or "None" section. The "What Looks Right So Far" label is deliberately tentative — it may need to be invalidated by later user messages, and strong language like "What's Correct" would over-commit (the very problem we're solving).

## 6. User Messages Extraction

**File**: `src/ctx_editor/core/trace.py`

Added `get_user_messages_string()` method to `ConversationTrace`. Returns user messages numbered by turn, excluding system and assistant messages:

```
[Message 1]
Write a sort function

[Message 2]
Make it descending

[Message 3]
Also handle empty lists
```

This supports the v6 two-query architecture where Q1 only sees user messages.

## 7. Prompt Design Rationale

### What was removed from the original analyzer prompt

- **Enumerated subsections** (ERRORS, UNGROUNDED ASSUMPTIONS, BLOAT, WHAT WORKS, CORRECTIVE DIRECTION): replaced by the natural comparison structure of Q2. The model doesn't need five labeled categories — it needs one clear job.
- **Lost-in-middle language**: this is a fundamental LLM attention property, not addressable through prompting, and the summarization subtask (where it was most observed) was dropped from our evaluation.
- **Explicit failure mode descriptions**: the original prompt listed three failure patterns. The v6 compare prompt distills this to one sentence: "the assistant may have made assumptions early on that contradict requirements the user specified later. Such content is actively harmful."

### What was kept

- **Independent reviewer framing**: the analyzer is still presented as a third party, not as self-reflection.
- **No previous analyses in input**: when generating analysis A_i, previous analyses A_j are still excluded. The analyzer always sees the raw conversation.
- **Memory injection via cheatsheet**: the `{memory_section}` placeholder in the compare prompt allows learned patterns to guide the comparison.

## Summary of File Changes

| File | Change |
|---|---|
| `strategies/analyzer.py` | Two-query architecture, file-based prompts, new AnalysisResult with aligned/issues fields, backward compat properties |
| `strategies/prompts/analyzer_v6_task_spec.txt` | New: Q1 prompt (user messages → task spec) |
| `strategies/prompts/analyzer_v6_compare.txt` | New: Q2 prompt (task spec vs conversation → aligned/issues) |
| `strategies/prompts/analyzer_v4.txt` | Preserved for backward compat |
| `strategies/prompts/analyzer_v5.txt` | Preserved for backward compat |
| `strategies/context_edit_v2.py` | Edited context uses `[compacted conversation]` role, issues not reintroduced, takes AnalysisResult directly |
| `strategies/append_analysis.py` | Structured markdown format with tentative labels, issues section conditionally omitted |
| `core/trace.py` | Added `get_user_messages_string()` |
