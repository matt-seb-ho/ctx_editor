#!/usr/bin/env python3
"""Prepare LiveCodeBench hard problems for the sharding pipeline.

Downloads the LCB hard problems from HuggingFace and converts them into
the input format expected by shard_instructions.py.

Usage:
    python scripts/prep_lcb_hard.py -o data/lcb_hard_input.json
    python scripts/prep_lcb_hard.py -o data/lcb_hard_input.json --limit 10
"""

import argparse
import json
import random
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Prepare LCB hard problems for sharding")
    parser.add_argument("-o", "--output", type=Path, required=True, help="Output JSON file")
    parser.add_argument("--limit", type=int, help="Limit number of problems")
    parser.add_argument(
        "--sample",
        type=int,
        help="Randomly sample this many problems (after platform filtering)",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for sampling (default: 42)")
    parser.add_argument(
        "--platforms",
        nargs="+",
        default=["leetcode"],
        help="Platforms to include (default: leetcode only, to match LiC LCB split)",
    )
    args = parser.parse_args()

    from datasets import load_dataset

    print("Loading LiveCodeBench dataset...")
    lcb = load_dataset(
        "livecodebench/code_generation_lite",
        version_tag="release_v6",
        trust_remote_code=True,
    )
    ds = lcb["test"]

    # Filter hard problems
    hard_items = []
    for i in range(len(ds)):
        item = ds[i]
        if item["difficulty"] == "hard" and item["platform"] in args.platforms:
            hard_items.append(item)

    print(f"Found {len(hard_items)} hard problems across platforms: {args.platforms}")

    if args.sample and args.sample < len(hard_items):
        random.seed(args.seed)
        hard_items = random.sample(hard_items, args.sample)
        print(f"Randomly sampled {len(hard_items)} problems (seed={args.seed})")

    if args.limit:
        hard_items = hard_items[: args.limit]
        print(f"Limited to {len(hard_items)} problems")

    # Convert to shard_instructions input format
    # shard_instructions expects: {"question": str, "question_id": str, ...}
    output_items = []
    for item in hard_items:
        output_items.append(
            {
                "question_id": item["question_id"],
                "question": item["question_content"],
                "question_title": item["question_title"],
                "platform": item["platform"],
                "contest_id": item["contest_id"],
                "contest_date": item["contest_date"],
                "starter_code": item["starter_code"],
                "difficulty": item["difficulty"],
                "public_test_cases": item["public_test_cases"],
                "private_test_cases": item["private_test_cases"],
                "metadata": item["metadata"],
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(output_items, f, indent=2)

    print(f"Wrote {len(output_items)} problems to {args.output}")


if __name__ == "__main__":
    main()
