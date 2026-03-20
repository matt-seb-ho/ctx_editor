# Database & Actions Task Diagnosis — 2026-03-15

## Overview

| Task | S0 | S1 | S1+mem | S2 | S2+mem | Real asst errors |
|------|:--:|:--:|:------:|:--:|:------:|:----------------:|
| database | 4% | 12% | 8% | 16% | 16% | 5/25 (20%) |
| actions | 8% | 12% | 20% | 8% | 8% | 6/25 (24%) |

Both tasks are dominated by **evaluation artifacts**, not strategy failures.

---

## Database: 76% of errors are evaluation artifacts

### Error breakdown (S2, 21 errors)
- **12 strict_comparison**: Assistant SQL is semantically correct but returns extra columns
- **5 assistant_error**: Genuine mistakes
- **2 extraction_failure** + **2 other**

### Root cause: Extra columns fail execution-based matching

The database_v2 evaluator runs both queries against SQLite and compares result sets via
`result_eq()`. This function rejects results if **column count differs** — even if the
expected columns are present among the returned columns.

gpt-5-mini consistently over-engineers SQL by adding extra columns, JOINs, and defensive
coding (COALESCE, NULLIF, CAST, TRIM). Examples:

- **spider-val-946**: GT returns 2 columns (date, first_name). Assistant returned 9 columns
  including treatment_id, dog_id, treatment_type, etc. The required columns are present.
- **spider-val-457**: GT returns 2 columns. Assistant returned 6 columns.
- **spider-val-832**: GT is `SELECT max(SHARE), min(SHARE) FROM performance`. Assistant
  added `CAST(NULLIF(REPLACE(p.Share, '%', ''), '') AS REAL)` transforms that may produce
  different numeric values.

### The 5 real assistant errors

1. "Number of professionals" interpreted as "enumerate" not "count" (shard phrasing)
2. "Casualties" interpreted as killed+injured combined (broader than GT)
3. Friend relationship interpreted as bidirectional (GT uses directional-only)
4. `Age <= 33` instead of `Age = 32 OR Age = 33` (shard didn't specify "exactly")
5. LEFT JOIN instead of INNER JOIN (GT excludes zero-vote rows)

All 5 stem from ambiguous shard phrasing where multiple SQL interpretations are valid.

### Potential fixes

- **Evaluator**: Project only GT columns from assistant result before comparison
- **System prompt**: "Return ONLY the exact columns requested, no extras"
- Note: Both are LiC evaluation changes, not strategy changes

---

## Actions: 70% of errors are evaluation artifacts

### Error breakdown (S1+mem, 20 errors)
- **7 extraction_failure**: Correct calls exist across turns, evaluator only sees last turn
- **6 assistant_error**: Genuine mistakes
- **5 strict_comparison**: Formatting differences ("substance A" vs "A")
- **1 sharding_distortion** + **1 other**

### Root cause 1: Multi-turn extraction failure (7 errors)

The BFCL evaluator requires ALL parallel function calls in a single response. The
`answer_extraction_strategy = "full_response"` only takes the last assistant message.

In multi-turn, the assistant correctly makes one call per turn as information arrives.
The evaluator then sees only the final turn's call(s) and fails:

- **parallel_134**: 4 correct BMI calls across 4 turns. Evaluator sees only the 4th.
- **parallel_177**: Gold/silver/platinum/palladium across 4 turns. Only palladium extracted.
- **parallel_30**: Two flight bookings across 2 turns. Only second extracted.

### Root cause 2: S2 context compaction destroys accumulation (S2: 8%)

S2 replaces the conversation with `{task_spec, what_looks_right, last_user_message}`.
For actions, this is catastrophic:

- The task requires accumulating function calls across turns
- The assistant sees the summary of prior calls as "completed work" + the last user
  message requesting one more call → naturally produces just that one call
- The evaluator expects all N calls in one response

Example (**parallel_198**, lawsuit_search): S2 compacted context includes task spec
listing all search requirements (Google, Facebook). But the last user message says
"focus on Facebook in San Mateo County." Assistant correctly responds with just the
Facebook call. Evaluator expected both Google and Facebook calls together.

### Root cause 3: Carry-forward parameter loss (S2)

Parameters established in early turns don't carry forward through S2 compaction:

- **parallel_91**: User specified `operating_hours=22` for LA restaurants. In later turns
  asking for SF and Seattle, the parameter isn't re-stated. After S2 compaction, the
  assistant calls `find_nearby("Seattle")` without `operating_hours=22`.

S1 avoids this because the full conversation is preserved — the assistant can see it
applied the parameter in earlier turns and continues doing so.

### Root cause 4: Strict string matching (5 errors)

BFCL's `string_checker` fails on minor formatting differences:
- `"substance A"` vs `"A"`
- Boolean serialization (`true` vs `True`)
- These are evaluation artifacts, not strategy failures.

### The 6 real assistant errors

1. Combinatorial ambiguity: 4 calls expected (2 teams × 2 years) but shards only name 2
2. Missing carry-forward parameter (operating_hours)
3. Over-delivered: 6 calls instead of expected 2
4. Extra call with missing parameter
5-6. Dropped one call from a pair

### Potential fixes

- **Evaluator**: Aggregate function calls across ALL assistant messages, not just last
- **S2 for actions**: Needs accumulation-aware compaction — "What Looks Right" should
  list the actual function calls made so the assistant knows to re-issue them all
- **String matching**: Use looser BFCL normalization

---

## Implications for Strategy Design

1. **S2 is structurally wrong for accumulation tasks** (actions). The compaction format
   signals "prior work is done, just handle the latest request." For tasks where the
   final answer must include all accumulated outputs, S2 needs a different compaction
   strategy that tells the assistant to re-emit everything.

2. **Database errors are mostly about SQL style** (extra columns), not understanding.
   The assistant understands the task correctly in most cases. A system prompt directive
   about column selection would help.

3. **Adjusted accuracy** (removing evaluation artifacts) shows our methods are working
   much better than raw numbers suggest:

| Task | S2 raw | S2 adjusted (eval artifacts removed) |
|------|:------:|:------------------------------------:|
| database | 16% | ~80% (16 artifacts + 5 real errors) |
| actions (S1+mem) | 20% | ~72% (14 artifacts + 6 real errors) |

These adjusted numbers should be taken directionally — the error attribution model
may misclassify some cases. But the signal is clear: **evaluation methodology is the
bottleneck, not the context editing strategy.**
