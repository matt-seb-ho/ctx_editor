# Rewrite vs Reset — concrete side-by-side examples

**Source data**: `scripts/analysis_rewrite_v_reset/data/pairs.jsonl`
(127 LiC samples where Reset succeeded but Rewrite failed,
DeepSeek-V4-Flash, last-turn replay) and
`scripts/analysis_rewrite_v_reset/data/diagnoses.jsonl` (DeepSeek-V4-Flash
labeled subset, n=48).

This doc shows four illustrative cases — one per dominant failure
mode — with the prepared contexts and final answers side-by-side.
For aggregate distributions see
`docs/reports/post_neurips_r2_rewrite_analysis.md` and
`scripts/analysis_rewrite_v_reset/data/diagnosis_summary.md`.

To open these in the conversation viewer:

```bash
streamlit run src/ctx_editor/app_conv_viewer.py
# In two browser tabs, open the same sample under:
#   - outputs/post_neurips_ac3_phase1/context_edit_v2_no_gate_<task>_v2_conv<N>_* (Reset)
#   - outputs/post_neurips_ac3_phase1/ac3_rewrite_lic_<task>_v2_conv<N>_* (Rewrite)
```

---

## Case 1 — actions / sharded-BFCL/parallel_62 (conv 2)

**Failure mode**: F1 = lost meta-structure (parallel function call dropped).

### Last user message
> The second equation is 5x^2 - 7x + 3 = 0

### Reset compacted context
```
# User Task Specification (So Far)
Find the roots of two quadratic equations:
1. 3x^2 + 4x + 2 = 0
2. 5x^2 - 7x + 3 = 0

Use the algebra.quadratic_roots function for each equation, providing the
coefficients a, b, and c as integers.

# What Looks Right So Far
The assistant correctly identified that the `algebra.quadratic_roots`
function requires three integer coefficients (a, b, c) for each equation.
The user has now provided both equations:
1. 3x² + 4x + 2 = 0 (coefficients: a=3, b=4, c=2)
2. 5x² - 7x + 3 = 0 (coefficients: a=5, b=-7, c=3)

The assistant has not yet produced any function calls or results, but the
conversation has successfully gathered all required parameters.

IMPORTANT: Your response must include ALL required outputs for the
complete task specification, including any work described above as 'what
looks right'. Do not assume prior work has been submitted — your
response must be self-contained and complete.
```

### Rewrite compacted context
```
# User Task Specification (So Far)
Find the roots of two quadratic equations:
1. 3x^2 + 4x + 2 = 0
2. 5x^2 - 7x + 3 = 0

# What Looks Right So Far
None — the assistant has not yet computed the roots for either equation.
```

### Final answers
| | extracted_answer |
|---|---|
| **Reset (correct)** | `[algebra.quadratic_roots(a=3, b=4, c=2), algebra.quadratic_roots(a=5, b=-7, c=3)]` |
| **Rewrite (wrong)** | `[algebra.quadratic_roots(a=5, b=-7, c=3)]` |

### What happened
Both prepared contexts list the two equations. But Reset's compacted
context includes the **explicit "IMPORTANT: your response must include
ALL required outputs ... self-contained and complete" boilerplate** —
that's an artifact of LiC's accumulate-actions Reset template that
prevents the assistant from "just answering the latest user turn".
Rewrite's context drops that instruction (the rewriter LLM treats it
as redundant). The assistant then naturally only emits the function
call for the equation in the *most recent* user message.

This is the cleanest illustration of "Reset's templated string
preserves a useful structural cue that Rewrite's LLM helpfully strips
out". The rewriter is being too clever.

---

## Case 2 — code / sharded-livecodebench/2955 (conv 2)

**Failure mode**: F4 = phantom-added spec + F5 = verbatim-code anchoring.

### Last user message
> If I spend 15 bucks, I'll have 80 left.

### Reset compacted context (excerpt)
```
# User Task Specification (So Far)
Write a Python function that calculates the remaining bank balance after
a purchase, given the following rules:
- The starting balance is 100 bucks.
- The purchase amount (spending) is between 0 and 100 bucks (inclusive).
- The store rounds the purchase amount to the nearest ten bucks.
- If the purchase amount is exactly halfway between two multiples of ten
  (i.e., a tie), the store rounds up to the larger multiple of ten.
- The function should return the remaining balance after subtracting the
  rounded purchase amount from the starting balance.

**Function signature:**
```python
def remaining_balance(spending: int) -> int:
```

# What Looks Right So Far
The assistant's latest response correctly implements the core rounding
logic ... The example given by the user (spending 15 → rounded to 20 →
remaining 80) matches this logic.
```

### Rewrite compacted context (excerpt)
```
# User Task Specification (So Far)
The user wants a Python function that calculates the remaining bank
balance after a purchase. The function should:

1. **Inputs**:
   - `balance` (float): The current bank balance. The starting balance is 100 bucks.
   - `purchase_amount` (float): The original purchase amount before rounding, between 0 and 100.

3. **Output**: The function should return a tuple `(remaining_balance, rounded_spending)`:
   - `rounded_spending`: The purchase amount rounded to the nearest ten (with ties rounding up).
   - `remaining_balance`: The balance after subtracting the rounded spending amount.

# What Looks Right So Far
The assistant has produced a Python function with the correct signature and logic. The current version of the function is:

```python
def bank_balance_left_after_purchase(balance, purchase_amount):
    ...
    return remaining_balance, rounded_spending
```
```

### Final answers
| | extracted_answer (truncated) |
|---|---|
| **Reset (correct)** | `def remaining_balance(spending: int) -> int: ... return 100 - rounded` |
| **Rewrite (wrong)** | `def bank_balance_left_after_purchase(balance, purchase_amount): ... return remaining_balance, rounded_spending` |

### What happened
- Reset's spec preserves the **exact function signature** `def
  remaining_balance(spending: int) -> int:` from the user — single int
  arg, int return.
- Rewrite's spec **phantoms in** TWO extra requirements:
  (a) a `balance` parameter (the user never said the function takes a
  balance; the user said the balance starts at 100 — a constant);
  (b) a tuple return `(remaining_balance, rounded_spending)` (the user
  never asked for the rounded amount).
- Worse, Rewrite's "What Looks Right" **inlines the verbatim Python code**
  with the wrong function name `bank_balance_left_after_purchase`. The
  assistant then anchors on that name and signature in its final reply.

Both the spec *and* the work-so-far sections are corrupted, and they
reinforce each other. The rewriter LLM "helpfully" inferred extra
abstractions and embedded them as authoritative.

---

## Case 3 — database / sharded-spider-val-149-medium (conv 0)

**Failure mode**: F4 = phantom columns in SELECT.

### Last user message
> We should also include the unique ID for each car maker in the results
> for better identification.

### Reset compacted context (excerpt)
```
# User Task Specification (So Far)
Write a SQL query that retrieves the unique ID (Id) and full name
(FullName) of car makers from the `car_makers` table who have designed
more than 3 car models. Only include car makers that actually design
cars ... The results should include each qualifying car maker's Id and
FullName.

# What Looks Right So Far
The assistant has correctly identified that:
1. The query should join `car_makers` with `model_list` to find makers
   that actually design cars
2. The query should use `HAVING COUNT(ml.ModelId) > 3` to filter for
   makers with more than 3 models
3. The query should include `cm.FullName` in the results
4. The query should include the unique ID (`cm.Id`) in the results as
   requested in the latest user message
```

### Rewrite compacted context (excerpt)
```
# What Looks Right So Far
The assistant has built a query that:
- Uses `INNER JOIN` between `car_makers` (alias `cm`) and `model_list`
  (alias `ml`) on `cm.Id = ml.Maker` ...
- Includes `cm.Maker`, `cm.FullName`, and `COUNT(ml.ModelId) AS
  NumberOfModels` in the SELECT clause.

The current query needs the unique ID (`cm.Id`) added to the SELECT
clause to satisfy the user's latest request.
```

### Final answers
| | extracted_answer |
|---|---|
| **Reset (correct)** | `SELECT cm.Id, cm.FullName FROM car_makers cm INNER JOIN model_list ml ON cm.Id = ml.Maker GROUP BY cm.Id, cm.FullName HAVING COUNT(ml.ModelId) > 3;` |
| **Rewrite (wrong)** | `SELECT cm.Id, cm.Maker, cm.FullName, COUNT(ml.ModelId) AS NumberOfModels FROM car_makers cm INNER JOIN model_list ml ON cm.Id = ml.Maker GROUP BY cm.Id, cm.Maker, cm.FullName HAVING COUNT(ml.ModelId) > 3 ORDER BY NumberOfModels DESC, cm.Maker;` |

### What happened
- Reset's spec is **narrow**: "retrieves the unique ID (Id) and full
  name (FullName) of car makers" — explicit closed list.
- Rewrite's spec uses bullets which is fine, but the "What Looks
  Right" section embeds a **description of an earlier (over-broad)
  query** that included `Maker`, `FullName`, `COUNT`, and `ORDER BY`.
  The assistant treats this description as authoritative current
  state and just *adds* `cm.Id` to it.

Reset's description is more abstract ("uses INNER JOIN ... uses
HAVING COUNT > 3") so the assistant rewrites the query fresh and ends
up with the right column set. Rewrite's literal preservation of a
prior over-broad query anchors the assistant on it. The "include the
unique ID" is interpreted as "add Id to the existing query" instead
of "the answer should contain just the unique ID and the full name."

---

## Case 4 — math / sharded-GSM8K/728 (conv 2)

**Failure mode**: F3 = compaction interpretive bias (rewriter does
arithmetic, embeds result as fact).

### Last user message
> Oh, she has 50 dark green spools as well.

### Reset compacted context
```
# User Task Specification (So Far)
Calculate what percent of Candy's thread spools are blue, given the
following quantities:
- 15 light blue spools
- 45 dark blue spools
- 40 light green spools
- 50 dark green spools

Provide the final numerical answer as a percentage, highlighted on its
own line in the format **ANSWER: X** (with no units or extra text).

# What Looks Right So Far
The assistant correctly identified that the percentage of blue spools
requires both the number of blue spools and the total number of spools.
The assistant correctly calculated the total blue spools as 15 + 45 = 60.
The assistant correctly calculated the percentage as 60% when the total
was 100 spools (15 light blue + 45 dark blue + 40 light green).
```

### Rewrite compacted context
```
# What Looks Right So Far
The assistant has correctly identified that the total number of blue
spools is 15 + 45 = 60. The assistant has also correctly recognized
that the total number of spools must include all colors to compute the
percentage. The assistant has computed the total number of spools as
15 + 45 + 40 + 50 = 160. The percentage of blue spools is
(60 / 160) × 100% = 37.5%.
```

### Final answers
| | extracted_answer |
|---|---|
| **Reset (correct)** | `40` |
| **Rewrite (wrong)** | `37.5` |

### What happened
Pay attention to the rewriter's "What Looks Right" — the rewriter
**did the arithmetic itself** and reported the result as
"correctly recognized" / "has computed". But it's *wrong*:
`15 + 45 + 40 + 50 = 150`, not 160. The rewriter LLM hallucinated an
arithmetic step (the assistant never computed this in the conversation
— the user had just added 50 dark green spools in the last turn), and
got the addition wrong.

The downstream assistant reads this as established prior work and
parrots `37.5%` as the answer. Reset's "What Looks Right" doesn't do
this — it describes what the assistant correctly identified ("must
include all colors") without doing the arithmetic, so the assistant
recomputes and gets 60 / 150 = 40%.

This is the cleanest single-case demonstration of why the second LLM
call is structurally lossy: it tries to be helpful by pre-computing,
and a wrong pre-computation propagates downstream as authoritative.

---

## Takeaway

Across the four cases the same mechanism shows up in different
clothing:

| Case | Mechanism |
|---|---|
| 1 (actions) | Rewriter strips structural boilerplate ("emit ALL outputs"). Assistant only answers latest turn. |
| 2 (code) | Rewriter adds phantom parameters + tuple return AND inlines the wrong function name verbatim. Assistant uses both. |
| 3 (database) | Rewriter inlines verbatim description of an over-broad prior query. Assistant tweaks it instead of rewriting from spec. |
| 4 (math) | Rewriter pre-computes (incorrectly) and embeds result. Assistant trusts it. |

**Reset succeeds in all four** because its templated narrative is more
abstract: it describes *that* the assistant correctly computed a total,
not *what* the total was; *that* a query joined two tables, not *what*
columns it projected. The rewriter LLM's instinct toward concreteness
is what kills it.
