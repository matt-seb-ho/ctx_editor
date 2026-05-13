# v12 analyzer-prompt attempt — archive

Archive of the `analyzer_v12_*` prompt experiment and the underlying Azure
content-filter investigation. Captured here on **2026-05-12** before resetting
local `main` to `origin/main` (which had a major experiment-infrastructure
refactor: AC3 rename, analyzer prompt registry, Hydra-ified Huang eval, etc.).

The pre-pull snapshot lives on branch `backup/pre-infra-pull` (commit
`ed800ca` "wip: snapshot before resetting main to origin/main"). Anything in
this archive can be recovered verbatim from there as well.

## What v12 was trying to do

Two-query analyzer prompt template designed to avoid Azure OpenAI's prompt-
injection content filter. Differences vs. v8/v11:

1. **Drops the conversation's original system message entirely** from the
   analyzer's input. The original system message is typically generic
   role-defining boilerplate ("the assistant is designed to be helpful…") and
   is not load-bearing for an analyzer that only needs to summarize the user's
   intent and the assistant's progress.
2. **Markdown headers as section delimiters in both input and output**:
   `TASK SPECIFICATION:`, `ALIGNED:`, `ISSUES:`. No XML.
3. **No `[system]` role-prefix in the conversation dump**; turns are prefixed
   `[user]` / `[assistant]` only.

Wired into `ConversationAnalyzer` via a new `_analyze_v12` method (see the
analyzer.py diff on `backup/pre-infra-pull`).

## Why it was tried

See `azure_jailbreak_filter_triggers.md` in this directory for the full write-
up of the underlying problem. Headline:

- Across 6+ runs (n=20 each) on `gpt-4o-mini` / `gpt-5-mini` via Azure, the
  analyzer call was being rejected with HTTP 400 + `jailbreak: filtered=true`
  on benign analyzer prompts.
- Trip rate on gpt-4o-mini with XML-wrapped system messages: ~95–100% of
  conversations had at least one rejected analyzer call, killing the
  conversation.
- The filter is matching the *structural* pattern (XML-wrapped role-defining
  content, output-schema scaffolding, meta-instruction language), not the
  semantic content. There is nothing unsafe in any of the rejected payloads.

## How v12 performed

**On the content-filter axis (the thing it was designed to fix): worked.**
0 content-filter trips across 6 fresh runs (4 Gated-Reset + 2 Augment, 20
conversations each). Raw accuracy on math: Gated-Reset went from ~5–10% (with
the filter killing most conversations) to ~40%; Augment ~30% → ~60%. Those
numbers reflect actual strategy performance instead of CF-survival rates.

**On the broader analyzer-quality axis: did not work out nicely.** It is
preserved here as a starting point for porting into the post-Phase-3 prompt
registry, not as a finished prompt to drop back in.

## Files

- `analyzer_v12_task_spec.txt` — Query 1 template: user-messages-only → spec.
- `analyzer_v12_compare.txt` — Query 2 template: spec + conversation →
  `ALIGNED` / `ISSUES`.
- `azure_jailbreak_filter_triggers.md` — Full write-up of the Azure filter
  behavior with verbatim rejected requests, trip-rate tables across template
  variants, reproduction paths to JSONL of rejected requests, and the
  practical-takeaways list.

## Porting hints for the new infra

The post-pull repo introduced an **analyzer prompt registry** (commits
`1c777c0` "refactor: lift analyzer prompt versions into a registry" and
`ed57ccc` "feat: add agentic prompt registry"). If we want to revive any part
of v12, the right shape is probably:

1. Register `analyzer_v12_task_spec` and `analyzer_v12_compare` in that
   registry.
2. Add a v12 branch to whatever the post-refactor analyzer entry point is
   (was `ConversationAnalyzer._analyze_v12` pre-pull; check the new layout).
3. Drop the conversation's system message from the analyzer's input there,
   as v12 does; keep the markdown-only delimiters.
4. Re-test the content-filter survival rate (should be ~0% trips) before
   re-running the full strategy sweep.

The analyzer-quality issues that made the original v12 "not work out nicely"
should be addressed during the port — the archived prompts above are the
*input* to that rework, not the answer.
