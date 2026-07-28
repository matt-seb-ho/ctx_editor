# Replies v2

Paste-ready OpenReview comments. One file per comment to post.

| File | Post as |
|---|---|
| `00_general_response.md` | Official Comment to all reviewers + AC |
| `01_reviewer_iNYK.md` | Reply to Reviewer iNYK |
| `02_reviewer_Vg97.md` | Reply to Reviewer Vg97 |
| `03_reviewer_5YHP.md` | Reply to Reviewer 5YHP |

## What changed from v1

v1 was written in a concede-then-convert register. v2 is written to project strength, per the agreed strategy: defend our choices, lead with the post-submission matrix, and reserve full disclosure for a camera-ready limitations appendix.

Concrete changes:
1. **Leads with the mega-table.** The same four operators are now run across 3 models x 4 LiC tasks x 3 prefixes, plus CollabLLM, WildChat, and tau2. This is the direct answer to "the method changes per setting," which the AC named first.
2. **Adds paired significance** (new, zero API cost): AC3-Reset improves over full context on 33 of 36 paired comparisons, mean +15.9pp, sign-test p < 0.0001. This is exactly the paired test Vg97 asked for.
3. **Turns iNYK's strongest specific attack into a win.** The contested "exceeds the oracle on database" result now replicates across all three models at scale (Reset 49.0 / 56.2 / 55.1 vs AO 45.6 / 27.9 / 30.6).
4. **Defends the baseline selection** rather than apologising for it: we target pollution, not context-length pressure. Compression baselines are being added to test the boundary.
5. **Defends replay** as a deliberate causal-attribution design, backed by the new end-to-end run.
6. **Reframes tau2** using the failure-mode data: on gpt-5-mini only 1 of 11 baseline failures is pollution-attributable, so that cell was never pollution-limited. On models where pollution binds, AC3 delivers double digits.
7. Removes hedging language, cuts length, minimises em dashes.

## Claims that must stay accurate

Do not let the strength framing drift into these:
- Report **best operator per cell**, never "every operator beats baseline" (6 sub-baseline cells exist in Table 2).
- tau2 Kimi gain is quoted **conservatively (+24 to +34pp)** because that baseline was rate-limit-clipped.
- WildChat honest range is **72-92%**.
- Exclude **Rewrite** from the paired-statistics claim: those rows are pre-analyzer-parity and superseded by R6.
- iNYK correctly quoted tau2 Baseline 53.3 vs Gated-Reset 48.3 from our own appendix. Reframe what it means, do not dispute the number.

## Before posting
- Verify numbers against `../../experiment_todos.md` and `../../experiments/*.txt`.
- Push the paper edit (inner repo `b1a629a`) so the PDF matches. See `../../paper_edits_needed.md`.
- Coordinate with co-authors.
