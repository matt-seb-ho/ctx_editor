# T14 — Audit of the false-negative adjustment; corrected LiC numbers

**Bottom line.** The bias is real, it is a pure post-treatment-conditioning artefact, and its
magnitude on *reset-based* arms is **+14 to +56 pp** — much larger than the single +12 pp cell
T1 measured. **Two qualitative conclusions flip** under the correction (AC3-Rewrite on code and
on actions go from beating baseline to losing to it), though neither is in a currently-published
table. **AC3-Reset and AC3-Gated-Reset survive intact**: they beat baseline in every cell under
every metric, and the Gated-vs-Reset ordering is unchanged.

The paper's headline `tab:main` is **much less exposed than expected** — see §3 — but it has a
*different* and arguably worse comparability defect that this audit surfaced: **its denominators
are not constant down a column**, and the rows that get the larger (unfiltered) denominator are
ERGO and AC3-Gated-Reset.

---

## 1. Mechanism, with file:line

Three lines of code compose into the bug.

1. `src/ctx_editor/core/trace.py:102-105` — `reset_conversation` marks **every** currently
   visible message invisible, *user messages included*, then appends the replacement context.
2. `src/ctx_editor/strategies/context_edit_v2.py:117-124` — the replacement context is
   `[system, Message(role="compacted conversation", ...), latest user shard]`. The user's
   accumulated specification survives, but under the role `"compacted conversation"`, not `user`.
   (Same shape in `context_compaction.py:340`, `summarization.py:212`, `mtosc.py:324`,
   `ergo_restart.py:181`, `prior_work_baselines.py:98`.)
3. `src/ctx_editor/identify_false_negatives.py:190-193` (`get_active_messages`, filters on
   `visible`), `:173` (`format_user_messages`, keeps only `role == "user"`), `:228-230`
   (`analyze_sample` feeds only that subset into the prompt).

So after one reset the sufficiency judge's `{user_messages}` field holds **exactly one turn**.
The prompt at `:100-110` then asks it whether "the UNION of all user messages" contains every
critical detail and instructs it to answer *insufficient* if a detail "is completely absent from
ALL user messages". Given one shard out of eight, *insufficient* is the correct answer to the
question the judge was asked. The judge is not malfunctioning — it is being handed a
post-treatment input.

Finally `:419` and `:426`:

```python
user_sim_induced = [r for r in fn_results if not r.user_sim_sufficient]
adjusted_denominator = total_valid - len(user_sim_induced)
```

Failures are deleted from the denominator; the numerator is untouched. Accuracy therefore
inflates monotonically with how much user text an arm hides. Note `:427`: the *other* exclusion
category (non-answer-attempts) is behind a config flag; this one is unconditional.

**Measured directly.** Mean user turns the judge saw, per incorrect sample, on AC3-Rewrite:
**1.00** under the shipped path vs **5.20** under the arm-symmetric path. On Baseline: 5.35 vs
5.35. That single number is the whole finding.

---

## 2. Exclusion rates and inflation across the archived matrix

`survey.py` → `survey.json`. 558 archived runs with FN analysis, read from shipped
`false_negatives.json` + `run_summary.json`; **no LLM calls**, so this half of the audit is
exact and reproducible offline.

The split is exactly the reset / no-reset split predicted by the mechanism.

| arm family | resets? | task | analysed | excluded | excl % | raw | shipped adj | inflation |
|---|---|---|---|---|---|---|---|---|
| Baseline | no | math_v2 | 340 | 90 | 26.5% | 70.2% | 76.1% | +6.0 |
| Baseline | no | code_v2 | 550 | 213 | 38.7% | 53.3% | 65.1% | +11.8 |
| Baseline | no | database_v2 | 901 | 36 | 4.0% | 19.3% | 19.9% | +0.6 |
| Baseline | no | actions_v2 | 166 | 15 | 9.0% | 84.2% | 85.4% | +1.2 |
| AO / Omit-Assistant | no | math_v2 | 73 | 5 | 6.8% | 84.3% | 85.2% | +0.9 |
| AO / Omit-Assistant | no | code_v2 | 119 | 42 | 35.3% | 68.4% | 77.0% | +8.6 |
| AO / Omit-Assistant | no | database_v2 | 305 | 4 | 1.3% | 33.8% | 34.1% | +0.3 |
| AO / Omit-Assistant | no | actions_v2 | 43 | 9 | 20.9% | 90.4% | 92.3% | +1.8 |
| AC3-Augment (S1) | no | math_v2 | 86 | 5 | 5.8% | 81.7% | 82.6% | +0.9 |
| AC3-Augment (S1) | no | code_v2 | 139 | 52 | 37.4% | 64.5% | 74.4% | +9.9 |
| AC3-Augment (S1) | no | database_v2 | 242 | 3 | 1.2% | 49.7% | 50.0% | +0.3 |
| AC3-Augment (S1) | no | actions_v2 | 50 | 12 | 24.0% | 88.9% | 91.3% | +2.4 |
| **AC3-Reset** | **yes** | math_v2 | 65 | 54 | **83.1%** | 84.3% | 96.7% | **+12.4** |
| **AC3-Reset** | **yes** | code_v2 | 120 | 111 | **92.5%** | 66.4% | 96.3% | **+30.0** |
| **AC3-Reset** | **yes** | database_v2 | 205 | 121 | **59.0%** | 53.4% | 73.7% | **+20.3** |
| **AC3-Gated-Reset** | **yes** | math_v2 | 25 | 25 | **100.0%** | 82.6% | 100.0% | **+17.4** |
| **AC3-Gated-Reset** | **yes** | code_v2 | 50 | 43 | **86.0%** | 55.8% | 90.0% | **+34.2** |
| **AC3-Gated-Reset** | **yes** | database_v2 | 74 | 47 | **63.5%** | 49.7% | 73.0% | **+23.3** |
| **AC3-Rewrite** | **yes** | math_v2 | 426 | 425 | **99.8%** | 78.6% | 99.7% | **+21.0** |
| **AC3-Rewrite** | **yes** | code_v2 | 828 | 768 | **92.8%** | 50.0% | 93.2% | **+43.2** |
| **AC3-Rewrite** | **yes** | database_v2 | 1306 | 842 | **64.5%** | 37.2% | 62.5% | **+25.3** |
| **AC3-Rewrite** | **yes** | actions_v2 | 518 | 516 | **99.6%** | 75.3% | 99.9% | **+24.5** |

No-reset arms: 1–39% excluded, +0.3 to +11.8 pp. Reset arms: 59–100% excluded, +12.4 to
+43.2 pp. Several cells hit **100% exclusion** (AC3-Gated-Reset math 25/25; the GEPA candidate
sweep 240/240), i.e. shipped adjusted accuracy is 100.0% *by construction*. The metric cannot
report a failure for an arm that resets hard enough.

---

## 3. The published `tab:main` — what it actually uses

`writing/overleaf_repo/neurips/neurips_2026_conference.tex:252-275`.
**The exact run directories behind every cell are gone** — not on disk, not in
`snapshot.tar.gz` (no `outputs/2026-03-21` at all; `2026-03-16` stops at `16-16-14`), not in
`supplementary.tar.gz`. So the published cells cannot be re-judged directly and the analysis
below is reconstruction from denominators plus the surviving provenance docs.

### 3a. There are two FN mechanisms; only one is broken

**Mechanism A — pool-level pre-filter. Arm-symmetric and correct.**
`data/baseline_traces_v2/{math,code,database}_false_negatives.json` are FN analyses run once on
**baseline** traces (nothing hidden) and used to prune the replay pool before any arm runs:

| task | prefixes available | user_sim_induced pruned | n in `tab:main` |
|---|---|---|---|
| math | 23 | 3 (`GSM8K/1287`, `/267`, `/534`) | **20** ✓ |
| code | 25 | 6 (`HumanEval/113`, `livecodebench/2791,2850,2873,2916,2920`) | **19** ✓ |
| database | 25 | 0 | **25** ✓ |
| actions | 25 | (2; file not recovered) | **23** ✓ |

These reproduce `tab:main`'s denominators exactly. Same excluded sample set for every arm →
this is the arm-symmetric correction, applied before the fact. **Defend it, don't retract it.**

**Mechanism B — per-run `adjusted_accuracy`.** The broken one. Its footprint inside `tab:main`
is at most **1 sample per cell**, in four cells:
AO/code (14/18), Concat-User/math (16/19), AC3-Augment/code (10/18), AC3-Reset/code (11/18).
`docs/reports/prior_work_baselines.md:97` confirms two explicitly: *"Omit-assistant code had 1
additional user-sim exclusion (14/18 adj = 77.8%); concatenate-user math had 1 additional (16/19
adj = 84.2%)."* The other two 18s may instead be timeout-driven — `v8_batch_results.md:53`
documents error-shrunk code denominators (n=16, n=17), and the paper's own variance appendix
writes "code (n=18--19)" while claiming *raw n, no auxiliary normalization*
(`neurips_2026_conference.tex:489,494`). Either way the per-cell effect is capped at ~1 sample =
**+3.0 to +4.2 pp**, and **two of the four cells favour prior work** (AO +4.1, Concat-User +4.2)
against two that favour us (AC3-Augment +3.0, AC3-Reset +3.2). `tab:main` is not systematically
self-serving on this axis.

### 3b. But `tab:main` has a worse problem: denominators are not constant down a column

Inferred numerators/denominators from the printed percentages:

| row | math | code | database | actions |
|---|---|---|---|---|
| Baseline | 12/**20** | 3/**19** | 1/**25** | 8/**23** |
| + Memory | 11/20 | 4/19 | 1/25 | 8/23 |
| AO | 17/20 | 14/**18** | 8/25 | 19/23 |
| Concat User | 16/**19** | 13/19 | 8/25 | 20/23 |
| **ERGO** | 16/**23** | 11/**25** | 3/25 | 12/**25** |
| AC3-Augment | 16/20 | 10/**18** | 8/25 | 11/23 |
| + Memory | 18/20 | 13/19 | 11/25 | 11/23 |
| AC3-Reset | 15/20 | 11/**18** | 12/25 | 12/23 |
| + Memory | 17/20 | 13/19 | 11/25 | 12/23 |
| **AC3-Gated-Reset** | mean, n=20 | mean, n=18–19 | mean, n=25 | mean, n=**25** |

**ERGO's denominators are 23 / 25 / 25 / 25 — exactly the *unfiltered* replay pools.** Every
other row uses the filtered 20 / 19 / 25 / 23. ERGO is therefore scored against a strictly
dirtier sample set, including the very items pruned as user-sim-broken. Upper bounds if ERGO's
cells were placed on the same filtered pools (all pruned items assumed ERGO failures):

| | published | upper bound on filtered pool | AC3-Reset (published) |
|---|---|---|---|
| math | 69.6 | **80.0** (16/20) | 75.0 |
| code | 44.0 | **57.9** (11/19) | 61.1 |
| actions | 48.0 | **52.2** (12/23) | 52.2 |
| database | 12.0 | 12.0 (same pool) | 48.0 |

**On math and actions, ERGO could tie or beat AC3-Reset once the denominators are made
comparable.** This is a bound, not a measurement — the ERGO runs have no provenance record
anywhere in the repo, so it cannot be resolved from disk. It is the single most reviewer-legible
defect in `tab:main` and it is larger than the FN-adjustment effect.

The symmetric problem exists on the `actions` column in our own disfavour: the Gated-Reset row
uses raw n=25 (disclosed at `:508`) while every other actions row uses n=23. Placing it on the
filtered pool would move it from 61.3 to at most 66.7.

---

## 4. Corrected matrix at scale — arm-symmetric re-judge

Since the published runs are unrecoverable, the correction was executed on the largest complete
comparable matrix that survives: `outputs/post_neurips_ac3_phase1` — deepseek-v4-flash, sharded
user sim, **4 tasks × 6 arms × 3 replicate runs at temperature 1.0** (not "seeds"). 1217
incorrect samples re-judged; **0 errors, 0 missing traces**. Judge
`gpt-5.4-mini_2026-03-17` on trapi at concurrency 5. `rejudge.py` reuses
`identify_false_negatives.analyze_sample` verbatim, so message visibility is the only thing that
differs from the shipped path.

n and correct pooled over the 3 replicate runs.

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

After correction, adjusted−raw collapses to **+0.0 to +3.9 pp and is uniform across arms** —
which is what a valid adjustment looks like.

---

## 5. ⚠ Does any qualitative conclusion change? **Yes — two.**

Δ vs Baseline, per task:

| arm | task | Δ raw | Δ shipped-adj | Δ arm-symmetric | verdict |
|---|---|---|---|---|---|
| AO | all four | +10.0 … +25.7 | +12.7 … +28.4 | +11.2 … +27.4 | holds |
| AC3-Augment | all four | +8.0 … +23.9 | +10.6 … +25.2 | +9.1 … +25.6 | holds |
| AC3-Reset | math/code/db/actions | +9.7 / +24.8 / +26.5 / +7.3 | +25.4 / +56.1 / +47.3 / +21.7 | +10.5 / +27.1 / +26.6 / +7.9 | **holds in all 4** |
| AC3-Gated-Reset | math/code/db/actions | +10.4 / +21.2 / +27.2 / +9.3 | +26.2 / +51.8 / +50.4 / +21.7 | +10.6 / +22.2 / +26.9 / +9.9 | **holds in all 4** |
| AC3-Rewrite | math | +1.4 | +25.3 | +0.9 | holds (barely) |
| AC3-Rewrite | database | +5.4 | +25.1 | +5.3 | holds |
| **AC3-Rewrite** | **code** | **−6.2** | **+46.0** | **−5.3** | **FLIP: win → loss** |
| **AC3-Rewrite** | **actions** | **−2.0** | **+22.4** | **−1.5** | **FLIP: win → loss** |

**AC3-Rewrite beats baseline in 4/4 cells under the shipped metric and loses in 2/4 under the
correction.** On code it goes from **+46.0 pp ahead to 5.3 pp behind**.

**Scope — stated precisely so this is neither buried nor overstated.** `tab:main` has no
AC3-Rewrite LiC row, and `tab:megatable` — where AC3-Rewrite does appear — is computed from raw
(`scripts/build_mega_table.py:87-96`). **The flip is therefore not a currently-published
error.** What it is: proof, on our own arm and our own data, that this metric can manufacture a
46 pp win out of a 6 pp loss. That is the argument for deleting it.

**What survives.** AC3-Reset and AC3-Gated-Reset beat Baseline in **all 8 cells** under raw,
shipped-adjusted and arm-symmetric alike. The Gated-vs-Reset ordering is preserved cell-for-cell
under raw and arm-symmetric (Gated ahead on math/database/actions, Reset ahead on code); the
shipped metric alone ties them on actions (99.2 vs 99.2), because exclusion pins both at the
ceiling.

---

## 6. Controls

Four separate harness faults were found elsewhere tonight, so every number above is backed by a
control with a known answer.

- **C1 — reproduce the shipped metric exactly.** For all 499 archived runs carrying
  `adjusted_accuracy`, `correct / (n_valid − user_sim_induced)` reproduces the shipped value to
  1e-6. **0 discrepancies.** My reader is on the right fields.
- **C2 — cross-file agreement.** `results.json` ↔ `metrics.json` ↔ `run_summary.json` on n,
  correct and accuracy, per run: **0 mismatches** (guards the double-write corruption trap).
  `metrics.user_sim_induced` ↔ `false_negatives.json.summary`: **0 mismatches**.
- **C3 — the no-op trap screened.** 0 archived runs have incorrect samples but 0 analysed; 0
  all-errored; 0 errored FN samples. Every archived judge is `gpt-5-mini`, served on the
  endpoints in use at the time. **No archived adjusted number needs excluding on this ground.**
  (The trap applies to *new* runs under `load_balancer=trapi`; `rejudge.py` accordingly pins
  `gpt-5.4-mini_2026-03-17`.)
- **C4 — judge-model drift is separated from the visibility effect, not assumed away.**
  `rejudge.py --mode visible` reruns the *shipped* visibility with the *new* judge, giving a
  clean two-step decomposition over the same 1217 samples:

  | arm | resets? | judged | shipped excl (gpt-5-mini, visible) | visible excl (gpt-5.4-mini, visible) | symmetric excl (gpt-5.4-mini, all) | Δ from judge swap | Δ from visibility | user turns seen (visible → symmetric) |
  |---|---|---|---|---|---|---|---|---|
  | AC3-Augment | no | 180 | 18 | 10 | 10 | −4.4% | **+0.0%** | 5.09 → 5.06 |
  | AO | no | 166 | 20 | 12 | 12 | −4.8% | **+0.0%** | 4.90 → 4.88 |
  | Baseline | no | 264 | 18 | 7 | 10 | −4.2% | **+1.1%** | 5.38 → 5.35 |
  | AC3-Gated-Reset | **yes** | 171 | 136 | 88 | 9 | −28.1% | **−46.2%** | 1.18 → 5.15 |
  | AC3-Reset | **yes** | 172 | 135 | 94 | 13 | −23.8% | **−47.1%** | 1.18 → 5.05 |
  | AC3-Rewrite | **yes** | 264 | 212 | 150 | 13 | −23.5% | **−51.9%** | 1.00 → 5.20 |

  Pooled: judge swap −4.4% (no-reset) / −24.9% (reset); **visibility +0.5% (no-reset) / −48.9%
  (reset)**. The visibility column is the falsifiable prediction and it passes: on arms where
  the two inputs are literally the same text, changing "visibility" moves nothing (+0.5%); on
  arms that reset it moves half of all judged samples. Reported honestly: gpt-5.4-mini is
  somewhat more lenient than gpt-5-mini when handed a single shard, so ~24 of the reset arms'
  ~80% shipped exclusion rate is judge-specific — but that is a *second* problem with the
  metric (it is judge-sensitive precisely because the input is degenerate), not an escape from
  the first.
- **C5 — positive control on the mechanism.** `mean_user_turns_seen` under the shipped path is
  **1.00** for AC3-Rewrite and **1.18** for the Reset arms, against 4.9–5.4 for every no-reset
  arm and 4.9–5.2 for every arm under the symmetric path. The judge really is being shown one
  shard, exactly as `format_user_messages` + `reset_conversation` predict.

---

## 7. Recommendation — what the paper should report

**Report raw accuracy as the primary metric, and keep the pool-level pre-filter as the only
false-negative adjustment. Delete per-run `adjusted_accuracy` from the paper entirely.**

Justification a reviewer would accept: a false-negative adjustment is legitimate only if the
exclusion decision is independent of the treatment. Our pool-level filter satisfies that — it is
computed once from baseline traces and applied identically to every arm, so it removes the same
items from every denominator and is just a cleaner benchmark. The per-run adjustment does not:
the judge is shown only the *visible* messages, which for any arm that resets the context is a
single user shard, so the exclusion rate is a downstream consequence of the intervention being
measured. We observe it deleting 59–100% of failures from reset arms against 1–39% from
non-reset arms and inflating accuracy by up to 56 pp; on our own AC3-Rewrite arm it converts a
5-point loss against the baseline into a 46-point win. Re-running the identical judge and prompt
on the complete user-message history — which is identical across arms by construction, since
every arm receives the same shards from the same user simulator — collapses exclusions to a
uniform 0–9 per cell and returns adjusted accuracy to within 0–4 pp of raw, in every arm. At
that point the adjustment no longer changes any ordering, so raw accuracy is both the safer and
the simpler thing to report.

Concretely:

1. **`tab:main`:** report raw over the pre-filtered pool. Recompute the four
   possibly-adjusted cells (AO/code, Concat-User/math, AC3-Augment/code, AC3-Reset/code) at the
   pool denominator; the change is ≤ 4.2 pp per cell and two of the four move in prior work's
   favour, which is worth saying out loud.
2. **Fix the denominators before worrying about the metric.** Put ERGO and AC3-Gated-Reset on
   the same pre-filtered pools as every other row (§3b). ERGO is currently scored on 23/25/25/25
   while everyone else is on 20/19/25/23 — an unfair-to-baseline discrepancy of up to ~14 pp
   that a reviewer can spot from the printed percentages alone.
3. **Rewrite `neurips_2026_conference.tex:478-480`.** As written it says "we collate all user
   simulator messages"; the code collates the visible ones. Describe the pool-level filter (what
   we actually want to defend), state the sample IDs removed, and drop the per-run procedure.
4. **Report raw + n per cell, and stop mixing metrics inside a column.** The current `actions`
   column mixes n=23 and n=25 rows; the `code` column mixes 18, 19 and 25.
5. **Ship the arm-symmetric re-judge as the fix** if any adjustment is kept: two-line change —
   in `identify_false_negatives.get_active_messages`, do not filter on `visible` for the
   sufficiency check, and dedupe.
6. **Never quote `run_summary.json → metrics.adjusted_accuracy` for a context-editing arm.**
   `neurips_review/replies/v5/README.md:105` already says this; the rebuttal (v5) is clean and
   discloses the bias. v4 was not — it quoted AC3-Reset at 100.0 ± 0.0 from
   `exp1_reps_results.txt`, where rep3 reset reads raw 87.50% (35/40) → adjusted 100.00%
   (35/35), 5 of 5 failures deleted.

---

## 8. Artifacts

| file | contents |
|---|---|
| `survey.py` / `survey.json` | shipped exclusion rates + inflation for all 558 archived FN runs, no LLM calls |
| `rejudge.py` | arm-symmetric re-judge; `--mode symmetric\|visible`; reuses `analyze_sample` verbatim |
| `rejudge_post_neurips_ac3_phase1_symmetric.json` | per-run symmetric results, 72 cells |
| `rejudge_post_neurips_ac3_phase1_visible.json` | per-run shipped-visibility control, same judge |
| `analyze.py` / `corrected_matrix.{json,txt}` | the §4/§5 tables and the flip test |
| `worklog.md` | chronological record |

Snapshot extracted to `/home/t-matthewho/ac3/t14_snapshot/` (5.0 GB, `outputs/ scripts/ docs/`);
delete when done. Nothing was written into other agents' output directories.
