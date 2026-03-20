"""Identify false negatives in incorrect conversation traces.

Two focused checks on every incorrect sample:

  1. User simulator sufficiency (LLM): Did the user simulator's messages, taken
     together, convey all information needed to solve the problem? If not, this is
     a user-simulator-induced error — the assistant never had a fair chance.

  2. Answer attempt classification (programmatic): Is the last assistant turn
     classified as an answer_attempt? If not, the evaluator automatically marks
     it incorrect, which may or may not be fair depending on configuration.

Future work: branch detection — check if the assistant presented multiple answers
for multiple interpretations, and whether any of them is correct.

Usage:
    python -m ctx_editor.identify_false_negatives outputs/2026-01-30/04-56-38
    python -m ctx_editor.identify_false_negatives outputs/2026-01-30/04-56-38 --model gpt-4o
    python -m ctx_editor.identify_false_negatives outputs/2026-01-30/04-56-38 --concurrency 10
    python -m ctx_editor.identify_false_negatives outputs/2026-01-30/04-56-38 --task math -v
"""

import argparse
import asyncio
import json
import logging
import os
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv
from tqdm.asyncio import tqdm_asyncio

from .models import get_model_client
from .paths import PROJECT_ROOT

load_dotenv(PROJECT_ROOT / ".env")

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data loading helpers
# ---------------------------------------------------------------------------

TASK_DATA_FILES: dict[str, str] = {
    "math": "full_math_subset.json",
    "code": "full_code_subset.json",
    "database": "full_database_subset.json",
    "actions": "full_actions_subset.json",
}


def load_task_metadata() -> dict[str, dict[str, str]]:
    """Load full_spec_q and ground_truth_a from data files, keyed by task_id."""
    data_dir = PROJECT_ROOT / "data"
    metadata: dict[str, dict[str, str]] = {}
    for task_name, filename in TASK_DATA_FILES.items():
        filepath = data_dir / filename
        if not filepath.exists():
            continue
        with open(filepath) as f:
            samples = json.load(f)
        for sample in samples:
            tid = sample.get("task_id", "")
            if tid:
                metadata[tid] = {
                    "full_spec_q": sample.get("full_spec_q", ""),
                    "ground_truth_a": sample.get("ground_truth_a", ""),
                }
    return metadata


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

USER_SIM_SUFFICIENCY_PROMPT = """\
You are auditing an AI evaluation system. In this system a "user simulator" \
reveals a problem to an assistant piece-by-piece across multiple turns. \
Your job is to decide whether the user simulator's messages, taken together \
(i.e. their UNION), gave a capable solver ALL the information needed to solve \
the problem correctly.

## Original Problem (complete, single-turn version)
{full_spec_q}

## Ground Truth Answer
{ground_truth_a}

## System Message (instructions/context given to the assistant)
{system_message}

## User Simulator Messages (all turns, in order)
{user_messages}

## Instructions
Compare the COMBINED content of the system message and all user messages against the original problem.

IMPORTANT context: It is EXPECTED that information is split across turns. \
That is by design, not a flaw. You must evaluate the UNION of all user \
messages — treat them as if you concatenated them into one block of text.

Mark the information as "sufficient" UNLESS one of these is true:
1. A critical detail (number, constraint, relationship, entity) from the \
original problem is completely absent from ALL user messages.
2. A critical detail was CHANGED in meaning (not merely reworded) in a way \
that makes the correct answer unreachable.

Do NOT flag:
- Information arriving late or in a different order than the original.
- Minor rewordings, paraphrasing, or splitting of sentences.
- Information that is inferable from the combination of user messages even if \
not stated in exactly the same words as the original.

Respond with a JSON object:
{{
    "sufficient": <true if a capable solver who read ALL the user messages has enough info to reach the ground-truth answer>,
    "missing_elements": ["list ONLY details that are truly absent or materially distorted; empty list if sufficient"],
    "explanation": "one or two sentence summary"
}}
"""


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class FalseNegativeResult:
    """Result of false-negative analysis for a single incorrect sample."""

    sample_id: str
    task_name: str

    # Check 1: user simulator sufficiency (LLM)
    user_sim_sufficient: bool = True
    missing_elements: list[str] = field(default_factory=list)
    sufficiency_explanation: str = ""

    # Check 2: answer attempt classification (programmatic)
    is_answer_attempt: bool = True
    last_turn_classification: str = ""  # e.g. "answer_attempt", "clarification", ...

    # Misc
    ground_truth: str = ""
    error: str = ""  # non-empty if analysis itself failed

    @property
    def exclusion_reason(self) -> Optional[str]:
        """Why this sample should be excluded from the accuracy denominator.

        Returns:
            "user_sim_induced" if user simulator distorted the problem (always excluded),
            "non_answer_attempt" if last turn wasn't an answer attempt (configurable),
            None if the sample should be counted normally.
        """
        if not self.user_sim_sufficient:
            return "user_sim_induced"
        if not self.is_answer_attempt:
            return "non_answer_attempt"
        return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def format_user_messages(messages: list[dict]) -> str:
    """Return a numbered list of user-role messages."""
    user_msgs = [m for m in messages if m.get("role") == "user"]
    if not user_msgs:
        return "(no user messages found)"
    lines = []
    for i, m in enumerate(user_msgs, 1):
        lines.append(f"[Turn {i}] {m.get('content', '').strip()}")
    return "\n\n".join(lines)


def format_system_message(messages: list[dict]) -> str:
    """Return the system message content, if any."""
    sys_msgs = [m for m in messages if m.get("role") == "system"]
    if not sys_msgs:
        return ""
    return sys_msgs[0].get("content", "").strip()


def get_active_messages(trace: dict) -> list[dict]:
    """Return only visible messages from a ctx_editor trace dict."""
    messages = trace.get("messages", [])
    return [m for m in messages if m.get("visible", True) and m.get("role") != "log"]


def get_last_turn_classification(sample: dict) -> str:
    """Get the response_type from the last verification log entry."""
    trace = sample.get("trace", {})
    if not isinstance(trace, dict):
        return ""
    logs = trace.get("logs", [])
    for log in reversed(logs):
        if log.get("type") == "verification":
            return log.get("data", {}).get("response_type", "")
    return ""


# ---------------------------------------------------------------------------
# Core analysis
# ---------------------------------------------------------------------------

async def analyze_sample(
    sample: dict,
    model_client: Any,
    model: str,
) -> FalseNegativeResult:
    """Run false-negative checks on a single incorrect sample."""
    sample_id = sample.get("sample_id", "unknown")
    task_name = sample.get("task_name", "unknown")
    metadata = sample.get("metadata", {})
    full_spec_q = metadata.get("full_spec_q", "")
    ground_truth_a = metadata.get("ground_truth_a", "")

    # ------------------------------------------------------------------
    # Check 1 (LLM): user simulator sufficiency
    # ------------------------------------------------------------------
    trace = sample.get("trace", {})
    messages = get_active_messages(trace) if isinstance(trace, dict) else []
    user_messages_str = format_user_messages(messages)
    system_message_str = format_system_message(messages)

    prompt = USER_SIM_SUFFICIENCY_PROMPT.format(
        full_spec_q=full_spec_q or "(not available)",
        ground_truth_a=ground_truth_a or "(not available)",
        system_message=system_message_str or "(none)",
        user_messages=user_messages_str,
    )

    resp = await model_client.generate_json(
        messages=[{"role": "user", "content": prompt}],
        model=model,
        temperature=0.0,
    )
    llm_result = resp.content

    sufficient = llm_result.get("sufficient", True)
    missing_elements = llm_result.get("missing_elements", [])
    explanation = llm_result.get("explanation", "")

    # ------------------------------------------------------------------
    # Check 2 (programmatic): last turn classification
    # ------------------------------------------------------------------
    last_classification = get_last_turn_classification(sample)
    is_answer_attempt = last_classification == "answer_attempt"

    return FalseNegativeResult(
        sample_id=sample_id,
        task_name=task_name,
        user_sim_sufficient=sufficient,
        missing_elements=missing_elements,
        sufficiency_explanation=explanation,
        is_answer_attempt=is_answer_attempt,
        last_turn_classification=last_classification,
        ground_truth=ground_truth_a,
    )


async def analyze_sample_inline(
    result_dict: dict[str, Any],
    model_client: Any,
    model: str,
) -> Optional[FalseNegativeResult]:
    """Analyze a single SimulationResult dict. Returns None for correct results.

    This is the entry point for inline analysis from run_experiment.py.
    """
    if result_dict.get("is_correct", True):
        return None
    return await analyze_sample(result_dict, model_client, model)


async def _analyze_with_semaphore(
    sem: asyncio.Semaphore,
    sample: dict,
    model_client: Any,
    model: str,
    verbose: bool,
) -> FalseNegativeResult:
    """Wrapper that respects a concurrency semaphore."""
    async with sem:
        sid = sample.get("sample_id", "unknown")
        try:
            result = await analyze_sample(sample, model_client, model)
        except Exception as e:
            if verbose:
                print(f"  ERROR [{sid}]: {e}")
            result = FalseNegativeResult(
                sample_id=sid,
                task_name=sample.get("task_name", "unknown"),
                user_sim_sufficient=True,  # default to not excluding on error
                is_answer_attempt=True,
                ground_truth=sample.get("metadata", {}).get("ground_truth_a", ""),
                error=str(e),
            )
        if verbose:
            flags = []
            if not result.user_sim_sufficient:
                flags.append("user_sim_induced")
            if not result.is_answer_attempt:
                flags.append(f"non_answer({result.last_turn_classification})")
            tag = " ".join(flags) if flags else "ok"
            print(f"  [{sid}] {tag}")
        return result


async def run_analysis(
    run_dir: str,
    model: str = "gpt-5-mini",
    concurrency: int = 5,
    max_samples: Optional[int] = None,
    task_filter: Optional[str] = None,
    verbose: bool = False,
    debug: bool = False,
) -> list[FalseNegativeResult]:
    """Run false-negative checks on all incorrect samples in a run directory."""
    run_path = Path(run_dir)

    task_metadata = load_task_metadata()

    # Load samples from traces/ or results.json
    samples: list[dict] = []
    traces_dir = run_path / "traces"
    if traces_dir.exists():
        for trace_file in sorted(traces_dir.rglob("*.json")):
            try:
                with open(trace_file) as f:
                    samples.append(json.load(f))
            except Exception as e:
                if verbose:
                    print(f"Warning: could not load {trace_file}: {e}")
    else:
        results_path = run_path / "results.json"
        if not results_path.exists():
            raise FileNotFoundError(
                f"Neither traces/ directory nor results.json found in {run_dir}"
            )
        with open(results_path) as f:
            samples = json.load(f)

    # Inject metadata from data files if not already present
    for sample in samples:
        if not sample.get("metadata"):
            sample_id = sample.get("sample_id", "")
            meta = task_metadata.get(sample_id, {})
            sample["metadata"] = meta

    incorrect = [s for s in samples if not s.get("is_correct", True)]

    if task_filter:
        incorrect = [s for s in incorrect if s.get("task_name") == task_filter]

    if max_samples:
        incorrect = incorrect[:max_samples]

    print(f"Found {len(incorrect)} incorrect samples to analyze (concurrency={concurrency})")
    if not incorrect:
        return []

    if debug:
        s = incorrect[0]
        meta = s.get("metadata", {})
        print("\n" + "=" * 60)
        print("DEBUG: first sample")
        print("=" * 60)
        print(f"sample_id:       {s.get('sample_id')}")
        print(f"task_name:       {s.get('task_name')}")
        print(f"full_spec_q:     {bool(meta.get('full_spec_q'))}  {str(meta.get('full_spec_q',''))[:200]}")
        print(f"ground_truth_a:  {bool(meta.get('ground_truth_a'))}  {str(meta.get('ground_truth_a',''))[:200]}")
        print(f"last_classification: {get_last_turn_classification(s)!r}")
        print("=" * 60 + "\n")

    model_client = get_model_client(model)
    sem = asyncio.Semaphore(concurrency)

    tasks = [
        _analyze_with_semaphore(sem, sample, model_client, model, verbose)
        for sample in incorrect
    ]

    results: list[FalseNegativeResult] = await tqdm_asyncio.gather(
        *tasks, desc="False negative analysis", disable=verbose
    )

    return results


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def compute_adjusted_accuracy(
    total_correct: int,
    total_valid: int,
    fn_results: list[FalseNegativeResult],
    exclude_non_answer_attempts: bool = False,
) -> dict[str, Any]:
    """Compute adjusted accuracy metrics given false-negative analysis results.

    Args:
        total_correct: Number of correct results (from evaluation).
        total_valid: Total non-errored results (denominator for raw accuracy).
        fn_results: False-negative analysis results (only for incorrect samples).
        exclude_non_answer_attempts: If True, also exclude non-answer-attempts
            from the denominator.

    Returns:
        Dict with raw and adjusted accuracy info.
    """
    user_sim_induced = [r for r in fn_results if not r.user_sim_sufficient]
    non_answer_attempts = [
        r for r in fn_results
        if r.user_sim_sufficient and not r.is_answer_attempt
    ]

    # Always exclude user_sim_induced from denominator
    adjusted_denominator = total_valid - len(user_sim_induced)
    if exclude_non_answer_attempts:
        adjusted_denominator -= len(non_answer_attempts)

    raw_accuracy = total_correct / total_valid if total_valid > 0 else 0
    adjusted_accuracy = total_correct / adjusted_denominator if adjusted_denominator > 0 else 0

    return {
        "raw_correct": total_correct,
        "raw_total": total_valid,
        "raw_accuracy": raw_accuracy,
        "adjusted_correct": total_correct,
        "adjusted_total": adjusted_denominator,
        "adjusted_accuracy": adjusted_accuracy,
        "user_sim_induced": len(user_sim_induced),
        "non_answer_attempts": len(non_answer_attempts),
        "excluded_non_answer_attempts": exclude_non_answer_attempts,
    }


def print_fn_summary(
    fn_results: list[FalseNegativeResult],
    total_correct: int = 0,
    total_valid: int = 0,
    exclude_non_answer_attempts: bool = False,
) -> None:
    """Print a summary of false-negative analysis results."""
    if not fn_results:
        print("No incorrect samples to analyze for false negatives.")
        return

    total_incorrect = len(fn_results)
    errors = sum(1 for r in fn_results if r.error)

    user_sim_induced = [r for r in fn_results if not r.user_sim_sufficient]
    non_answer = [
        r for r in fn_results
        if r.user_sim_sufficient and not r.is_answer_attempt
    ]

    print("\n" + "=" * 60)
    print("FALSE NEGATIVE ANALYSIS")
    print("=" * 60)

    print(f"\nTotal incorrect samples analyzed: {total_incorrect}")
    if errors:
        print(f"Analysis errors: {errors}")

    # User simulator induced
    print(f"\n--- User Simulator Induced ({len(user_sim_induced)}) ---")
    if user_sim_induced:
        print("  These are ALWAYS excluded from the accuracy denominator.")
        for r in user_sim_induced:
            missing = "; ".join(r.missing_elements) if r.missing_elements else r.sufficiency_explanation
            print(f"  [{r.sample_id}] {missing[:140]}")
    else:
        print("  None detected.")

    # Non-answer attempts
    print(f"\n--- Non-Answer Attempts ({len(non_answer)}) ---")
    excl_label = "EXCLUDED" if exclude_non_answer_attempts else "INCLUDED in denominator (configurable)"
    print(f"  {excl_label}")
    if non_answer:
        classification_counts = Counter(r.last_turn_classification for r in non_answer)
        for cls, count in sorted(classification_counts.items(), key=lambda x: -x[1]):
            print(f"    {cls or '(empty)':<20} {count:3d}")
    else:
        print("  None detected.")

    # Adjusted accuracy
    if total_valid > 0:
        adj = compute_adjusted_accuracy(
            total_correct, total_valid, fn_results, exclude_non_answer_attempts
        )
        print(f"\n--- Accuracy ---")
        print(f"  Raw:      {adj['raw_correct']}/{adj['raw_total']} ({adj['raw_accuracy']:.2%})")
        print(f"  Adjusted: {adj['adjusted_correct']}/{adj['adjusted_total']} ({adj['adjusted_accuracy']:.2%})")


def save_fn_results(fn_results: list[FalseNegativeResult], output_path: str) -> None:
    """Save false-negative analysis results to a JSON file."""
    output_data = {
        "timestamp": datetime.now().isoformat(),
        "total_analyzed": len(fn_results),
        "summary": {
            "user_sim_induced": sum(1 for r in fn_results if not r.user_sim_sufficient),
            "non_answer_attempts": sum(
                1 for r in fn_results
                if r.user_sim_sufficient and not r.is_answer_attempt
            ),
            "non_answer_classification_breakdown": dict(Counter(
                r.last_turn_classification for r in fn_results
                if r.user_sim_sufficient and not r.is_answer_attempt
            )),
            "user_sim_induced_ids": [r.sample_id for r in fn_results if not r.user_sim_sufficient],
            "non_answer_attempt_ids": [
                r.sample_id for r in fn_results
                if r.user_sim_sufficient and not r.is_answer_attempt
            ],
        },
        "results": [
            {
                "sample_id": r.sample_id,
                "task_name": r.task_name,
                "exclusion_reason": r.exclusion_reason,
                "user_sim_sufficient": r.user_sim_sufficient,
                "missing_elements": r.missing_elements,
                "sufficiency_explanation": r.sufficiency_explanation,
                "is_answer_attempt": r.is_answer_attempt,
                "last_turn_classification": r.last_turn_classification,
                "ground_truth": r.ground_truth,
                "error": r.error,
            }
            for r in fn_results
        ],
    }

    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)

    logger.info(f"False negative analysis saved to: {output_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="False negative identification for incorrect conversation traces"
    )
    parser.add_argument(
        "run_dir",
        help="Path to the run directory (must contain traces/ or results.json)",
    )
    parser.add_argument(
        "--model",
        default="gpt-5-mini",
        help="Model to use for LLM checks (default: gpt-5-mini)",
    )
    parser.add_argument(
        "--concurrency", "-c",
        type=int,
        default=5,
        help="Max concurrent LLM requests (default: 5)",
    )
    parser.add_argument(
        "--output", "-o",
        help="Output JSON file path (default: {run_dir}/false_negatives.json)",
    )
    parser.add_argument(
        "--max-samples", "-n",
        type=int,
        help="Maximum number of samples to analyze",
    )
    parser.add_argument(
        "--task",
        help="Filter to a specific task (e.g. 'math', 'code')",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print per-sample progress and results",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print details for the first sample before running",
    )

    args = parser.parse_args()

    results = asyncio.run(
        run_analysis(
            run_dir=args.run_dir,
            model=args.model,
            concurrency=args.concurrency,
            max_samples=args.max_samples,
            task_filter=args.task,
            verbose=args.verbose,
            debug=args.debug,
        )
    )

    print_fn_summary(results)

    output_path = args.output or os.path.join(args.run_dir, "false_negatives.json")
    save_fn_results(results, output_path)


if __name__ == "__main__":
    main()
