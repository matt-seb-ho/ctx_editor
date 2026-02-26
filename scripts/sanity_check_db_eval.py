"""Sanity check: re-evaluate LiC database log predictions through V1 and V2 evaluators.

Loads predicted SQL from LiC logs, joins with sample data, and runs both
TaskDatabase (V1) and TaskDatabaseV2 (V2) evaluator_function on each.
Compares results against the original LiC scores to detect discrepancies.

Known issue in V1: eval_exec_match receives a directory path (e.g. .../orchestra)
but calls os.path.dirname() on it, which goes up to the parent (.../databases/).
There are no .sqlite files at that level, so db_paths is empty, the inner loop
never runs, pred_passes stays 1, and every prediction vacuously "passes".
V2 fixes this by passing {db_id}/{db_id}.sqlite as the db path.

Usage:
    python scripts/sanity_check_db_eval.py [--log-file PATH] [--limit N]
"""

import argparse
import json
import sys
from pathlib import Path

# Ensure project is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from lic.tasks.database.task_database import TaskDatabase
from lic.tasks.database.task_database_v2 import TaskDatabaseV2


DEFAULT_LOG = "data/imported_lic_logs/nano_user_logs/database/sharded/sharded_database_gpt-5-mini.jsonl"
DEFAULT_DATA = "data/sharded_instructions_600.json"


def load_logs(log_path: str):
    with open(log_path) as f:
        return [json.loads(line) for line in f]


def load_samples(data_path: str):
    with open(data_path) as f:
        samples = json.load(f)
    return {s["task_id"]: s for s in samples if s["task"] == "database"}


def get_last_extracted_answer(log_entry: dict) -> str | None:
    """Pull the last exact_answer from answer-evaluation log entries."""
    last_answer = None
    for entry in log_entry["trace"]:
        if isinstance(entry.get("content"), dict) and entry["content"].get("type") == "answer-evaluation":
            last_answer = entry["content"].get("exact_answer", "")
    return last_answer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log-file", default=DEFAULT_LOG, help="Path to LiC JSONL log file")
    parser.add_argument("--data-file", default=DEFAULT_DATA, help="Path to sample data JSON")
    parser.add_argument("--limit", type=int, default=None, help="Only process first N entries")
    args = parser.parse_args()

    logs = load_logs(args.log_file)
    samples = load_samples(args.data_file)

    if args.limit:
        logs = logs[: args.limit]

    task_v1 = TaskDatabase()
    task_v2 = TaskDatabaseV2()

    results = []
    v1_match_lic = 0
    v1_mismatch_lic = 0
    v2_match_lic = 0
    v2_mismatch_lic = 0
    v2_match_v1 = 0
    v2_mismatch_v1 = 0

    for i, log in enumerate(logs):
        task_id = log["task_id"]
        lic_score = log["score"]
        extracted = get_last_extracted_answer(log)

        if extracted is None:
            print(f"[{i}] {task_id}: no answer-evaluation found, skipping")
            continue

        sample = samples.get(task_id)
        if sample is None:
            print(f"[{i}] {task_id}: no matching sample, skipping")
            continue

        # Run both evaluators on the same extracted answer
        try:
            v1_result = task_v1.evaluator_function(extracted, sample)
            v1_score = v1_result["score"] if isinstance(v1_result, dict) else (1.0 if v1_result else 0.0)
        except Exception as e:
            v1_score = -1.0
            print(f"[{i}] {task_id}: V1 eval error: {e}")

        try:
            v2_result = task_v2.evaluator_function(extracted, sample)
            v2_score = v2_result["score"] if isinstance(v2_result, dict) else (1.0 if v2_result else 0.0)
        except Exception as e:
            v2_score = -1.0
            print(f"[{i}] {task_id}: V2 eval error: {e}")

        # Compare
        lic_v1_match = (lic_score == v1_score) or (lic_score is None)
        lic_v2_match = (lic_score == v2_score) or (lic_score is None)
        v1_v2_match = v1_score == v2_score

        if lic_v1_match:
            v1_match_lic += 1
        else:
            v1_mismatch_lic += 1

        if lic_v2_match:
            v2_match_lic += 1
        else:
            v2_mismatch_lic += 1

        if v1_v2_match:
            v2_match_v1 += 1
        else:
            v2_mismatch_v1 += 1

        status = ""
        if not lic_v1_match:
            status += " *** LiC!=V1"
        if not lic_v2_match:
            status += " *** LiC!=V2"
        if not v1_v2_match:
            status += " *** V1!=V2"

        print(
            f"[{i:3d}] {task_id:45s}  LiC={lic_score}  V1={v1_score}  V2={v2_score}{status}"
        )

        results.append({
            "task_id": task_id,
            "lic_score": lic_score,
            "v1_score": v1_score,
            "v2_score": v2_score,
            "extracted_answer_preview": extracted[:120],
        })

    # Summary
    total = len(results)
    print("\n" + "=" * 80)
    print(f"SUMMARY ({total} entries)")
    print(f"  LiC vs V1:  {v1_match_lic} match, {v1_mismatch_lic} mismatch")
    print(f"  LiC vs V2:  {v2_match_lic} match, {v2_mismatch_lic} mismatch")
    print(f"  V1  vs V2:  {v2_match_v1} match, {v2_mismatch_v1} mismatch")
    print(f"  LiC accuracy: {sum(1 for r in results if r['lic_score'] == 1.0) / total:.1%}")
    print(f"  V1  accuracy: {sum(1 for r in results if r['v1_score'] == 1.0) / total:.1%}")
    print(f"  V2  accuracy: {sum(1 for r in results if r['v2_score'] == 1.0) / total:.1%}")

    if v1_mismatch_lic > 0:
        print(f"\n  V1 bug: {v1_mismatch_lic} cases where V1 disagrees with LiC.")
        print("  Root cause: eval_exec_match receives a dir path, os.path.dirname()")
        print("  goes up one level, finds no .sqlite files -> vacuous pass.")

    if v2_mismatch_lic > 0:
        print(f"\n  V2 vs LiC: {v2_mismatch_lic} disagreements (inspect individually).")
        for r in results:
            if r["lic_score"] != r["v2_score"] and r["lic_score"] is not None:
                print(f"    {r['task_id']}: LiC={r['lic_score']} V2={r['v2_score']}")

    if v2_mismatch_v1 > 0:
        print(f"\n  V1 vs V2: {v2_mismatch_v1} disagreements.")


if __name__ == "__main__":
    main()
