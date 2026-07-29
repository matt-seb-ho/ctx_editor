# T2B — Counterfactual span ablation (causal, non-circular pollution labels)

**Design source:** `neurips_review/experiment_todos.md` §T2, Tier B ("the gold standard").
**Reviewer prompt:** 5YHP W5, plus the circularity objection to judge-based pollution labels.
**Status:** in progress (2026-07-29 overnight session, operator asleep). Every ambiguity resolved here.

**What T2B adds over T2A.** T2A established a detector-free causal effect for *injected* spans
(harmful −11.1pp, useful +15.1pp on an unedited context) and a 2×2 against AC3-Reset / AC3-Rewrite.
Its stated limitation is that injected pollution is plausibly more salient than natural pollution.
T2B keeps the causal design and swaps constructed spans for **naturally occurring** ones:
**natural spans, causal labels.**

---

## 0. Reconnaissance (t+0 .. t+25 min, 15:45–16:10)

Read, as instructed: `experiment_todos.md` §T2; `tasks/T2A/{RESULTS.md,worklog.md,run_matrix.sh,run_factorial.sh,make_single_arms.py}`;
`src/ctx_editor/execution/replay.py`.

### 0.1 Trap 3 — is the `seed=` fix present?

Checked in this tree exactly as T2A did:

```
grep -rn "seed" src/ctx_editor/run_experiment.py src/ctx_editor/execution/*.py
```

(result recorded in §0.1a below). **Decision D0: T2B does not rely on `seed=`.** T2B's whole
design is repeated sampling at temperature 1.0 — replicates are the measurement instrument, not a
nuisance. I therefore call them "replicate runs at temperature 1.0" throughout, as the brief
permits, and never claim bit-for-bit reproducibility of an individual replicate.

### 0.2 Venue (brief + TODO)

LiC **database_v2** and **code_v2**. No math (ceiling + T2c analyzer answer-leakage confound).
Replay prefixes: `data/valid_prefixes_htn50_52/deepseek_v4_flash_foundry/{database_v2,code_v2}/conv0`
— the paper's own phase-1 prefixes, same source T2A used. Spider DBs restored (`data/spider/databases/`).

### 0.3 Harness facts confirmed by reading the code

* `build_replay_trace(..., replay_turns=1)` → `truncate_final_assistant=True`. So the **prefix that
  the ablation acts on** is messages `0 .. n-2`, i.e. system + all user turns + all assistant
  messages **except the last one**. Spans therefore live in assistant messages at indices
  `2, 4, …, n-3`.
* `load_baseline_traces()` keys by `sample_id` and `rglob`s the directory, so **one variant per
  directory** — ablation conditions must be separate directories. (Also: it picks up
  `false_negatives.json` for user-sim skipping; I copy only trace files, as T2A did, so no
  condition-dependent skipping.)
* Run invocation copied verbatim from `T2A/run_matrix.sh`, including
  `false_negative_analysis.model=gpt-5.4-mini_2026-03-17` (trap 1) and
  `model=gpt5_4_mini_trapi load_balancer=trapi execution.max_concurrent=5` (trap 6).
* Output dir is **T2B-scoped** (`outputs/T2B/...`), trap 5.
* **Metric = raw accuracy** (trap 2). `adjusted_accuracy` excludes 50–78% of editing-arm failures
  vs 9% for baseline, so it is not comparable across arms; and for the ablation arms specifically
  the whole point is to measure the assistant's raw success rate under a fixed prefix. Stated
  explicitly in RESULTS.

### 0.4 Timing budget (from `T2A/run_matrix.log`)

Baseline replay cells of 40–80 samples took 1.5–2.5 min at `max_concurrent=5`, i.e. ≈ 2–3.5 s of
wall clock per sample. A T2B condition-run of ~25 conversations is therefore ≈ 1–1.5 min. This is
what makes N replicates per condition affordable.

### 0.1a Trap 3 result — the `seed=` fix is **not** in this tree

```
grep -rn "seed" src/ctx_editor/run_experiment.py      -> 0 hits
grep -rn "seed" src/ctx_editor/execution/*.py         -> 0 hits
git log --oneline -3 -> 1030d0d chore(rebuttal): dispatch T2B natural-span causal ablation
```

Same finding T2A recorded. I am told not to `git checkout` (trap 4), so **D0 stands: no `seed=`.**
Replicates are described throughout as **"replicate runs at temperature 1.0"**. Confirmed from the
run log that temperature really is 1.0 and not 0: `ctx_editor - WARNING - gpt-5 models require
temperature=1.0, overriding 0.0 -> 1.0`. Good — the replicates are genuine independent draws, which
is a precondition for this whole design.

### 0.5 A stale-clock note

`uptime` and my first `date` reading disagreed with the run log by ~50 min. All times in this
worklog are taken from `date` / the run logs, which agree with each other. (T2A hit the same thing.)

---

## 1. Design

### 1.1 What a "span" is

A **span** is a naturally occurring block inside an assistant message of the replay prefix:
a fenced code block, or a blank-line-separated paragraph. Nothing is authored, nothing is injected.
`build_corpus.py::split_blocks` partitions each assistant message exhaustively into such blocks.

Choices, with reasons:

* **Block, not whole message.** Ablating a whole assistant message leaves the following user turn
  answering a question that is no longer there, which confounds "this span was harmful" with "the
  conversation stopped making sense". Block-level ablation keeps the clarifying question in place
  and removes one unit of content. It is also finer, and it is what "span" means in the TODO.
* **Only assistant messages, only in the prefix.** The final assistant message is stripped by
  `truncate_final_assistant`, so it is not part of the context under test.
* **Both arms are canonicalised.** The present corpus rebuilds every prefix assistant message as
  `"\n\n".join(blocks)`. The ablated corpus is the same rebuild minus one block. Without this the
  ablated arm would differ from the present arm in incidental whitespace as well as in the span.
* **A span may not be the only block in its message** (removal would leave an empty assistant
  message, which is an API artifact rather than an ablation).
* **Minimum 40 characters.**

### 1.2 Span selection, K = 4 per conversation

All admissible blocks are enumerated (~9 per conversation); 4 are kept, **stratified by block kind**
— up to 2 code blocks and the rest prose, each spread over conversation position by a deterministic
rule (`spread()`). Selection uses **position and block kind only**: never correctness, never content,
never any effect estimate. The stratification exists so the sample is not swamped by boilerplate
prose ("This query joins the tables ...") and actually contains the SQL/code that is the plausible
anchoring content.

### 1.3 The run matrix

Per task, conditions are `present`, `abl1..abl4`, and three controls. Loop order is **rep-major**,
so a truncated session yields fewer replicates of everything rather than zero replicates of some
conditions. Every cell is skipped if `run_summary.json` already exists, so replicates can be topped
up later by re-running with a larger `R_*`.

### 1.4 Controls (trap 1 — mandatory, and stated before the results)

Three injected spans of **known causal sign**, all placed identically (appended as a new final block
of the last prefix assistant message). Their "span removed" arm is the plain `present` corpus, so
each costs one condition, not two.

| control | span | expectation |
|---|---|---|
| `ctl_filler` | contentless, in T2A's surface frame | ablation effect ≈ **0** (negative control) |
| `ctl_harm` | the T2A `H_PHANTOM_COL` / `H_PHANTOM_PARAM` span for this exact conversation — the two injection types T2A §4 causally validated as harmful | ablation effect **> 0** |
| `ctl_answer` | the fully specified question (+ the gold `reference_sql` for database) | ablation effect **≪ 0** — this is the brief's "ablate the span containing the answer" |

`ctl_harm` reuses T2A's `manifest.jsonl` verbatim, so the two studies are on one scale.

### 1.5 Statistics — and the honest bit about power

* Per span: `delta = p_ablated - p_present`, sign convention **positive = removing the span helped =
  the span was harmful**. CI by Newcombe hybrid score; test by two-sided Fisher exact; multiplicity
  by Benjamini–Hochberg at q = 0.10.
* Fisher implementation validated against textbook values before use
  (`fisher.test(matrix(c(3,1,1,3),2))` = 0.4857 ✓; lady-tasting-tea 4/4 vs 0/4 = 0.02857 ✓).
  **My first implementation was wrong** — the hypergeometric support bounds were
  `max(0, c1 - b)` instead of `max(0, r1 + c1 - n)`, which made `mde()` return 0.000 and reported
  p = 0.023 for 5/8 vs 5/10. Caught precisely because I sanity-checked against known values before
  trusting the number, which is trap 1 in its purest form.
* **Minimum detectable effect**, exact, at `n_present = 12`, `n_ablated = 10`:
  * smallest *observed* difference that can reach p < 0.05: **0.400**
  * smallest *true* difference detectable with 80% power: **+0.61** at base rate 0.20,
    **+0.55** at base rate 0.40.
  * Downward (a span being *useful*): **bounded by the base rate itself** — at `p0 = 0.20` no
    downward effect above 0.20 is even expressible, so useful spans are undetectable at floor.
    This is the single most important power fact in the study and it is why §2 selects
    conversations with headroom.
* Consequently, **per-span labels resolve only large effects**, and the load-bearing analyses are
  aggregate: the distribution of `delta` over all spans, and a label-free test of whether AC3's
  remove/keep decision predicts `delta`.

---

## 2. Pilot and conversation selection (16:57–16:24 by the run log)

`run_pilot.sh` — 6 replicate runs of the **unablated** prefix over the full conv0 pools
(49 database, 35 code), `experiment=baseline`, i.e. the reference arm only.

**Finding that changed the design: the present-arm accuracy distribution is strongly bimodal.**
After 3 replicates, database was 41/49 never-solved, 5/49 always-solved, 3 mixed; code was
15/35 never-solved, 17/35 always-solved, 3 mixed. Mean raw accuracy on database ≈ 10%.

This matters because it bounds what an ablation can reveal:

* a **floor** conversation has only upward headroom → it can reveal a **harmful** span (removing it
  rescues the turn) and can never reveal a useful one;
* a **ceiling** conversation has only downward headroom → it can reveal a **useful** span only;
* mid-range conversations can reveal either, but there are very few of them.

My first selection rule ("keep conversations with pilot rate strictly between 0 and 1") would have
found 3 per task. **Rejected.** Replacement rule, declared before looking at which conversations it
picks: **sort by pilot accuracy, take an evenly spaced sample across the sorted order**, so the
selected set spans floor, middle and ceiling in proportion. Ties break toward conversations that
have a T2A manifest entry, so the `ctl_harm` control covers as much of the set as possible.

Selection uses the *pilot* copy of the present arm only. The analysis then uses **fresh present
replicates**, so selection cannot manufacture an effect through regression to the mean.

**Selected: 17 database + 15 code = 32 conversations → 128 spans (4 per conversation).**

### 2.1 Alignment-probe feasibility, checked before committing compute

Ran the probe offline against T2A's *existing* `ac3_clean_database_v2_conv0` traces, which replay
the same conv0 prefixes, so this cost nothing:

* 185 candidate spans over 49 conversations; **93 (50.3%) have ≥ 2 unique content tokens** and are
  therefore probe-admissible. The other half are boilerplate whose vocabulary is fully shared with
  the rest of the conversation and cannot be probed without a judge — they still receive causal
  labels, they just cannot be scored for AC3 alignment. This is a stated coverage limit.
* On those, AC3-Reset's keep rate is **9.7%**, consistent with T2A's 4.0% preservation rate on
  injected spans. The probe is clearly not saturated at 1.

## 3. Run plan committed (t ≈ 16:25)

| | value |
|---|---|
| conversations | 17 database + 15 code |
| spans | 128 (4 per conversation, ≤2 code + rest prose) |
| replicates, present | 14 |
| replicates, ablation | 12 |
| replicates, controls | 8 |
| MDE (observed difference reaching p<0.05) at (14, 12) | 0.333 |
| runs | 86 per task |
| estimated wall clock | ≈ 3.9 h (database ≈ 66 s/run, code ≈ 96 s/run) |

Rep-major loop + skip-if-complete, so replicates can be topped up later and a truncated session
still yields a balanced matrix.

### 3.1 Selection rule revised once more, before any ablation compute

The even-spacing rule alone put database at mean pilot rate 0.137 — almost all floor, i.e. almost
no ability to detect a *useful* span on that task. Revised (still present-arm-only, still declared
in advance): **take all mid-range conversations first** (they are scarce and can express an effect
in either direction), **then fill by even spacing over the sorted rest**. Result:

| task | selected | pilot rates of the selected set | mean |
|---|---|---|---|
| database | 17 | ten at 0.00, then 0.17, 0.33, 0.50, 0.67, 0.83, 0.83, 1.00 | 0.255 |
| code | 15 | 0.00, three at 0.17, 0.50, five at 0.67, three at 0.83, two at 1.00 | 0.589 |

`ctl_harm` (the T2A injected-pollutant control) covers 24 of the 32; `ctl_answer` covers all 32.

### 3.2 Corpus integrity check (offline, before spending compute)

For all **111 spans**: the ablated trace differs from the present trace **in exactly one message**,
that message contains the span in the present arm, does not contain it in the ablated arm, and the
length delta equals the span length (± the 2-char block join). **111/111 pass, 0 failures.** This is
the check that would have caught a silent no-op ablation, which is the T2B analogue of the two
silent `0.0` returns the brief warns about.

Corpus sizes on disk (database / code): present 17/15, abl1 17/13, abl2 17/13, abl3 17/11,
abl4 12/11, ctl_filler 17/15, ctl_harm 13/11, ctl_answer 17/15. 111 spans total
(43 code blocks, 68 prose).

**Matrix launched 16:25.**

### 3.3 AC3-arm smoke test (16:28)

3 database conversations through both editors before committing the full alignment runs:

* `context_edit_v2_no_gate` (**AC3-Reset**) — logs `conversation_analysis` + `edit_decision` +
  `context_edit_output`; `carried_context()` returns 766–1172 chars, gate open in 3/3.
* `ac3_rewrite_v8_lic` with `analysis_cache_dir=null` (**AC3-Rewrite**) — logs
  `compaction_analysis` + `context_compaction`; `carried_context()` returns 627–892 chars.

Both branches of T2A's `carried_context()` therefore fire correctly on T2B traces, so the alignment
probe will not be silently reading an empty string (which is exactly how a "0.0 removal rate"
harness fault would look).

---

## 4. Analysis pipeline built and dry-run against partial data (16:30–16:47)

`measure_lib.py` (stats + probe) and `analyze.py` (RESULTS.md generator). T2A is reused directly:
`analyze.py` imports `carried_context()` and `full_body()` from `tasks/T2A/measure.py`, so the
definition of "the context AC3 actually handed the assistant" is **literally the same function** in
both studies, including its handling of the Rewrite (`context_compaction`) log schema and its
exclusion of `issues`.

Dry-run on 1–2 replicates confirmed the whole pipeline runs end to end and, more usefully, that the
**probe controls behave**:

| probe control | expected | measured (66 admissible spans) |
|---|---|---|
| PC-identity — carried context = the full unedited conversation | 1.00 | **1.000** |
| PC-nuke — carried context = "" | 0.00 | **0.000** |
| PC-other — carried context = the conversation *minus this span* | 0.00 | **0.000** |

PC-other is the one that matters: it proves the probe is testing *this span* rather than the
conversation's general vocabulary. It is 0 by construction (uniqueness is defined against the rest
of the conversation), which is precisely why spans without ≥2 unique tokens are **excluded** rather
than guessed at — 66 of 111 spans (59.5%) are probe-admissible.

### 4.1 Empirical null added — using the negative control as the noise floor

A fixed threshold like |delta| ≥ 0.25 is arbitrary and, at these replicate counts, roughly 1.3
standard errors — so a meaningful share of truly inert spans would clear it by chance. Rather than
argue about the threshold I take it from the data: **`ctl_filler` is a genuine null ablation**
(a contentless span removed from a real conversation, scored by exactly the ablation code path), so
the 95th percentile of its |effect| distribution is an empirical noise floor. Three labellings are
now reported side by side:

1. **strict** — two-sided Fisher exact p < 0.05 (conservative; resolves only large effects);
2. **null-calibrated** — |delta| above the 95th percentile of the filler null (the principled one);
3. **lenient** — |delta| ≥ 0.25 (exploratory, reported for continuity with T2A's framing).

The 2×2 alignment table is produced under all three.

### 4.2 Status at 16:47

Main matrix 24/172 runs; AC3 alignment 3/12 runs. Rate is steady at ≈ 1.1 runs/min and the AC3
stream (running at `max_concurrent=3` alongside the main stream's 5) has not slowed it. Projected
finish ≈ 19:00 for the matrix.
