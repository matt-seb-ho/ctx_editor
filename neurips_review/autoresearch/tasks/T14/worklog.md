# T14 — Audit of `adjusted_accuracy` (false-negative adjustment) and corrected LiC matrix

Started 2026-07-29. Autonomous session. Operator asleep.

## Goal
1. Characterise the FN-judge bias mechanism with file:line evidence.
2. Quantify per-arm exclusion rates across the LiC matrix (tasks × strategies).
3. Re-derive corrected accuracies with T1's arm-symmetric re-judge.
4. State whether any qualitative conclusion flips.
5. Recommend what the paper should report.

## 0. Ground rules adopted
- Reuse `neurips_review/autoresearch/tasks/T1/fn_rejudge.py` verbatim where possible.
- Output dir scoped to T14 (`outputs/T14/`), never write into other agents' dirs.
- No `git checkout` in this tree.
- Judge model `gpt-5.4-mini_2026-03-17` under `load_balancer=trapi`; `execution.max_concurrent=5`.
- Positive controls mandatory before trusting any number.

---

## 1. Mechanism — confirmed, file:line

`src/ctx_editor/identify_false_negatives.py`

- **L190-193** `get_active_messages(trace)` — `return [m for m in messages if m.get("visible", True) and m.get("role") != "log"]`. Filters on the per-message `visible` flag.
- **L228** inside `analyze_sample`: `messages = get_active_messages(trace) if isinstance(trace, dict) else []`
- **L229-230** `user_messages_str = format_user_messages(messages)` / `system_message_str = format_system_message(messages)` — only the *visible* subset reaches the prompt.
- **L96-104** the prompt then asks the judge to evaluate "the UNION of all user messages", and **L106-110** instructs it to mark insufficient if "a critical detail ... is completely absent from ALL user messages".
- **L160-164** `exclusion_reason` → `"user_sim_induced"` when `not user_sim_sufficient`.
- **L419, L426** `compute_adjusted_accuracy` — `adjusted_denominator = total_valid - len(user_sim_induced)`; user-sim-induced samples are *always* dropped from the denominator (no config gate, unlike non-answer-attempts at L427).

So: an arm that hides user turns causes the judge to see a truncated union, conclude the user
never specified the problem, and get the sample deleted from its own denominator. Numerator
(`total_correct`) is untouched. Deleting failures from the denominator only ⇒ accuracy inflates
monotonically with how much user text an arm hides. This is post-treatment conditioning; the
exclusion rate is a function of the treatment.

Confirmed magnitude by T1 on LiC-database: baseline excludes 9% of its failures, AC3-Reset 62%,
summarisation 78%.

TODO next: confirm which strategies actually set `visible=False` on *user* messages (vs only
assistant messages) — that determines which paper cells are affected.

---

## Log

### ~T+35min — mechanism nailed, sharper than T1 stated

The bias is worse than "truncated user history". Two facts combine:

1. `src/ctx_editor/core/trace.py:102-105` — `reset_conversation` marks **every** currently
   visible message invisible, *including user messages*, then appends the new context.
2. `src/ctx_editor/strategies/context_edit_v2.py:117-124` (`_build_edited_context`) — the new
   visible context is `[system, Message(role="compacted conversation", ...), latest user shard]`.
   The user's accumulated specification is carried in the **`"compacted conversation"` role**, not
   in a `user` role.
3. `src/ctx_editor/identify_false_negatives.py:173` — `format_user_messages` keeps only
   `m["role"] == "user"`.

So after a single AC3 reset the sufficiency judge's `{user_messages}` field contains **exactly one
turn** — the latest shard — even though the spec is sitting right there in the compacted message.
The judge is then asked (L100-110) whether "the UNION of all user messages" contains every
critical detail, and told to mark insufficient if a detail "is completely absent from ALL user
messages". Given one shard out of nine, the correct answer to the question it was asked is *no*.
The judge is not malfunctioning; it is being fed a post-treatment input.

Empirical confirmation on real traces (`outputs/T1/main/*/traces/.../<first sample>.json`):

| cell | roles in full trace | roles visible at end |
|---|---|---|
| db_baseline | system 1, user 6, assistant 6 | system 1, **user 6**, assistant 6 |
| db_reset | system 5, user 9, assistant 5, compacted 4 | system 1, **user 1**, assistant 1, compacted 1 |
| db_gated | system 3, user 7, assistant 5, compacted 2 | system 1, **user 1**, assistant 1, compacted 1 |
| db_summarize1 | system 5, user 9, assistant 5, compacted 4 | system 1, **user 1**, assistant 1, compacted 1 |

Then `identify_false_negatives.py:419,426` — `adjusted_denominator = total_valid -
len(user_sim_induced)` — deletes those samples from the denominator only. Numerator untouched.
Every arm that resets therefore gets its failures deleted at a rate the baseline does not.
Note L427: non-answer-attempt exclusion is behind a config flag; user-sim-induced exclusion is
**unconditional**.

### Data recovery
`snapshot.tar.gz` extracted (outputs/, scripts/, docs/) to `/home/t-matthewho/ac3/t14_snapshot/`
(5.0 GB). 558 `false_negatives.json` files across 23 top-level run groups. Shipped exclusion
counts can be read straight out of those files with no LLM calls — that gives the exclusion-rate
table across the whole matrix for free. The arm-symmetric re-judge needs LLM calls and will be
scoped to the cells the paper actually reports.

Note: `outputs/lic_false_negative_analysis/` + `scripts/lic_false_negative_analysis.py` are a
*separate* analysis over Laban's original LiC logs (vanilla gpt-5.2, no context editing). Those
are **not** affected by this bug — with no resets, all messages are visible. Recorded so the
correction is not over-applied.

### ~T+70min — exclusion-rate table across the whole archived matrix (no LLM calls needed)

`survey.py` reads the *shipped* `false_negatives.json` + `run_summary.json` for all 558 archived
runs that have FN analysis. Output `survey.json`.

**Positive controls (stated, as required):**
1. **Reproduce the shipped metric exactly.** For all 499 runs that carry `adjusted_accuracy`,
   `correct / (n_valid − user_sim_induced)` reproduces the shipped value to 1e-6 — **0
   discrepancies**. So my reader is on the right fields and the shipped formula is exactly
   `identify_false_negatives.py:426`.
2. **Cross-file consistency.** `results.json` ↔ `metrics.json` ↔ `run_summary.json` agreement on
   n, correct and accuracy asserted per run — **0 mismatches** (guards the double-write trap).
3. **`metrics.user_sim_induced` vs `false_negatives.json.summary.user_sim_induced`** — 0
   mismatches.
4. **Trap #2 (silent FN no-op) screened.** 0 runs have incorrect samples but 0 analysed; 0 runs
   are all-errored; 0 FN samples errored anywhere. Every archived FN judge is `gpt-5-mini`, which
   *was* served on the endpoints used at the time. **No archived run was produced under the
   trapi/gpt-5-mini no-op condition** — so no archived adjusted number needs excluding on that
   ground. (The no-op trap applies to *new* runs launched tonight under `load_balancer=trapi`.)

**Exclusion rate by arm family × task, pooled over all archived runs** (analysed = incorrect
samples the judge saw; excl = flagged user-sim-induced and deleted from the denominator):

| arm family | task | analysed | excl | excl % | raw acc | shipped adj acc | inflation |
|---|---|---|---|---|---|---|---|
| **Baseline** | math_v2 | 340 | 90 | 26.5% | 70.2% | 76.1% | +6.0 |
| **Baseline** | code_v2 | 550 | 213 | 38.7% | 53.3% | 65.1% | +11.8 |
| **Baseline** | database_v2 | 901 | 36 | **4.0%** | 19.3% | 19.9% | +0.6 |
| **Baseline** | actions_v2 | 166 | 15 | **9.0%** | 84.2% | 85.4% | +1.2 |
| **OmitAssistant** (no reset) | math_v2 | 73 | 5 | 6.8% | 84.3% | 85.2% | +0.9 |
| **OmitAssistant** | code_v2 | 119 | 42 | 35.3% | 68.4% | 77.0% | +8.6 |
| **OmitAssistant** | database_v2 | 305 | 4 | 1.3% | 33.8% | 34.1% | +0.3 |
| **OmitAssistant** | actions_v2 | 43 | 9 | 20.9% | 90.4% | 92.3% | +1.8 |
| **AC3-Augment / S1** (no reset) | math_v2 | 86 | 5 | 5.8% | 81.7% | 82.6% | +0.9 |
| **AC3-Augment / S1** | code_v2 | 139 | 52 | 37.4% | 64.5% | 74.4% | +9.9 |
| **AC3-Augment / S1** | database_v2 | 242 | 3 | 1.2% | 49.7% | 50.0% | +0.3 |
| **AC3-Augment / S1** | actions_v2 | 50 | 12 | 24.0% | 88.9% | 91.3% | +2.4 |
| **AC3-Reset** (resets) | math_v2 | 65 | 54 | **83.1%** | 84.3% | 96.7% | **+12.4** |
| **AC3-Reset** | code_v2 | 120 | 111 | **92.5%** | 66.4% | 96.3% | **+30.0** |
| **AC3-Reset** | database_v2 | 205 | 121 | **59.0%** | 53.4% | 73.7% | **+20.3** |
| **AC3-Gated-Reset** (resets) | math_v2 | 25 | 25 | **100.0%** | 82.6% | 100.0% | **+17.4** |
| **AC3-Gated-Reset** | code_v2 | 50 | 43 | **86.0%** | 55.8% | 90.0% | **+34.2** |
| **AC3-Gated-Reset** | database_v2 | 74 | 47 | **63.5%** | 49.7% | 73.0% | **+23.3** |
| **AC3-Rewrite** (resets) | math_v2 | 426 | 425 | **99.8%** | 78.6% | 99.7% | **+21.0** |
| **AC3-Rewrite** | code_v2 | 828 | 768 | **92.8%** | 50.0% | 93.2% | **+43.2** |
| **AC3-Rewrite** | database_v2 | 1306 | 842 | **64.5%** | 37.2% | 62.5% | **+25.3** |
| **AC3-Rewrite** | actions_v2 | 518 | 516 | **99.6%** | 75.3% | 99.9% | **+24.5** |

The split is **exactly** the reset/no-reset split, which is the prediction the mechanism makes:

- **Arms that never call `reset_conversation`** — Baseline (`BaselineStrategy`), OmitAssistant
  (`assistant_omit.py:50-51`, filters the returned list, never touches `visible`), AC3-Augment /
  S1 (`append_analysis.py:115,119,160`, returns `get_active_messages()` unchanged) — exclude
  **1–39%** and inflate **+0.3 to +11.8 pp**.
- **Arms that call `reset_conversation`** — AC3-Reset / AC3-Gated-Reset
  (`context_edit_v2.py:195`), AC3-Rewrite (`context_compaction.py:340`), and also
  summarisation (`summarization.py:212`), MT-OSC (`mtosc.py:324`), ERGO
  (`ergo_restart.py:181`), Concat-User (`prior_work_baselines.py:98`) — exclude **59–100%** and
  inflate **+12.4 to +43.2 pp**.

Several cells reach **100% exclusion**: AC3-Gated-Reset on math_v2 (25/25) and the GEPA candidate
sweep on math_v2 (240/240) have *every single failure* deleted, i.e. shipped adjusted accuracy
is 100.0% by construction. That is the reductio: the metric cannot report a failure for an arm
that resets aggressively enough.

Residual, non-treatment part of the exclusion rate is visible in the no-reset arms and is
task-dependent (code_v2 ~35-39%, math_v2 ~6-27%, database_v2 ~1-4%). Interpretation: some of the
code_v2 exclusions are genuine (the LiC code shards really do underspecify), which is why raw is
not automatically the "true" number either — see §recommendation.

### ~T+75min — provenance: the published cells are NOT recoverable

Located `tab:main` at `writing/overleaf_repo/neurips/neurips_2026_conference.tex:252-275`
(label `tab:main`). Metric disclosure at `:454`, `:478`, and critically `:480`: *"Instances
flagged as insufficient are excluded from accuracy calculations."* So the paper's headline LiC
table **is** the shipped `adjusted_accuracy` for 9 of its 10 rows; the Gated-Reset row (`:489`,
`:508`) is raw n=25. **The table currently mixes the two metrics in the same column.**

Per-cell run dirs are recorded in `docs/reports/v8_batch_results.md:159-206`,
`docs/sans_issue_injection_redux.md:171-182`, `docs/reports/prior_work_baselines.md:170-179`,
`docs/reports/v9_experiments.md:95-98` — they name `outputs/2026-03-16/19-*`,
`outputs/2026-03-21/05-*` and `10-3*`, `outputs/2026-03-26/04-*`.

**None of those directories exist on this machine, and none are in `snapshot.tar.gz`.** The
snapshot has no `2026-03-21` at all; its `2026-03-16` stops at `16-16-14` and its `2026-03-26`
has only `12-*` and `21-*`. `supplementary.tar.gz` is HLE/collabmem, not LiC outputs.
Two rows have no provenance record at all: ERGO, and Gated-Reset runs 2-3 (the cited
`docs/multi_run_variance_2026-05-07.md` was never committed).

**Consequence for T14's scope:** the arm-symmetric re-judge cannot be run on the exact published
traces. Re-planned deliverable (recorded so this is not mistaken for scope creep):
 (a) exclusion-rate + inflation table across the full archived matrix — done above, and it is
     the load-bearing evidence, since it needs no traces;
 (b) arm-symmetric re-judge on the largest *available* LiC runs with traces, same tasks, same
     arms, to establish the correction factor empirically;
 (c) reconstruct the published cells' raw counterparts from the fractions recorded in the
     provenance docs where those docs state numerator/denominator.

### ~T+105min — IMPORTANT correction to the premise: `tab:main` is far less exposed than the pipeline is

Chasing the published denominators produced a finding that changes the headline. Two separate
FN mechanisms exist in this project and they must not be conflated.

**Mechanism A — pool-level pre-filter (arm-symmetric, methodologically sound).**
`data/baseline_traces_v2/{math,code,database}_false_negatives.json` are FN analyses run **once,
on the baseline traces**, and used to prune the replay pool before any arm runs. Verified counts:

| task | replay prefixes available | user_sim_induced pruned | n in paper |
|---|---|---|---|
| math | 23 (`data/baseline_traces_v2/math`) | 3 (`GSM8K/1287, /267, /534`) | **20** ✓ |
| code | 25 (`data/baseline_traces_v2/code`) | 6 (`HumanEval/113`, `livecodebench/2791,2850,2873,2916,2920`) | **19** ✓ |
| database | 25 | 0 | **25** ✓ |
| actions | 25 (`data/baseline_traces/actions`) | (2, no file recovered) | **23** ✓ |

These four numbers reproduce `tab:main`'s denominators exactly. Because the filter is computed
from *baseline* traces (nothing hidden) and applied *identically to every arm*, it is the
arm-symmetric correction, done right, before the fact. **This part of the paper's protocol is
fine and should be defended, not retracted.**

**Mechanism B — per-run, per-arm `adjusted_accuracy` (the biased one).** This is the one
audited above. Its exposure inside `tab:main` is small: across the 40 cells, the observable
denominators deviate from the pool n by **at most 1 sample**, and only in four cells
(AO/code 14/18, Concat-User/math 16/19, AC3-Augment/code 10/18, AC3-Reset/code 11/18).
`docs/reports/prior_work_baselines.md:97` confirms two of them explicitly: *"Omit-assistant code
had 1 additional user-sim exclusion (14/18 adj = 77.8%); concatenate-user math had 1 additional
(16/19 adj = 84.2%)."* `docs/reports/v8_batch_results.md:53` shows the other route to a shrunken
denominator is **timeout errors** (code S1.5 ran with n=16, S1.5+mem n=17), so at least some of
the 18s may be error-driven rather than FN-driven. The exact runs are gone, so this cannot be
settled from disk; both readings cap the per-cell effect at ~1 sample = **+3 to +4.2 pp**.

Note which way those four cells cut: **two of the four favour prior work** (AO +4.1 pp,
Concat-User +4.2 pp) and two favour us (AC3-Augment +3.0 pp, AC3-Reset +3.2 pp on code). The
adjustment in `tab:main` is not systematically self-serving.

**Where the real exposure is.** `neurips_review/autoresearch/tasks/RECON/worklog.md:115` records
that the *canonical headline number* for current work is
`run_summary.json → metrics.adjusted_accuracy`, and that **the rebuttal quotes it** ("raw 95.00%
→ adjusted 100.00% for reset rep2"). That number is Mechanism B, unfiltered, and the archived
matrix shows it running +12 to +43 pp for reset arms. So:

- `tab:main` (NeurIPS submission): exposure ≤ ~1 sample/cell, mixed direction. Low.
- Anything quoting `adjusted_accuracy` from a *run* — the rebuttal, the mega-table, arXiv
  updates, tonight's new runs — exposure +12 to +43 pp, always in our favour. **High.**

Next: audit the rebuttal artifacts for quoted adjusted numbers.

### ~T+125min — exposure map of the *other* tables, and rebuttal status

- **`tab:megatable`** is built by `scripts/build_mega_table.py:87-96`, which computes
  `n_correct / n_total` straight off `results.json`. That is **raw accuracy**; the mega-table is
  not exposed to this bug.
- **Rebuttal (v5)** already switched everything to raw and discloses the bias:
  `neurips_review/replies/v5/00_general_response.md:5,85,108`,
  `01_reviewer_iNYK.md:61`, `02_reviewer_Vg97.md:56`, `04_response_to_AC.md:48`,
  `README.md:105` ("Never quote `adjusted_accuracy` for a context-editing arm"). The v4 draft
  *was* exposed — it quoted AC3-Reset 100.0 ± 0.0 from
  `neurips_review/experiments/exp1_reps_results.txt`, where rep2 reset reads
  `Accuracy 95.00% (38/40)` / `Adjusted Accuracy 100.00% (38/38)` and rep3 reset reads
  `87.50% (35/40)` / `100.00% (35/35)` — 5 of 5 failures deleted. Already corrected.
- **The live hazard is the paper's *protocol text*, not most of its numbers.**
  `neurips_2026_conference.tex:478-480` describes the biased procedure as the method:
  *"we collate all user simulator messages … Instances flagged as insufficient are excluded from
  accuracy calculations."* As implemented, "all user simulator messages" means "the visible
  ones", which for a reset arm is one shard. A reviewer who reimplements what `:478-480` says
  will not reproduce our denominators; a reviewer who reimplements what the code does will find
  a metric that reports 100% for any arm that resets hard enough.

### Rejudge run — controls firing correctly mid-flight
`rejudge.py` on `post_neurips_ac3_phase1` (deepseek-v4-flash; 4 tasks × 6 arms × 3 replicate
runs = 72 cells, 1217 incorrect samples). Judge `gpt-5.4-mini_2026-03-17`, trapi, concurrency 5.
Live examples:

```
append_analysis_code_v2_conv0   shipped-excl 4/21  symmetric-excl 4/21   userturns seen 5.76/5.81
baseline_database_v2_conv2      shipped-excl 0/32  symmetric-excl 0/32   userturns seen 4.25/4.25
baseline_math_v2_conv1          shipped-excl 0/11  symmetric-excl 0/11   userturns seen 6.73/6.73
ac3_rewrite_lic_actions_v2_conv0 shipped-excl 20/20 symmetric-excl 0/20  userturns seen 5.35/6.35
```
On non-reset arms the shipped and symmetric inputs are identical, so shipped-vs-symmetric
agreement there is a **direct measurement of judge-model drift** (gpt-5-mini → gpt-5.4-mini) —
and it is ~0. On the reset arm the shipped judge excluded 20/20 and the symmetric judge 0/20.
That is the whole finding in one line.

### ~T+150min — ⚠ TWO QUALITATIVE CONCLUSIONS FLIP. Full corrected matrix below.

Arm-symmetric re-judge complete on `post_neurips_ac3_phase1`: deepseek-v4-flash, 4 tasks × 6
arms × 3 replicate runs = 72 cells, **1217 incorrect samples re-judged, 0 errors, 0 missing
traces**. Judge `gpt-5.4-mini_2026-03-17` on trapi, concurrency 5.
Artifacts: `rejudge_post_neurips_ac3_phase1_symmetric.json`, `corrected_matrix.json`,
`corrected_matrix.txt`.

**Controls, stated:**
- **C1 — judge-model drift is not the effect.** On the three arms that never reset, the
  symmetric input *is* the shipped input, so any shipped-vs-symmetric difference is pure
  gpt-5-mini→gpt-5.4-mini drift (and the forced `temperature=1.0` for gpt-5-class judges).
  Measured: **34 decision changes over 610 judged samples = 5.6%**. On the three reset arms the
  same comparison gives **448 over 607 = 73.8%**. 13× separation, and the 5.6% floor bounds how
  much of the reset-arm effect could be judge noise.
- **C2 — the mechanism, measured.** Mean *user turns the judge actually saw* per sample:
  symmetric view 4.9–5.4 for every arm (flat by construction). Shipped view for AC3-Rewrite:
  **1.00**. Exactly one shard, exactly as `format_user_messages` + `reset_conversation` predict.
- **C3 — shipped numbers reproduced.** `correct/(n − shipped_excluded)` reproduces every
  archived `adjusted_accuracy` to 1e-6 across 499 runs (see T+70min entry).

#### Corrected matrix — shipped-adjusted vs raw vs arm-symmetric

n and correct are pooled over the 3 replicate runs per cell.

| arm | task | n | correct | RAW | shipped excl | SHIPPED-ADJ | sym excl | SYM-ADJ | shipped−raw | sym−raw |
|---|---|---|---|---|---|---|---|---|---|---|
| Baseline | math | 144 | 104 | 72.2% | 3/40 | 73.8% | 3/40 | 73.8% | +1.5 | +1.5 |
| Baseline | code | 113 | 39 | 34.5% | 11/74 | 38.2% | 5/74 | 36.1% | +3.7 | +1.6 |
| Baseline | database | 147 | 33 | 22.4% | 1/114 | 22.6% | 2/114 | 22.8% | +0.2 | +0.3 |
| Baseline | actions | 150 | 114 | 76.0% | 3/36 | 77.6% | 0/36 | 76.0% | +1.6 | +0.0 |
| AO | math | 144 | 124 | 86.1% | 1/20 | 86.7% | 3/20 | 87.9% | +0.6 | +1.8 |
| AO | code | 113 | 68 | 60.2% | 11/45 | 66.7% | 6/45 | 63.6% | +6.5 | +3.4 |
| AO | database | 147 | 67 | 45.6% | 1/80 | 45.9% | 1/80 | 45.9% | +0.3 | +0.3 |
| AO | actions | 150 | 129 | 86.0% | 7/21 | 90.2% | 2/21 | 87.2% | +4.2 | +1.2 |
| AC3-Augment | math | 144 | 121 | 84.0% | 1/23 | 84.6% | 1/23 | 84.6% | +0.6 | +0.6 |
| AC3-Augment | code | 113 | 66 | 58.4% | 9/47 | 63.5% | 6/47 | 61.7% | +5.1 | +3.3 |
| AC3-Augment | database | 147 | 61 | 41.5% | 1/86 | 41.8% | 1/86 | 41.8% | +0.3 | +0.3 |
| AC3-Augment | actions | 150 | 126 | 84.0% | 7/24 | 88.1% | 2/24 | 85.1% | +4.1 | +1.1 |
| **AC3-Reset** | math | 144 | 118 | 81.9% | **25/26** | **99.2%** | 4/26 | 84.3% | **+17.2** | +2.3 |
| **AC3-Reset** | code | 113 | 67 | 59.3% | **42/46** | **94.4%** | 7/46 | 63.2% | **+35.1** | +3.9 |
| **AC3-Reset** | database | 147 | 72 | 49.0% | **44/75** | **69.9%** | 1/75 | 49.3% | **+20.9** | +0.3 |
| **AC3-Reset** | actions | 150 | 125 | 83.3% | **24/25** | **99.2%** | 1/25 | 83.9% | **+15.9** | +0.6 |
| **AC3-Gated-Reset** | math | 144 | 119 | 82.6% | **25/25** | **100.0%** | 3/25 | 84.4% | **+17.4** | +1.8 |
| **AC3-Gated-Reset** | code | 113 | 63 | 55.8% | **43/50** | **90.0%** | 5/50 | 58.3% | **+34.2** | +2.6 |
| **AC3-Gated-Reset** | database | 147 | 73 | 49.7% | **47/74** | **73.0%** | 0/74 | 49.7% | **+23.3** | +0.0 |
| **AC3-Gated-Reset** | actions | 150 | 128 | 85.3% | **21/22** | **99.2%** | 1/22 | 85.9% | **+13.9** | +0.6 |
| **AC3-Rewrite** | math | 144 | 106 | 73.6% | **37/38** | **99.1%** | 2/38 | 74.6% | **+25.5** | +1.0 |
| **AC3-Rewrite** | code | 113 | 32 | 28.3% | **75/81** | **84.2%** | 9/81 | 30.8% | **+55.9** | +2.5 |
| **AC3-Rewrite** | database | 147 | 41 | 27.9% | **61/106** | **47.7%** | 1/106 | 28.1% | **+19.8** | +0.2 |
| **AC3-Rewrite** | actions | 150 | 111 | 74.0% | **39/39** | **100.0%** | 1/39 | 74.5% | **+26.0** | +0.5 |

Inflation for no-reset arms: **+0.2 to +6.5 pp**. For reset arms: **+13.9 to +55.9 pp**.
After the correction, adjusted ≈ raw everywhere (**+0.0 to +3.9 pp**, uniform across arms) —
which is the definition of the metric behaving.

#### ⚠ FLIPS — two of them

Δ vs Baseline, per task:

| arm | task | Δ raw | Δ shipped-adj | Δ sym-adj | |
|---|---|---|---|---|---|
| AC3-Reset | math / code / database / actions | +9.7 / +24.8 / +26.5 / +7.3 | +25.4 / +56.1 / +47.3 / +21.7 | +10.5 / +27.1 / +26.6 / +7.9 | holds |
| AC3-Gated-Reset | math / code / database / actions | +10.4 / +21.2 / +27.2 / +9.3 | +26.2 / +51.8 / +50.4 / +21.7 | +10.6 / +22.2 / +26.9 / +9.9 | holds |
| **AC3-Rewrite** | **code** | **−6.2** | **+46.0** | **−5.3** | **FLIP** |
| **AC3-Rewrite** | **actions** | **−2.0** | **+22.4** | **−1.5** | **FLIP** |
| AC3-Rewrite | math / database | +1.4 / +5.4 | +25.3 / +25.1 | +0.9 / +5.3 | holds (barely) |

**AC3-Rewrite beats baseline in all four cells under the shipped metric and LOSES to baseline in
two of four under the correction.** On code it goes from +46.0 pp ahead to 5.3 pp *behind*. That
is a win turning into a loss, driven entirely by the metric.

**Scope of the flip — do not overstate it.** `tab:main` has **no AC3-Rewrite LiC row**, and
`tab:megatable`, where AC3-Rewrite does appear, is computed from raw
(`scripts/build_mega_table.py:87-96`). So this flip is **not currently a published error**. It is
a demonstration that the metric is capable of manufacturing a win from a loss, on our own arm,
on our own data — which is the strongest possible argument for removing it, and the thing a
reviewer would find if they ran our pipeline.

**Conclusions that do hold:** AC3-Reset and AC3-Gated-Reset beat Baseline in **every one of the
8 cells** under raw, shipped-adjusted and arm-symmetric alike. The Gated-vs-Reset ordering is
preserved cell-for-cell across all three metrics (Gated ahead on math/database/actions, Reset
ahead on code) — the one exception is that the shipped metric ties them on actions (99.2 vs
99.2) purely because both are pinned near the 100% ceiling by exclusion.

### ~T+185min — `--mode visible` control complete; clean 2-step decomposition

Both re-judge modes done (72/72 each, 0 errors, 0 missing traces). Holding the judge fixed at
`gpt-5.4-mini` and toggling only visibility separates the two effects:

| arm | resets? | judged | shipped (5-mini, visible) | visible (5.4-mini, visible) | symmetric (5.4-mini, all) | Δ judge | Δ visibility | turns seen vis→sym |
|---|---|---|---|---|---|---|---|---|
| AC3-Augment | no | 180 | 18 | 10 | 10 | −4.4% | **+0.0%** | 5.09 → 5.06 |
| AO | no | 166 | 20 | 12 | 12 | −4.8% | **+0.0%** | 4.90 → 4.88 |
| Baseline | no | 264 | 18 | 7 | 10 | −4.2% | **+1.1%** | 5.38 → 5.35 |
| AC3-Gated-Reset | yes | 171 | 136 | 88 | 9 | −28.1% | **−46.2%** | 1.18 → 5.15 |
| AC3-Reset | yes | 172 | 135 | 94 | 13 | −23.8% | **−47.1%** | 1.18 → 5.05 |
| AC3-Rewrite | yes | 264 | 212 | 150 | 13 | −23.5% | **−51.9%** | 1.00 → 5.20 |

Pooled: judge swap −4.4% / −24.9% (no-reset / reset); **visibility +0.5% / −48.9%**.
The null control passes exactly: where the two inputs are the same text, "changing visibility"
moves +0.0 to +1.1%. Where the arm resets, it moves ~half of all judged samples.

Honest caveat recorded: gpt-5.4-mini is more lenient than gpt-5-mini *given a single shard*
(−25% on reset arms), so the shipped number is also judge-sensitive. That is a second defect of
the same root cause — the metric is unstable because its input is degenerate — not a reason to
discount the first.

### Deliverables written
`RESULTS.md` in this directory: mechanism (file:line), exclusion-rate table over 558 archived
runs, `tab:main` provenance + the two-FN-mechanism distinction, the corrected 6-arm × 4-task
matrix with all three metrics, the flip analysis, controls, and the recommendation.

**Headline for the operator:** two flips, both on **AC3-Rewrite** (code +46.0 → −5.3;
actions +22.4 → −1.5 vs baseline). Neither is in a currently-published table — `tab:main` has no
AC3-Rewrite LiC row and `tab:megatable` is computed from raw. **AC3-Reset and AC3-Gated-Reset
beat baseline in all 8 cells under every metric**, and the Gated-vs-Reset ordering holds.
Separately: `tab:main`'s ERGO row is scored on the *unfiltered* replay pools (23/25/25/25) while
every other row uses the filtered pools (20/19/25/23) — a comparability defect worth up to
~14 pp *against* prior work, larger than the FN-adjustment effect and visible from the printed
percentages alone.
