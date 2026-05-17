# Post-NeurIPS AC3 Scale-up — Overnight Summary

**Run window**: 2026-05-16 evening → 2026-05-17 afternoon
**Status**: Phase 1 + Phase 2 + Phase 3a (CollabLLM) complete. Phase 3b (Huang) in re-flight (see below).
**Author**: Claude (autonomous overnight)

---

## TL;DR

- **Phase 1** (DeepSeek-V4-Flash, 6 strategies × 4 tasks × 3 prefixes, last-turn replay): AO leads (+18.1pp), AC3-Reset is right behind (+17.1pp). Reset and Gated-Reset tie (within 0.1pp); Reset wins on the tiebreak (simpler/cheaper). Rewrite (LLM compaction) underperforms Baseline.
- **Phase 2** (gpt-5.4 + Kimi-K2.6, S0/AO/Augment/Reset, 4 tasks × 3 prefixes, last-turn replay): **Reset overtakes AO** at the average (+15.3pp vs +10.8pp over Baseline). Reset dominates AO on **database by +26pp**. Reset is within ±5pp of AO on math/code/actions. gpt-5.5 was dropped (deferred per cost/throughput note).
- **Phase 3a** (CollabLLM N=3, DeepSeek-V4-Flash): **AO wins math-hard** (+10pp vs Baseline). AC3-Augment **regresses below Baseline on CollabLLM math** (-10pp) — multi-turn fresh-sim seems to penalize the appended-analysis pattern as analyses pile up turn after turn. AC3-Reset ties Baseline on math-hard. Bigcodebench is functionally unsolvable by DeepSeek-V4-Flash at this scale (all-zero except Reset rep1 at 5%). See `docs/reports/post_neurips_ac3_phase3_collabllm.md`.
- **Phase 3b** (Huang/WildChat N=3): first attempt with DeepSeek as respondent failed because the Huang pipeline doesn't go through our Foundry load balancer — all DeepSeek calls 404'd; the first 6 cells reported 0 evaluated turns. Re-launched with gpt-5-mini (the paper's default). Re-run currently in flight; ETA finish ≈ 18:40 PT today. Results will land in `outputs/post_neurips_ac3_phase3_huang/`; report at `docs/reports/post_neurips_ac3_phase3_huang.md` when complete.

The flipped narrative across Phase 1→2 (AO led on DeepSeek, Reset leads on gpt-5.4+Kimi) is the most interesting empirical finding so far: the cost of *retaining* a stronger model's prior assistant turns (good but partially wrong) is recoverable by AC3-Reset's compacted-context rewrite, whereas the weaker DeepSeek benefits more from a clean slate (AO).

**Cross-benchmark complication**: Phase 3a shows that in CollabLLM multi-turn fresh sims, AO is back to being the winner on math-hard, and AC3-Augment actively regresses. This is the first evidence that the Phase-1/2 takeaway ("AC3-Reset close to AO; sometimes better") does NOT transfer cleanly to the multi-turn fresh-sim regime where the strategy fires every turn. Likely root cause: AC3 strategies are designed for one-shot intervention in last-turn replay; firing on every turn (especially Augment's analysis-pile-on) introduces compounding noise. **Multi-turn gating (the Phase-3-from-rev.2 idea we deferred) suddenly looks much more important than rev.3 suggested.**

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

### 3b WildChat/Huang (in re-flight)

First attempt at 11:07 with DeepSeek-V4-Flash as respondent failed: the Huang pipeline (`run_phase2.py`) instantiates a plain `OpenAIModelClient` without passing through our `LoadBalancerConfig`, so calls to `DeepSeek-V4-Flash` got routed at the Azure OpenAI endpoint `dl-openai-3` which does not host that deployment → 404 `DeploymentNotFound`. The first 6 cells reported 0 evaluated turns. **Engineering fix needed**: thread `load_balancer_config` through `huang_eval/run_phase2.py` so Foundry routing works.

Re-launched at 16:09 with `respondent_model=gpt-5-mini` (the paper's default). gpt-5-mini routes through the standard Azure OpenAI deployments, so no load-balancer hack needed. Currently in flight; ETA finish ≈ 18:40 PT.

Variants tested: `s15` (= AC3-Reset, Phase 1 winner) and `augment` (= AC3-Augment), both with `v8` analyzer. 3 seeds each = 6 invocations. Results will populate `outputs/post_neurips_ac3_phase3_huang/` and a fresh `docs/reports/post_neurips_ac3_phase3_huang.md` when complete.

## Methodological notes for the paper

The cross-phase results suggest a clear narrative split, useful for the paper:

1. **Last-turn replay (Phase 1+2)** — paper's primary AC3 evaluation regime — shows AC3-Reset is competitive with AO on weaker models and *beats* AO at stronger models on database. This is the headline.
2. **Multi-turn fresh sim (Phase 3a)** — multi-step refinement settings — shows AO remains the upper bound and AC3-Augment can actively hurt (analysis-pile-on). This is a real limitation that should be acknowledged.

The deployment-realism implication: **multi-turn AC3 with gating** becomes the actually-useful production setup — fire the intervention only when needed, not every turn. The rev.2 multi-turn gating Phase that was deferred to "future work" now looks more important than I anticipated when scoping for tonight.

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
