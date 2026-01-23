#!/usr/bin/env python3
"""Main entry point for running context editor experiments."""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Optional

import hydra
from omegaconf import DictConfig, OmegaConf

# Add lic to path for task imports
sys.path.insert(0, str(Path(__file__).parent.parent / "lic"))

from ctx_editor.core import ConversationSimulator, SimulatorConfig
from ctx_editor.agents import UserAgent, SystemAgent
from ctx_editor.models import OpenAIModelClient, AnthropicModelClient
from ctx_editor.cheatsheet import Cheatsheet, CheatsheetUpdater
from ctx_editor.execution import ParallelRunner, BatchedRunner
from ctx_editor.utils.logging import setup_logging, save_results, save_metrics, get_logger


def get_task(task_name: str, version: str = None):
    """Get a task instance by name.

    Bridges to the existing LIC tasks module.
    """
    try:
        from tasks import get_task as lic_get_task
        return lic_get_task(task_name, version)
    except ImportError:
        # Fallback: try to import directly
        if task_name == "math":
            from tasks.math import TaskMath
            return TaskMath(version=version) if version else TaskMath()
        elif task_name == "code":
            from tasks.code import TaskCode
            return TaskCode(version=version) if version else TaskCode()
        elif task_name.startswith("database"):
            from tasks.database import TaskDatabase
            return TaskDatabase(version=version) if version else TaskDatabase()
        elif task_name.startswith("actions"):
            from tasks.actions import TaskActions
            return TaskActions(version=version) if version else TaskActions()
        else:
            raise ValueError(f"Task {task_name} not found")


def load_samples(cfg: DictConfig) -> list[dict[str, Any]]:
    """Load samples based on configuration."""
    data_file = cfg.task.get("data_file", "data/sharded_instructions_600.json")

    # Handle relative paths
    if not Path(data_file).is_absolute():
        # Try relative to project root
        project_root = Path(__file__).parent.parent.parent
        data_file = project_root / data_file

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
    model_name = cfg.model.get("assistant", cfg.model.name)

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
        BaselineStrategy,
        ContextEditStrategy,
        AgenticEditStrategy,
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
    logger.info(f"Config:\n{OmegaConf.to_yaml(cfg)}")

    # Load components
    task = get_task(cfg.task.name)
    samples = load_samples(cfg)
    model_client = get_model_client(cfg)
    strategy = get_strategy(cfg)
    cheatsheet = setup_cheatsheet(cfg)

    logger.info(f"Loaded {len(samples)} samples for task {cfg.task.name}")

    # Create simulator factory
    def make_simulator(sample: dict, cheatsheet: Optional[Cheatsheet] = None):
        sim_config = SimulatorConfig(
            max_turns=cfg.task.get("max_turns", 20),
            assistant_model=cfg.model.get("assistant", cfg.model.name),
            user_model=cfg.model.get("user", "gpt-4o-mini"),
            system_model=cfg.model.get("system", "gpt-4o-mini"),
            temperature=cfg.model.get("temperature", 1.0),
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

    if execution_mode == "batched" and cfg.cheatsheet.enabled and cfg.cheatsheet.source == "continual":
        # Batched execution with continual learning
        runner = BatchedRunner(
            batch_size=cfg.execution.batch_size,
            max_concurrent=cfg.execution.max_concurrent,
            model_client=model_client,
            updater=CheatsheetUpdater(),
            save_cheatsheet_path=cfg.cheatsheet.get("save_path"),
        )
        results = await runner.run(samples, make_simulator, cheatsheet)
    elif execution_mode == "sequential":
        # Sequential with continual learning
        runner = BatchedRunner(
            batch_size=1,
            max_concurrent=1,
            model_client=model_client,
            updater=CheatsheetUpdater(),
        )
        results = await runner.run_sequential(samples, make_simulator, cheatsheet)
    else:
        # Parallel execution (default)
        runner = ParallelRunner(max_concurrent=cfg.execution.max_concurrent)
        results = await runner.run(samples, make_simulator, cheatsheet)

    # Compute metrics
    total = len(results)
    correct = sum(1 for r in results if r.is_correct)
    avg_score = sum(r.score for r in results) / total if total > 0 else 0
    total_cost = sum(r.total_cost_usd for r in results)
    avg_turns = sum(r.num_turns for r in results) / total if total > 0 else 0

    metrics = {
        "experiment_name": cfg.experiment_name,
        "total_samples": total,
        "correct": correct,
        "accuracy": correct / total if total > 0 else 0,
        "average_score": avg_score,
        "total_cost_usd": total_cost,
        "average_turns": avg_turns,
        "execution_mode": execution_mode,
    }

    logger.info(f"Results: {correct}/{total} correct ({metrics['accuracy']:.2%})")
    logger.info(f"Average score: {avg_score:.3f}")
    logger.info(f"Total cost: ${total_cost:.4f}")

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
                assistant_model=cfg.model.get("assistant", cfg.model.name),
            )

    # Save final cheatsheet
    if cheatsheet and cfg.cheatsheet.get("save_path"):
        cheatsheet.save(cfg.cheatsheet.save_path)

    logger.info(f"Results saved to {output_dir}")

    return metrics


@hydra.main(config_path="config", config_name="config", version_base=None)
def main(cfg: DictConfig) -> None:
    """Main entry point."""
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
    print(f"Results saved to: {cfg.logging.output_dir}")


if __name__ == "__main__":
    main()
