# Rewrite versions vs Baseline / Reset on LiC (DeepSeek-V4-Flash, last-turn replay, htn50_52)

Per-task averages across 3 prefix replicates. Each cell shows accuracy% and total n.

| Variant | math | code | database | actions | avg |
|---|---|---|---|---|---|
| Baseline | 72.2% (n=144, e=0) | 34.5% (n=113, e=0) | 22.4% (n=147, e=0) | 76.0% (n=150, e=0) | 51.3% |
| AO | 86.1% (n=144, e=0) | 60.2% (n=113, e=0) | 45.6% (n=147, e=0) | 86.0% (n=150, e=0) | 69.5% |
| Reset | 81.9% (n=144, e=0) | 59.3% (n=113, e=0) | 49.0% (n=147, e=0) | 83.3% (n=150, e=0) | 68.4% |
| Rewrite-v1 | 73.6% (n=144, e=0) | 28.3% (n=113, e=0) | 27.9% (n=147, e=0) | 74.0% (n=150, e=0) | 51.0% |
| Rewrite-v2 | 70.8% (n=144, e=0) | 36.3% (n=113, e=0) | 21.8% (n=147, e=0) | 70.0% (n=150, e=0) | 49.7% |
| Rewrite-v3-no-conv | 68.8% (n=144, e=3) | 31.9% (n=113, e=0) | 22.4% (n=147, e=0) | 72.7% (n=150, e=0) | 48.9% |
| Rewrite-v4-strict | 66.0% (n=144, e=9) | 33.6% (n=113, e=3) | 21.1% (n=147, e=4) | 64.7% (n=150, e=7) | 46.3% |


## Δ vs Baseline (positive = rewrite better)

| Variant | math | code | database | actions | avg |
|---|---|---|---|---|---|
| AO | +13.9pp | +25.7pp | +23.1pp | +10.0pp | +18.2pp |
| Reset | +9.7pp | +24.8pp | +26.5pp | +7.3pp | +17.1pp |
| Rewrite-v1 | +1.4pp | -6.2pp | +5.4pp | -2.0pp | -0.3pp |
| Rewrite-v2 | -1.4pp | +1.8pp | -0.7pp | -6.0pp | -1.6pp |
| Rewrite-v3-no-conv | -3.5pp | -2.7pp | +0.0pp | -3.3pp | -2.4pp |
| Rewrite-v4-strict | -6.2pp | -0.9pp | -1.4pp | -11.3pp | -5.0pp |
