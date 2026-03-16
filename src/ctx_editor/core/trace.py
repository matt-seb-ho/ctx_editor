"""Conversation trace management."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from .types import Message


@dataclass
class ConversationTrace:
    """Manages the conversation history and provides utilities for context manipulation.

    Uses a visibility-based approach for context editing: all messages are preserved
    in the trace for history/debugging, but only "visible" messages form the active
    conversation. When context editing resets the conversation, old messages are
    marked as visible=False and new edited context is added as visible=True.

    This allows:
    - Full history preservation for analysis
    - Clean separation of "what assistant sees" vs "what we log"
    - Proper conversation resets after context editing
    """

    messages: list[Message] = field(default_factory=list)
    logs: list[dict[str, Any]] = field(default_factory=list)
    # Track number of context resets for analysis
    num_resets: int = 0
    # Provenance tracking for replay mode — records where this trace originated
    provenance: Optional[dict[str, Any]] = None

    def get_active_messages(self) -> list[Message]:
        """Get only visible messages (the active conversation)."""
        return [msg for msg in self.messages if msg.visible]

    @property
    def system_message(self) -> Optional[Message]:
        """Get the system message if present (from active conversation)."""
        for msg in self.get_active_messages():
            if msg.role == "system":
                return msg
        return None

    @property
    def last_user_message(self) -> Optional[Message]:
        """Get the most recent user message (from active conversation)."""
        for msg in reversed(self.get_active_messages()):
            if msg.role == "user":
                return msg
        return None

    @property
    def last_assistant_message(self) -> Optional[Message]:
        """Get the most recent assistant message (from active conversation)."""
        for msg in reversed(self.get_active_messages()):
            if msg.role == "assistant":
                return msg
        return None

    @property
    def num_user_turns(self) -> int:
        """Count the number of user messages (in active conversation)."""
        return sum(1 for msg in self.get_active_messages() if msg.role == "user")

    @property
    def num_assistant_turns(self) -> int:
        """Count the number of assistant messages (in active conversation)."""
        return sum(1 for msg in self.get_active_messages() if msg.role == "assistant")

    @property
    def total_user_turns(self) -> int:
        """Count total user messages across all resets (for metrics)."""
        return sum(1 for msg in self.messages if msg.role == "user")

    @property
    def total_assistant_turns(self) -> int:
        """Count total assistant messages across all resets (for metrics)."""
        return sum(1 for msg in self.messages if msg.role == "assistant")

    def add_system_message(self, content: str) -> None:
        """Add or replace the system message."""
        # Mark existing visible system messages as not visible
        for msg in self.messages:
            if msg.role == "system" and msg.visible:
                msg.visible = False
        # Insert at the beginning
        self.messages.insert(0, Message(role="system", content=content, visible=True))

    def reset_conversation(self, new_messages: list[Message], label: str = "context_edit") -> None:
        """Reset the active conversation with new context.

        Marks all currently visible messages as invisible and adds the new messages
        as the active conversation. This is used after context editing to ensure
        future turns build on the edited context, not the full history.

        All messages (visible and hidden) are preserved in the trace for analysis.

        Args:
            new_messages: The new messages to form the active conversation.
            label: Label for the reset event in logs.
        """
        # Mark all currently visible messages as invisible
        for msg in self.messages:
            if msg.visible:
                msg.visible = False

        # Add new messages as visible
        for msg in new_messages:
            # Create a copy to avoid reference issues
            new_msg = Message(
                role=msg.role,
                content=msg.content,
                metadata=dict(msg.metadata) if msg.metadata else {},
                timestamp=msg.timestamp,
                visible=True,
            )
            self.messages.append(new_msg)

        self.num_resets += 1

        self.add_log(
            "conversation_reset",
            {
                "label": label,
                "new_message_count": len(new_messages),
                "total_resets": self.num_resets,
            },
        )

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

    def append_to_system_message(self, content_suffix: str) -> bool:
        """Append content to the visible system message.

        Args:
            content_suffix: Content to append to the system message.

        Returns:
            True if system message was found and modified, False otherwise.
        """
        for msg in self.messages:
            if msg.role == "system" and msg.visible:
                msg.content += content_suffix
                return True
        return False

    def append_to_last_user_message(self, content_suffix: str) -> bool:
        """Append content to the last visible user message.

        Args:
            content_suffix: Content to append to the last user message.

        Returns:
            True if a user message was found and modified, False otherwise.
        """
        for msg in reversed(self.messages):
            if msg.role == "user" and msg.visible:
                msg.content += content_suffix
                return True
        return False

    def add_log(self, log_type: str, data: dict[str, Any]) -> None:
        """Add a log entry to the trace."""
        self.logs.append(
            {
                "type": log_type,
                "data": data,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

    def replace_messages(self, new_messages: list[Message]) -> None:
        """Replace messages with a new list.

        DEPRECATED: Use reset_conversation() instead, which preserves history
        via visibility flags rather than destructively replacing messages.
        """
        self.messages = new_messages
        self.add_log(
            "context_replaced",
            {"new_message_count": len(new_messages)},
        )

    def to_messages(self, include_system: bool = True, active_only: bool = True) -> list[Message]:
        """Get messages for API calls.

        Args:
            include_system: Whether to include the system message.
            active_only: If True, only return visible messages (default).
                         If False, return all messages regardless of visibility.

        Returns:
            List of Message objects.
        """
        if active_only:
            messages = self.get_active_messages()
        else:
            messages = list(self.messages)

        if not include_system:
            messages = [msg for msg in messages if msg.role != "system"]

        return messages

    def to_dict_messages(self, include_system: bool = True) -> list[dict[str, str]]:
        """Get all messages as dictionaries for API calls."""
        messages = self.to_messages(include_system)
        return [msg.to_dict() for msg in messages]

    def to_full_trace(self) -> dict[str, Any]:
        """Get the full trace including logs for serialization.

        Returns:
            Dictionary with 'messages', 'logs', 'num_resets', and optionally 'provenance'.
            All messages (visible and hidden) are included - use the 'visible'
            field to reconstruct pre/post-edit states.
        """
        messages = []
        for msg in self.messages:
            entry = {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp,
                "visible": msg.visible,
            }
            if msg.metadata:
                entry["metadata"] = msg.metadata
            messages.append(entry)

        result = {
            "messages": messages,
            "logs": self.logs,
            "num_resets": self.num_resets,
        }
        if self.provenance:
            result["provenance"] = self.provenance
        return result

    def get_user_messages_string(
        self,
        active_only: bool = True,
        include_compacted: bool = False,
        all_unique: bool = False,
    ) -> str:
        """Get only user messages as a formatted string, numbered by turn.

        Args:
            active_only: If True, only include visible messages.
            include_compacted: If True, also include "compacted conversation" messages.
                This is important for S2 (context edit) — after a reset, the compacted
                conversation contains the previous task spec and should be included
                when the analyzer builds a new task spec.
            all_unique: If True, include ALL user messages (visible and hidden),
                deduplicated by content. This ensures the task spec query sees
                every user message across all resets, without the bias of a
                previous compacted task spec. Overrides active_only and
                include_compacted when set.
        """
        if all_unique:
            # Get all user messages across resets, deduplicated
            all_msgs = self.to_messages(include_system=False, active_only=False)
            user_msgs = [msg for msg in all_msgs if msg.role == "user"]
            # Deduplicate by content (preserves order, keeps first occurrence)
            seen: set[str] = set()
            unique_msgs = []
            for msg in user_msgs:
                content = msg.content.strip()
                if content not in seen:
                    seen.add(content)
                    unique_msgs.append(msg)
            parts = []
            for i, msg in enumerate(unique_msgs, 1):
                parts.append(f"[Message {i}]\n{msg.content}")
            return "\n\n".join(parts)

        messages = self.to_messages(include_system=False, active_only=active_only)
        relevant_roles = {"user"}
        if include_compacted:
            relevant_roles.add("compacted conversation")
        relevant_msgs = [msg for msg in messages if msg.role in relevant_roles]
        parts = []
        for i, msg in enumerate(relevant_msgs, 1):
            if msg.role == "compacted conversation":
                parts.append(f"[Previous Task Summary]\n{msg.content}")
            else:
                parts.append(f"[Message {i}]\n{msg.content}")
        return "\n\n".join(parts)

    def get_conversation_string(
        self,
        skip_system: bool = False,
        only_last_turn: bool = False,
        active_only: bool = True,
    ) -> str:
        """Get conversation as a formatted string.

        Args:
            skip_system: Whether to exclude the system message.
            only_last_turn: If True, only include messages after the last user message.
            active_only: If True, only include visible messages (default).

        Returns:
            Formatted string representation of the conversation.
        """
        messages = self.to_messages(include_system=not skip_system, active_only=active_only)

        if only_last_turn:
            # Get messages after the last user message
            user_indices = [i for i, msg in enumerate(messages) if msg.role == "user"]
            if user_indices:
                last_user_idx = user_indices[-1]
                messages = messages[last_user_idx + 1 :]

        return "\n\n".join([f"[{msg.role}] {msg.content}" for msg in messages])

    @property
    def previous_task_spec(self) -> Optional[str]:
        """Extract the task spec from the last compacted conversation message, if any.

        Returns the content under '# User Task Specification (So Far)' from
        the most recent compacted conversation message, or None if no resets
        have occurred.
        """
        for msg in reversed(self.messages):
            if msg.role == "compacted conversation":
                content = msg.content
                marker = "# User Task Specification (So Far)"
                idx = content.find(marker)
                if idx == -1:
                    return None
                # Extract from after the marker to the next section header or end
                start = idx + len(marker)
                rest = content[start:]
                # Find next section header (# ...) if any
                next_section = rest.find("\n# ")
                if next_section != -1:
                    return rest[:next_section].strip()
                return rest.strip()
        return None

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
                visible=msg.visible,
            )
            for msg in self.messages
        ]
        new_trace.logs = [dict(log) for log in self.logs]
        new_trace.num_resets = self.num_resets
        new_trace.provenance = dict(self.provenance) if self.provenance else None
        return new_trace

    @classmethod
    def from_saved_trace(
        cls,
        trace_data: dict[str, Any],
        truncate_final_assistant: bool = False,
        truncate_turns: int = 0,
        provenance: Optional[dict[str, Any]] = None,
    ) -> "ConversationTrace":
        """Reconstruct a ConversationTrace from saved trace data.

        Args:
            trace_data: The 'trace' dict from a saved trace file, containing
                'messages', 'logs', and 'num_resets'.
            truncate_final_assistant: If True, remove the last assistant message
                from visible messages (for replay mode — we want to regenerate it).
                Ignored if truncate_turns > 0.
            truncate_turns: Number of complete turns (user+assistant pairs) to
                remove from the end for multi-turn replay. When > 0, overrides
                truncate_final_assistant.
            provenance: Optional provenance metadata to attach to this trace.

        Returns:
            A ConversationTrace with the reconstructed state.
        """
        trace = cls()
        trace.provenance = provenance

        # Reconstruct messages
        for msg_data in trace_data.get("messages", []):
            trace.messages.append(Message.from_dict(msg_data))

        # Reconstruct logs
        trace.logs = list(trace_data.get("logs", []))
        trace.num_resets = trace_data.get("num_resets", 0)

        if truncate_turns > 0:
            # Multi-turn truncation: remove the last k visible (user, assistant) pairs.
            # Walk backwards removing messages, counting complete turns removed.
            turns_removed = 0
            while turns_removed < truncate_turns:
                # Remove the last visible assistant message
                found_assistant = False
                for i in range(len(trace.messages) - 1, -1, -1):
                    if trace.messages[i].role == "assistant" and trace.messages[i].visible:
                        trace.messages.pop(i)
                        found_assistant = True
                        break
                if not found_assistant:
                    break  # No more assistant messages to remove

                # Remove the last visible user message
                for i in range(len(trace.messages) - 1, -1, -1):
                    if trace.messages[i].role == "user" and trace.messages[i].visible:
                        trace.messages.pop(i)
                        break

                # Strip the corresponding logs for this turn (verification, answer_evaluation,
                # shard_revealed — each turn produces one verification log and optionally others)
                while trace.logs and trace.logs[-1]["type"] in (
                    "verification",
                    "answer_evaluation",
                ):
                    trace.logs.pop()
                # Remove the shard_revealed log for this turn if present
                if trace.logs and trace.logs[-1]["type"] == "shard_revealed":
                    trace.logs.pop()

                turns_removed += 1

        elif truncate_final_assistant:
            # Single-turn truncation (original behavior): remove last assistant message only.
            for i in range(len(trace.messages) - 1, -1, -1):
                msg = trace.messages[i]
                if msg.role == "assistant" and msg.visible:
                    trace.messages.pop(i)
                    break

            # Strip logs from the final turn's verification/evaluation.
            while trace.logs and trace.logs[-1]["type"] in (
                "verification",
                "answer_evaluation",
            ):
                trace.logs.pop()

        return trace
