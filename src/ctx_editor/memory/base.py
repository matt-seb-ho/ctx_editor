"""Abstract base classes for the memory system."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..core.types import SimulationResult
    from ..models.base import ModelClient


class MemoryModule(ABC):
    """Abstract base class for memory modules.

    A memory module stores learned knowledge that can be injected into
    conversation context to improve performance. Concrete implementations
    determine the format and structure of stored knowledge.
    """

    @property
    @abstractmethod
    def content(self) -> str:
        """The current memory content as a string for context injection."""
        ...

    @property
    @abstractmethod
    def version(self) -> int:
        """The current version number of the memory."""
        ...

    @abstractmethod
    def update(self, new_content: str) -> None:
        """Replace the memory content with new content."""
        ...

    @abstractmethod
    def clone(self) -> "MemoryModule":
        """Create a deep copy of this memory module."""
        ...

    @abstractmethod
    def save(self, filepath: str) -> None:
        """Persist the memory to disk."""
        ...

    @classmethod
    @abstractmethod
    def load(cls, filepath: str) -> "MemoryModule":
        """Load a memory module from disk."""
        ...


class MemoryUpdater(ABC):
    """Abstract base class for memory updaters.

    A memory updater reflects on completed trajectories and updates
    the memory module with learned insights.
    """

    @abstractmethod
    async def update_from_trajectory(
        self,
        memory: MemoryModule,
        trajectory: "SimulationResult",
        model_client: "ModelClient",
    ) -> MemoryModule:
        """Update memory based on a single completed trajectory.

        Args:
            memory: The current memory module.
            trajectory: The completed simulation result.
            model_client: Model client for reflection.

        Returns:
            The updated memory module.
        """
        ...

    @abstractmethod
    async def batch_update(
        self,
        memory: MemoryModule,
        trajectories: list["SimulationResult"],
        model_client: "ModelClient",
    ) -> MemoryModule:
        """Update memory from multiple trajectories at once.

        Args:
            memory: The current memory module.
            trajectories: List of completed simulation results.
            model_client: Model client for reflection.

        Returns:
            The updated memory module.
        """
        ...
