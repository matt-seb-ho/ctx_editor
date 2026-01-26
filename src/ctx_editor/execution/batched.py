"""Batched execution runner for continual learning."""

import asyncio
from typing import Any, Callable, Iterator, Optional

from .runner import ExperimentRunner
from .parallel import ParallelRunner
from ..core.types import SimulationResult
from ..cheatsheet.cheatsheet import Cheatsheet
from ..cheatsheet.updater import CheatsheetUpdater
from ..models.base import ModelClient
from ..utils.logging import get_logger


class BatchedRunner(ExperimentRunner):
    """Run problems in batches for continual learning.

    This runner processes problems in batches, updating the cheatsheet
    after each batch. Within a batch, problems run in parallel with
    a frozen cheatsheet.
    """

    def __init__(
        self,
        batch_size: int = 5,
        max_concurrent: int = 10,
        model_client: Optional[ModelClient] = None,
        updater: Optional[CheatsheetUpdater] = None,
        save_cheatsheet_path: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ):
        """Initialize the batched runner.

        Args:
            batch_size: Number of problems per batch.
            max_concurrent: Max concurrent problems within a batch.
            model_client: Model client for cheatsheet updates.
            updater: CheatsheetUpdater instance.
            save_cheatsheet_path: Path to save cheatsheet after each batch.
            progress_callback: Optional callback(completed, total) for progress updates.
        """
        self.batch_size = batch_size
        self.max_concurrent = max_concurrent
        self.model_client = model_client
        self.updater = updater or CheatsheetUpdater()
        self.save_cheatsheet_path = save_cheatsheet_path
        self.progress_callback = progress_callback
        self.logger = get_logger("batched_runner")

        self.parallel_runner = ParallelRunner(max_concurrent=max_concurrent)

    def _batches(
        self,
        items: list[Any],
        batch_size: int,
    ) -> Iterator[list[Any]]:
        """Split items into batches.

        Args:
            items: List of items to batch.
            batch_size: Size of each batch.

        Yields:
            Batches of items.
        """
        for i in range(0, len(items), batch_size):
            yield items[i:i + batch_size]

    async def run(
        self,
        problems: list[dict[str, Any]],
        simulator_factory: Callable,
        cheatsheet: Optional[Cheatsheet] = None,
    ) -> list[SimulationResult]:
        """Run problems in batches with cheatsheet updates.

        Args:
            problems: List of problem samples.
            simulator_factory: Factory that creates simulator for a problem.
            cheatsheet: Cheatsheet to update (will be modified in place).

        Returns:
            List of all results.
        """
        if cheatsheet is None:
            cheatsheet = Cheatsheet()

        all_results = []
        batches = list(self._batches(problems, self.batch_size))
        total_batches = len(batches)

        self.logger.info(
            f"Running {len(problems)} problems in {total_batches} batches "
            f"(batch_size={self.batch_size})"
        )

        for batch_num, batch in enumerate(batches, 1):
            self.logger.info(
                f"Starting batch {batch_num}/{total_batches} "
                f"(cheatsheet v{cheatsheet.version})"
            )

            # Run batch with current cheatsheet (frozen for this batch)
            batch_results = await self.parallel_runner.run(
                problems=batch,
                simulator_factory=simulator_factory,
                cheatsheet=cheatsheet,
            )
            all_results.extend(batch_results)

            # Update cheatsheet from batch results
            if self.model_client:
                cheatsheet = await self.updater.batch_update(
                    cheatsheet=cheatsheet,
                    trajectories=batch_results,
                    model_client=self.model_client,
                )
                self.logger.info(f"Updated cheatsheet to v{cheatsheet.version}")

            # Save checkpoint
            if self.save_cheatsheet_path:
                checkpoint_path = f"{self.save_cheatsheet_path}.batch{batch_num}"
                cheatsheet.save(checkpoint_path)
                self.logger.info(f"Saved cheatsheet checkpoint: {checkpoint_path}")

            # Progress callback
            if self.progress_callback:
                self.progress_callback(len(all_results), len(problems))

            # Log batch summary
            batch_scores = [r.score for r in batch_results]
            avg_score = sum(batch_scores) / len(batch_scores) if batch_scores else 0
            self.logger.info(
                f"Batch {batch_num} complete: avg_score={avg_score:.3f}, "
                f"correct={sum(1 for r in batch_results if r.is_correct)}/{len(batch_results)}"
            )

        # Save final cheatsheet
        if self.save_cheatsheet_path:
            cheatsheet.save(self.save_cheatsheet_path)
            self.logger.info(f"Saved final cheatsheet: {self.save_cheatsheet_path}")

        return all_results

    async def run_sequential(
        self,
        problems: list[dict[str, Any]],
        simulator_factory: Callable,
        cheatsheet: Optional[Cheatsheet] = None,
    ) -> list[SimulationResult]:
        """Run problems sequentially, updating cheatsheet after each.

        This is useful for maximum learning but is slower.

        Args:
            problems: List of problem samples.
            simulator_factory: Factory that creates simulator.
            cheatsheet: Cheatsheet to update.

        Returns:
            List of all results.
        """
        if cheatsheet is None:
            cheatsheet = Cheatsheet()

        results = []

        for i, problem in enumerate(problems, 1):
            self.logger.info(
                f"Running problem {i}/{len(problems)}: {problem.get('task_id', 'unknown')} "
                f"(cheatsheet v{cheatsheet.version})"
            )

            try:
                simulator = simulator_factory(problem, cheatsheet=cheatsheet.clone())
                result = await simulator.run()
                results.append(result)

                # Progress callback
                if self.progress_callback:
                    self.progress_callback(len(results), len(problems))

                # Update cheatsheet after each problem
                if self.model_client:
                    cheatsheet = await self.updater.update_from_trajectory(
                        cheatsheet=cheatsheet,
                        trajectory=result,
                        model_client=self.model_client,
                    )

            except Exception as e:
                self.logger.error(f"Error on problem {problem.get('task_id')}: {e}")
                results.append(SimulationResult(
                    sample_id=problem.get("task_id", "unknown"),
                    task_name=problem.get("task", "unknown"),
                    is_correct=False,
                    score=0.0,
                    num_turns=0,
                    total_cost_usd=0.0,
                    trace=[],
                    metadata={"error": str(e)},
                ))
                # Progress callback even on error
                if self.progress_callback:
                    self.progress_callback(len(results), len(problems))

        return results
