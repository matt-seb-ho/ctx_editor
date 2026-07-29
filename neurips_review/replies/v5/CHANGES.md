# CHANGES.md — v4 → v5 claim audit

Every assertion in `replies/v4/` audited against the 2026-07-29 autoresearch session (findings **F1–F49**, decisions **D1–D11**: `../../autoresearch/WORKLOG.md`; retired claims: `../../autoresearch/PROVENANCE.md`). Task T15 worklog: `../../autoresearch/tasks/T15/worklog.md`.

**Revision history.** T15 wrote this audit at F1–F38, with four claims on HOLD pending two in-flight audits. **T19** (`../../autoresearch/tasks/T19/worklog.md`) revised it once T14, T16, T17 and T18 landed: the T14 hold is resolved, U1 is retired, and the ERGO denominator disclosure is added as §9 and as claim rows 1.23 / 2.10 / 3.12 / 5.9 / 6.x. **The T6 (tau2) holds are untouched and remain live.**

## Tally

| Status | Count |
|---|---|
| **Unchanged** (re-verified, wording untouched) | 24 |
| **Corrected** (number or wording changed) | 15 |
| **Struck** (removed from v5) | 6 |
| **Newly added** (result that did not exist in v4) | 16 |
| **On HOLD** (blocked on an in-flight task) | 3 |
| **UNVERIFIED** (no artifact found — see §7) | 1 |
| **Total claims audited** | 67 |

Of the 15 corrections, **7 move against us** (CollabLLM MATH-Hard, the CollabLLM assistant-omission column, FN-adjusted accuracy / end-to-end table, preservation attribution, WildChat headline, memory gains, auditing-on-math), **3 move in our favour** (BigCodeBench, database leak-free replication, budget accounting), and 5 are wording-only. Of the 5 claims T19 newly added, **all 5 are the ERGO denominator disclosure**, which moves against us by raising a competitor.

**Changes made by T19 to T15's tally.** Newly-added 11 → 16 (five ERGO disclosure rows). On-HOLD 4 → 3 (1.13, 2.4, 3.2, 4.4 were the four; the T14-gated provisional flag on all LiC figures is lifted, and 4.4's hold is now T6-only — the three remaining holds are all tau2). UNVERIFIED 5 → 4 (**U1 retired**: the gate-statistic artifacts do exist, at `scripts/analysis_rewrite_v_reset/data/gated_reset_reconstructed_{lic,collabllm}.md`, and T16 re-derived both independently from raw traces). Total 64 → 67.

**Changes made by T21 (from T20's verification pass).** UNVERIFIED 4 → **1**: U2, U3, U4 and U5 are all resolved, leaving only U6, which is unclosable by construction. Corrections 14 → 15, the new one being the CollabLLM assistant-omission column taken from N=1 to N=3 (§10). On-HOLD stays at 3 — all three are tau2, and every INTERNAL/HOLD block in the reply files is byte-identical to what T15 wrote (verified mechanically; see §10).

**Changes made by T25 (from T2B and the T23 red team).** Corrections 15 → **16**, and one of the existing sixteen changed direction: the "preserve what's correct" claim, which T19 had re-attributed to **AC3-Rewrite**, is now **retracted for both operators** after T2B measured selectivity causally on naturally occurring spans (F66). Rows 3.11 and 4.16 and §8 rule 3 are revised accordingly, and a new **§11** records the retraction, the assembled counter-case to the red team's strongest objection, and the nine red-team HIGH items applied or deferred. On-HOLD stays at 3 and every INTERNAL/HOLD block remains byte-identical (verified mechanically; see §11.4).

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
| 1.13 | CW4 tau2 table (FC 68.4/31.6/26.3; AO 0/0/0; best AC3 84.2/57.9/73.7) | **HOLD** | **T6 in flight.** Interim N=3 Baselines: gpt-5.4 68.4±13.9, DSV4F **70.2±11.0** (published 31.6), Kimi **80.4±2.5** (published 26.3) — `AR/tasks/T6/worklog.md` 15:10 entry | Table moved inside a `⚠ INTERNAL — HOLD` block with fallback wording drafted |
| 1.14 | "Assistant omission collapses to 0% on every model" | **unchanged, and strengthened** | T6 positive control #2: AO rollouts terminate on `max_steps`, never `user_stop`, while the other four arms return reward 1.0 in the same process — `AR/tasks/T6/worklog.md` 13:58 | Promoted to carry CW4 on its own, with the mechanism stated |
| 1.15 | Kimi footnote: "rate-limit-clipped, so we quote a conservative **+24 to +34pp**" | **struck** | **T6 interim**: the whole Kimi baseline cell is a clipped floor; re-measured 80.4 is above every published Kimi AC3 number. A "conservative" range off a broken control is not conservative | removed |
| 1.16 | "only **1 of 11** baseline failures on gpt-5-mini attributable to context pollution" | **CORRECTED — softened** (T21, from T20/§7 U4) | **F56**. Number traced to `~/ac3/tau2_ctxe/ctx_edit/EXPERIMENT_LOG.md` commit `169b044`, but the 20 traces and any labels file are **unrecoverable**, the labelling had no rubric and no second annotator, and it is the 45.0% trial while the table reports best-of-3 | "1 of 11" dropped. Now: the baseline failures were **dominated by missing domain knowledge and step-budget exhaustion**, with a single repetitive-loop case; stated explicitly as a qualitative reading of one trial rather than a rubric-based annotation, with a proper taxonomy promised for the camera-ready |
| 1.17 | tau2 "confirms the rule: lightest operator wins on the strongest model, heaviest on the weakest" | **struck (pending T6)** | derived from the same N=1 cells T6 is re-measuring | removed; replaced by the analyzer-sweep evidence (F21/F22) as the CW1 generality argument |
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
| 2.4 | W3 tau2 defence | **HOLD** + **newly added concession** | **T6**, `AR/tasks/T6/worklog.md` 14:38 | New: at n=19, binomial sd ≈ **10.7pp**, our N=3 Baseline re-measurement spreads **±13.9pp**; "several of the differences we reported at N=1 are inside that". Magnitudes held |
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
| 3.2 | W2 cross-reference to tau2 | **HOLD** + **newly added concession** | **T6** | Adds the 10.7pp noise-floor concession; no magnitudes |
| 3.3 | Q2 WildChat 89.8 / 92.1 | **corrected** | **F31** | 87.8 +/- 2.1 / 91.2 +/- 2.1 + judge-agreement summary |
| 3.4 | Q2 "tau2 … per-model results against baseline rather than best-of-3" | **corrected** (wording) | **T6** | "mean +/- std over three replicates per cell" |
| 3.5 | *(new)* | **newly added** | **F28** | Proactive disclosure of the FN-adjustment bias in the Q2 answer |
| 3.6 | Q3 "our strongest evidence is already in the paper" — Table 5 contagious pollution refutes the extra-compute hypothesis | **unchanged** | paper Table 5 | verbatim |
| 3.7 | Q3 self-reflection control "97.5 vs AC3-Reset 97.5 vs full context 90.0"; "**We are re-running** the same control on high-pollution tasks" | **promise fulfilled**; numbers **unchanged** and now labelled raw/N=1 | `EXP/exp2_results.txt` (reflection 97.5), `EXP/exp1_results.txt` (reset 39/40 = 97.5 raw, baseline 36/40 = 90.0 raw) | Retained as the non-discriminating near-ceiling control, then superseded by the T1 high-pollution result. *(Note: v4 was internally inconsistent — 100.0 in CW3 vs 97.5 here for the same run. v5 is consistent at raw.)* |
| 3.8 | Q3 latency "**13% wall-clock** (231s vs 205s for 40 conversations)" | **unchanged** | `EXP/exp1_results.txt` / `EXP/exp2_results.txt` wallclock fields | verbatim, plus measured per-conversation strategy-call counts from **F27** |
| 3.9 | Q3 analyzer-model sensitivity — **v4 never answered this half of the question** | **newly added** | **F20/F21/F22**, `AR/tasks/T9/worklog.md` (commit `1f4f32d`), `OUT/T9/{rep1,rep2}/<task>_<arm>/` | Five-analyzer table (Kimi +39.9 / DSV4F +28.7 / gpt-5.4-mini +27.0 / Llama-70B +18.0 / gpt-4o-mini +12.9), n=178 matched pairs, exact McNemar; the under-detect-not-mis-detect mechanism; the non-OpenAI point; stated limits |
| 3.10 | Q4 component table | **unchanged** | — | verbatim |
| 3.11 | *(new)* | **newly added, then REVISED by T25** | **F25** + **F66**, `AR/tasks/T2A/RESULTS.md`, `AR/tasks/T2B/RESULTS.md` §4 | Q4 now carries the *corrected* operator-level statement. T19 wrote "Rewrite is the selective operator (27.0 / 38.9)"; **T2B retracts that** — on natural spans Reset keeps 5/66 and Rewrite keeps **0/66**, preservation 0% for both, edit precision 63.6% = base rate for both. Q4 now says the mechanism is the **same for both operators** (detect → discard the assistant side → rebuild from the user side) and that they differ in *how much* they rebuild, which keeps the operator a knob rather than a second method |
| 3.12 | *(new — added by T19)* | **newly added — disclosure** | **F43/F44/F48/F49**, `AR/tasks/T18/worklog.md` R1/R4 | New paragraph in the **W1** answer. Vg97's central weakness is the *baseline set*, so a defect in how an existing baseline was scored belongs there. Same three numbers plus the n≈20 non-significance result, explicitly tied back to Vg97's own W2 statistical-reliability point; cross-references CW5 |

---

## 4. `03_reviewer_5YHP.md`

| # | Claim as written in v4 | Status | Evidence | New wording in v5 |
|---|---|---|---|---|
| 4.1 | W1 scope defence (structural exclusion is the scope, not a gap; Table 5; Appendix D) | **unchanged** | — | verbatim |
| 4.2 | *(new)* | **newly added — the strongest new mechanism evidence** | **F10**, `AR/tasks/T2c/RESULTS.md`, `AR/tasks/T2c/{answer_check.jsonl,math_numeric_probe.json,leak_labels_final.jsonl}`; source traces `~/ac3/recovered_t2c/ctx_editor/outputs/post_neurips_ac3_phase1/` | Auditing-vs-re-solving table: leak rates (code 0%, database 1%, actions 2%, math 38%) and leak-free gains (code **+30.2**, database **+26.0**, pooled **+20.7 [+14.8, +25.3] p<0.0001**) |
| 4.3 | *(new)* | **newly added — concession** | **F10** | **Math conceded outright**: leak-free gain **−2.6pp** (n=77, p=0.815); math's entire +9.7pp sits on the leaking subset. Conceded in the same paragraph, before the wins |
| 4.4 | W1 "On tau2-bench … blanket omission scores 0% on all three models **while AC3 beats full context on all three**" | **half struck** | AO=0% corroborated by T6 PC2; the AC3 half depends on the contested cells | Keeps AO=0% with the mechanism; drops "AC3 beats full context on all three" pending T6 |
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
| 5.4 | Evidence table row "Corrected tau2 reporting: AO 0% on every model; best AC3 beats full context on every model" | **half struck / HOLD** | as 1.13 / 4.4 | row removed from the table pending T6; AO=0% survives in the body |
| 5.5 | "MATH-Hard 100 vs 95 and 90; BigCodeBench 20 vs 5 and 15" | **corrected** | as 4.8 / 4.9 | replaced by the N=3 correction, listed as self-correction #1 |
| 5.6 | *(new)* | **newly added** | F16, F28, F25, F31, F12, T8 §5 | A numbered "corrections we are making to our own numbers" list (4 items posted, 2 more in `05_final_remarks.md`), made part of the tractability argument |
| 5.7 | *(new)* | **newly added** | F27 | Evidence-table rows for the condensation baseline, MT-OSC engagement rate, analyzer sensitivity, detector evaluation, WildChat judge audit |
| 5.8 | Closing tractability argument | **unchanged**, extended | — | adds: "the corrections listed above are the discussion period working as intended … every one was found by us" |
| 5.9 | *(new — added by T19)* | **newly added — disclosure** | **F42/F43/F44/F47/F48/F49**, `AR/tasks/T17/RESULTS.md`, `AR/tasks/T18/worklog.md` R1/R4 | Numbered correction **5** added to the "corrections we are making" list, and the lead-in changed from "four corrections" to "five", with the fifth explicitly labelled as moving against us by *raising a baseline*. Carries math 69.6 → 80.0, code ≈44.0, database untouched, actions unclosable, and the n≈20 non-significance result. Closes on why we would rather state it: it is recoverable from our own printed percentages |
| 5.10 | Placement relative to the T6 HOLD block | **bookkeeping (T19)** | — | The T6 HOLD block is left **byte-identical** and still refers to the pending tau2 withdrawal as "a fifth correction". A separate `⚠ INTERNAL — T19 renumbering note` was added *after* it recording that tau2 becomes item **6**. The HOLD block was not edited, softened or resolved |

---

## 6. `05_final_remarks.md`

Mirrors the above. All ten revision bullets updated to the corrected numbers; four bullets converted from promise to result (condensation, detector, judge audit, memory split); three bullets added (auditing-vs-re-solving, analyzer sensitivity, memory variance); one new section added listing the six self-corrections; one `⚠ INTERNAL` HOLD note for a possible seventh (tau2).

**T19 additions.** A **seventh** numbered correction added for the ERGO denominator defect (**F43/F44/F48/F49**; `AR/tasks/T18/worklog.md` R1/R4): math 69.6 → 80.0 above AC3-Reset's 75.0 and level with AC3-Gated-Reset's 80.0, code ≈44.0, database 12.0 untouched, actions unclosable and printed as an interval, closing on the n≈20 non-significance result. The condensation-baseline revision bullet gained a closing sentence pointing at it. As in `04`, the T6 HOLD block is left **byte-identical** — it still says the tau2 withdrawal would be "a seventh item", and a separate `⚠ INTERNAL — T19 renumbering note` after it records that tau2 becomes item **8**.

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
6. **No tau2 magnitudes until T6 lands.** Five `⚠ INTERNAL — HOLD` blocks mark every affected passage (`00` x2, `01`, `04`, `05`), plus an orientation preamble at the top of `00`.
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
| **T6** — multi-replicate tau2 | **STILL RUNNING** | Unknown. Preliminary Baseline cells (DSV4F 70.2 ± 11.0, Kimi 80.4 ± 2.5 against published 31.6 and 26.3) suggest the published tau2 baselines may not replicate | **Nothing.** All five `⚠ INTERNAL — HOLD` blocks and their pre-drafted withdrawal wording are left byte-identical to what T15 wrote, and so is the T6 item in `00`'s orientation preamble. Not resolved, not softened, not guessed |

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
moves four.** Condensation got no easy ride either: it scores below full context in every venue.

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
