# T17 — Denominator mismatch audit (ERGO vs the rest of tab:main)

## 16:0x — start
Read T14 RESULTS.md + WORKLOG F28/F40–F42. Confirmed the claim shape:
tab:main prints percentages that back out to denominators 20/19/25/23 for most rows
but 23/25/25/25 for ERGO. Goal: establish ground truth per row, recompute on the
uniformly filtered pool, produce corrected table.

Plan:
1. Independently re-derive numerator/denominator for every printed cell (exact rational search).
2. Locate the pool filter files + the replay pools; confirm 20/19/25/23.
3. Hunt disk for ERGO per-sample results (T14 says gone — verify myself, incl. snapshot).
4. Positive control: reproduce non-ERGO published cells from whatever source I find.

## 16:20 — denominators independently confirmed; ERGO provenance FOUND
Rational reconstruction over d in [15,30] of every printed tab:main cell reproduces
T14's inference exactly. ERGO = 16/23, 11/25, 3/25, 12/25 is the ONLY consistent
solution for all four ERGO cells (unique fit for 69.6, 44.0, 12.0, 48.0 in that range).

**Provenance located** (T14 said "no provenance record anywhere"; that was wrong —
it is in the *paper repo's* git history, not the code repo):
`writing/overleaf_repo` commit `d856247` (2026-05-07) "revise: ERGO with proper-prompt
rerun", message body states verbatim:
  "ERGO row in Table 1a now reports the proper-prompt local re-run
   (16/23, 11/25, 3/25, 12/25) -> 69.6 / 44.0 / 12.0 / 48.0 ...
   the local runs at outputs/2026-05-01/23-* use the actual ERGO rewrite prompt."
Earlier commit `b9a2ee8` (2026-05-03) had ERGO = 76/65/15/60 from a concat-style stand-in.
So the denominators 23/25/25/25 are confirmed from the author's own commit message, not
just back-inferred. Next: locate outputs/2026-05-01/23-*.
