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
    and passed directly to the assistant. The only mutation is optional
    one-time cheatsheet injection.
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
        """Return the full conversation trace (mutates trace for cheatsheet only).

        Args:
            trace: The current conversation trace (mutated if cheatsheet injected).
            cheatsheet: Optional cheatsheet (only used if use_cheatsheet=True).
            model_client: Not used in baseline strategy.

        Returns:
            Active messages from the trace.
        """
        # Inject cheatsheet once if configured
        if self.use_cheatsheet and cheatsheet:
            self._inject_cheatsheet_to_trace(trace, cheatsheet, target=self.cheatsheet_target)

        return trace.get_active_messages()
