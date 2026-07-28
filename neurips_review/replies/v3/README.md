# Replies v3 (current)

Restructured to match the LaDiR rebuttal format recommended by the advisor (`../../ladir_rebuttal.md`).

## Posting order

| # | File | Post as |
|---|---|---|
| 1 | `00_general_response.md` | Official Comment, all reviewers + AC. **Post first.** |
| 2 | `01_reviewer_iNYK.md` | Reply to Reviewer iNYK |
| 3 | `02_reviewer_Vg97.md` | Reply to Reviewer Vg97 |
| 4 | `03_reviewer_5YHP.md` | Reply to Reviewer 5YHP |
| 5 | `04_final_remarks.md` | Post at the **end** of the discussion period |

The General Response must go up first because all three per-reviewer replies cross-reference its Common Weakness sections.

## What changed from v2

v2 was correct on substance but organised around our own analysis rather than around the reviewers' text. v3 adopts the reference format:

1. **Thematic Common Weakness sections** (1-5) in the General Response, each attributed to the reviewers who raised it. Shared concerns are answered once, and per-reviewer replies point to them. This removes roughly a third of the duplication in v2.
2. **Reviewer text quoted in blockquotes**, with responses labelled `W1`, `Q1`, and so on to mirror each reviewer's own numbering. 5YHP numbered W1-W6 and Vg97 numbered Q1-Q4, so those map directly.
3. **Opens with Common Strengths**, quoting each reviewer's own praise. This is standard in the reference and frames the discussion before any rebuttal.
4. **Explicit "Revision:" commitments** after each substantive response.
5. **Added `04_final_remarks.md`**, a closing Summary of Key Revisions cross-referenced to reviewer IDs and weakness numbers.
6. Warmer register throughout, with firmer technical pushback where we have evidence.

## Deliberately NOT copied from the reference

The reference includes a section challenging the independence and quality of two reviews. **We should not do this.** Our three reviews are clearly independent and substantively different, they engage closely with our actual content, and several of their criticisms were correct. Raising that argument here would read as bad faith and would likely cost us the Area Chair.

## Where we push back rather than concede

| Concern | Our position |
|---|---|
| Method changes per benchmark | Demonstrated as one method via the matrix. CollabLLM and tau2 configurations are the stated theory applied, not exceptions |
| Hard-subset selection bias | Difficulty stratification does what it is designed for; and the gains now hold on a random subset, so it is no longer the primary evidence |
| Replay is not end-to-end | Replay is defended as a causal-attribution design; a new end-to-end run supplies the complementary evidence |
| Soft-attention gap (5YHP W1) | This is the precise scope of the claim, not a gap. The operator family covers referential settings, with tau2 and WildChat as direct evidence |
| Weak baselines | We target pollution; compaction targets length pressure. Justified positively, with a condensation baseline added to test the boundary |
| CollabLLM below AO | Withdrawn as a user-simulator artifact. AC3 leads on both datasets with a competent simulator |
| Memory is mixed | Optional and ablated; no headline claim depends on it. The reviewer's diagnosis supports our thesis rather than undercutting it |

Where we do agree (best-of-3 was the wrong statistic, the database claim needed replication, the analyzer should be evaluated as a detector), we say so plainly and show the fix. Remaining limitations go in the camera-ready limitations appendix, not here.

## Accuracy guardrails

- Report **best operator per cell**, never "every operator beats baseline."
- tau2 Kimi gain quoted **conservatively (+24 to +34pp)**; that baseline was rate-limit-clipped.
- WildChat honest range is **72-92%**.
- Exclude **Rewrite** from the paired-statistics claim (pre-analyzer-parity, superseded by R6).
- iNYK quoted tau2 Baseline 53.3 vs Gated-Reset 48.3 correctly from our own appendix. We reframe what it means and never dispute the number.

## Before posting
- Verify numbers against `../../experiments/*.txt` and `../../experiment_todos.md`.
- Push the paper edit (inner repo `b1a629a`) so the PDF matches. See `../../paper_edits_needed.md`.
- Fill in the two in-flight results (condensation baseline, detector metric) if they land before the deadline.
- Coordinate with co-authors.
