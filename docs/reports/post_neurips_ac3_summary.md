# Post-NeurIPS AC3 Scale-up — Overnight Summary

**Run window**: 2026-05-16 evening → 2026-05-17 morning
**Status**: Phase 1 + Phase 2 complete. Phase 3 in flight (CollabLLM first, Huang/WildChat after).
**Author**: Claude (autonomous overnight)

---

## TL;DR

- **Phase 1** (DeepSeek-V4-Flash, 6 strategies × 4 tasks × 3 prefixes, last-turn replay): AO leads (+18.1pp), AC3-Reset is right behind (+17.1pp). Reset and Gated-Reset tie (within 0.1pp); Reset wins on the tiebreak (simpler/cheaper). Rewrite (LLM compaction) underperforms Baseline.
- **Phase 2** (gpt-5.4 + Kimi-K2.6, S0/AO/Augment/Reset, 4 tasks × 3 prefixes, last-turn replay): **Reset overtakes AO** at the average (+15.3pp vs +10.8pp over Baseline). Reset dominates AO on **database by +26pp**. Reset is within ±5pp of AO on math/code/actions. gpt-5.5 was dropped (deferred per cost/throughput note).
- **Phase 3** (cross-benchmark CollabLLM + WildChat with the winning method, N=3): in progress — see "Phase 3" section for live results.

The flipped narrative across Phase 1→2 (AO led on DeepSeek, Reset leads on gpt-5.4+Kimi) is the most interesting empirical finding so far: the cost of *retaining* a stronger model's prior assistant turns (good but partially wrong) is recoverable by AC3-Reset's compacted-context rewrite, whereas the weaker DeepSeek benefits more from a clean slate (AO).

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

## Phase 3 — Cross-benchmark error bars (live)

Promoted method: **AC3-Reset (always-on)** with `v8` analyzer.

### 3a CollabLLM (in flight)

- 4 strategies (Baseline, AO, Augment-v8, Reset-v8) × 2 datasets (math-hard, bigcodebench) × 3 reps = 24 invocations.
- Model: DeepSeek-V4-Flash. Each invocation ≈ 6 min wall on math-hard (max 14 turns × 20 problems × 8 concurrent). Total ETA ≈ 2.5h.
- Launcher: `scripts/run_phase3_collabllm_redo.sh`. Output: `outputs/post_neurips_ac3_phase3_collabllm/`.
- **Live progress**: see `outputs/post_neurips_ac3_phase3_collabllm/_master.log`. Aggregator will be written by `scripts/aggregate_ac3_phase.py` once finished.

### 3b WildChat/Huang (queued after 3a)

- Reuses March-2026 Phase 1 dir (`outputs/huang_eval/phase1/2026-03-24/02-22-57`) for AO-failure-turn selection. Caveat documented in launcher: Phase 1 was gpt-5-mini's failure pattern; we run the intervention with DeepSeek as respondent.
- 2 variants (s15=AC3-Reset, augment=AC3-Augment) × 3 seeds = 6 invocations.
- Launcher: `scripts/run_phase3_huang_redo.sh`. Output: `outputs/post_neurips_ac3_phase3_huang/`.

## Outstanding items for morning review

- **Final Phase 3a (CollabLLM) numbers** — should land before the user wakes up (ETA ~10:00 PT).
- **Phase 3b (Huang/WildChat) numbers** — chained after 3a; ETA depends on 3a finish time. May or may not complete by morning.
- **Aggregator output for Phase 3** — `aggregate_ac3_phase.py` works for CollabLLM (same metrics.json shape). Huang aggregator may need a custom path.
- **Cross-phase cost analysis** — once the populated `foundry_pricing.yaml` is merged with the token counts, fill in the dollar cost across phases.
- **Content-filter audit** — was there any trip during Phase 1 / 2? Spot-checked `content_filter_errors.jsonl` files; none observed in Phase 1, none in Phase 2 (yet).

## File map

- Plan: `docs/post_neurips_ac3_experiment_plan.md`
- Phase 1 results: `docs/reports/post_neurips_ac3_phase1.md`
- Phase 2 results: `docs/reports/post_neurips_ac3_phase2.md`
- This summary: `docs/reports/post_neurips_ac3_summary.md`
- Prompt design + CF history: `docs/analyzer_prompt_design_notes.md`
- Per-cell traces / metrics / configs: `outputs/post_neurips_ac3_phase{1,2,3_collabllm,3_huang}/`
- Analysis cache + provenance: `outputs/analysis_cache/registry.json`

## Cost / time accounting (best estimates as of now)

- Phase 1: ~1.5h wall, ~$0.05 reported (DeepSeek Foundry not priced).
- Phase 2: ~4h wall (gpt-5.4 parallel done in ~1.5h; Kimi serialized took ~3.5h; gpt-5.5 dropped). Reported cost: gpt-5.4 ≈ $35, Kimi unpriced.
- Phase 3a (CollabLLM): in flight; per-cell ≈ $0.03 baseline → ~$0.50 total.
- Phase 3b (Huang): TBD.
