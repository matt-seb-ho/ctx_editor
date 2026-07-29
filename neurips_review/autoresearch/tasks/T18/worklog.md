# T18 — ERGO replays on the filtered pools (closing T17's bound)

**Goal.** T17 established that `tab:main` scores ERGO on *unfiltered* replay pools
(16/23, 11/25, 3/25, 12/25) while every other row uses the filtered pools (20/19/25/23).
The per-sample results for the published ERGO run (`outputs/2026-05-01/23-*`) are gone, so
T17 could only bound the corrected cells (ERGO/code widest at [26.3, 57.9]). T18 runs the
87 last-turn ERGO replays against `data/baseline_traces_v2/{task}` so the pool filter fires,
producing a **measured** ERGO row on the same pools as every other row.

**Honesty note up front.** The correction favours a competitor. Numbers below are reported
as measured, whichever way they fall.

**Comparability caveat, stated before any number.** This is a **replication under a different
model** (`gpt-5.4-mini_2026-03-17` on TRAPI) than the 2026-05 published ERGO run (`gpt5_mini`).
It is evidence about ERGO's standing on the filtered pools; it is *not* a bit-exact reproduction
of the 2026-05 run, and it cannot recover the per-sample split of that run. The ERGO/database
cell (n=25, nothing pruned, published 12.0) is the positive control for comparability.

---

## Pre-flight (before any API call)

| check | result |
|---|---|
| `.venv` present, `ctx-editor` on PATH | yes |
| TRAPI auth (`api://trapi/.default` via `DefaultAzureCredential`) | token acquired OK |
| Hydra dry-run (`--cfg job`) of the ERGO/math command | resolves; `execution.replay_source=data/baseline_traces_v2/math`, `replay_turns=1`, `false_negative_analysis.model=gpt-5.4-mini_2026-03-17` all present |
| `outputs/T18/` collision with concurrent agents | dir does not exist; T18-scoped |
| **Trap 4 — is `seed=` live on LiC?** | **No.** `grep -rn seed src/ctx_editor/**/*.py`: `cfg.seed` is read only by `run_collabllm.py:110` and `huang_eval/run_phase{1,2}.py`. `run_experiment.py` (the LiC entry point) never reads it. Tonight's dispatcher fix landed in `run_collabllm.py`, **not** in the LiC path. → any replicate here is a "replicate run at temperature 1.0", not a seeded run. Logged, no reliance on `seed=`. |

### Pool sizes / sidecars (re-verified on disk, not taken from T17)

| task | pool dir | files | sidecar | pruned | expected filtered n |
|---|---|---|---|---|---|
| math | `data/baseline_traces_v2/math` | 23 | `math_false_negatives.json` | 3 (`sharded-GSM8K/{1287,267,534}`) | **20** |
| code | `data/baseline_traces_v2/code` | 25 | `code_false_negatives.json` | 6 | **19** |
| database | `data/baseline_traces_v2/database` | 25 | `database_false_negatives.json` | 0 | **25** |
| actions | `data/baseline_traces/actions` | 25 | **none exists** | 0 | **25** (paper's 23 is the ad-hoc "common-23" normalisation, no artifact — T17 §1a) |

20 + 19 + 25 + 25 = 89 replays (T17 said 87, assuming actions n=23; there is no sidecar to
make that fire, so actions will run at 25 and is reported at n=25 raw).

---

## Log

### 16:2x — launched
Commands (run sequentially, database first as the positive control):

```bash
ctx-editor experiment=ergo model=gpt5_4_mini_trapi load_balancer=trapi \
  task=<TASK>_v2 \
  execution.replay_source=<POOL> execution.replay_turns=1 \
  execution.max_concurrent=5 \
  false_negative_analysis.model=gpt-5.4-mini_2026-03-17 \
  experiment_name=T18_ergo_<TASK> logging.output_dir=outputs/T18/ergo_<TASK>
```

(status: running — results appended below as each task lands)
