# Post-May-18 R4 — get Rewrite working on LiC

> ⚠️ **Caveat — Rewrite numbers pre-analyzer-parity (2026-05-21)**: any AC3-Rewrite result in this doc was computed with `AC3RewriteStrategy._run_analysis` using the bespoke `compaction_analysis.txt` prompt — **not** the shared `ConversationAnalyzer + v8` used by Augment / Reset / Gated-Reset. Some unknown fraction of the Rewrite-vs-Reset gap is attributable to analyzer divergence rather than the rewriter step. Augment / Reset / Gated-Reset numbers in this doc are unaffected. See [`docs/analyzer_parity_finding.md`](../analyzer_parity_finding.md) for the smoking gun and [`docs/post_may18_r5_analyzer_parity_plan.md`](../post_may18_r5_analyzer_parity_plan.md) for the re-run plan.


**Run window**: 2026-05-21 (start TBD) → (in progress)
**Prior batches**: R3 (`post_may18_r3_summary.md`) found rewriter-LLM
hallucination = 63% of failures; v2/v3/v4 prompts all net-negative.

**This batch's two ideas**:

1. **v5 Reset-like**: explicitly nudge the rewriter to behave like
   AC3-Reset's template-fill, with analyzer-only input (no
   conversation). Existence proof that *some* template→context
   transformation works (Reset). See if LLM can emulate that with
   minor polish.
2. **GEPA optimization** for the rewrite prompt. If GEPA is too slow,
   look into Combee for parallelization (arxiv 2604.04247).

## Workhorse + conventions

- DeepSeek-V4-Flash as the task LM and evaluator-LLM.
- Notes for any papers/blogs go under `docs/notes/literature/`.
- Run commands, output paths, scores, takeaways logged here.

## Phase 0 — Sanity check: system prompt preserved post-rewrite

**Verdict**: ✅ confirmed across `ac3_rewrite_lic` (v1),
`ac3_rewrite_v3_no_conv_lic`, and `ac3_rewrite_v4_strict_lic`. After
`trace.reset_conversation(...)`, the new visible message sequence is
always `[system, compacted conversation, last_user, ...]`. The
original system prompt content is re-injected verbatim (verified by
content length match pre- vs post-reset).

The code path responsible: `context_compaction.py` lines 157-162
explicitly copies the system message into the new message list before
appending the compacted-conversation message. The assistant sees the
full system prompt + compacted context + last user message.

No bug here. Whatever's wrong with Rewrite isn't a missing system
prompt.

## Phase 1 — v5 Reset-like Rewrite

**Prompt**: `src/ctx_editor/strategies/prompts/context_compaction_v5_resetlike.txt`.
**Config**: `src/ctx_editor/config/experiment/ac3_rewrite_v5_resetlike_lic.yaml`.
**Launcher**: `scripts/run_post_may18_r4_rewrite_v5.sh` (12 cells, throttled).
**Output**: `outputs/post_may18_r4_rewrite_v5/`.

Design: ONLY the analyzer's `task_spec` + `aligned` go into the rewriter
prompt (no conversation, no issues, matching v3_no_conv). The prompt
shows the rewriter the literal Reset template format and asks it to
"complete the template" with minor copy-edit polish. Forbid adding new
constraints, removing constraints, recomputing numbers, inlining code.

Result (12 cells, DeepSeek-V4-Flash):

| Task | v1 | v2 | v3-no-conv | v4-strict | **v5-resetlike** | Reset | Baseline |
|---|---|---|---|---|---|---|---|
| math | 73.6 | 70.8 | 68.8 | 66.0 | **69.4** | 81.9 | 72.2 |
| code | 28.3 | 36.3 | 31.9 | 33.6 | **35.4** | 59.3 | 34.5 |
| database | 27.9 | 21.8 | 22.4 | 21.1 | **25.2** | 49.0 | 22.4 |
| actions | 74.0 | 70.0 | 72.7 | 64.7 | **72.0** | 83.3 | 76.0 |
| **avg** | 51.0 | 49.7 | 48.9 | 46.3 | **50.5** | 68.4 | 51.3 |
| **Δ vs Baseline** | **−0.3pp** | −1.6pp | −2.4pp | −5.0pp | **−0.8pp** | **+17.1pp** | — |

**Verdict**: v5 is essentially tied with v1 (−0.8pp vs Baseline; v1
was −0.3pp). Small gain on code/database; small loss on math/actions.
Confirms again that hand-crafted prompts can't close the Reset gap.

**Why** (from spot-checking v5 traces): the rewriter LLM continues to
faithfully *copy* interpretive content from the analyzer's `task_spec`
output (e.g., the "(Implicitly, from the last message)" bullet on the
pizza math case). The analyzer itself produces interpretive
content — v5 successfully suppresses rewriter-side hallucination but
inherits analyzer-side interpretation. To close the gap we'd either
need to: (a) swap to the same analyzer Reset uses (`v8`), or (b) post-
process the analyzer output before the rewriter sees it.

## Phase 2 — Combee paper notes

Notes in `docs/notes/literature/combee_notes.md`. Verdict: **skip
Combee for our rewrite-prompt GEPA run**. Combee solves
*aggregator context-overload under high parallelism in iterative
prompt-evolution loops* — our setup has 1 reflection per evaluation,
nowhere near the overload regime. Our actual bottleneck is per-candidate
evaluation latency, which GEPA's built-in `num_threads` parallelism
addresses directly.

## Phase 3 — GEPA optimizer for rewrite

### Setup

- **Evaluator** (`scripts/gepa_rewrite/evaluator.py`): one call = run
  ctx-editor on a fixed 12-problem subset (math conv0, limit=12,
  DeepSeek-V4-Flash, throttled MC=4). Returns `(accuracy, side_info)`
  where side_info includes failure samples + run dir for the
  reflection LM.
- **Reflection LM**: DeepSeek-V4-Flash via our load balancer, wrapped
  as a sync `LanguageModel` callable (own asyncio event loop on a
  dedicated thread; thread-safe).
- **Seed candidate**: the current v1 prompt
  (`context_compaction.txt`).
- **Config**: `GEPAConfig(EngineConfig(max_metric_calls=30,
  parallel=False))`. Serial because the evaluator already shells out
  to ctx-editor which is multi-process internally.
- **Run**: `scripts/gepa_rewrite/run_gepa.py --budget 30`.
- **Smoke**: budget=3 ran end-to-end in 263s ✓.
- **Main run output**:
  `outputs/_gepa_rewrite_runs/gepa_run_1779400412/`.

### Result

- 32 evaluations in **45 min** (88s/call mean).
- Seed score: **0.500** (6/12 correct on the mini-eval).
- Best candidate (idx=3): **0.750** (9/12 correct) — **+25pp** on the
  mini-eval.
- Best prompt promoted to
  `src/ctx_editor/strategies/prompts/context_compaction_v6_gepa.txt`.

### Best prompt strategy (paraphrase)

The GEPA-evolved prompt is **even more aggressive** than v4-strict
at preventing the rewriter from interpreting. Key clauses:

- *"You must NOT compute, calculate, recalculate, or verify any
  numerical values, formulas, or code from the conversation."*
- *"Copy numbers, formulas, and code exactly as they appear in the
  user's messages."*
- *"If the conversation contains multiple user messages, concatenate
  them in order, preserving exact wording. Do not summarize."*
- For Section 2 (Work Completed): *"Copy the 'What the Assistant Got
  Right' section from the reviewer's notes EXACTLY, word-for-word,
  including all formatting."*

Notably **it diverges from v5** by telling the rewriter to extract
the task spec **directly from the user's messages in the
conversation**, not from the analyzer's potentially-paraphrased
`task_spec`. This neatly side-steps the analyzer-interpretation
problem v5 inherited.

### Full LiC validation

Launcher: `scripts/run_post_may18_r4_rewrite_v6.sh`. 12 cells
(DeepSeek-V4-Flash, last-turn replay, htn50_52). All done in
~10 min wall (throttled MC=4, 4 parallel cells).

| Task | v1 | v5 | **v6-GEPA** | Reset | Baseline |
|---|---|---|---|---|---|
| math | 73.6 | 69.4 | **76.4** | 81.9 | 72.2 |
| code | 28.3 | 35.4 | **45.1** | 59.3 | 34.5 |
| database | 27.9 | 25.2 | **27.2** | 49.0 | 22.4 |
| actions | 74.0 | 72.0 | **78.7** | 83.3 | 76.0 |
| **avg** | 51.0 | 50.5 | **56.8** | 68.4 | 51.3 |
| **Δ vs Baseline** | −0.3pp | −0.8pp | **+5.6pp** | +17.1pp | — |

**v6-GEPA is the first Rewrite variant in any of our overnight
batches to materially beat Baseline.** It also closes ~35% of the
v1-vs-Reset gap (Δ to Reset: was −17.4pp with v1, now −11.6pp with
v6).

Per-task wins vs v1:

- code: **+16.8pp** (the standout — from 28.3% to 45.1%)
- actions: +4.7pp
- math: +2.8pp
- database: −0.7pp (essentially tied)

The code win is interesting because earlier hand-iterated v2/v5 had
already shown a small code gain. GEPA found a much stronger code-
specific lift. The prompt's "concatenate user messages in order,
preserving exact wording" instruction is particularly well-suited to
LiC's code task, where the user often dictates exact function
signatures and return shapes that v1 routinely paraphrased away.

### Why GEPA worked where hand-iteration didn't

Hand prompts (v2/v3/v4/v5) all attacked the same axis — *constrain
the rewriter from interpreting*. The GEPA prompt added a different
angle: **extract the task spec from the user's conversation
messages directly**, bypassing the analyzer's possibly-paraphrased
`task_spec` field. v5 tried something similar (analyzer-only input,
no conversation) but routed the spec *through* the interpretive
analyzer; v6-GEPA points the rewriter back at the raw user words.

This is the key insight v5 missed: the analyzer is itself a source of
interpretation. v6 inherits the conversation in the rewrite prompt
input (unlike v3/v4/v5 which removed it) AND tells the rewriter to
prefer user words over analyzer paraphrase.

### Cost / time

- GEPA optimization (30 metric calls): **45 min**, ~$0.30 reported
  cost (DeepSeek-V4-Flash for both rewriter and reflection LM,
  via foundry). Tractable for an overnight follow-up loop.
- v6 full LiC validation (12 cells): ~10 min, throttled.

## TL;DR

| Question | Answer |
|---|---|
| System prompt preserved post-rewrite? | ✅ yes, verified across v1/v3/v4 traces |
| Can a "Reset-like LLM" prompt match Reset? | No — v5 ≈ v1, neither beats Baseline meaningfully |
| Does Combee help us? | No — wrong tool for our latency profile; notes in `docs/notes/literature/combee_notes.md` |
| Does GEPA help? | **Yes — v6 is +5.6pp vs Baseline, first time any Rewrite variant clears Baseline; closes 35% of the gap to Reset** |
| Can Rewrite beat Reset on LiC? | Not yet; v6 is −11.6pp behind Reset. Further GEPA iterations or better evaluators (multi-task subset, more budget) could close more. |

## Decisions log

- **Skip Combee implementation**: notes-only. Combee's bottleneck
  (aggregator context overload under high parallelism) doesn't match
  ours (per-candidate evaluation latency). GEPA's built-in
  `max_workers` parallelism is the right knob.
- **GEPA eval subset = math conv0 limit=12**: cheapest signal. ~88s
  per call. Math is where Rewrite has the closest gap to Reset so
  any prompt improvement should be detectable. Could broaden to
  cross-task subset for v7 if we want.
- **GEPA budget = 30**: rough first pass. Score converged
  (saw 0.75 twice in iterations 22-30). Marginal returns likely;
  more budget might help but not 5x more.
- **v6 promoted to a stable name** (`context_compaction_v6_gepa.txt`
  + `ac3_rewrite_v6_gepa_lic.yaml`) so future runs can reference it.

## Next steps (for follow-up overnight)

1. **GEPA round 2 with multi-task subset** (4 tasks × 3 problems
   each = 12). Avoids over-fitting to math.
2. **Larger budget GEPA** (~80-100 metric calls) — see if the score
   plateau breaks.
3. **GEPA on the analyzer prompt** too (`compaction_analysis.txt`).
   Tonight only optimized the rewriter; the analyzer is also
   producing interpretive output that bleeds into the rewriter even
   when the rewriter is strict.
4. **Validate v6 cross-model** (gpt-5.4, Kimi-K2.6) — does the
   GEPA-evolved prompt transfer or did we overfit to DeepSeek?

## File map (R4)

- This summary: `docs/reports/post_may18_r4_summary.md`
- Rewrite comparison table:
  `scripts/analysis_rewrite_v_reset/data/rewrite_versions_compared.md`
- Combee notes: `docs/notes/literature/combee_notes.md`
- GEPA notes: `docs/notes/literature/gepa_notes.md`
- v5 prompt + config:
  `src/ctx_editor/strategies/prompts/context_compaction_v5_resetlike.txt`,
  `src/ctx_editor/config/experiment/ac3_rewrite_v5_resetlike_lic.yaml`
- v6 prompt + config (GEPA winner):
  `src/ctx_editor/strategies/prompts/context_compaction_v6_gepa.txt`,
  `src/ctx_editor/config/experiment/ac3_rewrite_v6_gepa_lic.yaml`
- GEPA evaluator + runner:
  `scripts/gepa_rewrite/evaluator.py`,
  `scripts/gepa_rewrite/run_gepa.py`
- GEPA run artifacts:
  `outputs/_gepa_rewrite_runs/gepa_run_1779400412/`
- Run outputs:
  - v5: `outputs/post_may18_r4_rewrite_v5/`
  - v6: `outputs/post_may18_r4_rewrite_v6/`

## Decisions log

_filled in as we go_
