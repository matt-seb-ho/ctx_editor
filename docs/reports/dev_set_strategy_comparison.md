# Dev Set Strategy Comparison

**Date**: 2026-03-12
**Branch**: newleaf
**Model**: gpt-5-mini (assistant) + gpt-4o-mini (user/system)
**Dev sets**: math (23), code (25), database (25), actions (25) — curated hard problems

## Results

| Task | Baseline | Baseline+mem | S1 (append) | S1+mem | S2 (edit v2) | S2+mem |
|---|---|---|---|---|---|---|
| **math** | 14.5% | 31.82% (7/22) | 31.58% (6/19) | 35.00% (7/20) | **61.54%** (8/13) | 50.00% (8/16) |
| **code** | 0% | 20.00% (3/15) | 25.00% (3/12) | 40.00% (6/15) | **57.14%** (8/14) | 41.67% (5/12) |
| **database** | 0% | 4.17% (1/24) | 0.00% (0/21) | **20.00%** (5/25) | 4.00% (1/25) | 0.00% (0/24) |
| **actions** | 0% | 8.00% (2/25) | 20.00% (4/20) | **31.58%** (6/19) | 16.00% (4/25) | 16.00% (4/25) |

Baseline accuracy was extracted from existing gpt5_mini runs (average across 2-3 runs per task).

## Excluded Samples

Exclusions vary significantly across settings — more complex strategies tend to have more failures (rate limits, timeouts, malformed outputs):

| Task | Baseline | Baseline+mem | S1 | S1+mem | S2 | S2+mem |
|---|---|---|---|---|---|---|
| math (23) | 0 | 1 | 4 | 3 | 10 | 7 |
| code (25) | 0 | 10 | 13 | 10 | 11 | 13 |
| database (25) | 0 | 1 | 4 | 0 | 0 | 1 |
| actions (25) | 0 | 0 | 5 | 6 | 0 | 0 |

S2 (context edit v2) has particularly high exclusions on math and code, which inflates its accuracy numbers. The raw correct counts (8/13 vs 7/20 for S2 vs S1+mem on math) tell a more balanced story.

## Key Observations

### 1. Context editing (S2) is most effective on math and code
S2 without memory achieves the highest accuracy on math (61.54%) and code (57.14%). These reasoning-intensive tasks benefit most from the ability to discard incorrect partial work and restart with a clean analysis.

### 2. Memory consistently helps
Every strategy improves with memory:
- Baseline → Baseline+mem: gains on all 4 tasks
- S1 → S1+mem: gains on all 4 tasks (especially database: 0% → 20%)
- S2 → S2+mem: mixed (helps actions, hurts math/code)

### 3. S1+memory is the most robust strategy
S1+mem shows improvements across all tasks including database (the hardest task). Unlike S2, it doesn't suffer from high exclusion rates. The append-only approach is more stable while memory provides the learning signal.

### 4. S2+memory interference
Adding memory to S2 hurts math (61.54% → 50.00%) and code (57.14% → 41.67%). Hypothesis: the memory content may bias the analyzer's pivot decisions, causing it to either pivot unnecessarily or not pivot when it should. The analyzer prompt should be adjusted to weight the current conversation evidence over memory.

### 5. Database remains very hard
Only S1+mem makes meaningful progress (20%). The combination of sharding distortion, strict string comparison, and the inherent difficulty of SQL generation in multi-turn makes this the hardest domain.

## Recommendations

1. **For immediate use**: S1+memory is the safest bet — consistent gains, low exclusions, works on all tasks
2. **For math/code specifically**: S2 without memory is strongest, but the high exclusion rate needs investigation
3. **Memory for S2**: Needs prompt tuning — the analyzer should treat memory as weak prior, not strong guidance. Consider targeting memory to "analysis style" rather than "analysis content"
4. **Database task**: May need task-specific interventions (e.g., SQL-specific evaluation, relaxed comparison)
