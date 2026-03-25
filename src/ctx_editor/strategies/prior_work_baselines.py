"""Baseline strategies from prior work for comparison.

Implements simplified versions of approaches from:
- Huang et al. (2026): Omit all assistant messages
- ERGO / Khalid et al. (2025): Concatenate user messages into a single prompt (reset)
"""

from typing import TYPE_CHECKING, Optional

from ..core.types import Message
from .base import BaseStrategy

if TYPE_CHECKING:
    from ..core.trace import ConversationTrace
    from ..memory.base import MemoryModule
    from ..models.base import ModelClient


class OmitAssistantStrategy(BaseStrategy):
    """Huang et al. baseline: strip all assistant messages from the conversation.

    The assistant sees only the system message and user messages, with no
    prior assistant responses. This tests whether simply hiding the assistant's
    own prior reasoning is sufficient to recover performance.
    """

    def __init__(self, min_turns: int = 1):
        self.min_turns = min_turns

    async def prepare_context(
        self,
        trace: "ConversationTrace",
        memory: Optional["MemoryModule"],
        model_client: "ModelClient",
    ) -> list[Message]:
        if trace.num_user_turns < self.min_turns:
            return trace.get_active_messages()

        active = trace.get_active_messages()
        # Keep system + user messages only, drop assistant messages
        filtered = [msg for msg in active if msg.role in ("system", "user")]

        trace.add_log(
            "omit_assistant",
            {
                "original_count": len(active),
                "filtered_count": len(filtered),
                "removed_assistant_msgs": len(active) - len(filtered),
            },
        )

        return filtered


class ConcatenateUserStrategy(BaseStrategy):
    """ERGO-style baseline: concatenate all user messages into a single prompt.

    Resets the conversation to a single user message containing all user
    messages concatenated together. No analysis or LLM calls — just raw
    concatenation. This approximates ERGO's reset behavior without the
    entropy-based trigger (we apply it unconditionally at the final turn
    via replay).
    """

    def __init__(self, min_turns: int = 1, numbered: bool = True):
        self.min_turns = min_turns
        self.numbered = numbered

    async def prepare_context(
        self,
        trace: "ConversationTrace",
        memory: Optional["MemoryModule"],
        model_client: "ModelClient",
    ) -> list[Message]:
        if trace.num_user_turns < self.min_turns:
            return trace.get_active_messages()

        # Get all unique user messages across resets
        user_messages_str = trace.get_user_messages_string(all_unique=True)

        # Build the concatenated prompt
        concatenated = (
            "Here are all the messages from the user so far. "
            "Please provide a complete, correct response based on all of them.\n\n"
            f"{user_messages_str}"
        )

        # Get system message if present
        system_msg = trace.system_message
        new_messages = []
        if system_msg:
            new_messages.append(
                Message(role="system", content=system_msg.content)
            )
        new_messages.append(Message(role="user", content=concatenated))

        # Reset the conversation
        trace.reset_conversation(new_messages, label="concatenate_user_reset")

        trace.add_log(
            "concatenate_user",
            {
                "user_messages_concatenated": True,
                "numbered": self.numbered,
            },
        )

        return trace.get_active_messages()
