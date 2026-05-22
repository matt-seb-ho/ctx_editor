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
| Rewrite-v5-resetlike | 69.4% (n=144, e=0) | 35.4% (n=113, e=0) | 25.2% (n=147, e=0) | 72.0% (n=150, e=0) | 50.5% |
| Rewrite-v6-GEPA | 76.4% (n=144, e=2) | 45.1% (n=113, e=2) | 27.2% (n=147, e=0) | 78.7% (n=150, e=2) | 56.8% |
| Rewrite-A1-v1+v8analyzer | 84.0% (n=144, e=0) | 54.0% (n=113, e=0) | 39.5% (n=147, e=0) | 78.7% (n=150, e=0) | 64.0% |
| Rewrite-A2-v8 | 83.3% (n=144, e=3) | 56.6% (n=113, e=1) | 46.3% (n=147, e=0) | 72.7% (n=150, e=1) | 64.7% |
| Rewrite-A3-v9-no-conv | 80.6% (n=144, e=7) | 63.7% (n=113, e=1) | 53.1% (n=147, e=0) | 56.7% (n=150, e=2) | 63.5% |
| Rewrite-A4-v10-GEPA | 81.2% (n=144, e=2) | 54.0% (n=113, e=3) | 53.1% (n=147, e=0) | 60.0% (n=150, e=1) | 62.1% |


## Δ vs Baseline (positive = rewrite better)

| Variant | math | code | database | actions | avg |
|---|---|---|---|---|---|
| AO | +13.9pp | +25.7pp | +23.1pp | +10.0pp | +18.2pp |
| Reset | +9.7pp | +24.8pp | +26.5pp | +7.3pp | +17.1pp |
| Rewrite-v1 | +1.4pp | -6.2pp | +5.4pp | -2.0pp | -0.3pp |
| Rewrite-v2 | -1.4pp | +1.8pp | -0.7pp | -6.0pp | -1.6pp |
| Rewrite-v3-no-conv | -3.5pp | -2.7pp | +0.0pp | -3.3pp | -2.4pp |
| Rewrite-v4-strict | -6.2pp | -0.9pp | -1.4pp | -11.3pp | -5.0pp |
| Rewrite-v5-resetlike | -2.8pp | +0.9pp | +2.7pp | -4.0pp | -0.8pp |
| Rewrite-v6-GEPA | +4.2pp | +10.6pp | +4.8pp | +2.7pp | +5.6pp |
| Rewrite-A1-v1+v8analyzer | +11.8pp | +19.5pp | +17.0pp | +2.7pp | +12.7pp |
| Rewrite-A2-v8 | +11.1pp | +22.1pp | +23.8pp | -3.3pp | +13.4pp |
| Rewrite-A3-v9-no-conv | +8.3pp | +29.2pp | +30.6pp | -19.3pp | +12.2pp |
| Rewrite-A4-v10-GEPA | +9.0pp | +19.5pp | +30.6pp | -16.0pp | +10.8pp |
