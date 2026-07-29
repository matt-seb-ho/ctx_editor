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

### 00:25 — Recovery + harness reading complete
- Extracted from `snapshot.tar.gz` into `~/ac3/recovered/ctx_editor/outputs/`:
  `post_neurips_ac3_phase3_huang/{s15,augment}_seed{42,43,44}_*`,
  `huang_eval/{phase1,phase2,rejudge}`, `post_may26_wildchat_gpt54`.
- Verified the headline reproduces from the recovered files: `s15_seed42` →
  66/73 = **90.4%** AO-failure turns where Reset beats AO on quality, matching
  `docs/reports/post_neurips_ac3_phase3_huang.md`. 452 (AO, variant) pairs total
  across the 6 cells (225 Reset / 227 Augment); all 452 join cleanly to the 30
  Phase-1 conversations.
- Judge = **gpt-5-mini** (respondent + analyzer also gpt-5-mini), prompt
  `src/ctx_editor/huang_eval/prompts/pairwise_judge.txt`.

**Two findings from reading the harness (both matter for the checks):**
1. `judge_pairwise()` **already randomizes A/B order per call** (`rng.random() < 0.5`),
   so the headline is order-*randomized* but not order-*balanced*, and the realized
   order was **never stored** (`_judgment_dict` drops `position_assignment`). So the
   existing files cannot be re-analyzed for position bias — the judging must be re-run.
   Re-running judging only (generations reused verbatim from the recovered files).
2. **The judge did not actually run at temperature 0.** `judge_pairwise` passes
   `temperature=0.0`, but the OpenAI client prints
   `gpt-5 models require temperature=1.0, overriding 0.0 -> 1.0`. So the headline
   judge is stochastic, and self-consistency is a real (not degenerate) measurement.

### 00:30 — Positive controls (trap #1)
Control = judge each variant response against a **degraded copy of itself**
(first 25% truncated mid-sentence + generic filler tail), judged in **both** orders.
Smoke results, all "good" wins:
- gpt-5-mini: 6/6 ✅  · DeepSeek-V4-Flash: 4/4 ✅ · Kimi-K2.6: 4/4 ✅
Full n=20-pair controls queued for all three judges. Also: `judge_once` in my
harness **never coerces a failure to "tie"** (the shipped `judge_pairwise` does —
that is exactly the silent-0.0 class of bug); failures are recorded as `ok:false`
with the error text and excluded from denominators, with counts reported.

### 00:35 — Runs launched
- Judge A (gpt-5-mini, = headline judge): **all 452 pairs × 2 forced orders** (904 calls), running.
- Shared cross-judge subset frozen at `out/subset160.json` — 160 pairs, stratified
  ~27 per cell, deterministic (seed 1234).
- Second/third judge families verified live on `mgalley-foundry2` via
  `load_balancer=t9_foundry_trapi`: DeepSeek-V4-Flash (~16 s/call), Kimi-K2.6 (~45 s/call).
- Script: `neurips_review/autoresearch/tasks/T11/rejudge.py` (self-contained; does not
  modify anything under `src/`). Outputs to `neurips_review/autoresearch/tasks/T11/out/`
  (T11-scoped, per trap #3).

### 01:05 — Runs in flight, first partial numbers (do not quote — interim)
Progress: gpt-5-mini 294/904 judgements, DeepSeek 166/320, Kimi 67/320. **0 hard failures** on all three.

Interim (gpt-5-mini, 147 pairs of 452 complete): variant-second 93.2%, variant-first 87.8%,
order-balanced 90.5%, swap-consistency 89.1%. Direction of bias: gpt-5-mini favours the
**second**-presented response (recency), DeepSeek and Kimi favour the **first**. Cross-family
raw agreement 84-86%, kappa 0.36-0.42.

Note for the write-up: kappa is depressed here by extreme marginal imbalance (the variant wins
~90% of pairs), the classic kappa paradox. Adding PABAK and Gwet's AC1 alongside raw+kappa,
and reporting each judge's *own* win-rate on the shared subset, which is the quantity the
paper's claim actually rests on.
