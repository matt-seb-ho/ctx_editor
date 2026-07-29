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

### Round 2 — prompt v3, held-out draw: **10/24 exact, 11/24 binary**

Fresh stratified draw (2 per task × label, seed 99), excluding every record used in round 1 or
quoted in a prompt. I adjudicated before reading the judge's justification.

| task | exact | binary |
|---|---|---|
| math | 3/6 | 3/6 |
| database | 2/6 | 2/6 |
| code | 3/6 | 4/6 |
| actions | 2/6 | 2/6 |
| **total** | **10/24 (42%)** | **11/24 (46%)** |

**12 of the 13 disagreements are again over-calls.** The residual failure modes:
- the analyzer states a *wrong* final value and the judge scores it as a leak
  (`sharded-GSM8K/315`: analyzer says "the final answer should remain 16", gold is 14;
  `sharded-spider-val-671` conv0: analyzer writes `SELECT Earnings FROM poker_player;`, gold is a
  join returning `Name`; `sharded-HumanEval/88`: analyzer guesses ascending, gold is descending);
- requirement transcription on `actions` (`BFCL/parallel_132`: the four `calculate_average`
  argument lists are literally the four number sets the user typed);
- the analyzer endorsing the assistant's own already-correct artifact.

One under-call, again on math: `sharded-GSM8K/1166`, where `<aligned>` contains
"50 + 150 + 350 + 800 + 0 + 1000 = 2350" and gold is 2350.

**Conclusion: the raw 3-way judge label is not reliable enough to report.** But the error is
one-directional, so the `NO_LEAK` *label* is a high-precision filter even though the judge's
recall for `NO_LEAK` is poor. That is the quantity the analysis actually depends on, so I
measured it directly.

### Round 3 — precision of the `NO_LEAK` label (the load-bearing quantity)

24 records **all labelled `NO_LEAK` by v3** (6 per task, seed 555, disjoint from rounds 1-2),
hand-adjudicated for whether the injected text really withholds the answer:

| task | correct `NO_LEAK` | errors |
|---|---|---|
| math | 4/6 | `GSM8K/117` ("the final calculation (6 pairs × $60 = $360)", gold 360); `GSM8K/420` (borderline — "simply added the three numbers ($5,000 + $4,000 + $8,000)", gold 17000, recipe not evaluated) |
| database | 6/6 | — |
| code | 6/6 | — |
| actions | 6/6 | — |
| **total** | **22/24 (92%)** | |

Pooling with the 8 `NO_LEAK` records that fell in the round-2 draw: **29/32 = 91%**
(Wilson 95% CI [76%, 97%]). Every error is on math.

An objective, model-free cross-check agrees: of the 62 math records v3 called `NO_LEAK`, the
numeric probe finds the analyzer-derived gold number in 15 (24%), bounding math `NO_LEAK`
precision at ≤76%. On `database`/`code`/`actions` there were no hand-validation errors at all.

### Decision D6 — do not report the raw judge label as the primary split

Three detectors of the same underlying event, in increasing strictness:

1. **judge 3-way** (`LEAKS`∪`PARTIAL`) — high recall, poor precision → an **upper bound** on
   leakage, and a **conservative** definition of the `NO_LEAK` stratum.
2. **answer-verification pass** (`answer_check.py`, `prompt` in that file) — re-examines only the
   records the judge flagged, asking one narrow, checkable question: does the analyzer output
   state a value/artifact that *matches the ground truth*? Verdicts
   `CORRECT_ANSWER_STATED` / `WRONG_ANSWER_STATED` / `NOT_STATED`. This is what caught the
   wrong-answer over-calls: of 170 math records judged `LEAKS`, only 92 state the correct answer,
   52 state a wrong one, 26 state none; of 45 `code` `LEAKS`, **2**; of 26 `database` `LEAKS`, **0**.
3. **model-free numeric probe** — math only, no model in the loop.

**`leak_final` = LEAK iff (answer verified `CORRECT_ANSWER_STATED`) OR (math ∧ probe-derived).**
A union of two independent detectors, so it is high-recall for leakage and the resulting
`NO_LEAK` stratum is conservative. The two detectors converge on math (38% vs 40%), which is
the only place both apply — a useful validation of each.

Everything is reported under **both** `leak_final` (primary) and `leak_judge` (secondary), and
they agree on the direction and significance of every headline row.

---

## 6. Results

Full tables: [`RESULTS.md`](RESULTS.md), regenerable with
`.venv/bin/python neurips_review/autoresearch/tasks/T2c/final_tables.py`.
Artifact for every number: `~/ac3/recovered_t2c/ctx_editor/outputs/post_neurips_ac3_phase1/`
(extracted from `~/ac3/blob_staging/snapshot.tar.gz`; the on-disk
`outputs/post_neurips_ac3_phase1/` has only `winners.json`).

### 6a. Leakage base rate

| task | n analyzer outputs | judge `LEAKS`∪`PARTIAL` (upper bound) | **answer verified correct (strict)** | model-free probe |
|---|---|---|---|---|
| math | 144 | 110 (76%) | **54 (38%)** | 57 (40%) |
| code | 106 | 33 (31%) | **0 (0%)** | n/a |
| database | 147 | 25 (17%) | **1 (1%)** | n/a |
| actions | 150 | 14 (9%) | **3 (2%)** | n/a |
| **all** | **547** | **182 (33%)** | **58 (11%)** | — |

### 6b. Paired AC3-vs-Baseline split by leakage — strict definition

| subset | n | Baseline | AC3-Reset | Δ (pp) | 95% CI | W/L | McNemar p |
|---|---|---|---|---|---|---|---|
| math+code+database, all | 397 | 43.1% | 64.5% | +21.4 | [+16.4, +25.3] | 110/25 | <0.0001 |
| &nbsp;&nbsp;**NO_LEAK** | **329** | 36.5% | 57.1% | **+20.7** | [+14.8, +25.3] | 93/25 | **<0.0001** |
| &nbsp;&nbsp;LEAK | 68 | 75.0% | 100.0% | +25.0 | [+15.8, +25.0] | 17/0 | <0.0001 |
| math, NO_LEAK | 77 | 68.8% | 66.2% | **−2.6** | [−11.9, +7.6] | 8/10 | 0.815 |
| math, LEAK | 67 | 76.1% | 100.0% | +23.9 | [+14.6, +23.9] | 16/0 | <0.0001 |
| code, NO_LEAK | 106 (all) | 32.1% | 62.3% | **+30.2** | [+20.3, +34.7] | 36/4 | <0.0001 |
| database, NO_LEAK | 146 | 22.6% | 48.6% | **+26.0** | [+16.5, +32.4] | 49/11 | <0.0001 |
| actions, NO_LEAK | 147 | 76.2% | 83.0% | +6.8 | [−0.5, +12.6] | 20/10 | 0.099 |

Gated-Reset replicates: NO_LEAK n=311, 35.0% → 54.7%, **+19.6pp** [+13.8, +24.0], p<0.0001.

Under the conservative judge label the same rows read: NO_LEAK n=229, **+24.5pp**
[+17.3, +29.6] versus LEAK n=168, +17.3pp — i.e. the gain is *larger* on the non-leaking
subset under that definition too.

### 6c. What this means

- **Code and database — the two tasks with AC3's largest headline gains — have essentially no
  answer leakage at all (0/106 and 1/147).** Their +30.2pp and +26.5pp are therefore fully
  attributable to context editing. This is the strongest single fact for 5YHP.
- **Math is the exception and should be conceded.** 38-40% of math analyzer outputs contain the
  analyzer's own derived gold answer, and math's entire +9.7pp gain sits on that subset
  (+23.9pp on LEAK, −2.6pp on NO_LEAK). This is not surprising in hindsight: to say "your total
  of 3,270 is wrong because year 9 is 0" on a GSM8K item you have to compute the right total.
  Auditing and solving are not separable on short-answer arithmetic.
- The **overall** picture holds: on 329 of 397 conversations nothing correct was leaked, and AC3
  still gains **+20.7pp** there (p<0.0001).

### 6d. Caveats to state honestly if these numbers are used

1. **Post-treatment conditioning.** The leak label only exists in the AC3 arm, so the strata are
   selected on an AC3-arm variable. They differ in difficulty: baseline accuracy is 36.5% on
   NO_LEAK versus 75.0% on LEAK — the analyzer leaks on the *easy* items. The within-stratum
   paired comparison is valid; the between-stratum comparison is not causal.
2. **AC3 = 100% on the LEAK stratum is near-tautological** and should not be quoted as a result.
3. **Single model, single benchmark family, one run per cell.** DeepSeek-V4-Flash on the LiC
   replay matrix; the replay design makes the arms sample-matched, but there are no reps.
   `outputs/rebuttal_random/` (gpt-5.4-mini, math only) was rejected as the primary source
   because baseline sits at 87.5%.
4. **`code` has no stored gold solution** (`ground_truth_a: null`; graded by hidden tests), so
   its "leak" bar is "a complete correct implementation", judged from the problem statement.
   A strict bar; the 0% should be read as "the analyzer never wrote the program", which is what
   the hand-validation shows.
5. **The 3-way judge label is noisy** (42% exact hand-agreement) and is reported only as an
   upper bound / conservative alternative, never as the primary number.

---

## 7. Files

| file | what |
|---|---|
| `extract_analyzer_outputs.py` | traces → `analyzer_outputs.jsonl` (1079 analyzer invocations, 4 arms) |
| `numeric_probe.py` → `math_numeric_probe.json` | model-free gold-number probe for math |
| `prompt_v2.txt`, `prompt_v3.txt` | leakage-classifier prompts (v3 is the one used) |
| `classify_leakage.py` → `leak_labels_v{1,2,3}.jsonl` | 3-way LLM labels |
| `answer_check.py` → `answer_check.jsonl` | answer-verification pass over judge-flagged records |
| `paired_split.py` | sample-level paired McNemar / Wilson machinery |
| `final_tables.py` → `leak_labels_final.jsonl`, `RESULTS.md` | final labels + rebuttal tables |
| `make_tables.py` | earlier v3-only table builder (superseded by `final_tables.py`) |

