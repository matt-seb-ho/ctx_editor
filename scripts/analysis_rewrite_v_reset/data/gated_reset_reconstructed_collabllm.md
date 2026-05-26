# Gated-Reset reconstruction (LiC last-turn replay, DSV4F)

Reconstructed from existing Reset analyzer logs + Baseline traces. No new LLM calls.
Per-sample rule: Reset if `needs_edit=True`, else Baseline.

| task | conv | n | reset acc | baseline acc | **gated acc** | n_reset_chosen | n_baseline_chosen |
|---|---|---|---|---|---|---|---|
| bigcodebench | 1 | 20 | 5.0% | 0.0% | **5.0%** | 20 | 0 |
| bigcodebench | 2 | 20 | 0.0% | 0.0% | **0.0%** | 20 | 0 |
| bigcodebench | 3 | 19 | 0.0% | 0.0% | **0.0%** | 19 | 0 |
| math-hard | 1 | 20 | 35.0% | 30.0% | **35.0%** | 20 | 0 |
| math-hard | 2 | 20 | 30.0% | 30.0% | **30.0%** | 19 | 0 |
| math-hard | 3 | 20 | 25.0% | 30.0% | **25.0%** | 19 | 0 |

## Per-task aggregates

| task | total n | reset acc | baseline acc | **gated acc** | %samples gated-open |
|---|---|---|---|---|---|
| bigcodebench | 59 | 1.7% | 0.0% | **1.7%** | 100.0% |
| math-hard | 60 | 30.0% | 30.0% | **30.0%** | 96.7% |

## Overall

- Total n: 119
- Reset accuracy: **15.97%**
- Baseline accuracy: 15.13%
- **Gated-Reset (reconstructed): 15.97%**
- Samples where gate opened (Reset chosen): 117/119 (98.3%)
