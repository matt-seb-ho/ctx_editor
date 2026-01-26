"""Context editor agent for intelligent context compression."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional

from ..utils.helpers import load_prompt

if TYPE_CHECKING:
    from ..core.trace import ConversationTrace
    from ..cheatsheet.cheatsheet import Cheatsheet
    from ..models.base import ModelClient


DEFAULT_EDITOR_PROMPT = """\
You are a context editor. Analyze the conversation and create a condensed summary.

<conversation>
{conversation}
</conversation>

{cheatsheet_section}

Create a condensed context preserving:
1. The user's core request and requirements
2. All revealed constraints and specifications
3. Any partial progress or intermediate results
4. Critical clarifications (remove redundant exchanges)

Condensed context:"""


@dataclass
class EditResult:
    """Result of a context editing operation."""
    edited_context: str
    original_length: int
    edited_length: int
    compression_ratio: float
    cost_usd: float = 0.0


class ContextEditorAgent:
    """Agent that intelligently compresses conversation context.

    This agent can be used standalone or as part of a context editing strategy.
    It analyzes conversations and produces condensed versions that preserve
    essential information while reducing length.
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        prompt_file: Optional[str] = None,
        prompt: Optional[str] = None,
        temperature: float = 0.0,
    ):
        """Initialize the context editor agent.

        Args:
            model: Model to use for editing.
            prompt_file: Path to custom prompt file.
            prompt: Custom prompt string.
            temperature: Sampling temperature.
        """
        self.model = model
        self.temperature = temperature

        if prompt_file:
            self.prompt = load_prompt(prompt_file)
        elif prompt:
            self.prompt = prompt
        else:
            self.prompt = DEFAULT_EDITOR_PROMPT

    async def edit(
        self,
        trace: "ConversationTrace",
        model_client: "ModelClient",
        cheatsheet: Optional["Cheatsheet"] = None,
    ) -> EditResult:
        """Edit/compress the conversation context.

        Args:
            trace: The conversation trace to compress.
            model_client: Model client for generation.
            cheatsheet: Optional cheatsheet for guidance.

        Returns:
            EditResult with the compressed context and metrics.
        """
        # Get conversation as string
        conversation_str = trace.get_conversation_string(skip_system=True)
        original_length = len(conversation_str)

        # Build cheatsheet section
        cheatsheet_section = ""
        if cheatsheet and cheatsheet.content:
            cheatsheet_section = f"""
<cheatsheet>
Use this guidance to identify what information is most important:
{cheatsheet.content}
</cheatsheet>
"""

        # Build prompt
        prompt = self.prompt.format(
            conversation=conversation_str,
            cheatsheet_section=cheatsheet_section,
        )

        # Generate edited context
        response = await model_client.generate(
            messages=[{"role": "user", "content": prompt}],
            model=self.model,
            temperature=self.temperature,
        )

        edited_context = response.content.strip()
        edited_length = len(edited_context)

        return EditResult(
            edited_context=edited_context,
            original_length=original_length,
            edited_length=edited_length,
            compression_ratio=edited_length / original_length if original_length > 0 else 1.0,
            cost_usd=response.total_usd,
        )

    async def should_edit(
        self,
        trace: "ConversationTrace",
        model_client: "ModelClient",
        threshold_turns: int = 3,
        threshold_chars: int = 2000,
    ) -> tuple[bool, str]:
        """Decide whether the context should be edited.

        Args:
            trace: The conversation trace.
            model_client: Model client for decision.
            threshold_turns: Minimum turns before considering editing.
            threshold_chars: Minimum characters before considering editing.

        Returns:
            Tuple of (should_edit, reasoning).
        """
        # Simple heuristics first
        if trace.num_user_turns < threshold_turns:
            return False, f"Too few turns ({trace.num_user_turns} < {threshold_turns})"

        conversation_str = trace.get_conversation_string()
        if len(conversation_str) < threshold_chars:
            return False, f"Context short enough ({len(conversation_str)} < {threshold_chars} chars)"

        # Could add model-based decision here
        return True, f"Context is long ({len(conversation_str)} chars) with {trace.num_user_turns} turns"

    async def iterative_edit(
        self,
        trace: "ConversationTrace",
        model_client: "ModelClient",
        target_compression: float = 0.5,
        max_iterations: int = 3,
        cheatsheet: Optional["Cheatsheet"] = None,
    ) -> EditResult:
        """Iteratively edit context to achieve target compression.

        Args:
            trace: The conversation trace.
            model_client: Model client for generation.
            target_compression: Target compression ratio (0.5 = 50% of original).
            max_iterations: Maximum editing iterations.
            cheatsheet: Optional cheatsheet for guidance.

        Returns:
            EditResult with final compressed context.
        """
        # Create a working copy of the trace
        current_trace = trace.clone()
        total_cost = 0.0

        for i in range(max_iterations):
            result = await self.edit(current_trace, model_client, cheatsheet)
            total_cost += result.cost_usd

            if result.compression_ratio <= target_compression:
                result.cost_usd = total_cost
                return result

            # Update trace with edited content for next iteration
            # This is a simplified approach - in practice you might want
            # to preserve the structure differently
            from ..core.trace import ConversationTrace
            from ..core.types import Message

            new_trace = ConversationTrace()
            if trace.system_message:
                new_trace.add_system_message(trace.system_message.content)
            new_trace.messages.append(Message(
                role="assistant",
                content=result.edited_context,
            ))
            current_trace = new_trace

        # Return last result if target not reached
        result.cost_usd = total_cost
        return result
