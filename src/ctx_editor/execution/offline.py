"""Offline memory learning from pre-existing trajectories."""

import json
from pathlib import Path
from typing import Any, Iterator, Optional

from ..core.types import SimulationResult
from ..memory.base import MemoryModule, MemoryUpdater
from ..memory.cheatsheet import CheatsheetMemory
from ..models.base import ModelClient
from ..utils.logging import get_logger


def _batches(items: list[Any], batch_size: int) -> Iterator[list[Any]]:
    """Split items into batches."""
    for i in range(0, len(items), batch_size):
        yield items[i : i + batch_size]


def load_trajectories(path: str) -> list[SimulationResult]:
    """Load trajectories from saved results on disk.

    Supports:
    - A single JSON file containing a list of result dicts
    - A JSONL file with one result dict per line
    - A directory containing individual JSON result files

    Args:
        path: Path to results file or directory.

    Returns:
        List of SimulationResult objects.
    """
    p = Path(path)

    if p.is_dir():
        # Load all JSON files in the directory
        raw_results = []
        for f in sorted(p.glob("*.json")):
            with open(f, "r") as fh:
                data = json.load(fh)
                if isinstance(data, list):
                    raw_results.extend(data)
                else:
                    raw_results.append(data)
    elif p.suffix == ".jsonl":
        raw_results = []
        with open(p, "r") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    raw_results.append(json.loads(line))
    else:
        with open(p, "r") as fh:
            data = json.load(fh)
            raw_results = data if isinstance(data, list) else [data]

    # Convert dicts to SimulationResult objects
    trajectories = []
    for r in raw_results:
        # Skip error results
        if "error" in r.get("metadata", {}):
            continue
        trajectories.append(
            SimulationResult(
                sample_id=r.get("sample_id", "unknown"),
                task_name=r.get("task_name", "unknown"),
                is_correct=r.get("is_correct", False),
                score=r.get("score", 0.0),
                num_turns=r.get("num_turns", 0),
                total_cost_usd=r.get("total_cost_usd", 0.0),
                trace=r.get("trace", {"messages": [], "logs": [], "num_resets": 0}),
                extracted_answer=r.get("extracted_answer"),
                metadata=r.get("metadata", {}),
            )
        )

    return trajectories


class OfflineMemoryLearner:
    """Learn memory from pre-existing trajectories without running new simulations.

    Uses the Reflect-then-Unify batch update approach: trajectories are processed
    in batches, with parallel per-trajectory reflection followed by a unification
    step that integrates takeaways into the memory.
    """

    def __init__(
        self,
        updater: MemoryUpdater,
        model_client: ModelClient,
    ):
        self.updater = updater
        self.model_client = model_client
        self.logger = get_logger("offline_learner")

    async def learn(
        self,
        trajectories: list[SimulationResult],
        memory: Optional[MemoryModule] = None,
        batch_size: int = 5,
        save_path: Optional[str] = None,
    ) -> MemoryModule:
        """Run memory updates over saved trajectories.

        Processes trajectories in batches using Reflect-then-Unify.

        Args:
            trajectories: Pre-existing simulation results to learn from.
            memory: Starting memory module. If None, starts from empty.
            batch_size: Number of trajectories per batch.
            save_path: If provided, save memory checkpoint after each batch.

        Returns:
            The updated memory module.
        """
        if memory is None:
            memory = CheatsheetMemory()

        total = len(trajectories)
        batches = list(_batches(trajectories, batch_size))
        self.logger.info(
            f"Offline learning: {total} trajectories in {len(batches)} batches "
            f"(batch_size={batch_size})"
        )

        for batch_num, batch in enumerate(batches, 1):
            self.logger.info(
                f"Processing batch {batch_num}/{len(batches)} "
                f"({len(batch)} trajectories, memory v{memory.version})"
            )

            memory = await self.updater.batch_update(
                memory=memory,
                trajectories=batch,
                model_client=self.model_client,
            )

            self.logger.info(f"Updated memory to v{memory.version}")

            if save_path:
                checkpoint_path = f"{save_path}.batch{batch_num}"
                memory.save(checkpoint_path)
                self.logger.info(f"Saved checkpoint: {checkpoint_path}")

        # Save final memory
        if save_path:
            memory.save(save_path)
            self.logger.info(f"Saved final memory: {save_path}")

        return memory
