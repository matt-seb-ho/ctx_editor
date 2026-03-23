"""Huang et al. strategy: omit all assistant messages from context.

Based on Huang et al. (2026) "Do LLMs Benefit from Their Own Words?"
The Assistant-Omitted (AO) configuration strips all assistant messages
from the context, presenting only the system prompt and user messages.

This is the simplest baseline that avoids anchoring on bad assistant
output, at the cost of losing all assistant work product.
"""

from typing import TYPE_CHECKING, Optional

from ..core.types import Message
from .base import BaseStrategy

if TYPE_CHECKING:
    from ..core.trace import ConversationTrace
    from ..memory.base import MemoryModule
    from ..models.base import ModelClient


class AssistantOmitStrategy(BaseStrategy):
    """Strip all assistant messages from context (Huang et al. AO baseline).

    On every turn, returns only system + user messages. The assistant
    never sees its own prior responses, preventing anchoring on bad
    reasoning but also losing all work product.

    No LLM calls, no threshold -- applies from the start.
    """

    def __init__(
        self,
        use_memory: bool = False,
        memory_target: str = "system",
    ):
        self.use_memory = use_memory
        self.memory_target = memory_target

    async def prepare_context(
        self,
        trace: "ConversationTrace",
        memory: Optional["MemoryModule"],
        model_client: "ModelClient",
    ) -> list[Message]:
        """Return context with all assistant messages stripped."""
        if self.use_memory and memory and self.memory_target == "system":
            self._inject_memory_to_trace(trace, memory, target="system")

        active = trace.get_active_messages()
        return [msg for msg in active if msg.role != "assistant"]
