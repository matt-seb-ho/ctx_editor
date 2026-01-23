"""Structured logging utilities."""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


def setup_logging(
    output_dir: Optional[str] = None,
    level: int = logging.INFO,
    log_file: str = "experiment.log",
) -> logging.Logger:
    """Set up logging with file and console handlers.

    Args:
        output_dir: Directory for log files. If None, only console logging.
        level: Logging level.
        log_file: Name of the log file.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger("ctx_editor")
    logger.setLevel(level)

    # Clear existing handlers
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(output_path / log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(console_format)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "ctx_editor") -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name.

    Returns:
        Logger instance.
    """
    return logging.getLogger(name)


def log_conversation(
    experiment_type: str,
    task_name: str,
    sample_id: str,
    trace: list[dict[str, Any]],
    is_correct: bool,
    score: float,
    output_dir: str,
    assistant_model: str = "unknown",
    user_model: str = "unknown",
    system_model: str = "unknown",
    metadata: Optional[dict[str, Any]] = None,
) -> str:
    """Log a conversation trace to a file.

    Args:
        experiment_type: Type of experiment (baseline, context_edit, etc.).
        task_name: Name of the task.
        sample_id: Sample identifier.
        trace: Conversation trace.
        is_correct: Whether the final answer was correct.
        score: Evaluation score.
        output_dir: Directory for output files.
        assistant_model: Model used for assistant.
        user_model: Model used for user simulation.
        system_model: Model used for system verification.
        metadata: Additional metadata to include.

    Returns:
        Path to the saved log file.
    """
    output_path = Path(output_dir)
    traces_dir = output_path / "traces" / task_name / experiment_type
    traces_dir.mkdir(parents=True, exist_ok=True)

    # Create log entry
    log_entry = {
        "sample_id": sample_id,
        "task_name": task_name,
        "experiment_type": experiment_type,
        "is_correct": is_correct,
        "score": score,
        "models": {
            "assistant": assistant_model,
            "user": user_model,
            "system": system_model,
        },
        "trace": trace,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    if metadata:
        log_entry["metadata"] = metadata

    # Save to file
    # Sanitize sample_id for filename
    safe_id = sample_id.replace("/", "_").replace("\\", "_")
    log_file = traces_dir / f"{safe_id}.json"

    with open(log_file, "w") as f:
        json.dump(log_entry, f, indent=2)

    return str(log_file)


def save_results(
    results: list[dict[str, Any]],
    output_dir: str,
    filename: str = "results.json",
) -> str:
    """Save experiment results to a JSON file.

    Args:
        results: List of result dictionaries.
        output_dir: Directory for output files.
        filename: Name of the results file.

    Returns:
        Path to the saved results file.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    results_file = output_path / filename
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)

    return str(results_file)


def save_metrics(
    metrics: dict[str, Any],
    output_dir: str,
    filename: str = "metrics.json",
) -> str:
    """Save experiment metrics to a JSON file.

    Args:
        metrics: Metrics dictionary.
        output_dir: Directory for output files.
        filename: Name of the metrics file.

    Returns:
        Path to the saved metrics file.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    metrics_file = output_path / filename
    with open(metrics_file, "w") as f:
        json.dump(metrics, f, indent=2)

    return str(metrics_file)
