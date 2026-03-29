"""Build htn20_52 subset: top 20 high-true-negative problems per task from gpt-5.2 logs.

Produces:
  1. data/htn20_52_{task}_subset.json — problem definitions (same format as dev_*_subset.json)
  2. data/baseline_traces_htn20_52/{task}/ — replay traces converted from LiC logs
  3. data/baseline_traces_htn20_52/{task}/conv_manifest.json — maps sample_id -> list of conv_ids
     so callers can select a specific set of conversations to replay

Also checks how the existing dev subsets compare.
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

L3_DIR = Path.home() / "l3_dir"

TASK_FILES = {
    "math": "laban_lic_logs_math_sharded/lazy/lazy_math_t-gpt-5.2.jsonl",
    "code": "laban_lic_logs_code_sharded/lazy/lazy_python_t-gpt-5.2.jsonl",
    "database": "laban_lic_logs_database_sharded/lazy/lazy_database_t-gpt-5.2.jsonl",
    "actions": "laban_lic_logs_actions_sharded/lazy/lazy_apis_t-gpt-5.2.jsonl",
}

DEV_SUBSET_FILES = {
    "math": "data/dev_math_subset.json",
    "code": "data/dev_code_subset.json",
    "database": "data/dev_database_subset.json",
    "actions": "data/dev_actions_subset.json",
}

TOP_N = 20


# ---------------------------------------------------------------------------
# Task ID mapping
# ---------------------------------------------------------------------------

def lic_to_qa(tid: str) -> str:
    if tid.startswith("LazyGSM8K/"): return tid.replace("LazyGSM8K/", "sharded-GSM8K/")
    if tid.startswith("LazyBFCL/"): return tid.replace("LazyBFCL/", "sharded-BFCL/")
    if tid.startswith("Lazy-HumanEval/"): return tid.replace("Lazy-HumanEval/", "sharded-HumanEval/")
    if tid.startswith("livecodebench/"): return tid.replace("livecodebench/", "sharded-livecodebench/")
    if tid.startswith("lazy-"): return tid.replace("lazy-", "sharded-", 1)
    return tid


def qa_to_trace_filename(qa_key: str) -> str:
    """Convert qa_key to a safe filename for trace files."""
    return qa_key.replace("/", "_") + ".json"


# ---------------------------------------------------------------------------
# Convert LiC trace to our replay trace format
# ---------------------------------------------------------------------------

def convert_lic_trace_to_replay(conv: dict, qa_key: str, task_name: str) -> dict:
    """Convert a LiC log conversation to our baseline trace format.

    Our format (from replay.py):
      sample_id, task_name, experiment_type, is_correct, score, models, timestamp,
      trace: { messages: [{role, content, visible}], logs: [{type, data}], num_resets }
    """
    lic_trace = conv["trace"]

    messages = []
    logs = []

    for entry in lic_trace:
        role = entry.get("role")
        content = entry.get("content", "")

        if role == "log":
            # Convert LiC log format to our log format
            log_content = content if isinstance(content, dict) else {}
            log_type = log_content.get("type", "")

            if log_type == "hint_revealed":
                logs.append({
                    "type": "shard_revealed",
                    "data": {"shard_id": log_content.get("hint_id", 0)},
                })
            elif log_type == "system-verification":
                response = log_content.get("response", {})
                resp_type = response.get("response_type", "")
                logs.append({
                    "type": "verification",
                    "data": {
                        "response_type": resp_type,
                        "is_answer_attempt": resp_type == "answer_attempt",
                    },
                })
            elif log_type == "answer-evaluation":
                logs.append({
                    "type": "answer_evaluation",
                    "data": {
                        "extracted_answer": log_content.get("exact_answer", ""),
                        "is_correct": log_content.get("is_correct"),
                        "score": log_content.get("score", 0.0),
                    },
                })
        elif role in ("system", "user", "assistant"):
            messages.append({
                "role": role,
                "content": content,
                "visible": True,
            })

    score = conv.get("score", 0.0)
    is_correct_val = score is not None and float(score) == 1.0

    return {
        "sample_id": qa_key,
        "task_name": task_name,
        "experiment_type": "lic_baseline",
        "is_correct": is_correct_val,
        "score": float(score) if score is not None else 0.0,
        "models": {
            "assistant": conv.get("assistant_model", "t-gpt-5.2"),
            "user": conv.get("user_model", "unknown"),
            "system": conv.get("system_model", "unknown"),
        },
        "timestamp": conv["trace"][-1].get("timestamp", "") if conv["trace"] else "",
        "lic_conv_id": conv["conv_id"],  # provenance: original LiC conversation ID
        "trace": {
            "messages": messages,
            "logs": logs,
            "num_resets": 0,
        },
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # Load hard problems ranking
    with open(PROJECT_ROOT / "outputs/lic_false_negative_analysis/hard_problems.json") as f:
        hard_problems = json.load(f)

    # Load QA metadata for building subset files
    with open(PROJECT_ROOT / "data/question_id_to_full_spec_qa.json") as f:
        qa_metadata = json.load(f)

    # Load dev subsets for reference format
    dev_subsets = {}
    for task, path in DEV_SUBSET_FILES.items():
        full_path = PROJECT_ROOT / path
        if full_path.exists():
            with open(full_path) as f:
                dev_subsets[task] = {s["task_id"]: s for s in json.load(f)}

    # Load all LiC conversations keyed by (task_id, conv_id)
    print("Loading LiC conversations...")
    lic_convs: dict[str, list[dict]] = defaultdict(list)
    for task_name, rel_path in TASK_FILES.items():
        filepath = L3_DIR / rel_path
        with open(filepath) as f:
            for line in f:
                if line.strip():
                    conv = json.loads(line)
                    conv["_task_name"] = task_name
                    lic_convs[conv["task_id"]].append(conv)

    # Load user sim sufficiency results
    with open(PROJECT_ROOT / "outputs/lic_false_negative_analysis/user_sim_sufficiency.json") as f:
        sufficiency = json.load(f)

    # Process each task
    traces_base = PROJECT_ROOT / "data" / "baseline_traces_htn20_52"

    for task_name in ["math", "code", "database", "actions"]:
        print(f"\n{'='*60}")
        print(f"  {task_name.upper()}")
        print(f"{'='*60}")

        items = hard_problems[task_name]
        top_items = items[:TOP_N]

        print(f"  Top {len(top_items)} problems by true negative count:")
        print(f"  {'task_id':<45s} TN  FN  OK")
        for item in top_items:
            print(f"  {item['task_id']:<45s} {item['true_negatives']:2d}  {item['false_negatives']:2d}  {item['correct']:2d}")

        # 1. Build subset JSON (same format as dev_*_subset.json)
        subset_samples = []
        dev_format = dev_subsets.get(task_name, {})

        for item in top_items:
            qa_key = item["qa_key"]
            lic_tid = item["task_id"]

            # Try to get full sample from dev subset first (has all fields)
            if qa_key in dev_format:
                sample = dict(dev_format[qa_key])  # copy
            else:
                # Build minimal sample from QA metadata + LiC data
                meta = qa_metadata.get(qa_key, {})
                sample = {
                    "task_id": qa_key,
                    "task": task_name,
                    "full_spec_q": meta.get("full_spec_q", ""),
                    "ground_truth_a": meta.get("ground_truth_a", ""),
                }

                # Try to get shards from a LiC conversation
                convs = lic_convs.get(lic_tid, [])
                if convs:
                    # Extract shards from trace log entries
                    shards = []
                    trace = convs[0]["trace"]
                    user_msgs = [e for e in trace if e.get("role") == "user"]
                    for i, msg in enumerate(user_msgs, 1):
                        shards.append({"shard_id": i, "shard": msg.get("content", "").strip()})
                    sample["shards"] = shards

                # Add task-specific fields
                if task_name == "math":
                    sample["question"] = meta.get("full_spec_q", "")
                    sample["answer"] = meta.get("ground_truth_a", "")
                elif task_name == "code":
                    sample["prompt"] = meta.get("full_spec_q", "")
                elif task_name == "database":
                    sample["fully_specified_question"] = meta.get("full_spec_q", "")
                    sample["reference_sql"] = meta.get("ground_truth_a", "")

            # Annotate with TN stats
            sample["htn20_52_stats"] = {
                "true_negatives": item["true_negatives"],
                "false_negatives": item["false_negatives"],
                "correct": item["correct"],
            }

            subset_samples.append(sample)

        subset_path = PROJECT_ROOT / "data" / f"htn20_52_{task_name}_subset.json"
        with open(subset_path, "w") as f:
            json.dump(subset_samples, f, indent=2)
        print(f"\n  Wrote {len(subset_samples)} samples to {subset_path.relative_to(PROJECT_ROOT)}")

        # 2. Convert LiC conversations to replay traces
        traces_dir = traces_base / task_name
        traces_dir.mkdir(parents=True, exist_ok=True)

        conv_manifest: dict[str, list[dict]] = {}  # qa_key -> list of {conv_id, index, is_correct, user_sim_sufficient}
        trace_count = 0

        for item in top_items:
            qa_key = item["qa_key"]
            lic_tid = item["task_id"]
            convs = lic_convs.get(lic_tid, [])[:10]

            conv_entries = []
            for idx, conv in enumerate(convs):
                conv_id = conv["conv_id"]
                replay_trace = convert_lic_trace_to_replay(conv, qa_key, task_name)

                # Save each conversation as its own trace file
                # Filename encodes both problem and conversation index for easy selection
                safe_qa = qa_key.replace("/", "_")
                trace_filename = f"{safe_qa}__conv{idx}.json"
                with open(traces_dir / trace_filename, "w") as f:
                    json.dump(replay_trace, f, indent=2)
                trace_count += 1

                # Build manifest entry
                suff = sufficiency.get(lic_tid, {}).get(conv_id, True)
                score = conv.get("score", 0.0)
                is_correct_val = score is not None and float(score) == 1.0
                conv_entries.append({
                    "conv_id": conv_id,
                    "index": idx,
                    "trace_file": trace_filename,
                    "is_correct": is_correct_val,
                    "score": float(score) if score is not None else 0.0,
                    "user_sim_sufficient": suff,
                    "is_true_negative": not is_correct_val and suff,
                })

            conv_manifest[qa_key] = conv_entries

        # Save manifest
        manifest_path = traces_dir / "conv_manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(conv_manifest, f, indent=2)

        # Also save a false_negatives.json so replay.py can auto-skip user-sim-induced
        fn_ids = []
        for qa_key, entries in conv_manifest.items():
            for e in entries:
                if not e["is_correct"] and not e["user_sim_sufficient"]:
                    fn_ids.append(qa_key)
                    break  # one per sample_id is enough
        fn_data = {
            "summary": {
                "user_sim_induced_ids": fn_ids,
            }
        }
        with open(traces_dir / "false_negatives.json", "w") as f:
            json.dump(fn_data, f, indent=2)

        print(f"  Wrote {trace_count} trace files to {traces_dir.relative_to(PROJECT_ROOT)}/")
        print(f"  Manifest: {manifest_path.relative_to(PROJECT_ROOT)}")

    # 3. Print summary of what to select for replay
    print(f"\n{'='*60}")
    print("USAGE")
    print(f"{'='*60}")
    print("""
To run a replay experiment on the htn20_52 subset:

  ctx-editor experiment=context_edit_v2 task=math \\
    task.data_file=data/htn20_52_math_subset.json \\
    execution.replay_source=data/baseline_traces_htn20_52/math

To replay a specific set of conversations (e.g., only conv0 for each problem):
  1. Copy only the desired trace files (e.g., *__conv0.json) into a temp dir
  2. Point execution.replay_source at that dir
  OR use the conv_manifest.json to build a filtered trace set programmatically.

The conv_manifest.json maps each problem to its 10 conversations with metadata:
  - conv_id: original LiC conversation UUID
  - index: 0-9 position in the original run order
  - is_correct, user_sim_sufficient, is_true_negative: for filtering
""")


if __name__ == "__main__":
    main()
