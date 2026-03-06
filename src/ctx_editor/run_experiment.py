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

from ctx_editor.agents import LengthConstrainedUserAgent, NaturalUserAgent, SystemAgent, UserAgent
from ctx_editor.cheatsheet import Cheatsheet, CheatsheetUpdater
from ctx_editor.core import ConversationSimulator, ModelConfig, SimulatorConfig
from ctx_editor.execution import BatchedRunner, ParallelRunner
from ctx_editor.models import AnthropicModelClient, LoadBalancerConfig, OpenAIModelClient, set_content_filter_log_path
from ctx_editor.utils.ledger import add_run
from ctx_editor.utils.logging import (
    get_logger,
    log_conversation,
    save_metrics,
    save_results,
    setup_logging,
)
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
        elif task_name == "aime":
            from ctx_editor.tasks import TaskAIME

            return TaskAIME(version=version) if version else TaskAIME()
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
        # Check for load balancer configuration
        load_balancer_config = None
        if hasattr(cfg, "load_balancer") and cfg.load_balancer:
            lb_dict = OmegaConf.to_container(cfg.load_balancer, resolve=True)
            load_balancer_config = LoadBalancerConfig.from_dict(lb_dict)

        return OpenAIModelClient(load_balancer_config=load_balancer_config)


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

    # Configure content filter error log (captures Azure content filter rejections
    # with the full request messages so they can be investigated)
    set_content_filter_log_path(output_dir / "content_filter_errors.jsonl")

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

        raw_task_name = sample.get("task", cfg.task.name)
        version_map = cfg.task.get("task_version_map", {}) or {}
        resolved_task_name = version_map.get(raw_task_name, raw_task_name)
        sample_task = get_task(resolved_task_name)

        # Select user agent based on user_mode config
        user_mode = cfg.user_mode.name
        if user_mode == "natural":
            user_agent = NaturalUserAgent(
                task=sample_task,
                model=sim_config.user_model,
                include_shards=cfg.user_mode.get("include_shards", False),
                max_turns=cfg.user_mode.get("max_turns", 20),
            )
        elif user_mode == "length_constrained":
            user_agent = LengthConstrainedUserAgent(
                task=sample_task,
                model=sim_config.user_model,
                total_token_budget=cfg.user_mode.get("total_token_budget", 500),
                per_turn_token_budget=cfg.user_mode.get("per_turn_token_budget", 150),
                hard_cap_multiplier=cfg.user_mode.get("hard_cap_multiplier", 1.2),
                include_shards=cfg.user_mode.get("include_shards", False),
            )
        else:
            user_agent = UserAgent(sample_task, model=sim_config.user_model)

        return ConversationSimulator(
            sample=sample,
            task=sample_task,
            user_agent=user_agent,
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

    # Incremental result saving - save each result as it completes so
    # progress is not lost if the experiment hangs or is interrupted.
    partial_results_path = output_dir / "results_partial.jsonl"

    def save_result_incrementally(result: "SimulationResult") -> None:
        """Save a single result to disk immediately upon completion."""
        # Append to JSONL file (atomic per-line, safe for concurrent writes)
        with open(partial_results_path, "a") as f:
            f.write(json.dumps(result.to_dict(include_trace=False)) + "\n")

        # Save individual trace file
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

    # Create cheatsheet updater with grounding config
    cheatsheet_updater = CheatsheetUpdater(
        include_full_spec_q=cfg.cheatsheet.get("include_full_spec_q", False),
        include_ground_truth_a=cfg.cheatsheet.get("include_ground_truth_a", False),
    )

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
            updater=cheatsheet_updater,
            save_cheatsheet_path=cfg.cheatsheet.get("save_path"),
            progress_callback=update_progress,
            on_result=save_result_incrementally,
        )
        results = await runner.run(samples, make_simulator, cheatsheet)
    elif execution_mode == "sequential":
        # Sequential with continual learning
        runner = BatchedRunner(
            batch_size=1,
            max_concurrent=1,
            model_client=model_client,
            updater=cheatsheet_updater,
            progress_callback=update_progress,
            on_result=save_result_incrementally,
        )
        results = await runner.run_sequential(samples, make_simulator, cheatsheet)
    else:
        # Parallel execution (default)
        runner = ParallelRunner(
            max_concurrent=cfg.execution.max_concurrent,
            progress_callback=update_progress,
            on_result=save_result_incrementally,
        )
        results = await runner.run(samples, make_simulator, cheatsheet)

    pbar.close()

    # Separate valid results from error results (exceptions during conversation)
    valid_results = [r for r in results if "error" not in r.metadata]
    error_results = [r for r in results if "error" in r.metadata]

    def _user_output_tokens(r) -> int:
        """Extract user agent output tokens from a result."""
        if r.usage_stats:
            return r.usage_stats.user.output_tokens
        return 0

    # Compute overall metrics (excluding errored conversations)
    total_attempted = len(results)
    total = len(valid_results)
    num_errors = len(error_results)
    correct = sum(1 for r in valid_results if r.is_correct)
    avg_score = sum(r.score for r in valid_results) / total if total > 0 else 0
    total_cost = sum(r.total_cost_usd for r in results)  # cost includes errors
    avg_turns = sum(r.num_turns for r in valid_results) / total if total > 0 else 0
    avg_user_tokens = (
        sum(_user_output_tokens(r) for r in valid_results) / total if total > 0 else 0
    )

    # Compute per-task metrics (excluding errored conversations)
    valid_by_task = defaultdict(list)
    errors_by_task = defaultdict(list)
    for r in valid_results:
        valid_by_task[r.task_name].append(r)
    for r in error_results:
        errors_by_task[r.task_name].append(r)

    all_task_names = sorted(set(list(valid_by_task.keys()) + list(errors_by_task.keys())))

    per_task_metrics = {}
    for task_name in all_task_names:
        task_results = valid_by_task.get(task_name, [])
        task_errors = errors_by_task.get(task_name, [])
        task_total = len(task_results)
        task_correct = sum(1 for r in task_results if r.is_correct)
        task_avg_score = sum(r.score for r in task_results) / task_total if task_total > 0 else 0
        task_cost = sum(r.total_cost_usd for r in task_results) + sum(
            r.total_cost_usd for r in task_errors
        )
        task_avg_turns = (
            sum(r.num_turns for r in task_results) / task_total if task_total > 0 else 0
        )
        task_avg_user_tokens = (
            sum(_user_output_tokens(r) for r in task_results) / task_total
            if task_total > 0
            else 0
        )

        per_task_metrics[task_name] = {
            "total_samples": task_total,
            "total_attempted": task_total + len(task_errors),
            "errors": len(task_errors),
            "correct": task_correct,
            "accuracy": task_correct / task_total if task_total > 0 else 0,
            "average_score": task_avg_score,
            "total_cost_usd": task_cost,
            "average_turns": task_avg_turns,
            "average_user_tokens": task_avg_user_tokens,
        }

    metrics = {
        "experiment_name": cfg.experiment_name,
        "total_samples": total,
        "total_attempted": total_attempted,
        "errors": num_errors,
        "correct": correct,
        "accuracy": correct / total if total > 0 else 0,
        "average_score": avg_score,
        "total_cost_usd": total_cost,
        "average_turns": avg_turns,
        "average_user_tokens": avg_user_tokens,
        "execution_mode": execution_mode,
        "per_task": per_task_metrics,
    }

    # Log overall metrics
    error_suffix = f" ({num_errors} errors excluded)" if num_errors > 0 else ""
    logger.info(f"Results: {correct}/{total} correct ({metrics['accuracy']:.2%}){error_suffix}")
    logger.info(f"Average score: {avg_score:.3f}")
    logger.info(f"Total cost: ${total_cost:.4f}")

    # Log per-task metrics
    if len(per_task_metrics) > 1:
        logger.info("Per-task breakdown:")
        for task_name, task_m in sorted(per_task_metrics.items()):
            err_str = f" [{task_m['errors']} errors]" if task_m["errors"] > 0 else ""
            logger.info(
                f"  {task_name}: {task_m['correct']}/{task_m['total_samples']} "
                f"({task_m['accuracy']:.2%}), avg_score={task_m['average_score']:.3f}{err_str}"
            )

    # Log error details
    if error_results:
        logger.warning(f"{num_errors} conversations failed with errors (excluded from scoring):")
        for r in error_results:
            logger.warning(f"  {r.sample_id} ({r.task_name}): {r.metadata.get('error', 'unknown')}")

    # Save final results (traces already saved incrementally)
    save_results(
        [r.to_dict(include_trace=False) for r in results],
        str(output_dir),
    )
    save_metrics(metrics, str(output_dir))

    # Clean up partial results file now that final results are saved
    if partial_results_path.exists():
        partial_results_path.unlink()

    # Update ledger with run info
    outputs_root = output_dir.parent.parent  # outputs/{date}/{time} -> outputs/
    run_path = f"{output_dir.parent.name}/{output_dir.name}"  # "{date}/{time}"
    add_run(
        outputs_dir=outputs_root,
        run_path=run_path,
        strategy=cfg.experiment.name,
        model=cfg.model.name,
        task=cfg.task.name,
        status="completed",
        samples=total,
        accuracy=metrics["accuracy"],
        total_cost_usd=total_cost,
        average_turns=avg_turns,
        notes=cfg.get("notes", ""),
        extra={
            "user_mode": cfg.user_mode.name,
            "data_file": cfg.task.get("data_file", ""),
        },
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

    # Build summary text (used for both stdout and file)
    summary_lines = []
    summary_lines.append("=" * 60)
    summary_lines.append("EXPERIMENT COMPLETE")
    summary_lines.append("=" * 60)
    summary_lines.append(f"Experiment: {cfg.experiment_name}")

    num_errors = metrics.get("errors", 0)
    error_note = f"  ({num_errors} errors excluded)" if num_errors > 0 else ""
    summary_lines.append(
        f"Accuracy: {metrics['accuracy']:.2%} "
        f"({metrics['correct']}/{metrics['total_samples']}){error_note}"
    )
    summary_lines.append(f"Average Score: {metrics['average_score']:.3f}")
    summary_lines.append(f"Total Cost: ${metrics['total_cost_usd']:.4f}")
    summary_lines.append(f"Average Turns: {metrics['average_turns']:.1f}")
    summary_lines.append(f"Average User Tokens: {metrics['average_user_tokens']:.0f}")

    # Per-task breakdown if multiple tasks
    per_task = metrics.get("per_task", {})
    if len(per_task) > 1:
        summary_lines.append("")
        summary_lines.append("-" * 80)
        summary_lines.append("PER-TASK BREAKDOWN")
        summary_lines.append("-" * 80)
        summary_lines.append(
            f"{'Task':<15} {'Accuracy':<20} {'Avg Score':<10} "
            f"{'Turns':<8} {'User Tok':<10} {'Cost':<10}"
        )
        summary_lines.append("-" * 80)
        for task_name, task_m in sorted(per_task.items()):
            acc_str = f"{task_m['accuracy']:.1%} ({task_m['correct']}/{task_m['total_samples']})"
            summary_lines.append(
                f"{task_name:<15} {acc_str:<20} "
                f"{task_m['average_score']:<10.3f} "
                f"{task_m['average_turns']:<8.1f} "
                f"{task_m.get('average_user_tokens', 0):<10.0f} "
                f"${task_m['total_cost_usd']:<9.4f}"
            )
        summary_lines.append("-" * 80)

    summary_lines.append(f"\nResults saved to: {cfg.logging.output_dir}")

    summary_text = "\n".join(summary_lines)

    # Print to stdout
    print("\n" + summary_text)

    # Write summary file
    summary_path = Path(cfg.logging.output_dir) / "summary.txt"
    with open(summary_path, "w") as f:
        f.write(summary_text + "\n")


if __name__ == "__main__":
    main()
