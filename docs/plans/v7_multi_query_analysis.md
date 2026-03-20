# V7 Analyzer: Multi-Query/Multi-Call Task Support

## Problem

Actions tasks require **multiple function calls** (2-4 per task), where each call is a separate "ask" within the overall task. The current v6 task spec prompt biases toward unifying everything into a single task specification, which is correct for math/code (single answer) but loses the separability of multi-call tasks.

When the assistant gets one call right but another wrong, the current analysis treats progress as a monolithic block. The `<aligned>` section doesn't distinguish "call 1 is correct, call 2 is wrong" — so a context edit either preserves everything or discards everything.

Database tasks are single-query (single SQL), so they behave like math/code. But the v7 prompts should handle both cases gracefully without separate prompt sets.

## Design Principles

1. **Unified prompts** — one set of prompts handles both single-answer (math/code/database) and multi-answer (actions) tasks. No task-specific prompt branches.
2. **Backward compatible** — v6 remains default. v7 is opt-in via `prompt_version="v7"`.
3. **No code changes to S2 strategy** — the compacted context format (`# Task Spec` + `# What Looks Right So Far`) is unchanged. The prompts just produce better content for these sections.

## Changes

### Query 1: Task Spec Extraction (`analyzer_v7_task_spec.txt`)

Key change: instruct the model to **preserve separable sub-tasks/calls as distinct items** rather than merging them.

New instruction additions:
- "If the user's request involves multiple distinct operations (e.g., multiple function calls, multiple queries, multiple independent computations), list each as a **separate numbered sub-task**. Do not merge them into a single description."
- "For single-answer tasks, a single specification is fine."

This is a soft instruction — for math/code where the user's messages really do describe one task, the model will naturally produce a single spec. For actions where the user says "search for Google lawsuits AND Facebook lawsuits", it will produce two numbered sub-tasks.

### Query 2: Critical Comparison (`analyzer_v7_compare.txt`)

Key changes to `<aligned>` and `<issues>` output:

**`<aligned>` section** — add a `## Completed Sub-tasks` subsection when the task spec has multiple sub-tasks. Format:

```
<aligned>
## Completed Sub-tasks
- Sub-task 1 (lawsuit_search for Google): The assistant correctly produced this call with entity="Google", county="Santa Clara", state="California".

## Other Aligned Work
- [any other progress worth preserving]
</aligned>
```

For single-answer tasks, this subsection simply won't appear (the model sees one task spec item and reports aligned work as before).

**`<issues>` section** — reference specific sub-tasks that are wrong:

```
<issues>
- Sub-task 2 (lawsuit_search for Facebook): The assistant used county="Santa Clara" instead of "San Mateo" as specified.
</issues>
```

### How S2 Uses This

The beauty is that S2's `_build_edited_context` already does the right thing:
- `# Task Spec` now contains numbered sub-tasks → assistant sees all required calls
- `# What Looks Right So Far` now contains `## Completed Sub-tasks` → assistant knows which calls are done and correct, and which still need work
- Issues are stripped from context (as before) → wrong calls removed

The assistant after a context edit sees: "Here are 4 function calls needed. Calls 1 and 3 are done correctly. Now continue." This is exactly what we want.

## Implementation Plan

1. Create `analyzer_v7_task_spec.txt` — copy of v6 with multi-task preservation instructions
2. Create `analyzer_v7_compare.txt` — copy of v6 with sub-task tracking in aligned/issues
3. Update `ConversationAnalyzer.__init__` to load v7 prompts when `prompt_version="v7"`
4. Add v7 experiment configs (can be done later when ready to run)

## Risk Assessment

- **Math/code regression**: Low risk. The added instructions are conditional ("if multiple distinct operations..."). For single-answer tasks, the model should produce output identical to v6.
- **Running v6 experiments**: Zero risk. v7 is new files + a new branch in the version dispatch. Default remains v6.
- **Prompt length**: Minimal increase (~2-3 sentences in each prompt).

## Framing Note

For the paper: actions and database tasks represent a slightly different setting from the core LiC single-task decomposition. They involve **multiple separable operations** where shards may cluster around different calls. This is a natural extension — real-world multi-turn conversations often involve compound requests. The v7 analyzer handles this by preserving sub-task structure in the analysis, enabling the context editor to selectively preserve correct sub-results while removing incorrect ones.
