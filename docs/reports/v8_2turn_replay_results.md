# V8 Replay-Last-2-Turns Results — 2026-03-16

## Setup

Replay mode reuses S0 (baseline) conversation prefixes, strips the final 2 assistant messages,
applies a context intervention strategy (S1 or S2), and regenerates the last 2 turns.
This tests whether interventions can recover from errors that compound across multiple turns.

- **Source traces**: S0 baseline traces (v2 for math/code/database, v1 for actions)
- **Model**: gpt-5-mini
- **Analyzer prompts**: v8
- **Load balancer**: multi_endpoint (round-robin across 4 Azure endpoints)
- **Replay turns**: 2 (last 2 turns regenerated)
- **Max concurrent**: 8
- **False negative filtering**: Enabled (user-sim-induced samples skipped)
- **Memory config** (where applicable): continual source, batched mode, batch_size=5,
  includes full spec Q + ground truth A

## Raw Results

| Task | n | S0 | S0+mem | S1 | S1+mem | S2 | S2+mem |
|------|:-:|:--:|:------:|:--:|:------:|:--:|:------:|
| **math** | 20 (3 skipped) | 50.0% | 50.0% | **75.0%** | **80.0%** | 65.0% | 55.0% |
| **code** | 19 (6 skipped) | 10.5% | 15.8% | **52.6%** | **57.9%** | 36.8% | 42.1% |
| **database** | 25 | 4.0% | 4.0% | **40.0%** | **40.0%** | 20.0% | 16.0% |
| **actions** | 25 | 4.0% | 12.0% | 12.0% | **16.0%** | 12.0% | 4.0% |

### Absolute correct counts

| Task | S0 | S0+mem | S1 | S1+mem | S2 | S2+mem |
|------|:--:|:------:|:--:|:------:|:--:|:------:|
| **math** | 10 | 10 | 15 | 16 | 13 | 11 |
| **code** | 2 | 3 | 10 | 11 | 7 | 8 |
| **database** | 1 | 1 | 10 | 10 | 5 | 4 |
| **actions** | 1 | 3 | 3 | 4 | 3 | 1 |

## Key Observations

### S1 (append analysis) dominates across all tasks

S1 consistently outperforms both S0 and S2, with large absolute gains:
- Math: +25pp over S0 (50% to 75%)
- Code: +42pp over S0 (10.5% to 52.6%)
- Database: +36pp over S0 (4% to 40%)
- Actions: +8pp over S0 (4% to 12%)

### S2 (context edit) improves over S0 but trails S1

S2 lands between S0 and S1 on math, code, and database. The rewriting step may be
discarding useful context that S1 preserves by appending rather than editing.

### Memory effects are modest

- Memory helps S0 only on actions (+8pp) and code (+5pp).
- Memory helps S1 slightly on math (+5pp) and code (+5pp), but is flat on database and actions.
- Memory hurts S2 on math (-10pp) and database (-4pp), while helping on code (+5pp).

### Comparison with 1-turn replay (batch 1)

These 2-turn replay results show substantially higher S1 performance than the earlier
1-turn replay experiments (batch 1), suggesting the v8 analyzer prompts and/or the
extra regenerated turn provide significant benefit. The v2 baseline traces and false
negative filtering also changed the sample denominators, so direct comparison requires
care.

## Run Metadata

- **Timestamp**: 2026-03-16_13-09-27
- **Branch**: newleaf2
- **Logs**: `outputs/replay_logs/2026-03-16_13-09-27/`
- **Memory checkpoints**: `outputs/replay_memories/2026-03-16_13-09-27/`
- **Total runtime**: ~3h 18m (13:09 to 16:27)
