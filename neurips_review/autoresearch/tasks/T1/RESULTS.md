# T1 — Summarisation baseline vs AC3, LiC database + code

gpt-5.4-mini (TRAPI), sharded user sim, full LiC pool (`data/sharded_instructions_600.json`): n=107 database, n=100 code. 1 run per cell.
Pairing: same samples in every arm; McNemar exact on discordant pairs.
Budgets measured from `call_meter.json` (pre-false-negative-analysis snapshot).

## Accuracy

| Task | Arm | Acc (raw) | n correct | Δ vs baseline | 95% CI | W/L | McNemar p | Adj. acc | Artifact |
|---|---|---|---|---|---|---|---|---|---|
| LiC-database | Baseline (full context) | 56.1% | 60/107 | — | — | — | — | 58.3% | `outputs/T1/main/db_baseline` |
| LiC-database | Summarisation (1 call/turn) | 53.3% | 57/107 | -2.8pp | [-10.5, +5.7] | 10/13 | 0.6776 | 83.8% | `outputs/T1/main/db_summarize1` |
| LiC-database | Summarisation (2 calls/turn, budget-matched) | 47.7% | 51/107 | -8.4pp | [-14.2, -0.0] | 6/15 | 0.0784 | 79.7% | `outputs/T1/main/db_summarize2` |
| LiC-database | MT-OSC (reimpl., w=4, as published) | 60.7% | 65/107 | +4.7pp | [-3.6, +11.5] | 13/8 | 0.3833 | 62.5% | `outputs/T1/main/db_mtosc_w4` |
| LiC-database | AC3-Reset | 75.7% | 81/107 | +19.6pp | [+9.2, +26.1] | 28/7 | 0.0005 | 89.0% | `outputs/T1/main/db_reset` |
| LiC-database | AC3-Gated-Reset | 73.8% | 79/107 | +17.8pp | [+7.6, +24.3] | 26/7 | 0.0013 | 84.9% | `outputs/T1/main/db_gated` |

## Pooled over both tasks (paired)

| Arm | Acc | Δ vs baseline | 95% CI | W/L | McNemar p |
|---|---|---|---|---|---|
| Baseline (full context) | 56.1% | — | — | — | — |
| Summarisation (1 call/turn) | 53.3% | -2.8pp | [-10.5, +5.7] | 10/13 | 0.6776 |
| Summarisation (2 calls/turn, budget-matched) | 47.7% | -8.4pp | [-14.2, -0.0] | 6/15 | 0.0784 |
| MT-OSC (reimpl., w=4, as published) | 60.7% | +4.7pp | [-3.6, +11.5] | 13/8 | 0.3833 |
| AC3-Reset | 75.7% | +19.6pp | [+9.2, +26.1] | 28/7 | 0.0005 |
| AC3-Gated-Reset | 73.8% | +17.8pp | [+7.6, +24.3] | 26/7 | 0.0013 |

## Head-to-head: summarisation vs AC3-Reset (paired)

| Task | Comparison | Δ | W/L | McNemar p |
|---|---|---|---|---|
| LiC-database | AC3-Reset − summarize1 | +22.4pp | 31/7 | 0.0001 |
| LiC-database | AC3-Reset − summarize2 | +28.0pp | 36/6 | 0.0000 |
| LiC-database | AC3-Reset − mtosc_w4 | +15.0pp | 21/5 | 0.0025 |

## Measured budget (per arm, whole run)

| Task | Arm | LLM calls total | strategy calls | assistant | user sim | system judge | total tokens | strategy tokens | calls/conv | strategy calls/conv | avg turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| LiC-database | Baseline (full context) | 1222 | 0 | 443 | 336 | 443 | 874,226 | 0 | 11.4 | 0.0 | 4.1 |
| LiC-database | Summarisation (1 call/turn) | 1558 | 336 | 443 | 336 | 443 | 1,596,358 | 559,644 | 14.6 | 3.1 | 7.3 |
| LiC-database | Summarisation (2 calls/turn, budget-matched) | 1909 | 678 | 446 | 339 | 446 | 2,294,569 | 1,268,902 | 17.8 | 6.3 | 7.3 |
| LiC-database | MT-OSC (reimpl., w=4, as published) | 1258 | 30 | 445 | 338 | 445 | 940,225 | 51,711 | 11.8 | 0.3 | 4.3 |
| LiC-database | AC3-Reset | 1879 | 666 | 440 | 333 | 440 | 1,682,405 | 781,968 | 17.6 | 6.2 | 6.9 |
| LiC-database | AC3-Gated-Reset | 1483 | 276 | 438 | 331 | 438 | 1,204,787 | 330,333 | 13.9 | 2.6 | 5.3 |

