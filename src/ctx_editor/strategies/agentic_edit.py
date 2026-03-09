"""Agent-decided context editing strategy."""

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from ..core.types import Message
from .base import BaseStrategy
from .baseline import BaselineStrategy
from .context_edit import ContextEditStrategy, DEFAULT_EDITOR_PROMPT, MEMORY_SECTION_TEMPLATE

if TYPE_CHECKING:
    from ..core.trace import ConversationTrace
    from ..memory.base import MemoryModule
    from ..models.base import ModelClient


DECISION_PROMPT = """\
Analyze the current conversation and decide whether context compression would be beneficial.

<conversation>
{conversation}
</conversation>

Consider these common failure modes that compression can help address:
1. Premature answer attempts - did the assistant make guesses that were later invalidated?
2. Invalid assumptions - are there assumptions in the context that turned out to be wrong?
3. Outdated intermediate work - is there prior reasoning/work that was invalidated by new information?
4. Redundant clarifications - are there repeated exchanges that can be summarized?
5. Information scatter - is critical information spread across many turns?

Compression is beneficial when the context contains invalidated work or wrong assumptions that might mislead the assistant. Compression is risky if it might lose still-valid critical details.

Respond with your decision and analysis using the following format. Always provide thorough notes \
regardless of your decision — these notes are used for downstream editing and error analysis.

<notes>
Your detailed analysis of the conversation state. Include:
- What failure modes (if any) are present in the conversation
- What information is critical to preserve
- What content is misleading, outdated, or redundant
- How an edit might help or hurt at this point
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
        decision_model: str = "gpt-4o-mini",
        editor_model: str = "gpt-4o-mini",
        edit_threshold_turns: int = 3,
        use_memory: bool = False,
        memory_target: str = "context_editor",
    ):
        """Initialize the agentic edit strategy.

        Args:
            decision_prompt: Custom prompt for the edit decision.
            decision_model: Model to use for deciding whether to edit.
            editor_model: Model to use for context editing.
            edit_threshold_turns: Minimum turns before considering editing.
            use_memory: Whether to use memory.
            memory_target: Where memory is used.
        """
        self.decision_prompt = decision_prompt or DECISION_PROMPT
        self.decision_model = decision_model
        self.edit_threshold_turns = edit_threshold_turns

        # Create the underlying strategies
        self.baseline_strategy = BaselineStrategy(
            use_memory=use_memory,
            memory_target="system" if memory_target == "assistant" else "system",
        )
        self.edit_strategy = ContextEditStrategy(
            editor_model=editor_model,
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

        response = await model_client.generate(
            messages=[{"role": "user", "content": prompt}],
            model=self.decision_model,
            temperature=0.0,
        )

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
The following analysis was produced during the decision to compress this context.
Use it to guide your editing — it identifies key issues to address:

{decision_notes}
</decision_analysis>

Condensed context:"""

        # Replace the trailing "Condensed context:" with the augmented version
        if base_prompt.rstrip().endswith("Condensed context:"):
            base_prompt = base_prompt.rstrip()[: -len("Condensed context:")].rstrip()
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

        # Generate edited context
        response = await model_client.generate(
            messages=[{"role": "user", "content": editor_input}],
            model=self.edit_strategy.editor_model,
            temperature=0.0,
        )
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

        # Build new context: system + condensed prior context + last user message
        new_messages = []

        system_msg = trace.system_message
        if system_msg:
            new_messages.append(Message(role="system", content=system_msg.content))

        new_messages.append(
            Message(role="user", content="[Prior conversation context, condensed]")
        )
        new_messages.append(
            Message(role="assistant", content=edited_context)
        )

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
