"""Trajectory rendering functions for different memory update targets.

Each renderer takes a SimulationResult and returns a string representation
of the conversation suitable for reflection by that target's updater.
"""

import re
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from ..core.types import SimulationResult


# Regex to strip S1's embedded <conversation_analysis> blocks from user messages
_ANALYSIS_TAG_RE = re.compile(r"\n*<conversation_analysis>.*?</conversation_analysis>", re.DOTALL)


def _format_analysis_block(log_data: dict) -> str:
    """Format a conversation_analysis log entry as a readable block."""
    parts = []
    if log_data.get("user_intent"):
        parts.append(f"# User Task Specification (So Far)\n{log_data['user_intent']}")
    if log_data.get("aligned"):
        parts.append(f"# What Looks Right\n{log_data['aligned']}")
    if log_data.get("issues") and log_data.get("needs_edit"):
        parts.append(f"# What Needs to Change\n{log_data['issues']}")
    elif log_data.get("issues"):
        parts.append(f"# Notes\n{log_data['issues']}")
    return "\n\n".join(parts) if parts else "(no analysis content)"


def render_for_assistant(trajectory: "SimulationResult") -> str:
    """Standard role/content rendering for the assistant target.

    Shows only what the assistant saw — active messages, no edit internals.
    """
    messages = trajectory.trace.get("messages", [])
    parts = []
    for msg in messages:
        role = msg.get("role", "")
        if role in ("system", "user", "assistant") and msg.get("visible", True):
            parts.append(f"[{role}]\n{msg.get('content', '')}")
    return "\n\n".join(parts)


def render_for_context_editor(trajectory: "SimulationResult") -> str:
    """Renders the full trajectory with context edit operations highlighted.

    Shows all messages (including archived ones) and marks where thread resets
    occurred and what the editor produced at each edit point.
    """
    messages = trajectory.trace.get("messages", [])
    logs = trajectory.trace.get("logs", [])

    # Extract edit events in order
    edit_logs = [l for l in logs if l["type"] in ("context_edit_output", "conversation_reset")]

    parts = []
    reset_count = 0

    for msg in messages:
        role = msg.get("role", "")
        visible = msg.get("visible", True)
        content = msg.get("content", "")

        if role not in ("system", "user", "assistant"):
            continue

        # When we hit the first visible message after a reset, insert an edit marker
        if visible and reset_count < len(edit_logs):
            edit_log = edit_logs[reset_count]
            if edit_log["type"] == "context_edit_output":
                edited = edit_log["data"].get("edited_context", "(no output)")
                parts.append(
                    f"\n--- CONTEXT EDIT (Reset #{reset_count + 1}) ---\n"
                    f"Editor output:\n{edited}\n"
                    f"--- NEW THREAD BEGINS ---\n"
                )
            reset_count += 1

        prefix = f"[{role}]" if visible else f"[{role} — ARCHIVED]"
        parts.append(f"{prefix} {content}")

    return "\n\n".join(parts)


def render_for_edit_decision(trajectory: "SimulationResult") -> str:
    """Renders trajectory focusing on edit decision points and their outcomes.

    Shows each decision made (should_edit + reasoning), then the full
    active conversation for context.
    """
    logs = trajectory.trace.get("logs", [])
    messages = trajectory.trace.get("messages", [])
    final_outcome = "Success" if trajectory.is_correct else "Failure"

    parts = [
        f"Final outcome: {final_outcome} (score: {trajectory.score}, turns: {trajectory.num_turns})"
    ]

    decision_logs = [l for l in logs if l["type"] == "edit_decision"]

    if decision_logs:
        parts.append(f"\n--- Edit Decisions ({len(decision_logs)} total) ---")
        for i, log in enumerate(decision_logs, 1):
            d = log["data"]
            decision_str = "EDIT" if d.get("should_edit") else "NO EDIT"
            reasoning = d.get("reasoning", "")
            notes = d.get("notes", "")
            entry = f"Decision {i}: {decision_str}\nReasoning: {reasoning}"
            if notes:
                entry += f"\nNotes: {notes}"
            parts.append(entry)
    else:
        parts.append("\n(No edit decisions were made in this trajectory)")

    parts.append("\n--- Full Conversation ---")
    for msg in messages:
        role = msg.get("role", "")
        if role in ("system", "user", "assistant") and msg.get("visible", True):
            parts.append(f"[{role}]\n{msg.get('content', '')}")

    return "\n\n".join(parts)


def render_for_analyzer(trajectory: "SimulationResult") -> str:
    """Renders the full trajectory with analysis outputs interleaved chronologically.

    Reconstructs the conversation timeline showing analyses at the point they
    occurred. Handles both S1 (append analysis) and S2 (context edit v2) traces:

    S1 (append): Analysis was appended to user messages as <conversation_analysis>
    tags. This renderer strips those tags and shows the analysis as a separate
    [conversation analysis] block, reflecting the flow: user spoke → analysis
    generated → assistant saw analysis alongside the conversation.

    S2 (context edit): Analysis may trigger a context rewrite. The renderer shows
    the analysis, the edit decision, and (if edited) a clear NEW CONVERSATION
    boundary followed by the compacted context.

    Uses timestamps to merge messages and log events into a unified timeline.
    """
    messages = trajectory.trace.get("messages", [])
    logs = trajectory.trace.get("logs", [])

    # Build unified timeline from messages and logs
    # Each event: (timestamp, sequence_number, type, data)
    # sequence_number ensures stable ordering within same-second timestamps
    events = []
    seq = 0

    for msg in messages:
        role = msg.get("role", "")
        if role not in ("system", "user", "assistant", "compacted conversation"):
            continue
        events.append((msg.get("timestamp", ""), seq, "msg", msg))
        seq += 1

    for log_entry in logs:
        if log_entry["type"] in ("conversation_analysis", "edit_decision"):
            events.append((log_entry.get("timestamp", ""), seq, "log", log_entry))
            seq += 1

    # Sort by (timestamp, seq) — ISO format strings sort chronologically
    events.sort(key=lambda e: (e[0], e[1]))

    # Render the timeline
    parts = []
    system_content_shown = None  # Track system message to skip duplicates from resets
    reset_count = 0

    for _, _, etype, data in events:
        if etype == "msg":
            role = data.get("role", "")
            content = data.get("content", "")

            # Strip embedded <conversation_analysis> tags from user messages (S1 artifact)
            if role == "user" and "<conversation_analysis>" in content:
                content = _ANALYSIS_TAG_RE.sub("", content).rstrip()

            # Handle compacted conversation → NEW CONVERSATION boundary
            if role == "compacted conversation":
                reset_count += 1
                parts.append(
                    f"\n{'=' * 50}\n" f"NEW CONVERSATION (Reset #{reset_count})\n" f"{'=' * 50}"
                )
                parts.append(f"[compacted conversation]\n{content}")
                continue

            # Skip duplicate system messages from resets (same content as original)
            if role == "system":
                if system_content_shown is not None and content == system_content_shown:
                    continue
                system_content_shown = content

            parts.append(f"[{role}]\n{content}")

        elif etype == "log":
            log_type = data["type"]
            log_data = data["data"]

            if log_type == "conversation_analysis":
                analysis_text = _format_analysis_block(log_data)
                parts.append(f"[conversation analysis]\n{analysis_text}")

            elif log_type == "edit_decision":
                should_edit = log_data.get("should_edit", False)
                if should_edit:
                    parts.append("→ Decision: EDIT — rewriting context")
                else:
                    parts.append("→ Decision: NO EDIT — approach is aligned")

    return "\n\n".join(parts)


# Registry mapping target name → renderer function
RENDERERS: dict[str, Callable[["SimulationResult"], str]] = {
    "assistant": render_for_assistant,
    "context_editor": render_for_context_editor,
    "edit_decision": render_for_edit_decision,
    "analyzer": render_for_analyzer,
}
