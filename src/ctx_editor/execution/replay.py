"""Replay runner: re-evaluate context interventions on saved baseline traces.

Instead of re-simulating the full conversation, loads baseline traces and only
regenerates the final assistant turn with a new strategy applied. This is much
faster than full simulation and ensures the conversational prefix is identical
across strategies, enabling controlled comparison.
"""

import asyncio
import json
import traceback
from pathlib import Path
from typing import Any, Callable, Optional

from ..core.trace import ConversationTrace
from ..core.types import SimulationResult
from ..memory.base import MemoryModule
from ..utils.logging import get_logger


def load_baseline_traces(
    trace_source: str,
) -> dict[str, dict[str, Any]]:
    """Load baseline trace files from a directory or results file.

    Args:
        trace_source: Path to either:
            - A directory containing trace JSON files (e.g. outputs/2026-03-06/02-22-02/traces/math/baseline/)
            - A parent output directory (e.g. outputs/2026-03-06/02-22-02/) — will search traces/ recursively
            - A results.json or results_partial.jsonl file with embedded traces

    Returns:
        Dict mapping sample_id -> full trace file data (including 'trace', 'sample_id', etc.)
    """
    logger = get_logger("replay")
    source = Path(trace_source)
    traces = {}

    if source.is_file():
        # Load from results file
        if source.suffix == ".jsonl":
            with open(source) as f:
                for line in f:
                    if line.strip():
                        entry = json.loads(line)
                        if "trace" in entry:
                            traces[entry["sample_id"]] = entry
        else:
            with open(source) as f:
                data = json.load(f)
            if isinstance(data, list):
                for entry in data:
                    if "trace" in entry:
                        traces[entry["sample_id"]] = entry
            elif isinstance(data, dict) and "trace" in data:
                traces[data["sample_id"]] = data
    elif source.is_dir():
        # Find all trace JSON files recursively
        json_files = list(source.rglob("*.json"))
        for json_file in json_files:
            try:
                with open(json_file) as f:
                    data = json.load(f)
                if "trace" in data and "sample_id" in data:
                    traces[data["sample_id"]] = data
            except (json.JSONDecodeError, KeyError):
                continue

    logger.info(f"Loaded {len(traces)} baseline traces from {trace_source}")
    return traces


def build_replay_trace(
    trace_file_data: dict[str, Any],
    source_path: str,
) -> ConversationTrace:
    """Build a ConversationTrace for replay from saved trace data.

    Reconstructs the conversation up to and including the last user message,
    removing the final assistant response so it can be regenerated with a
    new strategy.

    Args:
        trace_file_data: The full saved trace file data (with 'trace', 'sample_id', etc.)
        source_path: Path to the source trace directory/file (for provenance).

    Returns:
        ConversationTrace ready for replay, with provenance metadata.
    """
    provenance = {
        "source_path": source_path,
        "source_experiment": trace_file_data.get("experiment_type", "unknown"),
        "source_sample_id": trace_file_data["sample_id"],
        "source_is_correct": trace_file_data.get("is_correct"),
        "source_score": trace_file_data.get("score"),
        "source_models": trace_file_data.get("models"),
        "source_timestamp": trace_file_data.get("timestamp"),
    }

    return ConversationTrace.from_saved_trace(
        trace_data=trace_file_data["trace"],
        truncate_final_assistant=True,
        provenance=provenance,
    )


class ReplayRunner:
    """Run context interventions on saved baseline traces.

    Only regenerates the final assistant turn — the conversational prefix
    (all user and assistant messages up to the last user message) comes
    from a previously saved baseline run.
    """

    def __init__(
        self,
        trace_source: str,
        max_concurrent: int = 10,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        on_result: Optional[Callable[[SimulationResult], None]] = None,
    ):
        """Initialize the replay runner.

        Args:
            trace_source: Path to baseline traces (directory or file).
            max_concurrent: Maximum concurrent replays.
            progress_callback: Optional callback(completed, total) for progress.
            on_result: Optional callback(result) after each result.
        """
        self.trace_source = trace_source
        self.max_concurrent = max_concurrent
        self.progress_callback = progress_callback
        self.on_result = on_result
        self.logger = get_logger("replay_runner")

    async def run(
        self,
        problems: list[dict[str, Any]],
        simulator_factory: Callable,
        memory: Optional[MemoryModule] = None,
    ) -> list[SimulationResult]:
        """Run replay on all problems that have matching baseline traces.

        Args:
            problems: List of problem samples. Each must have a 'task_id' field.
            simulator_factory: Factory that creates a simulator. Must accept
                a `trace` keyword argument for the pre-loaded trace.
            memory: Optional frozen memory module.

        Returns:
            List of SimulationResult in the same order as problems.
        """
        # Load baseline traces
        baseline_traces = load_baseline_traces(self.trace_source)

        # Match problems to traces
        matched = []
        skipped = []
        for problem in problems:
            sample_id = problem.get("task_id", "unknown")
            if sample_id in baseline_traces:
                matched.append((problem, baseline_traces[sample_id]))
            else:
                skipped.append(sample_id)

        if skipped:
            self.logger.warning(
                f"Skipped {len(skipped)} problems with no matching baseline trace: "
                f"{skipped[:5]}{'...' if len(skipped) > 5 else ''}"
            )
        self.logger.info(f"Replaying {len(matched)} problems (skipped {len(skipped)})")

        # Run replays
        semaphore = asyncio.Semaphore(self.max_concurrent)
        completed = 0
        total = len(matched)

        async def run_one(
            problem: dict, trace_data: dict, index: int
        ) -> tuple[int, SimulationResult]:
            nonlocal completed

            async with semaphore:
                try:
                    # Build replay trace
                    replay_trace = build_replay_trace(trace_data, self.trace_source)

                    # Clone memory if provided
                    mem = memory.clone() if memory else None

                    # Create simulator with pre-loaded trace
                    simulator = simulator_factory(problem, memory=mem, trace=replay_trace)

                    # Run the simulator — it detects replay mode via trace.provenance
                    # and only regenerates the final turn
                    result = await simulator.run()

                    completed += 1
                    if self.on_result:
                        self.on_result(result)
                    if self.progress_callback:
                        self.progress_callback(completed, total)

                    return index, result

                except Exception as e:
                    self.logger.error(
                        f"Replay error on {problem.get('task_id', 'unknown')}:\n"
                        f"{traceback.format_exc()}"
                    )
                    error_result = SimulationResult(
                        sample_id=problem.get("task_id", "unknown"),
                        task_name=problem.get("task", "unknown"),
                        is_correct=False,
                        score=0.0,
                        num_turns=0,
                        total_cost_usd=0.0,
                        trace={"messages": [], "logs": [], "num_resets": 0},
                        metadata={
                            "error": str(e),
                            "traceback": traceback.format_exc(),
                            "replay_mode": True,
                        },
                    )
                    completed += 1
                    if self.on_result:
                        self.on_result(error_result)
                    if self.progress_callback:
                        self.progress_callback(completed, total)

                    return index, error_result

        tasks = [run_one(problem, trace_data, i) for i, (problem, trace_data) in enumerate(matched)]
        indexed_results = await asyncio.gather(*tasks)
        indexed_results.sort(key=lambda x: x[0])

        return [r for _, r in indexed_results]
