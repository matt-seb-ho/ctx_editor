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
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import streamlit as st
import tiktoken
import yaml

# Regex to strip S1's embedded <conversation_analysis> blocks from user messages
_ANALYSIS_TAG_RE = re.compile(r"\n*<conversation_analysis>.*?</conversation_analysis>", re.DOTALL)

# Regex to extract <cheatsheet> content from system messages
_CHEATSHEET_RE = re.compile(r"<cheatsheet>(.*?)</cheatsheet>", re.DOTALL)


@st.cache_resource
def _get_tokenizer():
    return tiktoken.encoding_for_model("gpt-4o")


def count_tokens(text: str) -> int:
    return len(_get_tokenizer().encode(text))


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

        # Load error attribution if available
        ea_path = os.path.join(run_dir, "error_analysis.json")
        if os.path.exists(ea_path):
            try:
                ea_data = json.load(open(ea_path))
                ea_results = ea_data.get("results", [])
                sample_id = merged.get("sample_id", "")
                for ea in ea_results:
                    if ea.get("sample_id") == sample_id:
                        if "metadata" not in merged:
                            merged["metadata"] = {}
                        merged["metadata"]["error_attribution"] = ea
                        break
            except Exception:
                pass

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


def get_original_sample_data(run_dir: str, task_id: str) -> dict:
    """Get the full original sample data (including shards) for a given task_id.

    Args:
        run_dir: Path to the run directory containing config.yaml
        task_id: The task_id to look up

    Returns:
        Dict with full_spec_q, ground_truth_a, shards, etc. Empty dict if not found.
    """
    config = load_config_file(run_dir)
    if not config:
        return {}

    data_file = config.get("task", {}).get("data_file")
    if not data_file:
        return {}

    # Resolve data file path
    if os.path.exists(data_file):
        data_file_path = data_file
    else:
        script_dir = Path(__file__).parent.parent.parent
        data_file_path = str(script_dir / data_file)
        if not os.path.exists(data_file_path):
            run_path = Path(run_dir)
            for i in range(1, 5):
                candidate = run_path.parents[i] / data_file if i < len(run_path.parents) else None
                if candidate and candidate.exists():
                    data_file_path = str(candidate)
                    break

    indexed_data = load_data_file_indexed(data_file_path)
    return indexed_data.get(task_id, {})


def get_original_problem_spec(run_dir: str, task_id: str) -> tuple[Optional[str], Optional[str]]:
    """Get the original problem specification for a given task_id.

    Args:
        run_dir: Path to the run directory containing config.yaml
        task_id: The task_id to look up

    Returns:
        Tuple of (full_spec_q, ground_truth_a), either can be None if not found
    """
    task_data = get_original_sample_data(run_dir, task_id)
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

        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_dir.name):
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
                            run_info["strategy"] = config.get("experiment", {}).get(
                                "name", "unknown"
                            )
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


def build_shard_index(shards: list[dict]) -> dict[int, str]:
    """Build a mapping from shard_id to shard text."""
    return {s["shard_id"]: s["shard"] for s in shards}


def build_turn_shard_map(logs: list[dict]) -> dict[int, int]:
    """Build a mapping from user turn number (1-indexed) to shard_id revealed.

    Counts shard_revealed events in order — the Nth shard_revealed corresponds
    to the Nth user turn.
    """
    turn_map: dict[int, int] = {}
    turn_num = 0
    for log in logs:
        if log.get("type") == "shard_revealed":
            turn_num += 1
            turn_map[turn_num] = log["data"]["shard_id"]
    return turn_map


def display_shard_comparison(user_content: str, shard_text: str, shard_id: int) -> None:
    """Display side-by-side comparison of actual shard vs user simulator phrasing."""
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            f'<div style="background-color: #1a2a3a; padding: 10px; border-radius: 5px; '
            f'border-left: 4px solid #5a9fd4;">'
            f'<strong style="color: #7ab3e0;">Actual Shard #{shard_id}</strong><br>'
            f'<span style="color: #e0e0e0;">{shard_text}</span>'
            f"</div>",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f'<div style="background-color: #2a1a3a; padding: 10px; border-radius: 5px; '
            f'border-left: 4px solid #9c5ad4;">'
            f'<strong style="color: #c4a8e6;">User Simulator Phrasing</strong><br>'
            f'<span style="color: #e0e0e0;">{user_content}</span>'
            f"</div>",
            unsafe_allow_html=True,
        )


def display_shard_summary(full_spec_q: Optional[str], shards: list[dict]) -> None:
    """Display the full spec question and all shards as bullet points."""
    st.divider()
    st.subheader("Shard Breakdown")

    if full_spec_q:
        st.markdown(
            f'<div style="background-color: #1a2a3a; padding: 12px; border-radius: 5px; '
            f'margin-bottom: 15px; border: 1px solid #3a5a7a;">'
            f'<strong style="color: #7ab3e0;">Full Spec Question</strong><br><br>'
            f'<span style="color: #e0e0e0;">{full_spec_q}</span>'
            f"</div>",
            unsafe_allow_html=True,
        )

    if shards:
        shard_bullets = "".join(
            f'<li style="margin-bottom: 6px;">'
            f'<strong style="color: #7ab3e0;">Shard #{s["shard_id"]}:</strong> '
            f'<span style="color: #e0e0e0;">{s["shard"]}</span></li>'
            for s in shards
        )
        st.markdown(
            f'<div style="background-color: #1a2a2a; padding: 12px; border-radius: 5px; '
            f'border: 1px solid #3a5a5a;">'
            f'<strong style="color: #5ad4a8;">All Shards</strong>'
            f'<ul style="margin-top: 8px; margin-bottom: 0;">{shard_bullets}</ul>'
            f"</div>",
            unsafe_allow_html=True,
        )


def display_edit_decision(log: dict) -> None:
    """Display an edit decision log entry."""
    data = log.get("data", {})
    should_edit = data.get("should_edit", False)
    reasoning = data.get("reasoning", "")

    if should_edit:
        st.markdown(
            f'<div style="background-color: #2d4a3e; padding: 10px; border-radius: 5px; margin: 5px 0; border-left: 4px solid #28a745;">'
            f"<strong>Context Edit Decision:</strong> EDIT<br>"
            f"<em>{reasoning}</em>"
            f"</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div style="background-color: #3d3d3d; padding: 10px; border-radius: 5px; margin: 5px 0; border-left: 4px solid #6c757d;">'
            f"<strong>Context Edit Decision:</strong> NO EDIT<br>"
            f"<em>{reasoning}</em>"
            f"</div>",
            unsafe_allow_html=True,
        )


def display_shard_revealed(log: dict) -> None:
    """Display a shard revealed log entry."""
    data = log.get("data", {})
    shard_id = data.get("shard_id", "?")
    st.markdown(
        f'<div style="background-color: #1a3a4a; padding: 5px 10px; border-radius: 5px; margin: 2px 0; font-size: 0.9em;">'
        f"Shard revealed: <strong>#{shard_id}</strong>"
        f"</div>",
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
        f'<div style="background-color: {color}; padding: 5px 10px; border-radius: 5px; margin: 2px 0; font-size: 0.9em;">'
        f"{icon} Response classified as: <strong>{response_type}</strong>"
        f"</div>",
        unsafe_allow_html=True,
    )


def display_answer_evaluation(log: dict, task_name: str = "") -> None:
    """Display an answer evaluation log entry."""
    data = log.get("data", {})
    is_correct = data.get("is_correct", False)
    score = data.get("score", 0.0)
    extracted = data.get("extracted_answer", "")

    # For code/database tasks, use expander for long extracted answers
    if task_name in ("code", "database") and extracted and len(extracted) > 80:
        label = "Correct" if is_correct else "Incorrect"
        if is_correct:
            st.success(f"Answer: {label} (score: {score})")
        else:
            st.error(f"Answer: {label} (score: {score})")
        lang = "python" if task_name == "code" else "sql"
        with st.expander("View extracted answer", expanded=False):
            st.code(extracted, language=lang)
    else:
        if is_correct:
            st.success(f"Answer: `{extracted}` - Correct (score: {score})")
        else:
            st.error(f"Answer: `{extracted}` - Incorrect (score: {score})")


def display_context_replaced(log: dict) -> None:
    """Display a context replaced log entry."""
    data = log.get("data", {})
    new_count = data.get("new_message_count", "?")

    st.markdown(
        f'<div style="background-color: #4a2d4a; padding: 10px; border-radius: 5px; margin: 10px 0; border: 2px dashed #9c27b0;">'
        f"<strong>CONTEXT REPLACED</strong><br>"
        f"New message count: {new_count}<br>"
        f"<em>The assistant now sees a condensed version of the conversation.</em>"
        f"</div>",
        unsafe_allow_html=True,
    )


def display_reflection_generated(log: dict) -> None:
    """Display a reflection generated log entry."""
    data = log.get("data", {})
    reflection = data.get("reflection", "")

    st.markdown(
        f'<div style="background-color: #2d3a4a; padding: 10px; border-radius: 5px; margin: 10px 0; border-left: 4px solid #17a2b8;">'
        f"<strong>Reflection Added to Context</strong><br>"
        f'<em style="color: #a8d4e6;">{reflection}</em>'
        f"</div>",
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
        f'<div style="background-color: #2d4a2d; padding: 10px; border-radius: 5px; margin: 10px 0; border-left: 4px solid #28a745;">'
        f'<strong>Context Editor Output</strong> <span style="font-size: 0.85em; color: #888;">(model: {editor_model}, original turns: {original_turns})</span>'
        f"</div>",
        unsafe_allow_html=True,
    )

    with st.expander("View edited context sent to assistant", expanded=False):
        st.markdown(edited_context)


def display_context_edit_marker(turn_num: int) -> None:
    """Display a marker indicating context was edited (for context_edit strategy)."""
    st.markdown(
        f'<div style="background-color: #3d2d4a; padding: 8px; border-radius: 5px; margin: 10px 0; border: 1px solid #9c27b0; text-align: center;">'
        f'<strong style="color: #d4a8e6;">--- Context Edited (Turn {turn_num}) ---</strong><br>'
        f'<span style="font-size: 0.85em; color: #b8a8c8;">The assistant sees a condensed summary instead of full history above</span>'
        f"</div>",
        unsafe_allow_html=True,
    )


def display_original_problem(
    full_spec_q: Optional[str], ground_truth_a: Optional[str], task_name: str = ""
) -> None:
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
            f'<div style="background-color: #0d1a26; padding: 12px; border-radius: 5px; margin-bottom: 10px;">'
            f'<strong style="color: #5a9fd4;">Question:</strong><br>'
            f'<span style="color: #e0e0e0;">{full_spec_q}</span>'
            f"</div>",
            unsafe_allow_html=True,
        )

    if ground_truth_a:
        # For code/database tasks, always use expander with syntax-highlighted code
        if task_name in ("code", "database"):
            lang = "python" if task_name == "code" else "sql"
            with st.expander("Ground Truth Answer", expanded=False):
                st.code(ground_truth_a, language=lang)
        elif len(ground_truth_a) > 500:
            with st.expander("Ground Truth Answer (click to expand)", expanded=False):
                st.markdown(
                    f'<div style="background-color: #0d2618; padding: 12px; border-radius: 5px;">'
                    f'<span style="color: #a8e6cf;">{ground_truth_a}</span>'
                    f"</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                f'<div style="background-color: #0d2618; padding: 12px; border-radius: 5px;">'
                f'<strong style="color: #5ad4a8;">Ground Truth Answer:</strong><br>'
                f'<span style="color: #a8e6cf;">{ground_truth_a}</span>'
                f"</div>",
                unsafe_allow_html=True,
            )

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown(
        '<p style="font-size: 0.85em; color: #888; text-align: center; margin-top: 5px;">'
        "The problem above was sharded into multiple turns in the conversation below"
        "</p>",
        unsafe_allow_html=True,
    )


def display_log_entry(log: dict, show_verification: bool = True, task_name: str = "") -> None:
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
        display_answer_evaluation(log, task_name=task_name)
    elif log_type == "context_replaced":
        display_context_replaced(log)
    elif log_type == "reflection_generated":
        display_reflection_generated(log)
    elif log_type == "context_edit_output":
        display_context_edit_output(log)


def display_message(
    msg: dict,
    logs: list[dict],
    show_logs: bool = True,
    show_token_counts: bool = False,
    user_turn_number: int | None = None,
) -> None:
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
            caption_parts = []
            if timestamp:
                caption_parts.append(format_timestamp(timestamp))
            if show_token_counts:
                tok_count = count_tokens(content)
                turn_label = f"Turn {user_turn_number}" if user_turn_number else "User"
                caption_parts.append(f"{turn_label}: {tok_count} tokens")
            if caption_parts:
                st.caption("_" + " | ".join(caption_parts) + "_")

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
            f'<div style="background-color: #1e1e2e; padding: 10px; border-radius: 5px; margin: 5px 0; border-left: 4px solid #6c757d;">'
            f"<strong>System:</strong> {content}"
            f"</div>",
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


def extract_memory_from_system(content: str) -> tuple[str, str]:
    """Extract cheatsheet memory from system message content.

    Returns:
        Tuple of (system_content_without_memory, memory_content).
        memory_content is empty string if no cheatsheet found.
    """
    match = _CHEATSHEET_RE.search(content)
    if not match:
        return content, ""
    memory_content = match.group(1).strip()
    clean_content = _CHEATSHEET_RE.sub("", content).strip()
    return clean_content, memory_content


def display_memory_block(memory_content: str) -> None:
    """Display memory/cheatsheet content in a collapsible block."""
    if not memory_content:
        return
    with st.expander("Memory (Cheatsheet)", expanded=False):
        st.markdown(
            f'<div style="background-color: #2a2a1a; padding: 12px; border-radius: 5px; '
            f'border-left: 4px solid #d4a017;">'
            f'<span style="color: #e8d88a; white-space: pre-wrap;">{memory_content}</span>'
            f"</div>",
            unsafe_allow_html=True,
        )


def display_analysis_block(log_data: dict) -> None:
    """Display a conversation analysis log as an interleaved block."""
    parts = []
    if log_data.get("user_intent"):
        parts.append(f"**Task Spec**\n{log_data['user_intent']}")
    if log_data.get("aligned"):
        parts.append(f"**What Looks Right**\n{log_data['aligned']}")
    if log_data.get("issues") and log_data.get("needs_edit"):
        parts.append(f"**What Needs to Change**\n{log_data['issues']}")
    elif log_data.get("issues"):
        parts.append(f"**Notes**\n{log_data['issues']}")

    analyzer_model = log_data.get("analyzer_model", "")
    model_str = (
        f' <span style="font-size: 0.8em; color: #888;">({analyzer_model})</span>'
        if analyzer_model
        else ""
    )

    analysis_text = "\n\n".join(parts) if parts else "(no analysis content)"

    with st.expander(
        f"Conversation Analysis{' — issues found' if log_data.get('needs_edit') else ' — aligned'}",
        expanded=log_data.get("needs_edit", False),
    ):
        st.markdown(
            f'<div style="background-color: #1a2a3a; padding: 12px; border-radius: 5px; '
            f'border-left: 4px solid #17a2b8;">'
            f'<strong style="color: #7ab3e0;">Analyzer Output</strong>{model_str}'
            f"</div>",
            unsafe_allow_html=True,
        )
        st.markdown(analysis_text)


def display_edit_decision_inline(log_data: dict) -> None:
    """Display an edit decision as an inline indicator."""
    should_edit = log_data.get("should_edit", False)
    if should_edit:
        st.markdown(
            '<div style="background-color: #2d4a3e; padding: 8px 12px; border-radius: 5px; '
            'margin: 5px 0; border-left: 4px solid #28a745; text-align: center;">'
            '<strong style="color: #7ae6a8;">Decision: EDIT</strong> — rewriting context'
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="background-color: #2a2a2a; padding: 8px 12px; border-radius: 5px; '
            'margin: 5px 0; border-left: 4px solid #6c757d; text-align: center;">'
            '<strong style="color: #aaa;">Decision: NO EDIT</strong> — approach is aligned'
            "</div>",
            unsafe_allow_html=True,
        )


def display_context_reset_boundary(reset_num: int) -> None:
    """Display a visual boundary when context is reset (S2 edit)."""
    st.markdown(
        f'<div style="background-color: #3d2d4a; padding: 12px; border-radius: 5px; '
        f'margin: 15px 0; border: 2px dashed #9c27b0; text-align: center;">'
        f'<strong style="color: #d4a8e6; font-size: 1.1em;">'
        f"--- NEW CONVERSATION (Reset #{reset_num}) ---</strong><br>"
        f'<span style="font-size: 0.85em; color: #b8a8c8;">'
        f"Context was rewritten. The assistant now sees compacted context below.</span>"
        f"</div>",
        unsafe_allow_html=True,
    )


def display_compacted_conversation(content: str) -> None:
    """Display a compacted conversation message (from S2 context edit)."""
    with st.expander("Compacted Context (what the assistant sees)", expanded=True):
        st.markdown(
            f'<div style="background-color: #1a1a2e; padding: 12px; border-radius: 5px; '
            f'border-left: 4px solid #9c27b0;">'
            f'<span style="color: #d4c4e6; white-space: pre-wrap;">{content}</span>'
            f"</div>",
            unsafe_allow_html=True,
        )


def display_conversation(sample: dict, exp_type: str = "", run_dir: str = "") -> None:
    """Display a full conversation with interleaved analysis and context edits.

    Renders the conversation timeline similar to render_for_analyzer() in renderers.py:
    messages and analysis/edit logs are merged chronologically, showing exactly when
    the external context module intervened.

    Handles:
    - S0 (baseline): Simple message display
    - S1 (append_analysis): Strips embedded <conversation_analysis> tags from user
      messages and shows analysis as separate interleaved blocks
    - S2 (context_edit_v2): Shows analysis, edit decisions, and context reset
      boundaries with compacted conversation blocks
    - Memory: Extracts <cheatsheet> from system message and shows in collapsible
    """
    # Load original sample data (including shards) from data file
    task_id = sample.get("sample_id")
    task_name = sample.get("task_name", "")
    original_data: dict = {}
    if run_dir and task_id:
        original_data = get_original_sample_data(run_dir, task_id)
        full_spec_q = original_data.get("full_spec_q")
        ground_truth_a = original_data.get("ground_truth_a")
        display_original_problem(full_spec_q, ground_truth_a, task_name=task_name)

    # Prepare shard data for comparison
    shards_list = original_data.get("shards", [])
    shard_index = build_shard_index(shards_list) if shards_list else {}

    trace = sample.get("trace", {})

    # Handle empty trace
    if not trace or (isinstance(trace, list) and len(trace) == 0):
        error_msg = sample.get("metadata", {}).get("error", "No trace data")
        st.warning(f"No conversation data. Error: {error_msg}")
        return

    messages = get_messages_from_trace(trace)
    logs = get_logs_from_trace(trace)
    num_resets = trace.get("num_resets", 0)

    # Create a timeline of events (messages + logs)
    st.subheader("Conversation")

    if num_resets > 0:
        st.caption(f"Context was reset {num_resets} time(s) during this conversation.")

    # Show toggle for detailed logs
    show_verification = st.checkbox("Show verification logs", value=False)
    show_token_counts = st.checkbox("Show user token counts", value=True)
    show_shard_comparison = st.checkbox("Show shard comparison", value=False) if shard_index else False

    # Build a unified timeline of messages and logs, sorted by (timestamp, sequence)
    # This mirrors render_for_analyzer() — interleaving analysis at decision points
    events: list[tuple[str, int, str, dict]] = []
    seq = 0

    for msg in messages:
        events.append((msg.get("timestamp", ""), seq, "msg", msg))
        seq += 1

    for log_entry in logs:
        events.append((log_entry.get("timestamp", ""), seq, "log", log_entry))
        seq += 1

    # Sort by (timestamp, seq) — ISO format strings sort chronologically
    events.sort(key=lambda e: (e[0], e[1]))

    # Build turn → shard_id mapping from logs
    turn_shard_map = build_turn_shard_map(logs) if shard_index else {}

    # Render the timeline
    system_content_shown: str | None = None
    memory_content_shown = False
    reset_count = 0
    user_turn_count = 0

    for _, _, etype, data in events:
        if etype == "msg":
            role = data.get("role", "")
            content = data.get("content", "")
            timestamp = data.get("timestamp", "")
            visible = data.get("visible", True)

            # Handle compacted conversation → show reset boundary + compacted content
            if role == "compacted conversation":
                reset_count += 1
                display_context_reset_boundary(reset_count)
                display_compacted_conversation(content)
                continue

            # Skip non-visible messages (archived by S2 resets) — they're the old
            # conversation that was replaced. The compacted conversation above
            # represents what the assistant sees instead.
            if not visible:
                continue

            # Handle system message — extract memory, show once
            if role == "system":
                if system_content_shown is not None and content == system_content_shown:
                    # Skip duplicate system message from reset
                    continue
                system_content_shown = content

                # Extract and display memory separately
                clean_content, memory_content = extract_memory_from_system(content)

                if memory_content and not memory_content_shown:
                    display_memory_block(memory_content)
                    memory_content_shown = True

                # Show system message in expander (like existing pattern)
                with st.expander("System Message", expanded=False):
                    st.markdown(
                        f'<div style="background-color: #1e1e2e; padding: 10px; '
                        f'border-radius: 5px; border-left: 4px solid #6c757d;">'
                        f"{clean_content}</div>",
                        unsafe_allow_html=True,
                    )
                continue

            # Strip embedded <conversation_analysis> tags from user messages (S1 artifact)
            if role == "user" and "<conversation_analysis>" in content:
                content = _ANALYSIS_TAG_RE.sub("", content).rstrip()

            # Display user/assistant messages
            if role == "user":
                user_turn_count += 1
                with st.chat_message("user"):
                    st.markdown(content)
                    caption_parts = []
                    if timestamp:
                        caption_parts.append(format_timestamp(timestamp))
                    if show_token_counts:
                        tok_count = count_tokens(content)
                        caption_parts.append(f"Turn {user_turn_count}: {tok_count} tokens")
                    if caption_parts:
                        st.caption("_" + " | ".join(caption_parts) + "_")

                # Show shard comparison below the user message
                if show_shard_comparison and user_turn_count in turn_shard_map:
                    shard_id = turn_shard_map[user_turn_count]
                    shard_text = shard_index.get(shard_id, "(shard text not found)")
                    display_shard_comparison(content, shard_text, shard_id)

            elif role == "assistant":
                with st.chat_message("assistant"):
                    st.markdown(content)
                    if timestamp:
                        st.caption(f"_{format_timestamp(timestamp)}_")

        elif etype == "log":
            log_type = data.get("type", "")
            log_data = data.get("data", {})

            if log_type == "conversation_analysis":
                display_analysis_block(log_data)

            elif log_type == "edit_decision":
                display_edit_decision_inline(log_data)

            elif log_type == "context_edit_output":
                display_context_edit_output(data)

            elif log_type == "shard_revealed":
                display_shard_revealed(data)

            elif log_type == "verification":
                if show_verification:
                    display_verification(data)

            elif log_type == "answer_evaluation":
                display_answer_evaluation(data, task_name=task_name)

            elif log_type == "context_replaced":
                display_context_replaced(data)

            elif log_type == "reflection_generated":
                display_reflection_generated(data)

            elif log_type == "conversation_reset":
                # Already handled by compacted conversation boundary
                pass

    # Show total user tokens at the end of the conversation
    if show_token_counts:
        user_messages = [m for m in messages if m.get("role") == "user"]
        total_user_tokens = sum(count_tokens(m.get("content", "")) for m in user_messages)
        st.markdown(
            f"""<div style="background-color: #1a2a1a; padding: 10px; border-radius: 5px; """
            f"""margin: 15px 0; border: 1px solid #3a5a3a; text-align: center;">"""
            f"""<strong>Total user tokens: {total_user_tokens}</strong> """
            f"""across {len(user_messages)} turn(s)</div>""",
            unsafe_allow_html=True,
        )

    # Show shard breakdown at the bottom
    if shards_list:
        display_shard_summary(original_data.get("full_spec_q"), shards_list)

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
            if task_name in ("code", "database"):
                lang = "python" if task_name == "code" else "sql"
                st.markdown("**Ground Truth Answer:**")
                st.code(ground_truth, language=lang)
            else:
                st.success(f"**Ground Truth Answer:** {ground_truth}")
        elif ref_answer:
            if task_name in ("code", "database"):
                lang = "python" if task_name == "code" else "sql"
                st.markdown("**Reference Answer:**")
                st.code(ref_answer, language=lang)
            else:
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

    # User token stats from trace
    trace = sample.get("trace", {})
    if trace:
        user_msgs = [m for m in trace.get("messages", []) if m.get("role") == "user"]
        if user_msgs:
            per_turn = [count_tokens(m.get("content", "")) for m in user_msgs]
            total = sum(per_turn)
            st.sidebar.write(f"**User tokens:** {total} ({len(user_msgs)} turns)")
            st.sidebar.caption(f"Per turn: {per_turn}")

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

    # Provenance (replay mode)
    trace = sample.get("trace", {})
    provenance = trace.get("provenance")
    if provenance:
        st.sidebar.subheader("Replay Provenance")
        src_exp = provenance.get("source_experiment", "?")
        src_correct = provenance.get("source_is_correct")
        src_score = provenance.get("source_score")
        st.sidebar.write(f"**Source:** {src_exp}")
        if src_correct is not None:
            result_str = f"{'Correct' if src_correct else 'Incorrect'} (score: {src_score})"
            st.sidebar.write(f"**Source result:** {result_str}")
        src_path = provenance.get("source_path", "")
        if src_path:
            st.sidebar.caption(f"From: {src_path}")

    # Error attribution
    metadata = sample.get("metadata", {})
    error_attr = metadata.get("error_attribution")
    if error_attr:
        st.sidebar.subheader("Error Attribution")
        category = error_attr.get("error_category", error_attr.get("category", "unknown"))
        cat_colors = {
            "assistant_error": "red",
            "extraction_failure": "orange",
            "sharding_distortion": "blue",
            "strict_comparison": "violet",
            "clarification_ignored": "orange",
        }
        color = cat_colors.get(category, "grey")
        st.sidebar.markdown(f":{color}[**{category}**]")
        explanation = error_attr.get("explanation", "")
        if explanation:
            with st.sidebar.expander("Details", expanded=False):
                st.write(explanation)

    # Branch info
    branch = metadata.get("branch", "")
    if branch:
        st.sidebar.write(f"**Branch:** `{branch}`")

    # Extracted answer
    extracted = sample.get("extracted_answer")
    if extracted:
        task_name = sample.get("task_name", "")
        st.sidebar.subheader("Extracted Answer")
        if task_name in ("code", "database"):
            lang = "python" if task_name == "code" else "sql"
            with st.sidebar.expander("View extracted answer", expanded=False):
                st.code(extracted, language=lang)
        else:
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
    selected_user_mode = None

    if custom_path and custom_path.strip():
        # Use custom path directly
        custom_path = custom_path.strip()
        if os.path.exists(custom_path):
            selected_run = custom_path
            # Try to get experiment type and user mode from config
            config = load_config_file(custom_path)
            selected_exp = (
                config.get("experiment", {}).get("name", "unknown") if config else "unknown"
            )
            selected_user_mode = config.get("user_mode", {}).get("name") if config else None
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
            user_mode = r.get("user_mode", "")
            acc = r.get("accuracy")
            acc_str = f" ({acc:.0%})" if acc is not None else ""
            mode_str = f" <{user_mode}>" if user_mode else ""
            return f"{path} [{strategy}]{mode_str}{acc_str}"

        selected_run_idx = st.sidebar.selectbox(
            "Run",
            range(len(filtered_runs)),
            format_func=lambda i: make_run_label(filtered_runs[i]),
        )

        selected_run_info = filtered_runs[selected_run_idx]
        selected_run = selected_run_info.get("full_path", "")
        selected_exp = selected_run_info.get("strategy", "unknown")
        selected_user_mode = selected_run_info.get("user_mode")

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

    # Build strategy description — detect S0/S1/S2 and memory
    has_memory = "memory" in effective_exp_type
    memory_tag = " + Memory" if has_memory else ""

    if "context_edit_v2" in effective_exp_type:
        strategy_desc = f"**Strategy:** S2 — Context Edit{memory_tag} — Analyzer-driven context rewriting when issues found"
    elif "context_edit" in effective_exp_type and "agentic" not in effective_exp_type:
        strategy_desc = f"**Strategy:** S2 — Context Edit{memory_tag} — Conversation is compressed before each assistant turn"
    elif "append_analysis" in effective_exp_type:
        strategy_desc = f"**Strategy:** S1 — Append Analysis{memory_tag} — Analysis appended to context (no rewriting)"
    elif "agentic_edit" in effective_exp_type:
        strategy_desc = (
            f"**Strategy:** Agentic Edit{memory_tag} — Model decides when to compress context"
        )
    elif "reflection" in effective_exp_type:
        strategy_desc = (
            f"**Strategy:** Reflection{memory_tag} — Reflection prompts added to context"
        )
    elif "baseline" in effective_exp_type:
        strategy_desc = f"**Strategy:** S0 — Baseline{memory_tag} — No context modifications"
    else:
        strategy_desc = f"**Strategy:** {effective_exp_type}"

    # Append user mode if available
    if selected_user_mode:
        mode_labels = {
            "sharded": "Sharded (pre-defined shard reveals)",
            "natural": "Natural (full problem, no constraints)",
            "length_constrained": "Length-Constrained (token-budgeted turns)",
        }
        mode_label = mode_labels.get(selected_user_mode, selected_user_mode)
        strategy_desc += f"  |  **User Mode:** {mode_label}"

    st.info(strategy_desc)

    # Display the conversation
    display_conversation(
        selected_sample_with_trace, exp_type=effective_exp_type, run_dir=selected_run
    )


if __name__ == "__main__":
    main()
