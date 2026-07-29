# Operator Handoff — Autoresearch Session 2, 2026-07-29

Read this instead of `WORKLOG.md`. Everything here traces to a finding ID (F*) in
[`WORKLOG.md`](WORKLOG.md) and an artifact on disk. Paths are relative to the repo root
`/home/t-matthewho/ac3/ctx_editor/` unless they start with `~`.

**Refreshed by T29 at F1–F83 / D1–D21. The session is over: every experiment and every edit
pass is complete, nothing is in flight.** Two earlier versions exist (T22 at F58, commit
`11d8e40`; T26 at F72, commit `701f6b6`) and **both are now wrong about the headline**.

**Amended by T36 at F94–F97 (zero API calls).** T31b turned §4's item list into a ready-to-apply
edit specification, [`PAPER_EDITS.md`](PAPER_EDITS.md), and in doing so found that **this document
endorsed a drafted PAPER-9 caption that is wrong twice** (F94), that **Figure 1's image — not only
its caption — is now false and has no recoverable source** (F95), that the "appropriate intensity"
ordering **inverts rather than weakens** (F96), and that **four PAPER items have no target in the
paper as §4 describes them** (F97). Those corrections are folded in below.

**For anything under §4, work from [`PAPER_EDITS.md`](PAPER_EDITS.md), not from §4's one-line
descriptions.** It gives, per item, the exact current text quoted from the live `.tex`, the
paste-ready replacement, the finding ID behind every number, and effort/risk. **Nine of the eleven
items are paste-ready; two (PAPER-5, PAPER-11) are judgement calls with options laid out and
deliberately not chosen.** PAPER-7 remains the **only** posting blocker and is now a **~20-minute
paste** (item 7a); T31b's items 1–7 total roughly **1 h 30 m**. §4 below stays as the rationale and
the priority argument; `PAPER_EDITS.md` is where the work happens.

**If you read only one thing: the tau2-bench comparison is withdrawn.** T6, the last and
longest experiment of the session, re-ran the full published tau2 matrix at N=3 and found that
**two of three published baselines do not replicate**. On all three models the remeasured
baseline is at or above every AC3 arm. This is not a caveat; it removes a benchmark that was
front and centre in the abstract, Figure 1, the General Response and the AC letter. See §2 row
**0**, §3 first subsection, and **PAPER-11**.

The counterweight, which is real: **the Area Chair's baseline reservation is now empirically
closed** (§3, T27/M11), and the core LiC result survived everything thrown at it.

---

## 1. Bottom line

The session **net-strengthened the submission, but overwhelmingly by subtraction**. It found
substantially more problems with claims we had already written than it produced new wins.
Roughly a dozen of our own numbers moved; most moved against us, one correction *raises a
competitor's* number, and one **withdraws an entire benchmark**. Nearly all of it was findable
by a reviewer with our own printed tables and a calculator, so finding it first is the good
outcome — but do not read the finding count as a win column.

**Two things are simultaneously true and both belong in the same sentence when you brief
anyone:**

1. **The tau2 story inverts and the improvement claim is gone** (F78–F81, D21). The one tau2
   result that survives — **AO → 0.0% on every model, structurally, 9/9 cells, 171 rollouts,
   reproducing the published 0/0/0 exactly** — is also the one the paper most needs tau2 for,
   because it is the evidence that blanket omission fails when state lives in assistant turns.
2. **The core LiC result survives every attack**: AC3-Reset and AC3-Gated-Reset beat baseline in
   **all 8 LiC cells under raw, shipped-adjusted and arm-symmetric-corrected accuracy alike**
   (F40), the Gated-vs-Reset ordering holds cell-for-cell, and the headline paired result now
   carries an item-level test and a problem-clustered interval: **+15.4 pp, 95% CI [+11.5,
   +19.4]**, 350 W / 93 L over 1,668 paired items (F77).

Four promises from v4 are now completed experiments (condensation baseline, detector
evaluation, WildChat judge checks, memory split analysis), plus the analyzer sweep Vg97 asked
for and we had never answered. **T1, T9, T2A/T2B, T11 and T27 are genuinely new evidence**, not
repairs.

Three things to act on, in order:

1. **Absorb the tau2 withdrawal before you talk to anyone about this paper.** `replies/v5/` is
   already fully rewritten around it (T28, zero API calls) — the withdrawal is applied in `00`
   CW1+CW4, `01` W3, `02` W2/Q2, `04` correction 6, `05` correction 8, `README`, `CHANGES` §12.3.
   The **paper** still asserts the old story in the abstract, Figure 1, the intro,
   `tab:megatable`, §`sec:tau2-results`, the discussion and the conclusion. That is **PAPER-11**.
2. **PAPER-7 is still the only hard blocker on posting.** We scored ERGO on the wrong
   denominators, understating a competitor by up to ~10 pp on math. `replies/v5/` commits to
   that fix **in front of the reviewers** in five places. Posting without making the paper edit
   means announcing a correction we have not made (F58). **T31b has since specified it
   paste-ready — `PAPER_EDITS.md` §PAPER-7a: one table row, one caption, ~20 minutes, zero
   judgement.** Do that first and nothing else is gating.
3. **Two contribution-framing decisions need a human, not an agent: PAPER-5 and PAPER-11.**
   T2B killed "we preserve what's correct and remove what's harmful" for *both* operators, which
   also dissolves the ERGO differentiation; the tau2 withdrawal removes the far end of the
   "spectrum of referentiality" narrative. Together they change what the paper claims to
   contribute, not just what it reports. **A third belongs with them (F96): the "appropriate
   intensity" thesis — lighter operators for stronger respondents, heavier for weaker — is
   *absent* from the re-measured tau2 matrix, not merely weakened.** Gated-Reset is best or
   tied-best on all three respondents, which points the other way. It appears in three places
   (L358, L372, L405) and is a **claim change, not a number change**; `PAPER_EDITS.md` PAPER-11
   J2 lays out the options and recommends against replacing it with the new tau2 ordering, which
   would swap a withdrawn pattern for an underpowered one.

---

## 2. Claims that must change before anything is submitted

Ordered by severity. "Fixed in v5" means the reply set already carries the corrected wording; it
does **not** mean the paper does. Rows 1–20 keep their original numbers so cross-references from
earlier handoff versions still resolve; **row 0** and rows 21–22 are new since the T26 version.

| # | We claimed | What is true | Finding | Artifact | Status |
|---|---|---|---|---|---|
| **0** | *(new — the largest single change to the submission)* **tau2-bench: "the best AC3 operator beats full context by double-digit margins on every respondent"** (abstract, Fig. 1, intro, §tau2-results, discussion, conclusion) | **Withdrawn.** T6 re-ran the full published matrix at N=3 — 3 models × 5 arms × 3 replicates × 19 tasks = **855 scored rollouts** (899 run), 15/15 cells, same hyperparameters and model identities as the committed sweep scripts. **Two of three published baselines do not replicate: DSV4F 31.6 → 70.2 ± 11.0, Kimi 26.3 → 78.9 ± 0.0.** On **all three models the remeasured Baseline is at or above every AC3 arm**; AC3-Augment is significantly *worse* than baseline on all three (−21.1 p=.008 / −19.3 p=.043 / −21.1 p=.012). **What survives: AO → 0.0 across all 9 cells / 171 rollouts, structural and exact.** Also surviving: the gpt-5.4 Gated-Reset regression (57.9 ± 21.1 vs 68.4, paired −10.5 pp, p=0.24) — reproduces in direction, kept, not upgraded | **F78–F81, D21** | `tasks/T6/worklog.md` (Tables 1–2, §"the finding the rebuttal has to deal with"); traces at `~/ac3/tau2_ctxe/ctx_edit/outputs/T6_reps/` | **Withdrawn throughout v5 by T28.** **Paper: PAPER-11 — not applied, and it is the highest-stakes item on that list** |
| 0a | *(scope of #0)* "these are not comparable measurements across model eras" | **No — this was tested, and the answer is "the published baselines were wrong".** The positive control **reproduced**: gpt-5.4 Baseline 68.4 vs published 68.4, AO 0.0 across 9 cells vs published 0/0/0. `gpt-5-mini` *was* reachable (dl-openai-1 + dl-openai-3), invocation strings byte-identical, **no model substitution anywhere**. Supporting: the AC3 arms on DSV4F/Kimi replicate well, T6's baseline runs terminate 60/60 and 59/60 `user_stop` with zero short-exits, and **our own source report already concedes Kimi's baseline was rate-limit-clipped** — 14/20 short exits, described there as "floors, not honest performance". The paper's `tab:megatable` caption already says this too. **Do not soften the withdrawal into "mixed results" or "not comparable"** | **F79** | `tasks/T6/worklog.md` §"Did the positive control reproduce?"; paper `tab:megatable` caption | Codified as a rule in `replies/v5/README.md` Blocker 2 |
| 0b | *(open problem inside #0, disclosed not explained)* — | **gpt-5.4's AC3 collapse is unexplained.** Augment 84.2 → 47.4, Rewrite 73.7 → 47.4, while that model's *baseline* reproduced exactly. T6 ruled out model substitution, gating, degenerate termination and rate limits. It found a **real fork bug** — `ctx_edit/analyzer.py:89-95` `_extract_tag` regexes only for `<task_spec>`, and **459 of 862 analyzer Q1 calls (53%) hit the raw-completion fallback**, splicing escaped JSON into the agent briefing — but the gated fix moved accuracy **42.1 → 44.4 (+2.3 pp)**, not the ~37 pp needed. **Disclose it as an open problem; do not paper over it.** The parser should be fixed upstream regardless | **F80** | `tasks/T6/worklog.md` §"Bug found in the fork"; diagnostic at `~/ac3/tau2_ctxe/ctx_edit/outputs/T6_diag/gpt5_4_s1_fixparse/` | Disclosed in v5. Fork fix is behind `T6_FIX_TAG_PARSE=1`, **not merged** |
| 1 | ERGO scored comparably to every other row in `tab:main` | **ERGO alone used the unfiltered pools** (23/25/25/25 vs everyone else's 20/19/25/23). Corrected: math **69.6 → 80.0**, code **≈44.0** (unchanged), database 12.0, actions unclosable **[43.5, 52.2]**. Corrected ERGO/math **beats AC3-Reset (75.0) and ties Gated-Reset (80.0)**. Measured scorecard: ERGO wins-or-ties **3/12**, not the published 1/12 | F42, F43, F44, F48 | `tasks/T17/RESULTS.md`, `tasks/T17/corrected_tabmain.json`, `tasks/T18/worklog.md` | Disclosed in v5 (5 places). **Paper: PAPER-7, not applied — the posting blocker** |
| 2 | Per-run `adjusted_accuracy` is a valid metric | The FN judge reads **visible** messages only, so reset arms get 50–78% of failures excluded vs 9% for baseline. Inflates reset arms **+13.9 to +55.9 pp**, no-reset arms +0.2 to +6.5. Shipped example: AC3-Reset database **89.0% published vs 77.1% corrected**. Judge sees 1.00 user turns/sample on Rewrite vs 5.35 on baseline | F28, F40, F41 | `tasks/T14/{RESULTS.md,corrected_matrix.*}` | v5 is raw throughout. **Paper: PAPER-6** |
| 2b | (scope of #2) `tab:main`'s 20/19/25/23 denominators are suspect | **They are not.** They come from an arm-symmetric **pool-level pre-filter** (`data/baseline_traces_v2/*_false_negatives.json`) that reproduces them exactly. **Defend this, do not concede it.** Only the *per-run* metric is invalid | F42, D13 | same | v5 defends it explicitly |
| 3 | Rebuttal end-to-end: **AC3-Reset 100.0 ± 0.0** | That table was itself FN-adjusted with **asymmetric exclusions** (Reset 1/2/5 items excluded, Baseline 0). Raw: Baseline **87.5 ± 2.0**, Reset **93.3 ± 4.2**, Gated-Reset **95.0 ± 0.0**. Claim survives — both operators win in all three runs — the perfect score does not. It appeared in **five files**. **Now also carries clustered CIs** (F77/M3): Reset +5.8 pp [+0.0, +12.5], p=0.119; Gated-Reset +7.5 pp [+1.7, +15.0], **p=0.023** — reads honestly in both directions | F34, F77 | `neurips_review/experiments/exp1_reps_results.txt`, `tasks/T27/m3_bootstrap.py` | Fixed in v5 |
| 4 | CollabLLM MATH-Hard **100%** | Does not replicate. N=3: AC3-Augment **91.7 ± 7.6** vs Baseline **91.7 ± 5.8** — identical means *and* identical 55/60 per-problem totals; per-replicate delta [+5, −10, +5] = **0.0 ± 8.7**. Say **"matches Baseline"**, which still refutes 5YHP's regression claim | F16 | `tasks/T8/worklog.md` | Fixed in v5. **Paper: PAPER-4** |
| 5 | "We preserve what's correct and remove what's harmful" | **Not supported for *either* operator — retract, do not re-attribute.** T2A (constructed spans) put Reset's edit precision at **50.4%** against 50% chance with **4.0%** preservation, and Rewrite looked like the selective exception (27.0 / 38.9), which is why F25 said "attribute, don't retract". **T2B overturns that on *natural* spans, causally, with no detector or judge in the label path:** Reset keeps **5/66** probe-admissible spans, **Rewrite keeps 0/66**, preservation on causally useful spans is **0% for both**, edit precision is **63.6% = the base rate for both**, and the label-free aggregate test agrees (Reset removed−kept −0.014, p=0.85). **The mechanism for both operators is *detect → discard the assistant side → rebuild the specification from the user side*.** **Consequence nobody had named: this breaks the ERGO differentiation** — "unlike prior work that discards all assistant messages" was how the paper distinguished itself, and T2B says we largely *do* discard them | F25, **superseded by F66** | `tasks/T2B/RESULTS.md` §4, `tasks/T2B/per_span_alignment.json`; earlier `tasks/T2A/RESULTS.md`, `outputs/T2A/` | **Retracted in v5** (`replies/v5/CHANGES.md` §11.1). **Paper: PAPER-5** (framing is also in `CLAUDE.md`/project overview) |
| 6 | Bare **97.6%** pollution-removal rate | True but unquotable alone — a delete-everything editor scores 1.000 on it, as our own PC3/PC4 controls show. Always report the quartet: detection (**78.6%** pollutant naming, 89.7% on the causally-harmful subset), removal 97.6%, preservation 4.0%, edit precision 50.4% vs chance 50 | F23, F26, D9 | `tasks/T2A/{RESULTS.md,measure.py}` | Fixed in v5 |
| 7 | "N=3 **seeds**" on LiC and CollabLLM | `cfg.seed` was read only by `huang_eval/`; every `seed=$((42+rep))` was **inert**, and the CollabLLM loaders hardcode `random.Random(42)` so all replicates drew the *same 20 problems*. Replicates varied through **temperature-1.0 sampling only**. Say "3 replicate runs at temperature 1.0". **WildChat's N=3 are real seeds and keep the word. So does tau2** — `--seed` genuinely threads on that fork (`run_parallel:131` → `orchestrator:526-528` → `llm_config.py:41-48` → litellm), best-effort at the provider, so ship "N=3 replicate runs (seeds 42/43/44)" (F81) | F4, F19, **F81** | `tasks/RECON/worklog.md`, `tasks/T8/worklog.md`, `tasks/T6/worklog.md` §13:56 | Fixed in v5. **Paper: PAPER-1** |
| 8 | Memory gains **+10 pp math / +12 pp database** | Single trials against a **~6 pp learner noise floor** — under 2σ. Variance controls: across-ordering sd **6.5** does not exceed same-ordering sd **6.1**, so ordering is not a distinguished factor; the learner is just noisy. An N=4 remeasure on gpt-5.4-mini gives **−5.0 / −8.0 pp** (different model, so not a direct refutation — but the variance argument is model-independent) | F12, D7 | `tasks/T12-T13/worklog.md` §9, `outputs/T12_T13/` | Dropped from v5. **Paper: PAPER-3** |
| 9 | WildChat headline **89.8 / 92.1** | Order-balanced re-judge: **87.8 ± 2.1** (Reset) / **91.2 ± 2.1** (Augment). The headline judge prefers the second-presented response (32 vs 8 of 44 discordant pairs, binomial **p = 1.8e-4**), but `pairwise_judge.py` already randomises A/B 50/50, so the published number is unbiased *in expectation* — report the corrected values anyway, it is a cheap concession | F30, F31 | `tasks/T11/{worklog.md,out/}` | Fixed in v5 |
| 10 | AC3-Reset beats assistant omission on BigCodeBench (+6.7 pp) | AO column at N=3 is **18.3 ± 5.8**, narrowing the margin to **+3.3 pp** — two problem-instances in sixty, inside the noise, and the two arms succeed on partly different problems. **Do not claim this ordering.** Lead instead with AC3-Reset over **full context**: +15 pp in 3 of 3 replicates | F57 | `tasks/T21/worklog.md`, `outputs/T21/` | Fixed in v5 |
| 11 | Table 3 caption: gpt-5.4 comparison "on the same prefixes" | **False.** Reset scored on 44 turns, Gated-Reset on 58, only **35 shared**. On the matched 35 the gap survives (+14.3 pp) but rests on **7 discordant turns, 6 vs 1, exact McNemar p = 0.125** | F55 | `tasks/T20/worklog.md` §U2 | Claim struck from v5. **Paper: PAPER-8** |
| 12 | Gate-open rates 97.3% / 98.3% are *turn*-level detection rates | Numbers reproduce **exactly**, but they are per-**conversation**, and turn-level CollabLLM is **95.3%** (628/659). Also a **firing** rate, not a detection rate: 29% (LiC) / 73% (CollabLLM) of gate-open records carry `issues: "None"` while setting `needs_edit=true` | F39 | `tasks/T16/{gate_stats.py,report.md}` | Fixed in v5 |
| 13 | Two things we conceded that were false | (a) "BigCodeBench cannot be evaluated with executable tests" — it can; that path runs real `untrusted_check` execution. (b) Two documentation artifacts the paper cites do not exist: `docs/paper_experiments_provenance.md` names absent configs, and `docs/multi_run_variance_2026-05-07.md` — cited **twice** as the source of the appendix variance table — has never existed | F36, F8 | `tasks/T8/worklog.md` §5; `tasks/RECON/worklog.md` | (a) struck from v5. (b) **Paper: PAPER-2** |
| 14 | Judging was deterministic (temperature 0) | The client logs `gpt-5 models require temperature=1.0, overriding 0.0 -> 1.0`. Substitute the honest figure: **96.9% self-consistency, κ 0.810** | F33 | `tasks/T11/worklog.md` | Fixed in v5 |
| 15 | Three full-context baselines for the same benchmark, **52 points apart**, with nothing in the rebuttal explaining it: paper 4.0 / 15.8, `01` W1 19.0–22.4, `00` CW5 (T1) 56.1 / 83.0 | **All three are correct measurements of deliberately different populations; the dominant term is pool difficulty selection**, not model era, evaluator or metric. Verified two independent ways agreeing within 2 pp: restricting T1's *own* run to the paper's exact 25 items gives 56.1 → **32.0** (database), 83.0 → **48.0** (code); LiC's released logs put GPT-5-mini at **29.9%** on the full 107-item pool vs 4.0% on its top-25. The paper's 4.0% = 1/25 **is what the construction guarantees**, not an independent measurement | F59 (red team H1), **F68** | `tasks/T24/worklog.md` §7 | Fixed in v5 (`00` CW5, `01`, `02`, `04`, `05`). **Paper: PAPER-9** |
| 16 | `01_reviewer_iNYK.md:31` — the 36-comparison matrix is on "the full, non-difficulty-selected pool" | **False.** It runs on difficulty-selected pools, which is **iNYK's exact complaint**, asserted about our own new headline evidence. If a reviewer checks one claim in the rebuttal, this is the one they check. The fix is a swap, not a retraction: **T1** is the experiment that genuinely satisfies the claim (complete unselected pool, end-to-end) | **F70** | `tasks/T24/worklog.md` §7 | Fixed in v5 (`01` W2 + `00` CW2) |
| 17 | CW1: "the same four operators", above a table printing **three** | `paired_analysis_results.txt` holds a fifth row we did not print: **AC3-Rewrite −0.3 pp, 6 W / 6 L**. Rewrite is precisely the operator 5YHP's W4 was about. Printing three of four while claiming four colours a reviewer's reading of everything else. **M15 makes that row better, not worse**: at item level it is **+0.0 pp, 42 W / 42 L, CI [−3.8, +3.8]** — "neutral on LiC, bounded within ±4 pp" | **F60** (H2), F77 | `neurips_review/experiments/paired_analysis_results.txt`, `tasks/T27/m15_results.txt` | Fixed in v5 |
| 18 | "AC3 beats assistant omission in every WildChat cell (22 populated cells)" | Two arithmetic errors in one sentence: **9 of the 22 are against full context**, and 4×4 ≠ 22. Inherited from T20's suggested wording — a *verified number* arrived inside a *wrong sentence* | **F63** (H7) | `tasks/T23/RED_TEAM.md` H7 | Fixed in v5 |
| 19 | AC3-Reset separates from assistant omission generally | **Matrix-wide head-to-head is a wash.** Cell level: **+2.6 pp, 15 W / 17 L / 4 T**. Item level, independently derived: **+2.8 pp, clustered 95% CI [−0.3, +5.9]** — includes zero. The separation is **concentrated**: database **+18.7 pp cell-level / +18.6 pp item-level, CI [+10.7, +26.6]**; tau2 AO 0% structural; WildChat every populated cell. **Guardrail: never quote the matrix-wide item-level McNemar p = 0.010 as a win** — it treats 1,668 items as independent when they are 191 problems × up to 9 correlated replicates. Had it been quoted, two sections of `00` would have contradicted each other (F82) | **F64, F71, F77, F82** | `tasks/T23/RED_TEAM.md` (final section), `tasks/T25/worklog.md` §2, `tasks/T27/m15_results.txt` | Fixed in v5; guardrail codified in `CHANGES.md` §8 rule 6b and `README.md` |
| 20 | Vg97 asked for AC3's latency; we reported the **summariser's** | AC3's own wall-clock, recovered at **zero API cost** from `outputs/T1/main/*/experiment.log`: full context 578 s, Gated-Reset 781 s (**+35%**), Reset 1,051 s (**+82%**), summariser-2 1,214 s (+110%). Decomposed, most of the gap is **turn inflation** (6.9 vs 4.1 turns): **per turn** Reset is **+9%**, Gated-Reset +5%, summariser-2 +19%. Report both halves | **F72** (H10) | `tasks/T25/worklog.md` §H10, `outputs/T1/main/*/experiment.log` | Fixed in v5 |
| **21** | *(new)* Our own defence that "MT-OSC barely fires, so the comparison is unfair to us, not to them" | **Retire it — we no longer need it, and it is now the weaker argument.** Scaling the window down so MT-OSC *does* engage makes it **worse**: w=2 scores **47.7%, −13.1 pp vs w=4's 60.7%** (p=0.016), with the engagement fix verified live (`raw_pairs_carried` 133 vs the buggy run's 0). It engages **9× more** and loses by more. AC3-Reset is **+28.0 pp** over it. Lead with the measured result, keep "structurally cannot engage" as the mechanism behind it | **F76** | `tasks/T27/worklog.md` §7.2, `outputs/T27/` | Fixed in v5 (`00` CW5 table + paragraph, `02` Q1, `04`, `05`) |
| **22** | *(new)* Two fixes **the red team itself proposed** are false and must never be posted | (a) M3's *"the analyzer cache was disabled for these runs"* — **false**; `context_edit_v2_gated.yaml:18` sets `analysis_cache_dir` and `run_exp1_reps.sh` never overrides it. The **true** answer is stronger and measured: **39/39 conversations have differing analyzer outputs across the three replicates**, the two failing problems are a different pair each run (**intersection 0**), turn counts differ on 7/40 and answers on 5/40. (b) M11's *"it degrades with more budget (−2.8 → −8.4 pp), which is itself the mechanism prediction"* — the 1-call arm **replicates at 47.7%, exactly the 2-call value**, and the two 1-call runs differ by *more* than 1-call differs from 2-call. Print "neutral-to-negative", never a mechanism | **F74, D20** | `tasks/T27/worklog.md` §3.1, §7.1; annotated in place as `⚠ SUPERSEDED — DO NOT APPLY` at `tasks/T23/RED_TEAM.md:451` and `:556` | Neither is written anywhere in v5 |

**One live pattern, not a single claim (F61, H4):** 5YHP asked about Rewrite and was answered
with Augment; iNYK asked about Gated-Reset's 38.7% and was answered with Reset. Individually
each substitution is defensible; named as a *pattern* it reads as a per-cell oracle and
discounts every headline in the paper. Applied in v5, but keep it in mind when drafting
anything new.

---

## 3. New results that strengthen the rebuttal

### T27 / M11 — the Area Chair's baseline reservation, closed (F75, F76, F77, F74)

**This is the best news of the second half of the session.** The AC's central reservation was
that AC3's advantage over condensation might be an artifact of a condenser prompt *we* wrote,
and v5 previously had to concede that the one control for it "did not finish in the window."
It has now finished:

| Arm (LiC-database, complete 107-item pool) | Accuracy |
|---|---|
| Full context | 56.1% |
| Our condenser prompt, replicate 1 / replicate 2 | 53.3 / 47.7 |
| **Neutral condenser prompt (the control)** | **51.4%** |
| AC3-Gated-Reset | 73.8 (**+22.4** vs neutral) |
| AC3-Reset | 75.7 (**+24.3** vs neutral) |
| MT-OSC, w=2 (engagement-fixed) | 47.7 (**−13.1** vs w=4's 60.7, p=0.016) |

The neutral prompt lands **between our own prompt's two replicates** — so the condensation
result does not depend on our wording. **The load-bearing detail is not the 51.4%:** with the
"find errors" clause removed, the condenser **flags an assistant error 0 times in 340
summaries**, identical to with it (probe validated: 26.4% on AC3 analyzer output, 0% on baseline
turns). *A summariser does not audit, whatever you instruct it to do.* That sentence is what
carries the item.

**M15 upgrades the headline statistic**, on 1,668 paired items across 191 problem clusters,
recovered from the snapshot at **$0**: AC3-Reset **+15.4 pp, 95% CI [+11.5, +19.4]**, 350 W /
93 L; Augment +14.6 [+10.8, +18.6]; Gated-Reset +16.8 [+11.6, +22.0]; AO +12.6 [+9.2, +16.1];
Rewrite **+0.0 [−3.8, +3.8]**. Both positive controls reproduce exactly (168/168 cells, and all
five printed rows to the digit). Cost of the whole task **$19.60**, $4.60 over guidance, spent
on the decisive item; two of the five triaged items were **declined with reasons** (human
validation, U-Fold on tau2) and those declines are as defensible as the runs.
Artifacts: `tasks/T27/{worklog.md,m15_results.txt,m15_itemlevel.py,m3_bootstrap.py,run_results.txt}`,
`outputs/T27/`.

### T6 — tau2 at N=3 (see §2 row 0 for the withdrawal)

Listed here too because **one tau2 result is new evidence and should still be posted**:
**AO = 0.0% on every model, every replicate, 9 cells / 171 rollouts**, reproducing the published
0/0/0 exactly, via the confirmed `max_steps` termination path — rollouts exhaust the step budget
in infinite re-lookup loops because stripping assistant messages erases every diagnostic result
the agent fetched. This is structural, does not depend on the baseline's level, and survives the
withdrawal intact. It is also the only quantitative evidence in the paper that blanket omission
fails when state lives in assistant turns, so the tau2 *section* stands even though the
comparison does not. Artifact: `tasks/T6/worklog.md`; fork at `~/ac3/tau2_ctxe`.

### T2B — causal span ablation, the gold standard (F65, F66, F67)

**111 naturally occurring spans** across 30 LiC database+code conversations, each re-run
**14× present / 12× removed** at temperature 1.0 — 3,357 assistant turns, 0 errors, **no
detector, judge or LLM anywhere in the label-generation path**, which is what makes it immune
to the circularity objection. Cost $62.80, the most expensive task of the session and the only
one where that was warranted. Two results, one for us and one against:

| Question | Answer |
|---|---|
| Is natural pollution real? | **Yes, and concentrated.** Effect SD **0.155** vs a replicate-matched parametric null's **0.125** (2,000 sims, **p = 0.0085**); **16** large-effect spans (\|Δ\| ≥ 0.25) where the null predicts **9.3** (**p = 0.017**). Mean effect **+0.020** [−0.010, +0.048] — **the typical span is inert**; the phenomenon lives in a ~6% excess minority |
| Are the operators selective? | **No — neither of them.** Reset keeps **5/66** probe-admissible spans, Rewrite keeps **0/66**. Removal on causally harmful spans **100% (7/7, both)**; preservation on causally useful spans **0% (0/4, both)**; edit precision **63.6% = the base rate for both**. Label-free aggregate agrees (Reset removed−kept −0.014, p=0.85) |

**Controls pass in both directions**, tying T2A and T2B onto one scale: contentless span
**+0.033** (n.s.), T2A's causally-validated pollutant **+0.368** (p=1e-4), full-spec + gold-SQL
span **−0.447** (p<1e-4). Probe controls identity 1.000 / nuke 0.000 / other 0.000. MDE 0.333.
Same-corpus raw accuracy: Baseline 39.3%, Reset 51.9%, Rewrite 53.1%.

**The reconciliation is load-bearing and ships in the reviewer text:** T2A flagged synthetic
salience as an upper-bound caveat in its own first paragraph, and the caveat turned out to be
exactly right. So T2B **extends** T2A rather than contradicting it — which is what stops a
reviewer reading two studies as two inconsistent results. T2B also states **eight** limits
itself. Artifacts: `tasks/T2B/{RESULTS.md,worklog.md,per_span.json,per_span_alignment.json}`
(`289de75`), `outputs/T2B/`.

### T24 — the 52-point baseline spread, fully explained (F68, F69, F70)

The red team's worst item (H1). All three baselines are correct measurements of different
populations:

| Source | Value | Population |
|---|---|---|
| paper | 4.0 / 15.8 | GPT-5-mini, last-turn replay, `dev_{task}_subset` — **top-25 items by GPT-5-mini baseline failure rate** (≥60% error over 5 runs; database 75 eligible → 25 kept). **4.0% = 1/25 is what the construction guarantees.** *(Per-task correction, F94: the top-25 cut binds on database, code and actions but **not on math**, which had only 23 eligible instances and kept all of them; and **code had only four usable baseline runs**, not five. Do not restate this row as a uniform "top 25 across five runs" — see PAPER-9.)* |
| `01` iNYK reply | 19.0–22.4 | three newer models, last-turn replay, `htn50_52`, with replay prefixes deliberately weighted toward baseline failures (74–86% on database). A floor by construction |
| T1 (`00` CW5) | 56.1 / 83.0 | gpt-5.4-mini, **full end-to-end** sharded simulation, the **complete unselected pool** (107 / 100) |

**T1 still answers the Area Chair with no re-scoping (F69).** On the unselected pool the
fully-specified single-turn ceiling is **94.4% database / 98.0% code** (positive control: LiC's
own `full` band for this pool is 89.7–98.1%). So T1's venue carries a **38.3 / 15.0 pp**
multi-turn gap and AC3 closes **51% / 60%** of it — the same fraction as on the paper's much
harder pool (**50%**). And condensation got no easy ride: it scores *below* full context in
every venue.

**The line to keep: *baselines move 52 points across venues; gap-closure moves 4.***
Artifact: `tasks/T24/worklog.md` (`78226bd`).

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
**+13.0 / +12.0 pp** (code), all p < 0.01. Better than parity: the budget-matched summariser
**over-consumed** AC3-Reset (**1.02–1.19× strategy calls, 1.62–2.14× strategy tokens**) and
still lost by 12–28 pp. Gated-Reset gets +17.8 pp on **0.41×** Reset's calls. **Do not read the
−2.8 → −8.4 ordering as a budget mechanism** — T27's replicate of the 1-call arm scores 47.7%
(§2 row 22b). MT-OSC at published w=4 fired **30 times across 107 conversations (0.3/conv)**;
T27 now supplies the measured w=2 counterpart (§2 row 21).
Artifacts: `tasks/T1/{RESULTS.md,worklog.md,analyze.py}`, `outputs/T1/`.

### T9 — analyzer-model sensitivity, the unanswered half of Vg97 Q3 (F21, F22)

Assistant pinned to DeepSeek-V4-Flash; only `model.ctx_editor.model` varies. n=178 matched
pairs, exact McNemar, LiC code+database replay (Baseline 21.3% pooled).

| Analyzer | Family | AC3-Reset | Δ vs Baseline | p |
|---|---|---|---|---|
| Kimi-K2.6 | Moonshot | 61.2 ± 2.4 | **+39.9** | 2e-17 |
| DeepSeek-V4-Flash (ref) | DeepSeek | 50.0 ± 2.4 | **+28.7** | 3e-09 |
| gpt-5.4-mini | OpenAI | 48.3 ± 1.6 | **+27.0** | 1e-08 |
| Llama-3.3-70B | Meta | 39.3 ± 0.0 | **+18.0** | 6e-06 |
| gpt-4o-mini | OpenAI | 34.3 ± 0.8 | **+12.9** | 8e-04 |

Graceful degradation, not collapse: every analyzer is individually significant, the weakest
still beats Baseline by 12.9 pp, and **no arm falls below Baseline on either task in either
replicate**. Weak analyzers **under-detect rather than mis-detect** (gpt-4o-mini fires on 74.4%
of turns vs ~97%, 2.7× shorter issue lists, `user_intent` parsed on 100% of calls). Three of
five analyzers are non-OpenAI, the **best is Kimi-K2.6** and the *weakest* is an OpenAI model,
which kills the "gpt-specific" reading. Defend the shape and the endpoints, not the exact
ordering. Artifacts: `tasks/T9/worklog.md` (`1f4f32d`), `outputs/T9/`.

### T2A + T2c — the detector story (F10, F23, F24, F25)

**T2A (constructed pollution, no judge anywhere).** n=126 admissible. Removal **97.6%**
[93.2, 99.2] · preservation **4.0%** · edit precision **50.4%** (chance = 50) · gate
sensitivity **98.4%** · **analyzer names the injected pollutant in `issues` 78.6%** of the time
(89.7% on the causally-harmful subset). That naming rate is the part not explainable by "it
deletes everything." Causality is built out of **Baseline** arms, not detector output: a
factorial over clean / harm-only / useful-only / both gives the harmful span **−11.1 pp** and
the true span **+15.1 pp**; on the causally-validated subset Baseline clean 24.7% → 9.3% with
the pollutant → **AC3 59.8% with the pollutant still present**. Four positive controls pass
exactly. **T2A's own stated caveat turned out to be load-bearing — see T2B.**

**T2c (auditing vs re-solving — 5YHP's mechanism challenge).** Zero re-runs. Strict leakage
base rate: math 38%, code **0%**, database 1%, actions 2%; overall 11% (n=547). **Paired gain on
the NO_LEAK subset (exact McNemar), n=329: 36.5% → 57.1% = +20.7 pp [+14.8, +25.3],
p < 0.0001.** Code alone **+30.2 pp with zero leaks**; database +26.0 pp with one. **Concede
math outright**: NO_LEAK n=77 gives **−2.6 pp [−11.9, +7.6]**.
Artifacts: `tasks/T2A/{RESULTS.md,inject.py,measure.py}`, `tasks/T2c/{RESULTS.md,worklog.md}`.

### T11 — WildChat judge checks (F30–F33)

1,824 judgements, 0 hard failures. Position bias is real (**p = 1.8e-4**) but the harness
already randomises A/B per call, so the published number is unbiased in expectation; corrected
headline **87.8 / 91.2** (§2 #9). Cross-family agreement: raw 85.9–88.8%, κ 0.445–0.507, and
because κ is depressed by the ~90% marginal the right statistics are **PABAK 0.79–0.83 and
Gwet's AC1 0.84–0.87**. Self-consistency **96.9% / κ 0.810**, cleanly attributing judge
instability to **order rather than sampling**. Per-judge order-balanced win rates 88.8 / 85.6 /
85.3; under a punitive "2-of-3 judges in both orders" rule, still **82.5%**. Positive controls
(intact vs degraded copy) 39/40, 36/40, 40/40. Artifacts: `tasks/T11/{worklog.md,out/}`.

### T13 — zero contamination (F13)

5YHP's contamination concern is **measurably unfounded**. Learn set vs the canonical
`lic_eval_subset`: **0/120 exact duplicates, 0 near-duplicates** (max Jaccard 0.416, boilerplate
only). A within-instance probe of the transductive protocol gives **0.0 pp on both tasks**. On
the 11/98 overlapping instances memory is equal or worse than no-memory. This is the half of the
memory story to lead with (D7). Artifact: `tasks/T12-T13/worklog.md` §9.

### T8 — BigCodeBench survives and is stronger than we claimed (F17)

| Arm | rep1 | rep2 | rep3 | mean ± sd |
|---|---|---|---|---|
| AC3-Reset | 5/20 | 5/20 | 3/20 | **21.7 ± 5.8** |
| Baseline | 2/20 | 2/20 | 0/20 | **6.7 ± 5.8** |

**+15 pp in every replicate — 3/3 wins, sd of the delta 0.0.** Reset solves 9
problem-instances Baseline never solves once and loses none. It **reproduces on a fully disjoint
20-problem draw** (0/20 overlap): Reset 3/20 vs Baseline 1/20. Quote as "≈1 in 5, ±1 problem"
with the scoring environment named, never a bare percentage. **The AO column is N=3 and narrows
the Reset-over-AO margin to +3.3 pp — see §2 #10 and #19.**
Artifacts: `tasks/T8/worklog.md`, `outputs/T8/`, `tasks/T21/worklog.md`.

---

## 4. The operator action list — PAPER-1..11

These all touch `writing/overleaf_repo/`, which is shared with Lianhui and Michel and synced to
Overleaf. They were deliberately **not** actioned autonomously. Pull before editing
(`git -C writing/overleaf_repo pull origin main`).

**Do not work from this table alone — work from [`PAPER_EDITS.md`](PAPER_EDITS.md)** (T31b), which
locates every item in the *current* `.tex`, quotes the text as it stands, and supplies the
replacement. Where the two disagree, `PAPER_EDITS.md` is right: it re-derived each item against the
file, and four of the rows below describe an edit whose target does not exist as described (F97).
The **effort column has been corrected** against it.

**Only PAPER-7 gates posting.** PAPER-11 is the largest and highest-stakes edit, but it is a
*withdrawal* — a reviewer reading "we withdraw this claim" needs no paper edit to verify it,
whereas PAPER-7 asserts corrected numbers a reviewer can check against a table that still prints
the old ones.

| ID | Do this | From | Effort | Blocking for the rebuttal? |
|---|---|---|---|---|
| **PAPER-7** | Fix ERGO's denominators in `tab:main`. Ship math **80.0**, code **≈44.0** (T18 measures **43.9** — print that), database 12.0; actions is **unclosable** — print as interval **[43.5, 52.2]** or drop, never as a point estimate. **Never ship T17's 57.9 for code** (it overstates a competitor by ~14 pp; T18 measured k = 2.67/6, not 0/6). Lead the passage with F49: **no ERGO-vs-AC3 `tab:main` difference is significant at n≈20 in either direction** (code p=0.375, math p=1.00). **⚠ Correction: the two body numbers this row used to bundle in — code gap-closure 78% → 82% and "closes 55–80%" → "67–82%" — are consequences of the *optional* comparability pass (7b), not of the ERGO fix. Do not make them if you apply only 7a** (`PAPER_EDITS.md` §7b). Paste-ready at `PAPER_EDITS.md` §PAPER-7a, with a merged caption that also carries PAPER-9 | F42–F44, F48, D14 | **7a ~20 min** (7b optional, ~1 h) | **YES — the only blocking item** (F58) |
| **PAPER-11** | *(new)* **Remove the tau2 improvement claim from the paper.** Places, in `neurips/neurips_2026_conference.tex`: abstract L110 ("only approach that improves over full context across the entire spectrum" + "substantially outperforms full context in agentic tool use — by double-digit margins per respondent"); Fig. 1 caption L122; intro L139; `tab:megatable` tau2 block + caption L280 (the caption's own rate-limit-clipped concession becomes the finding); L328; §`sec:tau2-results` L356–L360; discussion L369, L372; conclusion L405; limitations L808. **`PAPER_EDITS.md` has the full 25-location inventory, the paste-ready limitations paragraph, and three framing decisions (J1–J3) left open for you.** **Keep**: AO = 0% on every respondent (structural, reproduces exactly), and the honest replacement claim already drafted for the rebuttal — AC3 is *"the only method that remains **viable** in the stateful agentic setting, where blanket omission fails structurally."* Also fold in the unexplained gpt-5.4 collapse and the fork parser bug as stated limitations. **Three additions since T29: (a) Figure 1's *image* is false, not just its caption — see the blocker note below the table (F95); (b) the "appropriate intensity" ordering *inverts* (F96, §1 item 3) and is an authorial call, not a number swap; (c) `checklist.tex:98` carries a stale `Table~\ref{tab:main}d` cross-reference to a tau2 panel that no longer exists, plus best-of-3 reporting v5 replaces with mean ± std** | **F78–F81, D21**, F95–F97 | 3–5 h of text **plus a figure redraw of unknown cost**; touches abstract, figure, two sections and the conclusion | **No** — v5 posts the withdrawal in its own words. **But it is the highest-stakes item on this list and must land before any revision or arXiv push** |
| **PAPER-9** | `tab:main` caption must disclose that the LiC pool is **difficulty-selected**, and that the design-oracle rows use the same instances so the gap-closure percentages are pool-independent. Without this, the paper's 4.0% database baseline reads as a measurement when it is largely what the selection guarantees. **⚠ The caption this handoff previously endorsed is wrong twice (F94) — do not paste it.** It came from T24 §7.4 and said the instances are "the 25 per task with the highest full-context failure rate across five GPT-5-mini baseline runs". Against `docs/lic_dev_set_provenance.md`: **math is not a top-25 selection — it had only 23 eligible instances and all were kept** (`:50,54`), and **code used four usable baseline runs, not five** (one run's artifacts lost to a directory collision, `:32`). **Use the corrected caption in `PAPER_EDITS.md` §PAPER-9.** That item also carries two body sentences (L328, L139) that currently imply the default subset is *not* difficulty-selected | F68, **F94** | 10–15 min | Camera-ready — but **highest value per minute on the list**; it is the discrepancy a reviewer is most likely to catch unaided |
| **PAPER-6** | Report **raw** as primary; keep the arm-symmetric pool-level pre-filter as the only FN adjustment and **defend** it; rewrite `tex:478-480`, which says "all user simulator messages" when the code collates only the visible ones. **Correction: there is no metric to delete — the paper never names `adjusted_accuracy` anywhere**, so this reduces to the appendix rewrite, paste-ready at `PAPER_EDITS.md` §PAPER-6 | F28, F40–F42, D13 | **45 min** (not 2–3 h) | Camera-ready (v5 is already raw). **Do before arXiv** — it moves published magnitudes |
| **PAPER-5** | **Delete** "we preserve what's correct and remove what's harmful" from the abstract, intro and method — do **not** re-attribute it to AC3-Rewrite. Replace with the mechanism supported for **both** operators: *detect → discard the assistant side → rebuild the specification from the user side*. **Also rewrite the ERGO differentiation**: the difference is not "we are selective and they are not" — it is that AC3 rebuilds the specification from the user side while ERGO rewrites user turns. Defensible empirical claims that remain: the 78.6% pollutant-naming rate, the factorial (9.3% → 59.8% with the pollutant still present), and T2B's 100% removal of causally-harmful natural spans. Same edit in `CLAUDE.md` / project overview | F25, **F66** | 1–2 h | Camera-ready — a **contribution-framing** change, not a number change, so budget review time |
| **PAPER-1** | **Correction: the paper does not have this defect.** `seed` appears exactly twice in the `.tex` (L360, L558) and **both are tau2, which keeps the word** (F81); the LiC and CollabLLM passages already say "$N{=}3$ replay-mode reruns" at temperature 1.0. The F4 defect lived in the launcher scripts and the rebuttal drafts, not in the paper. What remains is **one limitations sentence** at L808 stating what the replicates actually vary — paste-ready at `PAPER_EDITS.md` §PAPER-1 | F4, F19, F81, **F97** | 10 min | Camera-ready, but cheap and an integrity item — do it early |
| **PAPER-8** | **Two locations, not one.** `PAPER_EDITS.md` §PAPER-8 has both paste-ready: **L300** (`tab:wildchat` caption — the line this handoff called `tex:299`) and a **second occurrence at L347** in §`sec:wildchat-results` ("Gated Reset on the same prefix set"), which T29 did not mention. Fixing one leaves caption and body disagreeing. Both become: 44 and 58 turns with 35 shared, $-$14.3pp on the matched 35, exact McNemar $p=0.125$. One hedge decision attached (the "we recommend always-on Reset" sentence now rests on p=0.125) | F55, **F97** | 10 min | Camera-ready only — the claim is struck from v5 |
| **PAPER-4** | **Correction: no target exists. Close as not-applicable.** The string `100` does not occur anywhere in the 815-line `.tex`; the 100% was a **v4 rebuttal** claim about AC3-Augment on MATH-Hard, never a paper claim, and it is already corrected in v5. Keep the finding for the day a MATH-Hard figure is added: say "matches Baseline" (91.7 vs 91.7) | F16, **F97** | 0 | Not applicable |
| **PAPER-3** | Table 1's `+ Memory` rows are single-trial below a ~6 pp noise floor. Either re-run at **N ≥ 4** or soften — softening is recommended and is paste-ready across **five** locations at `PAPER_EDITS.md` §PAPER-3 (re-running needs GPT-5-mini, which is unreachable from this environment). **Addition (F97): the LiC `+ Memory` protocol is *transductive* and the paper never says so.** L709 says only "On LiC, we use online learning"; operationally the cheatsheet applied to an instance is distilled from **other instances of the evaluation set itself, together with their gold answers** (`include_full_spec_q` / `ground_truth_a`). **This is a disclosure gap, not bookkeeping** — and it is free to close, because T13 measured that protocol's effect at **0.0 pp on both tasks** (n=15 database / 14 math). Ship the disclosure with the softening; it pre-empts a serious objection at no cost | F12, **F13, F97** | 20–30 min to soften + disclose; hours of compute to re-run | Camera-ready |
| **PAPER-10** | **Correction: no table is mislabelled today.** Every LiC strategy in `tab:main` runs in replay mode (L456), so the `$^{\diamond}$` design-oracle marker is not the defect F69 describes and there is **no mandatory edit**. What is left is an *optional* caption line that **strengthens** the paper: on T24's complete unselected database pool (n=107, end-to-end) AO reaches 69.2% and Concat-User 63.6% against a measured single-turn ceiling of 94.4%, with AC3-Reset at 75.7% **above both** — a cleaner replication of the "exceeds the design oracle" claim than `tab:main`'s 48.0 vs 32.0. Paste-ready at `PAPER_EDITS.md` §PAPER-10 | F69, **F97** | 10 min | Camera-ready; optional, and it is a gain not a concession |
| **PAPER-2** | **Correction: not a paper edit at all.** `grep -rn "multi_run_variance\|paper_experiments_provenance" writing/overleaf_repo/` returns **nothing** — no `.tex` cites the missing doc. The dangling references are in the **outer** repo: `docs/paper_experiments_provenance.md` (L41, 45, 138) and `docs/index.md` (L140, 250), the latter in violation of the CLAUDE.md rule that index entries resolve. The paper's variance table is separately attested: T17's PC5 reproduces the per-run values printed at L496–L499 to 0.1 pp. So this is a ~20-minute **outer-repo docs fix** that needs no pull/push through Overleaf — see `PAPER_EDITS.md` §PAPER-2 | F8, **F97** | 20 min (outer repo) | Camera-ready |

**Order if time is short — use T31b's, which supersedes T29's: PAPER-7a (20 min, blocking) →
PAPER-9 (15 min; the merged caption makes it one paste with 7a) → PAPER-4 + PAPER-2 (0 + 20 min,
both close without touching the paper) → PAPER-1 (10 min) → PAPER-8 (10 min) → PAPER-10 (10 min)
→ PAPER-3 (25 min) → PAPER-6 (45 min) → PAPER-5 + PAPER-11 in one sitting.** Items 1–7 total
roughly **1 h 30 m** and cover the blocker plus every mechanical item on the list. Do PAPER-5 and
PAPER-11 together: they share an abstract, and doing them apart means rewriting it twice.

**⚠ New camera-ready blocker, not on the table above (F95): Figure 1's *image* is false, not just
its caption — and it cannot be regenerated from source.** `assets/ctxe_story.drawio.png` draws the
"Ours" curve **strictly above** the flat "Vanilla" line across the whole x-axis **including the
tau2-bench band**, with an inset reading *"Fine-grained context management remains robust in more
complex, more referential interactions!"*. Under the withdrawal, at the tau2 end AC3 is at or below
vanilla on all three respondents (68.4 / 70.2 / 78.9 for Baseline). The teal curve must cross or
meet the orange line inside the tau2 band and the inset must change — **a redraw, not a caption
edit**. And **`find` over the whole tree returns no `.drawio` file**, only exported PNGs, so
whoever holds the draw.io document has to redraw it. **Budget this separately from PAPER-11's text
edits and start chasing the source file early**, since it is the one item whose cost is not ours to
control. The figure is labelled "Schematic of qualitative trends", which does give licence to
redraw the band rather than replace it with real data (`PAPER_EDITS.md` PAPER-11 J3).

**Not a paper item, but do it anyway:** patch `ctx_edit/analyzer.py:89-95` upstream in
`matt-seb-ho/tau2_ctxe`. Half the analyzer briefings in that fork are corrupt and nobody knew
(F80). Currently fixed only behind `T6_FIX_TAG_PARSE=1` in the local clone, unpushed.

---

## 5. Still open

### Posting blockers

`replies/v5/README.md` carries six numbered entries. **Five are now RESOLVED; one is
bookkeeping. The real blocker is PAPER-7, which is not in that list.**

| # | Blocker | State |
|---|---|---|
| — | **PAPER-7** — the paper edit v5 commits to in front of the reviewers | **OPEN. The hard blocker** (F58) |
| 1 | Resolve and delete every `⚠ INTERNAL` block | **Effectively closed.** `grep -rn "⚠ INTERNAL" replies/v5/*.md` now returns only **one block** — the orientation preamble at the top of `00_general_response.md` (it self-references, so the grep shows two lines from the same block). Delete it before posting. The five tau2 HOLDs and both T19 renumbering notes were resolved and removed by T28 |
| 2 | tau2 on HOLD pending T6 | **RESOLVED — and it goes against us.** Improvement claim withdrawn (§2 row 0, D21). Rule: no tau2 improvement claim on any model; do not soften into "mixed results"; keep AO = 0%; keep the gpt-5.4 Gated-Reset regression unupgraded; disclose the gpt-5.4 collapse as unexplained |
| 3 | T14 (FN-adjustment audit) | RESOLVED, largely in our favour. `tab:main`'s denominators are **defended, not conceded** |
| 4 | T17 + T18 (ERGO denominator defect) | RESOLVED and folded into v5 in five places — but see PAPER-7 |
| **5** | The "only method that improves over full context across the entire spectrum" sentence | **RESOLVED and REPLACED.** T6 made it false on the very benchmark it was sharpened to survive. The pre-drafted fallback is applied in `00` CW4, `01` W3, `04` correction 6 and `05`: "…the only method that remains **viable** in the stateful agentic setting, where blanket omission fails structurally (0% on every respondent)." **Do not reinstate the stronger wording anywhere** |
| 6 | H1 (52-point baseline spread) and F70 (false "non-difficulty-selected pool") | RESOLVED — T24 measured, T25 applied (§2 #15, #16) |

**HOLD integrity was verified four times**, most strongly by per-block SHA-256 from `d989c50`:
all **nine** regions byte-identical through the entire T27 pass (`tasks/T28/hold_baseline.txt`).
The deliberate phase-2 unsealing is recorded separately from phase 1, so the record distinguishes
"sealed and untouched" from "opened on instruction".

### Genuinely unresolved, in descending order of consequence

1. **The gpt-5.4 tau2 AC3 collapse (84.2 → 47.4) has no explanation** (F80, §2 row 0b). The
   baseline reproduced exactly; the one real bug found is worth +2.3 pp. This belongs in the
   camera-ready as an open problem, and it is the kind of thing a hostile reviewer will ask
   about once we disclose the tau2 withdrawal.
2. **Figure 1 cannot be corrected from anything in the repo** (F95, §4). The image contradicts the
   tau2 withdrawal on its face and **no `.drawio` source exists anywhere in the tree** — only
   exported PNGs. This is unresolved in the literal sense that the fix requires a file we do not
   have, so it is the one camera-ready blocker whose timeline is not ours. Ask Lianhui and Michel
   for the draw.io document before anything else on the figure.
3. **U4** ("1 of 11 baseline failures attributable to context pollution", the paper's
   `tab:tau2-failure-modes`) is **unverified and characterises a tau2 baseline that has now
   moved**. Its traces are gone. Standing recommendation unchanged: **soften now, defer
   re-derivation to camera-ready** (F56). Note it was never re-run — T6 targeted the multi-model
   sweep, not the paper-era gpt-5-mini tau2 cells.
4. **Red-team M1 — the self-correction count reads 3 / 5 / 7 / 10 (now 6 / 8 in places) across
   four files.** Each count is defensible in its own scope; making them agree is a tone judgement
   about how prominently the general response should carry the total. Left to you deliberately
   (`tasks/T28/worklog.md` §8).
5. **Declined and worth knowing about:** a human-validation study for the WildChat judge (5YHP's
   third named check — v5 now names the gap explicitly rather than faking a stand-in), and
   U-Fold on tau2 (the red team's own suggested remedy was to *offer* it to the reviewer, not to
   run an unvalidated overnight adaptation of someone else's method).

---

## 6. Where everything lives

| What | Where |
|---|---|
| **The rebuttal to post** | `neurips_review/replies/v5/` — `00_general_response.md` first, then `01`/`02`/`03`, then `04_response_to_AC.md`, then `05_final_remarks.md` at the end of the discussion period |
| **The paper edits to make** | `neurips_review/autoresearch/PAPER_EDITS.md` — the ready-to-apply spec for PAPER-1..11: exact current text from the live `.tex`, paste-ready replacements, finding ID per number. **Nine items paste-ready, two (PAPER-5, PAPER-11) judgement calls with options.** This is the entry point for §4, not §4 itself. Method and caveats in `tasks/T31/worklog.md` |
| **Claim-by-claim audit** | `neurips_review/replies/v5/CHANGES.md` — every v4 assertion, status, finding ID, artifact path, new wording. **§12 is T28's integration record** (T27 items, tau2 withdrawal, HOLD verification) |
| **Pre-posting checklist, blockers, guardrails, rhetoric plan** | `neurips_review/replies/v5/README.md` — read "Accuracy guardrails" before you touch any number |
| **The adversarial read** | `neurips_review/autoresearch/tasks/T23/RED_TEAM.md` — 30 items (10 HIGH, 15 MEDIUM, 5 LOW), each with quoted text, the attack, and drop-in revision wording. **Now annotated in place**: a D20 banner at the top, `⚠ SUPERSEDED — DO NOT APPLY` at M3 (`:451`) and M11 (`:556`), and `✅ RESOLVED` notes on M12/M15/M6. Its closing section is still the strongest single objection against us |
| **v4 (diff baseline, untouched)** | `neurips_review/replies/v4/` |
| **Full narrative record, F1–F83 / D1–D21** | `neurips_review/autoresearch/WORKLOG.md`. **All 21 decisions are now written up in prose**, not only in the JSONL — D15–D19 were backfilled at 19:55, D20 and D21 written in the same command that logged them |
| **What was run, in what order, and dead ends** | `neurips_review/autoresearch/PROVENANCE.md` — the "Dead ends and why" table at the bottom is the fastest way to see what we retired and why |
| **Per-task detail, scripts, verbatim prompts** | `neurips_review/autoresearch/tasks/<ID>/{worklog.md,RESULTS.md,*.py}` — 24 task dirs |
| **Machine logs** | `neurips_review/autoresearch/{logs/orchestrator.jsonl,logs/heartbeat.jsonl,state/}` — the JSONL carries the authoritative timestamps; `WORKLOG.md` is the human record |
| **Run outputs from tonight** | `outputs/{T1,T2A,T2B,T8,T9,T12_T13,T18,T21,T24,T27}/` |
| **tau2 results from T6** | `~/ac3/tau2_ctxe/ctx_edit/outputs/T6_reps/<model>_<arm>/traces/*.json` (per-rollout, with full message history and `analysis_log`); aggregators `t6_aggregate.py` / `t6_paired.py`; diagnostic at `outputs/T6_diag/`. **Local patches are uncommitted and unpushed** |
| **Recovered prior outputs** | `~/ac3/blob_staging/snapshot.tar.gz` (whole `outputs/` tree incl. CollabLLM competent-user-sim and all WildChat runs; the 168 per-sample `results.json` M15 needed live here); `~/ac3/recovered/`, `~/ac3/recovered_t2c/`, `~/ac3/recovered_t20/`, `~/ac3/t14_snapshot/` |
| **Spider DBs (newly recovered)** | `data/spider/databases/` — 4.9 GB, gitignored, 17/17 db_ids, **test-suite** execution semantics. Provenance belongs in the camera-ready if we report database numbers (F1) |
| **tau2 fork** | `~/ac3/tau2_ctxe` (deliberately outside the shared tree) |

---

## 7. Methodological lessons worth keeping

### Positive controls caught **twelve** harness or analysis faults tonight

Several would otherwise have become published numbers. **Two of the twelve were faults in
*analysis* code rather than in the harness** (items 5 and 10), which is the harder class to
catch because nothing crashes.

| # | Fault | Caught by | Finding |
|---|---|---|---|
| 1 | `unzip` leaving `__MACOSX/._*.sqlite` sidecars, which the eval's substring DB filter treats as real databases | DB-count sanity check | F2 |
| 2 | Under TRAPI the default FN-analysis model is not served, so FN analysis **silently no-ops** and deflates every accuracy number | Model-availability probe | F2 |
| 3 | `bigcodebench` package absent → cells report `0/0` | Known-value re-score | F18 |
| 4 | Package present but **matplotlib** missing → `reliability_guard` dies in-sandbox and the pass rate is swallowed as `0.0`. **A real 5/20 cell read 0/20 this way** | Re-scoring a known-4/20 cell and getting 0 | F18 |
| 5 | *(analysis)* Word-boundary vs substring matching (`Museum_ID` ⊂ `Museum_IDs`) in the measurement probe, silently overstating removal | Control PC2 | F26 |
| 6 | An MT-OSC schedule dropping raw pairs completed after the condensation window, manufacturing a 30 pp low score — **do not quote its 26.2%** | Treating an anomalous number as a suspected fault | F29 |
| 7 | A duplicated background chain double-writing output dirs | Contradiction between `metrics.json` and `run_summary.json` | F14 |
| 8 | T18's positive control **failing** to reproduce ERGO/database (44.0 vs published 12.0) because the published-era model is unreachable — which is exactly what stopped a plausible-looking set of numbers being written into `tab:main` | The control itself | F46 |
| 9 | The AO BigCodeBench cell never re-scored under the unified dependency environment while every other cell in its row was | Auditing the auditor | F54 |
| 10 | *(analysis)* T2B's first empirical null came from the filler control at **mismatched replicate counts**, producing a **false negative**; replaced with a matched parametric null | The agent re-deriving its own null | F67 |
| 11 | The tau2 fork's tag-parse defect — **459 of 862 (53%)** analyzer Q1 calls splice escaped JSON into the briefing; degrades AC3 arms only, cannot touch Baseline or AO | Gated diagnostic; worth +2.3 pp, so **not** the explanation for the gpt-5.4 collapse | F80 |
| 12 | Harness error rows recorded as `num_turns == 0` with `is_correct: false` and **no `error` field** — a failed conversation is indistinguishable from a wrong answer. Scoring them as failures would have silently penalised whichever arm errored more (Kimi/math/conv0 prints 34/39 against 48 rows on disk) | M15's PC-1: only 165/168 cells reproduced their printed value; dropping `num_turns == 0` takes it to **168/168 exact** | F77 |

**A thirteenth catch of a different kind, worth its own line (F82):** T28 checked the new
item-level AO statistics against the CW2 subsection T25 had already written. Both agree
(+2.8 vs +2.6 pp cell-level; +18.6 vs +18.7 pp on database) — **but had it quoted the
anti-conservative McNemar p = 0.010, the two sections of the same document would have
contradicted each other**, one saying "wash" and the other "significant". Cross-file consistency
is a control too, and it is the one nothing else in the pipeline performs.

### Adding replicates dissolved an asserted margin **five** separate times

CollabLLM math-hard 100% (F16), the memory gains (F12), the ERGO ordering (F49),
AC3-Reset-over-AO on BigCodeBench (F57), and the summarisation "degrades with more budget"
ordering (F74). The pattern is consistent enough to state in the paper as a positive claim about
what the evaluation can and cannot support (D16):

> At n≈20 per cell, this benchmark family cannot resolve differences below roughly 10 pp.

Several of our narrower claims were reading noise. This is also the most defensible frame for
the ERGO comparison: not "who wins", but "n≈20 cannot resolve this." **The tau2 withdrawal is
the same lesson at benchmark scale** — a whole comparison rested on N=1 cells whose controls
were degraded, and nobody had re-measured them.

### Factual audit and adversarial read are complementary — run both (D17, D18)

Three accuracy audits (T15, T19, T20/T21) asked *"is what we wrote true?"* One red-team pass
asked *"what does a hostile reviewer do with it?"* and found in a single pass what all three
missed, including the 52-point baseline spread (F59) and the false "non-difficulty-selected
pool" statement (F70) — which sits in the reply to the very reviewer whose objection it
misdescribes. Note the mechanism: **both** the H7 arithmetic error and the 22-cell error were
*inherited from a prior verification step*. **A verified number can arrive inside a wrong
sentence.**

### Adversarial output is itself a hypothesis list, not a patch set (D20)

**Two of `RED_TEAM.md`'s own suggested fixes were measured and found false** (§2 row 22), and
both would have handed a reviewer a checkable false statement in the exact paragraph meant to
rebut a suspicion. The red team wrote its wording under time pressure without running anything:
its *attacks* were excellent, its *proposed replacements* need the same verification as any
other claim. Both are now annotated in place so a future reader cannot apply them by accident.

### The strongest recurring pattern of the session: **proposed wording gets inherited, not verified**

Four instances, and they are the same failure every time. The red team's **two suggested fixes**
were measured and found false (F74/D20). **Two numbers originating in orchestrator briefs** — the
"+21 pp over AO" that T25 recomputed as +18.7, and the "83 audited claims" that turned out never to
have been printed anywhere (D19, F92). And now **a drafted `tab:main` caption that this document
endorsed**, carried from T24 §7.4 through two consolidation passes without anyone re-deriving it,
of which two facts were wrong (F94). **Findings were re-derived reliably all night; *replacement
text* was not** — the moment a claim becomes a proposed sentence, it stops being audited and starts
being copied. Carry it into future sessions as a standing rule: **a suggested fix is a hypothesis
with the same evidential burden as the claim it replaces**, and briefs should cite finding IDs so
the receiving agent re-derives rather than inherits. Every one of the four was caught by the *next*
agent downstream, never by the pass that wrote it.

### Three smaller rules earned tonight

- **Never strike a claim for unverifiability without a documented deep search** across the repo,
  `scripts/`, `docs/`, `outputs/`, `runs.yaml`, both tarballs and the recovered trees. Twice
  tonight "no artifact exists" meant "the audit did not look hard enough" (D15, F39, F53).
- **Report a validated sub-metric rather than an unvalidated headline.** T2c's 3-way leak
  classifier scored only 10/24 on a held-out draw, so it reported the quantity it could
  validate — **precision of the NO_LEAK label, 29/32** — and built the primary numbers on a
  stricter model-free detector instead (F10).
- **Declining an experiment with a stated cost and reason is a result.** T27 declined two of five
  triaged items and spent the money on the one that closed the AC's reservation; T6 refused to
  substitute a reachable model for an unreachable one and thereby kept "the published baselines
  were wrong" separable from "these are not comparable".

### And one aimed at whoever writes the next brief (D19)

The orchestrator's brief to T25 said "+21 pp over AO on database", carried forward from an
earlier summary without re-derivation. **T25 recomputed it as +18.7 pp and printed the measured
value** rather than the instructed one — and T27's independent item-level pass later returned
+18.6 pp, confirming the agent and not the brief. Briefs must cite finding IDs so the agent can
re-derive rather than trust. An agent that verifies its orchestrator is behaving correctly.
