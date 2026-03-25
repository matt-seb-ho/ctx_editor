#!/usr/bin/env python3
"""Dump per-problem analysis for actions samples where omit/concat beat S1.5+accumulate."""

import json
import os
from pathlib import Path

OUTPUT_DIR = Path("/tmp/actions_analysis")

# Directories
S15_ACC_DIR = Path("outputs/2026-03-21/08-06-56/traces/actions/s15")
OMIT_DIR = Path("outputs/2026-03-21/05-15-08/traces/actions/omit_assistant")
CONCAT_DIR = Path("outputs/2026-03-21/05-15-09/traces/actions/concatenate_user")
S1_DIR = Path("outputs/2026-03-16/20-29-27/traces")  # S1 source (has analysis logs)
DATA_FILE = Path("data/dev_actions_subset.json")


def load_traces(d):
    traces = {}
    for f in sorted(d.rglob("*.json")):
        with open(f) as fh:
            t = json.load(fh)
        sid = t.get("sample_id", f.stem)
        traces[sid] = t
    return traces


def load_samples(path):
    with open(path) as f:
        data = json.load(f)
    return {s["task_id"]: s for s in data}


def get_score(trace):
    if trace is None:
        return None
    return trace.get("score", trace.get("is_correct", 0))


def fmt_messages(messages):
    """Format a list of message dicts as readable markdown."""
    parts = []
    for m in messages:
        role = m.get("role", "unknown")
        content = m.get("content", "")
        parts.append(f"**[{role}]**\n\n{content}")
    return "\n\n---\n\n".join(parts)


def extract_analysis_from_s1(s1_trace):
    """Extract conversation_analysis from S1 trace logs."""
    logs = s1_trace.get("trace", {}).get("logs", [])
    for log in reversed(logs):
        if log.get("type") == "conversation_analysis":
            return log["data"]
    return None


def extract_conversation_from_s1(s1_trace):
    """Extract full conversation from S1 trace."""
    messages = s1_trace.get("trace", {}).get("messages", [])
    parts = []
    for m in messages:
        if not m.get("visible", True):
            continue
        role = m.get("role", "unknown")
        content = m.get("content", "")
        parts.append(f"**[{role}]**\n\n{content}")
    return "\n\n---\n\n".join(parts)


def main():
    s15_acc = load_traces(S15_ACC_DIR)
    omit = load_traces(OMIT_DIR)
    concat = load_traces(CONCAT_DIR)
    s1 = load_traces(S1_DIR)
    samples = load_samples(DATA_FILE)

    # Find samples where omit OR concat got it right but S1.5+acc got it wrong
    failures = []
    all_sids = sorted(set(list(s15_acc.keys()) + list(omit.keys()) + list(concat.keys())))

    for sid in all_sids:
        acc_score = get_score(s15_acc.get(sid))
        omit_score = get_score(omit.get(sid))
        concat_score = get_score(concat.get(sid))

        if acc_score == 0 and (omit_score == 1 or concat_score == 1):
            failures.append(sid)

    print(f"Found {len(failures)} samples where omit/concat beat S1.5+accumulate")

    for sid in failures:
        safe_name = sid.replace("/", "_")
        prob_dir = OUTPUT_DIR / safe_name
        prob_dir.mkdir(parents=True, exist_ok=True)

        acc_trace = s15_acc.get(sid, {})
        omit_trace = omit.get(sid, {})
        concat_trace = concat.get(sid, {})
        s1_trace = s1.get(sid, {})
        sample = samples.get(sid, {})

        # 1. Question info
        question = sample.get("fully_specified_question", sample.get("question", "N/A"))
        if isinstance(question, list):
            # FSQ is nested [[{role, content}]] — extract the content
            try:
                question = question[0][0]["content"]
            except (IndexError, KeyError, TypeError):
                question = json.dumps(question, indent=2)
        ground_truth = sample.get("ground_truth_a", sample.get("reference_answer", sample.get("answer", "N/A")))
        if isinstance(ground_truth, (list, dict)):
            ground_truth = json.dumps(ground_truth, indent=2)

        question_md = f"# {sid}\n\n"
        question_md += f"## Single-Turn Question\n\n{question}\n\n"
        question_md += f"## Expected Answer (Ground Truth Calls)\n\n```json\n{ground_truth}\n```\n\n"
        question_md += "## Scores\n\n"
        question_md += f"| Strategy | Score |\n|---|---|\n"
        question_md += f"| S1.5 + accumulate | {get_score(acc_trace)} |\n"
        question_md += f"| Omit assistant | {get_score(omit_trace)} |\n"
        question_md += f"| Concatenate user | {get_score(concat_trace)} |\n"

        with open(prob_dir / "question_info.md", "w") as f:
            f.write(question_md)

        # 2. S1.5+accumulate conversation log (what the assistant saw + its response)
        conv_md = f"# S1.5 + Accumulate — Conversation Log\n\n## {sid}\n\n"
        messages_sent = acc_trace.get("messages_sent", [])
        if messages_sent:
            conv_md += "## Messages Sent to Assistant\n\n"
            conv_md += fmt_messages(messages_sent)
        conv_md += f"\n\n## Assistant Response\n\n```\n{acc_trace.get('assistant_response', 'N/A')}\n```\n\n"
        conv_md += f"## Extracted Answer\n\n```\n{acc_trace.get('extracted_answer', 'N/A')}\n```\n"

        with open(prob_dir / "conversation_log.md", "w") as f:
            f.write(conv_md)

        # 3. Analysis (full, untruncated from S1 trace)
        analysis_md = f"# Analysis — {sid}\n\n"

        s1_analysis = extract_analysis_from_s1(s1_trace)
        if s1_analysis:
            analysis_md += f"## Task Spec (User Intent)\n\n{s1_analysis.get('user_intent', 'N/A')}\n\n"
            analysis_md += f"## Aligned (What Looks Right)\n\n{s1_analysis.get('aligned', 'N/A')}\n\n"
            analysis_md += f"## Issues\n\n{s1_analysis.get('issues', 'N/A')}\n\n"
            analysis_md += f"## Needs Edit\n\n{s1_analysis.get('needs_edit', 'N/A')}\n\n"
        else:
            # Fallback to S1.5+acc trace (may be truncated)
            analysis_used = acc_trace.get("analysis_used", {})
            analysis_md += f"## Task Spec (User Intent)\n\n{analysis_used.get('user_intent', 'N/A')}\n\n"
            analysis_md += f"## Aligned (What Looks Right)\n\n{analysis_used.get('aligned', 'N/A')}\n\n"
            analysis_md += f"## Issues\n\n{analysis_used.get('issues', 'N/A')}\n\n"
            analysis_md += f"## Needs Edit\n\n{analysis_used.get('needs_edit', 'N/A')}\n\n"
            analysis_md += "*Note: Using truncated analysis from S1.5 trace (S1 trace not found)*\n\n"

        with open(prob_dir / "analysis.md", "w") as f:
            f.write(analysis_md)

        # 4. Full conversation (from S1 trace — the original multi-turn conversation)
        full_conv_md = f"# Full Conversation — {sid}\n\n"
        full_conv_md += extract_conversation_from_s1(s1_trace)

        with open(prob_dir / "full_conversation.md", "w") as f:
            f.write(full_conv_md)

        print(f"  {sid}: acc={get_score(acc_trace)} omit={get_score(omit_trace)} concat={get_score(concat_trace)}")

    print(f"\nOutput written to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
