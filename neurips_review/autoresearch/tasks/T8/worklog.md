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

## 5. Per-replicate raw results

_(filled in as cells complete — see §6 for the paste-ready table)_

---

## 6. Paste-ready table

_(pending)_
