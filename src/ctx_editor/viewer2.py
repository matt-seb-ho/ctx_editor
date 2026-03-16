"""
Context Editor Trace Viewer v2

Usage:
    streamlit run src/ctx_editor/viewer2.py
"""

import json
import os
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
    "system": "gear",
    "user": "person",
    "assistant": "robot",
    "compacted conversation": "clipboard",
    "analysis": "search",
    "analyst": "search",
    "context_edit_output": "pencil",
    "reset_marker": "arrow-repeat",
}

RESPONSE_TYPE_LABELS = {
    "answer_attempt": "Answer Attempt",
    "interrogation": "Interrogation",
    "discussion": "Discussion",
    "partial_answer": "Partial Answer",
    "other": "Other",
}

# Tasks where extracted answer should be shown as a code block
CODE_BLOCK_TASKS = {"code", "database", "actions"}

# Error attribution category display labels
ERROR_CATEGORY_LABELS = {
    "assistant_error": "Assistant Error",
    "extraction_failure": "Extraction Failure",
    "strict_comparison": "Strict Comparison",
    "user_simulator_error": "User Simulator Error",
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
    candidate = os.path.join(OUTPUTS_ROOT, p)
    if os.path.exists(candidate):
        return candidate
    if os.path.exists(p):
        return p
    return p


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


@st.cache_data
def load_error_analysis(run_dir: str) -> Optional[dict]:
    """Load error_analysis.json from a run directory."""
    path = os.path.join(run_dir, "error_analysis.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return None


def find_result_for_sample(
    results: Optional[list[dict]], sample_id: str
) -> Optional[dict]:
    """Find the result entry for a given sample_id in results.json."""
    if not results:
        return None
    normalized = sample_id.replace("_", "/")
    for r in results:
        if r.get("sample_id") == normalized or r.get("sample_id") == sample_id:
            return r
    return None


def find_error_for_sample(
    error_analysis: Optional[dict], sample_id: str
) -> Optional[dict]:
    """Find the error attribution entry for a given sample_id."""
    if not error_analysis:
        return None
    normalized = sample_id.replace("_", "/")
    for r in error_analysis.get("results", []):
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

    display = []
    log_idx = 0

    for msg_idx, msg in enumerate(messages):
        role = msg.get("role", "unknown")
        visible = msg.get("visible", True)

        # For S2: insert analysis + reset marker before compacted conversation
        if role == "system" and msg_idx > 0 and not messages[msg_idx - 1].get("visible", True):
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
                elif log["type"] in ("conversation_analysis", "edit_decision"):
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
                    break
                elif log["type"] in ("verification", "answer_evaluation",
                                     "conversation_analysis", "edit_decision"):
                    post_turn_logs.append(
                        {
                            "log_type": log["type"],
                            "data": log["data"],
                            "timestamp": log.get("timestamp", ""),
                        }
                    )
                    log_idx += 1
                elif log["type"] in ("context_edit_output", "conversation_reset"):
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


def render_message_card(msg: dict, idx: int, task_name: str = ""):
    """Render a single message as a styled card."""
    role = msg["role"]
    visible = msg.get("visible", True)
    content = msg.get("content", "")

    color = ROLE_COLORS.get(role, "#333")
    icon = ROLE_ICONS.get(role, "chat-dots")
    opacity = "1.0" if visible else "0.5"

    # Role label
    if role == "compacted conversation":
        role_label = "Compacted Conversation"
    elif role == "reset_marker":
        role_label = content
    elif role == "analysis":
        role_label = "Analyzer Output"
    else:
        role_label = role.title()

    # Shard tag
    shard_tag = ""
    if msg.get("shard_ids"):
        shard_strs = [f"Shard {s}" for s in msg["shard_ids"]]
        shard_tag = " · ".join(shard_strs)

    # Visibility tag
    vis_tag = "(hidden — pre-reset)" if not visible else ""

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

    # --- Render card ---
    with st.container():
        # Build header parts as separate elements to avoid markdown-in-html issues
        header_parts = [f":{icon}: **{role_label}**"]
        if shard_tag:
            header_parts.append(f"`{shard_tag}`")
        if vis_tag:
            header_parts.append(f"*{vis_tag}*")
        ts = msg.get("timestamp", "")
        if ts:
            header_parts.append(f"— *{ts}*")

        # Use a colored container via border-left, but header as pure markdown
        st.markdown(
            f'<div style="border-left: 4px solid {color}; padding-left: 12px; opacity: {opacity};">',
            unsafe_allow_html=True,
        )
        st.markdown(" &nbsp; ".join(header_parts))

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

        # --- Post-turn info (inline, not in expander) ---
        if msg.get("post_turn_logs"):
            _render_post_turn(msg["post_turn_logs"], task_name)

        # Injection indicators
        if msg.get("injections"):
            for inj in msg["injections"]:
                if inj["type"] == "memory_injected":
                    target = inj["data"].get("target", "?")
                    st.caption(f"Memory injected (target: {target})")
                elif inj["type"] == "analysis_addendum_added":
                    st.caption("Analysis addendum added to system prompt")

        # Close the border div
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("---")


def _render_post_turn(post_turn_logs: list[dict], task_name: str):
    """Render post-turn processing info inline (compact)."""
    # Collect the pieces
    verification = None
    evaluation = None
    analysis_logs = []
    edit_decision = None

    for log_entry in post_turn_logs:
        lt = log_entry["log_type"]
        if lt == "verification":
            verification = log_entry["data"]
        elif lt == "answer_evaluation":
            evaluation = log_entry["data"]
        elif lt == "conversation_analysis":
            analysis_logs.append(log_entry["data"])
        elif lt == "edit_decision":
            edit_decision = log_entry["data"]

    # Line 1: categorization + evaluation on a single line
    if verification:
        resp_type = verification.get("response_type", "unknown")
        label = RESPONSE_TYPE_LABELS.get(resp_type, resp_type)

        line = f"**{label}**"
        if evaluation:
            is_correct = evaluation.get("is_correct", False)
            eval_icon = "correct" if is_correct else "incorrect"
            line += f" — evaluation: **{eval_icon}**"

        st.markdown(line)

    # Line 2: extracted answer
    if evaluation:
        extracted = evaluation.get("extracted_answer")
        if extracted:
            if task_name in CODE_BLOCK_TASKS:
                lang = {"code": "python", "database": "sql"}.get(task_name, None)
                if task_name == "code":
                    with st.expander("Extracted Answer", expanded=False):
                        st.code(extracted, language=lang)
                else:
                    st.code(extracted, language=lang)
            else:
                st.markdown(f"Extracted: `{extracted}`")

    # Conversation analysis (for S1/S2) — collapsed
    if analysis_logs:
        with st.expander("Conversation Analysis", expanded=False):
            for data in analysis_logs:
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
                    st.markdown(f"**Needs Edit:** {'Yes' if needs else 'No'}")

    if edit_decision:
        should = edit_decision.get("should_edit", False)
        st.markdown(f"**Edit Decision:** {'Edit' if should else 'Pass'}")


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
    messages = trace_file.get("trace", {}).get("messages", [])
    system_msgs = [m for m in messages if m.get("role") == "system" and m.get("visible", True)]
    if system_msgs:
        st.code(system_msgs[0]["content"], language=None)
    else:
        st.info("No system prompt found.")

    st.subheader("Full Specification Question")
    full_spec = None
    if sample and sample.get("full_spec_q"):
        full_spec = sample["full_spec_q"]
    elif sample and sample.get("question"):
        full_spec = sample["question"]
    else:
        meta = trace_file.get("metadata", {})
        if isinstance(meta, dict) and meta.get("full_spec_q"):
            full_spec = meta["full_spec_q"]

    if full_spec:
        st.markdown(full_spec)
    else:
        st.info("Full spec question not available.")

    st.subheader("Ground Truth Answer")
    gt = None
    if sample and sample.get("ground_truth_a"):
        gt = sample["ground_truth_a"]
    elif sample and sample.get("answer"):
        gt = sample["answer"]
    else:
        meta = trace_file.get("metadata", {})
        if isinstance(meta, dict) and meta.get("ground_truth_a"):
            gt = meta["ground_truth_a"]

    if gt:
        st.code(gt, language=None)
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
    error_entry: Optional[dict],
):
    """Tab 2: Conversation Information."""
    sample_id = trace_file.get("sample_id", "N/A")

    # --- Overview section ---
    st.subheader("Overview")

    col1, col2 = st.columns([3, 1])
    with col1:
        st.code(sample_id, language=None)
    with col2:
        if st.button("Copy Sample ID", key="copy_sample_id"):
            st.toast(f"Sample ID: {sample_id}")

    trace = trace_file.get("trace", {})
    messages = trace.get("messages", [])
    num_resets = trace.get("num_resets", 0)

    user_turns = sum(1 for m in messages if m.get("role") == "user")
    asst_turns = sum(1 for m in messages if m.get("role") == "assistant")
    visible_user = sum(
        1 for m in messages if m.get("role") == "user" and m.get("visible", True)
    )
    visible_asst = sum(
        1 for m in messages if m.get("role") == "assistant" and m.get("visible", True)
    )

    is_correct = trace_file.get("is_correct", False)
    score = trace_file.get("score", "N/A")
    result_str = "Correct" if is_correct else "Incorrect"

    info_lines = [
        f"- **Task:** {trace_file.get('task_name', 'N/A')} · **Experiment:** {trace_file.get('experiment_type', 'N/A')}",
        f"- **Result:** {result_str} (score: {score})",
        f"- **User turns:** {user_turns} (visible: {visible_user}) · **Assistant turns:** {asst_turns} (visible: {visible_asst}) · **Resets:** {num_resets}",
        f"- **Timestamp:** {trace_file.get('timestamp', 'N/A')}",
    ]

    # Models inline
    models = trace_file.get("models", {})
    if models:
        model_parts = [f"**{r.title()}:** {m}" for r, m in models.items()]
        info_lines.append(f"- {' · '.join(model_parts)}")

    st.markdown("\n".join(info_lines))

    # --- Usage Stats section ---
    if result and result.get("usage_stats"):
        st.subheader("Usage Stats")
        stats = result["usage_stats"]
        total_cost = stats.get("total_cost_usd") or result.get("total_cost_usd", 0)
        st.markdown(f"**Total Cost:** ${total_cost:.4f}")

        for role_name in ["user", "assistant", "system", "ctx_editor"]:
            role_stats = stats.get(role_name, {})
            if role_stats and role_stats.get("num_requests", 0) > 0:
                parts = [f"Requests: {role_stats.get('num_requests', 0)}"]
                parts.append(f"In: {role_stats.get('input_tokens', 0):,}")
                parts.append(f"Out: {role_stats.get('output_tokens', 0):,}")
                if role_stats.get("reasoning_tokens"):
                    parts.append(f"Reasoning: {role_stats['reasoning_tokens']:,}")
                if role_stats.get("cached_tokens"):
                    parts.append(f"Cached: {role_stats['cached_tokens']:,}")
                parts.append(f"${role_stats.get('cost_usd', 0):.4f}")
                st.markdown(f"- **{role_name.title()}:** {' · '.join(parts)}")

    # --- Error Attribution section ---
    if error_entry:
        st.subheader("Error Attribution")
        category = error_entry.get("category", "unknown")
        category_label = ERROR_CATEGORY_LABELS.get(category, category)
        correct_present = error_entry.get("correct_answer_present", False)

        st.markdown(
            f"- **Category:** {category_label}\n"
            f"- **Correct answer present in response:** {'Yes' if correct_present else 'No'}"
        )

        explanation = error_entry.get("explanation", "")
        if explanation:
            with st.expander("Attribution Detail (LLM output)", expanded=False):
                st.markdown(explanation)

    # --- Replay Provenance section ---
    provenance = trace.get("provenance")
    if provenance:
        st.subheader("Replay Provenance")
        st.json(provenance)


def render_conversation_tab(trace_file: dict):
    """Tab 3: Conversation Viewer."""
    trace = trace_file.get("trace", {})
    task_name = trace_file.get("task_name", "")
    display_messages = build_display_messages(trace)

    if not display_messages:
        st.info("No messages to display.")
        return

    for idx, msg in enumerate(display_messages):
        render_message_card(msg, idx, task_name=task_name)


def render_memory_tab(
    trace_file: dict,
    result: Optional[dict],
    config: Optional[dict],
):
    """Tab 4: Memory."""
    trace = trace_file.get("trace", {})
    logs = trace.get("logs", [])
    exp_type = trace_file.get("experiment_type", "")

    memory_logs = [l for l in logs if l.get("type") == "memory_injected"]
    has_memory = bool(memory_logs) or "memory" in exp_type.lower()

    if not has_memory:
        st.info("No memory was used in this run.")
        return

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

            st.markdown(
                f"- **Target component:** `{target}` · **Injection location:** {injection_loc}"
                + (f" · {ts}" if ts else "")
            )

    if config and config.get("experiment", {}).get("strategy", {}).get("use_memory"):
        st.subheader("Memory Configuration")
        strategy_cfg = config["experiment"]["strategy"]
        st.markdown(f"**Memory target:** `{strategy_cfg.get('memory_target', 'N/A')}`")

    # Look for cheatsheet content in messages
    messages = trace.get("messages", [])
    for msg in messages:
        content = msg.get("content", "")
        if "<cheatsheet>" in content:
            start = content.find("<cheatsheet>")
            end = content.find("</cheatsheet>")
            if start != -1 and end != -1:
                cheatsheet_content = content[start + len("<cheatsheet>"):end].strip()
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

        # Load run-level data
        results_list = load_results_json(run_dir)
        config = load_config(run_dir)
        metrics = load_metrics(run_dir)
        error_analysis = load_error_analysis(run_dir)

        # --- Run statistics ---
        if metrics:
            exp_name = metrics.get("experiment_name", "unknown")
            correct = metrics.get("correct", 0)
            total = metrics.get("total_attempted", metrics.get("total_samples", 0))
            acc = metrics.get("accuracy", 0)
            st.markdown(f"**{exp_name}**, {correct}/{total} = {acc:.0%}")

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
            data = load_trace(t["path"])
            correct = data.get("is_correct", False)
            icon = "+" if correct else "-"
            label = f"[{icon}] {t['sample_id']}"
            sample_labels.append(label)

        # Session state for navigation
        if "sample_idx" not in st.session_state:
            st.session_state.sample_idx = 0

        st.session_state.sample_idx = max(
            0, min(st.session_state.sample_idx, len(trace_index) - 1)
        )

        # Prev / Next buttons
        col_prev, col_next, col_count = st.columns([1, 1, 1])
        with col_prev:
            if st.button("Prev", disabled=st.session_state.sample_idx == 0):
                st.session_state.sample_idx -= 1
                st.rerun()
        with col_next:
            if st.button(
                "Next",
                disabled=st.session_state.sample_idx >= len(trace_index) - 1,
            ):
                st.session_state.sample_idx += 1
                st.rerun()
        with col_count:
            st.markdown(
                f"**{st.session_state.sample_idx + 1}** / {len(trace_index)}"
            )

        selected_sample_label = st.selectbox(
            "Sample",
            options=sample_labels,
            index=st.session_state.sample_idx,
            key="sample_select",
        )

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
    sample_id = trace_file.get("sample_id", "N/A")
    result = find_result_for_sample(results_list, sample_id)
    error_entry = find_error_for_sample(error_analysis, sample_id)

    # Try to load sample data for shards/full_spec_q
    sample = None
    if config:
        data_file = config.get("task", {}).get("data_file", "")
        if data_file:
            sample = load_sample_data(data_file, sample_id)

    if result and not sample:
        meta = result.get("metadata", {})
        if meta:
            sample = {
                "full_spec_q": meta.get("full_spec_q", ""),
                "ground_truth_a": meta.get("ground_truth_a", ""),
            }

    # Title
    is_correct = trace_file.get("is_correct", False)
    result_icon = "+" if is_correct else "-"
    st.title(f"[{result_icon}] {sample_id}")

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
        render_conversation_info_tab(trace_file, result, config, error_entry)

    with tabs[2]:
        render_conversation_tab(trace_file)

    if has_memory and len(tabs) > 3:
        with tabs[3]:
            render_memory_tab(trace_file, result, config)


if __name__ == "__main__":
    main()
