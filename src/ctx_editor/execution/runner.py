"""Base experiment runner interface."""

from abc import ABC, abstractmethod
from typing import Any, Callable, Optional

from ..cheatsheet.cheatsheet import Cheatsheet
from ..core.types import SimulationResult


class ExperimentRunner(ABC):
    """Abstract base class for experiment runners."""

    @abstractmethod
    async def run(
        self,
        problems: list[dict[str, Any]],
        simulator_factory: Callable,
        cheatsheet: Optional[Cheatsheet] = None,
    ) -> list[SimulationResult]:
        """Run the experiment on a list of problems.

        Args:
            problems: List of problem samples to run.
            simulator_factory: Factory function that creates a simulator for a problem.
            cheatsheet: Optional cheatsheet for continual learning.

        Returns:
            List of simulation results.
        """
        pass
