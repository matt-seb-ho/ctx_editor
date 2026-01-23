"""Conversation trace management."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from .types import Message


@dataclass
class ConversationTrace:
    """Manages the conversation history and provides utilities for context manipulation."""

    messages: list[Message] = field(default_factory=list)
    logs: list[dict[str, Any]] = field(default_factory=list)

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
        self.messages.append(Message(
            role="user",
            content=content,
            metadata=metadata or {},
        ))

    def add_assistant_message(self, content: str, metadata: Optional[dict] = None) -> None:
        """Add an assistant message to the trace."""
        self.messages.append(Message(
            role="assistant",
            content=content,
            metadata=metadata or {},
        ))

    def add_log(self, log_type: str, data: dict[str, Any]) -> None:
        """Add a log entry to the trace."""
        self.logs.append({
            "type": log_type,
            "data": data,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

    def to_messages(self, include_system: bool = True) -> list[Message]:
        """Get all messages for API calls."""
        if include_system:
            return list(self.messages)
        return [msg for msg in self.messages if msg.role != "system"]

    def to_dict_messages(self, include_system: bool = True) -> list[dict[str, str]]:
        """Get all messages as dictionaries for API calls."""
        messages = self.to_messages(include_system)
        return [msg.to_dict() for msg in messages]

    def to_full_trace(self) -> list[dict[str, Any]]:
        """Get the full trace including logs for serialization."""
        trace = []
        for msg in self.messages:
            entry = {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp,
            }
            if msg.metadata:
                entry.update(msg.metadata)
            trace.append(entry)

        # Interleave logs at appropriate positions based on timestamp
        for log in self.logs:
            trace.append({
                "role": "log",
                "content": log,
                "timestamp": log["timestamp"],
            })

        return trace

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
                messages = messages[last_user_idx + 1:]

        return "\n\n".join([f"[{msg.role}] {msg.content}" for msg in messages])

    def get_revealed_shard_ids(self) -> list[str]:
        """Get IDs of shards that have been revealed."""
        return [
            log["data"]["shard_id"]
            for log in self.logs
            if log["type"] == "shard_revealed"
        ]

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
        return new_trace
