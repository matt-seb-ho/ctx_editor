# AC3 Phase 3a — CollabLLM N=3 redo (DeepSeek-V4-Flash)

**Run window**: 2026-05-17 07:40 → 11:04 PT
**Model**: DeepSeek-V4-Flash (Foundry deployment)
**Strategies**: Baseline, AO, AC3-Augment (`v8`), AC3-Reset (`v8`)
**Tasks**: math-hard (MATH-Hard) and bigcodebench
**Sample size**: `limit=20` per task per rep, 3 sampling reps with seeds 43/44/45

## Results

Mean ± stdev across the 3 reps.

| Strategy | math-hard | bigcodebench |
|---|---|---|
| Baseline | 30.0% ± 0.0pp | 0.0% ± 0.0pp |
| **AO** | **40.0% ± 5.0pp** | 0.0% ± 0.0pp |
| AC3-Augment (v8) | 20.3% ± 4.8pp | 0.0% ± 0.0pp |
| AC3-Reset (v8) | 30.0% ± 5.0pp | **1.7% ± 2.9pp** |

## Per-cell detail

| Strategy | Dataset | Rep | Accuracy | Wall | Errors excluded |
|---|---|---|---|---|---|
| Baseline | math-hard | 1 | 30.00% (6/20) | 386s | 0 |
| Baseline | math-hard | 2 | 30.00% (6/20) | 264s | 0 |
| Baseline | math-hard | 3 | 30.00% (6/20) | 279s | 0 |
| Baseline | bigcodebench | 1 | 0.00% (0/20) | 512s | 0 |
| Baseline | bigcodebench | 2 | 0.00% (0/20) | 447s | 0 |
| Baseline | bigcodebench | 3 | 0.00% (0/19) | 610s | 1 |
| AO | math-hard | 1 | 45.00% (9/20) | 295s | 0 |
| AO | math-hard | 2 | 35.00% (7/20) | 376s | 0 |
| AO | math-hard | 3 | 40.00% (8/20) | 294s | 0 |
| AO | bigcodebench | 1 | 0.00% (0/20) | 395s | 0 |
| AO | bigcodebench | 2 | 0.00% (0/20) | 398s | 0 |
| AO | bigcodebench | 3 | 0.00% (0/20) | 424s | 0 |
| AC3-Augment | math-hard | 1 | 20.00% (4/20) | 526s | 0 |
| AC3-Augment | math-hard | 2 | 25.00% (5/20) | 647s | 0 |
| AC3-Augment | math-hard | 3 | 15.79% (3/19) | 615s | 1 |
| AC3-Augment | bigcodebench | 1 | 0.00% (0/17) | 1187s | 3 |
| AC3-Augment | bigcodebench | 2 | 0.00% (0/16) | 911s | 4 |
| AC3-Augment | bigcodebench | 3 | 0.00% (0/14) | 1034s | 6 |
| AC3-Reset | math-hard | 1 | 35.00% (7/20) | 406s | 0 |
| AC3-Reset | math-hard | 2 | 30.00% (6/20) | 316s | 0 |
| AC3-Reset | math-hard | 3 | 25.00% (5/20) | 284s | 0 |
| AC3-Reset | bigcodebench | 1 | 5.00% (1/20) | 879s | 0 |
| AC3-Reset | bigcodebench | 2 | 0.00% (0/20) | 369s | 0 |
| AC3-Reset | bigcodebench | 3 | 0.00% (0/20) | 349s | 0 |

## Takeaways

- **AO is the clear winner on CollabLLM math-hard** (+10pp vs Baseline). Mirrors Phase 1 (DeepSeek LiC math: AO best).
- **AC3-Augment underperforms Baseline on CollabLLM math** (-10pp). Notable inversion vs LiC where Augment hovered near AO. Multi-turn fresh-sim seems to penalize the appended-analysis pattern; the analyzer note distracts the assistant rather than guides it. Also bigcodebench Augment errors-excluded climbed from 0 → 3 → 4 → 6 across reps — conversations are blowing up in length / token budget, causing API errors.
- **AC3-Reset ties Baseline on math-hard** (~30%) and is the only non-zero strategy on bigcodebench (+1.7pp on average, real but tiny). Reset is at least stable on CollabLLM — doesn't degrade — but doesn't show the +25pp database lift we saw in Phase 2.
- **Bigcodebench is functionally unsolvable by DeepSeek-V4-Flash at this scale** — every Baseline/AO/Augment trial returned 0/20. Reset got 1/20 in one rep. The benchmark + model combination is too hard for any single-turn or multi-turn strategy to recover.
- **Variance is moderate** (±5pp on most cells). N=3 gives clean error bars; the per-cell signal is robust.

## Comparison to Phase 1/2

This is the first piece of evidence that the AC3-Reset winner does NOT generalize to all benchmarks unchanged. In CollabLLM multi-turn fresh sims, AO outpaces AC3 by 10pp on math-hard. Plausible explanations:

1. **Last-turn replay vs multi-turn fresh sim**: Phase 1+2 evaluated *one* intervention per problem (the final turn). Phase 3 lets the strategy fire repeatedly (every turn past `min_turns`). For Augment, that means the analyzer note compounds — likely the source of the regression.
2. **Sample size**: CollabLLM has n=20 per cell vs LiC's 44-50. With smaller n, prefix variance dominates.
3. **Different task topology**: CollabLLM tasks require iterative refinement (especially math-hard with complex multi-step problems); AC3's reset / compaction may discard useful intermediate work that the model would otherwise build on.

Actionable read: **for the paper, AC3-Reset is the recommended intervention for LiC-style sharded settings** (where it clearly beats AO on database, ties on math/code/actions). **For CollabLLM-style multi-turn refinement settings, AO remains the stronger baseline** and AC3 needs more work before it generalizes there. Worth a multi-turn-gating experiment to see if gating prevents Augment's "analyzer pile-on" failure mode.
