# Prompt Changes v8 — Deliberation & Planned Changes

## Overview

This document analyzes proposed prompt and formatting changes across the analysis pipeline, drawing inspiration from the Dynamic Cheatsheet paper's prompt structure while adapting to our multi-turn conversation setting.

---

## 1. Cheatsheet Integration — Adding Introductory Context

### Current State

Three different injection patterns exist:

| Target | Format | Introduction |
|--------|--------|-------------|
| **Analyzer** (query 2) | `MEMORY_SECTION_TEMPLATE` in `analyzer.py` | "Use this cheatsheet to guide your analysis — it contains lessons learned from similar tasks:" |
| **Assistant** (via system msg) | `MEMORY_BLOCK_TEMPLATE` in `base.py` | None — bare `<cheatsheet>` tags |
| **Editor** (legacy) | `MEMORY_SECTION_TEMPLATE` in `context_edit.py` | "Use this cheatsheet to help identify what information is most important to preserve:" |

The analyzer injection has a brief intro, but the assistant injection (`MEMORY_BLOCK_TEMPLATE` in `base.py`) has none — the cheatsheet is dumped raw into `<cheatsheet>` tags.

### Proposed Change

Add a brief preamble to `MEMORY_BLOCK_TEMPLATE` in `base.py` (the one used for assistant-targeted injection). The tone should be advisory, not prescriptive — matching the user's request for a "non-committal" framing:

```python
MEMORY_BLOCK_TEMPLATE = """\n
<cheatsheet>
The following cheatsheet contains strategies, common pitfalls, and lessons learned from \
previous similar tasks. Use your discretion to decide which points are relevant to the \
current task — not all will apply.

{memory_content}
</cheatsheet>"""
```

Also update the analyzer's `MEMORY_SECTION_TEMPLATE` to use similar advisory language:

```python
MEMORY_SECTION_TEMPLATE = """\
<cheatsheet>
The following cheatsheet contains strategies, common pitfalls, and lessons learned from \
previous similar tasks. Use your discretion to decide which points are relevant — not all \
will apply.

{memory_content}
</cheatsheet>
"""
```

### Rationale

- The Dynamic Cheatsheet paper includes substantial preamble explaining the cheatsheet's purpose
- Our current bare injection relies on the model inferring what `<cheatsheet>` means
- Advisory framing ("use your discretion") reduces the risk of the model blindly following maladaptive rules (e.g., "ask clarifying questions")
- This directly addresses the observed problem where harmful cheatsheet rules cause regressions

### Impact Assessment

Low risk. This only adds context around content that's already injected. The advisory framing should reduce harm from bad rules without reducing benefit from good ones.

---

## 2. Append-Only (S1) Analysis Injection — Separate Message Role

### Current State

S1 appends the analysis to the **last user message** via `trace.append_to_last_user_message()` and adds a system prompt addendum explaining the `<conversation_analysis>` tags.

The analysis appears inside the user's message, which conflates the user's actual words with the independent review.

### Proposed Change

Instead of appending to the last user message, inject the analysis as a **separate message with a distinct role**, similar to how S2 uses `"compacted conversation"`:

```python
# New: insert analysis as its own message, before the latest user message
Message(role="conversation analysis", content=analysis_text)
```

The Option 2 renderer (`_render_for_assistant`) already handles arbitrary roles — it renders `[{msg.role}]\n{msg.content}`, so `[conversation analysis]` will appear naturally in the conversation string.

The flow becomes:
```
[user]
blah

[assistant]
blah blah

[conversation analysis]
An independent reviewer analyzed the conversation so far...

# User Task Specification (So Far)
...

# What Looks Right So Far
...

# What Needs to Change
...

[user]
blah blah blah
```

### Implementation Detail

This requires modifying `append_analysis.py` to insert a new message before the last user message rather than appending to it. The trace needs a method like `insert_before_last_user_message()` or we build the messages list manually.

Actually, looking more carefully: the analysis is generated *after* the user message is already in the trace. We need to either:
1. Add a `trace.insert_message_before_last_user(msg)` method, or
2. Build the message list in `prepare_context` by taking `trace.get_active_messages()`, finding the last user message, and inserting before it

Option 2 is simpler since `prepare_context` already returns `list[Message]` and we can manipulate the list without mutating trace internals.

### System Prompt Addendum Update

The current addendum references `<conversation_analysis>` tags. Update to reference the role instead:

```python
ANALYSIS_SYSTEM_ADDENDUM = """

Note: An independent reviewer may analyze the conversation between turns. \
These analyses appear as [conversation analysis] messages. They summarize what the user \
has specified and identify which parts of your approach are consistent with the specifications \
and which parts may be erroneous. Consider this analysis when preparing your next response, \
but do not reference it directly."""
```

### Rationale

- Consistent with S2's approach of using distinct message roles
- Cleaner separation between user content and analysis content
- The assistant model sees the analysis as coming from a distinct source, not embedded in the user's words
- Matches the user's preference for the analysis to feel like it comes from a third party

---

## 3. Renaming "Task Spec" → "User Task Specification (So Far)"

### Current State

The section header is `# Task Spec` in both S1 and S2 analysis output. The XML tag in the analyzer prompt is `<task_spec>`.

### Proposed Change

Rename the **display header** (what the assistant sees) from `# Task Spec` to `# User Task Specification (So Far)`. Keep the internal XML tag as `<task_spec>` — changing internal parsing tags is unnecessary risk.

Changes in:
- `append_analysis.py` line 119: `f"# Task Spec\n{...}"` → `f"# User Task Specification (So Far)\n{...}"`
- `context_edit_v2.py` line 86: same change
- `renderers.py` lines 24, 189: update display labels (for memory reflection rendering)

### Rationale

- "Task Spec" is our internal shorthand; to the assistant model, "User Task Specification" is more self-descriptive
- It makes clear this is a summary of what *the user* asked for, derived from their messages
- "Specification" retains the precision-oriented connotation — this isn't a loose summary, it's a detailed spec
- **"(So Far)" is critical**: the spec is a living document that evolves as the user reveals more information. In our sharded-disclosure setting, the user progressively specifies their requirements across turns. Without this qualifier, the assistant (or analyzer on subsequent passes) might treat the spec as final and definitive, ignoring or underweighting new user messages that modify, refine, or extend it. This is especially important when S2 has already compacted the conversation — the next analysis pass sees the previous task spec + new user messages, and needs to understand the spec can be updated.
- The other section headers already carry this provisional tone: "What Looks Right **So Far**" and "What **Needs to** Change" both signal that the assessment is current-state, not permanent. The task spec heading should match.

---

## 4. Introducing the Analysis / Edited Context

### Current State

**S1**: The system addendum gives a brief explanation, but the analysis sections themselves (`# Task Spec`, `# What Looks Right`, `# What Needs to Change`) appear without preamble inside the analysis block.

**S2**: The compacted context uses role `"compacted conversation"` with `# Task Spec` and `# What Looks Right So Far` headers but no introductory text explaining what this is.

### Proposed Change

**S1** — Add a brief preamble inside the `[conversation analysis]` message:

```
An independent reviewer analyzed the conversation so far. It summarizes what the user has \
specified and identifies which parts of your approach are consistent with the specifications \
and which parts may need to change. Consider this analysis when preparing your next response.
```

This goes at the top of the analysis text, before the `# User Task Specification (So Far)` header.

**S2** — Add a brief preamble inside the `[compacted conversation]` message:

```
The conversation history has been compacted. Below is a summary of the user's full \
specification and the work completed so far that is consistent with it.
```

### Rationale for S2

The headers `# User Task Specification (So Far)` and `# What Looks Right So Far` are fairly self-descriptive, but one sentence of orientation helps the assistant understand *why* the conversation looks different from a normal multi-turn exchange. Without it, the model might be confused by the sudden shift from a multi-turn conversation to a compacted summary. The preamble anchors the model: "this is intentional, here's why."

This is **minimal** — just one sentence. The headers carry the weight. We're not writing a paragraph explaining the methodology.

---

## 5. Task Spec Subtask Prompt Adjustments

### Current Problem

The v6 prompt says "Only what the user said — no interpretation" and "Do not paraphrase or summarize away precision." In practice, the model interprets this as "just concatenate user messages verbatim" — making the entire query a no-op.

The *intent* is to consolidate and organize the user's specifications in a way that's easier to parse, while preserving all details. The current wording over-corrects for the original problem (destroying information).

### Proposed v8 Task Spec Prompt

```
Here are the user's messages from a multi-turn conversation, in order:

{user_messages}

Construct the complete, up-to-date user task specification from these messages. Your goal \
is to produce a clear, organized specification that consolidates what the user is asking \
for based on everything they have said so far. Note that the user may continue to refine \
or extend their requirements in future messages — this specification reflects the current \
state of their request, not necessarily the final version.

Guidelines:
- Include every requirement, constraint, example, and correction the user stated.
- If a later message overrides or refines an earlier one, use the latest version.
- Preserve all specific details: exact numbers, formulas, formats, examples, edge cases, \
and constraints. Do not lose precision.
- You may reorganize and consolidate for clarity, but do not add interpretation or \
assumptions beyond what the user stated.
- If the user's messages describe multiple distinct deliverables (e.g., multiple function \
calls, multiple queries, multiple independent outputs), list each as a separate numbered \
item. Keep single-output tasks as a single specification.

Use this format for your answer:

<task_spec>
[The complete user task specification]
</task_spec>
```

### Key Changes from v6/v7

1. **"You may reorganize and consolidate for clarity"** — explicitly permits the model to structure the output, not just parrot messages back
2. **"do not add interpretation or assumptions beyond what the user stated"** — replaces the overly restrictive "Only what the user said — no interpretation" while preserving the core constraint
3. **"multiple distinct deliverables"** — uses "deliverables" instead of "operations" to be more precise. The concern isn't about multiple *steps* to produce one output, it's about multiple *separate outputs* the user expects
4. **Removes "Do not paraphrase or summarize away precision"** — this line was causing the concatenation behavior. Replaced by "Preserve all specific details" + explicit list of what to preserve

### Multi-Subtask Concern

The user raises a valid concern: will the multi-subtask instruction harm math/code tasks where there's always a single answer?

**Assessment**: The instruction says "If the user's messages describe multiple distinct deliverables... list each as a separate numbered item. Keep single-output tasks as a single specification." The conditional framing ("if") and the explicit single-task fallback ("Keep single-output tasks as a single specification") should prevent over-splitting on math/code.

**Recommendation**: Do NOT split off subtask handling into actions-only prompts. Reasons:
1. The conditional phrasing is sufficient to handle single-output tasks
2. Real conversations can involve multiple outputs regardless of domain
3. Maintaining separate prompt versions per task adds complexity and fragility
4. If we see regressions on math/code, we can revisit, but the phrasing is conservative enough

---

## 6. Comparison Subtask Adjustments

### Current Problem

The v7 compare prompt has multi-subtask handling, but the concern is that sharded questions (where information is revealed incrementally) might trick the analyzer into thinking the user expects multiple separate artifacts when they don't.

### Proposed v8 Compare Prompt

```
Here is what the user is asking for:

<task_spec>
{task_spec}
</task_spec>

Here is the conversation so far:

<conversation>
{conversation}
</conversation>

{memory_section}

Compare the assistant's work against the user task specification so far. Be critical — the \
assistant may have made assumptions early on that contradict requirements the user specified \
later. Such content is actively harmful: if it remains in context, the assistant will anchor \
on it and repeat the same mistakes.

If the user task specification contains multiple numbered items (i.e., the user expects \
multiple distinct outputs), evaluate each item separately. Track which items the assistant \
has completed correctly, which have errors, and which haven't been attempted. Correctly \
completed items must be preserved even when other items need to be redone.

Use this format for your answer:

<aligned>
What in the assistant's responses is consistent with the user task specification so far. Be \
specific — cite the concrete results the assistant produced that are correct.

If there are multiple items in the specification, list each correctly completed item with \
the specific result the assistant produced.
</aligned>

<issues>
What in the assistant's responses contradicts the user task specification so far, is built on \
unfounded assumptions, or is unnecessary complexity from earlier wrong attempts. Be specific. \
If nothing, write "None".

If there are multiple items, reference which specific item(s) have problems.
</issues>
```

### Key Changes from v7

1. **"multiple numbered items (i.e., the user expects multiple distinct outputs)"** — ties back to the task spec's numbering, making it clear we're tracking multiple *outputs*, not multiple *shards of a single question*
2. **Removes "sub-tasks" terminology** — "items" is more neutral. "Sub-tasks" suggests decomposition of a single task, which could mislead the analyzer into treating sharded revelations as separate tasks
3. **"cite the concrete results"** — makes the aligned section more actionable for S2, where preserved results need to be specific enough to use directly

### On the Sharding Concern

The key protection is that the *task spec* prompt now says "multiple distinct deliverables" — if the task spec doesn't number items (because it's a single output), the compare prompt won't activate multi-item tracking. The chain works: task spec controls whether items are numbered → compare prompt responds to the numbering.

---

## 7. Open Questions — Deliberation

### Should subtask changes be split off for actions only?

**Recommendation: No.** Keep unified prompts.

The multi-item handling in both prompts is conditional — it only activates when the task spec actually contains numbered items. For math and code, the task spec will almost always be a single specification, so the compare prompt won't enter multi-item tracking mode.

The real risk isn't the prompt — it's whether the task spec model will incorrectly number items for single-output tasks. The phrasing "multiple distinct deliverables" (not "multiple requirements" or "multiple steps") should prevent this. A math problem with multiple constraints is still one deliverable. A code problem asking for one function is still one deliverable.

If we see regressions, the fix is to tighten the task spec prompt's numbering criteria, not to fork the prompts.

### Should we request more CoT for the comparison task?

**Recommendation: No, not yet.**

Analysis:
1. **What the Dynamic Cheatsheet paper does**: They request detailed reasoning steps in the *generator* (solver) prompt to expose more process for the updater to learn from. Their updater sees the full response including reasoning.

2. **What we do**: Our updater (cheatsheet reflector) sees the full *conversation trace* including all analysis outputs via `render_for_analyzer()`. The trace already includes the analyzer's outputs (`[conversation analysis]` blocks) interleaved chronologically. So the reflector already sees what the analyzer produced.

3. **What it doesn't see**: The analyzer's *internal reasoning* (chain of thought). Currently the analyzer prompt doesn't request step-by-step reasoning — it goes straight to structured output (`<aligned>`, `<issues>`).

4. **Would more CoT help?**
   - For the *analyzer itself*: Possibly — asking it to reason before producing structured output could improve analysis quality. But our analyzer model is often gpt-4o-mini or gpt-5-mini, which already have decent reasoning. Adding CoT increases cost and latency on every turn.
   - For the *memory updater*: The updater already sees the conversation + analysis outputs + outcomes. The bottleneck in memory quality isn't insufficient signal — it's the unification step collapsing specifics into platitudes. More CoT from the analyzer wouldn't fix that.

5. **Cost consideration**: CoT adds tokens to every analysis call (2 per turn past min_turns). Memory updates happen once per trajectory. The cost/benefit ratio is unfavorable.

**If we revisit this later**: The right place to add CoT is a `<reasoning>` block before the `<aligned>` and `<issues>` tags in the compare prompt. The tag can be stripped before injection into the conversation (S1/S2 don't need the reasoning, only the conclusions).

### Is the memory updater configured to include full responses?

**Yes.** The `render_for_analyzer()` function in `renderers.py` shows the full conversation timeline with analysis blocks interleaved. It includes assistant responses in full, analysis outputs, edit decisions, and compacted conversation boundaries. The reflector sees everything.

The takeaway extractor (`analyzer_reflect_takeaways.txt`) also receives the full trajectory via `{conversation}` which uses `render_for_analyzer()`.

So the signal is available — the issue is whether the model can extract useful patterns from it, not whether the data is there.

---

## 8. Summary of All Planned Changes

### Files to Modify

| File | Change |
|------|--------|
| `src/ctx_editor/strategies/base.py` | Update `MEMORY_BLOCK_TEMPLATE` with advisory preamble |
| `src/ctx_editor/strategies/analyzer.py` | Update `MEMORY_SECTION_TEMPLATE` with advisory preamble |
| `src/ctx_editor/strategies/append_analysis.py` | (1) Insert analysis as separate `[conversation analysis]` message instead of appending to user msg. (2) Update system addendum. (3) Add introductory sentence to analysis text. (4) Rename `# Task Spec` → `# User Task Specification (So Far)` |
| `src/ctx_editor/strategies/context_edit_v2.py` | (1) Add introductory sentence to compacted conversation. (2) Rename `# Task Spec` → `# User Task Specification (So Far)` |
| `src/ctx_editor/strategies/prompts/analyzer_v8_task_spec.txt` | New prompt file — reorganized task spec prompt |
| `src/ctx_editor/strategies/prompts/analyzer_v8_compare.txt` | New prompt file — updated compare prompt with refined multi-item handling |
| `src/ctx_editor/memory/renderers.py` | Update `# Task Spec` display labels to `# User Task Specification (So Far)` |

### New Prompt Files (v8)

Create `analyzer_v8_task_spec.txt` and `analyzer_v8_compare.txt` as new version files. The analyzer already supports version dispatch (`prompt_version` parameter), so v8 just needs to be added to the version check in `analyzer.py`.

### What's NOT Changing

- Internal XML tags (`<task_spec>`, `<aligned>`, `<issues>`) — no parsing changes needed
- The two-query architecture — still Query 1 (task spec) → Query 2 (compare)
- The edit decision mechanism — substantive issues in `<issues>` still triggers edit
- Memory update pipeline — no changes to renderers' behavior, just display labels
- Legacy strategy prompts (v4, v5, v6, v7) — kept for backward compatibility

---

## 9. Risk Assessment

| Change | Risk | Mitigation |
|--------|------|------------|
| Cheatsheet preamble | Low | Advisory framing should reduce harm from bad rules |
| S1 separate message role | Medium | Test on dev set; the Option 2 renderer handles arbitrary roles but the assistant model needs to interpret `[conversation analysis]` correctly |
| Task Spec rename + "(So Far)" | Low | Display-only change, no parsing impact. "(So Far)" reinforces that the spec evolves with new user messages |
| Analysis preamble text | Low | One sentence, minimal overhead |
| Task spec prompt rewrite | Medium | The balance between "allow reorganization" and "don't lose precision" is delicate. Dev set testing required |
| Multi-item handling | Medium | Risk of over-splitting on single-output tasks. Conditional phrasing + "distinct deliverables" should prevent this but needs validation |

### Recommended Testing Order

1. **Batch A**: Cheatsheet preamble + S1 message role + rename + preambles (low risk, formatting only)
2. **Batch B**: v8 task spec + compare prompts (medium risk, functional changes)
3. Run dev set for math, code, database, actions with both batches to measure impact
