# Rewrite (AC3-Rewrite) Failure-Mode Analysis

> ⚠️ **Caveat — Rewrite numbers pre-analyzer-parity (2026-05-21)**: any AC3-Rewrite result in this doc was computed with `AC3RewriteStrategy._run_analysis` using the bespoke `compaction_analysis.txt` prompt — **not** the shared `ConversationAnalyzer + v8` used by Augment / Reset / Gated-Reset. Some unknown fraction of the Rewrite-vs-Reset gap is attributable to analyzer divergence rather than the rewriter step. Augment / Reset / Gated-Reset numbers in this doc are unaffected. See [`docs/analyzer_parity_finding.md`](../analyzer_parity_finding.md) for the smoking gun and [`docs/post_may18_r5_analyzer_parity_plan.md`](../post_may18_r5_analyzer_parity_plan.md) for the re-run plan.


**Date**: 2026-05-18
**Author**: Claude (overnight R2, autonomous)
**Status**: Draft — final numbers + v2 outcomes filled in once cells finish.

## Question

The Phase-1 (post-NeurIPS AC3) sweep found that the LLM-based Rewrite
strategy *underperforms* every other intervention — including Baseline
— on three of four LiC tasks:

| Strategy | math | code | database | actions | Δ vs Baseline (avg) |
|---|---|---|---|---|---|
| Baseline | 72.2 | 34.5 | 22.4 | 76.0 | 0 |
| Reset | 81.9 | 59.3 | 49.0 | 83.3 | +17.1pp |
| Rewrite | 73.6 | 28.3 | 27.9 | 74.0 | -0.3pp |

Reset uses the same analyzer output but pipes it through a
template (Reset = templatized restatement of the analyzer's notes;
Rewrite = an extra LLM call that "produces compacted context"). The
question this report answers: **what does the extra rewrite LLM call
actually break?**

## Method

Two-tier LLM-driven analysis, hierarchical:

1. **Failure extraction** (`scripts/analysis_rewrite/extract_failures.py`):
   walks Phase-1 outputs, finds 178 rewrite samples where Reset (or
   Baseline / AO) succeeded but Rewrite failed. Per-task counts:
   actions=35, code=59, database=57, math=27.
2. **Failure classification** (`scripts/analysis_rewrite/categorize_failures.py`):
   I read 4 traces (one per task) and hypothesized 7 failure modes
   (F1–F7). Then queried **DeepSeek-V4-Flash** as a labeler over a
   balanced sample (12 per task = 48 cases total), classifying primary
   + secondary failure modes for each case. Outputs:
   `scripts/analysis_rewrite/data/rewrite_failure_labels.jsonl`.
3. **Aggregation** (`scripts/analysis_rewrite/aggregate_labels.py`):
   distribution + co-occurrence + illustrative rationales.

## Failure modes (hypothesized from 4-trace human reading)

- **F1 — Lost meta-structure.** Compaction preserves task spec but
  drops a structural requirement ("compute both pairs", "return
  parallel function calls", "sum across sub-problems"). Assistant
  produces a partial-answer matching the rewritten (incomplete) spec.

- **F2 — Anchored on partial wrong work.** Compaction preserves an
  early, mathematically-wrong intermediate result as "What Looks Right
  So Far"; assistant extends the wrong work rather than rederiving.

- **F3 — Compaction interpretive bias.** Compaction speculates about
  future steps ("80% of 40 would leave 8 pizzas"); assistant parrots
  the speculation as the answer.

- **F4 — Overfit requirements.** Compaction re-narrates the user's
  task with phantom requirements (extra columns, extra constraints)
  the user never asked for; assistant produces the over-fit answer.

- **F5 — Schema / detail lost.** Compaction drops task-critical
  reference material — schemas, function signatures, exact test-case
  inputs, return-type requirements; assistant guesses and is wrong.

- **F6 — Tone / format mismatch.** Compaction reformats output style
  (loses code fences, `\boxed{}`, etc.).

- **F7 — Other.**

## Results (n=48 labeled cases, DeepSeek-V4-Flash labeler)

| Task | F1 | F2 | F3 | F4 | F5 | F6 | F7 | n |
|---|---|---|---|---|---|---|---|---|
| actions | 9 | 0 | 0 | 2 | 0 | 0 | 1 | 12 |
| code | 1 | 1 | 0 | 6 | 4 | 0 | 0 | 12 |
| database | 0 | 0 | 0 | 10 | 1 | 0 | 1 | 12 |
| math | 1 | 8 | 0 | 3 | 0 | 0 | 0 | 12 |
| **All** | 11 | 9 | 0 | 21 | 5 | 0 | 2 | 48 |

Secondary distribution: F5×13, F1×6, F4×4, F3×3. Top
primary×secondary pair: **F4 ⨯ F5 = 13** (over half of F4 cases also
lost task-critical detail). Mean labeler confidence 0.95.

**Headline**: each task has a distinctive Rewrite failure mode.

- **Actions (F1 = 9/12 = 75%)** — parallel-call structure dropped.
- **Database (F4 = 10/12 = 83%)** — phantom columns / overfitting the
  SELECT projection.
- **Code (F4 + F5 = 10/12 = 83%)** — wrong return-type AND wrong
  phantom parameters.
- **Math (F2 = 8/12 = 67%)** — preserved wrong intermediate
  computations as established fact.

Overall F4 = 21/48 = **44%** is the single dominant cause; including
its co-occurrence with F5 (where the LLM substitutes one requirement
for another) it touches the majority of cases.

### Per-task character

- **Actions (F1 dominant)**: parallel-function-call structure is the
  metarequirement; rewrite consistently drops it. The user's "compute
  GCDs for both pairs" becomes "compute GCD for the latest pair."
- **Code (F4 + F5)**: rewrite both adds phantom parameters (e.g., a
  bogus "threshold") AND drops the actual return-shape requirement
  (e.g., "return a tuple of (palindrome, changes)"). The assistant
  ends up answering a different problem.
- **Database (F4 dominant)**: classic SELECT-bloat — rewrite asks for
  Maker, FullName, COUNT when the user wanted just (Id, FullName);
  rewrite invents extra columns to project that are not in the spec.
- **Math (F2 dominant)**: rewrite preserves a wrong intermediate
  calculation as "established fact" ("Year 8 = 800 fruits", "$30.67
  per client"). The assistant builds on the wrong base.

### Conversation-length correlation

Rewrite v1 accuracy by `num_turns` (Phase 1 DeepSeek, all 4 tasks
pooled, n ≥ 3 per bucket):

| turns | n | accuracy |
|---|---|---|
| 3 | 15 | 73.3% |
| 4 | 53 | 64.2% |
| 5 | 160 | 51.2% |
| 6 | 148 | 50.0% |
| 7 | 95 | 65.3% |
| 8 | 38 | 44.7% |
| 9 | 13 | 30.8% |
| 10 | 8 | 25.0% |
| 11 | 11 | 27.3% |

Roughly monotonic decline past 5 turns. Longer conversations give the
compaction LLM more material to lose track of (F5) or invent around
(F4). Consistent with the failure-mode story.

### Why Reset doesn't suffer the same way

Reset emits the analyzer's `task_spec` / `aligned` / `issues` sections
verbatim into a templated message — no second LLM is asked to
*re-narrate*. Because Reset doesn't paraphrase, it can't add phantom
requirements (F4) or drop schemas (F5) in the same way. It can still
fail if the analyzer's output is wrong, but it doesn't compound by
running an additional interpretation pass.

The empirical gap (~21pp on database, ~31pp on code) is consistent
with rewrite being a *higher-variance* operation that mostly hurts on
tasks where exact-value preservation matters most.

## Implication for the paper

This is the cleanest articulation we have of "why the simpler
intervention wins":

- Rewrite is **flexible** — it can recombine, reword, and prioritize.
  In principle this is good for ambiguous or messy contexts.
- Rewrite is **lossy** — re-narration introduces opportunities to
  invent or drop requirements. In our deterministic
  task-spec-preservation setting, this is a net negative.

Reset wins because the operation it performs is *narrower* — promote
analyzer output into a structured context message, without a second
"interpret what the user wants" pass.

## v2 prompt design

`src/ctx_editor/strategies/prompts/context_compaction_v2.txt` (already
in-tree, previously unused). Key changes that target the observed
failure modes:

- **Numbered enumeration of sub-tasks** with explicit "Do NOT merge
  distinct sub-tasks" → F1.
- **"Be EXHAUSTIVE — missing a single parameter value, constraint, or
  sub-task will cause the assistant to fail"** → F4 (drop side) and
  F5.
- **"Preserve exact values: numbers, strings, column names, function
  signatures, formulas. Do not paraphrase values."** → F4 (add side)
  and F5.
- **"Output as structured data (exact values, function calls,
  results), not prose"** → F3.

Wired up via `compaction_prompt` kwarg on
`AC3RewriteStrategy.__init__` and new experiment config
`ac3_rewrite_v2_lic.yaml`.

## v2 results

Launcher: `scripts/run_post_neurips_r2_rewrite_v2.sh` —
12 cells (4 tasks × 3 prefixes), DeepSeek-V4-Flash, last-turn
replay against the htn50_52 prefix set. Aggregator output:
`docs/reports/post_neurips_r2_rewrite_v2.md`.

| Task | v1 Rewrite (Phase 1) | v2 Rewrite (R2) | Δ vs v1 | Reset baseline |
|---|---|---|---|---|
| math | 73.6% | 70.8% ± 14.4pp | **−2.8pp** | 81.9% |
| code | 28.3% | 36.3% ± 9.9pp | **+8.0pp** | 59.3% |
| database | 27.9% | 21.8% ± 5.0pp | **−6.1pp** | 49.0% |
| actions | 74.0% | 70.0% ± 7.2pp | **−4.0pp** | 83.3% |
| **avg** | 50.9% | 49.7% | **−1.2pp** | 68.4% |

Sample-by-sample (script:
`scripts/analysis_rewrite/compare_v1_v2.py`), across 554 shared
samples:

| Task | n | v1 acc | v2 acc | v1→v2 fixed | v1→v2 broke | net |
|---|---|---|---|---|---|---|
| actions | 150 | 74.0% | 70.0% | +14 | −20 | −6 |
| code | 113 | 28.3% | 36.3% | +12 | −3 | **+9** |
| database | 147 | 27.9% | 21.8% | +6 | −15 | **−9** |
| math | 144 | 73.6% | 70.8% | +7 | −11 | −4 |
| **All** | 554 | 52.3% | 50.5% | +39 | −49 | **−10** |

### Interpretation

The v2 prompt is **net slightly negative** but breaks down distinctly
by task:

- **Code: clear win (+9 cases, +8pp).** The "preserve exact values"
  rule fixes F5 cases (return-shape, parameter signature loss). E.g.
  HumanEval/83: v2 correctly distinguishes "start-with-1 ∨ end-with-1"
  using inclusion-exclusion; v1 had used the wrong formula factor.

- **Database: regression (−9 cases, −6pp).** The "Be EXHAUSTIVE"
  instruction makes F4 (overfit / phantom columns) *worse*: v2 turns
  a clean `SELECT AVG(Age), MIN(Age), MAX(Age)` into a window-function
  query that pulls every column from the table. The LLM is interpreting
  "exhaustive" as "include everything mentioned anywhere in
  conversation."

- **Actions: regression (−6 cases, −4pp).** v2 helps F1 (parallel-call
  enumeration) on some samples (we saw a clean fix on
  BFCL/parallel_170 where 3 compound-interest calls are correctly
  enumerated and emitted) but breaks others where "exhaustive
  numbered list" produces over-broad call sets.

- **Math: small regression (−4pp).** F2 (anchored on partial wrong
  work) isn't addressed by v2 since the "verified work" section still
  permits the same anchoring.

### Bottom line

**Prompt engineering alone cannot close the Rewrite gap.** The dominant
failure mode is F4 (overfit / over-interpretation), and instructions
to "preserve more" or "enumerate exhaustively" reduce one side of
F4 (drop) while exacerbating the other (add). Reset wins because it
does not run an extra "interpret what the user wants" pass — the
analyzer's structured output is promoted into context verbatim, with
no opportunity for the kind of phantom-requirement creep we see in
both v1 and v2 of Rewrite.

This is a clean negative result that supports the paper's
"Reset is sufficient" framing: the flexibility of Rewrite is not free
— it introduces interpretive variance that hurts task-spec-preserving
benchmarks.

## Possible v3 (deferred)

If we wanted another iteration, the obvious moves are:

- **Anchor each spec item on a quoted user message**: forbid spec
  items not directly traceable to user text. Direct counter to F4.
- **Forbid prose speculation in verified_work** ("the next step is…",
  "the answer would be…"). Counter to F3.
- **Append the latest user message verbatim** as the final spec item.
- **Conditional firing only**: only rewrite when the analyzer flagged
  non-trivial `issues` — i.e., a gate. This is the natural extension
  of the Gated-Reset idea to Rewrite.

But the per-task pattern above suggests these moves would help on
some axes and hurt on others — the same trade-off as v2. Reset
sidesteps the trade-off entirely.
