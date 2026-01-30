#!/usr/bin/env python3
"""Migrate old output directory structure to new format and rebuild ledger.

Old format: outputs/{strategy}_{model}_{task}/{YYYY-MM-DD_HH-MM-SS}/
New format: outputs/{YYYY-MM-DD}/{HH-MM-SS}/

This script:
1. Moves runs from old format directories to new format
2. Rebuilds the ledger from all existing runs (both formats)
3. Optionally removes empty old-format directories

Usage:
    python scripts/migrate_outputs.py [--dry-run] [--no-cleanup]
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Optional

import yaml

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ctx_editor.utils.ledger import add_run, get_ledger_path


def parse_old_format_name(dirname: str) -> Optional[dict]:
    """Parse strategy_model_task from old format directory name.

    Examples:
        'baseline_gpt-5-mini_all' -> {'strategy': 'baseline', 'model': 'gpt-5-mini', 'task': 'all'}
        'context_edit_gpt-5-mini_math' -> {'strategy': 'context_edit', 'model': 'gpt-5-mini', 'task': 'math'}
    """
    # Known strategies (order matters - longer matches first)
    strategies = [
        "agentic_edit",
        "context_edit",
        "reflection_only",
        "reflection",
        "baseline",
    ]

    for strategy in strategies:
        if dirname.startswith(strategy + "_"):
            remainder = dirname[len(strategy) + 1:]  # Remove strategy_ prefix
            # Split on last underscore to get task
            if "_" in remainder:
                last_underscore = remainder.rfind("_")
                model = remainder[:last_underscore]
                task = remainder[last_underscore + 1:]
                return {"strategy": strategy, "model": model, "task": task}

    return None


def parse_timestamp_dir(dirname: str) -> Optional[tuple]:
    """Parse date and time from timestamp directory name.

    Handles both:
        '2026-01-29_09-00-12' (old format) -> ('2026-01-29', '09-00-12')
        '09-00-12' (new format, already just time) -> (None, '09-00-12')
    """
    # Old format: YYYY-MM-DD_HH-MM-SS
    old_pattern = re.compile(r'^(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{2})$')
    match = old_pattern.match(dirname)
    if match:
        return match.group(1), match.group(2)

    # New format: just HH-MM-SS (date is parent dir)
    new_pattern = re.compile(r'^(\d{2}-\d{2}-\d{2})$')
    if new_pattern.match(dirname):
        return None, dirname

    return None


def is_valid_run_dir(path: Path) -> bool:
    """Check if a directory contains a valid run (has config.yaml or metrics.json)."""
    return (path / "config.yaml").exists() or (path / "metrics.json").exists()


def is_date_dir(dirname: str) -> bool:
    """Check if directory name is a date (YYYY-MM-DD)."""
    return bool(re.match(r'^\d{4}-\d{2}-\d{2}$', dirname))


def extract_run_metadata(run_dir: Path) -> dict:
    """Extract metadata from a run directory."""
    metadata = {
        "samples": None,
        "accuracy": None,
        "total_cost_usd": None,
        "average_turns": None,
        "strategy": None,
        "model": None,
        "task": None,
    }

    # Try metrics.json first
    metrics_path = run_dir / "metrics.json"
    if metrics_path.exists():
        with open(metrics_path) as f:
            metrics = json.load(f)
            metadata["samples"] = metrics.get("total_samples")
            metadata["accuracy"] = metrics.get("accuracy")
            metadata["total_cost_usd"] = metrics.get("total_cost_usd")
            metadata["average_turns"] = metrics.get("average_turns")

            # Parse experiment_name for strategy/model/task
            exp_name = metrics.get("experiment_name", "")
            parsed = parse_old_format_name(exp_name)
            if parsed:
                metadata.update(parsed)

    # Try config.yaml for more accurate strategy/model/task
    config_path = run_dir / "config.yaml"
    if config_path.exists():
        with open(config_path) as f:
            config = yaml.safe_load(f)
            if config:
                if "experiment" in config and "name" in config["experiment"]:
                    metadata["strategy"] = config["experiment"]["name"]
                if "model" in config and "name" in config["model"]:
                    metadata["model"] = config["model"]["name"]
                if "task" in config and "name" in config["task"]:
                    metadata["task"] = config["task"]["name"]

    return metadata


def find_all_runs(outputs_dir: Path) -> list[dict]:
    """Find all runs in both old and new format directories."""
    runs = []

    for item in outputs_dir.iterdir():
        if not item.is_dir() or item.name.startswith("."):
            continue

        # Check if it's a date directory (new format)
        if is_date_dir(item.name):
            date_dir = item
            for time_dir in date_dir.iterdir():
                if time_dir.is_dir() and is_valid_run_dir(time_dir):
                    runs.append({
                        "path": time_dir,
                        "format": "new",
                        "date": date_dir.name,
                        "time": time_dir.name,
                        "run_path": f"{date_dir.name}/{time_dir.name}",
                    })

        # Check if it's an old format directory (strategy_model_task)
        elif parse_old_format_name(item.name):
            parsed = parse_old_format_name(item.name)
            for timestamp_dir in item.iterdir():
                if timestamp_dir.is_dir():
                    ts_parsed = parse_timestamp_dir(timestamp_dir.name)
                    if ts_parsed and is_valid_run_dir(timestamp_dir):
                        date, time = ts_parsed
                        runs.append({
                            "path": timestamp_dir,
                            "format": "old",
                            "date": date,
                            "time": time,
                            "run_path": f"{date}/{time}",
                            "old_parent": item,
                            **parsed,
                        })

    return runs


def migrate_run(run: dict, outputs_dir: Path, dry_run: bool = False) -> Optional[Path]:
    """Migrate a run from old format to new format.

    If target exists, merges contents (old format files take precedence for conflicts).
    Returns the new path if migrated, None if already in new format.
    """
    if run["format"] == "new":
        return None

    old_path = run["path"]
    new_date_dir = outputs_dir / run["date"]
    new_path = new_date_dir / run["time"]

    if dry_run:
        if new_path.exists():
            print(f"  Would merge: {old_path.relative_to(outputs_dir)} -> {new_path.relative_to(outputs_dir)}")
        else:
            print(f"  Would move: {old_path.relative_to(outputs_dir)} -> {new_path.relative_to(outputs_dir)}")
        return new_path

    # Create date directory if needed
    new_date_dir.mkdir(parents=True, exist_ok=True)

    if new_path.exists():
        # Merge: copy contents from old to new (old takes precedence)
        for item in old_path.iterdir():
            target = new_path / item.name
            if item.is_dir():
                if target.exists():
                    # Recursively merge directories
                    shutil.copytree(item, target, dirs_exist_ok=True)
                else:
                    shutil.copytree(item, target)
            else:
                # Copy file (overwrite if exists)
                shutil.copy2(item, target)
        # Remove old directory after successful merge
        shutil.rmtree(old_path)
        print(f"  Merged: {old_path.relative_to(outputs_dir)} -> {new_path.relative_to(outputs_dir)}")
    else:
        # Simple move
        shutil.move(str(old_path), str(new_path))
        print(f"  Moved: {old_path.relative_to(outputs_dir)} -> {new_path.relative_to(outputs_dir)}")

    return new_path


def cleanup_empty_dirs(outputs_dir: Path, dry_run: bool = False) -> list[Path]:
    """Remove empty old-format directories."""
    removed = []

    for item in outputs_dir.iterdir():
        if not item.is_dir() or item.name.startswith("."):
            continue

        # Only clean up old-format directories
        if parse_old_format_name(item.name):
            # Check if empty (no subdirectories with content)
            has_content = False
            for subdir in item.iterdir():
                if subdir.is_dir() and any(subdir.iterdir()):
                    has_content = True
                    break

            if not has_content:
                if dry_run:
                    print(f"  Would remove empty directory: {item.name}")
                else:
                    shutil.rmtree(item)
                    print(f"  Removed empty directory: {item.name}")
                removed.append(item)

    return removed


def rebuild_ledger(outputs_dir: Path, dry_run: bool = False) -> int:
    """Rebuild the ledger from all existing runs."""
    runs = find_all_runs(outputs_dir)
    count = 0

    # Clear existing ledger
    ledger_path = get_ledger_path(outputs_dir)
    if not dry_run and ledger_path.exists():
        ledger_path.unlink()

    for run in sorted(runs, key=lambda r: r["run_path"]):
        metadata = extract_run_metadata(run["path"])

        # Use metadata from run dict if not in files
        strategy = metadata["strategy"] or run.get("strategy", "unknown")
        model = metadata["model"] or run.get("model", "unknown")
        task = metadata["task"] or run.get("task", "unknown")

        if dry_run:
            print(f"  Would add to ledger: {run['run_path']} ({strategy}, {model}, {task})")
        else:
            add_run(
                outputs_dir=outputs_dir,
                run_path=run["run_path"],
                strategy=strategy,
                model=model,
                task=task,
                status="completed",
                samples=metadata["samples"],
                accuracy=metadata["accuracy"],
                total_cost_usd=metadata["total_cost_usd"],
                average_turns=metadata["average_turns"],
            )
        count += 1

    return count


def main():
    parser = argparse.ArgumentParser(description="Migrate outputs to new format and rebuild ledger")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    parser.add_argument("--no-cleanup", action="store_true", help="Don't remove empty old-format directories")
    parser.add_argument("--outputs-dir", type=Path, default=None, help="Path to outputs directory")
    args = parser.parse_args()

    # Find outputs directory
    if args.outputs_dir:
        outputs_dir = args.outputs_dir
    else:
        # Try to find it relative to script location
        script_dir = Path(__file__).parent
        outputs_dir = script_dir.parent / "outputs"

    if not outputs_dir.exists():
        print(f"ERROR: Outputs directory not found: {outputs_dir}")
        sys.exit(1)

    print(f"Outputs directory: {outputs_dir}")
    if args.dry_run:
        print("DRY RUN - no changes will be made\n")

    # Step 1: Find all runs
    print("Finding all runs...")
    runs = find_all_runs(outputs_dir)
    old_format_runs = [r for r in runs if r["format"] == "old"]
    new_format_runs = [r for r in runs if r["format"] == "new"]
    print(f"  Found {len(old_format_runs)} runs in old format")
    print(f"  Found {len(new_format_runs)} runs in new format")

    # Step 2: Migrate old format runs
    if old_format_runs:
        print("\nMigrating old format runs...")
        for run in old_format_runs:
            migrate_run(run, outputs_dir, args.dry_run)

    # Step 3: Clean up empty directories
    if not args.no_cleanup and old_format_runs:
        print("\nCleaning up empty directories...")
        cleanup_empty_dirs(outputs_dir, args.dry_run)

    # Step 4: Rebuild ledger
    print("\nRebuilding ledger...")
    count = rebuild_ledger(outputs_dir, args.dry_run)
    print(f"  Added {count} runs to ledger")

    if not args.dry_run:
        print(f"\nLedger saved to: {get_ledger_path(outputs_dir)}")

    print("\nDone!")


if __name__ == "__main__":
    main()
