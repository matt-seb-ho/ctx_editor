# R6 design iterations — prompt + strategy decisions

**Companion to**: `docs/post_may18_r6_plan.md`. Captures the
back-and-forth that produced the v8/v9 prompts and the
`open_ended_output` strategy mode. Reading this is optional; the
plan doc is the canonical source of "what we're about to run."

This log exists so a reader can reconstruct *why* the v8 design
choices look the way they do, especially when a particular choice
looks arbitrary in isolation.

## Session timeline

### Iteration 0 — R5 wrap-up state

Coming in: analyzer-parity refactor landed (R5 commit `44b3242`).
`AC3RewriteStrategy` now uses the shared `ConversationAnalyzer` +
`v8` analyzer prompt instead of the bespoke `compaction_analysis.txt`.
The smoking-gun finding from `docs/analyzer_parity_finding.md` is
documented. Existing rewrite prompts (v1, v2, v3*, v4, v5, v6) were
expected to work unchanged against the new analyzer.

Open question entering this session: was the Rewrite-vs-Reset gap
mostly an analyzer-parity issue, or is the rewriter prompt itself
also worse than Reset's template-fill?

### Iteration 1 — initial three-arm plan

Initial framing of R6 had three arms:

- A1 — v1 + v8 analyzer (parity probe)
- A2 — v3-no-conv + v8 analyzer (test the "remove conversation"
  hypothesis from `docs/next_todos_post_may18.md` Task 1.2b)
- A3 — GEPA fallback if A1/A2 trail Reset

Wall-clock budget targeted ~2.5–3 h so the tau2 follow-up
(`docs/tau2_absorption_decision.md` Step 5 + sweeps) would still fit
the working window.

### Iteration 2 — v3-no-conv was a confounded ablation

User pointed out that `context_compaction_v3_no_conv.txt` was not a
clean ablation against v1. v3 had additional Reset-style
editorialization baked in:

- *"**promote** the reviewer's content into the assistant's working context"*
- *"**Re-emit** the reviewer's task specification as a clean, numbered list"*
- *"Do NOT include verbatim code blocks or numerical computations"*

That conflated "remove conversation" with "act more like Reset's
template." For a clean conversation-presence ablation we need a
no-conversation arm that's structurally identical to v1 in all
other respects.

Action: created `context_compaction_v7_no_conv_minimal.txt` as v1
minus `{conversation}`. Smoke-tested 2/2 on math conv0 limit=2.

### Iteration 3 — GEPA reframed from "fallback" to "stretch goal"

User: even if A1/A2 reach Reset parity, we should still try to
*exceed* Reset. An LLM rewrite is strictly more expressive than
templated Reset, so even a modest GEPA search should find a
prompt that wins.

Changes:

- A3 (GEPA) now runs *unconditionally*, not gated on A1/A2 trailing.
- Budget cut from 50 → 20 metric calls (we're not exploring a wide
  design space; we're looking for incremental gains over a
  now-stronger baseline).
- Seed = max(A1, A2) rather than always v1.

User also asked for follow-up wall-clock for cross-model
(gpt-5.4 + Kimi-K2.6) and cross-benchmark (CollabLLM + WildChat)
runs on the winner. B-stage section added to the plan.

### Iteration 4 — v1 itself has a wart

User asked whether v1 was the right baseline to lock in. Honest
read on v1 surfaced what we now call **Wart 1**:

- *"the reviewer's task spec is guidance but may contain errors"*
- *"Derive [the task spec] from the user's actual messages in the conversation"*
- *"If the reviewer's task spec contradicts what the user actually said in the conversation, trust the user's messages"*

These actively tell the rewriter to deprioritize the analyzer and
re-derive the spec from raw user messages. That framing made sense
when the analyzer was the bespoke `compaction_analysis.txt` (which
produced bad task specs — see the GSM8K/2 smoking gun); with the
v8 analyzer it is now backwards.

Knock-on effect on the v1 vs no-conv ablation: A1 ("trust user
messages over analyzer") vs A2 (no conversation, forced to trust
analyzer) confounds presence-of-conversation with
deprioritize-vs-trust-analyzer. Not clean.

Decision (proposed by user, confirmed): keep v1 unchanged for *one*
historical-comparison run (still useful for attributing the
analyzer-parity delta against pre-parity numbers), but create a
fixed-v1 prompt as the going-forward baseline. The fixed prompt is
the one v9_no_conv should be derived from.

Action: created `context_compaction_v8.txt` (analyzer-centered,
with conversation) and `context_compaction_v9_no_conv.txt` (v8
minus `{conversation}`). Removed the never-run v7 prompt + config.
Smoke-tested 2/2 each.

### Iteration 5 — em dashes + Reset-shape mimicry

User flagged two things about the v8 prompt:

1. Stylistic: remove em dashes (carried project preference).
2. Substantive: v8 was still mandating a two-section output shape
   (`<task_spec>` + `<work_so_far>`), which mimics Reset's
   template. The whole point of using an LLM rewrite is that it's
   strictly more expressive than templated Reset. Locking it into
   the same shape defeats that.

Investigated the strategy code and discovered **Wart 2**: the
two-section shape was enforced both in the prompt *and* in the
strategy's downstream parser:

- `_extract_tag` pulled `<task_spec>` / `<work_so_far>` (or
  `<verified_work>`) tags.
- `_build_compacted_context` hardcoded the headers
  `# User Task Specification (So Far)` and
  `# What Looks Right So Far`.

So even an "open-ended" prompt was being funneled back into Reset's
template by the strategy itself.

Action: added an `open_ended_output: bool = False` kwarg to
`AC3RewriteStrategy`. When `true`, the LLM's full output passes
through as the compacted message body (no tag parsing, no enforced
sections); default `false` preserves v1–v6 backward compat.
Rewrote v8 + v9_no_conv to drop em dashes and stop prescribing
sections.

Smoke-test observation: open-ended v8 on `sharded-GSM8K_1066`
produced the final numeric answer (`**ANSWER: 14**`) itself instead
of preparing context. Flagged as a possible confound for the
A-stage; we'd see if it persists.

### Iteration 6 — overreaction check + CoT scratchpad

User reconsidered whether the two-section division was actually
restrictive. Honest read: it names a real semantic distinction
(user-grounded task spec vs. potentially-wrong assistant work) that
is worth preserving conceptually; the question is whether
*enforcing* it locks the rewriter out of organizations we haven't
thought of. The open-ended A2/A3 lets the data tell us; if it
underperforms a structured baseline, we add a "structured-but-warts-
fixed" arm in a future round. Don't pre-commit.

Two minor follow-ups from user:

1. "the user's most recent turn" → "the user's request(s)" (more
   general, handles cases where the most recent message is not the
   canonical request).
2. "Output ONLY the message itself" denies non-reasoning models a
   scratchpad. Reasoning models (DSV4F, GPT-5, Claude) have
   internal CoT, but the framing shouldn't depend on that.

Action: introduced a single `<new_context>...</new_context>`
wrapper tag. The rewriter may put free-form scratchpad text before
the tag; only the wrapper contents reach the assistant. Strategy
parses `<new_context>` first, falls back to the full output if the
tag is absent (lenient — models that follow instructions get
scratchpad, models that ignore the tag still work).

Verified the parse + fallback against three cases (with tag +
scratchpad, no tag, unclosed tag) and re-ran smoke tests (2/2).

### Iteration 7 — rewriter doing the assistant's job is a category error

User: the rewriter pre-computing the answer is a confound, not a
feature. The point is selective attention and mental reset, not
solving the task. LiC tasks may be easy enough to be single-turn
solvable, which is why the encroachment is happening here.

System-prompt audit (requested by user): could the original task's
system prompt (with role framing like "you are a math solver") be
leaking into the rewriter and biasing it to act as the solver?
Findings:

- **Rewriter**: safe by construction. `{conversation}` uses
  `get_conversation_string(skip_system=True)` — original system
  message is stripped. The rewriter LLM is itself called as a
  bare user message (no system role), so no role-priming on the
  rewriter call.
- **Analyzer**: NOT safe in the same sense. Uses
  `skip_system=False` plus a dedicated `{system_message}`
  placeholder, so role framing is prominently visible to the
  analyzer LLM. Deferred to global TODO (a).

So the rewriter encroachment is most likely the rewriter
pattern-matching to solver-style assistant turns inside the
conversation, plus my prompt not explicitly forbidding it.

Action (this session): added a role-boundary paragraph at the top
of v8/v9:

> Your role is to prepare context, not to solve the task. The
> assistant will produce the final response to the user; do not
> pre-compute the answer or write the assistant's reply on its
> behalf. Your job is selective attention: keep what helps, remove
> what distracts.

Re-smoke: partial mitigation. `GSM8K_1066` now explicitly hands
off; `GSM8K_189` still pre-computes behind a thin handoff veneer.
Will observe at A-stage scale; escalation phrase ("do not write
any arithmetic that resolves to the user's final answer") is the
easy next iteration if it persists.

### Iteration 8 — global TODOs

User pulled out three follow-up ideas that aren't bound to R6 and
asked for a cross-batch place to track them:

(a) Programmatic system-prompt preprocessing for the analyzer (and
    by symmetry, possibly the rewriter via its assistant-turn
    inputs).
(b) Order-of-inputs ablation for the rewriter: try putting the
    `{conversation}` block above the analyzer's notes (analyzer
    closest to the generation point).
(c) Negative-guidance content in the compacted context: explicit
    "avoid this direction" statements alongside the positive
    content.

Action: created `docs/global_todos.md` with each item written up
with status / idea / hypothesis / open-questions / effort.
Registered in `docs/index.md` Start-here section + chronological
log.

## Net design changes (relative to R5 wrap-up)

| Surface | Change |
|---|---|
| `AC3RewriteStrategy` | New `open_ended_output: bool` kwarg. When true, `<new_context>`-wrapped output is the compacted message body; falls back to full output if the tag is absent. Trace log adds `compacted_open_ended_text`. |
| Default rewriter prompt going forward | v8 (analyzer-centered, open-ended, with conversation, role-boundary clause, `<new_context>` wrapper). |
| No-conversation ablation arm | v9_no_conv = v8 minus `{conversation}`. |
| Historical-comparison arm | A1 keeps the original v1 prompt + default `open_ended_output: false` (two-section structured output). One-shot, not the going-forward baseline. |
| GEPA (A4) | Always-on (not gated on A2/A3 falling short). Budget 20. Seeded by max(A2, A3). Objective updated to reflect `<new_context>` wrapper. |
| B-stage | Cross-model (gpt-5.4 + Kimi-K2.6) + cross-benchmark (CollabLLM + WildChat × 3 models) wall-clock added. |
| Global follow-ups | `docs/global_todos.md` for the three cross-batch ideas. |

## Behavioral observations from smoke tests (worth re-checking at A-stage scale)

1. **Rewriter encroachment**: open-ended v8 occasionally pre-computes
   the final answer despite the role-boundary clause. Look for
   `**ANSWER: ...**` patterns inside the `compacted_open_ended_text`
   field in A2/A3 traces.
2. **A2 vs A3 verbosity asymmetry**: in the smoke tests, A3
   (no-conv) tended to be more reserved (handed off the
   computation), while A2 (with-conv) tended to do more of the work
   itself. Watch whether this drives a real accuracy delta or just
   shifts where the work happens.
3. **Tag adherence**: DeepSeek-V4-Flash followed the
   `<new_context>` wrapper reliably in smoke tests; the lenient
   fallback was not triggered. If cross-model B2 surfaces a model
   that ignores the tag, the fallback handles it.
