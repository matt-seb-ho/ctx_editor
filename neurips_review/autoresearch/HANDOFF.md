# Operator Handoff — Autoresearch Session 2, 2026-07-29

Read this instead of `WORKLOG.md`. Everything here traces to a finding ID (F*) in
[`WORKLOG.md`](WORKLOG.md) and an artifact on disk. Paths are relative to the repo root
`/home/t-matthewho/ac3/ctx_editor/` unless they start with `~`.

Two agents (T6, T2B) were still running when this was written. See §5.

---

## 1. Bottom line

The session **net-strengthened the submission, but mostly by subtraction**: it found more
problems with claims we had already written than it produced new wins. Nine of our own
numbers moved; four of those moved against us, and a tenth correction *raises a
competitor's* number. Every one of them was findable by a reviewer with our own printed
tables and a calculator, so finding them first is the good outcome — but do not read the
finding count as a win column.

The core result survives everything thrown at it: **AC3-Reset and AC3-Gated-Reset beat
baseline in all 8 LiC cells under raw, shipped-adjusted and arm-symmetric-corrected
accuracy alike** (F40), and the Gated-vs-Reset ordering holds cell-for-cell.

Four promises from v4 are now completed experiments (condensation baseline, detector
evaluation, WildChat judge checks, memory split analysis), plus the analyzer sweep Vg97
asked for and we had never answered.

**Most urgent single thing: PAPER-7.** We scored ERGO on the wrong denominators, which
understated a competitor by up to ~10 pp on math. `replies/v5/` now commits to that fix
**in front of the reviewers**. Posting the rebuttal without making the paper edit means
announcing a correction we have not made.

**Second: do not post anything yet.** Five `⚠ INTERNAL — HOLD` blocks in `replies/v5/`
are sealed pending T6, which has preliminary evidence that two of three published tau2
baselines do not replicate.

---

## 2. Claims that must change before anything is submitted

Ordered by severity. "Fixed in v5" means the reply set already carries the corrected
wording; it does **not** mean the paper does.

| # | We claimed | What is true | Finding | Artifact | Status |
|---|---|---|---|---|---|
| 1 | ERGO scored comparably to every other row in `tab:main` | **ERGO alone used the unfiltered pools** (23/25/25/25 vs everyone else's 20/19/25/23). Corrected: math **69.6 → 80.0**, code **≈44.0** (unchanged), database 12.0, actions unclosable **[43.5, 52.2]**. Corrected ERGO/math **beats AC3-Reset (75.0) and ties Gated-Reset (80.0)**. Measured scorecard: ERGO wins-or-ties **3/12**, not the published 1/12 | F42, F43, F44, F48 | `autoresearch/tasks/T17/RESULTS.md`, `tasks/T17/corrected_tabmain.json`, `tasks/T18/worklog.md` | Disclosed in v5 (5 places). **Paper: PAPER-7, not applied** |
| 2 | Per-run `adjusted_accuracy` is a valid metric | The FN judge reads **visible** messages only, so reset arms get 50–78% of failures excluded vs 9% for baseline. Inflates reset arms **+13.9 to +55.9 pp**, no-reset arms +0.2 to +6.5. Shipped example: AC3-Reset database **89.0% published vs 77.1% corrected**. Judge sees 1.00 user turns/sample on Rewrite vs 5.35 on baseline | F28, F40, F41 | `autoresearch/tasks/T14/{RESULTS.md,corrected_matrix.*}` | v5 is raw throughout. **Paper: PAPER-6** |
| 2b | (scope of #2) `tab:main`'s 20/19/25/23 denominators are suspect | **They are not.** They come from an arm-symmetric **pool-level pre-filter** (`data/baseline_traces_v2/*_false_negatives.json`) that reproduces them exactly. **Defend this, do not concede it.** Only the *per-run* metric is invalid | F42, D13 | same | v5 defends it explicitly |
| 3 | Rebuttal end-to-end: **AC3-Reset 100.0 ± 0.0** | That table was itself FN-adjusted with **asymmetric exclusions** (Reset 1/2/5 items excluded, Baseline 0). Raw: Baseline **87.5 ± 2.0**, Reset **93.3 ± 4.2**, Gated-Reset **95.0 ± 0.0**. Claim survives — both operators win in all three runs — the perfect score does not. It appeared in **five files** | F34 | `neurips_review/experiments/exp1_reps_results.txt` | Fixed in v5 |
| 4 | CollabLLM MATH-Hard **100%** | Does not replicate. N=3: AC3-Augment **91.7 ± 7.6** vs Baseline **91.7 ± 5.8** — identical means *and* identical 55/60 per-problem totals; per-replicate delta [+5, −10, +5] = **0.0 ± 8.7**. Say **"matches Baseline"**, which still refutes 5YHP's regression claim | F16 | `autoresearch/tasks/T8/worklog.md` | Fixed in v5. **Paper: PAPER-4** |
| 5 | "We preserve what's correct and remove what's harmful" | **Not supported for *either* operator — retract, do not re-attribute.** On *constructed* spans, Reset's edit precision is **50.4%** against 50% chance with **4.0%** preservation, and Rewrite looked like the selective exception (27.0 / 38.9) — which is why F25 said "attribute, don't retract". **T2B overturns that on *natural* spans, causally, with no detector or judge in the label path:** Reset keeps **5/66** probe-admissible spans, **Rewrite keeps 0/66**, preservation on causally useful spans is **0% for both**, edit precision is **63.6% = the base rate for both**, and the label-free aggregate test agrees (Reset removed−kept −0.014, p=0.85). Rewrite only looked selective because a short self-contained *injected* sentence survives compaction verbatim; the model's own prose and code get paraphrased. **The mechanism for both operators is *detect → discard the assistant side → rebuild the specification from the user side*.** | F25, **superseded by F66** | `autoresearch/tasks/T2B/RESULTS.md` §4, `tasks/T2B/per_span_alignment.json`; earlier: `tasks/T2A/RESULTS.md`, `outputs/T2A/` | **Retracted in v5 by T25** (`replies/v5/CHANGES.md` §11.1). **Paper: PAPER-5** (framing is also in `CLAUDE.md`/project overview) |
| 6 | Bare **97.6%** pollution-removal rate | True but unquotable alone — a delete-everything editor scores 1.000 on it, as our own PC3/PC4 controls show. Always report the quartet: detection (**78.6%** pollutant naming, 89.7% on the causally-harmful subset), removal 97.6%, preservation 4.0%, edit precision 50.4% vs chance 50 | F23, F26, D9 | `autoresearch/tasks/T2A/{RESULTS.md,measure.py}` | Fixed in v5 |
| 7 | "N=3 **seeds**" on LiC and CollabLLM | `cfg.seed` was read only by `huang_eval/`; every `seed=$((42+rep))` was **inert**, and the CollabLLM loaders hardcode `random.Random(42)` so all replicates drew the *same 20 problems*. Replicates varied through **temperature-1.0 sampling only** — decoder variance, not sampling variance. Say "3 replicate runs at temperature 1.0". **WildChat's N=3 are real seeds and keep the word.** Fixed going forward in 2 lines (F19); prior runs reproduce bit-for-bit | F4, F19 | `autoresearch/tasks/RECON/worklog.md`, `tasks/T8/worklog.md` | Fixed in v5. **Paper: PAPER-1** |
| 8 | Memory gains **+10 pp math / +12 pp database** | Single trials against a **~6 pp learner noise floor** — under 2σ. Variance controls: across-ordering sd **6.5** does not exceed same-ordering sd **6.1**, so ordering is not a distinguished factor; the learner is just noisy. An N=4 remeasure on gpt-5.4-mini gives **−5.0 / −8.0 pp** (different model, so not a direct refutation — but the variance argument is model-independent) | F12, D7 | `autoresearch/tasks/T12-T13/worklog.md` §9, `outputs/T12_T13/` | Dropped from v5. **Paper: PAPER-3** |
| 9 | WildChat headline **89.8 / 92.1** | Order-balanced re-judge: **87.8 ± 2.1** (Reset) / **91.2 ± 2.1** (Augment). The headline judge prefers the second-presented response (32 vs 8 of 44 discordant pairs, binomial **p = 1.8e-4**), but `pairwise_judge.py` already randomises A/B 50/50, so the published number is unbiased *in expectation* — report the corrected values anyway, it is a cheap concession | F30, F31 | `autoresearch/tasks/T11/{worklog.md,out/}` | Fixed in v5 |
| 10 | AC3-Reset beats assistant-omission on BigCodeBench (+6.7 pp) | AO column at N=3 is **18.3 ± 5.8**, narrowing the margin to **+3.3 pp** — two problem-instances in sixty, inside the noise, and the two arms succeed on partly different problems. **Do not claim this ordering.** Lead instead with AC3-Reset over **full context**: +15 pp in 3 of 3 replicates | F57 | `autoresearch/tasks/T21/worklog.md`, `outputs/T21/` | Fixed in v5 |
| 11 | Table 3 caption: gpt-5.4 comparison "on the same prefixes" | **False.** Reset scored on 44 turns, Gated-Reset on 58, only **35 shared**. On the matched 35 the gap survives (+14.3 pp) but rests on **7 discordant turns, 6 vs 1, exact McNemar p = 0.125** | F55 | `autoresearch/tasks/T20/worklog.md` §U2 | Claim struck from v5. **Paper: PAPER-8** |
| 12 | Gate-open rates 97.3% / 98.3% are *turn*-level detection rates | Numbers reproduce **exactly**, but they are per-**conversation**, and turn-level CollabLLM is **95.3%** (628/659). Also a **firing** rate, not a detection rate: 29% (LiC) / 73% (CollabLLM) of gate-open records carry `issues: "None"` while setting `needs_edit=true` | F39 | `autoresearch/tasks/T16/{gate_stats.py,report.md}` | Fixed in v5 |
| 13 | Two things we conceded that were false | (a) "BigCodeBench cannot be evaluated with executable tests" — it can; that path runs real `untrusted_check` execution. (b) Two documentation artifacts the paper cites do not exist: `docs/paper_experiments_provenance.md` names absent configs, and `docs/multi_run_variance_2026-05-07.md` — cited **twice** as the source of the appendix variance table — has never existed | F36, F8 | `autoresearch/tasks/T8/worklog.md` §5; `tasks/RECON/worklog.md` | (a) struck from v5. (b) **Paper: PAPER-2** |
| 14 | Judging was deterministic (temperature 0) | The client logs `gpt-5 models require temperature=1.0, overriding 0.0 -> 1.0`. Substitute the honest figure: **96.9% self-consistency, κ 0.810** | F33 | `autoresearch/tasks/T11/worklog.md` | Fixed in v5 |

---

## 3. New results that strengthen the rebuttal

### T1 — the Area Chair's "limited baselines", answered empirically (F27)

| Task | Arm | Acc | n | Δ vs base | McNemar p |
|---|---|---|---|---|---|
| database | Baseline (full context) | 56.1% | 60/107 | — | — |
| database | Summarisation, 1 call/turn | 53.3% | 57/107 | −2.8 | 0.678 |
| database | Summarisation, 2 calls/turn (budget-matched) | 47.7% | 51/107 | −8.4 | 0.078 |
| database | MT-OSC (reimplemented, w=4 as published) | 60.7% | 65/107 | +4.7 | 0.383 |
| database | **AC3-Reset** | **75.7%** | 81/107 | **+19.6** | **0.0005** |
| database | **AC3-Gated-Reset** | **73.8%** | 79/107 | **+17.8** | **0.0013** |
| code | Baseline (full context) | 83.0% | 83/100 | — | — |
| code | Summarisation, 1 / 2 calls | 79.0 / 80.0% | — | −4.0 / −3.0 | 0.481 / 0.581 |
| code | **AC3-Reset** | **92.0%** | 92/100 | **+9.0** | **0.023** |

Head-to-head paired: AC3-Reset − summarisation = **+22.4 / +28.0 pp** (database),
**+13.0 / +12.0 pp** (code), all p < 0.01.

The budget result is better than parity: the budget-matched summariser **over-consumed**
AC3-Reset (**1.02–1.19× strategy calls, 1.62–2.14× strategy tokens**) and still lost by
12–28 pp. Gated-Reset gets +17.8 pp on **0.41×** Reset's calls. MT-OSC at published w=4
fired **30 times across 107 conversations (0.3/conv)** because it cannot touch context
before turn 6 while LiC conversations average 4.1 turns — i.e. length-triggered
compaction schedules *structurally cannot engage* with early pollution. That is our
scoping argument with a number behind it.
Artifacts: `autoresearch/tasks/T1/{RESULTS.md,worklog.md,analyze.py}`, `outputs/T1/`.

### T9 — analyzer-model sensitivity, the unanswered half of Vg97 Q3 (F21, F22)

Assistant pinned to DeepSeek-V4-Flash; only `model.ctx_editor.model` varies. n=178
matched pairs, exact McNemar, LiC code+database replay (Baseline 21.3% pooled).

| Analyzer | Family | AC3-Reset | Δ vs Baseline | p |
|---|---|---|---|---|
| Kimi-K2.6 | Moonshot | 61.2 ± 2.4 | **+39.9** | 2e-17 |
| DeepSeek-V4-Flash (ref) | DeepSeek | 50.0 ± 2.4 | **+28.7** | 3e-09 |
| gpt-5.4-mini | OpenAI | 48.3 ± 1.6 | **+27.0** | 1e-08 |
| Llama-3.3-70B | Meta | 39.3 ± 0.0 | **+18.0** | 6e-06 |
| gpt-4o-mini | OpenAI | 34.3 ± 0.8 | **+12.9** | 8e-04 |

Graceful degradation, not collapse: every analyzer is individually significant, the
weakest still beats Baseline by 12.9 pp, and **no arm falls below Baseline on either task
in either replicate**. The mechanism is measured, not assumed — weak analyzers
**under-detect rather than mis-detect** (gpt-4o-mini fires on 74.4% of turns vs ~97% for
strong analyzers, 2.7× shorter issue lists, but `user_intent` parsed on 100% of calls and
`edited_context` non-empty on 100% of applied edits). Three of five analyzers are
non-OpenAI, the **best is Kimi-K2.6 (+12.9 pp above our own default)** and the *weakest*
is an OpenAI model — so the best cell contains no OpenAI model anywhere, which kills the
"gpt-specific" reading. Defend the shape and the endpoints, not the exact ordering.
The `analysis_cache` confound was resolved, not worked around (F20).
Artifact: `autoresearch/tasks/T9/worklog.md` (`1f4f32d`), `outputs/T9/`.

### T2A + T2c — the detector story (F10, F23, F24, F25)

**T2A (constructed pollution, no judge anywhere).** Two spans injected per conversation —
one known-false, one known-true, identical surface frame — so labels are ground truth by
construction and preservation is measurable at all. n=126 admissible.
Removal **97.6%** [93.2, 99.2] · preservation **4.0%** · edit precision **50.4%** (chance
= 50) · gate sensitivity **98.4%** · **analyzer names the injected pollutant in `issues`
78.6%** of the time (89.7% on the causally-harmful subset). That naming rate is the part
not explainable by "it deletes everything."

Causality is built out of **Baseline** arms, not detector output, so it is non-circular:
a factorial over clean / harm-only / useful-only / both gives the harmful span
**−11.1 pp** and the true span **+15.1 pp**; on the causally-validated subset Baseline
clean 24.7% → 9.3% with the pollutant → **AC3 59.8% with the pollutant still present**.
Four positive controls pass exactly (identity 0.000/1.000, oracle 1.000/1.000, nuke and
delete-both 1.000/0.000). Stated caveat: injected pollution is more salient than natural,
so this is an upper bound / sanity check.

**T2c (auditing vs re-solving — 5YHP's mechanism challenge).** Analyzer text was already
persisted, so zero re-runs. Strict leakage base rate: math 38%, code **0%**, database 1%,
actions 2%; overall 11% (n=547), with a model-free numeric probe on math returning 40%
against the LLM's 38%. **Paired gain on the NO_LEAK subset (exact McNemar), n=329:
36.5% → 57.1% = +20.7 pp [+14.8, +25.3], p < 0.0001.** Code alone **+30.2 pp with zero
leaks**; database +26.0 pp with one; Gated-Reset replicates at +19.6 pp.
**Concede math outright**: NO_LEAK n=77 gives **−2.6 pp [−11.9, +7.6]** — on GSM8K you
cannot say "your total of 3,270 is wrong" without computing the right total, so auditing
and solving are not separable there. Conceding math and holding code/database is far more
credible than claiming the mechanism everywhere.
Artifacts: `autoresearch/tasks/T2A/{RESULTS.md,inject.py,measure.py}`,
`autoresearch/tasks/T2c/{RESULTS.md,worklog.md}`.

### T11 — WildChat judge checks (F30–F33)

1,824 judgements, 0 hard failures. Position bias is real (**p = 1.8e-4**) but the harness
already randomises A/B per call, so the published number is unbiased in expectation;
corrected headline **87.8 / 91.2** (see §2 #9). Cross-family agreement: raw 85.9–88.8%,
κ 0.445–0.507, and because κ is depressed by the ~90% marginal (the kappa paradox) the
right statistics are **PABAK 0.79–0.83 and Gwet's AC1 0.84–0.87**. Self-consistency
**96.9% / κ 0.810** — materially above swap-consistency, cleanly attributing judge
instability to **order rather than sampling**. Per-judge order-balanced win rates
88.8 / 85.6 / 85.3 (max spread 3.5 pp); under a punitive "2-of-3 judges in both orders"
rule, still **82.5%**. Positive controls (intact vs degraded copy) 39/40, 36/40, 40/40.
Artifacts: `autoresearch/tasks/T11/{worklog.md,out/}`.

### T13 — zero contamination (F13)

5YHP's contamination concern is **measurably unfounded**, with numbers. Learn set vs the
canonical `lic_eval_subset`: **0/120 exact duplicates, 0 near-duplicates** (max Jaccard
0.416, boilerplate only). A within-instance probe of the transductive protocol — same
instance with an empty cheatsheet vs one distilled from 5–20 *other* eval instances
**plus their gold answers** — gives **0.0 pp on both tasks**. On the 11/98 overlapping
instances memory is equal or worse than no-memory. This is the half of the memory story
to lead with (D7).
Artifact: `autoresearch/tasks/T12-T13/worklog.md` §9.

### T8 — BigCodeBench survives and is stronger than we claimed (F17)

| Arm | rep1 | rep2 | rep3 | mean ± sd |
|---|---|---|---|---|
| AC3-Reset | 5/20 | 5/20 | 3/20 | **21.7 ± 5.8** |
| Baseline | 2/20 | 2/20 | 0/20 | **6.7 ± 5.8** |

**+15 pp in every replicate — 3/3 wins, sd of the delta 0.0.** Reset solves 9
problem-instances Baseline never solves once and loses none. It **reproduces on a fully
disjoint 20-problem draw** (0/20 overlap): Reset 3/20 vs Baseline 1/20 — same-direction
evidence on non-overlapping problems, which is worth stating explicitly. Quote as
"≈1 in 5, ±1 problem" with the scoring environment named, never a bare percentage: at
n=20 every cell moves in 5 pp steps and one problem flips deterministically on a library
version. All cells re-scored offline under one unified environment.
Artifact: `autoresearch/tasks/T8/worklog.md`, `outputs/T8/`.

---

## 4. PAPER-1..8 — the operator action list

These all touch `writing/overleaf_repo/`, which is shared with Lianhui and Michel and
synced to Overleaf. They were deliberately **not** actioned autonomously. Pull before
editing (`git -C writing/overleaf_repo pull origin main`).

| ID | Do this | From | Effort | Blocking? |
|---|---|---|---|---|
| **PAPER-7** | Fix ERGO's denominators in `tab:main`. Ship math **80.0**, code **≈44.0**, database 12.0; actions is **unclosable** — print as interval **[43.5, 52.2]** or drop, never as a point estimate. **Never ship T17's 57.9 for code** (it overstates a competitor by ~14 pp; T18 measured k = 2.67/6, not 0/6). Lead the passage with F49: **no ERGO-vs-AC3 `tab:main` difference is significant at n≈20 in either direction** (code p=0.375, math p=1.00). Two body numbers move *in our favour*: code gap-closure 78% → 82%, "closes 55–80%" → "67–82%" | F42–F44, F48, D14 | 1–2 h | **YES — blocking.** `replies/v5/` commits to this fix in front of the reviewers |
| **PAPER-6** | Delete per-run `adjusted_accuracy` as a reported metric; report **raw** as primary; keep the arm-symmetric pool-level pre-filter as the only FN adjustment and **defend** it; rewrite `tex:478-480`, which says "all user simulator messages" when the code collates only the visible ones | F28, F40–F42, D13 | 2–3 h | Rebuttal-adjacent (v5 is already raw). Do before arXiv |
| **PAPER-5** | **Delete** "we preserve what's correct and remove what's harmful" from the abstract, intro and method — do **not** re-attribute it to AC3-Rewrite, which is what an earlier version of this row said. F66 shows neither operator is selective on naturally occurring spans (Reset keeps 5/66, Rewrite 0/66, edit precision at the base rate for both). Replace with the mechanism that is supported for **both** operators: *detect → discard the assistant side → rebuild the specification from the user side*, Reset by dropping that side and Rewrite by recompacting it. This also changes the **ERGO differentiation**: the difference is not "we are selective and they are not", it is that AC3 rebuilds the specification from the user side while ERGO rewrites user turns — and the defensible empirical claims are the 78.6% pollutant-naming rate, the factorial (9.3% → 59.8% with the pollutant still present), and T2B's 100% removal of causally-harmful natural spans. Same edit needed in the project overview / `CLAUDE.md` | F25, **F66** | 1–2 h (framing appears in intro + method) | Camera-ready |
| **PAPER-4** | Any CollabLLM MATH-Hard "100" → "matches Baseline" (91.7 vs 91.7) | F16 | 15 min | Camera-ready (already fixed in v5) |
| **PAPER-3** | Table 1's `+ Memory` rows are single-trial below a ~6 pp noise floor. Either re-run at **N ≥ 4** or soften the claim | F12 | 15 min to soften; hours of compute to re-run | Camera-ready |
| **PAPER-1** | Reword LiC/CollabLLM "seeds" → "replicate runs (temperature 1.0)"; add the decoder-vs-sampling-variance caveat to limitations. **WildChat keeps "seeds."** Note F19 fixed true seeding going forward and all prior runs reproduce bit-for-bit | F4, F19 | 30–45 min | Camera-ready, but cheap and an integrity item — do it early |
| **PAPER-2** | The appendix variance table cites `docs/multi_run_variance_2026-05-07.md`, which does not exist; `docs/paper_experiments_provenance.md` names absent configs (`assistant_omit`, `concat_baseline`). Re-derive or re-source | F8 | Unknown — depends whether the runs are recoverable from `~/ac3/blob_staging/snapshot.tar.gz` | Camera-ready |
| **PAPER-8** | `writing/overleaf_repo/neurips/neurips_2026_conference.tex:299` — replace "on the same prefixes" with the queued wording: "($-$14.5pp vs.\ always-on Reset; $-$14.3pp on the 35 prefixes both arms were evaluated on, exact McNemar $p=0.125$)" | F55 | 5 min | Camera-ready only — the claim is struck from v5, so nothing we post depends on it |
| **PAPER-9** | *(added by T25 from T24 §7.4)* `tab:main` caption: state that instances are the 25 per task with the **highest full-context failure rate** across five GPT-5-mini baseline runs, and that the design-oracle rows use the same instances so the gap-closure percentages are pool-independent. Without this, the paper's 4.0% database baseline reads as a measurement when it is largely what the selection guarantees | F68 | 10 min | Camera-ready — but **high value**: it is the paper-side half of the reconciliation the rebuttal now commits to |
| **PAPER-10** | *(added by T25 from T24 §7.5)* If any table reports assistant omission or Concatenate-User in **end-to-end** (non-replay) mode, label them baselines rather than upper bounds: they concatenate the *simulator's* paraphrases of the shards, not the original question, so they inherit the simulator's loss. On T24's unselected pool AO reaches 69.2% and Concat-User 63.6% against a measured single-turn ceiling of 94.4%. Report the single-turn ceiling separately | F69 | 30 min | Camera-ready; conditional on which tables survive |

Suggested order if time is short: **PAPER-7 → PAPER-1 → PAPER-8 → PAPER-6 → PAPER-4 →
PAPER-5 → PAPER-3 → PAPER-2.**

---

## 5. Still open

### T6 — multi-replicate tau2 (running)

**This is the session's largest remaining exposure and it may force a fifth
self-correction.** Preliminary only — do not treat the numbers below as final.

| Cell | published (seed 42) | remeasured N=3 | verdict |
|---|---|---|---|
| gpt-5.4 Baseline | 68.4 | **68.4 ± 13.9** | replicates exactly on the mean |
| **DSV4F Baseline** | **31.6** | **70.2 ± 11.0** | **does not — +39 pp** |
| **Kimi Baseline** | **26.3** | **80.4 ± 2.5** | **does not — +53 pp** |

If this holds, two of three tau2 cells were measured against **broken controls** — the
source report for the Kimi run itself admits infrastructure degradation ("14/20 short
exits", "true Baseline is probably 40–50%"; the remeasure says even that guess was low).
Kimi's remeasured baseline (80.4) is **above every published Kimi AC3 number** (Augment
57.9, Gated-Reset 68.4, Rewrite 73.7), which would invert the sign of those gains.
Note also that per-replicate spread is huge (gpt-5.4 Baseline spans 52.6–78.9 across
seeds, sd 13.9) — several published tau2 cell-to-cell differences are smaller than that.

T6 separately found a **tag-parse defect in the fork** (53% of analyzer briefings fall
back to an unparsed path; it degrades AC3 arms only and cannot touch Baseline or AO). It
chased that confound to ground with a gated diagnostic: fixing it moved accuracy **+2.3
pp**, not the ~37 pp needed to explain the AC3 collapse. So the AC3 underperformance in
this environment is being reported as a genuine measurement, not an artefact — but the
parser should still be fixed in the fork.

Status at 17:55: gpt-5.4 block **complete** (5 arms × 3 reps); Kimi has s0–s3 with AO
running; DSV4F has s0–s2 with s3 then AO to go. 3 errors in ~1700 rollouts.
**Consequences:**
- **Five `⚠ INTERNAL — HOLD` blocks in `replies/v5/` are sealed pending T6** — two in
  `00_general_response.md`, one each in `01`, `04`, `05`. Their integrity has been
  verified byte-identical twice. **Post nothing until they are resolved.**
  (`README.md` counts *eight* `⚠ INTERNAL` blocks total; the other three are an
  orientation preamble and two renumbering notes — bookkeeping, not unsettled results.)
- v5's tau2 section has already been rebuilt around the **AO-collapses-to-0%** result,
  which is mechanism-corroborated and safe, so the section stands even if the magnitudes
  are withdrawn. Draft withdrawal wording is pre-written inside the HOLD blocks.
- **U4** ("1 of 11 baseline failures") must be re-checked in the same pass — it is
  unverified *and* characterises a baseline T6 may move. T20 established it is
  technically decoupled from T6's matrix, and its traces are gone, so the standing
  recommendation is **soften now, defer re-derivation to camera-ready** (F56).

Log: `autoresearch/tasks/T6/worklog.md`. Fork at `~/ac3/tau2_ctxe` (deliberately outside
the shared tree).

### T2B — counterfactual span ablation (running)

Upgrades T2A's synthetic injections to **naturally occurring** spans, which is T2A's own
stated limitation, and includes the alignment check against **Rewrite** as well as Reset.
At 18:19 the main matrix was **120/172 runs (70%)**, projected finish ≈ 19:08, with
**0 errors in 2000+ samples**. Its three harness controls have already discharged in both
directions (contentless filler +0.029, p=0.79; T2A's validated pollutant +0.344, p<1e-4;
full-spec-plus-gold −0.440, p=1e-4), which ties T2A and T2B onto one scale. **The
natural-span result itself is not in yet — do not assume its direction.** Partial
artifacts: `autoresearch/tasks/T2B/{RESULTS.md,worklog.md,per_span.json}`, `outputs/T2B/`.

---

## 6. Where everything lives

| What | Where |
|---|---|
| **The rebuttal to post** | `neurips_review/replies/v5/` — `00_general_response.md` first, then `01`/`02`/`03`, then `04_response_to_AC.md`, then `05_final_remarks.md` at the end of the discussion period |
| **Claim-by-claim audit** | `neurips_review/replies/v5/CHANGES.md` — every v4 assertion, status, finding ID, artifact path, new wording |
| **Pre-posting checklist, guardrails, rhetoric plan** | `neurips_review/replies/v5/README.md` — read the "Accuracy guardrails" list before you touch any number |
| **v4 (diff baseline, untouched)** | `neurips_review/replies/v4/` |
| **Full narrative record, F1–F57, D1–D16** | `neurips_review/autoresearch/WORKLOG.md` |
| **What was run, in what order, and dead ends** | `neurips_review/autoresearch/PROVENANCE.md` — the "Dead ends and why" table at the bottom is the fastest way to see what we retired |
| **Per-task detail, scripts, verbatim prompts** | `neurips_review/autoresearch/tasks/<ID>/{worklog.md,RESULTS.md,*.py}` |
| **Machine logs** | `neurips_review/autoresearch/{logs/orchestrator.jsonl,state/}` — note D11–D14 lived only here for a while; the JSONL is the machine log, `WORKLOG.md` is the human one |
| **Run outputs from tonight** | `outputs/{T1,T2A,T2B,T8,T9,T12_T13,T18,T21}/` |
| **Recovered prior outputs** | `~/ac3/blob_staging/snapshot.tar.gz` (whole `outputs/` tree incl. CollabLLM competent-user-sim and all WildChat runs); `~/ac3/recovered/`, `~/ac3/recovered_t2c/`, `~/ac3/recovered_t20/`, `~/ac3/t14_snapshot/` |
| **Spider DBs (newly recovered)** | `data/spider/databases/` — 4.9 GB, gitignored, 17/17 db_ids, **test-suite** execution semantics from the `taoyds/test-suite-sql-eval` bundle. Provenance belongs in the camera-ready if we report database numbers (F1) |
| **tau2 fork** | `~/ac3/tau2_ctxe` |

---

## 7. Methodological lessons worth keeping

**Positive controls caught nine harness/comparability faults tonight**, several of which
would otherwise have become published numbers:

1. `unzip` leaving `__MACOSX/._*.sqlite` sidecars, which the eval's substring DB filter
   treats as real databases (F2).
2. Under TRAPI, the default FN-analysis model is not served, so FN analysis **silently
   no-ops** and deflates every accuracy number (F2).
3. `bigcodebench` package absent → cells report `0/0` (F18).
4. Package present but **matplotlib** missing → `reliability_guard` dies in-sandbox and
   the pass rate is swallowed as `0.0`. **A real 5/20 cell read 0/20 this way** — caught
   only by re-scoring a known-4/20 cell and getting 0 (F18).
5. Word-boundary vs substring matching (`Museum_ID` ⊂ `Museum_IDs`) silently overstating
   removal, caught by control PC2 (F26).
6. An MT-OSC schedule dropping raw pairs completed after the condensation window,
   manufacturing a 30 pp low score — **do not quote its 26.2%** (F29).
7. A duplicated background chain double-writing output dirs, caught by a contradiction
   between `metrics.json` and `run_summary.json` (F14).
8. T18's positive control **failing** to reproduce ERGO/database (44.0 vs published 12.0)
   because the published-era model is unreachable — which is exactly what stopped a
   plausible-looking set of numbers being written into `tab:main` (F46).
9. The AO BigCodeBench cell never re-scored under the unified dependency environment while
   every other cell in its row was, found by auditing the auditor (F54).

Plus a tenth in flight: T6's tag-parse defect, silently corrupting half of all analyzer
briefings in the tau2 fork (§5).

**Adding replicates dissolved an asserted margin four separate times** — CollabLLM
math-hard 100% (F16), the memory gains (F12), the ERGO ordering (F49), and
AC3-Reset-over-AO on BigCodeBench (F57). At n≈20 per cell, this benchmark family
**cannot resolve differences below roughly 10 pp**, and several of our narrower claims
were reading noise. That belongs in the paper's limitations as a positive statement about
what the evaluation can and cannot support (D16), and it is also the most defensible
frame for the ERGO comparison: not "who wins", but "n≈20 cannot resolve this."

**Two smaller rules earned tonight:**
- **Never strike a claim for unverifiability without a documented deep search** across the
  repo, `scripts/`, `docs/`, `outputs/`, `runs.yaml`, both tarballs and the recovered
  trees. Twice tonight "no artifact exists" meant "the audit did not look hard enough" —
  T20 recovered three of four, and striking a true claim gave away a defensible number
  for nothing (D15, F39, F53).
- **Report a validated sub-metric rather than an unvalidated headline.** T2c's 3-way leak
  classifier scored only 10/24 on a held-out draw, so it reported the quantity it could
  validate — **precision of the NO_LEAK label, 29/32** — and built the primary numbers on
  a stricter model-free detector instead (F10).
