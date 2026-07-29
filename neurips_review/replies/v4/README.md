# Replies v4 (current)

Incorporates mentor feedback (`../../mentor_feedback.md`). Built on the v3 structure, which follows the LaDiR reference format.

## Posting order

| # | File | Post as |
|---|---|---|
| 1 | `00_general_response.md` | Official Comment, all reviewers + AC. **Post first** |
| 2 | `01_reviewer_iNYK.md` | Reply to Reviewer iNYK |
| 3 | `02_reviewer_Vg97.md` | Reply to Reviewer Vg97 |
| 4 | `03_reviewer_5YHP.md` | Reply to Reviewer 5YHP |
| 5 | `04_response_to_AC.md` | Official Comment to Area Chair / SAC / PC. **New in v4** |
| 6 | `05_final_remarks.md` | Post at the **end** of the discussion period |

The General Response goes first because every per-reviewer reply cross-references its Common Weakness sections. The AC response goes after the reviewer replies so the AC encounters it once the supporting evidence is already visible on the thread.

---

# Rhetoric plan

## The one argument everything serves

> **The reviewers were right about the submitted version. The post-submission evidence answers them. Therefore the reservations were tractable, not disqualifying.**

This is aimed squarely at the AC's decisive sentence: *"if the reservations are correct, then the concerns are too large to be dealt with in the rebuttal process."* We do not contest that the reservations were reasonable. We contest only the prediction about tractability, and we contest it with completed experiments rather than promises. Every file serves this arc, and `04_response_to_AC.md` states it explicitly.

This framing matters because the alternative, arguing that the reviewers misread us, would require us to be right about seven separate things in front of an AC who has already signalled skepticism. Arguing tractability requires us to be right about one thing, and the evidence is already in hand.

## Tone

Warm, specific, and confident. We thank generously and quote reviewers' own praise back to them before any pushback, which frames the discussion around what they already agreed was valuable. We use "we would respectfully note" and "our best reading is" when disagreeing, never "the reviewer is incorrect." Firmness comes from the numbers, not from the register.

## Concede precisely, defend broadly

We make exactly **three** concessions, each chosen because a reviewer was verifiably right, and each paired immediately with a completed fix:

| Concession | Fix shown |
|---|---|
| Best-of-3 was the wrong statistic to headline | Replaced with mean +/- std and paired tests |
| The database result rested on a single run | Now replicates across all three models at n=147 per cell |
| The analyzer was never evaluated as a detector | Span-level precision/recall evaluation being added |

Conceding these three cheaply buys credibility for the places we hold firm:

| We defend | On what basis |
|---|---|
| Method changes per benchmark | The matrix demonstrates one method, one code path. CollabLLM and tau2 are the stated theory applied, not exceptions |
| Hard-subset selection bias | Difficulty stratification does what it is designed for, and gains now hold on a random subset regardless |
| Replay is not end-to-end | Replay is a causal-attribution design; the new end-to-end run supplies complementary evidence |
| Soft-attention gap (5YHP W1) | This is the precise scope of the claim, tested adversarially, not an unexamined assumption |
| Baselines are too weak | We target pollution; compaction targets length pressure. Justified positively, with a condensation baseline added to test the boundary |
| CollabLLM below AO | Withdrawn as a user-simulator artifact |
| Memory is mixed | Optional and ablated. The reviewer's diagnosis supports our thesis rather than undercutting it |

## Rules we hold to

1. **Never dispute a checkable fact.** iNYK correctly quoted tau2 Baseline 53.3 vs. Gated-Reset 48.3 from our own appendix. We reframe what the number means and never contest the number. Disputing it would take the AC thirty seconds to falsify.
2. **Every defence carries a number.** Assertion alone reads as evasion in a rebuttal where the AC has pre-committed to skepticism.
3. **Convert the strongest attacks into wins where the data allows.** iNYK's sharpest specific hit, the single-run database claim, is now among the best-supported results in the paper. 5YHP's CollabLLM objection dissolves into a simulator artifact.
4. **Answer once, then cross-reference.** Shared concerns live in Common Weakness sections. This respects reviewer time and signals a coordinated response rather than three defensive ones.
5. **Remaining limitations go to the camera-ready appendix, not here.** Full disclosure is a commitment we honour after acceptance, not a reason to argue against ourselves during review.

## What we deliberately do not do

The LaDiR reference includes a section challenging whether two reviews were independent or AI-generated. **We do not make that move.** Our three reviews are visibly independent, engage closely with our actual content, and several criticisms landed correctly. Raising that argument would read as bad faith and would very likely cost us the AC.

---

# Changes from v3

## 1. Corrected the gating claim (mentor's catch, and a real error)

v3 said the gate "opens on at least 97% of text turns... so its errors are dominated by **false negatives** (missed interventions) rather than spurious harmful edits."

This was backwards. If the gate opens 97% of the time it is intervening almost always, so its errors are predominantly **false positives**, meaning edits made when nothing needed fixing. The v3 sentence conflated the overall error profile with a separate observation about the small minority of turns where the gate closes.

**This correction mattered.** 5YHP asked specifically for a "breakdown of harmful false-positive edits and missed pollution." Shipping an inverted claim into a reply to the one reviewer who asked precisely that question would have been costly.

The v4 text (in `03_reviewer_5YHP.md`) now:

* Reports the measured rates plainly: 97.3% on LiC (n=554), 98.3% on CollabLLM (n=119), against the roughly 72% 5YHP observed on WildChat.
* Frames the gate as **deliberately high-recall**, reflecting a judgement that missing pollution costs more than editing unnecessarily.
* Adds a genuinely independent supporting argument: **always-on Reset edits every turn by construction, yet it is our strongest operator** (33 of 36 paired wins, +15.9pp), and on WildChat with gpt-5.4 it **beats Gated-Reset by 14.5pp** (88.6 vs. 74.1). If spurious edits were damaging, an always-on editor would be penalised on exactly the turns where the gate would have closed. It is not. (Avoid leaning on the LiC Gated = Reset identity of 68.95% here: the two coincide *because* the gate rarely closes, so that comparison is close to tautological.)
* Declines to claim a precision/recall direction, since firing rates say how often the gate fires and not how often it was right to fire. That is exactly what the detector evaluation supplies.

This turns a wrong claim into a defensible one without conceding ground, and it makes the promised detector metric read as the natural next step rather than as a patch.

Note for internal awareness, not for the rebuttal: a gate that opens 97% of the time also saves little compute on text, which weakens the cost-saving rationale for gating. No reviewer raised this, so we do not volunteer it. It belongs in the camera-ready limitations section, and the honest framing there is that gating earns its place in stateful settings where an unnecessary edit is genuinely risky, not as a cost lever on text.

## 2. Added `04_response_to_AC.md` (new)

Addresses the meta-review directly, which no previous version did.

* **On "validity of theoretical assumptions."** No reviewer raised an objection in formal or theoretical terms, so we offer our best reading (5YHP's W1, the scope condition for structural exclusion) and invite correction. We then make the substantive point from the mentor: context pollution is a phenomenon characterised **empirically rather than formally**, and our contribution is comparable in kind to Laban et al. (2025) and Huang et al. (2026), in the same register of falsifiable predictions tested against controlled experiments. We also note the condition is tested adversarially in Table 5 and past its own boundary in Appendix D, which is the opposite of an unexamined assumption.
* **On tractability.** The closing paragraph makes the indirect argument the mentor suggested: each reservation proved answerable within the window, and the resulting numbers strengthen rather than qualify the claims. Phrased as a favourable reading rather than a rebuke.
* Consolidates the headline evidence into a single table so the AC can evaluate the response without reading four reviewer threads.

## 3. Renumbered

`04_final_remarks.md` became `05_final_remarks.md` to make room for the AC response.

---

# Accuracy guardrails

* Report **best operator per cell**, never "every operator beats baseline."
* tau2 Kimi gain quoted **conservatively (+24 to +34pp)**; that baseline was rate-limit-clipped.
* WildChat honest range is **72-92%**.
* Exclude **Rewrite** from the paired-statistics claim (pre-analyzer-parity, superseded by R6).
* Gate firing rates are **not** precision/recall. Do not restate them as an error-profile claim.

# Before posting

* Verify numbers against `../../experiments/*.txt` and `../../experiment_todos.md`.
* Push the paper edit (inner repo `b1a629a`) so the PDF matches the rebuttal. See `../../paper_edits_needed.md`.
* The two in-flight items (condensation baseline, detector metric) are written as in-progress commitments, not as results. No text needs filling before posting. If they land during the discussion period, post the numbers as a follow-up comment (v5).
* Coordinate with co-authors before posting.
