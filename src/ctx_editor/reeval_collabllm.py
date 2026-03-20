#!/usr/bin/env python3
"""Re-evaluate CollabLLM traces with a different extraction/eval model.

Loads saved traces, re-runs extraction + accuracy judging, and saves updated results.
Avoids re-running the expensive conversation simulation.

Usage:
    python -m ctx_editor.reeval_collabllm \
        --trace_dir outputs/2026-03-18/22-07-15 \
        --eval_model gpt-5 \
        --eval_method pass_rate
"""

import argparse
import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from omegaconf import OmegaConf
from tqdm import tqdm

from ctx_editor.data.collabllm_loader import COLLABLLM_DATASETS, load_collabllm_dataset
from ctx_editor.evaluation.collabllm_metrics import (
    CollabLLMEvaluator,
    count_assistant_tokens,
)
from ctx_editor.models import LoadBalancerConfig, OpenAIModelClient
from lic.paths import PROJECT_ROOT

load_dotenv(PROJECT_ROOT / ".env")
logger = logging.getLogger(__name__)


def load_traces(trace_dir: Path) -> list[dict[str, Any]]:
    """Load all trace files from a trace directory."""
    traces = []
    for trace_file in sorted(trace_dir.rglob("*.json")):
        with open(trace_file) as f:
            trace_data = json.load(f)
        traces.append({
            "path": str(trace_file),
            "sample_id": trace_file.stem,
            "trace": trace_data,
        })
    return traces


def get_messages_from_trace(trace_data: dict) -> list[dict[str, str]]:
    """Extract visible messages from a saved trace."""
    messages = []
    for msg in trace_data["trace"]["messages"]:
        if msg.get("visible", True):
            messages.append({"role": msg["role"], "content": msg["content"]})
    return messages


async def reeval(
    trace_dir: str,
    eval_model: str,
    dataset_name: str,
    eval_method: str | None = None,
    lb_config_path: str | None = None,
    max_concurrent: int = 1,
) -> dict[str, Any]:
    """Re-evaluate all traces in a directory with a new model."""
    trace_path = Path(trace_dir)
    config_path = trace_path / "config.yaml"

    # Load original config for context
    if config_path.exists():
        cfg = OmegaConf.load(config_path)
        orig_dataset = cfg.get("task", {}).get("dataset_name", dataset_name)
        logger.info(f"Original experiment: {cfg.get('experiment_name', 'unknown')}")
    else:
        orig_dataset = dataset_name

    # Get dataset info for eval_method and sample metadata
    dataset_info = COLLABLLM_DATASETS[orig_dataset]
    if eval_method is None:
        eval_method = dataset_info.get("eval_method", "llm_judge")
    extract_type = dataset_info["extract_type"]

    # Load samples to get metadata (test cases, entry_point, etc.)
    samples = load_collabllm_dataset(orig_dataset)
    sample_metadata = {}
    for s in samples:
        # Key by the last part of task_id to match trace filenames
        key = s["task_id"].replace("/", "_")
        sample_metadata[key] = s

    # Setup model client with load balancer
    load_balancer_config = None
    if lb_config_path:
        lb_dict = OmegaConf.to_container(
            OmegaConf.load(lb_config_path), resolve=True
        )
        load_balancer_config = LoadBalancerConfig.from_dict(lb_dict)
    model_client = OpenAIModelClient(load_balancer_config=load_balancer_config)

    # Setup evaluator
    evaluator = CollabLLMEvaluator(
        model=eval_model,
        extract_type=extract_type,
        eval_method=eval_method,
    )

    # Load traces
    traces = load_traces(trace_path / "traces")
    logger.info(f"Loaded {len(traces)} traces from {trace_path}")
    logger.info(f"Re-evaluating with model={eval_model}, method={eval_method}")

    # Prepare evaluation tasks
    eval_tasks = []
    for trace_entry in traces:
        sample_id = trace_entry["sample_id"]
        messages = get_messages_from_trace(trace_entry["trace"])
        num_resets = trace_entry["trace"].get("trace", {}).get("num_resets", 0)

        meta = None
        prompt = ""
        completion = ""
        for key, s in sample_metadata.items():
            if sample_id in key or key in sample_id:
                meta = s.get("single_turn_metadata", {})
                prompt = s.get("single_turn_prompt", "")
                completion = s.get("single_turn_completion", "")
                break

        if meta is None:
            logger.warning(f"No metadata found for {sample_id}, skipping")
            continue

        eval_tasks.append({
            "sample_id": sample_id,
            "messages": messages,
            "meta": meta,
            "prompt": prompt,
            "completion": completion,
            "num_resets": num_resets,
        })

    # Re-evaluate with concurrency
    sem = asyncio.Semaphore(max_concurrent)
    results = [None] * len(eval_tasks)
    pbar = tqdm(total=len(eval_tasks), desc=f"Re-evaluating with {eval_model}")

    async def eval_one(idx: int, task: dict):
        async with sem:
            sample_id = task["sample_id"]
            try:
                eval_result = await evaluator.evaluate(
                    messages=task["messages"],
                    single_turn_prompt=task["prompt"],
                    single_turn_completion=task["completion"],
                    model_client=model_client,
                    metadata=task["meta"],
                )
                results[idx] = {
                    "sample_id": sample_id,
                    "accuracy": eval_result.accuracy,
                    "interactivity": eval_result.interactivity,
                    "assistant_tokens": eval_result.assistant_tokens,
                    "extracted_answer": eval_result.extracted_answer,
                    "is_correct": eval_result.accuracy == 1.0,
                    "eval_cost_usd": eval_result.eval_cost_usd,
                    "num_resets": task["num_resets"],
                }
                status = "PASS" if eval_result.accuracy == 1.0 else "FAIL"
                pbar.set_postfix(last=f"{sample_id}: {status}")
            except Exception as e:
                logger.error(f"Error re-evaluating {sample_id}: {e}")
                results[idx] = {
                    "sample_id": sample_id,
                    "accuracy": -1.0,
                    "error": str(e),
                    "is_correct": False,
                    "num_resets": task["num_resets"],
                }
            pbar.update(1)

    await asyncio.gather(*[eval_one(i, t) for i, t in enumerate(eval_tasks)])
    pbar.close()
    results = [r for r in results if r is not None]

    # Compute metrics
    valid = [r for r in results if r.get("accuracy", -1) >= 0]
    correct = sum(1 for r in valid if r["is_correct"])
    total = len(valid)
    avg_accuracy = sum(r["accuracy"] for r in valid) / total if total else 0
    total_cost = sum(r.get("eval_cost_usd", 0) for r in results)

    metrics = {
        "original_trace_dir": str(trace_path),
        "eval_model": eval_model,
        "eval_method": eval_method,
        "total_samples": total,
        "correct": correct,
        "accuracy": avg_accuracy,
        "total_eval_cost_usd": total_cost,
    }

    # Save results
    method_suffix = f"_{eval_method}" if eval_method else ""
    output_dir = trace_path / f"reeval_{eval_model.replace('/', '_')}{method_suffix}"
    output_dir.mkdir(exist_ok=True)

    with open(output_dir / "results.json", "w") as f:
        json.dump(results, f, indent=2)
    with open(output_dir / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"\n{'='*60}")
    print(f"RE-EVALUATION COMPLETE")
    print(f"{'='*60}")
    print(f"Model: {eval_model}")
    print(f"Method: {eval_method}")
    print(f"Accuracy: {avg_accuracy:.1%} ({correct}/{total})")
    print(f"Eval cost: ${total_cost:.4f}")
    print(f"Results saved to: {output_dir}")

    return metrics


def main():
    parser = argparse.ArgumentParser(description="Re-evaluate CollabLLM traces")
    parser.add_argument("--trace_dir", required=True, help="Path to trace directory")
    parser.add_argument("--eval_model", default="gpt-5", help="Model for extraction/eval")
    parser.add_argument("--dataset_name", default="bigcodebench", help="Dataset name")
    parser.add_argument("--eval_method", default=None, help="Eval method (pass_rate or llm_judge)")
    parser.add_argument(
        "--lb_config",
        default="src/ctx_editor/config/load_balancer/multi_endpoint_full.yaml",
        help="Load balancer config path",
    )
    parser.add_argument("--max_concurrent", type=int, default=1, help="Max concurrent evaluations")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    asyncio.run(reeval(
        trace_dir=args.trace_dir,
        eval_model=args.eval_model,
        dataset_name=args.dataset_name,
        eval_method=args.eval_method,
        lb_config_path=args.lb_config,
        max_concurrent=args.max_concurrent,
    ))


if __name__ == "__main__":
    main()
