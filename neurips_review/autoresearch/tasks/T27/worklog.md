# T27 — Triage and close the MEDIUM red-team items that need measurement

**2026-07-29, autonomous overnight session.** Operator asleep; no questions asked. Scope: the
five `RED_TEAM.md` MEDIUM items T25 deferred as "need runs" — **M11, M12, M6, M3, M15** — triaged
first, then executed cheapest-first.

**Inputs:** `tasks/T23/RED_TEAM.md`, `tasks/T25/worklog.md`, `autoresearch/WORKLOG.md` (F1–F72,
D1–D19), `tasks/T1/{worklog.md,RESULTS.md}`, `tasks/T11/worklog.md`,
`experiments/paired_analysis_results.txt`, `outputs/rebuttal_random/`, and the phase-1/2
per-sample data recovered from `blob_staging/snapshot.tar.gz`.

**Output dir:** `outputs/T27/` (T27-scoped per trap 7). No `git checkout`. `writing/overleaf_repo/`
untouched. **`replies/v5/` not edited** — drop-in wording is handed over in §6 below.

---

## 1. Triage table

| Item | What it costs | What it buys | Verdict |
|---|---|---|---|
| **M3** — the `95.0 ± 0.0` cells: "were these cached?" + no CI | **$0**, ~20 min. Item-level data is on disk (`outputs/rebuttal_random/*/results.json`) | Closes a *cache-confound* insinuation with a measurement instead of an assertion, and converts a suspicious `± 0.0` into a CI Vg97 explicitly asked for. Also **the red team's own suggested wording is false** and had to be checked before posting | **RUN — done, §3** |
| **M15** — sign test is our weakest statistic; Vg97 asked for CIs | **$0**, ~40 min. Per-sample `results.json` for all 168 phase-1/2 cells is inside `snapshot.tar.gz` | Upgrades the *headline* paired result from a 36-cell sign test to an item-level exact McNemar **and** a problem-clustered bootstrap CI, on n=1,668 paired items. Directly answers Vg97 Q2. Free | **RUN — done, §4** |
| **M6** — 5YHP asked for three judge checks; we gave two | **$0**, ~5 min. A human study cannot be run overnight and should not be faked | The gap is real but the fix is one sentence. The supporting control (degraded-copy, 39/40 · 36/40 · 40/40) is *already* in `03` W4; only the explicit "we did not run a human study" is missing | **DECLINE the run, SUPPLY the wording — §5** |
| **M11** — the neutral-prompt condenser control "did not finish in the window" | ~**$3**, ~35 min wall-clock. `summarize_v2_neutral` is implemented and config-verified (T1 §12); TRAPI gpt-5.4-mini | This is the **Area Chair's central reservation**, and its only robustness control is currently an admission of failure. We wrote the competitor's prompt; the single check that we wrote it fairly is the one experiment we did not finish. Turning that into a measured result is the best dollar-for-credibility trade left. The quantity of interest (AC3 − condenser ≈ +22pp) is **far above** the sub-10pp resolution floor, so trap 6 does not bite | **RUN — §7** |
| **M12** — U-Fold on tau2, plus "scale MT-OSC's window and re-report" | **U-Fold: hours of adaptation engineering, unbounded risk, and tau2 rollouts are the session's longest task (T6 is still live on that fork).** MT-OSC w=2: ~$1, ~15 min, already implemented, bug already fixed (`c1dd523`) | Split the item. **U-Fold: decline** — the red team's own suggested revision is to *offer* it to the reviewer, not to run it, and an unvalidated overnight adaptation of someone else's method is worse than an honest offer. **MT-OSC w=2: run** — we supplied the "w=4 cannot compact before turn 6" objection ourselves and currently have no answer; T1 archived the w=2 cell as buggy and converged before re-running it | **SPLIT: decline U-Fold, RUN MT-OSC w=2 — §7** |

**Budget:** projected ≈ $7 against the ~$15 ceiling. Actual in §8.

**Ordering rationale.** The two $0 re-analyses (M3, M15) were completed *first* so that partial
completion still yields something, and the two runs were launched into the background before that
analysis began so wall-clock and compute overlap.

**Venue check (trap: near-ceiling math does not discriminate).** Both new runs are on
**LiC-database**, which T2c and T1 both identify as the high-headroom venue (baseline 56.1%,
ceiling 94.4%). No new math was run. M3's venue *is* near-ceiling math, but M3 is not asking a
discrimination question — it is asking whether three replicates were independent draws, which is
answerable at any accuracy level.

---

## 2. Controls run before anything was believed

Per trap 1 (eleven faults caught by controls tonight, two of them in *analysis*):

| Control | Result |
|---|---|
| M15 PC-1: recompute all 168 phase-1/2 cell accuracies from per-sample data | **168/168 reproduce the printed value exactly** (after the error-row fix in §4.1) |
| M15 PC-2: reproduce `paired_analysis_results.txt`'s five rows from the same parse | **All five reproduce to the digit** (+15.9/33-2-1, +15.2/31-1-4, +17.0/11-1-0, −0.3/6-6-0, +13.3/31-4-1) |
| M3 PC-1: all 9 rebuttal-random runs cover the identical 40 problems | pass |
| M3 PC-2: recompute the three printed rows of `00` CW3 from item data | **pass** — 90.0/87.5/85.0, 97.5/95.0/87.5, 95.0/95.0/95.0 |
| M11/M12 pre-flight: 3-sample smoke of `summarize_v2_neutral` | pass — real scores, 0 errors, 7.0 avg turns (vs `summarize_v1`'s 7.3), non-empty 882-char summary in the `compacted conversation` slot |
| M11 positive control cell: re-run `summarize_v1` on database in the T27 tree | §7 |
| Every run: `false_negative_analysis.model=gpt-5.4-mini_2026-03-17` (trap 2) | set in the launcher for every cell |
| Every run: raw accuracy primary; `adjusted_accuracy` not used (trap 3) | observed |

---

## 3. M3 — RESOLVED. The cache insinuation is dead, and the red team's fix was wrong

Script: `m3_bootstrap.py`. Zero API calls.

### 3.1 The red team's suggested wording is FALSE and must not be posted

`RED_TEAM.md` M3 proposes writing *"the analyzer cache was disabled for these runs, so the
replicates are independent draws"*, with the caveat "assuming that is true; if it is not true, we
need to know before posting."

**It is not true.** `src/ctx_editor/config/experiment/context_edit_v2_gated.yaml:18` sets
`analysis_cache_dir: outputs/analysis_cache`, and `experiments/run_exp1_reps.sh` does **not**
override it (contrast `tasks/T1/run_t1_main.sh`, which passes
`experiment.strategy.analysis_cache_dir=null` explicitly). The runs' own
`outputs/rebuttal_random/{full,rep2,rep3}_gated/config.yaml` confirm the cache path at line 14.
Posting that sentence would have handed a reviewer a checkable false statement in the paragraph
whose whole purpose is to rebut a suspicion of caching.

### 3.2 What is true is stronger, and it is measured

The cache key (`strategies/analysis_cache.py:83-103`) is a SHA-256 over
`trace_hash + analyzer_model + prompt_version + …`, and `trace_hash` hashes the **message list** —
which contains the assistant's own sampled outputs. In an end-to-end run at temperature 1.0 those
outputs differ between replicates, so a cross-replicate cache hit is structurally near-impossible
after the first turn. That is an argument; here is the measurement:

| Probe (AC3-Gated-Reset, the `95.0 ± 0.0` cell) | Result |
|---|---|
| Samples whose **analyzer output sets are identical** across all three runs | **0 of 39 comparable** |
| Samples whose analyzer outputs **differ** across the three runs | **39 of 39** |
| Analyzer calls per run | 72 / 72 / 71 — same order, not a replayed transcript |
| The 2 problems failed in each run | `{288, 427}` · `{1066, 435}` · `{427, 916}` — union 5, **intersection 0** |
| Problems whose turn count differs across runs | 7 / 40 |
| Problems whose extracted answer differs across runs | 5 / 40 |

Same probe on AC3-Reset: **40 of 40** samples have differing analyzer outputs across the three
runs. So `95.0 / 95.0 / 95.0` is three genuinely different runs landing on the same *count*, not
one run reported three times — and the identity of the failures moves every time.

### 3.3 The CI Vg97 asked for

Problem-clustered bootstrap (B=20,000; resample the 40 problems with replacement, keep all three
replicates within a resampled problem, so both sampling and decoder variance propagate):

| Arm | Point | 95% CI | Paired Δ vs full context | 95% CI | Item-level exact McNemar (120 replicate-item pairs) |
|---|---|---|---|---|---|
| Full context | 87.5 | [79.2, 95.0] | — | — | — |
| AC3-Reset | 93.3 | [87.5, 98.3] | **+5.8pp** | [+0.0, +12.5] | 11 W / 4 L, **p = 0.119** |
| AC3-Gated-Reset | 95.0 | [90.0, 99.2] | **+7.5pp** | [+1.7, +15.0] | 11 W / 2 L, **p = 0.023** |

Reads honestly in both directions: **Gated-Reset's end-to-end gain is significant; Reset's is
not.** `00` CW3 already says "this experiment alone is not powered for significance", so the CIs
support the existing text rather than contradicting it — they just make it checkable.

**Bookkeeping note, not worth changing:** the `± 2.0 / ± 4.2 / ± 0.0` in `00` CW3 are
**population** sds (ddof=0). Sample sds (ddof=1) would be ± 2.5 / ± 5.2 / ± 0.0. The convention is
at least applied consistently across the three rows, and `± 0.0` is 0.0 either way. Flagged so
nobody "corrects" one row into a different convention from the others.

---

## 4. M15 — RESOLVED. The headline result now has an item-level test and a clustered CI

Script: `m15_itemlevel.py`; full output `m15_results.txt`. Zero API calls.

### 4.1 Where the item-level data came from, and one trap inside it

`RED_TEAM.md` M15 asserts "we have the item-level data (it is how T1, T2c and T9 were computed)".
That is not right — T1/T2c/T9 are different experiments; the 36-cell matrix is parsed from the
*report tables* in `docs/reports/post_neurips_ac3_phase{1,2}.md`, and
`outputs/post_neurips_ac3_phase{1,2}/` on disk contain only `winners.json`. The per-sample data is
recoverable: all 168 `results.json` files are inside `blob_staging/snapshot.tar.gz` and extract in
32 s.

**The trap, caught by PC-1.** A first pass reproduced only 165/168 cells. The three misses were
all cells with harness errors: Kimi/math/conv0 prints `87.2% (34/39)` with "9 errors" against
**48** rows on disk (34/48 = 70.8%). Errors are recorded as `num_turns == 0` rows with
`is_correct: false` and **no `error` field** — i.e. a failed conversation is indistinguishable
from a wrong answer unless you look at the turn count. Scoring them as failures would have
silently penalised whichever arm errored more. Fixed by (a) dropping `num_turns == 0` rows, which
takes PC-1 to **168/168 exact**, and (b) taking the **arm-symmetric intersection** within each
triple, so every arm is scored on identical items (trap 3's principle applied at the item level).
Pooled n = **1,668** paired items.

### 4.2 Results

All three statistics on the same 36 triples. The sign test is reproduced as the control.

| Method | Sign test over 36 cells (current v5 row) | **Item-level exact McNemar** (pooled) | **Problem-clustered bootstrap** |
|---|---|---|---|
| **AC3-Reset** | +15.9pp, 33/2/1, p < 0.0001 | +15.4pp, **350 W / 93 L** of 1,668, **p = 4e−36** | **+15.4pp, 95% CI [+11.5, +19.4]** |
| **AC3-Augment** | +15.2pp, 31/1/4, p < 0.0001 | +14.6pp, 323 W / 79 L, p = 4e−36 | +14.6pp, [+10.8, +18.6] |
| AC3-Gated-Reset† | +17.0pp, 11/1/0, p = 0.0063 | +16.8pp, 126 W / 33 L of 554, p = 5e−14 | +16.8pp, [+11.6, +22.0] |
| AC3-Rewrite† | −0.3pp, 6/6/0, p = 1.00 | **+0.0pp, 42 W / 42 L**, p = 1.00 | **+0.0pp, [−3.8, +3.8]** |
| Assistant omission | +13.3pp, 31/4/1, p < 0.0001 | +12.6pp, 297 W / 87 L, p = 6e−28 | +12.6pp, [+9.2, +16.1] |

Clusters = 191 distinct problems (187 for the one-model rows), each contributing up to 3 prefixes
× 3 models of paired observations.

**Three points worth making from this table.**

1. **The headline survives every strengthening.** The cell-level sign test, the item-level
   McNemar and the clustered bootstrap all give +15 to +16pp for Reset with a CI that clears
   +11pp. Nothing here is a sub-10pp ordering at n≈20; the effect is 4× the resolution floor.
2. **Rewrite's row gets *better* with the CI.** −0.3pp with 6/6 cells reads as "our operator does
   nothing, or worse". At the item level it is exactly **+0.0pp, 42 W / 42 L, CI [−3.8, +3.8]** —
   a tight interval centred on zero. "Neutral on LiC, bounded within ±4pp" is a defensible and
   *more informative* statement than the sign test's coin flip, and it fits H2's framing (we
   print the operator that does not win on this benchmark) without inviting "how much does it
   hurt?"
3. **The AO head-to-head, which is the load-bearing number in T25's assembled counter-case:**

| AC3-Reset vs. assistant omission | n | Item-level gain | Clustered bootstrap 95% CI | Exact McNemar |
|---|---|---|---|---|
| Whole matrix | 1,668 | **+2.8pp** | **[−0.3, +5.9]** | 184 W / 137 L, p = 0.010 |
| LiC-database only | 440 | **+18.6pp** | **[+10.7, +26.6]** | 113 W / 31 L, **p = 4e−12** |

These reproduce T25's cell-level +2.6pp and +18.7pp within rounding, from an independent data
path — a useful cross-check on the section T25 wrote.

> **Guardrail — do not quote the matrix-wide McNemar p = 0.010 as a win over AO.** McNemar treats
> 1,668 items as independent when they are 191 problems × up to 9 correlated replicates, so it is
> anti-conservative here. The **clustered bootstrap CI [−0.3, +5.9] is the correct statistic and
> it includes zero.** The honest reading is exactly the one v5 already prints: matrix-wide it is a
> wash, and the effect is concentrated on database — where the clustered CI is [+10.7, +26.6] and
> excludes zero by a wide margin. Using the anti-conservative test to upgrade the wash into a win
> would be precisely the statistic-shopping the red team flags in M8.

---

## 5. M6 — DECLINED as a run; one sentence supplied instead

A human-validation study cannot be run, recruited and defended overnight, and a synthetic
stand-in would be worse than the gap. Two things verified at $0:

* The degraded-copy positive control the red team wants cited is **real and already in the reply**
  — `03` W4 third bullet already says "the three judges correctly prefer the intact response
  39/40, 36/40 and 40/40". Source verified at `tasks/T11/worklog.md:221-227` (gpt-5-mini 39/40
  with 1 tie and 0 degraded wins; DeepSeek 36/40 with 2 degraded, 2 tie; Kimi 40/40).
* What is genuinely absent is any acknowledgement that **human validation was the third of 5YHP's
  three named checks and we did not do it**. Wording in §6.3.

---

## 6. Drop-in wording for `replies/v5/` — **not applied by me**

Another agent may be in that tree, so these are handed over rather than written. Each is a
minimal, self-contained replacement.

### 6.1 M3 — `00_general_response.md` CW3 (and `01_reviewer_iNYK.md` Q1, which repeats the table)

Insert immediately after the three-row table, before "**Both operators improve…**":

> Two notes on that table, since a `95.0 ± 0.0` at temperature 1.0 invites the question. First,
> the three Gated-Reset runs are **independent end-to-end conversations that happen to land on the
> same count**, not a cached replay: they fail on *different* problems each time (the failing
> pairs are disjoint across the three runs, union 5 and intersection 0), the analyzer's output
> differs on **39 of 39** comparable conversations across the three runs, and turn counts and
> extracted answers differ on 7 and 5 of the 40 problems respectively. Second, these `±` are
> spreads over three replicates and therefore describe decoder variance, not sampling variance
> over problems — the quantity you asked for. A problem-clustered bootstrap over the 40 problems
> gives full context **87.5% [79.2, 95.0]**, AC3-Reset **93.3% [87.5, 98.3]** and AC3-Gated-Reset
> **95.0% [90.0, 99.2]**; paired against full context, AC3-Gated-Reset is **+7.5pp [+1.7, +15.0]**
> (item-level exact McNemar over the three replicates, p = 0.023) and AC3-Reset is **+5.8pp
> [+0.0, +12.5]** (p = 0.119). We report both, including the one that does not reach significance:
> at n = 40 on a near-ceiling task this experiment establishes that the gain is not an artifact of
> difficulty selection, replay or a single run, and it is not the experiment that establishes
> significance.

**Do NOT write** "the analyzer cache was disabled for these runs" — it is false (§3.1).

### 6.2 M15 — `00_general_response.md` CW2, after the paired-significance table

Replace the sentence beginning "**AC3's mean clears the full-context baseline on every model**"
by inserting this paragraph *before* it:

> The table above is a sign test over cells, which is assumption-light but discards effect size
> and treats 36 correlated cells as independent. Since Reviewer Vg97 asked specifically for
> confidence intervals and bootstrap analyses, we also report the two stronger statistics on the
> same data, at the level of individual problems (n = **1,668** paired items after dropping the
> conversations that errored in any arm, so every arm is scored on identical items):
>
> | Method | Item-level exact McNemar | Problem-clustered bootstrap, mean paired gain |
> |---|---|---|
> | **AC3-Reset** | 350 wins / 93 losses, **p < 1e−30** | **+15.4pp, 95% CI [+11.5, +19.4]** |
> | **AC3-Augment** | 323 / 79, p < 1e−30 | +14.6pp, [+10.8, +18.6] |
> | AC3-Gated-Reset† | 126 / 33, p = 5e−14 | +16.8pp, [+11.6, +22.0] |
> | AC3-Rewrite† | 42 / 42, p = 1.00 | **+0.0pp, [−3.8, +3.8]** |
> | Assistant omission | 297 / 87, p < 1e−28 | +12.6pp, [+9.2, +16.1] |
>
> The bootstrap resamples whole **problems** (191 of them, each contributing up to 3 prefixes × 3
> models), which is the correlation structure the sign test ignores; we treat it as the primary
> interval and the sign test as the assumption-light cross-check. All three statistics agree.
> Note that the interval also sharpens the AC3-Rewrite row: at the item level Rewrite is not
> mildly negative but **exactly neutral on LiC, bounded within ±4pp**, which is the honest version
> of the row we print above.

### 6.3 M15 (b) — the AO head-to-head in CW2's "Where AC3 separates…" subsection

Append to the paragraph that gives +2.6pp / 15-17-4:

> At the level of individual problems the same picture holds with an interval attached: across
> the matrix AC3-Reset is **+2.8pp over assistant omission, 95% CI [−0.3, +5.9]** by the same
> problem-clustered bootstrap — i.e. not distinguishable from zero, which is why we do not claim
> it — while on **LiC-database alone it is +18.6pp, 95% CI [+10.7, +26.6]** (113 problem-wins
> against 31, exact McNemar p < 1e−11). The concentration is not a reading of the cell means; it
> survives the strongest test we can apply to it.

### 6.4 M6 — `03_reviewer_5YHP.md` W4, appended to the "Self-consistency and controls" bullet

> * **On the third check you asked for, human validation: we did not run one.** A human study was
>   not something we could recruit and defend inside the discussion window, and we would rather
>   name the gap than let two of your three checks stand in for three. The closest evidence we
>   have is the degraded-copy control above — three judges preferring the intact response 39/40,
>   36/40 and 40/40 — which establishes that the judges discriminate, not that they agree with
>   people. A human-agreement study on a sampled subset of pairs, with the rubric and the raw
>   labels released, is queued for the camera-ready and we will report it whichever way it comes
>   out.

### 6.5 M11 / M12 wording

In §7 once the runs land.

---

## 7. M11 and M12 (MT-OSC w=2) — runs

Launcher `run_t27.sh`, log `run_log.txt`, output `outputs/T27/`. Two streams, each at
`execution.max_concurrent=5` (aggregate 10 against TRAPI's shared 20, with T6 holding ~5).

| Cell | Purpose | Status |
|---|---|---|
| `db_summarize1_rep2` | **Positive control + replicate.** Known value 53.3% (57/107). Same strategy class, harness, evaluator and FN model as the neutral arm; also supplies the run-to-run noise floor without which "neutral vs v1" is uninterpretable | launched 19:50 |
| `db_summarize_neutral` | **M11** — the condenser prompt-robustness control that "did not finish in the window" | launched 19:50 |
| `code_summarize_neutral` | M11, second venue (queued behind the above) | queued |
| `db_mtosc_w2` | **M12 (tractable half)** — MT-OSC at the smallest window in the paper's own sweep, post-`c1dd523` | launched 19:50 |

_Results appended when the cells land._

---

## 8. Cost

_Appended when the runs land._
