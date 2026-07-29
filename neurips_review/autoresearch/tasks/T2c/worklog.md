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

## 4. Leakage measurement

Two independent measurements, deliberately: one deterministic (auditable, no model trust
required) and one LLM-judged (covers all four tasks and the nuanced 3-way label).

### 4a. Deterministic numeric probe — LiC-math only (`numeric_probe.py`)

For each math analyzer output: does the GSM8K gold final answer appear as a standalone number
(thousands separators and trailing `.0` normalised, word-boundary matched) in the analyzer's
output? And is that same number already present in (i) the user messages the analyzer saw,
(ii) the assistant messages the analyzer saw?

Three-way provenance falls out with no model in the loop:

| | `context_edit_v2_no_gate` | `context_edit_v2_gated` |
|---|---|---|
| gold number appears in analyzer output | 73 / 144 (50.7%) | 73 / 142 (51.4%) |
| ...already stated by the **user** | 9 | 9 |
| ...already produced by the **assistant** | 7 | 7 |
| **derived by the analyzer itself** | **57 (39.6%)** | **57 (40.1%)** |
| derived *and* injected into the context | 57 (39.6%) | 57 (40.1%) |

Hand-read of the derived cases confirms they are real, not string coincidences, e.g.
`sharded-GSM8K/1113`: *"The correct morning temperature would be 2 - 8 + 3 = -3°C"* (gold -3);
`sharded-GSM8K/1131`: *"80 planks × $1.20 = $96.00"* (gold 96);
`sharded-GSM8K/1166`: *"Total = 50 + 150 + 350 + 800 + 0 + 1,000 = **2,350**"* (gold 2350).

**Decision D3 — the assistant-message check is not optional.** Without it the "derived" rate
reads 44.4%; 7/144 of those are the analyzer *preserving a correct result the assistant had
already produced*, which is the paper's stated mechanism, not the analyzer solving anything.
The task brief flagged the user-quotation case; the assistant-echo case is the same problem one
step over and matters just as much.

### 4b. LLM classifier (`classify_leakage.py`)

Judge `gpt-5.4-mini_2026-03-17` on TRAPI `redmond/interactive`, concurrency 5, one call per
analyzer invocation. Inputs: task type, ground truth, the user messages the analyzer saw, the
assistant messages the analyzer saw, and the analyzer's output (the injected `edited_context`
where one exists, otherwise the reconstructed `task_spec`/`aligned`/`issues` block).

**Decision D4 — the unit of "leakage" is NET NEW answer content.** Anything the user had
already stated, or the assistant had already produced, is excluded by construction. This is the
only operationalisation that answers 5YHP's actual question ("is the analyzer solving the
task?") rather than a proxy for "does the answer string appear anywhere".

**Prompt v1 and v2 both failed validation; v3 is the one used for every reported number.**
Full text of each is kept (`prompt_v2.txt`, `prompt_v3.txt`), and the label files are kept
side by side (`leak_labels_v1.jsonl`, `leak_labels_v2.jsonl` (partial, 386 rows, abandoned),
`leak_labels_v3.jsonl`).

| prompt | what changed | how it failed / passed |
|---|---|---|
| v1 | first attempt; provenance asked for alongside the label | 14/23 binary hand-agreement. **Systematic over-call**: faithful restatement of user-supplied requirements scored as leakage (worst on `actions`, 2/6). |
| v2 | provenance-first decision procedure + 3 worked examples | **Over-corrected**: 42/46 math outputs labelled `NO_LEAK`, versus 39.6% derived-gold from the model-free numeric probe. Cause traced to the phrase "not recoverable by restating the user messages", which the judge read as "not derivable from the user's numbers", filing arithmetic on user values under `QUOTED_FROM_USER`. Killed at 386/1079. |
| **v3** | draws the quoting/deriving line explicitly at **computation** ("copying a number the user wrote is quoting; *combining* two numbers the user wrote is deriving"), plus 5 worked examples spanning all four tasks | adopted — see §5 |

**Decision D5 — calibrate the math subset against the model-free probe, not against my own
labels.** The numeric probe (§4a) is an objective, 144-item check that needs no trust in the
judge. Any prompt whose math `LEAKS`+`PARTIAL` rate is far from the probe's ~40-50% is wrong.
This is what caught v2; v1 and v3 both clear it.

*Contamination note:* v3's worked examples were written from records I had already adjudicated
(`sharded-GSM8K/856`, `/1124`, `sharded-BFCL/parallel_199`, `sharded-livecodebench/2977`,
`sharded-spider-val-257-hard`). Those, and the whole round-1 sample, are excluded from the
held-out round-2 hand-validation draw.

*Non-injected analyses:* 16/1079 records have `needs_edit=false`, so nothing was inserted into
the context and no leak was possible. They are forced to `NO_LEAK` in the paired analysis.

---

## 5. Hand validation

### Round 1 — prompt v1: **14/23 binary agreement (61%). Rejected.**

24 records drawn stratified (2 per task × label cell, seed 2026); 1 unadjudicable because the
dump printed `edited_context`, which was empty for a non-injected record. I read the ground
truth, the user shards, the last assistant message and the full injected text for each, and
adjudicated before looking at the judge's justification.

| task | exact 3-way | binary (NO_LEAK vs PARTIAL∪LEAKS) |
|---|---|---|
| math | 5/6 | 5/6 |
| database | 2/5 | 2/5 |
| code | 4/6 | 5/6 |
| actions | 2/6 | 2/6 |
| **total** | **13/23 (57%)** | **14/23 (61%)** |

**9 of the 10 disagreements were the same error in the same direction: the judge scored a
faithful restatement of user-supplied requirements as leakage.** Canonical case,
`sharded-BFCL/parallel_199`: the user names four cities and asks for humidity; the analyzer
lists the four `get_current_weather(...)` calls with those cities; the judge called that
`LEAKS / DERIVED_BY_ANALYZER`. Nothing was derived. Same pattern on
`sharded-spider-val-617` (user literally asks for "min share" and "max share"),
`sharded-spider-val-257`, `sharded-BFCL/parallel_139`, `sharded-BFCL/parallel_175`.
One case was the mirror error on the assistant side (`sharded-livecodebench/2977`: the analyzer
endorses the assistant's own correct implementation → judged `LEAKS / ECHOED_FROM_ASSISTANT`,
violating the prompt's own rule).

The single disagreement in the other direction was `sharded-GSM8K/961`, where the analyzer
writes "recalculate using the complete data: 70 + 70 + 85 = 225" (gold 225) and the judge said
`NO_LEAK`.

Because the bias is one-directional, v1's numbers are **conservative for the paper's defence**
(over-calling leakage shrinks the `NO_LEAK` subset and dilutes the `LEAKS` subset with
non-leaky samples) — but 61% agreement is not good enough to report, hence v2.

### Round 2 — prompt v2

(filled in below)

---

## 6. Results

(filled in below)

