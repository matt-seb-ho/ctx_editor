"""Baseline strategy with no context modification."""

from typing import TYPE_CHECKING, Optional

from ..core.types import Message
from .base import BaseStrategy

if TYPE_CHECKING:
    from ..cheatsheet.cheatsheet import Cheatsheet
    from ..core.trace import ConversationTrace
    from ..models.base import ModelClient


class BaselineStrategy(BaseStrategy):
    """No modification strategy - returns the full conversation as-is.

    This is the baseline approach where all conversation history is preserved
    and passed directly to the assistant.
    """

    def __init__(self, use_cheatsheet: bool = False, cheatsheet_target: str = "system"):
        """Initialize the baseline strategy.

        Args:
            use_cheatsheet: Whether to inject cheatsheet into context.
            cheatsheet_target: Where to inject cheatsheet ('system' or 'user').
        """
        self.use_cheatsheet = use_cheatsheet
        self.cheatsheet_target = cheatsheet_target

    async def prepare_context(
        self,
        trace: "ConversationTrace",
        cheatsheet: Optional["Cheatsheet"],
        model_client: "ModelClient",
    ) -> list[Message]:
        """Return the full conversation trace.

        Args:
            trace: The current conversation trace.
            cheatsheet: Optional cheatsheet (only used if use_cheatsheet=True).
            model_client: Not used in baseline strategy.

        Returns:
            All messages from the trace, optionally with cheatsheet.
        """
        messages = self._messages_to_list(trace)

        if self.use_cheatsheet and cheatsheet:
            messages = self._inject_cheatsheet(
                messages,
                cheatsheet,
                target=self.cheatsheet_target,
            )

        return messages
