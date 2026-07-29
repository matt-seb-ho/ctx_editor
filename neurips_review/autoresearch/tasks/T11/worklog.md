# T11 — WildChat judge-agreement and position-bias checks

**Started:** 2026-07-29 (overnight autonomous session)

## Commitment being delivered
`neurips_review/replies/v4/03_reviewer_5YHP.md`, W4 Revision line, verbatim:

> **Revision:** We will report the corrected CollabLLM numbers, add execution-based scoring where the harness permits, **add judge-agreement and position-bias checks for WildChat**, and footnote the per-method sample counts, which differ because each method is evaluated against its own assistant-omission failure pool.

Also relevant (W4 body): "On **WildChat**, results are over 3 seeds with tight intervals (Reset **89.8 +/- 1.4**, Augment **92.1 +/- 1.3**), spanning 72-92% across cells."

So the deliverable is exactly: (1) position-bias check on the WildChat pairwise judge, (2) judge-agreement check. Scoped to WildChat only.

## Log

### 00:00 — Setup
- Read 5YHP v4 reply + RECON worklog §B.3 (WildChat/Huang harness map).
- Key facts from RECON: harness at `src/ctx_editor/huang_eval/`, judge prompt at
  `src/ctx_editor/huang_eval/prompts/pairwise_judge.txt` (emits `quality_winner`,
  `ontopic_winner`, `confidence`; **A/B order randomized by caller's rng** — so the
  existing numbers are already partially order-randomized; need to check this in code).
- Headline source: `outputs/post_neurips_ac3_phase3_huang/*_seed{42,43,44}_*`, N=3 real seeds.
- All prior outputs off disk; extracting from `~/ac3/blob_staging/snapshot.tar.gz`.
