"""STQ (Single-Turn Question) baseline — true upper-bound for a model.

Sends the original unsharded prompt as a single user message and grades the
response with the task's normal evaluator. Distinct from `run_concat_baseline.py`
which concatenates the shards (still LiC-rewritten) rather than using the
original natural-language prompt.

Usage examples:

    python scripts/run_stq_baseline.py \
        --model gpt5_4 --load-balancer multi_endpoint \
        --tasks math_v2 code_v2 database_v2 actions_v2 \
        --n-runs 3 --data-dir data --subset htn50_52 \
        --output-root outputs/post_neurips_lic_vanilla_stq

    python scripts/run_stq_baseline.py \
        --model deepseek_v4_flash_foundry --load-balancer multi_endpoint_foundry \
        --tasks math_v2 code_v2 database_v2 actions_v2 \
        --n-runs 3 --subset htn50_52

The script reuses the project's Hydra-configured model + load balancer wiring by
loading the appropriate config files manually (no Hydra @main decorator — we want
to dispatch many (model, task, run) cells from a single Python process for
simplicity).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import yaml
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
load_dotenv(PROJECT_ROOT / ".env")

from ctx_editor.models import LoadBalancerConfig, OpenAIModelClient  # noqa: E402
from lic.tasks import get_task  # noqa: E402


CONFIG_DIR = PROJECT_ROOT / "src" / "ctx_editor" / "config"


def load_model_cfg(name: str) -> dict:
    with (CONFIG_DIR / "model" / f"{name}.yaml").open() as f:
        return yaml.safe_load(f)


def load_lb_cfg(name: str) -> dict | None:
    if not name:
        return None
    with (CONFIG_DIR / "load_balancer" / f"{name}.yaml").open() as f:
        return yaml.safe_load(f)


def task_data_file(task_config_name: str, subset: str) -> str:
    """Map a task config (e.g. 'math_v2') + subset name to a data path."""
    base = task_config_name.removesuffix("_v2").removesuffix("_v3")
    return f"data/{subset}_{base}_subset.json"


async def run_one_cell(
    *,
    model_cfg: dict,
    task_cfg_name: str,
    data_file: str,
    model_client: OpenAIModelClient,
    max_concurrent: int,
    run_idx: int,
    output_root: Path,
) -> dict:
    """Run STQ for one (model, task, run) cell.

    Returns a summary dict. Writes per-sample JSONL into output_root.
    """
    assistant_cfg = model_cfg["assistant"]
    model_name = assistant_cfg["model"]
    model_label = model_cfg["name"]
    base_task = task_cfg_name.removesuffix("_v2").removesuffix("_v3")
    task = get_task(task_cfg_name)

    # Load samples (filtered to this task).
    with open(PROJECT_ROOT / data_file) as f:
        all_samples = json.load(f)
    samples = [s for s in all_samples if s.get("task") == base_task]

    cell_dir = output_root / f"{model_label}__{task_cfg_name}__run{run_idx}"
    cell_dir.mkdir(parents=True, exist_ok=True)
    rows_path = cell_dir / "results.jsonl"

    # Reset file
    rows_path.write_text("")

    sem = asyncio.Semaphore(max_concurrent)

    async def run_one_sample(sample: dict) -> dict:
        async with sem:
            try:
                system_prompt = task.generate_system_prompt(sample)
                user_prompt = task.populate_fully_specific_prompt(sample)
            except Exception as e:
                return {
                    "task_id": sample.get("task_id", "?"),
                    "is_correct": False, "score": 0.0,
                    "error": f"prompt-build: {e}", "cost_usd": 0.0,
                }
            try:
                resp = await model_client.generate(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    model=model_name,
                    temperature=assistant_cfg.get("temperature", 1.0),
                    max_tokens=assistant_cfg.get("max_tokens", 10000),
                    timeout=assistant_cfg.get("timeout", 300),
                    reasoning_effort=assistant_cfg.get("reasoning_effort"),
                )
            except Exception as e:
                return {
                    "task_id": sample.get("task_id", "?"),
                    "is_correct": False, "score": 0.0,
                    "error": f"model: {e}", "cost_usd": 0.0,
                }
            raw = resp.content
            cost = resp.total_usd

            strategy = getattr(task, "answer_extraction_strategy", "gen")
            try:
                if strategy == "task_specific" and hasattr(task, "extract_answer"):
                    extracted = task.extract_answer(raw)
                else:
                    extracted = raw
            except Exception as e:
                return {
                    "task_id": sample.get("task_id", "?"),
                    "is_correct": False, "score": 0.0,
                    "error": f"extract: {e}", "cost_usd": cost,
                }

            try:
                ev = task.evaluator_function(extracted, sample)
            except Exception as e:
                return {
                    "task_id": sample.get("task_id", "?"),
                    "is_correct": False, "score": 0.0,
                    "error": f"eval: {e}", "cost_usd": cost,
                }

            if isinstance(ev, dict):
                score = ev.get("score", 0.0)
                is_correct = ev.get("is_correct", score == 1.0)
            elif isinstance(ev, tuple):
                is_correct, _ = ev
                score = 1.0 if is_correct else 0.0
            else:
                is_correct = bool(ev)
                score = 1.0 if is_correct else 0.0

            return {
                "task_id": sample.get("task_id", "?"),
                "is_correct": bool(is_correct),
                "score": float(score),
                "cost_usd": cost,
                "response_preview": raw[:200],
                "extracted_preview": str(extracted)[:200] if extracted else "",
            }

    started = time.time()
    results = await asyncio.gather(*(run_one_sample(s) for s in samples))
    elapsed = time.time() - started

    # Save per-sample rows
    with rows_path.open("a") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    total = len(results)
    valid = [r for r in results if "error" not in r]
    errors = total - len(valid)
    correct = sum(1 for r in valid if r["is_correct"])
    acc = correct / len(valid) if valid else 0.0
    total_cost = sum(r["cost_usd"] for r in results)

    summary = {
        "model": model_label,
        "model_id": model_name,
        "task": task_cfg_name,
        "run_idx": run_idx,
        "total_samples": total,
        "errors": errors,
        "correct": correct,
        "accuracy": acc,
        "total_cost_usd": total_cost,
        "wall_seconds": elapsed,
        "data_file": data_file,
        "output_dir": str(cell_dir if not cell_dir.is_relative_to(PROJECT_ROOT) else cell_dir.relative_to(PROJECT_ROOT)),
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }
    with (cell_dir / "summary.json").open("w") as f:
        json.dump(summary, f, indent=2)
    print(
        f"  [{datetime.now().strftime('%H:%M:%S')}] {model_label} {task_cfg_name} run{run_idx} "
        f"  → {correct}/{len(valid) if valid else 0} ({acc:.1%}) "
        f"errors={errors} cost=${total_cost:.2f} wall={elapsed:.0f}s"
    )
    return summary


async def main_async(args):
    model_cfg = load_model_cfg(args.model)
    lb_cfg = load_lb_cfg(args.load_balancer)
    lb_config = LoadBalancerConfig.from_dict(lb_cfg) if lb_cfg else None
    model_client = OpenAIModelClient(load_balancer_config=lb_config)

    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    all_summaries = []
    for task_cfg in args.tasks:
        data_file = task_data_file(task_cfg, args.subset)
        for run_idx in range(1, args.n_runs + 1):
            s = await run_one_cell(
                model_cfg=model_cfg,
                task_cfg_name=task_cfg,
                data_file=data_file,
                model_client=model_client,
                max_concurrent=args.max_concurrent,
                run_idx=run_idx,
                output_root=output_root,
            )
            all_summaries.append(s)

    out_path = output_root / f"_all_{args.model}_{int(time.time())}.json"
    with out_path.open("w") as f:
        json.dump({"runs": all_summaries}, f, indent=2)
    print(f"\nWrote per-model summary: {out_path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, help="model config name, e.g. gpt5_4")
    parser.add_argument("--load-balancer", default=None,
                        help="load_balancer config name (e.g. multi_endpoint, multi_endpoint_foundry)")
    parser.add_argument("--tasks", nargs="+", required=True,
                        help="task config names, e.g. math_v2 code_v2 database_v2 actions_v2")
    parser.add_argument("--n-runs", type=int, default=3)
    parser.add_argument("--subset", default="htn50_52")
    parser.add_argument("--max-concurrent", type=int, default=20)
    parser.add_argument("--output-root", default="outputs/post_neurips_lic_vanilla_stq")
    args = parser.parse_args()

    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
