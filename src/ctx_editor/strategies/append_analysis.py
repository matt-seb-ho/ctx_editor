"""S1: Append analysis strategy — analysis is shown to assistant alongside full conversation.

Before each assistant turn (after min_turns threshold), generates an independent
analysis of the conversation and appends it to the context. The assistant sees the
full conversation history plus the analysis, but the context is never rewritten.

This is the append-only variant: the hypothesis is that showing the assistant a
critical review of its approach will help it course-correct without needing to
rewrite the conversation.
"""

from typing import TYPE_CHECKING, Optional

from ..core.types import Message
from .analyzer import ConversationAnalyzer
from .base import BaseStrategy

if TYPE_CHECKING:
    from ..core.trace import ConversationTrace
    from ..memory.base import MemoryModule
    from ..models.base import ModelClient


# Appended to system message once to explain the analysis block
ANALYSIS_SYSTEM_ADDENDUM = """

Note: An independent reviewer may analyze the conversation between turns. \
These analyses appear as [conversation analysis] messages. They summarize what the user \
has specified so far and identify which parts of your approach are consistent with the \
specifications and which parts may be erroneous. Consider this analysis when preparing \
your next response, but do not reference it directly."""

ANALYSIS_PREAMBLE = (
    "An independent reviewer analyzed the conversation so far. It summarizes what the user "
    "has specified and identifies which parts of your approach are consistent with the "
    "specifications and which parts may need to change. Consider this analysis when "
    "preparing your next response."
)


class AppendAnalysisStrategy(BaseStrategy):
    """S1: Append conversation analysis without modifying history.

    For each turn past min_turns, generates a structured analysis and appends
    it to the last user message. The assistant sees full history + analysis.
    """

    def __init__(
        self,
        analyzer_model: str = "gpt-4o-mini",
        analyzer_timeout: int = 60,
        analyzer_max_tokens: Optional[int] = None,
        analyzer_reasoning_effort: Optional[str] = None,
        analyzer_prompt_version: str = "v8",
        min_turns: int = 3,
        use_memory: bool = False,
        memory_target: str = "analyzer",
        memory_target_query: str = "compare",
        enforce_compliance: bool = False,
        spec_only: bool = False,
    ):
        self.analyzer = ConversationAnalyzer(
            model=analyzer_model,
            timeout=analyzer_timeout,
            max_tokens=analyzer_max_tokens,
            reasoning_effort=analyzer_reasoning_effort,
            prompt_version=analyzer_prompt_version,
        )
        # min_turns="auto" is resolved by run_experiment before instantiation,
        # but default to 3 if it somehow reaches here unresolved.
        self.min_turns = min_turns if isinstance(min_turns, int) else 3
        self.use_memory = use_memory
        self.memory_target = memory_target
        # Which query receives memory: "compare" (default), "spec", or "both"
        self.memory_target_query = memory_target_query
        # Append compliance rules to Query 2 to prevent clarification-seeking
        self.enforce_compliance = enforce_compliance
        # spec_only: only append the task spec, skip aligned/issues (and Query 2)
        self.spec_only = spec_only

    def _is_analysis_addendum_added(self, trace: "ConversationTrace") -> bool:
        return any(log["type"] == "analysis_addendum_added" for log in trace.logs)

    async def prepare_context(
        self,
        trace: "ConversationTrace",
        memory: Optional["MemoryModule"],
        model_client: "ModelClient",
    ) -> list[Message]:
        """Prepare context with appended analysis (mutates trace).

        Mutates the trace by:
        1. Adding system addendum explaining analysis tags (once)
        2. Injecting memory if configured (once)
        3. Appending analysis to last user message
        """
        # Inject memory to assistant if configured
        if self.use_memory and memory and self.memory_target == "assistant":
            self._inject_memory_to_trace(trace, memory, target="system")

        # Skip analysis if too few turns
        if trace.num_user_turns < self.min_turns:
            return trace.get_active_messages()

        # No assistant output yet — nothing to analyze
        if trace.num_assistant_turns == 0:
            return trace.get_active_messages()

        # Add system addendum (once)
        if not self._is_analysis_addendum_added(trace):
            trace.append_to_system_message(ANALYSIS_SYSTEM_ADDENDUM)
            trace.add_log("analysis_addendum_added", {})

        # Generate analysis — pass memory only if targeting analyzer
        analysis_memory = memory if (self.use_memory and self.memory_target == "analyzer") else None
        result = await self.analyzer.analyze(
            trace, model_client, memory=analysis_memory, spec_only=self.spec_only,
            memory_target_query=self.memory_target_query,
            enforce_compliance=self.enforce_compliance,
        )

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

        # Build analysis text
        parts = [ANALYSIS_PREAMBLE]
        if result.user_intent:
            parts.append(f"# User Task Specification (So Far)\n{result.user_intent}")
        if not self.spec_only:
            if result.aligned:
                parts.append(f"# What Looks Right So Far\n{result.aligned}")
            if result.issues and result.needs_edit:
                parts.append(f"# What Needs to Change\n{result.issues}")
        analysis_text = "\n\n".join(parts)

        # Insert analysis as a separate message before the last user message
        messages = trace.get_active_messages()
        if analysis_text and len(messages) >= 1:
            analysis_msg = Message(role="conversation analysis", content=analysis_text)
            # Find last user message and insert analysis before it
            last_user_idx = None
            for i in range(len(messages) - 1, -1, -1):
                if messages[i].role == "user":
                    last_user_idx = i
                    break
            if last_user_idx is not None:
                messages.insert(last_user_idx, analysis_msg)
            else:
                messages.append(analysis_msg)

        return messages
