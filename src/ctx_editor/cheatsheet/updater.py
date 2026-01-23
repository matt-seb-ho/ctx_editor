"""Cheatsheet updater for post-simulation reflection."""

from typing import TYPE_CHECKING, Optional

from .cheatsheet import Cheatsheet
from ..utils.helpers import load_prompt

if TYPE_CHECKING:
    from ..core.types import SimulationResult
    from ..models.base import ModelClient


DEFAULT_REFLECTION_PROMPT = """You are updating a cheatsheet based on a completed conversation trajectory.

<current_cheatsheet>
[[CURRENT_CHEATSHEET]]
</current_cheatsheet>

<trajectory>
Task: [[TASK_NAME]]
Sample ID: [[SAMPLE_ID]]
Outcome: [[OUTCOME]] (score: [[SCORE]])
Number of turns: [[NUM_TURNS]]

Conversation:
[[CONVERSATION]]
</trajectory>

Based on this trajectory, update the cheatsheet to capture any useful lessons learned. Consider:
1. What patterns or strategies led to success or failure?
2. What information was critical to preserve in context?
3. What types of questions or clarifications were most helpful?
4. Are there task-specific insights to remember?

Provide an updated cheatsheet that would help in future similar problems. Keep it concise and actionable.
Focus on generalizable insights rather than problem-specific details.

Updated cheatsheet:"""


class CheatsheetUpdater:
    """Updates cheatsheet based on completed simulation trajectories.

    This implements the continual learning aspect where the cheatsheet
    evolves based on experience.
    """

    def __init__(
        self,
        reflection_prompt: Optional[str] = None,
        reflection_prompt_file: Optional[str] = None,
        model: str = "gpt-4o-mini",
        update_on_success: bool = True,
        update_on_failure: bool = True,
    ):
        """Initialize the updater.

        Args:
            reflection_prompt: Custom prompt for reflection.
            reflection_prompt_file: Path to prompt file.
            model: Model to use for reflection.
            update_on_success: Whether to update on successful outcomes.
            update_on_failure: Whether to update on failed outcomes.
        """
        if reflection_prompt_file:
            self.reflection_prompt = load_prompt(reflection_prompt_file)
        elif reflection_prompt:
            self.reflection_prompt = reflection_prompt
        else:
            self.reflection_prompt = DEFAULT_REFLECTION_PROMPT

        self.model = model
        self.update_on_success = update_on_success
        self.update_on_failure = update_on_failure

    def _extract_conversation(self, trace: list[dict]) -> str:
        """Extract conversation from trace for reflection.

        Args:
            trace: The full trace.

        Returns:
            Formatted conversation string.
        """
        conversation_parts = []
        for entry in trace:
            role = entry.get("role", "")
            if role in ["system", "user", "assistant"]:
                content = entry.get("content", "")
                conversation_parts.append(f"[{role}] {content}")
        return "\n\n".join(conversation_parts)

    async def update_from_trajectory(
        self,
        cheatsheet: Cheatsheet,
        trajectory: "SimulationResult",
        model_client: "ModelClient",
    ) -> Cheatsheet:
        """Update the cheatsheet based on a completed trajectory.

        Args:
            cheatsheet: The current cheatsheet.
            trajectory: The completed simulation result.
            model_client: Model client for reflection.

        Returns:
            Updated cheatsheet (the same object, modified in place).
        """
        # Check if we should update based on outcome
        if trajectory.is_correct and not self.update_on_success:
            return cheatsheet
        if not trajectory.is_correct and not self.update_on_failure:
            return cheatsheet

        # Build reflection prompt
        conversation = self._extract_conversation(trajectory.trace)
        outcome = "Success" if trajectory.is_correct else "Failure"

        prompt = self.reflection_prompt.replace(
            "[[CURRENT_CHEATSHEET]]",
            cheatsheet.content if cheatsheet.content else "(empty)",
        ).replace(
            "[[TASK_NAME]]", trajectory.task_name
        ).replace(
            "[[SAMPLE_ID]]", trajectory.sample_id
        ).replace(
            "[[OUTCOME]]", outcome
        ).replace(
            "[[SCORE]]", str(trajectory.score)
        ).replace(
            "[[NUM_TURNS]]", str(trajectory.num_turns)
        ).replace(
            "[[CONVERSATION]]", conversation
        )

        # Generate updated cheatsheet
        response = await model_client.generate(
            messages=[{"role": "user", "content": prompt}],
            model=self.model,
            temperature=0.3,  # Slightly creative but mostly consistent
        )

        new_content = response.content.strip()

        # Update the cheatsheet
        cheatsheet.update(new_content)

        # Add metadata about this update
        cheatsheet.metadata[f"update_{cheatsheet.version}"] = {
            "sample_id": trajectory.sample_id,
            "task_name": trajectory.task_name,
            "outcome": outcome,
            "score": trajectory.score,
        }

        return cheatsheet

    async def batch_update(
        self,
        cheatsheet: Cheatsheet,
        trajectories: list["SimulationResult"],
        model_client: "ModelClient",
    ) -> Cheatsheet:
        """Update cheatsheet from multiple trajectories at once.

        This can be more efficient for batch updates, synthesizing
        insights from multiple problems.

        Args:
            cheatsheet: The current cheatsheet.
            trajectories: List of completed simulation results.
            model_client: Model client for reflection.

        Returns:
            Updated cheatsheet.
        """
        # Filter trajectories based on update settings
        filtered = []
        for t in trajectories:
            if t.is_correct and self.update_on_success:
                filtered.append(t)
            elif not t.is_correct and self.update_on_failure:
                filtered.append(t)

        if not filtered:
            return cheatsheet

        # Build a combined reflection prompt
        trajectories_text = []
        for i, t in enumerate(filtered, 1):
            conversation = self._extract_conversation(t.trace)
            outcome = "Success" if t.is_correct else "Failure"
            trajectories_text.append(f"""
--- Trajectory {i} ---
Task: {t.task_name}
Sample ID: {t.sample_id}
Outcome: {outcome} (score: {t.score})
Turns: {t.num_turns}

{conversation}
""")

        batch_prompt = f"""You are updating a cheatsheet based on multiple completed conversation trajectories.

<current_cheatsheet>
{cheatsheet.content if cheatsheet.content else "(empty)"}
</current_cheatsheet>

<trajectories>
{"".join(trajectories_text)}
</trajectories>

Synthesize insights from all trajectories to update the cheatsheet. Look for:
1. Common patterns across successful/failed attempts
2. Critical information that needed to be preserved
3. Effective strategies and pitfalls to avoid

Provide an updated, concise cheatsheet:"""

        response = await model_client.generate(
            messages=[{"role": "user", "content": batch_prompt}],
            model=self.model,
            temperature=0.3,
        )

        cheatsheet.update(response.content.strip())

        # Record batch update metadata
        cheatsheet.metadata[f"batch_update_{cheatsheet.version}"] = {
            "num_trajectories": len(filtered),
            "sample_ids": [t.sample_id for t in filtered],
        }

        return cheatsheet
