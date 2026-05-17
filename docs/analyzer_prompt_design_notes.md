# Analyzer Prompt Versions — Design Notes

**Date**: 2026-05-16

This consolidates the trade-off between **analyzer-quality** and
**Azure-content-filter survival** across the prompt versions that exist
today, plus the design sketch for a hypothetical `v13` we have on
standby in case Azure CF starts tripping during Phase 2.

There was no standalone "design doc" for any of these prompts —
information was scattered across:

- `docs/archive/v12_attempt/azure_jailbreak_filter_triggers.md` — trip-rate evidence per template family (gpt-4o-mini, gpt-5-mini).
- `docs/archive/v12_attempt/notes.md` — v12 design rationale + post-mortem.
- `docs/reports/dev_set_round2_content_filter_fix.md` — March 2026 round where s1 was first deployed.
- `docs/context_strategies.md` — how the registry threads prompts into the strategies.

This doc is the canonical synthesis going forward.

## Active prompt registry

`src/ctx_editor/strategies/analyzer_prompts.py` registers all versions. Names below are the keys passed via `analyzer_prompt_version=...`.

| Version | Flow | Template files | Default for | CF behavior |
|---|---|---|---|---|
| `v4` | single_query_legacy | analyzer_v4.txt | (older experiments) | not characterized |
| `v5` | single_query_legacy | analyzer_v5.txt | (older experiments) | not characterized |
| `v6` | two_query | analyzer_v6_task_spec.txt + analyzer_v6_compare.txt | older two-query baseline | early CF trips |
| `v7` | two_query | analyzer_v7_task_spec.txt + analyzer_v7_compare.txt | (intermediate) | early CF trips |
| **`v8`** | two_query | analyzer_v8_task_spec.txt + analyzer_v8_compare.txt | **LiC paper default. Current `DEFAULT_ANALYZER_VERSION`.** | 60–100% trip on gpt-4o-mini, ~65–70% on gpt-5-mini through Azure OAI |
| `v9` | two_query | analyzer_v9_compare.txt + v8 task_spec | "corrective direction" experiment | similar to v8 |
| `v11` | two_query | analyzer_v11_compare.txt + v8 task_spec | Huang/WildChat Gated-Reset row in the paper | similar to v8 |
| `v8_soft` / `v8_soft_cot` | two_query_soft | analyzer_v8_soft_spec.txt + analyzer_v8_compare.txt | soft-attention variants | not characterized |
| `v8_single` | single_query_combined | analyzer_v8_single.txt | single-query ablation | not characterized |
| **`s1`** | single_query_s1 | s1_analysis.txt | CollabLLM paper headline (CF fallback) | **~65% trip on gpt-5-mini** when the conversation's original system message is embedded. Partial fix, not complete. |
| `v12` (archived) | two_query | archive/v12_attempt/analyzer_v12_*.txt | content-filter survival probe (May 2026) | **0% trip** but analyzer-content quality regressed; not in active registry |

The registry intentionally **does not** include `v12` — the v12 prompt's analyzer-content was rushed and worse than v8. `v13` (below) is the planned re-do that keeps v12's structural CF-safety fix while restoring v8's content quality.

## The Azure content-filter problem

Source: `docs/archive/v12_attempt/azure_jailbreak_filter_triggers.md`. Summarized:

- Across 6+ runs (n=20 each) on `gpt-4o-mini` / `gpt-5-mini` via Azure OAI in May 2026, analyzer calls were rejected with HTTP 400 + `jailbreak: filtered=true`.
- **100%** of trips were the `jailbreak` filter category; zero `hate` / `sexual` / `self_harm` / `violence`. The detector matches a **structural pattern** (XML-wrapped role-defining content, output-schema scaffolding, meta-instruction language), not semantic content. There is nothing unsafe in any of the rejected payloads.
- Trip rates by template family on `gpt-5-mini`:
  - `v8` XML-wrapped system message: ~70% of conversations had at least one analyzer call rejected.
  - `[system] ...` prefix-style (no XML, still embeds original system message): ~65%.
  - `s1` no-XML header-format: still ~65% when the original system message gets embedded (it strips XML but does not strip the system message).
  - `v12` markdown-only delimiters + **drops the conversation's original system message**: 0% trips across 6 fresh runs.

**Key takeaway**: the load-bearing trick is dropping the conversation's original system message from the analyzer's input. XML vs markdown alone is not enough. `s1` was an early step in this direction (drops XML) but missed the system-message piece.

## Why dropping the system message is delicate

The user flagged this directly: **for actions and database tasks, the system prompt contains task-critical information** (function schemas / DB schemas). Removing it from the analyzer's input means the analyzer doesn't see those constraints, which can degrade its task spec.

Counter-evidence (math / code / generic conversation): the system prompts there are usually generic role-defining boilerplate ("the assistant is designed to be helpful…"), and the analyzer doesn't need them to extract the user's intent — the user messages carry all task content.

The current LiC v8 system prompts by task:

| Task | System prompt content | Load-bearing for analyzer? |
|---|---|---|
| math (`math_system_prompt_v2.txt`) | Just "highlight final answer as **ANSWER: N**" — generic formatting. | No |
| code (`lcb_system_prompt_v2.txt` / `humaneval_system_prompt_v2.txt`) | Output-format ("wrap in `\`\`\`python` fences"). | No |
| database (`db_system_prompt_v2.txt`) | Generic helper + **the entire SQL schema** inlined via `[[SCHEMA]]`. | **YES** — schema is here, not in shards. |
| actions (`actions_system_prompt_v2.txt`) | Function-call format + **the entire function set** inlined via `[[FUNCTIONS]]` + accumulate instruction. | **YES** — function definitions are here. |

So a "drop system message" fix is safe for math and code; for database/actions it would need to selectively **keep** the load-bearing part (schema / function set) while dropping role-defining boilerplate.

## Contingency: `v13` design sketch

Only built if **both `v8` and `s1` trip CF > 5%** on a Phase 2 cell. Design:

### Goals

- 0% Azure jailbreak-filter trip rate (matching v12).
- Analyzer-content quality at parity with v8 (the post-mortem on v12 was that its content was rushed).
- Compatible with the existing `two_query` flow so no analyzer-code changes are needed.

### Concrete changes vs `v8`

1. **Drop the conversation's original system message UNLESS it is load-bearing for the task** (see table above). Implementation: the analyzer call site passes `task_name` to the prompt formatter, which decides whether to drop or preserve. For database/actions we keep the system prompt but rewrap it in plain `Schema:` / `Available functions:` markdown sections rather than the `<system_message>` XML wrapper.
2. **No XML tags anywhere in the prompt template, input, or expected output.** Use markdown headers for sections:
   - Input delimiters: `[user]:` / `[assistant]:` prefixes (no `<system_message>` / `<turn>` wrappers).
   - Output schema: `TASK SPECIFICATION:` / `ALIGNED:` / `ISSUES:` (already used by s1; carries over).
3. **Strip meta-instruction language** from the analyzer prompt. v8 says "You are an independent reviewer; do not hallucinate; follow exactly the schema below". Many of these phrases (especially "independent reviewer evaluating prompts") are what trip the filter. Replace with neutral framing: "Summarize the user's intent from the conversation below."
4. **Drop the `<task_spec>`-style XML output tags**, parse markdown headers instead. Update the analyzer's parser (one regex per section header).

### Validation gate before any large run uses v13

- Smoke probe: 10 problems × 1 task on gpt-5.4 + gpt-5-mini through Azure OAI. Verify 0/10 jailbreak trips.
- Quality probe: same 10 problems, compare v13's `task_spec` and `issues` outputs vs v8's. Quality target: human-readable parity, no obvious omissions for the task-critical info.

If either gate fails, we don't ship v13 — we report partial CF coverage on the affected cells and move on.

## Choosing a prompt version per cell

In the Phase 1/2 launchers we default to `v8`. The Phase 1+2 plan documents the escalation chain:

1. Cell runs with `v8` → check `content_filter_errors.jsonl` in the output dir.
2. Trip rate > 5% on that cell → rerun with `analyzer_prompt_version=s1`.
3. Trip rate still > 5% with `s1` → build `v13` (gated by the validation probe above) and retry.

In Phase 1 on DeepSeek-V4-Flash via the Foundry endpoint, expected trip rate is 0% because the Foundry-route OAI-compatible endpoint historically has not exhibited the same filter behavior as the dl-openai/fxdata-* Azure OAI routes. **But the Foundry endpoint is still part of Azure**, so the user warned us to not assume zero — we still monitor.

## Cross-benchmark consistency

`v8` is the planned default across LiC, CollabLLM, WildChat in the post-NeurIPS scale-up. The paper used:
- LiC: `v8`
- CollabLLM: `s1` (it was the only thing that worked through the Azure filter at the time of submission)
- Huang/WildChat Reset/Rewrite: `v8`
- Huang/WildChat Gated-Reset: `v11`

For the post-NeurIPS Phase 3 cross-benchmark redos we use **`v8` everywhere**, falling back to `s1`/`v13` per the escalation chain only if a specific cell trips CF.

## Open questions

- **Does Foundry (mgalley-foundry2) apply the same Azure jailbreak filter as the dl-openai/fxdata OpenAI Azure routes?** Unknown; we'll find out in Phase 1.
- **Has Azure's filter changed since May 2026?** Possible — they update heuristics regularly. The v8 trip rate might have moved. Empirical check on Phase 2's gpt-5.4 / gpt-5.5 cells will tell us.
- **Are there `gpt-5.4`-specific filter behaviors?** Each Azure-deployed model can theoretically have a different filter policy attached. Worth keeping an eye on if the trip pattern differs from what gpt-5-mini showed in May.
