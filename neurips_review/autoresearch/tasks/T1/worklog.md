# T1 — Condensation / summarisation baseline at matched call budget

**Reviewer prompt:** Area Chair "limited baselines" + Vg97 W1/Q1. We currently *argue* that
compaction / folding methods target context-length pressure rather than context pollution.
One run at the boundary converts that scoping argument into an empirical claim.

**Prediction (registered before running):** a faithful summariser carries invalidated reasoning
forward in compressed form and therefore does **not** close the multi-turn gap. If it does close
the gap, that is a real negative result for us and gets reported as such.

**Status:** in progress (2026-07-29 overnight session). **Operator asleep — no questions asked.**

---

## 0. Decisions taken up front (all ambiguity resolved here)

**D1 — venue.** LiC `database_v2` + `code_v2`, N=30 each (the full `data/lic_eval_subset.json`
slice per task). **No math**: session 1's T5 equal-budget control was run on near-ceiling math,
all arms landed at ~97.5%, and the experiment was non-discriminating. T2c independently shows
code/database are where the headroom is (baseline 22–32% on the informative subsets) while math
sits near ceiling.

**D2 — what the summarisation baseline is.** A *generic, non-analyzer* LLM condenser of the kind
production agent harnesses use for context-length management. Every turn it compresses the
conversation and the assistant proceeds from the condensed context.

**D3 — the fairness constraint that makes this an experiment rather than a strawman.** The
summariser is told to compress **faithfully**. It is never told to find errors, judge
correctness, remove invalidated reasoning, or drop the assistant's wrong approach. It is
explicitly told the opposite: *"Your job is compression, not evaluation… Preserve the
assistant's current approach and conclusions as they stand."* If it were told to drop wrong
reasoning it would just be AC3 and the comparison would be vacuous. Full prompts are reproduced
verbatim in §A so a reviewer can check we did not handicap it.

**D4 — plumbing parity.** `SummarizationStrategy` builds its replacement context with exactly
the same structure AC3-Reset / AC3-Rewrite use — `[system] + [compacted conversation] +
[latest user message]`, same `role="compacted conversation"` tag, same `trace.reset_conversation`
call, same `min_turns=1`. The *only* thing that differs between the summarisation arm and the
AC3 arm is the text of the replacement message. This is deliberate: it isolates "what the
replacement says" from "how replacement is plumbed in".

**D5 — call budget.** Measured, not asserted (see §2). AC3-Reset's `ConversationAnalyzer` is a
**two-query** flow (Q1 task spec from user messages only, Q2 comparison) → **2 extra LLM calls
per fired turn**. So we run *two* summarisation arms:
- `summarize_v1` — 1 condenser call/turn (the natural form; **under** AC3's budget).
- `summarize_v1_2pass` — condense + a faithfulness-refinement pass = **2 calls/turn, exact call
  parity with AC3-Reset**. Its only purpose is to close off "you gave the baseline half the
  compute". The refinement pass checks the *summary against the transcript*, never the
  assistant's work against the task.

**D6 — analysis cache disabled for the AC3 arms** (`experiment.strategy.analysis_cache_dir=null`).
Two reasons: (a) a cache hit means no LLM call, which would silently understate AC3's measured
budget and destroy the whole point of the measurement; (b) `outputs/analysis_cache` is shared
with two other agents running concurrently tonight. The cache key does include `analyzer_model`
(`analyzer.py:585`), so no stale-hit correctness risk existed — this is purely about clean
measurement and write contention.

**D7 — output isolation.** Everything under `outputs/T1/`. Concurrent agents share the
`outputs/` tree and have already caused one double-write corruption incident, so every cell gets
a task-scoped `logging.output_dir` and `metrics.json` is cross-checked against `run_summary.json`
before any number is trusted.

**D8 — FN-analysis model.** `false_negative_analysis.model=gpt-5.4-mini_2026-03-17` on every
cell. The default is not served on TRAPI and silently no-ops on every incorrect sample, which
deflates accuracy with no error raised. (RECON's worklog names `gpt-4o_2024-11-20`, which is
also served; the task brief specifies gpt-5.4-mini and that is what is used, uniformly across
all arms, so the adjustment is at least internally consistent.)

**D9 — replicates.** `seed=` is inert on LiC (`cfg.seed` is read only by `huang_eval/`).
Variation would come from `temperature: 1.0` only. N=1 per cell for now; if the sweep finishes
early, reps are added and called "replicate runs", never "seeds".

---

## 1. What was built

| file | what |
|---|---|
| `src/ctx_editor/strategies/summarization.py` | `SummarizationStrategy` — the condensation baseline. `num_passes ∈ {1,2}`. |
| `src/ctx_editor/strategies/prompts/summarize_v1.txt` | condenser prompt (verbatim in §A) |
| `src/ctx_editor/strategies/prompts/summarize_v1_refine.txt` | faithfulness-refinement prompt for the 2-call parity arm (verbatim in §A) |
| `src/ctx_editor/config/experiment/summarize_v1.yaml` | 1 call/turn arm |
| `src/ctx_editor/config/experiment/summarize_v1_2pass.yaml` | 2 calls/turn (budget-parity) arm |
| `src/ctx_editor/utils/call_meter.py` | process-global call/token meter (see §2) |
| `neurips_review/autoresearch/tasks/T1/run_t1.sh` | the sweep launcher |

Reuse audit, as instructed: `ContextCompactionStrategy` (`ac3_rewrite_v8_lic`) was read first.
It could **not** be reused as-is — it hard-wires a `ConversationAnalyzer` stage-1 and templates
the analyzer's `user_intent`/`aligned`/`issues` into the rewriter prompt, i.e. it *is* an
analyzer-driven method. Making it non-analyzer would have meant a `analyzer=None` code path
through `prepare_context` plus a bypass of the `compaction_analysis` logging — more invasive
than a 200-line strategy that mirrors its `_build_*_context` / `reset_conversation` structure
exactly. The new class is a deliberate structural copy of it minus the analyzer.

---

## 2. Budget measurement (this is a measurement, not an assertion)

Nothing in the repo measured strategy-side LLM cost: `UsageStats` only records the
`user` / `assistant` / `system` roles (`core/simulator.py`), so analyzer and rewriter calls were
invisible in `metrics.json` and `results.json`. Added `utils/call_meter.py`:

- a process-global accumulator hooked into `OpenAIModelClient._parse_response` — the single
  choke point every OpenAI-dialect response passes through;
- attribution via a `contextvars` tag so concurrent async conversations do not clobber each
  other's labels. `user_agent`, `system_agent`, `analyzer`, `context_compaction` and
  `summarization` tag their own calls; anything untagged defaults to `assistant`;
- dumped to `<run_dir>/call_meter.json` **before** false-negative analysis (so the numbers
  describe the experiment, not the post-hoc adjustment) and to `call_meter_final.json` after.

Verified on the smoke run (`outputs/T1/smoke_summarize_db`, 2 database samples, `summarize_v1`):
total 28 calls / 29,046 tokens, split `assistant` 8, `system` 8, `user` 6, `strategy` 6 — and
6 strategy calls is exactly the number of summarisation events logged in the traces. The meter
is consistent with the trace logs.

---

## 3. Smoke test (2 database samples, `summarize_v1`)

Ran before the sweep. Raw 1/2, adjusted 1/1 (the miss was FN-classified user-sim-induced).
The condenser output is a good-faith faithful summary — it reproduces the schema, the user's
two shards verbatim, **and the assistant's prior SQL unchanged**, with "Current state: the
initial approach was to find the match with the maximum `minutes`." That is precisely the
behaviour the experiment is designed to test: the prior approach is carried forward in
compressed form rather than audited.

---

## 4. Sweep

Launcher: `neurips_review/autoresearch/tasks/T1/run_t1.sh` (idempotent — skips any cell whose
`run_summary.json` already exists). Cells run **sequentially** at `execution.max_concurrent=5`;
TRAPI capacity is shared with two other agents tonight, so no parallel cells.

Order is deliberate — the core result lands first in case the session runs out of time:

1. `db_baseline` 2. `db_summarize1` 3. `db_reset`
4. `code_baseline` 5. `code_summarize1` 6. `code_reset`
7. `db_summarize2` 8. `code_summarize2`
9. `db_gated` 10. `code_gated`

Canonical command (all cells identical modulo `experiment=` / `task=` / dir):

```bash
ctx-editor \
  experiment=summarize_v1 \
  model=gpt5_4_mini_trapi \
  load_balancer=trapi \
  task=database_v2 \
  user_mode=sharded \
  execution.max_concurrent=5 \
  false_negative_analysis.model=gpt-5.4-mini_2026-03-17 \
  experiment_name=T1_db_summarize1 \
  logging.output_dir=outputs/T1/db_summarize1
```

AC3 cells add `experiment.strategy.analysis_cache_dir=null` (D6).

Launched 2026-07-29 ~11:52. Progress log: `neurips_review/autoresearch/tasks/T1/run_log.txt`.

---

## 5. Results

*(filled in as cells complete — see §6)*

---

## A. Appendix — the summariser prompts, verbatim

Reviewers will want to check the baseline was not handicapped, so both prompts are reproduced
in full. Source of truth: `src/ctx_editor/strategies/prompts/summarize_v1.txt` and
`summarize_v1_refine.txt`.

### A.1 `summarize_v1.txt` (the condenser — used by both summarisation arms)

```
You are condensing a multi-turn conversation so that it fits in a smaller context window.

The AI assistant in this conversation will continue working on the task. It will see ONLY the summary you produce, plus the system prompt and the most recent user message; it will not see the original conversation history. Your summary must therefore carry forward everything needed to continue seamlessly.

Write a faithful, information-preserving summary. Include:
- Every requirement, constraint, value, name, and detail the user has provided so far, stated precisely.
- What the assistant has done so far: the approach it is taking, the reasoning behind it, and any intermediate results, code, queries, or answers it has produced. Reproduce code, SQL, formulas, and specific values verbatim where they matter.
- The current state of the work and what remains to be done.
- Any assumptions, decisions, or clarifications that have been made during the conversation.

Guidelines:
- Be faithful to the conversation. Report what was actually said and done; do not add information that is not there, and do not invent details.
- Your job is compression, not evaluation. Do not judge whether the assistant's work is correct, do not critique it, and do not attempt to solve the task yourself. Preserve the assistant's current approach and conclusions as they stand.
- Preserve detail wherever removing it would lose information the assistant needs. Compress by removing redundancy, conversational filler, and repetition — not by dropping substance.
- Use whatever structure, sectioning, and length best preserves the content.

## System Prompt (for context; already visible to the assistant, do not repeat it)
{system_message}

## Conversation So Far
{conversation}

Wrap your final summary in <summary>...</summary> tags. Only the content inside those tags will be shown to the assistant.
```

### A.2 `summarize_v1_refine.txt` (second pass, budget-parity arm only)

```
You are reviewing a draft summary of a multi-turn conversation for FAITHFULNESS and COMPLETENESS before it replaces the conversation history.

The AI assistant in this conversation will continue working on the task and will see ONLY this summary, plus the system prompt and the most recent user message. If the summary omits or garbles something, that information is lost.

Compare the draft summary against the original conversation and produce a revised summary that fixes:
- Omissions: user-provided requirements, constraints, values, names, or details that are missing from the draft.
- Inaccuracies: anything the draft states that does not match what the conversation actually says.
- Lost specifics: code, SQL, formulas, numbers, or intermediate results that were dropped or paraphrased away and should be reproduced precisely.
- Missing state: what the assistant is currently doing, the reasoning behind it, and what remains to be done.

Guidelines:
- You are checking the summary against the transcript, not checking the assistant's work against the task. Do not judge whether the assistant's approach or answers are correct, do not critique them, and do not attempt to solve the task yourself. If the assistant took an approach, the summary should say so faithfully.
- Do not add information that is not in the conversation.
- If the draft is already faithful and complete, return it essentially unchanged.

## System Prompt (for context; already visible to the assistant, do not repeat it)
{system_message}

## Conversation So Far
{conversation}

## Draft Summary
{draft_summary}

Wrap your final revised summary in <summary>...</summary> tags. Only the content inside those tags will be shown to the assistant.
```

**Design tension recorded honestly.** The clause *"Your job is compression, not evaluation"* is
load-bearing in both directions. Without it, a strong model summarising a conversation may
spontaneously start auditing the assistant's work — which would make the arm a partial
reimplementation of AC3 and make a positive result uninterpretable. With it, a reviewer could
argue we forbade the baseline from doing the useful thing. We keep it, because the claim under
test is specifically "generic condensation ≠ pollution removal", and a condenser that removes
pollution is not a generic condenser. The sentence is also standard in real compaction prompts
(faithfulness instructions are the norm). If the result is null, the honest framing is: *the
gain comes from the audit, not from the compression* — which is exactly the paper's claim, and
the prompt makes that separation legible rather than hiding it.
