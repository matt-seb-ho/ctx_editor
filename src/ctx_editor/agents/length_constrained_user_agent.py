"""Length-constrained natural user agent with per-turn and total token budgets."""

from typing import TYPE_CHECKING, Any

from ..paths import PROMPTS_DIR
from .user_agent import UserResponse

if TYPE_CHECKING:
    from ..core.trace import ConversationTrace
    from ..models.base import ModelClient


LENGTH_CONSTRAINED_PROMPT = (PROMPTS_DIR / "length_constrained_user_agent.txt").read_text()


class LengthConstrainedUserAgent:
    """User agent that sees the full problem and reveals info naturally, subject to token budgets.

    Like NaturalUserAgent, this agent sees the full problem description and presents
    it conversationally. Additionally, it enforces per-turn and total token budgets
    to produce turn lengths comparable to the LiC sharded setting.

    Token budgeting uses two levels:
    - Soft (prompt): the model is told a word budget to aim for.
    - Hard (API): max_tokens is set slightly above the soft budget (via hard_cap_multiplier)
      so the model can finish its thought gracefully without mid-sentence truncation.
    Total budget tracking uses actual completion_tokens from the API.
    """

    def __init__(
        self,
        task: Any,
        model: str = "gpt-4o-mini",
        total_token_budget: int = 500,
        per_turn_token_budget: int = 150,
        hard_cap_multiplier: float = 1.2,
        include_shards: bool = False,
    ):
        self.task = task
        self.model = model
        self.total_token_budget = total_token_budget
        self.per_turn_token_budget = per_turn_token_budget
        self.hard_cap_multiplier = hard_cap_multiplier
        self.include_shards = include_shards
        self.tokens_used = 0
        self._problem_description: str | None = None

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
    ) -> UserResponse:
        """Generate the next user response."""
        tokens_remaining = self.total_token_budget - self.tokens_used

        # Budget exhausted — signal done
        if tokens_remaining <= 0:
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

        # Approximate words remaining/per-turn (tokens * 0.75)
        words_remaining = max(1, int(tokens_remaining * 0.75))
        words_per_turn = max(1, int(self.per_turn_token_budget * 0.75))

        extra_instructions = ""
        if is_first_turn:
            extra_instructions = (
                "This is your first message. State the core ask or question "
                "without giving all the details, constraints, or examples yet."
            )

        prompt = LENGTH_CONSTRAINED_PROMPT.format(
            problem_description=problem_description,
            conversation_so_far=conversation_so_far,
            words_remaining=words_remaining,
            words_per_turn=words_per_turn,
            extra_instructions=extra_instructions,
        )

        # Soft budget = per_turn_token_budget (communicated in prompt as word count)
        # Hard cap = soft * multiplier (passed to API), capped by remaining total budget
        hard_cap = int(self.per_turn_token_budget * self.hard_cap_multiplier)
        max_tokens = min(hard_cap, tokens_remaining)

        response = await model_client.generate(
            messages=[{"role": "user", "content": prompt}],
            model=self.model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Track actual usage against total budget
        self.tokens_used += response.completion_tokens

        return UserResponse(
            content=response.content,
            shard_id=None,
            cost_usd=response.total_usd,
            model_response=response,
        )
