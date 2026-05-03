"""ERGO-style strategy: rewrite user messages into consolidated prompt, restart conversation.

Based on Khalid et al. (2025). ERGO triggers on entropy spikes; in our replay-mode
evaluation we trigger unconditionally before the final turn, which is functionally
equivalent for the reset's effect on the assistant's last response (the only thing
graded). The reset itself is faithful to ERGO:

  1. Collect all prior user messages, formatted as "User Instruction N: <msg>".
  2. Send them to a rewriter LLM with ERGO's exact system + user prompt
     (`/home/agent/ergo/core/{ergo.py,prompts.py}`), asking the LLM to produce
     a single optimally-ordered rewrite without answering.
  3. Reset the conversation to [original system message, rewritten user message].

We omit ERGO's per-task few-shot demonstrations (their `prompts.py` ships
GSM8K/Code/DB/D2T exemplars). The exemplars in their codebase exist mainly to
support smaller open-weight models; gpt-5-mini follows the zero-shot rewrite
instruction reliably. The algorithm and the prompt wording are otherwise
identical.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Optional

from ..core.types import Message
from ..utils.logging import get_logger
from .base import BaseStrategy

if TYPE_CHECKING:
    from ..core.trace import ConversationTrace
    from ..memory.base import MemoryModule
    from ..models.base import ModelClient

logger = get_logger("ergo")

_PROMPT_DIR = Path(__file__).parent / "prompts"

# Verbatim from /home/agent/ergo/core/prompts.py (system message used across all
# task-specific rewrite prompts).
_REWRITER_SYSTEM = (
    "You are a prompt rewriter whose main goal is to rewrite the prompt given "
    "by the user in the most optimal way without losing any information in them."
)


def _load_prompt(name: str) -> str:
    path = _PROMPT_DIR / f"{name}.txt"
    return path.read_text()


class ERGORestartStrategy(BaseStrategy):
    """ERGO-style: rewrite user messages into single prompt, discard all assistant work.

    Every turn past min_turns:
    1. Collect all user messages (across resets if any)
    2. Pass through LLM rewriter to consolidate into a single prompt
    3. Reset trace with system message + rewritten user prompt

    This discards ALL assistant progress, which is the key difference
    from our compaction strategy that preserves correct work.
    """

    def __init__(
        self,
        rewrite_model: str = "gpt-5-mini",
        rewrite_timeout: int = 300,
        rewrite_max_tokens: Optional[int] = None,
        rewrite_reasoning_effort: Optional[str] = None,
        min_turns: int = 4,
        use_memory: bool = False,
        memory_target: str = "system",
    ):
        self.model = rewrite_model
        self.timeout = rewrite_timeout
        self.max_tokens = rewrite_max_tokens
        self.reasoning_effort = rewrite_reasoning_effort
        self.min_turns = min_turns if isinstance(min_turns, int) else 4
        self.use_memory = use_memory
        self.memory_target = memory_target

        self._rewrite_template = _load_prompt("ergo_rewrite")

    @staticmethod
    def _format_user_instructions(trace: "ConversationTrace") -> str:
        """Format user messages as ERGO does: 'User Instruction N: <msg>' lines.

        Mirrors `Ergo.rewrite_prompt` in /home/agent/ergo/core/ergo.py.
        """
        all_msgs = trace.to_messages(include_system=False, active_only=False)
        user_msgs = [m for m in all_msgs if m.role == "user"]
        seen: set[str] = set()
        unique: list[str] = []
        for m in user_msgs:
            content = m.content.strip()
            if content not in seen:
                seen.add(content)
                unique.append(content)
        return "\n".join(f"User Instruction {i+1}: {c}" for i, c in enumerate(unique))

    async def _generate_messages(
        self, messages: list[dict], model_client: "ModelClient"
    ) -> str:
        generate_kwargs: dict = {
            "messages": messages,
            "model": self.model,
            "temperature": 0.0,
            "timeout": self.timeout,
        }
        if self.max_tokens:
            generate_kwargs["max_tokens"] = self.max_tokens
        if self.reasoning_effort:
            generate_kwargs["reasoning_effort"] = self.reasoning_effort
        response = await model_client.generate(**generate_kwargs)
        return response.content

    async def _rewrite_user_messages(
        self,
        trace: "ConversationTrace",
        model_client: "ModelClient",
    ) -> str:
        """Collect all user messages and rewrite into a single consolidated prompt."""
        user_messages_str = self._format_user_instructions(trace)
        user_content = self._rewrite_template.format(user_messages=user_messages_str)
        messages = [
            {"role": "system", "content": _REWRITER_SYSTEM},
            {"role": "user", "content": user_content},
        ]
        return await self._generate_messages(messages, model_client)

    @staticmethod
    def _build_restarted_context(
        trace: "ConversationTrace",
        rewritten_prompt: str,
    ) -> list[Message]:
        """Build reset context: system message + rewritten user prompt only."""
        new_messages = []

        # System message: pass through unmodified
        system_msg = trace.system_message
        if system_msg:
            new_messages.append(Message(role="system", content=system_msg.content))

        # Single consolidated user message (no assistant work preserved)
        new_messages.append(Message(role="user", content=rewritten_prompt))

        return new_messages

    async def prepare_context(
        self,
        trace: "ConversationTrace",
        memory: Optional["MemoryModule"],
        model_client: "ModelClient",
    ) -> list[Message]:
        """Prepare context with ERGO-style restart after min_turns.

        Flow:
        1. Skip if too few turns
        2. Rewrite all user messages into single prompt via LLM
        3. Reset trace with system + rewritten prompt (discard all assistant work)
        """
        if self.use_memory and memory and self.memory_target == "system":
            self._inject_memory_to_trace(trace, memory, target="system")

        if trace.num_assistant_turns == 0 or trace.num_user_turns < self.min_turns:
            return trace.get_active_messages()

        # Rewrite user messages
        rewritten = await self._rewrite_user_messages(trace, model_client)

        trace.add_log(
            "ergo_rewrite",
            {
                "rewritten_prompt": rewritten,
                "model": self.model,
                "original_turn_count": trace.total_user_turns,
                "active_turn_count": trace.num_user_turns,
            },
        )

        # Reset with only the rewritten prompt (no assistant work)
        new_messages = self._build_restarted_context(trace, rewritten)
        trace.reset_conversation(new_messages, label="ergo_restart")

        return trace.get_active_messages()
