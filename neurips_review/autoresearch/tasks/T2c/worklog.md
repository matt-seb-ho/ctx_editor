# T2c — Is the analyzer auditing the context, or just re-solving the task?

**Reviewer prompt:** 5YHP's mechanism challenge. Skeptical reading: AC3's analyzer solves the
task itself and leaks the answer into the rewritten context, making AC3 an expensive ensemble
rather than a context-editing method.

**Status:** in progress (2026-07-29 overnight session).
**Operator asleep — no questions asked; all ambiguity resolved here.**

---

## 1. What is actually logged (schema archaeology)

Checked first, before designing anything, as instructed.

### Run dir layout
```
<run_dir>/
  config.yaml  experiment.log  false_negatives.json  metrics.json
  results.json  run_summary.json  summary.txt  verbose.log
  traces/<task>/<strategy>/<sample_id>.json
```

`results.json` is a list of per-sample records: `sample_id, is_correct, score, num_turns,
extracted_answer, metadata.{full_spec_q, ground_truth_a}, usage_stats`. **No analyzer text.**

`traces/<task>/<strategy>/<sample>.json` **does** carry the analyzer text, in
`trace.logs[]`. Log types observed on an AC3-Reset run:

| `type` | `data` keys |
|---|---|
| `shard_revealed` | `shard_id` |
| `verification` | `response_type`, `is_answer_attempt` |
| `conversation_analysis` | `user_intent`, `aligned`, `issues`, `needs_edit`, `analyzer_model` |
| `edit_decision` | `should_edit` |
| `context_edit_output` | `edited_context`, `analyzer_model`, `original_turn_count`, `active_turn_count` |
| `conversation_reset` | `label`, `new_message_count`, `total_resets` |
| `answer_evaluation` | `extracted_answer`, `is_correct`, `score` |

So **analyzer output is fully persisted per turn**, and so is the exact text that was
injected into the assistant's context. No re-runs needed. This is the single most important
finding for the feasibility of T2c.

### Two distinct units of "analyzer output"
1. **`conversation_analysis`** — every analyzer invocation, including turns where
   `needs_edit=false` and *nothing was injected*.
2. **`context_edit_output.edited_context`** — the text actually placed in the assistant's
   context. For AC3-Reset this is literally a template of
   `<task_spec>` (= `user_intent`) + `<aligned>` + `<issues>`.

**Decision D1.** The causally relevant unit for the "AC3 is an ensemble" charge is (2): a leak
that is never injected cannot help the assistant. But the base-rate question ("what fraction of
analyzer outputs leak at all") is about (1). I report **both**, and use (2) for the
paired accuracy split. Since (2) is a deterministic function of (1)'s fields, one classifier
call per `conversation_analysis` record covers both — I tag each record with whether it was
injected.

### What the analyzer can see
`strategies/prompts/analyzer_v8_*.txt`: the analyzer is given only the **system message** and
the **conversation so far**. It never sees `ground_truth_a`. So it is information-equivalent to
the assistant — any answer it states it had to *derive*. This is structural, and worth one line
in the rebuttal regardless of the empirical result.

---

## 2. Artifact selection

| Candidate | Verdict |
|---|---|
| `outputs/rebuttal_random/{full,rep2,rep3}_{baseline,reset,gated}` | on disk, N=40 math, gpt-5.4-mini, **but baseline is 87.5% — near ceiling**, so the NO_LEAK split would be badly underpowered. Kept as a secondary/robustness set. |
| `outputs/post_neurips_ac3_phase{1,2}/` | **only `winners.json` on disk** — run dirs live in `~/ac3/blob_staging/snapshot.tar.gz` (2.2 GB, 2026-06-12). Extracted to `~/ac3/recovered_t2c/` (excluding `verbose.log`). |
| `outputs/2026-07-27/*` | Hydra mirrors of the `rebuttal_random` runs. Redundant. |
| `outputs/2026-07-29/*` | 3-sample database smoke tests. Too small. |

**Decision D2 — use phase1 (DeepSeek-V4-Flash) as the primary set.** It is the paper's headline
LiC matrix, it is a *replay* design (every strategy branches from the same recorded prefix, so
baseline and AC3 arms are matched sample-for-sample), and baseline accuracy is far from ceiling:

| task | conv | baseline | AC3-Reset (`context_edit_v2_no_gate`) |
|---|---|---|---|
| math_v2 | 0/1/2 | .5625 / .7708 / .8333 | .7292 / .8750 / .8542 |
| code_v2 | 0/1/2 | .3000 / .3243 / .4167 | .5000 / .7027 / .5833 |
| database_v2 | 0/1/2 | .1429 / .1837 / .3469 | .5102 / .4286 / .5306 |

n = 144 (math) + 113 (code) + 147 (database) = **404 paired samples**. `actions_v2` has no plain
`no_gate` arm (only `*_accumulate`), so it is reported separately if at all.

---

## 3. Pairing logic

`neurips_review/experiments/paired_analysis.py` pairs at the **cell** level
(model × task × prefix) by regexing accuracy rows out of the report markdown, and applies an
exact two-sided binomial sign test. T2c needs **sample-level** pairing (the leak label is
per-sample), so I reuse its statistical core — exact binomial / McNemar on discordant pairs —
but pair on `(task, conv_prefix, sample_id)` read straight from `results.json`. Same design
philosophy (same triples on both arms), finer granularity.

---

## 4. Leakage classification

(Filled in below as the work proceeds.)
