# Concat Baseline — Single-Turn Upper Bound

## What It Is

The concat baseline evaluates the assistant model in a single turn by concatenating all
problem shards into one user message. No multi-turn simulation, no user agent — just:

```
system: {task system prompt}
user:   {all shards concatenated via task.populate_concat_prompt()}
```

**Important distinction**: This is the **Concat** setting from LiC, NOT the STQ (Single-Turn
Question, a.k.a. "Full") setting. The difference:

- **STQ / Full** (`full_spec_q`): The original, naturally-written single-turn question
- **Concat**: The LLM-generated shards concatenated back together as bullet points

LiC's sharding process uses an LLM to segment the STQ into shards, then rewrites each shard.
Concatenating these shards back is *similar* to the original question (LiC verifies Concat
performance is within 90% of STQ), but not identical — the phrasing is different and the
information is presented as a bulleted list rather than flowing prose.

The Concat baseline is the appropriate upper bound for our multi-turn experiments because
it uses the same shard content that the user agent reveals turn by turn. The gap between
Concat and our multi-turn results isolates the degradation caused by incremental disclosure.

## How to Run

```bash
# All three tasks (math, code, actions)
python scripts/run_concat_baseline.py --tasks math code actions

# Single task with custom settings
python scripts/run_concat_baseline.py \
    --tasks math \
    --model gpt-5-mini \
    --reasoning-effort medium \
    --temperature 1.0 \
    --max-tokens 10000 \
    --max-concurrent 10 \
    --data-dir data \
    --output-dir outputs/concat_baseline

# Different model
python scripts/run_concat_baseline.py --tasks code --model gpt-4o --reasoning-effort none
```

## Arguments

| Arg | Default | Description |
|-----|---------|-------------|
| `--tasks` | math code actions | Which tasks to run |
| `--model` | gpt-5-mini | Assistant model |
| `--temperature` | 1.0 | Sampling temperature |
| `--timeout` | 60 | API timeout (seconds) |
| `--reasoning-effort` | medium | Reasoning effort for reasoning models |
| `--max-tokens` | 10000 | Max response tokens |
| `--max-concurrent` | 10 | Concurrent API calls |
| `--data-dir` | data | Directory containing dev_{task}_subset.json |
| `--output-dir` | outputs/concat_baseline | Where to save results |

## Output

Results saved as `{output-dir}/concat_baseline_{task}.json` with per-sample details
including response preview, extracted answer, and evaluation result.

## Baseline Results (gpt-5-mini, medium reasoning, 2026-03-14)

| Task | Samples | Correct | Accuracy |
|------|---------|---------|----------|
| math | 23 | 15 | **65.2%** |
| code | 25 | 21 | **84.0%** |
| actions | 25 | 15 | **60.0%** |

## How It Uses Task Infrastructure

The script reuses the existing LiC task classes:
- `TaskMath.populate_concat_prompt()` — formats shards as bulleted list in math prompt template
- `TaskCode.populate_concat_prompt()` — handles both LCB and HumanEval formats
- `TaskActions.populate_concat_prompt()` — formats shards in actions prompt template
- Each task's `evaluator_function()` is used as-is for scoring
- For code: `task.extract_answer()` extracts Python functions from the response
- For actions: raw response is passed to the AST checker

The system prompt is the same one used in multi-turn simulations (`task.generate_system_prompt()`).
