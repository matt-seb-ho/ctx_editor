"""S3: Context compaction strategy — single-query analysis + context compaction.

Two-step process applied every turn after min_turns:
1. Single-query analysis: independent reviewer produces task_spec, aligned, issues
2. Context compaction: analysis + conversation → compacted context

Unlike S2 (ContextEditV2), this strategy ALWAYS compacts after the threshold,
rather than conditionally editing only when issues are found.
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

logger = get_logger("compaction")

_PROMPT_DIR = Path(__file__).parent / "prompts"


def _load_prompt(name: str) -> str:
    path = _PROMPT_DIR / f"{name}.txt"
    return path.read_text()


class ContextCompactionStrategy(BaseStrategy):
    """S3: Single-query analysis + unconditional context compaction.

    Every turn past min_turns:
    1. Run a single-query analysis prompt (independent reviewer framing)
       that produces task_spec, aligned, and issues sections.
    2. Feed the analysis + full conversation into the context compaction prompt
       to produce compacted context.
    3. Reset the trace with compacted context.
    """

    def __init__(
        self,
        compaction_model: str = "gpt-5-mini",
        compaction_timeout: int = 60,
        compaction_max_tokens: Optional[int] = None,
        compaction_reasoning_effort: Optional[str] = None,
        min_turns: int = 4,
        use_memory: bool = False,
        memory_target: str = "system",
    ):
        self.model = compaction_model
        self.timeout = compaction_timeout
        self.max_tokens = compaction_max_tokens
        self.reasoning_effort = compaction_reasoning_effort
        self.min_turns = min_turns if isinstance(min_turns, int) else 4
        self.use_memory = use_memory
        self.memory_target = memory_target

        self._analysis_template = _load_prompt("compaction_analysis")
        self._compaction_template = _load_prompt("context_compaction")

    async def _generate(self, prompt: str, model_client: "ModelClient") -> str:
        """Run a single LLM generation."""
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
        response = await model_client.generate(**generate_kwargs)
        return response.content

    @staticmethod
    def _extract_tag(text: str, tag: str) -> str:
        """Extract content from an XML tag."""
        import re

        match = re.search(rf"<{tag}>(.*?)</{tag}>", text, re.DOTALL)
        return match.group(1).strip() if match else ""

    async def _run_analysis(
        self,
        trace: "ConversationTrace",
        model_client: "ModelClient",
    ) -> dict[str, str]:
        """Run single-query analysis (step 1)."""
        conversation_str = trace.get_conversation_string(skip_system=True)

        prompt = self._analysis_template.format_map(
            defaultdict(str, {"conversation": conversation_str, "memory_section": ""})
        )
        output = await self._generate(prompt, model_client)

        task_spec = self._extract_tag(output, "task_spec") or output.strip()
        aligned = self._extract_tag(output, "aligned")
        issues = self._extract_tag(output, "issues")

        return {
            "task_spec": task_spec,
            "aligned": aligned,
            "issues": issues,
            "raw_output": output,
        }

    async def _run_compaction(
        self,
        trace: "ConversationTrace",
        analysis: dict[str, str],
        model_client: "ModelClient",
    ) -> dict[str, str]:
        """Run context compaction (step 2)."""
        conversation_str = trace.get_conversation_string(skip_system=True)

        prompt = self._compaction_template.format_map(
            defaultdict(
                str,
                {
                    "analysis_user_intent": analysis["task_spec"],
                    "analysis_aligned": analysis["aligned"],
                    "analysis_issues": analysis["issues"],
                    "conversation": conversation_str,
                },
            )
        )
        output = await self._generate(prompt, model_client)

        task_spec = self._extract_tag(output, "task_spec") or analysis["task_spec"]
        work_so_far = self._extract_tag(output, "work_so_far")

        return {
            "task_spec": task_spec,
            "work_so_far": work_so_far,
            "raw_output": output,
        }

    @staticmethod
    def _build_compacted_context(
        trace: "ConversationTrace",
        compaction: dict[str, str],
    ) -> list[Message]:
        """Build the reset messages from compaction output."""
        new_messages = []

        # System message: pass through unmodified
        system_msg = trace.system_message
        if system_msg:
            new_messages.append(Message(role="system", content=system_msg.content))

        # Compacted conversation
        compact_parts = [
            "The conversation history has been compacted. Below is a summary of the "
            "user's full specification and the work completed so far that is consistent "
            "with it.",
            f"# User Task Specification (So Far)\n{compaction['task_spec']}",
        ]
        if compaction["work_so_far"] and compaction["work_so_far"].lower() != "none":
            compact_parts.append(f"# What Looks Right So Far\n{compaction['work_so_far']}")

        new_messages.append(
            Message(role="compacted conversation", content="\n\n".join(compact_parts))
        )

        # Latest user message
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
        """Prepare context with unconditional compaction after min_turns.

        Flow:
        1. Skip if too few turns
        2. Run single-query analysis (independent reviewer)
        3. Run context compaction (analysis + conversation → compacted context)
        4. Reset trace with compacted context
        """
        # Inject memory if configured
        if self.use_memory and memory and self.memory_target == "system":
            self._inject_memory_to_trace(trace, memory, target="system")

        # Skip if first turn or too few user turns
        if trace.num_assistant_turns == 0 or trace.num_user_turns < self.min_turns:
            return trace.get_active_messages()

        # Step 1: Analysis
        analysis = await self._run_analysis(trace, model_client)

        trace.add_log(
            "compaction_analysis",
            {
                "task_spec": analysis["task_spec"],
                "aligned": analysis["aligned"],
                "issues": analysis["issues"],
                "model": self.model,
            },
        )

        # Step 2: Compaction (always runs, unlike S2's conditional edit)
        compaction = await self._run_compaction(trace, analysis, model_client)

        trace.add_log(
            "context_compaction",
            {
                "compacted_task_spec": compaction["task_spec"],
                "compacted_work_so_far": compaction["work_so_far"],
                "model": self.model,
                "original_turn_count": trace.total_user_turns,
                "active_turn_count": trace.num_user_turns,
            },
        )

        # Step 3: Reset trace with compacted context
        new_messages = self._build_compacted_context(trace, compaction)
        trace.reset_conversation(new_messages, label="context_compaction")

        return trace.get_active_messages()
