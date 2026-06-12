# Mega-table experiments — next batch plan

**Goal**: fill in the **model × benchmark × method** matrix that
underwrites the updated paper's results section. Today (post-R2)
we have full coverage on **LiC only**. This doc plans the cheapest
path to filling CollabLLM and WildChat rows, plus the gaps inside
LiC itself.

**Author**: Claude, 2026-05-18 03:30 PT (post-R2)
**Status**: Plan only — *no experiments launched yet, awaiting
approval*.

## Current coverage matrix

Models considered: gpt-5.4 · DeepSeek-V4-Flash · Kimi-K2.6
(plus gpt-5-mini in legacy Huang runs).

Methods considered (in paper-relevant order):
**Baseline · AO · AC3-Augment · AC3-Reset · AC3-Rewrite · AC3-Gated-Reset**.

### LiC (last-turn replay, htn50_52, 4 tasks × 3 prefixes)

| Method | gpt-5.4 | DeepSeek | Kimi-K2.6 |
|---|:-:|:-:|:-:|
| Baseline | ✅ Phase 2 | ✅ Phase 1 | ✅ Phase 2 |
| AO | ✅ Phase 2 | ✅ Phase 1 | ✅ Phase 2 |
| AC3-Augment | ✅ Phase 2 | ✅ Phase 1 | ✅ Phase 2 |
| AC3-Reset | ✅ Phase 2 | ✅ Phase 1 | ✅ Phase 2 |
| AC3-Rewrite (v1) | ❌ | ✅ Phase 1 | ❌ |
| AC3-Rewrite (v2) | ❌ | ✅ R2 | ❌ |
| AC3-Gated-Reset | ❌ | ✅ Phase 1 | ❌ |

**Gaps**: Rewrite + Gated-Reset on gpt-5.4 / Kimi-K2.6.

### CollabLLM (multi-turn fresh sim, 2 tasks × 20 problems)

User-sim choice now matters: **DeepSeek-V4-Flash is the standard**
(per R2 finding that gpt-4o-mini drifts).

| Method | gpt-5.4 (asst) | DeepSeek (asst) | Kimi-K2.6 (asst) |
|---|:-:|:-:|:-:|
| Baseline | ❌ | ✅ R2 (DS user) + Phase 3a (4o-mini user) | ❌ |
| AO | ❌ | ✅ R2 + Phase 3a | ❌ |
| AC3-Augment | ❌ | ✅ R2 + Phase 3a | ❌ |
| AC3-Reset | ❌ | ✅ R2 + Phase 3a | ❌ |
| AC3-Rewrite | ❌ never tested | ❌ never tested | ❌ never tested |
| AC3-Gated-Reset | ❌ | ❌ | ❌ |

**Gaps**: everything on gpt-5.4 / Kimi · Rewrite anywhere · Gated anywhere.

### WildChat / Huang (pairwise judge, 76 AO-failure turns, replay-mode)

WildChat already *is* replay-mode (single-turn response on a frozen
human-conversation prefix), so cells are cheap. The pairwise judge
means we have "wins-vs-AO" / "wins-vs-FC" not raw accuracy.

| Method | gpt-5-mini | DeepSeek | Kimi-K2.6 |
|---|:-:|:-:|:-:|
| AC3-Reset (s15) | ✅ Phase 3b (N=3) | ✅ R2 (N=1) | ✅ R2 (N=1) |
| AC3-Augment | ✅ Phase 3b (N=3) | ✅ R2 (N=1) | ❌ |
| AC3-Rewrite (s3) | ❌ | ❌ | ❌ |
| AC3-Gated-Reset | ❌ | ❌ | ❌ |

**Gaps**: Augment on Kimi · Rewrite on everything · Gated on everything.

## Are CollabLLM / WildChat last-turn replayable?

### WildChat — yes, already
Huang's Phase 2 evaluation IS a last-turn-replay protocol: it loads
real human-conversation prefixes, runs each AC3 variant to produce
one assistant response, and pairwise-judges the candidates. Cell
cost is just 76 turns × ~5 calls each. **No engineering needed**.

### CollabLLM — no, currently
`run_collabllm.py` runs full fresh sims (~14 turns per problem,
~280 calls per problem × 20 problems = ~5600 calls per cell). The
"prefix" that would let us replay only the final assistant turn
isn't materialized anywhere.

A real replay variant would need:
1. **Prefix capture**: run Baseline cells once per (task, problem,
   seed) and snapshot the prefix at each turn k ∈ {6, 8, 10, 12}.
2. **Replay loop**: load prefix at turn k, apply the strategy, get
   one assistant response, evaluate.
3. **Eval reuse**: pass-rate / LLM-judge against the gold target.

**Engineering**: ~half a day. Once built, each cell drops from
~30 min to ~2 min, and the cost drops by 14×.

### Compromise for the mega table
Build the CollabLLM replay infrastructure **before** running the
gpt-5.4 / Kimi sweep. That keeps the cross-model sweep cheap and
makes multi-rep error bars affordable.

If we're in a hurry, we can also just do fresh-sim CollabLLM on
the new models — that's ~2h per model × 2 models = ~4h. Acceptable
for one overnight if replay infrastructure is too much.

## Proposed next batch (priority order)

### P0 — Cheapest fills, highest value (≈ 1.5h total)

| Task | Cells | Wall | Cost |
|---|---|---|---|
| LiC Rewrite (v1+v2) on gpt-5.4 + Kimi | 4 models × 4 tasks × 3 prefixes = 48 cells, parallel | ~45 min | small |
| LiC Gated-Reset on gpt-5.4 + Kimi | 2 × 4 × 3 = 24 cells, parallel | ~30 min | small |
| WildChat Rewrite (s3) on DeepSeek + Kimi + gpt-5-mini | 3 cells, sequential ≤ 30 min each | ~90 min | small |
| WildChat Augment on Kimi-K2.6 | 1 cell | ~25 min | small |

After P0, the LiC and WildChat rows of the mega table are **complete**.

### P1 — CollabLLM scale-out (≈ 4h overnight)

| Task | Cells | Wall | Notes |
|---|---|---|---|
| CollabLLM full sweep on gpt-5.4: Baseline · AO · Augment · Reset | 4 × 2 tasks × 1 rep = 8 cells, parallel | ~75 min | First multi-rep candidate |
| CollabLLM full sweep on Kimi-K2.6: same 4 strategies | 8 cells, parallel | ~90 min | Kimi slower per call than DeepSeek |
| CollabLLM Rewrite on DeepSeek (one model) | 2 cells | ~30 min | Probably under-performs; confirms LiC story generalizes |
| CollabLLM N=3 multi-rep fill-in on DeepSeek for variance bars | 8 cells (×2 reps each) | ~90 min | Tightens R2's N=1 numbers, especially math-hard 85 vs 95 |

After P1, the CollabLLM row has gpt-5.4 / Kimi for the 4 standard
methods, Rewrite for at least one model, and multi-rep error bars
on the headline DeepSeek cells.

### P2 — Replay infrastructure for CollabLLM (≈ 1 day eng + small follow-up sweep)

Build CollabLLM replay so future cells are 2 min instead of 30 min.
This is the pre-requisite for any larger-N or per-turn-k analysis
(e.g., "AC3-Reset wins more at later turns").

### P3 — Gated everywhere

Once Reset + Rewrite are mapped, run Gated-Reset on the same matrix.
The argument for gating is **deployment realism** (don't fire the
intervention every turn), so this is mainly a cost-curve table for
the deployment section of the paper — not a primary results-table
entry.

## Mega-table draft (what the paper will report)

Two tables, one per evaluation paradigm.

### Table A — LiC + CollabLLM, raw accuracy

Rows: methods. Columns: (benchmark, model, subtask). One average
column per (benchmark, model).

| Method | LiC (gpt-5.4) | LiC (DS) | LiC (Kimi) | CollabLLM (gpt-5.4) | CollabLLM (DS) | CollabLLM (Kimi) |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| Baseline | 60.4% | 51.3% | 62.0% | ?? | 50.0% (math 95, code 5) | ?? |
| AO | 71.2% | 69.4% | 67.7% | ?? | 52.5% (math 90, code 15) | ?? |
| Reset | 75.7% | 68.4% | 73.1% | ?? | 52.5% (math 85, code 20) | ?? |
| Augment | 76.2% | 67.0% | 72.8% | ?? | 57.5% (math 100, code 15) | ?? |
| Rewrite | ❌ | 50.9% / 49.7% (v1/v2) | ❌ | ❌ | ❌ | ❌ |
| Gated-Reset | ❌ | 67.4% | ❌ | ❌ | ❌ | ❌ |

(LiC numbers here are computed from the existing Phase 1+2 / R2
reports. "??" entries fill in after P1 lands.)

### Table B — WildChat / Huang (pairwise win-rates vs AO, quality axis)

| Method | gpt-5-mini | DeepSeek | Kimi-K2.6 |
|---|:-:|:-:|:-:|
| AC3-Reset | 89.8% | 75.0% | 71.6% |
| AC3-Augment | 92.1% | 84.2% | ?? (after P0) |
| AC3-Rewrite | ?? (after P0) | ?? (after P0) | ?? (after P0) |
| AC3-Gated-Reset | ?? (P3) | ?? (P3) | ?? (P3) |

## Cost / time summary

| Phase | Wall (est) | $ (est) | New rows in mega table |
|---|---|---|---|
| P0 | 1.5h | < $1 | LiC × Rewrite / Gated; WildChat × Rewrite / Augment-Kimi |
| P1 | 4h | $3–5 | CollabLLM × gpt-5.4 + Kimi (all standard methods); CollabLLM × Rewrite; multi-rep error bars |
| P2 | 1 day + 1h follow-up | small | infra; faster mega-table re-runs |
| P3 | 2h | < $1 | Gated-Reset row |

## Open design questions for the meeting

1. **Multi-rep budget**. Do we want N=3 reps for the headline cells
   (where error bars matter for paper claims) or N=1 across the
   whole matrix? My preference: N=1 to fill the matrix, then a
   targeted N=3 pass on the cells we cite in the abstract.
2. **gpt-5.5 inclusion**. Phase 2 dropped it for throughput. Is it
   worth the cost of one more model column? Probably not for the
   mega table unless the editor specifically asks.
3. **gpt-5-mini in the mega table**? It's in WildChat (legacy) but
   not in LiC / CollabLLM. Either drop it from WildChat-Table or
   backfill the others.
4. **Per-respondent test-set selection on WildChat**. The current
   Huang test set is the 76 turns where *gpt-5-mini's* AO lost to
   FC. If we want cleanest cross-model claims, we'd re-run Phase 1
   per respondent (~1h per model). Cheap to add to P0.
