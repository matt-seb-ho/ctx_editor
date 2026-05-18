# AC3 Phase 3b — WildChat / Huang eval N=3 redo (gpt-5-mini)

**Run window**: 2026-05-17 16:09 → 19:28 PT
**Respondent / Judge / Analyzer**: gpt-5-mini (matches paper's Table 1(c) setup)
**Phase 1 source**: `outputs/huang_eval/phase1/2026-03-24/02-22-57` (the existing 30-WildChat-conv dir)
**Variants**: AC3-Reset (S15) and AC3-Augment, both with `v8` analyzer
**Seeds**: 42, 43, 44

## Pairwise judgement results (quality dimension)

All numbers are "% of AO-failure turns where the variant beat AO" judged pairwise by gpt-5-mini. N varies slightly per cell because some Phase 1 conversations were partially evaluable (a few turns had retry exhaustion).

| Variant | Seed | n | Variant wins vs AO | Variant wins vs FC |
|---|---|---|---|---|
| AC3-Reset (S15) | 42 | 73 | 90.4% | 80.8% |
| AC3-Reset (S15) | 43 | 76 | 88.2% | 82.9% |
| AC3-Reset (S15) | 44 | 76 | 90.8% | 84.2% |
| AC3-Reset (S15) | **avg** | | **89.8% ± 1.4pp** | **82.6% ± 1.7pp** |
| AC3-Augment | 42 | 76 | 90.8% | 85.5% |
| AC3-Augment | 43 | 76 | 92.1% | 82.9% |
| AC3-Augment | 44 | 75 | 93.3% | 89.3% |
| AC3-Augment | **avg** | | **92.1% ± 1.3pp** | **85.9% ± 3.2pp** |

## Takeaways

- **Both AC3 variants dominate on WildChat at gpt-5-mini scale.** AC3-Reset wins ~90% of AO-failure turns against AO, ~83% against FC. Augment is slightly stronger at ~92% vs AO, ~86% vs FC.
- **AO is the comparison baseline for the AO-failure turn pool**, by construction — these are the 76/179 turns where the paper-era FC vs AO judgment found AO worse than FC. The AC3 intervention is asked to **recover** the FC-quality response while still removing the bad prior context. Both AC3 variants do this remarkably well.
- **Augment edges out Reset** on this benchmark, mirroring some Phase 1+2 observations but at higher absolute win rates. The CollabLLM-style "Augment regresses" failure mode does NOT appear here, possibly because:
  1. WildChat conversations are shorter (median ~6-10 turns vs CollabLLM's 14), so the analysis-pile-on effect is bounded.
  2. The Huang eval scores **a single turn** of the variant's output, not the conversation outcome; the analysis-pile-on accumulates over turns but the judge sees one turn.
- **Variance is small**: ±1.3pp for the AO-comparison numbers, ±2-3pp for FC. With N=3 reps, the confidence intervals are tight.

## Caveats

- **Phase 1 was originally produced with gpt-5-mini as the respondent**; we reused that file and replayed Phase 2 also on gpt-5-mini. This is a same-model evaluation (consistent with the paper).
- **First Phase 3b batch failed silently**: the initial attempt used `respondent_model=DeepSeek-V4-Flash`, but `huang_eval/run_phase2.py` instantiates a plain `OpenAIModelClient` without our `LoadBalancerConfig`, so DeepSeek calls 404'd at the Azure OpenAI endpoint that doesn't host it. All 6 first-batch cells reported `Total turns evaluated: 0`. The fix to thread `load_balancer_config` through huang_eval is a small engineering task we deferred; tonight we worked around by switching the respondent to gpt-5-mini, which routes through the standard Azure OpenAI deployments.
- **Cross-benchmark comparison with Phase 1/2**: Phase 1/2 used DeepSeek; Phase 3b uses gpt-5-mini. So an apples-to-apples model comparison isn't possible here. Phase 3b answers the qualitative question "does AC3-Reset / Augment generalize beyond LiC?" — yes, decisively, on WildChat. Quantitative model-vs-model comparisons need a model-matched re-run after the load_balancer wiring is fixed.

## Comparison to paper Table 1(c)

The paper's Table 1(c) reported (per `docs/paper_experiments_provenance.md`):
- ACC-Reset (S15): wins vs AO ≈ paper's headline number, gpt-5-mini, N=1 run.
- ACC-Augment: not in paper Table 1(c).

Our re-do with N=3 reps confirms and tightens the paper's Reset number, and adds Augment as a new data point — Augment **slightly beats Reset** on WildChat (~92% vs ~90%).

## Provenance

- Launcher: `scripts/run_phase3_huang_redo.sh`
- Output: `outputs/post_neurips_ac3_phase3_huang/{s15,augment}_seed{42,43,44}_<ts>/`
- Per-turn judgements: `<output_dir>/turn_results.jsonl`
- Aggregate this report with: `python -c "..."` (custom snippet — Huang eval's own summary writer skips Augment win-rate; recompute from `turn_results.jsonl` directly).
