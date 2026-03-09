"""Parallel execution runner."""

import asyncio
import traceback
from typing import Any, Callable, Optional

from ..core.types import SimulationResult
from ..memory.base import MemoryModule
from ..utils.logging import get_logger
from .runner import ExperimentRunner


class ParallelRunner(ExperimentRunner):
    """Run problems in parallel with a frozen memory module.

    This runner executes multiple simulations concurrently using asyncio,
    with a semaphore to limit the maximum number of concurrent executions.
    """

    def __init__(
        self,
        max_concurrent: int = 10,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        on_result: Optional[Callable[[SimulationResult], None]] = None,
    ):
        """Initialize the parallel runner.

        Args:
            max_concurrent: Maximum number of concurrent simulations.
            progress_callback: Optional callback(completed, total) for progress updates.
            on_result: Optional callback(result) called after each result completes.
        """
        self.max_concurrent = max_concurrent
        self.progress_callback = progress_callback
        self.on_result = on_result
        self.logger = get_logger("parallel_runner")

    async def run(
        self,
        problems: list[dict[str, Any]],
        simulator_factory: Callable,
        memory: Optional[MemoryModule] = None,
    ) -> list[SimulationResult]:
        """Run all problems in parallel.

        Args:
            problems: List of problem samples.
            simulator_factory: Factory that creates simulator for a problem.
                Signature: simulator_factory(problem, memory=None) -> ConversationSimulator
            memory: Optional frozen memory module (same for all problems).

        Returns:
            List of results in the same order as problems.
        """
        semaphore = asyncio.Semaphore(self.max_concurrent)
        completed = 0
        total = len(problems)

        async def run_one(problem: dict, index: int) -> tuple[int, SimulationResult]:
            """Run a single problem with semaphore control."""
            nonlocal completed

            async with semaphore:
                try:
                    # Clone memory if provided to avoid any shared state issues
                    mem = memory.clone() if memory else None

                    # Create and run simulator
                    simulator = simulator_factory(problem, memory=mem)
                    result = await simulator.run()

                    completed += 1
                    if self.on_result:
                        self.on_result(result)
                    if self.progress_callback:
                        self.progress_callback(completed, total)

                    return index, result

                except Exception as e:
                    self.logger.error(
                        f"Error on problem {problem.get('task_id', 'unknown')}:\n{traceback.format_exc()}"
                    )
                    # Return a failed result
                    error_result = SimulationResult(
                        sample_id=problem.get("task_id", "unknown"),
                        task_name=problem.get("task", "unknown"),
                        is_correct=False,
                        score=0.0,
                        num_turns=0,
                        total_cost_usd=0.0,
                        trace=[],
                        metadata={
                            "error": str(e),
                            "traceback": traceback.format_exc(),
                        },
                    )
                    completed += 1
                    if self.on_result:
                        self.on_result(error_result)
                    if self.progress_callback:
                        self.progress_callback(completed, total)

                    return index, error_result

        # Run all problems concurrently
        tasks = [run_one(problem, i) for i, problem in enumerate(problems)]
        indexed_results = await asyncio.gather(*tasks)

        # Sort by original index to maintain order
        indexed_results.sort(key=lambda x: x[0])
        results = [r for _, r in indexed_results]

        return results
