"""Natural user agent that sees the full problem and reveals info conversationally.

No token budget constraints — the model decides how to pace information delivery
naturally. Multi-turn behavior arises from the instruction to break up the problem
across messages, not from artificial length limits.
"""

from typing import TYPE_CHECKING, Any, Optional

from ..core.types import ReasoningEffort
from ..paths import PROMPTS_DIR
from .user_agent import UserResponse

if TYPE_CHECKING:
    from ..core.trace import ConversationTrace
    from ..models.base import ModelClient


NATURAL_USER_PROMPT = (PROMPTS_DIR / "natural_user_agent.txt").read_text()


class NaturalUserAgent:
    """User agent that sees the full problem and presents it naturally without length constraints.

    Unlike the sharded UserAgent which reveals pre-defined shards one at a time,
    this agent sees the full problem description and decides how to present
    information across turns. Unlike LengthConstrainedUserAgent, there are no
    token budgets — the model paces information delivery on its own.

    Clarification policy: the agent may only answer clarifying questions using
    information contained in or clearly implied by the original problem description.
    It does not provide information beyond the single-turn spec.
    """

    def __init__(
        self,
        task: Any,
        model: str = "gpt-4o-mini",
        include_shards: bool = False,
        max_turns: int = 20,
    ):
        self.task = task
        self.model = model
        self.include_shards = include_shards
        self.max_turns = max_turns
        self.turns_used = 0
        self._problem_description: str | None = None
        self._all_info_shared = False

    def _get_problem_description(self, sample: dict[str, Any]) -> str:
        """Get the full problem description, caching after first call."""
        if self._problem_description is None:
            self._problem_description = self.task.populate_fully_specific_prompt(sample)
            if self.include_shards and "shards" in sample:
                shard_text = "\n".join(f"- {s['shard']}" for s in sample["shards"])
                self._problem_description += (
                    f"\n\n(The problem can be broken into these pieces:\n{shard_text})"
                )
        return self._problem_description

    async def generate_response(
        self,
        trace: "ConversationTrace",
        sample: dict[str, Any],
        model_client: "ModelClient",
        temperature: float = 1.0,
        reasoning_effort: Optional[ReasoningEffort] = None,
    ) -> UserResponse:
        """Generate the next user response."""
        self.turns_used += 1

        # Safety cap on turns
        if self.turns_used > self.max_turns:
            return UserResponse(
                content="I've shared all the relevant information I have.",
                shard_id=None,
                cost_usd=0.0,
                budget_exhausted=True,
            )

        problem_description = self._get_problem_description(sample)
        is_first_turn = trace.num_user_turns == 0

        # Build conversation context (skip system prompt — not relevant to user)
        conversation_so_far = trace.get_conversation_string(skip_system=True)
        if not conversation_so_far:
            conversation_so_far = "(No conversation yet — this is your first message.)"

        extra_instructions = ""
        if is_first_turn:
            extra_instructions = (
                "This is your first message. State the core ask or question "
                "without giving all the details, constraints, or examples yet."
            )

        prompt = NATURAL_USER_PROMPT.format(
            problem_description=problem_description,
            conversation_so_far=conversation_so_far,
            extra_instructions=extra_instructions,
        )

        response = await model_client.generate(
            messages=[{"role": "user", "content": prompt}],
            model=self.model,
            temperature=temperature,
            reasoning_effort=reasoning_effort,
        )

        return UserResponse(
            content=response.content,
            shard_id=None,
            cost_usd=response.total_usd,
            model_response=response,
        )
