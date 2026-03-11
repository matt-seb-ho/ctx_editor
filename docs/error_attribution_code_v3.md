# Error Attribution: Context Edit V3 Code Experiments

**Date**: 2026-03-11
**Runs analyzed**:
- Context Edit V3 (no memory): `outputs/2026-03-10/21-49-09/` — 9/20 correct (45%)
- Context Edit V3 + memory: `outputs/2026-03-11/00-59-07/` — 7/19 correct (37%)

**Model**: gpt-5-mini (assistant + context editor), gpt-4o-mini (user/system)
**Task**: code, `data/test_code_subset.json` (20 problems)

## Methodology

Every incorrect conversation from both runs was manually analyzed by reading the full trace (user shard messages, assistant responses, context edit summaries) and comparing against the ground truth specification. Each failure was categorized into one of three buckets:

1. **non-assistant**: User simulator messages don't sufficiently describe the problem, context editor corrupts intent, or answer extraction failure (model got it right but evaluation couldn't extract/match the answer)
2. **assistant-communication**: Assistant exhibits bad multi-turn behavior — premature assumptions, not backtracking when corrected, failing to integrate information across turns. The failure is in conversational understanding (the LiC-style failure mode)
3. **assistant-coding**: User relayed the task sufficiently, assistant understood the task, but made an implementation mistake (wrong algorithm, wrong return type, off-by-one, missing rounding, etc.)

## Results Summary

| Category | No-Memory (11 wrong /20) | With-Memory (13 wrong /19) |
|---|---|---|
| **non-assistant** | 4 (36%) | 4 (31%) |
| **assistant-communication** | 1 (9%) | 1 (8%) |
| **assistant-coding** | 6 (55%) | 8 (62%) |

## Detailed Per-Problem Analysis

### Problems wrong in BOTH runs (9 persistent failures)

| Problem | Category | Failure Description |
|---|---|---|
| HumanEval/113 | **non-assistant** | Spec requires a bizarre string output format: `"the number of odd elements 4n the str4ng 4 of the 4nput."` where the count replaces every "i". The user simulator never described this format — only mentioned "counting odd digits." Assistant reasonably returned integer counts. |
| HumanEval/128 | **non-assistant** | Spec returns a single number: `product_of_signs * sum_of_abs_values`. User said "calculate product of signs and aggregate them" and "add up absolute values" separately, but never stated the final operation is to multiply them together. Assistant returned a dict with both components. |
| HumanEval/71 | **assistant-coding** | Correct algorithm (Heron's formula, triangle inequality, returns -1 for invalid). But **missing `round(area, 2)`** — returns raw `math.sqrt()` result. User hinted with "6.00" but assistant didn't implement rounding. |
| livecodebench/2816 | **assistant-coding** | Correct palindrome algorithm (set mismatched pairs to `min(a,b)`), but **returns tuple `(moves, string)` instead of just the string**. |
| livecodebench/2825 | **assistant-coding** | **Wrong algorithm**: uses `sum(count % 2 for each char)` parity approach. This gives correct answer for the provided example ("aaabc"→3) by coincidence, but fails on inputs like "aab" (returns 1, correct is 2) or "aaaa" (returns 0, correct is 1). Doesn't model the actual deletion operation. |
| livecodebench/2916 | **assistant-communication** | User said "the array's length n is between 1 and 100" (defining n = len(arr)), but assistant defined `can_split_into_n(nums, m, n)` with n as a separate parameter. Failed to integrate the information that n = len(nums) from the user's constraint description. |
| livecodebench/2920 | **assistant-coding** | **Circular gap bug**: The array wraps around (spec uses `(i-1+n)%n` and `(i+1)%n`). Assistant computes wrap-around distance as `max(left_dist, right_dist)` instead of `(left_dist + right_dist) // 2`. E.g., single occurrence at index 0 in array of 5 → returns 4 instead of correct answer 2. |
| livecodebench/3000 | **assistant-coding** | Enforces `gap = max(1, x)` when x=0 should allow same-index pairs. Also uses nested class `BIT` inside the function which causes extraction failure — but even with extraction fixed, the algorithm has edge case bugs. |

Note: HumanEval/62 was originally borderline. The algorithm is correct but the function is named `polynomial_derivative` instead of `derivative`, causing extraction failure. Also has edge case differences (returns `[0]` for constant polynomial, GT returns `[]`). Categorized as **non-assistant** since the primary failure is the user never specifying the expected function name.

| HumanEval/62 | **non-assistant** | Correct derivative algorithm matching the user's example. Function named `polynomial_derivative` instead of `derivative` → extraction/evaluation failure. User never specified required function name. Secondary issue: returns `[0]` for constant polynomial where GT returns `[]`. |

### Problems wrong ONLY in no-memory run (2)

| Problem | Category | Failure Description |
|---|---|---|
| livecodebench/2791 | **non-assistant** | User misrepresented the formula: said "i is the current holder, k is the turn number" when spec says i = turn number, k = fixed step parameter. Both variable meanings were swapped. Assistant faithfully implemented the (wrong) user description. |
| livecodebench/2873 | **assistant-coding** | Correct sieve + pair-finding algorithm. Returns list of tuples `[(p,q)]` instead of list of lists `[[x,y]]` as spec requires. |

### Memory regressions (4 — correct without memory, wrong with)

| Problem | Category | Failure Description |
|---|---|---|
| livecodebench/2756 | **assistant-coding** | Correct logic (find two cheapest chocolates, check affordability). **Returns tuple `(starting_cash, remaining)`** instead of single int. The no-memory run returned a single value correctly. |
| livecodebench/2883 | **assistant-coding** | Correct DP algorithm over power-of-5 binary substrings. **Off-by-one**: returns `dp[n] - 1` (number of cuts) instead of `dp[n]` (number of substrings). Spec asks for "minimum number of substrings." The no-memory run returned the correct count. |
| livecodebench/2888 | **assistant-coding** | Correct Boyer-Moore + prefix scan algorithm. **Off-by-one in split index**: spec defines split at i as left=`nums[0:i+1]`, code uses left=`arr[:i]`. Returns index 1 higher than expected. E.g., for [1,2,2,2] returns 3 instead of spec's expected 2. |
| livecodebench/2893 | **non-assistant** | The context editor manufactured a false A/B clarification ("A: parity moves forbidden, B: negate the value"), neither matching the actual spec (subtract a fixed penalty `x`). The user simulator was forced to pick option B, leading the assistant to implement value negation instead of a fixed penalty. Function signature `max_score(nums)` also omits the `x` parameter entirely. |

## Observations

### 1. Coding errors dominate (~55-60%)

The majority of failures are implementation bugs where the assistant understood the problem but made mistakes:
- **Wrong return types** (4 cases): returning tuples instead of single values or strings, tuples instead of lists
- **Off-by-one errors** (2 cases): cuts vs parts, split index interpretation
- **Wrong algorithms** (1 case): parity-count approach for 2825
- **Missing operations** (1 case): no rounding in triangle area
- **Circular array bugs** (1 case): wrong distance calculation for 2920

### 2. User/system failures are significant (~30-35%)

Four problems have fundamental issues outside the assistant's control:
- User simulator failing to describe key output formats (HE113's string template, HE128's multiplication operation)
- User simulator swapping variable meanings (LC2791)
- Context editor corrupting the problem description (LC2893 regression)
- Function name mismatch causing extraction failure (HE62)

### 3. Multi-turn communication failures are rare (~8%)

Only 1 of 15 unique wrong problems (livecodebench/2916) exhibits the LiC-style multi-turn breakdown we are specifically studying. The assistant failed to integrate "the array's length n is between 1 and 100" with the goal of splitting into n arrays. This suggests context editing has largely solved the communication problem, but the model still struggles with correct implementation.

### 4. Memory regressions are implementation bugs, not communication

All 4 memory regressions are assistant-coding errors (3 implementation bugs + 1 context editor corruption). Memory doesn't appear to hurt communication — it may encourage over-engineering (returning richer data structures like tuples) or introduce subtle off-by-one errors through cheatsheet-influenced assumptions about problem semantics.

### 5. Implications for research direction

Since ~60% of failures are coding mistakes on problems the model understood:
- Context editing improvements have diminishing returns on these problems
- Memory-based learning could potentially help if it captures patterns like "return the simplest data type" or "match the spec's indexing convention"
- The evaluation harness should be audited for extraction robustness (several livecodebench problems have `extracted_answer: ""`)
- The 4 non-assistant failures should be excluded or fixed before drawing conclusions about strategy effectiveness
