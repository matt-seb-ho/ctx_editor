# T20 — Verify or retire the remaining unverifiable claims (§7 U2–U5)

**Started:** 2026-07-29 ~17:20 UTC. **Status: COMPLETE.**
**API calls made: 0.** Everything below is recomputation from recovered artifacts.

Scope: `neurips_review/replies/v5/CHANGES.md` §7, entries **U2, U3, U4, U5** (U1 was
retired by T16; U6 is T17/T18's and is explicitly out of scope).

**Headline:** the T16 base rate held. **U2, U3 and U5 are all VERIFIED — every number
reproduces to the digit from artifacts that exist.** Only **U4** is genuinely
unrecoverable, and it is unrecoverable in a specific way: the *number* is traceable to a
dated, committed lab notebook, but the *evidence* behind it (the 20 traces and the
per-failure labels) no longer exists anywhere and never existed as a file.

Two new problems were found in the course of verifying, both of which are more serious
than the provenance worry that put the claims on the list:

* **U2 (new): the two arms in the 88.6-vs-74.1 comparison were scored on different
  pools** (44 vs 58 turns, 35 shared). The paper's Table 3 caption says "on the same
  prefixes". That is false as written. The delta survives matching (+14.3pp) but is
  **not significant** (exact McNemar p = 0.125).
* **U5 (new, and it resolves in our favour): the assistant-omission BigCodeBench cell
  had never been re-scored** under the unified dependency environment that T8 applied to
  every other cell in the same table row. I re-scored it. It is **unchanged at 15.0**,
  so the row is internally comparable after all — but nobody had checked, and the two
  cells beside it both moved by a problem when re-scored.

Artifacts written (T20-scoped, nothing under `outputs/`, nothing in another task's dir):

| File | What |
|---|---|
| `recompute_u2.py` | U2 recomputation + matched-pool paired test |
| `recompute_u3.py` | Table 3 (`tab:wildchat`) full reconstruction |
|  `snapshot_index.txt.gz` | `tar -tzf` index of `snapshot.tar.gz` (69,738 entries) |
|  `supp_index.txt.gz` | index of `supplementary.tar.gz` (2,167 entries) |
| `~/ac3/recovered_t20/` | the WildChat cells extracted for U3 (T20-scoped, does not collide with `~/ac3/recovered/`) |

---

## U2 — WildChat gpt-5.4: Reset 88.6 vs Gated-Reset 74.1 (−14.5pp)

### Search performed

Traced to `docs/reports/post_may26_megatable_round_summary.md:66-67` and
`docs/jun1_megatable_findings.md:50`, and to the paper at
`writing/overleaf_repo/neurips/neurips_2026_conference.tex:311` (Table 3) and `:347`
(discussion). The underlying run is `outputs/post_may26_wildchat_gpt54/`, N=1, **seed 42**
(as RECON already recorded at `tasks/RECON/worklog.md:378`). It is off disk but present
in `snapshot.tar.gz`, and **T11 had already extracted it** to
`~/ac3/recovered/ctx_editor/outputs/post_may26_wildchat_gpt54/` — four cells, each with
`turn_results.jsonl` carrying the per-turn judge verdicts.

**T11's re-judge does not settle U2.** T11 re-judged the 452 (AO, AC3) pairs of the
Phase-3b **gpt-5-mini** N=3 run (`post_neurips_ac3_phase3_huang`, arms s15 and augment).
The 88.6/74.1 cell is a different respondent (**gpt-5.4**) and a different arm pair
(Reset vs **Gated-Reset**, which T11 never judged). No overlap.

### Positive control (trap #1)

Before computing anything new, I reproduced all four **published** gpt-5.4 Table 3
"vs AO" cells from the same files with the same parser:

| arm | n | wins | ties | recomputed | published | match |
|---|---|---|---|---|---|---|
| Reset (`s15`) | 44 | 39 | 0 | **88.6%** | 88.6 | yes |
| Gated-Reset (`s2`) | 58 | 43 | 0 | **74.1%** | 74.1 | yes |
| Augment | 57 | 48 | 2 | **84.2%** | 84.2 | yes |
| Rewrite (`s3`) | 48 | 40 | 1 | **83.3%** | 83.3 | yes |

All four to the digit. Win-rate definition confirmed as `strategy wins / n`, ties counted
as non-wins. Pipeline sound.

### Verdict: **RECOMPUTED — the numbers are real. Keep it struck anyway, for a better reason.**

Three things came out of the recomputation.

**1. The comparison is not on a common pool.** The four arms share the same 179 Phase-1
turns and the same 76 AO-failure turns, but each Phase-2 arm was evaluated on a different
subset of them:

```
       s15 vs s2       |s15|=44 |s2|=58  shared=35  s15-only=9  s2-only=23
```

So `88.6 (n=44)` and `74.1 (n=58)` are computed over **different denominators with only
35 turns in common**. The paper's Table 3 caption states the Gated-Reset cell is
"$-$14.5pp vs. always-on Reset **on the same prefixes**"
(`neurips_2026_conference.tex:299`). That is **factually wrong as written**, and it is
exactly the kind of thing a reviewer handed the output directory would find. (`00`, `01`
and `03` already footnote that "each method is evaluated against its own
assistant-omission failure pool" — the caption simply contradicts that footnote.)

**2. The magnitude survives matching.** On the 35 shared turns:

| arm | matched | rate | published (unmatched) |
|---|---|---|---|
| AC3-Reset | 31/35 | **88.6%** | 88.6% (n=44) |
| AC3-Gated-Reset | 26/35 | **74.3%** | 74.1% (n=58) |
| delta | | **+14.3pp** | +14.5pp |

So the −14.5pp is not an artifact of the unequal pools. Good news for the paper's
substance.

**3. It is not statistically significant.** Paired on those 35 turns there are only
**7 discordant turns** (Reset-only win 6, Gated-only win 1). Exact McNemar
**p = 0.125**. A 14pp headline gap that rests on a 6-vs-1 split of seven turns, at N=1,
seed 42, un-order-balanced, is not a claim to put in front of a reviewer who has already
complained about statistical reliability.

**Recommendation: keep struck (as v5 already does), and update §7 U2's stated reason.**
The current reason ("not re-judged under order balancing") is the weakest of the three
available and invites "so re-judge it". The decisive reasons are the p = 0.125 and the
mismatched pools. There is no cheap experiment that fixes this: order-balancing 35 turns
would cost pennies but cannot manufacture significance out of seven discordant turns.

### Replacement wording — §7 U2 row of `CHANGES.md` (drop-in)

> | **U2** | WildChat gpt-5.4: Reset **88.6** vs Gated-Reset **74.1** (−14.5pp) | struck from v5 | **RESOLVED (T20) — the numbers are real but the claim is not supportable.** Both cells reproduce to the digit from `~/ac3/recovered/ctx_editor/outputs/post_may26_wildchat_gpt54/{s15,s2}_gpt5_4_seed42_1779830054/turn_results.jsonl` (39/44 and 43/58; `AR/tasks/T20/recompute_u2.py`, positive control: all four published gpt-5.4 cells reproduce exactly). But (i) the two arms were scored on **different pools** — 44 vs 58 turns, only 35 shared — so the paper's Table 3 caption claim "on the same prefixes" is wrong; (ii) on the matched 35-turn pool the gap survives at 88.6 vs 74.3 (**+14.3pp**), so the substance is fine, but (iii) it rests on **seven discordant turns** (6 vs 1), exact McNemar **p = 0.125** — not significant, at N=1 seed 42, un-order-balanced | **Keep struck. Do not reintroduce.** Not because it is unverified — it is verified — but because it is a 14pp headline resting on a 6-vs-1 split of seven turns. Separately: **fix the Table 3 caption** for the arXiv version (paper action, not rebuttal action) |

### Separate paper-side action (arXiv, not the rebuttal)

`writing/overleaf_repo/neurips/neurips_2026_conference.tex:299`, Table 3 caption. Replace

> The \mgpt~Gated-Reset cell ($-$14.5pp vs.\ always-on Reset on the same prefixes) is discussed in Section~\ref{sec:wildchat-results};

with

> The \mgpt~Gated-Reset cell ($-$14.5pp vs.\ always-on Reset; $-$14.3pp on the 35 prefixes both arms were evaluated on, exact McNemar $p=0.125$) is discussed in Section~\ref{sec:wildchat-results};

I did **not** apply this — `writing/overleaf_repo/` is out of bounds per the task brief.

---

## U3 — the WildChat "72–92%" honest range

### Search performed

The range's origin is documented, not mysterious: `docs/arxiv_push/debate/01_reviewer_skeptic.md:46`
raised that the paper's "84–86%" band was cherry-picked because **Table 3 spans
71.6%–91.5%**, and recommended "report the honest range (~72–92%)".
`docs/arxiv_push/debate/03_synthesis.md:24` accepted it and
`docs/arxiv_push/arxiv_revision_plan.md:70` scheduled it as edit **H2**. So "72–92%" is
the **rounded envelope of the 22 populated cells of `tab:wildchat`** — nothing more and
nothing less.

To check whether that envelope is real, I reconstructed **every populated cell of
Table 3** from per-turn judge verdicts. The cells are spread over five run directories,
none on disk; I located them in  `snapshot_index.txt.gz` and extracted the
`turn_results.jsonl` for each into `~/ac3/recovered_t20/`.

### Verdict: **VERIFIED — all 22 cells reproduce exactly. The range is 71.6–91.5 → "72–92%".**

| Model | Arm | vs AO recomputed | published | vs FC recomputed | published | source dir |
|---|---|---|---|---|---|---|
| gpt-5-mini | Reset | 146/176 **83.0** | 83.0 | 147/176 **83.5** | 83.5 | `huang_eval/phase2_s15_full/2026-03-25/09-05-26` |
| gpt-5-mini | Gated-Reset | 149/173 **86.1** | 86.1 | 145/173 **83.8** | 83.8 | `huang_eval/phase2_s2_full/2026-03-25/06-13-04` |
| gpt-5-mini | Rewrite | 147/178 **82.6** | 82.6 | 143/178 **80.3** | 80.3 | `huang_eval/phase2_full/2026-03-25/01-39-43` |
| gpt-5.4 | Augment | 48/57 **84.2** | 84.2 | 44/57 **77.2** | 77.2 | `post_may26_wildchat_gpt54/augment_*` |
| gpt-5.4 | Reset | 39/44 **88.6** | 88.6 | 34/44 **77.3** | 77.3 | `.../s15_*` |
| gpt-5.4 | Gated-Reset | 43/58 **74.1** | 74.1 | 42/58 **72.4** | 72.4 | `.../s2_*` |
| gpt-5.4 | Rewrite | 40/48 **83.3** | 83.3 | 35/48 **72.9** | 72.9 | `.../s3_*` |
| DSV4F | Augment | 64/76 **84.2** | 84.2 | 61/76 80.3 | — | `post_neurips_r2_huang_models/augment_DeepSeek_V4_Flash_*` |
| DSV4F | Reset | 57/76 **75.0** | 75.0 | 54/76 71.1 | — | `.../s15_DeepSeek_V4_Flash_*` |
| DSV4F | Rewrite | 57/72 **79.2** | 79.2 | 53/72 **73.6** | 73.6 | `post_may18_r6_b3_wildchat/s3_v8_dsv4f_*` |
| Kimi | Augment | 60/70 **85.7** | 85.7 | 55/70 78.6 | — | `post_may18_r3_wildchat_fills/augment_Kimi_K2_6_*` |
| Kimi | Reset | 53/74 **71.6** ← **min** | 71.6 | 45/74 60.8 | — | `post_neurips_r2_huang_models/s15_Kimi_K2_6_*` |
| Kimi | Rewrite | 54/59 **91.5** ← **max** | 91.5 | 45/59 **76.3** | 76.3 | `post_may18_r6_b3_wildchat/s3_v8_kimi_*` |

**22 of 22 populated cells reproduce to the digit.** Min = 71.6 (Kimi, Reset, vs AO,
n=74). Max = 91.5 (Kimi, Rewrite, vs AO, n=59). Rounded envelope = **72–92%**. The claim
is exactly what it says it is.

Three things worth knowing that the audit did not:

1. **T11's corrections do not touch a single Table 3 cell.** T11 corrected the *Phase-3b
   N=3 pooled* gpt-5-mini figures 89.8 → 87.8 (Reset) and 92.1 → 91.2 (Augment). Those
   pooled figures **appear nowhere in Table 3** — Table 3's gpt-5-mini column is the
   original Phase-2 run (its own caption says so), and its Reset cell is 83.0, not 89.8.
   So **there is no arithmetic conflict** between "72–92%" and "87.8 / 91.2". They are
   different quantities computed over different pools. §7 U3's "do not mix" instruction
   is right about presentation but the underlying worry — that one supersedes the other —
   is unfounded.
2. **The published cells are not cherry-picked across prompt versions.** Two Rewrite
   cells have a second run available at an earlier prompt version: DSV4F Rewrite is
   79.2 (v8, published) vs 83.6 (`post_may18_r3_wildchat_fills`, earlier prompt) and Kimi
   Rewrite is 91.5 (v8, published) vs 82.1 (earlier prompt). The published value is the
   **v8** run in *both* cases — once lower, once higher. Consistent rule, not selection.
   Worth knowing if a reviewer finds both directories.
3. **The range is a min/max over 22 N=1 cells**, so it is an order statistic and is
   systematically wider than the underlying spread. Binomial sd at the endpoints is
   ≈5.2pp (71.6, n=74) and ≈3.6pp (91.5, n=59), and T11 measured a further ±2pp of
   presentation-order randomisation variance per cell. The honest gloss is "every cell in
   the table lands between roughly 70% and 92%", not "the effect ranges from 72 to 92".

### Verdict and recommendation

**Not a liability. Retire U3 from §7 as verified.** It should not be struck; if anything
the current v5 posture (retired from reviewer text) gives away a defensible number. The
only requirement is a correct label.

### Replacement wording — §7 U3 row of `CHANGES.md` (drop-in)

> | ~~**U3**~~ | ~~WildChat per-cell range **72–92%**~~ | struck from v5 reviewer text; retained only in the guardrails list | **RETIRED (T20).** Verified, not unverifiable. The range is the rounded envelope of the 22 populated cells of `tab:wildchat` (min 71.6 = Kimi/Reset vs AO n=74; max 91.5 = Kimi/Rewrite vs AO n=59), an edit adopted deliberately at `docs/arxiv_push/arxiv_revision_plan.md:70` (H2). **All 22 cells were re-derived from per-turn judge verdicts and all 22 reproduce to the digit** (`AR/tasks/T20/recompute_u3.py`). T11's corrections touch **none** of them: T11 corrected the Phase-3b *pooled* figures (89.8→87.8, 92.1→91.2), which do not appear in Table 3 — Table 3's gpt-5-mini column is the original Phase-2 run and its Reset cell is 83.0 | **Safe to use, with a label.** Say "every cell of our per-respondent table lands between 72% and 92%", never "AC3 wins 72–92%" — it is a min/max over 22 single-run cells (binomial sd 3.6–5.2pp at the endpoints, plus ±2pp order variance per F30), so it is an order statistic, not an effect range. Still do not put it in the **same sentence** as the corrected 87.8/91.2 headline: different pools, different quantity |

### Optional reviewer-facing sentence, if the range is wanted back in `03_reviewer_5YHP.md` W1

> Across our full per-respondent breakdown (four operators x four respondent models, 22 populated cells), AC3 beats assistant omission in **every** cell, with per-cell win-rates between **72% and 92%**; these are single-run cells with a binomial standard deviation of 4–5pp each, so we quote them as a spread across configurations rather than as a confidence interval, and separately report the order-balanced pooled figures above.

---

## U4 — tau2 gpt-5-mini: "only 1 of 11 baseline failures attributable to context pollution"

### Search performed

| Where I looked | Result |
|---|---|
| paper tex | **Found.** `writing/overleaf_repo/neurips/neurips_2026_conference.tex:360` and `:558`; the table itself is `tab:tau2-failure-modes` at `:565-577`. Present in the COLM draft too |
| source artifact | **Found.** `~/ac3/tau2_ctxe/ctx_edit/EXPERIMENT_LOG.md:120-137`, section "Diagnostic: Failure Mode Analysis (2026-03-25)". Committed as `169b044` ("docs: diagnostic analysis + experiment 3 (3-trial) launched", 2026-03-24 21:06 UTC, Matthew Ho). The five categories and counts are **verbatim identical** to the paper's Table 8, including the parenthetical `break_app_sms_perm` that the paper drops |
| the 11 failures themselves | **NOT FOUND, anywhere.** See below |
| `~/ac3/tau2_ctxe/ctx_edit/outputs/` | only `T6_reps`, `T6_smoke_*`. `exp4_parallel/` and `diagnostic_s2_losses/` are gone |
| `git -C ~/ac3/tau2_ctxe log --all --name-only` | `outputs/` was **never tracked**; `git ls-files \| grep outputs` is empty. Only `run_diagnostic.py` was ever committed |
| `snapshot.tar.gz` (69,738 entries) | 13 tau2 hits, **all** docs and prompt templates. Zero tau2 output directories |
| `supplementary.tar.gz` (2,167 entries) | zero tau2 hits |
| `~/ac3/recovered/`, `~/ac3/recovered_t2c/`, `~/ac3/t14_snapshot/`, `outputs/runs.yaml` | no tau2 outputs |
| grep for the category strings (`Premature transfer`, `Task too hard`, `User sim issue`) across `~/ac3` | 7 hits: 6 `.tex` copies and `EXPERIMENT_LOG.md`. **No labels file, no rubric, no per-failure record has ever existed** |

### Coordination with T6 (per the brief — read first, ran nothing)

Read `AR/tasks/T6/worklog.md` in full. **T6 does not touch this claim.** Its matrix is
three *agent* models — gpt-5.4, DeepSeek-V4-Flash, Kimi-K2.6 (worklog line 11, 140,
163-165). `gpt-5-mini` appears in T6 only as the **user simulator and analyzer** for every
arm, never as the respondent. The gpt-5-mini respondent cell that U4 characterises is the
Appendix `app:tau2-diagnostic` cell, which T6 is not re-running. **U4 is decoupled from
T6 and does not need to wait for it.** I ran nothing against `~/ac3/tau2_ctxe` and wrote
nothing into T6's directories.

But T6's *direction* changes what U4 is for. As of T6's 17:16 entry, remeasured Baseline
is at or above every AC3 arm on all three models. If that lands, the tau2 row is
withdrawn, and a sentence whose job is to explain away a null on a fourth model by saying
"that configuration had no headroom" will read as a general-purpose excuse rather than a
diagnosis. That is a rhetorical risk independent of whether the number is right.

### Verdict: **PARTIALLY VERIFIED — the number is traceable, the evidence is unrecoverable. Soften.**

What is solid: the claim is not invented. It is transcribed faithfully from a dated,
committed lab-notebook entry into Table 8, and the arithmetic is internally consistent —
Experiment 4 (`exp4_parallel`) scored S0 at 9/20 = 45%, so 11 failures is exactly right
for that run.

What cannot be produced, and never could be:

1. **The 20 traces are gone** and were never committed, archived or snapshotted. If a
   reviewer asks "show us the 11 failures", we have a table and nothing behind it.
2. **The labelling is one author's qualitative reading**, with no published rubric, no
   second annotator and no inter-annotator agreement. The categories are not defined
   anywhere. This is fine as a lab note; it is presented in the paper as a Table.
3. **It is the worst of three trials.** The appendix reports gpt-5-mini Baseline per-trial
   as {45.0, 55.0, 60.0}% and says the main table reports **best-of-3**. The 11 failures
   are the **45.0** trial (Experiment 4). A reviewer reading "of 11 Baseline failures"
   against a reported 60% cell computes 8 failures at n=20 and finds a mismatch. The
   denominator and the reported cell come from different trials, and nothing in the paper
   says so.
4. **`n` is ambiguous.** Exp 4 ran 20 tasks; the published tau2 sweep uses n=19
   (`telecom_small` minus `[service_issue]break_apn_settings[PERSONA:None]`, T6 worklog
   line 11). "11 of 20" and "11 of 19" are different denominators.

None of (1)–(4) makes the claim false. All of them make it indefensible under a follow-up
question, which is precisely the liability §7 exists to catch.

**Recommendation: (b) soften.** Keep the substance — tau2's gpt-5-mini configuration is
not pollution-limited — and drop the false precision of "1 of 11", which we cannot
document, cannot attribute to a rubric, and which is drawn from a different trial than the
cell it is used to excuse.

Not (a) strike: the substance is genuinely load-bearing for the CW4 answer and is
independently supported by the *mechanism* sentence already in the paper (the customer
service policy enumerates diagnostic options, which substitutes for an external editor).
Not (c) re-run: re-deriving it means re-running the gpt-5-mini tau2 baseline **and**
hand-labelling 8–11 failures, in the middle of T6's sweep on the same fork and the same
rate-limited endpoints. Cost ≈ 20 rollouts (~$0.6, ~15 min) plus a human labelling pass
we cannot do overnight and cannot make defensible without a second annotator. **Not worth
it during the discussion period.** The right home for this is the camera-ready, where the
labelling can be done properly with a published rubric.

### Replacement wording 1 — `00_general_response.md` line 144 (drop-in)

Current:

> On the specific gpt-5-mini cell iNYK cites: our own failure-mode analysis finds that **only 1 of 11 baseline failures on that model is attributable to context pollution**. That configuration is simply not pollution-limited, so a null result there is the expected outcome rather than evidence against the method. The informative comparisons are the models where pollution actually binds.

Replace with:

> On the specific gpt-5-mini cell iNYK cites: our own inspection of that configuration's baseline failures found that **almost all of them are not pollution-driven** — they are dominated by missing domain knowledge and by step-budget exhaustion under the hard personas, with a single case of the repetitive-loop behaviour our method targets. That configuration is simply not pollution-limited, so a null result there is the expected outcome rather than evidence against the method. We flag that this was a qualitative reading of one trial's traces rather than a rubric-based annotation, and we will replace it in the camera-ready with a labelled failure taxonomy over all trials, with a published rubric and a second annotator. The informative comparisons are the models where pollution actually binds.

### Replacement wording 2 — `01_reviewer_iNYK.md` line 43 (drop-in)

Current:

> Two further points on the specific cell you cite. First, our own failure-mode analysis of that gpt-5-mini configuration finds that **only 1 of 11 baseline failures is attributable to context pollution**, so that configuration is not pollution-limited and offers almost no headroom for any pollution-removal method. A null result there is expected rather than contradictory. Second, we have sharpened the abstract and introduction to the precise claim that AC3 is **the only method tested that improves over full context across the entire spectrum**.

Replace with:

> Two further points on the specific cell you cite. First, when we inspected that gpt-5-mini configuration's baseline failures, **almost none of them were pollution-driven**: the dominant modes were missing domain knowledge and step-budget exhaustion under the hard personas, with a single instance of the repetitive-loop behaviour our method is designed to remove. That configuration therefore offers almost no headroom for any pollution-removal method, and a null result there is expected rather than contradictory. In the interest of precision we should say that this was a qualitative reading of one trial's traces, not a rubric-based annotation with a second annotator; we will do it properly for the camera-ready and report the taxonomy over all trials. Second, we have sharpened the abstract and introduction to the precise claim that AC3 is **the only method tested that improves over full context across the entire spectrum**.

### Replacement wording 3 — §7 U4 row of `CHANGES.md` (drop-in)

> | **U4** | tau2 gpt-5-mini: "only **1 of 11** baseline failures attributable to context pollution" | v5 `00_general_response.md` CW4, `01_reviewer_iNYK.md` W3 | **RESOLVED (T20) — number traceable, evidence unrecoverable.** Source found: `~/ac3/tau2_ctxe/ctx_edit/EXPERIMENT_LOG.md` §"Diagnostic: Failure Mode Analysis (2026-03-25)", commit `169b044` (2026-03-24), whose five-row table is verbatim identical to the paper's `tab:tau2-failure-modes`. Arithmetic checks out: Exp 4 scored S0 9/20 = 45%, so 11 failures is right *for that trial*. But the 20 traces are **gone** — never tracked in `tau2_ctxe` git, absent from the 69,738-entry `snapshot.tar.gz`, absent from `supplementary.tar.gz`, absent from disk — and **no labels file or rubric has ever existed**; the labelling is one author's qualitative reading with no second annotator. Two further defects: it is the **45.0% trial**, the *worst* of the three gpt-5-mini trials {45.0, 55.0, 60.0}, while the table reports **best-of-3**, so 11 failures does not reconcile with the reported cell; and n is ambiguous (Exp 4 used 20 tasks, the published sweep uses 19). **Decoupled from T6**, which re-measures gpt-5.4/DSV4F/Kimi only — gpt-5-mini appears in T6 solely as user-sim and analyzer | **SOFTEN — drop "1 of 11", keep the substance.** Replacement wording for both files in `AR/tasks/T20/worklog.md` §U4. Re-deriving it costs ~20 rollouts (~$0.6) *plus* a hand-labelling pass that cannot be made defensible overnight; the right home is the camera-ready, with a published rubric and a second annotator, over all three trials |

---

## U5 — CollabLLM assistant-omission column (MATH-Hard 90, BigCodeBench 15), still N=1

### Search performed

`AR/tasks/T8/worklog.md` §3: T8's sweep was **4 arms x reps {2,3}** = 8 fresh cells, and
those four arms are Baseline and AC3-Augment on math-hard, Baseline and AC3-Reset on
bigcodebench. **No assistant-omission arm was run.** The AO numbers come from replicate 1
only, recovered from the snapshot at
`~/ac3/recovered/ctx_editor/outputs/post_neurips_r2_collabllm_user_deepseek/`.

`src/ctx_editor/config/experiment/collabllm_assistant_omit.yaml` exists, so the arm is a
one-line config away from runnable.

### Recomputation, and a comparability defect nobody had checked

**Raw cell values** (from each cell's `metrics.json`, zero API calls):

| cell | correct/20 | acc |
|---|---|---|
| `collabllm_assistant_omit_math-hard_rep1` | 18/20 | **90.0** |
| `collabllm_assistant_omit_bigcodebench_rep1` | 3/20 | **15.0** |
| `collabllm_baseline_math-hard_rep1` | 19/20 | 95.0 (control) |
| `collabllm_baseline_bigcodebench_rep1` | 1/20 | 5.0 (control) |
| `collabllm_ac3_augment_v8_math-hard_rep1` | 20/20 | 100.0 (control) |
| `collabllm_ac3_reset_v8_bigcodebench_rep1` | 4/20 | 20.0 (control) |

Both AO cells reproduce the reviewer-facing numbers exactly, and the four controls
reproduce the numbers T8 recovered. So far, so unremarkable.

**The defect.** T8 §6 found that BigCodeBench's sandbox silently scores 0 when a
dependency is missing, and therefore **re-scored every bigcodebench cell offline in one
unified dependency environment** — which moved Reset rep1 from 4/20 to 5/20 and Baseline
rep1 from 1/20 to 2/20 (`BigCodeBench/451`, a deterministic library-version difference).
The reviewer-facing table in `03_reviewer_5YHP.md` W4 therefore prints **re-scored**
Baseline 6.7 and Reset 21.7 **beside an AO cell that was never re-scored**. Two of the
three cells in that row had moved by a problem under re-scoring and nobody had checked
the third.

**So I re-scored it** — offline, from the stored `extracted_answer` fields, using T8's own
`rescore_bcb.py`, zero API calls.

**Positive control (trap #1):** re-score the two cells whose re-scored values T8
published, first.

| cell | stored | T8's re-score | my re-score | control |
|---|---|---|---|---|
| AC3-Reset rep1 | 4/20 | **5/20** | **5/20** | reproduces |
| Baseline rep1 | 1/20 | **2/20** | **2/20** | reproduces |
| **AO rep1** | 3/20 | *never done* | **3/20 — unchanged** | **new** |
| AC3-Augment rep1 | 3/20 | *never done* | **3/20 — unchanged** | new |

**Result: the AO bigcodebench cell is 15.0 under the unified scorer, identical to its
stored value.** The row is internally comparable after all. This is a real check that did
not previously exist, and it lands in the paper's favour — the AO column can stay in the
table without a scoring-environment caveat.

(math-hard AO needs no equivalent check: math-hard is LLM-judged by gpt-4o-mini, not
execution-scored, so the dependency-environment failure mode does not apply.)

### Verdict: **VERIFIED and strengthened. The only remaining liability is N=1 — and it is cheap to remove.**

### Cost of removing it

4 cells: assistant-omission x {math-hard, bigcodebench} x reps {2, 3}. From T8's own logs:

| | per cell |
|---|---|
| API cost | $0.036–0.061 (median ~$0.045) |
| wall-clock | 15–25 min at `execution.max_concurrent=5` |

AO runs **no analyzer**, so it should sit at the cheap end (Baseline-like). Two streams in
parallel, as T8 ran them:

> **≈ $0.20 total and ≈ 50 minutes wall-clock.** Plus one offline re-score pass for the
> two new bigcodebench cells (free).

Invocation, identical to T8 §3 with the arm swapped and no `analysis_cache_dir` override
(AO has no analyzer, so passing it is a Hydra struct error, same as for Baseline):

```bash
.venv/bin/python -m ctx_editor.run_collabllm \
  experiment=collabllm_assistant_omit \
  model=deepseek_v4_flash_user_deepseek \
  load_balancer=multi_endpoint_foundry \
  task.name=<collabllm_math|collabllm_code> \
  task.dataset_name=<math-hard|bigcodebench> \
  task.limit=20 execution.max_concurrent=5 \
  experiment_name=T20_ao_<tag> logging.output_dir=outputs/T20/<tag>
```

Two traps for whoever runs it: (i) `bigcodebench` + its 11 transitive test dependencies
must be installed or every cell silently scores 0 (T8 §5/§6) — run the canonical-solution
pre-flight (`canon_check.py`, expect 19/20) first; (ii) re-score the new bigcodebench
cells offline with `rescore_bcb.py` so they sit in the same environment as the rest of the
row.

**This is the cheapest open item in the reply set.** $0.20 and under an hour converts the
last N=1 column in a reviewer-facing table into N=3. I did not run it: it is a new
experiment and the brief scopes T20 to verification.

### Replacement wording — if the cells are NOT run, `03_reviewer_5YHP.md` W4 footnote (drop-in)

Current:

> † assistant-omission cells are single runs and were not re-replicated; treat them accordingly.

Replace with:

> † The assistant-omission cells are **single runs** and were not re-replicated at N=3, so they should be read as point estimates on a 5pp-quantised 20-problem draw, not as means. We have verified that they are nonetheless **scoring-comparable** with the replicated cells beside them: the BigCodeBench assistant-omission cell was re-scored offline in the same unified dependency environment as every other cell in this table and is unchanged at 15.0 (by contrast, re-scoring moved both the full-context and AC3-Reset replicate-1 cells by one problem). MATH-Hard is LLM-judged and is unaffected by that environment. We will replicate the assistant-omission column at N=3 for the camera-ready.

### Replacement wording — §7 U5 row of `CHANGES.md` (drop-in)

> | **U5** | CollabLLM assistant-omission cells (MATH-Hard 90, BigCodeBench 15) | v5 `03_reviewer_5YHP.md` W4 table | **RESOLVED (T20) — verified and strengthened; only N=1 remains.** Both cells reproduce exactly from `~/ac3/recovered/ctx_editor/outputs/post_neurips_r2_collabllm_user_deepseek/collabllm_assistant_omit_{math-hard,bigcodebench}_rep1_1779092497/metrics.json` (18/20 and 3/20). **New:** T8 re-scored every *other* bigcodebench cell in that table row under a unified dependency environment (which moved Baseline rep1 1→2 and Reset rep1 4→5) but **never re-scored the AO cell** — so the row mixed scoring environments and nobody had checked. T20 re-scored it offline, zero API calls, positive controls reproducing T8's 5/20 and 2/20: **AO is unchanged at 3/20 = 15.0**, so the row *is* internally comparable. AC3-Augment bigcodebench rep1 likewise unchanged at 3/20 | **Keep the column; upgrade the footnote** (wording in `AR/tasks/T20/worklog.md` §U5) — the comparability check is a point in our favour and should be stated. **Better still, run it:** 4 cells (AO x 2 datasets x reps 2,3) ≈ **$0.20 and ~50 min** wall-clock on two parallel streams, per T8's own per-cell cost/time logs. Cheapest open item in the reply set |

---

## Summary table

| ID | Verdict | Recomputed value | Action |
|---|---|---|---|
| **U2** | Recomputed — real, but not supportable | 88.6 (39/44) / 74.1 (43/58) exact; matched pool 88.6 vs 74.3, **+14.3pp, McNemar p = 0.125** | **Keep struck**, update the stated reason. Fix the Table 3 caption in the paper |
| **U3** | **Verified** — 22/22 cells reproduce to the digit | range **71.6–91.5** → "72–92%" | **Retire from §7.** Safe to use with a label; T11's corrections touch no Table 3 cell |
| **U4** | Number traceable, **evidence unrecoverable** | 11 failures = 20 − 9 on the 45% trial, consistent | **Soften** — drop "1 of 11". Re-deriving needs a hand-labelling pass; defer to camera-ready |
| **U5** | **Verified and strengthened** | AO 18/20 = 90.0, 3/20 = 15.0; **AO re-score unchanged at 15.0** | **Keep + upgrade footnote.** Or run 4 cells for **≈$0.20 / ~50 min** to reach N=3 |

**Struck or softened: U4 only** (soften). **U2 stays struck** but for a stronger reason.
**U3 and U5 are cleared.**

## Ambiguities I resolved myself (per the brief)

* The brief asks for a replacement wording "for every claim you cannot verify". U2, U3
  and U5 all verified, so strictly none was owed for them — but U2's §7 *reason* was
  wrong and U5's footnote was leaving a defensive point on the table, so I wrote drop-in
  replacements for those too. U3's is optional and marked as such.
* I extracted to `~/ac3/recovered_t20/` rather than the shared `~/ac3/recovered/` to
  avoid a double-write collision, per the trap about `outputs/`.
* I did **not** apply the Table 3 caption fix. It is a paper edit, and
  `writing/overleaf_repo/` is out of bounds for this task. It is written out above ready
  to paste.
* I read `~/ac3/tau2_ctxe/ctx_edit/EXPERIMENT_LOG.md` and `tau2_ctxe`'s git log
  (read-only) but ran nothing against the tau2 fork and wrote nothing into T6's
  directories, per the coordination instruction.
* No `git checkout` was performed. Nothing under `src/`, `outputs/`, `replies/v5/` or any
  other task's directory was modified.
