"""Run ledger for tracking experiment outputs with atomic file locking."""

import fcntl
import os
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import yaml


LEDGER_FILENAME = "runs.yaml"


@contextmanager
def file_lock(filepath: Path, mode: str = "r+"):
    """Context manager for file locking with fcntl.

    Uses exclusive lock (LOCK_EX) for writes and shared lock (LOCK_SH) for reads.
    Creates the file if it doesn't exist when opening for write.
    """
    # Ensure parent directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # For write modes, create file if it doesn't exist
    if "w" in mode or "a" in mode or "+" in mode:
        if not filepath.exists():
            filepath.touch()

    lock_type = fcntl.LOCK_EX if ("w" in mode or "a" in mode or "+" in mode) else fcntl.LOCK_SH

    f = open(filepath, mode)
    try:
        fcntl.flock(f.fileno(), lock_type)
        yield f
    finally:
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        f.close()


def get_ledger_path(outputs_dir: Path) -> Path:
    """Get the path to the ledger file."""
    return outputs_dir / LEDGER_FILENAME


def load_ledger(outputs_dir: Path) -> dict[str, Any]:
    """Load the ledger from disk with file locking.

    Returns empty structure if ledger doesn't exist.
    """
    ledger_path = get_ledger_path(outputs_dir)

    if not ledger_path.exists():
        return {"runs": []}

    with file_lock(ledger_path, "r") as f:
        content = f.read()
        if not content.strip():
            return {"runs": []}
        return yaml.safe_load(content) or {"runs": []}


def save_ledger(outputs_dir: Path, ledger: dict[str, Any]) -> None:
    """Save the ledger to disk with file locking."""
    ledger_path = get_ledger_path(outputs_dir)

    with file_lock(ledger_path, "w") as f:
        yaml.dump(ledger, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def add_run(
    outputs_dir: Path,
    run_path: str,
    strategy: str,
    model: str,
    task: str,
    status: str = "completed",
    samples: Optional[int] = None,
    accuracy: Optional[float] = None,
    total_cost_usd: Optional[float] = None,
    average_turns: Optional[float] = None,
    notes: str = "",
    extra: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Add a run entry to the ledger with atomic file locking.

    Args:
        outputs_dir: Path to the outputs directory containing the ledger.
        run_path: Relative path to the run directory (e.g., "2026-01-29/09-00-12").
        strategy: Strategy name (e.g., "baseline", "context_edit").
        model: Model name (e.g., "gpt-4o-mini", "claude-sonnet").
        task: Task name (e.g., "math", "all").
        status: Run status ("completed", "failed", "running").
        samples: Number of samples processed.
        accuracy: Accuracy metric (0.0 to 1.0).
        total_cost_usd: Total cost in USD.
        average_turns: Average number of turns per sample.
        notes: Optional notes about the run.
        extra: Additional metadata to store.

    Returns:
        The run entry that was added.
    """
    ledger_path = get_ledger_path(outputs_dir)

    # Build the run entry
    run_entry = {
        "path": run_path,
        "strategy": strategy,
        "model": model,
        "task": task,
        "status": status,
        "timestamp": datetime.now().isoformat(),
    }

    if samples is not None:
        run_entry["samples"] = samples
    if accuracy is not None:
        run_entry["accuracy"] = round(accuracy, 4)
    if total_cost_usd is not None:
        run_entry["total_cost_usd"] = round(total_cost_usd, 6)
    if average_turns is not None:
        run_entry["average_turns"] = round(average_turns, 2)
    if notes:
        run_entry["notes"] = notes
    if extra:
        run_entry.update(extra)

    # Atomic read-modify-write with file lock
    with file_lock(ledger_path, "r+") as f:
        content = f.read()
        if content.strip():
            ledger = yaml.safe_load(content) or {"runs": []}
        else:
            ledger = {"runs": []}

        # Check if run already exists (by path)
        existing_idx = None
        for i, run in enumerate(ledger["runs"]):
            if run.get("path") == run_path:
                existing_idx = i
                break

        if existing_idx is not None:
            # Update existing entry
            ledger["runs"][existing_idx] = run_entry
        else:
            # Append new entry
            ledger["runs"].append(run_entry)

        # Write back
        f.seek(0)
        f.truncate()
        yaml.dump(ledger, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    return run_entry


def update_run_status(
    outputs_dir: Path,
    run_path: str,
    status: str,
    **updates: Any,
) -> bool:
    """Update an existing run's status and other fields.

    Args:
        outputs_dir: Path to the outputs directory.
        run_path: Relative path to the run directory.
        status: New status value.
        **updates: Additional fields to update.

    Returns:
        True if the run was found and updated, False otherwise.
    """
    ledger_path = get_ledger_path(outputs_dir)

    if not ledger_path.exists():
        return False

    with file_lock(ledger_path, "r+") as f:
        content = f.read()
        if not content.strip():
            return False

        ledger = yaml.safe_load(content) or {"runs": []}

        # Find and update the run
        found = False
        for run in ledger["runs"]:
            if run.get("path") == run_path:
                run["status"] = status
                run.update(updates)
                found = True
                break

        if found:
            f.seek(0)
            f.truncate()
            yaml.dump(ledger, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

        return found


def get_run(outputs_dir: Path, run_path: str) -> Optional[dict[str, Any]]:
    """Get a specific run entry by path."""
    ledger = load_ledger(outputs_dir)

    for run in ledger.get("runs", []):
        if run.get("path") == run_path:
            return run

    return None


def list_runs(
    outputs_dir: Path,
    strategy: Optional[str] = None,
    model: Optional[str] = None,
    task: Optional[str] = None,
    status: Optional[str] = None,
) -> list[dict[str, Any]]:
    """List runs with optional filtering.

    Args:
        outputs_dir: Path to the outputs directory.
        strategy: Filter by strategy name.
        model: Filter by model name.
        task: Filter by task name.
        status: Filter by status.

    Returns:
        List of matching run entries.
    """
    ledger = load_ledger(outputs_dir)
    runs = ledger.get("runs", [])

    if strategy:
        runs = [r for r in runs if r.get("strategy") == strategy]
    if model:
        runs = [r for r in runs if r.get("model") == model]
    if task:
        runs = [r for r in runs if r.get("task") == task]
    if status:
        runs = [r for r in runs if r.get("status") == status]

    return runs
