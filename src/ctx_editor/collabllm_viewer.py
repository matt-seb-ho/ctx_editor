"""
CollabLLM Trace Viewer

Streamlit app for inspecting CollabLLM multi-turn conversations,
context interventions (analysis, compaction/reset), and extracted outputs.

Usage:
    streamlit run src/ctx_editor/collabllm_viewer.py
"""

import json
import os
from pathlib import Path
from typing import Any, Optional

import streamlit as st

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OUTPUTS_ROOT = "outputs"

# Rose Pine palette
RP_BASE = "#191724"
RP_SURFACE = "#1f1d2e"
RP_OVERLAY = "#26233a"
RP_MUTED = "#6e6a86"
RP_SUBTLE = "#908caa"
RP_TEXT = "#e0def4"
RP_LOVE = "#eb6f92"
RP_GOLD = "#f6c177"
RP_ROSE = "#ebbcba"
RP_PINE = "#31748f"
RP_FOAM = "#9ccfd8"
RP_IRIS = "#c4a7e7"

ROLE_COLORS = {
    "system": RP_SUBTLE,
    "user": RP_FOAM,
    "assistant": RP_LOVE,
    "compacted conversation": RP_IRIS,
    "analysis": RP_GOLD,
    "compaction_analysis": RP_GOLD,
    "context_compaction": RP_ROSE,
    "reset_marker": RP_LOVE,
}

ROLE_ICONS = {
    "system": "gear",
    "user": "person",
    "assistant": "robot",
    "compacted conversation": "clipboard",
    "analysis": "search",
    "compaction_analysis": "search",
    "context_compaction": "pencil",
    "reset_marker": "arrow-repeat",
}


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


@st.cache_data
def load_trace(path: str) -> dict[str, Any]:
    with open(path, "r") as f:
        return json.load(f)


@st.cache_data
def load_config(run_dir: str) -> Optional[dict]:
    path = os.path.join(run_dir, "config.yaml")
    if os.path.exists(path):
        import yaml

        with open(path) as f:
            return yaml.safe_load(f)
    return None


@st.cache_data
def load_metrics(run_dir: str) -> Optional[dict]:
    path = os.path.join(run_dir, "metrics.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None


@st.cache_data
def load_results(run_dir: str) -> Optional[list]:
    path = os.path.join(run_dir, "results.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None


@st.cache_data
def load_reeval_results(run_dir: str, model: str) -> Optional[dict]:
    """Load re-evaluation results for a specific model."""
    reeval_dir = os.path.join(run_dir, f"reeval_{model.replace('/', '_')}")
    metrics_path = os.path.join(reeval_dir, "metrics.json")
    results_path = os.path.join(reeval_dir, "results.json")
    if os.path.exists(metrics_path):
        with open(metrics_path) as f:
            metrics = json.load(f)
        results = None
        if os.path.exists(results_path):
            with open(results_path) as f:
                results = json.load(f)
        return {"metrics": metrics, "results": results}
    return None


def list_trace_files(run_dir: str) -> list[dict]:
    """List all trace files in a run directory."""
    traces_dir = os.path.join(run_dir, "traces")
    if not os.path.isdir(traces_dir):
        return []

    files = []
    for root, _, filenames in os.walk(traces_dir):
        for fn in sorted(filenames):
            if fn.endswith(".json"):
                full_path = os.path.join(root, fn)
                # Extract task and experiment from path
                rel = os.path.relpath(root, traces_dir)
                parts = rel.split(os.sep)
                task_name = parts[0] if len(parts) > 0 else ""
                exp_name = parts[1] if len(parts) > 1 else ""
                files.append({
                    "path": full_path,
                    "filename": fn,
                    "sample_id": fn.replace(".json", ""),
                    "task_name": task_name,
                    "exp_name": exp_name,
                })
    return files


def find_run_dirs(outputs_root: str) -> list[str]:
    """Find all run directories (those containing config.yaml)."""
    dirs = []
    if not os.path.isdir(outputs_root):
        return dirs
    for date_dir in sorted(os.listdir(outputs_root), reverse=True):
        date_path = os.path.join(outputs_root, date_dir)
        if not os.path.isdir(date_path):
            continue
        for time_dir in sorted(os.listdir(date_path), reverse=True):
            run_path = os.path.join(date_path, time_dir)
            if os.path.isfile(os.path.join(run_path, "config.yaml")):
                dirs.append(run_path)
    return dirs


def find_sample_in_results(results: list, sample_id: str) -> Optional[dict]:
    """Find a sample's result entry by ID."""
    if not results:
        return None
    for r in results:
        if r.get("sample_id", "") == sample_id or sample_id in r.get("sample_id", ""):
            return r
    return None


# ---------------------------------------------------------------------------
# Conversation display construction
# ---------------------------------------------------------------------------


def build_display_messages(trace_data: dict) -> list[dict]:
    """Build a timeline of messages interleaved with log events.

    Reconstructs the conversation with analysis/compaction events
    inserted at the correct points in the timeline.
    """
    messages = trace_data.get("trace", {}).get("messages", [])
    logs = trace_data.get("trace", {}).get("logs", [])

    # Index logs by type for quick lookup
    analysis_logs = [l for l in logs if l["type"] in ("compaction_analysis", "conversation_analysis")]
    compaction_logs = [l for l in logs if l["type"] == "context_compaction"]
    reset_logs = [l for l in logs if l["type"] == "conversation_reset"]
    eval_logs = [l for l in logs if l["type"] == "collabllm_evaluation"]

    display = []
    analysis_idx = 0
    compaction_idx = 0
    reset_idx = 0

    for i, msg in enumerate(messages):
        role = msg.get("role", "unknown")
        visible = msg.get("visible", True)

        # Before any compacted conversation message (visible or not), insert the
        # analysis/compaction/reset that triggered it. Each compacted conversation
        # corresponds to one reset cycle.
        if role == "compacted conversation":
            # Only insert logs for the first compacted message in each reset
            # (resets produce system + compacted + user, we trigger on compacted)
            prev_role = messages[i - 1].get("role") if i > 0 else None
            if prev_role == "system" or i == 0:
                # Insert analysis log
                if analysis_idx < len(analysis_logs):
                    display.append({
                        "role": "analysis",
                        "content": _format_analysis_log(analysis_logs[analysis_idx]),
                        "visible": True,
                        "log_data": analysis_logs[analysis_idx],
                        "is_log": True,
                    })
                    analysis_idx += 1

                # Insert compaction log
                if compaction_idx < len(compaction_logs):
                    display.append({
                        "role": "context_compaction",
                        "content": _format_compaction_log(compaction_logs[compaction_idx]),
                        "visible": True,
                        "log_data": compaction_logs[compaction_idx],
                        "is_log": True,
                    })
                    compaction_idx += 1

                # Insert reset marker
                if reset_idx < len(reset_logs):
                    display.append({
                        "role": "reset_marker",
                        "content": f"Context Reset #{reset_logs[reset_idx]['data'].get('total_resets', '?')}",
                        "visible": True,
                        "metadata": reset_logs[reset_idx]["data"],
                        "is_log": True,
                    })
                    reset_idx += 1

        # Add the actual message
        display.append({
            "role": role,
            "content": msg.get("content", ""),
            "visible": visible,
            "timestamp": msg.get("timestamp", ""),
            "metadata": msg.get("metadata", {}),
        })


    # Append evaluation log at the end
    if eval_logs:
        display.append({
            "role": "evaluation",
            "content": _format_eval_log(eval_logs[-1]),
            "visible": True,
            "log_data": eval_logs[-1],
            "is_log": True,
        })

    return display


def _format_analysis_log(log: dict) -> str:
    """Format an analysis log entry for display."""
    data = log.get("data", {})
    parts = []
    if data.get("task_spec"):
        parts.append(f"**Task Specification:**\n{data['task_spec']}")
    if data.get("aligned"):
        parts.append(f"**What Looks Right:**\n{data['aligned']}")
    if data.get("issues"):
        parts.append(f"**Issues:**\n{data['issues']}")
    if data.get("needs_edit") is not None:
        parts.append(f"**Needs Edit:** {'Yes' if data['needs_edit'] else 'No'}")
    return "\n\n".join(parts) if parts else str(data)


def _format_compaction_log(log: dict) -> str:
    """Format a compaction log entry for display."""
    data = log.get("data", {})
    parts = []
    if data.get("compacted_task_spec"):
        parts.append(f"**Compacted Task Spec:**\n{data['compacted_task_spec']}")
    if data.get("compacted_work_so_far"):
        parts.append(f"**Compacted Work So Far:**\n{data['compacted_work_so_far']}")
    parts.append(f"Original turns: {data.get('original_turn_count', '?')}, "
                 f"Active turns: {data.get('active_turn_count', '?')}")
    return "\n\n".join(parts) if parts else str(data)


def _format_eval_log(log: dict) -> str:
    """Format evaluation log for display."""
    data = log.get("data", {})
    parts = []
    acc = data.get("accuracy", -1)
    parts.append(f"**Accuracy:** {acc:.0%}" if acc >= 0 else "**Accuracy:** N/A")
    inter = data.get("interactivity", -1)
    if inter >= 0:
        parts.append(f"**Interactivity:** {inter:.3f}")
    tokens = data.get("assistant_tokens", 0)
    if tokens:
        parts.append(f"**Assistant Tokens:** {tokens}")
    extracted = data.get("extracted_answer", "")
    if extracted:
        parts.append(f"**Extracted Answer:**\n```\n{extracted[:2000]}\n```")
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def render_message_card(msg: dict, task_name: str = ""):
    """Render a single message as a styled card."""
    role = msg["role"]
    visible = msg.get("visible", True)
    content = msg.get("content", "")
    is_log = msg.get("is_log", False)

    color = ROLE_COLORS.get(role, RP_SUBTLE)

    # Role labels
    role_labels = {
        "compacted conversation": "Compacted Conversation",
        "reset_marker": "Context Reset",
        "analysis": "Analysis (Independent Reviewer)",
        "compaction_analysis": "Compaction Analysis",
        "context_compaction": "Context Compaction Output",
        "evaluation": "End-of-Conversation Evaluation",
    }
    role_label = role_labels.get(role, role.title())

    vis_tag = ""
    if not visible and role not in ("reset_marker",):
        vis_tag = "(hidden, pre-reset)"

    # --- Reset marker ---
    if role == "reset_marker":
        st.divider()
        reset_num = msg.get("metadata", {}).get("total_resets", "?")
        st.markdown(
            f'<div style="text-align:center; padding:8px; '
            f"background:{RP_LOVE}18; border:1px solid {RP_LOVE}; "
            f'border-radius:8px; margin:8px 0;">'
            f"<strong>Context Reset #{reset_num}</strong>"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.divider()
        return

    # --- Header ---
    header_parts = [
        f'<span style="color:{color}; font-weight:600;">{role_label}</span>'
    ]
    if vis_tag:
        header_parts.append(
            f'<span style="color:{RP_MUTED}; font-style:italic;">{vis_tag}</span>'
        )
    ts = msg.get("timestamp", "")
    if ts:
        header_parts.append(
            f'<span style="color:{RP_MUTED}; font-size:0.85em;">  {ts}</span>'
        )

    st.markdown(
        f'<div style="border-left:4px solid {color}; padding-left:12px; '
        f'margin-bottom:2px;">'
        f'<p style="margin:4px 0;">{"&nbsp;&nbsp;".join(header_parts)}</p>'
        f"</div>",
        unsafe_allow_html=True,
    )

    # --- Content ---
    if role == "system":
        with st.expander("System Prompt", expanded=False):
            st.markdown(content)
    elif role == "analysis" or role == "compaction_analysis":
        with st.expander("Analysis Details", expanded=True):
            st.markdown(content)
    elif role == "context_compaction":
        with st.expander("Compaction Output", expanded=True):
            st.markdown(content)
    elif role == "compacted conversation":
        with st.expander("Compacted Conversation", expanded=True):
            st.code(content, language=None)
    elif role == "evaluation":
        with st.expander("Evaluation Results", expanded=True):
            st.markdown(content)
    elif not visible:
        with st.expander(f"{role_label} (hidden)", expanded=False):
            st.markdown(content)
    else:
        # Regular user/assistant message
        if "collabllm_code" in task_name and role == "assistant":
            st.markdown(content)
        else:
            st.markdown(content)

    st.markdown("---")


# ---------------------------------------------------------------------------
# Tab renderers
# ---------------------------------------------------------------------------


def render_question_tab(trace_data: dict, config: Optional[dict], sample_result: Optional[dict]):
    """Tab: Original question and ground truth."""
    # Try to find the original prompt from config or trace
    logs = trace_data.get("trace", {}).get("logs", [])

    st.subheader("Original Question (single_turn_prompt)")
    st.caption("This is the full problem specification that the user simulator has access to. "
               "The user simulator is instructed to be vague and not copy this directly.")

    # We don't store single_turn_prompt in traces, but we can show what the user sim saw
    # by looking at the first user message or config
    if config:
        dataset = config.get("task", {}).get("dataset_name", "unknown")
        st.markdown(f"**Dataset:** `{dataset}`")
        st.markdown(f"**Max Turns:** `{config.get('task', {}).get('max_turns', '?')}`")

    if sample_result:
        st.markdown(f"**Sample ID:** `{sample_result.get('sample_id', '?')}`")
        st.markdown(f"**Correct:** {'Yes' if sample_result.get('is_correct') else 'No'}")
        st.markdown(f"**Score:** `{sample_result.get('score', '?')}`")
        st.markdown(f"**Turns:** `{sample_result.get('num_turns', '?')}`")
        st.markdown(f"**Cost:** `${sample_result.get('total_cost_usd', 0):.4f}`")

    # Show evaluation results from logs
    eval_log = next((l for l in logs if l["type"] == "collabllm_evaluation"), None)
    if eval_log:
        data = eval_log["data"]
        st.subheader("Evaluation Results")
        col1, col2, col3 = st.columns(3)
        acc = data.get("accuracy", -1)
        col1.metric("Accuracy", f"{acc:.0%}" if acc >= 0 else "N/A")
        inter = data.get("interactivity", -1)
        col2.metric("Interactivity", f"{inter:.3f}" if inter >= 0 else "N/A")
        col3.metric("Asst Tokens", data.get("assistant_tokens", 0))

        extracted = data.get("extracted_answer", "")
        if extracted:
            st.subheader("Extracted Answer")
            st.code(extracted, language="python")


def render_conversation_tab(trace_data: dict, task_name: str = "", show_hidden: bool = True):
    """Tab: Full conversation timeline with interventions."""
    display = build_display_messages(trace_data)

    num_resets = trace_data.get("trace", {}).get("num_resets", 0)
    messages = trace_data.get("trace", {}).get("messages", [])
    total_user = sum(1 for m in messages if m.get("role") == "user")
    total_asst = sum(1 for m in messages if m.get("role") == "assistant")
    visible_user = sum(1 for m in messages if m.get("role") == "user" and m.get("visible", True))

    st.caption(
        f"Total turns: {total_user} user + {total_asst} assistant | "
        f"Visible: {visible_user} user | "
        f"Resets: {num_resets}"
    )

    for i, msg in enumerate(display):
        if not show_hidden and not msg.get("visible", True):
            continue
        render_message_card(msg, task_name=task_name)


def render_interventions_tab(trace_data: dict):
    """Tab: Just the context interventions (analysis + compaction + resets)."""
    logs = trace_data.get("trace", {}).get("logs", [])

    intervention_types = {"compaction_analysis", "conversation_analysis", "context_compaction",
                          "conversation_reset", "edit_decision", "context_edit_output"}
    interventions = [l for l in logs if l["type"] in intervention_types]

    if not interventions:
        st.info("No context interventions in this conversation (baseline run).")
        return

    st.caption(f"{len(interventions)} intervention events")

    for i, log in enumerate(interventions):
        log_type = log["type"]
        data = log.get("data", {})
        ts = log.get("timestamp", "")

        if log_type in ("compaction_analysis", "conversation_analysis"):
            color = RP_GOLD
            label = "Analysis"
            st.markdown(
                f'<div style="border-left:4px solid {color}; padding-left:12px;">'
                f'<span style="color:{color}; font-weight:600;">{label}</span>'
                f'&nbsp;&nbsp;<span style="color:{RP_MUTED}; font-size:0.85em;">{ts}</span>'
                f"</div>",
                unsafe_allow_html=True,
            )
            if data.get("task_spec"):
                st.markdown("**Task Spec:**")
                st.code(data["task_spec"], language=None)
            if data.get("aligned"):
                st.markdown("**Aligned:**")
                st.code(data["aligned"], language=None)
            if data.get("issues"):
                st.markdown("**Issues:**")
                st.code(data["issues"], language=None)
            if data.get("needs_edit") is not None:
                st.markdown(f"Needs edit: **{'Yes' if data['needs_edit'] else 'No'}**")
            st.markdown("---")

        elif log_type == "context_compaction":
            color = RP_ROSE
            label = "Compaction Output"
            st.markdown(
                f'<div style="border-left:4px solid {color}; padding-left:12px;">'
                f'<span style="color:{color}; font-weight:600;">{label}</span>'
                f'&nbsp;&nbsp;<span style="color:{RP_MUTED}; font-size:0.85em;">{ts}</span>'
                f"</div>",
                unsafe_allow_html=True,
            )
            if data.get("compacted_task_spec"):
                st.markdown("**Compacted Task Spec:**")
                st.code(data["compacted_task_spec"], language=None)
            if data.get("compacted_work_so_far"):
                st.markdown("**Work So Far:**")
                st.code(data["compacted_work_so_far"], language=None)
            st.caption(f"Original turns: {data.get('original_turn_count', '?')}, "
                       f"Active turns: {data.get('active_turn_count', '?')}")
            st.markdown("---")

        elif log_type == "conversation_reset":
            st.divider()
            reset_num = data.get("total_resets", "?")
            st.markdown(
                f'<div style="text-align:center; padding:8px; '
                f"background:{RP_LOVE}18; border:1px solid {RP_LOVE}; "
                f'border-radius:8px;">'
                f"<strong>Context Reset #{reset_num}</strong> "
                f'<span style="color:{RP_MUTED};">({data.get("new_message_count", "?")} new messages)</span>'
                f"</div>",
                unsafe_allow_html=True,
            )
            st.divider()

        elif log_type == "edit_decision":
            should = data.get("should_edit", False)
            st.caption(f"Edit decision: **{'Edit' if should else 'Pass'}** ({ts})")

        elif log_type == "context_edit_output":
            st.markdown("**Context Edit Output:**")
            if data.get("edited_context"):
                st.code(data["edited_context"][:2000], language=None)


def render_run_info_tab(run_dir: str, metrics: Optional[dict], results: Optional[list]):
    """Tab: Run-level metrics and config."""
    config = load_config(run_dir)

    if config:
        st.subheader("Configuration")
        exp_name = config.get("experiment_name", "unknown")
        st.markdown(f"**Experiment:** `{exp_name}`")
        st.markdown(f"**Model:** `{config.get('model', {}).get('name', '?')}`")
        st.markdown(f"**Dataset:** `{config.get('task', {}).get('dataset_name', '?')}`")

        strategy = config.get("experiment", {}).get("strategy", {})
        if strategy:
            st.markdown(f"**Strategy:** `{strategy.get('_target_', '?').split('.')[-1]}`")
            for k, v in strategy.items():
                if k != "_target_":
                    st.markdown(f"  - {k}: `{v}`")

    if metrics:
        st.subheader("Metrics")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Accuracy", f"{metrics.get('accuracy', 0):.1%}")
        col2.metric("Samples", f"{metrics.get('correct', 0)}/{metrics.get('total_samples', 0)}")
        col3.metric("Avg Turns", f"{metrics.get('average_turns', 0):.1f}")
        col4.metric("Cost", f"${metrics.get('total_cost_usd', 0):.4f}")

        if metrics.get("interactivity"):
            st.metric("Interactivity", f"{metrics['interactivity']:.3f}")
        if metrics.get("errors", 0) > 0:
            st.warning(f"{metrics['errors']} errors excluded from metrics")

    # Per-sample results table
    if results:
        st.subheader("Per-Sample Results")
        table_data = []
        for r in results:
            table_data.append({
                "Sample": r.get("sample_id", "?"),
                "Correct": "Yes" if r.get("is_correct") else "No",
                "Accuracy": f"{r.get('metadata', {}).get('accuracy', -1):.1%}",
                "Turns": r.get("num_turns", "?"),
                "Cost": f"${r.get('total_cost_usd', 0):.4f}",
            })
        st.dataframe(table_data, use_container_width=True)

    # Re-evaluation results
    reeval_dirs = []
    for item in os.listdir(run_dir):
        if item.startswith("reeval_"):
            reeval_dirs.append(item)

    if reeval_dirs:
        st.subheader("Re-evaluations")
        for rd in sorted(reeval_dirs):
            model_name = rd.replace("reeval_", "")
            reeval_path = os.path.join(run_dir, rd, "metrics.json")
            if os.path.exists(reeval_path):
                with open(reeval_path) as f:
                    rm = json.load(f)
                st.markdown(f"**{model_name}:** {rm.get('accuracy', 0):.1%} "
                            f"({rm.get('correct', 0)}/{rm.get('total_samples', 0)}), "
                            f"eval cost: ${rm.get('total_eval_cost_usd', 0):.4f}")


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------


def main():
    st.set_page_config(page_title="CollabLLM Viewer", layout="wide")
    st.title("CollabLLM Trace Viewer")

    # --- Sidebar: run selection ---
    with st.sidebar:
        st.header("Run Selection")

        # Path prefix for rsync mirrors
        path_prefix = st.text_input("Path prefix", value="", help="Prefix for resolving output paths")
        outputs_root = os.path.join(path_prefix, OUTPUTS_ROOT) if path_prefix else OUTPUTS_ROOT

        run_dirs = find_run_dirs(outputs_root)

        if not run_dirs:
            st.warning(f"No runs found in {outputs_root}")
            return

        # Build labels for each run
        run_labels = []
        for rd in run_dirs:
            config = load_config(rd)
            metrics = load_metrics(rd)
            label = os.path.relpath(rd, outputs_root)
            if config:
                exp = config.get("experiment_name", "")
                if exp:
                    label = f"{label} ({exp})"
            if metrics:
                acc = metrics.get("accuracy", 0)
                n = metrics.get("total_samples", 0)
                label += f" [{acc:.0%}, n={n}]"
            run_labels.append(label)

        selected_idx = st.selectbox(
            "Run",
            range(len(run_dirs)),
            format_func=lambda i: run_labels[i],
        )
        run_dir = run_dirs[selected_idx]

        # Load traces
        trace_files = list_trace_files(run_dir)
        if not trace_files:
            st.warning("No traces found in this run")
            return

        # Task filter
        tasks = sorted(set(t["task_name"] for t in trace_files))
        if len(tasks) > 1:
            task_filter = st.selectbox("Task", ["All"] + tasks)
            if task_filter != "All":
                trace_files = [t for t in trace_files if t["task_name"] == task_filter]

        # Correctness filter
        results = load_results(run_dir)
        filter_correct = st.selectbox("Filter", ["All", "Correct", "Incorrect"])
        if filter_correct != "All" and results:
            filtered = []
            for tf in trace_files:
                r = find_sample_in_results(results, tf["sample_id"])
                if r:
                    is_correct = r.get("is_correct", False)
                    if (filter_correct == "Correct" and is_correct) or \
                       (filter_correct == "Incorrect" and not is_correct):
                        filtered.append(tf)
            trace_files = filtered

        st.caption(f"{len(trace_files)} samples")

        # Show/hide hidden messages
        show_hidden = st.checkbox("Show hidden messages", value=True)

        st.markdown("---")

        # Run-level stats
        metrics = load_metrics(run_dir)
        if metrics:
            st.metric("Accuracy", f"{metrics.get('accuracy', 0):.1%}")
            st.metric("Avg Turns", f"{metrics.get('average_turns', 0):.1f}")
            st.metric("Cost", f"${metrics.get('total_cost_usd', 0):.4f}")

    if not trace_files:
        st.info("No traces match the current filters.")
        return

    # --- Sample navigation ---
    if "sample_idx" not in st.session_state:
        st.session_state.sample_idx = 0

    # Clamp index
    st.session_state.sample_idx = max(0, min(st.session_state.sample_idx, len(trace_files) - 1))

    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("Prev") and st.session_state.sample_idx > 0:
            st.session_state.sample_idx -= 1
            st.rerun()
    with col2:
        selected = st.selectbox(
            "Sample",
            range(len(trace_files)),
            index=st.session_state.sample_idx,
            format_func=lambda i: trace_files[i]["sample_id"],
            key="sample_select",
        )
        if selected != st.session_state.sample_idx:
            st.session_state.sample_idx = selected
            st.rerun()
    with col3:
        if st.button("Next") and st.session_state.sample_idx < len(trace_files) - 1:
            st.session_state.sample_idx += 1
            st.rerun()

    # Load selected trace
    tf = trace_files[st.session_state.sample_idx]
    trace_data = load_trace(tf["path"])
    task_name = tf["task_name"]
    sample_result = find_sample_in_results(results, tf["sample_id"]) if results else None

    # Header with quick stats
    is_correct = sample_result.get("is_correct", False) if sample_result else None
    if is_correct is not None:
        badge_color = "#2ea043" if is_correct else "#da3633"
        badge_text = "CORRECT" if is_correct else "INCORRECT"
        st.markdown(
            f'<span style="background:{badge_color}; color:white; padding:2px 8px; '
            f'border-radius:4px; font-weight:600; font-size:0.9em;">{badge_text}</span>'
            f'&nbsp;&nbsp;{tf["sample_id"]}',
            unsafe_allow_html=True,
        )

    # --- Tabs ---
    tab_names = ["Conversation", "Interventions", "Question & Eval", "Run Info"]
    tabs = st.tabs(tab_names)

    with tabs[0]:
        render_conversation_tab(trace_data, task_name=task_name, show_hidden=show_hidden)

    with tabs[1]:
        render_interventions_tab(trace_data)

    with tabs[2]:
        render_question_tab(trace_data, load_config(run_dir), sample_result)

    with tabs[3]:
        render_run_info_tab(run_dir, metrics, results)


if __name__ == "__main__":
    main()
