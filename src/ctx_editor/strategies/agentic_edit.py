"""Agent-decided context editing strategy."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from .base import BaseStrategy
from .baseline import BaselineStrategy
from .context_edit import ContextEditStrategy
from ..core.types import Message

if TYPE_CHECKING:
    from ..core.trace import ConversationTrace
    from ..cheatsheet.cheatsheet import Cheatsheet
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

Respond with a JSON object:
{{
    "should_edit": true/false,
    "reasoning": "Brief explanation of your decision"
}}"""


@dataclass
class EditDecision:
    """Decision about whether to edit the context."""
    should_edit: bool
    reasoning: str


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
        use_cheatsheet: bool = False,
        cheatsheet_target: str = "context_editor",
    ):
        """Initialize the agentic edit strategy.

        Args:
            decision_prompt: Custom prompt for the edit decision.
            decision_model: Model to use for deciding whether to edit.
            editor_model: Model to use for context editing.
            edit_threshold_turns: Minimum turns before considering editing.
            use_cheatsheet: Whether to use cheatsheet.
            cheatsheet_target: Where cheatsheet is used.
        """
        self.decision_prompt = decision_prompt or DECISION_PROMPT
        self.decision_model = decision_model
        self.edit_threshold_turns = edit_threshold_turns

        # Create the underlying strategies
        self.baseline_strategy = BaselineStrategy(
            use_cheatsheet=use_cheatsheet,
            cheatsheet_target="system" if cheatsheet_target == "assistant" else "system",
        )
        self.edit_strategy = ContextEditStrategy(
            editor_model=editor_model,
            use_cheatsheet=use_cheatsheet,
            cheatsheet_target=cheatsheet_target,
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
            EditDecision with the decision and reasoning.
        """
        # Don't edit if conversation is short
        if trace.num_user_turns < self.edit_threshold_turns:
            return EditDecision(
                should_edit=False,
                reasoning=f"Conversation has fewer than {self.edit_threshold_turns} turns",
            )

        # Ask the model
        conversation_str = trace.get_conversation_string(skip_system=True)
        prompt = self.decision_prompt.format(conversation=conversation_str)

        response = await model_client.generate_json(
            messages=[{"role": "user", "content": prompt}],
            model=self.decision_model,
            temperature=0.0,
        )

        result = response.content
        return EditDecision(
            should_edit=result.get("should_edit", False),
            reasoning=result.get("reasoning", ""),
        )

    async def prepare_context(
        self,
        trace: "ConversationTrace",
        cheatsheet: Optional["Cheatsheet"],
        model_client: "ModelClient",
    ) -> list[Message]:
        """Prepare context, deciding whether to edit first.

        Args:
            trace: The current conversation trace.
            cheatsheet: Optional cheatsheet.
            model_client: Model client for decisions and editing.

        Returns:
            Either the full context or edited context based on decision.
        """
        decision = await self._should_edit(trace, model_client)

        # Log the decision
        trace.add_log("edit_decision", {
            "should_edit": decision.should_edit,
            "reasoning": decision.reasoning,
        })

        if decision.should_edit:
            return await self.edit_strategy.prepare_context(trace, cheatsheet, model_client)
        else:
            return await self.baseline_strategy.prepare_context(trace, cheatsheet, model_client)
