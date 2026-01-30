"""User simulation agent adapted from LIC."""

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional

from ..core.types import ModelResponse
from ..paths import PROMPTS_DIR
from ..utils.helpers import load_prompt

if TYPE_CHECKING:
    from ..core.trace import ConversationTrace
    from ..models.base import ModelClient


# Load the default prompt from the prompts directory (matches LiC exactly)
DEFAULT_USER_PROMPT = (PROMPTS_DIR / "user_agent.txt").read_text()


@dataclass
class UserResponse:
    """Response from the user agent."""
    content: str
    shard_id: Optional[str] = None
    cost_usd: float = 0.0
    model_response: Optional[ModelResponse] = None  # For detailed usage tracking


class UserAgent:
    """Agent that simulates a user revealing information gradually.

    Adapted from the LIC user_agent.py to work with the async model client.
    """

    def __init__(
        self,
        task: Any,
        model: str = "gpt-4o-mini",
        prompt_file: Optional[str] = None,
    ):
        """Initialize the user agent.

        Args:
            task: The task instance (provides task-specific behavior).
            model: Model to use for user simulation.
            prompt_file: Optional path to custom user prompt.
        """
        self.task = task
        self.model = model
        self.task_name = task.get_task_name() if hasattr(task, "get_task_name") else str(task)

        if prompt_file:
            self.prompt_response = load_prompt(prompt_file)
        else:
            self.prompt_response = DEFAULT_USER_PROMPT

    async def generate_response(
        self,
        trace: "ConversationTrace",
        sample: dict[str, Any],
        model_client: "ModelClient",
        temperature: float = 1.0,
    ) -> UserResponse:
        """Generate the next user response.

        Args:
            trace: Current conversation trace.
            sample: The sample data with shards.
            model_client: Model client for generation.
            temperature: Sampling temperature.

        Returns:
            UserResponse with the message and optionally revealed shard ID.
        """
        num_user_msgs = trace.num_user_turns

        # Some tasks use pre-defined prompts (translation, summary, data2text)
        if self.task_name in ["translation", "summary", "data2text"]:
            if hasattr(self.task, "populate_sharded_prompt"):
                content, shard_id = self.task.populate_sharded_prompt(sample, num_user_msgs)
                return UserResponse(content=content, shard_id=shard_id, cost_usd=0.0)

        # First turn: return the initial query
        if num_user_msgs == 0:
            first_shard = sample["shards"][0]
            return UserResponse(
                content=first_shard["shard"],
                shard_id=first_shard["shard_id"],
                cost_usd=0.0,
            )

        # Subsequent turns: use the model to generate a response
        revealed_shard_ids = trace.get_revealed_shard_ids()

        # Get shards (excluding the first one which is the initial query)
        shards = sample["shards"][1:]
        shards_revealed = [s for s in shards if s["shard_id"] in revealed_shard_ids]
        shards_not_revealed = [s for s in shards if s["shard_id"] not in revealed_shard_ids]

        # If all information has been revealed, indicate that
        if not shards_not_revealed:
            return UserResponse(
                content="I've shared all the relevant information I have.",
                shard_id=None,
                cost_usd=0.0,
            )

        # Build the prompt
        conversation_str = trace.get_conversation_string(skip_system=True)
        prompt = self.prompt_response.format(
            conversation_so_far=conversation_str,
            shards_revealed=json.dumps(shards_revealed),
            shards_not_revealed=json.dumps(shards_not_revealed),
        )

        # Generate response
        response = await model_client.generate_json(
            messages=[{"role": "user", "content": prompt}],
            model=self.model,
            temperature=temperature,
        )

        result = response.content
        return UserResponse(
            content=result.get("response", ""),
            shard_id=result.get("shard_id"),
            cost_usd=response.total_usd,
            model_response=response,
        )
