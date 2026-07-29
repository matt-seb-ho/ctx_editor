# T1 — Summarisation baseline vs AC3, LiC database + code

gpt-5.4-mini (TRAPI), sharded user sim, N=30 samples/task, 1 run per cell.
Pairing: same 30 samples in every arm; McNemar exact on discordant pairs.
Budgets measured from `call_meter.json` (pre-false-negative-analysis snapshot).

## Accuracy

| Task | Arm | Acc (raw) | n correct | Δ vs baseline | 95% CI | W/L | McNemar p | Adj. acc | Artifact |
|---|---|---|---|---|---|---|---|---|---|
| LiC-database | Baseline (full context) | 53.3% | 16/30 | — | — | — | — | — | `outputs/T1/db_baseline` |

## Pooled over both tasks (paired, n=60)

| Arm | Acc | Δ vs baseline | 95% CI | W/L | McNemar p |
|---|---|---|---|---|---|
| Baseline (full context) | 53.3% | — | — | — | — |

## Head-to-head: summarisation vs AC3-Reset (paired)

| Task | Comparison | Δ | W/L | McNemar p |
|---|---|---|---|---|

## Measured budget (per arm, whole run: 30 conversations)

| Task | Arm | LLM calls total | strategy calls | assistant | user sim | system judge | total tokens | strategy tokens | calls/conv | strategy calls/conv | avg turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| LiC-database | Baseline (full context) | 336 | 0 | 122 | 92 | 122 | 236,962 | 0 | 11.2 | 0.0 | 4.1 |

