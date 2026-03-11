"""Batched execution runner for continual learning."""

import asyncio
import traceback
from typing import Any, Callable, Iterator, Optional

from ..core.types import SimulationResult
from ..memory.base import MemoryModule, MemoryUpdater
from ..memory.cheatsheet import CheatsheetMemory, CheatsheetUpdater
from ..models.base import ModelClient
from ..utils.logging import get_logger
from .parallel import ParallelRunner
from .runner import ExperimentRunner


class BatchedRunner(ExperimentRunner):
    """Run problems in batches for continual learning.

    This runner processes problems in batches, updating the memory module
    after each batch. Within a batch, problems run in parallel with
    a frozen memory snapshot.
    """

    def __init__(
        self,
        batch_size: int = 5,
        max_concurrent: int = 10,
        model_client: Optional[ModelClient] = None,
        updater: Optional[MemoryUpdater] = None,
        save_memory_path: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        on_result: Optional[Callable[[SimulationResult], None]] = None,
    ):
        """Initialize the batched runner.

        Args:
            batch_size: Number of problems per batch.
            max_concurrent: Max concurrent problems within a batch.
            model_client: Model client for memory updates.
            updater: MemoryUpdater instance.
            save_memory_path: Path to save memory after each batch.
            progress_callback: Optional callback(completed, total) for progress updates.
            on_result: Optional callback(result) called after each result completes.
        """
        self.batch_size = batch_size
        self.max_concurrent = max_concurrent
        self.model_client = model_client
        self.updater = updater or CheatsheetUpdater()
        self.save_memory_path = save_memory_path
        self.progress_callback = progress_callback
        self.on_result = on_result
        self.logger = get_logger("batched_runner")

        self.parallel_runner = ParallelRunner(
            max_concurrent=max_concurrent, on_result=on_result
        )

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
            yield items[i : i + batch_size]

    async def run(
        self,
        problems: list[dict[str, Any]],
        simulator_factory: Callable,
        memory: Optional[MemoryModule] = None,
    ) -> list[SimulationResult]:
        """Run problems in batches with memory updates.

        Args:
            problems: List of problem samples.
            simulator_factory: Factory that creates simulator for a problem.
            memory: Memory module to update (will be modified in place).

        Returns:
            List of all results.
        """
        if memory is None:
            memory = CheatsheetMemory()

        all_results = []
        batches = list(self._batches(problems, self.batch_size))
        total_batches = len(batches)

        self.logger.info(
            f"Running {len(problems)} problems in {total_batches} batches "
            f"(batch_size={self.batch_size})"
        )

        for batch_num, batch in enumerate(batches, 1):
            self.logger.info(
                f"Starting batch {batch_num}/{total_batches} (memory v{memory.version})"
            )

            # Run batch with current memory (frozen for this batch)
            batch_results = await self.parallel_runner.run(
                problems=batch,
                simulator_factory=simulator_factory,
                memory=memory,
            )
            all_results.extend(batch_results)

            # Update memory from batch results (skip error results with no conversation)
            valid_results = [r for r in batch_results if not r.metadata.get("error")]
            if self.model_client and valid_results:
                memory = await self.updater.batch_update(
                    memory=memory,
                    trajectories=valid_results,
                    model_client=self.model_client,
                )
                self.logger.info(f"Updated memory to v{memory.version}")

            # Save checkpoint
            if self.save_memory_path:
                checkpoint_path = f"{self.save_memory_path}.batch{batch_num}"
                memory.save(checkpoint_path)
                self.logger.info(f"Saved memory checkpoint: {checkpoint_path}")

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

        # Save final memory
        if self.save_memory_path:
            memory.save(self.save_memory_path)
            self.logger.info(f"Saved final memory: {self.save_memory_path}")

        return all_results

    async def run_sequential(
        self,
        problems: list[dict[str, Any]],
        simulator_factory: Callable,
        memory: Optional[MemoryModule] = None,
    ) -> list[SimulationResult]:
        """Run problems sequentially, updating memory after each.

        This is useful for maximum learning but is slower.

        Args:
            problems: List of problem samples.
            simulator_factory: Factory that creates simulator.
            memory: Memory module to update.

        Returns:
            List of all results.
        """
        if memory is None:
            memory = CheatsheetMemory()

        results = []

        for i, problem in enumerate(problems, 1):
            self.logger.info(
                f"Running problem {i}/{len(problems)}: {problem.get('task_id', 'unknown')} "
                f"(memory v{memory.version})"
            )

            try:
                simulator = simulator_factory(problem, memory=memory.clone())
                result = await simulator.run()
                results.append(result)

                if self.on_result:
                    self.on_result(result)
                # Progress callback
                if self.progress_callback:
                    self.progress_callback(len(results), len(problems))

                # Update memory after each problem
                if self.model_client:
                    memory = await self.updater.update_from_trajectory(
                        memory=memory,
                        trajectory=result,
                        model_client=self.model_client,
                    )

            except Exception as e:
                self.logger.error(
                    f"Error on problem {problem.get('task_id')}:\n{traceback.format_exc()}"
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
                    },
                )
                results.append(error_result)
                if self.on_result:
                    self.on_result(error_result)
                # Progress callback even on error
                if self.progress_callback:
                    self.progress_callback(len(results), len(problems))

        return results
