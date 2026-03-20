# CollabLLM Evaluation Loop

Reference documentation for the CollabLLM evaluation pipeline. Based on the [CollabLLM repository](~/collabllm).

## Overview

CollabLLM evaluates multi-turn collaborative conversations. A **user simulator** (LLM) role-plays as a human with access to the full problem, gradually revealing requirements through vague messages. An **assistant** (the model being evaluated) responds. After the conversation ends, artifacts are **extracted** from the conversation and **evaluated** against ground truth.

## Conversation Simulation Loop

```
┌──────────────────────────────────────────────────────┐
│  ChatSessionSimulator.run_chat_simulation()          │
│                                                      │
│  Input: task_desc, single_turn_prompt, max_new_turns │
│                                                      │
│  while budget > 0 and not terminated:                │
│    1. USER TURN                                      │
│       - UserSimulator formats prompt with:           │
│         task_desc, single_turn_prompt, chat_history   │
│       - LLM generates JSON: {current_answer,         │
│         thought, response}                           │
│       - If response == "[[TERMINATE CHAT]]" → stop   │
│       - Append {"role": "user", "content": response} │
│       - budget -= 1                                  │
│                                                      │
│    2. ASSISTANT TURN                                  │
│       - LLMCollaborator passes messages to LLM       │
│       - method="none": raw messages → litellm        │
│       - method="proact": prompted with JSON output   │
│       - Append {"role": "assistant", "content": resp}│
│       - budget -= 1                                  │
│                                                      │
│  Output: List[Dict[str, str]] (conversation)         │
└──────────────────────────────────────────────────────┘
```

### Key parameters
- `max_new_turns`: Total message budget (counts both user and assistant messages)
- `add_system_prompt_ratio`: Fraction of sessions that get a system prompt prepended (default 0.0 for base models, 1.0 for trained models)
- Assistant temperature: 0.8 (default), 0.6 (math)
- User simulator: always gpt-4o with temperature 1.0

### Termination conditions
1. User outputs `[[TERMINATE CHAT]]` as its response
2. Message budget exhausted (`max_new_turns` reached)

## Answer Extraction

After the conversation, artifacts are extracted using an LLM (Claude 3.5 Sonnet in their setup):

```
┌─────────────────────────────────────────────────┐
│  SingleTurnOrChatMetric._extract_final_completion()  │
│                                                      │
│  Input: conversation messages, extract_type           │
│                                                      │
│  Prompt: EXTRACT_MULTITURN_COMPLETION_PROMPT          │
│  - "Extract the final and complete version of         │
│     a/an {extract_type}..."                           │
│  - For code: extraction_requirement appended           │
│    ("start with the following code: def task_func()")  │
│  - Instructions: integrate all revisions, focus on     │
│    completeness, for code include all imports          │
│                                                      │
│  Output: JSON {"thought": "...",                       │
│                "final_completion": "<artifact>"}       │
└──────────────────────────────────────────────────┘
```

### Extract types by task
- **Math**: `"answer"` -- extracts the final numerical/symbolic answer
- **Code**: `"runnable code"` -- extracts complete, executable code. The `extraction_requirement` field tells the extractor to start with the required function signature (e.g., `def task_func(df, dct):`)
- **Document**: `"document"` -- extracts the final document text

### Extraction model
CollabLLM uses `claude-3-5-sonnet-latest` for extraction via `eval_generation_kwargs`. This is a strong model that can reliably restructure code to match the required function signature even when the conversation used different naming.

## Evaluation (Metrics)

Metrics are registered via `@SingleTurnOrChatMetric.register_metric("name")` and invoked with signature strings like `"answer->accuracy"` or `"runnable code->pass_rate"`.

### Math: `accuracy` metric

```
┌──────────────────────────────────────────────────┐
│  AccuracyMetric.score()                           │
│                                                   │
│  Input: prompt (question), groundtruth, completion│
│                                                   │
│  ACCURACY_PROMPT:                                 │
│  "You are a helpful and meticulous evaluator.     │
│   Determine whether the model's final response    │
│   is factually correct and consistent with the    │
│   provided ground truth."                         │
│                                                   │
│  Rating: binary (1 = correct, 0 = incorrect)      │
│  Output: JSON {"thought": "...", "accuracy": 0|1} │
│                                                   │
│  Model: eval model (Claude Sonnet), temp=0.0      │
│  Retries: up to 50 attempts, 60s retry delay      │
└──────────────────────────────────────────────────┘
```

### Code: `pass_rate` metric

```
┌──────────────────────────────────────────────────┐
│  PassRateMetric.score()                           │
│                                                   │
│  Input: completion (extracted code),              │
│         metadata.test (unittest code),            │
│         metadata.entry_point (function name)       │
│                                                   │
│  bigcodebench.eval.untrusted_check(               │
│      completion,           # extracted code        │
│      metadata["test"],     # test suite            │
│      metadata["entry_point"],  # "task_func"       │
│      max_as_limit=300*1024,                        │
│      max_data_limit=300*1024,                      │
│      max_stack_limit=300*1024,                     │
│      min_time_limit=60,                            │
│      gt_time_limit=60,                             │
│  )                                                │
│                                                   │
│  Returns: 1.0 if all tests pass, 0.0 otherwise    │
│  No LLM involved -- pure code execution           │
└──────────────────────────────────────────────────┘
```

The test suite is a full unittest.TestCase class from BigCodeBench that calls `task_func(...)` with specific arguments and checks return values.

### Interactivity: `interactivity` metric

```
┌──────────────────────────────────────────────────┐
│  InteractivityMetric.score()                      │
│                                                   │
│  Input: messages (full conversation)              │
│                                                   │
│  INTERACTIVITY_PROMPT:                            │
│  "Judge how interactive the assistant was..."      │
│  Scale: 0 (not interactive) to 1 (highly)         │
│                                                   │
│  Output: JSON {"thought": "...",                   │
│                "interactivity": float}             │
│                                                   │
│  Model: eval model, temp=0.0                      │
└──────────────────────────────────────────────────┘
```

### Token efficiency: `token_amount` metric

Counts assistant output tokens using tiktoken (cl100k_base). Returns `assistant_tokens / 1000`. Used with negative weight in reward aggregation to penalize verbose responses.

## Reward Aggregation

```python
MR = sum(metric_score[i] * weight[i] for i in range(len(metrics)))
```

Example weights:
- Math: `accuracy: 1.0`, `interactivity: 0.0`, `token_amount: -0.5`
- Code: `pass_rate: 1.0`, `interactivity: 0.0`, `token_amount: -0.5`

## End-to-End Flow

```
Dataset (e.g., BigCodeBench)
    │
    ▼
For each sample:
    │
    ├─ single_turn_prompt: "Compares and visualizes sales data..."
    ├─ single_turn_completion: ground truth code
    ├─ metadata: {test, entry_point, extraction_requirement}
    │
    ▼
ChatSessionSimulator.run_chat_simulation()
    │  user sim: gpt-4o, assistant: model under test
    │  max_new_turns: 14 (7 exchanges)
    │
    ▼
conversation: [{"role": "user", "content": ...}, ...]
    │
    ▼
For each metric (parallel via ThreadPoolExecutor):
    │
    ├─ "runnable code->pass_rate":
    │      1. Extract code via LLM (Claude Sonnet)
    │      2. Run bigcodebench.eval.untrusted_check()
    │      3. Return 1.0 or 0.0
    │
    ├─ "interactivity":
    │      1. Judge via LLM
    │      2. Return [0, 1]
    │
    └─ "token_amount":
           1. Count tokens (tiktoken)
           2. Return tokens/1000
    │
    ▼
Aggregate: MR = weighted sum
    │
    ▼
Save eval_results.json + eval_details.json
```

## Our Implementation Differences

| Aspect | CollabLLM | Our ctx_editor |
|--------|-----------|----------------|
| Assistant input | Standard messages list | Option 2 (packed into single user msg) |
| System prompt | Conditional (ratio-based) | Always prepended |
| Extraction model | Claude 3.5 Sonnet | gpt-4o-mini / gpt-4o |
| User simulator | gpt-4o | gpt-4o-mini |
| Async | ThreadPoolExecutor | asyncio |
| Context editing | N/A | Strategy.prepare_context() between user/assistant turns |
| Turn counting | max_new_turns (total messages) | max_turns (user messages only) |
