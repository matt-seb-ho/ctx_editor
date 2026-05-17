# Decision: Replicate Across Prefixes vs Replicate Across Sampling Reps

**Date**: 2026-05-16
**Author**: Matthew (with Claude)
**Context**: We are scaling up the AC3 (and other context-strategy) evaluation
to produce stronger empirical evidence for the paper. We are using
last-turn-replay over saved vanilla-sharded prefixes. The question is how to
spend our N=3 budget per problem.

## The question

For each problem in the htn50_52 subset, we need 3 measurements per
(strategy, model) cell. Two ways to spend those three:

**Option A — 3 sampling reps per prefix.**
For each problem we pick ONE valid vanilla-sharded prefix (≥ 1 turn replayed,
or the full last turn). We then run each strategy 3 times against that *same*
fixed prefix, varying only the assistant-side sampling seed. Variance
estimated = pure sampling variance of the strategy's last-turn generation.

**Option B — 3 distinct prefixes per problem.**
For each problem we save 3 different vanilla-sharded prefixes (3 independent
user-simulator runs through the shards). For each strategy we run *once* on
each prefix. Variance estimated = combined prefix-and-sampling variance.

We do **not** want to do both — that would 3× the experiment count.

## Side-by-side

| Dimension | A: same prefix × 3 reps | B: 3 distinct prefixes |
|---|---|---|
| Captures sampling noise in the assistant's last-turn generation | ✅ | partially (1 sample per prefix) |
| Captures variance from different user-sim paths | ❌ (fixed) | ✅ |
| Paired comparison (S0 vs AC3 on identical prefix) | ✅ (cleanest possible) | ✅ per prefix; not across the 3 prefixes |
| Tighter error bars → easier to detect treatment effects | ✅ | usually wider (more sources of variance) |
| Generalizes claims across conversation paths | ❌ | ✅ |
| Matches the "what would a deployed user see?" framing | partial | ✅ |
| Trace-replay infra reuse | minimal (same prefix file every time) | requires us to manage 3 prefix files per problem |
| Risk of being criticized as "overfit to one lucky/unlucky prefix" | high | low |

## Argument for A (same-prefix, 3 sampling reps)

- **Cleanest treatment isolation.** Holding the prefix fixed means any
  difference between S0 and AC3 last-turn outputs is the treatment plus
  sampling noise. This is the design with the lowest noise floor for
  detecting effects, especially for the high-cost reasoning models where 50
  problems × 3 reps × 2 strategies is already a lot of API calls.
- **Aligned with the *original motivation* for last-turn replay.** We chose
  last-turn replay specifically because the user-sim (gpt-4o-mini) is a
  comparatively weak source of variance we wanted to remove. Locking the
  prefix in place is the strongest possible removal.
- **Cheaper.** One prefix per problem × 3 strategies × 3 reps = 9 last-turn
  generations per problem. With Option B we either reduce reps per prefix
  (giving up some signal) or keep them and multiply cost.

## Argument for B (distinct prefixes)

- **External validity.** A reviewer's natural question is "does the gain on
  prefix X generalize to prefixes X′, X″?" If we only have one prefix per
  problem we cannot answer this empirically. We can argue it intuitively
  ("the model gets the same shards in some order"), but the data won't show
  it.
- **The htn50_52 problems were *selected* by their tendency to fail in many
  conversations.** That selection is at the *problem* level, not the prefix
  level — different runs through the same shards land in genuinely different
  failure modes (different early commitments, different shard orderings the
  user-sim chose, different intermediate code). One prefix per problem
  collapses that distribution.
- **Diversifies the failure-mode coverage** that the paper can report on. We
  can decompose results by "how hard was this prefix" via the vanilla S0
  baseline accuracy on that prefix.
- **Mitigates the "lucky prefix" criticism.** If we report N = 50 with one
  prefix per problem, half of cell-level variance is just "did we get a hard
  starter run for that problem?" Three prefixes give us a paired-comparison
  envelope per problem that absorbs this.

## Decision: **Option B (3 distinct prefixes per problem).**

Justification:

1. The whole point of scaling up from the original paper's setup is to get
   broader empirical coverage; collapsing to one prefix per problem
   structurally re-introduces the narrowness we are trying to escape.
2. Paired comparison across (problem, prefix) cells is still possible — for
   each prefix we run every strategy, so each strategy is evaluated on the
   same 150-or-so prefix population. We just give up the *additional*
   pairing across sampling reps on the same prefix, which is a smaller win.
3. Last-turn replay already removes the dominant source of prefix variance
   (the user-sim's wording within a given turn). The variance that remains
   between distinct prefixes is meaningful signal — "the user-sim revealed
   shard 3 before shard 4 vs after" — not noise we should suppress.
4. Cost is comparable to Option A: 3 prefixes × 1 rep × N strategies vs
   1 prefix × 3 reps × N strategies — same number of last-turn generations.

## What we give up, and how we cover it: complementary sampling-variance probe

Option A's strength is "how noisy is the assistant's last-turn generation
under a fixed prefix?" That's a real question reviewers may ask. We will
answer it with a single complementary experiment that does NOT multiply the
main matrix:

- **Model**: DeepSeek-V4-Flash (cheapest of the four, large enough to
  exhibit non-trivial sampling variance).
- **Strategy**: AC3-Gated-Reset (`context_edit_v2`) — the headline
  strategy. Run S0 (baseline) for comparison on the same prefixes.
- **Tasks**: math_v2 and database_v2 — the two with the largest sharded
  vs STQ gap, where treatment effects are most likely.
- **Design**: pick the 3 valid prefixes per problem from our prefix pool
  (~150 prefixes per task). For each prefix, run the strategy **3 times**
  with different sampling seeds. So we have 50 problems × 3 prefixes × 3
  reps = 450 last-turn generations per task, vs the main matrix's
  50 × 3 × 1 = 150.
- **Analysis**: report (i) within-prefix sampling stdev, (ii) cross-prefix
  stdev for the same problem, (iii) cross-problem stdev. The decomposition
  shows reviewers which sources dominate.

If sampling variance turns out to dominate prefix variance, we will rethink
the main matrix's design choice for the next batch. Until then, Option B is
the default for all main-matrix runs.

## Implications for the prefix-gathering process

- Vanilla-sharded runs are now treated as **prefix factories**, not
  end-of-the-line evaluations. Each conversation's accuracy is recorded
  but the real product is its sharded trace.
- "Valid prefix" = a vanilla-sharded conversation whose **user-simulator was
  judged to have revealed enough information**, as established by the
  existing FN-analysis (`identify_false_negatives.py`,
  `false_negative_analysis.mode=batch`). User-sim-insufficient runs are
  discarded; they would propagate "carried-forward error" into any
  intervention experiments.
- We must hit **3 valid prefixes per problem**. The vanilla 3-run batch we
  already have may not provide that for every problem (some problems' first
  three runs may include a user-sim-insufficient conversation). We
  therefore launch follow-on vanilla runs targeted at the under-covered
  problems until each problem has ≥ 3 valid prefixes (or we exhaust a
  conservative cap, in which case we switch the user simulator to
  DeepSeek-V4-Flash for those holdouts).
- The final prefix set is checked into `data/valid_prefixes_htn50_52/{task}/`
  (3 trace files per problem). The replay infra reads from there.

## Open questions / follow-ups

- We could also report a "stretched prefix" robustness check: re-running
  AC3 on prefix 1 with seeds {a, b, c} for a single (task, model) cell to
  see if AC3's last-turn output is meaningfully sensitive to seed. Cheap
  to do at the end if questions arise.
- If the FN-analysis judge (gpt-5-mini, temperature 0) is biased toward
  declaring borderline prefixes "sufficient", we may include a sensitivity
  check using a stricter judge. Not for v1 of the prefix pool.
