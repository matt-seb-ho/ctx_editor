# Gated-Reset reconstruction (LiC last-turn replay, DSV4F)

Reconstructed from existing Reset analyzer logs + Baseline traces. No new LLM calls.
Per-sample rule: Reset if `needs_edit=True`, else Baseline.

| task | conv | n | reset acc | baseline acc | **gated acc** | n_reset_chosen | n_baseline_chosen |
|---|---|---|---|---|---|---|---|
| actions | 0 | 50 | 80.0% | 64.0% | **80.0%** | 49 | 1 |
| actions | 1 | 50 | 84.0% | 74.0% | **84.0%** | 50 | 0 |
| actions | 2 | 50 | 86.0% | 90.0% | **86.0%** | 50 | 0 |
| code | 0 | 40 | 50.0% | 30.0% | **50.0%** | 37 | 0 |
| code | 1 | 37 | 70.3% | 32.4% | **70.3%** | 33 | 2 |
| code | 2 | 36 | 58.3% | 41.7% | **58.3%** | 33 | 1 |
| database | 0 | 49 | 51.0% | 14.3% | **51.0%** | 49 | 0 |
| database | 1 | 49 | 42.9% | 18.4% | **42.9%** | 48 | 1 |
| database | 2 | 49 | 53.1% | 34.7% | **53.1%** | 47 | 2 |
| math | 0 | 48 | 72.9% | 56.2% | **72.9%** | 48 | 0 |
| math | 1 | 48 | 87.5% | 77.1% | **87.5%** | 48 | 0 |
| math | 2 | 48 | 85.4% | 83.3% | **85.4%** | 47 | 1 |

## Per-task aggregates

| task | total n | reset acc | baseline acc | **gated acc** | %samples gated-open |
|---|---|---|---|---|---|
| actions | 150 | 83.3% | 76.0% | **83.3%** | 99.3% |
| code | 113 | 59.3% | 34.5% | **59.3%** | 91.2% |
| database | 147 | 49.0% | 22.4% | **49.0%** | 98.0% |
| math | 144 | 81.9% | 72.2% | **81.9%** | 99.3% |

## Overall

- Total n: 554
- Reset accuracy: **68.95%**
- Baseline accuracy: 52.35%
- **Gated-Reset (reconstructed): 68.95%**
- Samples where gate opened (Reset chosen): 539/554 (97.3%)
