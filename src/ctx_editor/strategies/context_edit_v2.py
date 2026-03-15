"""S2: Context edit strategy — analysis-driven context rewriting.

Uses the ConversationAnalyzer to assess the conversation, then:
- If no pivot needed: proceed like baseline (full conversation, no changes)
- If pivot needed: rewrite the context into a compacted form using the analysis

This replaces both the old ContextEditStrategy (which always edited) and
AgenticEditStrategy (which used a separate decision prompt). Now the analysis
itself produces the pivot decision as part of its structured output.
"""

from typing import TYPE_CHECKING, Optional

from ..core.types import Message
from .analyzer import AnalysisResult, ConversationAnalyzer
from .base import BaseStrategy

if TYPE_CHECKING:
    from ..core.trace import ConversationTrace
    from ..memory.base import MemoryModule
    from ..models.base import ModelClient


class ContextEditV2Strategy(BaseStrategy):
    """S2: Analysis-driven context editing.

    Runs the conversation analyzer before each turn (past min_turns threshold).
    When the analysis indicates a pivot is needed, rewrites the conversation
    context using the analysis output. Otherwise, passes through like baseline.
    """

    def __init__(
        self,
        analyzer_model: str = "gpt-4o-mini",
        analyzer_timeout: int = 60,
        analyzer_max_tokens: Optional[int] = None,
        analyzer_reasoning_effort: Optional[str] = None,
        min_turns: int = 3,
        max_resets: int = 3,
        use_memory: bool = False,
        memory_target: str = "analyzer",
    ):
        self.analyzer = ConversationAnalyzer(
            model=analyzer_model,
            timeout=analyzer_timeout,
            max_tokens=analyzer_max_tokens,
            reasoning_effort=analyzer_reasoning_effort,
        )
        self.min_turns = min_turns if isinstance(min_turns, int) else 3
        self.max_resets = max_resets
        self.use_memory = use_memory
        self.memory_target = memory_target

    @staticmethod
    def _build_edited_context(
        trace: "ConversationTrace",
        result: "AnalysisResult",
    ) -> list[Message]:
        """Build compacted context from analysis output.

        Purges the full conversation history (hard attention) and replaces it
        with a compacted version. The "issues" from the analysis guided the
        decision to edit but are NOT reintroduced — the point is to remove
        harmful content from context, not redescribe it.

        The compacted context uses a [compacted conversation] role tag so the
        simulator's Option 2 renderer treats it like any other conversation
        turn, keeping everything in a single user message.

        Produces:
        - System message (original, unmodified)
        - Compacted conversation (task spec + what looks right)
        - Latest user message
        """
        new_messages = []

        # System message — pass through unmodified
        system_msg = trace.system_message
        if system_msg:
            new_messages.append(Message(role="system", content=system_msg.content))

        # Compacted conversation: task spec + aligned content
        task_spec = result.user_intent if result.user_intent else result.raw_output
        compact_parts = [f"# Task Spec\n{task_spec}"]
        if result.aligned:
            compact_parts.append(f"# What Looks Right So Far\n{result.aligned}")

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
        """Prepare context, editing if analysis warrants it (mutates trace).

        Flow:
        1. Skip analysis if too few turns or max resets reached
        2. Run analyzer to get user_intent + approach_eval + pivot_decision
        3. If pivot needed: reset trace with compacted context
        4. If no pivot: return full conversation as-is (like baseline)
        """
        # Inject memory to assistant if configured
        if self.use_memory and memory and self.memory_target == "assistant":
            self._inject_memory_to_trace(trace, memory, target="system")

        # Skip if first turn or too few turns
        if trace.num_assistant_turns == 0 or trace.num_user_turns < self.min_turns:
            return trace.get_active_messages()

        # Stop editing if max resets reached
        if trace.num_resets >= self.max_resets:
            return trace.get_active_messages()

        # Run analysis — pass memory only if targeting analyzer
        analysis_memory = memory if (self.use_memory and self.memory_target == "analyzer") else None
        result = await self.analyzer.analyze(trace, model_client, memory=analysis_memory)

        # Log the analysis
        trace.add_log(
            "conversation_analysis",
            {
                "user_intent": result.user_intent,
                "aligned": result.aligned,
                "issues": result.issues,
                "needs_edit": result.needs_edit,
                "analyzer_model": self.analyzer.model,
            },
        )

        if not result.needs_edit:
            # No substantive issues — pass through like baseline
            trace.add_log("edit_decision", {"should_edit": False})
            return trace.get_active_messages()

        # Issues found — rewrite context
        trace.add_log("edit_decision", {"should_edit": True})

        # Build compacted context from analysis
        new_messages = self._build_edited_context(trace, result)

        # Log before reset
        trace.add_log(
            "context_edit_output",
            {
                "edited_context": result.raw_output,
                "analyzer_model": self.analyzer.model,
                "original_turn_count": trace.total_user_turns,
                "active_turn_count": trace.num_user_turns,
            },
        )

        trace.reset_conversation(new_messages, label="context_edit")
        return trace.get_active_messages()
