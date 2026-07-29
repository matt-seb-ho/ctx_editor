# CHANGES.md — v4 → v5 claim audit

Every assertion in `replies/v4/` audited against the 2026-07-29 autoresearch session (findings **F1–F33**, decisions **D1–D11**: `../../autoresearch/WORKLOG.md`; retired claims: `../../autoresearch/PROVENANCE.md`). Task T15 worklog: `../../autoresearch/tasks/T15/worklog.md`.

## Tally

| Status | Count |
|---|---|
| **Unchanged** (re-verified, wording untouched) | 24 |
| **Corrected** (number or wording changed) | 14 |
| **Struck** (removed from v5) | 6 |
| **Newly added** (result that did not exist in v4) | 11 |
| **On HOLD** (blocked on an in-flight task) | 4 |
| **UNVERIFIED** (no artifact found tonight — see §7) | 5 |
| **Total claims audited** | 64 |

Of the 14 corrections, **6 move against us** (CollabLLM MATH-Hard, FN-adjusted accuracy / end-to-end table, preservation attribution, WildChat headline, memory gains, auditing-on-math), **3 move in our favour** (BigCodeBench, database leak-free replication, budget accounting), and 5 are wording-only.

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
| 1.6 | AC3-Reset "outperforms the assistant-omission design-oracle" (+15.9 vs +13.3) | **unchanged** | `EXP/paired_analysis_results.txt` | verbatim |
| 1.7 | WildChat "**89.8 +/- 1.4** (Reset) and **92.1 +/- 1.3** (Augment)" | **corrected** | **F31**, `AR/tasks/T11/worklog.md` §(a); raw `AR/tasks/T11/out/order_gpt5mini.jsonl` | "**87.8 +/- 2.1** (Reset) and **91.2 +/- 2.1** (Augment) … order-balanced values from a full re-judge" |
| 1.8 | WildChat "over 3 **seeds**" | **unchanged** | **F4** — WildChat's N=3 *are* real seeds (42/43/44), confirmed in `AR/tasks/T11/worklog.md` | keeps "seeds" |
| 1.9 | CW3 end-to-end table: Full context 87.5±2.0, **AC3-Reset 100.0±0.0**, **Gated-Reset 99.1±1.2** | **CORRECTED — the largest numeric change in v5** | **F28**. Those were FN-*adjusted*. Source rows: `EXP/exp1_results.txt` (rep1: reset "100.00% (39/39) [1 excluded]"), `EXP/exp1_reps_results.txt` (rep2 "Accuracy 95.00% (38/40)" vs adjusted 100.00% (38/38) [2 excluded]; rep3 raw 87.50% vs adjusted 100.00% [5 excluded]). Baseline had **0** exclusions in all three runs | Raw: Full context **87.5 +/- 2.0** (90.0/87.5/85.0), **AC3-Reset 93.3 +/- 4.2** (97.5/95.0/87.5), **AC3-Gated-Reset 95.0 +/- 0.0**; plus an explicit self-correction paragraph |
| 1.10 | "Both operators improve over the baseline in every one of the three reruns" | **unchanged in substance**, wording fixed | holds on raw: Reset +7.5/+7.5/+2.5, Gated +5.0/+7.5/+10.0 | "…in every one of the three **runs**", with per-run deltas shown |
| 1.11 | "not an artifact of … replay, or a **single seed**" | **corrected** (wording) | **F4** — `cfg.seed` is inert on LiC; replicates varied by temperature-1.0 sampling only | "…or a **single run**", plus a new paragraph stating that LiC/CollabLLM intervals estimate **decoder variance** |
| 1.12 | *(new)* | **newly added** | **F28**, `AR/tasks/T1/RESULTS.md` (adjusted-vs-raw columns), `AR/tasks/T1/fn_rejudge.json`, `AR/tasks/T14/worklog.md` §1 (file:line mechanism) | New CW2 paragraph disclosing the FN-adjustment bias (9% vs 62% exclusion; 89.0% → 77.1%) and committing to raw reporting |
| 1.13 | CW4 tau2 table (FC 68.4/31.6/26.3; AO 0/0/0; best AC3 84.2/57.9/73.7) | **HOLD** | **T6 in flight.** Interim N=3 Baselines: gpt-5.4 68.4±13.9, DSV4F **70.2±11.0** (published 31.6), Kimi **80.4±2.5** (published 26.3) — `AR/tasks/T6/worklog.md` 15:10 entry | Table moved inside a `⚠ INTERNAL — HOLD` block with fallback wording drafted |
| 1.14 | "Assistant omission collapses to 0% on every model" | **unchanged, and strengthened** | T6 positive control #2: AO rollouts terminate on `max_steps`, never `user_stop`, while the other four arms return reward 1.0 in the same process — `AR/tasks/T6/worklog.md` 13:58 | Promoted to carry CW4 on its own, with the mechanism stated |
| 1.15 | Kimi footnote: "rate-limit-clipped, so we quote a conservative **+24 to +34pp**" | **struck** | **T6 interim**: the whole Kimi baseline cell is a clipped floor; re-measured 80.4 is above every published Kimi AC3 number. A "conservative" range off a broken control is not conservative | removed |
| 1.16 | "only **1 of 11** baseline failures on gpt-5-mini attributable to context pollution" | **unchanged** — but see §7 (U4) | paper tex L360/L558 via `neurips_review/worklog.md:158`; not re-verified tonight | verbatim |
| 1.17 | tau2 "confirms the rule: lightest operator wins on the strongest model, heaviest on the weakest" | **struck (pending T6)** | derived from the same N=1 cells T6 is re-measuring | removed; replaced by the analyzer-sweep evidence (F21/F22) as the CW1 generality argument |
| 1.18 | CW5: "**We are adding** a condensation baseline at matched compute … our prediction is …" | **replaced by results** | **F27**, `AR/tasks/T1/RESULTS.md`, `AR/tasks/T1/analyze.py`, `OUT/T1/main/*` | Full 10-row accuracy table, head-to-head paired deltas, measured budgets, MT-OSC engagement rate |
| 1.19 | CW5 baseline-justification prose (pollution vs. length pressure) | **unchanged** | — | verbatim, now followed by the measurement |
| 1.20 | *(new)* | **newly added** | **F27**, `AR/tasks/T1/RESULTS.md` "Measured budget" table (from `utils/call_meter.py`) | Budget-matched summariser **over-consumed** AC3-Reset: 1.02–1.19x strategy calls, 1.62–2.14x strategy tokens, still lost by 12–28pp; Gated-Reset +17.8pp on **0.41x** Reset's calls |
| 1.21 | *(new)* | **newly added** | **F27** + PROVENANCE dead-ends table | MT-OSC at w=4 fires **0.3x/conversation** on 4.1-turn conversations → *structurally inapplicable*, reported as a scoping result, **not** as a beaten baseline |
| 1.22 | *(new)* | **newly added** | **F21/F22**, `AR/tasks/T9/worklog.md` §pooled table, `OUT/T9/{rep1,rep2}/` | CW1 now cites the five-analyzer sweep (+12.9 to +39.9pp, all significant, none below baseline) as the empirical form of "the analyzer is the shared component" |

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
| 3.11 | *(new)* | **newly added** | **F25**, `AR/tasks/T2A/RESULTS.md` §"Contrast: AC3-Rewrite" | Operator-level mechanism distinction added to Q4: Reset = detect/discard/re-derive (97.6 removal, 4.0 preservation); Rewrite = selective (27.0 / 38.9) |

---

## 4. `03_reviewer_5YHP.md`

| # | Claim as written in v4 | Status | Evidence | New wording in v5 |
|---|---|---|---|---|
| 4.1 | W1 scope defence (structural exclusion is the scope, not a gap; Table 5; Appendix D) | **unchanged** | — | verbatim |
| 4.2 | *(new)* | **newly added — the strongest new mechanism evidence** | **F10**, `AR/tasks/T2c/RESULTS.md`, `AR/tasks/T2c/{answer_check.jsonl,math_numeric_probe.json,leak_labels_final.jsonl}`; source traces `~/ac3/recovered_t2c/ctx_editor/outputs/post_neurips_ac3_phase1/` | Auditing-vs-re-solving table: leak rates (code 0%, database 1%, actions 2%, math 38%) and leak-free gains (code **+30.2**, database **+26.0**, pooled **+20.7 [+14.8, +25.3] p<0.0001**) |
| 4.3 | *(new)* | **newly added — concession** | **F10** | **Math conceded outright**: leak-free gain **−2.6pp** (n=77, p=0.815); math's entire +9.7pp sits on the leaking subset. Conceded in the same paragraph, before the wins |
| 4.4 | W1 "On tau2-bench … blanket omission scores 0% on all three models **while AC3 beats full context on all three**" | **half struck** | AO=0% corroborated by T6 PC2; the AC3 half depends on the contested cells | Keeps AO=0% with the mechanism; drops "AC3 beats full context on all three" pending T6 |
| 4.5 | W1 "On WildChat, AC3 wins **72-92%** of pairwise comparisons" | **corrected** | **F31** | Replaced by the order-balanced headline (87.8 / 91.2). The 72–92% per-cell range was **not** re-judged and is retired from reviewer-facing text (see §7 U3) |
| 4.6 | W3 end-to-end numbers 87.5 / 100.0 / 99.1 | **corrected** | as 1.9 | raw 87.5 / 93.3 / 95.0 + self-correction sentence |
| 4.7 | W3 replay-is-causal defence | **unchanged** | — | verbatim |
| 4.8 | W4 CollabLLM table: MATH-Hard 95 / 90 / **100 (Augment)** | **CORRECTED — claim struck** | **F16**, `AR/tasks/T8/worklog.md` §6, §8; `OUT/T8/*` | N=3: Full context **91.7 ± 5.8**, AC3-Augment **91.7 ± 7.6** — **exactly tied**, identical 55/60 per-problem totals, per-replicate delta 0.0 ± 8.7. v5 says AC3-Augment **matches** Baseline: refutes the regression, claims no improvement |
| 4.9 | W4 CollabLLM BigCodeBench 5 / 15 / **20 (Reset)** | **corrected — strengthened** | **F17/F18**, `AR/tasks/T8/worklog.md` §6, §9; `OUT/T8/seed1234_{reset,baseline}_bigcodebench` | N=3: Reset **21.7 ± 5.8** vs Baseline **6.7 ± 5.8**, +15pp in 3/3 replicates, 9 problems solved that Baseline never solves, and it reproduces on a **fully disjoint** draw (3/20 vs 1/20). Quoted as "≈1 in 5, ±1 problem" |
| 4.10 | W4 AO cells (90 MATH-Hard, 15 BigCodeBench) | **unchanged**, now flagged | not re-replicated tonight (T8 ran 4 cells = 2 arms x 2 datasets) | dagger footnote: "assistant-omission cells are single runs and were not re-replicated" |
| 4.11 | W4 "executable tests are unavailable because the simulator does not transmit the required function signatures, which is a property of the benchmark harness" | **STRUCK — factually wrong** | **F18** / `AR/tasks/T8/worklog.md` §5: the CollabLLM BigCodeBench path is `eval_method: pass_rate` → `judge_pass_rate` → `bigcodebench.eval.untrusted_check`, i.e. **real test execution**. (This also corrects RECON Unknown #7) | Replaced with a correction *in the reviewer's favour*: the numbers **are** execution-based pass rates, but they are library-version sensitive; every cell re-scored offline in one unified environment with a canonical-solution pre-flight (19/20) |
| 4.12 | W4 "the judge discriminates sharply … v8-Rewrite 17.6% vs Reset 0% on gpt-5.4; 16.7% vs 0% on Kimi-K2.6" | **struck** | moot once scoring is execution-based (4.11); also not re-verified tonight (see §7 U1) | removed |
| 4.13 | W4 "**We will add** judge-agreement and position-bias checks for WildChat" | **replaced by results** | **F30/F31/F32/F33**, `AR/tasks/T11/worklog.md` §(a)–(d), `AR/tasks/T11/out/*.jsonl` | Position bias (+5.5pp toward slot 2, p=1.8e-4, opposite-signed on the other two judges); corrected headline; PABAK 0.79–0.83 / AC1 0.84–0.87; self-consistency 96.9%; punitive 2-of-3 rule 82.5%; positive controls 39/40, 36/40, 40/40 |
| 4.14 | *(new)* | **newly added — disclosure** | **F33** | "our judge does not run at temperature 0 … the provider overrides it to 1.0. The 96.9% self-consistency figure replaces any determinism claim" |
| 4.15 | W5 "**We are adding** a span-level evaluation … removal recall / preservation precision / gating accuracy … as a confusion matrix" | **replaced by results** | **F23/F24/F26**, `AR/tasks/T2A/RESULTS.md`, `AR/tasks/T2A/{inject.py,measure.py,manifest.jsonl,per_conversation.json}`, `OUT/T2A/` (32 cells), commit `88cacb3` | Full judge-free constructed-pollution study with the two-span design and four offline positive controls |
| 4.16 | *(new)* | **newly added — correction to a paper claim** | **F25**, D9 | "We preserve what's correct and remove what's harmful" is attributed to **Rewrite** (27.0 removal / 38.9 preservation), **not** Reset (97.6 / 4.0, edit precision 50.4% vs 50% chance). Reset's mechanism restated as *detect, discard the assistant side, re-derive from the user side* |
| 4.17 | *(new)* | **newly added** | **F24**, `AR/tasks/T2A/RESULTS.md` §factorial | Detector-free causal ladder: harmful span **−11.1pp** on unedited context, true span **+15.1pp**; clean 24.7% → polluted 9.3% → AC3-Reset with pollutant present **59.8%** |
| 4.18 | W5 gate-open rates **97.3%** LiC (n=554), **98.3%** CollabLLM (n=119), ~72% WildChat | **unchanged** — but see §7 (U1) | session-1 source `neurips_review/03_rebuttal_plan.md:66`; consistent with **F23**'s 96.8% clean-arm open rate and **F21**'s ~97% for strong analyzers | verbatim, now supported by T2A's gate sensitivity 98.4% |
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

---

## 6. `05_final_remarks.md`

Mirrors the above. All ten revision bullets updated to the corrected numbers; four bullets converted from promise to result (condensation, detector, judge audit, memory split); three bullets added (auditing-vs-re-solving, analyzer sensitivity, memory variance); one new section added listing the six self-corrections; one `⚠ INTERNAL` HOLD note for a possible seventh (tau2).

---

## 7. Claims we could NOT verify against any artifact tonight

**These are liabilities. Confirm or cut before posting.**

| ID | Claim | Where it appears | Why it is unverified | Recommendation |
|---|---|---|---|---|
| **U1** | Gate-open rate **97.3%** on LiC (n=554) and **98.3%** on CollabLLM (n=119) | v5 `03_reviewer_5YHP.md`, W5 | Sourced only to session-1 prose (`neurips_review/03_rebuttal_plan.md:66`); no per-turn `needs_edit` tally artifact was located. T2A independently measures a 96.8% clean-arm open rate and 98.4% gate sensitivity, which is consistent but is a different quantity | **Re-derive** from `traces/*/conversation_analysis.needs_edit` before posting (cheap, no API). Otherwise quote T2A's numbers instead |
| **U2** | WildChat gpt-5.4: Reset **88.6** vs Gated-Reset **74.1** (−14.5pp) | struck from v5 | Not re-judged in T11's order-balanced sweep; per-cell judge numbers carry a ±2pp order effect (F30) | **Already struck.** Do not reintroduce |
| **U3** | WildChat per-cell range **72–92%** | struck from v5 reviewer text; retained only in the guardrails list | Only the two pooled operator cells were re-judged | **Do not mix** with the corrected headline. If the range is needed, label it "published judge, not order-balanced" |
| **U4** | tau2 gpt-5-mini: "only **1 of 11** baseline failures attributable to context pollution" | v5 `00_general_response.md` CW4, `01_reviewer_iNYK.md` W3 | Cited to paper tex L360/L558 and verified in session 1, but not re-verified tonight; and T6 may change the baseline this statement characterises | **Re-check the tex line** and re-confirm after T6 |
| **U5** | CollabLLM assistant-omission cells (MATH-Hard 90, BigCodeBench 15) | v5 `03_reviewer_5YHP.md` W4 table | T8 replicated only 4 cells (Baseline + one AC3 arm per dataset); the AO column is still N=1 | **Already footnoted** as single-run. Consider dropping the AO column entirely if the footnote reads defensively |

---

## 8. Cross-cutting rules applied throughout

1. **"Seeds" → "replicate runs at temperature 1.0"** wherever the number came from LiC or CollabLLM (**F4**, D4). WildChat keeps "seeds" — its N=3 are real. We state *what the replicates vary* and that the intervals are decoder variance; we do **not** confess a harness bug in a rebuttal.
2. **Raw accuracy everywhere on LiC** (**F28**). `adjusted_accuracy` is never quoted for a context-editing arm.
3. **Never a bare 97.6% removal rate** (**D9**). Always detection + removal + preservation + edit-precision-vs-chance, with selectivity attributed to Rewrite.
4. **Never the single-trial memory gains** (**D7**). Lead with contamination-zero; state variance as our own limitation.
5. **Concessions open the paragraph.** Applied to the CollabLLM correction, the FN-adjustment, the preservation attribution, the WildChat headline, math in the auditing analysis, and the memory noise floor.
6. **No tau2 magnitudes until T6 lands.** Five `⚠ INTERNAL — HOLD` blocks mark every affected passage (`00` x2, `01`, `04`, `05`), plus an orientation preamble at the top of `00`.
