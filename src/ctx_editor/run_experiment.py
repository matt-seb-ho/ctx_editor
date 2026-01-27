#!/usr/bin/env python3
"""Main entry point for running context editor experiments."""

import asyncio
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Optional

import hydra
from dotenv import load_dotenv
from omegaconf import DictConfig, OmegaConf
from tqdm import tqdm

from ctx_editor.agents import SystemAgent, UserAgent
from ctx_editor.cheatsheet import Cheatsheet, CheatsheetUpdater
from ctx_editor.core import ConversationSimulator, ModelConfig, SimulatorConfig
from ctx_editor.execution import BatchedRunner, ParallelRunner
from ctx_editor.models import AnthropicModelClient, OpenAIModelClient
from ctx_editor.utils.logging import get_logger, save_metrics, save_results, setup_logging
from lic.paths import PROJECT_ROOT

# Load environment variables from .env file at repo root
load_dotenv(PROJECT_ROOT / ".env")


def get_task(task_name: str, version: str = None):
    """Get a task instance by name.

    Bridges to the existing LIC tasks module.
    """
    try:
        from lic.tasks import get_task as lic_get_task

        return lic_get_task(task_name, version)
    except ImportError:
        # Fallback: try to import directly
        if task_name == "math":
            from ctx_editor.tasks import TaskMath

            return TaskMath(version=version) if version else TaskMath()
        elif task_name == "code":
            from ctx_editor.tasks import TaskCode

            return TaskCode(version=version) if version else TaskCode()
        elif task_name.startswith("database"):
            from ctx_editor.tasks import TaskDatabase

            return TaskDatabase(version=version) if version else TaskDatabase()
        elif task_name.startswith("actions"):
            from ctx_editor.tasks import TaskActions

            return TaskActions(version=version) if version else TaskActions()
        else:
            raise ValueError(f"Task {task_name} not found")


def load_samples(cfg: DictConfig) -> list[dict[str, Any]]:
    """Load samples based on configuration."""
    data_file = cfg.task.get("data_file", "data/sharded_instructions_600.json")

    # Handle relative paths - resolve to project root, not working directory
    if not Path(data_file).is_absolute():
        data_file = PROJECT_ROOT / data_file

    with open(data_file, "r") as f:
        samples = json.load(f)

    # Filter by task name if specified
    task_filter = cfg.task.get("filter")
    if task_filter:
        if isinstance(task_filter, str):
            task_filter = [task_filter]
        samples = [s for s in samples if s.get("task") in task_filter]

    # Limit number of samples if specified
    limit = cfg.task.get("limit")
    if limit and limit > 0:
        samples = samples[:limit]

    return samples


def get_model_client(cfg: DictConfig):
    """Create appropriate model client based on config."""
    model_name = cfg.model.get("assistant", None).model or cfg.model.name

    if "claude" in model_name.lower():
        return AnthropicModelClient()
    else:
        return OpenAIModelClient()


def get_strategy(cfg: DictConfig):
    """Instantiate strategy from config."""
    strategy_cfg = cfg.experiment.strategy

    # Use hydra's instantiate if _target_ is specified
    if "_target_" in strategy_cfg:
        return hydra.utils.instantiate(strategy_cfg)

    # Fallback to manual instantiation
    from ctx_editor.strategies import (
        AgenticEditStrategy,
        BaselineStrategy,
        ContextEditStrategy,
        ReflectionStrategy,
    )

    strategy_name = cfg.experiment.name
    if "baseline" in strategy_name:
        return BaselineStrategy(
            use_cheatsheet=strategy_cfg.get("use_cheatsheet", False),
            cheatsheet_target=strategy_cfg.get("cheatsheet_target", "system"),
        )
    elif "context_edit" in strategy_name:
        return ContextEditStrategy(
            editor_model=strategy_cfg.get("editor_model", "gpt-4o-mini"),
            use_cheatsheet=strategy_cfg.get("use_cheatsheet", False),
            cheatsheet_target=strategy_cfg.get("cheatsheet_target", "context_editor"),
        )
    elif "agentic" in strategy_name:
        return AgenticEditStrategy(
            decision_model=strategy_cfg.get("decision_model", "gpt-4o-mini"),
            editor_model=strategy_cfg.get("editor_model", "gpt-4o-mini"),
            use_cheatsheet=strategy_cfg.get("use_cheatsheet", False),
        )
    elif "reflection" in strategy_name:
        return ReflectionStrategy(
            reflection_model=strategy_cfg.get("reflection_model", "gpt-4o-mini"),
            use_cheatsheet=strategy_cfg.get("use_cheatsheet", False),
        )
    else:
        return BaselineStrategy()


def setup_cheatsheet(cfg: DictConfig) -> Optional[Cheatsheet]:
    """Setup cheatsheet based on config."""
    if not cfg.cheatsheet.enabled:
        return None

    source = cfg.cheatsheet.source
    if source and source != "continual" and Path(source).exists():
        return Cheatsheet.load(source)
    else:
        return Cheatsheet(content="")


async def run_experiment(cfg: DictConfig) -> dict[str, Any]:
    """Run the experiment based on configuration."""
    logger = get_logger("experiment")

    # Setup
    logger.info(f"Starting experiment: {cfg.experiment_name}")

    # Save resolved config to output directory
    output_dir = Path(cfg.logging.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    config_path = output_dir / "config.yaml"
    with open(config_path, "w") as f:
        f.write(OmegaConf.to_yaml(cfg, resolve=True))
    logger.info(f"Saved config to {config_path}")

    # Load components
    samples = load_samples(cfg)
    model_client = get_model_client(cfg)
    strategy = get_strategy(cfg)
    cheatsheet = setup_cheatsheet(cfg)

    logger.info(f"Loaded {len(samples)} samples for task config '{cfg.task.name}'")

    # Create simulator factory
    def make_simulator(sample: dict, cheatsheet: Optional[Cheatsheet] = None):
        # Build ModelConfig from hydra config
        model_cfg_dict = OmegaConf.to_container(cfg.model, resolve=True)
        model_config = ModelConfig.from_dict(model_cfg_dict)

        sim_config = SimulatorConfig(
            max_turns=cfg.task.get("max_turns", 20),
            model_config=model_config,
            verbose=cfg.logging.get("verbose", False),
        )

        sample_task = get_task(sample.get("task", cfg.task.name))

        return ConversationSimulator(
            sample=sample,
            task=sample_task,
            user_agent=UserAgent(sample_task, model=sim_config.user_model),
            system_agent=SystemAgent(sample_task, sim_config.system_model, sample),
            model_client=model_client,
            strategy=strategy,
            cheatsheet=cheatsheet,
            config=sim_config,
        )

    # Run experiment
    execution_mode = cfg.execution.mode

    # Create progress bar
    pbar = tqdm(total=len(samples), desc="Running samples", unit="sample")

    def update_progress(completed: int, total: int) -> None:
        pbar.n = completed
        pbar.refresh()

    if (
        execution_mode == "batched"
        and cfg.cheatsheet.enabled
        and cfg.cheatsheet.source == "continual"
    ):
        # Batched execution with continual learning
        runner = BatchedRunner(
            batch_size=cfg.execution.batch_size,
            max_concurrent=cfg.execution.max_concurrent,
            model_client=model_client,
            updater=CheatsheetUpdater(),
            save_cheatsheet_path=cfg.cheatsheet.get("save_path"),
            progress_callback=update_progress,
        )
        results = await runner.run(samples, make_simulator, cheatsheet)
    elif execution_mode == "sequential":
        # Sequential with continual learning
        runner = BatchedRunner(
            batch_size=1,
            max_concurrent=1,
            model_client=model_client,
            updater=CheatsheetUpdater(),
            progress_callback=update_progress,
        )
        results = await runner.run_sequential(samples, make_simulator, cheatsheet)
    else:
        # Parallel execution (default)
        runner = ParallelRunner(
            max_concurrent=cfg.execution.max_concurrent,
            progress_callback=update_progress,
        )
        results = await runner.run(samples, make_simulator, cheatsheet)

    pbar.close()

    # Compute overall metrics
    total = len(results)
    correct = sum(1 for r in results if r.is_correct)
    avg_score = sum(r.score for r in results) / total if total > 0 else 0
    total_cost = sum(r.total_cost_usd for r in results)
    avg_turns = sum(r.num_turns for r in results) / total if total > 0 else 0

    # Compute per-task metrics
    results_by_task = defaultdict(list)
    for r in results:
        results_by_task[r.task_name].append(r)

    per_task_metrics = {}
    for task_name, task_results in sorted(results_by_task.items()):
        task_total = len(task_results)
        task_correct = sum(1 for r in task_results if r.is_correct)
        task_avg_score = sum(r.score for r in task_results) / task_total if task_total > 0 else 0
        task_cost = sum(r.total_cost_usd for r in task_results)
        task_avg_turns = (
            sum(r.num_turns for r in task_results) / task_total if task_total > 0 else 0
        )

        per_task_metrics[task_name] = {
            "total_samples": task_total,
            "correct": task_correct,
            "accuracy": task_correct / task_total if task_total > 0 else 0,
            "average_score": task_avg_score,
            "total_cost_usd": task_cost,
            "average_turns": task_avg_turns,
        }

    metrics = {
        "experiment_name": cfg.experiment_name,
        "total_samples": total,
        "correct": correct,
        "accuracy": correct / total if total > 0 else 0,
        "average_score": avg_score,
        "total_cost_usd": total_cost,
        "average_turns": avg_turns,
        "execution_mode": execution_mode,
        "per_task": per_task_metrics,
    }

    # Log overall metrics
    logger.info(f"Results: {correct}/{total} correct ({metrics['accuracy']:.2%})")
    logger.info(f"Average score: {avg_score:.3f}")
    logger.info(f"Total cost: ${total_cost:.4f}")

    # Log per-task metrics
    if len(per_task_metrics) > 1:
        logger.info("Per-task breakdown:")
        for task_name, task_metrics in sorted(per_task_metrics.items()):
            logger.info(
                f"  {task_name}: {task_metrics['correct']}/{task_metrics['total_samples']} "
                f"({task_metrics['accuracy']:.2%}), avg_score={task_metrics['average_score']:.3f}"
            )

    # Save results
    output_dir = cfg.logging.output_dir
    save_results([r.to_dict() for r in results], output_dir)
    save_metrics(metrics, output_dir)

    # Save individual traces if configured
    if cfg.logging.save_traces:
        from ctx_editor.utils.logging import log_conversation

        for r in results:
            log_conversation(
                experiment_type=cfg.experiment.name,
                task_name=r.task_name,
                sample_id=r.sample_id,
                trace=r.trace,
                is_correct=r.is_correct,
                score=r.score,
                output_dir=output_dir,
                assistant_model=cfg.model.assistant.model,
            )

    # Save final cheatsheet
    if cheatsheet and cfg.cheatsheet.get("save_path"):
        cheatsheet.save(cfg.cheatsheet.save_path)

    logger.info(f"Results saved to {output_dir}")

    return metrics


@hydra.main(config_path="config", config_name="config", version_base=None)
def main(cfg: DictConfig) -> None:
    """Main entry point."""
    # Print output directory at start
    print(f"\nOutput directory: {cfg.logging.output_dir}\n")

    # Setup logging
    setup_logging(
        output_dir=cfg.logging.output_dir,
        level=20,  # INFO
    )

    # Run the experiment
    metrics = asyncio.run(run_experiment(cfg))

    # Print summary
    print("\n" + "=" * 50)
    print("EXPERIMENT COMPLETE")
    print("=" * 50)
    print(f"Experiment: {cfg.experiment_name}")
    print(f"Accuracy: {metrics['accuracy']:.2%} ({metrics['correct']}/{metrics['total_samples']})")
    print(f"Average Score: {metrics['average_score']:.3f}")
    print(f"Total Cost: ${metrics['total_cost_usd']:.4f}")
    print(f"Average Turns: {metrics['average_turns']:.1f}")

    # Print per-task breakdown if multiple tasks
    per_task = metrics.get("per_task", {})
    if len(per_task) > 1:
        print("\n" + "-" * 50)
        print("PER-TASK BREAKDOWN")
        print("-" * 50)
        print(f"{'Task':<15} {'Accuracy':<12} {'Avg Score':<12} {'Cost':<10}")
        print("-" * 50)
        for task_name, task_metrics in sorted(per_task.items()):
            acc_str = f"{task_metrics['accuracy']:.1%} ({task_metrics['correct']}/{task_metrics['total_samples']})"
            print(
                f"{task_name:<15} {acc_str:<12} "
                f"{task_metrics['average_score']:<12.3f} ${task_metrics['total_cost_usd']:<9.4f}"
            )
        print("-" * 50)

    print(f"\nResults saved to: {cfg.logging.output_dir}")


if __name__ == "__main__":
    main()
