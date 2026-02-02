"""Reflection strategy - append reflection without deleting context."""

from typing import TYPE_CHECKING, Optional

from ..core.types import Message
from ..utils.helpers import load_prompt
from .base import BaseStrategy

if TYPE_CHECKING:
    from ..cheatsheet.cheatsheet import Cheatsheet
    from ..core.trace import ConversationTrace
    from ..models.base import ModelClient


DEFAULT_REFLECTION_PROMPT = """\
Analyze the conversation so far and provide a brief reflection that will help the assistant respond more effectively.

<conversation>
{conversation}
</conversation>

{cheatsheet_section}

Consider:
1. What is the user's core goal or question?
2. What key information has been revealed so far?
3. What constraints or requirements must the answer satisfy?
4. What progress has been made toward the goal?
5. What information might still be missing?

IMPORTANT - Flag any issues that could mislead the assistant:
- Were there premature answer attempts that turned out to be wrong?
- Are there assumptions in the conversation that were later invalidated?
- Is there intermediate work that is now outdated due to new information?
If any of these exist, explicitly note them so the assistant knows to disregard them.

Provide a concise reflection (2-4 sentences) summarizing the state of the conversation, what the assistant should focus on, and any prior mistakes to avoid repeating:"""

# Explanation added to system message when reflection is used
REFLECTION_SYSTEM_ADDENDUM = """

Note: User messages may contain a <conversation_state_reflection> section at the end. This is NOT part of the user's message - it is automatically injected context from an external system that analyzes conversation state. Use it as helpful context for your response, but do not reference or respond to it directly."""

CHEATSHEET_SECTION_TEMPLATE = """\
<cheatsheet>
Reference this cheatsheet when reflecting:
{cheatsheet_content}
</cheatsheet>
"""

REFLECTION_BLOCK_TEMPLATE = "\n\n<conversation_state_reflection>\n{reflection}\n</conversation_state_reflection>"


class ReflectionStrategy(BaseStrategy):
    """Append a reflection to the context without removing history.

    This strategy generates a reflection/summary of the conversation and appends
    it to the last user message inside <conversation_state_reflection> tags.
    This preserves strict message alternation (system → user → assistant → ...)
    while providing the assistant with helpful context about conversation state.

    The reflection is persisted in the trace, so future turns will see previous
    user messages with their reflections included.
    """

    def __init__(
        self,
        reflection_prompt: Optional[str] = None,
        reflection_prompt_file: Optional[str] = None,
        reflection_model: str = "gpt-4o-mini",
        use_cheatsheet: bool = False,
        min_turns_for_reflection: int = 2,
    ):
        """Initialize the reflection strategy.

        Args:
            reflection_prompt: Custom prompt for generating reflections.
            reflection_prompt_file: Path to prompt file.
            reflection_model: Model to use for reflection generation.
            use_cheatsheet: Whether to include cheatsheet in reflection prompt.
            min_turns_for_reflection: Minimum user turns before adding reflection.
        """
        if reflection_prompt_file:
            self.reflection_prompt = load_prompt(reflection_prompt_file)
        elif reflection_prompt:
            self.reflection_prompt = reflection_prompt
        else:
            self.reflection_prompt = DEFAULT_REFLECTION_PROMPT

        self.reflection_model = reflection_model
        self.use_cheatsheet = use_cheatsheet
        self.min_turns_for_reflection = min_turns_for_reflection

    def _is_reflection_addendum_added(self, trace: "ConversationTrace") -> bool:
        """Check if the reflection system addendum has already been added."""
        return any(log["type"] == "reflection_addendum_added" for log in trace.logs)

    async def _generate_reflection(
        self,
        trace: "ConversationTrace",
        cheatsheet: Optional["Cheatsheet"],
        model_client: "ModelClient",
    ) -> str:
        """Generate a reflection on the conversation.

        Args:
            trace: The current conversation trace.
            cheatsheet: Optional cheatsheet for guidance.
            model_client: Model client for generation.

        Returns:
            The generated reflection text.
        """
        conversation_str = trace.get_conversation_string(skip_system=False)

        # Build cheatsheet section
        cheatsheet_section = ""
        if self.use_cheatsheet and cheatsheet and cheatsheet.content:
            cheatsheet_section = CHEATSHEET_SECTION_TEMPLATE.format(
                cheatsheet_content=cheatsheet.content
            )

        prompt = self.reflection_prompt.format(
            conversation=conversation_str,
            cheatsheet_section=cheatsheet_section,
        )

        response = await model_client.generate(
            messages=[{"role": "user", "content": prompt}],
            model=self.reflection_model,
            temperature=0.0,
        )

        return response.content

    async def prepare_context(
        self,
        trace: "ConversationTrace",
        cheatsheet: Optional["Cheatsheet"],
        model_client: "ModelClient",
    ) -> list[Message]:
        """Prepare context with appended reflection (mutates trace).

        Mutates the trace by:
        1. Adding explanation to system message about <conversation_state_reflection> tags (once)
        2. Appending reflection inside those tags to the last user message

        The reflection persists in the trace, so future turns see accumulated reflections.

        Args:
            trace: The current conversation trace (will be mutated).
            cheatsheet: Optional cheatsheet.
            model_client: Model client for reflection generation.

        Returns:
            Active messages from the trace.
        """
        # Don't add reflection if conversation is too short
        if trace.num_user_turns < self.min_turns_for_reflection:
            return trace.get_active_messages()

        # Add system addendum explaining reflection tags (only once)
        if not self._is_reflection_addendum_added(trace):
            trace.append_to_system_message(REFLECTION_SYSTEM_ADDENDUM)
            trace.add_log("reflection_addendum_added", {})

        # Generate reflection
        reflection = await self._generate_reflection(trace, cheatsheet, model_client)

        # Log the reflection
        trace.add_log("reflection_generated", {"reflection": reflection})

        # Append reflection to last user message in the trace
        reflection_block = REFLECTION_BLOCK_TEMPLATE.format(reflection=reflection)
        trace.append_to_last_user_message(reflection_block)

        return trace.get_active_messages()
