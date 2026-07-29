# T2A — Tier-A pollution detection (constructed pollution, no judge)

> **Read this first — these numbers are an upper bound, not a headline.**
> The pollution measured here was *injected*, so its position, phrasing and self-containedness are
> known to us and plausibly make it **more salient than naturally occurring pollution**. A detection
> rate on constructed pollution is therefore a **sanity check and a ceiling**, not an estimate of
> AC3's field performance. It answers exactly one question — *when a known-false span is definitely
> present, does AC3 find and remove it, while leaving correct content alone?* — and nothing more.
> The counterfactual span-ablation study (Tier B) is what would license a headline number.
>
> Two further limits, stated up front. (1) The injected spans use one shared surface frame, so they
> are stylistically homogeneous in a way real pollution is not; the frame is used for the harmful
> and the useful spans alike, which controls for "detector spots an injected-looking sentence" but
> not for "injected sentences are easier to reason about". (2) Single model (gpt-5.4-mini), single
> analyzer, one replay turn per conversation, no repeats.

## Headline

| metric | AC3-Reset | notes |
|---|---|---|
| **Pollution removal rate** | **97.6%** (123/126) | 96.9% on the causally-validated subset |
| **Preservation rate** | **4.0%** (5/126) | AC3-Reset discards correct injected content too |
| **Edit precision** | **50.4%** (123/244) | chance is 50.0% by construction |
| **Gate accuracy (sensitivity)** | **98.4%** (124/126) | clean-arm gate-open base rate 96.8% |
| Pollutant named explicitly in `issues` | **78.6%** (99/126) | 89.7% on the causally-validated subset |

AC3 **detects** the constructed pollutant (names it in `issues` in ~4 of 5 conversations, ~9 of 10
on the subset that is causally harmful) and **removes** it (97.6%). It is **not surgical**: it
removes correct injected content at essentially the same rate, so edit precision sits at chance.
The mechanism this supports is *detect-and-rebuild-from-the-user-side*, not *selective excision*.

Conversations in manifest: **145**; complete across all four run cells: **145**; of those, **126** pass the mechanical probe-admissibility check and form the primary analysis set.

Excluded 19 conversation(s) whose anchor is not a reliable probe: {'harmful_anchor_not_unique': 1, 'useful_anchor_too_short_numeric': 16, 'harmful_anchor_too_short_numeric': 5, 'useful_anchor_not_unique': 2}. The check is mechanical and applied identically to the harmful and the useful side, so it cannot bias the 2x2 in either direction.

`metrics.json` and `run_summary.json` agree on accuracy in every run cell (trap 5 check).

## 0. Positive controls (offline, no API, run over all injected conversations)

| control editor | n | removal rate | preservation rate | expected removal | expected preservation | pass |
|---|---|---|---|---|---|---|
| PC1 identity (no edit at all) | 126 | 0.000 | 1.000 | 0.0 | 1.0 | PASS |
| PC2 oracle (harmful span deleted by hand) | 126 | 1.000 | 1.000 | 1.0 | 1.0 | PASS |
| PC3 nuke (empty context) | 126 | 1.000 | 0.000 | 1.0 | 0.0 | PASS |
| PC4 delete-both | 126 | 1.000 | 0.000 | 1.0 | 0.0 | PASS |

**All controls pass: True.** PC1 proves the probe fires when the span is present (so a 0% removal rate is reachable); PC2 proves a hand-removed span scores as removed *and* that removal is separable from preservation; PC3/PC4 prove a delete-everything editor scores 100% removal and 0% preservation — i.e. removal rate alone is gameable and preservation rate is what stops it.

## 1. The 2x2


### All tasks (primary: probe-admissible conversations)  (n = 126 conversations = 126 harmful + 126 useful spans)

| | harmful (injected, false by construction) | useful (injected, true by construction) |
|---|---|---|
| **AC3 removed** | 123 | 121 |
| **AC3 kept** | 3 | 5 |

- **Pollution removal rate** = 97.6% (123/126)  [95% CI 93.2–99.2%]
- **Preservation rate** = 4.0% (5/126)  [95% CI 1.7–9.0%]
- **Edit precision** = 50.4% (123/244)  (chance = 50.0% by construction: exactly one harmful and one useful span per conversation, so an indiscriminate editor scores 50%)
- clean-arm spontaneous base rate: harmful anchor 0.0%, useful anchor 0.0%
- base-rate-attributable preservation = 4.0%
- harmful span named explicitly in the analyzer's `issues` section: 78.6% (99/126); useful span named there (a false alarm): 42.1% (53/126)

### Robustness: every complete conversation, including inadmissible probes  (n = 145 conversations = 145 harmful + 145 useful spans)

| | harmful (injected, false by construction) | useful (injected, true by construction) |
|---|---|---|
| **AC3 removed** | 142 | 135 |
| **AC3 kept** | 3 | 10 |

- **Pollution removal rate** = 97.9% (142/145)  [95% CI 94.1–99.3%]
- **Preservation rate** = 6.9% (10/145)  [95% CI 3.8–12.2%]
- **Edit precision** = 51.3% (142/277)  (chance = 50.0% by construction: exactly one harmful and one useful span per conversation, so an indiscriminate editor scores 50%)
- clean-arm spontaneous base rate: harmful anchor 0.0%, useful anchor 2.1%
- base-rate-attributable preservation = 4.9%
- harmful span named explicitly in the analyzer's `issues` section: 79.3% (115/145); useful span named there (a false alarm): 42.1% (61/145)

### database  (n = 80 conversations = 80 harmful + 80 useful spans)

| | harmful (injected, false by construction) | useful (injected, true by construction) |
|---|---|---|
| **AC3 removed** | 77 | 78 |
| **AC3 kept** | 3 | 2 |

- **Pollution removal rate** = 96.2% (77/80)  [95% CI 89.5–98.7%]
- **Preservation rate** = 2.5% (2/80)  [95% CI 0.7–8.7%]
- **Edit precision** = 49.7% (77/155)  (chance = 50.0% by construction: exactly one harmful and one useful span per conversation, so an indiscriminate editor scores 50%)
- clean-arm spontaneous base rate: harmful anchor 0.0%, useful anchor 0.0%
- base-rate-attributable preservation = 2.5%
- harmful span named explicitly in the analyzer's `issues` section: 82.5% (66/80); useful span named there (a false alarm): 37.5% (30/80)

### code  (n = 46 conversations = 46 harmful + 46 useful spans)

| | harmful (injected, false by construction) | useful (injected, true by construction) |
|---|---|---|
| **AC3 removed** | 46 | 43 |
| **AC3 kept** | 0 | 3 |

- **Pollution removal rate** = 100.0% (46/46)  [95% CI 92.3–100.0%]
- **Preservation rate** = 6.5% (3/46)  [95% CI 2.2–17.5%]
- **Edit precision** = 51.7% (46/89)  (chance = 50.0% by construction: exactly one harmful and one useful span per conversation, so an indiscriminate editor scores 50%)
- clean-arm spontaneous base rate: harmful anchor 0.0%, useful anchor 0.0%
- base-rate-attributable preservation = 6.5%
- harmful span named explicitly in the analyzer's `issues` section: 71.7% (33/46); useful span named there (a false alarm): 50.0% (23/46)

### pair design = MATCHED  (n = 29 conversations = 29 harmful + 29 useful spans)

| | harmful (injected, false by construction) | useful (injected, true by construction) |
|---|---|---|
| **AC3 removed** | 29 | 29 |
| **AC3 kept** | 0 | 0 |

- **Pollution removal rate** = 100.0% (29/29)  [95% CI 88.3–100.0%]
- **Preservation rate** = 0.0% (0/29)  [95% CI 0.0–11.7%]
- **Edit precision** = 50.0% (29/58)  (chance = 50.0% by construction: exactly one harmful and one useful span per conversation, so an indiscriminate editor scores 50%)
- clean-arm spontaneous base rate: harmful anchor 0.0%, useful anchor 0.0%
- base-rate-attributable preservation = 0.0%
- harmful span named explicitly in the analyzer's `issues` section: 41.4% (12/29); useful span named there (a false alarm): 44.8% (13/29)

### pair design = MIXED  (n = 97 conversations = 97 harmful + 97 useful spans)

| | harmful (injected, false by construction) | useful (injected, true by construction) |
|---|---|---|
| **AC3 removed** | 94 | 92 |
| **AC3 kept** | 3 | 5 |

- **Pollution removal rate** = 96.9% (94/97)  [95% CI 91.3–98.9%]
- **Preservation rate** = 5.2% (5/97)  [95% CI 2.2–11.5%]
- **Edit precision** = 50.5% (94/186)  (chance = 50.0% by construction: exactly one harmful and one useful span per conversation, so an indiscriminate editor scores 50%)
- clean-arm spontaneous base rate: harmful anchor 0.0%, useful anchor 0.0%
- base-rate-attributable preservation = 5.2%
- harmful span named explicitly in the analyzer's `issues` section: 89.7% (87/97); useful span named there (a false alarm): 41.2% (40/97)

- removal by harmful type `H_PHANTOM_COL`: 95.5% (63/66)

- removal by harmful type `H_PHANTOM_PARAM`: 100.0% (31/31)

- removal by harmful type `H_WRONG_EXEC_FACT`: 100.0% (14/14)

- removal by harmful type `H_WRONG_TEST`: 100.0% (15/15)
- preservation by useful type `U_EXEC_FACT`: 2.5% (2/80)
- preservation by useful type `U_TRUE_SIG`: 9.1% (2/22)
- preservation by useful type `U_TRUE_TEST`: 4.2% (1/24)

### Contrast: AC3-Rewrite (S3), which *compacts* instead of resetting


### AC3-Rewrite, all tasks  (n = 126 conversations = 126 harmful + 126 useful spans)

| | harmful (injected, false by construction) | useful (injected, true by construction) |
|---|---|---|
| **AC3 removed** | 34 | 77 |
| **AC3 kept** | 92 | 49 |

- **Pollution removal rate** = 27.0% (34/126)  [95% CI 20.0–35.3%]
- **Preservation rate** = 38.9% (49/126)  [95% CI 30.8–47.6%]
- **Edit precision** = 30.6% (34/111)  (chance = 50.0% by construction: exactly one harmful and one useful span per conversation, so an indiscriminate editor scores 50%)
- clean-arm spontaneous base rate: harmful anchor 2.4%, useful anchor 0.0%
- base-rate-attributable preservation = 38.9%
- harmful span named explicitly in the analyzer's `issues` section: 77.8% (98/126); useful span named there (a false alarm): 42.9% (54/126)

**Two editors, one 2x2, same probes** — the metric is not saturated by construction:

| editor | removal | preservation | edit precision (chance 50%) | pollutant named in `issues` |
|---|---|---|---|---|
| AC3-Reset (rebuilds context) | 97.6% (123/126) | 4.0% (5/126) | 50.4% (123/244) | 78.6% (99/126) |
| AC3-Rewrite (compacts context) | 27.0% (34/126) | 38.9% (49/126) | 30.6% (34/111) | 77.8% (98/126) |

## 2. Gate accuracy (turn level)

| arm | n | gate opened (analyzer chose to edit) |
|---|---|---|
| injected | 126 | 98.4% (124/126) |
| clean | 126 | 96.8% (122/126) |

On the injected arm there was *always* something to remove (one false span per conversation, by construction), so every closed gate is a miss: **gate sensitivity = 98.4% (124/126)**. Closed-gate conversations retain the harmful span by definition (2 of them).

The clean-arm figure is a *reference base rate*, **not** a false-positive rate: these are real LiC conversations that already contain natural pollution, so an open gate there may be correct. Split by whether the recorded baseline answer was right:
- clean arm, baseline correct: gate opened 94.3% (33/35)
- clean arm, baseline wrong: gate opened 97.8% (89/91)

## 3. Does removal predict accuracy?

| arm | Baseline (full context) | AC3-Reset | delta |
|---|---|---|---|
| clean | 27.8% (35/126) | 65.1% (82/126) | +37.3pp |
| injected | 36.5% (46/126) | 65.1% (82/126) | +28.6pp |

AC3-Rewrite on the injected arm: 63.5% (80/126).

The `injected` arm carries **both** spans, so its effect is a net of the two. Injecting the pair moves the **Baseline** by +8.7pp (35/126 -> 46/126) and **AC3** by +0.0pp (82/126 -> 82/126). AC3 is essentially **invariant** to injected assistant-side content: it drops the false span and the true span alike. Section 4 decomposes the two effects; section 5 gives the accuracy story on the causally-harmful subset, which is the one that answers the mechanistic question.

Per-conversation split by whether AC3 actually removed the injected span (**underpowered — AC3 removes almost everything, so the 'no' cell is tiny**; the factorial in section 4 is the load-bearing evidence, not this table):

| AC3 removed the harmful span? | n | Baseline acc | AC3 acc | delta |
|---|---|---|---|---|
| yes | 123 | 36.6% | 65.9% | +29.3pp |
| no | 3 | 33.3% | 33.3% | +0.0pp |

## 4. What is each injected span actually worth? (detector-free)

Baseline = full context, no editing of any kind, so each cell measures the span itself, not anyone's detection of it. Same n, same prefixes, paired.

| arm | useful span | harmful span | Baseline accuracy |
|---|---|---|---|
| clean | absent | absent | 27.8% (35/126) |
| use_only | **present** | absent | 42.9% (54/126) |
| harm_only | absent | **present** | 16.7% (21/126) |
| injected | **present** | **present** | 36.5% (46/126) |

- **Harmful span, main effect:** -11.1pp on an unedited context — this is the damage AC3 has to undo, measured without any detector.
- **Useful span, main effect:** +15.1pp — this is what the preservation rate is protecting. If this is ~0 the span is *true but inert*, and a low preservation rate on it is not a defect; read the preservation number accordingly.
  - `U_EXEC_FACT` (n=80): 16.2% -> 20.0% (+3.8pp)
  - `U_TRUE_SIG` (n=22): 45.5% -> 90.9% (+45.5pp)
  - `U_TRUE_TEST` (n=24): 50.0% -> 75.0% (+25.0pp)
  - `H_PHANTOM_COL` (n=66): 13.6% -> 4.5% (-9.1pp)
  - `H_PHANTOM_PARAM` (n=31): 48.4% -> 19.4% (-29.0pp)
  - `H_WRONG_EXEC_FACT` (n=14): 28.6% -> 28.6% (+0.0pp)
  - `H_WRONG_TEST` (n=15): 46.7% -> 53.3% (+6.7pp)

## 5. Restricting to injections that are *causally* harmful

Section 4 shows the two `*_WRONG_*` types are false by construction but **causally inert** on an unedited context (0.0pp and +6.7pp). Labelling them 'harmful' is defensible as a factual matter and indefensible as a causal one, so here is the 2x2 restricted to the injection types whose measured main effect on the Baseline is negative — i.e. pollution validated by causal effect, not by my say-so:

Types retained: ['H_PHANTOM_COL', 'H_PHANTOM_PARAM'].

### causally-validated harmful injections  (n = 97 conversations = 97 harmful + 97 useful spans)

| | harmful (injected, false by construction) | useful (injected, true by construction) |
|---|---|---|
| **AC3 removed** | 94 | 92 |
| **AC3 kept** | 3 | 5 |

- **Pollution removal rate** = 96.9% (94/97)  [95% CI 91.3–98.9%]
- **Preservation rate** = 5.2% (5/97)  [95% CI 2.2–11.5%]
- **Edit precision** = 50.5% (94/186)  (chance = 50.0% by construction: exactly one harmful and one useful span per conversation, so an indiscriminate editor scores 50%)
- clean-arm spontaneous base rate: harmful anchor 0.0%, useful anchor 0.0%
- base-rate-attributable preservation = 5.2%
- harmful span named explicitly in the analyzer's `issues` section: 89.7% (87/97); useful span named there (a false alarm): 41.2% (40/97)
- Baseline, clean: 24.7% (24/97)
- Baseline, harmful span only: 9.3% (9/97)
- AC3-Reset, harmful span present: 59.8% (58/97)

---

## Appendix A — verbatim injection templates

Every injected span, harmful and useful, is wrapped in the **same** frame:

```
Quick note so we don't lose track of this: {claim} I'll carry that forward.
```

`{claim}` per type, with a real instantiation drawn from the corpus:


**`H_PHANTOM_COL` — HARMFUL.** Attributes to the user a requirement never stated; the extra column makes the result set differ from reference_sql (Spider result_eq fails).

- template: `you also need `{table}.{col}` included as an extra output column in the final result, and rows where `{table}.{col}` is NULL filtered out.`
- instance (`sharded-spider-val-129-extra`): Quick note so we don't lose track of this: you also need `cars_data.Horsepower` included as an extra output column in the final result, and rows where `cars_data.Horsepower` is NULL filtered out. I'll carry that forward.

**`H_PHANTOM_PARAM` — HARMFUL.** Never requested; a required extra parameter makes the grader's call signature fail outright.

- template: `the function also has to take a required `{param}` parameter and return a tuple `(result, {param})` rather than the bare result.`
- instance (`sharded-HumanEval/111`): Quick note so we don't lose track of this: the function also has to take a required `trace_log` parameter and return a tuple `(result, trace_log)` rather than the bare result. I'll carry that forward.

**`H_WRONG_EXEC_FACT` — HARMFUL.** Contradicts the executed reference_sql result. False by construction.

- template: `I checked this against the data — the correct result has {n_true} row(s), and `{wrong_value}` is one of the values that must appear in the `{col}` column.`
- instance (`sharded-spider-val-455-medium`): Quick note so we don't lose track of this: I checked this against the data — the correct result has 20662 row(s), and `Lonn` is one of the values that must appear in the `last_name` column. I'll carry that forward.

**`H_WRONG_TEST` — HARMFUL.** Contradicts the benchmark public test case. False by construction.

- template: `I checked the expected behaviour — for the input `{input}` the function must return `{wrong_output}`.`
- instance (`sharded-HumanEval/106`): Quick note so we don't lose track of this: I checked the expected behaviour — for the input `7` the function must return `[1, 2, 6, 24, 15, 720, 35]`. I'll carry that forward.

**`U_EXEC_FACT` — USEFUL.** Obtained by executing reference_sql against the restored Spider DB. True.

- template: `I checked this against the data — the correct result has {n_true} row(s), and `{true_value}` is one of the values that must appear in the `{col}` column.`
- instance (`sharded-spider-val-129-extra`): Quick note so we don't lose track of this: I checked this against the data — the correct result has 2 row(s), and `france` is one of the values that must appear in the `CountryName` column. I'll carry that forward.

**`U_TRUE_TEST` — USEFUL.** A benchmark public test case. True by construction.

- template: `I checked the expected behaviour — for the input `{input}` the function must return `{true_output}`.`
- instance (`sharded-HumanEval/106`): Quick note so we don't lose track of this: I checked the expected behaviour — for the input `5` the function must return `[1, 2, 6, 24, 15]`. I'll carry that forward.

**`U_TRUE_SIG` — USEFUL.** Read verbatim off the benchmark starter_code. True by construction.

- template: `the graded interface is `{starter_code}` — the function must be named `{func}` and take exactly those arguments.`
- instance (`sharded-livecodebench/2728`): Quick note so we don't lose track of this: the graded interface is `class Solution: def matrixSum(self, nums: List[List[int]]) -> int` — the function must be named `matrixSum` and take exactly those arguments. I'll carry that forward.

Slot values are filled deterministically: schema columns and foreign keys from the Spider DDL, executed-result values by running `reference_sql` against the restored Spider SQLite database, test cases from the benchmark's `public_test_cases`, signatures from `starter_code`. Wrong variants are produced by a fixed `corrupt()` function (integer +7, last list element +7, final character substituted for proper nouns). Nothing is authored by a model, so a reviewer can regenerate every span from `neurips_review/autoresearch/tasks/T2A/inject.py`.
