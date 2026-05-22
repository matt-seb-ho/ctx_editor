# The Analyzer-Parity Bug

**Discovered**: 2026-05-21 (session r2b)
**Severity**: invalidates all comparison claims about AC3-Rewrite-vs-other-AC3-variants on LiC (Phase 1 onwards). Augment / Reset / Gated-Reset comparisons remain valid.
**Status**: documented + fix planned (`docs/post_may18_r5_analyzer_parity_plan.md`).

## What was wrong

All AC3 strategies are supposed to share the same upstream analyzer
step:

> First-stage analyzer → produce `task_spec` + `aligned` + `issues`
> from the conversation, then each strategy uses this analysis
> differently (Augment appends it, Reset templates it, Gated-Reset
> conditionally resets on it, Rewrite re-summarizes via a second
> LLM call).

This is the "shared first stage" the paper relies on for fair
cross-variant comparison.

**`AC3RewriteStrategy` was silently using a different first-stage analyzer.**

Architecturally:

- **Augment, Reset, Gated-Reset** all import and use
  `ConversationAnalyzer` (`src/ctx_editor/strategies/analyzer.py`)
  with prompt version `v8` (the paper-grade two-query flow:
  Q1 user-messages-only → task spec; Q2 spec + conversation →
  aligned/issues).
- **AC3-Rewrite** does **not** use `ConversationAnalyzer`. It has
  its own private `_run_analysis` in
  `src/ctx_editor/strategies/context_compaction.py` that loads the
  one-off prompt file `compaction_analysis.txt`. This prompt is
  **not in the analyzer prompt registry**
  (`analyzer_prompts.ANALYZER_PROMPT_REGISTRY`). It was written
  when AC3-Rewrite was added and never reviewed for parity against
  the `v8` prompts.

The grep is unambiguous:

```
$ grep -c ConversationAnalyzer src/ctx_editor/strategies/context_compaction.py
0
```

Reset / Augment also write to and read from `outputs/analysis_cache/`
(content-addressed `AnalysisCache`, added in R2 for cross-strategy
share). Rewrite does not.

## Concrete impact: the smoking gun

Sample `sharded-GSM8K/2` (Josh house-flip; one of 11 cases where
Reset succeeds and v5-Rewrite fails on math conv0):

Last user message: *"Josh is just starting out with house flipping."*

The original problem stipulates that **"repairs improved the
house's value by 150%"** — which the LiC gold answer interprets as
*the new value is 250% of the purchase price*. The correct
profit is $200,000 − $130,000 = **$70,000**.

| | Reset's analyzer (`ConversationAnalyzer` + `v8`) | Rewrite's analyzer (`compaction_analysis.txt`) |
|---|---|---|
| Spec parse of "150%" | "the value increased by 150% of the original purchase price, or the new value is 250% of the original purchase price" ✓ | "interpreted as the selling price being the total cost plus 150% of the total cost" ✗ |
| `aligned` field | Flags the assistant's wrong prior computation and tells the assistant to redo it | Calls the assistant's wrong $195,000 profit "correctly calculated" |
| `issues` field | Explicit: "The assistant's final calculation is wrong. It incorrectly applied the 150% increase to the total cost ($130,000) instead of the original purchase price ($80,000)" | (rewrite's prompt produces a non-comparable `issues` field) |
| Downstream answer | **70000** ✓ | **195000** ✗ |

The two analyzers give materially different (and one-of-them
wrong) parses of the user spec. Then the downstream Rewrite
strategy faithfully relays its analyzer's wrong content into the
compacted context, and the assistant produces a wrong answer.

This is what made it look like Rewrite was structurally lossy. In
fact, on this case at least, **Rewrite is doing its job correctly
on top of broken input**.

## Why this matters for paper claims

Every comparison statement in the prior batches of the form:

> "AC3-Rewrite under-performs AC3-Reset by X% on LiC ..."

is *not* a clean apples-to-apples comparison. Some unknown fraction
of the gap is explained by the analyzer divergence rather than the
rewriter step. The paper-relevant finding "the LLM rewriter step is
lossy" cannot be defended from this data alone.

Specifically affected:

- All Phase 1 AC3-Rewrite numbers (DeepSeek-V4-Flash).
- The R2 Rewrite-v2 numbers.
- The R3 v3 / v4 numbers and the entire "63% rewriter hallucination"
  attribution (a portion of attributed "rewriter hallucination" may
  in fact be "rewriter faithfully relaying analyzer-side
  interpretation").
- The R4 v5 / v6 numbers and the "first Rewrite to beat Baseline"
  claim (v6 may have benefited from extracting spec from raw user
  msgs precisely because it bypassed the worse analyzer — and may
  not show the same gain once the analyzer is fixed).

**What stays valid**:

- AC3-Augment vs Baseline / AO numbers (single shared analyzer).
- AC3-Reset vs Baseline / AO numbers (same).
- AC3-Reset vs AC3-Augment vs AC3-Gated-Reset comparisons across
  Phase 1, Phase 2, R2, R3 (all three use `ConversationAnalyzer` +
  cache).
- WildChat / Huang results (those use the separate
  `huang_eval/strategies.py` path which is independently consistent
  internally).
- CollabLLM Baseline / AO / Augment / Reset comparisons.

## What stays unaffected — explicit confirmation

The user asked: "Please tell me augment and gated reset runs are
unaffected by the way?" — **Yes, both unaffected.**

| Strategy | Source file | Uses `ConversationAnalyzer`? | Uses `AnalysisCache`? |
|---|---|---|---|
| Baseline | `baseline.py` | no analyzer | n/a |
| AO | `assistant_omit.py` | no analyzer | n/a |
| **Augment** | `append_analysis.py` | **yes (v8)** | yes |
| **Reset** | `context_edit_v2.py` (gate_on_issues=False) | **yes (v8)** | yes |
| **Gated-Reset** | `context_edit_v2.py` (gate_on_issues=True) | **yes (v8)** | yes |
| **Rewrite** ✗ | `context_compaction.py` | **NO** | no |

Only `AC3RewriteStrategy` is the outlier.

## How this happened

The most likely chain:

1. AC3-Reset and AC3-Augment were built first, sharing
   `ConversationAnalyzer`.
2. AC3-Rewrite was added later as a separate strategy, probably
   adapted from earlier code (likely `collabllm_compaction.py`,
   per the comment in `ac3_rewrite_lic.yaml`).
3. The original `compaction_analysis.txt` was carried over as the
   analyzer step, never re-pointed at `ConversationAnalyzer`.
4. The two analyzer paths produced superficially similar XML
   outputs (`<task_spec>` / `<aligned>` / `<issues>`) so no test
   failure flagged the divergence.
5. The R2 `AnalysisCache` infrastructure was added with Rewrite
   listed as a beneficiary in its docstring — but Rewrite never
   plugged in.

The kind of bug that's easy to miss in review because both halves
work and produce similar-shaped outputs.

## The fix (planned, R5 Phase 0)

Refactor `AC3RewriteStrategy` to use `ConversationAnalyzer(
prompt_version="v8")` and pass through `AnalysisCache`, identical
to what Reset / Augment do. Drop the bespoke `_run_analysis` step
and the `compaction_analysis.txt` dependency.

After the refactor, every existing rewrite prompt (v1 through v6)
gets the v8 analyzer for free, and Rewrite hits the 3,311 cached v8
analyses for free on the htn50_52 prefix set.

See `docs/post_may18_r5_analyzer_parity_plan.md` for the full plan
(Phases 0-3, plus optional Phase 4 if the analyzer wasn't the
bottleneck).

## What to re-run after the fix

In rough priority order:

1. Re-evaluate **Rewrite-v1** with the v8 analyzer on the LiC
   subset that other strategies were run on. This is the "is the
   bespoke prompt even necessary?" data point.
2. Re-evaluate **Rewrite-v3-no-conv** with v8 analyzer — tests
   whether removing the conversation from the rewriter prompt
   matters when the analyzer is good.
3. Optionally re-evaluate v6-GEPA with v8 — may or may not retain
   its gains, since some of v6's improvement was specifically about
   bypassing the bad analyzer.

Past Rewrite numbers (Phase 1 / R2 / R3 / R4) should be **labeled
as pre-analyzer-parity** in their respective docs, with a pointer
to this file.
