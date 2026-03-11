# Code Experiment Analysis: Why Context Editing Hurts Code Performance

## Overview

Context editing approaches (context_edit, agentic_edit) significantly hurt code task performance compared to baseline, while reflection_only improves it. This document analyzes why.

## Results Summary

| Experiment | Accuracy | Avg Turns (wrong) | Hit Max Turns (wrong) |
|---|---|---|---|
| baseline | 4/19 (21.1%) | 7.5 | 0/15 |
| **reflection_only** | **6/20 (30.0%)** | 7.3 | 0/14 |
| context_edit | 2/19 (10.5%) | 20.8 | **12/17** |
| agentic_edit | 2/18 (11.1%) | 13.8 | 3/16 |

## False Negative Analysis

Only **1 out of 16** incorrect baseline results was a user-simulator distortion (livecodebench/3000, which also timed out). The remaining 15 are genuine assistant failures. The user sim is not the issue for code.

## Per-Problem Comparison

```
Sample ID                   baseline  reflect  ctx_edit  agnt_edit
HumanEval/113                    8t       ✓       22t       14t
HumanEval/128                    6t      6t       16t       10t
HumanEval/141                   10t       ✓       28t       22t
HumanEval/150                    ✓       5t       13t        9t
HumanEval/62                     5t      5t       13t       11t
HumanEval/71                     6t      8t       16t       10t
livecodebench/2754               7t      7t        ✓       11t
livecodebench/2756              10t       ✓       28t       18t
livecodebench/2791               8t       ✓       22t        ✓
livecodebench/2816               7t      7t       19t       11t
livecodebench/2825               7t      7t       19t       15t
livecodebench/2857                ✓       ✓       ERR       ERR
livecodebench/2873               8t      8t       22t       15t
livecodebench/2881                ✓      10t       28t       16t
livecodebench/2883               8t      9t       22t       12t
livecodebench/2888               8t       ✓        ✓        ✓
livecodebench/2893                ✓      8t       22t       14t
livecodebench/2916               9t      9t       28t       23t
livecodebench/2920               6t      6t       16t       10t
livecodebench/3000              ERR      7t       19t       ERR
```

Key observations:
- **Baseline wins that editing loses**: 150, 2881, 2893 — baseline solves in 1-6 turns, editing burns through all turns
- **Reflection wins that baseline loses**: 113, 141, 2756, 2791, 2888 — reflection adds 5 new wins
- **Editing's rare wins**: 2754 (1-turn solve, no editing needed), 2888 (also solved by reflection)
- **context_edit hits max turns on 12/17 wrong problems** — it loops endlessly

## Root Causes from Trace Analysis

### 1. Wrong Assumption Amplifier (Primary Failure Mode)

The context editor condenses early wrong assumptions into clean, authoritative specification documents. Once an incorrect interpretation is "cleaned up" into spec language, it becomes much harder to question.

**Example — Problem 2881 (split strings):**
- Baseline: Correctly solves in 2 turns
- Context edit: Turn 1 guess produces `split_strings(arr, sep, maxsplit)` returning `List[List[str]]`. The editor condenses this into a clean spec. Through **10 conversation resets and 28 turns**, the wrong `List[List[str]]` return type persists because each reset presents it as authoritative spec. The actual problem wants a flat `List[str]`.

**Example — Problem 2893 (max score with parity):**
- Baseline: Progressively refines over 6 turns, eventually dropping the incorrect `k` (jump limit) parameter
- Context edit: Editor bakes `k` into the spec from turn 1. Even when user says "can go to any index on the right" (contradicting `k`), the editor preserves `k` in the summary. After 7 resets and 22 turns, `k` is still there.

### 2. Loss of Corrective Signals After Reset

When the conversation resets, contradicting information from the user gets reinterpreted as confirmation or elaboration rather than correction, because it's now read against the editor's authoritative summary.

In problem 2893, the user saying "can go to any index on the right" was meant to remove the `k` constraint. In the original conversation, this contradicts the previous turn. After a reset, the context summary still has `k`, so the model treats the message as additional flavor text.

### 3. Function Signature Lock-in

For code tasks, the function name, parameter list, and return type decided on turn 1 tend to persist forever under context editing. The editor has no way to know which design decisions are correct vs. incorrect, so it preserves all of them.

- 2881: `split_strings(arr, sep, maxsplit)` persisted through all 10 resets
- 2893: `max_score(nums, k, P)` persisted through 7 resets (should be `max_score(nums, x)`)

### 4. Endless Looping to Max Turns

Context editing causes 12/17 wrong problems to hit max turns (vs 0/15 for baseline). The loop pattern:
1. Editor summarizes (baking in wrong assumptions)
2. Reset conversation
3. Model produces similar wrong code (guided by the authoritative summary)
4. New shard arrives, editor summarizes again
5. Repeat until max turns

Each cycle costs ~2 turns (edit + response) but makes no progress because the summary doesn't change materially.

## Why Reflection Works Better

Reflection succeeds where editing fails because:

1. **Append-only**: Doesn't remove any information — adds "step back and think" guidance
2. **Forces reconceptualization**: Reflection notes like "The user wants a transformation... confirm which concrete output form is desired" (HumanEval/113) prompt the model to reconsider its approach
3. **Delays premature commitment**: On problem 2888, reflection led the model to ask for clarification before coding, avoiding the off-by-one indexing error that the baseline committed to on turn 1
4. **Preserves contradictions**: When user messages contradict earlier assumptions, the full conversation + reflection makes this visible

## Cheatsheet Comparison

All three cheatsheets learned generic, reasonable advice (e.g., "clarify requirements early", "handle edge cases"). None learned anything code-specific or actionable enough to change behavior. The cheatsheets are too high-level to address the structural problems with context editing on code.

- **baseline_memory cheatsheet**: 13 generic items (clarify requirements, iterative development, etc.)
- **context_edit_memory cheatsheet**: 19 items organized into 6 categories, but all generic ("preserve key requirements", "remove irrelevant information")
- **agentic_edit_memory cheatsheet**: 11 items, similar generic advice

## Implications

1. **Context editing is counterproductive for code tasks** in its current form. The editor cannot distinguish correct vs. incorrect design decisions, and by condensing them into spec language, it amplifies wrong ones.

2. **Reflection is the right direction for code** — it adds meta-cognitive guidance without losing information.

3. **Potential improvements to context editing for code:**
   - Never remove code blocks or function signatures from user messages
   - Add explicit "uncertainty markers" in summaries for decisions not yet confirmed by user
   - Allow the editor to flag "this contradicts the previous assumption about X" rather than silently preserving both
   - Consider a hybrid: reflection + selective editing (only edit when the model explicitly asks for a reset)

4. **The cheatsheet learning needs to be more targeted** — current cheatsheets learn platitudes. They need to learn concrete patterns like "in sharded code problems, delay function signature commitment until at least 3 shards have arrived."
