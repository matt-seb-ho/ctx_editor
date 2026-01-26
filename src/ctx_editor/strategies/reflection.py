"""Reflection strategy - append reflection without deleting context."""

from typing import TYPE_CHECKING, Optional

from .base import BaseStrategy
from ..core.types import Message
from ..utils.helpers import load_prompt

if TYPE_CHECKING:
    from ..core.trace import ConversationTrace
    from ..cheatsheet.cheatsheet import Cheatsheet
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


class ReflectionStrategy(BaseStrategy):
    """Append a reflection to the context without removing history.

    This strategy generates a reflection/summary of the conversation
    and appends it as additional context, preserving all original messages.
    """

    def __init__(
        self,
        reflection_prompt: Optional[str] = None,
        reflection_prompt_file: Optional[str] = None,
        reflection_model: str = "gpt-4o-mini",
        use_cheatsheet: bool = False,
        inject_as: str = "system",  # 'system' or 'user'
        min_turns_for_reflection: int = 2,
    ):
        """Initialize the reflection strategy.

        Args:
            reflection_prompt: Custom prompt for generating reflections.
            reflection_prompt_file: Path to prompt file.
            reflection_model: Model to use for reflection generation.
            use_cheatsheet: Whether to include cheatsheet in reflection prompt.
            inject_as: How to inject the reflection ('system' or 'user').
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
        self.inject_as = inject_as
        self.min_turns_for_reflection = min_turns_for_reflection

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
        conversation_str = trace.get_conversation_string(skip_system=True)

        # Build cheatsheet section
        cheatsheet_section = ""
        if self.use_cheatsheet and cheatsheet and cheatsheet.content:
            cheatsheet_section = f"""
<cheatsheet>
Reference this cheatsheet when reflecting:
{cheatsheet.content}
</cheatsheet>
"""

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
        """Prepare context with appended reflection.

        Args:
            trace: The current conversation trace.
            cheatsheet: Optional cheatsheet.
            model_client: Model client for reflection generation.

        Returns:
            Full context with reflection appended.
        """
        messages = self._messages_to_list(trace)

        # Don't add reflection if conversation is too short
        if trace.num_user_turns < self.min_turns_for_reflection:
            return messages

        # Generate reflection
        reflection = await self._generate_reflection(trace, cheatsheet, model_client)

        # Log the reflection
        trace.add_log("reflection_generated", {"reflection": reflection})

        # Inject reflection
        if self.inject_as == "system":
            # Append to system message
            for msg in messages:
                if msg.role == "system":
                    msg.content += f"\n\n<reflection>\nConversation state: {reflection}\n</reflection>"
                    break
        else:
            # Insert before last user message
            last_user_idx = None
            for i in range(len(messages) - 1, -1, -1):
                if messages[i].role == "user":
                    last_user_idx = i
                    break

            if last_user_idx is not None:
                reflection_msg = Message(
                    role="user",
                    content=f"[System reflection on conversation so far: {reflection}]",
                )
                messages.insert(last_user_idx, reflection_msg)

        return messages
