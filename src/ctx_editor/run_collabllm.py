#!/usr/bin/env python3
"""Entry point for running CollabLLM-style evaluation experiments.

Similar to run_experiment.py but uses CollabLLM's simulation protocol:
- CollabLLM user simulator (role-plays as human with full problem access)
- No per-turn verification (evaluation at end of conversation)
- LLM-judged accuracy, interactivity, and token count metrics
- Dynamic data loading from HuggingFace
"""

import asyncio
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Optional

import hydra
from dotenv import load_dotenv
from omegaconf import DictConfig, OmegaConf
from tqdm import tqdm

from ctx_editor.agents.collabllm_user_agent import CollabLLMUserAgent
from ctx_editor.core import ConversationTrace, ModelConfig, SimulatorConfig
from ctx_editor.core.collabllm_simulator import CollabLLMSimulator
from ctx_editor.data.collabllm_loader import load_collabllm_dataset, COLLABLLM_DATASETS
from ctx_editor.evaluation.collabllm_metrics import CollabLLMEvaluator
from ctx_editor.memory import CheatsheetMemory, CheatsheetUpdater, MemoryModule
from ctx_editor.execution import BatchedRunner, ParallelRunner
from ctx_editor.models import (
    AnthropicModelClient,
    LoadBalancerConfig,
    OpenAIModelClient,
    set_content_filter_log_path,
)
from ctx_editor.utils.ledger import add_run
from ctx_editor.utils.logging import (
    get_logger,
    log_conversation,
    save_metrics,
    save_results,
    setup_logging,
)
from lic.paths import PROJECT_ROOT

load_dotenv(PROJECT_ROOT / ".env")


def get_model_client(cfg: DictConfig):
    """Create appropriate model client based on config."""
    model_name = cfg.model.get("assistant", None).model or cfg.model.name

    if "claude" in model_name.lower():
        return AnthropicModelClient()
    else:
        load_balancer_config = None
        if hasattr(cfg, "load_balancer") and cfg.load_balancer:
            lb_dict = OmegaConf.to_container(cfg.load_balancer, resolve=True)
            load_balancer_config = LoadBalancerConfig.from_dict(lb_dict)
        return OpenAIModelClient(load_balancer_config=load_balancer_config)


def get_strategy(cfg: DictConfig):
    """Instantiate strategy from config."""
    strategy_cfg = cfg.experiment.strategy

    if "_target_" in strategy_cfg:
        return hydra.utils.instantiate(strategy_cfg)

    # Fallback
    from ctx_editor.strategies import BaselineStrategy

    return BaselineStrategy()


def setup_memory(cfg: DictConfig) -> Optional[MemoryModule]:
    """Setup memory module based on config."""
    if not cfg.memory.enabled:
        return None
    source = cfg.memory.source
    if source and source not in ("continual", "offline") and Path(source).exists():
        return CheatsheetMemory.load(source)
    else:
        return CheatsheetMemory(_content="")


async def run_collabllm_experiment(cfg: DictConfig) -> dict[str, Any]:
    """Run a CollabLLM-style evaluation experiment."""
    logger = get_logger("collabllm")

    logger.info(f"Starting CollabLLM experiment: {cfg.experiment_name}")

    # Setup output directory
    output_dir = Path(cfg.logging.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    config_path = output_dir / "config.yaml"
    with open(config_path, "w") as f:
        f.write(OmegaConf.to_yaml(cfg, resolve=True))

    set_content_filter_log_path(output_dir / "content_filter_errors.jsonl")

    # Load data dynamically from HuggingFace
    dataset_name = cfg.task.get("dataset_name", "math-hard")
    limit = cfg.task.get("limit")
    split = cfg.task.get("split", None)
    samples = load_collabllm_dataset(dataset_name, limit=limit, split=split)
    logger.info(f"Loaded {len(samples)} samples from {dataset_name} ({split} split)")

    # Get dataset metadata
    dataset_info = COLLABLLM_DATASETS[dataset_name]
    task_desc = dataset_info["task_desc"]
    extract_type = dataset_info["extract_type"]

    # Setup components
    model_client = get_model_client(cfg)
    memory = setup_memory(cfg)
    strategy = get_strategy(cfg)

    # Evaluator config
    eval_model = cfg.model.get("system", {}).get("model", "gpt-4o-mini")
    evaluator = CollabLLMEvaluator(
        model=eval_model,
        extract_type=extract_type,
    )

    # Simulator factory
    def make_simulator(
        sample: dict,
        memory: Optional[MemoryModule] = None,
        trace: Optional[ConversationTrace] = None,
    ):
        model_cfg_dict = OmegaConf.to_container(cfg.model, resolve=True)
        model_config = ModelConfig.from_dict(model_cfg_dict)

        sim_config = SimulatorConfig(
            max_turns=cfg.task.get("max_turns", 14),
            model_config=model_config,
            verbose=cfg.logging.get("verbose", False),
        )

        user_agent = CollabLLMUserAgent(
            task_desc=task_desc,
            single_turn_prompt=sample["single_turn_prompt"],
            model=sim_config.model_config.user.model,
            temperature=sim_config.model_config.user.temperature,
            max_tokens=sim_config.model_config.user.max_tokens,
        )

        return CollabLLMSimulator(
            sample=sample,
            user_agent=user_agent,
            model_client=model_client,
            strategy=strategy,
            evaluator=evaluator,
            memory=memory,
            config=sim_config,
            trace=trace,
        )

    # Run experiment
    execution_mode = cfg.execution.mode
    pbar = tqdm(total=len(samples), desc="Running samples", unit="sample")

    def update_progress(completed: int, total: int) -> None:
        pbar.n = completed
        pbar.refresh()

    partial_results_path = output_dir / "results_partial.jsonl"

    def save_result_incrementally(result):
        with open(partial_results_path, "a") as f:
            f.write(json.dumps(result.to_dict(include_trace=False)) + "\n")
        log_conversation(
            experiment_type=cfg.experiment.name,
            task_name=result.task_name,
            sample_id=result.sample_id,
            trace=result.trace,
            is_correct=result.is_correct,
            score=result.score,
            output_dir=str(output_dir),
            assistant_model=cfg.model.assistant.model,
        )

    # Memory updater for batched mode
    memory_updater = CheatsheetUpdater(
        target=cfg.memory.get("target", "assistant"),
        model=cfg.model.ctx_editor.model,
        timeout=cfg.model.ctx_editor.get("timeout", 60),
        include_full_spec_q=cfg.memory.get("include_full_spec_q", False),
        include_ground_truth_a=cfg.memory.get("include_ground_truth_a", False),
    )

    if execution_mode == "batched" and cfg.memory.enabled and cfg.memory.source == "continual":
        runner = BatchedRunner(
            batch_size=cfg.execution.batch_size,
            max_concurrent=cfg.execution.max_concurrent,
            model_client=model_client,
            updater=memory_updater,
            save_memory_path=cfg.memory.get("save_path"),
            progress_callback=update_progress,
            on_result=save_result_incrementally,
        )
        results = await runner.run(samples, make_simulator, memory)
    elif execution_mode == "sequential":
        runner = BatchedRunner(
            batch_size=1,
            max_concurrent=1,
            model_client=model_client,
            updater=memory_updater,
            progress_callback=update_progress,
            on_result=save_result_incrementally,
        )
        results = await runner.run_sequential(samples, make_simulator, memory)
    else:
        runner = ParallelRunner(
            max_concurrent=cfg.execution.max_concurrent,
            progress_callback=update_progress,
            on_result=save_result_incrementally,
        )
        results = await runner.run(samples, make_simulator, memory)

    pbar.close()

    # Compute metrics
    valid_results = [r for r in results if "error" not in r.metadata]
    error_results = [r for r in results if "error" in r.metadata]

    total_attempted = len(results)
    total = len(valid_results)
    num_errors = len(error_results)
    correct = sum(1 for r in valid_results if r.is_correct)
    total_cost = sum(r.total_cost_usd for r in results)
    avg_turns = sum(r.num_turns for r in valid_results) / total if total > 0 else 0

    # CollabLLM-specific metrics from metadata
    accuracies = [
        r.metadata.get("accuracy", -1) for r in valid_results if r.metadata.get("accuracy", -1) >= 0
    ]
    interactivities = [
        r.metadata.get("interactivity", -1)
        for r in valid_results
        if r.metadata.get("interactivity", -1) >= 0
    ]
    assistant_tokens = [
        r.metadata.get("assistant_tokens", 0) for r in valid_results
    ]

    avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0
    avg_interactivity = sum(interactivities) / len(interactivities) if interactivities else 0
    avg_assistant_tokens = sum(assistant_tokens) / len(assistant_tokens) if assistant_tokens else 0

    metrics = {
        "experiment_name": cfg.experiment_name,
        "dataset_name": dataset_name,
        "total_samples": total,
        "total_attempted": total_attempted,
        "errors": num_errors,
        "correct": correct,
        "accuracy": avg_accuracy,
        "interactivity": avg_interactivity,
        "avg_assistant_tokens": avg_assistant_tokens,
        "total_cost_usd": total_cost,
        "average_turns": avg_turns,
        "execution_mode": execution_mode,
    }

    # Log results
    error_suffix = f" ({num_errors} errors excluded)" if num_errors > 0 else ""
    logger.info(f"Results: {correct}/{total} correct ({avg_accuracy:.2%}){error_suffix}")
    logger.info(f"Accuracy (LLM judge): {avg_accuracy:.3f}")
    logger.info(f"Interactivity: {avg_interactivity:.3f}")
    logger.info(f"Avg assistant tokens: {avg_assistant_tokens:.0f}")
    logger.info(f"Average turns: {avg_turns:.1f}")
    logger.info(f"Total cost: ${total_cost:.4f}")

    # Save results
    save_results(
        [r.to_dict(include_trace=False) for r in results],
        str(output_dir),
    )
    save_metrics(metrics, str(output_dir))

    if partial_results_path.exists():
        partial_results_path.unlink()

    # Update ledger
    outputs_root = output_dir.parent.parent
    run_path = f"{output_dir.parent.name}/{output_dir.name}"
    add_run(
        outputs_dir=outputs_root,
        run_path=run_path,
        strategy=cfg.experiment.name,
        model=cfg.model.name,
        task=cfg.task.name,
        status="completed",
        samples=total,
        accuracy=avg_accuracy,
        total_cost_usd=total_cost,
        average_turns=avg_turns,
        notes=cfg.get("notes", ""),
        extra={
            "interactivity": avg_interactivity,
            "avg_assistant_tokens": avg_assistant_tokens,
            "dataset_name": dataset_name,
            **dict(cfg.get("metadata", {})),
        },
    )

    if memory and cfg.memory.get("save_path"):
        memory.save(cfg.memory.save_path)

    logger.info(f"Results saved to {output_dir}")
    return metrics


@hydra.main(config_path="config", config_name="collabllm", version_base=None)
def main(cfg: DictConfig) -> None:
    """Main entry point for CollabLLM experiments."""
    print(f"\nOutput directory: {cfg.logging.output_dir}\n")

    setup_logging(
        output_dir=cfg.logging.output_dir,
        level=20,
    )

    metrics = asyncio.run(run_collabllm_experiment(cfg))

    # Print summary
    lines = []
    lines.append("=" * 60)
    lines.append("COLLABLLM EXPERIMENT COMPLETE")
    lines.append("=" * 60)
    lines.append(f"Experiment: {cfg.experiment_name}")
    lines.append(f"Dataset: {cfg.task.get('dataset_name', 'math-hard')}")

    num_errors = metrics.get("errors", 0)
    error_note = f"  ({num_errors} errors excluded)" if num_errors > 0 else ""
    lines.append(
        f"Accuracy: {metrics['accuracy']:.2%} ({metrics['correct']}/{metrics['total_samples']}){error_note}"
    )
    lines.append(f"Interactivity: {metrics['interactivity']:.3f}")
    lines.append(f"Avg Assistant Tokens: {metrics['avg_assistant_tokens']:.0f}")
    lines.append(f"Average Turns: {metrics['average_turns']:.1f}")
    lines.append(f"Total Cost: ${metrics['total_cost_usd']:.4f}")
    lines.append(f"\nResults saved to: {cfg.logging.output_dir}")

    summary_text = "\n".join(lines)
    print("\n" + summary_text)

    summary_path = Path(cfg.logging.output_dir) / "summary.txt"
    with open(summary_path, "w") as f:
        f.write(summary_text + "\n")


if __name__ == "__main__":
    main()
