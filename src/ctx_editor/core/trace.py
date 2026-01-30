"""Conversation trace management."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from .types import Message


@dataclass
class ConversationTrace:
    """Manages the conversation history and provides utilities for context manipulation.

    Includes history tracking for context editing experiments where the conversation
    may be destructively modified. The history field stores snapshots of the messages
    list at key points, allowing post-hoc analysis of how the context evolved.
    """

    messages: list[Message] = field(default_factory=list)
    logs: list[dict[str, Any]] = field(default_factory=list)
    # History tracking: list of snapshots, each snapshot is (timestamp, messages_copy)
    history: list[tuple[str, list[Message]]] = field(default_factory=list)

    @property
    def system_message(self) -> Optional[Message]:
        """Get the system message if present."""
        for msg in self.messages:
            if msg.role == "system":
                return msg
        return None

    @property
    def last_user_message(self) -> Optional[Message]:
        """Get the most recent user message."""
        for msg in reversed(self.messages):
            if msg.role == "user":
                return msg
        return None

    @property
    def last_assistant_message(self) -> Optional[Message]:
        """Get the most recent assistant message."""
        for msg in reversed(self.messages):
            if msg.role == "assistant":
                return msg
        return None

    @property
    def num_user_turns(self) -> int:
        """Count the number of user messages."""
        return sum(1 for msg in self.messages if msg.role == "user")

    @property
    def num_assistant_turns(self) -> int:
        """Count the number of assistant messages."""
        return sum(1 for msg in self.messages if msg.role == "assistant")

    def add_system_message(self, content: str) -> None:
        """Add or replace the system message."""
        # Remove existing system message if present
        self.messages = [msg for msg in self.messages if msg.role != "system"]
        # Insert at the beginning
        self.messages.insert(0, Message(role="system", content=content))

    def add_user_message(self, content: str, metadata: Optional[dict] = None) -> None:
        """Add a user message to the trace."""
        self.messages.append(
            Message(
                role="user",
                content=content,
                metadata=metadata or {},
            )
        )

    def add_assistant_message(self, content: str, metadata: Optional[dict] = None) -> None:
        """Add an assistant message to the trace."""
        self.messages.append(
            Message(
                role="assistant",
                content=content,
                metadata=metadata or {},
            )
        )

    def add_log(self, log_type: str, data: dict[str, Any]) -> None:
        """Add a log entry to the trace."""
        self.logs.append(
            {
                "type": log_type,
                "data": data,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

    def take_snapshot(self, label: Optional[str] = None) -> None:
        """Take a snapshot of the current messages for history tracking.

        Call this before any destructive modification to preserve the state.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        snapshot_label = f"{timestamp}" + (f" ({label})" if label else "")
        messages_copy = [
            Message(
                role=msg.role,
                content=msg.content,
                metadata=dict(msg.metadata),
                timestamp=msg.timestamp,
            )
            for msg in self.messages
        ]
        self.history.append((snapshot_label, messages_copy))

    def replace_messages(
        self,
        new_messages: list[Message],
        snapshot_label: Optional[str] = "before_edit",
    ) -> None:
        """Replace messages with a new list, taking a snapshot first.

        Use this for context editing operations that destructively modify history.
        """
        if snapshot_label:
            self.take_snapshot(snapshot_label)
        self.messages = new_messages
        self.add_log(
            "context_replaced",
            {
                "new_message_count": len(new_messages),
                "history_snapshot_count": len(self.history),
            },
        )

    def to_messages(self, include_system: bool = True) -> list[Message]:
        """Get all messages for API calls."""
        if include_system:
            return list(self.messages)
        return [msg for msg in self.messages if msg.role != "system"]

    def to_dict_messages(self, include_system: bool = True) -> list[dict[str, str]]:
        """Get all messages as dictionaries for API calls."""
        messages = self.to_messages(include_system)
        return [msg.to_dict() for msg in messages]

    def to_full_trace(self, include_history: bool = False) -> dict[str, Any]:
        """Get the full trace including logs for serialization.

        Args:
            include_history: If True, include the full history of message snapshots.
                            Use this for context editing experiments.

        Returns:
            Dictionary with 'messages', 'logs', and optionally 'history'.
        """
        messages = []
        for msg in self.messages:
            entry = {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp,
            }
            if msg.metadata:
                entry.update(msg.metadata)
            messages.append(entry)

        result = {
            "messages": messages,
            "logs": self.logs,
        }

        if include_history and self.history:
            result["history"] = [
                {
                    "label": label,
                    "messages": [
                        {"role": m.role, "content": m.content, "timestamp": m.timestamp}
                        for m in snapshot_messages
                    ],
                }
                for label, snapshot_messages in self.history
            ]

        return result

    def get_conversation_string(
        self,
        skip_system: bool = False,
        only_last_turn: bool = False,
    ) -> str:
        """Get conversation as a formatted string."""
        messages = self.to_messages(include_system=not skip_system)

        if only_last_turn:
            # Get messages after the last user message
            user_indices = [i for i, msg in enumerate(messages) if msg.role == "user"]
            if user_indices:
                last_user_idx = user_indices[-1]
                messages = messages[last_user_idx + 1 :]

        return "\n\n".join([f"[{msg.role}] {msg.content}" for msg in messages])

    def get_revealed_shard_ids(self) -> list[str]:
        """Get IDs of shards that have been revealed."""
        return [log["data"]["shard_id"] for log in self.logs if log["type"] == "shard_revealed"]

    def clone(self) -> "ConversationTrace":
        """Create a deep copy of the trace."""
        new_trace = ConversationTrace()
        new_trace.messages = [
            Message(
                role=msg.role,
                content=msg.content,
                metadata=dict(msg.metadata),
                timestamp=msg.timestamp,
            )
            for msg in self.messages
        ]
        new_trace.logs = [dict(log) for log in self.logs]
        # Deep copy history
        new_trace.history = [
            (
                label,
                [
                    Message(
                        role=m.role,
                        content=m.content,
                        metadata=dict(m.metadata),
                        timestamp=m.timestamp,
                    )
                    for m in snapshot_messages
                ],
            )
            for label, snapshot_messages in self.history
        ]
        return new_trace
