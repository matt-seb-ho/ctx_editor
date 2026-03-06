"""Identify preliminary false negatives in incorrect conversation traces.

General-purpose (task-agnostic) preliminary checks on every incorrect sample:

  Check 1 (programmatic): Did we fail to extract an answer? Is `extracted_answer`
    null or empty? Also records the last assistant turn's classification
    (answer_attempt, clarification, interrogation, discussion, hedge, refuse, missing).

  Check 2 (LLM): When combined, do the user simulator's messages convey all the
    information present in the original single-turn question? If not, this is a
    sharding distortion — the assistant never had a fair chance.

Task-specific checks can be registered via TASK_EXTRA_CHECKS and are run after the
preliminary checks.

Usage:
    python -m ctx_editor.identify_false_negatives outputs/2026-01-30/04-56-38
    python -m ctx_editor.identify_false_negatives outputs/2026-01-30/04-56-38 --model gpt-4o
    python -m ctx_editor.identify_false_negatives outputs/2026-01-30/04-56-38 --concurrency 10
    python -m ctx_editor.identify_false_negatives outputs/2026-01-30/04-56-38 --task math -v
"""

import argparse
import asyncio
import json
import os
from collections import Counter
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv
from tqdm.asyncio import tqdm_asyncio

from .models import get_model_client
from .paths import PROJECT_ROOT

load_dotenv(PROJECT_ROOT / ".env")


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

USER_SIM_SUFFICIENCY_PROMPT = """\
You are auditing an AI evaluation system. In this system a "user simulator" \
reveals a problem to an assistant piece-by-piece across multiple turns. \
Your job is to decide whether the user simulator's messages, taken together, \
gave a capable solver ALL the information needed to solve the problem correctly.

## Original Problem (complete, single-turn version)
{full_spec_q}

## Ground Truth Answer
{ground_truth_a}

## User Simulator Messages (all turns, in order)
{user_messages}

## Instructions
Compare the user messages against the original problem.

- Do the user messages collectively convey every constraint, quantity, \
relationship, and instruction that is necessary to arrive at the ground-truth answer?
- Minor rewordings are acceptable. Focus on whether any critical detail is \
missing or was stated in a way that changes the problem's meaning.

Respond with a JSON object:
{{
    "sufficient": <true if all necessary information was present, false otherwise>,
    "missing_elements": ["list every crucial detail that was absent or distorted; empty list if sufficient"],
    "explanation": "one or two sentence summary of your assessment"
}}
"""


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class PrelimFNResult:
    sample_id: str
    task_name: str

    # Check 1: extraction / classification
    has_extracted_answer: bool
    extracted_answer: str = ""
    last_turn_classification: str = ""  # e.g. "answer_attempt", "clarification", ...

    # Check 2: user sim sufficiency (LLM)
    user_sim_sufficient: bool = True
    missing_elements: list[str] = field(default_factory=list)
    sufficiency_explanation: str = ""

    # Task-specific extras (populated by registered hooks)
    task_extras: dict[str, Any] = field(default_factory=dict)

    # Misc
    ground_truth: str = ""
    error: str = ""  # non-empty if analysis itself failed

    @property
    def is_preliminary_fn(self) -> bool:
        """True if either preliminary check flags this as a likely false negative."""
        return not self.has_extracted_answer or not self.user_sim_sufficient


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


def get_active_messages(trace: dict) -> list[dict]:
    """Return only visible messages from a ctx_editor trace dict."""
    messages = trace.get("messages", [])
    return [m for m in messages if m.get("visible", True) and m.get("role") != "log"]


def get_extracted_answer(sample: dict) -> str:
    """Try to find the extracted answer from the sample / trace logs."""
    extracted = sample.get("extracted_answer", "")
    if extracted:
        return extracted
    trace = sample.get("trace", {})
    if isinstance(trace, dict):
        logs = trace.get("logs", [])
        for log in reversed(logs):
            if log.get("type") == "answer_evaluation":
                ans = log.get("data", {}).get("extracted_answer", "")
                if ans:
                    return ans
    return ""


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
# Task-specific extra checks (register per task)
# ---------------------------------------------------------------------------

# Signature: async (sample, model_client, model) -> dict[str, Any]
TaskExtraCheck = Callable[[dict, Any, str], Coroutine[Any, Any, dict[str, Any]]]

# Register task-specific checks here. They run AFTER the two preliminary checks.
# Each returns a dict that gets merged into result.task_extras.
TASK_EXTRA_CHECKS: dict[str, list[TaskExtraCheck]] = {}


# ---------------------------------------------------------------------------
# Core analysis
# ---------------------------------------------------------------------------

async def analyze_sample(
    sample: dict,
    model_client: Any,
    model: str,
) -> PrelimFNResult:
    """Run preliminary false-negative checks on a single sample."""
    sample_id = sample.get("sample_id", "unknown")
    task_name = sample.get("task_name", "unknown")
    metadata = sample.get("metadata", {})
    full_spec_q = metadata.get("full_spec_q", "")
    ground_truth_a = metadata.get("ground_truth_a", "")

    # ------------------------------------------------------------------
    # Check 1 (programmatic): extracted answer + last turn classification
    # ------------------------------------------------------------------
    extracted_answer = get_extracted_answer(sample)
    has_extracted = bool(extracted_answer)
    last_classification = get_last_turn_classification(sample)

    # ------------------------------------------------------------------
    # Check 2 (LLM): user sim sufficiency
    # ------------------------------------------------------------------
    trace = sample.get("trace", {})
    messages = get_active_messages(trace) if isinstance(trace, dict) else []
    user_messages_str = format_user_messages(messages)

    prompt = USER_SIM_SUFFICIENCY_PROMPT.format(
        full_spec_q=full_spec_q or "(not available)",
        ground_truth_a=ground_truth_a or "(not available)",
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

    result = PrelimFNResult(
        sample_id=sample_id,
        task_name=task_name,
        has_extracted_answer=has_extracted,
        extracted_answer=extracted_answer,
        last_turn_classification=last_classification,
        user_sim_sufficient=sufficient,
        missing_elements=missing_elements,
        sufficiency_explanation=explanation,
        ground_truth=ground_truth_a,
    )

    # ------------------------------------------------------------------
    # Task-specific extras
    # ------------------------------------------------------------------
    extra_checks = TASK_EXTRA_CHECKS.get(task_name, [])
    for check_fn in extra_checks:
        extras = await check_fn(sample, model_client, model)
        result.task_extras.update(extras)

    return result


async def _analyze_with_semaphore(
    sem: asyncio.Semaphore,
    sample: dict,
    model_client: Any,
    model: str,
    verbose: bool,
) -> PrelimFNResult:
    """Wrapper that respects a concurrency semaphore."""
    async with sem:
        sid = sample.get("sample_id", "unknown")
        try:
            result = await analyze_sample(sample, model_client, model)
        except Exception as e:
            if verbose:
                print(f"  ERROR [{sid}]: {e}")
            result = PrelimFNResult(
                sample_id=sid,
                task_name=sample.get("task_name", "unknown"),
                has_extracted_answer=False,
                extracted_answer=get_extracted_answer(sample),
                ground_truth=sample.get("metadata", {}).get("ground_truth_a", ""),
                error=str(e),
            )
        if verbose:
            flags = []
            if not result.has_extracted_answer:
                flags.append(f"no_answer({result.last_turn_classification})")
            if not result.user_sim_sufficient:
                flags.append("sharding_distortion")
            tag = " ".join(flags) if flags else "pass"
            print(f"  [{sid}] {tag}")
        return result


async def run_analysis(
    run_dir: str,
    model: str = "gpt-4o-mini",
    concurrency: int = 5,
    max_samples: Optional[int] = None,
    task_filter: Optional[str] = None,
    verbose: bool = False,
    debug: bool = False,
) -> list[PrelimFNResult]:
    """Run preliminary false-negative checks on all incorrect samples in a run directory."""
    run_path = Path(run_dir)

    # Load samples
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

    # Keep only incorrect samples
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
        print(f"extracted_answer: {get_extracted_answer(s)!r}")
        print(f"last_classification: {get_last_turn_classification(s)!r}")
        print("=" * 60 + "\n")

    model_client = get_model_client(model)
    sem = asyncio.Semaphore(concurrency)

    tasks = [
        _analyze_with_semaphore(sem, sample, model_client, model, verbose)
        for sample in incorrect
    ]

    results: list[PrelimFNResult] = await tqdm_asyncio.gather(
        *tasks, desc="Analyzing", disable=verbose
    )

    return results


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def print_summary(results: list[PrelimFNResult]) -> None:
    if not results:
        print("No results to summarize.")
        return

    print("\n" + "=" * 60)
    print("PRELIMINARY FALSE NEGATIVE ANALYSIS")
    print("=" * 60)

    total = len(results)
    errors = sum(1 for r in results if r.error)

    # Check 1 stats
    no_answer = [r for r in results if not r.has_extracted_answer]
    classification_counts = Counter(r.last_turn_classification for r in no_answer)

    # Check 2 stats
    distortions = [r for r in results if not r.user_sim_sufficient]

    # Combined
    prelim_fn = [r for r in results if r.is_preliminary_fn]

    print(f"\nTotal incorrect samples analyzed: {total}")
    if errors:
        print(f"Analysis errors: {errors}")

    print("\n--- Check 1: Answer Extraction ---")
    print(f"Missing extracted answer: {len(no_answer)} / {total} ({len(no_answer)/total:.1%})")
    if classification_counts:
        print("  Last turn classifications for missing-answer cases:")
        for cls, count in sorted(classification_counts.items(), key=lambda x: -x[1]):
            print(f"    {cls or '(empty)':<20} {count:3d}")

    print("\n--- Check 2: User Sim Sufficiency ---")
    print(f"Sharding distortion: {len(distortions)} / {total} ({len(distortions)/total:.1%})")
    if distortions:
        print("  Examples (up to 5):")
        for r in distortions[:5]:
            missing = "; ".join(r.missing_elements) if r.missing_elements else r.sufficiency_explanation
            print(f"    [{r.sample_id}] {missing[:140]}")

    print("\n--- Summary ---")
    print(f"Preliminary false negatives: {len(prelim_fn)} / {total} ({len(prelim_fn)/total:.1%})")
    print(f"Likely true negatives: {total - len(prelim_fn) - errors} / {total}")

    # Per-task breakdown
    task_counts = Counter(r.task_name for r in results)
    if len(task_counts) > 1:
        print("\nPer-task breakdown:")
        print("-" * 50)
        for task, count in sorted(task_counts.items(), key=lambda x: -x[1]):
            task_results = [r for r in results if r.task_name == task]
            fn = sum(1 for r in task_results if r.is_preliminary_fn)
            no_ans = sum(1 for r in task_results if not r.has_extracted_answer)
            dist = sum(1 for r in task_results if not r.user_sim_sufficient)
            print(f"  {task:<15} {count:3d} samples | {fn} prelim FN | {no_ans} no answer | {dist} distortion")


def save_results(results: list[PrelimFNResult], output_path: str) -> None:
    output_data = {
        "timestamp": datetime.now().isoformat(),
        "total_analyzed": len(results),
        "summary": {
            "preliminary_false_negatives": sum(1 for r in results if r.is_preliminary_fn),
            "no_extracted_answer": sum(1 for r in results if not r.has_extracted_answer),
            "sharding_distortion": sum(1 for r in results if not r.user_sim_sufficient),
            "by_last_classification": dict(Counter(
                r.last_turn_classification for r in results if not r.has_extracted_answer
            )),
        },
        "results": [
            {
                "sample_id": r.sample_id,
                "task_name": r.task_name,
                "is_preliminary_fn": r.is_preliminary_fn,
                "has_extracted_answer": r.has_extracted_answer,
                "extracted_answer": r.extracted_answer,
                "last_turn_classification": r.last_turn_classification,
                "user_sim_sufficient": r.user_sim_sufficient,
                "missing_elements": r.missing_elements,
                "sufficiency_explanation": r.sufficiency_explanation,
                "task_extras": r.task_extras,
                "ground_truth": r.ground_truth,
                "error": r.error,
            }
            for r in results
        ],
    }

    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"\nResults saved to: {output_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Preliminary false negative identification for incorrect conversation traces"
    )
    parser.add_argument(
        "run_dir",
        help="Path to the run directory (must contain traces/ or results.json)",
    )
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="Model to use for LLM checks (default: gpt-4o-mini)",
    )
    parser.add_argument(
        "--concurrency", "-c",
        type=int,
        default=5,
        help="Max concurrent LLM requests (default: 5)",
    )
    parser.add_argument(
        "--output", "-o",
        help="Output JSON file path (default: {run_dir}/prelim_fn.json)",
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

    print_summary(results)

    output_path = args.output or os.path.join(args.run_dir, "prelim_fn.json")
    save_results(results, output_path)


if __name__ == "__main__":
    main()
