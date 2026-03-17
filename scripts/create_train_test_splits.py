#!/usr/bin/env python3
"""Split dev subsets into train/test halves for memory learning experiments.

Creates deterministic splits (sorted by task_id, first half = train, second half = test).
Also splits corresponding baseline traces into separate directories.

Usage:
    python scripts/create_train_test_splits.py
"""

import json
import shutil
from pathlib import Path

DATA_DIR = Path("data")
TRACE_DIR = DATA_DIR / "baseline_traces_v2"

TASKS = {
    "math": {
        "data_file": "dev_math_subset.json",
        "trace_subdir": "math",
    },
    "code": {
        "data_file": "dev_code_subset.json",
        "trace_subdir": "code",
    },
    "database": {
        "data_file": "dev_database_subset.json",
        "trace_subdir": "database",
    },
}


def sample_id_to_filename(sample_id: str) -> str:
    """Convert sample_id like 'sharded-GSM8K/1166' to filename 'sharded-GSM8K_1166.json'."""
    return sample_id.replace("/", "_") + ".json"


def main():
    for task_name, task_info in TASKS.items():
        data_file = DATA_DIR / task_info["data_file"]
        samples = json.loads(data_file.read_text())

        # Sort by task_id for deterministic split
        samples.sort(key=lambda s: s["task_id"])

        mid = len(samples) // 2
        train_samples = samples[:mid]
        test_samples = samples[mid:]

        # Write train/test data files
        train_file = DATA_DIR / f"dev_{task_name}_train.json"
        test_file = DATA_DIR / f"dev_{task_name}_test.json"

        train_file.write_text(json.dumps(train_samples, indent=2))
        test_file.write_text(json.dumps(test_samples, indent=2))

        print(f"{task_name}: {len(samples)} total → {len(train_samples)} train, {len(test_samples)} test")
        print(f"  Train IDs: {[s['task_id'] for s in train_samples]}")
        print(f"  Test  IDs: {[s['task_id'] for s in test_samples]}")

        # Split baseline traces
        trace_src = TRACE_DIR / task_info["trace_subdir"]
        if not trace_src.exists():
            print(f"  Warning: trace dir {trace_src} not found, skipping trace split")
            continue

        for split_name, split_samples in [("train", train_samples), ("test", test_samples)]:
            trace_dst = TRACE_DIR / f"{task_info['trace_subdir']}_{split_name}"
            trace_dst.mkdir(exist_ok=True)

            for sample in split_samples:
                fname = sample_id_to_filename(sample["task_id"])
                src = trace_src / fname
                dst = trace_dst / fname
                if src.exists():
                    shutil.copy2(src, dst)
                else:
                    print(f"  Warning: trace {src} not found")

            print(f"  {split_name} traces → {trace_dst} ({len(list(trace_dst.glob('*.json')))} files)")

        print()


if __name__ == "__main__":
    main()
