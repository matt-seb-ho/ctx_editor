"""Base strategy protocol and interface."""

from typing import TYPE_CHECKING, Optional, Protocol, runtime_checkable

from ..core.types import Message

if TYPE_CHECKING:
    from ..cheatsheet.cheatsheet import Cheatsheet
    from ..core.trace import ConversationTrace
    from ..models.base import ModelClient


@runtime_checkable
class ContextStrategy(Protocol):
    """Protocol for context modification strategies.

    Strategies determine how to prepare the context for each assistant turn.
    This is the main extension point for experimenting with different
    context editing approaches.
    """

    async def prepare_context(
        self,
        trace: "ConversationTrace",
        cheatsheet: Optional["Cheatsheet"],
        model_client: "ModelClient",
    ) -> list[Message]:
        """Prepare the context for the next assistant turn.

        Args:
            trace: The current conversation trace.
            cheatsheet: Optional cheatsheet for context augmentation.
            model_client: Model client for generating edits/reflections.

        Returns:
            List of messages to use as context for the assistant.
        """
        ...


class BaseStrategy:
    """Base class for strategies with common utilities."""

    def _inject_cheatsheet(
        self,
        messages: list[Message],
        cheatsheet: "Cheatsheet",
        target: str = "system",
    ) -> list[Message]:
        """Inject cheatsheet content into messages.

        Args:
            messages: List of messages.
            cheatsheet: Cheatsheet to inject.
            target: Where to inject ('system' or 'user').

        Returns:
            Messages with cheatsheet injected.
        """
        if not cheatsheet or not cheatsheet.content:
            return messages

        cheatsheet_block = f"\n\n<cheatsheet>\n{cheatsheet.content}\n</cheatsheet>"

        if target == "system":
            # Append to system message
            for msg in messages:
                if msg.role == "system":
                    msg.content += cheatsheet_block
                    break
        elif target == "user":
            # Prepend to last user message
            for msg in reversed(messages):
                if msg.role == "user":
                    msg.content = cheatsheet_block + "\n\n" + msg.content
                    break

        return messages

    def _messages_to_list(self, trace: "ConversationTrace") -> list[Message]:
        """Convert trace to a list of Message objects."""
        return trace.to_messages()
