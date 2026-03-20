"""CollabLLM user simulator agent.

Implements CollabLLM's user behavior: role-plays as a human user with access
to the full problem/reference goal, providing vague initial requests and
gradually revealing intent through natural conversation.
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from ..core.types import ModelResponse

if TYPE_CHECKING:
    from ..core.trace import ConversationTrace
    from ..models.base import ModelClient


logger = logging.getLogger(__name__)

# Load the user simulator prompt
_PROMPTS_DIR = Path(__file__).parent.parent / "prompts" / "collabllm"
USER_SIMULATOR_PROMPT = (_PROMPTS_DIR / "user_simulator.txt").read_text()

# Termination signal — user emits this when satisfied or giving up
TERMINATION_SIGNAL = "[[TERMINATE CHAT]]"


@dataclass
class CollabLLMUserResponse:
    """Response from the CollabLLM user simulator."""

    content: str
    terminated: bool = False
    cost_usd: float = 0.0
    model_response: Optional[ModelResponse] = None


def _format_chat_history(messages: list[dict[str, str]]) -> str:
    """Format messages as CollabLLM-style chat history.

    Produces **Role**: content lines, matching CollabLLM's parse_messages.
    Strips system messages. Renders "compacted conversation" as an
    assistant summary so the user sim sees a natural-looking conversation.
    """
    parts = []
    for msg in messages:
        role = msg.get("role", "unknown")
        if role == "system":
            continue
        content = msg.get("content", "")
        if role == "compacted conversation":
            # Present as an assistant summary -- from the user's perspective,
            # the assistant is summarizing the conversation state
            parts.append(f"**Assistant**: [Conversation summary] {content}")
        else:
            parts.append(f"**{role.capitalize()}**: {content}")
    return "\n".join(parts)


def _parse_user_response(text: str) -> dict | None:
    """Parse JSON response from user simulator."""
    # Try direct parse
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        pass

    # Try finding JSON object
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except (json.JSONDecodeError, TypeError):
            pass

    return None


class CollabLLMUserAgent:
    """Agent that simulates a CollabLLM-style user.

    Uses CollabLLM's user simulator prompt to role-play as a human user
    who provides vague initial requests and gradually reveals intent.
    The user can terminate the conversation via a termination signal.
    """

    def __init__(
        self,
        task_desc: str,
        single_turn_prompt: str,
        model: str = "gpt-4o-mini",
        temperature: float = 1.0,
        max_tokens: int = 1024,
        max_retries: int = 5,
    ):
        """Initialize the CollabLLM user agent.

        Args:
            task_desc: Description of the task type (e.g., "question answering").
            single_turn_prompt: The full problem/reference goal (hidden from assistant).
            model: Model to use for user simulation.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens for user responses.
            max_retries: Number of retries on parse failure.
        """
        self.task_desc = task_desc
        self.single_turn_prompt = single_turn_prompt
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_retries = max_retries

    async def generate_response(
        self,
        trace: "ConversationTrace",
        model_client: "ModelClient",
    ) -> CollabLLMUserResponse:
        """Generate the next user message.

        Args:
            trace: Current conversation trace.
            model_client: Model client for LLM calls.

        Returns:
            CollabLLMUserResponse with the user's message.
        """
        # Build chat history that includes:
        # 1. Prior user messages from before any resets (so user sim doesn't repeat)
        # 2. Active messages (compacted conversation + current exchange)
        active_messages = trace.get_active_messages()

        chat_history_msgs = []
        if trace.num_resets > 0:
            # Collect unique prior user messages (hidden by resets)
            all_msgs = trace.to_messages(include_system=False, active_only=False)
            active_set = set(id(m) for m in active_messages)
            seen_content: set[str] = set()

            for msg in all_msgs:
                if msg.role == "user" and id(msg) not in active_set:
                    content = msg.content.strip()
                    if content not in seen_content:
                        seen_content.add(content)
                        chat_history_msgs.append(
                            {"role": "user", "content": msg.content}
                        )

        # Add active messages (system filtered out by _format_chat_history)
        for msg in active_messages:
            chat_history_msgs.append(
                {"role": msg.role, "content": msg.content}
            )

        chat_history_str = _format_chat_history(chat_history_msgs)

        # Build the user simulator prompt
        prompt = USER_SIMULATOR_PROMPT.format(
            task_desc=self.task_desc,
            single_turn_prompt=self.single_turn_prompt,
            chat_history=chat_history_str if chat_history_str else "(empty)",
            terminal_signal=TERMINATION_SIGNAL,
        )

        # Call LLM to generate user response
        for attempt in range(self.max_retries):
            try:
                response = await model_client.generate(
                    messages=[{"role": "user", "content": prompt}],
                    model=self.model,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )

                # Parse JSON response
                parsed = _parse_user_response(response.content)
                if parsed and isinstance(parsed, dict):
                    required_keys = {"current_answer", "thought", "response"}
                    if required_keys.issubset(parsed.keys()):
                        user_text = parsed["response"].strip()

                        # Check for termination
                        terminated = TERMINATION_SIGNAL in user_text

                        return CollabLLMUserResponse(
                            content=user_text,
                            terminated=terminated,
                            cost_usd=response.total_usd,
                            model_response=response,
                        )
                    else:
                        logger.warning(
                            f"User simulator attempt {attempt + 1}: "
                            f"missing keys {required_keys - parsed.keys()}"
                        )
                else:
                    logger.warning(
                        f"User simulator attempt {attempt + 1}: "
                        f"failed to parse JSON from response"
                    )
            except Exception as e:
                logger.warning(f"User simulator attempt {attempt + 1} error: {e}")

        # Fallback: return the raw response if JSON parsing failed
        logger.error("User simulator: all retries exhausted, using raw response")
        return CollabLLMUserResponse(
            content=response.content if response else "I need help with this problem.",
            terminated=False,
            cost_usd=response.total_usd if response else 0.0,
            model_response=response,
        )
