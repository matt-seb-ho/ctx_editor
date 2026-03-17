#!/usr/bin/env python3
"""S1.5 / S3 experiment: Reset context using S1's pre-computed analysis.

S1.5: Programmatic compaction — templates analysis fields into compacted context.
S3:   LLM compaction — an LLM reads the full conversation + analysis and writes
      optimized compacted context.

Both modes take S1 output traces (which contain conversation_analysis logs),
build compacted context, and replay the final assistant turn.

Usage:
    # S1.5 (programmatic compaction)
    python scripts/run_s15_experiment.py \
        --s1-dir outputs/2026-03-16/20-08-42 \
        --task math --model gpt-5-mini --label S15_nomem_math

    # S3 (LLM compaction)
    python scripts/run_s15_experiment.py --mode s3 \
        --s1-dir outputs/2026-03-17/03-02-33 \
        --task math --model gpt-5-mini --label S3_single_math
"""

import argparse
import asyncio
import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(".env")

from ctx_editor.models import get_model_client
from ctx_editor.utils.logging import setup_logging, get_logger


logger = get_logger("s15_experiment")

_COMPACTION_PROMPT_PATH = (
    Path(__file__).parent.parent / "src" / "ctx_editor" / "strategies" / "prompts" / "context_compaction.txt"
)


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


def sanitize_analysis(analysis: dict) -> dict:
    """Remove clarification-seeking and over-specification patterns from analysis.

    Targets the three anti-patterns identified in memory error analysis:
    1. Clarification-seeking leakage ("ask the user", "if unclear", "open questions")
    2. Invitation to not answer ("do not assume answers", "before producing")
    3. Over-hedging ("if anything above is unclear")

    Returns a new dict with sanitized user_intent and issues.
    """
    import re

    # Patterns that invite clarification-seeking behavior
    CLARIFICATION_PATTERNS = [
        # Direct invitations to ask
        re.compile(
            r"[^.]*(?:ask the user|ask (?:the )?user|ask before|"
            r"clarif(?:y|ication)|if (?:anything )?(?:above )?is unclear|"
            r"open question|do not assume answer|"
            r"needed from the user|check with the user)[^.]*\.?\s*",
            re.IGNORECASE,
        ),
        # Bullet points / list items that invite clarification
        re.compile(
            r"^[ \t]*[-•*]\s*[^\n]*(?:ask the user|clarif|if unclear|"
            r"open question|needed from the user|do not assume)[^\n]*\n?",
            re.IGNORECASE | re.MULTILINE,
        ),
        # Numbered items that invite clarification
        re.compile(
            r"^[ \t]*\d+[\.\)]\s*[^\n]*(?:ask the user|clarif|if unclear|"
            r"open question|needed from the user|do not assume)[^\n]*\n?",
            re.IGNORECASE | re.MULTILINE,
        ),
        # Sections headers about open questions
        re.compile(
            r"^#+\s*(?:open question|clarification|ambiguit)[^\n]*\n(?:[^\n#]+\n)*",
            re.IGNORECASE | re.MULTILINE,
        ),
    ]

    def _sanitize_text(text: str) -> str:
        if not text:
            return text
        result = text
        for pattern in CLARIFICATION_PATTERNS:
            result = pattern.sub("", result)
        # Clean up double blank lines left by removals
        result = re.sub(r"\n{3,}", "\n\n", result)
        return result.strip()

    sanitized = dict(analysis)
    sanitized["user_intent"] = _sanitize_text(analysis.get("user_intent", ""))
    sanitized["issues"] = _sanitize_text(analysis.get("issues", ""))
    return sanitized


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


def get_conversation_string(trace_data: dict) -> str:
    """Reconstruct the full conversation as a formatted string from trace messages."""
    messages = trace_data.get("trace", {}).get("messages", [])
    parts = []
    for msg in messages:
        if not msg.get("visible", True):
            continue
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        parts.append(f"[{role}] {content}")
    return "\n\n".join(parts)


async def build_compacted_messages_s3(
    system_message: str,
    analysis: dict,
    last_user_message: str,
    conversation: str,
    model_client,
    model: str,
) -> list[dict]:
    """Build compacted context via LLM compaction (S3).

    An LLM reads the full conversation + analysis output and writes
    optimized compacted context, controlling task spec presentation.
    """
    prompt_template = _COMPACTION_PROMPT_PATH.read_text()
    prompt = prompt_template.format(
        conversation=conversation,
        analysis_user_intent=analysis.get("user_intent", ""),
        analysis_aligned=analysis.get("aligned", ""),
        analysis_issues=analysis.get("issues", ""),
    )

    response = await model_client.generate(
        messages=[{"role": "user", "content": prompt}],
        model=model,
        temperature=0.0,
        timeout=60,
    )
    compaction_output = response.content

    # Parse tagged sections
    task_spec_match = re.search(r"<task_spec>(.*?)</task_spec>", compaction_output, re.DOTALL)
    work_match = re.search(r"<work_so_far>(.*?)</work_so_far>", compaction_output, re.DOTALL)

    task_spec = task_spec_match.group(1).strip() if task_spec_match else ""
    work_so_far = work_match.group(1).strip() if work_match else ""

    if not task_spec:
        logger.warning("S3 compaction: <task_spec> tag not found, falling back to raw output")
        task_spec = compaction_output.strip()

    # Build messages in same format as S1.5
    messages = []
    if system_message:
        messages.append({"role": "system", "content": system_message})

    compact_parts = [
        "The conversation history has been compacted. Below is a summary of the "
        "user's full specification and the work completed so far that is consistent "
        "with it.",
        f"# User Task Specification (So Far)\n{task_spec}",
    ]
    if work_so_far and work_so_far.lower() != "none":
        compact_parts.append(f"# What Looks Right So Far\n{work_so_far}")

    messages.append({"role": "user", "content": "\n\n".join(compact_parts)})

    if last_user_message:
        messages.append({"role": "assistant", "content": "I'll work on this now based on the updated specification."})
        messages.append({"role": "user", "content": last_user_message})

    return messages, compaction_output


async def run_experiment(
    s1_dir: str,
    task_filter: str,
    model: str,
    label: str,
    max_concurrent: int = 8,
    sanitize: bool = False,
    mode: str = "s15",
):
    """Run S1.5 or S3 experiment on S1 traces."""
    # Load traces
    traces = load_s1_traces(s1_dir)
    if task_filter:
        traces = [t for t in traces if t.get("task_name") == task_filter]

    logger.info(f"Loaded {len(traces)} traces from {s1_dir}")

    # Setup output
    timestamp = datetime.now().strftime("%Y-%m-%d/%H-%M-%S")
    output_dir = Path(f"outputs/{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)
    traces_out_dir = output_dir / "traces" / task_filter / mode
    traces_out_dir.mkdir(parents=True, exist_ok=True)

    setup_logging(str(output_dir), level=20)
    logger.info(f"{mode.upper()} experiment: {label}")
    logger.info(f"Output directory: {output_dir}")

    model_client = get_model_client(model)
    semaphore = asyncio.Semaphore(max_concurrent)

    # Load ground truth from data files
    from ctx_editor.identify_false_negatives import load_task_metadata
    task_metadata = load_task_metadata()

    # Load task evaluator and original samples
    evaluator = None
    original_samples = {}
    if task_filter == "math":
        from lic.tasks.math.task_math_v2 import TaskMathV2
        evaluator = TaskMathV2()
    elif task_filter == "code":
        from lic.tasks.code.task_code_v2 import TaskCodeV2
        evaluator = TaskCodeV2()
    elif task_filter == "database":
        from lic.tasks.database.task_database_v2 import TaskDatabaseV2
        evaluator = TaskDatabaseV2()
    elif task_filter == "actions":
        from lic.tasks.actions.task_actions import TaskActions
        evaluator = TaskActions()

    # Load original samples from dev subset data files
    dev_data_files = {
        "math": "data/dev_math_subset.json",
        "code": "data/dev_code_subset.json",
        "database": "data/dev_database_subset.json",
        "actions": "data/dev_actions_subset.json",
    }
    data_file = dev_data_files.get(task_filter)
    if data_file and Path(data_file).exists():
        with open(data_file) as f:
            for sample in json.load(f):
                original_samples[sample.get("task_id", "")] = sample
        logger.info(f"Loaded {len(original_samples)} original samples from {data_file}")

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

            # Optionally sanitize analysis to remove clarification-seeking patterns
            if sanitize:
                analysis = sanitize_analysis(analysis)

            # Build compacted context
            system_msg = get_system_message(trace_data)
            last_user_msg = get_last_user_message(trace_data)
            compaction_output = None

            if mode == "s3":
                conversation = get_conversation_string(trace_data)
                messages, compaction_output = await build_compacted_messages_s3(
                    system_msg, analysis, last_user_msg, conversation, model_client, model,
                )
            else:
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
            if evaluator:
                orig_sample = original_samples.get(sample_id, {})
                if task_name == "actions":
                    # Actions: evaluator_function takes raw response + sample
                    if orig_sample:
                        eval_result = evaluator.evaluator_function(assistant_response, orig_sample)
                        is_correct = eval_result.get("is_correct", False)
                    else:
                        is_correct = False
                    extracted = assistant_response[:200]
                else:
                    # Math/code/database: extract_answer + evaluator_function
                    extracted = evaluator.extract_answer(assistant_response)
                    if extracted and orig_sample:
                        eval_result = evaluator.evaluator_function(extracted, orig_sample)
                        if isinstance(eval_result, bool):
                            is_correct = eval_result
                        elif isinstance(eval_result, dict):
                            is_correct = eval_result.get("is_correct", eval_result.get("score", 0) >= 1.0)
                        else:
                            is_correct = False
                    else:
                        is_correct = False
                score = 1.0 if is_correct else 0.0
            else:
                is_correct = False
                score = 0.0
                extracted = None

            # Save trace
            result = {
                "sample_id": sample_id,
                "task_name": task_name,
                "mode": mode,
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
            if compaction_output:
                result["compaction_output"] = compaction_output

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
        "mode": mode,
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
    print(f"{mode.upper()} EXPERIMENT: {label}")
    print(f"{'='*60}")
    print(f"Source: {s1_dir}")
    print(f"Results: {correct}/{total} ({accuracy:.2%}){skip_note}{error_note}")
    print(f"Output: {output_dir}")
    print(f"{'='*60}\n")

    return summary


def main():
    parser = argparse.ArgumentParser(description="S1.5/S3 experiment: reset context with S1 analysis")
    parser.add_argument("--s1-dir", required=True, help="S1 output directory with traces")
    parser.add_argument("--task", required=True, help="Task filter (math, code, database, actions)")
    parser.add_argument("--model", default="gpt-5-mini", help="Model for assistant generation")
    parser.add_argument("--label", default="s15", help="Experiment label")
    parser.add_argument("--max-concurrent", type=int, default=8)
    parser.add_argument(
        "--mode", choices=["s15", "s3"], default="s15",
        help="Compaction mode: s15 (programmatic) or s3 (LLM-based)",
    )
    parser.add_argument(
        "--sanitize", action="store_true",
        help="Sanitize analysis to remove clarification-seeking patterns before context building",
    )

    args = parser.parse_args()
    asyncio.run(run_experiment(
        s1_dir=args.s1_dir,
        task_filter=args.task,
        model=args.model,
        label=args.label,
        max_concurrent=args.max_concurrent,
        sanitize=args.sanitize,
        mode=args.mode,
    ))


if __name__ == "__main__":
    main()
