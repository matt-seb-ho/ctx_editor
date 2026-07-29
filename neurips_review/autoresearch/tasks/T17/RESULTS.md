# T17 — The `tab:main` denominator audit, and the corrected ERGO row

**Bottom line.** T14's finding is confirmed and is worse than the "bound" framing suggested.
ERGO is the only row in `tab:main` scored on **unfiltered** replay pools (23/25/25/25) while
every other row is on the filtered pools (20/19/25/23). Placing ERGO on the same pools moves it
**up** by up to +10.4 / +13.9 / 0.0 / +4.2 pp, while four *other* cells (AO/code,
Concat-User/math, AC3-Augment/code, AC3-Reset/code) move **down** by 3.0–4.2 pp. Under the point
estimate the paper's ordering does not survive: **ERGO beats AC3-Reset on math (80.0 vs 75.0),
ties it on code (57.9) and on actions (52.2), and ties AC3-Gated-Reset on math (80.0 vs 80.0).**
Only the database column is untouched, and there AC3 still wins by a mile.

**The corrected numerators cannot be recovered from disk.** The ERGO runs
(`outputs/2026-05-01/23-*`), the AO/Concat-User runs (`outputs/2026-03-21/05-*`) and the whole v8
batch (`outputs/2026-03-16/19-*` onward) are absent from every archive we hold. The correction is
therefore an *interval*, with a defensible point estimate; the only way to make it a measurement
is to re-run ERGO on the filtered pools — 87 last-turn replays, a few dollars. **Recommended.**

---

## 1. The mechanism, with file:line

`tab:main`'s denominators come from a **pool-level pre-filter** — the thing T14 correctly told us
to defend. Three lines:

| # | Location | Behaviour |
|---|---|---|
| 1 | `src/ctx_editor/execution/replay.py:21-56` (`load_user_sim_induced_ids`) | Given `execution.replay_source=<dir>`, looks for `<dir>/false_negatives.json`, else `<parent>/<name>_false_negatives.json`; returns `summary.user_sim_induced_ids`. Returns `set()` if neither file exists. |
| 2 | `src/ctx_editor/run_experiment.py:441-470` | Drops those IDs from `samples`, re-emits each as a `skip_result` with `is_correct=False`, `num_turns=0`, `trace={"messages": []}`, and writes it to `traces/` via `log_conversation`. |
| 3 | `src/ctx_editor/run_experiment.py:528,542-543` | `total = len(valid_results)`; skips are **not** in `results`, so `metrics.total_samples` is the *filtered* n. |

Correct (uniform) denominators are therefore `|pool| − |user_sim_induced_ids|`:

| task | pool dir | pool size | pruned IDs | correct n |
|---|---|---|---|---|
| math | `data/baseline_traces_v2/math` | 23 | 3 — `sharded-GSM8K/{1287,267,534}` | **20** |
| code | `data/baseline_traces_v2/code` | 25 | 6 — `sharded-HumanEval/113`, `sharded-livecodebench/{2791,2850,2873,2916,2920}` | **19** |
| database | `data/baseline_traces_v2/database` | 25 | 0 | **25** |
| actions | `data/baseline_traces/actions` | 25 | **no sidecar exists** — see §1a | **23** (by convention) |

### 1a. The `actions` column has weaker provenance than the other three

There has never been an `actions_false_negatives.json`: not in git history
(`git log --all -- "data/baseline_traces*false_negatives*"` returns only math/code/database and
the htn50_52 sidecars), not in `snapshot.tar.gz` (69,738-entry index), not on disk. Every archived
actions run replaying from `data/baseline_traces/actions` reports **n=25, `user_sim_skipped=0`**
(7 such runs). The paper's actions n=23 is the *ad hoc* "common 23-sample" normalization
documented at `docs/reports/v10_paper_updates.md:24-26` and confessed in the paper itself at
`neurips_2026_conference.tex:508-510` ("applied non-uniformly across runs"). One earlier run
(`outputs/2026-03-13/02-09-40`) reached n=23 through **2 errored conversations**, not a filter.
The actions column is internally consistent at n=23 for nine of ten rows; it is just not
reproducible from an artifact.

### 1b. Why ERGO's denominators are exactly the unfiltered pool sizes

`load_baseline_traces` (`replay.py:78-88`) globs `<source>/**/*.json` and keys on `sample_id`.
A *run directory* contains a trace file for every pruned sample — an empty stub written by the
skip path in (2). So replaying from a run directory silently re-admits the pruned items:

```
math 20+3 = 23   code 19+6 = 25   database 25+0 = 25   actions 23+2 = 25
```

which is ERGO's row, cell for cell. Whether ERGO's run used a run directory or a checkout without
the sidecars, the effect is identical: **the pruned items were attempted and counted against
ERGO, and against no one else.**

---

## 2. Row-by-row denominator audit

Denominators back-inferred by exhaustive rational search over all `n/d`, `d ∈ [15,30]`, matching
each printed percentage to 0.1pp; then cross-checked against an independent source document for
every row. `T` = tex line in `writing/overleaf_repo/neurips/neurips_2026_conference.tex`.

| Row | math | code | database | actions | denominator used | should be | source of truth |
|---|---|---|---|---|---|---|---|
| Baseline (full context) | 12/20 | 3/19 | 1/25 | 8/23 | 20/19/25/23 ✓ | same | `docs/reports/v8_batch_results.md:27,29`; T:262 |
| ⤷ + Memory | 11/20 | 4/19 | 1/25 | 8/23 | 20/19/25/23 ✓ | same | `v8_batch_results.md:30`; T:263 |
| AO (Huang) | 17/20 | **14/18** | 8/25 | 19/23 | 20/**18**/25/23 ✗ | 20/**19**/25/23 | `docs/reports/prior_work_baselines.md:95,98`; T:264 |
| Concat User (Laban) | **16/19** | 13/19 | 8/25 | 20/23 | **19**/19/25/23 ✗ | **20**/19/25/23 | `prior_work_baselines.md:96,98`; T:265 |
| **ERGO (Khalid)** | **16/23** | **11/25** | 3/25 | **12/25** | **23/25/25/25** ✗✗ | **20/19/25/23** | overleaf commit `d856247` msg; T:266 |
| AC3-Augment | 16/20 | **10/18** | 8/25 | 11/23 | 20/**18**/25/23 ✗ | 20/**19**/25/23 | `v8_batch_results.md:31`; T:269 |
| ⤷ + Memory | 18/20 | 13/19 | 11/25 | 11/23 | 20/19/25/23 ✓ | same | `v8_batch_results.md:32`; T:270 |
| AC3-Reset | 15/20 | **11/18** | 12/25 | 12/23 | 20/**18**/25/23 ✗ | 20/**19**/25/23 | `docs/sans_issue_injection_redux.md:35-38`; T:271 |
| ⤷ + Memory | 17/20 | 13/19 | 11/25 | 12/23 | 20/19/25/23 ✓ | same | `sans_issue_injection_redux.md:46-51`; T:272 |
| AC3-Gated-Reset (mean N=3) | 15,16,17 /20 | 13/**18**, 12/19, 11/19 | 11,8,10 /25 | 17,14,15 /**25** | 20/**18–19**/25/**25** ✗ | 20/**19**/25/**23** | T:273; per-run values at T:496-499 |

**Two distinct defects.**

* **D1 — ERGO, and only ERGO, is on unfiltered pools.** 3 of 4 cells affected. Moves ERGO
  **down** relative to everyone else. This is the reviewer-legible one: `16/23`, `11/25`, `12/25`
  are recoverable from the printed percentages alone by anyone with a calculator, and the
  denominators visibly disagree with the row above and below.
* **D2 — four cells sit one sample *below* the pool denominator**, and the Gated-Reset actions row
  sits two samples *above* it. Per `prior_work_baselines.md:98` the AO/code and Concat/math drops
  are the per-run `adjusted_accuracy` that T14 recommends deleting; per
  `sans_issue_injection_redux.md:37` the code n=18s are at least partly timeout-driven. This
  defect is roughly self-cancelling — two of the four favour prior work, two favour us.

The Gated-Reset **actions** cell at n=25 is the one place the table is unfair **to us** (T:508-510
discloses it), and the Gated-Reset **code** row mixes n=18 and n=19 inside a single mean.

---

## 3. Corrected `tab:main`, side by side

Point estimate assumes **k = 0**: the pruned items, which are pruned precisely because the union
of user shards does not contain a critical fact, were failures for the arm that was forced to
attempt them. Justification and the interval are in §4.

| Strategy | Math pub → corr | Code pub → corr | Database pub → corr | Actions pub → corr |
|---|---|---|---|---|
| Baseline (full context) | 60.0 → **60.0** | 15.8 → **15.8** | 4.0 → **4.0** | 34.8 → **34.8** |
| ⤷ + Memory | 55.0 → **55.0** | 21.1 → **21.1** | 4.0 → **4.0** | 34.8 → **34.8** |
| AO ◇ | 85.0 → **85.0** | 77.8 → **73.7** (−4.1)† | 32.0 → **32.0** | 82.6 → **82.6** |
| Concat User ◇ | 84.2 → **80.0** (−4.2)† | 68.4 → **68.4** | 32.0 → **32.0** | 87.0 → **87.0** |
| **ERGO** | 69.6 → **80.0** (**+10.4**)\* | 44.0 → **57.9** (**+13.9**)\* | 12.0 → **12.0** | 48.0 → **52.2** (**+4.2**)\* |
| AC3-Augment | 80.0 → **80.0** | 55.6 → **52.6** (−3.0)† | 32.0 → **32.0** | 47.8 → **47.8** |
| ⤷ + Memory | 90.0 → **90.0** | 68.4 → **68.4** | 44.0 → **44.0** | 47.8 → **47.8** |
| AC3-Reset | 75.0 → **75.0** | 61.1 → **57.9** (−3.2)† | 48.0 → **48.0** | 52.2 → **52.2** |
| ⤷ + Memory | 85.0 → **85.0** | 68.4 → **68.4** | 44.0 → **44.0** | 52.2 → **52.2** |
| AC3-Gated-Reset ‡ | 80.0 → **80.0** | 64.4 → **63.2** (−1.2)† | 38.7 → **38.7** | 61.3 → **66.7** (+5.4)\* |

\* cell whose denominator was the unfiltered pool; corrected value is the **top** of the interval
in §4. † cell that had one sample dropped below the pool denominator; corrected value restores it
as a failure (bottom of its interval). ‡ mean over N=3.

Ten of forty cells move. Seven of the ten cells that move are on rows that are **not** ours.

---

## 4. Intervals — what is measured, what is assumed

| Row · task | published | corrected interval | point est. | what the interval spans |
|---|---|---|---|---|
| **ERGO · math** | 69.6 (16/23) | **[65.0, 80.0]** | **80.0** | how many of the 3 pruned math items ERGO solved (0–3) |
| **ERGO · code** | 44.0 (11/25) | **[26.3, 57.9]** | **57.9** | 0–6 of the 6 pruned code items |
| ERGO · database | 12.0 (3/25) | 12.0 — exact | 12.0 | nothing pruned; already correct |
| **ERGO · actions** | 48.0 (12/25) | **[43.5, 52.2]** | **52.2** | 0–2 of the 2 excluded actions items |
| AC3-Gated-Reset · actions | 61.3 | [58.0, 66.7] | 66.7 | 0–2 per run; run 1 is **known** to be 0 (T:508) |
| AC3-Gated-Reset · code | 64.4 | [63.2, 64.4] | 63.2 | whether run 1's dropped item was an error |
| AO · code | 77.8 | [73.7, 77.8] | 73.7 | whether the dropped item was an FN adjustment (restore) or an error (keep) |
| Concat User · math | 84.2 | [80.0, 84.2] | 80.0 | same |
| AC3-Augment · code | 55.6 | [52.6, 55.6] | 52.6 | same |
| AC3-Reset · code | 61.1 | [57.9, 61.1] | 57.9 | same |

**Why k = 0 is the right point estimate, and why it is still an assumption.**

*For:* every pruned ID's `missing_elements` is a semantic omission or an outright contradiction in
the user shards — GSM8K/1287 never states the 12-year-old is the *younger* brother and asserts the
opposite; lcb/2920 never states the array is circular; lcb/2916 mis-states the split condition.
ERGO's operating context is an LLM rewrite of exactly those user messages, so the fact is not
available to it by construction. The one directly observable case agrees: the Gated-Reset headline
actions run scored **17/25 raw and 17/23 filtered** (`tex:508`, `v10_paper_updates.md:24-26`) —
both excluded items were failures, k = 0. So did the baseline run that generated the math pool
(13/23 correct, all 3 pruned IDs among its failures).

*Against:* two of the three math items are *contradictions* rather than pure omissions, and a
solver that resolves the contradiction the intended way lands on the right answer. Across 870
archived attempts on those 9 IDs the solve rate is 32.9% — **that number is not admissible
evidence** (those runs use different shardings, where the missing fact may be present), but it is
a reason not to assert k = 0 as fact. On code the interval is 31.6pp wide, which is too wide to
publish as a point estimate at all.

**Recommendation: re-run ERGO on the filtered pools.** `ctx-editor experiment=ergo task=dev_{math,code,database,actions} model=gpt5_mini execution.replay_turns=1 execution.replay_source=data/baseline_traces_v2/{task}` — 87 last-turn replays, ~\$0.20, and the pool filter then fires automatically. This is the only way to turn §3 into a measurement rather than a defensible estimate, and it is cheap enough that shipping the estimate instead would be hard to defend.

---

## 5. ⚠ Conclusions that change

Comparisons at the point estimate, ERGO vs the no-memory AC3 operators (the like-for-like
comparison — ERGO has no memory component):

| task | ERGO pub → corr | vs AC3-Augment | vs AC3-Reset | vs AC3-Gated-Reset |
|---|---|---|---|---|
| math | 69.6 → **80.0** | 80.0 → **TIE** (was AC3 +10.4) | 75.0 → **ERGO +5.0** (was AC3 +5.4) | 80.0 → **TIE** (was AC3 +10.4) |
| code | 44.0 → **57.9** | 52.6 → **ERGO +5.3** (was AC3 +11.6) | 57.9 → **TIE** (was AC3 +17.1) | 63.2 → AC3 +5.3 (was +20.4) |
| database | 12.0 → **12.0** | 32.0 → AC3 +20.0 | 48.0 → AC3 +36.0 | 38.7 → AC3 +26.7 |
| actions | 48.0 → **52.2** | 47.8 → **ERGO +4.4** (was ERGO +0.2) | 52.2 → **TIE** (was AC3 +4.2) | 66.7 → AC3 +14.5 (was +13.3) |

**Yes — ERGO ties or beats an AC3 operator on three of four tasks after the correction.**

1. **ERGO beats AC3-Reset on math**, 80.0 vs 75.0. Published, it lost by 5.4pp.
2. **ERGO ties AC3-Reset on code (57.9) and on actions (52.2)**, and ties `AC3-Reset + Memory` on
   actions (52.2) as well.
3. **ERGO ties AC3-Gated-Reset — the paper's recommended default — on math**, 80.0 vs 80.0.
   Published, Gated-Reset led by 10.4pp. Gated-Reset's only remaining strict wins over ERGO are
   code (+5.3), database (+26.7) and actions (+14.5).
4. **ERGO beats AC3-Augment on code (+5.3) and actions (+4.4)** and ties it on math.
5. Across the twelve no-memory ERGO-vs-AC3 cells, ERGO goes from **losing 11 of 12** to
   **winning or tying 7 of 12**.

**What survives.**

* **Database is untouched and decisive.** ERGO 12.0 vs Reset 48.0 / Augment 32.0 / Gated 38.7. The
  paper's specific ERGO claim — "its LLM rewrite step can paraphrase or compress the user's exact
  phrasing, which is why it underperforms simple concatenation on database and actions"
  (`tex:779`, `tex:233`) — **holds**: 12.0 < 32.0 on database and 52.2 < 87.0 on actions.
* **AC3-Gated-Reset ≥ ERGO on all four tasks** still holds — but math becomes a tie, not a 10-point
  win, and the correction makes AC3-Reset's advantage over ERGO vanish on three tasks.
* **Every AC3 operator still beats the full-context Baseline in all four cells**, and the
  Gated-vs-Reset ordering is unchanged. Nothing in §3 touches the baseline row.
* **No sentence in the paper asserts "AC3 beats all prior work on task X"** — the LiC prose is
  framed against AO and the Full-Context baseline, not against ERGO. So no printed claim becomes
  literally false. The damage is to the *table's visual ordering* and to the framing that ERGO is
  the weak non-oracle prior work that AC3 clears comfortably.

**Two body-text numbers change as a side effect, both in our favour** (`tex:318`):
"on code, Gated Reset reaches 64.4%, closing 78% of the 62.0pp gap" → **63.2%, closing 82% of the
57.9pp gap** (AO/code drops to 73.7). The abstract/conclusion "closes 55–80% of the LiC gap" (`tex:110,139,405`)
becomes **67–82%** if the actions cell is placed on n=23 (66.7 vs AO 82.6).

---

## 6. Positive controls

Seven harness faults were found elsewhere tonight, so every claim above is backed by something
with a known answer.

* **PC1 — the denominator rule reproduces on every archived run that uses it, 0 exceptions.**
  Scanned all 484 archived runs carrying a `replay` block; the 28 that replay from the four
  `tab:main` pools report `total_samples` = **20 / 19 / 25 / 25** and `user_sim_skipped` =
  **3 / 6 / 0 / 0**, matching `|pool| − |sidecar ids|` exactly in all 28. (`/tmp/t17_scan.py`
  logic; run list in worklog.)
* **PC2 — the "23 = 20 + 3" arithmetic is verified against files, not inferred.**
  `outputs/2026-03-16/13-09-27` reports `total_samples=20` yet its `traces/` directory holds
  **23 files, of which exactly 3 are empty** — `sharded-GSM8K_{1287,267,534}`, precisely the three
  IDs in `math_false_negatives.json`. This is the file-level demonstration that a run directory
  re-admits pruned samples.
* **PC3 — blind reconstruction matched the ground truth.** The fractions `16/23, 11/25, 3/25,
  12/25` were derived by exhaustive rational search over the four printed ERGO percentages
  **before** the provenance was located. The Overleaf commit `d856247` (2026-05-07) then states
  verbatim: *"the ERGO row … now reports the proper-prompt local re-run (16/23, 11/25, 3/25,
  12/25) → 69.6 / 44.0 / 12.0 / 48.0 … the local runs at `outputs/2026-05-01/23-*` use the actual
  ERGO rewrite prompt."* Exact match, all four cells. T14 reported that ERGO "has no provenance
  record anywhere in the repo" — it does, in the *paper* repo's history.
* **PC4 — reproduced published cells I was not meant to change, from independent documents.**
  `prior_work_baselines.md:95-96` gives AO `17/20, 14/18, 8/25, 19/23` → 85.0/77.8/32.0/82.6 and
  Concat `16/19, 13/19, 8/25, 20/23` → 84.2/68.4/32.0/87.0 — both match `tab:main` to the digit.
  `v8_batch_results.md:29-32` reproduces the Baseline and Augment rows on math/code/database.
  `sans_issue_injection_redux.md:35-38` reproduces AC3-Reset `15/20, 11/18, 12/25, 12/23` →
  75.0/61.1/48.0/52.2. Three independent documents, three published rows, zero discrepancies.
* **PC5 — reproduced the N=3 Gated-Reset row from its own per-run values.**
  `tex:496-499` prints 75.0/80.0/85.0, 72.2/63.2/57.9, 44.0/32.0/40.0, 68.0/56.0/60.0; the means
  are 80.0 / 64.43 / 38.67 / 61.33, matching the printed 80.0 / 64.4 / 38.7 / 61.3 to 0.1pp, and
  the only n's consistent with those per-run values are 20 / {18,19,19} / 25 / 25.
* **PC6 — every unchanged cell in §3 is bit-identical to the published cell.** 30 of 40 cells do
  not move, by construction, and the ten that move are exactly the ten with a documented
  denominator defect. If the recomputation were sloppy, unrelated cells would drift; none do.

---

## 7. What could not be recomputed, and why

**The published per-sample results do not exist.** Verified independently of T14:

| needed for | run dirs | status |
|---|---|---|
| ERGO row | `outputs/2026-05-01/23-*` | **0 hits** in the 69,738-line `snapshot.tar.gz` index; 0 in `supplementary.tar.gz`; absent from `~/ac3/{recovered,recovered_t2c,t14_snapshot}`. `outputs/runs.yaml` (875 entries) has no 2026-05-01 row. |
| AO + Concat User rows | `outputs/2026-03-21/05-12-15 … 05-15-09` | absent — the snapshot has no `2026-03-21` at all |
| AC3-Reset row | `outputs/2026-03-21/10-33-19 … 10-37-32` | absent, same gap |
| Baseline / Augment / +Memory rows | `outputs/2026-03-16/19-* … 2026-03-17/08-*` | absent — `2026-03-16` stops at `16-16-14` |
| Gated-Reset N=3 actions runs | replay source `outputs/2026-03-16/19-26-46` | absent |

The archive's coverage gap is 2026-03-21 → 2026-03-22 and 2026-04-28 → 2026-05-05, consistent with
the ERGO commit's own description of them as "local runs" made off the VM.

So §3 is arithmetic on recovered numerators over corrected denominators, not a re-scoring. The
numerators themselves are solid — each is attested by an independent source document (PC4) or by
the author's own commit message (PC3). What is *not* recoverable is the per-sample split needed to
close the intervals in §4. **This row genuinely cannot be finished without new runs** — 87
last-turn ERGO replays, which is the smallest experiment on the board and the one with the
largest reviewer-facing payoff.

---

## 8. Recommended action for the operator (PAPER-7)

1. **Re-run ERGO on the four filtered pools** before anything else. It is ~\$0.20 and it converts
   the largest reviewer-visible defect in the paper into a measured number.
2. If the re-run is not possible, **print ERGO's intervals**, not the published point estimates,
   and say in the caption that ERGO was scored on a dirtier pool.
3. **Put AC3-Gated-Reset's actions cell on n=23** like every other actions row (61.3 → ~66.7),
   and un-mix its code row (n=18 in run 1). This one favours us; do it in the same pass so the fix
   reads as "make the column comparable", not "raise ERGO".
4. **Restore the four n=18/19 cells to the pool denominator** (AO/code, Concat/math,
   Augment/code, Reset/code) — two move against prior work, two against us.
5. **Print n per cell in the table.** The whole defect is invisible only because the table prints
   percentages.
6. **Say it out loud in the paper.** A one-sentence appendix note ("ERGO was initially scored on
   the unfiltered replay pool; the row below places it on the same filtered pool as every other
   row, which raises it by up to N pp") is worth far more than the ordering it costs.

---

## 9. Artifacts

| file | contents |
|---|---|
| `build_corrected.py` | the §3/§4 recomputation; zero API calls, no repo state touched |
| `corrected_tabmain.json` | published / corrected / lo / hi / defect-kind per cell |
| `worklog.md` | chronological record, including the discarded 870-attempt tally and why |

No files outside `neurips_review/autoresearch/tasks/T17/` were written. `writing/overleaf_repo/`
was read only.
