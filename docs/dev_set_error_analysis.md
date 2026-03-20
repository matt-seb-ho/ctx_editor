# Dev Set Error Analysis — 2026-03-14

## Experiment Setup

- **Model**: gpt-5-mini (medium reasoning effort) as assistant/analyzer/editor
- **User/System agent**: gpt-4o-mini
- **Data**: `dev_{task}_subset.json` (23 math, 25 code, 25 actions)
- **Strategies**: S0 (baseline), S1 (append analysis), S2 (context edit v2), each ± memory
- **Memory**: batched mode (batch_size=5), continual learning, with full_spec_q + ground_truth_a grounding

## Results Summary

| Task | Concat (ceiling) | S0 | S0+mem | S1 | S1+mem | S2 | S2+mem |
|------|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| **math** (n=23) | **65%** | 22% | 43% | **48%** | 43% | 39% | 30% |
| **code** (n=25) | **84%** | 4% | 16% | 8% | **21%** | 9% | 8% |
| **actions** (n=25) | **60%** | 8% | 0% | **16%** | 12% | 0% | 4% |

The concat baseline confirms a massive gap: multi-turn performance is far below the
single-turn ceiling. All strategies have significant room to improve.

## Concat Baseline (Upper Bound)

Single-turn evaluation: all shards concatenated into one user message (as a bulleted list),
sent to gpt-5-mini. No user simulation, no multi-turn interaction.

Note: This is the LiC **Concat** setting, not the STQ (original single-turn question).
Concat uses the same shard content that the user agent reveals turn by turn, so the gap
between Concat and multi-turn results isolates degradation from incremental disclosure.
See `docs/concat_baseline.md` for details on the distinction.

**How to run:**
```bash
python scripts/run_concat_baseline.py --tasks math code actions
python scripts/run_concat_baseline.py --tasks math --model gpt-5-mini --reasoning-effort medium
```

Results: math 65%, code 84%, actions 60%. This is the ceiling — any multi-turn strategy
scoring below this is losing performance to the sharded disclosure process.

## Finding 1: S2 Analyzer Is Too Passive (7-11% edit rate)

Across all S2 runs, the analyzer almost never triggers edits:

| Task | Analyses | EDITs | NO EDITs | Edit rate |
|------|----------|-------|----------|-----------|
| math | 85 | 6 | 79 | **7%** |
| code | 113 | 12 | 101 | **11%** |
| actions | 79 | 8 | 71 | **10%** |

When edits DO occur, they often hurt: in S2 math, only **1 of 6 edited problems was solved
correctly** (17% edit success rate). Meanwhile, 8 of 17 non-edited problems were solved correctly
(47%) — matching baseline behavior since no edits means S2 behaves like S0.

**Root cause**: The analyzer correctly extracts user intent and checks whether the assistant's
approach contradicts it. But gpt-5-mini's common failure mode — presenting multiple interpretations
and asking clarifying questions instead of committing — doesn't register as "contradicting user
intent." The assistant's approach is technically valid (listing possibilities), it just wastes turns.

**The analyzer doesn't detect**:
- Over-branching / multi-scenario presentation when a single interpretation is natural
- Failure to commit to an answer within limited turns
- Wasted turns on unnecessary clarification

## Finding 2: S2 Has a Structural Problem with Actions

S2 scores **0%** on actions (vs S1's 16%, S0's 8%). The actions task (BFCL parallel function calls)
requires the final response to contain ALL accumulated function calls from across the conversation.

S2's context compaction destroys the accumulated state:
- Old conversation → compacted to task spec + aligned work
- Assistant sees compacted context + latest user message
- Assistant responds only to the latest request, not the full accumulated set
- Ground truth requires all calls in one response

S1 works better because the analysis tags accumulate all user requirements in a bulleted list,
and the assistant can see the full history of prior calls to re-emit them.

## Finding 3: Memory Injection Harms Actions (S0: 8% → 0%)

The cheatsheet learned for S0+mem actions contains analyzer-focused workflow instructions
like "If any required information is missing or ambiguous, ask a targeted clarifying question"
and "Do not assume sensible defaults for required values." These directly conflict with the
actions system prompt which says "You should only return the function calls in your response."

The cheatsheet is written for the analyzer (target=assistant uses render_for_assistant), but its
prescriptive rules about clarification and defaults cause the assistant to ask questions instead
of emitting function calls, burning turns.

## Finding 4: S2+mem Math Regresses (39% → 30%)

The S2+mem cheatsheet amplifies gpt-5-mini's multi-branching tendency. Rules like "present
labeled scenarios," "never silently substitute numeric defaults," and "ask one minimal
clarifying question" cause the model to present even MORE interpretations and commit even less.

Combined with S2's low edit rate, memory makes S2 worse because:
1. The cheatsheet encourages over-analysis → more turns wasted
2. The analyzer rarely triggers edits to rescue the conversation
3. When edits do occur, the compacted context can lose important state

## Finding 5: S1 Works Through Passive Consolidation

S1's advantage is not that the analysis adds deep critical insight — it's that:
1. **Preserves full conversation history** (no context loss)
2. **Provides a consolidated task spec** that accumulates user facts across turns
3. **Doesn't disrupt the assistant's flow** with context resets

The `<conversation_analysis>` tags essentially give the assistant a clean, numbered list of
everything the user has said so far. This is particularly valuable when the user reveals
information gradually (the core LiC setup).

## Finding 6: Error Attribution Was Disabled

Error attribution was disabled (`error_attribution.enabled: false`) in all runs. To get
automated error categorization, re-run with `error_attribution.enabled=true error_attribution.mode=batch`.

## Actionable Next Steps

1. **Fix S2 edit sensitivity**: The analyzer needs to detect over-branching and failure to commit,
   not just factual contradictions. Consider adding turn-count awareness ("if the assistant has
   not committed to an answer after N turns, flag this as an issue").

2. **Fix actions + S2 interaction**: Either (a) don't use S2 for actions, or (b) change compaction
   to preserve the full set of accumulated function calls, not just the task spec.

3. **Fix memory target for S0**: S0+mem uses target=assistant, which means the cheatsheet is
   rendered with `render_for_assistant` and injected into the system prompt. But the cheatsheet
   content is written for the analyzer (the reflection prompts produce analyzer-focused principles).
   Either use a separate assistant-focused reflection prompt, or don't use memory with S0.

4. **Re-run with error attribution enabled** to get automated failure categorization.

5. **Consider task-specific strategy selection**: S1 for actions (preserves accumulation),
   S2 for math/code (where context compaction should help most), once S2's edit rate is fixed.
