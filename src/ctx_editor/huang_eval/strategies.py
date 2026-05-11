"""Huang-eval AC3 strategies as :class:`ContextStrategy` subclasses.

Phase 2 of the post-COLM cleanup: lifts the inline ``generate_s2`` /
``generate_s3`` / ``generate_s15`` logic from :mod:`huang_eval.replay` into
named strategy classes that implement the standard ``ContextStrategy`` protocol
from :mod:`ctx_editor.strategies.base`. This:

1. Unifies the AC3 contract across LiC, CollabLLM, and Huang eval. All four
   AC3 variants (Augment / Reset / Gated-Reset / Rewrite) now exist as
   ``ContextStrategy`` subclasses for Huang.
2. Adds **AC3-Augment** for Huang eval (it was missing before).
3. Makes prompt-version sweeps trivial: every strategy reads from
   :data:`ctx_editor.strategies.analyzer_prompts.ANALYZER_PROMPT_REGISTRY`.

Why a Huang-specific module instead of reusing the LiC strategy classes?
Huang's replay path produces a one-shot generation per turn-index (not a
running conversation), and uses a specific compacted-message layout
("Below is a summary of the user's specification… # What Looks Right So Far…")
with a synthetic assistant ack before the last user message. That layout is
baked into the paper's pairwise-judge prompts, so changing it would mean
re-running every judge call. Keeping these as Huang-specific subclasses
preserves bit-for-bit output while giving us the protocol.

See ``docs/strategy_name_history.md`` for the full name map and
``docs/paper_experiments_provenance.md`` for which paper results used which
strategy + analyzer prompt version.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from ..core.trace import ConversationTrace
from ..core.types import Message
from ..strategies.analyzer import AnalysisResult, ConversationAnalyzer
from ..strategies.base import BaseStrategy

if TYPE_CHECKING:
    from ..memory.base import MemoryModule
    from ..models.base import ModelClient


# Compaction prompt for the LLM-rewrite variant (S3). Shared with LiC's
# AC3RewriteStrategy; lives under strategies/prompts/ as the single copy.
_COMPACTION_PROMPT_PATH = (
    Path(__file__).parent.parent / "strategies" / "prompts" / "context_compaction.txt"
)


def _extract_tag(text: str, tag: str) -> str:
    """Extract content from an XML tag (Huang-eval local copy)."""
    import re

    match = re.search(rf"<{tag}>(.*?)</{tag}>", text, re.DOTALL)
    return match.group(1).strip() if match else ""


@dataclass
class HuangContextEditResult:
    """Side-channel result of one ``prepare_context`` call.

    ``ContextStrategy.prepare_context`` is contracted to return ``list[Message]``,
    but Huang's evaluation harness wants to log the analyzer output and whether
    an edit fired. After ``prepare_context`` returns, callers can read
    ``strategy.last_result`` for this metadata.
    """

    edited: bool
    analysis: Optional[AnalysisResult] = None
    gated_reason: Optional[str] = None
    compaction_output: Optional[str] = None  # only populated for the Rewrite variant


class _HuangAC3Base(BaseStrategy):
    """Shared scaffolding for Huang AC3 strategies.

    Subclasses define one method, ``_build_edited_messages``, that turns an
    :class:`AnalysisResult` plus the current trace into the new conversation
    layout. The base class handles analyzer setup, the ``needs_edit`` gate,
    and the trace mutation.
    """

    def __init__(
        self,
        analyzer_model: str = "gpt-5-mini",
        analyzer_prompt_version: str = "v8",
        analyzer_timeout: int = 120,
        min_user_turns: int = 0,
    ):
        self.analyzer_model = analyzer_model
        self.analyzer_prompt_version = analyzer_prompt_version
        self.analyzer_timeout = analyzer_timeout
        self.min_user_turns = min_user_turns
        self.last_result: Optional[HuangContextEditResult] = None

    def _make_analyzer(self) -> ConversationAnalyzer:
        return ConversationAnalyzer(
            model=self.analyzer_model,
            timeout=self.analyzer_timeout,
            prompt_version=self.analyzer_prompt_version,
        )

    async def prepare_context(
        self,
        trace: "ConversationTrace",
        memory: Optional["MemoryModule"],
        model_client: "ModelClient",
    ) -> list[Message]:
        # Gate: not enough user turns yet?
        if trace.num_user_turns < self.min_user_turns:
            self.last_result = HuangContextEditResult(
                edited=False, gated_reason="too_few_turns"
            )
            return trace.get_active_messages()

        analyzer = self._make_analyzer()
        analysis = await analyzer.analyze(trace, model_client, memory=memory)

        if not analysis.needs_edit:
            self.last_result = HuangContextEditResult(edited=False, analysis=analysis)
            return trace.get_active_messages()

        new_messages, compaction_output = await self._build_edited_messages(
            trace=trace, analysis=analysis, model_client=model_client
        )
        trace.reset_conversation(new_messages, label="huang_context_edit")
        self.last_result = HuangContextEditResult(
            edited=True, analysis=analysis, compaction_output=compaction_output
        )
        return trace.get_active_messages()

    async def _build_edited_messages(
        self,
        trace: "ConversationTrace",
        analysis: AnalysisResult,
        model_client: "ModelClient",
    ) -> tuple[list[Message], Optional[str]]:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# AC3 variants — exact behavior parity with the legacy generate_* functions
# in replay.py. Each ``_build_edited_messages`` mirrors the message layout
# the paper's judges have already scored against; do not edit casually.
# ---------------------------------------------------------------------------


class HuangAC3ResetStrategy(_HuangAC3Base):
    """AC3-Reset for Huang eval — programmatic context reset (no LLM rewrite).

    Equivalent to the legacy ``generate_s15`` in :mod:`replay`. Uses the v8
    two-query analyzer by default. Gating: needs_edit only (no min_user_turns
    gate unless the caller sets one).
    """

    async def _build_edited_messages(
        self,
        trace: "ConversationTrace",
        analysis: AnalysisResult,
        model_client: "ModelClient",
    ) -> tuple[list[Message], None]:
        return _build_s15_messages(trace, analysis), None


class HuangAC3GatedResetStrategy(_HuangAC3Base):
    """AC3-Gated-Reset for Huang eval — programmatic reset, gated by min_turns.

    Equivalent to the legacy ``generate_s2`` in :mod:`replay`. Uses the v11
    "mid-task reflection" analyzer by default. Gating: ``min_user_turns`` plus
    needs_edit. The compacted-message wording is the v11/S2 variant
    ("A mid-task review identified opportunities to improve…").
    """

    def __init__(
        self,
        analyzer_model: str = "gpt-5-mini",
        analyzer_prompt_version: str = "v11",
        analyzer_timeout: int = 120,
        min_user_turns: int = 2,
    ):
        super().__init__(
            analyzer_model=analyzer_model,
            analyzer_prompt_version=analyzer_prompt_version,
            analyzer_timeout=analyzer_timeout,
            min_user_turns=min_user_turns,
        )

    async def _build_edited_messages(
        self,
        trace: "ConversationTrace",
        analysis: AnalysisResult,
        model_client: "ModelClient",
    ) -> tuple[list[Message], None]:
        return _build_s2_messages(trace, analysis), None


class HuangAC3RewriteStrategy(_HuangAC3Base):
    """AC3-Rewrite for Huang eval — analyzer + LLM compaction.

    Equivalent to the legacy ``generate_s3`` in :mod:`replay`. After the
    analyzer flags issues, calls the compaction prompt to produce
    ``<task_spec>`` and ``<work_so_far>`` tags, then builds the compacted
    message layout from those.
    """

    async def _build_edited_messages(
        self,
        trace: "ConversationTrace",
        analysis: AnalysisResult,
        model_client: "ModelClient",
    ) -> tuple[list[Message], str]:
        return await _build_s3_messages(trace, analysis, model_client, self.analyzer_model)


class HuangAC3AugmentStrategy(_HuangAC3Base):
    """AC3-Augment for Huang eval — append analyzer output to context, no rewrite.

    New in Phase 2: Huang eval previously had no Augment variant. Appends the
    analyzer's structured output as a system note before the last user
    message, mirroring LiC's ``AC3AugmentStrategy`` semantics but staying in
    the Huang one-shot generation flow.
    """

    async def _build_edited_messages(
        self,
        trace: "ConversationTrace",
        analysis: AnalysisResult,
        model_client: "ModelClient",
    ) -> tuple[list[Message], None]:
        return _build_augment_messages(trace, analysis), None


# ---------------------------------------------------------------------------
# Message builders — bit-for-bit copies of the layouts in replay.py.
# Kept as module-level helpers so the legacy generate_* wrappers in
# replay.py can call them directly without instantiating a strategy.
# ---------------------------------------------------------------------------


def _build_s15_messages(
    trace: "ConversationTrace", analysis: AnalysisResult
) -> list[Message]:
    """S1.5 / AC3-Reset message layout. Mirrors generate_s15 in replay.py."""
    task_spec = analysis.user_intent
    aligned = analysis.aligned
    issues = analysis.issues

    sys_msg = trace.system_message
    last_user = trace.last_user_message

    compact_parts = [
        "The conversation history has been compacted. Below is a summary of the "
        "user's full specification and the work completed so far that is consistent "
        "with it.",
        f"# User Task Specification (So Far)\n{task_spec}",
    ]
    if aligned:
        compact_parts.append(f"# What Looks Right So Far\n{aligned}")

    new_messages: list[Message] = []
    if sys_msg:
        sys_content = sys_msg.content
        if issues and issues.strip().lower() != "none":
            sys_content += f"\n\n<context_edit_notes>\n{issues}\n</context_edit_notes>"
        new_messages.append(Message(role="system", content=sys_content))
    new_messages.append(Message(role="user", content="\n\n".join(compact_parts)))
    if last_user:
        new_messages.append(
            Message(
                role="assistant",
                content="I'll work on this now based on the updated specification.",
            )
        )
        new_messages.append(Message(role="user", content=last_user.content))
    return new_messages


def _build_s2_messages(
    trace: "ConversationTrace", analysis: AnalysisResult
) -> list[Message]:
    """S2 / AC3-Gated-Reset message layout. Mirrors generate_s2 in replay.py."""
    task_spec = analysis.user_intent
    aligned = analysis.aligned
    issues = analysis.issues

    sys_msg = trace.system_message
    last_user = trace.last_user_message

    compact_parts = [
        "The conversation history has been compacted. A mid-task review identified "
        "opportunities to improve the approach. Below is a clean summary to "
        "continue from.",
        f"# User Task Specification (So Far)\n{task_spec}",
    ]
    if aligned:
        compact_parts.append(
            "# Progress So Far\n"
            "The following appears to be correct and useful based on analysis of "
            "the conversation so far.\n\n"
            f"{aligned}"
        )

    new_messages: list[Message] = []
    if sys_msg:
        sys_content = sys_msg.content
        if issues and issues.strip().lower() != "none":
            sys_content += f"\n\n<context_edit_notes>\n{issues}\n</context_edit_notes>"
        new_messages.append(Message(role="system", content=sys_content))
    new_messages.append(Message(role="user", content="\n\n".join(compact_parts)))
    if last_user:
        new_messages.append(
            Message(
                role="assistant",
                content="I'll work on this now based on the updated specification.",
            )
        )
        new_messages.append(Message(role="user", content=last_user.content))
    return new_messages


async def _build_s3_messages(
    trace: "ConversationTrace",
    analysis: AnalysisResult,
    model_client: "ModelClient",
    compaction_model: str,
) -> tuple[list[Message], str]:
    """S3 / AC3-Rewrite message layout. Mirrors generate_s3 in replay.py.

    Returns (messages, compaction_output) so the caller can log the raw
    compaction-LLM output if desired.
    """
    conversation_str = trace.get_conversation_string(skip_system=True)
    compaction_template = _COMPACTION_PROMPT_PATH.read_text()
    compaction_prompt = compaction_template.format(
        conversation=conversation_str,
        analysis_user_intent=analysis.user_intent,
        analysis_aligned=analysis.aligned,
        analysis_issues=analysis.issues,
    )
    compaction_response = await model_client.generate(
        messages=[{"role": "user", "content": compaction_prompt}],
        model=compaction_model,
        temperature=0.0,
        timeout=120,
    )
    compaction_output = compaction_response.content
    task_spec = _extract_tag(compaction_output, "task_spec") or analysis.user_intent
    work_so_far = _extract_tag(compaction_output, "work_so_far")

    sys_msg = trace.system_message
    last_user = trace.last_user_message

    compact_parts = [
        "The conversation history has been compacted. Below is a summary of the "
        "user's full specification and the work completed so far that is consistent "
        "with it.",
        f"# User Task Specification (So Far)\n{task_spec}",
    ]
    if work_so_far and work_so_far.lower() != "none":
        compact_parts.append(f"# What Looks Right So Far\n{work_so_far}")

    new_messages: list[Message] = []
    if sys_msg:
        new_messages.append(Message(role="system", content=sys_msg.content))
    new_messages.append(Message(role="user", content="\n\n".join(compact_parts)))
    if last_user:
        new_messages.append(
            Message(
                role="assistant",
                content="I'll work on this now based on the updated specification.",
            )
        )
        new_messages.append(Message(role="user", content=last_user.content))
    return new_messages, compaction_output


def _build_augment_messages(
    trace: "ConversationTrace", analysis: AnalysisResult
) -> list[Message]:
    """AC3-Augment message layout for Huang eval.

    Keeps the full conversation intact and inserts an analyzer note as a system
    message addendum (so the assistant sees the full history plus a critical
    review of its current approach). The note is a structured combination of
    the task spec and the analyzer's aligned/issues fields.
    """
    messages = list(trace.get_active_messages())  # copy
    note = (
        "<conversation_analysis>\n"
        f"# User Task Specification (So Far)\n{analysis.user_intent}\n\n"
        f"# What Looks Right So Far\n{analysis.aligned or '(nothing flagged)'}\n\n"
        f"# Issues To Address\n{analysis.issues or '(none)'}\n"
        "</conversation_analysis>"
    )
    if analysis.corrective_direction:
        note += (
            f"\n\n<corrective_direction>\n{analysis.corrective_direction}\n"
            "</corrective_direction>"
        )

    # Find the system message (if any) and append the note. Otherwise insert a
    # new system message at the front.
    new_messages: list[Message] = []
    inserted = False
    for msg in messages:
        if msg.role == "system" and not inserted:
            new_messages.append(
                Message(role="system", content=msg.content + "\n\n" + note)
            )
            inserted = True
        else:
            new_messages.append(msg)
    if not inserted:
        new_messages.insert(0, Message(role="system", content=note))
    return new_messages
