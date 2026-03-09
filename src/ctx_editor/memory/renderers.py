"""Trajectory rendering functions for different memory update targets.

Each renderer takes a SimulationResult and returns a string representation
of the conversation suitable for reflection by that target's updater.
"""

from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from ..core.types import SimulationResult


def render_for_assistant(trajectory: "SimulationResult") -> str:
    """Standard role/content rendering for the assistant target.

    Shows only what the assistant saw — active messages, no edit internals.
    """
    messages = trajectory.trace.get("messages", [])
    parts = []
    for msg in messages:
        role = msg.get("role", "")
        if role in ("system", "user", "assistant") and msg.get("visible", True):
            parts.append(f"[{role}] {msg.get('content', '')}")
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

    parts = [f"Final outcome: {final_outcome} (score: {trajectory.score}, turns: {trajectory.num_turns})"]

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
            parts.append(f"[{role}] {msg.get('content', '')}")

    return "\n\n".join(parts)


# Registry mapping target name → renderer function
RENDERERS: dict[str, Callable[["SimulationResult"], str]] = {
    "assistant": render_for_assistant,
    "context_editor": render_for_context_editor,
    "edit_decision": render_for_edit_decision,
}
