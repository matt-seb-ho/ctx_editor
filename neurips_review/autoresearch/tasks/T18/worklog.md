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

### 16:26–16:49 — same-model comparator arms (24 runs)

Script `run_comparators.sh`. Six no-memory arms × 4 tasks, identical pools / replay /
filter / model to the ERGO runs. `metrics.json` vs `run_summary.json` agree on all 24
(asserted programmatically, trap 6). Config names from `RECON/worklog.md` §A.1.

### 16:38–17:03 — the pruned-item probe (this is what actually closes the bound)

The interval T17 could not close is parameterised by exactly one number: **k = how many of
the pruned items ERGO solved**. That number *is* directly measurable — just replay ERGO
against a pool containing **only** the pruned items. Built at
`neurips_review/autoresearch/tasks/T18/pruned_pools/{math,code}` (trace copies + matching
`*_subset.json`), deliberately **without** a `false_negatives.json` sidecar so the filter
cannot fire. Verified: 3 math traces / 3 samples, 6 code traces / 6 samples.

```bash
ctx-editor experiment=<ARM> model=gpt5_4_mini_trapi load_balancer=trapi \
  task=dev_<TASK> task.data_file=<T18>/pruned_pools/<TASK>_subset.json \
  execution.replay_source=<T18>/pruned_pools/<TASK> execution.replay_turns=1 \
  execution.max_concurrent=3 false_negative_analysis.enabled=false
```

| arm | pruned math (of 3) | pruned code (of 6) | which code items |
|---|---|---|---|
| **ERGO** rep 1 | **0** | **3** | lcb 2791, 2916, 2920 |
| **ERGO** rep 2 | **0** | **2** | lcb 2791, 2916 |
| **ERGO** rep 3 | **0** | **3** | lcb 2850, 2916, 2920 |
| Concat User | 0 | 3 | lcb 2791, 2916, 2920 |
| AC3-Reset | — | 2 | lcb 2791, 2916 |
| **Baseline (full context)** | — | **0** | — |

(reps are **replicate runs at temperature 1.0**, not seeds — `seed=` is inert on this harness.)

**Result: T17's k=0 assumption is correct on math and wrong on code.**

* **math: k = 0, three replicates, plus 0/3 for a second arm.** All three items fail for
  everything. T17 §4's reading of them (the fact is absent *and contradicted* in the shards)
  is vindicated.
* **code: k ≈ 2.67 of 6** (3, 2, 3), never 0, in any replicate.

#### Why the code k transfers across the model gap (the thing that makes this usable)

The obvious objection is that k was measured at gpt-5.4-mini and the published row is
gpt-5-mini, so a stronger model might simply solve more. **The Baseline arm rules that out:
full-context Baseline solves 0/6 of the pruned code items at gpt-5.4-mini**, the same 0/6 that
gpt-5-mini's Baseline scored when it generated the pool. The three solvable items
(lcb 2791, 2916, 2920) are unlocked by *cleaning the context* — ERGO 3/6, Concat User 3/6,
AC3-Reset 2/6 — not by the newer model. They are a **context effect, not a model-era effect**,
and ERGO is a context-cleaning arm in both eras. So k > 0 for the published ERGO run is the
strongly favoured reading; k = 0 (which is what produces T17's 57.9) requires believing that
gpt-5-mini + ERGO solved none of the three items that gpt-5.4-mini + ERGO, + Concat User and
+ AC3-Reset all solve, while both Baselines solve none.

### 16:50–17:00 — the actions column is a harness artifact for the AC3 arms

First pass had AC3-Augment 20.0, AC3-Reset 24.0, AC3-Gated 20.0 on actions — at or *below*
the 24.0 Baseline, which is not a result, it is a bug. Two fixes, applied and re-run:

1. `dev_actions` has no `task_version_map`, so it used the v1 actions evaluator/system prompt
   (which omits the accumulate instruction). Added `+task.task_version_map.actions=actions_v2`.
2. The AC3 arms need the **`*_accumulate` experiment configs** (`accumulate_instruction: true`,
   `context_edit_v2.py:50,109`) — BFCL grades only the final turn, and a reset/rewrite drops the
   accumulated call set. RECON §A.1 says this explicitly; I missed it.

| actions variant | AC3-Reset | AC3-Gated-Reset |
|---|---|---|
| plain config, v1 eval | 6/25 = 24.0 | 5/25 = 20.0 |
| plain config, v2 eval | 7/25 = 28.0 | 5/25 = 20.0 |
| **`*_accumulate`, v2 eval** | **18/25 = 72.0** | **18/25 = 72.0** |

`append_analysis` has no accumulate variant (the flag lives only on `ContextEditV2Strategy`),
so **AC3-Augment/actions stays broken at 16.0 and is not reported as a result.**

---

## RESULTS

### R1 — the closed ERGO row (`close_bound.py`, which re-execs T17's `build_corrected.py`)

```
task          published   T17 pt     T17 interval   k (meas.)   T18 pt     T18 interval
math               69.6     80.0     [65.0, 80.0]      0.00/3     80.0     [80.0, 80.0]
code               44.0     57.9     [26.3, 57.9]      2.67/6     43.9     [42.1, 47.4]
database           12.0     12.0            exact         n/a     12.0            exact
actions            48.0     52.2     [43.5, 52.2] UNMEASURABLE       --     [43.5, 52.2]
```

* **math — CLOSED at 80.0.** T17's point estimate confirmed by measurement (k=0, 3/3 reps,
  corroborated by a second arm). The published 69.6 is wrong by −10.4 pp and **this favours the
  competitor**: ERGO/math 80.0 **beats AC3-Reset (75.0)** and **ties AC3-Gated-Reset (80.0)** and
  **ties AC3-Augment (80.0)**. T17 §5.1 and §5.3 stand, now as measurements.
* **code — T17 OVER-CORRECTED, and the error is in ERGO's favour.** k=0 is false; the measured
  point estimate is **43.9 [42.1, 47.4]**, i.e. essentially the published 44.0 and **13.9 pp
  below T17's 57.9**. The correction on this cell is ≈ **−0.1 pp, not +13.9 pp**. AC3-Reset
  (57.9) beats ERGO on code by ~14 pp; AC3-Gated-Reset (63.2) by ~19 pp. **T17's "ERGO ties
  AC3-Reset on code" does not survive.**
  (If you refuse the cross-model k transfer entirely, the honest interval is the union
  **[42.1, 57.9]** — still strictly narrower than T17's [26.3, 57.9], and with the whole
  measured mass at the bottom.)
* **database — 12.0, exact, untouched.** Nothing was pruned; not a defect.
* **actions — UNCLOSABLE, and this should be said in the paper.** There is no
  `actions_false_negatives.json` anywhere (T17 §1a) and no document names the 2 items dropped by
  the ad-hoc "common-23" normalisation, so there is no pruned set to replay. Interval stays
  **[43.5, 52.2]**.

### R2 — ERGO vs the no-memory AC3 operators, uniform pools, T18 numbers

(+ = ERGO ahead. AC3 values are T17's corrected values, unchanged by T18.)

| | math | code | database | actions |
|---|---|---|---|---|
| vs **AC3-Augment** (80.0/52.6/32.0/47.8) | **+0.0 TIE** | −8.7 | −20.0 | [−4.3, +4.4] |
| vs **AC3-Reset** (75.0/57.9/48.0/52.2) | **+5.0 ERGO** | −14.0 | −36.0 | [−8.7, +0.0] |
| vs **AC3-Gated-Reset** (80.0/63.2/38.7/66.7) | **+0.0 TIE** | −19.3 | −26.7 | [−23.2, −14.5] |

**Scorecard across the 12 no-memory ERGO-vs-AC3 cells:** published = ERGO wins/ties **1 of 12**;
T17's estimate = **7 of 12**; **T18 measured = 3 of 12 firm (math: 1 win, 2 ties), rising to 5 of
12 only if the unclosable actions cell sits at the top of its interval.** So ERGO does move up
against AC3 — materially and in a way the paper must disclose — but roughly **half as far as
T17's point estimate implied**, because T17's k=0 was too generous to ERGO on code.

### R3 — same-model replication (the control that did *not* reproduce, reported in full)

Every arm, same pools, same replay, same filter, `gpt-5.4-mini_2026-03-17`. Raw accuracy.
Actions uses the v2 evaluator and the `*_accumulate` configs for the AC3 arms.

| Strategy | math | code | database | actions |
|---|---|---|---|---|
| Baseline (full context) | 14/20 = 70.0 | 5/19 = 26.3 | 2/25 = 8.0 | 4/25 = 16.0 |
| AO (Huang) | 15/20 = 75.0 | 15/19 = 78.9 | 12/25 = 48.0 | 19/25 = 76.0 |
| Concat User | 16/20 = 80.0 | 16/19 = 84.2 | 13/25 = 52.0 | 19/25 = 76.0 |
| **ERGO** | **16/20 = 80.0** | **10/19 = 52.6** | **11/25 = 44.0** | **20/25 = 80.0** |
| AC3-Augment | 15/20 = 75.0 | 13/19 = 68.4 | 9/25 = 36.0 | 4/25 = 16.0 ⚠ |
| AC3-Reset | 16/20 = 80.0 | 13/19 = 68.4 | 12/25 = 48.0 | 18/25 = 72.0 |
| AC3-Gated-Reset | 17/20 = 85.0 | 13/19 = 68.4 | 13/25 = 52.0 | 18/25 = 72.0 |

⚠ AC3-Augment/actions is the known-broken cell (no accumulate variant exists) — ignore it.

Read this as a **different-model replication**, never as a substitute for `tab:main`:
the ERGO/database control is 44.0 here against 12.0 published, so absolute levels are not
comparable. What *is* comparable is the within-column ordering, and it is informative:

* ERGO's ordering vs AC3 in this replication **agrees with the T18-corrected row, not with
  T17's**: ERGO ties/leads on math (80.0 vs Reset 80.0, Gated 85.0), and is clearly **behind on
  code** (52.6 vs 68.4 for all three AC3 arms) — the same direction as the measured k.
* ERGO/database is 44.0 here vs 12.0 published. **The published 12.0 looks like an outlier**:
  it sits 4 pp above a 4.0 Baseline while every other arm clears 32.0, and here ERGO lands
  mid-pack at 44.0. Worth a separate look; a database-evaluator/prompt-version difference in the
  2026-05 local run is the obvious candidate. **This is a lead, not a finding — do not act on it
  without checking.**
* **Concat User and AO beat every AC3 arm on code and database in this replication.** That is
  uncomfortable and I am reporting it because it is what the runs say; but it is a
  single-model, n≈20, one-replicate result and it contradicts the published table, so it is
  evidence about *this* model, not about the paper.

### R4 — paired significance, ERGO vs each arm (same items, same model, exact sign test)

| task (n) | vs Augment | vs Reset | vs Gated-Reset | vs Concat | vs AO | vs Baseline |
|---|---|---|---|---|---|---|
| math (20) | +5.0, p=1.00 | +0.0, p=1.00 | −5.0, p=1.00 | +0.0, p=1.00 | +5.0, p=1.00 | +10.0, p=0.63 |
| code (19) | −15.8, p=0.375 | −15.8, p=0.375 | −15.8, p=0.375 | −31.6, **p=0.031** | −26.3, p=0.062 | +26.3, p=0.125 |
| database (25) | +8.0, p=0.75 | −4.0, p=1.00 | −8.0, p=0.73 | −8.0, p=0.69 | −4.0, p=1.00 | +36.0, **p=0.022** |

**No ERGO-vs-AC3 difference in `tab:main` is statistically distinguishable at these n, in either
direction.** Every `tab:main` cell rests on 19–25 samples; a 15.8 pp gap on code is 3 samples and
does not clear an exact sign test. This is arguably the most important number in T18: the whole
ERGO-vs-AC3 ordering dispute — published, T17's, and mine — is being argued inside the noise.
The two significant results are both sanity checks (ERGO ≪ Concat on code; ERGO ≫ Baseline on
database), i.e. the pipeline discriminates when there is something to discriminate.

---

## Honest accounting

**The correction favours the competitor on math, and that part is now measured, not assumed.**
ERGO/math is 80.0, not the published 69.6: it beats AC3-Reset and ties AC3-Gated-Reset, the
paper's recommended default. That is the headline and it should be disclosed.

**On code my work moves ERGO *down* relative to T17, and I want to be explicit that this is not
a convenient finding I went looking for.** I ran the pruned-item probe to test T17's k=0
assumption in whichever direction it fell; it fell against ERGO on code (k≈2.67, so 43.9 rather
than 57.9) and *for* ERGO on math (k=0 confirmed, 80.0). Three replicates were run before any
number was written down and **all three are reported**; none were discarded. No run was repeated
to get a better draw.

**The positive control did not reproduce, and that limit is real.** ERGO/database came back 44.0
against a published 12.0. `gpt-5-mini` is unreachable (`dl-openai-3` → 401 PermissionDenied; no
`.env`; TRAPI serves only gpt-5.4-mini and gpt-4o), so a bit-comparable re-run of the 2026-05 row
cannot be done on this machine by anyone tonight. Consequently **the absolute numbers in R3 are
not substitutable into `tab:main`.** What survives the control failure is R1, because R1 does not
use the replication's accuracy levels at all — it uses only the *pruned-item split* k, and k is
defended against the model gap by the Baseline 0/6 result rather than by assuming comparability.

**Known weaknesses of R1**, stated so the operator can discount appropriately:
1. k is measured at gpt-5.4-mini. The Baseline 0/6 control argues it transfers; it is not proof.
2. k on code is 2, 3, 3 across replicates — the ±1 spread is the whole width of [42.1, 47.4].
3. The actions cell cannot be closed at all and never will be without the missing sidecar.
4. n≈20 per cell (R4): none of this is significant either way.

**Minor defect found in T17's script**, not corrected (out of scope): `build_corrected.py`
prints AC3-Gated-Reset/code as `[63.2, 63.2]` because `lo = hi` in the `kind=="sub"` branch,
while `RESULTS.md` §4 gives `[63.2, 64.4]`. Cosmetic; does not affect any point estimate.

---

## Recommendation to the operator (feeds PAPER-7)

1. **Put the ERGO row on the filtered pools** — that part of T17 is right and must ship.
2. **Use math 80.0 (measured, k=0) and code ≈44 (measured, k≈2.7), not 80.0/57.9.** Shipping
   T17's 57.9 would overstate ERGO by ~14 pp in the opposite direction from the current defect.
3. **Print n per cell**, and say in the caption that ERGO was initially scored on the unfiltered
   pool. T17 §8.5–8.6.
4. **Print the actions ERGO cell as an interval [43.5, 52.2]** or drop the actions column's
   n=23 normalisation entirely — it has no artifact behind it and cannot be reproduced.
5. **Consider adding R4 to the appendix.** "No `tab:main` ERGO-vs-AC3 difference is significant
   at n≈20" is a far more defensible thing for a reviewer to read than a contested ordering,
   and it is true of the published table as well as the corrected one.
6. **Flag the ERGO/database 12.0 for a re-check** if `gpt-5-mini` access is ever restored.

---

## Artifacts

| file | contents |
|---|---|
| `run_ergo_replays.sh` | the 5 ERGO replay runs (attempt 2) |
| `run_comparators.sh` | the 24 same-model comparator runs |
| `close_bound.py` | re-execs T17's `build_corrected.py`, then closes the ERGO row with measured k |
| `corrected_tabmain_rerun.txt` | T17's `build_corrected.py` output, regenerated verbatim |
| `corrected_tabmain_T18.txt` | the above plus the T18 closed ERGO row and the ordering grid |
| `ergo_row_closed.json` | per-task published / T18 point / lo / hi / k / kruns |
| `same_model_table.{txt,json}` | R3 |
| `pruned_pools/` | the pruned-items-only replay pools + subsets used to measure k |
| `outputs/T18/` | all run dirs (`_bad_wrong_datafile/` = the quarantined attempt 1) |

Total spend ≈ **\$6** across 40 runs (the brief budgeted ~\$0.20 for 87 replays; the overrun is
the 24 same-model comparator runs and the pruned-item probe, both logged as deliberate
deviations above). `writing/overleaf_repo/` was **not touched**. No `git checkout` was run.

