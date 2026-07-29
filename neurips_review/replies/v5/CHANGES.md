# CHANGES.md — v4 → v5 claim audit

Every assertion in `replies/v4/` audited against the 2026-07-29 autoresearch session (findings **F1–F81**, decisions **D1–D21**: `../../autoresearch/WORKLOG.md`; retired claims: `../../autoresearch/PROVENANCE.md`). Task T15 worklog: `../../autoresearch/tasks/T15/worklog.md`.

**Revision history.** T15 wrote this audit at F1–F38, with four claims on HOLD pending two in-flight audits. **T19** (`../../autoresearch/tasks/T19/worklog.md`) revised it once T14, T16, T17 and T18 landed: the T14 hold is resolved, U1 is retired, and the ERGO denominator disclosure is added as §9 and as claim rows 1.23 / 2.10 / 3.12 / 5.9 / 6.x. **The T6 (tau2) holds were untouched and still live at that point — they were discharged later, by T28; see §12.3.** **T30** audited the whole set for internal coherence and left four items open; **T32** (`../../autoresearch/tasks/T32/worklog.md`) settled the two factual ones from artifacts, with no re-runs — see §13. **T33** (`../../autoresearch/tasks/T33/worklog.md`) closed the remaining cleanup: J3, the T2c caption at its generator, and one tone leak; J4 was escalated there rather than fixed. **T34** (`../../autoresearch/tasks/T34/worklog.md`) then resolved J4: the Tally is re-derived from the rows, the bucket scheme is written out, and a derivation rule is stated so the drift cannot recur — see §14.4. T34 changed no claim, no row and nothing reviewer-facing. **T35** (`../../autoresearch/tasks/T35/worklog.md`) then closed the two row-level items T34 had reported but was not authorised to fix: row **1.17**'s stale "(pending T6)" now states the settled position, matching row 4.4, and row **3.9** carries the `*(new)*` marker its status implies. The tally is unchanged and still reconciles at 82.

## Tally

> **Derivation rule (T34).** *This table is derived from the numbered rows of §§1–6 and from nothing else. Whenever a row is added, removed, or its Status cell changes, re-derive every bucket from the rows — do not increment the table in prose.* Every drift this table has suffered was an increment recorded in a "Changes made by T*n*" paragraph and never applied here; naming the mechanism is the fix.

| Status bucket | Count |
|---|---|
| **Unchanged** (re-verified; wording untouched, or only a label/frame added around it) | 20 |
| **Corrected** (a v4 number or wording changed; the claim survives) | 21 |
| **Struck** (a v4 claim, or an identified half of one, removed from v5) | 9 |
| **Replaced by results** (a v4 *promise* — "we are adding X" — discharged by a measurement) | 5 |
| **HOLD → resolved** (a claim sealed pending an in-flight task, since unsealed by its result) | 3 |
| **Newly added** (result that did not exist in v4) | 22 |
| **Bookkeeping / not used** (records no reviewer-facing claim at all) | 2 |
| **Total numbered rows, §§1–6** | **82** |

Two counts that are **not** row buckets, and are therefore stated outside the total rather than added into it:

| | |
|---|---|
| **On HOLD** (blocked on an in-flight task) | **0** — no row carries a live hold; the three former holds are in *HOLD → resolved* |
| **UNVERIFIED** (no artifact found) | **1** — U6 alone, and it is a **§7** liability, not a numbered row of §§1–6 |

### The bucket scheme, written down so nobody has to re-derive it

**How a row is assigned.** Read the row's **Status** cell only, and take the *tokens* it contains. Where a cell carries more than one token, assign the single highest-precedence one, so that every row lands in exactly one bucket and the buckets sum to the row count:

**Struck > Corrected > HOLD → resolved > Replaced by results > Newly added > Unchanged > Bookkeeping.**

Precedence runs from least to most flattering to us, which is also the tie-break rule for genuine judgement calls: where a row could honestly be read two ways, take the reading that concedes more.

**The statuses that previously mapped to no bucket, and where they now go.**

| Status token as written in the rows | Bucket | Why |
|---|---|---|
| "replaced by results", "promise fulfilled" | **Replaced by results** | A v4 promise kept is not a v4 error corrected. Nothing was wrong with the v4 text; it said we would measure something and we did. Folding these into *Corrected* would inflate our own error count; folding them into *Unchanged* would hide that the text was rewritten. They get their own bucket. |
| "HOLD → resolved", "resolved (T19)" | **HOLD → resolved** | A claim deliberately sealed pending an in-flight audit, then unsealed by that audit's result. The seal is a process state, not a defect: the claim was never asserted in a state we could not stand behind. Distinct from *Corrected* (we printed something wrong) and from *Struck* (we removed it). |
| "qualified by T25" | **Corrected** | Judgement call, taken against us. The v4 numbers stand but v5 materially qualifies what they support, which is a wording change. |
| "unchanged in substance, wording fixed" | **Corrected** | Judgement call, taken against us: wording changed, so it is a correction, notwithstanding the lead word. |
| "struck / corrected", "half struck", "CORRECTED — claim struck" | **Struck** | Precedence. If part of a claim is gone, the row records a removal. |
| "not used", "bookkeeping" | **Bookkeeping / not used** | Rows 4.24 and 5.10 audit no reviewer-facing assertion — 4.24 records a framing retired *before* it was ever written into a reply, 5.10 records the placement of an internal note. Counting them as claims would overstate the audit's scope; deleting them would lose the record, which is what they exist for. |

**The one status where the Claim column overrides the Status cell: none.** All **22** rows whose Claim column reads *(new)* carry a *newly added* status, and the reverse now holds too. **3.9** was the one row where the two disagreed: its Claim column names a v4 question ("Q3 analyzer-model sensitivity") and then states that **v4 never answered this half of it**, so it carried a *newly added* status without the marker. By the printed definition — *result that did not exist in v4* — 3.9 is newly added, which is why *Newly added* is 22 and not 21; **T35 added the missing *(new)* marker to its Claim cell**, so the marker count and the bucket agree. Rows **2.4** and **3.2** also carry a trailing "+ newly added concession" token, but lead with *HOLD → resolved* and are counted there, once each.

**Per-bucket row lists, so the arithmetic is checkable without re-reading the tables.**

* **Unchanged (20)** — 1.1, 1.2, 1.3, 1.5, 1.8, 1.14, 1.19, 2.1, 2.7, 2.8, 3.6, 3.8, 3.10, 4.1, 4.7, 4.20, 4.21, 4.25, 5.1, 5.8
* **Corrected (21)** — 1.4, 1.6, 1.7, 1.9, 1.10, 1.11, 1.16, 2.3, 2.5, 2.6, 2.9, 3.3, 3.4, 4.5, 4.6, 4.9, 4.10, 4.18, 5.2, 5.3, 5.5
* **Struck (9)** — 1.13, 1.15, 1.17, 4.4, 4.8, 4.11, 4.12, 4.19, 5.4
* **Replaced by results (5)** — 1.18, 3.1, 3.7, 4.13, 4.15
* **HOLD → resolved (3)** — 1.24, 2.4, 3.2
* **Newly added (22)** — 1.12, 1.20, 1.21, 1.22, 1.23, 2.2, 2.10, 3.5, 3.9, 3.11, 3.12, 4.2, 4.3, 4.14, 4.16, 4.17, 4.18a, 4.22, 4.23, 5.6, 5.7, 5.9
* **Bookkeeping / not used (2)** — 4.24, 5.10

20 + 21 + 9 + 5 + 3 + 22 + 2 = **82**. §6 contributes no numbered rows — it is prose mirroring §§1–5 — so all 82 sit in §§1–5.

*Bookkeeping note (T28): this table had drifted — T25's increment from 15 to 16 corrections was recorded in prose but never applied to the table, and the printed total of 67 did not equal the sum of its own rows. The counts were made the sum of the rows as of T28, and the three T6 holds are discharged (§12.3), which is why On HOLD is zero.*

*Bookkeeping note (T34): T28's fix decayed, because later passes introduced statuses ("replaced by results", "HOLD → resolved", "promise fulfilled", "not used", "bookkeeping") that no bucket covered, so eleven rows counted toward nothing and the printed total of 69 stood against 82 actual rows. T34 re-derived every bucket from the rows under the scheme above, added the three missing buckets, and moved On HOLD and UNVERIFIED out of the total because neither describes a §§1–6 row. **Two counts moved for reasons that are not re-bucketing and are worth stating plainly: the row count is 82, not the 81 recorded in §14.4 — the difference is row 4.18a, a real row with its own status and its own evidence that the T33 enumeration missed; and Newly added is 22, not 21, for the 3.9 reason given above.** No row's status, claim, number or evidence was touched, and nothing reviewer-facing was touched. See `../../autoresearch/tasks/T34/worklog.md` for the row-by-row enumeration.*

*Bookkeeping note (T35): T34 reported three row-level defects it was not authorised to repair; T35 closed two of them, and the tally is unaffected by both. (i) **Row 1.17** still read "struck (pending T6)" although T6 had landed and its parallel row 4.4 had been updated; 1.17 now records the settled position in 4.4's wording — the strike is permanent (§12.3), because T6 refuted the cells the claim rested on (F78/F79). Bucket unchanged: *Struck* either way. (ii) **Row 3.9** was newly added but carried no `*(new)*` marker in its Claim cell, which is why the marker count read 21 against a *Newly added* bucket of 22; the marker is added, so 22 rows now carry it and the two agree. Bucket unchanged: *Newly added*. The re-derived counts are identical to T34's — 20 / 21 / 9 / 5 / 3 / 22 / 2 = **82** — and were re-checked mechanically against the rows. (iii) T34's third item, that a "we audited N claims" statement should quote fewer than 82, needed no edit: **no such statement exists** in `CHANGES.md`, in `README.md`, or in any of the six reviewer-facing files (the only claim totals anywhere are the historical "64 claims" in T15's worklog and `PROVENANCE.md`, which describe the table as it stood then). What N should be is left open deliberately — see `../../autoresearch/tasks/T35/worklog.md`, which records why the question is under-specified rather than arithmetical.*

Of the 17 corrections, **8 move against us** (CollabLLM MATH-Hard, the CollabLLM assistant-omission column, FN-adjusted accuracy / end-to-end table, the selectivity claim — first re-attributed to Rewrite, then retracted for both operators — the WildChat headline, memory gains, auditing-on-math, and the tau2 withdrawal), **3 move in our favour** (BigCodeBench, database leak-free replication, budget accounting), and the remainder are wording-only. Of the 5 claims T19 newly added, **all 5 are the ERGO denominator disclosure**, which moves against us by raising a competitor. *(T30: this paragraph still read "of the 15 corrections … 7 move against us" after T25 and T28 had taken the count to 17. The two later additions are the T2B-driven selectivity retraction and the tau2 withdrawal, both against us.)* *(T34: the "17" here is the pre-T34 tally figure, **left exactly as written**. It was never derived from the rows, so it cannot be reconciled against them; the row-derived **Corrected** bucket is **21** (see the Tally above). The eight-against / three-in-favour split names specific corrections and is a characterisation, not an arithmetic total, so T34 did not touch it — re-deriving it would be a claim decision, not bookkeeping. Nothing reviewer-facing quotes either number; the reviewer-facing self-correction count is the separate "eight in total", re-verified at §14.2.)*

**The four paragraphs that follow are a historical record of how the tally moved, pass by pass. They are not the tally.** They are kept because the audit trail is worth having, but per the derivation rule above the table is authoritative and is re-derived from the rows; the counts quoted below are those that were current when each paragraph was written.

**Changes made by T19 to T15's tally.** Newly-added 11 → 16 (five ERGO disclosure rows). On-HOLD 4 → 3 (1.13, 2.4, 3.2, 4.4 were the four; the T14-gated provisional flag on all LiC figures is lifted, and 4.4's hold is now T6-only — the three remaining holds are all tau2). UNVERIFIED 5 → 4 (**U1 retired**: the gate-statistic artifacts do exist, at `scripts/analysis_rewrite_v_reset/data/gated_reset_reconstructed_{lic,collabllm}.md`, and T16 re-derived both independently from raw traces). Total 64 → 67.

**Changes made by T21 (from T20's verification pass).** UNVERIFIED 4 → **1**: U2, U3, U4 and U5 are all resolved, leaving only U6, which is unclosable by construction. Corrections 14 → 15, the new one being the CollabLLM assistant-omission column taken from N=1 to N=3 (§10). On-HOLD stays at 3 — all three are tau2, and every INTERNAL/HOLD block in the reply files is byte-identical to what T15 wrote (verified mechanically; see §10).

**Changes made by T25 (from T2B and the T23 red team).** Corrections 15 → **16**, and one of the existing sixteen changed direction: the "preserve what's correct" claim, which T19 had re-attributed to **AC3-Rewrite**, is now **retracted for both operators** after T2B measured selectivity causally on naturally occurring spans (F66). Rows 3.11 and 4.16 and §8 rule 3 are revised accordingly, and a new **§11** records the retraction, the assembled counter-case to the red team's strongest objection, and the nine red-team HIGH items applied or deferred. On-HOLD stays at 3 and every INTERNAL/HOLD block remains byte-identical (verified mechanically; see §11.4).

**Changes made by T28 (from T27's measured items and T6's landing).** Corrections 16 → **17**, the new one being the **withdrawal of the tau2 improvement claim** after T6 re-ran the full published matrix at N=3 and found two of three published baselines did not replicate. On-HOLD 3 → **0**: all five `⚠ INTERNAL — HOLD` tau2 blocks and both `⚠ INTERNAL — T19 renumbering` notes are **resolved and removed**, which is what they were written for. Newly-added 16 → **21**, from T27's four resolved MEDIUM items (the neutral-prompt condenser control, MT-OSC at w=2, the item-level McNemar plus problem-clustered CIs, the M3 independence probes and bootstrap, and the M6 human-validation disclosure). Two of the red team's own suggested fixes were measured and found **false**; neither is posted, and both are annotated in place in `AR/tasks/T23/RED_TEAM.md` per decision **D20**. New **§12** records all of it, including the two places that needed reconciling and the per-block HOLD verification.

## Path legend

| Shorthand | Full path |
|---|---|
| `AR/` | `neurips_review/autoresearch/` |
| `EXP/` | `neurips_review/experiments/` |
| `RPT/` | `docs/reports/` |
| `OUT/` | `outputs/` (repo root; gitignored) |

---

## 1. `00_general_response.md`

| # | Claim as written in v4 | Status | Evidence (finding + artifact) | New wording in v5 |
|---|---|---|---|---|
| 1.1 | Reviewer-praise quotes (self-contained vs. referential; structural exclusion; modularity) | **unchanged** | `neurips_review/ac3_reviews_clean.md` | verbatim |
| 1.2 | "same four operators across 3 models x 4 LiC tasks, plus CollabLLM, WildChat, tau2, one code path, no per-benchmark tuning" | **unchanged** | `RPT/post_neurips_ac3_phase1.md`, `RPT/post_neurips_ac3_phase2.md` | verbatim |
| 1.3 | Paired significance: AC3-Reset **+15.9pp, 33/2/1, p < 0.0001** | **unchanged**, now explicitly labelled *raw accuracy* | `EXP/paired_analysis_results.txt`; source tables `RPT/post_neurips_ac3_phase{1,2}.md`. **Verified raw**: every (task, prefix) cell uses one denominator across all strategies, so the F28 FN-adjustment bias does not touch this table | "…across all 36 paired comparisons …, on **raw accuracy**:" |
| 1.4 | "50 problems per task" | **corrected** (wording) | `RPT/post_neurips_ac3_phase1.md` — per-cell denominators are 36–50, not uniformly 50 (code_v2 conv2 = 36) | "**up to 50** problems per task … (36–50 conversations per prefix depending on task, up to 150 per cell)" |
| 1.5 | Per-model paired gains **+17.1 / +16.7 / +13.9pp** | **unchanged** | `EXP/paired_analysis_results.txt` | verbatim |
| 1.6 | AC3-Reset "outperforms the assistant-omission design-oracle" (+15.9 vs +13.3) | **qualified by T25** | `EXP/paired_analysis_results.txt`; head-to-head recomputed by T25 from `RPT/post_neurips_ac3_phase{1,2}.md` | The two means are correct, but the head-to-head over the same 36 triples is **+2.6pp on 15 W / 17 L / 4 T** — a wash outside LiC-database (+18.7pp, 8/9). A reviewer can derive this from the two printed rows, so v5 now states it itself and uses it to make the operator-by-regime argument (see §11.2) |
| 1.7 | WildChat "**89.8 +/- 1.4** (Reset) and **92.1 +/- 1.3** (Augment)" | **corrected** | **F31**, `AR/tasks/T11/worklog.md` §(a); raw `AR/tasks/T11/out/order_gpt5mini.jsonl` | "**87.8 +/- 2.1** (Reset) and **91.2 +/- 2.1** (Augment) … order-balanced values from a full re-judge" |
| 1.8 | WildChat "over 3 **seeds**" | **unchanged** | **F4** — WildChat's N=3 *are* real seeds (42/43/44), confirmed in `AR/tasks/T11/worklog.md` | keeps "seeds" |
| 1.9 | CW3 end-to-end table: Full context 87.5±2.0, **AC3-Reset 100.0±0.0**, **Gated-Reset 99.1±1.2** | **CORRECTED — the largest numeric change in v5** | **F28**. Those were FN-*adjusted*. Source rows: `EXP/exp1_results.txt` (rep1: reset "100.00% (39/39) [1 excluded]"), `EXP/exp1_reps_results.txt` (rep2 "Accuracy 95.00% (38/40)" vs adjusted 100.00% (38/38) [2 excluded]; rep3 raw 87.50% vs adjusted 100.00% [5 excluded]). Baseline had **0** exclusions in all three runs | Raw: Full context **87.5 +/- 2.0** (90.0/87.5/85.0), **AC3-Reset 93.3 +/- 4.2** (97.5/95.0/87.5), **AC3-Gated-Reset 95.0 +/- 0.0**; plus an explicit self-correction paragraph |
| 1.10 | "Both operators improve over the baseline in every one of the three reruns" | **unchanged in substance**, wording fixed | holds on raw: Reset +7.5/+7.5/+2.5, Gated +5.0/+7.5/+10.0 | "…in every one of the three **runs**", with per-run deltas shown |
| 1.11 | "not an artifact of … replay, or a **single seed**" | **corrected** (wording) | **F4** — `cfg.seed` is inert on LiC; replicates varied by temperature-1.0 sampling only | "…or a **single run**", plus a new paragraph stating that LiC/CollabLLM intervals estimate **decoder variance** |
| 1.12 | *(new)* | **newly added** | **F28**, `AR/tasks/T1/RESULTS.md` (adjusted-vs-raw columns), `AR/tasks/T1/fn_rejudge.json`, `AR/tasks/T14/worklog.md` §1 (file:line mechanism) | New CW2 paragraph disclosing the FN-adjustment bias (9% vs 62% exclusion; 89.0% → 77.1%) and committing to raw reporting |
| 1.13 | CW4 tau2 table (FC 68.4/31.6/26.3; AO 0/0/0; best AC3 84.2/57.9/73.7) | **struck / corrected against us (T28)** | **T6 landed.** N=3 over the full published matrix, 855 scored rollouts: FC 68.4±13.9 / **70.2±11.0** (published 31.6) / **78.9±0.0** (published 26.3); AO 0.0 everywhere; best AC3 arm below the re-measured baseline on all three models. Controls: gpt-5.4 FC and AO both reproduce published values exactly — `AR/tasks/T6/worklog.md` | Table **replaced** by the N=3 matrix and the **tau2 improvement claim withdrawn**; the AO = 0% structural result kept and carried on its own. See §12 |
| 1.14 | "Assistant omission collapses to 0% on every model" | **unchanged, and strengthened** | T6 positive control #2: AO rollouts terminate on `max_steps`, never `user_stop`, while the other four arms return reward 1.0 in the same process — `AR/tasks/T6/worklog.md` 13:58 | Promoted to carry CW4 on its own, with the mechanism stated |
| 1.15 | Kimi footnote: "rate-limit-clipped, so we quote a conservative **+24 to +34pp**" | **struck** | **T6 interim**: the whole Kimi baseline cell is a clipped floor; re-measured 80.4 is above every published Kimi AC3 number. A "conservative" range off a broken control is not conservative | removed |
| 1.16 | "only **1 of 11** baseline failures on gpt-5-mini attributable to context pollution" | **CORRECTED — softened** (T21, from T20/§7 U4) | **F56**. Number traced to `~/ac3/tau2_ctxe/ctx_edit/EXPERIMENT_LOG.md` commit `169b044`, but the 20 traces and any labels file are **unrecoverable**, the labelling had no rubric and no second annotator, and it is the 45.0% trial while the table reports best-of-3 | "1 of 11" dropped. Now: the baseline failures were **dominated by missing domain knowledge and step-budget exhaustion**, with a single repetitive-loop case; stated explicitly as a qualitative reading of one trial rather than a rubric-based annotation, with a proper taxonomy promised for the camera-ready |
| 1.17 | tau2 "confirms the rule: lightest operator wins on the strongest model, heaviest on the weakest" | **struck; the strike is now permanent (T28)** | derived from the same N=1 cells **T6 re-measured at N=3, and T6 refuted them** (F78/F79): two of three published baselines did not replicate, and on all three models the re-measured baseline is at or above every AC3 arm. The positive controls reproduced, so this is "the published baselines were wrong", not "not comparable" | removed; **gone for good**, not pending (§12.3); replaced by the analyzer-sweep evidence (F21/F22) as the CW1 generality argument |
| 1.18 | CW5: "**We are adding** a condensation baseline at matched compute … our prediction is …" | **replaced by results** | **F27**, `AR/tasks/T1/RESULTS.md`, `AR/tasks/T1/analyze.py`, `OUT/T1/main/*` | Full 10-row accuracy table, head-to-head paired deltas, measured budgets, MT-OSC engagement rate |
| 1.19 | CW5 baseline-justification prose (pollution vs. length pressure) | **unchanged** | — | verbatim, now followed by the measurement |
| 1.20 | *(new)* | **newly added** | **F27**, `AR/tasks/T1/RESULTS.md` "Measured budget" table (from `utils/call_meter.py`) | Budget-matched summariser **over-consumed** AC3-Reset: 1.02–1.19x strategy calls, 1.62–2.14x strategy tokens, still lost by 12–28pp; Gated-Reset +17.8pp on **0.41x** Reset's calls |
| 1.21 | *(new)* | **newly added** | **F27** + PROVENANCE dead-ends table | MT-OSC at w=4 fires **0.3x/conversation** on 4.1-turn conversations → *structurally inapplicable*, reported as a scoping result, **not** as a beaten baseline |
| 1.22 | *(new)* | **newly added** | **F21/F22**, `AR/tasks/T9/worklog.md` §pooled table, `OUT/T9/{rep1,rep2}/` | CW1 now cites the five-analyzer sweep (+12.9 to +39.9pp, all significant, none below baseline) as the empirical form of "the analyzer is the shared component" |
| 1.23 | *(new — added by T19)* | **newly added — disclosure that moves against us** | **F42/F43/F44/F47/F48/F49**; `AR/tasks/T17/RESULTS.md` §1–§2 (mechanism at `replay.py:21-56`, `run_experiment.py:441-470`; Overleaf commit `d856247` as ground truth), `AR/tasks/T18/worklog.md` R1/R4, `AR/tasks/T18/{ergo_row_closed.json,close_bound.py}` | Three new paragraphs in **CW5**, placed after the baseline-justification paragraph and before the condensation results: (i) the concession — ERGO alone was scored on unfiltered pools, n=23/25/25/25 vs 20/19/25/23; (ii) the measured correction — **math 69.6 → 80.0** (above AC3-Reset 75.0, level with AC3-Gated-Reset 80.0), code ≈44.0, database 12.0 untouched, actions **unclosable** and printed as an interval; (iii) the frame — **no ERGO-vs-AC3 difference is significant at n≈20 in either direction** (code p=0.375, math p=1.00), true of the published table too. CW5's Revision line extended with the table fix |
| 1.24 | Preamble: "every LiC figure is provisional pending T14" | **resolved (T19)** | **F40/F41/F42**, `AR/tasks/T14/RESULTS.md` | Provisional flag **lifted**. `tab:main`'s 20/19/25/23 come from an arm-symmetric **pool-level pre-filter** which is correct and to be **defended**; only per-run `adjusted_accuracy` is invalid, and this reply set never quotes it. Reset/Gated-Reset beat baseline in all 8 cells under raw, shipped-adjusted and corrected alike. Two flips occur on **Rewrite** (code +46.0 → −5.3, actions +22.4 → −1.5), neither a published error |

---

## 2. `01_reviewer_iNYK.md`

| # | Claim as written in v4 | Status | Evidence | New wording in v5 |
|---|---|---|---|---|
| 2.1 | W1 database replication 49.0 / 56.2 / 55.1 vs oracle 45.6 / 27.9 / 30.6 | **unchanged** | `RPT/post_neurips_ac3_phase{1,2}.md` (raw) | verbatim, labelled "(raw accuracy)" |
| 2.2 | *(new)* | **newly added** | **F10**, `AR/tasks/T2c/RESULTS.md` Table 2 | Database gain survives leak-free: 1/147 verified leaks; **+26.0pp** on n=146, p < 0.0001 |
| 2.3 | W2 cross-reference quoting **AC3-Reset 100.0 +/- 0.0** | **corrected** | as 1.9 | "**AC3-Reset 93.3 +/- 4.2**, with Reset ahead in every run" |
| 2.4 | W3 tau2 defence | **HOLD → resolved (T28); the improvement claim is withdrawn** + **newly added concession** | **T6**, `AR/tasks/T6/worklog.md` 14:38 | New: at n=19, binomial sd ≈ **10.7pp**, our N=3 Baseline re-measurement spreads **±13.9pp**; "several of the differences we reported at N=1 are inside that". Magnitudes **not** held — `01` W3 now reports the two non-replicating baselines and the withdrawal (§12.3) |
| 2.5 | W3 "~20% per-turn cost … Gated-Reset is deployment-relevant" | **corrected** (upgraded from assertion to measurement) | **F27** budget table | AC3-Reset 6.2 strategy calls/conv, Gated-Reset 2.6 = **0.41x** for +17.8pp vs +19.6pp |
| 2.6 | Q1 end-to-end table | **corrected** | as 1.9 | raw table + per-run values + explicit FN-adjustment correction paragraph |
| 2.7 | Q1 "By your stated criterion, the generalization claim stands." | **unchanged**, with a new limits paragraph | — | kept; followed by "at n=40 the per-run margins are two to four problems and this experiment on its own is not powered for significance" |
| 2.8 | Q2 paired table | **unchanged** | `EXP/paired_analysis_results.txt` | verbatim |
| 2.9 | Q2 "mean ± std over the three **seeds**" (in our own answer text) | **corrected** (wording) | **F4** | reviewer's quote kept verbatim; our answer adds a paragraph distinguishing LiC/CollabLLM **replicate runs (temperature 1.0)** from WildChat **seeds** |
| 2.10 | *(new — added by T19)* | **newly added — disclosure** | **F43/F44/F48/F49**, `AR/tasks/T18/worklog.md` R1/R4 | New closing paragraph in the **W1** answer. Chosen deliberately: iNYK's W1 *is* the small-samples/noise complaint, so the ERGO disclosure lands there as his point being vindicated rather than as an unprompted confession. Gives math 69.6 → 80.0, code ≈44.0, and the n≈20 non-significance result, then cross-references CW5 |

---

## 3. `02_reviewer_Vg97.md`

| # | Claim as written in v4 | Status | Evidence | New wording in v5 |
|---|---|---|---|---|
| 3.1 | W1/Q1 "**We are adding** a condensation baseline … will report the result either way" | **replaced by results** | **F27** | Three-part answer: summarisation loses, budget over-consumed, MT-OSC structurally inapplicable |
| 3.2 | W2 cross-reference to tau2 | **HOLD → resolved (T28)** + **newly added concession** | **T6** | Adds the 10.7pp noise-floor concession; `02` W2 now also carries the withdrawal itself (§12.3) |
| 3.3 | Q2 WildChat 89.8 / 92.1 | **corrected** | **F31** | 87.8 +/- 2.1 / 91.2 +/- 2.1 + judge-agreement summary |
| 3.4 | Q2 "tau2 … per-model results against baseline rather than best-of-3" | **corrected** (wording) | **T6** | "mean +/- std over three replicates per cell" |
| 3.5 | *(new)* | **newly added** | **F28** | Proactive disclosure of the FN-adjustment bias in the Q2 answer |
| 3.6 | Q3 "our strongest evidence is already in the paper" — Table 5 contagious pollution refutes the extra-compute hypothesis | **unchanged** | paper Table 5 | verbatim |
| 3.7 | Q3 self-reflection control "97.5 vs AC3-Reset 97.5 vs full context 90.0"; "**We are re-running** the same control on high-pollution tasks" | **promise fulfilled**; numbers **unchanged** and now labelled raw/N=1 | `EXP/exp2_results.txt` (reflection 97.5), `EXP/exp1_results.txt` (reset 39/40 = 97.5 raw, baseline 36/40 = 90.0 raw) | Retained as the non-discriminating near-ceiling control, then superseded by the T1 high-pollution result. *(Note: v4 was internally inconsistent — 100.0 in CW3 vs 97.5 here for the same run. v5 is consistent at raw.)* |
| 3.8 | Q3 latency "**13% wall-clock** (231s vs 205s for 40 conversations)" | **unchanged** | `EXP/exp1_results.txt` / `EXP/exp2_results.txt` wallclock fields | verbatim, plus measured per-conversation strategy-call counts from **F27** |
| 3.9 | *(new)* Q3 analyzer-model sensitivity — **v4 never answered this half of the question** | **newly added** | **F20/F21/F22**, `AR/tasks/T9/worklog.md` (commit `1f4f32d`), `OUT/T9/{rep1,rep2}/<task>_<arm>/` | Five-analyzer table (Kimi +39.9 / DSV4F +28.7 / gpt-5.4-mini +27.0 / Llama-70B +18.0 / gpt-4o-mini +12.9), n=178 matched pairs, exact McNemar; the under-detect-not-mis-detect mechanism; the non-OpenAI point; stated limits |
| 3.10 | Q4 component table | **unchanged** | — | verbatim |
| 3.11 | *(new)* | **newly added, then REVISED by T25** | **F25** + **F66**, `AR/tasks/T2A/RESULTS.md`, `AR/tasks/T2B/RESULTS.md` §4 | Q4 now carries the *corrected* operator-level statement. T19 wrote "Rewrite is the selective operator (27.0 / 38.9)"; **T2B retracts that** — on natural spans Reset keeps 5/66 and Rewrite keeps **0/66**, preservation 0% for both, edit precision 63.6% = base rate for both. Q4 now says the mechanism is the **same for both operators** (detect → discard the assistant side → rebuild from the user side) and that they differ in *how much* they rebuild, which keeps the operator a knob rather than a second method |
| 3.12 | *(new — added by T19)* | **newly added — disclosure** | **F43/F44/F48/F49**, `AR/tasks/T18/worklog.md` R1/R4 | New paragraph in the **W1** answer. Vg97's central weakness is the *baseline set*, so a defect in how an existing baseline was scored belongs there. Same three numbers plus the n≈20 non-significance result, explicitly tied back to Vg97's own W2 statistical-reliability point; cross-references CW5 |

---

## 4. `03_reviewer_5YHP.md`

| # | Claim as written in v4 | Status | Evidence | New wording in v5 |
|---|---|---|---|---|
| 4.1 | W1 scope defence (structural exclusion is the scope, not a gap; Table 5; Appendix D) | **unchanged** | — | verbatim |
| 4.2 | *(new)* | **newly added — the strongest new mechanism evidence** | **F10**, `AR/tasks/T2c/RESULTS.md`, `AR/tasks/T2c/{answer_check.jsonl,math_numeric_probe.json,leak_labels_final.jsonl}`; source traces `~/ac3/recovered_t2c/ctx_editor/outputs/post_neurips_ac3_phase1/` | Auditing-vs-re-solving table: leak rates under the primary `leak_final` union label (code 0%, database 1%, actions 2%, **math 47%**, pooled 17%) and leak-free gains (code **+30.2**, database **+26.0**, pooled **+20.7 [+14.8, +25.3] p<0.0001**). **Math corrected 38% → 47% by T32**: 38% was the answer-verification component alone and did not reconcile with the printed n=77 subset |
| 4.3 | *(new)* | **newly added — concession** | **F10** | **Math conceded outright**: leak-free gain **−2.6pp** (n=77, p=0.815); math's entire +9.7pp sits on the leaking subset. Conceded in the same paragraph, before the wins |
| 4.4 | W1 "On tau2-bench … blanket omission scores 0% on all three models **while AC3 beats full context on all three**" | **half struck; the struck half is now permanent (T28)** | AO=0% corroborated by T6 PC2; the AC3 half depended on the contested cells and **T6 refuted it** | Keeps AO=0% with the mechanism; "AC3 beats full context on all three" is **gone for good**, not pending (§12.3) |
| 4.5 | W1 "On WildChat, AC3 wins **72-92%** of pairwise comparisons" | **corrected, then partly restored** | **F31**, **F53** | The *headline* is the order-balanced pooled figure (87.8 / 91.2). The 72–92% per-cell range is **verified** (T20: all 22 populated `tab:wildchat` cells re-derived, 22/22 exact; min 71.6, max 91.5) and T21 restored it to `03` W1 as a **separate bullet** describing the spread across configurations — never as the win-rate claim, and never in the same sentence as the pooled headline (see §7 U3) |
| 4.6 | W3 end-to-end numbers 87.5 / 100.0 / 99.1 | **corrected** | as 1.9 | raw 87.5 / 93.3 / 95.0 + self-correction sentence |
| 4.7 | W3 replay-is-causal defence | **unchanged** | — | verbatim |
| 4.8 | W4 CollabLLM table: MATH-Hard 95 / 90 / **100 (Augment)** | **CORRECTED — claim struck** | **F16**, `AR/tasks/T8/worklog.md` §6, §8; `OUT/T8/*` | N=3: Full context **91.7 ± 5.8**, AC3-Augment **91.7 ± 7.6** — **exactly tied**, identical 55/60 per-problem totals, per-replicate delta 0.0 ± 8.7. v5 says AC3-Augment **matches** Baseline: refutes the regression, claims no improvement |
| 4.9 | W4 CollabLLM BigCodeBench 5 / 15 / **20 (Reset)** | **corrected — strengthened** | **F17/F18**, `AR/tasks/T8/worklog.md` §6, §9; `OUT/T8/seed1234_{reset,baseline}_bigcodebench` | N=3: Reset **21.7 ± 5.8** vs Baseline **6.7 ± 5.8**, +15pp in 3/3 replicates, 9 problems solved that Baseline never solves, and it reproduces on a **fully disjoint** draw (3/20 vs 1/20). Quoted as "≈1 in 5, ±1 problem" |
| 4.10 | W4 AO cells (90 MATH-Hard, 15 BigCodeBench) | **CORRECTED — now N=3** (T21) | **F54**; `AR/tasks/T21/worklog.md`, `OUT/T21/*`; rep1 recovered, reps 2–3 fresh under T8's exact config | MATH-Hard **88.3 ± 2.9** (18/17/18) and BigCodeBench **18.3 ± 5.8** (3/3/5, re-scored). Dagger footnote **removed** — the column is no longer single-run. The BigCodeBench move narrows AC3-Reset's margin over AO from +6.7pp to **+3.3pp**, which the reply now reports as a second self-reported correction and declines to claim as an ordering. See §10 |
| 4.11 | W4 "executable tests are unavailable because the simulator does not transmit the required function signatures, which is a property of the benchmark harness" | **STRUCK — factually wrong** | **F18** / `AR/tasks/T8/worklog.md` §5: the CollabLLM BigCodeBench path is `eval_method: pass_rate` → `judge_pass_rate` → `bigcodebench.eval.untrusted_check`, i.e. **real test execution**. (This also corrects RECON Unknown #7) | Replaced with a correction *in the reviewer's favour*: the numbers **are** execution-based pass rates, but they are library-version sensitive; every cell re-scored offline in one unified environment with a canonical-solution pre-flight (19/20) |
| 4.12 | W4 "the judge discriminates sharply … v8-Rewrite 17.6% vs Reset 0% on gpt-5.4; 16.7% vs 0% on Kimi-K2.6" | **struck** | moot once scoring is execution-based (4.11); also not re-verified tonight (see §7 U1) | removed |
| 4.13 | W4 "**We will add** judge-agreement and position-bias checks for WildChat" | **replaced by results** | **F30/F31/F32/F33**, `AR/tasks/T11/worklog.md` §(a)–(d), `AR/tasks/T11/out/*.jsonl` | Position bias (+5.5pp toward slot 2, p=1.8e-4, opposite-signed on the other two judges); corrected headline; PABAK 0.79–0.83 / AC1 0.84–0.87; self-consistency 96.9%; punitive 2-of-3 rule 82.5%; positive controls 39/40, 36/40, 40/40 |
| 4.14 | *(new)* | **newly added — disclosure** | **F33** | "our judge does not run at temperature 0 … the provider overrides it to 1.0. The 96.9% self-consistency figure replaces any determinism claim" |
| 4.15 | W5 "**We are adding** a span-level evaluation … removal recall / preservation precision / gating accuracy … as a confusion matrix" | **replaced by results** | **F23/F24/F26**, `AR/tasks/T2A/RESULTS.md`, `AR/tasks/T2A/{inject.py,measure.py,manifest.jsonl,per_conversation.json}`, `OUT/T2A/` (32 cells), commit `88cacb3` | Full judge-free constructed-pollution study with the two-span design and four offline positive controls |
| 4.16 | *(new)* | **newly added — correction to a paper claim; RE-CORRECTED by T25** | **F25**, D9, superseded by **F66** / `AR/tasks/T2B/RESULTS.md` §4 | v5 as written by T15/T19 **re-attributed** "we preserve what's correct and remove what's harmful" to **Rewrite** (27.0 / 38.9) on the strength of the *constructed*-span study. **T2B measured the same thing on naturally occurring spans, causally, with no detector or judge in the label path, and the attribution does not survive**: Reset keeps 5/66 probe-admissible spans, **Rewrite keeps 0/66**, preservation on causally useful spans is 0% for both, and edit precision is 63.6% — exactly the base rate — for both. The label-free aggregate test agrees (Reset removed−kept = −0.014, p = 0.85). **The claim is now retracted for both operators, not re-attributed.** Explanation shipped alongside it, because it makes T2B an *extension* of T2A rather than a contradiction: a compactor can copy a short self-contained injected sentence verbatim, but paraphrases the model's own verbose prose and code, so nothing distinctive survives. T2A flagged synthetic salience as an upper-bound caveat and the caveat was load-bearing |
| 4.17 | *(new)* | **newly added** | **F24**, `AR/tasks/T2A/RESULTS.md` §factorial | Detector-free causal ladder: harmful span **−11.1pp** on unedited context, true span **+15.1pp**; clean 24.7% → polluted 9.3% → AC3-Reset with pollutant present **59.8%** |
| 4.18 | W5 gate-open rates **97.3%** LiC (n=554), **98.3%** CollabLLM (n=119), ~72% WildChat | **corrected (T16), and U1 retired** | **F39**, `AR/tasks/T16/{report.md,gate_stats.py,gate_stats.json}`; the 2026-06 artifacts U1 could not find **do exist**, at `scripts/analysis_rewrite_v_reset/data/gated_reset_reconstructed_{lic,collabllm}.md`, stating `539/554 (97.3%)` and `117/119 (98.3%)` verbatim | Both figures reproduce to the digit; the *labelling* was wrong. Now: LiC **97.3% per-conversation** (98.5% turn-level, n=547) and CollabLLM **95.3% turn-level** (n=659 calls over 120 conversations; 98.3% per-conversation) |
| 4.18a | *(new — added by T19)* | **newly added — self-stated limitation** | **F39** (T16's new caveat), `AR/tasks/T16/report.md` | New paragraph after the gate rates: they are a **firing rate, not a detection rate** — 29% (LiC) / 73% (CollabLLM) of gate-open records have the analyzer writing `issues: "None"` while still setting `needs_edit=true`. Names it before a reviewer handed `gate_stats.py` would; redirects the detection claim to T2A's 78.6% pollutant-naming rate. The existing "we would not over-read firing rates into a precision/recall claim" sentence is kept and now has evidence behind it |
| 4.19 | W5 "on WildChat with gpt-5.4 [always-on Reset] **outperforms Gated-Reset by 14.5pp (88.6 vs. 74.1)**" | **struck** | not re-judged under order balancing; **F30** shows single-cell judge numbers carry a ±2pp order effect. Superseded by direct T2A evidence | removed; the "spurious edits are not harmful" argument now rests on the 33/36 paired-win record plus T2A |
| 4.20 | W5 "We would not want to over-read this into a precision/recall claim" | **unchanged** | D9 guardrail | verbatim |
| 4.21 | W6 "memory is an **optional, ablated component**; every main result holds without it" | **unchanged** | — | verbatim |
| 4.22 | *(new)* | **newly added — answers W6 with the strong half** | **F13**, `AR/tasks/T12-T13/worklog.md` §9; `OUT/T12_T13/{database,math}/*` | Contamination is measurably zero: **0/120** exact and near-duplicates vs `data/lic_eval_subset.json`; 11/98 (11.2%) overlap with the dev subsets where memory is **equal or worse**; within-instance transductive probe **0.0pp** on both tasks |
| 4.23 | *(new)* | **newly added — self-stated limitation** | **F12**, D7, PROVENANCE dead-ends | Learner variance ~6pp (across-ordering 6.5 vs same-ordering control 6.1 vs eval-only control 3.8); the paper's **+10 / +12pp are single trials below that floor**; N=4 remeasure on gpt-5.4-mini gives −5.0 / −8.0pp; commit to re-run at N ≥ 4 or soften |
| 4.24 | *(never in v4)* "memory is order-robust" | **not used** | **F12** retired this framing before it was ever written into a reply | n/a — recorded so it is not reintroduced |
| 4.25 | W6 "your diagnosis is a satisfying consistency check on our own thesis" | **unchanged** | — | verbatim, now with the cheatsheet-overlap number (Jaccard 0.29–0.32) behind it |

---

## 5. `04_response_to_AC.md`

| # | Claim as written in v4 | Status | Evidence | New wording in v5 |
|---|---|---|---|---|
| 5.1 | "Validity of theoretical assumptions" reading + empirical-not-formal argument | **unchanged** | — | verbatim, plus the auditing-vs-re-solving evidence and the math concession |
| 5.2 | Generalizability paragraph incl. "tau2 confirms the rule directly" | **corrected** | as 1.17 | tau2 rule removed; replaced by the five-analyzer, four-family sweep |
| 5.3 | Evidence table row "New unbiased … **AC3-Reset 100.0 +/- 0.0**" | **corrected** | as 1.9 | raw values |
| 5.4 | Evidence table row "Corrected tau2 reporting: AO 0% on every model; best AC3 beats full context on every model" | **half struck / HOLD → resolved (T28)** | as 1.13 / 4.4 | Row was removed pending T6; **T28 restored a tau2 row to the evidence table** reporting the re-run and the withdrawal ("Against us…"), with AO = 0% carried in the body |
| 5.5 | "MATH-Hard 100 vs 95 and 90; BigCodeBench 20 vs 5 and 15" | **corrected** | as 4.8 / 4.9 | replaced by the N=3 correction, listed as self-correction #1 |
| 5.6 | *(new)* | **newly added** | F16, F28, F25, F31, F12, T8 §5 | A numbered "corrections we are making to our own numbers" list, made part of the tractability argument. T15 wrote 4 items here and 6 in `05_final_remarks.md`; after T19 (ERGO) and T28 (tau2) the lists stand at **6 in `04` and 8 in `05`** — `04` carries the six most consequential, `05` all eight |
| 5.7 | *(new)* | **newly added** | F27 | Evidence-table rows for the condensation baseline, MT-OSC engagement rate, analyzer sensitivity, detector evaluation, WildChat judge audit |
| 5.8 | Closing tractability argument | **unchanged**, extended | — | adds: "the corrections listed above are the discussion period working as intended … every one was found by us" |
| 5.9 | *(new — added by T19)* | **newly added — disclosure** | **F42/F43/F44/F47/F48/F49**, `AR/tasks/T17/RESULTS.md`, `AR/tasks/T18/worklog.md` R1/R4 | Numbered correction **5** added to the "corrections we are making" list, and the lead-in changed from "four corrections" to "five", with the fifth explicitly labelled as moving against us by *raising a baseline*. Carries math 69.6 → 80.0, code ≈44.0, database untouched, actions unclosable, and the n≈20 non-significance result. Closes on why we would rather state it: it is recoverable from our own printed percentages |
| 5.10 | Placement relative to the T6 HOLD block | **bookkeeping (T19); discharged (T28)** | — | The T6 HOLD block was left **byte-identical** by T19 and T25 and still referred to the pending tau2 withdrawal as "a fifth correction"; a separate `⚠ INTERNAL — T19 renumbering note` recorded that tau2 becomes item **6**. **T28 removed both**, and tau2 is item **6** in `04` as predicted. Nothing on hold remains |

---

## 6. `05_final_remarks.md`

Mirrors the above. All ten revision bullets updated to the corrected numbers; four bullets converted from promise to result (condensation, detector, judge audit, memory split); three bullets added (auditing-vs-re-solving, analyzer sensitivity, memory variance); one new section added listing the six self-corrections; one `⚠ INTERNAL` HOLD note for a possible seventh (tau2). *(As written by T15. The list is now **eight** items — T19 added ERGO as item 7, T28 added the tau2 withdrawal as item 8 and removed the HOLD note; see §12.3.)*

**T19 additions.** A **seventh** numbered correction added for the ERGO denominator defect (**F43/F44/F48/F49**; `AR/tasks/T18/worklog.md` R1/R4): math 69.6 → 80.0 above AC3-Reset's 75.0 and level with AC3-Gated-Reset's 80.0, code ≈44.0, database 12.0 untouched, actions unclosable and printed as an interval, closing on the n≈20 non-significance result. The condensation-baseline revision bullet gained a closing sentence pointing at it. As in `04`, the T6 HOLD block was left **byte-identical** by T19 — it still said the tau2 withdrawal would be "a seventh item", and a separate `⚠ INTERNAL — T19 renumbering note` after it recorded that tau2 becomes item **8**. **T28 removed both and tau2 is item 8**, exactly as predicted.

---

## 7. Claims that could not be verified when v5 was written — status after T16/T19/T20/T21

**Originally a liability list; it is now mostly a clearance record.** U1 was retired by T16/T19. **T20 then resolved all four of U2–U5, and T21 applied its wordings and closed U5's remaining N=1.** Every row is kept, struck where retired, so the record of each alarm — true or false — survives.

**Current state: U1 and U3 retired (verified, in use); U2 verified but deliberately kept struck; U4 softened; U5 verified and now replicated at N=3. U6 is the only live liability.**

| ID | Claim | Where it appears | Why it was unverified / what was found | Recommendation |
|---|---|---|---|---|
| ~~**U1**~~ | ~~Gate-open rate **97.3%** on LiC (n=554) and **98.3%** on CollabLLM (n=119)~~ | v5 `03_reviewer_5YHP.md`, W5 | **RETIRED (T19, from F39).** U1 was a false alarm about provenance. The 2026-06 artifacts **do exist in-repo**, at `scripts/analysis_rewrite_v_reset/data/gated_reset_reconstructed_{lic,collabllm}.md`, stating `539/554 (97.3%)` and `117/119 (98.3%)` verbatim; the T15 audit simply missed them. T16 then re-derived both **independently from raw traces** with zero API calls (`AR/tasks/T16/gate_stats.py`), matching to the digit, with an independent regex parser agreeing across all 3,179 fields and 0/1,197 disagreements against `edit_decision.should_edit` | **No action.** The reply now reports LiC 97.3% per-conversation / 98.5% turn-level and CollabLLM 95.3% turn-level / 98.3% per-conversation (claim 4.18), and states the firing-rate-vs-detection-rate caveat itself (claim 4.18a) |
| **U2** | WildChat gpt-5.4: Reset **88.6** vs Gated-Reset **74.1** (−14.5pp) | struck from v5 | **RESOLVED (T20) — the numbers are real but the claim is not supportable.** Both cells reproduce to the digit from `~/ac3/recovered/ctx_editor/outputs/post_may26_wildchat_gpt54/{s15,s2}_gpt5_4_seed42_1779830054/turn_results.jsonl` (39/44 and 43/58; `AR/tasks/T20/recompute_u2.py`, positive control: all four published gpt-5.4 cells reproduce exactly). But (i) the two arms were scored on **different pools** — 44 vs 58 turns, only 35 shared — so the paper's Table 3 caption claim "on the same prefixes" is wrong; (ii) on the matched 35-turn pool the gap survives at 88.6 vs 74.3 (**+14.3pp**), so the substance is fine, but (iii) it rests on **seven discordant turns** (6 vs 1), exact McNemar **p = 0.125** — not significant, at N=1 seed 42, un-order-balanced | **Keep struck. Do not reintroduce.** Not because it is unverified — it is verified — but because it is a 14pp headline resting on a 6-vs-1 split of seven turns. **The reason to give, if asked, is non-significance, not "not order-balanced"** — the latter invites "so re-judge it", and re-judging 35 turns cannot manufacture significance out of seven discordant ones. Separately: **fix the Table 3 caption** for the arXiv version — queued as **PAPER-8** (paper action, not rebuttal action; see below) |
| ~~**U3**~~ | ~~WildChat per-cell range **72–92%**~~ | **restored to v5** reviewer text (`03_reviewer_5YHP.md` W1) by T21, with the label below | **RETIRED (T20).** Verified, not unverifiable. The range is the rounded envelope of the 22 populated cells of `tab:wildchat` (min 71.6 = Kimi/Reset vs AO n=74; max 91.5 = Kimi/Rewrite vs AO n=59), an edit adopted deliberately at `docs/arxiv_push/arxiv_revision_plan.md:70` (H2). **All 22 cells were re-derived from per-turn judge verdicts and all 22 reproduce to the digit** (`AR/tasks/T20/recompute_u3.py`). T11's corrections touch **none** of them: T11 corrected the Phase-3b *pooled* figures (89.8→87.8, 92.1→91.2), which do not appear in Table 3 — Table 3's gpt-5-mini column is the original Phase-2 run and its Reset cell is 83.0 | **Safe to use, with a label.** Say "every cell of our per-respondent table lands between 72% and 92%", never "AC3 wins 72–92%" — it is a min/max over 22 single-run cells (binomial sd 3.6–5.2pp at the endpoints, plus ±2pp order variance per F30), so it is an order statistic, not an effect range. Still do not put it in the **same sentence** as the corrected 87.8/91.2 headline: different pools, different quantity. **Applied by T21** as its own bullet in `03` W1 |
| **U4** | tau2 gpt-5-mini: "only **1 of 11** baseline failures attributable to context pollution" | v5 `00_general_response.md` CW4, `01_reviewer_iNYK.md` W3 | **RESOLVED (T20) — number traceable, evidence unrecoverable.** Source found: `~/ac3/tau2_ctxe/ctx_edit/EXPERIMENT_LOG.md` §"Diagnostic: Failure Mode Analysis (2026-03-25)", commit `169b044` (2026-03-24), whose five-row table is verbatim identical to the paper's `tab:tau2-failure-modes`. Arithmetic checks out: Exp 4 scored S0 9/20 = 45%, so 11 failures is right *for that trial*. But the 20 traces are **gone** — never tracked in `tau2_ctxe` git, absent from the 69,738-entry `snapshot.tar.gz`, absent from `supplementary.tar.gz`, absent from disk — and **no labels file or rubric has ever existed**; the labelling is one author's qualitative reading with no second annotator. Two further defects: it is the **45.0% trial**, the *worst* of the three gpt-5-mini trials {45.0, 55.0, 60.0}, while the table reports **best-of-3**, so 11 failures does not reconcile with the reported cell; and n is ambiguous (Exp 4 used 20 tasks, the published sweep uses 19). **Decoupled from T6**, which re-measures gpt-5.4/DSV4F/Kimi only — gpt-5-mini appears in T6 solely as user-sim and analyzer | **SOFTENED — "1 of 11" dropped, substance kept. APPLIED by T21** to both `00_general_response.md` CW4 and `01_reviewer_iNYK.md` W3 (T20's drop-in wordings, `AR/tasks/T20/worklog.md` §U4). Both now say the failures were dominated by missing domain knowledge and step-budget exhaustion with a single repetitive-loop case, and both state plainly that this was a qualitative reading of one trial's traces rather than a rubric-based annotation, with re-derivation deferred to the camera-ready (published rubric, second annotator, all trials). Re-deriving it now costs ~20 rollouts (~$0.6) *plus* a hand-labelling pass that cannot be made defensible overnight |
| **U5** | CollabLLM assistant-omission cells (MATH-Hard 90, BigCodeBench 15) | v5 `03_reviewer_5YHP.md` W4 table | **RESOLVED (T20) — verified and strengthened.** Both cells reproduce exactly from `~/ac3/recovered/ctx_editor/outputs/post_neurips_r2_collabllm_user_deepseek/collabllm_assistant_omit_{math-hard,bigcodebench}_rep1_1779092497/metrics.json` (18/20 and 3/20). **New:** T8 re-scored every *other* bigcodebench cell in that table row under a unified dependency environment (which moved Baseline rep1 1→2 and Reset rep1 4→5) but **never re-scored the AO cell** — so the row mixed scoring environments and nobody had checked. T20 re-scored it offline, zero API calls, positive controls reproducing T8's 5/20 and 2/20: **AO is unchanged at 3/20 = 15.0**, so the row *is* internally comparable. AC3-Augment bigcodebench rep1 likewise unchanged at 3/20. **T21 re-ran all three positive controls independently and reproduced 5/20, 2/20 and 3/20 exactly before running anything new** | **N=1 CLOSED by T21 — the column is now N=3.** See §10 |

**New liability introduced by T19 (U6).** The ERGO/actions cell **cannot be corrected and never will be** without an artifact that has never existed. `AR/tasks/T17/RESULTS.md` §1a establishes that no `actions_false_negatives.json` appears in git history, in the 69,738-entry `snapshot.tar.gz` index, or on disk, and no document names the 2 items dropped by the ad-hoc "common-23" normalisation, so there is no pruned set to replay. The reply text therefore promises an **interval**, not a point estimate. Do not let that promise drift into a number.

**New paper-side action from T20 (PAPER-8) — the Table 3 caption is false as written.** `writing/overleaf_repo/neurips/neurips_2026_conference.tex:299` describes the \mgpt~Gated-Reset cell as "$-$14.5pp vs.\ always-on Reset **on the same prefixes**". The two arms were **not** scored on the same prefixes: Reset was scored on 44 turns and Gated-Reset on 58, with only **35 in common** (T20 §U2). The caption also contradicts the footnote already in `00`, `01` and `03` that each method is evaluated against its own assistant-omission failure pool. The queued replacement reads "($-$14.5pp vs.\ always-on Reset; $-$14.3pp on the 35 prefixes both arms were evaluated on, exact McNemar $p=0.125$)". **Not applied** — `writing/overleaf_repo/` is a shared repo synced to Overleaf and is out of bounds for the autoresearch agents; this is queued for the operator alongside PAPER-1..7. It is an arXiv/camera-ready item, not a rebuttal item: the claim itself is struck from the reply set, so nothing we post depends on it.

---

## 8. Cross-cutting rules applied throughout

1. **"Seeds" → "replicate runs at temperature 1.0"** wherever the number came from LiC or CollabLLM (**F4**, D4). WildChat keeps "seeds" — its N=3 are real. We state *what the replicates vary* and that the intervals are decoder variance; we do **not** confess a harness bug in a rebuttal.
2. **Raw accuracy everywhere on LiC** (**F28**). `adjusted_accuracy` is never quoted for a context-editing arm.
3. **Never a bare 97.6% removal rate** (**D9**). Always detection + removal + preservation + edit-precision-vs-chance. **Selectivity is attributed to no operator** (**F66**, T25): on natural spans Reset keeps 5/66 and Rewrite 0/66, edit precision at the base rate for both. The mechanism statement for both is *detect → discard the assistant side → rebuild the specification from the user side*. Lead the detector passages with what *is* supported: 78.6% pollutant naming, the causal factorial (9.3% → 59.8% with the pollutant still present), and T2B's 100% removal of causally-harmful natural spans.
4. **Never the single-trial memory gains** (**D7**). Lead with contamination-zero; state variance as our own limitation.
5. **Concessions open the paragraph.** Applied to the CollabLLM correction, the FN-adjustment, the preservation attribution, the WildChat headline, math in the auditing analysis, and the memory noise floor.
6. **tau2 magnitudes — RESOLVED by T6 and WITHDRAWN (T28).** All five `⚠ INTERNAL — HOLD` blocks (`00` x2, `01`, `04`, `05`) and both `⚠ INTERNAL — T19 renumbering` notes are now resolved and removed. The rule that replaces the hold: **no tau2 improvement claim on any model**, do not soften the withdrawal into "mixed results", keep the AO = 0% structural result, keep the gpt-5.4 Gated-Reset regression, and disclose the gpt-5.4 AC3 collapse as unexplained. Only `00`'s orientation preamble remains as an `⚠ INTERNAL` block.
6b. **Never quote the matrix-wide AC3-vs-AO item-level McNemar (p = 0.010) as a win** (**T27/F77**). It ignores the clustering of 1,668 items inside 191 problems and is anti-conservative here. The primary statistic is the problem-clustered bootstrap: **+2.8pp, 95% CI [−0.3, +5.9]**, which includes zero. Matrix-wide is a wash; the separation is on database, **+18.6pp [+10.7, +26.6]**. This is deliberately consistent with §11.2's assembled counter-case, which already says the same thing at cell level (+2.6pp, 15/17/4).
7. **ERGO's corrected values are math 80.0 and code ≈44.0** (**T19**, from F47/F48). T17's estimated 57.9 for code is **never** used — T18 measured the free parameter directly and shipping 57.9 would overstate a competitor by ~14pp, an error in the opposite direction and equally unacceptable. Database stays 12.0; actions is unclosable and is promised as an interval.
8. **Every ERGO passage leads with the significance frame, not an ordering** (**T19**, from F49). "No `tab:main` ERGO-vs-AC3 difference is significant at n≈20 in either direction" is stated plainly and early, before any per-cell number, and is noted to hold of the published table as well as the corrected one. We do not compensate for the correction by claiming ERGO still loses overall: the measured scorecard is 3/12 ERGO wins-or-ties, up from a published 1/12.
9. **The pool-level pre-filter is defended, not conceded** (**T19**, from F42). `tab:main`'s 20/19/25/23 denominators are arm-symmetric and correct. Only per-run `adjusted_accuracy` is invalid, and rule 2 above already excludes it. Do not let the FN-adjustment concession bleed into an admission that the denominators themselves are wrong — they are not, except on the ERGO row.

---

## 9. Resolved since T15 wrote v5 (T19 integration record)

| Audit | Landed | Outcome | What changed in `replies/v5/` |
|---|---|---|---|
| **T14** — FN-adjustment audit | 16:15 | Largely **in the paper's favour**. Pool-level pre-filter is correct and arm-symmetric; only per-run `adjusted_accuracy` is invalid, touching ≤4 `tab:main` cells at ≤1 sample each (2 of which favour prior work). Two flips, both on **AC3-Rewrite**, neither a published error. Reset and Gated-Reset win all 8 cells under raw, shipped-adjusted and corrected alike | `00` preamble item 1 rewritten from "provisional pending T14" to "resolved"; `README.md` blocker 3 likewise. **No accuracy figure moved** — v5 was already raw throughout |
| **T16** — gate statistics | 15:55 | Claim reproduces to the digit; the *labelling* was wrong, and U1's provenance alarm was false | Correction already applied to `03` by the main thread at 15:57. T19 retired **§7 U1** and added the firing-rate caveat (claim 4.18a) |
| **T17** — ERGO denominator audit | 16:20 | Defect **confirmed** against Overleaf commit `d856247`; ERGO alone on unfiltered pools. Bound too wide to publish on code | Superseded on code by T18; the mechanism, the `d856247` confirmation and the actions-column provenance gap all ship |
| **T18** — closing the bound | 17:10 | **math 80.0 CLOSED** (k=0 measured, 3 replicates) — ships. **code ≈43.9**, i.e. T17's 57.9 was ~14pp too generous to ERGO — T17's figure must **not** ship. Actions unmeasurable. F49: nothing is significant at n≈20 | The ERGO disclosure written into `00` CW5, `01` W1, `02` W1, `04` correction 5, `05` correction 7 |
| **T6** — multi-replicate tau2 | **LANDED (T28 applied it)** | **Against us.** Full published matrix at N=3 (3 models x 5 arms x 3 replicate runs x 19 tasks = **855 scored rollouts**, 15/15 cells). Two of three published baselines do **not** replicate: DSV4F 31.6 → **70.2 ± 11.0**, Kimi 26.3 → **78.9 ± 0.0**. On all three models the re-measured baseline is **at or above every AC3 arm**; AC3-Augment is significantly worse on all three. Positive controls hold (gpt-5.4 baseline 68.4 vs published 68.4; AO 0.0 in 9/9 cells, 171 rollouts; `gpt-5-mini` reachable; byte-identical invocation strings; no substitution), so this is "the published baselines were clipped floors", not "not comparable" | **The tau2 improvement claim is withdrawn.** See §12 |

### What the corrected ERGO numbers actually are, stated precisely

This matters because the reviewer-facing text must not claim more than was done. The corrected cells are **the published numerator over the corrected denominator**, with the one free parameter — *k*, how many of the pruned items ERGO was solving — **measured** by replaying ERGO against a pruned-items-only pool. math: k = 0 over three replicate runs, so 16/23 → 16/20 = **80.0**. code: k ≈ 2.67 of 6 (3, 2, 3), so 11/25 → ≈8.3/19 = **43.9** [42.1, 47.4].

**T18's own positive control did not reproduce**, and this is a real limit on what may be quoted. ERGO/database came back at 44.0 against a published 12.0 because `gpt-5-mini` (the published-era model) is unreachable — `dl-openai-3` returns 401, there is no `.env`, and TRAPI serves only `gpt-5.4-mini`/`gpt-4o`. So **no absolute accuracy level from T18's re-runs is substitutable into `tab:main` by anyone**, and none is quoted anywhere in this reply set. What survives the control failure is *k*, because *k* does not use the replication's accuracy levels: it is defended against the model gap by the observation that **full-context Baseline solves 0/6 of the pruned code items at the newer model too**, so the three solvable ones are unlocked by context cleaning rather than by the model era. That argument is strong but is not proof; the reply text says "roughly half" on code rather than quoting 43.9, which is the right level of precision to commit to in front of reviewers. Source: `AR/tasks/T18/worklog.md` §"Honest accounting".

---

## 10. T21 integration record — §7 cleared, and the CollabLLM assistant-omission column taken to N=3

T21 did two things: applied T20's drop-in wordings for U2–U5 to the reply files (§7 above
now records the outcome of each), and **ran the one experiment T20 identified as the
cheapest open item in the reply set** — the assistant-omission (AO) column of the
`03_reviewer_5YHP.md` W4 table, which was the last N=1 column in any reviewer-facing table.

### The AO column at N=3

Four fresh cells (AO x {math-hard, bigcodebench} x replicates {2, 3}), run under T8's exact
configuration so the column is comparable with the arms beside it: `model=deepseek_v4_flash_user_deepseek`,
`load_balancer=multi_endpoint_foundry`, `task.limit=20`, `execution.max_concurrent=5`. AO
runs no analyzer, so `analysis_cache_dir` is omitted for the same reason it is omitted for
Baseline. Replicate 1 is the recovered snapshot cell. **These are replicate runs at
temperature 1.0 on a fixed 20-problem draw, not seeds.** Cost ≈ $0.17, 25 min wall-clock on
two parallel streams. Artifacts: `outputs/T21/`; log `AR/tasks/T21/worklog.md`.

| Dataset | rep1 (recovered) | rep2 | rep3 | **mean ± sd** | N=1 value the reply previously quoted |
|---|---|---|---|---|---|
| MATH-Hard | 18/20 (90.0) | 17/20 (85.0) | 18/20 (90.0) | **88.3 ± 2.9** | 90.0 |
| BigCodeBench (re-scored) | 3/20 (15.0) | 3/20 (15.0) | 5/20 (25.0) | **18.3 ± 5.8** | 15.0 |

**Did the numbers move materially?** Not in absolute terms — MATH-Hard moves −1.7pp and
BigCodeBench +3.3pp, both **less than one problem** on a 20-problem draw that quantises in
5pp steps. But the BigCodeBench move **does** change a comparison the reply was making:
AC3-Reset's margin over assistant omission drops from **+6.7pp to +3.3pp**, i.e. from about
1.3 problems to 0.67, which is inside the replicate-to-replicate noise. The W4 text now
states this as a **second self-reported correction** and explicitly declines to claim that
AC3 beats assistant omission on BigCodeBench. The load-bearing claim — AC3-Reset over
**full context**, +15pp in 3 of 3 replicates — is untouched.

**Per-problem, all three bigcodebench arms over 3 replicates (60 instances each):**
AO **11/60**, AC3-Reset **13/60**, full context **4/60**. The two treatment arms succeed on
partly different problems (AO solves `228` 3/3 where Reset solves it 1/3; Reset solves `285`
and `563` 2/3 each where AO never does), which is the substantive reason not to read a
3.3pp gap as an ordering.

### Controls, because two harness bugs in this pipeline silently return 0.0

All verified **before** launching, not after:

* **Judge live.** `fxdata-shared` 401s for this identity and `multi_endpoint_foundry.yaml`
  routes `gpt-4o-mini` — the judge/extractor role — through it; T8's `gpt-4o-mini: 150`
  entry on `dl-openai-3` is still present. A 2-sample AO smoke run returned real verdicts
  (`2/2`, cost $0.0038), not the `0/0` signature of a dead judge.
* **Sandbox live.** Canonical-solution pre-flight on the seed-42 draw: **19/20 reference
  solutions pass**, the one failure being `BigCodeBench/501`, exactly reproducing T8.
  `matplotlib` present (its absence kills every test subprocess in-sandbox and is swallowed
  as 0.0 — this is how T8's first Reset rep2 read 0/20 when it was really 5/20).
* **Re-scorer reproduces known cells.** Before any new cell existed, T21 re-scored the three
  recovered rep1 bigcodebench cells offline and got **AC3-Reset 5/20, full context 2/20,
  AO 3/20** — T8's and T20's published re-scores to the item, with `BigCodeBench/451` the
  only mover in each. The final per-problem pass also reproduced T8's full N=3 grids for
  AC3-Reset (5/5/3) and full context (2/2/0) and T8's math-hard grids (20/17/18 and
  19/19/17) unchanged.
* **Every cell cross-checked** across `metrics.json`, `run_summary.json` and `results.json`;
  all agree, `total_attempted: 20` and `errors: 0` everywhere.

**One new finding, reported rather than smoothed over.** `BigCodeBench/859` trains an SVM
and asserts a minimum accuracy with no seed fixed in the test, so it is **intrinsically
stochastic**: over eight full-suite re-scoring passes of the identical stored code it passed
seven times and failed once, and 7/7 in isolation. AO rep3 is therefore reported at its
modal **5/20**, and the reply now discloses the flakiness. This is a different failure mode
from the `BigCodeBench/451` dependency-version difference T8 found — that one is
deterministic — and it is worth knowing for anyone reporting BigCodeBench at n=20, where a
single flaky problem is a full 5pp.

### Effect on the tally

**UNVERIFIED 4 → 1.** U2, U3, U4 and U5 are all resolved (U3 retired and restored to the
reviewer text, U2 verified but deliberately kept struck, U4 softened, U5 verified and now
replicated). **U6 alone remains**, and it is unclosable by construction. **Corrections
14 → 15**, the new one being the AO column, which moves *against* us in the sense that it
narrows a gap we had shown — so 7 of 15 corrections now move against us. **One paper action
added, PAPER-8** (Table 3 caption). Every INTERNAL/HOLD tau2 block in the reply files is
**unchanged and byte-identical**; T6's outcome is still unknown and nothing here touches it.
Verified two ways against the pre-T21 commit `1382e61`: `git diff 1382e61 -U0 -- replies/v5/ |
grep -E '^[-+]>'` returns **nothing** (no blockquote line anywhere in v5 was added or
removed), and the extracted HOLD blocks of `00`, `01`, `04` and `05` hash identically.

---

## 11. T25 integration record — the Rewrite retraction (T2B) and the assembled counter-case (T23 red team)

T25 did two things: it **retracted** a claim that v5 had just finished re-attributing, because
T2B's causal measurement landed and overturned it; and it **assembled** the counter-evidence to
the red team's strongest single objection, which existed but was scattered across six files.
It also applied the red-team HIGH items that need no new measurement.

### 11.1 The retraction — "we preserve what's correct and remove what's harmful"

**What v5 said before T25.** T2A injected one known-false and one known-true span per
conversation and found AC3-Reset non-selective (edit precision 50.4% against 50% chance,
preservation 4.0%) while AC3-**Rewrite** looked selective (27.0% removal, 38.9% preservation).
On that basis, five places in v5 — `02` Q4, `03` W5, `04` correction 3, `05` correction 3, and
the `README.md` guardrail — attributed the paper's selectivity claim to **Rewrite**.

**What T2B measured** (`AR/tasks/T2B/RESULTS.md`, F65–F67, commit `289de75`). 111 spans
occurring **naturally** in 30 LiC database and code conversations, each re-run **14× present and
12× removed**, everything else byte-identical (3,357 assistant turns, 0 errors). **No detector,
no judge and no LLM of any kind appears anywhere in the path that produces the labels.** All
three controls pass: contentless span **+0.033** (n.s.), T2A's validated pollutant **+0.368**,
the full-spec/gold-SQL span **−0.447**.

| | AC3-Reset | AC3-Rewrite |
|---|---|---|
| Probe-admissible spans **kept** | 5 / 66 | **0 / 66** |
| Removal on causally harmful spans | 100.0% (7/7) | 100.0% (7/7) |
| Preservation on causally useful spans | 0.0% (0/4) | 0.0% (0/4) |
| Edit precision (base rate 63.6%) | 63.6% | 63.6% |
| Label-free aggregate (removed − kept) | −0.014, p = 0.85 | not computable — kept nothing |

**Verdict: the Rewrite attribution does not survive, and it is retracted rather than moved
again.** The honest mechanism statement for **both** operators is **rebuild-from-the-user-side,
not surgical excision**.

**Why the two studies disagree, stated in the reviewer text rather than left to be asked.**
Rewrite looked selective on T2A's spans because they were **short, self-contained sentences
anchored on a rare token**, which a compacting operator can carry across verbatim. On the
model's own verbose prose and code it paraphrases, and nothing distinctive survives the
paraphrase. T2A flagged synthetic salience as an upper-bound caveat in its own first paragraph;
the caveat turned out to be load-bearing. That framing makes T2B an **extension** of T2A rather
than a contradiction of it, which is how the reply presents it.

**This is not written up as a loss.** T2B is the causal gold standard the reviewer asked for and
it establishes two things we did not previously have: **natural pollution is real and
concentrated** (SD of per-span effects **0.155** against a replicate-matched null's **0.125**,
p = **0.0085**; **16** spans with |Δ| ≥ 0.25 where the null predicts **9.3**, p = **0.0170**;
mean effect over all spans +0.020 [−0.010, +0.048], i.e. the typical span is inert), and **AC3
removes 100% of the spans the ablation proves harmful**. Reviewer 5YHP's W5 asked for exactly
this measurement, and the reply says so — including the part that cost us.

**Files changed for the retraction.** `03` W5 (rewritten: the "by construction" frame for
Reset's precision, the missing false-alarm-control disclosure, the full T2B block with its own
eight limits, the retraction paragraph, and the corrected mechanism sentence); `02` Q4 (two-study
bullet list replacing the "Rewrite is the selective operator" paragraph); `04` correction 3
(rewritten as "our first fix was also wrong"); `05` correction 3 and the detector bullet;
`README.md` concession table + guardrail; `CHANGES.md` rows 3.11 / 4.16 and §8 rule 3.
**`HANDOFF.md` row 5 and the PAPER-5 action were rewritten**: PAPER-5 previously said
*attribute the claim to Rewrite*; it now says **delete the framing** and state the
rebuild-from-the-user-side mechanism for both operators.

### 11.2 The assembled counter-case — new subsection in Common Weakness 2

`AR/tasks/T23/RED_TEAM.md` closes with the strongest objection available to a reviewer: that
v5's own concessions have quietly reduced AC3-Reset to *assistant omission plus a
spec-extraction call*, and that we conceded every piece of it separately without ever seeing it
assembled. The counter-evidence existed; it was in four different files. T25 followed the
red team's four-move plan and added **"Where AC3 separates from assistant omission, and where it
does not"** to `00` Common Weakness 2, with a two-sentence pointer from `04`.

What it says, and the numbers behind each line:

* **The matrix-wide head-to-head is a wash, and we say so first.** AC3-Reset vs. AO over all 36
  triples: mean **+2.6pp**, **15 W / 17 L / 4 T**. Recomputed by T25 from
  `RPT/post_neurips_ac3_phase{1,2}.md` with `EXP/paired_analysis.py`'s own parser. A reviewer
  can derive this from the two printed rows (+15.9 vs +13.3), so surfacing it is not optional.
* **The separation is concentrated where the mechanism predicts.** LiC-database **+18.7pp,
  8 W / 1 L** over 9 triples (49.0 / 56.2 / 55.1 against 45.6 / 27.9 / 30.6). Note: the red-team
  brief called this "+21pp"; the measured value is **+18.7pp** and T25 printed the measured one.
  math −3.1 (1/7/1), code −3.8 (2/6/1), actions −1.3 (4/3/2) — printed alongside, not omitted.
* **tau2**: AO is 0% on every model and fails *structurally* (rollouts exhaust the step budget
  because omission destroys tool-call results).
* **WildChat**: every populated cell of the per-respondent table favours AC3, 13 of them against
  AO; pooled order-balanced 87.8 / 91.2.
* **Two results no delete-everything editor can produce**: the factorial (9.3% → **59.8%** with
  the pollutant still in context) and T2B's concentration result plus 100% harmful-span removal.
* **The claim we actually defend** (red-team move 4): AC3 is a **decision procedure over
  operators indexed by referentiality**, of which AO is the correct choice in exactly one regime,
  and the regime is identifiable from a property observable *before* running anything. That
  claim predicts AO's successes instead of needing to beat them everywhere.

### 11.3 Red-team HIGH items applied

| Item | What was wrong | What T25 did |
|---|---|---|
| **H2** | `paired_analysis_results.txt` has a fifth row (Rewrite −0.3pp, 6/6/0, n=12) that v5 did not print, while CW1 claims "the same four operators" | Row **printed** in `00` CW2 with a dagger footnote: pre-analyzer-parity, one model, n=12; explicit "we do not claim Rewrite improves LiC accuracy"; Rewrite's evidence pointed at WildChat (Kimi/Rewrite 91.5% vs AO, the top cell of Table 3) |
| **H3** | Gated-Reset's 11/1/0 sums to 12 inside a table headed "36 comparisons"; three files gave three different recommendations | Same footnote explains the 12 (one respondent, reported separately not pooled). **One** deployment sentence now used in `00`, `01`, `02`, `03`: *always-on Reset where an intervention is cheap; Gated-Reset where an unnecessary edit carries state-disruption cost.* "the configuration we recommend" removed from `00` CW5 and `04`; "our strongest operator overall" removed from `03` |
| **H4** | Three places answer a criticism of one operator with a different operator's result | `03` W4: states plainly that the AC3 column is a per-row best, that **Rewrite** was not re-run on CollabLLM at N=3, and **withdraws rather than substitutes**. `01` W1: gives **Gated-Reset**'s new database figure — **49.7% (73/147)** on DSV4F, three prefixes 44.9 / 49.0 / 55.1, against full context 22.4 and AO 45.6 — the operator iNYK actually named. Selection rule stated once in `00` CW1 and again in `01`: the 33/36 row is a **single fixed configuration**, not a per-cell maximum |
| **H5** | We concede the FN metric was "biased in our own favour" and never say Table 1 is unaffected, though F40–F42 establish exactly that | Defending sentences added to `00` CW2 and `04` correction 2: Table 1's 20/19/25/23 come from an **arm-symmetric pool-level pre-filter** applied before any method runs; the per-run metric touches ≤4 cells at ≤1 sample each and 2 of those favour prior work; what is withdrawn is the *reported statistic*, not the main table |
| **H6** | `00` CW5 says no difference in `tab:main` is resolvable at n≈20 and then asserts three orderings from it, one of which breaches our own guardrail | Rewritten to apply the same standard to our own rows and to point at the 36-comparison matrix as the headline evidence. **"every AC3 operator still clears the full-context baseline in every cell" deleted outright** — it is false globally (Table 2 has AC3-Reset 47.0 vs Baseline 55.0 on gpt-5.4/CollabLLM) |
| **H7** | "22 populated cells … AC3 beats **assistant omission** in every cell" — 9 of the 22 are against full context, and 4 × 4 ≠ 22 | `03` W1 now reads "four operators × four respondents, against **two** baselines, 22 populated cells … every populated cell favours AC3 — 13 against assistant omission and 9 against full context" |
| **H8** | The one cell we lose is explained away using an unblinded single-annotator reading of the *worst* of three trials, whose traces no longer exist | `00` CW4 and `01` W3 now open with **"we do not have a defensible failure taxonomy for it"**, offer the reading as a hypothesis, and commit to a published rubric with a second annotator over all trials |
| **H9** | The "only method that improves over full context across the entire spectrum" sentence is tau2-dependent and sits **outside** every HOLD block | Reviewer text deliberately **not** changed (nothing may pre-empt T6). Added as **Blocker 5** in `README.md` with the pre-drafted "remains **viable** in the stateful agentic setting" fallback, ready to swap into `00`, `01` and `05` the moment T6 lands |
| **H10** | Vg97 asked for AC3's latency; we reported the summariser control's | **AC3's own wall-clock now reported**, recovered with zero API calls from `OUT/T1/main/*/experiment.log` timestamps (107 conversations, concurrency 5, arms back-to-back on one machine): full context **578 s**, MT-OSC 587 s (+2%), **Gated-Reset 781 s (+35%)**, summariser-1 835 s (+44%), **Reset 1,051 s (+82%)**, summariser-2 1,214 s (+110%). Decomposed honestly: most of the gap is **turn inflation** (6.9 vs 4.1 turns), and **per turn** Reset is +9%, Gated-Reset +5%, summariser-2 **+19%**. The n=40 math figures are given too (205 / 231 / 266 / **547 s**), since the old text quoted the control's 231 s and dropped AC3-Reset's 547 s |

**Deferred, with reasons.**

* **H1 and T24's `F-T24-1` / F70 — initially deferred, then routed to T25 mid-task and APPLIED.**
  See §11.3b: the false *"full, non-difficulty-selected pool"* sentence in `01` W2 is corrected,
  and the three-way baseline reconciliation is folded into `00` CW2/CW5, `01` W1, `02` Q1, `04`
  and `05`. Two of T24's items stay open because they are **paper** edits and
  `writing/overleaf_repo/` is out of bounds for autoresearch agents: the `tab:main` caption
  addition (T24 §7.4) and the "the design oracles are not oracles in end-to-end mode" note
  (§7.5). Both queued for the operator alongside PAPER-1..8.
* **M11** (neutral-prompt condenser control did not finish), **M12** (U-Fold never run or
  mentioned), **M6** (human validation, the third of 5YHP's three judge checks), **M14's**
  clean-arm naming rate, **M3's** bootstrap CI, **M15's** clustered bootstrap — all need runs or
  re-analysis beyond a text pass. **M14 was partly closed for free**: `03` W5 now discloses that
  naming precision against non-injected spans was never measured and points at the causal work
  as the better argument.
* **M1** (self-correction count reads 3 / 5 / 7 / 10 across four files), **M2** ("no
  per-benchmark tuning"), **M4**, **M7**, **M8**, **M9**, **M10**, **M13**, **L1**, **L3**–**L5**
  — real but survivable, and several are tone judgements the operator may want to make. **M5**
  is closed (the "by construction" frame is now in `03` W5 and `04` correction 3) and **L2** is
  closed (the 554/547 sentence is reworded).

### 11.3b T24's findings folded in (routed to T25 mid-task, to avoid two editors on one tree)

T24 resolved the red team's **H1** and, while doing so, found something worse (**F70**). Both were
routed to T25 rather than dispatched to a second agent, because two editors on `replies/v5/` is
the double-write pattern that corrupted output directories earlier in the session.

**F70 — a false statement in the reply to iNYK, now fixed.** `01_reviewer_iNYK.md` W2 said the
36-comparison paired matrix is on *"the full, non-difficulty-selected pool"*. **It is not** — it
runs on `htn50_52_*`, the 50 highest-failure-rate instances per task from the GPT-5.2 logs, with
replay prefixes further weighted toward baseline failures (74–86% failure-prefixes on database).
Difficulty selection is exactly what iNYK's W2 complained about, so we were answering the
reviewer's own objection with a claim they could falsify. **The fix is a swap, not a retraction:**
the sentence now states plainly that the matrix *is* difficulty-selected, that its +15.9pp on
33/36 is a valid **paired effect but not a population estimate**, and points the unbiased claim at
the two experiments that genuinely satisfy it — the uniformly random n=40 end-to-end subset
(CW3/Q1) and the condensation experiment on the **complete, unselected** pool (CW5, n=107/100,
end-to-end). The same disclosure was added to `00` CW2's sample-size paragraph, since the general
response is read first, and an n-and-provenance clause was added under `01` W1's 3-model table.

**H1 / F68–F69 — the baseline spread is explained, and the explanation is a strength.** All three
full-context numbers are correct measurements of deliberately different populations:

| Where it appears | Full context | Population |
|---|---|---|
| `tab:main` (submission) | 4.0 / 15.8 | 25 instances/task, **selected for highest** full-context failure rate under GPT-5-mini; last-turn replay |
| `01` W1 (3-model matrix) | 19.0–22.4 | 50 instances/task selected the same way from GPT-5.2 logs, prefixes further failure-weighted |
| `00` CW5 (condensation) | 56.1 / 83.0 | The **complete, unselected** pool (107 / 100), full end-to-end simulation |

Verified **by restriction, not inference**: restricting T1's own baseline run to `tab:main`'s exact
25 items — same model, same evaluator, same protocol — gives 56.1 → **32.0** (database) and
83.0 → **48.0** (code); independently, LiC's released logs put GPT-5-mini at 29.9% on the whole
107-item pool against 4.0% on its top-25 subset. Two routes to a ≈25pp selection effect, agreeing
within 2pp.

**The line that defuses the attack, now in `00` CW5 and `04`:** the unselected pool is not an easy
setting — its measured single-turn ceiling is **94.4% / 98.0%**, so it carries a **38.3pp /
15.0pp** multi-turn gap, and AC3-Reset closes **51% / 60%** of it against **50%** on `tab:main`'s
much harder subset. **Our baselines move 52 points across venues; the fraction of the gap we close
moves by ten points at most.** Condensation got no easy ride either: it scores below full context in every venue.
*(T30: this line read "moves four" until the coherence pass. "Four" is T24 §5.4's database-only
spread across three pools (47–51%); the sentence as printed in `00` CW5 and `04` quotes 51 / 60
against 50, whose largest gap is ten. Corrected to ten in both reviewer-facing files.)*

Applied to `00` CW5 (three-note comparability block + the ceiling paragraph), `01` W1 (n clause)
and W2 (the F70 swap), `00` CW2 (sample-size disclosure), `02` Q1 (comparability note), `04` (the
three-row reconciliation table + ceiling argument), `05` (condensation bullet). Source:
`AR/tasks/T24/worklog.md` §7. One item **not** applied: T24 §7.4's `tab:main` caption addition and
§7.5's "not an oracle in end-to-end mode" note are **paper edits** — `writing/overleaf_repo/` is
out of bounds for autoresearch agents, so they are queued for the operator alongside PAPER-1..8.

### 11.4 HOLD blocks

**All five `⚠ INTERNAL — HOLD` tau2 blocks, both `⚠ INTERNAL — T19 renumbering` notes and the
orientation preamble in `00` are byte-identical to what T15 and T19 wrote.** Nothing T25 touched
is inside a blockquote. Verified mechanically against the pre-T25 commit: `git diff <pre-T25> --
replies/v5/ | grep '^[-+].*⚠ INTERNAL'` returns nothing, and `git diff <pre-T25> -U0 --
replies/v5/*.md | grep -E '^[-+]>'` returns nothing — no blockquote line anywhere in the reply
files was added, removed or altered. T6's outcome remains unknown and nothing here pre-empts it.

---

## 12. T28 integration record — T27's measured items applied, and the T6 tau2 withdrawal

Two independent inputs landed on the same pass. T27 (`AR/tasks/T27/worklog.md`, findings
**F73–F77**) resolved four of the five red-team MEDIUM items that needed measurement, and **T6**
(`AR/tasks/T6/worklog.md`) finished the multi-replicate tau2 sweep the five HOLD blocks were
sealed for. T28 applied both. Decision **D20** governs the first: *adversarial-reader output is a
hypothesis list, not a patch set* — two of `RED_TEAM.md`'s own suggested fixes turned out to be
false, and both are now annotated in place in that document rather than deleted.

### 12.1 T27's items

| Item | What changed | Where | Evidence |
|---|---|---|---|
| **M11** — the neutral-prompt condenser control "did not finish in the window" | **The concession is replaced by a result, and it comes out in our favour.** The neutral-prompt condenser (our "compression, not evaluation" clause deleted) scores **51.4%** against full context's 56.1%, landing **between two replicate runs of our own prompt** (53.3 and 47.7) — so the condensation result does not depend on our phrasing. AC3 leads it by **+24.3pp** (Reset, 31/5) and **+22.4pp** (Gated-Reset, 30/6), p ≤ 0.0001. The decisive detail is the mechanism: with the clause removed the condenser flags an assistant error **0 times out of 340**, identical to with it (0/336, 0/341). A summariser does not audit, whatever you instruct it to do | `00` CW5, `02` Q1, `04` addition table, `05` condensation bullet; `00` "Summary of New Evidence" item 4 | F74/F75; `AR/tasks/T27/worklog.md` §7.3 |
| **M11 (b)** — the budget ordering | **Not claimed.** The −2.8 → −8.4pp contrast between the 1-call and 2-call condenser does **not** survive replication: a second run of the **1-call** arm scores −8.4pp, exactly the 2-call value, and the two 1-call replicates differ by more (p = 0.29, 0.26) than 1-call differs from 2-call. The cell carries ≈±6pp of run-to-run variation. We print only "neutral-to-negative at either budget" | `00` CW5, `02` Q1 | F73; T27 §7.1 |
| **M12** — MT-OSC's window | **Our own low-engagement defence is retired because we no longer need it.** At w=2 (the smallest window in MT-OSC's published sweep) the method engages **~8× more** — 2.2 condensations per conversation against 0.3 at w=4 (237 vs 30 over the same 107 conversations), with `raw_pairs_carried` 133 against the archived buggy run's 0 — and scores **47.7%, −13.1pp against its own w=4 run** (22 L / 8 W, p = 0.016); AC3-Reset leads it by **+28.0pp** (37/7). The MT-OSC w=2 row is added to `00` CW5's table. The reply now says "we scaled the window and it hurt" rather than "it barely fires", which rules out the reading that MT-OSC would have won if tuned | `00` CW5 (paragraph + table row), `02` Q1, `04` MT-OSC row, `05` condensation bullet | F76; T27 §7.2; **engagement counter corrected by T32** |
| **M12 (b)** — U-Fold on tau2 | Silence replaced by an **honest offer**: we did not manage an adaptation in the window, we say so, we give the engagement argument as our reason for expecting it to behave like the compaction family, we do not claim that settles it, and we ask Vg97 whether they want it run during the discussion period | `02` Q1 | T27 §6.6 |
| **M15** — the sign test | The 36-cell sign test is **kept as the assumption-light cross-check** and supplemented by two stronger statistics on the same data at the item level (n = **1,668** paired items, arm-symmetric intersection, 191 problem clusters): AC3-Reset **+15.4pp, 95% CI [+11.5, +19.4]**, **350 W / 93 L**. The interval also sharpens the row we like least — AC3-Rewrite is not −0.3pp but **exactly neutral, [−3.8, +3.8]** | `00` CW2 (full table), `01` Q2 (one-line version), `02` Q2 (full table — Vg97 asked) | F77; T27 §4 |
| **M15 (b)** — AC3 vs assistant omission | Interval attached to the head-to-head: matrix-wide **+2.8pp, 95% CI [−0.3, +5.9]** (we do not claim it), LiC-database **+18.6pp, [+10.7, +26.6]**. **Guardrail carried into the text and into rule 6b of §8: the matrix-wide item-level McNemar (p = 0.010) is never quoted as a win** — it treats 1,668 correlated items as independent. Reconciled with §11.2's cell-level statement (+2.6pp, 15/17/4): both now say a wash matrix-wide, concentrated on database | `00` CW2 AO subsection, `04`, `05` | F77; T27 §4.2 |
| **M3** — the `95.0 ± 0.0` cell | **The measured answer, not the proposed one.** Across the three replicates, **39 of 39** comparable conversations have differing analyzer outputs, the two failed problems are a **different pair each run (intersection 0, union 5)**, and turn counts and extracted answers differ on **7 and 5 of 40**. A problem-clustered bootstrap is added: FC **87.5 [79.2, 95.0]**, Reset **93.3 [87.5, 98.3]**, Gated-Reset **95.0 [90.0, 99.2]**; paired, Gated-Reset **+7.5pp [+1.7, +15.0]** (p = 0.023) and Reset **+5.8pp [+0.0, +12.5]** (p = 0.119), and we print the one that does not reach significance | `00` CW3, `01` Q1 | T27 §3.2–3.3 |
| **M6** — human validation | One sentence, undressed: **we did not run a human study**, the degraded-copy control (39/40, 36/40, 40/40) establishes that the judges discriminate and not that they agree with people, and a human-agreement study with released rubric and raw labels is queued for the camera-ready | `03` W4 | T27 §5 |

**Two of the red team's own suggested fixes were measured and are FALSE. Neither is posted, and both are now annotated in `AR/tasks/T23/RED_TEAM.md` with an inline `⚠ SUPERSEDED — DO NOT APPLY` note** (originals kept — the record of what was proposed and why it was wrong is worth keeping):

* **M3's** proposed clause *"the analyzer cache was disabled for these runs"* is **false**.
  `context_edit_v2_gated.yaml:18` sets `analysis_cache_dir: outputs/analysis_cache` and
  `run_exp1_reps.sh` never overrides it; the runs' own `config.yaml` confirms the path. Posting it
  would have handed a reviewer a checkable false statement inside the paragraph whose purpose is
  to rebut a caching suspicion. The independence probes above are the true, stronger answer.
* **M11's** proposed *"it degrades with more budget (−2.8 → −8.4pp), which is itself the mechanism
  prediction"* asserts a mechanism from an ordering that **dissolves under replication** (F73).

### 12.2 Two places that needed reconciling

1. **`00` CW3's "this experiment alone is not powered for significance"** now sits beside a
   bootstrap in which Gated-Reset reaches p = 0.023. Reworded to *"we do not rest our headline
   significance on it"*, which is true and does not contradict the interval. Same fix in `01` Q1.
2. **The AO head-to-head appears in three places at two levels of analysis.** §11.2's assembled
   counter-case gives the cell-level +2.6pp / 15-17-4; T27's item-level pass gives +2.8pp with a
   clustered CI. They agree, and the text now says so rather than printing two numbers for the
   same quantity. The anti-conservative McNemar p is excluded from all three (§8 rule 6b).

### 12.3 The T6 tau2 withdrawal

T6 completed the full published tau2 matrix at **N=3** — 3 models x 5 arms x 3 replicate runs x
19 tasks = **855 scored rollouts**, 15/15 cells.

| tau2 (reward %) | gpt-5.4 | DSV4F | Kimi-K2.6 |
|---|---|---|---|
| FC published (N=1) | 68.4 | **31.6** | **26.3** |
| **FC re-measured (N=3)** | **68.4 ± 13.9** | **70.2 ± 11.0** | **78.9 ± 0.0** |
| AO | 0.0 | 0.0 | 0.0 |
| AC3-Augment | 47.4 ± 5.3 | 50.9 ± 8.0 | 57.9 ± 9.1 |
| AC3-Gated-Reset | 57.9 ± 21.1 | 57.9 ± 10.5 | 71.9 ± 11.0 |
| AC3-Rewrite | 47.4 ± 5.3 | 57.9 ± 13.9 | 66.7 ± 8.0 |

**On all three models the re-measured baseline is at or above every AC3 arm**, and AC3-Augment is
significantly *worse* than baseline on all three (−21.1 p=0.008; −19.3 p=0.043; −21.1 p=0.012).
**The tau2 improvement claim is withdrawn**, not softened into "mixed results".

*This is "our published baselines were wrong", not "not comparable", and that was tested.*
gpt-5.4's baseline reproduces at **68.4** against a published 68.4; AO reproduces at **0.0 in all
nine cells / 171 rollouts**; `gpt-5-mini` was reachable; invocation strings byte-identical to the
committed sweep scripts; no model substitution. Our own source report already described the Kimi
baseline cells as floors (14/20 and 19/20 short-exits).

**What survives and is still posted:** AO = **0.0% on every model**, structurally — rollouts never
reach `user_stop` and exhaust the 50-step budget, paired −68.4 / −69.6 / −78.9pp at p < 0.0001.
It does not depend on the baseline's level, which is why the correction leaves it standing.
**Kept, not upgraded:** the gpt-5.4 Gated-Reset regression iNYK identified, 57.9 ± 21.1 vs 68.4,
paired −10.5pp, exact p = 0.238 over 57 pairs. **Disclosed as unexplained:** gpt-5.4's AC3
collapse (Augment 84.2 → 47.4) with its baseline reproducing exactly — substitution, non-firing,
degenerate termination and rate limits all ruled out, and the one real fork defect found (53% of
analyzer calls falling back to splicing a raw completion into the briefing) is worth **+2.3pp**
when patched. Phrasing: **"N=3 replicate runs (seeds 42/43/44)"** — `--seed` genuinely threads to
the provider's `seed` parameter on this fork, best-effort.

**Red-team H9 is closed.** The "improves over full context across the entire spectrum" sentence
would have been false on the benchmark it was sharpened to survive. README Blocker 5's pre-drafted
fallback is now **applied** in `00` CW4, `01` W3, `04` correction 6 and `05` — "improves over full
context on every self-contained and referential benchmark, and the only method that remains
**viable** in the stateful agentic setting".

**Correction counts move.** `04` goes from five numbered corrections to **six** (tau2 is item 6);
`05` from seven to **eight** (tau2 is item 8) — exactly the numbering the two T19 renumbering notes
predicted, which is why both notes are now discharged rather than carried. `README.md`'s concession
count moves from ten to **eleven**. Red-team **M1** (the count reads differently in four files)
remains open and is unchanged by this.

### 12.4 HOLD blocks — verification, and the deliberate unsealing

Two phases, recorded separately because they have different statuses.

**Phase 1 (T27 items).** Per-block SHA-256 over each `⚠ INTERNAL — HOLD` region, computed from the
pre-edit commit `d989c50` and again after the T27 pass. **All nine detected regions match to the
digit** (five reply-file HOLD blocks plus the four `CHANGES.md` lines that mention HOLD); only line
numbers shifted. Baseline recorded at `AR/tasks/T28/hold_baseline.txt`. Nothing in the T27 pass
touched a held passage.

**Phase 2 (T6).** The orchestrator routed T6's landing to T28 mid-task, which **supersedes the
byte-identical constraint**: the blocks existed to be resolved on exactly this outcome. All five
`⚠ INTERNAL — HOLD (T6 in flight)` blocks and both `⚠ INTERNAL — T19 renumbering` notes were
**resolved and removed**, and their pre-drafted withdrawal wording applied. `00`'s orientation
preamble is retained, with its T6 item rewritten from "on HOLD" to "resolved, and it goes against
us". `grep -rn "⚠ INTERNAL" replies/v5/*.md` now returns only the preamble.

---

## 13. T32 integration record — T30's two factual open items (J1, J2) settled from artifacts

T30's coherence pass left four open items. J3 and J4 are internal wording/bookkeeping and remain
open by design. **J1 and J2 were factual questions with determinate answers**, so T32 settled them
against the code and the run artifacts rather than handing the operator a choice. Zero API calls,
no experiments, no `git checkout`; `writing/overleaf_repo/` untouched. Full evidence:
`../../autoresearch/tasks/T32/worklog.md`.

### 13.1 J1 — MT-OSC's engagement rate is **condenser calls**, and the ratio is ~8×, not 9×

**The conflict.** `00` CW5 and `02` Q1 printed MT-OSC's w=4 engagement as 0.3/conversation and
0.6/conversation three sentences apart; `04` and `05` printed 0.3 *with* "nine times", and
"nine-fold" only reconciles against 0.6. At least one sentence was wrong however it resolved.

**What settled it.** `src/ctx_editor/strategies/mtosc.py` emits **three distinct log types**, not
one: `mtosc_decider` at every scheduled trigger turn (`:336`), `mtosc_condensation` when the
condenser call returns a parseable condensation (`:345`), and `mtosc_applied` when a pending
condensation is actually spliced into the context (`:327`). T27's "log events / conversation"
(`AR/tasks/T27/worklog.md:446–450`) summed all three. That is **not** an engagement rate — it is
~3 records per single condensation — and T27 used it correctly, as a *positive control that the
schedule was live after the `raw_pairs_carried` fix*, never as a reviewer-facing statistic. T1's
counter (`AR/tasks/T1/worklog.md:354`) counted condenser calls, which is what "MT-OSC fired" means
to a reader.

**Recounted directly from the run traces** (`outputs/T1/main/db_mtosc_w4/traces/database/mtosc_w4/`
and `outputs/T27/db_mtosc_w2/traces/database/mtosc_w2/`, 107 conversations each):

| counter | w=4 | w=2 | ratio |
|---|---|---|---|
| `mtosc_decider` | 30 (0.28/conv) | 237 (2.22/conv) | 7.9× |
| **`mtosc_condensation`** (condenser calls — **adopted**) | **30 (0.28/conv)** | **237 (2.22/conv)** | **7.9×** |
| `mtosc_applied` (reached the context) | 6 (0.06/conv) | 133 (1.24/conv) | 22.2× |
| *all `mtosc_*` records* (T27's composite) | *66 (0.62/conv)* | *607 (5.67/conv)* | *9.2×* |

Decider and condensation counts are identical because the Decider **never withheld** in either run
(0/30 and 0/237) — exactly as `mtosc.py`'s docstring predicts, since τ = 1000 user tokens is never
reached by LiC's short sharded messages. So the composite counter's 9.2× was an artefact of summing
log types, and "nine-fold" was numerology on a quantity nobody would recognise as engagement.

**Applied:** 0.3 (w=4) and **2.2** (w=2) condensations per conversation, ratio **~8×**, in `00`
CW5, `02` Q1, `04`'s additions table, `05`'s condensation bullet, `README` (two places) and §12's
M12 row. "5.7 / 0.6 events" and "nine-fold" / "nine times" appear nowhere in the reply set; the
`README` carries a do-not-quote note so the retired figures cannot migrate back.

**One strengthening fact added** to `00` CW5, since it is measured and it is the point of the
paragraph: because the paper's condenser runs with a deliberate one-turn lag, only **6 of the 30**
w=4 condensations were ever applied to a context before the conversation ended. The "nearly a
no-op" characterisation is if anything understated. We keep **0.3** as the headline rather than
0.06 because 0.3 is the *conservative* choice — it is the figure least favourable to our own
argument.

### 13.2 J2 — the leak table now uses one label end to end; math's rate rises 38% → 47%

**The conflict.** `03` W1 printed math leak 38% (54/144) beside a no-leak subset of n=77, and
144 − 54 = 90 ≠ 77. The pooled cell read "11% overall", a rate over all four tasks inside a row
covering three.

**What settled it.** `AR/tasks/T2c/final_tables.py:37` defines the primary label:
`leak_final = LEAK if (verdict == "CORRECT_ANSWER_STATED" or pderived)` — the **union** of the
answer-verification pass and the math-only model-free numeric probe. Line `:116` passes
`leak_final` to every split in Table 2, so **n=77 and n=329 were always union-label subsets**;
line `:64` computes Table 1's rate column from `answer_verdict` **alone**. The two tables were
therefore reporting different partitions, and T2c's own Table 2 caption ("strict: analyzer output
verified to contain the correct answer") describes only the first arm of the union — since fixed at
the generator and regenerated by T33, §14.3. Recounted from
`leak_labels_final.jsonl`: math union LEAK **67**, NO_LEAK **77** (67 + 77 = 144 ✓); pooled
math+code+database union LEAK **68**, NO_LEAK **329** ✓; verification-alone gives math 54 and
pooled 55.

**The headline check the brief asked for: the +20.7pp on n=329 is a `leak_final` row**, so the
union label is the one backing the result, and it is the label we now report throughout. The judge
label stays where it already was — a robustness note (`03`: no-leak gain +24.5 vs leak +17.3, so
both definitions agree in direction).

**Applied** in `03` W1: column relabelled "Leak rate (either detector fires)", the lead-in now
states the union explicitly, **math 38% (54/144) → 47% (67/144)**, pooled **11% overall → 17%
(68/397)**, and a following sentence gives the single-detector rates (verification 38% math /
14% pooled; probe 40% math) as reference values that are deliberately not used to cut subsets.
`04`'s and `05`'s one-line summaries are reworded from "never states the correct answer" to also
cover the numeric probe. Code (0/106), database (1/147) and actions (3/150) are **unchanged** —
the probe is math-only, so their union equals their verification count.

**Direction: against us.** Math's admitted leak rate rises by 9 points. **No headline number
moves**: +30.2 code, +26.0 database, +20.7 pooled, −2.6 math and every n were already computed on
this label.

**Knock-on correction.** `03`'s caveat sentence cited the 29/32 hand-validation as validating "the
no-leak label". `AR/tasks/T2c/worklog.md:238–251` shows that adjudication was drawn from records
the **v3 LLM judge** called `NO_LEAK`, not from the `leak_final` stratum, so as written it
validated a different label than the table used. Reworded to attribute it to the judge label and
to state what it actually implies — all three errors were on math, which is *why* the primary
label adds the model-free probe.

### 13.3 Tally impact: none

Both corrections land on rows already booked as **newly added** in v5 (row 5.7, the MT-OSC
engagement rate; row 4.2, the auditing-vs-re-solving table). They are not v4 claims, so the
Corrected count stays at **17** and the total stays at **69**. Recorded explicitly because T30's F8
found this exact tally drifting twice.

*(T34: the two figures quoted in the previous sentence are superseded — the tally is now derived
from the rows, where Corrected is **21** and the total **82**. §13.3's substantive point is
unaffected and still holds: both T32 corrections land on rows already booked **Newly added**, so
neither row changed bucket and T32's tally impact remains none.)*

## 14. T33 cleanup record — T30's J3, the T2c caption, and one tone leak

`../../autoresearch/tasks/T33/worklog.md`. Zero API calls, no re-runs, no `git checkout`,
`writing/overleaf_repo/` untouched.

### 14.1 Reviewer-facing: our own file structure no longer leaks into the replies

T30 §5.2 flagged that two reviewer-facing sentences described the reply set by its internal file
count. Reviewers see a discussion thread, not our directory.

* `00` CW2: "…than leave a reader to **do it from six documents**" → "…than leave a reader to
  **piece it together from our separate replies**".
* `04` lead-in: "…rather than leave it **distributed across six documents**" → "…rather than leave
  it **distributed across our separate replies**".

Wording only; no claim, number or emphasis changes. The two remaining "six files" mentions are in
`README` and §11 of this file, which are internal and stay as written. T30's other two register
notes (the bolded lead-ins clustering in `00` CW5; the length of `03` W5) were **not** touched —
neither has a local fix and a style pass was out of scope.

### 14.2 Internal: `README`'s dangling ordinal (T30's J3) — fixed

`README`'s tractability paragraph read "…and **an eighth** correction raises a *competitor's*
number". ERGO is item **7** in `05` and item **5** in `04`, so the ordinal resolved to nothing.
Re-verified before editing: `05` lists eight corrections, seven of them ours (items 1–6 and 8) and
one — ERGO, item 7 — raising a competitor's number, so the counts around it were right.

* **Before:** "…and **an eighth correction** raises a *competitor's* number."
* **After:** "…and **the ERGO correction** raises a *competitor's* number."

"We surface all eight ourselves" in the next clause is unaffected (seven ours + ERGO = eight).

### 14.3 `AR/tasks/T2c/RESULTS.md` Table 2 caption — fixed at the generator

§13.2 above recorded that T2c's Table 2 caption called the `leak_final` split *"strict: analyzer
output verified to contain the correct answer"*, which describes only the first arm of the union
and was the proximate cause of the J2 confusion. T32 deliberately did not patch the generated file,
since anyone regenerating it would reproduce the same caption. **T33 fixed the generator**
(`final_tables.py:116`) and regenerated `RESULTS.md`:

* **Before:** "…split by leakage (strict: analyzer output verified to contain the correct answer)"
* **After:** "…split by leakage (primary — union: analyzer output verified to contain the correct
  answer OR the math-only model-free numeric probe fires)"

Verified: the regenerated file differs from the previous one on **that one line only** — every
rate, `n`, Δ, CI, W/L and p-value is byte-identical, and `leak_labels_final.jsonl` (rewritten as a
side effect of the run) is byte-identical to its backup. Table 1's "strict leak rate" column head
is left alone: it is computed at `:64` from `answer_verdict` alone and the label is accurate there.
**No reviewer-facing number is affected** — `03` W1 already reports the union label after T32.

### 14.4 Escalated by T33, RESOLVED by T34: T30's J4 (the tally split)

**T33 left J4 alone** on the grounds that it was larger than the "count wording" it had been
scoped as. T30 had rewritten the tally prose to "17 corrections, 8 against us, 3 in our favour,
remainder wording-only" and noted the split was partly inherited; checking it against the rows did
not reconcile. What T33 recorded:

| bucket | printed in the Tally table | rows carrying that status in §§1–6 |
|---|---|---|
| Newly added | 21 | **21** ✓ |
| Unchanged | 24 | 20 (+1 "unchanged in substance") |
| Corrected | 17 | 20 (+1 "struck / corrected against us") |
| Struck | 6 | 5 (+2 "half struck") |
| — | total 69 (68 rows + 1 UNVERIFIED) | **81 numbered rows**, 1.1–5.10, no gaps or duplicates |

Eleven further rows carried statuses that mapped to no bucket at all ("replaced by results" ×4,
"HOLD → resolved" ×2, "resolved", "qualified by T25", "promise fulfilled", "not used",
"bookkeeping"). So T28's note that "the counts above are the sum of the rows" was not true of the
rows as they then stood, and fixing J4 meant deciding which statuses count as corrections and
re-deriving every bucket — a bookkeeping decision about how we characterise our own audit.

**Resolution (T34).** The buckets were re-derived from the rows and the tally now reconciles
exactly; the bucket scheme, the assignment rule and the per-bucket row lists are written into the
**Tally** section at the top of this file so the derivation does not have to be repeated. Three
buckets were added for the statuses that mapped nowhere — *Replaced by results*, *HOLD → resolved*
and *Bookkeeping / not used* — because those are genuinely different events from a correction, and
On HOLD and UNVERIFIED were moved out of the total, UNVERIFIED because U6 is a §7 liability rather
than a §§1–6 row. The reconciled counts are **Unchanged 20, Corrected 21, Struck 9, Replaced by
results 5, HOLD → resolved 3, Newly added 22, Bookkeeping / not used 2 = 82**. A derivation rule is
now stated at the head of the table naming the decay mechanism: the tally is derived from the rows
and must be re-derived whenever a row changes, never incremented in prose.

**Two corrections to the T33 table above, which are counting errors rather than bucket
disagreements.** The row count is **82**, not 81: the T33 enumeration missed **4.18a**, which is a
full row with its own status, evidence and new wording, not a sub-note of 4.18. And *Newly added*
is **22**, not 21 — the one bucket believed to reconcile did not: row **3.9** carries a *newly
added* status while its Claim column names a v4 question that v4 never answered, so it lacks the
*(new)* marker the other 21 carry. Both are recorded here rather than quietly absorbed, because
"the bucket that reconciled" was the reason to trust the rest.

**Unchanged by T34**: every row's status, claim, number, evidence and new-wording cell; the
"17 corrections, 8 against us, 3 in our favour" paragraph, which counts named corrections rather
than rows and whose re-derivation would be a claim decision, not arithmetic (it is annotated in
place, not rewritten); and every reviewer-facing file. **The 17 remains internal-only**: no
reviewer-facing file quotes it. The reviewer-facing count is the separate "seven of our own numbers
moved … eight in total", which was re-verified in §14.2 and is right.
