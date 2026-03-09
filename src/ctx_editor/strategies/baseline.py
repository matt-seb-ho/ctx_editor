"""Baseline strategy with no context modification."""

from typing import TYPE_CHECKING, Optional

from ..core.types import Message
from .base import BaseStrategy

if TYPE_CHECKING:
    from ..core.trace import ConversationTrace
    from ..memory.base import MemoryModule
    from ..models.base import ModelClient


class BaselineStrategy(BaseStrategy):
    """No modification strategy - returns the full conversation as-is.

    This is the baseline approach where all conversation history is preserved
    and passed directly to the assistant. The only mutation is optional
    one-time memory injection.
    """

    def __init__(self, use_memory: bool = False, memory_target: str = "system"):
        """Initialize the baseline strategy.

        Args:
            use_memory: Whether to inject memory into context.
            memory_target: Where to inject memory ('system' or 'user').
        """
        self.use_memory = use_memory
        self.memory_target = memory_target

    async def prepare_context(
        self,
        trace: "ConversationTrace",
        memory: Optional["MemoryModule"],
        model_client: "ModelClient",
    ) -> list[Message]:
        """Return the full conversation trace (mutates trace for memory only).

        Args:
            trace: The current conversation trace (mutated if memory injected).
            memory: Optional memory module (only used if use_memory=True).
            model_client: Not used in baseline strategy.

        Returns:
            Active messages from the trace.
        """
        # Inject memory once if configured
        if self.use_memory and memory:
            self._inject_memory_to_trace(trace, memory, target=self.memory_target)

        return trace.get_active_messages()
