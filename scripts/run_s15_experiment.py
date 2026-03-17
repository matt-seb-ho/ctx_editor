#!/usr/bin/env python3
"""S1.5 experiment: Always reset context using S1's pre-computed analysis.

Takes S1 output traces (which contain conversation_analysis logs), builds
compacted context (like S2 does on reset), and replays the final assistant
turn on this clean context. Tests whether removing bad context helps
beyond what S1's appended analysis already provides.

Usage:
    python scripts/run_s15_experiment.py \
        --s1-dir outputs/2026-03-16/20-08-42 \
        --task math \
        --model gpt-5-mini \
        --label S15_nomem_math
"""

import argparse
import asyncio
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(".env")

from ctx_editor.models import get_model_client
from ctx_editor.utils.logging import setup_logging, get_logger


logger = get_logger("s15_experiment")


def load_s1_traces(s1_dir: str) -> list[dict]:
    """Load all trace files from an S1 output directory."""
    traces_dir = Path(s1_dir) / "traces"
    traces = []
    for trace_file in sorted(traces_dir.rglob("*.json")):
        with open(trace_file) as f:
            traces.append(json.load(f))
    return traces


def extract_analysis(trace_data: dict) -> dict | None:
    """Extract conversation_analysis from trace logs."""
    logs = trace_data.get("trace", {}).get("logs", [])
    for log in reversed(logs):
        if log.get("type") == "conversation_analysis":
            return log["data"]
    return None


def get_system_message(trace_data: dict) -> str:
    """Get the system message from trace."""
    messages = trace_data.get("trace", {}).get("messages", [])
    for msg in messages:
        if msg.get("role") == "system":
            return msg.get("content", "")
    return ""


def get_last_user_message(trace_data: dict) -> str:
    """Get the last user message from trace."""
    messages = trace_data.get("trace", {}).get("messages", [])
    for msg in reversed(messages):
        if msg.get("role") == "user" and msg.get("visible", True):
            return msg.get("content", "")
    return ""


def build_compacted_messages(
    system_message: str,
    analysis: dict,
    last_user_message: str,
) -> list[dict]:
    """Build compacted context from analysis, like S2 does on reset."""
    messages = []

    # System message
    if system_message:
        messages.append({"role": "system", "content": system_message})

    # Compacted conversation: task spec + aligned
    task_spec = analysis.get("user_intent", "")
    aligned = analysis.get("aligned", "")

    compact_parts = [
        "The conversation history has been compacted. Below is a summary of the "
        "user's full specification and the work completed so far that is consistent "
        "with it.",
        f"# User Task Specification (So Far)\n{task_spec}",
    ]
    if aligned:
        compact_parts.append(f"# What Looks Right So Far\n{aligned}")

    messages.append({"role": "user", "content": "\n\n".join(compact_parts)})

    # Context edit notes (issues) as system injection, like S2 does
    issues = analysis.get("issues", "")
    if issues and issues.strip().lower() != "none":
        notes = f"\n\n<context_edit_notes>\n{issues}\n</context_edit_notes>"
        messages[0]["content"] += notes

    # Last user message
    if last_user_message:
        messages.append({"role": "assistant", "content": "I'll work on this now based on the updated specification."})
        messages.append({"role": "user", "content": last_user_message})

    return messages


async def run_experiment(
    s1_dir: str,
    task_filter: str,
    model: str,
    label: str,
    max_concurrent: int = 8,
):
    """Run S1.5 experiment on S1 traces."""
    # Load traces
    traces = load_s1_traces(s1_dir)
    if task_filter:
        traces = [t for t in traces if t.get("task_name") == task_filter]

    logger.info(f"Loaded {len(traces)} traces from {s1_dir}")

    # Setup output
    timestamp = datetime.now().strftime("%Y-%m-%d/%H-%M-%S")
    output_dir = Path(f"outputs/{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)
    traces_out_dir = output_dir / "traces" / task_filter / "s15"
    traces_out_dir.mkdir(parents=True, exist_ok=True)

    setup_logging(str(output_dir), level=20)
    logger.info(f"S1.5 experiment: {label}")
    logger.info(f"Output directory: {output_dir}")

    model_client = get_model_client(model)
    semaphore = asyncio.Semaphore(max_concurrent)

    # Load task evaluators
    evaluators = {}
    if task_filter == "math":
        from lic.tasks.math.task_math_v2 import TaskMathV2
        evaluators["math"] = TaskMathV2()
    elif task_filter == "code":
        from lic.tasks.code.task_code_v2 import TaskCodeV2
        evaluators["code"] = TaskCodeV2()
    elif task_filter == "database":
        from lic.tasks.database.task_database_v2 import TaskDatabaseV2
        evaluators["database"] = TaskDatabaseV2()
    elif task_filter == "actions":
        from lic.tasks.actions.task_actions import TaskActions
        evaluators["actions"] = TaskActions()

    results = []

    async def process_one(trace_data: dict) -> dict:
        async with semaphore:
            sample_id = trace_data.get("sample_id", "unknown")
            task_name = trace_data.get("task_name", "unknown")

            # Check if trace was skipped (user-sim-induced)
            metadata = trace_data.get("metadata", {})
            if metadata.get("skipped"):
                return {
                    "sample_id": sample_id,
                    "task_name": task_name,
                    "is_correct": False,
                    "score": 0.0,
                    "skipped": True,
                    "skip_reason": metadata.get("skip_reason", "unknown"),
                }

            # Extract analysis
            analysis = extract_analysis(trace_data)
            if not analysis:
                logger.warning(f"[{sample_id}] No analysis found, skipping")
                return {
                    "sample_id": sample_id,
                    "task_name": task_name,
                    "is_correct": False,
                    "score": 0.0,
                    "error": "no_analysis",
                }

            # Build compacted context
            system_msg = get_system_message(trace_data)
            last_user_msg = get_last_user_message(trace_data)
            messages = build_compacted_messages(system_msg, analysis, last_user_msg)

            # Generate assistant response
            try:
                response = await model_client.generate(
                    messages=messages,
                    model=model,
                    max_tokens=4000,
                    temperature=1.0,
                )
                assistant_response = response.content
            except Exception as e:
                logger.error(f"[{sample_id}] Generation failed: {e}")
                return {
                    "sample_id": sample_id,
                    "task_name": task_name,
                    "is_correct": False,
                    "score": 0.0,
                    "error": str(e),
                }

            # Evaluate
            evaluator = evaluators.get(task_name)
            if evaluator:
                ground_truth = trace_data.get("metadata", {}).get("ground_truth_a", "")
                if not ground_truth:
                    # Try to get from the original trace evaluation
                    for log in trace_data.get("trace", {}).get("logs", []):
                        if log.get("type") == "answer_evaluation":
                            ground_truth = log.get("data", {}).get("ground_truth", "")
                            break

                extracted = evaluator.extract_answer(assistant_response)
                is_correct = evaluator.evaluate(extracted, ground_truth) if extracted and ground_truth else False
                score = 1.0 if is_correct else 0.0
            else:
                is_correct = False
                score = 0.0
                extracted = None

            # Save trace
            result = {
                "sample_id": sample_id,
                "task_name": task_name,
                "is_correct": is_correct,
                "score": score,
                "extracted_answer": str(extracted) if extracted else "",
                "assistant_response": assistant_response,
                "analysis_used": {
                    "user_intent": analysis.get("user_intent", "")[:500],
                    "aligned": analysis.get("aligned", "")[:500],
                    "issues": analysis.get("issues", "")[:500],
                    "needs_edit": analysis.get("needs_edit"),
                },
                "messages_sent": messages,
            }

            trace_file = traces_out_dir / f"{sample_id.replace('/', '_')}.json"
            with open(trace_file, "w") as f:
                json.dump(result, f, indent=2)

            tag = "correct" if is_correct else "WRONG"
            logger.info(f"  [{sample_id}] {tag} (extracted: {str(extracted)[:80]})")

            return result

    # Run all
    tasks = [process_one(t) for t in traces]
    results = await asyncio.gather(*tasks)

    # Compute metrics
    valid = [r for r in results if not r.get("skipped") and not r.get("error")]
    skipped = [r for r in results if r.get("skipped")]
    errors = [r for r in results if r.get("error")]
    correct = sum(1 for r in valid if r["is_correct"])
    total = len(valid)

    accuracy = correct / total if total > 0 else 0
    skip_note = f" ({len(skipped)} skipped)" if skipped else ""
    error_note = f" ({len(errors)} errors)" if errors else ""
    logger.info(f"Results: {correct}/{total} correct ({accuracy:.2%}){skip_note}{error_note}")

    # Save summary
    summary = {
        "label": label,
        "s1_source": s1_dir,
        "task": task_filter,
        "model": model,
        "total": total,
        "correct": correct,
        "accuracy": accuracy,
        "skipped": len(skipped),
        "errors": len(errors),
        "timestamp": datetime.now().isoformat(),
    }
    with open(output_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n{'='*60}")
    print(f"S1.5 EXPERIMENT: {label}")
    print(f"{'='*60}")
    print(f"Source: {s1_dir}")
    print(f"Results: {correct}/{total} ({accuracy:.2%}){skip_note}{error_note}")
    print(f"Output: {output_dir}")
    print(f"{'='*60}\n")

    return summary


def main():
    parser = argparse.ArgumentParser(description="S1.5 experiment: always-reset with S1 analysis")
    parser.add_argument("--s1-dir", required=True, help="S1 output directory with traces")
    parser.add_argument("--task", required=True, help="Task filter (math, code, database, actions)")
    parser.add_argument("--model", default="gpt-5-mini", help="Model for assistant generation")
    parser.add_argument("--label", default="s15", help="Experiment label")
    parser.add_argument("--max-concurrent", type=int, default=8)

    args = parser.parse_args()
    asyncio.run(run_experiment(
        s1_dir=args.s1_dir,
        task_filter=args.task,
        model=args.model,
        label=args.label,
        max_concurrent=args.max_concurrent,
    ))


if __name__ == "__main__":
    main()
