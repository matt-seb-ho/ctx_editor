"""Base strategy protocol and interface."""

from typing import TYPE_CHECKING, Optional, Protocol, runtime_checkable

from ..core.types import Message

MEMORY_BLOCK_TEMPLATE = "\n\n<cheatsheet>\n{memory_content}\n</cheatsheet>"

if TYPE_CHECKING:
    from ..core.trace import ConversationTrace
    from ..memory.base import MemoryModule
    from ..models.base import ModelClient


@runtime_checkable
class ContextStrategy(Protocol):
    """Protocol for context modification strategies.

    Strategies determine how to prepare the context for each assistant turn.
    This is the main extension point for experimenting with different
    context editing approaches.

    IMPORTANT: prepare_context() MUTATES the trace. It modifies the trace's
    messages directly (e.g., appending reflections, resetting conversation
    after context editing) and returns the active messages for the API call.
    """

    async def prepare_context(
        self,
        trace: "ConversationTrace",
        memory: Optional["MemoryModule"],
        model_client: "ModelClient",
    ) -> list[Message]:
        """Prepare the context for the next assistant turn.

        This method MUTATES the trace by modifying messages as needed
        (e.g., appending reflections, resetting visibility after edits).
        The returned messages are the trace's active messages after mutation.

        Args:
            trace: The current conversation trace (will be mutated).
            memory: Optional memory module for context augmentation.
            model_client: Model client for generating edits/reflections.

        Returns:
            List of active messages to use as context for the assistant.
        """
        ...


class BaseStrategy:
    """Base class for strategies with common utilities."""

    def _is_memory_injected(self, trace: "ConversationTrace") -> bool:
        """Check if memory has already been injected into this trace."""
        return any(log["type"] == "memory_injected" for log in trace.logs)

    def _inject_memory_to_trace(
        self,
        trace: "ConversationTrace",
        memory: "MemoryModule",
        target: str = "system",
    ) -> bool:
        """Inject memory content into the trace (mutates trace).

        Only injects once - subsequent calls are no-ops.

        Args:
            trace: The conversation trace to mutate.
            memory: Memory module to inject.
            target: Where to inject ('system' or 'user').

        Returns:
            True if memory was injected, False if skipped (already injected or empty).
        """
        if not memory or not memory.content:
            return False

        # Only inject once per trace
        if self._is_memory_injected(trace):
            return False

        memory_block = MEMORY_BLOCK_TEMPLATE.format(memory_content=memory.content)

        if target == "system":
            success = trace.append_to_system_message(memory_block)
        elif target == "user":
            success = trace.append_to_last_user_message(memory_block)
        else:
            return False

        if success:
            trace.add_log("memory_injected", {"target": target})

        return success
