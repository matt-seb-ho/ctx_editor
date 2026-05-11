"""Core replay engine: build traces per condition, generate responses.

For each turn in a real conversation, regenerates the assistant's response
under different context conditions (FC, AO, S3, S1.5).
"""

import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from ..core.trace import ConversationTrace
from ..core.types import Message

if TYPE_CHECKING:
    from ..models.base import ModelClient

logger = logging.getLogger(__name__)

_AO_SYSTEM_MSG = (Path(__file__).parent / "prompts" / "ao_system_message.txt").read_text()

# Compaction prompt for S3 (reuse existing)
_COMPACTION_PROMPT_PATH = (
    Path(__file__).parent.parent / "strategies" / "prompts" / "context_compaction.txt"
)

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
# S3 (Surgical edit via LLM compaction) condition
# ---------------------------------------------------------------------------

def _extract_tag(text: str, tag: str) -> str:
    """Extract content from an XML tag."""
    match = re.search(rf"<{tag}>(.*?)</{tag}>", text, re.DOTALL)
    return match.group(1).strip() if match else ""


async def generate_s3(
    turns: list[dict[str, str]],
    turn_index: int,
    model_client: "ModelClient",
    respondent_model: str,
    analyzer_model: str,
    analyzer_prompt_version: str = "v8",
) -> tuple[str, dict[str, Any]]:
    """Generate S3 response: analyzer-driven surgical context editing.

    1. Build ConversationTrace from original messages up to turn_index
    2. Run ConversationAnalyzer to get task_spec/aligned/issues
    3. Feed analysis + conversation into compaction prompt (LLM compaction)
    4. Generate response from compacted context

    ``analyzer_prompt_version`` selects the registered analyzer prompt set;
    see :mod:`ctx_editor.strategies.analyzer_prompts` for the registry.

    Returns:
        Tuple of (response_text, analysis_metadata).
    """
    from ..strategies.analyzer import ConversationAnalyzer

    # Build trace from original conversation
    trace = build_fc_trace(turns, turn_index)

    # Run analyzer (two-query hard attention)
    analyzer = ConversationAnalyzer(
        model=analyzer_model,
        timeout=120,
        prompt_version=analyzer_prompt_version,
    )
    analysis = await analyzer.analyze(trace, model_client)

    analysis_meta = {
        "user_intent": analysis.user_intent,
        "aligned": analysis.aligned,
        "issues": analysis.issues,
        "needs_edit": analysis.needs_edit,
    }

    # If no issues, just use FC (no edit needed)
    if not analysis.needs_edit:
        api_messages = _render_for_assistant(trace.get_active_messages())
        response = await model_client.generate(
            messages=api_messages,
            model=respondent_model,
            temperature=0.7,
            timeout=120,
        )
        analysis_meta["edited"] = False
        return response.content, analysis_meta

    # Run LLM compaction (S3): analysis + conversation -> compacted context
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
        model=analyzer_model,
        temperature=0.0,
        timeout=120,
    )
    compaction_output = compaction_response.content

    # Parse compaction output
    task_spec = _extract_tag(compaction_output, "task_spec") or analysis.user_intent
    work_so_far = _extract_tag(compaction_output, "work_so_far")

    # Build compacted messages (same format as run_s15_experiment.py)
    compacted_messages = []

    # System message from trace (if any)
    sys_msg = trace.system_message
    if sys_msg:
        compacted_messages.append({"role": "system", "content": sys_msg.content})

    # Compacted conversation
    compact_parts = [
        "The conversation history has been compacted. Below is a summary of the "
        "user's full specification and the work completed so far that is consistent "
        "with it.",
        f"# User Task Specification (So Far)\n{task_spec}",
    ]
    if work_so_far and work_so_far.lower() != "none":
        compact_parts.append(f"# What Looks Right So Far\n{work_so_far}")

    compacted_messages.append({"role": "user", "content": "\n\n".join(compact_parts)})

    # Last user message
    last_user = trace.last_user_message
    if last_user:
        compacted_messages.append({
            "role": "assistant",
            "content": "I'll work on this now based on the updated specification.",
        })
        compacted_messages.append({"role": "user", "content": last_user.content})

    # Generate from compacted context
    api_messages = _render_raw_messages(compacted_messages)
    response = await model_client.generate(
        messages=api_messages,
        model=respondent_model,
        temperature=0.7,
        timeout=120,
    )

    analysis_meta["edited"] = True
    analysis_meta["compaction_output"] = compaction_output

    return response.content, analysis_meta


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
) -> tuple[str, dict[str, Any]]:
    """Generate S2 response: gated context edit (only resets when issues found).

    Uses the v11 analyzer prompt (generalized from tau2's v10 "mid-task reflection"
    framing). Key difference from S1.5/S3: S2 gates on needs_edit -- if the analyzer
    finds no issues, returns FC (no reset). This avoids unnecessary resets on turns
    where the conversation is going well.

    When reset IS triggered, uses programmatic template (like S1.5) with the v11
    analysis output. No LLM compaction step.

    Returns:
        Tuple of (response_text, analysis_metadata).
    """
    from ..strategies.analyzer import ConversationAnalyzer

    trace = build_fc_trace(turns, turn_index)

    # Gate: skip analysis if too few turns
    user_turn_count = sum(1 for t in turns[:turn_index + 1] if t["role"] == "user")
    if user_turn_count < min_turns:
        api_messages = _render_for_assistant(trace.get_active_messages())
        response = await model_client.generate(
            messages=api_messages,
            model=respondent_model,
            temperature=0.7,
            timeout=120,
        )
        return response.content, {"edited": False, "gated": "too_few_turns"}

    # Run analyzer
    analyzer = ConversationAnalyzer(
        model=analyzer_model,
        timeout=120,
        prompt_version=analyzer_prompt_version,
    )
    analysis = await analyzer.analyze(trace, model_client)

    analysis_meta = {
        "user_intent": analysis.user_intent,
        "aligned": analysis.aligned,
        "issues": analysis.issues,
        "needs_edit": analysis.needs_edit,
        "analyzer_prompt_version": analyzer_prompt_version,
    }

    # Gate: if no issues, use FC (no reset)
    if not analysis.needs_edit:
        api_messages = _render_for_assistant(trace.get_active_messages())
        response = await model_client.generate(
            messages=api_messages,
            model=respondent_model,
            temperature=0.7,
            timeout=120,
        )
        analysis_meta["edited"] = False
        return response.content, analysis_meta

    # Issues found: build compacted context (programmatic template)
    task_spec = analysis.user_intent
    aligned = analysis.aligned

    compacted_messages = []

    sys_msg = trace.system_message
    if sys_msg:
        compacted_messages.append({"role": "system", "content": sys_msg.content})

    compact_parts = [
        "The conversation history has been compacted. A mid-task review identified "
        "opportunities to improve the approach. Below is a clean summary to "
        "continue from.",
        f"# User Task Specification (So Far)\n{task_spec}",
    ]
    if aligned:
        compact_parts.append(
            f"# Progress So Far\n"
            f"The following appears to be correct and useful based on analysis of "
            f"the conversation so far.\n\n"
            f"{aligned}"
        )

    compacted_messages.append({"role": "user", "content": "\n\n".join(compact_parts)})

    # Inject issues as context edit notes in system message
    issues = analysis.issues
    if issues and issues.strip().lower() != "none":
        if compacted_messages and compacted_messages[0].get("role") == "system":
            compacted_messages[0]["content"] += (
                f"\n\n<context_edit_notes>\n{issues}\n</context_edit_notes>"
            )

    last_user = trace.last_user_message
    if last_user:
        compacted_messages.append({
            "role": "assistant",
            "content": "I'll work on this now based on the updated specification.",
        })
        compacted_messages.append({"role": "user", "content": last_user.content})

    api_messages = _render_raw_messages(compacted_messages)
    response = await model_client.generate(
        messages=api_messages,
        model=respondent_model,
        temperature=0.7,
        timeout=120,
    )

    analysis_meta["edited"] = True
    return response.content, analysis_meta


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
) -> tuple[str, dict[str, Any]]:
    """Generate S1.5 response: analyzer output programmatically templated into context.

    Same as S3 but without the LLM compaction step -- analysis fields are
    directly templated into the compacted context.

    ``analyzer_prompt_version`` selects the registered analyzer prompt set;
    see :mod:`ctx_editor.strategies.analyzer_prompts` for the registry.

    Args:
        memory: Optional MemoryModule to inject into analyzer compare query.

    Returns:
        Tuple of (response_text, analysis_metadata).
    """
    from ..strategies.analyzer import ConversationAnalyzer

    # Build trace from original conversation
    trace = build_fc_trace(turns, turn_index)

    # Run analyzer
    analyzer = ConversationAnalyzer(
        model=analyzer_model,
        timeout=120,
        prompt_version=analyzer_prompt_version,
    )
    analysis = await analyzer.analyze(trace, model_client, memory=memory)

    analysis_meta = {
        "user_intent": analysis.user_intent,
        "aligned": analysis.aligned,
        "issues": analysis.issues,
        "needs_edit": analysis.needs_edit,
    }

    # If no issues, just use FC
    if not analysis.needs_edit:
        api_messages = _render_for_assistant(trace.get_active_messages())
        response = await model_client.generate(
            messages=api_messages,
            model=respondent_model,
            temperature=0.7,
            timeout=120,
        )
        analysis_meta["edited"] = False
        return response.content, analysis_meta

    # Programmatic compaction (no LLM call)
    task_spec = analysis.user_intent
    aligned = analysis.aligned

    compacted_messages = []

    sys_msg = trace.system_message
    if sys_msg:
        compacted_messages.append({"role": "system", "content": sys_msg.content})

    compact_parts = [
        "The conversation history has been compacted. Below is a summary of the "
        "user's full specification and the work completed so far that is consistent "
        "with it.",
        f"# User Task Specification (So Far)\n{task_spec}",
    ]
    if aligned:
        compact_parts.append(f"# What Looks Right So Far\n{aligned}")

    compacted_messages.append({"role": "user", "content": "\n\n".join(compact_parts)})

    # Inject issues as context edit notes
    issues = analysis.issues
    if issues and issues.strip().lower() != "none" and compacted_messages[0].get("role") == "system":
        compacted_messages[0]["content"] += (
            f"\n\n<context_edit_notes>\n{issues}\n</context_edit_notes>"
        )

    last_user = trace.last_user_message
    if last_user:
        compacted_messages.append({
            "role": "assistant",
            "content": "I'll work on this now based on the updated specification.",
        })
        compacted_messages.append({"role": "user", "content": last_user.content})

    api_messages = _render_raw_messages(compacted_messages)
    response = await model_client.generate(
        messages=api_messages,
        model=respondent_model,
        temperature=0.7,
        timeout=120,
    )

    analysis_meta["edited"] = True
    return response.content, analysis_meta
