"""Streamlit conversation viewer for ctx_editor experiments.

Supports viewing conversations from different context editing strategies,
showing edit decisions and context modifications.

Usage:
    # Browse all experiments in outputs/
    streamlit run src/ctx_editor/app_conv_viewer.py

    # Load a specific run directory
    streamlit run src/ctx_editor/app_conv_viewer.py -- --run outputs/2026-01-29/09-00-12

    # Or via query params: http://localhost:8501?run=outputs/2026-01-29/09-00-12
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import streamlit as st
import yaml


def load_results_file(file_path: str) -> list[dict]:
    """Load results from a JSON file (array format)."""
    with open(file_path, "r") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    return [data]


def load_trace_file(file_path: str) -> dict:
    """Load a single trace file."""
    with open(file_path, "r") as f:
        return json.load(f)


def find_trace_file(run_dir: str, sample: dict, experiment_type: str) -> str | None:
    """Find the trace file for a sample.

    Trace files are stored at: {run_dir}/traces/{task_name}/{experiment_type}/{sample_id}.json

    Args:
        run_dir: Path to the run directory
        sample: Sample dict with sample_id and task_name
        experiment_type: The experiment type (e.g., "baseline", "context_edit")

    Returns:
        Path to trace file if found, None otherwise.
    """
    task_name = sample.get("task_name", "unknown")
    sample_id = sample.get("sample_id", "unknown")

    # Sanitize sample_id for filename (same logic as logging.py)
    safe_id = sample_id.replace("/", "_").replace("\\", "_")

    trace_path = Path(run_dir) / "traces" / task_name / experiment_type / f"{safe_id}.json"

    if trace_path.exists():
        return str(trace_path)

    return None


def load_sample_with_trace(run_dir: str, sample: dict, experiment_type: str) -> dict:
    """Load a sample and merge in its trace data from the individual trace file.

    Args:
        run_dir: Path to the run directory
        sample: Sample dict from results.json (may not have trace)
        experiment_type: The experiment type

    Returns:
        Sample dict with trace data merged in.
    """
    # If sample already has trace data, return as-is
    if sample.get("trace"):
        return sample

    # Find and load the trace file
    trace_path = find_trace_file(run_dir, sample, experiment_type)
    if not trace_path:
        return sample

    try:
        trace_data = load_trace_file(trace_path)
        # Merge trace into sample
        merged = dict(sample)
        merged["trace"] = trace_data.get("trace", {})
        # Also merge models info if present in trace file
        if "models" in trace_data and "models" not in merged:
            merged["models"] = trace_data["models"]
        return merged
    except Exception:
        return sample


def load_config_file(run_dir: str) -> Optional[dict]:
    """Load the config.yaml from a run directory.

    Tries multiple locations:
    1. {run_dir}/config.yaml (copied config)
    2. {run_dir}/.hydra/config.yaml (hydra output)
    """
    # Try direct config.yaml first
    config_path = os.path.join(run_dir, "config.yaml")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return yaml.safe_load(f)

    # Try .hydra subdirectory
    hydra_config_path = os.path.join(run_dir, ".hydra", "config.yaml")
    if os.path.exists(hydra_config_path):
        with open(hydra_config_path, "r") as f:
            return yaml.safe_load(f)

    return None


@st.cache_data
def load_data_file_indexed(data_file_path: str) -> dict[str, dict]:
    """Load a data file and index it by task_id.

    Returns:
        Dict mapping task_id to the full sample data (with full_spec_q, ground_truth_a, etc.)
    """
    if not os.path.exists(data_file_path):
        return {}

    with open(data_file_path, "r") as f:
        data = json.load(f)

    if not isinstance(data, list):
        data = [data]

    # Index by task_id
    indexed = {}
    for item in data:
        task_id = item.get("task_id")
        if task_id:
            indexed[task_id] = item

    return indexed


def get_original_problem_spec(
    run_dir: str, task_id: str
) -> tuple[Optional[str], Optional[str]]:
    """Get the original problem specification for a given task_id.

    Args:
        run_dir: Path to the run directory containing config.yaml
        task_id: The task_id to look up

    Returns:
        Tuple of (full_spec_q, ground_truth_a), either can be None if not found
    """
    # Load config to get data_file path
    config = load_config_file(run_dir)
    if not config:
        return None, None

    # Get data file path from config
    data_file = config.get("task", {}).get("data_file")
    if not data_file:
        return None, None

    # Resolve data file path relative to project root
    # The data_file in config is relative to project root (e.g., "data/lic_eval_subset.json")
    # We need to find the project root from run_dir
    # run_dir is like: outputs/baseline_gpt-5-mini_all/2026-01-29_08-03-51
    # Project root is 3 levels up from the new-style paths, but could vary

    # Try to resolve from current working directory first
    if os.path.exists(data_file):
        data_file_path = data_file
    else:
        # Try relative to the script location
        script_dir = Path(__file__).parent.parent.parent
        data_file_path = str(script_dir / data_file)

        if not os.path.exists(data_file_path):
            # Try relative to run_dir by going up directories
            run_path = Path(run_dir)
            for i in range(1, 5):  # Try up to 4 levels up
                candidate = run_path.parents[i] / data_file if i < len(run_path.parents) else None
                if candidate and candidate.exists():
                    data_file_path = str(candidate)
                    break

    # Load and index the data file
    indexed_data = load_data_file_indexed(data_file_path)

    # Look up the task
    task_data = indexed_data.get(task_id, {})

    return task_data.get("full_spec_q"), task_data.get("ground_truth_a")


def load_ledger(base_path: str = "outputs") -> list[dict]:
    """Load the runs ledger if it exists.

    Returns:
        List of run entries from the ledger, or empty list if not found.
    """
    ledger_path = Path(base_path) / "runs.yaml"
    if not ledger_path.exists():
        return []

    with open(ledger_path) as f:
        data = yaml.safe_load(f)
        return data.get("runs", []) if data else []


def find_output_dirs(base_path: str = "outputs") -> list[dict]:
    """Find all output directories using ledger or directory scan.

    Returns:
        List of run info dicts with keys: path, strategy, model, task, accuracy, etc.
    """
    base = Path(base_path)

    if not base.exists():
        return []

    # Try loading from ledger first
    runs = load_ledger(base_path)
    if runs:
        # Add full_path to each run and filter to those that exist
        valid_runs = []
        for run in runs:
            full_path = base / run["path"]
            if full_path.exists() and (full_path / "results.json").exists():
                run["full_path"] = str(full_path)
                valid_runs.append(run)
        return valid_runs

    # Fallback: scan directory structure (new format: {date}/{time})
    runs = []
    for date_dir in base.iterdir():
        if not date_dir.is_dir() or date_dir.name.startswith("."):
            continue

        # Check if it's a date directory (YYYY-MM-DD)
        import re
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_dir.name):
            continue

        for time_dir in date_dir.iterdir():
            if time_dir.is_dir():
                results_file = time_dir / "results.json"
                config_file = time_dir / "config.yaml"

                if results_file.exists():
                    run_info = {
                        "path": f"{date_dir.name}/{time_dir.name}",
                        "full_path": str(time_dir),
                        "strategy": "unknown",
                        "model": "unknown",
                        "task": "unknown",
                    }

                    # Try to extract info from config
                    if config_file.exists():
                        config = load_config_file(str(time_dir))
                        if config:
                            run_info["strategy"] = config.get("experiment", {}).get("name", "unknown")
                            run_info["model"] = config.get("model", {}).get("name", "unknown")
                            run_info["task"] = config.get("task", {}).get("name", "unknown")

                    runs.append(run_info)

    return runs


def get_experiment_type(sample: dict) -> str:
    """Extract experiment type from a sample."""
    # Try different locations
    if "experiment_type" in sample:
        return sample["experiment_type"]

    sample_id = sample.get("sample_id", "")
    if "context_edit" in sample_id:
        return "context_edit"
    elif "agentic_edit" in sample_id:
        return "agentic_edit"
    elif "reflection" in sample_id:
        return "reflection"
    elif "baseline" in sample_id:
        return "baseline"

    return "unknown"


def format_timestamp(timestamp_str: str) -> str:
    """Format a timestamp string for display."""
    if not timestamp_str:
        return ""
    try:
        dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%H:%M:%S")
    except ValueError:
        return timestamp_str


def get_messages_from_trace(trace: dict) -> list[dict]:
    """Extract messages from a trace dictionary."""
    if isinstance(trace, dict):
        return trace.get("messages", [])
    return []


def get_logs_from_trace(trace: dict) -> list[dict]:
    """Extract logs from a trace dictionary."""
    if isinstance(trace, dict):
        return trace.get("logs", [])
    return []


def get_history_from_trace(trace: dict) -> list[dict]:
    """Extract history snapshots from a trace (if present)."""
    if isinstance(trace, dict):
        return trace.get("history", [])
    return []


def get_log_at_timestamp(logs: list[dict], timestamp: str, log_type: str) -> Optional[dict]:
    """Find a log entry around a given timestamp of a specific type."""
    for log in logs:
        if log.get("type") == log_type:
            log_ts = log.get("timestamp", "")
            if log_ts and timestamp and log_ts[:16] == timestamp[:16]:  # Match to minute
                return log
    return None


def get_logs_before_message(logs: list[dict], msg_timestamp: str) -> list[dict]:
    """Get all logs that occurred just before a message timestamp."""
    if not msg_timestamp:
        return []

    relevant_logs = []
    for log in logs:
        log_ts = log.get("timestamp", "")
        if log_ts:
            # Include logs within 30 seconds before message
            try:
                log_dt = datetime.strptime(log_ts, "%Y-%m-%d %H:%M:%S")
                msg_dt = datetime.strptime(msg_timestamp, "%Y-%m-%d %H:%M:%S")
                diff = (msg_dt - log_dt).total_seconds()
                if 0 <= diff <= 30:
                    relevant_logs.append(log)
            except ValueError:
                continue

    return relevant_logs


def display_edit_decision(log: dict) -> None:
    """Display an edit decision log entry."""
    data = log.get("data", {})
    should_edit = data.get("should_edit", False)
    reasoning = data.get("reasoning", "")

    if should_edit:
        st.markdown(
            f"""<div style="background-color: #2d4a3e; padding: 10px; border-radius: 5px; margin: 5px 0; border-left: 4px solid #28a745;">
            <strong>Context Edit Decision:</strong> EDIT<br>
            <em>{reasoning}</em>
            </div>""",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""<div style="background-color: #3d3d3d; padding: 10px; border-radius: 5px; margin: 5px 0; border-left: 4px solid #6c757d;">
            <strong>Context Edit Decision:</strong> NO EDIT<br>
            <em>{reasoning}</em>
            </div>""",
            unsafe_allow_html=True,
        )


def display_shard_revealed(log: dict) -> None:
    """Display a shard revealed log entry."""
    data = log.get("data", {})
    shard_id = data.get("shard_id", "?")
    st.markdown(
        f"""<div style="background-color: #1a3a4a; padding: 5px 10px; border-radius: 5px; margin: 2px 0; font-size: 0.9em;">
        Shard revealed: <strong>#{shard_id}</strong>
        </div>""",
        unsafe_allow_html=True,
    )


def display_verification(log: dict) -> None:
    """Display a verification log entry."""
    data = log.get("data", {})
    response_type = data.get("response_type", "unknown")
    is_answer = data.get("is_answer_attempt", False)

    color = "#4a3d1a" if is_answer else "#2d2d4a"
    icon = "" if is_answer else ""

    st.markdown(
        f"""<div style="background-color: {color}; padding: 5px 10px; border-radius: 5px; margin: 2px 0; font-size: 0.9em;">
        {icon} Response classified as: <strong>{response_type}</strong>
        </div>""",
        unsafe_allow_html=True,
    )


def display_answer_evaluation(log: dict) -> None:
    """Display an answer evaluation log entry."""
    data = log.get("data", {})
    is_correct = data.get("is_correct", False)
    score = data.get("score", 0.0)
    extracted = data.get("extracted_answer", "")

    if is_correct:
        st.success(f"Answer: `{extracted}` - Correct (score: {score})")
    else:
        st.error(f"Answer: `{extracted}` - Incorrect (score: {score})")


def display_context_replaced(log: dict) -> None:
    """Display a context replaced log entry."""
    data = log.get("data", {})
    new_count = data.get("new_message_count", "?")

    st.markdown(
        f"""<div style="background-color: #4a2d4a; padding: 10px; border-radius: 5px; margin: 10px 0; border: 2px dashed #9c27b0;">
        <strong>CONTEXT REPLACED</strong><br>
        New message count: {new_count}<br>
        <em>The assistant now sees a condensed version of the conversation.</em>
        </div>""",
        unsafe_allow_html=True,
    )


def display_reflection_generated(log: dict) -> None:
    """Display a reflection generated log entry."""
    data = log.get("data", {})
    reflection = data.get("reflection", "")

    st.markdown(
        f"""<div style="background-color: #2d3a4a; padding: 10px; border-radius: 5px; margin: 10px 0; border-left: 4px solid #17a2b8;">
        <strong>Reflection Added to Context</strong><br>
        <em style="color: #a8d4e6;">{reflection}</em>
        </div>""",
        unsafe_allow_html=True,
    )


def display_context_edit_output(log: dict) -> None:
    """Display the context editor's output."""
    data = log.get("data", {})
    edited_context = data.get("edited_context", "")
    editor_model = data.get("editor_model", "unknown")
    original_turns = data.get("original_turn_count", "?")

    # Truncate for display but allow expansion
    preview_length = 500
    is_long = len(edited_context) > preview_length

    st.markdown(
        f"""<div style="background-color: #2d4a2d; padding: 10px; border-radius: 5px; margin: 10px 0; border-left: 4px solid #28a745;">
        <strong>Context Editor Output</strong> <span style="font-size: 0.85em; color: #888;">(model: {editor_model}, original turns: {original_turns})</span>
        </div>""",
        unsafe_allow_html=True,
    )

    with st.expander("View edited context sent to assistant", expanded=False):
        st.markdown(edited_context)


def display_context_edit_marker(turn_num: int) -> None:
    """Display a marker indicating context was edited (for context_edit strategy)."""
    st.markdown(
        f"""<div style="background-color: #3d2d4a; padding: 8px; border-radius: 5px; margin: 10px 0; border: 1px solid #9c27b0; text-align: center;">
        <strong style="color: #d4a8e6;">--- Context Edited (Turn {turn_num}) ---</strong><br>
        <span style="font-size: 0.85em; color: #b8a8c8;">The assistant sees a condensed summary instead of full history above</span>
        </div>""",
        unsafe_allow_html=True,
    )


def display_original_problem(full_spec_q: Optional[str], ground_truth_a: Optional[str]) -> None:
    """Display the original single-turn problem specification.

    This shows what the complete problem looks like before being sharded
    into a multi-turn conversation.
    """
    if not full_spec_q and not ground_truth_a:
        return

    st.markdown(
        """<div style="background-color: #1a2a3a; padding: 15px; border-radius: 8px; margin-bottom: 20px; border: 2px solid #3a5a7a;">
        <h4 style="color: #7ab3e0; margin-top: 0; margin-bottom: 10px;">Original Single-Turn Problem</h4>
        """,
        unsafe_allow_html=True,
    )

    if full_spec_q:
        st.markdown(
            f"""<div style="background-color: #0d1a26; padding: 12px; border-radius: 5px; margin-bottom: 10px;">
            <strong style="color: #5a9fd4;">Question:</strong><br>
            <span style="color: #e0e0e0;">{full_spec_q}</span>
            </div>""",
            unsafe_allow_html=True,
        )

    if ground_truth_a:
        # Truncate long answers for display
        display_answer = ground_truth_a
        if len(display_answer) > 500:
            with st.expander("Ground Truth Answer (click to expand)", expanded=False):
                st.markdown(
                    f"""<div style="background-color: #0d2618; padding: 12px; border-radius: 5px;">
                    <span style="color: #a8e6cf;">{ground_truth_a}</span>
                    </div>""",
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                f"""<div style="background-color: #0d2618; padding: 12px; border-radius: 5px;">
                <strong style="color: #5ad4a8;">Ground Truth Answer:</strong><br>
                <span style="color: #a8e6cf;">{display_answer}</span>
                </div>""",
                unsafe_allow_html=True,
            )

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown(
        """<p style="font-size: 0.85em; color: #888; text-align: center; margin-top: 5px;">
        The problem above was sharded into multiple turns in the conversation below
        </p>""",
        unsafe_allow_html=True,
    )


def display_log_entry(log: dict, show_verification: bool = True) -> None:
    """Display a log entry based on its type."""
    log_type = log.get("type", "unknown")

    if log_type == "edit_decision":
        display_edit_decision(log)
    elif log_type == "shard_revealed":
        display_shard_revealed(log)
    elif log_type == "verification":
        if show_verification:
            display_verification(log)
    elif log_type == "answer_evaluation":
        display_answer_evaluation(log)
    elif log_type == "context_replaced":
        display_context_replaced(log)
    elif log_type == "reflection_generated":
        display_reflection_generated(log)
    elif log_type == "context_edit_output":
        display_context_edit_output(log)


def display_message(msg: dict, logs: list[dict], show_logs: bool = True) -> None:
    """Display a single message with associated logs."""
    role = msg.get("role", "")
    content = msg.get("content", "")
    timestamp = msg.get("timestamp", "")

    # Get associated logs
    if show_logs:
        relevant_logs = get_logs_before_message(logs, timestamp)
        for log in relevant_logs:
            display_log_entry(log)

    # Display message
    if role == "user":
        with st.chat_message("user"):
            st.markdown(content)
            if timestamp:
                st.caption(f"_{format_timestamp(timestamp)}_")

    elif role == "assistant":
        with st.chat_message("assistant"):
            st.markdown(content)
            if timestamp:
                st.caption(f"_{format_timestamp(timestamp)}_")

    elif role == "system":
        # st.markdown(
        #     f"""<div style="background-color: #1e1e2e; padding: 10px; border-radius: 5px; margin: 5px 0; border-left: 4px solid #6c757d;">
        #     <strong>System:</strong> {content[:500]}{"..." if len(content) > 500 else ""}
        #     </div>""",
        #     unsafe_allow_html=True,
        # )
        st.markdown(
            f"""<div style="background-color: #1e1e2e; padding: 10px; border-radius: 5px; margin: 5px 0; border-left: 4px solid #6c757d;">
            <strong>System:</strong> {content}
            </div>""",
            unsafe_allow_html=True,
        )


def display_history_snapshot(snapshot: dict, index: int) -> None:
    """Display a history snapshot from context editing."""
    label = snapshot.get("label", f"Snapshot {index}")
    messages = snapshot.get("messages", [])

    with st.expander(f"History Snapshot: {label} ({len(messages)} messages)"):
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")[:500]  # Truncate for display
            if len(msg.get("content", "")) > 500:
                content += "..."

            if role == "user":
                st.markdown(f"**[user]** {content}")
            elif role == "assistant":
                st.markdown(f"**[assistant]** {content}")
            elif role == "system":
                st.markdown(f"**[system]** {content}")


def display_conversation(sample: dict, exp_type: str = "", run_dir: str = "") -> None:
    """Display a full conversation with all logs and context edits.

    Args:
        sample: The sample data containing trace, metadata, etc.
        exp_type: The experiment type (e.g., "context_edit", "baseline")
        run_dir: Path to the run directory (for loading original problem spec)
    """
    # Display original problem specification from data file
    task_id = sample.get("sample_id")
    if run_dir and task_id:
        full_spec_q, ground_truth_a = get_original_problem_spec(run_dir, task_id)
        display_original_problem(full_spec_q, ground_truth_a)

    trace = sample.get("trace", {})

    # Handle empty trace
    if not trace or (isinstance(trace, list) and len(trace) == 0):
        error_msg = sample.get("metadata", {}).get("error", "No trace data")
        st.warning(f"No conversation data. Error: {error_msg}")
        return

    messages = get_messages_from_trace(trace)
    logs = get_logs_from_trace(trace)
    history = get_history_from_trace(trace)

    # Determine if this is a context_edit experiment (always edits after turn 1)
    is_context_edit = "context_edit" in exp_type and "agentic" not in exp_type

    # Show history snapshots if present (indicates context editing occurred)
    if history:
        st.subheader("Context Edit History")
        st.info(f"This conversation has {len(history)} context snapshots from editing operations.")
        for i, snapshot in enumerate(history):
            display_history_snapshot(snapshot, i)
        st.divider()

    # Create a timeline of events (messages + logs)
    st.subheader("Conversation")

    # Show toggle for detailed logs
    show_verification = st.checkbox("Show verification logs", value=False)

    # Build a combined timeline of messages and logs
    timeline = []

    # Add messages to timeline
    for i, msg in enumerate(messages):
        msg_ts = msg.get("timestamp", "")
        timeline.append(
            {
                "type": "message",
                "timestamp": msg_ts,
                "data": msg,
                "index": i,
            }
        )

    # Add logs to timeline
    for i, log in enumerate(logs):
        log_ts = log.get("timestamp", "")
        timeline.append(
            {
                "type": "log",
                "timestamp": log_ts,
                "data": log,
                "index": i,
            }
        )

    # Sort by timestamp
    def parse_ts(item):
        ts = item.get("timestamp", "")
        if ts:
            try:
                return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass
        return datetime.min

    timeline.sort(key=parse_ts)

    # Track assistant turn count for context_edit markers
    assistant_turn_count = 0
    last_was_user = False

    for item in timeline:
        if item["type"] == "message":
            msg = item["data"]
            role = msg.get("role", "")

            # For context_edit strategy, show edit marker before assistant responses (after turn 1)
            if is_context_edit and role == "assistant" and assistant_turn_count > 0:
                display_context_edit_marker(assistant_turn_count + 1)

            display_message(msg, [], show_logs=False)

            if role == "assistant":
                assistant_turn_count += 1
            last_was_user = role == "user"

        elif item["type"] == "log":
            log = item["data"]
            display_log_entry(log, show_verification=show_verification)

    # Show reference answer and ground truth if available
    metadata = sample.get("metadata", {})
    ref_answer = metadata.get("reference_answer")
    ground_truth = metadata.get("ground_truth_a")
    full_spec = metadata.get("full_spec_q")

    if ref_answer or ground_truth or full_spec:
        st.divider()
        st.subheader("Reference Information")

        if full_spec:
            with st.expander("Full Problem Specification", expanded=False):
                st.markdown(full_spec)

        if ground_truth:
            st.success(f"**Ground Truth Answer:** {ground_truth}")
        elif ref_answer:
            st.info(f"**Reference Answer:** {ref_answer}")


def display_sidebar_info(sample: dict) -> None:
    """Display sample information in the sidebar."""
    st.sidebar.header("Conversation Info")

    st.sidebar.write(f"**Sample ID:** {sample.get('sample_id', 'N/A')}")
    st.sidebar.write(f"**Task:** {sample.get('task_name', 'N/A')}")

    # Result info
    is_correct = sample.get("is_correct", False)
    score = sample.get("score", 0.0)
    if is_correct:
        st.sidebar.success(f"Result: Correct (score: {score})")
    else:
        st.sidebar.error(f"Result: Incorrect (score: {score})")

    st.sidebar.write(f"**Turns:** {sample.get('num_turns', 0)}")
    st.sidebar.write(f"**Cost:** ${sample.get('total_cost_usd', 0):.6f}")

    # Model info
    models = sample.get("models", {})
    if models:
        st.sidebar.subheader("Models")
        for role, model in models.items():
            st.sidebar.write(f"- {role}: {model}")

    # Usage stats
    usage = sample.get("usage_stats", {})
    if usage:
        st.sidebar.subheader("Usage Stats")
        for role in ["user", "assistant", "system", "ctx_editor"]:
            role_stats = usage.get(role, {})
            if role_stats and role_stats.get("num_requests", 0) > 0:
                st.sidebar.write(f"**{role}:** {role_stats.get('num_requests', 0)} requests")
                st.sidebar.write(f"  - Input: {role_stats.get('input_tokens', 0)} tokens")
                st.sidebar.write(f"  - Output: {role_stats.get('output_tokens', 0)} tokens")

    # Extracted answer
    extracted = sample.get("extracted_answer")
    if extracted:
        st.sidebar.subheader("Extracted Answer")
        st.sidebar.code(extracted)


def get_statistics(samples: list[dict]) -> dict:
    """Compute statistics for a list of samples."""
    if not samples:
        return {"total": 0, "correct": 0, "rate": 0.0, "avg_turns": 0.0}

    total = len(samples)
    correct = sum(1 for s in samples if s.get("is_correct", False))
    avg_turns = sum(s.get("num_turns", 0) for s in samples) / total if total > 0 else 0

    return {
        "total": total,
        "correct": correct,
        "rate": (correct / total * 100) if total > 0 else 0.0,
        "avg_turns": avg_turns,
    }


def get_run_path_from_args() -> Optional[str]:
    """Get run path from command line arguments."""
    # Parse args after -- separator (streamlit passes args this way)
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=str, help="Path to a specific run directory")
    parser.add_argument("--outputs", type=str, default="outputs", help="Base outputs directory")

    # Find args after -- in sys.argv
    try:
        separator_idx = sys.argv.index("--")
        args = parser.parse_args(sys.argv[separator_idx + 1 :])
        return args.run
    except (ValueError, SystemExit):
        return None


def main():
    st.set_page_config(
        page_title="Context Editor Conversation Viewer",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("Context Editor Conversation Viewer")

    # Check for run path from multiple sources
    run_from_args = get_run_path_from_args()
    run_from_query = st.query_params.get("run")

    # Sidebar: Directory selection
    st.sidebar.header("Data Source")

    # Determine base path for browsing
    base_path = "outputs"
    if not os.path.exists(base_path):
        script_dir = Path(__file__).parent.parent.parent.parent
        base_path = str(script_dir / "outputs")

    # Option to enter custom path
    custom_path = st.sidebar.text_input(
        "Custom run path",
        value=run_from_args or run_from_query or "",
        placeholder="e.g., outputs/2026-01-29/09-00-12",
        help="Enter a path to a specific run directory, or leave empty to browse",
    )

    # Determine selected run
    selected_run = None
    selected_exp = None

    if custom_path and custom_path.strip():
        # Use custom path directly
        custom_path = custom_path.strip()
        if os.path.exists(custom_path):
            selected_run = custom_path
            # Try to get experiment type from config
            config = load_config_file(custom_path)
            selected_exp = config.get("experiment", {}).get("name", "unknown") if config else "unknown"
            st.sidebar.success(f"Loaded: {os.path.basename(custom_path)}")
        else:
            st.sidebar.error(f"Path not found: {custom_path}")
            return
    else:
        # Browse mode
        st.sidebar.divider()
        st.sidebar.header("Browse Experiments")

        all_runs = find_output_dirs(base_path)

        if not all_runs:
            st.error(f"No experiment outputs found in {base_path}")
            st.info("Run some experiments first with: `ctx-editor`")
            st.info("Or enter a custom path in the sidebar.")
            return

        # Get unique values for filters
        strategies = sorted(set(r.get("strategy", "unknown") for r in all_runs))
        models = sorted(set(r.get("model", "unknown") for r in all_runs))
        tasks = sorted(set(r.get("task", "unknown") for r in all_runs))

        # Filter controls
        selected_strategy = st.sidebar.selectbox("Strategy", ["All"] + strategies)
        selected_model = st.sidebar.selectbox("Model", ["All"] + models)
        selected_task_filter = st.sidebar.selectbox("Task", ["All"] + tasks)

        # Apply filters
        filtered_runs = all_runs
        if selected_strategy != "All":
            filtered_runs = [r for r in filtered_runs if r.get("strategy") == selected_strategy]
        if selected_model != "All":
            filtered_runs = [r for r in filtered_runs if r.get("model") == selected_model]
        if selected_task_filter != "All":
            filtered_runs = [r for r in filtered_runs if r.get("task") == selected_task_filter]

        if not filtered_runs:
            st.warning("No runs match the selected filters.")
            return

        # Sort by path (which includes date/time) descending for most recent first
        filtered_runs = sorted(filtered_runs, key=lambda r: r.get("path", ""), reverse=True)

        # Create run labels with key info
        def make_run_label(r: dict) -> str:
            path = r.get("path", "unknown")
            strategy = r.get("strategy", "?")
            acc = r.get("accuracy")
            acc_str = f" ({acc:.0%})" if acc is not None else ""
            return f"{path} [{strategy}]{acc_str}"

        selected_run_idx = st.sidebar.selectbox(
            "Run",
            range(len(filtered_runs)),
            format_func=lambda i: make_run_label(filtered_runs[i]),
        )

        selected_run_info = filtered_runs[selected_run_idx]
        selected_run = selected_run_info.get("full_path", "")
        selected_exp = selected_run_info.get("strategy", "unknown")

    # Load results
    results_path = os.path.join(selected_run, "results.json")
    if not os.path.exists(results_path):
        st.error(f"Results file not found: {results_path}")
        return

    try:
        samples = load_results_file(results_path)
    except Exception as e:
        st.error(f"Error loading results: {e}")
        return

    if not samples:
        st.warning("No samples found in results file.")
        return

    # Filter options
    st.sidebar.divider()
    st.sidebar.header("Filters")

    # Filter by task
    tasks = sorted(set(s.get("task_name", "unknown") for s in samples))
    selected_tasks = st.sidebar.multiselect("Tasks", tasks, default=tasks)

    # Filter by correctness
    filter_option = st.sidebar.radio(
        "Show",
        ["All", "Correct only", "Incorrect only"],
    )

    # Apply filters
    filtered_samples = [s for s in samples if s.get("task_name", "unknown") in selected_tasks]

    if filter_option == "Correct only":
        filtered_samples = [s for s in filtered_samples if s.get("is_correct", False)]
    elif filter_option == "Incorrect only":
        filtered_samples = [s for s in filtered_samples if not s.get("is_correct", False)]

    # Statistics
    st.sidebar.divider()
    st.sidebar.header("Statistics")
    stats = get_statistics(filtered_samples)
    st.sidebar.metric("Total Samples", stats["total"])
    st.sidebar.metric("Correct", f"{stats['correct']} ({stats['rate']:.1f}%)")
    st.sidebar.metric("Avg Turns", f"{stats['avg_turns']:.1f}")

    # Sample selection
    st.sidebar.divider()
    st.sidebar.header("Sample Selection")

    # Group by task
    grouped = defaultdict(list)
    for s in filtered_samples:
        grouped[s.get("task_name", "unknown")].append(s)

    # Select task then sample
    if len(grouped) > 1:
        selected_task = st.sidebar.selectbox("Task", sorted(grouped.keys()))
        task_samples = grouped[selected_task]
    else:
        task_samples = filtered_samples

    # Create sample labels
    sample_labels = []
    for s in task_samples:
        sample_id = s.get("sample_id", "unknown")
        is_correct = "+" if s.get("is_correct", False) else "-"
        turns = s.get("num_turns", 0)
        sample_labels.append(f"{is_correct} {sample_id} ({turns} turns)")

    if not sample_labels:
        st.warning("No samples match the current filters.")
        return

    selected_sample_idx = st.sidebar.selectbox(
        "Sample",
        range(len(task_samples)),
        format_func=lambda i: sample_labels[i],
    )

    selected_sample = task_samples[selected_sample_idx]

    # Show experiment type badge
    exp_type = get_experiment_type(selected_sample)

    # Determine effective experiment type from sample or directory name
    effective_exp_type = exp_type
    if effective_exp_type == "unknown" and selected_exp:
        effective_exp_type = selected_exp

    # Load full trace data (traces are stored in separate files)
    selected_sample_with_trace = load_sample_with_trace(
        selected_run, selected_sample, effective_exp_type
    )

    # Display sample info in sidebar
    display_sidebar_info(selected_sample_with_trace)

    # Main content: Display conversation
    sample_id = selected_sample_with_trace.get("sample_id", "unknown")
    st.header(f"Conversation: {sample_id}")

    if "context_edit" in effective_exp_type and "agentic" not in effective_exp_type:
        st.info(
            "**Strategy:** Context Edit - Conversation is compressed before each assistant turn"
        )
    elif "agentic_edit" in effective_exp_type:
        st.info("**Strategy:** Agentic Edit - Model decides when to compress context")
    elif "reflection" in effective_exp_type:
        st.info("**Strategy:** Reflection - Reflection prompts added to context")
    elif "baseline" in effective_exp_type:
        st.info("**Strategy:** Baseline - No context modifications")

    # Display the conversation
    display_conversation(selected_sample_with_trace, exp_type=effective_exp_type, run_dir=selected_run)


if __name__ == "__main__":
    main()
