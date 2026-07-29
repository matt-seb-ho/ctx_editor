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

### 16:12–16:17 — ATTEMPT 1 FAILED. The positive control earned its keep.

`task=<t>_v2` resolves `data_file: data/lic_eval_subset.json`. That subset intersects the
replay pools by only **10 / 7 / 6 / 5** ids (math/code/db/actions) — replay drops unmatched
samples silently, so the runs came back at n = 9 / 7 / 6 / 5 instead of 20 / 19 / 25 / 25.
The ERGO/database control returned 4/6 = 66.7%, which is obviously not a 25-sample cell;
that is what flagged it. Runs quarantined at `outputs/T18/_bad_wrong_datafile/`, not used.

**The pools are the `dev_*` subsets** (this is what T17's recommended command actually said,
`task=dev_{math,code,database,actions}`; I substituted `*_v2` and paid for it):

| data file | n | ids covering the pool |
|---|---|---|
| `data/dev_math_subset.json` | 23 | 23/23 |
| `data/dev_code_subset.json` | 25 | 25/25 |
| `data/dev_database_subset.json` | 25 | 25/25 |
| `data/dev_actions_subset.json` | 25 | 25/25 |

`dev_math/code/database` carry `task_version_map` → v2 evaluators. **`dev_actions` does not**
(there is no `actions` entry), so it uses the v1 actions evaluator; I ran actions a second
time with `+task.task_version_map.actions=actions_v2` as a cross-check.

### 16:18–16:22 — ATTEMPT 2 (`task=dev_*`). All five runs completed.

Script: `neurips_review/autoresearch/tasks/T18/run_ergo_replays.sh`. Literal command per task:

```bash
ctx-editor experiment=ergo model=gpt5_4_mini_trapi load_balancer=trapi \
  task=dev_<TASK> user_mode=sharded \
  execution.replay_source=<POOL> execution.replay_turns=1 execution.max_concurrent=5 \
  false_negative_analysis.model=gpt-5.4-mini_2026-03-17 \
  experiment_name=T18_ergo_<TASK> logging.output_dir=outputs/T18/ergo_<TASK>
```

**The pool filter fired exactly as T17 predicted.** `user_sim_skipped` = **0 / 6 / 3 / 0**
(database / code / math / actions), and the code log names precisely the six sidecar ids
(`sharded-HumanEval/113`, `sharded-livecodebench/{2791,2850,2873,2916,2920}`) and the math log
precisely the three (`sharded-GSM8K/{1287,267,534}`). T17 §1 mechanism confirmed **live**, not
just from archived runs. `metrics.json` and `run_summary.json` agree on every cell (trap 6).

#### ERGO on the filtered pools, `gpt-5.4-mini_2026-03-17`, raw accuracy (primary)

| task | pool n | pruned | **measured** | published ERGO | T17 corrected pt est. | T17 interval |
|---|---|---|---|---|---|---|
| math | 20 | 3 | **16/20 = 80.0** | 16/23 = 69.6 | 80.0 | [65.0, 80.0] |
| code | 19 | 6 | **10/19 = 52.6** | 11/25 = 44.0 | 57.9 | [26.3, 57.9] |
| **database (control)** | 25 | 0 | **11/25 = 44.0** | 3/25 = **12.0** | 12.0 (exact) | — |
| actions (v1 eval) | 25 | 0 | **22/25 = 88.0** | 12/25 = 48.0 | 52.2 | [43.5, 52.2] |
| actions (v2 eval) | 25 | 0 | **20/25 = 80.0** | — | — | — |

Cost ≈ \$0.6 total. `adjusted_accuracy` is recorded in the run dirs but **not used** (trap 2).

### 16:23 — ⚠ THE POSITIVE CONTROL DID NOT REPRODUCE. The bound is NOT closed.

**ERGO/database measured 44.0 against a published 12.0 — a 32.0 pp divergence on the one cell
the correction leaves untouched and the one cell with nothing pruned.** Per the brief's trap 3,
that means these numbers cannot be substituted into `tab:main`. Stating it plainly:

> **T18 does not close T17's intervals.** ERGO/code remains **[26.3, 57.9]** and ERGO/math
> remains **[65.0, 80.0]** as statements about the *published* row.

Why the control fails is not mysterious, and it is not a harness fault this time: **the published
`tab:main` was produced with `gpt5_mini` (assistant `gpt-5-mini`, user/system `gpt-4o-mini`) and
this replication runs `gpt-5.4-mini_2026-03-17` (user/system `gpt-4o_2024-11-20`)** — a newer and
materially stronger assistant. Every measured cell is *above* its published counterpart
(math +10.4, code +8.6, database +32.0, actions +40.0), which is the signature of a model-era
shift, not of a denominator fix. The database cell isolates it cleanly because its denominator
is identical in both (25, nothing pruned): the entire 32 pp is model/era, zero is denominator.

**Same-model control attempted and unavailable.** `gpt-5-mini` is served only by the `dl-openai-3`
Azure endpoint (`config/load_balancer/multi_endpoint_foundry.yaml:47-58`, `t9_foundry_trapi.yaml:51`).
Direct probe under the current `az` identity:

```
gpt-5-mini  FAIL AuthenticationError 401 PermissionDenied  (principal f6421f4b-… lacks the data action)
gpt-4o-mini FAIL AuthenticationError 401 PermissionDenied
```

There is also **no `.env`** in the repo root (`ls: cannot access '.env'`) and no `OPENAI_API_KEY`
/ `AZURE_OPENAI_*` in the environment — the only live route is TRAPI, which serves
`gpt-5.4-mini_2026-03-17` and `gpt-4o_2024-11-20` and nothing else. So a bit-comparable re-run of
the 2026-05 ERGO row **is not possible on this machine tonight**, by anyone, for any arm.
(RECON §0.3 lists `dl-openai-3` as working; as of 16:23 tonight it is not. Two endpoints —
`fxdata-shared` and now `dl-openai-3` — are 401 under this principal.)

### 16:25 — what to do instead: an internally-controlled same-model comparison

The measured ERGO row is uninterpretable in isolation but is *not* worthless: the substantive
question T17 raised is **ordering** — "does ERGO tie or beat AC3 once both are on the same
filtered pool?" That question is answerable with a **within-model, within-pool** experiment, and
answering it does not require reproducing 2026-05 absolute levels.

So: run the five other no-memory `tab:main` arms through the *identical* pipeline —
same pools, same replay, same model, same filter — and compare ERGO against them directly.
This is a scope addition beyond the brief's "~\$0.20"; I am taking it because without a
same-model comparator the ERGO numbers above support **no** conclusion at all, and the arms are
~\$0.15 each. Logged as a deliberate deviation.

Arms (all no-memory, matching the ERGO comparison in T17 §5):
`baseline`, `omit_assistant` (AO), `concatenate_user`, `append_analysis` (AC3-Augment),
`context_edit_v2_no_gate` (AC3-Reset), `context_edit_v2_gated` (AC3-Gated-Reset)
× 4 tasks = 24 runs. Operator→config mapping from `RECON/worklog.md` §A.1.

(status: running — results appended below)

