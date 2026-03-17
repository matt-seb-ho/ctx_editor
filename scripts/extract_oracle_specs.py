#!/usr/bin/env python3
"""Extract oracle hard-attention task specs from S1 traces.

Reads conversation_analysis logs from S1 hard-attention traces and extracts
the user_intent (task spec) for each sample. Outputs JSON mapping:
  { sample_id: oracle_spec_text }

These oracle specs serve as training targets for spec-curation memory learning.

Usage:
    python scripts/extract_oracle_specs.py

    # Or specify custom source dirs:
    python scripts/extract_oracle_specs.py \
        --math-dir outputs/2026-03-17/04-47-34/traces/math/append_analysis_spec_only \
        --code-dir outputs/2026-03-17/04-47-34/traces/code/append_analysis_spec_only \
        --database-dir outputs/2026-03-17/04-47-34/traces/database/append_analysis_spec_only
"""

import argparse
import json
from pathlib import Path

# Default: S1-speconly traces (1q hard attention) — cleanest specs
DEFAULT_DIRS = {
    "math": "outputs/2026-03-17/04-47-34/traces/math/append_analysis_spec_only",
    "code": "outputs/2026-03-17/04-47-34/traces/code/append_analysis_spec_only",
    "database": "outputs/2026-03-17/04-47-34/traces/database/append_analysis_spec_only",
}

OUTPUT_DIR = Path("data/oracle_specs")


def extract_specs_from_dir(trace_dir: Path) -> dict[str, str]:
    """Extract oracle specs from all trace files in a directory."""
    specs = {}
    for trace_file in sorted(trace_dir.glob("*.json")):
        data = json.loads(trace_file.read_text())
        sample_id = data["sample_id"]

        # Find the last conversation_analysis log (most complete spec)
        analysis_logs = [
            log for log in data["trace"]["logs"]
            if log["type"] == "conversation_analysis"
        ]

        if not analysis_logs:
            print(f"  Warning: no analysis log in {trace_file.name}")
            continue

        # Use the last analysis (after all shards revealed)
        last_analysis = analysis_logs[-1]
        user_intent = last_analysis["data"].get("user_intent", "")

        if not user_intent:
            print(f"  Warning: empty user_intent in {trace_file.name}")
            continue

        specs[sample_id] = user_intent

    return specs


def main():
    parser = argparse.ArgumentParser(description="Extract oracle task specs from hard-attention traces")
    parser.add_argument("--math-dir", default=DEFAULT_DIRS["math"])
    parser.add_argument("--code-dir", default=DEFAULT_DIRS["code"])
    parser.add_argument("--database-dir", default=DEFAULT_DIRS["database"])
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    all_specs = {}

    for task_name, dir_path in [("math", args.math_dir), ("code", args.code_dir), ("database", args.database_dir)]:
        trace_dir = Path(dir_path)
        if not trace_dir.exists():
            print(f"Warning: {trace_dir} not found, skipping {task_name}")
            continue

        print(f"Extracting {task_name} specs from {trace_dir}...")
        specs = extract_specs_from_dir(trace_dir)
        print(f"  Extracted {len(specs)} specs")

        # Save per-task file
        task_file = output_dir / f"{task_name}_oracle_specs.json"
        task_file.write_text(json.dumps(specs, indent=2))
        print(f"  Saved to {task_file}")

        all_specs.update(specs)

    # Save combined file
    combined_file = output_dir / "all_oracle_specs.json"
    combined_file.write_text(json.dumps(all_specs, indent=2))
    print(f"\nCombined: {len(all_specs)} specs → {combined_file}")


if __name__ == "__main__":
    main()
