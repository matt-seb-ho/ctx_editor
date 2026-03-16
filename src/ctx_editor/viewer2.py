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

# Rosé Pine palette
RP_BASE = "#191724"
RP_SURFACE = "#1f1d2e"
RP_OVERLAY = "#26233a"
RP_MUTED = "#6e6a86"
RP_SUBTLE = "#908caa"
RP_TEXT = "#e0def4"
RP_LOVE = "#eb6f92"  # red/pink
RP_GOLD = "#f6c177"  # warm yellow
RP_ROSE = "#ebbcba"  # soft pink
RP_PINE = "#31748f"  # teal/blue
RP_FOAM = "#9ccfd8"  # light cyan
RP_IRIS = "#c4a7e7"  # purple

ROLE_COLORS = {
    "system": RP_SUBTLE,
    "user": RP_FOAM,
    "assistant": RP_LOVE,
    "compacted conversation": RP_IRIS,
    "analysis": RP_GOLD,
    "analyst": RP_GOLD,
    "context_edit_output": RP_ROSE,
    "reset_marker": RP_LOVE,
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

# Short labels for experiment types in the sidebar run stats
_EXP_SHORT = {
    "baseline": "baseline",
    "baseline_memory": "baseline+mem",
    "append_analysis": "append",
    "append_analysis_memory": "append+mem",
    "context_edit": "edit",
    "context_edit_memory": "edit+mem",
    "context_edit_v2": "edit",
    "context_edit_v2_memory": "edit+mem",
    "agentic_edit": "agentic",
    "agentic_edit_memory": "agentic+mem",
}


def _short_exp_name(name: str) -> str:
    return _EXP_SHORT.get(name, name)


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
    with open(path, "r") as f:
        return json.load(f)


@st.cache_data
def load_config(run_dir: str) -> Optional[dict]:
    config_path = os.path.join(run_dir, "config.yaml")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    return None


@st.cache_data
def load_metrics(run_dir: str) -> Optional[dict]:
    metrics_path = os.path.join(run_dir, "metrics.json")
    if os.path.exists(metrics_path):
        with open(metrics_path, "r") as f:
            return json.load(f)
    return None


@st.cache_data
def load_results_json(run_dir: str) -> Optional[list[dict]]:
    results_path = os.path.join(run_dir, "results.json")
    if os.path.exists(results_path):
        with open(results_path, "r") as f:
            return json.load(f)
    return None


@st.cache_data
def load_error_analysis(run_dir: str) -> Optional[dict]:
    path = os.path.join(run_dir, "error_analysis.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return None


@st.cache_data
def load_cheatsheet_file(path: str) -> Optional[dict]:
    """Load a cheatsheet JSON file (content, version, history, metadata)."""
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return json.load(f)


def find_result_for_sample(
    results: Optional[list[dict]], sample_id: str
) -> Optional[dict]:
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
    if not error_analysis:
        return None
    normalized = sample_id.replace("_", "/")
    for r in error_analysis.get("results", []):
        if r.get("sample_id") == normalized or r.get("sample_id") == sample_id:
            return r
    return None


def load_sample_data(data_file: str, task_id: str) -> Optional[dict]:
    if not os.path.exists(data_file):
        return None
    with open(data_file, "r") as f:
        data = json.load(f)
    normalized = task_id.replace("_", "/")
    for sample in data:
        if sample.get("task_id") == task_id or sample.get("task_id") == normalized:
            return sample
    return None


def _get_cheatsheet_content(
    trace_data: dict, config: Optional[dict]
) -> Optional[str]:
    """Extract cheatsheet content from either trace messages or the save file.

    For memory_target=assistant/system: cheatsheet is embedded in the system
    message within <cheatsheet>...</cheatsheet> tags.

    For memory_target=analyzer: cheatsheet is passed at runtime to the analyzer
    prompt and NOT stored in trace messages. We load it from cfg.memory.save_path.
    """
    # 1) Check trace messages for <cheatsheet> tags (assistant-target)
    messages = trace_data.get("messages", [])
    for msg in messages:
        content = msg.get("content", "")
        if "<cheatsheet>" in content:
            start = content.find("<cheatsheet>")
            end = content.find("</cheatsheet>")
            if start != -1 and end != -1:
                return content[start + len("<cheatsheet>"):end].strip()

    # 2) Fall back to loading from save_path (analyzer-target)
    if config:
        save_path = config.get("memory", {}).get("save_path")
        if save_path and os.path.exists(save_path):
            cs_data = load_cheatsheet_file(save_path)
            if cs_data and cs_data.get("content"):
                return cs_data["content"]

    return None


def _build_batch_table(cs_data: dict) -> list[dict[str, Any]]:
    """Build the batch/version table from cheatsheet metadata.

    Returns a list of rows: [{batch, samples, version_used, version_after}, ...]
    """
    metadata = cs_data.get("metadata", {})
    rows = []

    # Collect batch entries sorted by key
    batch_keys = sorted(
        [k for k in metadata if k.startswith("batch_update_") or k.startswith("update_")],
        key=lambda k: int("".join(c for c in k if c.isdigit()) or "0"),
    )

    for i, key in enumerate(batch_keys):
        entry = metadata[key]
        batch_num = int("".join(c for c in key if c.isdigit()) or str(i + 1))

        if "sample_ids" in entry:
            sample_ids = entry["sample_ids"]
        elif "sample_id" in entry:
            sample_ids = [entry["sample_id"]]
        else:
            sample_ids = []

        # Shorten sample IDs for display
        short_ids = [sid.split("/")[-1] if "/" in sid else sid for sid in sample_ids]

        rows.append(
            {
                "batch": batch_num,
                "samples": sample_ids,
                "short_ids": ", ".join(short_ids),
                "num_samples": len(sample_ids),
                "version_used": batch_num - 1,
                "version_after": batch_num,
            }
        )

    return rows


def _find_sample_version(
    batch_table: list[dict], sample_id: str
) -> Optional[int]:
    """Find which cheatsheet version was used for a given sample_id."""
    normalized = sample_id.replace("_", "/")
    for row in batch_table:
        if normalized in row["samples"] or sample_id in row["samples"]:
            return row["version_used"]
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

    color = ROLE_COLORS.get(role, RP_SUBTLE)

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
            f'<div style="text-align:center; padding:8px; '
            f"background:{RP_LOVE}18; border:1px solid {RP_LOVE}; "
            f'border-radius:8px; margin:8px 0;">'
            f"<strong>Context Reset #{msg.get('metadata', {}).get('total_resets', '?')}</strong>"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.divider()
        return

    # --- Render card ---
    with st.container():
        # Header line: colored role label + metadata
        header_parts = []
        header_parts.append(
            f'<span style="color:{color}; font-weight:600;">{role_label}</span>'
        )
        if shard_tag:
            header_parts.append(
                f'<code style="font-size:0.85em;">{shard_tag}</code>'
            )
        if vis_tag:
            header_parts.append(
                f'<span style="color:{RP_MUTED}; font-style:italic;">{vis_tag}</span>'
            )
        ts = msg.get("timestamp", "")
        if ts:
            header_parts.append(
                f'<span style="color:{RP_MUTED}; font-size:0.85em;">— {ts}</span>'
            )

        st.markdown(
            f'<div style="border-left:4px solid {color}; padding-left:12px; '
            f'margin-bottom:2px;">'
            f'<p style="margin:4px 0;">{"&nbsp;&nbsp;".join(header_parts)}</p>'
            f"</div>",
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

        # --- Post-turn info (visually distinct box) ---
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

        st.markdown("---")


def _render_post_turn(post_turn_logs: list[dict], task_name: str):
    """Render post-turn processing as an expander.

    Header: categorization + evaluation result (e.g. "Answer Attempt (correct)")
    Body: extracted answer, conversation analysis, edit decision
    """
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

    # Build expander header
    header = ""
    if verification:
        resp_type = verification.get("response_type", "unknown")
        header = RESPONSE_TYPE_LABELS.get(resp_type, resp_type)
        if evaluation:
            is_correct = evaluation.get("is_correct", False)
            header += f" ({'correct' if is_correct else 'incorrect'})"

    if not header:
        header = "Post-turn Processing"

    # Determine if there's body content worth expanding
    has_body = bool(
        (evaluation and evaluation.get("extracted_answer"))
        or analysis_logs
        or edit_decision
    )

    if not has_body:
        # Just show the header as a caption, no expander needed
        st.caption(header)
        return

    with st.expander(header, expanded=False):
        # Extracted answer
        if evaluation:
            extracted = evaluation.get("extracted_answer")
            if extracted:
                if task_name in CODE_BLOCK_TASKS:
                    lang = {"code": "python", "database": "sql"}.get(task_name, None)
                    st.code(extracted, language=lang)
                else:
                    st.markdown(f"Extracted: `{extracted}`")

        # Conversation analysis (for S1/S2)
        if analysis_logs:
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


def render_run_info_tab(
    run_dir: str,
    config: Optional[dict],
    metrics: Optional[dict],
    results_list: Optional[list[dict]],
    trace_index: list[dict],
):
    """Tab: Run-level information (cross-conversation)."""

    # --- Run config summary ---
    st.subheader("Run Configuration")
    if config:
        exp_cfg = config.get("experiment", {})
        model_cfg = config.get("model", {})
        task_cfg = config.get("task", {})
        info = [
            f"- **Experiment:** {exp_cfg.get('name', 'N/A')}",
            f"- **Task:** {task_cfg.get('name', 'N/A')} · **Data:** `{task_cfg.get('data_file', 'N/A')}`",
        ]
        if model_cfg.get("name"):
            info.append(f"- **Model:** {model_cfg['name']}")
        strategy = exp_cfg.get("strategy", {})
        if strategy:
            strat_type = strategy.get("_target_", "").rsplit(".", 1)[-1]
            strat_parts = [f"**Strategy:** {strat_type}"]
            for k in ["min_turns", "max_resets", "use_memory", "memory_target",
                       "analyzer_model"]:
                if k in strategy:
                    strat_parts.append(f"{k}={strategy[k]}")
            info.append(f"- {' · '.join(strat_parts)}")
        st.markdown("\n".join(info))

    # --- Metrics summary ---
    if metrics:
        st.subheader("Metrics")
        correct = metrics.get("correct", 0)
        total = metrics.get("total_attempted", 0)
        acc = metrics.get("accuracy", 0)
        cost = metrics.get("total_cost_usd", 0)
        avg_turns = metrics.get("average_turns", 0)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Accuracy", f"{acc:.0%}", f"{correct}/{total}")
        col2.metric("Avg Turns", f"{avg_turns:.1f}")
        col3.metric("Total Cost", f"${cost:.2f}")
        col4.metric("Samples", str(total))

    # --- Per-sample results table ---
    if results_list:
        st.subheader("Per-Sample Results")
        rows = []
        for r in results_list:
            rows.append({
                "Sample": r.get("sample_id", "?"),
                "Correct": "Y" if r.get("is_correct") else "N",
                "Score": r.get("score", ""),
                "Turns": r.get("num_turns", ""),
                "Cost": f"${r.get('total_cost_usd', 0):.4f}",
                "Answer": (r.get("extracted_answer") or "")[:60],
            })
        st.dataframe(rows, use_container_width=True, hide_index=True)

    # --- Memory batch table ---
    memory_save_path = None
    if config:
        memory_save_path = config.get("memory", {}).get("save_path")

    if memory_save_path and os.path.exists(memory_save_path):
        cs_data = load_cheatsheet_file(memory_save_path)
        if cs_data:
            batch_table = _build_batch_table(cs_data)
            if batch_table:
                st.subheader("Memory Batch Schedule")
                st.markdown(
                    "Each batch runs with the cheatsheet version shown, "
                    "then updates it for the next batch."
                )

                table_rows = []
                for row in batch_table:
                    # Mark correct/incorrect per sample
                    sample_results = []
                    for sid in row["samples"]:
                        r = find_result_for_sample(results_list, sid)
                        if r:
                            mark = "+" if r.get("is_correct") else "-"
                            short = sid.split("/")[-1] if "/" in sid else sid
                            sample_results.append(f"[{mark}] {short}")
                        else:
                            short = sid.split("/")[-1] if "/" in sid else sid
                            sample_results.append(short)

                    table_rows.append({
                        "Batch": row["batch"],
                        "Version Used": f"v{row['version_used']}",
                        "Version After": f"v{row['version_after']}",
                        "Samples": ", ".join(sample_results),
                    })

                st.dataframe(table_rows, use_container_width=True, hide_index=True)

    # --- Error attribution summary ---
    error_analysis = load_error_analysis(run_dir)
    if error_analysis:
        st.subheader("Error Attribution Summary")
        summary = error_analysis.get("summary", {})
        by_cat = summary.get("by_category", {})
        if by_cat:
            cat_rows = []
            for cat, count in sorted(by_cat.items(), key=lambda x: -x[1]):
                label = ERROR_CATEGORY_LABELS.get(cat, cat)
                cat_rows.append({"Category": label, "Count": count})
            st.dataframe(cat_rows, use_container_width=True, hide_index=True)

        fn = summary.get("false_negatives")
        if fn is not None:
            st.markdown(f"**Estimated false negatives:** {fn}")


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
    """Tab 4: Memory.

    Memory content comes from two sources depending on memory_target:
    - assistant/system target: <cheatsheet> tags embedded in the system message
    - analyzer target: loaded from cfg.memory.save_path (not in trace messages)
    """
    trace = trace_file.get("trace", {})
    logs = trace.get("logs", [])
    exp_type = trace_file.get("experiment_type", "")

    memory_logs = [l for l in logs if l.get("type") == "memory_injected"]
    has_memory = bool(memory_logs) or "memory" in exp_type.lower()

    if not has_memory:
        st.info("No memory was used in this run.")
        return

    # --- Memory configuration ---
    memory_target = None
    memory_save_path = None
    if config:
        strategy_cfg = config.get("experiment", {}).get("strategy", {})
        memory_cfg = config.get("memory", {})
        memory_target = (
            strategy_cfg.get("memory_target")
            or memory_cfg.get("target")
        )
        memory_save_path = memory_cfg.get("save_path")

    st.subheader("Memory Configuration")

    if memory_target:
        if memory_target in ("assistant", "system"):
            injection_loc = "System prompt (prepended to assistant's system message)"
        elif memory_target == "analyzer":
            injection_loc = "Comparison prompt (injected into analyzer's context)"
        else:
            injection_loc = f"Unknown: {memory_target}"
        st.markdown(
            f"- **Target:** `{memory_target}` · **Injection:** {injection_loc}"
        )
    if memory_save_path:
        st.markdown(f"- **Save path:** `{memory_save_path}`")

    if memory_logs:
        for ml in memory_logs:
            ts = ml.get("timestamp", "")
            target = ml["data"].get("target", "?")
            st.caption(f"Injected at {ts} (target: {target})")

    # --- Load cheatsheet data and determine version used ---
    cs_data = None
    if memory_save_path and os.path.exists(memory_save_path):
        cs_data = load_cheatsheet_file(memory_save_path)

    batch_table = _build_batch_table(cs_data) if cs_data else []
    sample_id = trace_file.get("sample_id", "")
    sample_version = _find_sample_version(batch_table, sample_id) if batch_table else None

    # --- Cheatsheet content for this sample ---
    st.subheader("Cheatsheet Content")

    if sample_version is not None:
        st.markdown(f"**Version used for this sample:** v{sample_version}")
        # Get the content at that version
        history = cs_data.get("history", []) if cs_data else []
        if sample_version == 0:
            version_content = history[0] if history else ""
        elif sample_version < len(history):
            version_content = history[sample_version]
        else:
            version_content = cs_data.get("content", "") if cs_data else ""

        if version_content:
            st.code(version_content, language=None)
        else:
            st.info("v0 — empty cheatsheet (no prior learning)")
    else:
        # Fall back to extracting from trace or showing final version
        cheatsheet = _get_cheatsheet_content(trace, config)
        if cheatsheet:
            st.code(cheatsheet, language=None)
        else:
            st.info(
                "Cheatsheet content not found. "
                "For analyzer-target runs, content is only available if "
                "memory.save_path points to an existing cheatsheet JSON file."
            )

    # --- All versions (expandable) ---
    if cs_data:
        history = cs_data.get("history", [])
        final_version = cs_data.get("version", 0)
        st.subheader("All Versions")
        for i in range(final_version + 1):
            if i < len(history):
                content = history[i]
            elif i == final_version:
                content = cs_data.get("content", "")
            else:
                content = ""
            is_current = (sample_version == i) if sample_version is not None else False
            label = f"v{i}"
            if is_current:
                label += " (used for this sample)"
            if not content:
                label += " (empty)"
            with st.expander(label, expanded=is_current):
                if content:
                    st.code(content, language=None)
                else:
                    st.caption("Empty — no cheatsheet content at this version.")


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

        for r in runs:
            r["resolved"] = resolve_path(r["path"])

        run_options = {r["label"]: r for r in runs}
        selected_label = st.selectbox(
            "Select Run",
            options=list(run_options.keys()),
            key="selected_run",
        )
        selected_run = run_options[selected_label]
        run_dir = selected_run["resolved"]

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

        # --- Run statistics (short label) ---
        if metrics:
            exp_name = _short_exp_name(metrics.get("experiment_name", "unknown"))
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

        sample_labels = []
        for i, t in enumerate(trace_index):
            data = load_trace(t["path"])
            correct = data.get("is_correct", False)
            icon = "+" if correct else "-"
            label = f"[{icon}] {t['sample_id']}"
            sample_labels.append(label)

        if "sample_idx" not in st.session_state:
            st.session_state.sample_idx = 0

        st.session_state.sample_idx = max(
            0, min(st.session_state.sample_idx, len(trace_index) - 1)
        )

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

    trace_file = load_trace(selected_trace_info["path"])
    sample_id = trace_file.get("sample_id", "N/A")
    result = find_result_for_sample(results_list, sample_id)
    error_entry = find_error_for_sample(error_analysis, sample_id)

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

    is_correct = trace_file.get("is_correct", False)
    result_icon = "+" if is_correct else "-"
    st.title(f"[{result_icon}] {sample_id}")

    trace = trace_file.get("trace", {})
    exp_type = trace_file.get("experiment_type", "")
    has_memory = any(
        l.get("type") == "memory_injected" for l in trace.get("logs", [])
    ) or "memory" in exp_type.lower()

    tab_names = ["Question Info", "Conversation Info", "Conversation", "Run Info"]
    if has_memory:
        tab_names.append("Memory")

    tabs = st.tabs(tab_names)

    with tabs[0]:
        render_question_tab(trace_file, sample, config)

    with tabs[1]:
        render_conversation_info_tab(trace_file, result, config, error_entry)

    with tabs[2]:
        render_conversation_tab(trace_file)

    with tabs[3]:
        render_run_info_tab(run_dir, config, metrics, results_list, trace_index)

    if has_memory and len(tabs) > 4:
        with tabs[4]:
            render_memory_tab(trace_file, result, config)


if __name__ == "__main__":
    main()
