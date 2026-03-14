#!/usr/bin/env python
"""Concat baseline: single-turn upper bound evaluation.

Concatenates all shards into a single user message, sends to the assistant model
in one turn, extracts the answer, and evaluates. No simulation, no user agent.

This represents the theoretical ceiling for multi-turn strategies — if the model
can solve the problem when given all information at once, then the multi-turn
performance gap is due to the sharded disclosure process.

Usage:
    python scripts/run_concat_baseline.py --tasks math code actions
    python scripts/run_concat_baseline.py --tasks math --model gpt-5-mini --data-dir data
    python scripts/run_concat_baseline.py --tasks code --reasoning-effort medium
"""

import argparse
import asyncio
import json
import re
import sys
from pathlib import Path

# Load .env and add src to path
from dotenv import load_dotenv
load_dotenv()
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ctx_editor.models.openai_model import OpenAIModelClient
from lic.tasks.math.task_math import TaskMath
from lic.tasks.code.task_code import TaskCode
from lic.tasks.actions.task_actions import TaskActions


TASK_CLASSES = {
    "math": TaskMath,
    "code": TaskCode,
    "actions": TaskActions,
}


async def run_single(
    task,
    sample: dict,
    model_client: OpenAIModelClient,
    model: str,
    temperature: float,
    timeout: int,
    reasoning_effort: str | None,
    max_tokens: int,
) -> dict:
    """Run a single concat evaluation."""
    # Build messages: system prompt + concat of all shards
    system_prompt = task.generate_system_prompt(sample)
    user_prompt = task.populate_concat_prompt(sample)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    # Generate response
    response = await model_client.generate(
        messages=messages,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
        reasoning_effort=reasoning_effort,
    )

    # Extract answer
    raw_response = response.content
    task_name = task.get_task_name()

    if task_name == "code":
        extracted = task.extract_answer(raw_response)
    elif task_name == "actions":
        # Actions uses full response for extraction
        extracted = raw_response
    else:
        # Math — extract from the raw response using the system agent's approach
        # For concat baseline, we take the last number from the response
        extracted = raw_response

    # Evaluate
    eval_result = task.evaluator_function(extracted, sample)

    if isinstance(eval_result, dict):
        is_correct = eval_result.get("is_correct", eval_result.get("score", 0) == 1.0)
        score = eval_result.get("score", 1.0 if is_correct else 0.0)
    elif isinstance(eval_result, tuple):
        is_correct, _ = eval_result
        score = 1.0 if is_correct else 0.0
    else:
        is_correct = bool(eval_result)
        score = 1.0 if is_correct else 0.0

    return {
        "task_id": sample.get("task_id", "unknown"),
        "task": task_name,
        "is_correct": is_correct,
        "score": score,
        "cost_usd": response.total_usd,
        "response_preview": raw_response[:200],
        "extracted_preview": str(extracted)[:200] if extracted else "(empty)",
    }


async def run_task(
    task_name: str,
    data_file: str,
    model_client: OpenAIModelClient,
    model: str,
    temperature: float,
    timeout: int,
    reasoning_effort: str | None,
    max_tokens: int,
    max_concurrent: int,
    output_dir: Path,
) -> dict:
    """Run concat baseline for a single task."""
    task = TASK_CLASSES[task_name]()

    # Load data
    with open(data_file) as f:
        samples = json.load(f)

    # Filter to task type
    samples = [s for s in samples if s.get("task") == task_name]
    print(f"\n{'='*60}")
    print(f"Task: {task_name} ({len(samples)} samples)")
    print(f"{'='*60}")

    # Run with semaphore for concurrency control
    sem = asyncio.Semaphore(max_concurrent)
    results = []

    async def run_with_sem(sample):
        async with sem:
            try:
                return await run_single(
                    task, sample, model_client, model,
                    temperature, timeout, reasoning_effort, max_tokens,
                )
            except Exception as e:
                print(f"  ERROR {sample.get('task_id')}: {e}")
                return {
                    "task_id": sample.get("task_id", "unknown"),
                    "task": task_name,
                    "is_correct": False,
                    "score": 0.0,
                    "error": str(e),
                }

    tasks = [run_with_sem(s) for s in samples]
    results = await asyncio.gather(*tasks)

    # Summary
    correct = sum(1 for r in results if r["is_correct"])
    total = len(results)
    errors = sum(1 for r in results if "error" in r)
    accuracy = correct / total if total > 0 else 0

    print(f"\nResults: {correct}/{total} ({accuracy:.1%})")
    if errors:
        print(f"  ({errors} errors)")

    # Save results
    output_file = output_dir / f"concat_baseline_{task_name}.json"
    output = {
        "task": task_name,
        "model": model,
        "temperature": temperature,
        "reasoning_effort": reasoning_effort,
        "total": total,
        "correct": correct,
        "accuracy": accuracy,
        "errors": errors,
        "results": results,
    }
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)
    print(f"  Saved to {output_file}")

    return {"task": task_name, "correct": correct, "total": total, "accuracy": accuracy, "errors": errors}


async def main():
    parser = argparse.ArgumentParser(description="Concat baseline: single-turn upper bound")
    parser.add_argument("--tasks", nargs="+", default=["math", "code", "actions"],
                        choices=["math", "code", "actions"])
    parser.add_argument("--model", default="gpt-5-mini")
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--reasoning-effort", default="medium")
    parser.add_argument("--max-tokens", type=int, default=10000)
    parser.add_argument("--max-concurrent", type=int, default=10)
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--output-dir", default="outputs/concat_baseline")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    model_client = OpenAIModelClient()

    print(f"Concat Baseline — Single Turn Upper Bound")
    print(f"Model: {args.model} (reasoning_effort={args.reasoning_effort})")
    print(f"Tasks: {', '.join(args.tasks)}")

    summaries = []
    for task_name in args.tasks:
        data_file = f"{args.data_dir}/dev_{task_name}_subset.json"
        if not Path(data_file).exists():
            print(f"WARNING: {data_file} not found, skipping {task_name}")
            continue

        summary = await run_task(
            task_name=task_name,
            data_file=data_file,
            model_client=model_client,
            model=args.model,
            temperature=args.temperature,
            timeout=args.timeout,
            reasoning_effort=args.reasoning_effort,
            max_tokens=args.max_tokens,
            max_concurrent=args.max_concurrent,
            output_dir=output_dir,
        )
        summaries.append(summary)

    # Final summary
    print(f"\n{'='*60}")
    print("CONCAT BASELINE SUMMARY")
    print(f"{'='*60}")
    for s in summaries:
        print(f"  {s['task']:10s}: {s['correct']}/{s['total']} ({s['accuracy']:.1%})")


if __name__ == "__main__":
    asyncio.run(main())
