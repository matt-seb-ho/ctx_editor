"""Core replay engine: build traces per condition, generate responses.

For each turn in a real conversation, regenerates the assistant's response
under different context conditions (FC, AO, and the AC3 variants S1.5/S2/S3
plus Augment). The AC3 variants now live in :mod:`huang_eval.strategies` as
``ContextStrategy`` subclasses; the ``generate_*`` functions in this module
are thin wrappers that build the trace, invoke the strategy, and ship the
response back to the caller.
"""

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from ..core.trace import ConversationTrace
from ..core.types import Message

if TYPE_CHECKING:
    from ..models.base import ModelClient
    from .strategies import _HuangAC3Base

logger = logging.getLogger(__name__)

_AO_SYSTEM_MSG = (Path(__file__).parent / "prompts" / "ao_system_message.txt").read_text()

# Option 2 rendering wrapper (same as simulators use)
_ASSISTANT_PROMPT_WRAPPER = """\
Here is the current conversation:

{conversation}

Please respond to the user. Do not include [user] or [assistant] tags in your response."""


def _render_for_assistant(context_messages: list[Message]) -> list[dict[str, str]]:
    """Render context messages into Option 2 format for the API call.

    Replicates the rendering from CollabLLMSimulator._render_for_assistant.
    """
    system_content = None
    conversation_parts = []

    for msg in context_messages:
        if msg.role == "system":
            system_content = msg.content
        else:
            conversation_parts.append(f"[{msg.role}]\n{msg.content}")

    conversation_str = "\n\n".join(conversation_parts)
    user_content = _ASSISTANT_PROMPT_WRAPPER.format(conversation=conversation_str)

    api_messages = []
    if system_content:
        api_messages.append({"role": "system", "content": system_content})
    api_messages.append({"role": "user", "content": user_content})

    return api_messages


def _render_raw_messages(messages: list[dict[str, str]]) -> list[dict[str, str]]:
    """Render raw message dicts into Option 2 format for the API call."""
    system_content = None
    conversation_parts = []

    for msg in messages:
        if msg["role"] == "system":
            system_content = msg["content"]
        else:
            conversation_parts.append(f"[{msg['role']}]\n{msg['content']}")

    conversation_str = "\n\n".join(conversation_parts)
    user_content = _ASSISTANT_PROMPT_WRAPPER.format(conversation=conversation_str)

    api_messages = []
    if system_content:
        api_messages.append({"role": "system", "content": system_content})
    api_messages.append({"role": "user", "content": user_content})

    return api_messages


# ---------------------------------------------------------------------------
# FC (Full Context) condition
# ---------------------------------------------------------------------------

def build_fc_trace(
    turns: list[dict[str, str]],
    up_to_and_including: int,
) -> ConversationTrace:
    """Build a ConversationTrace with full context up to (and including) the target user turn."""
    trace = ConversationTrace()
    for msg in turns[: up_to_and_including + 1]:
        if msg["role"] == "user":
            trace.add_user_message(msg["content"])
        elif msg["role"] == "assistant":
            trace.add_assistant_message(msg["content"])
    return trace


async def generate_fc(
    turns: list[dict[str, str]],
    turn_index: int,
    model_client: "ModelClient",
    model: str,
) -> str:
    """Generate FC response: model sees full original context."""
    trace = build_fc_trace(turns, turn_index)
    api_messages = _render_for_assistant(trace.get_active_messages())

    response = await model_client.generate(
        messages=api_messages,
        model=model,
        temperature=0.7,
        timeout=120,
    )
    return response.content


# ---------------------------------------------------------------------------
# AO (Assistant-Omitted) condition
# ---------------------------------------------------------------------------

async def generate_ao(
    turns: list[dict[str, str]],
    turn_index: int,
    model_client: "ModelClient",
    model: str,
) -> str:
    """Generate AO response: assistant messages replaced with [Response provided]."""
    messages = []
    messages.append({"role": "system", "content": _AO_SYSTEM_MSG})

    for msg in turns[: turn_index + 1]:
        if msg["role"] == "user":
            messages.append({"role": "user", "content": msg["content"]})
        elif msg["role"] == "assistant":
            messages.append({"role": "assistant", "content": "[Response provided]"})

    api_messages = _render_raw_messages(messages)

    response = await model_client.generate(
        messages=api_messages,
        model=model,
        temperature=0.7,
        timeout=120,
    )
    return response.content


# ---------------------------------------------------------------------------
# AC3 variants (S1.5 / S2 / S3 / Augment) — each delegates to a strategy
# class in huang_eval.strategies that implements ``ContextStrategy``.
# ---------------------------------------------------------------------------


async def _generate_with_strategy(
    strategy: "_HuangAC3Base",
    turns: list[dict[str, str]],
    turn_index: int,
    model_client: "ModelClient",
    respondent_model: str,
) -> tuple[str, dict[str, Any]]:
    """Shared driver: build trace → strategy.prepare_context → generate.

    All Huang AC3 variants share this skeleton; only the strategy object differs.
    """
    trace = build_fc_trace(turns, turn_index)
    messages = await strategy.prepare_context(trace, memory=None, model_client=model_client)
    api_messages = _render_for_assistant(messages)
    response = await model_client.generate(
        messages=api_messages,
        model=respondent_model,
        temperature=0.7,
        timeout=120,
    )

    # Pack metadata for the logger / judge plumbing.
    meta: dict[str, Any] = {"edited": False}
    result = strategy.last_result
    if result is not None:
        meta["edited"] = result.edited
        if result.gated_reason:
            meta["gated"] = result.gated_reason
        if result.analysis is not None:
            meta["user_intent"] = result.analysis.user_intent
            meta["aligned"] = result.analysis.aligned
            meta["issues"] = result.analysis.issues
            meta["needs_edit"] = result.analysis.needs_edit
        if result.compaction_output is not None:
            meta["compaction_output"] = result.compaction_output
    return response.content, meta


async def generate_s3(
    turns: list[dict[str, str]],
    turn_index: int,
    model_client: "ModelClient",
    respondent_model: str,
    analyzer_model: str,
    analyzer_prompt_version: str = "v8",
    analysis_cache_dir: Optional[str] = None,
    compaction_prompt_name: str = "context_compaction",
    open_ended_output: bool = False,
) -> tuple[str, dict[str, Any]]:
    """Generate S3 response: AC3-Rewrite (analyzer + LLM compaction).

    Thin wrapper around :class:`HuangAC3RewriteStrategy`. ``analyzer_prompt_version``
    selects the registered analyzer prompt set; see
    :mod:`ctx_editor.strategies.analyzer_prompts` for the registry.

    ``compaction_prompt_name`` picks the rewriter prompt file (default = legacy
    v1 ``context_compaction``). Pair ``compaction_prompt_name=context_compaction_v8``
    with ``open_ended_output=True`` to run the R6 open-ended winner.
    """
    from .strategies import HuangAC3RewriteStrategy

    strategy = HuangAC3RewriteStrategy(
        analyzer_model=analyzer_model,
        analyzer_prompt_version=analyzer_prompt_version,
        analysis_cache_dir=analysis_cache_dir,
        compaction_prompt_name=compaction_prompt_name,
        open_ended_output=open_ended_output,
    )
    return await _generate_with_strategy(
        strategy, turns, turn_index, model_client, respondent_model
    )


# ---------------------------------------------------------------------------
# S2 (Gated context edit with v11 analyzer) condition
# ---------------------------------------------------------------------------

async def generate_s2(
    turns: list[dict[str, str]],
    turn_index: int,
    model_client: "ModelClient",
    respondent_model: str,
    analyzer_model: str,
    analyzer_prompt_version: str = "v11",
    min_turns: int = 2,
    analysis_cache_dir: Optional[str] = None,
) -> tuple[str, dict[str, Any]]:
    """Generate S2 response: AC3-Gated-Reset (programmatic reset, gated by needs_edit + min_turns).

    Thin wrapper around :class:`HuangAC3GatedResetStrategy`. Uses the v11
    analyzer prompt by default (generalized from tau2's v10 "mid-task
    reflection" framing).
    """
    from .strategies import HuangAC3GatedResetStrategy

    strategy = HuangAC3GatedResetStrategy(
        analyzer_model=analyzer_model,
        analyzer_prompt_version=analyzer_prompt_version,
        min_user_turns=min_turns,
        analysis_cache_dir=analysis_cache_dir,
    )
    response, meta = await _generate_with_strategy(
        strategy, turns, turn_index, model_client, respondent_model
    )
    meta["analyzer_prompt_version"] = analyzer_prompt_version
    return response, meta


# ---------------------------------------------------------------------------
# S1.5 (Programmatic reset) condition
# ---------------------------------------------------------------------------

async def generate_s15(
    turns: list[dict[str, str]],
    turn_index: int,
    model_client: "ModelClient",
    respondent_model: str,
    analyzer_model: str,
    memory: Optional[Any] = None,
    analyzer_prompt_version: str = "v8",
    analysis_cache_dir: Optional[str] = None,
) -> tuple[str, dict[str, Any]]:
    """Generate S1.5 response: AC3-Reset (programmatic, no LLM rewrite).

    Thin wrapper around :class:`HuangAC3ResetStrategy`. ``analyzer_prompt_version``
    selects the registered analyzer prompt set; see
    :mod:`ctx_editor.strategies.analyzer_prompts` for the registry.

    Args:
        memory: Optional MemoryModule to inject into analyzer compare query.
    """
    from .strategies import HuangAC3ResetStrategy

    strategy = HuangAC3ResetStrategy(
        analyzer_model=analyzer_model,
        analyzer_prompt_version=analyzer_prompt_version,
        analysis_cache_dir=analysis_cache_dir,
    )
    # Route memory through prepare_context — the strategy passes it to the analyzer.
    trace = build_fc_trace(turns, turn_index)
    messages = await strategy.prepare_context(trace, memory=memory, model_client=model_client)
    api_messages = _render_for_assistant(messages)
    response = await model_client.generate(
        messages=api_messages,
        model=respondent_model,
        temperature=0.7,
        timeout=120,
    )

    meta: dict[str, Any] = {"edited": False}
    result = strategy.last_result
    if result is not None:
        meta["edited"] = result.edited
        if result.analysis is not None:
            meta["user_intent"] = result.analysis.user_intent
            meta["aligned"] = result.analysis.aligned
            meta["issues"] = result.analysis.issues
            meta["needs_edit"] = result.analysis.needs_edit
    return response.content, meta


async def generate_augment(
    turns: list[dict[str, str]],
    turn_index: int,
    model_client: "ModelClient",
    respondent_model: str,
    analyzer_model: str,
    memory: Optional[Any] = None,
    analyzer_prompt_version: str = "v8",
    analysis_cache_dir: Optional[str] = None,
) -> tuple[str, dict[str, Any]]:
    """Generate Augment response: AC3-Augment for Huang eval (new in Phase 2).

    Keeps the full conversation; injects the analyzer's structured output as a
    system-message addendum. The assistant sees the same history as FC plus a
    critical review of its approach so far.
    """
    from .strategies import HuangAC3AugmentStrategy

    strategy = HuangAC3AugmentStrategy(
        analyzer_model=analyzer_model,
        analyzer_prompt_version=analyzer_prompt_version,
        analysis_cache_dir=analysis_cache_dir,
    )
    trace = build_fc_trace(turns, turn_index)
    messages = await strategy.prepare_context(trace, memory=memory, model_client=model_client)
    api_messages = _render_for_assistant(messages)
    response = await model_client.generate(
        messages=api_messages,
        model=respondent_model,
        temperature=0.7,
        timeout=120,
    )
    meta: dict[str, Any] = {"edited": False}
    result = strategy.last_result
    if result is not None:
        meta["edited"] = result.edited
        if result.analysis is not None:
            meta["user_intent"] = result.analysis.user_intent
            meta["aligned"] = result.analysis.aligned
            meta["issues"] = result.analysis.issues
            meta["needs_edit"] = result.analysis.needs_edit
    return response.content, meta
