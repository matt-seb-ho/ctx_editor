"""Automated error analysis for incorrect baseline conversations.

Analyzes why conversations were marked incorrect by sending them through an LLM
along with the original single-turn question and ground truth answer.

Usage:
    python -m ctx_editor.error_analysis outputs/2026-01-30/04-56-38
    python -m ctx_editor.error_analysis outputs/2026-01-30/04-56-38 --output analysis.json
    python -m ctx_editor.error_analysis outputs/2026-01-30/04-56-38 --model gpt-4o
"""

import argparse
import asyncio
import json
import os
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv

from .models import get_model_client
from .paths import PROJECT_ROOT

# Load environment variables from .env file at repo root
load_dotenv(PROJECT_ROOT / ".env")


# Error categories
ERROR_CATEGORIES = {
    "strict_comparison": "Overly strict string comparison (e.g., '6.00' vs '6', equivalent fractions)",
    "unit_mismatch": "Different units - question is ambiguous about units and assistant picked different ones",
    "extraction_failure": "Answer extraction failure - assistant's actual answer was correct but system extracted wrong value",
    "clarification_ignored": "Assistant asked clarifying questions or gave multiple interpretations, one of which was correct",
    "sharding_distortion": "Sharded presentation genuinely distorted the problem meaning",
    "assistant_error": "Assistant made a genuine reasoning or calculation error",
    "other": "Other type of error (see explanation)",
}

ANALYSIS_PROMPT = """You are analyzing a conversation from an evaluation system to determine why it was marked as incorrect.

## Context
This evaluation system tests LLMs in multi-turn conversations where a problem is revealed piece-by-piece ("sharded"). The assistant must solve the problem as information is gradually revealed.

## Your Task
Analyze whether the assistant actually got the answer wrong, or if this is a false negative due to evaluation issues.

## Information Provided

### Original Single-Turn Question (complete problem)
{full_spec_q}

### Ground Truth Answer
{ground_truth_a}

### The Multi-Turn Conversation
{conversation}

### System's Extracted Answer
The evaluation system extracted this as the assistant's final answer: "{extracted_answer}"

### Final Evaluation
The system marked this as INCORRECT.

## Error Categories
Classify this error into ONE of these categories:

1. **strict_comparison**: The assistant's answer is mathematically/semantically equivalent but failed string matching (e.g., "6.00" vs "6", "$2" vs "2", "1/2" vs "0.5")

2. **unit_mismatch**: The question was ambiguous about units and the assistant used different but reasonable units (e.g., minutes vs hours, dollars vs cents)

3. **extraction_failure**: The assistant's response contains the correct answer, but the system extracted the wrong value. Look for cases where the assistant mentions multiple numbers and the wrong one was extracted.

4. **clarification_ignored**: The assistant asked clarifying questions or provided multiple possible answers for different interpretations. Check if ANY of the interpretations/answers provided would be correct.

5. **sharding_distortion**: The way the problem was split into shards genuinely changed its meaning or made it unsolvable. The full question has a clear answer but the sharded presentation led to a different valid interpretation.

6. **assistant_error**: The assistant made a genuine mistake in reasoning or calculation. This is a TRUE negative - the marking is correct.

7. **other**: None of the above categories apply. You MUST provide a detailed explanation.

## Response Format
Respond with a JSON object:
{{
    "category": "<one of the category keys above>",
    "correct_answer_present": <true if the assistant's response somewhere contains the correct answer>,
    "assistant_final_answer": "<what you believe the assistant's intended final answer was>",
    "explanation": "<required if category is 'other', otherwise optional brief note>"
}}
"""


@dataclass
class AnalysisResult:
    """Result of analyzing a single incorrect conversation."""

    sample_id: str
    task_name: str
    category: str
    correct_answer_present: bool
    extracted_answer: str
    assistant_final_answer: str
    ground_truth: str
    explanation: str = ""
    raw_response: dict[str, Any] = field(default_factory=dict)


def format_conversation(messages: list[dict]) -> str:
    """Format conversation messages for the prompt."""
    lines = []
    for msg in messages:
        role = msg.get("role", "unknown").upper()
        content = msg.get("content", "")
        lines.append(f"[{role}]\n{content}\n")
    return "\n".join(lines)


def extract_ground_truth_final(ground_truth_a: str) -> str:
    """Extract just the final answer from ground truth (after ####)."""
    if "####" in ground_truth_a:
        return ground_truth_a.split("####")[1].strip()
    return ground_truth_a.strip()


async def analyze_conversation(
    sample: dict[str, Any],
    model_client: Any,
    model: str,
) -> AnalysisResult:
    """Analyze a single incorrect conversation."""

    sample_id = sample.get("sample_id", "unknown")
    task_name = sample.get("task_name", "unknown")

    # Get conversation from trace
    trace = sample.get("trace", {})
    messages = trace.get("messages", [])

    # Get metadata
    metadata = sample.get("metadata", {})
    full_spec_q = metadata.get("full_spec_q", "")
    ground_truth_a = metadata.get("ground_truth_a", "")

    # Get extracted answer - try multiple locations
    extracted_answer = sample.get("extracted_answer", "")
    if not extracted_answer:
        # Try to find it in the logs
        logs = trace.get("logs", [])
        for log in reversed(logs):
            if log.get("type") == "answer_evaluation":
                extracted_answer = log.get("data", {}).get("extracted_answer", "")
                if extracted_answer:
                    break

    # Format the prompt
    conversation_str = format_conversation(messages)
    prompt = ANALYSIS_PROMPT.format(
        full_spec_q=full_spec_q,
        ground_truth_a=ground_truth_a,
        conversation=conversation_str,
        extracted_answer=extracted_answer,
    )

    # Call the model
    response = await model_client.generate_json(
        messages=[{"role": "user", "content": prompt}],
        model=model,
        temperature=0.0,
    )

    result_data = response.content

    return AnalysisResult(
        sample_id=sample_id,
        task_name=task_name,
        category=result_data.get("category", "other"),
        correct_answer_present=result_data.get("correct_answer_present", False),
        extracted_answer=extracted_answer,
        assistant_final_answer=result_data.get("assistant_final_answer", ""),
        ground_truth=extract_ground_truth_final(ground_truth_a),
        explanation=result_data.get("explanation", ""),
        raw_response=result_data,
    )


async def run_analysis(
    run_dir: str,
    model: str = "gpt-4o-mini",
    max_samples: Optional[int] = None,
    task_filter: Optional[str] = None,
    verbose: bool = False,
) -> list[AnalysisResult]:
    """Run error analysis on all incorrect baseline samples in a run directory."""

    results_path = os.path.join(run_dir, "results.json")
    if not os.path.exists(results_path):
        raise FileNotFoundError(f"Results file not found: {results_path}")

    with open(results_path, "r") as f:
        samples = json.load(f)

    # Filter for incorrect samples only
    incorrect_samples = [s for s in samples if not s.get("is_correct", True)]

    # Optional task filter
    if task_filter:
        incorrect_samples = [s for s in incorrect_samples if s.get("task_name") == task_filter]

    # Optional limit
    if max_samples:
        incorrect_samples = incorrect_samples[:max_samples]

    print(f"Found {len(incorrect_samples)} incorrect samples to analyze")

    if not incorrect_samples:
        return []

    # Create model client
    model_client = get_model_client(model)

    results = []
    for i, sample in enumerate(incorrect_samples):
        sample_id = sample.get("sample_id", "unknown")
        if verbose:
            print(f"[{i + 1}/{len(incorrect_samples)}] Analyzing {sample_id}...")

        try:
            result = await analyze_conversation(sample, model_client, model)
            results.append(result)

            if verbose:
                print(f"  -> Category: {result.category}")
                if result.explanation:
                    print(f"  -> Explanation: {result.explanation[:100]}...")
        except Exception as e:
            print(f"  -> Error analyzing {sample_id}: {e}")
            results.append(
                AnalysisResult(
                    sample_id=sample_id,
                    task_name=sample.get("task_name", "unknown"),
                    category="analysis_error",
                    correct_answer_present=False,
                    extracted_answer="",
                    assistant_final_answer="",
                    ground_truth="",
                    explanation=str(e),
                )
            )

    return results


def print_summary(results: list[AnalysisResult]) -> None:
    """Print a summary of the analysis results."""

    if not results:
        print("No results to summarize.")
        return

    print("\n" + "=" * 60)
    print("ERROR ANALYSIS SUMMARY")
    print("=" * 60)

    # Count by category
    category_counts = Counter(r.category for r in results)

    print(f"\nTotal incorrect samples analyzed: {len(results)}")
    print("\nBreakdown by error category:")
    print("-" * 40)

    # Sort by count descending
    for category, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        pct = count / len(results) * 100
        desc = ERROR_CATEGORIES.get(category, category)
        print(f"  {category}: {count} ({pct:.1f}%)")
        print(f"    {desc}")

    # Count false negatives (where correct answer was present)
    false_negatives = sum(1 for r in results if r.correct_answer_present)
    print(
        f"\nPotential false negatives (correct answer was present): {false_negatives} ({false_negatives / len(results) * 100:.1f}%)"
    )

    # Breakdown by task
    task_counts = Counter(r.task_name for r in results)
    if len(task_counts) > 1:
        print("\nBreakdown by task:")
        print("-" * 40)
        for task, count in sorted(task_counts.items(), key=lambda x: -x[1]):
            print(f"  {task}: {count}")

    # Show "other" explanations
    other_results = [r for r in results if r.category == "other"]
    if other_results:
        print("\n'Other' category explanations:")
        print("-" * 40)
        for r in other_results:
            print(f"  [{r.sample_id}]: {r.explanation[:200]}")


def save_results(results: list[AnalysisResult], output_path: str) -> None:
    """Save analysis results to a JSON file."""

    output_data = {
        "timestamp": datetime.now().isoformat(),
        "total_analyzed": len(results),
        "summary": {
            "by_category": dict(Counter(r.category for r in results)),
            "false_negatives": sum(1 for r in results if r.correct_answer_present),
        },
        "results": [
            {
                "sample_id": r.sample_id,
                "task_name": r.task_name,
                "category": r.category,
                "correct_answer_present": r.correct_answer_present,
                "extracted_answer": r.extracted_answer,
                "assistant_final_answer": r.assistant_final_answer,
                "ground_truth": r.ground_truth,
                "explanation": r.explanation,
            }
            for r in results
        ],
    }

    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"\nResults saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze incorrect baseline conversations to categorize errors"
    )
    parser.add_argument(
        "run_dir",
        help="Path to the run directory containing results.json",
    )
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="Model to use for analysis (default: gpt-4o-mini)",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file for detailed results (JSON)",
    )
    parser.add_argument(
        "--max-samples",
        "-n",
        type=int,
        help="Maximum number of samples to analyze",
    )
    parser.add_argument(
        "--task",
        help="Filter to a specific task (e.g., 'math', 'code')",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print progress for each sample",
    )

    args = parser.parse_args()

    # Run analysis
    results = asyncio.run(
        run_analysis(
            run_dir=args.run_dir,
            model=args.model,
            max_samples=args.max_samples,
            task_filter=args.task,
            verbose=args.verbose,
        )
    )

    # Print summary
    print_summary(results)

    # Save detailed results if requested
    if args.output:
        save_results(results, args.output)
    else:
        # Default output path
        default_output = os.path.join(args.run_dir, "error_analysis.json")
        save_results(results, default_output)


if __name__ == "__main__":
    main()
