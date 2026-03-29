"""Post-hoc false negative analysis on LiC original repo logs for gpt-5.2.

Loads gpt-5.2 sharded conversations from ~/l3_dir, takes first 3 conversations
per question, and for each incorrect conversation:
  1. Runs user simulator sufficiency check (LLM, using gpt-5 as judge)
  2. Checks whether an answer was extracted in the last turn (programmatic)

Outputs:
  - user_sim_sufficiency.json: problem_id -> conv_id -> bool (sufficient=True means true negative)
  - answer_extracted.json: problem_id -> conv_id -> bool
  - adjusted_accuracy.json: corrected accuracy numbers
"""

import asyncio
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from tqdm.asyncio import tqdm_asyncio

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

from ctx_editor.models import LoadBalancerConfig, get_model_client
from ctx_editor.identify_false_negatives import USER_SIM_SUFFICIENCY_PROMPT

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

L3_DIR = Path.home() / "l3_dir"
ANALYSIS_MODEL = "gpt-5"
CONVS_PER_QUESTION = 3
CONCURRENCY = 30  # aggressive parallelism across 4 endpoints

TASK_FILES = {
    "math": "laban_lic_logs_math_sharded/lazy/lazy_math_t-gpt-5.2.jsonl",
    "code": "laban_lic_logs_code_sharded/lazy/lazy_python_t-gpt-5.2.jsonl",
    "database": "laban_lic_logs_database_sharded/lazy/lazy_database_t-gpt-5.2.jsonl",
    "actions": "laban_lic_logs_actions_sharded/lazy/lazy_apis_t-gpt-5.2.jsonl",
}

LOAD_BALANCER_CONFIG = {
    "endpoints": [
        {
            "name": "dl-openai-1",
            "type": "azure",
            "endpoint": "https://dl-openai-1.openai.azure.com",
            "api_version": "2024-10-21",
            "auth_method": "azure_cli",
            "max_concurrent": 10,
            "priority": 1,
            "supported_models": ["gpt-5"],
        },
        {
            "name": "dl-openai-3",
            "type": "azure",
            "endpoint": "https://dl-openai-3.openai.azure.com",
            "api_version": "2024-10-21",
            "auth_method": "azure_cli",
            "max_concurrent": 10,
            "priority": 1,
            "supported_models": ["gpt-5"],
        },
        {
            "name": "fxdata-eastus2",
            "type": "azure",
            "endpoint": "https://fxdata-eastus2.openai.azure.com",
            "api_version": "2024-10-21",
            "auth_method": "azure_cli",
            "max_concurrent": 10,
            "priority": 1,
            "supported_models": ["gpt-5"],
        },
        {
            "name": "fxdata-shared",
            "type": "azure",
            "endpoint": "https://fxdata-shared.openai.azure.com",
            "api_version": "2024-10-21",
            "auth_method": "azure_cli",
            "max_concurrent": 10,
            "priority": 1,
            "supported_models": ["gpt-5"],
        },
    ],
    "routing_strategy": "round_robin",
    "fallback_enabled": True,
    "max_retries_per_endpoint": 2,
}


# ---------------------------------------------------------------------------
# Task ID mapping: LiC log format -> question_id_to_full_spec_qa.json format
# ---------------------------------------------------------------------------

def lic_task_id_to_qa_key(task_id: str) -> str:
    """Convert LiC log task_id to the key used in question_id_to_full_spec_qa.json.

    LiC logs:                          QA json:
      LazyGSM8K/X                  ->  sharded-GSM8K/X
      LazyBFCL/parallel_X          ->  sharded-BFCL/parallel_X
      Lazy-HumanEval/X             ->  sharded-HumanEval/X
      livecodebench/X              ->  sharded-livecodebench/X
      lazy-spider-val-X            ->  sharded-spider-val-X
    """
    if task_id.startswith("LazyGSM8K/"):
        return task_id.replace("LazyGSM8K/", "sharded-GSM8K/")
    if task_id.startswith("LazyBFCL/"):
        return task_id.replace("LazyBFCL/", "sharded-BFCL/")
    if task_id.startswith("Lazy-HumanEval/"):
        return task_id.replace("Lazy-HumanEval/", "sharded-HumanEval/")
    if task_id.startswith("livecodebench/"):
        return task_id.replace("livecodebench/", "sharded-livecodebench/")
    if task_id.startswith("lazy-"):
        return task_id.replace("lazy-", "sharded-", 1)
    return task_id


# ---------------------------------------------------------------------------
# LiC trace helpers
# ---------------------------------------------------------------------------

def extract_user_messages(trace: list[dict]) -> str:
    """Format all user-role messages from a LiC trace into numbered turns."""
    user_msgs = [e for e in trace if e.get("role") == "user"]
    if not user_msgs:
        return "(no user messages found)"
    lines = []
    for i, m in enumerate(user_msgs, 1):
        content = m.get("content", "").strip()
        lines.append(f"[Turn {i}] {content}")
    return "\n\n".join(lines)


def extract_system_message(trace: list[dict]) -> str:
    """Extract the system message from a LiC trace."""
    for entry in trace:
        if entry.get("role") == "system":
            return entry.get("content", "").strip()
    return ""


def get_last_verification_type(trace: list[dict]) -> str:
    """Get the response_type from the last system-verification log entry."""
    for entry in reversed(trace):
        if entry.get("role") == "log":
            content = entry.get("content", {})
            if isinstance(content, dict) and content.get("type") == "system-verification":
                return content.get("response", {}).get("response_type", "")
    return ""


def get_answer_extracted(trace: list[dict]) -> bool:
    """Check if a non-empty answer was extracted in the answer-evaluation log."""
    for entry in reversed(trace):
        if entry.get("role") == "log":
            content = entry.get("content", {})
            if isinstance(content, dict) and content.get("type") == "answer-evaluation":
                exact_answer = content.get("exact_answer", "")
                return bool(exact_answer and str(exact_answer).strip())
    return False


def is_correct(conv: dict) -> bool:
    """Determine if a conversation was scored as correct."""
    score = conv.get("score", 0)
    return score is not None and float(score) == 1.0


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

def load_conversations() -> dict[str, list[dict]]:
    """Load all gpt-5.2 conversations grouped by task_id, first 3 per question."""
    by_task_id: dict[str, list[dict]] = defaultdict(list)

    for task_name, rel_path in TASK_FILES.items():
        filepath = L3_DIR / rel_path
        if not filepath.exists():
            print(f"WARNING: {filepath} not found, skipping {task_name}")
            continue
        with open(filepath) as f:
            for line in f:
                if not line.strip():
                    continue
                conv = json.loads(line)
                conv["_task_name"] = task_name  # annotate for later
                by_task_id[conv["task_id"]].append(conv)

    # Take first 3 per question
    result = {}
    for task_id, convs in by_task_id.items():
        result[task_id] = convs[:CONVS_PER_QUESTION]

    return result


def load_qa_metadata() -> dict[str, dict]:
    """Load question_id_to_full_spec_qa.json."""
    qa_path = PROJECT_ROOT / "data" / "question_id_to_full_spec_qa.json"
    with open(qa_path) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# LLM analysis
# ---------------------------------------------------------------------------

async def check_user_sim_sufficiency(
    conv: dict,
    qa_key: str,
    qa_metadata: dict[str, dict],
    model_client,
    sem: asyncio.Semaphore,
) -> dict:
    """Run user sim sufficiency check on a single incorrect conversation."""
    conv_id = conv["conv_id"]
    task_id = conv["task_id"]
    trace = conv["trace"]

    meta = qa_metadata.get(qa_key, {})
    full_spec_q = meta.get("full_spec_q", "")
    ground_truth_a = meta.get("ground_truth_a", "")

    if not full_spec_q:
        return {
            "conv_id": conv_id,
            "task_id": task_id,
            "qa_key": qa_key,
            "error": f"No full_spec_q found for qa_key={qa_key}",
            "user_sim_sufficient": True,  # default: don't exclude on error
            "missing_elements": [],
            "explanation": "",
        }

    user_messages_str = extract_user_messages(trace)
    system_message_str = extract_system_message(trace)

    prompt = USER_SIM_SUFFICIENCY_PROMPT.format(
        full_spec_q=full_spec_q,
        ground_truth_a=ground_truth_a or "(not available)",
        system_message=system_message_str or "(none)",
        user_messages=user_messages_str,
    )

    async with sem:
        try:
            resp = await model_client.generate_json(
                messages=[{"role": "user", "content": prompt}],
                model=ANALYSIS_MODEL,
                temperature=0.0,
            )
            llm_result = resp.content
            return {
                "conv_id": conv_id,
                "task_id": task_id,
                "qa_key": qa_key,
                "error": "",
                "user_sim_sufficient": llm_result.get("sufficient", True),
                "missing_elements": llm_result.get("missing_elements", []),
                "explanation": llm_result.get("explanation", ""),
            }
        except Exception as e:
            return {
                "conv_id": conv_id,
                "task_id": task_id,
                "qa_key": qa_key,
                "error": str(e),
                "user_sim_sufficient": True,
                "missing_elements": [],
                "explanation": "",
            }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    print("Loading conversations...")
    convs_by_task_id = load_conversations()
    qa_metadata = load_qa_metadata()

    total_questions = len(convs_by_task_id)
    total_convs = sum(len(v) for v in convs_by_task_id.values())
    print(f"Loaded {total_convs} conversations across {total_questions} questions (first {CONVS_PER_QUESTION} per question)")

    # Separate correct vs incorrect, build programmatic checks
    incorrect_convs = []  # (conv, qa_key) tuples for LLM analysis
    user_sim_sufficiency: dict[str, dict[str, bool]] = {}  # task_id -> conv_id -> bool
    answer_extracted: dict[str, dict[str, bool]] = {}  # task_id -> conv_id -> bool

    # Track per-task stats
    task_stats: dict[str, dict] = defaultdict(lambda: {"total": 0, "correct": 0, "incorrect": 0})

    qa_key_miss = 0
    for task_id, convs in convs_by_task_id.items():
        qa_key = lic_task_id_to_qa_key(task_id)
        if qa_key not in qa_metadata:
            qa_key_miss += 1

        user_sim_sufficiency[task_id] = {}
        answer_extracted[task_id] = {}

        task_name = convs[0]["_task_name"]

        for conv in convs:
            conv_id = conv["conv_id"]
            task_stats[task_name]["total"] += 1

            # Programmatic: answer extracted?
            ans_extracted = get_answer_extracted(conv["trace"])
            answer_extracted[task_id][conv_id] = ans_extracted

            if is_correct(conv):
                task_stats[task_name]["correct"] += 1
                # Correct conversations don't need sufficiency analysis
                # Mark as sufficient by default (they got it right)
                user_sim_sufficiency[task_id][conv_id] = True
            else:
                task_stats[task_name]["incorrect"] += 1
                incorrect_convs.append((conv, qa_key))
                # Will be filled by LLM analysis below

    if qa_key_miss:
        print(f"WARNING: {qa_key_miss} task_ids had no match in question_id_to_full_spec_qa.json")

    print(f"\nPer-task breakdown (first {CONVS_PER_QUESTION} runs):")
    for task_name in sorted(task_stats):
        s = task_stats[task_name]
        raw_acc = s["correct"] / s["total"] if s["total"] else 0
        print(f"  {task_name:10s}: {s['correct']}/{s['total']} correct ({raw_acc:.1%}), {s['incorrect']} incorrect to analyze")

    print(f"\nTotal incorrect conversations to analyze: {len(incorrect_convs)}")

    if not incorrect_convs:
        print("Nothing to analyze!")
        return

    # Run LLM analysis
    lb_config = LoadBalancerConfig.from_dict(LOAD_BALANCER_CONFIG)
    model_client = get_model_client(model_name=ANALYSIS_MODEL, load_balancer_config=lb_config)
    sem = asyncio.Semaphore(CONCURRENCY)

    tasks = [
        check_user_sim_sufficiency(conv, qa_key, qa_metadata, model_client, sem)
        for conv, qa_key in incorrect_convs
    ]

    print(f"\nRunning user sim sufficiency checks with {ANALYSIS_MODEL} (concurrency={CONCURRENCY})...")
    results = await tqdm_asyncio.gather(*tasks, desc="Sufficiency checks")

    # Fill in user_sim_sufficiency dict with LLM results
    errors = 0
    false_negatives = 0
    for r in results:
        task_id = r["task_id"]
        conv_id = r["conv_id"]
        user_sim_sufficiency[task_id][conv_id] = r["user_sim_sufficient"]
        if r["error"]:
            errors += 1
        if not r["user_sim_sufficient"]:
            false_negatives += 1

    print(f"\nLLM analysis complete. Errors: {errors}, False negatives (user_sim_induced): {false_negatives}")

    # ---------------------------------------------------------------------------
    # Compute adjusted accuracy
    # ---------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("ADJUSTED ACCURACY (3-run, excluding user-sim-induced false negatives)")
    print("=" * 70)

    # Per-task adjusted accuracy
    overall_correct = 0
    overall_total = 0
    overall_false_neg = 0

    for task_name in sorted(task_stats):
        task_correct = 0
        task_total = 0
        task_false_neg = 0

        for task_id, convs in convs_by_task_id.items():
            if convs[0]["_task_name"] != task_name:
                continue
            for conv in convs:
                conv_id = conv["conv_id"]
                task_total += 1
                if is_correct(conv):
                    task_correct += 1
                else:
                    sufficient = user_sim_sufficiency.get(task_id, {}).get(conv_id, True)
                    if not sufficient:
                        task_false_neg += 1

        raw_acc = task_correct / task_total if task_total else 0
        adj_denom = task_total - task_false_neg
        adj_acc = task_correct / adj_denom if adj_denom else 0

        print(f"\n  {task_name}:")
        print(f"    Raw:      {task_correct}/{task_total} ({raw_acc:.1%})")
        print(f"    False neg: {task_false_neg}")
        print(f"    Adjusted: {task_correct}/{adj_denom} ({adj_acc:.1%})")

        overall_correct += task_correct
        overall_total += task_total
        overall_false_neg += task_false_neg

    raw_overall = overall_correct / overall_total if overall_total else 0
    adj_overall_denom = overall_total - overall_false_neg
    adj_overall = overall_correct / adj_overall_denom if adj_overall_denom else 0

    print(f"\n  OVERALL:")
    print(f"    Raw:      {overall_correct}/{overall_total} ({raw_overall:.1%})")
    print(f"    False neg: {overall_false_neg}")
    print(f"    Adjusted: {overall_correct}/{adj_overall_denom} ({adj_overall:.1%})")

    # ---------------------------------------------------------------------------
    # Save outputs
    # ---------------------------------------------------------------------------
    output_dir = PROJECT_ROOT / "outputs" / "lic_false_negative_analysis"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. user_sim_sufficiency.json
    with open(output_dir / "user_sim_sufficiency.json", "w") as f:
        json.dump(user_sim_sufficiency, f, indent=2)

    # 2. answer_extracted.json
    with open(output_dir / "answer_extracted.json", "w") as f:
        json.dump(answer_extracted, f, indent=2)

    # 3. Full detailed results for provenance
    detailed_results = {
        "timestamp": datetime.now().isoformat(),
        "config": {
            "analysis_model": ANALYSIS_MODEL,
            "evaluated_model": "t-gpt-5.2",
            "convs_per_question": CONVS_PER_QUESTION,
            "concurrency": CONCURRENCY,
        },
        "task_stats": dict(task_stats),
        "overall": {
            "raw_correct": overall_correct,
            "raw_total": overall_total,
            "raw_accuracy": raw_overall,
            "false_negatives": overall_false_neg,
            "adjusted_total": adj_overall_denom,
            "adjusted_accuracy": adj_overall,
        },
        "llm_results": results,  # full per-conversation LLM output
    }
    with open(output_dir / "detailed_results.json", "w") as f:
        json.dump(detailed_results, f, indent=2)

    # 4. adjusted_accuracy.json (compact)
    accuracy_summary = {}
    for task_name in sorted(task_stats):
        task_correct = 0
        task_total = 0
        task_false_neg = 0
        for task_id, convs in convs_by_task_id.items():
            if convs[0]["_task_name"] != task_name:
                continue
            for conv in convs:
                conv_id = conv["conv_id"]
                task_total += 1
                if is_correct(conv):
                    task_correct += 1
                else:
                    sufficient = user_sim_sufficiency.get(task_id, {}).get(conv_id, True)
                    if not sufficient:
                        task_false_neg += 1
        adj_denom = task_total - task_false_neg
        accuracy_summary[task_name] = {
            "raw_correct": task_correct,
            "raw_total": task_total,
            "raw_accuracy": task_correct / task_total if task_total else 0,
            "false_negatives": task_false_neg,
            "adjusted_total": adj_denom,
            "adjusted_accuracy": task_correct / adj_denom if adj_denom else 0,
        }
    accuracy_summary["overall"] = detailed_results["overall"]

    with open(output_dir / "adjusted_accuracy.json", "w") as f:
        json.dump(accuracy_summary, f, indent=2)

    print(f"\nResults saved to {output_dir}/")
    print(f"  - user_sim_sufficiency.json  (problem_id -> conv_id -> bool)")
    print(f"  - answer_extracted.json      (problem_id -> conv_id -> bool)")
    print(f"  - adjusted_accuracy.json     (per-task and overall)")
    print(f"  - detailed_results.json      (full provenance)")


if __name__ == "__main__":
    asyncio.run(main())
