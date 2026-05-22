# Global TODOs

Long-running ideas worth exploring, decoupled from any active batch.
Per-batch followup docs (`post_may18_r3_followups.md`,
`post_neurips_r2_followups.md`, etc.) capture things specific to one
round of experiments; this file is for cross-cutting items that
outlive any single batch.

## Open

### (a) System-prompt preprocessing for analyzer (and possibly rewriter)

**Status**: not started. Raised 2026-05-21 during R6 planning.

**Idea**: the analyzer feeds `trace.get_conversation_string(skip_system=False)`
+ a dedicated `{system_message}` placeholder into its v8 prompt, so
the original task's system prompt (with role framing like
"You are a math solver" or "You are a database expert") is
prominently visible to the analyzer LLM. Possible failure mode:
- the role framing biases the analyzer into adopting the same role
  mindset, which may be a form of context pollution analogous to the
  one we already documented for the "task-spec from full conversation"
  variant.

Programmatic guard candidates:
- LLM-driven: a one-shot pre-step that strips "you are X / your role
  is Y" sentences while preserving genuinely task-relevant content
  (e.g. format directives, answer formats).
- Heuristic: regex strip of known role-priming patterns.
- Argument-from-symmetry: if we do this for the analyzer, the
  rewriter's `{conversation}` *does* contain assistant turns that may
  have been generated under the role-priming system prompt, so the
  same kind of pollution could leak in via assistant outputs even
  though the system message itself is stripped via `skip_system=True`.

**Open questions**:
- Does it actually matter empirically? Need a controlled ablation.
- Is the "format directive" content in system prompts (e.g.
  `**ANSWER: [n]**` format) load-bearing for downstream evaluation?
  Stripping must preserve those.

**Effort**: medium. ~1 day to prototype a preprocessor + run a
controlled ablation across math / code / database.

### (b) Order-of-inputs ablation for the rewriter

**Status**: not started. Raised 2026-05-21 during R6 planning.

**Idea**: the v8 / v9 rewriter prompt currently lays out:
1. Reviewer's notes (task spec, aligned, issues)
2. Full conversation history

Test moving the analyzer outputs *below* the conversation, i.e.:
1. Full conversation history
2. Reviewer's notes

**Hypothesis**: putting the analyzer's clean structured summary
closest to the rewriter's generation point (lowest in the prompt)
may anchor the rewriter on the clean version rather than on the
verbatim conversation. Mirrors the "recency bias in long contexts"
findings.

**Effort**: trivial code (swap two block orderings) + ~30 min
mini-eval. The expensive part is plumbing it through cross-model
follow-up if the result is meaningful.

### (c) Negative-guidance content in compacted context

**Status**: not started. Raised 2026-05-21 during R6 planning.

**Idea**: currently both Rewrite (v1-v9) and Reset explicitly avoid
including the analyzer's "issues" content in the assistant-facing
compacted context; the framing is "remove pollution, don't
redescribe it." Test the opposite: include explicit negative
guidance like "previous approaches that led nowhere included X,
avoid that direction."

**Tension with current design**: our working hypothesis is that
context pollution is contagious, so even *describing* the bad
direction risks anchoring the assistant on it. But there's
prior-art literature (e.g. negative few-shot exemplars in some
prompt-engineering work) suggesting explicit "don'ts" can help.

**Variants worth testing**:
- Rewrite-side: add an optional `<avoid>` section.
- Reset-side: extend the template with a third "avoid" field.
- Aggressive (probably bad): include the analyzer's full issues
  string verbatim.
- Minimal (most likely OK): a single one-line summary of the most
  recent dead-end.

**Effort**: low for the prompt variant + mini-eval; comparable to
A-stage of a normal round.

## Done / superseded

(nothing yet)
