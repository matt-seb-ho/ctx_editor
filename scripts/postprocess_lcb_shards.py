#!/usr/bin/env python3
"""Post-process sharded LCB problems into the experiment-ready format.

Takes the output of shard_instructions.py (run with --task code) and produces
a JSON file compatible with run_experiment.py and src/lic/run_simulations.py.

The output format matches data/original_lcb_subset.json.

Usage:
    python scripts/postprocess_lcb_shards.py data/lcb_hard_sharded.json -o data/lcb_hard_subset.json
"""

import argparse
import json
from pathlib import Path


def postprocess_item(item: dict) -> dict:
    """Convert a shard_instructions output item to experiment format."""
    question_id = item.get("question_id", item.get("task_id", ""))
    # Strip any existing prefix
    if question_id.startswith("sharded-"):
        clean_id = question_id[len("sharded-"):]
    elif question_id.startswith("livecodebench/"):
        clean_id = question_id
    else:
        clean_id = question_id

    task_id = f"sharded-livecodebench/{clean_id}"

    metadata = item.get("metadata", {})
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except json.JSONDecodeError:
            print(f"Warning: metadata for {question_id} is a string but not valid JSON, using empty dict instead")
            metadata = {}
    if len(metadata) == 0:
        print(f"Warning: metadata for {question_id} is empty")

    output = {
        "question_title": item.get("question_title", ""),
        "question_content": item.get("question_content", item.get("question", "")),
        "platform": item.get("platform", ""),
        "question_id": clean_id,
        "contest_id": item.get("contest_id", ""),
        "contest_date": item.get("contest_date", ""),
        "starter_code": item.get("starter_code", ""),
        "difficulty": item.get("difficulty", "hard"),
        "public_test_cases": item.get("public_test_cases", "[]"),
        "private_test_cases": item.get("private_test_cases", ""),
        # "metadata": item.get("metadata", {}),
        "metadata": metadata,
        "task_id": task_id,
        "source": f"lcb_{item.get('difficulty', 'hard')}",
        "shards": item["shards"],
        "task": "code",
    }

    return output


def main():
    parser = argparse.ArgumentParser(
        description="Post-process sharded LCB problems into experiment format"
    )
    parser.add_argument("input", type=Path, help="Input JSON from shard_instructions.py")
    parser.add_argument("-o", "--output", type=Path, required=True, help="Output JSON file")
    parser.add_argument("--max_shards", type=int, help="Filter out items with more than this many shards")
    args = parser.parse_args()

    with open(args.input) as f:
        items = json.load(f)

    results = []
    for item in items:
        if args.max_shards is not None and len(item.get("shards", [])) > args.max_shards:
            print(f"Skipping {item.get('question_id', item.get('task_id', 'unknown'))} with {len(item.get('shards', []))} shards (exceeds max_shards={args.max_shards})")
            continue
        results.append(postprocess_item(item))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Processed {len(results)} items -> {args.output}")

    # Summary
    from collections import Counter

    platforms = Counter(r["platform"] for r in results)
    print(f"Platforms: {dict(platforms)}")
    shard_counts = [len(r["shards"]) for r in results]
    print(f"Shards per item: min={min(shard_counts)}, max={max(shard_counts)}, avg={sum(shard_counts)/len(shard_counts):.1f}")


if __name__ == "__main__":
    main()
