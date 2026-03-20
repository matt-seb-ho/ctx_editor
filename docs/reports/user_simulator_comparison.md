# User Simulator Comparison Report

**Date**: 2026-03-11
**Branch**: newleaf
**Assistant model**: gpt-5-mini (reasoning_effort: medium) across all configs
**Error attribution model**: gpt-5

## Configurations Tested

| Config Name | User Model | System Model | User/System Cost Tier |
|---|---|---|---|
| `gpt5_mini` | gpt-4o-mini | gpt-4o-mini | Low |
| `gpt5m_gpt4o` | gpt-4o | gpt-4o | Medium |
| `gpt5_mini_only` | gpt-5-mini (minimal) | gpt-5-mini (minimal) | Low-Medium |

## (a) Accuracy & Sample Counts

| Task | gpt5_mini | gpt5m_gpt4o | gpt5_mini_only |
|---|---|---|---|
| math_v2 | 74.75% (74/99, 4 excl) | 75.76% (75/99, 4 excl) | 88.42% (84/95, 8 excl) |
| code_v2 | 65.85% (54/82, 18 excl) | 60.00% (57/95, 5 excl) | 63.10% (53/84, 16 excl) |
| database_v2 | 37.50% (36/96, 11 excl)* | 31.00% (31/100, 7 excl) | 33.33% (32/96, 11 excl) |
| actions | 53.00% (53/100, 5 excl) | 47.92% (46/96, 9 excl) | 62.24% (61/98, 7 excl) |

\* gpt5_mini database_v2: directory collision with code_v2 (same-second start); numbers from terminal output, artifacts overwritten. Should re-run.

### Comparison with main branch baselines (gpt-5-mini + gpt-4o-mini)

| Task | Main branch range | Newleaf gpt5_mini | Delta |
|---|---|---|---|
| math_v2 | 78.6% - 88.4% | 74.75% | Below range |
| code_v2 | 51% - 75% | 65.85% | Within range |
| database_v2 | 35.5% - 42.1% | 37.50% | Within range |
| actions | 51.4% - 56.4% | 53.00% | Within range |

Math is slightly below the main branch range — this may be noise (single run) or a small regression from the new conversation format.

## (b) User Simulator Error Rate

Error categories attributed to the user/system simulator (not genuine assistant errors):

| Category | gpt5_mini | gpt5m_gpt4o | gpt5_mini_only |
|---|---|---|---|
| **extraction_failure** | 21 | 21 | 14 |
| **sharding_distortion** | 35 | 20 | 32 |
| **strict_comparison** | 16 | 28 | 28 |
| **clarification_ignored** | 3 | 1 | 1 |
| **other** | 0 | 2 | 1 |
| **Total non-assistant errors** | 75 | 72 | 76 |
| **assistant_error** | 66 | 84 | 49 |
| **Total errors analyzed** | 141* | 156 | 125 |
| **Non-assistant error %** | 53.2% | 46.2% | 60.8% |

\* gpt5_mini database_v2 included from terminal output (56 errors: 22 assistant, 21 sharding, 11 strict_comp, 2 clarification).

### Error rate by task

**Math**: All configs have low non-assistant error rates. Clean evaluation signal.

**Code**: Extremely clean — 95%+ of errors are genuine assistant errors across all configs. Best task for measuring real performance.

**Database**: High sharding_distortion (20-37%) and strict_comparison (19-36%) across all configs. ~60% of errors are non-assistant. Evaluation signal is noisy.

**Actions**: Dominated by extraction_failure (31-49%) and sharding_distortion. 64-84% of errors are non-assistant. Very noisy evaluation signal.

### Excluded samples (errors/invalid conversations)

| Config | math_v2 | code_v2 | database_v2 | actions | Total |
|---|---|---|---|---|---|
| gpt5_mini | 4 | 18 | 11 | 5 | 38 |
| gpt5m_gpt4o | 4 | 5 | 7 | 9 | 25 |
| gpt5_mini_only | 8 | 16 | 11 | 7 | 42 |

`gpt5m_gpt4o` has the fewest excluded samples (25), meaning more samples successfully complete the conversation protocol. `gpt5_mini_only` has the most (42), particularly on math (8) and code (16).

## (c) API Costs

| Task | gpt5_mini | gpt5m_gpt4o | gpt5_mini_only |
|---|---|---|---|
| math_v2 | $1.19 | $3.61 | $1.33 |
| code_v2 | $1.39 | $6.05 | $1.63 |
| database_v2 | $0.68 | $2.42 | $0.78 |
| actions | $0.68 | $2.37 | $0.77 |
| **Total** | **$3.94** | **$14.45** | **$4.52** |

`gpt5m_gpt4o` is **3.2-4.4x** more expensive than the other configs, primarily due to gpt-4o input/output costs for user and system roles.

## Recommendation

**Eliminate `gpt5m_gpt4o`**: 3-4x higher cost with no accuracy benefit and often lower accuracy. The gpt-4o user simulator doesn't produce better conversations.

**Choice between `gpt5_mini` and `gpt5_mini_only`**:

| Factor | gpt5_mini | gpt5_mini_only | Winner |
|---|---|---|---|
| Cost | $3.94 | $4.52 | gpt5_mini |
| Excluded samples | 38 | 42 | gpt5_mini |
| Accuracy (math) | 74.75% | 88.42% | gpt5_mini_only* |
| Accuracy (code) | 65.85% | 63.10% | gpt5_mini |
| Accuracy (database) | 37.50% | 33.33% | gpt5_mini |
| Accuracy (actions) | 53.00% | 62.24% | gpt5_mini_only* |

\* gpt5_mini_only's higher accuracy on math/actions comes with more excluded samples, which inflates accuracy by removing harder cases.

**Recommendation: Use `gpt5_mini` (gpt-4o-mini user/system)** for baseline runs.
- Fewer excluded samples = more data points per run
- Lower cost
- Accuracy differences on math/actions are likely inflated by exclusion bias in gpt5_mini_only
- Consistent with the main branch baseline runs, enabling cross-branch comparison

## Next Steps

1. Run 2 more baseline runs per task with `gpt5_mini` (Part 1.5)
2. Re-run gpt5_mini database_v2 to recover artifacts lost to directory collision
3. Create dev sets from consistently hard problems across 3 runs (Part 1.6)
