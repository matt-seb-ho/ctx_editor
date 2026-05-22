# R4 Resume Document — Rewrite-on-LiC (sessions r2 + r2b)

> ⚠️ **Caveat — Rewrite numbers pre-analyzer-parity (2026-05-21)**: any AC3-Rewrite result in this doc was computed with `AC3RewriteStrategy._run_analysis` using the bespoke `compaction_analysis.txt` prompt — **not** the shared `ConversationAnalyzer + v8` used by Augment / Reset / Gated-Reset. Some unknown fraction of the Rewrite-vs-Reset gap is attributable to analyzer divergence rather than the rewriter step. Augment / Reset / Gated-Reset numbers in this doc are unaffected. See [`docs/analyzer_parity_finding.md`](../analyzer_parity_finding.md) for the smoking gun and [`docs/post_may18_r5_analyzer_parity_plan.md`](../post_may18_r5_analyzer_parity_plan.md) for the re-run plan.


**Purpose**: hand-off from the in-flight rewrite-optimization session
that's running long. Pick this up to continue exploring whether
Rewrite can be made competitive with Reset on LiC.

## Session summary (chronological)

**r2** (started 2026-05-20 22:53, branched into r2b later) and
**r2b** (current) were focused on making Rewrite work on LiC after
R3 found the rewriter-LLM hallucinates content in ~63% of failures
and that hand-iterated v2/v3/v4 prompts all regress vs Baseline.

### What we tried this session

1. **Sanity check** ✅ — confirmed the system prompt is preserved
   after `trace.reset_conversation` in v1/v3/v4 traces. The
   compacted-conversation message sits between the system prompt and
   the last user message; no bug in the message-sequence reconstruction.
2. **v5 Reset-like** (hand-crafted) — prompt explicitly mimics Reset's
   templated output, analyzer-only input (no conversation). Result:
   **net flat vs v1** (−0.8pp vs Baseline; v1 was −0.3pp). v5 succeeded
   at suppressing rewriter-side hallucination but failed because **the
   rewrite-specific analyzer (`compaction_analysis.txt`) is itself a
   different and weaker analyzer than Reset's `ConversationAnalyzer
   v8`** — v5 faithfully relayed worse upstream content. Documented
   in `docs/reports/post_may18_r4_summary.md`.
3. **Combee paper** read + skipped — solves aggregator overload under
   high parallelism; our bottleneck is per-candidate eval latency.
   Notes: `docs/notes/literature/combee_notes.md`.
4. **GEPA optimization** — wired GEPA `optimize_anything` to a 12-problem
   math-conv0 mini-eval, DeepSeek-V4-Flash as both task LM and
   reflection LM, 30 metric calls (~45 min wall). Best candidate
   (v6) hit 0.75 on the mini-eval (seed = v1 at 0.5).
5. **v6 (GEPA winner) full LiC validation** — **+5.6pp vs Baseline
   on avg, the first Rewrite variant to clearly beat Baseline.**
   Per-task: math +4.2pp, code +10.6pp, database +4.8pp, actions +2.7pp
   vs Baseline. Still −11.6pp behind Reset. Code is the standout
   (+16.8pp vs v1).

### Key markdown files

| File | What |
|---|---|
| `docs/reports/post_may18_r4_summary.md` | Full R4 writeup |
| `docs/reports/post_may18_r3_summary.md` | Prior batch (R3) — rewriter-hallucination diagnosis + v2/v3/v4 |
| `docs/reports/post_neurips_r2_summary.md` | R2 (CollabLLM user-sim swap; WildChat cross-model) |
| `docs/reports/post_neurips_ac3_summary.md` | Phase 1+2 (baseline AC3 results) |
| `docs/reports/post_may18_r4_rewrite_examples.md` | Side-by-side examples of Rewrite failure cases |
| `docs/notes/literature/gepa_notes.md` | GEPA notes + integration plan |
| `docs/notes/literature/combee_notes.md` | Combee notes; skipped for our use case |
| `docs/notes/literature/textgrad_notes.md` | TextGrad notes; subsumed by GEPA |
| `docs/notes/literature/tau2_replay_scoping.md` | tau2 replay-mode feasibility (deferred ~2 dev-days) |
| `docs/post_may18_r3_followups.md` | R3 follow-up backlog |
| `scripts/analysis_rewrite_v_reset/data/rewrite_versions_compared.md` | All Rewrite versions × {math, code, db, actions} table |
| `scripts/analysis_rewrite_v_reset/data/diagnosis_summary.md` | R3 LLM-driven attribution (63% rewriter hallucination) |

### Code + artifacts

- **GEPA evaluator + runner**: `scripts/gepa_rewrite/{evaluator.py, run_gepa.py}`
- **GEPA run artifacts**: `outputs/_gepa_rewrite_runs/gepa_run_1779400412/`
  (eval_log.jsonl, candidate_tree.html, best_candidate.txt)
- **v5 prompt**: `src/ctx_editor/strategies/prompts/context_compaction_v5_resetlike.txt`
- **v6 prompt (GEPA winner)**: `src/ctx_editor/strategies/prompts/context_compaction_v6_gepa.txt`
- **v5/v6 experiment configs**: `src/ctx_editor/config/experiment/ac3_rewrite_v{5_resetlike,6_gepa}_lic.yaml`
- **v5/v6 LiC run outputs**: `outputs/post_may18_r4_rewrite_v{5,6}/`

### Current scoreboard (LiC, DeepSeek-V4-Flash)

| Variant | math | code | database | actions | avg | Δ Baseline |
|---|---|---|---|---|---|---|
| Baseline | 72.2 | 34.5 | 22.4 | 76.0 | 51.3 | — |
| Reset | 81.9 | 59.3 | 49.0 | 83.3 | 68.4 | **+17.1pp** |
| AO | 86.1 | 60.2 | 45.6 | 86.0 | 69.5 | **+18.2pp** |
| Rewrite-v1 | 73.6 | 28.3 | 27.9 | 74.0 | 51.0 | −0.3pp |
| Rewrite-v2 (R2) | 70.8 | 36.3 | 21.8 | 70.0 | 49.7 | −1.6pp |
| Rewrite-v3-no-conv (R3) | 68.8 | 31.9 | 22.4 | 72.7 | 48.9 | −2.4pp |
| Rewrite-v4-strict (R3) | 66.0 | 33.6 | 21.1 | 64.7 | 46.3 | −5.0pp |
| Rewrite-v5-resetlike (R4) | 69.4 | 35.4 | 25.2 | 72.0 | 50.5 | −0.8pp |
| **Rewrite-v6-GEPA (R4)** | 76.4 | 45.1 | 27.2 | 78.7 | **56.8** | **+5.6pp** |

## Latest user questions + answers (verbatim — these inform next steps)

### Q1. "Can we repeat the analysis to compare v5 reset-like to the actual ac3-reset run? Like why aren't we even close to this? How are the new context different?"

**Short answer**: v5 and Reset are routed through **different upstream
analyzers**. v5 inherits a *different and weaker analyzer* than
Reset, so even when v5 faithfully relays its analyzer's output, the
content it's relaying is already wrong.

I pulled 11 cases on math conv0 where Reset succeeded and v5 failed.
The most diagnostic is `sharded-GSM8K/2` (Josh's house flip):

- **Reset's analyzer** (`ConversationAnalyzer` with `analyzer_v8`
  prompts) parses "improved the house's value by 150%" correctly:
  > *"...the value increased by 150% of the original purchase price,
  > or the new value is 250% of the original purchase price"*
  
  → produces an `issues` field flagging the assistant's prior wrong
  computation and pointing at the correct interpretation. Reset's
  templated context surfaces both the spec and the issue. Assistant
  recomputes → answer 70000. ✓

- **v5's analyzer** (`compaction_analysis.txt`, the rewrite-specific
  one) parses the same "150%" wrong:
  > *"The house's value was improved by 150% (interpreted as the
  > selling price being the total cost plus 150% of the total cost)"*

  → produces an `aligned` field that claims the assistant's wrong
  computation ($325,000 selling price → $195,000 profit) is *correct*.
  v5 dutifully relays this in "What Looks Right". Assistant copies
  the wrong number → answer 195000. ✗

The v5 design ("be a strict relay of analyzer output") works as
intended — but **the upstream rewrite-analyzer has different and
worse prompts than Reset's analyzer.** v5 can never beat Reset
because it's downstream of a worse signal.

Implications:
- v5 is essentially "Reset using the wrong analyzer". Not surprising
  it under-performs.
- If we want a fair LLM-rewrite comparison, the analyzer step has to
  be matched. Two ways: (i) wire `AC3RewriteStrategy` to call
  `ConversationAnalyzer` with `analyzer_v8` prompts directly instead
  of its own `compaction_analysis.txt`; (ii) GEPA the
  `compaction_analysis.txt` prompt too, separately from the rewriter.

### Q2. "Is GEPA's v6 inserting a new LLM query that replicates the first stage of our pipeline (consolidate task spec) or is it just adding this consolidate as part of the query for the rewrite as well?"

**Short answer**: not a new LLM call — it folds the "consolidate task
spec from raw user messages" work *into* the existing rewrite query.

Reading the v6 prompt: it still takes the four placeholders
`{analysis_user_intent}`, `{analysis_aligned}`, `{analysis_issues}`,
`{conversation}`. The pipeline still has the same two LLM calls:
analyzer → rewriter.

What changed: the rewriter is now **told to extract the task spec
directly from `{conversation}`'s user messages**, treating
`{analysis_user_intent}` as "for reference only". The
`{analysis_aligned}` is still copied into the work-so-far section.

So in practice the analyzer's `task_spec` output is now wasted
compute (the rewriter ignores it and re-derives spec from raw user
messages); the analyzer's `aligned` output is still load-bearing.

Concretely the rewriter LLM is now doing a small amount of
"consolidate user task spec from conversation" work inside its
single call, on top of its templating job.

### Q3. "How many gepa prompt candidates did you evaluate? What was the initial policy you initialized gepa with? Was it influenced by our idea of replicating reset? I'm kinda upset that gepa converged on what I wanted you to try for v5-reset-like... so I'm curious if you biased it in this direction at all?"

**You are right to be upset. I biased it heavily.**

Facts:
- **Number of evaluations**: 32 logged calls. Budget was set to
  `max_metric_calls=30`. Of those ~32, several are repeat-evaluations
  of the same baseline candidate (GEPA does this for variance
  estimation), so the number of **unique candidate prompts explored
  is ~20-25** — not a lot.
- **Seed candidate**: I seeded with the **v1 prompt** (current
  `context_compaction.txt`), not v5. That part is fine.
- **The bias** is in the `objective` and `background` strings I
  passed to GEPA. From `scripts/gepa_rewrite/run_gepa.py`:

> "The current prompt under-performs Baseline (no editing) and Reset
> (a deterministic template-fill from the same analyzer output). The
> dominant failure mode is the rewriter LLM hallucinating content
> (re-computing numbers, inlining prior code verbatim, adding
> phantom requirements). **Your improved prompt should reduce
> hallucination while still producing a useful compacted message.**"

And the background:

> "Reference: the deterministic Reset baseline produces exactly this
> template: ..."  (shows the Reset template)
> "Reset typically scores ~80-85% on the eval ... **A successful
> prompt will steer the rewriter to be a faithful re-emitter of the
> analyzer's content, not an interpreter.**"

I literally **told GEPA** "be a faithful re-emitter of the analyzer's
content" — which is the v5 design verbatim. GEPA's reflection LM
naturally converged on that frame. Of course it found roughly the
v5 design.

This was a serious framing error on my part. A cleaner experiment
would be:
- Minimal objective: "Optimize this prompt to maximize accuracy on
  the LiC math eval."
- Background: just the four placeholder semantics — no editorial
  about Reset's design or what the right failure mode is.
- Let GEPA explore design space without being told the conclusion.

### Q4. "Was including/excluding the input of the full conversation into this query a toggle that the optimizer could play with to optimize downstream performance or no?"

**No. I forced all four placeholders to always be present.**

From the same `objective` string in `run_gepa.py`:

> "The four placeholder tokens `{analysis_user_intent}`,
> `{analysis_aligned}`, `{analysis_issues}`, `{conversation}` **must
> appear in your prompt** (use Python str.format-style)."

GEPA can rephrase the surrounding instructions but it can't delete a
placeholder. So the "include conversation or not" toggle that I
tested by hand (v3-no-conv vs v1) was not available to GEPA as a
search dimension. GEPA's best prompt does still include
`{conversation}`; whether removing it would help wasn't tested in
this run.

## Implications + recommended next steps

These recommendations follow directly from the four answers above
and replace the "next steps" list in `post_may18_r4_summary.md`.

1. **GEPA round 2 — unbiased framing**. Re-run GEPA with a minimal
   objective ("maximize accuracy on this eval") and no editorial
   about Reset / hallucination / faithful re-emission. Let GEPA
   propose its own theories. Same budget (~30 calls) or higher.
   Most likely to surface novel designs.

2. **GEPA round 3 — placeholder toggles as part of the search**.
   Restructure the prompt so the choice of "include conversation or
   not" is part of the searchable string. E.g., document each
   placeholder and let GEPA's mutations drop or keep them as it
   wishes. Or do a 2×2×2 ablation outside of GEPA: cross product of
   {conv in, conv out} × {analyzer.task_spec in, out} × {analyzer.aligned
   in, out} → 8 prompts to manually probe the design space.

3. **Match Reset's analyzer**. The Q1 finding (different analyzers)
   means apples-to-apples comparison of "Reset's template-fill vs
   LLM rewrite" requires both starting from the same analyzer output.
   Refactor `AC3RewriteStrategy` to consume `ConversationAnalyzer`
   with `analyzer_v8` prompts instead of its own
   `compaction_analysis.txt`. Then re-evaluate v1/v5/v6 — the gap
   should shrink and we'll know how much of the Rewrite deficit is
   "weak analyzer" vs "lossy rewrite step".

4. **GEPA the analyzer prompt**. If (3) reveals the analyzer is a
   big chunk of the gap, run GEPA on `compaction_analysis.txt`
   itself, holding the rewriter fixed (use Reset's templater as the
   evaluator endpoint).

5. **Cross-model validation for v6**. Run v6 on gpt-5.4 + Kimi-K2.6
   on LiC. If v6's gains evaporate on stronger respondents, it's an
   overfit to DeepSeek-V4-Flash; if they hold, v6 is a real
   improvement we can claim.

6. **Multi-task GEPA subset**. Tonight's GEPA evaluator used only
   math conv0 (12 problems). Cross-task subset (3 problems × 4
   tasks) would reduce overfitting risk; ~same wall time per call.

## Operational state (when resuming)

- All R4 work committed: `git log --oneline -3` should show
  `4daafbf results: post-May-18 R4`.
- No long-running jobs in flight.
- `outputs/_gepa_rewrite_runs/gepa_run_1779400412/` has the run
  history if you want to re-inspect GEPA candidates.
- The viewer (`src/ctx_editor/app_conv_viewer.py`) now supports
  AC3-Rewrite log types + `?sample=...` deep-linking + prompt-version
  panel — useful for side-by-side tabs comparing v5/v6/Reset on the
  same sample.

## Open questions for the next session

- Which of the 6 recommended next steps is highest priority? My
  guess: (1) unbiased GEPA + (3) analyzer parity together. Both are
  cheap (~1h each) and (3) tells us if Rewrite is structurally
  doomed vs just analyzer-bottlenecked.
- Do we want to attempt GEPA round 2 *before* implementing the
  analyzer-parity refactor? The unbiased GEPA might be more honest
  but is also more likely to plateau at the same place if the
  analyzer is the real bottleneck.
