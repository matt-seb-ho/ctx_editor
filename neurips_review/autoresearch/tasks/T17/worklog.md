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

## 16:55 — mechanism nailed; ERGO runs confirmed unrecoverable
1. Pool filter mechanism (file:line):
   - `src/ctx_editor/execution/replay.py:21-56` `load_user_sim_induced_ids` — reads
     `<pool>/false_negatives.json` or `<parent>/<name>_false_negatives.json`,
     returns `summary.user_sim_induced_ids`.
   - `src/ctx_editor/run_experiment.py:441-470` — those IDs are dropped from `samples`
     and re-emitted as `skip_result(is_correct=False, num_turns=0, trace={"messages":[]})`.
   - `run_experiment.py:528,542-543` — `total = len(valid_results)`; skips are NOT in
     `results`, so `metrics.total_samples` = FILTERED n.
   VERIFIED on 28 archived runs replaying from the four tab:main pools: every single one
   reports n = 20 (math) / 19 (code) / 25 (database) / 25 (actions), 0 exceptions.

2. **`data/baseline_traces/actions` has NO sidecar** — never tracked in git, absent from
   snapshot.tar.gz. All archived actions replays report n=25, user_sim_skipped=0. So the
   paper's actions n=23 is NOT the pool filter; it is the "common 23-sample set"
   normalisation documented at `docs/reports/v10_paper_updates.md:24-26`
   ("Raw: 17/25 (68%) / On common 23-sample set: 17/23 (74%)"), and in one earlier
   run (`2026-03-13/02-09-40`) n=23 arose from **2 errored conversations**, not a filter.
   → the actions column's denominator has materially weaker provenance than math/code/db.

3. Stub-resurrection mechanism CONFIRMED offline (positive control):
   `outputs/2026-03-16/13-09-27` reports n=20 but its `traces/` holds **23 files, 3 empty**
   — exactly `sharded-GSM8K_{1287,267,534}`, the 3 IDs in `math_false_negatives.json`.
   `load_baseline_traces` (replay.py:78-88) globs `*.json` and keys on `sample_id`, so
   replaying from a *run directory* re-admits the pruned samples. 20+3=23, 19+6=25,
   25+0=25, 23+2=25 → **exactly ERGO's 23/25/25/25.**

4. ERGO source runs `outputs/2026-05-01/23-*`: 0 hits in the 69,738-entry snapshot.tar.gz
   index, 0 in supplementary.tar.gz, absent from ~/ac3/{recovered,recovered_t2c,t14_snapshot}.
   Also absent: `outputs/2026-03-21/*` (AO + Concat-User rows) and the whole v8 batch
   (2026-03-16 stops at 16-16-14). **The published tab:main per-sample results do not exist
   on disk.** Recomputation must therefore be arithmetic on the printed n/d, not re-scoring.

## 17:25 — pruned samples are NOT free wins for the published row; interval, not point
Attempted to bound k = #pruned samples ERGO answered correctly.
- Read `missing_elements` for all 9 math+code pruned IDs: every one is a *semantic*
  omission or contradiction in the user shards (e.g. GSM8K/1287 "12-year-old is the
  younger brother" absent + contradicted; lcb/2920 circular wrap-around never stated).
  ERGO's operating context is an LLM rewrite of exactly those user messages, so it
  cannot recover the missing fact except by luck → prior strongly favours k≈0.
- Naive empirical check across 870 archived attempts on those 9 IDs gives 32.9% solved —
  but **this is not admissible**: those runs use *different shardings* (htn20/htn50 pools,
  other user sims), where the missing detail may be present. Discarded as evidence.
- Admissible datapoint found: `tex:508-510` (app:variance note) discloses that the
  Gated-Reset headline **actions** run was **17/25 raw and 17/23 on the common-23 set** →
  both excluded items were failures, i.e. k=0 in the one case that is observable.
  Same pair reported at `docs/reports/v10_paper_updates.md:24-26`.
- Also: the baseline run that generated the math pool scored 13/23 with all 3 pruned IDs
  among its failures (`math_false_negatives.json` total_analyzed=10).
⇒ Report each affected ERGO cell as an interval with k=0 as the point estimate, flagged.

## 17:40 — Gated-Reset row denominators resolved exactly from the paper's own appendix
`tex:496-504` prints the N=3 per-run values: math 75.0/80.0/85.0 (n=20),
code 72.2/63.2/57.9 (**n=18 then 19,19** — mixed inside one row),
database 44.0/32.0/40.0 (n=25), actions 68.0/56.0/60.0 (**n=25**).
Means 80.0 / 64.4 / 38.7 / 61.3 reproduce the printed cells to 0.1pp. So the Gated-Reset
actions cell is on n=25 while every other actions row is on n=23 — disclosed at :508 but
still not comparable down the column. Note this one is in **our** disfavour.

## 18:05 — corrected table built; RESULTS.md written
`build_corrected.py` → `corrected_tabmain.json`. 10 of 40 cells move; 7 of the 10 are on
rows that are not ours. Headline: ERGO 69.6→80.0 (math), 44.0→57.9 (code), 12.0 (db, exact),
48.0→52.2 (actions) at the k=0 point estimate; AO/code 77.8→73.7, Concat/math 84.2→80.0,
Augment/code 55.6→52.6, Reset/code 61.1→57.9, Gated/code 64.4→63.2, Gated/actions 61.3→66.7.

**Conclusion changes (reported plainly, per brief):** ERGO now BEATS AC3-Reset on math
(80.0 vs 75.0), TIES it on code (57.9) and actions (52.2), and TIES AC3-Gated-Reset on math
(80.0 vs 80.0). Across the 12 no-memory ERGO-vs-AC3 cells ERGO goes from losing 11/12 to
winning-or-tying 7/12. Database is untouched and AC3 still wins it decisively; AC3-Gated-Reset
still ≥ ERGO on all four tasks (math now a tie, not a 10.4pp win). No printed *sentence*
becomes false — the LiC prose compares against AO and Baseline, not ERGO — and the paper's
one explicit ERGO claim (underperforms concatenation on db and actions) survives.

Side effects, both in our favour: `tex:318` "code … closing 78% of the 62.0pp gap" →
"63.2%, closing 82% of the 57.9pp gap"; abstract/conclusion "55–80%" → "67–82%".

Positive controls: PC1 denominator rule reproduces on all 28 archived pool-replay runs, 0
exceptions; PC2 the 20+3=23 stub arithmetic verified against actual files; PC3 blind rational
reconstruction of ERGO's fractions matched commit `d856247` exactly on all four cells; PC4
three independent source docs reproduce three published rows to the digit; PC5 the N=3
Gated-Reset means reproduce from the printed per-run values; PC6 all 30 unchanged cells are
bit-identical.

**Cannot be finished without new runs.** The intervals (widest: ERGO code [26.3, 57.9]) can
only be closed by re-running ERGO on the filtered pools — 87 last-turn replays, ~$0.20,
`execution.replay_source=data/baseline_traces_v2/{task}` so the filter fires automatically.
Recommended to the operator as step 1 of PAPER-7. No API calls were made by T17.
No files written outside tasks/T17/. `writing/overleaf_repo/` read only.
