"""Agent-decided context editing strategy."""

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from ...core.types import Message
from ..base import BaseStrategy
from ..baseline import BaselineStrategy
from .context_edit import ContextEditStrategy, DEFAULT_EDITOR_PROMPT, MEMORY_SECTION_TEMPLATE
from ..prompt_registry import get_decision_prompt

if TYPE_CHECKING:
    from ...core.trace import ConversationTrace
    from ...memory.base import MemoryModule
    from ...models.base import ModelClient


DECISION_PROMPT = """\
Analyze this conversation and decide: should the assistant get a fresh start?

<conversation>
{conversation}
</conversation>

A context reset clears the conversation and gives the assistant a clean summary of what the \
user actually asked for, helping it avoid repeating mistakes.

Answer these questions one by one:

1. WHAT DID THE USER ASK FOR? (Summarize the user's actual requirements in 1-2 sentences)

2. WHAT IS THE ASSISTANT DOING? (Summarize the assistant's current approach in 1-2 sentences)

3. IS THE ASSISTANT'S APPROACH CORRECT? Check for these specific problems:
   - Has the assistant introduced parameters, function names, or return types the user never mentioned?
   - Is the assistant building on an earlier wrong answer instead of reconsidering?
   - Has the user corrected the assistant, but the assistant ignored or misunderstood the correction?
   - Is the assistant producing similar wrong outputs repeatedly?

4. DECISION: Based on your analysis, should we reset? Answer "yes" if the assistant is on a \
fundamentally wrong path, or "no" if it is making reasonable progress.

You MUST answer all 4 questions. Format your response exactly like this:

<notes>
1. User wants: [your answer]
2. Assistant is: [your answer]
3. Problems found: [your answer, or "None — approach looks correct"]
</notes>

<edit_decision>yes or no</edit_decision>"""


def _parse_xml_tag(text: str, tag: str) -> str:
    """Extract content from an XML tag in text."""
    match = re.search(rf"<{tag}>(.*?)</{tag}>", text, re.DOTALL)
    return match.group(1).strip() if match else ""


@dataclass
class EditDecision:
    """Decision about whether to edit the context."""

    should_edit: bool
    reasoning: str
    notes: str


class AgenticEditStrategy(BaseStrategy):
    """Strategy where the model decides whether to edit context.

    This strategy first asks the model whether context compression would
    be beneficial, then either applies editing or returns the full context.
    """

    def __init__(
        self,
        decision_prompt: Optional[str] = None,
        prompt_version: Optional[str] = None,
        decision_model: str = "gpt-4o-mini",
        editor_model: str = "gpt-4o-mini",
        editor_timeout: int = 60,
        editor_max_tokens: Optional[int] = None,
        editor_reasoning_effort: Optional[str] = None,
        edit_threshold_turns: int = 3,
        use_memory: bool = False,
        memory_target: str = "context_editor",
    ):
        """Initialize the agentic edit strategy.

        Args:
            decision_prompt: Custom prompt for the edit decision (highest priority).
            prompt_version: Named version from prompt registry (e.g., 'v2', 'v3').
            decision_model: Model to use for deciding whether to edit.
            editor_model: Model to use for context editing.
            editor_timeout: Timeout in seconds for editor model calls.
            editor_max_tokens: Max tokens for editor model calls.
            editor_reasoning_effort: Reasoning effort for decision model only.
            edit_threshold_turns: Minimum turns before considering editing.
            use_memory: Whether to use memory.
            memory_target: Where memory is used.
        """
        if decision_prompt:
            self.decision_prompt = decision_prompt
        elif prompt_version:
            self.decision_prompt = get_decision_prompt(prompt_version)
        else:
            self.decision_prompt = DECISION_PROMPT
        self.decision_model = decision_model
        self.editor_timeout = editor_timeout
        self.editor_max_tokens = editor_max_tokens
        self.editor_reasoning_effort = editor_reasoning_effort
        self.edit_threshold_turns = edit_threshold_turns

        # Create the underlying strategies
        self.baseline_strategy = BaselineStrategy(
            use_memory=use_memory,
            memory_target="system" if memory_target == "assistant" else "system",
        )
        self.edit_strategy = ContextEditStrategy(
            editor_model=editor_model,
            editor_timeout=editor_timeout,
            editor_max_tokens=editor_max_tokens,
            prompt_version=prompt_version,
            use_memory=use_memory,
            memory_target=memory_target,
        )

    async def _should_edit(
        self,
        trace: "ConversationTrace",
        model_client: "ModelClient",
    ) -> EditDecision:
        """Decide whether to edit the context.

        Args:
            trace: The current conversation trace.
            model_client: Model client for the decision.

        Returns:
            EditDecision with the decision, reasoning, and analysis notes.
        """
        # Don't edit if conversation is short
        if trace.num_user_turns < self.edit_threshold_turns:
            return EditDecision(
                should_edit=False,
                reasoning=f"Conversation has fewer than {self.edit_threshold_turns} turns",
                notes="",
            )

        # Ask the model
        conversation_str = trace.get_conversation_string(skip_system=False)
        prompt = self.decision_prompt.format(conversation=conversation_str)

        generate_kwargs: dict = {
            "messages": [{"role": "user", "content": prompt}],
            "model": self.decision_model,
            "temperature": 0.0,
            "timeout": self.editor_timeout,
        }
        if self.editor_reasoning_effort:
            generate_kwargs["reasoning_effort"] = self.editor_reasoning_effort
        response = await model_client.generate(**generate_kwargs)

        text = response.content
        decision_str = _parse_xml_tag(text, "edit_decision").lower()
        notes = _parse_xml_tag(text, "notes")
        should_edit = decision_str.startswith("yes")

        return EditDecision(
            should_edit=should_edit,
            reasoning=decision_str,
            notes=notes,
        )

    def _build_editor_input_with_analysis(
        self,
        trace: "ConversationTrace",
        memory: Optional["MemoryModule"],
        decision_notes: str,
    ) -> str:
        """Build the editor prompt with injected decision analysis.

        Uses the same base editor prompt as ContextEditStrategy, then appends
        the decision analysis so the editor can act on it directly.

        Args:
            trace: The current conversation trace.
            memory: Optional memory module to include.
            decision_notes: Analysis notes from the decision step.

        Returns:
            Formatted editor prompt with decision analysis injected.
        """
        conversation_str = trace.get_conversation_string(skip_system=False)

        memory_section = ""
        if self.edit_strategy.use_memory and memory and memory.content:
            if self.edit_strategy.memory_target == "context_editor":
                memory_section = MEMORY_SECTION_TEMPLATE.format(
                    memory_content=memory.content
                )

        base_prompt = self.edit_strategy.editor_prompt.format(
            conversation=conversation_str,
            memory_section=memory_section,
        )

        # Inject decision analysis before the final instruction
        analysis_section = f"""
<decision_analysis>
The following analysis was produced during the decision to reset this context.
Use it to guide your editing — it identifies specific problems with the assistant's approach:

{decision_notes}
</decision_analysis>"""

        # Replace the trailing </approach_evaluation> marker with the augmented version
        if base_prompt.rstrip().endswith("</approach_evaluation>"):
            return base_prompt + "\n" + analysis_section
        else:
            return base_prompt + "\n" + analysis_section

    async def _perform_edit_with_analysis(
        self,
        trace: "ConversationTrace",
        memory: Optional["MemoryModule"],
        model_client: "ModelClient",
        decision_notes: str,
    ) -> list[Message]:
        """Perform context editing with injected decision analysis (mutates trace).

        Follows the same flow as ContextEditStrategy.prepare_context() but uses
        an augmented prompt that includes the decision analysis notes.

        Args:
            trace: The current conversation trace (will be mutated).
            memory: Optional memory module for guidance.
            model_client: Model client for generating the edit.
            decision_notes: Analysis notes from the decision step.

        Returns:
            Active messages from the trace after reset.
        """
        # Inject memory to assistant (via system message) if configured
        if self.edit_strategy.use_memory and memory:
            if self.edit_strategy.memory_target == "assistant":
                self._inject_memory_to_trace(trace, memory, target="system")

        # If this is the first turn, no editing needed
        if trace.num_assistant_turns == 0:
            return trace.get_active_messages()

        # Build editor input with decision analysis injected
        editor_input = self._build_editor_input_with_analysis(
            trace, memory, decision_notes
        )

        # Generate edited context (no reasoning_effort — editor needs full reasoning)
        generate_kwargs: dict = {
            "messages": [{"role": "user", "content": editor_input}],
            "model": self.edit_strategy.editor_model,
            "temperature": 0.0,
            "timeout": self.editor_timeout,
        }
        if self.editor_max_tokens:
            generate_kwargs["max_tokens"] = self.editor_max_tokens
        response = await model_client.generate(**generate_kwargs)
        edited_context = response.content

        # Log the context edit operation
        trace.add_log(
            "context_edit_output",
            {
                "edited_context": edited_context,
                "editor_model": self.edit_strategy.editor_model,
                "original_turn_count": trace.total_user_turns,
                "active_turn_count": trace.num_user_turns,
                "used_decision_analysis": True,
            },
        )

        # Build new context with structured separation (same as ContextEditStrategy)
        new_messages = []

        # Parse the structured editor output
        user_intent, approach_eval = ContextEditStrategy._parse_editor_output(edited_context)

        # Add system message with approach evaluation appended
        system_msg = trace.system_message
        system_content = system_msg.content if system_msg else ""
        if approach_eval:
            system_content += (
                "\n\n<context_edit_notes>\n"
                "The following is an analysis of the prior conversation. The assistant's "
                "previous approach may have had errors. Read this critically and be willing "
                "to take a completely different approach if the evaluation suggests it.\n\n"
                f"{approach_eval}\n"
                "</context_edit_notes>"
            )
        new_messages.append(Message(role="system", content=system_content))

        # Add user intent collation as user message (source of truth)
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

        trace.reset_conversation(new_messages, label="context_edit")

        return trace.get_active_messages()

    async def prepare_context(
        self,
        trace: "ConversationTrace",
        memory: Optional["MemoryModule"],
        model_client: "ModelClient",
    ) -> list[Message]:
        """Prepare context, deciding whether to edit first (mutates trace).

        When editing is chosen, the decision analysis notes are injected into
        the editor prompt so the editor can act on them directly instead of
        re-analyzing the conversation from scratch.

        Args:
            trace: The current conversation trace (will be mutated).
            memory: Optional memory module.
            model_client: Model client for decisions and editing.

        Returns:
            Active messages from the trace after strategy execution.
        """
        decision = await self._should_edit(trace, model_client)

        # Always log the full decision including notes (for error analysis)
        trace.add_log(
            "edit_decision",
            {
                "should_edit": decision.should_edit,
                "reasoning": decision.reasoning,
                "notes": decision.notes,
            },
        )

        if decision.should_edit:
            return await self._perform_edit_with_analysis(
                trace, memory, model_client, decision.notes
            )
        else:
            return await self.baseline_strategy.prepare_context(trace, memory, model_client)
