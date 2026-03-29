"""Post-hoc false negative analysis on LiC original repo logs for gpt-5.2.

All 10 conversations per question. Reuses existing results for convs 1-3
and runs LLM analysis only on the remaining 7 conversations' incorrect samples.

Outputs:
  - user_sim_sufficiency.json: problem_id -> conv_id -> bool
  - answer_extracted.json: problem_id -> conv_id -> bool
  - adjusted_accuracy.json: per-task and overall corrected accuracy
  - hard_problems.json: per task, questions sorted by true negative count (desc)
  - detailed_results.json: full provenance with costs
"""

import asyncio
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from tqdm.asyncio import tqdm_asyncio

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
CONVS_PER_QUESTION = 10  # all 10
CONCURRENCY = 30

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

OUTPUT_DIR = PROJECT_ROOT / "outputs" / "lic_false_negative_analysis"


# ---------------------------------------------------------------------------
# Task ID mapping
# ---------------------------------------------------------------------------

def lic_task_id_to_qa_key(task_id: str) -> str:
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
    user_msgs = [e for e in trace if e.get("role") == "user"]
    if not user_msgs:
        return "(no user messages found)"
    lines = []
    for i, m in enumerate(user_msgs, 1):
        lines.append(f"[Turn {i}] {m.get('content', '').strip()}")
    return "\n\n".join(lines)


def extract_system_message(trace: list[dict]) -> str:
    for entry in trace:
        if entry.get("role") == "system":
            return entry.get("content", "").strip()
    return ""


def get_answer_extracted(trace: list[dict]) -> bool:
    for entry in reversed(trace):
        if entry.get("role") == "log":
            content = entry.get("content", {})
            if isinstance(content, dict) and content.get("type") == "answer-evaluation":
                exact_answer = content.get("exact_answer", "")
                return bool(exact_answer and str(exact_answer).strip())
    return False


def is_correct(conv: dict) -> bool:
    score = conv.get("score", 0)
    return score is not None and float(score) == 1.0


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

def load_all_conversations() -> dict[str, list[dict]]:
    """Load all gpt-5.2 conversations grouped by task_id, all 10 per question."""
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
                conv["_task_name"] = task_name
                by_task_id[conv["task_id"]].append(conv)

    result = {}
    for task_id, convs in by_task_id.items():
        result[task_id] = convs[:CONVS_PER_QUESTION]
    return result


def load_qa_metadata() -> dict[str, dict]:
    qa_path = PROJECT_ROOT / "data" / "question_id_to_full_spec_qa.json"
    with open(qa_path) as f:
        return json.load(f)


def load_existing_results() -> dict[str, dict]:
    """Load existing LLM results from first-3 run, keyed by conv_id."""
    detail_path = OUTPUT_DIR / "detailed_results.json"
    if not detail_path.exists():
        return {}
    with open(detail_path) as f:
        data = json.load(f)
    existing = {}
    for r in data.get("llm_results", []):
        existing[r["conv_id"]] = r
    return existing


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
            "user_sim_sufficient": True,
            "missing_elements": [],
            "explanation": "",
            "cost_usd": 0.0,
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
                "cost_usd": resp.total_usd,
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
                "cost_usd": 0.0,
            }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    print("Loading all conversations (10 per question)...")
    convs_by_task_id = load_all_conversations()
    qa_metadata = load_qa_metadata()

    total_questions = len(convs_by_task_id)
    total_convs = sum(len(v) for v in convs_by_task_id.values())
    print(f"Loaded {total_convs} conversations across {total_questions} questions")

    # Load existing results from the first-3 run
    existing_results = load_existing_results()
    print(f"Loaded {len(existing_results)} existing LLM results from prior run")

    # Identify all incorrect convs, split into already-analyzed vs new
    new_incorrect = []  # (conv, qa_key) needing LLM calls
    reused_results = []  # results we can reuse
    all_correct_count = 0

    user_sim_sufficiency: dict[str, dict[str, bool]] = {}
    answer_extracted: dict[str, dict[str, bool]] = {}
    task_stats: dict[str, dict] = defaultdict(lambda: {"total": 0, "correct": 0, "incorrect": 0})

    for task_id, convs in convs_by_task_id.items():
        qa_key = lic_task_id_to_qa_key(task_id)
        user_sim_sufficiency[task_id] = {}
        answer_extracted[task_id] = {}
        task_name = convs[0]["_task_name"]

        for conv in convs:
            conv_id = conv["conv_id"]
            task_stats[task_name]["total"] += 1
            answer_extracted[task_id][conv_id] = get_answer_extracted(conv["trace"])

            if is_correct(conv):
                task_stats[task_name]["correct"] += 1
                user_sim_sufficiency[task_id][conv_id] = True
                all_correct_count += 1
            else:
                task_stats[task_name]["incorrect"] += 1
                if conv_id in existing_results:
                    r = existing_results[conv_id]
                    user_sim_sufficiency[task_id][conv_id] = r["user_sim_sufficient"]
                    reused_results.append(r)
                else:
                    new_incorrect.append((conv, qa_key))

    print(f"\nCorrect: {all_correct_count}")
    print(f"Incorrect already analyzed (reusing): {len(reused_results)}")
    print(f"Incorrect needing new LLM calls: {len(new_incorrect)}")

    print(f"\nPer-task breakdown (all 10 runs):")
    for task_name in sorted(task_stats):
        s = task_stats[task_name]
        raw_acc = s["correct"] / s["total"] if s["total"] else 0
        print(f"  {task_name:10s}: {s['correct']}/{s['total']} ({raw_acc:.1%}), {s['incorrect']} incorrect")

    # Run LLM analysis on new incorrect convs only
    all_new_results = []
    total_cost = 0.0
    reused_cost = sum(r.get("cost_usd", 0.0) for r in reused_results)

    if new_incorrect:
        lb_config = LoadBalancerConfig.from_dict(LOAD_BALANCER_CONFIG)
        model_client = get_model_client(model_name=ANALYSIS_MODEL, load_balancer_config=lb_config)
        sem = asyncio.Semaphore(CONCURRENCY)

        tasks = [
            check_user_sim_sufficiency(conv, qa_key, qa_metadata, model_client, sem)
            for conv, qa_key in new_incorrect
        ]

        print(f"\nRunning sufficiency checks on {len(tasks)} new conversations...")
        all_new_results = await tqdm_asyncio.gather(*tasks, desc="Sufficiency checks")

        # Fill in user_sim_sufficiency with new results
        errors = 0
        for r in all_new_results:
            task_id = r["task_id"]
            conv_id = r["conv_id"]
            user_sim_sufficiency[task_id][conv_id] = r["user_sim_sufficient"]
            total_cost += r.get("cost_usd", 0.0)
            if r["error"]:
                errors += 1

        print(f"\nNew LLM calls complete. Errors: {errors}")

    print(f"\nCost this run: ${total_cost:.4f}")
    print(f"Cost from prior run (reused): ${reused_cost:.4f}")
    print(f"Total cost: ${total_cost + reused_cost:.4f}")

    # Merge all LLM results
    all_llm_results = reused_results + all_new_results

    # ---------------------------------------------------------------------------
    # Compute per-question true negative counts and adjusted accuracy
    # ---------------------------------------------------------------------------

    # true_neg_counts: task_name -> task_id -> {true_neg, false_neg, correct, total}
    question_breakdown: dict[str, dict[str, dict]] = defaultdict(dict)

    for task_id, convs in convs_by_task_id.items():
        task_name = convs[0]["_task_name"]
        true_neg = 0
        false_neg = 0
        correct = 0
        for conv in convs:
            conv_id = conv["conv_id"]
            if is_correct(conv):
                correct += 1
            else:
                sufficient = user_sim_sufficiency.get(task_id, {}).get(conv_id, True)
                if sufficient:
                    true_neg += 1
                else:
                    false_neg += 1
        question_breakdown[task_name][task_id] = {
            "true_negatives": true_neg,
            "false_negatives": false_neg,
            "correct": correct,
            "total": len(convs),
        }

    # ---------------------------------------------------------------------------
    # Print adjusted accuracy
    # ---------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("ADJUSTED ACCURACY (10-run, excluding user-sim-induced false negatives)")
    print("=" * 70)

    overall_correct = 0
    overall_total = 0
    overall_false_neg = 0

    for task_name in sorted(task_stats):
        task_correct = 0
        task_total = 0
        task_false_neg = 0
        for task_id, breakdown in question_breakdown[task_name].items():
            task_correct += breakdown["correct"]
            task_total += breakdown["total"]
            task_false_neg += breakdown["false_negatives"]

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
    # Build hard_problems: per task, sorted by true negative count desc
    # ---------------------------------------------------------------------------
    hard_problems: dict[str, list[dict]] = {}
    for task_name in sorted(question_breakdown):
        items = []
        for task_id, bd in question_breakdown[task_name].items():
            items.append({
                "task_id": task_id,
                "qa_key": lic_task_id_to_qa_key(task_id),
                "true_negatives": bd["true_negatives"],
                "false_negatives": bd["false_negatives"],
                "correct": bd["correct"],
                "total": bd["total"],
            })
        items.sort(key=lambda x: x["true_negatives"], reverse=True)
        hard_problems[task_name] = items

    # Print top hard problems per task
    print("\n" + "=" * 70)
    print("HARDEST PROBLEMS (most true negatives in 10 runs)")
    print("=" * 70)
    for task_name, items in hard_problems.items():
        print(f"\n  {task_name} (showing top 10):")
        print(f"    {'task_id':<40s} TN  FN  OK  /10")
        print(f"    {'-'*40} --  --  --  ---")
        for item in items[:10]:
            print(
                f"    {item['task_id']:<40s} "
                f"{item['true_negatives']:2d}  "
                f"{item['false_negatives']:2d}  "
                f"{item['correct']:2d}  "
                f"/{item['total']}"
            )

    # ---------------------------------------------------------------------------
    # Save outputs
    # ---------------------------------------------------------------------------
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_DIR / "user_sim_sufficiency.json", "w") as f:
        json.dump(user_sim_sufficiency, f, indent=2)

    with open(OUTPUT_DIR / "answer_extracted.json", "w") as f:
        json.dump(answer_extracted, f, indent=2)

    with open(OUTPUT_DIR / "hard_problems.json", "w") as f:
        json.dump(hard_problems, f, indent=2)

    # Adjusted accuracy
    accuracy_summary = {}
    for task_name in sorted(task_stats):
        task_correct = sum(bd["correct"] for bd in question_breakdown[task_name].values())
        task_total = sum(bd["total"] for bd in question_breakdown[task_name].values())
        task_false_neg = sum(bd["false_negatives"] for bd in question_breakdown[task_name].values())
        adj_denom = task_total - task_false_neg
        accuracy_summary[task_name] = {
            "raw_correct": task_correct,
            "raw_total": task_total,
            "raw_accuracy": task_correct / task_total if task_total else 0,
            "false_negatives": task_false_neg,
            "adjusted_total": adj_denom,
            "adjusted_accuracy": task_correct / adj_denom if adj_denom else 0,
        }
    accuracy_summary["overall"] = {
        "raw_correct": overall_correct,
        "raw_total": overall_total,
        "raw_accuracy": raw_overall,
        "false_negatives": overall_false_neg,
        "adjusted_total": adj_overall_denom,
        "adjusted_accuracy": adj_overall,
    }
    with open(OUTPUT_DIR / "adjusted_accuracy.json", "w") as f:
        json.dump(accuracy_summary, f, indent=2)

    # Detailed results with costs
    detailed_results = {
        "timestamp": datetime.now().isoformat(),
        "config": {
            "analysis_model": ANALYSIS_MODEL,
            "evaluated_model": "t-gpt-5.2",
            "convs_per_question": CONVS_PER_QUESTION,
            "concurrency": CONCURRENCY,
        },
        "costs": {
            "this_run_usd": total_cost,
            "reused_from_prior_usd": reused_cost,
            "total_usd": total_cost + reused_cost,
        },
        "task_stats": dict(task_stats),
        "overall": accuracy_summary["overall"],
        "llm_results": all_llm_results,
    }
    with open(OUTPUT_DIR / "detailed_results.json", "w") as f:
        json.dump(detailed_results, f, indent=2)

    print(f"\nResults saved to {OUTPUT_DIR}/")
    print(f"  - user_sim_sufficiency.json  (problem_id -> conv_id -> bool)")
    print(f"  - answer_extracted.json      (problem_id -> conv_id -> bool)")
    print(f"  - adjusted_accuracy.json     (per-task and overall)")
    print(f"  - hard_problems.json         (per-task, sorted by true negatives desc)")
    print(f"  - detailed_results.json      (full provenance with costs)")


if __name__ == "__main__":
    asyncio.run(main())
