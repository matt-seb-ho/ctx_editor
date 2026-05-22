# R6 plan — analyzer parity + fixed-v1 (v8/v9) + GEPA to exceed Reset

**Status**: ready to execute. Phase 0 (the parity refactor) landed at
end of R5. New v8/v9 prompts created and smoke-tested this session.

**Resumes from**: `docs/reports/post_may18_r5_resume.md` and
`docs/post_may18_r5_analyzer_parity_plan.md` (predecessor — kept for
archival).

## TL;DR

Four experiments form the A-stage, ordered so we change one thing at
a time:

1. **A1 — original v1 prompt + v8 analyzer**. Locks down the
   "what does fixing only the analyzer do?" measurement. One-shot;
   not the going-forward baseline.
2. **A2 — v8 prompt (fixed v1) + v8 analyzer**. The new
   analyzer-centered baseline. v8 fixes the v1 wart where the rewriter
   was told to deprioritize the analyzer in favor of re-deriving the
   spec from raw user messages.
3. **A3 — v9_no_conv prompt + v8 analyzer**. Clean ablation against
   A2: identical prompt except `{conversation}` is removed.
4. **A4 — small-budget unbiased GEPA**, seeded from `max(A2, A3)`.
   Runs *regardless* of A2/A3 outcome because an LLM rewrite is
   strictly more expressive than Reset's template-fill, so we expect
   to beat Reset with modest search budget.

Then per-winner: cross-model on LiC + cross-benchmark on CollabLLM /
WildChat.

## Why we redesigned v1 → v8 this session

**Wart 1: v1 tells the rewriter to deprioritize the analyzer.**

- *"the reviewer's task spec is guidance but may contain errors"*
- *"Derive [the task spec] from the user's actual messages in the conversation"*
- *"If the reviewer's task spec contradicts what the user actually said in the conversation, trust the user's messages"*

This actively tells the rewriter to second-guess the analyzer and
re-derive the task spec from raw user messages. That framing made
sense when the analyzer was the bespoke `compaction_analysis.txt`
(which we now know produced bad task specs — see the GSM8K/2 smoking
gun). With the `v8` analyzer, designed specifically to extract task
spec from user-messages-only, this is now backwards: we built a
careful task-spec extractor and then told the rewriter to second-guess
it.

Knock-on for the ablation: A1 effectively says "trust user messages
over analyzer," while a no-conversation arm has no choice but to
trust the analyzer. That confounds "with vs without conversation"
with "deprioritize vs trust analyzer." Not clean.

**Wart 2: v1 mandates the two-section output shape (task_spec +
work_so_far) that Reset uses.** This was secretly enforced both in
the prompt and in the strategy's downstream parser (`_extract_tag`
pulling those exact tags, `_build_compacted_context` hardcoding the
headers `# User Task Specification (So Far)` and `# What Looks Right
So Far`). So even an "open-ended" prompt would funnel back into
Reset's template. That defeats the point of using an LLM rewrite
(which should be strictly more expressive than templated Reset).

**Fix**:

1. **Strategy** now supports `open_ended_output: true`. In that mode
   the LLM's full output is passed through as the compacted message
   body (wrapped with a single neutral preamble), no tag parsing,
   no enforced sections. Default remains `false` for v1–v6 backward
   compat.
2. **v8** = analyzer-centered framing + open-ended output. The
   prompt names the goal ("produce a message that gives the
   assistant the best chance of correctly responding to the user's
   most recent turn") and explicitly leaves structure / length /
   sectioning to the LLM.
3. **v9_no_conv** = v8 minus `{conversation}`. Differs ONLY by the
   conversation block.

**Wart 3: open-ended rewriter encroaches on the assistant's job.**
Initial smoke-test of open-ended v8 had the rewriter computing
`**ANSWER: 14**` itself on `sharded-GSM8K_1066`. That is a category
error: the rewriter's job is selective attention + mental reset,
not solving the task. Mitigation added this session: a
role-boundary paragraph in v8 and v9.

> Your role is to prepare context, not to solve the task. The
> assistant will produce the final response to the user; do not
> pre-compute the answer or write the assistant's reply on its
> behalf. Your job is selective attention: keep what helps, remove
> what distracts.

Re-smoke after the fix: partial mitigation. `GSM8K_1066` now
explicitly hands off the calculation; `GSM8K_189` still
pre-computes behind a thin handoff veneer. We will observe this at
A-stage scale; if persistent, an escalation phrase
("do not write any arithmetic that resolves to the user's final
answer") is the easy next iteration.

**System-prompt audit (this session)**: the rewriter is safe by
construction — `{conversation}` is populated via
`get_conversation_string(skip_system=True)` and the rewriter is
called as a bare user message (no system role). The analyzer is
*not* safe in this sense (uses `skip_system=False` plus a dedicated
`{system_message}` placeholder) but that surface is deferred to
`docs/global_todos.md` (a).

**Why A1 still exists**: we need *one* measurement of "original v1
prompt + new analyzer" to attribute the analyzer-parity delta cleanly
against the historical pre-parity numbers. A1 keeps the two-section
output shape (it has the v1 prompt + default `open_ended_output:
false`). We don't promote it to the new default.

## Pre-conditions (already met)

- ✅ `AC3RewriteStrategy` uses `ConversationAnalyzer` + `v8` prompt
  via shared `AnalysisCache` (R5 commit `44b3242`).
- ✅ All rewrite experiment YAMLs set `analyzer_prompt_version: v8`
  and point at `outputs/analysis_cache`.
- ✅ 3,311 v8 analyses cached on `htn50_52` (DSV4F 2257 / gpt-5.4
  531 / Kimi-K2.6 523). A1/A2/A3 hit cache for analyzer on DSV4F.
- ✅ `AC3RewriteStrategy` gained `open_ended_output: bool` kwarg.
  When true: the rewriter may put free-form scratchpad text before
  a `<new_context>...</new_context>` wrapper; only the wrapper
  contents are shown to the assistant. If the rewriter ignores the
  tag, the full output is used as-is (lenient fallback). No content
  shape (sections, task_spec/work_so_far division) is enforced.
- ✅ New v8 + v9_no_conv prompts + configs created and smoke-tested
  (2/2 each on math conv0 limit=2). No em dashes; no output-shape
  prescription. Configs set `open_ended_output: true`.
  - `src/ctx_editor/strategies/prompts/context_compaction_v8.txt`
  - `src/ctx_editor/strategies/prompts/context_compaction_v9_no_conv.txt`
  - `src/ctx_editor/config/experiment/ac3_rewrite_v8_lic.yaml`
  - `src/ctx_editor/config/experiment/ac3_rewrite_v9_no_conv_lic.yaml`
- ✅ Stale v7 prompt + config removed (never run on full sweep).

## A1 — original v1 + v8 analyzer

**Purpose**: lock down the "analyzer fix alone" measurement against
the historical pre-parity numbers. One-shot, not the going-forward
baseline.

**Config**: `experiment=ac3_rewrite_lic` (uses `context_compaction.txt`
= the v1 prompt, already on v8 analyzer).

**Wall clock**: **~20 min** (12 cells, MC=4, MAX_PARALLEL=4, analyzer
cache hits).

## A2 — v8 prompt (analyzer-centered) + v8 analyzer

**Purpose**: the new with-conversation baseline. This is the
going-forward default we'd put in the paper if it wins.

**Config**: `experiment=ac3_rewrite_v8_lic`.

**Wall clock**: **~20 min**.

## A3 — v9_no_conv + v8 analyzer

**Purpose**: clean ablation against A2; tests whether contagious
context pollution reaches the rewriter even with analyzer-centered
framing.

**Config**: `experiment=ac3_rewrite_v9_no_conv_lic`.

**Wall clock**: **~20 min**.

A1/A2/A3 share the analyzer cache; they can run concurrently with
separate output dirs. Combined wall **~25–30 min** depending on
load-balancer contention.

## A4 — small-budget unbiased GEPA

**Important**: A4 is **not gated** on A2/A3 falling short of Reset. We
run it regardless because the goal is to *exceed* Reset, not just
match it. An LLM rewrite is strictly more expressive than the Reset
template, so even a modest search budget should find a prompt that
beats Reset.

**Budget**: **20 metric calls** (down from R4's 30). Bump to 30 if the
first 20 still look like they're climbing.

**Seed**: whichever of A2 / A3 scored higher on the math mini-eval
(12 problems on math conv0). v1 is **not** in the seed pool — we don't
want GEPA optimizing the wart-bearing prompt.

**Reflection LM**: DeepSeek-V4-Flash (cost-cheap).

**Objective / background**: unbiased framing — `{conversation}`
optional, no Reset reference, no editorial about hallucination or
"faithful re-emitter."

### Objective string

> Optimize the prompt template for the second LLM call of a
> two-stage context-editing pipeline. The first stage already
> produced an analysis of a multi-turn conversation. Your prompt
> tells the second LLM how to turn (some subset of) the available
> inputs into a single 'compacted context' message that will
> REPLACE the conversation history before a downstream assistant
> generates its next response on a fixed last user message.
>
> Maximize the downstream task accuracy (LiC math eval on
> DeepSeek-V4-Flash).
>
> Available inputs (use any subset):
> - `{analysis_user_intent}` — analyzer's consolidated task spec.
> - `{analysis_aligned}` — analyzer's notes on what the assistant
>   got right.
> - `{analysis_issues}` — analyzer's notes on what the assistant
>   got wrong.
> - `{conversation}` — the full multi-turn conversation (OPTIONAL).
>
> Output format: the rewriter may put free-form scratchpad text
> first; wrap the final compacted message in
> `<new_context>...</new_context>`. Only the wrapped contents reach
> the downstream assistant.

### Background string

> The compacted context is the only summary the downstream assistant
> sees of the conversation history (besides the unchanged system
> prompt and the last user message). The compacted message should
> give the assistant enough state to continue the task correctly
> without dragging in distractions that might pull it off course.

**Wall clock**: **~30 min** at budget=20 (~1.5 min/eval based on R4's
30 calls → ~45 min observed); **~45 min** at budget=30.

**Open sign-off** (carried from R5 plan):
- Include or omit the "remove pollution / reorganize for downstream
  use" hint in `background`? Recommendation: **omit**.
- Math-only mini-eval, or cross-task? Recommendation: **math-only**.
- Reflection LM: DSV4F vs. gpt-5.4? Recommendation: **DSV4F**.

## A-stage wall clock summary

| Step | Wall (parallel) |
|---|---|
| A1 + A2 + A3 in parallel | **~25–30 min** |
| A4 GEPA (budget=20) | **~30 min** |
| A4 GEPA (budget=30 stretch) | ~45 min |
| **A-stage total** | **~55–75 min** |

## B-stage — validate the winner

Pick `winner ∈ {A1, A2, A3, A4}` by mean accuracy across the 12 DSV4F
cells (expected: A1 is reference, real candidates are A2/A3/A4).

### B1 — full-LiC re-confirmation on DSV4F

No-op if winner ran the full A-stage sweep. If winner is A4 (a new
prompt), run it through the 12-cell DSV4F sweep. **~20 min**.

### B2 — cross-model LiC sweep (gpt-5.4 + Kimi-K2.6)

12 cells × 2 additional models. Analyzer cache hits exist (gpt-5.4 =
531, Kimi-K2.6 = 523 — analyzer step is free).

- Per-model wall ~25–30 min.
- Two models in parallel (different LB pools): **~30–35 min**
  combined.

### B3 — cross-benchmark fills (CollabLLM + WildChat × 3 models)

Both benchmarks already have last-turn-replay infrastructure (each
cell = one rewrite + assistant call). Analyzer cache hits: confirmed
for the htn50_52 LiC prefix set; WildChat / CollabLLM may have
partial cache — check before running. Worst case: pay for analysis on
cold cells.

- **CollabLLM × winner × 3 models**: 2 datasets × 20 problems × 3
  models. **~30–35 min** combined when parallel across models.
- **WildChat × winner × 3 models**: 76 prefixes × 3 models. **~30
  min** parallel.

### B-stage wall clock summary

| Step | Conditions | Wall (parallel) |
|---|---|---|
| B1 — re-confirm winner on DSV4F | only if winner = A4 | 20 min |
| B2 — cross-model LiC | winner beats prior Rewrite by ≥3pp | ~35 min |
| B3 — cross-benchmark × 3 models | winner clearly wins LiC | ~65 min |
| **B-stage total** (B2 + B3, +B1 if needed) | full follow-up | **~100–120 min** |

## Total R6 wall-clock envelopes

| Scenario | A-stage | B-stage | Total |
|---|---|---|---|
| Best (A2 or A3 already > Reset, drop A4 if user agrees) | ~25 min | optional 35–100 min | 25 min – 2 h |
| Standard (A1+A2+A3+A4@20, then full B) | ~60 min | ~100–120 min | **~2.5–3 h** |
| Stretch (A4@30, full B) | ~75 min | ~120 min | ~3 h 15 m |

Leaves a workday window for tau2 follow-up.

## Tau2 budget context (next phase after R6)

After R6 wraps, tau2 work picks up:

- **Step 5 — Hydra-ify** `tau2-bench/ctx_edit/run_parallel.py`:
  ~1–2 h.
- **First tau2 sweep** (winner + Augment + Reset on one model,
  telecom domain): ~1–2 h.
- **Cross-model tau2 probe**: ~1–2 h more.

A same-day session covering R6 + tau2 step 5 + first tau2 sweep is
realistic if R6 stays in the ~3h envelope.

## Risks and open sign-off questions

1. **GEPA hint** — include "remove pollution / reorganize for
   downstream use" in `background`? Recommendation: **omit**.
2. **GEPA budget** — 20 metric calls (default) or 30 (stretch)?
   Recommendation: **20**.
3. **GEPA always-on** — A4 runs even if A2/A3 already beat Reset.
   Confirmed this session.
4. **B2 trigger threshold** — ≥3pp avg margin over prior Rewrite
   numbers (default).
5. **B3 scope** — both CollabLLM and WildChat parallel (default).
6. **WildChat / CollabLLM analyzer cache** — precheck cache hits
   before running B3; cold cells add ~$1–3 in foundry credits.

## Execution checklist

A-stage:

- [ ] Confirm `outputs/analysis_cache/ | wc -l` ≥ 3,311.
- [ ] Verify rewrite YAMLs on v8 (`grep analyzer_prompt_version
  src/ctx_editor/config/experiment/ac3_rewrite*.yaml`).
- [ ] Create `scripts/run_post_may18_r6_a_stage.sh` covering A1, A2,
  A3 in parallel (copy v6 template, swap experiments + TAG).
- [ ] Launch A1/A2/A3.
- [ ] Run
  `scripts/analysis_rewrite_v_reset/compare_rewrite_versions.py`
  with the new dirs.
- [ ] Launch A4 GEPA seeded by `max(A2, A3)`.
- [ ] Write `docs/reports/post_may18_r6_summary.md` with A-stage
  table.

B-stage:

- [ ] If winner = A4: run B1.
- [ ] If winner beats prior by ≥3pp: run B2.
- [ ] If winner clears the bar: precheck WildChat/CollabLLM analyzer
  cache, then run B3.
- [ ] Update `post_may18_r6_summary.md` with B-stage table + paper
  cells.

## File map

| File | Role |
|---|---|
| `docs/post_may18_r5_analyzer_parity_plan.md` | Predecessor (full refactor rationale) |
| `docs/reports/post_may18_r5_resume.md` | R5 wrap-up |
| `docs/analyzer_parity_finding.md` | Smoking-gun analyzer bug write-up |
| `docs/post_may18_r6_plan.md` (this file) | R6 plan + wall-clock budget |
| `docs/post_may18_r6_design_iterations.md` | Design-decision log for R6 prompts + strategy changes (this session) |
| `docs/global_todos.md` | Cross-batch follow-up ideas (sys-prompt preprocessing, input-order ablation, negative-guidance) |
| `src/ctx_editor/strategies/context_compaction.py` | `AC3RewriteStrategy` (shared v8 analyzer) |
| `src/ctx_editor/strategies/prompts/context_compaction.txt` | A1 prompt (v1, unchanged — used for one historical-comparison run) |
| `src/ctx_editor/strategies/prompts/context_compaction_v8.txt` | **NEW** A2 prompt (fixed v1, analyzer-centered, with conversation) |
| `src/ctx_editor/strategies/prompts/context_compaction_v9_no_conv.txt` | **NEW** A3 prompt (v8 minus `{conversation}`) |
| `src/ctx_editor/config/experiment/ac3_rewrite_lic.yaml` | A1 config |
| `src/ctx_editor/config/experiment/ac3_rewrite_v8_lic.yaml` | **NEW** A2 config |
| `src/ctx_editor/config/experiment/ac3_rewrite_v9_no_conv_lic.yaml` | **NEW** A3 config |
| `scripts/gepa_rewrite/run_gepa.py` | GEPA driver — needs new objective/background for A4 |
| `scripts/analysis_rewrite_v_reset/compare_rewrite_versions.py` | Cross-variant aggregator |
