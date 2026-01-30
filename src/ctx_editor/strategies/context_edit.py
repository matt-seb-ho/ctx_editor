"""Fixed context editing strategy."""

from typing import TYPE_CHECKING, Optional

from .base import BaseStrategy
from ..core.types import Message
from ..utils.helpers import load_prompt

if TYPE_CHECKING:
    from ..core.trace import ConversationTrace
    from ..cheatsheet.cheatsheet import Cheatsheet
    from ..models.base import ModelClient


DEFAULT_EDITOR_PROMPT = """\
You are a context editor. Your task is to condense the conversation history into a concise summary that preserves essential information while removing content that could mislead the assistant.

Given the conversation so far, create a condensed version that:
1. Preserves the user's original request and key requirements
2. Keeps track of all revealed information and constraints
3. Maintains ONLY still-valid progress and intermediate results
4. Removes redundant back-and-forth while keeping critical context

IMPORTANT - Remove or correct these common sources of confusion:
- Premature answer attempts that were later shown to be wrong
- Invalid assumptions that were corrected by subsequent information
- Outdated intermediate work that was invalidated by new constraints
- Incorrect reasoning paths that led nowhere

<conversation>
{conversation}
</conversation>

{cheatsheet_section}

Provide a condensed context that the assistant can use to continue helping the user. Focus on information density and accuracy - include only what the assistant needs to know, and ensure nothing misleading remains.

Condensed context:"""


class ContextEditStrategy(BaseStrategy):
    """Fixed context editing before every assistant turn.

    This strategy compresses the conversation history into a condensed form
    before each assistant response, reducing context length while preserving
    essential information.
    """

    def __init__(
        self,
        editor_prompt: Optional[str] = None,
        editor_prompt_file: Optional[str] = None,
        editor_model: str = "gpt-4o-mini",
        use_cheatsheet: bool = False,
        cheatsheet_target: str = "context_editor",
    ):
        """Initialize the context edit strategy.

        Args:
            editor_prompt: Custom prompt for the context editor.
            editor_prompt_file: Path to prompt file (alternative to editor_prompt).
            editor_model: Model to use for context editing.
            use_cheatsheet: Whether to include cheatsheet in editor input.
            cheatsheet_target: Where cheatsheet is used ('context_editor' or 'assistant').
        """
        if editor_prompt_file:
            self.editor_prompt = load_prompt(editor_prompt_file)
        elif editor_prompt:
            self.editor_prompt = editor_prompt
        else:
            self.editor_prompt = DEFAULT_EDITOR_PROMPT

        self.editor_model = editor_model
        self.use_cheatsheet = use_cheatsheet
        self.cheatsheet_target = cheatsheet_target

    def _build_editor_input(
        self,
        trace: "ConversationTrace",
        cheatsheet: Optional["Cheatsheet"],
    ) -> str:
        """Build the input for the context editor.

        Args:
            trace: The current conversation trace.
            cheatsheet: Optional cheatsheet to include.

        Returns:
            Formatted editor prompt.
        """
        # Get conversation as string (skip system message - we'll preserve it separately)
        conversation_str = trace.get_conversation_string(skip_system=True)

        # Build cheatsheet section if applicable
        cheatsheet_section = ""
        if self.use_cheatsheet and cheatsheet and cheatsheet.content:
            if self.cheatsheet_target == "context_editor":
                cheatsheet_section = f"""
<cheatsheet>
Use this cheatsheet to help identify what information is most important to preserve:
{cheatsheet.content}
</cheatsheet>
"""

        # Format the editor prompt
        prompt = self.editor_prompt.format(
            conversation=conversation_str,
            cheatsheet_section=cheatsheet_section,
        )

        return prompt

    async def prepare_context(
        self,
        trace: "ConversationTrace",
        cheatsheet: Optional["Cheatsheet"],
        model_client: "ModelClient",
    ) -> list[Message]:
        """Generate edited context for the assistant.

        The context is structured as:
        [system_message, edited_context_as_assistant_msg, last_user_message]

        Args:
            trace: The current conversation trace.
            cheatsheet: Optional cheatsheet for guidance.
            model_client: Model client for generating the edit.

        Returns:
            Condensed context messages.
        """
        # If this is the first turn (only system + user), no editing needed
        if trace.num_assistant_turns == 0:
            messages = self._messages_to_list(trace)
            if self.use_cheatsheet and cheatsheet and self.cheatsheet_target == "assistant":
                messages = self._inject_cheatsheet(messages, cheatsheet, target="system")
            return messages

        # Build editor input
        editor_input = self._build_editor_input(
            trace,
            cheatsheet if self.use_cheatsheet else None,
        )

        # Generate edited context
        response = await model_client.generate(
            messages=[{"role": "user", "content": editor_input}],
            model=self.editor_model,
            temperature=0.0,
        )
        edited_context = response.content

        # Log the context edit operation for auditing
        trace.add_log("context_edit_output", {
            "edited_context": edited_context,
            "editor_model": self.editor_model,
            "original_turn_count": trace.num_user_turns,
        })

        # Build the new context:
        # 1. Original system message
        # 2. Edited context as a "prior context" assistant message
        # 3. Last user message
        messages = []

        # Add system message
        system_msg = trace.system_message
        if system_msg:
            system_content = system_msg.content
            if self.use_cheatsheet and cheatsheet and self.cheatsheet_target == "assistant":
                system_content += f"\n\n<cheatsheet>\n{cheatsheet.content}\n</cheatsheet>"
            messages.append(Message(role="system", content=system_content))

        # Add a user message explaining this is condensed context, then the edited context
        messages.append(Message(
            role="user",
            content="[Prior conversation context, condensed]",
        ))
        messages.append(Message(
            role="assistant",
            content=edited_context,
        ))

        # Add last user message
        last_user = trace.last_user_message
        if last_user:
            messages.append(Message(role="user", content=last_user.content))

        return messages
