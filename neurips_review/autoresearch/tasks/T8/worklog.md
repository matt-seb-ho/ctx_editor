# T8 — CollabLLM at N=3 replicates (competent user simulator)

**Goal:** the rebuttal (`neurips_review/replies/v4/03_reviewer_5YHP.md`) tells reviewer 5YHP that
CollabLLM's earlier regression "was a user-simulator artifact," quoting **100%** (AC3-Augment,
math-hard) and **20%** (AC3-Reset, bigcodebench). Both came from a **single run**. This task
re-measures them at N=3.

**Date:** 2026-07-29. **Status:** COMPLETE — all 12 cells in hand (4 arms x 3 replicates).
All 8 fresh runs finished 11:17 UTC; bigcodebench re-scored offline under a unified environment.

> **STATUS LINE (11:4x UTC):** all runs complete, no processes outstanding, nothing wedged.
> Remaining work was analysis/write-up only, now finished.


---

## 0. Terminology — these are REPLICATES, not seeds

`seed=` is a **no-op** on the CollabLLM harness (verified, see §4). The loaders hardcoded
`random.Random(42)`, so every "seed" replicate drew the **same 20 problems**; replicate-to-replicate
variation comes only from `temperature: 1.0` decoding (user sim, assistant, and analyzer are all
DeepSeek-V4-Flash at temp 1.0).

**Report these as "3 replicate runs at temperature 1.0", never as "3 seeds."**

The prior Phase-3a Baseline triple of 30.0/30.0/30.0 is the *fingerprint of this bug*, not
evidence of stability.

---

## 1. Load-balancer fix (blocking — applied first)

`fxdata-shared` returns **401 PermissionDenied** for the current identity
(`sc-hy6197645@microsoft.com`), and `multi_endpoint_foundry.yaml` listed `gpt-4o-mini` **only**
there (a quota decision from when the endpoint still worked). `gpt-4o-mini` is the CollabLLM
**judge/extractor** role in `deepseek_v4_flash_user_deepseek.yaml`. Left unfixed, the judge fails.

Applied to `src/ctx_editor/config/load_balancer/multi_endpoint_foundry.yaml` — added
`gpt-4o-mini: 150` to the `dl-openai-3` block (commit `75e15c7`, on `main`).

### Judge verification BEFORE launching the sweep

2-sample smoke run (`outputs/T8/smoke`):

```bash
.venv/bin/python -m ctx_editor.run_collabllm \
  experiment=collabllm_baseline model=deepseek_v4_flash_user_deepseek \
  load_balancer=multi_endpoint_foundry \
  task.name=collabllm_math task.dataset_name=math-hard task.limit=2 \
  execution.max_concurrent=2 experiment_name=T8_smoke \
  logging.output_dir=outputs/T8/smoke
```

Result: `Accuracy: 100.00% (2/2)`, `Interactivity: 1.000`, `Avg Assistant Tokens: 512`, cost $0.0036.

Routing audit of `verbose.log`: **22 hits on `dl-openai-3`, 0 on `fxdata-shared`**; the
`gpt-4o-mini` extractor prompt bodies are present in the request log with real completions.
The 5 grep hits for `401|error` were all HuggingFace CDN 307/403 noise, not judge failures.
**Judge confirmed live.**

---

## 2. Reused replicate 1 — config verification

Recovered from the blob snapshot (extraction per the RECON worklog):

```bash
mkdir -p ~/ac3/recovered
tar -xzf ~/ac3/blob_staging/snapshot.tar.gz -C ~/ac3/recovered \
  ctx_editor/outputs/post_neurips_r2_collabllm_user_deepseek
```

The recovered N=1 cells reproduce the quoted numbers **exactly**:

| Cell | correct/20 | acc |
|---|---|---|
| `collabllm_baseline_math-hard_rep1` | 19/20 | **95%** |
| `collabllm_assistant_omit_math-hard_rep1` | 18/20 | 90% |
| `collabllm_ac3_augment_v8_math-hard_rep1` | 20/20 | **100%** ← the quoted claim |
| `collabllm_baseline_bigcodebench_rep1` | 1/20 | **5%** |
| `collabllm_assistant_omit_bigcodebench_rep1` | 3/20 | 15% |
| `collabllm_ac3_reset_v8_bigcodebench_rep1` | 4/20 | **20%** ← the quoted claim |
| `collabllm_ac3_augment_v8_bigcodebench_rep1` | 3/20 | 15% |
| `collabllm_ac3_reset_v8_math-hard_rep1` | 17/20 | 85% |

**Config match check** (rep1 `config.yaml` vs. my rep2/rep3 invocation) — all four reused cells:

| Field | rep1 | my reps | match |
|---|---|---|---|
| strategy `_target_` | `AppendAnalysisStrategy` / `ContextEditV2Strategy` / `BaselineStrategy` | same | yes |
| analyzer model / prompt / min_turns / max_resets | DeepSeek-V4-Flash, v8, 4 / 1, 100 | same | yes |
| model config | `deepseek-v4-flash-user-deepseek` (user+asst+ctx_editor = DeepSeek-V4-Flash, system = gpt-4o-mini) | same | yes |
| task limit / max_turns / dataset | 20 / 14 / math-hard, bigcodebench | same | yes |
| `seed` | 43 | 42 (default) | **irrelevant — no-op, same 20 problems** |
| `execution.max_concurrent` | 15 | 5 | differs, no effect on sampling semantics |

**Verdict: rep1 is reusable as replicate 1** for all four arms. Only `max_concurrent` differs, which
affects wall-clock scheduling only, not the conversation distribution.

### Analysis-cache contamination check

Rep1 configs set `analysis_cache_dir: outputs/analysis_cache`. A cache hit would make replicates
share analyzer outputs and **artificially suppress variance in exactly the arms we care about**.

- The on-disk cache holds **708 entries, all `analyzer_model=gpt-5.4-mini_2026-03-17`**. Our
  analyzer is `DeepSeek-V4-Flash`, and `analyzer_model` is part of the cache key
  (`strategies/analysis_cache.py`). So **zero hits** from the pre-existing cache.
- Belt-and-braces: each T8 replicate is given its **own** cache dir
  (`outputs/T8/cache/<tag>`), so no analyzer output is shared *between* replicates either.

---

## 3. The replicate sweep

Driver: `neurips_review/autoresearch/tasks/T8/run_t8.sh` (two streams, `math` and `code`, run in
parallel; cells within a stream run sequentially at `execution.max_concurrent=5`).

8 fresh cells = 4 arms x reps {2,3}. Arms:

| Stream | Arm | `experiment=` | dataset |
|---|---|---|---|
| math | AC3-Augment | `collabllm_ac3_augment_v8` | math-hard |
| math | Baseline | `collabllm_baseline` | math-hard |
| code | AC3-Reset | `collabllm_ac3_reset_v8` | bigcodebench |
| code | Baseline | `collabllm_baseline` | bigcodebench |

Literal per-cell invocation:

```bash
.venv/bin/python -m ctx_editor.run_collabllm \
  experiment=<ARM> \
  model=deepseek_v4_flash_user_deepseek \
  load_balancer=multi_endpoint_foundry \
  task.name=<collabllm_math|collabllm_code> \
  task.dataset_name=<math-hard|bigcodebench> \
  task.limit=20 \
  execution.max_concurrent=5 \
  experiment.strategy.analysis_cache_dir=outputs/T8/cache/<tag> \   # AC3 arms only
  experiment_name=T8_<tag> \
  logging.output_dir=outputs/T8/<tag> \
  metadata.branch=T8_collabllm_n3
```

(`collabllm_baseline`'s `BaselineStrategy` has no `analysis_cache_dir` key, so that override is
omitted for Baseline cells — passing it would be a Hydra struct error.)

Launched 2026-07-29 09:53 UTC.

---

## 4. Is true seeding cheaply fixable? — YES

**Finding:** the per-dataset loaders (`load_collabllm_math_hard`, `load_collabllm_bigcodebench`,
`load_collabllm_medium`) **already accept a `seed: int = 42` kwarg**. The bug is purely in the
dispatcher: `load_collabllm_dataset` neither accepted nor forwarded a seed, and
`run_collabllm.py:106` never passed `cfg.seed`. So it is a genuine **2-line fix**, not invasive.

Applied on branch **`T8_collabllm_true_seed`** (commit `6af5504`), *not* on `main`:

- `data/collabllm_loader.py` — `load_collabllm_dataset` gains `seed: int = 42`, forwards it.
- `run_collabllm.py` — reads `cfg.get("seed", 42)`, passes it, logs the effective `data_seed`.

**Back-compatibility verified:**

```
default draw == seed=42 draw : True      # every pre-2026-07-29 run reproduces bit-for-bit
seed=42 vs seed=1234 identical: False
overlap                       : 0 / 20   # fully disjoint problem draw
```

`main` was left untouched for the duration of the sweep so that every replicate runs identical
code (the seed default is 42 either way, so behaviour would have been unchanged — but keeping the
tree clean removes all doubt).

---

## 5. Failure encountered and resolved: bigcodebench execution scoring

The first `collabllm_ac3_reset_v8_bigcodebench_rep2` run completed all 20 conversations but
reported **`0/0 correct (20 errors excluded)`** — a *silent* metric failure:

```
File "src/ctx_editor/evaluation/collabllm_metrics.py", line 342, in judge_pass_rate
    from bigcodebench.eval import untrusted_check
ModuleNotFoundError: No module named 'bigcodebench'
```

BigCodeBench is scored by **actual test execution** (`eval_method: pass_rate` in
`COLLABLLM_DATASETS` → `judge_pass_rate` → `bigcodebench.eval.untrusted_check`), not by the LLM
judge. The package was absent from the current venv. (This also corrects RECON *Unknown #7*, which
guessed BigCodeBench scoring was LLM-based — it is execution-based and already wired in.)

**Resolution:** killed the code stream immediately (the queued Baseline bigcodebench cell would
have failed identically), installed the package (`uv pip install bigcodebench`), verified
`from bigcodebench.eval import untrusted_check` and that `ctx_editor` still imports, then re-smoked:
`outputs/T8/smoke_bcb` returned `0.00% (0/2)` — i.e. **2 samples actually evaluated, 0 errors
excluded** (vs the earlier `0/0`), consistent with Baseline's 5% in rep1. Deleted the poisoned
cell dirs and relaunched. Failed logs retained as `logs/FAILED_*.log`.

The math stream was unaffected (math-hard uses the LLM judge) and was left running; all four math
cells report the full 20 samples with **no errors excluded** and no tracebacks.

---

## 6. Per-replicate raw results

### math-hard (complete, n=3)

| Arm | rep1 (recovered) | rep2 | rep3 | mean | sd |
|---|---|---|---|---|---|
| **AC3-Augment** | **100.0** (20/20) | 85.0 (17/20) | 90.0 (18/20) | **91.67** | 7.64 |
| **Baseline** | 95.0 (19/20) | 95.0 (19/20) | 85.0 (17/20) | **91.67** | 5.77 |

Per-replicate delta (Augment − Baseline): `[+5, −10, +5]` → **mean 0.00, sd 8.66**.

**The quoted 100% does not replicate.** It is the *top* of the observed range, not its centre.
At n=3 the two arms have **identical** means.

#### Per-problem view (all replicates share the same 20 problems, so this is fully paired)

Total correct across the 3 replicates: **AC3-Augment 55/60, Baseline 55/60 — exactly tied.**

15 of the 20 problems are solved by **both** arms in **all** replicates (a ceiling block). All
variance comes from just 5 unstable problems (`math-hard/1116, 1209, 191, 447, 476`). This is the
context needed to read the sd: math-hard is a near-ceiling benchmark where a 20-problem draw
resolves ~5 problems' worth of decoding noise, i.e. ±5pp granularity per replicate.

### bigcodebench (in progress)

**Second, larger failure — and the reason every bigcodebench number here is *re-scored*.**

After installing `bigcodebench`, `collabllm_ac3_reset_v8_bigcodebench_rep2` ran all 20 samples with
**0 execution errors** and scored **0/20**. That looked like a catastrophic non-replication of the
20% claim. It was an artifact.

`judge_pass_rate` swallows any exception and `return 0.0`. Inside BigCodeBench's sandbox,
`reliability_guard()` does `import matplotlib.pyplot` — and matplotlib was not installed, so **every
test subprocess died and silently scored 0**, while the parent logged only the benign
`test failed for task_func: {}` (the empty `{}` detail is the tell).

**Diagnostic that caught it:** re-score the *recovered rep1* extractions (known stored total 4/20)
under the current environment. It returned **0/20** — proving the environment, not the model, was
producing zeros.

**Fix:** derived the actual dependency set from the 20 problems' own test code rather than guessing
(`bs4, matplotlib, mechanize, numpy, openpyxl, pandas, regex, scipy, seaborn, sklearn, xlwt`) and
installed it. Re-validation against rep1: **19/20 scores now match exactly**, total 5/20 vs stored
4/20. The single difference (`BigCodeBench/451`) is **deterministic** (scored 1.0 on 5/5 repeats),
so it is a *dependency-version* difference, not flakiness — the original 2026-06 environment had a
library version on which 451 failed.

**Consequence for methodology:** the historical bigcodebench numbers were produced under a
materially different dependency environment. Comparing a fresh replicate against them directly
would confound model behaviour with library versions. So **every bigcodebench cell — including the
recovered rep1 — is re-scored offline under one unified current environment**, and it is those
re-scored numbers that are reported. `results.json` stores `extracted_answer` per sample, so
re-scoring needs no re-run of any conversation. Script: `/tmp/rescore_bcb.py`.

Under the unified scorer, rep1's Reset cell is **5/20 (25%)**, not the 20% quoted in the rebuttal —
i.e. the quoted figure is itself environment-dependent by ±1 problem (±5pp).

#### bigcodebench results (all cells re-scored under the unified environment)

| Arm | rep1 (recovered) | rep2 | rep3 | mean | sd |
|---|---|---|---|---|---|
| **AC3-Reset** | 5/20 = **25.0** | 5/20 = **25.0** | 3/20 = **15.0** | **21.67** | 5.77 |
| **Baseline** | 2/20 = **10.0** | 2/20 = **10.0** | 0/20 = **0.0** | **6.67** | 5.77 |

Per-replicate delta (Reset − Baseline): `[+15, +15, +15]` → **mean +15.00, sd 0.00**.
Reset beats Baseline in **3/3 replicates**, by the same margin every time.

In-run vs re-scored scores per cell (shows which cells the matplotlib bug touched):

| Cell | in-run (unreliable) | re-scored (authoritative) |
|---|---|---|
| Reset rep1 (recovered, 2026-06 env) | 4/20 | 5/20 |
| Reset rep2 | 0/20 (matplotlib bug) | 5/20 |
| Reset rep3 | 3/20 | 3/20 |
| Baseline rep1 (recovered, 2026-06 env) | 1/20 | 2/20 |
| Baseline rep2 | 1/20 | 2/20 |
| Baseline rep3 | 0/20 | 0/20 |

#### Per-problem view — bigcodebench (fully paired; same 20 problems everywhere)

Total across the 3 replicates: **Reset 13/60, Baseline 4/60.**

**14 of the 20 problems are never solved by either arm in any replicate** — a hard floor. All signal
lives in 6 problems. Reset solves `209, 285, 563` (2 reps each) and `447, 54, 61` (1 rep each) —
**9 solves on problems Baseline never solves once**. The three problems Baseline does solve
(`228, 451, 859`) are also solved by Reset. **There is no problem that Baseline solves and Reset
does not.** Baseline rep3's 0/20 is a genuine floor reading, not an error.

---

## 7. Paste-ready table

**CollabLLM, competent user simulator (DeepSeek-V4-Flash as user + assistant + analyzer;
gpt-4o-mini as judge/extractor). N = 3 replicate runs at temperature 1.0 on a fixed 20-problem
draw — these are replicates, NOT seeds (`seed=` is a no-op; see §0/§4).**

| Arm | Dataset | rep1 | rep2 | rep3 | mean ± sd | n | Artifact path |
|---|---|---|---|---|---|---|---|
| Baseline | math-hard | 19/20 (95.0) | 19/20 (95.0) | 17/20 (85.0) | **91.7 ± 5.8** | 3 | `outputs/T8/collabllm_baseline_math-hard_rep{2,3}`; rep1 `~/ac3/recovered/ctx_editor/outputs/post_neurips_r2_collabllm_user_deepseek/collabllm_baseline_math-hard_rep1_1779092497` |
| **AC3-Augment** | math-hard | 20/20 (100.0) | 17/20 (85.0) | 18/20 (90.0) | **91.7 ± 7.6** | 3 | `outputs/T8/collabllm_ac3_augment_v8_math-hard_rep{2,3}`; rep1 `.../collabllm_ac3_augment_v8_math-hard_rep1_1779095798` |
| Baseline | bigcodebench | 2/20 (10.0) | 2/20 (10.0) | 0/20 (0.0) | **6.7 ± 5.8** | 3 | `outputs/T8/collabllm_baseline_bigcodebench_rep{2,3}`; rep1 `.../collabllm_baseline_bigcodebench_rep1_1779092497` |
| **AC3-Reset** | bigcodebench | 5/20 (25.0) | 5/20 (25.0) | 3/20 (15.0) | **21.7 ± 5.8** | 3 | `outputs/T8/collabllm_ac3_reset_v8_bigcodebench_rep{2,3}`; rep1 `.../collabllm_ac3_reset_v8_bigcodebench_rep1_1779092497` |

**Deltas vs. paired Baseline:** math-hard AC3-Augment **0.0 ± 8.7 pp** (per-rep `+5, −10, +5`);
bigcodebench AC3-Reset **+15.0 ± 0.0 pp** (per-rep `+15, +15, +15`; wins 3/3).

**Precision caveat — state this, don't let reviewers infer false precision.** Every cell is n = 20,
so accuracy is **quantised to 5pp**; one problem flipping moves a cell by a full 5 points. All
bigcodebench cells are re-scored under a single unified dependency environment, because the
original 2026-06 environment differed by ±1 problem (`BigCodeBench/451`) — which is exactly why the
quoted "20%" reads as 25% here. Treat both the quoted 20% and this 21.7% as "≈1 in 5, ±1 problem."

**Ceiling / floor flags:**
- math-hard is **near ceiling**: 15/20 problems are solved by both arms in all replicates. The
  sd's (5.8–7.6) come from ~5 unstable problems only.
- bigcodebench is **near floor**: 14/20 problems are never solved by anyone. Baseline rep3 = 0/20
  is a true floor reading. `sd = 0.00` on the bigcodebench delta is **not** the degenerate
  zero-variance artifact seen in the old Phase-3a 30.0/30.0/30.0 triple (which was the fixed-draw
  seed bug) — here the two arms' per-replicate scores move together across replicates while
  preserving a constant 3-problem gap.

#### Environment soundness check — canonical solutions

Because a broken sandbox silently scores 0 (§6), I bounded the environment by scoring each
problem's own **ground-truth solution** (`single_turn_completion`) against its own tests:

| draw | canonical solutions passing | failing |
|---|---|---|
| seed=42 (our main 20 problems) | **19/20** | `501` |
| seed=1234 (bonus draw) | **18/20** | `201`, `35` |

For the main results this is reassuring: only `BigCodeBench/501` is unscoreable in this
environment, it is **never solved by either arm in any replicate**, and it penalises both arms
identically. The effective bigcodebench ceiling here is therefore 19/20, and the Reset-vs-Baseline
comparison is unaffected. This check is the recommended pre-flight before any future bigcodebench
run — it distinguishes "the model failed" from "the sandbox is missing a library."


---

## 8. Verdict on the rebuttal claims

| Rebuttal claim (`replies/v4/03_reviewer_5YHP.md`) | N=1 quoted | N=3 measured | Survives? |
|---|---|---|---|
| AC3-Augment reaches **100%** on math-hard | 100.0 | **91.7 ± 7.6** (Baseline 91.7 ± 5.8) | **NO** |
| AC3-Reset reaches **20%** on bigcodebench | 20.0 | **21.7 ± 5.8** (Baseline 6.7 ± 5.8) | **YES** |

1. **The 100% math-hard figure does not replicate.** It is the top of the observed range, and at
   n=3 AC3-Augment and Baseline are **exactly tied** (91.67 vs 91.67; 55/60 vs 55/60 problem-solves;
   mean delta 0.0). The rebuttal currently reads as if Augment (100) beats Baseline (95) — that
   +5pp gap is decoding noise on a near-ceiling benchmark. **This sentence needs correcting before
   submission.** The honest statement is that on math-hard with a competent user simulator,
   AC3-Augment **matches** Baseline — which still refutes the *regression* reviewer 5YHP was
   pointing at (no arm degrades), but does **not** support a claimed improvement.
2. **The 20% bigcodebench figure replicates and is the stronger result than we claimed.** Reset is
   21.7 ± 5.8 vs Baseline 6.7 ± 5.8, **+15pp in every replicate, 3/3 wins**, and it solves 9
   problem-instances Baseline never solves while losing none. This claim is safe to lead with.



---

## 7. Paste-ready table

_(pending bigcodebench)_

