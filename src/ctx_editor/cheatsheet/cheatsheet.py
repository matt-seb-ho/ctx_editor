"""Cheatsheet data structure for maintaining learned knowledge."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class Cheatsheet:
    """A cheatsheet that accumulates learned knowledge across problems.

    The cheatsheet can be used to provide guidance to either the context
    editor or the assistant, helping them learn from previous experiences.
    """

    content: str = ""
    version: int = 0
    history: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def update(self, new_content: str) -> None:
        """Update the cheatsheet with new content.

        Args:
            new_content: The new cheatsheet content.
        """
        if new_content != self.content:
            self.history.append(self.content)
            self.content = new_content
            self.version += 1

    def append(self, additional_content: str) -> None:
        """Append additional content to the cheatsheet.

        Args:
            additional_content: Content to append.
        """
        self.history.append(self.content)
        if self.content:
            self.content = f"{self.content}\n\n{additional_content}"
        else:
            self.content = additional_content
        self.version += 1

    def rollback(self) -> bool:
        """Rollback to the previous version.

        Returns:
            True if rollback was successful, False if no history.
        """
        if self.history:
            self.content = self.history.pop()
            self.version -= 1
            return True
        return False

    def get_version(self, version: int) -> Optional[str]:
        """Get a specific version of the cheatsheet.

        Args:
            version: The version number to retrieve.

        Returns:
            The cheatsheet content at that version, or None if not found.
        """
        if version == self.version:
            return self.content
        elif version < self.version and version >= 0:
            # Calculate index in history
            history_idx = version
            if history_idx < len(self.history):
                return self.history[history_idx]
        return None

    def save(self, filepath: str) -> None:
        """Save the cheatsheet to a file.

        Args:
            filepath: Path to save the cheatsheet.
        """
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "content": self.content,
            "version": self.version,
            "history": self.history,
            "metadata": self.metadata,
        }

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, filepath: str) -> "Cheatsheet":
        """Load a cheatsheet from a file.

        Args:
            filepath: Path to load from.

        Returns:
            Loaded Cheatsheet instance.
        """
        with open(filepath, "r") as f:
            data = json.load(f)

        return cls(
            content=data.get("content", ""),
            version=data.get("version", 0),
            history=data.get("history", []),
            metadata=data.get("metadata", {}),
        )

    def clone(self) -> "Cheatsheet":
        """Create a deep copy of the cheatsheet.

        Returns:
            A new Cheatsheet instance with copied data.
        """
        return Cheatsheet(
            content=self.content,
            version=self.version,
            history=list(self.history),
            metadata=dict(self.metadata),
        )

    def __str__(self) -> str:
        """String representation showing version and content preview."""
        preview = self.content[:100] + "..." if len(self.content) > 100 else self.content
        return f"Cheatsheet(v{self.version}, {len(self.content)} chars): {preview}"
