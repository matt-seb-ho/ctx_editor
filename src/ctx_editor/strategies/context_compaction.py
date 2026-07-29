"""S3: Context compaction strategy — shared analyzer + LLM compaction.

Two-step process applied every turn after min_turns:
1. Run ``ConversationAnalyzer`` (the SHARED analyzer used by Augment /
   Reset / Gated-Reset). Default prompt version is ``v8`` to match
   Reset's defaults — see ``analyzer_prompts.ANALYZER_PROMPT_REGISTRY``
   for the full registry.
2. LLM context compaction: feed the analyzer's
   ``user_intent`` / ``aligned`` / ``issues`` (and optionally the full
   conversation) into a compaction prompt, parse out the compacted
   ``task_spec`` / ``work_so_far``, and use them to build a new
   compacted-conversation message.
3. Reset the trace with that compacted context.

Unlike S2 (ContextEditV2), this strategy ALWAYS compacts after the
threshold rather than conditionally editing only when issues are found.

**Analyzer parity (2026-05-21)**: this module previously used a
bespoke ``_run_analysis`` method that loaded
``compaction_analysis.txt`` and produced a different, lower-quality
analysis than what Reset/Augment/Gated-Reset used. As of 2026-05-21
this divergence is fixed — all AC3 strategies that consume an
analyzer share ``ConversationAnalyzer`` and write/read the same
``AnalysisCache``. See ``docs/analyzer_parity_finding.md``.
"""

from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from ..core.types import Message
from ..utils.logging import get_logger
from .analyzer import AnalysisResult, ConversationAnalyzer
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


class AC3RewriteStrategy(BaseStrategy):
    """AC3-Rewrite: shared-analyzer first stage + LLM compaction second stage.

    Historically known as ``ContextCompactionStrategy`` (paper-era
    "S3"). Every turn past ``min_turns``:

    1. Run ``ConversationAnalyzer`` (shared with Augment / Reset /
       Gated-Reset). Produces an ``AnalysisResult`` with
       ``user_intent`` / ``aligned`` / ``issues``.
    2. Feed those analyzer fields (and optionally the conversation
       string) into the compaction prompt template; an LLM produces
       a compacted spec + verified-work payload.
    3. Build a compacted-conversation message and reset the trace.

    Unlike AC3-Reset (which only resets on detected issues), this
    strategy resets unconditionally after the threshold.

    See ``docs/strategy_name_history.md`` for the full rename map and
    ``docs/analyzer_parity_finding.md`` for the 2026-05-21 refactor.
    """

    def __init__(
        self,
        compaction_model: str = "gpt-5-mini",
        compaction_timeout: int = 300,
        compaction_max_tokens: Optional[int] = None,
        compaction_reasoning_effort: Optional[str] = None,
        min_turns: int = 4,
        use_memory: bool = False,
        memory_target: str = "system",
        compaction_prompt: str = "context_compaction",
        open_ended_output: bool = False,
        # --- Analyzer parameters (mirror context_edit_v2.AC3ResetStrategy) ---
        analyzer_model: Optional[str] = None,
        analyzer_timeout: int = 60,
        analyzer_max_tokens: Optional[int] = None,
        analyzer_reasoning_effort: Optional[str] = None,
        analyzer_prompt_version: str = "v8",
        analysis_cache_dir: Optional[str] = None,
        # --- Deprecated kwargs kept for backwards-compat ---
        analysis_prompt: Optional[str] = None,
    ):
        """
        Args:
            compaction_model: LLM that runs the rewriter (second stage).
            compaction_timeout / max_tokens / reasoning_effort: rewriter knobs.
            min_turns: rewrite fires once ``num_user_turns >= min_turns``.
            use_memory / memory_target: optional memory injection.
            compaction_prompt: name (no extension) of the rewriter prompt
                file under ``strategies/prompts/``. Placeholders the
                prompt may reference: ``analysis_user_intent``,
                ``analysis_aligned``, ``analysis_issues``, ``conversation``.
                Missing placeholders are substituted with empty string.

            analyzer_model: model for the analyzer step. Defaults to the
                same model as the rewriter when not provided (mirrors
                prior behavior where everything ran on ``compaction_model``).
            analyzer_timeout / max_tokens / reasoning_effort: analyzer knobs.
            analyzer_prompt_version: which prompt version in
                ``analyzer_prompts.ANALYZER_PROMPT_REGISTRY`` to use.
                Default ``"v8"`` matches Reset's defaults — this is the
                key parity guarantee.
            analysis_cache_dir: optional path to a content-addressed
                ``AnalysisCache``. Lets Rewrite reuse v8 analyses already
                cached by Reset / Augment / Gated-Reset on the same prefix.

            analysis_prompt: **deprecated**. Previously controlled which
                bespoke rewrite-only analyzer prompt to load (e.g.
                ``compaction_analysis``). Now ignored with a warning,
                because the analyzer step uses ``ConversationAnalyzer``
                with ``analyzer_prompt_version`` instead. To pick an
                analyzer prompt, use ``analyzer_prompt_version``.
        """
        if analysis_prompt is not None and analysis_prompt != "compaction_analysis":
            logger.warning(
                "AC3RewriteStrategy.analysis_prompt=%r is deprecated and ignored "
                "(the rewriter now uses ConversationAnalyzer with "
                "analyzer_prompt_version=%r — see docs/analyzer_parity_finding.md).",
                analysis_prompt, analyzer_prompt_version,
            )

        # Rewriter (stage-2) knobs
        self.model = compaction_model
        self.timeout = compaction_timeout
        self.max_tokens = compaction_max_tokens
        self.reasoning_effort = compaction_reasoning_effort
        self.min_turns = min_turns if isinstance(min_turns, int) else 4
        self.use_memory = use_memory
        self.memory_target = memory_target

        self._compaction_template = _load_prompt(compaction_prompt)
        self._compaction_prompt_name = compaction_prompt
        self._open_ended_output = open_ended_output
        # Detect tag name used by the compaction prompt for the work-so-far section
        # (v1: <work_so_far>; v2: <verified_work>). Both stay supported.
        self._work_tag = "verified_work" if "verified_work" in self._compaction_template else "work_so_far"

        # Stage-1 analyzer: SHARED with Augment / Reset / Gated-Reset
        self.analyzer = ConversationAnalyzer(
            model=analyzer_model or compaction_model,
            timeout=analyzer_timeout,
            max_tokens=analyzer_max_tokens,
            reasoning_effort=analyzer_reasoning_effort,
            prompt_version=analyzer_prompt_version,
        )

        # Content-addressed cache for analyzer outputs (lets us hit v8 analyses
        # already cached by other strategies on the same prefix).
        self._analysis_cache = None
        if analysis_cache_dir:
            from .analysis_cache import AnalysisCache
            self._analysis_cache = AnalysisCache(analysis_cache_dir)

    async def _generate(self, prompt: str, model_client: "ModelClient") -> str:
        """Run a single LLM generation (used for the stage-2 rewriter)."""
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
        """Extract content from an XML tag."""
        import re

        match = re.search(rf"<{tag}>(.*?)</{tag}>", text, re.DOTALL)
        return match.group(1).strip() if match else ""

    async def _run_compaction(
        self,
        trace: "ConversationTrace",
        analysis: "AnalysisResult",
        model_client: "ModelClient",
    ) -> dict[str, str]:
        """Run the stage-2 LLM compaction.

        Takes an ``AnalysisResult`` (from the shared analyzer) and the
        live trace; produces the compacted ``task_spec`` /
        ``work_so_far`` payload by templating + parsing an LLM call.
        """
        conversation_str = trace.get_conversation_string(skip_system=True)

        prompt = self._compaction_template.format_map(
            defaultdict(
                str,
                {
                    "analysis_user_intent": analysis.user_intent,
                    "analysis_aligned": analysis.aligned,
                    "analysis_issues": analysis.issues,
                    "conversation": conversation_str,
                },
            )
        )
        output = await self._generate(prompt, model_client)

        if self._open_ended_output:
            # Prefer the wrapped <new_context>...</new_context> region if the
            # rewriter used it (lets non-reasoning models put scratchpad CoT
            # before the tag). Fall back to the whole output otherwise.
            wrapped = self._extract_tag(output, "new_context")
            return {
                "task_spec": "",
                "work_so_far": "",
                "open_ended_text": wrapped or output.strip(),
                "raw_output": output,
            }

        task_spec = self._extract_tag(output, "task_spec") or analysis.user_intent
        work_so_far = self._extract_tag(output, self._work_tag)

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
        if compaction.get("open_ended_text"):
            compact_parts = [
                "The conversation history has been compacted. Below is the prepared summary.",
                compaction["open_ended_text"],
            ]
        else:
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
        1. Skip if first turn or too few user turns.
        2. Run the shared ``ConversationAnalyzer`` (cache-aware).
        3. Run stage-2 LLM compaction on the analyzer output.
        4. Reset trace with the compacted context.
        """
        # Inject memory if configured
        if self.use_memory and memory and self.memory_target == "system":
            self._inject_memory_to_trace(trace, memory, target="system")

        # Skip if first turn or too few user turns
        if trace.num_assistant_turns == 0 or trace.num_user_turns < self.min_turns:
            return trace.get_active_messages()

        # Step 1: Shared analyzer (cache hit if a prior Reset/Augment/Gated-Reset
        # already analyzed this prefix at the same prompt_version/model).
        analysis: AnalysisResult = await self.analyzer.analyze(
            trace,
            model_client,
            memory=memory if (self.use_memory and self.memory_target == "analyzer") else None,
            cache=self._analysis_cache,
        )

        # Mirror the prior log_type for backwards compat with the viewer +
        # analysis tooling that already parses this key.
        trace.add_log(
            "compaction_analysis",
            {
                "task_spec": analysis.user_intent,
                "aligned": analysis.aligned,
                "issues": analysis.issues,
                "model": self.analyzer.model,
                "analyzer_prompt_version": self.analyzer.prompt_version,
                "compaction_prompt": self._compaction_prompt_name,
            },
        )

        # Step 2: Stage-2 LLM compaction (always runs, unlike S2's gated edit)
        compaction = await self._run_compaction(trace, analysis, model_client)

        trace.add_log(
            "context_compaction",
            {
                "compacted_task_spec": compaction["task_spec"],
                "compacted_work_so_far": compaction["work_so_far"],
                "compacted_open_ended_text": compaction.get("open_ended_text", ""),
                "model": self.model,
                "original_turn_count": trace.total_user_turns,
                "active_turn_count": trace.num_user_turns,
            },
        )

        # Step 3: Reset trace with compacted context
        new_messages = self._build_compacted_context(trace, compaction)
        trace.reset_conversation(new_messages, label="context_compaction")

        return trace.get_active_messages()


# Backwards-compatible alias. Predates the AC3-* naming convention.
ContextCompactionStrategy = AC3RewriteStrategy
