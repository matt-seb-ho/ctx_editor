"""Fixed context editing strategy."""

import re
from typing import TYPE_CHECKING, Optional

from ...core.types import Message
from ...utils.helpers import load_prompt
from ..base import BaseStrategy
from ..prompt_registry import get_editor_prompt

if TYPE_CHECKING:
    from ...core.trace import ConversationTrace
    from ...memory.base import MemoryModule
    from ...models.base import ModelClient


DEFAULT_EDITOR_PROMPT = """\
You are a context editor for a multi-turn conversation. Your job is to produce a clean \
context that helps the assistant avoid repeating past mistakes.

CRITICAL PRINCIPLE: The user's messages are the source of truth. The assistant's prior \
responses may contain wrong assumptions, incorrect approaches, or errors that snowballed \
across turns. You must clearly separate what the USER said from what the ASSISTANT tried.

<conversation>
{conversation}
</conversation>

{memory_section}

Produce your output in these two clearly separated sections:

<user_intent>
Collate ONLY information from the user's messages (and system message if present). Include:
- The user's goal/question
- All requirements, constraints, and specifications the user has provided
- Any examples, clarifications, or corrections from the user

IMPORTANT:
- Do NOT include the assistant's interpretations, assumptions, or invented details here.
- If the user didn't specify something, do NOT fill it in from the assistant's choices — \
leave it unspecified.
- If the assistant added requirements or constraints the user never mentioned, do NOT include them.
- If the user provided concrete examples, include them verbatim — they are the strongest \
signal for resolving ambiguity.
</user_intent>

<approach_evaluation>
Critically evaluate the assistant's current approach:

1. ERRORS: List specific mistakes in the assistant's solution. Check whether the output \
format/structure matches what the user asked for (e.g., is the assistant returning something \
different from what was requested?).

2. UNGROUNDED ASSUMPTIONS: List any assumptions the assistant introduced that the user never \
stated. Only flag these if they are likely causing incorrect behavior.

3. CORRECTIVE DIRECTION: Based on the errors found and the user's examples/constraints, \
state specifically what the assistant should do differently. Don't just say "reconsider the \
approach" — propose a concrete direction grounded in the user's messages. If the user provided \
examples, use them to determine the correct interpretation.

Do not flag ambiguity unless it's causing the assistant to do the wrong thing. If the user \
hasn't specified something and the assistant's default seems reasonable, that's fine. The goal \
is to fix actual errors, not to enumerate every unspecified detail.

If the assistant's approach is broadly correct but has minor issues, say so — don't make it \
sound worse than it is. If it has fundamental problems, say so clearly.
</approach_evaluation>"""

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
        prompt_version: Optional[str] = None,
        editor_model: str = "gpt-4o-mini",
        editor_timeout: int = 60,
        editor_max_tokens: Optional[int] = None,
        editor_reasoning_effort: Optional[str] = None,
        max_resets: int = 3,
        use_memory: bool = False,
        memory_target: str = "context_editor",
    ):
        """Initialize the context edit strategy.

        Args:
            editor_prompt: Custom prompt for the context editor (highest priority).
            editor_prompt_file: Path to prompt file (second priority).
            prompt_version: Named version from prompt registry (e.g., 'v2', 'v3').
            editor_model: Model to use for context editing.
            editor_timeout: Timeout in seconds for editor model calls.
            editor_max_tokens: Max tokens for editor model calls.
            editor_reasoning_effort: Reasoning effort for editor model.
            max_resets: Maximum number of context resets per conversation.
            use_memory: Whether to include memory in editor input.
            memory_target: Where memory is used ('context_editor' or 'assistant').
        """
        if editor_prompt_file:
            self.editor_prompt = load_prompt(editor_prompt_file)
        elif editor_prompt:
            self.editor_prompt = editor_prompt
        elif prompt_version:
            self.editor_prompt = get_editor_prompt(prompt_version)
        else:
            self.editor_prompt = DEFAULT_EDITOR_PROMPT

        self.editor_model = editor_model
        self.editor_timeout = editor_timeout
        self.editor_max_tokens = editor_max_tokens
        self.editor_reasoning_effort = editor_reasoning_effort
        self.max_resets = max_resets
        self.use_memory = use_memory
        self.memory_target = memory_target

    @staticmethod
    def _parse_editor_output(text: str) -> tuple[str, str]:
        """Parse structured editor output into user_intent and approach_evaluation.

        Returns:
            Tuple of (user_intent, approach_evaluation). Either may be empty if
            the editor didn't produce structured output.
        """
        user_match = re.search(
            r"<user_intent>(.*?)</user_intent>", text, re.DOTALL
        )
        eval_match = re.search(
            r"<approach_evaluation>(.*?)</approach_evaluation>", text, re.DOTALL
        )
        user_intent = user_match.group(1).strip() if user_match else ""
        approach_eval = eval_match.group(1).strip() if eval_match else ""
        return user_intent, approach_eval

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

        # If we've hit the max reset limit, stop editing and pass through
        if trace.num_resets >= self.max_resets:
            return trace.get_active_messages()

        # Build editor input (uses active conversation only)
        editor_input = self._build_editor_input(
            trace,
            memory if self.use_memory else None,
        )

        # Generate edited context
        generate_kwargs: dict = {
            "messages": [{"role": "user", "content": editor_input}],
            "model": self.editor_model,
            "temperature": 0.0,
            "timeout": self.editor_timeout,
        }
        if self.editor_max_tokens:
            generate_kwargs["max_tokens"] = self.editor_max_tokens
        if self.editor_reasoning_effort:
            generate_kwargs["reasoning_effort"] = self.editor_reasoning_effort
        response = await model_client.generate(**generate_kwargs)
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

        # Build the new context with structured separation:
        # 1. System message (original + approach evaluation as advisory context)
        # 2. User intent collation as user message (source of truth)
        # 3. Last user message
        new_messages = []

        # Parse the structured editor output
        user_intent, approach_eval = self._parse_editor_output(edited_context)

        # Add system message with approach evaluation appended
        system_msg = trace.system_message
        system_content = system_msg.content if system_msg else ""
        if approach_eval:
            system_content += (
                "\n\n<context_edit_notes>\n"
                "An independent review of the prior conversation identified areas "
                "for improvement. Consider this feedback when formulating your response.\n\n"
                f"{approach_eval}\n"
                "</context_edit_notes>"
            )
        new_messages.append(Message(role="system", content=system_content))

        # Add user intent collation as user message (this is the source of truth)
        user_context = user_intent if user_intent else edited_context
        new_messages.append(
            Message(
                role="user",
                content=(
                    "[The following summarizes what I've told you so far across "
                    "multiple messages. Please use this as the basis for your response.]\n\n"
                    + user_context
                ),
            )
        )

        # Add last user message
        last_user = trace.last_user_message
        if last_user:
            new_messages.append(Message(role="user", content=last_user.content))

        # Reset the trace's active conversation to the edited context
        trace.reset_conversation(new_messages, label="context_edit")

        return trace.get_active_messages()
