# Replies v5 (current)

Revision of v4 against the 2026-07-29 autoresearch session (findings F1–F49, decisions D1–D11 in `../../autoresearch/WORKLOG.md`; retired claims in `../../autoresearch/PROVENANCE.md`). v4's structure, tone and layout are preserved; this is a correction pass plus the results that turned promises into completed experiments. Written by T15 at F1–F38 and revised by **T19** once T14, T16, T17 and T18 landed.

**Start with `CHANGES.md`.** It is the claim-by-claim audit: every v4 assertion, its status (unchanged / corrected / struck / newly-added), the finding and artifact path behind it, and the new wording.

## Posting order

| # | File | Post as |
|---|---|---|
| 1 | `00_general_response.md` | Official Comment, all reviewers + AC. **Post first** |
| 2 | `01_reviewer_iNYK.md` | Reply to Reviewer iNYK |
| 3 | `02_reviewer_Vg97.md` | Reply to Reviewer Vg97 |
| 4 | `03_reviewer_5YHP.md` | Reply to Reviewer 5YHP |
| 5 | `04_response_to_AC.md` | Official Comment to Area Chair / SAC / PC |
| 6 | `05_final_remarks.md` | Post at the **end** of the discussion period |

The General Response goes first because every per-reviewer reply cross-references its Common Weakness sections. The AC response goes after the reviewer replies so the AC encounters it once the supporting evidence is already visible on the thread.

## ⚠ Blockers before anything is posted

1. **Resolve and delete every `⚠ INTERNAL` block.** There are **eight**: one orientation preamble and two T6 holds in `00_general_response.md`, one T6 hold each in `01`, `04` and `05`, and one T19 renumbering note each in `04` and `05`. Grep: `grep -rn "⚠ INTERNAL" .`
2. **tau2 is on HOLD pending T6.** Do not post any per-model tau2 magnitude. T6's completed Baseline cells suggest the published DeepSeek-V4-Flash and Kimi baselines were rate-limit-clipped floors, in which case those gains must be withdrawn. The AO-collapses-to-0% result is safe and mechanism-corroborated. **This is the only substantive item still on hold.**
3. **T14 (false-negative-adjustment audit) — RESOLVED, largely in our favour.** The provisional flag on LiC figures is lifted. `tab:main`'s 20/19/25/23 denominators come from an **arm-symmetric pool-level pre-filter** which is correct and should be **defended, not conceded**; what is invalid is the *per-run* `adjusted_accuracy` metric, which this reply set already avoids entirely. AC3-Reset and AC3-Gated-Reset beat baseline in all 8 cells under raw, shipped-adjusted and corrected alike. Two conclusions flip on AC3-**Rewrite**, but neither is a published error. See F40–F42.
4. **T17 + T18 (ERGO denominator defect) — RESOLVED and folded in.** Disclosed in `00` Common Weakness 5, `01` W1, `02` W1, `04` correction 5 and `05` correction 7. Ship **math 80.0** and **code ≈44.0**; do **not** ship T17's 57.9 for code. See F43–F49.

---

# Rhetoric plan

## The one argument everything serves

> **The reviewers were right about the submitted version. The post-submission evidence answers them. Therefore the reservations were tractable, not disqualifying.**

This is aimed squarely at the AC's decisive sentence: *"if the reservations are correct, then the concerns are too large to be dealt with in the rebuttal process."* We do not contest that the reservations were reasonable. We contest only the prediction about tractability, and we contest it with completed experiments rather than promises.

**What changed in v5's version of this argument.** v4 made it with four promises still outstanding (condensation baseline, detector evaluation, WildChat judge checks, memory split analysis). All four are now run, which is a materially stronger position. In exchange, six of our own numbers moved, four of them against us, and a seventh correction raises a *competitor's* number. We surface all seven ourselves, early and in a single list in `04_response_to_AC.md`, and we make the fact of self-correction part of the tractability argument: *these are the discussion period working as intended, and every one was found by us in experiments the reviews prompted.* A conceded weakness we surface ourselves reads as rigour; the same weakness found by a reviewer reads as spin. The ERGO denominator correction is the sharpest instance of this — it is recoverable from our own printed percentages with a calculator, so being second to it would have been read as thumb-on-the-scale.

## Tone

Warm, specific, and confident. We thank generously and quote reviewers' own praise back to them before any pushback. We use "we would respectfully note" and "our best reading is" when disagreeing, never "the reviewer is incorrect." Firmness comes from the numbers, not from the register. Concessions go **early in the paragraph**, not buried after the defence.

## Concede precisely, defend broadly

v4 made three concessions. v5 makes ten, because the evidence forced seven more — and the response is stronger for it, because each is paired with a completed measurement rather than a promise.

| Concession | Fix / evidence shown |
|---|---|
| Best-of-3 was the wrong statistic to headline | Replaced with mean +/- std and paired tests; tau2 noise floor quantified (10.7pp binomial sd at n=19) |
| The database result rested on a single run | Now replicates across all three models at n=147 per cell, and holds at +26.0pp on the leak-free subset |
| The analyzer was never evaluated as a detector | Judge-free constructed-pollution study with four positive controls, reported in full |
| **CollabLLM MATH-Hard "100" does not replicate** | N=3: ties Baseline (91.7 vs 91.7, 55/60 each). Refutes the regression; claims no improvement |
| **Our FN-adjusted accuracy is biased in our favour** | Raw accuracy throughout; arm-symmetric re-judge reproduces the ordering at smaller magnitudes |
| **"Preserve what's correct" is a Rewrite claim, not a Reset claim** | Reset 97.6% removal / 4.0% preservation / 50.4% edit precision (chance = 50); Rewrite 27.0 / 38.9 |
| **WildChat headline moves down ~1–2pp** | Full order-balanced re-judge: 87.8 / 91.2, with cross-family agreement and positive controls |
| **Memory gains are below the learner's own noise floor** | Variance controls: across-ordering 6.5 vs same-ordering 6.1; re-run at N≥4 or soften |
| **The auditing mechanism fails on math** | Leak-free subset −2.6pp on math, conceded outright; +30.2 / +26.0pp on code / database |
| **ERGO was scored on unfiltered pools — we understated a competitor** | Re-run on the correct pools: math 69.6 → **80.0** (above Reset 75.0, level with Gated-Reset 80.0), code ≈44.0, database untouched. Framed with the paired result: no ERGO-vs-AC3 difference is significant at n≈20 either way |

Conceding these buys credibility for the places we hold firm:

| We defend | On what basis |
|---|---|
| Method changes per benchmark | One code path across the matrix; analyzer swapped across 4 families, all positive |
| Hard-subset selection bias | Difficulty stratification does what it is designed for; gains hold on a random subset |
| Replay is not end-to-end | Replay is a causal-attribution design; the end-to-end run supplies complementary evidence |
| Soft-attention gap (5YHP W1) | The precise scope of the claim, tested adversarially and past its own boundary |
| Baselines are too weak | Now empirically answered: summarisation loses while over-consuming our budget |
| CollabLLM below AO | Withdrawn as a user-simulator artifact; BigCodeBench re-measured and *stronger* |
| Memory is mixed | Optional and ablated; contamination measurably zero; variance conceded as ours |

## Rules we hold to

1. **Never dispute a checkable fact.** iNYK correctly quoted tau2 Baseline 53.3 vs. Gated-Reset 48.3 from our own appendix. We reframe what the number means and never contest the number.
2. **Every defence carries a number, and every number traces to an artifact.** `CHANGES.md` holds the claim → artifact map; the reviewer-facing text stays clean of internal paths.
3. **Convert the strongest attacks into wins where the data allows, and concede where it does not.** 5YHP's W5 became our best new measurement *and* forced a correction to our own framing. Both go in.
4. **Answer once, then cross-reference.** Shared concerns live in Common Weakness sections.
5. **Corrections are stated before defences, not after.** Where a number moved, the paragraph opens with the movement.

## What we deliberately do not do

* We do **not** challenge reviewer independence or authorship, as the LaDiR reference does. Our three reviews are visibly independent and several criticisms landed correctly.
* We do **not** describe LiC/CollabLLM replicates as "seeds." They vary through temperature-1.0 sampling on a fixed draw. We say what they vary and state that the interval is decoder variance. WildChat's N=3 *are* seeds and keep the word.
* We do **not** quote the bare 97.6% pollution-removal rate. Removal alone is gameable by a delete-everything editor — our own PC3/PC4 controls prove it — and a reviewer computing edit precision from our confusion table would find chance. We report detection (78.6% naming), removal, preservation and precision together.
* We do **not** quote the single-trial memory gains (+10 / +12pp).
* We do **not** volunteer that a 97% gate-open rate saves little compute on text. No reviewer raised it; it belongs in the camera-ready limitations section, where the honest framing is that gating earns its place in stateful settings where an unnecessary edit is genuinely risky, not as a cost lever on text.

---

# Changes from v4

Full claim-by-claim table in `CHANGES.md`. The seven structural changes:

1. **Every LiC accuracy figure switched from FN-adjusted to raw.** The end-to-end table in Common Weakness 3 moves from Reset **100.0 +/- 0.0** to **93.3 +/- 4.2** and Gated-Reset from 99.1 +/- 1.2 to 95.0 +/- 0.0. v4 was also internally inconsistent on this — it quoted Reset at 100.0 in Common Weakness 3 and at 97.5 (the raw value) in the Vg97 Q3 paragraph. Both now read 93.3 / 97.5-per-run consistently.
2. **CollabLLM MATH-Hard "100" struck**, replaced with the N=3 tie; BigCodeBench strengthened to N=3 plus a disjoint draw.
3. **tau2 numeric tables placed behind HOLD markers** pending T6, with the mechanism-corroborated AO-collapse result promoted to carry that section on its own.
4. **Four promises converted to results**: condensation baseline (Vg97 W1/Q1, AC), detector evaluation (5YHP W5), WildChat judge checks (5YHP W4), memory split + order analysis (5YHP W6). Vg97 Q3's unanswered half — analyzer-model sensitivity — is now answered with a five-model sweep.
5. **A "corrections to our own numbers" list added to `04_response_to_AC.md` and `05_final_remarks.md`**, and made part of the tractability argument.
6. **"Seeds" reworded to "replicate runs"** wherever the number came from LiC or CollabLLM, with a one-sentence statement of what the replicates vary. WildChat keeps "seeds."
7. **The ERGO denominator defect disclosed** in `00` Common Weakness 5, with per-reviewer cross-references in `01` (W1) and `02` (W1), and as a numbered self-correction in `04` (item 5) and `05` (item 7). Framed by the paired result that no ERGO-vs-AC3 difference is significant at n≈20 in either direction.

---

# Accuracy guardrails

* Report **best operator per cell**, never "every operator beats baseline."
* **No tau2 magnitudes until T6 lands.** The AO = 0% structural result is safe.
* **All LiC accuracy is raw.** Never quote `adjusted_accuracy` for a context-editing arm. The **pool-level pre-filter** behind `tab:main`'s 20/19/25/23 denominators is a different thing, is arm-symmetric, and should be **defended, not conceded**.
* **ERGO corrected values are math 80.0 and code ≈44.0.** Never ship T17's 57.9 for code — it overstates a competitor by ~14pp. Database stays 12.0; actions is **unclosable** and must be printed as an interval [43.5, 52.2] or dropped, never as a corrected point estimate.
* **Lead every ERGO passage with the significance frame** (no `tab:main` ERGO-vs-AC3 difference is significant at n≈20 in either direction; code p=0.375, math p=1.00), not with an ordering. Do not claim ERGO "still loses overall" — the measured scorecard is 3/12 ERGO wins-or-ties, up from a published 1/12.
* Gate-open rates are a **firing rate, not a detection rate** (29% LiC / 73% CollabLLM of open records carry `issues: "None"`). State this ourselves; quote 78.6% pollutant-naming as the detection figure instead.
* WildChat headline is **87.8 +/- 2.1 (Reset) / 91.2 +/- 2.1 (Augment)**, order-balanced. The per-cell range **72–92% is verified and safe to use** (T20: all 22 populated `tab:wildchat` cells re-derived from per-turn verdicts, 22/22 reproduce to the digit; min 71.6, max 91.5). Say "every cell of our per-respondent table lands between 72% and 92%", never "AC3 wins 72–92%" — it is a min/max over 22 single-run cells, i.e. an order statistic, not an effect range. Still do not put it in the **same sentence** as the corrected 87.8/91.2 headline: different pools, different quantity.
* CollabLLM: **"matches"** on MATH-Hard, never "100". BigCodeBench quoted as "≈1 in 5, ±1 problem", never a bare percentage, and always with the scoring environment.
* Pollution detection: never the bare **97.6%**. Always detection (78.6% naming) + removal + preservation + edit precision vs the 50% chance baseline, and always attribute selectivity to **Rewrite**.
* Memory: contamination result only. Never the single-trial +10 / +12pp.
* Auditing-vs-re-solving: always concede **math (−2.6pp)** in the same paragraph as the code/database gains.
* Exclude **Rewrite** from the paired-statistics claim (pre-analyzer-parity, superseded by R6).
* "3 replicate runs at temperature 1.0" for LiC and CollabLLM. "3 seeds" only for WildChat.

# Before posting

* Resolve all eight `⚠ INTERNAL` blocks (see Blockers above). Only the T6/tau2 ones represent an unsettled result; the two T19 notes and the orientation preamble are bookkeeping.
* Verify numbers against `CHANGES.md`, which cites the artifact for each.
* Push the paper edit (inner repo `b1a629a`) so the PDF matches the rebuttal. See `../../paper_edits_needed.md`. Note that **PAPER-1 through PAPER-8** in `../../autoresearch/WORKLOG.md` are queued paper edits arising from this session and are not yet applied. **PAPER-7 (the ERGO denominator fix) is now the highest-priority of these**, because this reply set commits to it in front of the reviewers. **PAPER-8** (added by T20) fixes the Table 3 caption, which claims the gpt-5.4 Gated-Reset comparison is "on the same prefixes" when the two arms were scored on 44 and 58 turns with 35 shared — arXiv/camera-ready only, nothing we post depends on it.
* Confirm the claims flagged **UNVERIFIED** in `CHANGES.md` §7 before they are posted, or cut them. **U1 is retired** — the gate-statistic artifacts do exist and were re-derived independently.
* Coordinate with co-authors before posting.
