# Reasoning Effort Baseline Experiment: Medium vs High

**Date**: 2026-04-27
**Model**: gpt-5-mini
**Variable**: `reasoning_effort` (medium vs high) for the assistant role
**Subset**: Dev set (paper's main LiC subset) and htn20_52 (multi-model appendix subset)

## Motivation

Test whether increasing `reasoning_effort` from medium to high improves LiC baseline (S0) performance with gpt-5-mini. If the model simply "thinks harder" about its final response, does it overcome the context pollution effect without any context management?

## Setup

All runs use replay mode (final-turn regeneration only) on pre-existing baseline conversation traces. The only difference between conditions is the `reasoning_effort` parameter on the assistant's API call.

- **Medium**: `model=gpt5_mini` (existing paper config, `reasoning_effort: medium`)
- **High**: `model=gpt5_mini_high` (new config, `reasoning_effort: high`)

Model config: `src/ctx_editor/config/model/gpt5_mini_high.yaml`

## Results

### Dev Set (Paper's Main Table 2 Subset)

This is the primary comparison. Denominators match the paper's Table 2 numbers.

| Task | n | Medium (paper) | High | Delta |
|------|---|:-:|:-:|:-:|
| Math | 20 | 12/20 (60%) | 11/20 (55%) | -5pp |
| Code | 19 | 3/19 (16%) | 3/19 (16%) | 0pp |
| Database | 25 | 1/25 (4%) | 2/25 (8%) | +4pp |
| Actions | 23 | 2/23 (9%) | 5/25 (20%)* | +11pp |

*Actions high-reasoning ran on full 25 samples (no user-sim pre-filtering via false_negatives.json, since baseline_traces/actions doesn't have one). The medium baseline (9%) is from v8 batch which used n=23 after excluding 2 user-sim-induced. For apples-to-apples comparison, the adjusted actions high result is 5/23 = 21.7% (excluding 2 user-sim-induced found post-hoc).

**Adjusted accuracy** (after false-negative exclusion):

| Task | Medium (adj) | High (adj) | Delta |
|------|:-:|:-:|:-:|
| Math | 12/20 (60%) | 11/19 (57.9%) | ~-2pp |
| Code | 3/19 (16%) | 3/18 (16.7%) | ~+1pp |
| Database | 1/25 (4%) | 2/25 (8%) | +4pp |
| Actions | 2/23 (9%) | 5/23 (21.7%) | +13pp |

### htn20_52 Subset (Multi-Model Appendix Subset)

| Task | n | Medium | High | Delta |
|------|---|:-:|:-:|:-:|
| Math | 20 | 4/20 (20%) | 6/20 (30%) | +10pp |
| Code | 20 | 2/20 (10%) | 3/15 (20%)* | +10pp |
| Database | 20 | 1/20 (5%) | 2/20 (10%) | +5pp |
| Actions | 20 | 7/20 (35%)** | 7/20 (35%)** | 0pp |

*Code high-reasoning had 5 evaluator errors (livecodebench samples with non-Python prompts causing `ast.parse` failures). Effective n=15.

**Actions note: Both medium and high actions results here are from the standard pipeline (no +accumulate prompt). The paper's htn20_52 S0 actions number (12/20, 60%) used the s15 script with the +accumulate prompt variant. The medium control (7/20) confirms the pipeline difference accounts for the gap.

## Analysis

**High reasoning effort provides small, inconsistent gains on the LiC baseline.**

- Across 8 task-subset combinations, high reasoning improves in 5, ties in 2, and regresses in 1.
- The improvements are modest: +4pp to +13pp on dev set, +5pp to +10pp on htn20_52.
- The math dev set regression (-5pp) is within sampling noise at n=20.
- The largest gain is actions dev set (+13pp), but this is also the noisiest comparison (different denominators, no false_negatives.json for high).
- Even with high reasoning effort, the baseline remains far below the design-oracle and ACC results. For example, math dev set goes from 60% to 55% (vs 85% AO, 80% Augment). Database goes from 4% to 8% (vs 32% AO, 48% Reset).

**The core LiC degradation is not a reasoning effort problem.** The model's failure in multi-turn LiC is driven by anchoring on incorrect prior assistant responses in the context, not by insufficient reasoning depth on the final turn. Increasing reasoning effort does not remove the polluted context that causes the anchoring. This aligns with the paper's thesis: the bottleneck is what's in the context, not how hard the model thinks about it.

## Cost Comparison

High reasoning effort increases cost due to more reasoning tokens:

| Task (dev set) | Medium Cost | High Cost | Ratio |
|------|:-:|:-:|:-:|
| Math | ~$0.04 | $0.070 | ~1.7x |
| Code | ~$0.10 | $0.191 | ~1.9x |
| Database | ~$0.05 | $0.091 | ~1.8x |
| Actions | ~$0.02 | $0.033 | ~1.7x |

## Output Directories

### Dev Set (high reasoning)
| Task | Output Dir |
|------|------------|
| Math | `outputs/2026-04-27/13-12-44` |
| Code | `outputs/2026-04-27/13-12-45` |
| Database | `outputs/2026-04-27/13-12-46` |
| Actions | `outputs/2026-04-27/13-12-47` |

### htn20_52 (high reasoning)
| Task | Output Dir |
|------|------------|
| Math | `outputs/2026-04-27/13-08-26` |
| Code | `outputs/2026-04-27/13-08-28` |
| Database | `outputs/2026-04-27/13-08-29` |
| Actions | `outputs/2026-04-27/13-10-22` |

### htn20_52 (medium control, actions only)
| Task | Output Dir |
|------|------------|
| Actions | `outputs/2026-04-27/13-10-32` |

## Run Commands

```bash
# Dev set (high reasoning) -- paper's main subset
python -m ctx_editor.run_experiment experiment=baseline task=dev_math model=gpt5_mini_high \
  load_balancer=multi_endpoint execution.replay_source=data/baseline_traces_v2/math execution.max_concurrent=8

python -m ctx_editor.run_experiment experiment=baseline task=dev_code model=gpt5_mini_high \
  load_balancer=multi_endpoint execution.replay_source=data/baseline_traces_v2/code execution.max_concurrent=8

python -m ctx_editor.run_experiment experiment=baseline task=dev_database model=gpt5_mini_high \
  load_balancer=multi_endpoint execution.replay_source=data/baseline_traces_v2/database execution.max_concurrent=8

python -m ctx_editor.run_experiment experiment=baseline task=dev_actions model=gpt5_mini_high \
  load_balancer=multi_endpoint execution.replay_source=data/baseline_traces/actions execution.max_concurrent=8

# htn20_52 (high reasoning) -- multi-model appendix subset
python -m ctx_editor.run_experiment experiment=baseline task=math_v2 model=gpt5_mini_high \
  load_balancer=multi_endpoint task.data_file=data/htn20_52_math_subset.json \
  execution.replay_source=data/baseline_traces_htn20_52/math execution.max_concurrent=8

python -m ctx_editor.run_experiment experiment=baseline task=code_v2 model=gpt5_mini_high \
  load_balancer=multi_endpoint task.data_file=data/htn20_52_code_subset.json \
  execution.replay_source=data/baseline_traces_htn20_52/code execution.max_concurrent=8

python -m ctx_editor.run_experiment experiment=baseline task=database_v2 model=gpt5_mini_high \
  load_balancer=multi_endpoint task.data_file=data/htn20_52_database_subset.json \
  execution.replay_source=data/baseline_traces_htn20_52/database execution.max_concurrent=8

python -m ctx_editor.run_experiment experiment=baseline task=actions model=gpt5_mini_high \
  load_balancer=multi_endpoint task.data_file=data/htn20_52_actions_subset.json \
  execution.replay_source=data/baseline_traces_htn20_52/actions execution.max_concurrent=8
```

## Reference: Paper Baseline Numbers

### Paper Table 2 (dev set, medium reasoning)
Source: `docs/reports/v8_batch_results.md`

| Task | S0 Baseline | n |
|------|:-:|:-:|
| Math | 12/20 (60%) | 23 - 3 user-sim = 20 |
| Code | 3/19 (16%) | 25 - 6 user-sim = 19 |
| Database | 1/25 (4%) | 25 |
| Actions | 2/23 (9%) | 25 - 2 user-sim = 23 |

### htn20_52 S0 (medium reasoning, from htn20_52_experiment_results.md)

| Task | S0 Baseline | n |
|------|:-:|:-:|
| Math | 4/20 (20%) | 20 |
| Code | 2/20 (10%) | 20 |
| Database | 1/20 (5%) | 20 |
| Actions | 12/20 (60%)* | 20 |

*Actions used s15 script with +accumulate prompt. Without accumulate: 7/20 (35%).
