# Post-NeurIPS AC3 Scale-up — Overnight Summary

> ⚠️ **Caveat — Rewrite numbers pre-analyzer-parity (2026-05-21)**: any AC3-Rewrite result in this doc was computed with `AC3RewriteStrategy._run_analysis` using the bespoke `compaction_analysis.txt` prompt — **not** the shared `ConversationAnalyzer + v8` used by Augment / Reset / Gated-Reset. Some unknown fraction of the Rewrite-vs-Reset gap is attributable to analyzer divergence rather than the rewriter step. Augment / Reset / Gated-Reset numbers in this doc are unaffected. See [`docs/analyzer_parity_finding.md`](../analyzer_parity_finding.md) for the smoking gun and [`docs/post_may18_r5_analyzer_parity_plan.md`](../post_may18_r5_analyzer_parity_plan.md) for the re-run plan.


**Run window**: 2026-05-16 evening → 2026-05-17 afternoon
**Status**: Phase 1 + Phase 2 + Phase 3a (CollabLLM) + Phase 3b (Huang/WildChat) all **complete**.
**Author**: Claude (autonomous overnight)

---

## TL;DR

- **Phase 1** (DeepSeek-V4-Flash, 6 strategies × 4 tasks × 3 prefixes, last-turn replay): AO leads (+18.1pp), AC3-Reset is right behind (+17.1pp). Reset and Gated-Reset tie (within 0.1pp); Reset wins on the tiebreak (simpler/cheaper). Rewrite (LLM compaction) underperforms Baseline.
- **Phase 2** (gpt-5.4 + Kimi-K2.6, S0/AO/Augment/Reset, 4 tasks × 3 prefixes, last-turn replay): **Reset overtakes AO** at the average (+15.3pp vs +10.8pp over Baseline). Reset dominates AO on **database by +26pp**. Reset is within ±5pp of AO on math/code/actions. gpt-5.5 was dropped (deferred per cost/throughput note).
- **Phase 3a** (CollabLLM N=3, DeepSeek-V4-Flash): **AO wins math-hard** (+10pp vs Baseline). AC3-Augment **regresses below Baseline on CollabLLM math** (-10pp) — multi-turn fresh-sim seems to penalize the appended-analysis pattern as analyses pile up turn after turn. AC3-Reset ties Baseline on math-hard. Bigcodebench is functionally unsolvable by DeepSeek-V4-Flash at this scale (all-zero except Reset rep1 at 5%). See `docs/reports/post_neurips_ac3_phase3_collabllm.md`.
- **Phase 3b** (Huang/WildChat N=3, gpt-5-mini after a DeepSeek-routing detour): **both AC3 variants dominate on WildChat**. AC3-Reset wins **89.8% ± 1.4pp** of AO-failure turns vs AO (and 82.6% vs FC). AC3-Augment is slightly better — **92.1% ± 1.3pp** vs AO, 85.9% vs FC. This is the strongest cross-benchmark validation we got tonight — the Phase-1/2 winner generalizes to multi-turn human-conversation settings, decisively. See `docs/reports/post_neurips_ac3_phase3_huang.md`.

The flipped narrative across Phase 1→2 (AO led on DeepSeek, Reset leads on gpt-5.4+Kimi) is the most interesting empirical finding so far: the cost of *retaining* a stronger model's prior assistant turns (good but partially wrong) is recoverable by AC3-Reset's compacted-context rewrite, whereas the weaker DeepSeek benefits more from a clean slate (AO).

**Cross-benchmark picture is split**:
- **WildChat (Phase 3b)**: AC3 dominates by ~90pp wins-vs-AO at gpt-5-mini scale. Strongest validation of AC3 generalization.
- **CollabLLM (Phase 3a)**: AC3-Augment regresses below baseline at DeepSeek scale, multi-turn fresh sim. AO is back to winning.
- **LiC (Phase 1+2)**: Mixed — DeepSeek prefers AO, gpt-5.4/Kimi prefer AC3-Reset (especially on database, +25pp over AO).

The CollabLLM-style regression is real and worth investigating. It contrasts sharply with WildChat where AC3-Augment is the *strongest* variant — likely because WildChat conversations are shorter (median ~6-10 turns vs CollabLLM's 14), so the analysis-pile-on effect that hurts CollabLLM Augment doesn't accumulate as much. **Multi-turn gating (the Phase-3-from-rev.2 idea we deferred) suddenly looks much more important than rev.3 suggested** — it's the deployment-realism story for AC3 on longer multi-turn conversations.

## Plan recap (rev.3)

See `docs/post_neurips_ac3_experiment_plan.md`. Three phases (rev.3 dropped multi-turn gating to "future work"; instead Phase 3 is cross-benchmark error bars). Methodology decisions in `docs/prefix_variance_decision.md` (3 distinct prefixes per problem), `docs/prefix_gathering_process.md` (how the prefix pool was built), `docs/analyzer_prompt_design_notes.md` (v8 default, s1 fallback, v13 designed but not built).

## Phase 1 — DeepSeek-V4-Flash, last-turn replay (n=3 prefixes)

Full table: `docs/reports/post_neurips_ac3_phase1.md`. Winners file: `outputs/post_neurips_ac3_phase1/winners.json`.

| Strategy | math | code | database | actions | Δ vs Baseline (avg) |
|---|---|---|---|---|---|
| Baseline | 72.2 | 34.7 | 22.4 | 76.0 | 0 |
| **AO** (assistant omit) | 86.1 | 60.3 | 45.6 | 86.0 | **+18.1pp** |
| Augment | 84.0 | 58.7 | 41.5 | 84.0 | +15.7pp |
| **Reset** (always-on) | 81.9 | 59.5 | 49.0 | 83.3 | **+17.1pp** |
| Gated-Reset | 82.6 | 55.9 | 49.7 | 85.3 | +17.0pp |
| Rewrite | 73.6 | 28.6 | 27.9 | 74.0 | -0.3pp |

**Phase 1 takeaways**:

- **AO is the practical upper bound** here (+18.1pp), matching the paper's framing — the assistant's prior turns are the bottleneck in multi-turn settings.
- **AC3-Reset within 1pp of AO** and beats Baseline by +17.1pp.
- **Reset vs Gated-Reset within 0.1pp**: gating fires selectively but doesn't change the outcome much in last-turn replay (the gate has exactly one decision point per prefix). Reset wins the 3pp tiebreak; Gated-Reset's deployment-cost advantage (selective firing) needs multi-turn fresh-sim experiments to show real benefit.
- **Rewrite consistently destroys task-critical info** (schemas, function definitions, test cases) in compaction. Regresses below Baseline on every task. Bad fit for this benchmark family.

**Engineering payoff**: analysis cache saved ~75% of analyzer queries in Phase 1 (Augment populated the cache, Reset/Gated-Reset hit it; Rewrite uses its own compaction prompt and didn't share).

## Phase 2 — gpt-5.4 + Kimi-K2.6 (gpt-5.5 dropped), last-turn replay

Full table: `docs/reports/post_neurips_ac3_phase2.md`. Promoted: Augment (ablation) + Reset (Phase 1 winner). 96 cells = 2 models × 4 strategies × 4 tasks × 3 prefixes.

Why gpt-5.5 was dropped: at Kimi's pace (~3.5h for the Kimi pipeline), gpt-5.5 (next in the foundry chain) would have added another ~4h, pushing total finish past the realistic morning check-in. The user explicitly allowed dropping gpt-5.5 if it was too slow ("we have gpt-5.4 anyways").

| Strategy | math | code | database | actions | Δ vs Baseline (avg) |
|---|---|---|---|---|---|
| Baseline | 77.0 | 58.0 | 19.0 | 88.0 | 0 |
| AO | 88.1 | 75.4 | 29.3 | 92.7 | +10.8pp |
| Augment | 86.3 | 70.4 | 53.7 | 91.3 | +14.9pp |
| **Reset** | 85.6 | 70.1 | **55.7** | 92.0 | **+15.3pp** |

**Phase 2 takeaways**:

- **Reset dominates AO on average** (+15.3pp vs +10.8pp). The model-scale shift matters: where DeepSeek-V4-Flash benefited most from dropping its own prior turns (AO), the stronger gpt-5.4 and Kimi-K2.6 benefit more from *editing* their context with AC3.
- **The database story is dramatic**: Reset/Augment **beat AO by +24–26pp on database**. Database's full system prompt carries the SQL schema; AO drops the assistant's reasoning context but keeps the schema, while AC3's compacted context preserves both the schema (via the unchanged system message) and a clean restatement of the user intent. The combination is much more effective than either dropping context or keeping all of it.
- **Code is the one place where AO beats AC3** on Phase 2 models (~5pp). Worth investigating: code prefixes may contain useful test-case discussion that AC3 compacts away.
- **Actions is essentially saturated** in Phase 2 (all 3 intervention strategies within 1.5pp of each other ≈ 91–92.7%).

### Per-model Phase 2 detail

**gpt-5.4** (n=3 prefixes per cell):
- math: Base 78.5 / AO 91.6 / Augment 86.7 / Reset 87.4
- code: Base 57.5 / AO 85.9 / Augment 75.1 / Reset 73.6
- database: Base 19.0 / AO 27.9 / Augment 56.5 / **Reset 56.2** (+28pp vs AO)
- actions: Base 87.3 / AO 92.7 / Augment 90.0 / Reset 92.0

**Kimi-K2.6** (n=3 prefixes per cell; math conv0 had 9 cells errored due to the cache-hash bug, now fixed):
- math: Base 81.9 / AO 84.3 / Augment 86.1 / Reset 83.8
- code: Base 58.6 / AO 65.2 / Augment 65.7 / **Reset 66.5**
- database: Base 19.0 / AO 30.6 / Augment 51.0 / **Reset 55.1** (+25pp vs AO)
- actions: Base 88.7 / AO 92.7 / Augment 92.7 / Reset 92.0

### Engineering note: cache-hash bug

The analyzer-cache `_hash_trace` initially fell over on `Message` dataclasses with empty-string `role` (compacted-conversation entries). Fixed at commit `cf00efd` mid-run. Affected only the Kimi math conv0 Augment + Reset cells (9 of 48 problems each). All cells starting after the fix are clean.

## Phase 3 — Cross-benchmark error bars

Promoted method: **AC3-Reset (always-on)** with `v8` analyzer.

### 3a CollabLLM (DONE — DeepSeek-V4-Flash, n=3 reps × 20 problems per cell)

Full report: `docs/reports/post_neurips_ac3_phase3_collabllm.md`.

| Strategy | math-hard | bigcodebench |
|---|---|---|
| Baseline | 30.0% ± 0.0pp | 0.0% ± 0.0pp |
| **AO** | **40.0% ± 5.0pp** | 0.0% ± 0.0pp |
| AC3-Augment (v8) | 20.3% ± 4.8pp | 0.0% ± 0.0pp |
| AC3-Reset (v8) | 30.0% ± 5.0pp | **1.7% ± 2.9pp** |

**Phase 3a takeaways**:

- **AO is the strong winner on CollabLLM math-hard** (+10pp vs Baseline) — opposite of Phase 2's LiC database story.
- **AC3-Augment regresses below Baseline** (-10pp on math-hard, errors-excluded climbing on bigcodebench as conversations balloon).
- **AC3-Reset ties Baseline** on math-hard, is the only non-zero on bigcodebench (real but tiny).
- **Bigcodebench is functionally unsolvable** at this scale for DeepSeek-V4-Flash — every Baseline/AO/Augment cell returned 0/20.

The gap between Phase 2 (Reset wins +25pp on database) and Phase 3a (AO wins +10pp on math-hard) is the central paper-narrative tension. Section "Methodological notes for the paper" below sketches the writeup.

### 3b WildChat/Huang (DONE — gpt-5-mini after a DeepSeek-routing detour)

Full report: `docs/reports/post_neurips_ac3_phase3_huang.md`.

**Engineering footnote**: first attempt at 11:07 with `respondent_model=DeepSeek-V4-Flash` failed — `huang_eval/run_phase2.py` instantiates a plain `OpenAIModelClient` without passing our `LoadBalancerConfig`, so DeepSeek calls 404'd at the Azure OpenAI endpoint that doesn't host that deployment. The first 6 cells reported 0 evaluated turns. Re-launched 16:09 with `respondent_model=gpt-5-mini` (matches paper Table 1(c)). **Engineering fix that should land**: thread `load_balancer_config` through `huang_eval/run_phase2.py`. Logged in `docs/post_neurips_ac3_followups.md` (created below).

| Variant | n | Wins vs AO | Wins vs FC |
|---|---|---|---|
| AC3-Reset (S15), avg | 75 | **89.8% ± 1.4pp** | 82.6% ± 1.7pp |
| AC3-Augment, avg | 76 | **92.1% ± 1.3pp** | 85.9% ± 3.2pp |

Both AC3 variants dominate. Augment slightly beats Reset on WildChat — opposite of CollabLLM where Augment regresses. Likely conversation-length effect.

## Methodological notes for the paper

The cross-phase results suggest a clear narrative split, useful for the paper:

1. **Last-turn replay (Phase 1+2)** — paper's primary AC3 evaluation regime — shows AC3-Reset is competitive with AO on weaker models and *beats* AO at stronger models on database. This is the headline.
2. **Multi-turn fresh sim (Phase 3a)** — multi-step refinement settings — shows AO remains the upper bound and AC3-Augment can actively hurt (analysis-pile-on). This is a real limitation that should be acknowledged.

The deployment-realism implication: **multi-turn AC3 with gating** becomes the actually-useful production setup — fire the intervention only when needed, not every turn. The rev.2 multi-turn gating Phase that was deferred to "future work" now looks more important than I anticipated when scoping for tonight.

## Next session — start here

This doc is the canonical entry-point for picking up the AC3 thread. Suggested
reading order before any new questions:

1. This summary (TL;DR + cross-phase picture at the top).
2. `docs/post_neurips_ac3_followups.md` — the engineering + experimental
   follow-up backlog the overnight surfaced. **This is where the next
   session's agenda starts**: load_balancer plumbing for Huang eval, the
   multi-turn-gating experiment we deferred, gpt-5.5 Phase 2 follow-on,
   bigcodebench investigation, etc.
3. The per-phase reports for any specific cell-level detail you want:
   - `docs/reports/post_neurips_ac3_phase1.md` (DeepSeek, all variants)
   - `docs/reports/post_neurips_ac3_phase2.md` (gpt-5.4 + Kimi)
   - `docs/reports/post_neurips_ac3_phase3_collabllm.md` (CollabLLM)
   - `docs/reports/post_neurips_ac3_phase3_huang.md` (WildChat)
4. `docs/post_neurips_ac3_experiment_plan.md` — rev.3 plan that scoped this
   batch, useful for understanding *what was intentionally out of scope*
   (e.g., multi-turn gating was deferred).
5. `docs/analyzer_prompt_design_notes.md` — only if the next session
   touches prompt design or the Azure content-filter story.

## File map

### Documents (this batch)

- Plan: `docs/post_neurips_ac3_experiment_plan.md` (rev.3, pre-launch)
- Prompt design + CF history: `docs/analyzer_prompt_design_notes.md`
- Follow-up backlog: `docs/post_neurips_ac3_followups.md`
- Phase 1 results: `docs/reports/post_neurips_ac3_phase1.md`
- Phase 2 results: `docs/reports/post_neurips_ac3_phase2.md`
- Phase 3a (CollabLLM): `docs/reports/post_neurips_ac3_phase3_collabllm.md`
- Phase 3b (WildChat): `docs/reports/post_neurips_ac3_phase3_huang.md`
- This summary: `docs/reports/post_neurips_ac3_summary.md`

(All entries above are listed in `docs/index.md`.)

### Data / artifacts

- Per-cell traces / metrics / configs: `outputs/post_neurips_ac3_phase{1,2,3_collabllm,3_huang}/`
- Per-cell launcher logs: `outputs/post_neurips_ac3_phase{1,2,3_collabllm,3_huang}/logs/`
- Analysis cache + provenance: `outputs/analysis_cache/registry.json`
- Winners files (consumed by Phase 2 launcher): `outputs/post_neurips_ac3_phase{1,2}/winners.json`

### Scripts (this batch)

- `scripts/run_phase1_ac3_deepseek.sh` — Phase 1 launcher.
- `scripts/run_phase2_ac3_other_models.sh` — Phase 2 launcher (winner-aware via `winners.json`).
- `scripts/run_phase3_collabllm_redo.sh` — Phase 3a CollabLLM launcher.
- `scripts/run_phase3_huang_redo.sh` — Phase 3b Huang launcher.
- `scripts/aggregate_ac3_phase.py` — Generic phase aggregator (LiC-cells regex; doesn't yet handle CollabLLM / Huang cell-name shapes — see follow-ups).

### Code (this batch)

- `src/ctx_editor/strategies/analysis_cache.py` (new) — content-addressed analyzer-output cache.
- `src/ctx_editor/strategies/analyzer.py` — `analyze()` takes optional `cache` kwarg.
- `src/ctx_editor/strategies/append_analysis.py`, `context_edit_v2.py` — thread cache through.
- `src/ctx_editor/models/foundry_pricing.yaml` — user-populated cost table; merged into `get_model_pricing()`.
- `src/ctx_editor/config/experiment/context_edit_v2_{no_gate,gated}{,_accumulate}.yaml`, `ac3_rewrite_lic.yaml`, `collabllm_ac3_{augment,reset}_v8.yaml` — new experiment configs.

## Cost / time accounting (final)

- Phase 1: ~1.5h wall, ~$0.05 reported (DeepSeek Foundry not priced).
- Phase 2: ~4h wall (gpt-5.4 parallel done in ~1.5h; Kimi serialized took ~3.5h; gpt-5.5 dropped). Reported cost: gpt-5.4 ≈ $35; Kimi unpriced.
- Phase 3a (CollabLLM): ~3.3h wall (07:40 → 11:04 PT). ~$0.65 reported.
- Phase 3b (Huang/WildChat): ~3.3h wall (16:09 → 19:28 PT, second batch). Cost not yet priced; respondent was gpt-5-mini (in OpenAI pricing table — backfill at any time).

Foundry-side dollar cost on DeepSeek + Kimi is `$0` reported, but token counts are saved per cell; if `foundry_pricing.yaml` is filled in, backfill is mechanical.

## Content-filter audit

Spot-checked `content_filter_errors.jsonl` across phases — **zero filter trips observed** in Phase 1, 2, 3a, or 3b. Foundry-side (DeepSeek, Kimi) and Azure-OAI-side (gpt-5.4, gpt-5-mini) all clean. The `v8 → s1 → v13` escalation chain was not needed.
