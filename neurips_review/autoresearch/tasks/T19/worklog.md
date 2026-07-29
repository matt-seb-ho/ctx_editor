# T19 — Fold the settled findings into `replies/v5/`

**Dispatched** 2026-07-29 ~17:15. **Scope:** writing and verification only; **no experiments run, zero API calls.**
**Constraints honoured:** `writing/overleaf_repo/` not touched (not even read-modified); no `git checkout` anywhere in this shared tree.

**Inputs read in full:** `AR/WORKLOG.md` (F1–F49), `replies/v5/{CHANGES.md,README.md,00..05}`, `AR/tasks/T17/RESULTS.md`, `AR/tasks/T18/worklog.md`, `AR/PROVENANCE.md` (lineage block). `AR/tasks/T14/RESULTS.md` was consulted via F40–F42 in the central log rather than read end-to-end — noted under "not verified" below.

---

## 1. What I resolved

### 1a. T14 (FN adjustment) — provisional flags lifted, and the pool filter is now *defended*

T15 had flagged every LiC figure in v5 as "provisional pending T14". T14 landed in the paper's favour, so the flag comes off. The substantive reframing, which I propagated everywhere the FN adjustment is discussed:

* `tab:main`'s 20/19/25/23 denominators come from an **arm-symmetric pool-level pre-filter** (`data/baseline_traces_v2/*_false_negatives.json`, computed on baseline traces, applied identically to all arms). **This is correct and is to be defended, not conceded** (F42). I added this as cross-cutting rule 9 in `CHANGES.md` §8 specifically to stop the existing FN-adjustment concession from bleeding into an admission that the denominators are wrong — that was a live drift risk, because v5 concedes the FN metric loudly in five places.
* Only *per-run* `adjusted_accuracy` is invalid (F41): reset arms inflate +13.9 to +55.9 pp against +0.2 to +6.5 for no-reset arms, mechanism being 1.00 user turns/sample on Rewrite vs 5.35 on baseline. It touches ≤4 `tab:main` cells at ≤1 sample each, 2 of which favour prior work.
* The two flips (AC3-Rewrite code +46.0 → −5.3, actions +22.4 → −1.5) are **not published errors** — no Rewrite LiC row in `tab:main`, and `tab:megatable` is raw.
* Reset and Gated-Reset win all 8 cells under raw, shipped-adjusted and corrected alike (F40).

**No accuracy figure in the reply set moved.** v5 was already raw throughout, which is exactly the outcome T15's precaution was designed to produce.

Edits: `00` orientation preamble item 1 rewritten; `README.md` blocker 3 rewritten; `CHANGES.md` claim 1.24 + §8 rule 9 + §9 row.

### 1b. T17 + T18 (ERGO denominator defect) — disclosed in five places

Written into the reviewer-facing text at:

| file | location | why there |
|---|---|---|
| `00_general_response.md` | **CW5**, three paragraphs between the baseline-justification paragraph and the condensation results | CW5 is where ERGO is named, and the flow "here is our baseline set → here is an error in how one of them was scored → here is the new baseline we ran" is the honest order |
| `01_reviewer_iNYK.md` | end of the **W1** answer | iNYK's W1 *is* the small-samples/noise complaint. Landing it there makes the disclosure read as his point being vindicated rather than as an unprompted confession |
| `02_reviewer_Vg97.md` | **W1** answer | Vg97's central weakness is the baseline set. A defect in how an existing baseline was scored belongs there, and F49 ties directly back to his W2 |
| `04_response_to_AC.md` | numbered correction **5**; lead-in "four" → "five" | The AC letter's tractability argument runs on self-surfaced corrections. This is the strongest instance available |
| `05_final_remarks.md` | numbered correction **7**; condensation bullet cross-referenced | Mirrors `04` |

**Numbers shipped:** math 69.6 → **80.0** (above AC3-Reset 75.0, level with AC3-Gated-Reset 80.0); code **≈44.0**; database 12.0 untouched; actions **unclosable**, promised as an interval only.

**T17's 57.9 for code is nowhere in the reply set.** I checked by grep: every remaining `57.9` is either the tau2 HOLD table (unrelated) or an explicit "do not ship this" guardrail. Shipping it would have overstated a competitor by ~14 pp (F48) — the mirror image of the defect we are disclosing, and I treated it as equally disqualifying.

**F49 leads the framing in all five places**, per the brief: no ERGO-vs-AC3 `tab:main` difference is significant at n≈20 in either direction (code p=0.375, math p=1.00), and this is noted to be true of the published table as well as the corrected one. I also added a guardrail (`README.md`, `CHANGES.md` §8 rule 8) forbidding the obvious compensating move — claiming ERGO "still loses overall" — since the measured scorecard is 3/12 ERGO wins-or-ties against a published 1/12.

**Precision correction I made to my own first draft.** My initial wording in `00` and `04` was "we re-ran ERGO on the filtered pools". That overstates what T18 did: the positive control did **not** reproduce (ERGO/database 44.0 vs published 12.0, because `gpt-5-mini` is unreachable), so no absolute level from T18's runs is substitutable into `tab:main`. What was actually measured is *k*, the pruned-item split, and the corrected cells are published-numerator-over-corrected-denominator. I rewrote both passages to "we measured the correction rather than estimating it … we replayed ERGO against those excluded items directly", and recorded the full precision note in `CHANGES.md` §9. The reply text says "roughly half" on code rather than quoting 43.9, which is the level of precision that survives the control failure.

### 1c. T16 (gate stats) — U1 retired, firing-rate caveat added

* `CHANGES.md` §7 **U1 struck through and retired**, with the reason preserved rather than deleted: the artifacts do exist at `scripts/analysis_rewrite_v_reset/data/gated_reset_reconstructed_{lic,collabllm}.md`, and T16 re-derived both independently from raw traces at zero API cost. Claim row 4.18 updated from "unchanged — but see U1" to "corrected (T16), and U1 retired".
* New paragraph in `03_reviewer_5YHP.md` W5 (claim 4.18a): the rates are a **firing rate, not a detection rate** — 29% (LiC) / 73% (CollabLLM) of gate-open records have the analyzer writing `issues: "None"` while setting `needs_edit=true`. Redirects the detection claim to T2A's 78.6% pollutant-naming rate. I placed it *before* the existing "we would not over-read firing rates into a precision/recall claim" sentence so that sentence now lands as a conclusion with evidence rather than as a bare hedge.

---

## 2. What I deliberately left alone

**All five `⚠ INTERNAL — HOLD` blocks (T6/tau2) are byte-identical to what T15 wrote**, verified mechanically: `git diff -U0 | grep '^[-+].*⚠ INTERNAL'` shows **zero removed HOLD lines**. The pre-drafted withdrawal wording is untouched. The T6 item in `00`'s orientation preamble is also byte-identical — I rewrote items 1 and 3 around it without touching item 2.

I did not resolve, soften, delete or guess at anything tau2. T6's preliminary Baseline cells (DSV4F 70.2 ± 11.0, Kimi 80.4 ± 2.5 against published 31.6 and 26.3) are recorded in `CHANGES.md` §9 as "STILL RUNNING / Unknown" and nowhere else.

**A bookkeeping collision I resolved without touching the holds.** Adding an ERGO correction to the numbered lists in `04` and `05` makes the HOLD blocks' internal references stale — `04`'s block calls the pending tau2 withdrawal "a fifth correction" and `05`'s says "add a seventh item". Rather than edit the blocks, I added a separate `⚠ INTERNAL — T19 renumbering note` immediately *after* each one, recording that tau2 becomes item 6 and item 8 respectively, and stating explicitly that the block above was left byte-identical on purpose. This raises the total `⚠ INTERNAL` marker count from 6 to 8; `README.md`'s blocker list and pre-posting checklist are updated to match, and flag that only the T6 ones represent an unsettled result.

Also untouched, and worth naming because it was in reach: `writing/overleaf_repo/`. The paper-side consequences of all three audits stay queued as PAPER-1..7. I did promote **PAPER-7 (the ERGO denominator fix) to highest priority** in `README.md`'s pre-posting checklist, since the reply set now commits to it in front of the reviewers — posting the rebuttal without the paper edit would leave us having announced a fix we have not made.

---

## 3. Things I could not verify

1. **Decisions D12 and D13 do not exist.** The brief refers to "decisions D1–D13". `AR/WORKLOG.md` contains D1–D11 only, and **D11 itself is never written out** — it is referenced once, at the end of F28 ("Queued as PAPER-6, and see D11 below"), but no D11 entry follows. I cited "F1–F49, decisions D1–D11" in `CHANGES.md` and `README.md` rather than inventing coverage. Low impact; flagged so the central log can be repaired.
2. **`AR/tasks/T14/RESULTS.md` not read end-to-end.** I worked from F40–F42 in the central log plus T17's independent reconstruction of the same mechanism (`RESULTS.md` §1, with file:line). The two agree on the mechanism and on the denominators, which is a reasonable cross-check, but I did not independently re-derive the "≤4 cells at ≤1 sample each, 2 favouring prior work" claim from T14's own artifacts.
3. **The published `tab:main` percentages were not re-read from the paper.** I did not open `writing/overleaf_repo/` at all, per the brief. Every published ERGO value quoted in the reply set (69.6 / 44.0 / 12.0 / 48.0) and every AC3 comparator (75.0 / 80.0 / 57.9 / 63.2 …) is taken from T17 §2–§3 and T18 R1/R2. T17 backs these with six positive controls including a blind rational reconstruction that matched Overleaf commit `d856247` on all four ERGO cells, so I regard them as well-attested — but they are second-hand in this document.
4. **The cross-model *k* transfer is an argument, not a proof**, and T18 says so itself. If a reviewer presses on ERGO/code, the honest fallback is the union interval [42.1, 57.9], which is why the reply text commits only to "essentially unchanged" / "roughly half" rather than to 43.9.

---

## 4. Files changed

All under `neurips_review/replies/v5/`. Nothing else in the tree was written except this worklog.

| file | change |
|---|---|
| `00_general_response.md` | Orientation preamble items 1 and 3 (T14 resolved, T17/T18 resolved); summary-of-corrections sentence; three new CW5 paragraphs; CW5 Revision line |
| `01_reviewer_iNYK.md` | New closing paragraph in W1 |
| `02_reviewer_Vg97.md` | New paragraph in W1 |
| `03_reviewer_5YHP.md` | W5 gate paragraph split, firing-rate caveat inserted |
| `04_response_to_AC.md` | Lead-in "four" → "five"; new correction 5; T19 renumbering note after the HOLD block |
| `05_final_remarks.md` | Condensation bullet cross-reference; new correction 7; T19 renumbering note after the HOLD block |
| `CHANGES.md` | Header + revision history; tally 64 → 67 claims; new rows 1.23, 1.24, 2.10, 3.12, 4.18a, 5.9, 5.10; 4.18 rewritten; §6 T19 additions; §7 U1 retired + new U6; §8 rules 7–9; **new §9** integration record + ERGO precision note |
| `README.md` | Header provenance; blockers 1–4; rhetoric-plan paragraph; concessions table (9 → 10 rows); structural changes (6 → 7); guardrails (ERGO ×2, pool filter, firing rate; one redundant line removed); pre-posting checklist |

---

## 5. Biggest remaining exposure, in my judgement

**T6 / tau2**, and it is not close. Everything else in the reply set is now either measured or explicitly bounded. If the published DeepSeek-V4-Flash and Kimi tau2 baselines were rate-limit-clipped floors, then two of three tau2 cells were measured against broken controls, the AC letter needs a sixth self-correction, and `00`'s CW4 loses its table entirely — leaving the AO-collapse result to carry that section alone, which T15 has already pre-built it to do. Nothing in tonight's work reduces that exposure, and nothing should be posted until T6 returns.

Second-order: **U4** (the "1 of 11 baseline failures" tau2 claim) is unverified *and* characterises a baseline T6 may move. It appears in two files. If T6 lands badly, U4 has to be re-checked in the same pass, not after.
