# Lost in Conversation (LiC) Log Format

Reference for the cache of LiC original repo logs stored at `~/l3_dir`.

## Directory Structure

```
~/l3_dir/
├── laban_lic_logs_math_sharded/
│   └── lazy/
│       ├── lazy_math_t-gpt-5.2.jsonl
│       ├── lazy_math_t-gpt-5-mini.jsonl
│       ├── lazy_math_claude4.6-opus.jsonl
│       └── ...  (one JSONL per model)
├── laban_lic_logs_code_sharded/
│   └── lazy/
│       └── lazy_python_{model}.jsonl
├── laban_lic_logs_database_sharded/
│   └── lazy/
│       └── lazy_database_{model}.jsonl
├── laban_lic_logs_actions_sharded/
│   └── lazy/
│       └── lazy_apis_{model}.jsonl
└── *.zip  (original zips, already extracted)
```

**Naming convention**: `lazy_{task_keyword}_{model}.jsonl`
- Math: `lazy_math_{model}`
- Code: `lazy_python_{model}`
- Database: `lazy_database_{model}`
- Actions: `lazy_apis_{model}`

## Available Models (34 total)

Azure OpenAI (`t-` prefix): `t-gpt-4o`, `t-gpt-4o-mini`, `t-gpt-4o-whelp`, `t-gpt-4.1`, `t-gpt-4.5`, `t-gpt-5-chat`, `t-gpt-5-mini`, `t-gpt-5-nano`, `t-gpt-5.1`, `t-gpt-5.2`, `t-o1`, `t-o3`, `t-grok-4`

Direct API: `gpt-4o`, `gpt-4o-mini`, `claude3-haiku`, `claude3.7-sonnet`, `claude4.6-opus`, `claude4.6-sonnet`, `gemini-2.0-flash`, `gemini-2.5-flash`, `gemini-2.5-pro`, `gemini-3-pro-preview`, `command-a`, `deepseek-r1`

Local/other (`l-`/`b-`/`sfr-` prefixes): `l-phi-4`, `phi-4`, `l-llama3.1-8b`, `l-olmo2-13b`, `l-command-a`, `b-llama3.1-8b-instruct`, `b-deepseek-r1`, `sfr-llama3.3-70b-instruct`, `llama4-scout-17b-16e-instruct`

Not all models are present for all tasks. Check the directory listing.

## JSONL Record Format

Each line in a JSONL file is one conversation. One file contains all conversations for a given (task, model) pair.

```json
{
  "conv_id": "69978b57175c53948c8abe33",
  "conv_type": "lazy",
  "task": "math",
  "task_id": "LazyGSM8K/1058",
  "dataset_fn": "sharded_math.json",
  "assistant_model": "t-gpt-5.2",
  "system_model": "t-gpt-4o-mini",
  "user_model": "t-gpt-4o-mini",
  "git_version": "d531b96...",
  "trace": [ ... ],
  "is_correct": null,
  "score": 1.0
}
```

### Top-level fields

| Field | Type | Description |
|---|---|---|
| `conv_id` | str | Unique conversation UUID |
| `conv_type` | str | Always `"lazy"` for these logs (= "sharded" multi-turn mode) |
| `task` | str | `"math"`, `"python"`, `"database"`, or `"apis"` (note: not "code"/"actions") |
| `task_id` | str | Problem identifier (see task ID formats below) |
| `dataset_fn` | str | Source dataset filename |
| `assistant_model` | str | Model under evaluation |
| `system_model` | str | Model used for answer extraction/verification (usually `t-gpt-4o-mini`) |
| `user_model` | str | Model used for user simulation (usually `t-gpt-4o-mini`) |
| `git_version` | str | Commit hash of the LiC repo |
| `trace` | list[dict] | Ordered list of conversation events (see below) |
| `is_correct` | bool/null | Correctness flag (null for math; bool for actions) |
| `score` | float/null | 0.0 or 1.0 (primary correctness indicator for math/code/database) |

### Determining correctness

The `is_correct` and `score` fields have inconsistent semantics across tasks:

- **Math/code/database**: Use `score`. `1.0` = correct, `0.0` = wrong. `is_correct` is typically `null`.
- **Actions**: Use `is_correct` (bool). `score` may be `0`, `1`, or `null`.
- **Safe check**: `score is not None and float(score) == 1.0` works across all tasks, but for actions also check `is_correct is True`.

### Conversations per question

Each question has exactly **10 independent conversations** (10 runs). Conversations appear in file order, so `convs[:3]` gives the first 3 runs.

## Task ID Formats

| Task | Format | Example |
|---|---|---|
| Math | `LazyGSM8K/{id}` | `LazyGSM8K/1058` |
| Code (HumanEval) | `Lazy-HumanEval/{id}` | `Lazy-HumanEval/105` |
| Code (LiveCodeBench) | `livecodebench/{id}` | `livecodebench/2891` |
| Database | `lazy-spider-val-{id}-{difficulty}` | `lazy-spider-val-633-medium` |
| Actions | `LazyBFCL/{category}_{id}` | `LazyBFCL/parallel_198` |

### Mapping to ctx_editor format

Our `data/question_id_to_full_spec_qa.json` uses a different prefix convention. The mapping is:

| LiC log format | ctx_editor format |
|---|---|
| `LazyGSM8K/X` | `sharded-GSM8K/X` |
| `Lazy-HumanEval/X` | `sharded-HumanEval/X` |
| `livecodebench/X` | `sharded-livecodebench/X` |
| `lazy-spider-val-X` | `sharded-spider-val-X` |
| `LazyBFCL/X` | `sharded-BFCL/X` |

## Trace Format

The `trace` array contains all conversation events in chronological order. Each entry has a `role` field that determines its type.

### Message entries (role = system/user/assistant)

```json
{
  "role": "system",
  "content": "As an expert problem solver solve step by step the following mathematical questions.",
  "timestamp": "2026-02-19 17:14:30"
}
```

```json
{
  "role": "user",
  "content": "how many stickers does Leo have now?",
  "timestamp": "2026-02-19 17:14:30",
  "cost_usd": 0.0
}
```

```json
{
  "role": "assistant",
  "content": "I can't determine that from your message alone...",
  "timestamp": "2026-02-19 17:14:33",
  "cost_usd": 0.0007
}
```

- `system`: One per conversation, always first. Contains task-specific instructions.
- `user`: User simulator messages. Each reveals one "shard" (piece of the problem specification). `cost_usd` is the user model API cost.
- `assistant`: Model under evaluation's responses. `cost_usd` is the assistant model API cost.

### Log entries (role = log)

Log entries are metadata that were not shown to the LLM. The `content` field is a dict with a `type` discriminator.

#### `hint_revealed`

Logged after each user message. Indicates which shard of the problem was just revealed.

```json
{
  "role": "log",
  "content": {
    "type": "hint_revealed",
    "hint_id": 1
  }
}
```

`hint_id` is 1-indexed, matching the `shard_id` in our data files.

#### `system-verification`

Logged after each assistant message. The system agent classifies the assistant's response type.

```json
{
  "role": "log",
  "content": {
    "type": "system-verification",
    "response": {
      "response_type": "answer_attempt"
    }
  }
}
```

Possible `response_type` values:
- `answer_attempt` -- assistant is providing a final answer
- `clarification` -- assistant is asking for more information
- `discussion` -- assistant is discussing/reasoning but not answering
- `refuse` -- assistant refuses to answer (insufficient info)
- `hedge` -- assistant gives a tentative/hedged response
- `interrogation` -- assistant asks probing questions

#### `answer-evaluation`

Logged after the final assistant turn. Contains the extracted answer and evaluation result.

```json
{
  "role": "log",
  "content": {
    "type": "answer-evaluation",
    "exact_answer": "150",
    "is_correct": null,
    "score": 0.0,
    "evaluation_return": {
      "score": 0.0
    }
  }
}
```

- `exact_answer`: The answer extracted from the assistant's response (string). Empty string means no answer was extracted.
- `score`: 0.0 or 1.0. This is the authoritative correctness signal.
- `evaluation_return`: Task-specific evaluation details.

## Typical Trace Structure

A conversation typically follows this pattern:

```
[0]  system          Task instructions
[1]  user            Shard 1 (partial problem)
[2]  log:hint        hint_id=1
[3]  assistant       Response to shard 1
[4]  log:verify      response_type (e.g., "clarification")
[5]  user            Shard 2
[6]  log:hint        hint_id=2
[7]  assistant       Response to shards 1+2
[8]  log:verify      response_type
...
[N-2] assistant      Final response
[N-1] log:verify     response_type (hopefully "answer_attempt")
[N]  log:eval        answer-evaluation with score
```

The number of turns varies. The simulation continues until either:
- All shards are revealed and the assistant attempts an answer
- A maximum turn limit is reached (typically 20 turns)

## Quick Loading Example

```python
import json
from collections import defaultdict

# Load all conversations for a model+task
convs = []
with open("~/l3_dir/laban_lic_logs_math_sharded/lazy/lazy_math_t-gpt-5.2.jsonl") as f:
    for line in f:
        if line.strip():
            convs.append(json.loads(line))

# Group by question (10 per question)
by_question = defaultdict(list)
for c in convs:
    by_question[c["task_id"]].append(c)

# Check correctness
for task_id, runs in by_question.items():
    correct = sum(1 for r in runs if r.get("score", 0) == 1.0)
    print(f"{task_id}: {correct}/10 correct")

# Extract user messages from a conversation
def get_user_messages(conv):
    return [e["content"] for e in conv["trace"] if e["role"] == "user"]

# Extract assistant messages
def get_assistant_messages(conv):
    return [e["content"] for e in conv["trace"] if e["role"] == "assistant"]

# Check if last turn was an answer attempt
def was_answer_attempt(conv):
    for entry in reversed(conv["trace"]):
        if entry.get("role") == "log":
            c = entry.get("content", {})
            if isinstance(c, dict) and c.get("type") == "system-verification":
                return c["response"]["response_type"] == "answer_attempt"
    return False

# Get extracted answer
def get_extracted_answer(conv):
    for entry in reversed(conv["trace"]):
        if entry.get("role") == "log":
            c = entry.get("content", {})
            if isinstance(c, dict) and c.get("type") == "answer-evaluation":
                return c.get("exact_answer", "")
    return ""
```

## False Negative Identification

Not all incorrect conversations represent genuine assistant failures. Some are caused by the user simulator failing to convey all necessary information. We have tooling to distinguish these.

### Two checks per incorrect conversation

1. **User simulator sufficiency (LLM check)**: An LLM judge compares the union of all user simulator messages against the original single-turn problem specification (from `data/question_id_to_full_spec_qa.json`). If critical information is missing or distorted, it's a **false negative** (user sim's fault).

2. **Answer extraction (programmatic check)**: Was the last assistant turn classified as `answer_attempt`? If not (e.g., `clarification`, `refuse`), no answer was extracted, so the conversation is marked incorrect by default regardless of whether the assistant was on the right track.

### Sufficiency prompt

The prompt (`USER_SIM_SUFFICIENCY_PROMPT` in `src/ctx_editor/identify_false_negatives.py`) tells the judge to evaluate the **union** of all user messages -- information split across turns is expected by design, so late arrival is not flagged. Only truly absent or semantically distorted details count as insufficient.

### Terminology

- **True negative**: Incorrect AND user sim messages were sufficient. The assistant genuinely failed.
- **False negative**: Incorrect AND user sim messages were insufficient. The assistant never had a fair chance.
- **Adjusted accuracy**: `correct / (total - false_negatives)`. Removes user-sim-induced errors from the denominator.

### Existing analysis results

For gpt-5.2, we ran false negative analysis across all 10 conversations for all ~415 questions. Results are in `outputs/lic_false_negative_analysis/`:

| File | Description |
|---|---|
| `user_sim_sufficiency.json` | `task_id -> conv_id -> bool` (True = sufficient = true negative if incorrect) |
| `answer_extracted.json` | `task_id -> conv_id -> bool` (True = non-empty answer extracted) |
| `hard_problems.json` | Per task, questions sorted by true-negative count descending |
| `adjusted_accuracy.json` | Per-task and overall corrected accuracy |
| `detailed_results.json` | Full LLM responses with costs |

### Running your own analysis

```python
# Using the standalone scripts (no Hydra needed)

# 1. Run false negative analysis on LiC logs
python scripts/lic_false_negative_analysis_full.py

# 2. Or use the module directly for ctx_editor traces
python -m ctx_editor.identify_false_negatives outputs/2026-03-26/12-45-49 --model gpt-5 --concurrency 20 -v
```

The standalone script (`scripts/lic_false_negative_analysis_full.py`) handles the LiC log format directly. It:
- Loads JSONL files from `~/l3_dir`
- Maps LiC task IDs to our `sharded-*` format for QA metadata lookup
- Uses Azure OpenAI multi-endpoint load balancing (hardcoded in the script)
- Reuses prior results automatically (checks `outputs/lic_false_negative_analysis/detailed_results.json`)

The module (`ctx_editor.identify_false_negatives`) works on ctx_editor output directories (traces/ or results.json format).

### Using results for problem selection

The `hard_problems.json` file ranks questions by true-negative count. This was used to build the htn20_52 subset (top 20 per task). Example:

```python
import json

with open("outputs/lic_false_negative_analysis/hard_problems.json") as f:
    hard = json.load(f)

# Get the 10 hardest math problems
for item in hard["math"][:10]:
    print(f'{item["task_id"]}: TN={item["true_negatives"]}/10, '
          f'FN={item["false_negatives"]}, OK={item["correct"]}')
```

## Question Counts per Task

| Task | Questions | Convs per question | Total conversations |
|---|---|---|---|
| Math | ~103 | 10 | ~1030 |
| Code | ~100 | 10 | ~1000 |
| Database | ~107 | 10 | ~1070 |
| Actions | ~105 | 10 | ~1050 |

Exact counts vary slightly by model (some models may have fewer questions if runs were interrupted).
