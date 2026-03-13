# Simulation

This document describes how a single evaluation instance runs: the conversation loop, the user agent, and the system agent.

## Overview

A simulation consists of a multi-turn conversation between a simulated user and the assistant being evaluated. The user progressively reveals information (shards), and the assistant must gather enough information to answer correctly.

The key insight from LiC: the problem is *underspecified at the start*. The user has a complete specification split into shards, but only reveals them one at a time in response to the assistant's questions or attempts.

---

## ConversationSimulator

`core/simulator.py` — orchestrates the full conversation.

**Initialization:**
- Loads a `sample` (contains `shards`, `task_id`, `full_spec_q`, `ground_truth_a`)
- Generates the task system prompt and stores it in the trace

**Main loop (`run`):**

```
while not completed and turns < max_turns:
    if all shards revealed → break (termination: all_shards_revealed)
    run one turn
    if user budget exhausted → break (termination: user_budget_exhausted)

if no correct answer found → result is_correct=False
```

Termination reasons: `correct_answer` (implicit via `is_completed`), `all_shards_revealed`, `max_turns_reached`, `user_budget_exhausted`.

**Single turn (`_run_turn`):**

1. **User generates response** — UserAgent produces the next message and optionally reveals a shard
2. **Apply context strategy** — `strategy.prepare_context()` prepares the context (may run the `ConversationAnalyzer` for S1/S2, may reset the trace for S2)
3. **Render for assistant** — `_render_for_assistant()` converts the message list into a tagged string inside a single user message (Option 2 format: `[user]`/`[assistant]`/`[compacted conversation]` tags)
4. **Assistant generates response** — model call with the rendered context
5. **System verifies** — SystemAgent classifies the assistant's response type
6. **If answer attempt** — extract the answer and evaluate against ground truth
   - Correct → mark completed, store `SimulationResult`
   - Incorrect → conversation continues (user can reveal more shards)

---

## UserAgent

`agents/user_agent.py` — simulates a lazy user who reveals information gradually.

**Turn 0:** Returns the first shard verbatim as the opening message (no LLM call).

**Turn 1+:** Calls the LLM with:
- The conversation so far
- Already-revealed shards
- Not-yet-revealed shards

The model decides which (if any) unrevealed shard to reveal next, rephrased conversationally.

**Output format (JSON):**
```json
{"response": "yeah mostly in the mornings", "shard_id": 2}
```
`shard_id: -1` means no shard was revealed (e.g., assistant asked an irrelevant question).

**Prompt rules (summarized):**
- Reveal at most one shard per turn
- Include all information from the chosen shard (no partial reveals)
- Don't repeat already-revealed shards
- Rephrase shards conversationally; never copy verbatim
- Don't ask questions; stay declarative and brief
- Ignore irrelevant or vague clarification requests

**Special case:** Tasks like `translation`, `summary`, `data2text` use pre-scripted shard reveals via `task.populate_sharded_prompt` instead of LLM generation.

---

## SystemAgent

`agents/system_agent.py` — a judge that runs after every assistant turn.

### Step 1: Verify (`verify_response`)

Classifies the assistant's last response into one of:

| Type | Description |
|---|---|
| `answer_attempt` | A complete, extractable final answer |
| `clarification` | A single, specific question (<100 words) |
| `interrogation` | Multiple questions |
| `discussion` | Long elaboration without a final answer |
| `hedge` | Multiple conditional answer candidates |
| `refuse` | Explicit or implicit refusal |
| `missing` | Empty response |

Only `answer_attempt` triggers extraction. All other types let the conversation continue.

### Step 2: Extract (`extract_answer`)

If the response is an `answer_attempt`, extracts the verbatim answer string (up to 3 attempts). Extraction strategy is task-specific:

- `gen` — LLM extracts the answer string directly
- `prefix_suffix` — LLM outputs a `prefix[...]suffix` pattern to locate the span
- `full_response` — return the full assistant response as-is
- `task_specific` — delegate to `task.extract_answer()`

The extracted answer must be a substring of the original response (verified before accepting).

### Step 3: Evaluate

`task.evaluator_function(extracted_answer, sample)` checks correctness. The result is logged to the trace. Only a correct answer ends the simulation.
