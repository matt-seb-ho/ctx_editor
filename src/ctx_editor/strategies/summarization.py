"""Generic LLM condensation / summarisation baseline (non-analyzer).

Added 2026-07-29 (task T1) in response to the NeurIPS Area Chair's
"limited baselines" concern and reviewer Vg97's W1/Q1.

**What this is.** A good-faith, general-purpose conversation condenser of the
kind used by production agent harnesses for *context-length* management: at
each turn an LLM compresses the conversation history, and the assistant
proceeds from the condensed context instead of the raw transcript.

**What this deliberately is NOT.** The condenser is never asked to judge
correctness, find errors, decide what is invalidated, or drop the assistant's
wrong reasoning. Its instruction is to compress *faithfully* and preserve the
assistant's current approach and conclusions. That distinction is the whole
experiment: AC3 claims the gain comes from removing invalidated content, not
from shortening the context. A condenser that were told "drop wrong reasoning"
would just be a reimplementation of AC3 and the comparison would be vacuous.

Prompt files live in ``strategies/prompts/`` (``summarize_v1``,
``summarize_v1_refine``) and are quoted verbatim in the T1 worklog so a
reviewer can check the baseline was not handicapped.

Two budget modes:

- ``num_passes=1`` — a single condensation call per turn.
- ``num_passes=2`` — condense, then a *faithfulness* refinement pass that is
  allowed to fix omissions/inaccuracies **of the summary relative to the
  transcript** (never to re-judge the task). This exists purely to match
  AC3-Reset's two-query analyzer call budget, so that "summarisation does not
  close the gap" cannot be waved away as "you gave it half the compute".
"""

from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from ..core.types import Message
from ..utils.logging import get_logger
from .base import BaseStrategy

if TYPE_CHECKING:
    from ..core.trace import ConversationTrace
    from ..memory.base import MemoryModule
    from ..models.base import ModelClient

logger = get_logger("summarization")

_PROMPT_DIR = Path(__file__).parent / "prompts"


def _load_prompt(name: str) -> str:
    return (_PROMPT_DIR / f"{name}.txt").read_text()


class SummarizationStrategy(BaseStrategy):
    """Condense the conversation history each turn with a neutral summariser.

    Flow, every turn once ``num_user_turns >= min_turns``:

    1. Render the full conversation (system message excluded — it is passed
       through unmodified, exactly as AC3-Reset / AC3-Rewrite do).
    2. Ask an LLM to condense it (``num_passes`` calls).
    3. Replace the active context with ``[system] + [summary] + [latest user
       message]`` — structurally identical to the AC3-Reset / AC3-Rewrite
       reset, so the only difference between arms is *what the replacement
       text says*, not how it is plumbed in.
    """

    def __init__(
        self,
        summarizer_model: str = "gpt-4o-mini",
        summarizer_timeout: int = 300,
        summarizer_max_tokens: Optional[int] = None,
        summarizer_reasoning_effort: Optional[str] = None,
        summarize_prompt: str = "summarize_v1",
        refine_prompt: str = "summarize_v1_refine",
        num_passes: int = 1,
        min_turns: int = 1,
    ):
        self.model = summarizer_model
        self.timeout = summarizer_timeout
        self.max_tokens = summarizer_max_tokens
        self.reasoning_effort = summarizer_reasoning_effort
        self.min_turns = min_turns if isinstance(min_turns, int) else 1
        self.num_passes = int(num_passes)
        if self.num_passes not in (1, 2):
            raise ValueError(f"num_passes must be 1 or 2, got {num_passes}")

        self._summarize_template = _load_prompt(summarize_prompt)
        self._summarize_prompt_name = summarize_prompt
        self._refine_template = _load_prompt(refine_prompt) if self.num_passes == 2 else ""
        self._refine_prompt_name = refine_prompt if self.num_passes == 2 else ""

    async def _generate(self, prompt: str, model_client: "ModelClient") -> str:
        generate_kwargs: dict = {
            "messages": [{"role": "user", "content": prompt}],
            "model": self.model,
            "temperature": 0.0,
            "timeout": self.timeout,
        }
        if self.max_tokens:
            generate_kwargs["max_tokens"] = self.max_tokens
        if self.reasoning_effort:
            generate_kwargs["reasoning_effort"] = self.reasoning_effort

        from ..utils.call_meter import call_tag

        with call_tag("strategy"):
            response = await model_client.generate(**generate_kwargs)
        return response.content

    @staticmethod
    def _extract_tag(text: str, tag: str) -> str:
        import re

        match = re.search(rf"<{tag}>(.*?)</{tag}>", text, re.DOTALL)
        return match.group(1).strip() if match else ""

    async def _run_summarization(
        self,
        trace: "ConversationTrace",
        model_client: "ModelClient",
    ) -> dict[str, str]:
        conversation_str = trace.get_conversation_string(skip_system=True)
        system_message_str = trace.system_message.content if trace.system_message else ""

        prompt = self._summarize_template.format_map(
            defaultdict(
                str,
                {
                    "conversation": conversation_str,
                    "system_message": system_message_str,
                },
            )
        )
        raw = await self._generate(prompt, model_client)
        summary = self._extract_tag(raw, "summary") or raw.strip()
        raw_first = raw

        if self.num_passes == 2:
            refine_prompt = self._refine_template.format_map(
                defaultdict(
                    str,
                    {
                        "conversation": conversation_str,
                        "system_message": system_message_str,
                        "draft_summary": summary,
                    },
                )
            )
            raw2 = await self._generate(refine_prompt, model_client)
            revised = self._extract_tag(raw2, "summary") or raw2.strip()
            if revised:
                summary = revised
            return {"summary": summary, "raw_output": raw_first, "raw_output_refine": raw2}

        return {"summary": summary, "raw_output": raw_first, "raw_output_refine": ""}

    @staticmethod
    def _build_summarized_context(
        trace: "ConversationTrace",
        summary: str,
    ) -> list[Message]:
        new_messages = []

        system_msg = trace.system_message
        if system_msg:
            new_messages.append(Message(role="system", content=system_msg.content))

        parts = [
            "The conversation history has been condensed to save context. Below is a "
            "summary of the conversation so far.",
            summary,
        ]
        new_messages.append(Message(role="compacted conversation", content="\n\n".join(parts)))

        last_user = trace.last_user_message
        if last_user:
            new_messages.append(Message(role="user", content=last_user.content))

        return new_messages

    async def prepare_context(
        self,
        trace: "ConversationTrace",
        memory: Optional["MemoryModule"],
        model_client: "ModelClient",
    ) -> list[Message]:
        if trace.num_assistant_turns == 0 or trace.num_user_turns < self.min_turns:
            return trace.get_active_messages()

        result = await self._run_summarization(trace, model_client)

        trace.add_log(
            "conversation_summarization",
            {
                "summary": result["summary"],
                "model": self.model,
                "num_passes": self.num_passes,
                "summarize_prompt": self._summarize_prompt_name,
                "refine_prompt": self._refine_prompt_name,
                "original_turn_count": trace.total_user_turns,
                "active_turn_count": trace.num_user_turns,
            },
        )

        if not result["summary"].strip():
            logger.warning("Summariser returned empty output; leaving context unmodified.")
            return trace.get_active_messages()

        new_messages = self._build_summarized_context(trace, result["summary"])
        trace.reset_conversation(new_messages, label="conversation_summarization")

        return trace.get_active_messages()
