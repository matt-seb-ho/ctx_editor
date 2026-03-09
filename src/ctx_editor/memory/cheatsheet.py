"""Cheatsheet-based memory implementation.

Concrete implementation of MemoryModule and MemoryUpdater following
the Dynamic Cheatsheet approach (Suzgun et al 2025).
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Optional

from ..utils.helpers import load_prompt
from .base import MemoryModule, MemoryUpdater
from .renderers import RENDERERS

if TYPE_CHECKING:
    from ..core.types import SimulationResult
    from ..models.base import ModelClient

# Directory containing built-in prompt templates
_PROMPTS_DIR = Path(__file__).parent / "prompts"

# Map target → prompt file
_DEFAULT_PROMPT_FILES: dict[str, Path] = {
    "assistant": _PROMPTS_DIR / "assistant_reflection.txt",
    "context_editor": _PROMPTS_DIR / "context_editor_reflection.txt",
    "edit_decision": _PROMPTS_DIR / "edit_decision_reflection.txt",
}


@dataclass
class CheatsheetMemory(MemoryModule):
    """A cheatsheet that accumulates learned knowledge across problems.

    The cheatsheet can be used to provide guidance to either the context
    editor or the assistant, helping them learn from previous experiences.
    """

    _content: str = ""
    _version: int = 0
    history: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def content(self) -> str:
        return self._content

    @property
    def version(self) -> int:
        return self._version

    def update(self, new_content: str) -> None:
        """Update the cheatsheet with new content."""
        if new_content != self._content:
            self.history.append(self._content)
            self._content = new_content
            self._version += 1

    def append(self, additional_content: str) -> None:
        """Append additional content to the cheatsheet."""
        self.history.append(self._content)
        if self._content:
            self._content = f"{self._content}\n\n{additional_content}"
        else:
            self._content = additional_content
        self._version += 1

    def rollback(self) -> bool:
        """Rollback to the previous version.

        Returns:
            True if rollback was successful, False if no history.
        """
        if self.history:
            self._content = self.history.pop()
            self._version -= 1
            return True
        return False

    def get_version(self, version: int) -> Optional[str]:
        """Get a specific version of the cheatsheet.

        Args:
            version: The version number to retrieve.

        Returns:
            The cheatsheet content at that version, or None if not found.
        """
        if version == self._version:
            return self._content
        elif version < self._version and version >= 0:
            history_idx = version
            if history_idx < len(self.history):
                return self.history[history_idx]
        return None

    def save(self, filepath: str) -> None:
        """Save the cheatsheet to a file."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "content": self._content,
            "version": self._version,
            "history": self.history,
            "metadata": self.metadata,
        }

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, filepath: str) -> "CheatsheetMemory":
        """Load a cheatsheet from a file."""
        with open(filepath, "r") as f:
            data = json.load(f)

        return cls(
            _content=data.get("content", ""),
            _version=data.get("version", 0),
            history=data.get("history", []),
            metadata=data.get("metadata", {}),
        )

    def clone(self) -> "CheatsheetMemory":
        """Create a deep copy of the cheatsheet."""
        return CheatsheetMemory(
            _content=self._content,
            _version=self._version,
            history=list(self.history),
            metadata=dict(self.metadata),
        )

    def __str__(self) -> str:
        preview = self._content[:100] + "..." if len(self._content) > 100 else self._content
        return f"CheatsheetMemory(v{self._version}, {len(self._content)} chars): {preview}"


VALID_TARGETS = frozenset({"assistant", "context_editor", "edit_decision"})


class CheatsheetUpdater(MemoryUpdater):
    """Updates cheatsheet based on completed simulation trajectories.

    This implements the continual learning aspect where the cheatsheet
    evolves based on experience.
    """

    def __init__(
        self,
        target: str = "assistant",
        reflection_prompt: Optional[str] = None,
        reflection_prompt_file: Optional[str] = None,
        model: str = "gpt-4o-mini",
        update_on_success: bool = True,
        update_on_failure: bool = True,
        include_full_spec_q: bool = False,
        include_ground_truth_a: bool = False,
    ):
        """Initialize the updater.

        Args:
            target: What component to improve — "assistant", "context_editor",
                or "edit_decision". Controls the reflection prompt and trajectory
                rendering used during updates.
            reflection_prompt: Custom prompt override (overrides target default).
            reflection_prompt_file: Path to a prompt file (overrides target default).
            model: Model to use for reflection.
            update_on_success: Whether to update on successful outcomes.
            update_on_failure: Whether to update on failed outcomes.
            include_full_spec_q: Whether to include the fully-specified question
                in cheatsheet update prompts for grounding.
            include_ground_truth_a: Whether to include the ground truth answer
                in cheatsheet update prompts for grounding.
        """
        if target not in VALID_TARGETS:
            raise ValueError(f"Invalid target {target!r}. Must be one of {sorted(VALID_TARGETS)}")
        self.target = target
        self.renderer: Callable[["SimulationResult"], str] = RENDERERS[target]

        if reflection_prompt_file:
            self.reflection_prompt = load_prompt(reflection_prompt_file)
        elif reflection_prompt:
            self.reflection_prompt = reflection_prompt
        else:
            self.reflection_prompt = _DEFAULT_PROMPT_FILES[target].read_text()

        self.model = model
        self.update_on_success = update_on_success
        self.update_on_failure = update_on_failure
        self.include_full_spec_q = include_full_spec_q
        self.include_ground_truth_a = include_ground_truth_a

    def _render_trajectory(self, trajectory: "SimulationResult") -> str:
        """Render trajectory conversation using the target-specific renderer."""
        return self.renderer(trajectory)

    def _build_grounding_info(self, trajectory: "SimulationResult") -> str:
        """Build grounding information section for the prompt."""
        parts = []
        metadata = trajectory.metadata or {}

        if self.include_full_spec_q and "full_spec_q" in metadata:
            parts.append(f"""
<full_specification>
The fully-specified single-turn version of this problem:
{metadata["full_spec_q"]}
</full_specification>""")

        if self.include_ground_truth_a and "ground_truth_a" in metadata:
            parts.append(f"""
<ground_truth>
The ground truth answer:
{metadata["ground_truth_a"]}
</ground_truth>""")

        if parts:
            return "\n" + "\n".join(parts)
        return ""

    async def update_from_trajectory(
        self,
        memory: MemoryModule,
        trajectory: "SimulationResult",
        model_client: "ModelClient",
    ) -> MemoryModule:
        """Update the memory based on a completed trajectory."""
        # Check if we should update based on outcome
        if trajectory.is_correct and not self.update_on_success:
            return memory
        if not trajectory.is_correct and not self.update_on_failure:
            return memory

        # Build reflection prompt
        conversation = self._render_trajectory(trajectory)
        outcome = "Success" if trajectory.is_correct else "Failure"
        grounding_info = self._build_grounding_info(trajectory)

        prompt = self.reflection_prompt.format(
            current_cheatsheet=memory.content if memory.content else "(empty)",
            task_name=trajectory.task_name,
            sample_id=trajectory.sample_id,
            outcome=outcome,
            score=str(trajectory.score),
            num_turns=str(trajectory.num_turns),
            conversation=conversation,
            grounding_info=grounding_info,
        )

        # Generate updated cheatsheet
        response = await model_client.generate(
            messages=[{"role": "user", "content": prompt}],
            model=self.model,
            temperature=0.3,
        )

        new_content = response.content.strip()
        memory.update(new_content)

        # Add metadata about this update (only for CheatsheetMemory)
        if isinstance(memory, CheatsheetMemory):
            memory.metadata[f"update_{memory.version}"] = {
                "sample_id": trajectory.sample_id,
                "task_name": trajectory.task_name,
                "outcome": outcome,
                "score": trajectory.score,
            }

        return memory

    async def batch_update(
        self,
        memory: MemoryModule,
        trajectories: list["SimulationResult"],
        model_client: "ModelClient",
    ) -> MemoryModule:
        """Update memory from multiple trajectories at once."""
        # Filter trajectories based on update settings
        filtered = []
        for t in trajectories:
            if t.is_correct and self.update_on_success:
                filtered.append(t)
            elif not t.is_correct and self.update_on_failure:
                filtered.append(t)

        if not filtered:
            return memory

        # Build a combined reflection prompt
        trajectories_text = []
        for i, t in enumerate(filtered, 1):
            conversation = self._render_trajectory(t)
            outcome = "Success" if t.is_correct else "Failure"
            grounding_info = self._build_grounding_info(t)
            trajectories_text.append(f"""
--- Trajectory {i} ---
Task: {t.task_name}
Sample ID: {t.sample_id}
Outcome: {outcome} (score: {t.score})
Turns: {t.num_turns}

{conversation}
{grounding_info}""")

        current = memory.content if memory.content else "(empty)"
        all_trajectories = "".join(trajectories_text)
        batch_prompt = (
            f"You are updating a cheatsheet based on multiple completed conversation trajectories.\n\n"
            f"<current_cheatsheet>\n{current}\n</current_cheatsheet>\n\n"
            f"<trajectories>\n{all_trajectories}\n</trajectories>\n\n"
            "Synthesize insights from all trajectories to update the cheatsheet. Look for:\n"
            "1. Common patterns across successful/failed attempts\n"
            "2. Critical information that needed to be preserved\n"
            "3. Effective strategies and pitfalls to avoid\n\n"
            "Provide an updated, concise cheatsheet:"
        )

        response = await model_client.generate(
            messages=[{"role": "user", "content": batch_prompt}],
            model=self.model,
            temperature=0.3,
        )

        memory.update(response.content.strip())

        # Record batch update metadata (only for CheatsheetMemory)
        if isinstance(memory, CheatsheetMemory):
            memory.metadata[f"batch_update_{memory.version}"] = {
                "num_trajectories": len(filtered),
                "sample_ids": [t.sample_id for t in filtered],
            }

        return memory
