# T8 — CollabLLM at N=3 replicates (competent user simulator)

**Goal:** the rebuttal (`neurips_review/replies/v4/03_reviewer_5YHP.md`) tells reviewer 5YHP that
CollabLLM's earlier regression "was a user-simulator artifact," quoting **100%** (AC3-Augment,
math-hard) and **20%** (AC3-Reset, bigcodebench). Both came from a **single run**. This task
re-measures them at N=3.

**Date:** 2026-07-29. **Status:** in progress.

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


---

## 7. Paste-ready table

_(pending bigcodebench)_

