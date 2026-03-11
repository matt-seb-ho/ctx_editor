"""Build the test subset of problems exhibiting true multi-turn assistant failures.

Reads prelim_fn.json outputs from multiple variance runs and identifies problems
where the assistant (not the user simulator) is responsible for incorrect evaluation
in a majority of runs.

A "true negative" for a given run means:
  - The sample was incorrect (is_correct=False)
  - It was NOT flagged as a preliminary false negative (i.e. user sim was sufficient
    and an answer was extracted)

We count how many runs each problem appears as a true negative, then apply a
threshold to decide which problems belong in the test subset.

Usage:
    python -m ctx_editor.build_test_subset
    python -m ctx_editor.build_test_subset --threshold 1
    python -m ctx_editor.build_test_subset --output data/test_subset.json
"""

import argparse
import json
from collections import defaultdict
from pathlib import Path

from .paths import PROJECT_ROOT

# ---------------------------------------------------------------------------
# Run directories for each task (3 variance runs each)
# These correspond to the runs documented in misc/combined_variance_runs.md
# ---------------------------------------------------------------------------

VARIANCE_RUNS: dict[str, list[str]] = {
    "math": [
        "outputs/2026-03-06/04-56-49",
        "outputs/2026-03-06/05-11-40",
        "outputs/2026-03-06/05-57-29",
    ],
    "code": [
        "outputs/2026-03-06/06-11-33",
        "outputs/2026-03-06/07-31-16",
        "outputs/2026-03-06/08-26-32",
    ],
    "database": [
        "outputs/2026-03-08/00-30-18",
        "outputs/2026-03-08/00-37-49",
        "outputs/2026-03-08/00-45-08",
    ],
    "actions": [
        "outputs/2026-03-08/01-01-13",
        "outputs/2026-03-08/01-09-47",
        "outputs/2026-03-08/01-17-48",
    ],
}

NUM_RUNS = 3  # runs per task


def load_run_results(run_dir: str) -> dict:
    """Load prelim_fn.json from a run directory."""
    path = PROJECT_ROOT / run_dir / "prelim_fn.json"
    if not path.exists():
        raise FileNotFoundError(f"No prelim_fn.json in {run_dir}. Run identify_false_negatives first.")
    with open(path) as f:
        return json.load(f)


def load_all_trace_correctness(run_dir: str) -> dict[str, bool]:
    """Load is_correct for ALL samples (not just incorrect) from trace files."""
    traces_dir = PROJECT_ROOT / run_dir / "traces"
    correctness: dict[str, bool] = {}
    if traces_dir.exists():
        for trace_file in traces_dir.rglob("*.json"):
            with open(trace_file) as f:
                sample = json.load(f)
            sample_id = sample.get("sample_id", "")
            correctness[sample_id] = sample.get("is_correct", True)
    return correctness


def build_test_subset(threshold: int = 2) -> dict:
    """Build the test subset across all tasks.

    Args:
        threshold: Minimum number of runs where a problem must appear as a
            true negative to be included. Default 2 (majority of 3 runs).

    Returns:
        Dict with per-task results and the combined test subset.
    """
    all_results: dict[str, dict] = {}  # task -> problem analysis

    for task, run_dirs in VARIANCE_RUNS.items():
        # Track per-problem counts
        # true_neg_count: times the problem was incorrect AND classified as true negative
        # incorrect_count: times the problem was incorrect (regardless of classification)
        # fn_count: times the problem was incorrect AND classified as false negative
        # correct_count: times the problem was correct
        problem_stats: dict[str, dict] = defaultdict(lambda: {
            "true_neg_count": 0,
            "false_neg_count": 0,
            "incorrect_count": 0,
            "correct_count": 0,
            "fn_reasons": [],
        })

        for run_dir in run_dirs:
            # Load correctness for all samples in this run
            correctness = load_all_trace_correctness(run_dir)

            # Load false negative analysis (only covers incorrect samples)
            fn_data = load_run_results(run_dir)
            fn_results = {r["sample_id"]: r for r in fn_data["results"]}

            # Process all problems
            for sample_id, is_correct in correctness.items():
                stats = problem_stats[sample_id]
                if is_correct:
                    stats["correct_count"] += 1
                else:
                    stats["incorrect_count"] += 1
                    fn_result = fn_results.get(sample_id)
                    if fn_result and fn_result["is_preliminary_fn"]:
                        stats["false_neg_count"] += 1
                        reasons = []
                        if not fn_result["has_extracted_answer"]:
                            reasons.append(f"no_answer({fn_result['last_turn_classification']})")
                        if not fn_result["user_sim_sufficient"]:
                            reasons.append(f"distortion: {fn_result['missing_elements']}")
                        stats["fn_reasons"].append("; ".join(reasons))
                    else:
                        stats["true_neg_count"] += 1

        all_results[task] = dict(problem_stats)

    # Build the test subset: problems with true_neg_count >= threshold
    test_subset: dict[str, list[str]] = {}
    summary_stats: dict[str, dict] = {}

    for task, problem_stats in all_results.items():
        selected = []
        for problem_id, stats in sorted(problem_stats.items()):
            if stats["true_neg_count"] >= threshold:
                selected.append(problem_id)

        test_subset[task] = selected

        # Compute summary stats
        total_problems = len(problem_stats)
        always_correct = sum(
            1 for s in problem_stats.values() if s["correct_count"] == NUM_RUNS
        )
        ever_incorrect = sum(
            1 for s in problem_stats.values() if s["incorrect_count"] > 0
        )
        summary_stats[task] = {
            "total_problems": total_problems,
            "always_correct": always_correct,
            "ever_incorrect": ever_incorrect,
            "test_subset_size": len(selected),
            "true_neg_distribution": {
                str(i): sum(
                    1 for s in problem_stats.values() if s["true_neg_count"] == i
                )
                for i in range(NUM_RUNS + 1)
            },
        }

    return {
        "threshold": threshold,
        "num_runs_per_task": NUM_RUNS,
        "summary": summary_stats,
        "test_subset": test_subset,
        "detailed": {
            task: {
                pid: stats
                for pid, stats in sorted(problem_stats.items())
            }
            for task, problem_stats in all_results.items()
        },
    }


def print_report(result: dict) -> None:
    """Print a human-readable report."""
    threshold = result["threshold"]
    print("=" * 70)
    print(f"TEST SUBSET ANALYSIS (threshold = {threshold}/{NUM_RUNS} runs)")
    print("=" * 70)

    total_subset = 0
    total_problems = 0

    for task in VARIANCE_RUNS:
        stats = result["summary"][task]
        subset = result["test_subset"][task]
        total_subset += len(subset)
        total_problems += stats["total_problems"]

        print(f"\n--- {task} ---")
        print(f"  Total problems:     {stats['total_problems']}")
        print(f"  Always correct:     {stats['always_correct']}")
        print(f"  Ever incorrect:     {stats['ever_incorrect']}")
        print(f"  Test subset size:   {stats['test_subset_size']}")
        print(f"  True neg distribution (0/{NUM_RUNS} .. {NUM_RUNS}/{NUM_RUNS}):", end="")
        for i in range(NUM_RUNS + 1):
            count = stats["true_neg_distribution"][str(i)]
            print(f"  {i}:{count}", end="")
        print()

    print(f"\n{'=' * 70}")
    print(f"TOTAL: {total_subset} problems in test subset out of {total_problems}")
    print(f"{'=' * 70}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build test subset of problems with true multi-turn assistant failures"
    )
    parser.add_argument(
        "--threshold", "-t",
        type=int,
        default=2,
        help="Min runs with true negative to include (default: 2 = majority)",
    )
    parser.add_argument(
        "--output", "-o",
        default="data/test_subset.json",
        help="Output JSON file path (default: data/test_subset.json)",
    )
    args = parser.parse_args()

    result = build_test_subset(threshold=args.threshold)
    print_report(result)

    # Also try threshold=1 if threshold=2 gives small subsets
    if args.threshold == 2:
        result_t1 = build_test_subset(threshold=1)
        print(f"\n\nFor comparison with threshold=1:")
        for task in VARIANCE_RUNS:
            print(f"  {task}: {result_t1['summary'][task]['test_subset_size']} problems")
        total_t1 = sum(len(v) for v in result_t1["test_subset"].values())
        print(f"  TOTAL: {total_t1}")

    # Save
    output_path = PROJECT_ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save compact version (just the subset + summary, not full details)
    save_data = {
        "threshold": result["threshold"],
        "num_runs_per_task": NUM_RUNS,
        "summary": result["summary"],
        "test_subset": result["test_subset"],
    }
    with open(output_path, "w") as f:
        json.dump(save_data, f, indent=2)
    print(f"\nTest subset saved to: {output_path}")

    # Also save detailed analysis
    detailed_path = output_path.with_name("test_subset_detailed.json")
    with open(detailed_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Detailed analysis saved to: {detailed_path}")


if __name__ == "__main__":
    main()
