"""Fixed context editing strategy."""

from typing import TYPE_CHECKING, Optional

from ..core.types import Message
from ..utils.helpers import load_prompt
from .base import BaseStrategy

if TYPE_CHECKING:
    from ..core.trace import ConversationTrace
    from ..memory.base import MemoryModule
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

{memory_section}

Provide a condensed context that the assistant can use to continue helping the user. Focus on information density and accuracy - include only what the assistant needs to know, and ensure nothing misleading remains.

Condensed context:"""

MEMORY_SECTION_TEMPLATE = """\
<cheatsheet>
Use this cheatsheet to help identify what information is most important to preserve:
{memory_content}
</cheatsheet>
"""


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
        use_memory: bool = False,
        memory_target: str = "context_editor",
    ):
        """Initialize the context edit strategy.

        Args:
            editor_prompt: Custom prompt for the context editor.
            editor_prompt_file: Path to prompt file (alternative to editor_prompt).
            editor_model: Model to use for context editing.
            use_memory: Whether to include memory in editor input.
            memory_target: Where memory is used ('context_editor' or 'assistant').
        """
        if editor_prompt_file:
            self.editor_prompt = load_prompt(editor_prompt_file)
        elif editor_prompt:
            self.editor_prompt = editor_prompt
        else:
            self.editor_prompt = DEFAULT_EDITOR_PROMPT

        self.editor_model = editor_model
        self.use_memory = use_memory
        self.memory_target = memory_target

    def _build_editor_input(
        self,
        trace: "ConversationTrace",
        memory: Optional["MemoryModule"],
    ) -> str:
        """Build the input for the context editor.

        Args:
            trace: The current conversation trace.
            memory: Optional memory module to include.

        Returns:
            Formatted editor prompt.
        """
        # Get conversation as string (include system message so editor understands the task)
        conversation_str = trace.get_conversation_string(skip_system=False)

        # Build memory section if applicable
        memory_section = ""
        if self.use_memory and memory and memory.content:
            if self.memory_target == "context_editor":
                memory_section = MEMORY_SECTION_TEMPLATE.format(
                    memory_content=memory.content
                )

        # Format the editor prompt
        prompt = self.editor_prompt.format(
            conversation=conversation_str,
            memory_section=memory_section,
        )

        return prompt

    async def prepare_context(
        self,
        trace: "ConversationTrace",
        memory: Optional["MemoryModule"],
        model_client: "ModelClient",
    ) -> list[Message]:
        """Generate edited context for the assistant (mutates trace).

        Resets the trace's active conversation to:
        [system_message, edited_context_as_assistant_msg, last_user_message]

        This ensures future turns build on the edited context rather than full history.

        Args:
            trace: The current conversation trace (will be mutated).
            memory: Optional memory module for guidance.
            model_client: Model client for generating the edit.

        Returns:
            Active messages from the trace after reset.
        """
        # Inject memory to assistant (via system message) if configured
        if self.use_memory and memory and self.memory_target == "assistant":
            self._inject_memory_to_trace(trace, memory, target="system")

        # If this is the first turn (only system + user), no editing needed
        if trace.num_assistant_turns == 0:
            return trace.get_active_messages()

        # Build editor input (uses active conversation only)
        editor_input = self._build_editor_input(
            trace,
            memory if self.use_memory else None,
        )

        # Generate edited context
        response = await model_client.generate(
            messages=[{"role": "user", "content": editor_input}],
            model=self.editor_model,
            temperature=0.0,
        )
        edited_context = response.content

        # Log the context edit operation for auditing (before reset)
        trace.add_log(
            "context_edit_output",
            {
                "edited_context": edited_context,
                "editor_model": self.editor_model,
                "original_turn_count": trace.total_user_turns,
                "active_turn_count": trace.num_user_turns,
            },
        )

        # Build the new context:
        # 1. Original system message (with memory if already injected)
        # 2. Edited context as a "prior context" assistant message
        # 3. Last user message
        new_messages = []

        # Add system message
        system_msg = trace.system_message
        if system_msg:
            new_messages.append(Message(role="system", content=system_msg.content))

        # Add a user message explaining this is condensed context, then the edited context
        new_messages.append(
            Message(
                role="user",
                content="[Prior conversation context, condensed]",
            )
        )
        new_messages.append(
            Message(
                role="assistant",
                content=edited_context,
            )
        )

        # Add last user message
        last_user = trace.last_user_message
        if last_user:
            new_messages.append(Message(role="user", content=last_user.content))

        # Reset the trace's active conversation to the edited context
        trace.reset_conversation(new_messages, label="context_edit")

        return trace.get_active_messages()
