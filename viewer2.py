"""
Context Editor Trace Viewer v2

Usage:
    streamlit run viewer2.py
"""

import json
import os
from pathlib import Path
from typing import Any, Optional

import streamlit as st
import yaml

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OUTPUTS_ROOT = "outputs"

ROLE_COLORS = {
    "system": "#6c757d",
    "user": "#0d6efd",
    "assistant": "#198754",
    "compacted conversation": "#6f42c1",
    "analysis": "#fd7e14",
    "analyst": "#fd7e14",
    "context_edit_output": "#e83e8c",
    "reset_marker": "#dc3545",
}

ROLE_ICONS = {
    "system": "⚙️",
    "user": "👤",
    "assistant": "🤖",
    "compacted conversation": "📋",
    "analysis": "🔍",
    "analyst": "🔍",
    "context_edit_output": "✏️",
    "reset_marker": "🔄",
}

RESPONSE_TYPE_LABELS = {
    "answer_attempt": "Answer Attempt",
    "interrogation": "Interrogation",
    "discussion": "Discussion",
    "partial_answer": "Partial Answer",
    "other": "Other",
}

# ---------------------------------------------------------------------------
# Data loading helpers
# ---------------------------------------------------------------------------


def parse_run_input(text: str) -> list[dict[str, str]]:
    """Parse the run input textarea.

    Accepts either:
    - Newline-separated directory paths
    - YAML mapping of label -> path
    """
    text = text.strip()
    if not text:
        return []

    # Try YAML mapping first
    try:
        parsed = yaml.safe_load(text)
        if isinstance(parsed, dict):
            return [{"label": str(k), "path": str(v)} for k, v in parsed.items()]
    except yaml.YAMLError:
        pass

    # Fall back to newline-separated paths
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    return [{"label": os.path.basename(line.rstrip("/")), "path": line} for line in lines]


def resolve_path(p: str) -> str:
    """Resolve a path that may be relative to OUTPUTS_ROOT or absolute."""
    if os.path.isabs(p) and os.path.exists(p):
        return p
    # Try as relative to outputs root
    candidate = os.path.join(OUTPUTS_ROOT, p)
    if os.path.exists(candidate):
        return candidate
    # Try as-is
    if os.path.exists(p):
        return p
    return p  # Return as-is, will error later


def list_trace_files(run_dir: str) -> list[dict[str, Any]]:
    """List all trace files in a run directory, lazily (no content loading)."""
    traces_dir = os.path.join(run_dir, "traces")
    if not os.path.isdir(traces_dir):
        return []

    results = []
    for task_name in sorted(os.listdir(traces_dir)):
        task_dir = os.path.join(traces_dir, task_name)
        if not os.path.isdir(task_dir):
            continue
        for exp_type in sorted(os.listdir(task_dir)):
            exp_dir = os.path.join(task_dir, exp_type)
            if not os.path.isdir(exp_dir):
                continue
            for fname in sorted(os.listdir(exp_dir)):
                if fname.endswith(".json"):
                    results.append(
                        {
                            "task": task_name,
                            "experiment": exp_type,
                            "sample_id": fname.replace(".json", ""),
                            "path": os.path.join(exp_dir, fname),
                        }
                    )
    return results


@st.cache_data
def load_trace(path: str) -> dict[str, Any]:
    """Load a single trace file."""
    with open(path, "r") as f:
        return json.load(f)


@st.cache_data
def load_config(run_dir: str) -> Optional[dict]:
    """Load config.yaml from a run directory."""
    config_path = os.path.join(run_dir, "config.yaml")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    return None


@st.cache_data
def load_metrics(run_dir: str) -> Optional[dict]:
    """Load metrics.json from a run directory."""
    metrics_path = os.path.join(run_dir, "metrics.json")
    if os.path.exists(metrics_path):
        with open(metrics_path, "r") as f:
            return json.load(f)
    return None


@st.cache_data
def load_results_json(run_dir: str) -> Optional[list[dict]]:
    """Load results.json (list of SimulationResult dicts) from a run directory."""
    results_path = os.path.join(run_dir, "results.json")
    if os.path.exists(results_path):
        with open(results_path, "r") as f:
            return json.load(f)
    return None


def find_result_for_sample(
    results: Optional[list[dict]], sample_id: str
) -> Optional[dict]:
    """Find the result entry for a given sample_id in results.json."""
    if not results:
        return None
    # sample_id in trace files uses _ instead of /
    normalized = sample_id.replace("_", "/")
    for r in results:
        if r.get("sample_id") == normalized or r.get("sample_id") == sample_id:
            return r
    return None


def load_sample_data(data_file: str, task_id: str) -> Optional[dict]:
    """Load the original sample from the data file."""
    if not os.path.exists(data_file):
        return None
    with open(data_file, "r") as f:
        data = json.load(f)
    normalized = task_id.replace("_", "/")
    for sample in data:
        if sample.get("task_id") == task_id or sample.get("task_id") == normalized:
            return sample
    return None


# ---------------------------------------------------------------------------
# Conversation reconstruction for display
# ---------------------------------------------------------------------------


def build_display_messages(trace_data: dict) -> list[dict[str, Any]]:
    """Build an ordered list of display messages from trace data.

    Interleaves actual messages with log events (analysis, resets, evaluations)
    to create a complete timeline for display.
    """
    messages = trace_data.get("messages", [])
    logs = trace_data.get("logs", [])

    # Build a timeline: each entry has a timestamp and content
    display = []

    # Track which logs to interleave after each assistant message
    # Strategy: associate logs with the assistant turn they follow
    log_idx = 0

    for msg_idx, msg in enumerate(messages):
        role = msg.get("role", "unknown")
        visible = msg.get("visible", True)

        # For S2: insert analysis + reset marker before compacted conversation
        # when preceded by system message that starts a new reset cycle
        if role == "system" and msg_idx > 0 and not messages[msg_idx - 1].get("visible", True):
            # Check if there's a context_edit_output log to show before this reset
            while log_idx < len(logs):
                log = logs[log_idx]
                if log["type"] == "context_edit_output":
                    display.append(
                        {
                            "type": "analysis",
                            "role": "analysis",
                            "content": log["data"].get("edited_context", ""),
                            "visible": visible,
                            "timestamp": log.get("timestamp", ""),
                            "metadata": {
                                "analyzer_model": log["data"].get("analyzer_model", ""),
                                "log_type": "context_edit_output",
                            },
                        }
                    )
                    log_idx += 1
                    continue
                elif log["type"] == "conversation_reset":
                    display.append(
                        {
                            "type": "reset_marker",
                            "role": "reset_marker",
                            "content": f"Context Reset #{log['data'].get('total_resets', '?')}",
                            "visible": visible,
                            "timestamp": log.get("timestamp", ""),
                            "metadata": log["data"],
                        }
                    )
                    log_idx += 1
                    break
                elif log["type"] in (
                    "conversation_analysis",
                    "edit_decision",
                ):
                    # Skip — these are pre-reset analysis steps
                    log_idx += 1
                    continue
                else:
                    break

        # Add the message itself
        display_msg = {
            "type": "message",
            "role": role,
            "content": msg.get("content", ""),
            "visible": visible,
            "timestamp": msg.get("timestamp", ""),
            "metadata": msg.get("metadata", {}),
        }
        display.append(display_msg)

        # After each assistant message, consume relevant logs
        if role == "assistant":
            post_turn_logs = []
            while log_idx < len(logs):
                log = logs[log_idx]
                if log["type"] == "shard_revealed":
                    # This belongs to the *next* user turn, stop
                    break
                elif log["type"] == "verification":
                    post_turn_logs.append(
                        {
                            "log_type": "verification",
                            "data": log["data"],
                            "timestamp": log.get("timestamp", ""),
                        }
                    )
                    log_idx += 1
                elif log["type"] == "answer_evaluation":
                    post_turn_logs.append(
                        {
                            "log_type": "answer_evaluation",
                            "data": log["data"],
                            "timestamp": log.get("timestamp", ""),
                        }
                    )
                    log_idx += 1
                elif log["type"] == "conversation_analysis":
                    post_turn_logs.append(
                        {
                            "log_type": "conversation_analysis",
                            "data": log["data"],
                            "timestamp": log.get("timestamp", ""),
                        }
                    )
                    log_idx += 1
                elif log["type"] == "edit_decision":
                    post_turn_logs.append(
                        {
                            "log_type": "edit_decision",
                            "data": log["data"],
                            "timestamp": log.get("timestamp", ""),
                        }
                    )
                    log_idx += 1
                elif log["type"] in ("context_edit_output", "conversation_reset"):
                    # These will be consumed before the next system message
                    break
                else:
                    log_idx += 1

            if post_turn_logs:
                display[-1]["post_turn_logs"] = post_turn_logs

        # After user message, consume shard_revealed log
        if role == "user":
            while log_idx < len(logs) and logs[log_idx]["type"] == "shard_revealed":
                shard_id = logs[log_idx]["data"].get("shard_id", "?")
                display[-1].setdefault("shard_ids", []).append(shard_id)
                log_idx += 1

            # Also consume memory_injected, analysis_addendum_added
            while log_idx < len(logs) and logs[log_idx]["type"] in (
                "memory_injected",
                "analysis_addendum_added",
            ):
                display[-1].setdefault("injections", []).append(logs[log_idx])
                log_idx += 1

    return display


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------


def render_message_card(msg: dict, idx: int):
    """Render a single message as a styled card."""
    role = msg["role"]
    visible = msg.get("visible", True)
    content = msg.get("content", "")

    color = ROLE_COLORS.get(role, "#333")
    icon = ROLE_ICONS.get(role, "💬")
    opacity = "1.0" if visible else "0.5"

    # Role label
    role_label = role.title()
    if role == "compacted conversation":
        role_label = "Compacted Conversation"
    elif role == "reset_marker":
        role_label = content  # Use content as label for reset markers
    elif role == "analysis":
        role_label = "Analyzer Output"

    # Shard tag
    shard_tag = ""
    if msg.get("shard_ids"):
        shard_strs = [f"Shard {s}" for s in msg["shard_ids"]]
        shard_tag = " · ".join(shard_strs)

    # Visibility tag
    vis_tag = ""
    if not visible:
        vis_tag = " (hidden — pre-reset)"

    # Build header
    header = f"{icon} **{role_label}**"
    if shard_tag:
        header += f" &nbsp;`{shard_tag}`"
    if vis_tag:
        header += f" &nbsp;*{vis_tag}*"

    # Timestamp
    ts = msg.get("timestamp", "")
    if ts:
        header += f" &nbsp;—&nbsp; *{ts}*"

    if role == "reset_marker":
        st.divider()
        st.markdown(
            f"""<div style="text-align:center; padding:8px; background:#dc354520;
            border:1px solid #dc3545; border-radius:8px; margin:8px 0;">
            <strong>🔄 {content}</strong>
            </div>""",
            unsafe_allow_html=True,
        )
        st.divider()
        return

    # Render card
    with st.container():
        st.markdown(
            f"""<div style="border-left:4px solid {color}; padding:4px 0 0 12px;
            opacity:{opacity}; margin-bottom:4px;">
            <span style="font-size:0.9em;">{header}</span>
            </div>""",
            unsafe_allow_html=True,
        )

        # Content
        if role == "system":
            with st.expander("System Prompt", expanded=False):
                st.markdown(content)
        elif role == "analysis":
            with st.expander("Analyzer Output", expanded=True):
                st.code(content, language=None)
        elif role == "compacted conversation":
            with st.expander("Compacted Conversation", expanded=True):
                st.code(content, language=None)
        else:
            st.markdown(content)

        # Post-turn logs (for assistant messages)
        if msg.get("post_turn_logs"):
            with st.expander("Post-turn Processing", expanded=False):
                for log_entry in msg["post_turn_logs"]:
                    lt = log_entry["log_type"]
                    data = log_entry["data"]
                    if lt == "verification":
                        resp_type = data.get("response_type", "unknown")
                        label = RESPONSE_TYPE_LABELS.get(resp_type, resp_type)
                        is_answer = data.get("is_answer_attempt", False)
                        st.markdown(
                            f"**Turn Category:** {label}"
                            + (" ✅" if is_answer else "")
                        )
                    elif lt == "answer_evaluation":
                        extracted = data.get("extracted_answer", "N/A")
                        is_correct = data.get("is_correct", False)
                        score = data.get("score", 0)
                        icon_eval = "✅" if is_correct else "❌"
                        st.markdown(
                            f"**Extracted Answer:** `{extracted}`\n\n"
                            f"**Evaluation:** {icon_eval} "
                            f"{'Correct' if is_correct else 'Incorrect'} "
                            f"(score: {score})"
                        )
                    elif lt == "conversation_analysis":
                        st.markdown("**Conversation Analysis:**")
                        if data.get("user_intent"):
                            st.markdown("*User Intent:*")
                            st.code(data["user_intent"], language=None)
                        if data.get("aligned"):
                            st.markdown("*Aligned:*")
                            st.code(data["aligned"], language=None)
                        if data.get("issues"):
                            st.markdown("*Issues:*")
                            st.code(data["issues"], language=None)
                        needs = data.get("needs_edit")
                        if needs is not None:
                            st.markdown(
                                f"**Needs Edit:** {'Yes' if needs else 'No'}"
                            )
                    elif lt == "edit_decision":
                        should = data.get("should_edit", False)
                        st.markdown(
                            f"**Edit Decision:** {'✏️ Edit' if should else '➡️ Pass'}"
                        )

        # Injection indicators
        if msg.get("injections"):
            for inj in msg["injections"]:
                if inj["type"] == "memory_injected":
                    target = inj["data"].get("target", "?")
                    st.caption(f"💾 Memory injected (target: {target})")
                elif inj["type"] == "analysis_addendum_added":
                    st.caption("📝 Analysis addendum added to system prompt")

        st.markdown("---")


# ---------------------------------------------------------------------------
# Tab renderers
# ---------------------------------------------------------------------------


def render_question_tab(
    trace_file: dict,
    sample: Optional[dict],
    config: Optional[dict],
):
    """Tab 1: Question Information."""
    st.subheader("System Prompt")
    # Get system prompt from trace messages
    messages = trace_file.get("trace", {}).get("messages", [])
    system_msgs = [m for m in messages if m.get("role") == "system" and m.get("visible", True)]
    if system_msgs:
        st.code(system_msgs[0]["content"], language=None)
    else:
        st.info("No system prompt found.")

    st.subheader("Full Specification Question")
    if sample and sample.get("full_spec_q"):
        st.markdown(sample["full_spec_q"])
    elif sample and sample.get("question"):
        st.markdown(sample["question"])
    else:
        # Try metadata from results
        meta = trace_file.get("metadata", {})
        if isinstance(meta, dict) and meta.get("full_spec_q"):
            st.markdown(meta["full_spec_q"])
        else:
            st.info("Full spec question not available.")

    st.subheader("Ground Truth Answer")
    if sample and sample.get("ground_truth_a"):
        st.code(sample["ground_truth_a"], language=None)
    elif sample and sample.get("answer"):
        st.code(sample["answer"], language=None)
    else:
        meta = trace_file.get("metadata", {})
        if isinstance(meta, dict) and meta.get("ground_truth_a"):
            st.code(meta["ground_truth_a"], language=None)
        else:
            st.info("Ground truth answer not available.")

    st.subheader("Shards")
    if sample and sample.get("shards"):
        for shard in sample["shards"]:
            sid = shard.get("shard_id", "?")
            text = shard.get("shard", "")
            st.markdown(f"**Shard {sid}:** {text}")
    else:
        st.info("Shard data not available (sample data file not loaded).")


def render_conversation_info_tab(
    trace_file: dict,
    result: Optional[dict],
    config: Optional[dict],
):
    """Tab 2: Conversation Information."""
    sample_id = trace_file.get("sample_id", "N/A")

    col1, col2 = st.columns([3, 1])
    with col1:
        st.code(sample_id, language=None)
    with col2:
        # Copy button via st.button (clipboard API not directly available, show code)
        if st.button("📋 Copy Sample ID", key="copy_sample_id"):
            st.toast(f"Sample ID: {sample_id}")

    st.markdown(f"**Task:** {trace_file.get('task_name', 'N/A')}")
    st.markdown(f"**Experiment:** {trace_file.get('experiment_type', 'N/A')}")
    st.markdown(
        f"**Correct:** {'✅' if trace_file.get('is_correct') else '❌'} "
        f"(score: {trace_file.get('score', 'N/A')})"
    )

    trace = trace_file.get("trace", {})
    messages = trace.get("messages", [])
    num_resets = trace.get("num_resets", 0)

    # Count turns
    user_turns = sum(1 for m in messages if m.get("role") == "user")
    asst_turns = sum(1 for m in messages if m.get("role") == "assistant")
    visible_user = sum(
        1 for m in messages if m.get("role") == "user" and m.get("visible", True)
    )
    visible_asst = sum(
        1 for m in messages if m.get("role") == "assistant" and m.get("visible", True)
    )

    st.markdown(f"**Total User Turns:** {user_turns} (visible: {visible_user})")
    st.markdown(f"**Total Assistant Turns:** {asst_turns} (visible: {visible_asst})")
    st.markdown(f"**Context Resets:** {num_resets}")

    st.markdown(f"**Timestamp:** {trace_file.get('timestamp', 'N/A')}")

    # Models
    models = trace_file.get("models", {})
    if models:
        st.subheader("Models")
        for role, model in models.items():
            st.markdown(f"**{role.title()}:** {model}")

    # Cost / usage
    if result and result.get("usage_stats"):
        st.subheader("Usage Stats")
        stats = result["usage_stats"]
        total_cost = stats.get("total_cost_usd") or result.get("total_cost_usd", 0)
        st.markdown(f"**Total Cost:** ${total_cost:.4f}")

        for role_name in ["user", "assistant", "system", "ctx_editor"]:
            role_stats = stats.get(role_name, {})
            if role_stats and role_stats.get("num_requests", 0) > 0:
                with st.expander(f"{role_name.title()} Usage"):
                    st.markdown(f"- Requests: {role_stats.get('num_requests', 0)}")
                    st.markdown(
                        f"- Input tokens: {role_stats.get('input_tokens', 0):,}"
                    )
                    st.markdown(
                        f"- Output tokens: {role_stats.get('output_tokens', 0):,}"
                    )
                    if role_stats.get("reasoning_tokens"):
                        st.markdown(
                            f"- Reasoning tokens: {role_stats['reasoning_tokens']:,}"
                        )
                    if role_stats.get("cached_tokens"):
                        st.markdown(
                            f"- Cached tokens: {role_stats['cached_tokens']:,}"
                        )
                    st.markdown(f"- Cost: ${role_stats.get('cost_usd', 0):.4f}")

    # Replay provenance
    provenance = trace.get("provenance")
    if provenance:
        st.subheader("Replay Provenance")
        st.json(provenance)


def render_conversation_tab(trace_file: dict):
    """Tab 3: Conversation Viewer."""
    trace = trace_file.get("trace", {})
    display_messages = build_display_messages(trace)

    if not display_messages:
        st.info("No messages to display.")
        return

    for idx, msg in enumerate(display_messages):
        render_message_card(msg, idx)


def render_memory_tab(
    trace_file: dict,
    result: Optional[dict],
    config: Optional[dict],
):
    """Tab 4: Memory."""
    trace = trace_file.get("trace", {})
    logs = trace.get("logs", [])
    exp_type = trace_file.get("experiment_type", "")

    # Check if memory was used
    memory_logs = [l for l in logs if l.get("type") == "memory_injected"]

    has_memory = bool(memory_logs) or "memory" in exp_type.lower()

    if not has_memory:
        st.info("No memory was used in this run.")
        return

    # Show memory injection info
    if memory_logs:
        st.subheader("Memory Injection Events")
        for ml in memory_logs:
            target = ml["data"].get("target", "unknown")
            ts = ml.get("timestamp", "")

            if target in ("assistant", "system"):
                injection_loc = "System prompt (prepended to assistant's system message)"
            elif target == "analyzer":
                injection_loc = "Comparison prompt (injected into analyzer's context)"
            else:
                injection_loc = f"Unknown target: {target}"

            st.markdown(f"**Target component:** `{target}`")
            st.markdown(f"**Injection location:** {injection_loc}")
            if ts:
                st.markdown(f"**Timestamp:** {ts}")
            st.divider()

    # Try to find memory content in the system message or config
    if config and config.get("experiment", {}).get("strategy", {}).get("use_memory"):
        st.subheader("Memory Configuration")
        strategy_cfg = config["experiment"]["strategy"]
        st.markdown(
            f"**Memory target:** `{strategy_cfg.get('memory_target', 'N/A')}`"
        )

    # Look for cheatsheet content in messages
    messages = trace.get("messages", [])
    for msg in messages:
        content = msg.get("content", "")
        if "<cheatsheet>" in content:
            start = content.find("<cheatsheet>")
            end = content.find("</cheatsheet>")
            if start != -1 and end != -1:
                cheatsheet_content = content[
                    start + len("<cheatsheet>") : end
                ].strip()
                st.subheader("Cheatsheet Content")
                st.code(cheatsheet_content, language=None)
                break


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------


def main():
    st.set_page_config(
        page_title="Context Editor Viewer v2",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # -----------------------------------------------------------------------
    # Sidebar
    # -----------------------------------------------------------------------
    with st.sidebar:
        st.title("Context Editor Viewer")

        # --- Run selector ---
        st.subheader("Run Directory")
        run_input = st.text_area(
            "Paste run directories (one per line) or YAML mapping (label: path):",
            height=120,
            placeholder=(
                "2026-03-13/20-46-51\n"
                "2026-03-11/03-47-52\n\n"
                "Or YAML:\n"
                "baseline: 2026-03-11/03-47-52\n"
                "v3_mem: 2026-03-13/20-46-51"
            ),
            key="run_input",
        )

        runs = parse_run_input(run_input)

        if not runs:
            st.warning("Enter at least one run directory above.")
            st.stop()

        # Resolve paths
        for r in runs:
            r["resolved"] = resolve_path(r["path"])

        # Run selector
        run_options = {r["label"]: r for r in runs}
        selected_label = st.selectbox(
            "Select Run",
            options=list(run_options.keys()),
            key="selected_run",
        )
        selected_run = run_options[selected_label]
        run_dir = selected_run["resolved"]

        # Copy button for current run dir
        st.code(run_dir, language=None)

        if not os.path.isdir(run_dir):
            st.error(f"Directory not found: {run_dir}")
            st.stop()

        # Load trace index
        trace_index = list_trace_files(run_dir)
        if not trace_index:
            st.error(f"No traces found in {run_dir}/traces/")
            st.stop()

        # Load results.json for metadata
        results_list = load_results_json(run_dir)
        config = load_config(run_dir)

        # --- Task filter ---
        tasks = sorted(set(t["task"] for t in trace_index))
        if len(tasks) > 1:
            selected_task = st.selectbox("Filter by Task", ["All"] + tasks)
        else:
            selected_task = tasks[0]
            st.markdown(f"**Task:** {selected_task}")

        if selected_task != "All":
            trace_index = [t for t in trace_index if t["task"] == selected_task]

        # --- Correctness filter ---
        filter_mode = st.radio(
            "Filter by Result",
            ["All", "Correct", "Incorrect"],
            horizontal=True,
            key="filter_mode",
        )

        if filter_mode != "All":
            filtered = []
            for t in trace_index:
                data = load_trace(t["path"])
                is_correct = data.get("is_correct", False)
                if filter_mode == "Correct" and is_correct:
                    filtered.append(t)
                elif filter_mode == "Incorrect" and not is_correct:
                    filtered.append(t)
            trace_index = filtered

        if not trace_index:
            st.warning("No samples match the current filters.")
            st.stop()

        # --- Sample selector ---
        st.subheader("Sample Selector")

        # Build display labels
        sample_labels = []
        for i, t in enumerate(trace_index):
            # Quick peek at correctness
            data = load_trace(t["path"])
            correct = data.get("is_correct", False)
            icon = "✅" if correct else "❌"
            label = f"{icon} {t['sample_id']}"
            sample_labels.append(label)

        # Session state for navigation
        if "sample_idx" not in st.session_state:
            st.session_state.sample_idx = 0

        # Clamp
        st.session_state.sample_idx = max(
            0, min(st.session_state.sample_idx, len(trace_index) - 1)
        )

        # Prev / Next buttons
        col_prev, col_next, col_count = st.columns([1, 1, 1])
        with col_prev:
            if st.button("◀ Prev", disabled=st.session_state.sample_idx == 0):
                st.session_state.sample_idx -= 1
                st.rerun()
        with col_next:
            if st.button(
                "Next ▶",
                disabled=st.session_state.sample_idx >= len(trace_index) - 1,
            ):
                st.session_state.sample_idx += 1
                st.rerun()
        with col_count:
            st.markdown(
                f"**{st.session_state.sample_idx + 1}** / {len(trace_index)}"
            )

        # Selectbox (synced with session state)
        selected_sample_label = st.selectbox(
            "Sample",
            options=sample_labels,
            index=st.session_state.sample_idx,
            key="sample_select",
        )

        # Sync selectbox back to session state
        new_idx = sample_labels.index(selected_sample_label)
        if new_idx != st.session_state.sample_idx:
            st.session_state.sample_idx = new_idx
            st.rerun()

        selected_trace_info = trace_index[st.session_state.sample_idx]

    # -----------------------------------------------------------------------
    # Main area
    # -----------------------------------------------------------------------

    # Load trace data
    trace_file = load_trace(selected_trace_info["path"])
    result = find_result_for_sample(results_list, trace_file.get("sample_id", ""))

    # Try to load sample data for shards/full_spec_q
    sample = None
    if config:
        data_file = config.get("task", {}).get("data_file", "")
        if data_file:
            sample_id = trace_file.get("sample_id", "")
            sample = load_sample_data(data_file, sample_id)

    # Also try getting metadata from result
    if result and not sample:
        # Build a pseudo-sample from result metadata
        meta = result.get("metadata", {})
        if meta:
            sample = {
                "full_spec_q": meta.get("full_spec_q", ""),
                "ground_truth_a": meta.get("ground_truth_a", ""),
            }

    # Title
    sample_id = trace_file.get("sample_id", "N/A")
    is_correct = trace_file.get("is_correct", False)
    st.title(
        f"{'✅' if is_correct else '❌'} {sample_id}"
    )

    # Check if memory tab should be shown
    trace = trace_file.get("trace", {})
    exp_type = trace_file.get("experiment_type", "")
    has_memory = any(
        l.get("type") == "memory_injected" for l in trace.get("logs", [])
    ) or "memory" in exp_type.lower()

    # Tabs
    tab_names = ["Question Info", "Conversation Info", "Conversation"]
    if has_memory:
        tab_names.append("Memory")

    tabs = st.tabs(tab_names)

    with tabs[0]:
        render_question_tab(trace_file, sample, config)

    with tabs[1]:
        render_conversation_info_tab(trace_file, result, config)

    with tabs[2]:
        render_conversation_tab(trace_file)

    if has_memory and len(tabs) > 3:
        with tabs[3]:
            render_memory_tab(trace_file, result, config)


if __name__ == "__main__":
    main()
