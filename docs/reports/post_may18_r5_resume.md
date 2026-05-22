# R5 Resume Document — start here next session

**Status as of 2026-05-21**: analyzer-parity refactor + caveat
warnings landed. Code is ready for the planned re-runs. No long
experiments in flight.

**Quick context**: the previous session (r2b) found a major
architecture bug — `AC3RewriteStrategy` was using a bespoke
`compaction_analysis.txt` analyzer rather than the shared
`ConversationAnalyzer + v8` that Augment / Reset / Gated-Reset use.
This invalidates the rewriter-only conclusions from Phases 1, R2,
R3, R4. Augment / Reset / Gated-Reset numbers are unaffected.

## What this session did

1. **Diagnosed and documented the analyzer-parity bug.**
   - `docs/analyzer_parity_finding.md` — the smoking gun on
     `sharded-GSM8K/2`, full impact assessment, what's affected and
     what isn't.
   - Added a ⚠ pre-analyzer-parity caveat block to the top of every
     Rewrite-discussing report:
     `post_neurips_ac3_summary.md`,
     `post_neurips_ac3_phase1.md`,
     `post_neurips_r2_summary.md`,
     `post_neurips_r2_rewrite_analysis.md`,
     `post_neurips_r2_rewrite_v2.md`,
     `post_may18_r3_summary.md`,
     `post_may18_r3_rewrite_examples.md`,
     `post_may18_r3_mega_table.md`,
     `post_may18_r4_summary.md`,
     `post_may18_r4_resume.md`.

2. **Refactored `AC3RewriteStrategy`** to use `ConversationAnalyzer`
   + `AnalysisCache` (mirrors what Reset / Augment / Gated-Reset
   already do).
   - File: `src/ctx_editor/strategies/context_compaction.py`.
   - Dropped the bespoke `_run_analysis` method that loaded
     `compaction_analysis.txt`.
   - New constructor params (mirror `AC3ResetStrategy`):
     `analyzer_model`, `analyzer_timeout`, `analyzer_max_tokens`,
     `analyzer_reasoning_effort`, `analyzer_prompt_version` (default
     `"v8"`), `analysis_cache_dir`.
   - Old `analysis_prompt` kwarg is now **deprecated** — passing it
     a non-default value logs a warning and is ignored.
   - Existing rewriter prompts (v1..v6) work unchanged: the same
     four placeholders (`{analysis_user_intent}`,
     `{analysis_aligned}`, `{analysis_issues}`, `{conversation}`)
     are still substituted, just sourced from the v8 analyzer's
     `AnalysisResult` fields instead of the bespoke parser.
   - Smoke test: `experiment=ac3_rewrite_lic
     +experiment.strategy.analyzer_prompt_version=v8` on math conv0
     limit=2 → 2/2 ✓ (pre-refactor: was 1/2 on similar setup).

3. **Updated all rewrite experiment YAML configs** to set
   `analyzer_prompt_version: v8` and
   `analysis_cache_dir: outputs/analysis_cache` so default runs
   automatically use the shared analyzer and hit the 3,311 already-
   cached v8 analyses on disk:
   - `ac3_rewrite_lic.yaml` (v1)
   - `ac3_rewrite_v2_lic.yaml`
   - `ac3_rewrite_v3_no_conv_lic.yaml`
   - `ac3_rewrite_v3_conv_first_lic.yaml`
   - `ac3_rewrite_v4_strict_lic.yaml`
   - `ac3_rewrite_v5_resetlike_lic.yaml`
   - `ac3_rewrite_v6_gepa_lic.yaml`
   - `collabllm_compaction.yaml`

4. **Updated `docs/index.md`** with new entries:
   `analyzer_parity_finding.md`,
   `post_may18_r5_analyzer_parity_plan.md`,
   `post_may18_r4_resume.md`, plus a chronological-log row.

5. **Augment / Reset / Gated-Reset are unaffected.** Grep-confirmed:
   they all import and use `ConversationAnalyzer` directly, and they
   all write/read `AnalysisCache`. Only `context_compaction.py` was
   broken.

## What's preserved on disk for the next session

- **`outputs/analysis_cache/`** — 3,311 cached `v8` analyses
  (DeepSeek-V4-Flash 2257, gpt-5.4 531, Kimi-K2.6 523). The
  refactored Rewrite hits these for free on the `htn50_52` prefix
  set.
- **All prior rewrite output dirs** under
  `outputs/post_neurips_ac3_phase1/`,
  `outputs/post_neurips_r2_rewrite_v2/`,
  `outputs/post_may18_r3_rewrite_v3_v4/`,
  `outputs/post_may18_r4_rewrite_v{5,6}/` — kept as historical
  pre-parity reference. Comparison script
  (`scripts/analysis_rewrite_v_reset/compare_rewrite_versions.py`)
  unchanged; the next session's new outputs will appear as
  additional rows.
- **GEPA run artifacts** at
  `outputs/_gepa_rewrite_runs/gepa_run_1779400412/` (best_candidate.txt,
  eval_log.jsonl, candidate_tree.html).
- **All rewriter prompts** under
  `src/ctx_editor/strategies/prompts/context_compaction*.txt`
  (v1, v2, v3_no_conv, v3_conv_first, v4_strict, v5_resetlike,
  v6_gepa).
- **`compaction_analysis.txt`** (the deprecated bespoke analyzer
  prompt) kept for archival — old traces reference it. It's no
  longer loaded anywhere in code.

## Plan for the next session (from `docs/post_may18_r5_analyzer_parity_plan.md`)

Sign-off questions previously raised remain open. My recommended
order (cheapest first; happy to revise on user direction):

1. **Phase 1 re-run** (~30 min, cache hits):
   - Rewrite v1 + v8 analyzer on full LiC (12 cells, DeepSeek-V4-Flash).
   - Rewrite v3-no-conv + v8 analyzer on full LiC.
   - Compare new numbers to (a) Reset (b) prior pre-parity Rewrite numbers.
   - This tells us how much of the prior Rewrite gap was analyzer vs
     rewriter.

2. **Phase 2 unbiased GEPA round 2** (~75 min):
   - New `objective` / `background` strings drafted in the R5 plan
     doc (no "faithful re-emitter" framing; no Reset reference; no
     editorial about hallucination).
   - `{conversation}` is explicitly OPTIONAL in the prompt template
     contract — GEPA can produce candidates that omit it.
   - Same evaluator (math conv0 mini-eval, 12 problems) for tight
     iteration. Optionally broaden to cross-task mini-eval if math-
     only result looks suspicious.
   - Sign-off needed: include or skip the "remove distracting
     pollution / reorganize previous work for downstream usefulness"
     hint in the background?

3. **Phase 3 winner validation** — full LiC + cross-model probe on
   whatever Phase 2 produces.

4. **Phase 4 (only if rewriter is still bottleneck)** — GEPA the
   analyzer prompt too.

## Operational state

- All work committed: `git log --oneline -3` should show
  `adafc33 plan: R5 analyzer parity refactor + unbiased GEPA round 2`
  and the new R5 refactor commit landing after this session.
- No long-running jobs in flight.
- Refactored code smoke-tested ✓.

## File map (analyzer-parity related)

| File | Role |
|---|---|
| `docs/analyzer_parity_finding.md` | The architecture bug, smoking gun, impact |
| `docs/post_may18_r5_analyzer_parity_plan.md` | Plan + sign-off questions |
| `docs/reports/post_may18_r5_resume.md` (this) | Resume doc for next session |
| `src/ctx_editor/strategies/context_compaction.py` | Refactored AC3RewriteStrategy |
| `src/ctx_editor/strategies/analyzer.py` | Shared `ConversationAnalyzer` (no changes) |
| `src/ctx_editor/strategies/analysis_cache.py` | Shared `AnalysisCache` (no changes) |
| `src/ctx_editor/strategies/prompts/compaction_analysis.txt` | **Deprecated** (kept for archival) |
| `src/ctx_editor/config/experiment/ac3_rewrite*lic.yaml` | All 7 rewrite configs updated with `analyzer_prompt_version: v8` + `analysis_cache_dir` |
| `docs/index.md` | Updated with new entries + chronological-log row |

## Open sign-off questions (for the next session)

(Carried from R5 plan; the user is reviewing these.)

1. OK to proceed with the Phase 1 re-runs as listed?
2. OK with the proposed unbiased GEPA `objective` / `background`
   in `docs/post_may18_r5_analyzer_parity_plan.md`?
3. Include or skip the "remove pollution / reorganize work" hint to
   GEPA? (I lean *skip* — let it discover. User raised this as uncertain.)
4. GEPA mini-eval: math-only (cheap, tight) or cross-task (broader)?
5. Reflection LM: DeepSeek-V4-Flash (status quo) or upgrade to
   gpt-5.4 for ~$1-2 extra?
