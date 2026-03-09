"""Base experiment runner interface."""

from abc import ABC, abstractmethod
from typing import Any, Callable, Optional

from ..core.types import SimulationResult
from ..memory.base import MemoryModule


class ExperimentRunner(ABC):
    """Abstract base class for experiment runners."""

    @abstractmethod
    async def run(
        self,
        problems: list[dict[str, Any]],
        simulator_factory: Callable,
        memory: Optional[MemoryModule] = None,
    ) -> list[SimulationResult]:
        """Run the experiment on a list of problems.

        Args:
            problems: List of problem samples to run.
            simulator_factory: Factory function that creates a simulator for a problem.
            memory: Optional memory module for continual learning.

        Returns:
            List of simulation results.
        """
        pass
