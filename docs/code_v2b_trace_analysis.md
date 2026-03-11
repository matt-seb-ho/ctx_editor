# Context Edit V2b vs Baseline: Code Task Trace Analysis

**Date**: 2026-03-10
**Baseline run**: `outputs/2026-03-10/16-16-51/` (code/baseline)
**V2b run**: `outputs/2026-03-10/20-48-29/` (code/context_edit)

## Summary

| Category | Count | Problems |
|----------|-------|----------|
| Both correct | 2 | HumanEval/857, livecodebench/2893 |
| Both wrong | 14 | (see below) |
| Baseline right, V2b wrong | 2 | HumanEval/150, livecodebench/2881 |
| V2b right, baseline wrong | 2 | livecodebench/2791, livecodebench/2888 |

Net effect: tied at 4 vs 4 correct, but on different problems. The V2b editor helps in some cases and hurts in others.

---

## Regressions: Baseline correct, V2b wrong

### HumanEval/150 (`x_or_y`)

**Problem**: Write `x_or_y(n, x, y)` that returns x if n is prime, y otherwise.

**Baseline** solved this in 1 turn -- the initial shard ("Decide between two values based on a prime") was enough for the model to guess the function signature `decide_by_prime(n, val_if_prime, val_if_composite)` with correct logic.

**V2b** failed across 13 turns and 4 resets. The root cause: the editor correctly noted that the user "did NOT specify input format (how n, x, y are provided: stdin, function arguments, one line vs multiple lines)" and the assistant kept generating `solve()` functions that read from stdin instead of a function with proper arguments. Despite all 8 shards eventually being revealed, the assistant never converged on a function-argument interface.

**Diagnosis**: The editor's accurate identification of underspecification backfired. By explicitly flagging the ambiguity about input format, it nudged the assistant to make a wrong choice (stdin) rather than the natural default (function arguments). The baseline, by contrast, just wrote a function with arguments immediately without overthinking the input format. This is a case where **highlighting ambiguity made things worse** because the assistant's "resolution" of the ambiguity was wrong.

### livecodebench/2881 (`splitWordsBySeparator`)

**Problem**: Split each string in an array by a separator, return flat list of non-empty results.

**Baseline** solved this in 2 turns, correctly naming the function `split_strings_by_separator` and returning a flat list.

**V2b** failed across 28 turns and 9 resets. Two compounding issues:
1. **Function name**: The assistant kept using wrong names (`split_strings`, `split_strings_by_sep`) instead of the expected `split_strings_by_separator`. The editor never flagged function naming as important.
2. **Return structure**: The assistant repeatedly returned list-of-lists instead of a flat list, despite the editor correctly capturing "return an array of strings" in the user intent.

**Diagnosis**: The repeated resets actually prevented convergence. Each reset gave the assistant a fresh context, but the summarized intent was generic enough that the assistant kept re-inventing slightly different (wrong) implementations. The baseline had the advantage of accumulating conversation context that progressively clarified the problem.

---

## Improvements: V2b correct, baseline wrong

### livecodebench/2791 (Game losers in a circle)

**Problem**: Friends in a circle pass a ball k steps clockwise; game ends when someone receives it twice; return who never got the ball.

**Baseline** failed after 8 turns (no answer extracted). It kept producing the correct function `who_are_game_losers(n, k)` with correct logic, but somehow never passed evaluation -- possibly a function naming mismatch with what the test harness expected.

**V2b** succeeded after 7 turns and 2 resets. Key: the first edit correctly captured the game rules, and after the second edit refined the understanding (explicitly noting "no explicit passing rule, step size, or starting player provided"), the assistant produced `find_game_losers(n, k)` which passed.

**Diagnosis**: The editor's summarization helped the assistant build up a clearer mental model of the problem progressively, leading to a correct implementation that matched the test harness's expectations.

### livecodebench/2888 (Dominant element split)

**Problem**: Find smallest index to split an array such that both halves share the same dominant element.

**Baseline** failed after 8 turns. It produced `smallest_valid_split_index(arr)` repeatedly but the initial interpretation was wrong (splitting by sum equality) and later corrections still didn't converge.

**V2b** succeeded after 4 turns and 1 reset. The editor's first edit correctly identified the core issue: "the assistant's previous approach was wrong" and clearly stated the requirement about dominant elements in both parts. After the reset, the assistant got it right.

**Diagnosis**: This is the editor working as intended -- it identified the assistant's incorrect assumption from early turns, flagged it in the approach_evaluation, and the fresh start with corrected context led to a correct solution.

---

## Both-Wrong Cases: Did the Editor Help Intermediate Reasoning?

### HumanEval/62 (`derivative`)

**Problem**: Compute polynomial derivative from coefficient list.

**Both failed** to get the answer accepted, but the ctx_edit version actually produced correct logic: `derivative(coeffs)` returning `[i * seq[i] for i in range(1, len(seq))]` which gives correct results for all test cases. The baseline produced `polynomial_derivative(coeffs)` with identical logic but wrong function name.

**Editor quality**: The approach_evaluation correctly identified that the assistant's initial approach (parsing string polynomials) was wrong, and after one reset the assistant switched to the correct list-of-coefficients approach. The editor was doing its job well here -- the failure is likely in the test harness / answer extraction pipeline, not the editor.

### livecodebench/2825 (String deletion minimization)

**Problem**: Minimize string length by repeatedly choosing an index and deleting the closest occurrence of the same character on both sides.

**Both failed**. The baseline produced a wrong algorithm (deleting adjacent pairs or using an a/b/c specific rule). The ctx_edit version had a more interesting failure: the editor repeatedly flagged that the assistant's interpretation was wrong and that "nearby" and "spot" were ambiguous. By the final turn, the assistant was **still asking clarifying questions** instead of producing code.

**Editor quality**: The approach_evaluation was impressively accurate -- it correctly identified every wrong assumption the assistant made and noted what was unconfirmed. However, this turned into a failure mode: **the editor was so thorough at identifying ambiguity that the assistant became paralyzed** and never committed to an implementation. The baseline at least produced code (wrong code, but code).

---

## Key Findings

### What V2b Editor Does Well
1. **Approach evaluation is accurate**: The `<approach_evaluation>` sections correctly identify wrong assumptions and flawed reasoning in almost every case examined.
2. **Helps with complex multi-constraint problems**: For problems like livecodebench/2888 (dominant element split), the editor effectively purges wrong early reasoning and gives the assistant a clean slate.
3. **Separates user intent from assistant assumptions**: The `<user_intent>` sections generally do a good job cataloging what was stated vs. what was assumed.

### Remaining Failure Modes
1. **Over-flagging ambiguity**: By explicitly noting "the user did NOT specify X", the editor sometimes pushes the assistant to make worse choices than it would have made by default (HumanEval/150 stdin vs function args).
2. **Reset loops without convergence**: When the problem is genuinely hard or the shards don't resolve ambiguity, repeated resets create a cycle where the assistant keeps producing slightly different wrong answers (livecodebench/2881 with 9 resets).
3. **Analysis paralysis**: The editor can be so thorough at identifying unresolved ambiguity that the assistant stops producing code entirely and asks questions instead (livecodebench/2825).
4. **Function naming not preserved**: The editor summarizes semantic intent but loses syntactic details like expected function names, which matters for test harness evaluation.

### Recommendations
1. **Bias toward defaults**: When the editor flags unspecified aspects (like input format), it should recommend the most natural/common default rather than just noting the gap.
2. **Cap resets**: After 2-3 resets without improvement, the strategy should fall back to letting the conversation accumulate naturally.
3. **Preserve syntactic hints**: If any shard contains a function signature, the editor should preserve it verbatim in the user_intent section.
4. **Require code output**: The edited context or system prompt should emphasize that the assistant must always produce a code answer, never just ask questions.
