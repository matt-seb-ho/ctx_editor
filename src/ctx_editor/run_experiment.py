#!/usr/bin/env python3
"""Main entry point for running context editor experiments."""

import asyncio
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import hydra
from dotenv import load_dotenv
from omegaconf import DictConfig, OmegaConf
from tqdm import tqdm

from ctx_editor.agents import LengthConstrainedUserAgent, NaturalUserAgent, SystemAgent, UserAgent
from ctx_editor.core import ConversationSimulator, ConversationTrace, ModelConfig, SimulationResult, SimulatorConfig
from ctx_editor.identify_false_negatives import (
    FalseNegativeResult,
    analyze_sample_inline,
    compute_adjusted_accuracy,
    print_fn_summary,
    save_fn_results,
)
from ctx_editor.memory import CheatsheetMemory, CheatsheetUpdater, MemoryModule
from ctx_editor.execution import (
    BatchedRunner,
    OfflineMemoryLearner,
    ParallelRunner,
    load_trajectories,
)
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
        AppendAnalysisStrategy,
        BaselineStrategy,
        ContextEditStrategy,
        ContextEditV2Strategy,
        ReflectionStrategy,
    )

    strategy_name = cfg.experiment.name
    if "baseline" in strategy_name:
        return BaselineStrategy(
            use_memory=strategy_cfg.get("use_memory", False),
            memory_target=strategy_cfg.get("memory_target", "system"),
        )
    elif "append_analysis" in strategy_name:
        return AppendAnalysisStrategy(
            analyzer_model=strategy_cfg.get("analyzer_model", "gpt-4o-mini"),
            min_turns=strategy_cfg.get("min_turns", 3),
            use_memory=strategy_cfg.get("use_memory", False),
            memory_target=strategy_cfg.get("memory_target", "analyzer"),
        )
    elif "context_edit_v2" in strategy_name:
        return ContextEditV2Strategy(
            analyzer_model=strategy_cfg.get("analyzer_model", "gpt-4o-mini"),
            min_turns=strategy_cfg.get("min_turns", 3),
            max_resets=strategy_cfg.get("max_resets", 3),
            use_memory=strategy_cfg.get("use_memory", False),
            memory_target=strategy_cfg.get("memory_target", "analyzer"),
        )
    elif "context_edit" in strategy_name:
        return ContextEditStrategy(
            editor_model=strategy_cfg.get("editor_model", "gpt-4o-mini"),
            use_memory=strategy_cfg.get("use_memory", False),
            memory_target=strategy_cfg.get("memory_target", "context_editor"),
        )
    elif "agentic" in strategy_name:
        return AgenticEditStrategy(
            decision_model=strategy_cfg.get("decision_model", "gpt-4o-mini"),
            editor_model=strategy_cfg.get("editor_model", "gpt-4o-mini"),
            use_memory=strategy_cfg.get("use_memory", False),
        )
    elif "reflection" in strategy_name:
        return ReflectionStrategy(
            reflection_model=strategy_cfg.get("reflection_model", "gpt-4o-mini"),
            use_memory=strategy_cfg.get("use_memory", False),
        )
    else:
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
    memory = setup_memory(cfg)

    # Auto-compute min_turns for analysis strategies based on task data.
    # Ensures at least 2 analyses run per conversation: skip_turns = min_shards - 2.
    # Only applies when strategy config has min_turns="auto".
    strategy_cfg_raw = OmegaConf.to_container(cfg.experiment.strategy, resolve=True)
    if strategy_cfg_raw.get("min_turns") == "auto":
        shard_counts = [len(s.get("shards", [])) for s in samples]
        min_shards = min(shard_counts) if shard_counts else 5
        auto_min_turns = max(min_shards - 2, 2)  # At least 2 turns before analysis
        logger.info(f"Auto min_turns: min_shards={min_shards}, setting min_turns={auto_min_turns}")
        # Override in the Hydra config so strategy instantiation picks it up
        cfg.experiment.strategy.min_turns = auto_min_turns

    strategy = get_strategy(cfg)

    logger.info(f"Loaded {len(samples)} samples for task config '{cfg.task.name}'")

    # Create simulator factory
    def make_simulator(
        sample: dict,
        memory: Optional[MemoryModule] = None,
        trace: Optional[ConversationTrace] = None,
    ):
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
        elif user_mode == "entangled":
            from .agents.entanglement_user_agent import EntanglementUserAgent

            user_agent = EntanglementUserAgent(
                task=sample_task,
                model=sim_config.user_model,
                entanglement_level=cfg.user_mode.get("entanglement_level", 0),
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
            memory=memory,
            config=sim_config,
            trace=trace,
        )

    # Run experiment
    execution_mode = cfg.execution.mode

    # Create progress bar
    pbar = tqdm(total=len(samples), desc="Running samples", unit="sample")

    def update_progress(completed: int, total: int) -> None:
        pbar.n = completed
        pbar.refresh()

    # False negative analysis setup
    fna_cfg = cfg.get("false_negative_analysis", {})
    fna_enabled = fna_cfg.get("enabled", False)
    fna_mode = fna_cfg.get("mode", "batch")
    fna_model = fna_cfg.get("model", "gpt-5-mini")
    fna_exclude_non_answer = fna_cfg.get("exclude_non_answer_attempts", False)
    fn_results: list[FalseNegativeResult] = []

    # Incremental result saving - save each result as it completes so
    # progress is not lost if the experiment hangs or is interrupted.
    partial_results_path = output_dir / "results_partial.jsonl"

    async def _run_immediate_fn_analysis(result: "SimulationResult") -> None:
        """Run false negative analysis immediately after a conversation completes."""
        if not fna_enabled or fna_mode != "immediate":
            return
        try:
            result_dict = result.to_dict()
            fn_result = await analyze_sample_inline(result_dict, model_client, fna_model)
            if fn_result:
                fn_results.append(fn_result)
        except Exception as e:
            logger.warning(f"False negative analysis failed for {result.sample_id}: {e}")

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

        # Immediate false negative analysis (fire-and-forget via event loop)
        if fna_enabled and fna_mode == "immediate":
            asyncio.ensure_future(_run_immediate_fn_analysis(result))

    # Create memory updater with grounding config and target
    memory_updater = CheatsheetUpdater(
        target=cfg.memory.get("target", "assistant"),
        model=cfg.model.ctx_editor.model,
        timeout=cfg.model.ctx_editor.get("timeout", 60),
        include_full_spec_q=cfg.memory.get("include_full_spec_q", False),
        include_ground_truth_a=cfg.memory.get("include_ground_truth_a", False),
        include_oracle_spec=cfg.memory.get("include_oracle_spec", False),
        oracle_spec_path=cfg.memory.get("oracle_spec_path", None),
    )

    # Offline learning mode — learn memory from saved trajectories, no new simulations
    if cfg.memory.enabled and cfg.memory.source == "offline":
        offline_path = cfg.memory.get("offline_trajectories")
        if not offline_path:
            raise ValueError("memory.offline_trajectories must be set when memory.source=offline")

        logger.info(f"Running offline memory learning from: {offline_path}")
        trajectories = load_trajectories(offline_path)
        logger.info(f"Loaded {len(trajectories)} trajectories for offline learning")

        learner = OfflineMemoryLearner(
            updater=memory_updater,
            model_client=model_client,
        )
        memory = await learner.learn(
            trajectories=trajectories,
            memory=memory,
            batch_size=cfg.memory.get("offline_batch_size", 5),
            save_path=cfg.memory.get("save_path"),
        )

        # No simulation results in offline mode — return early with memory-only metrics
        pbar.close()
        metrics = {
            "experiment_name": cfg.experiment_name,
            "execution_mode": "offline",
            "total_samples": 0,
            "total_attempted": 0,
            "errors": 0,
            "correct": 0,
            "accuracy": 0,
            "average_score": 0,
            "total_cost_usd": 0,
            "average_turns": 0,
            "average_user_tokens": 0,
            "per_task": {},
            "offline_learning": {
                "source": offline_path,
                "num_trajectories": len(trajectories),
                "memory_version": memory.version,
            },
        }
        save_metrics(metrics, str(output_dir))
        logger.info(
            f"Offline learning complete: memory v{memory.version} "
            f"from {len(trajectories)} trajectories"
        )
        return metrics

    # Replay setup: if replay_source is set, load baseline traces and wrap the
    # simulator factory so each simulator gets a pre-loaded trace. This composes
    # with any execution mode (parallel, batched, sequential).
    replay_source = cfg.execution.get("replay_source")
    replay_traces = None
    user_sim_skip_results: list[SimulationResult] = []  # Results for skipped user-sim-induced samples
    if replay_source:
        from ctx_editor.execution.replay import (
            load_baseline_traces,
            build_replay_trace,
            load_user_sim_induced_ids,
        )

        replay_turns = cfg.execution.get("replay_turns", 1)
        replay_traces = load_baseline_traces(replay_source)
        logger.info(
            f"Replay mode: loaded {len(replay_traces)} baseline traces from {replay_source}"
            f" (replaying last {replay_turns} turn{'s' if replay_turns > 1 else ''})"
        )

        # Filter samples to only those with matching baseline traces
        original_count = len(samples)
        samples = [s for s in samples if s.get("task_id", "unknown") in replay_traces]
        if len(samples) < original_count:
            logger.warning(
                f"Replay: {original_count - len(samples)} samples skipped "
                f"(no matching baseline trace)"
            )

        # Skip samples with user-simulator-induced errors (pre-computed)
        user_sim_induced_ids = load_user_sim_induced_ids(replay_source)
        if user_sim_induced_ids:
            skipped_samples = [
                s for s in samples if s.get("task_id", "unknown") in user_sim_induced_ids
            ]
            samples = [
                s for s in samples if s.get("task_id", "unknown") not in user_sim_induced_ids
            ]
            logger.info(
                f"Replay: skipping {len(skipped_samples)} user-sim-induced samples: "
                f"{[s.get('task_id') for s in skipped_samples]}"
            )
            # Create skip results so they appear in output as user-sim-induced
            for s in skipped_samples:
                skip_result = SimulationResult(
                    sample_id=s.get("task_id", "unknown"),
                    task_name=s.get("task", "unknown"),
                    is_correct=False,
                    score=0.0,
                    num_turns=0,
                    total_cost_usd=0.0,
                    trace={"messages": [], "logs": [], "num_resets": 0},
                    metadata={
                        "skipped": True,
                        "skip_reason": "user_sim_induced",
                        "replay_mode": True,
                    },
                )
                user_sim_skip_results.append(skip_result)
                save_result_incrementally(skip_result)

        pbar.total = len(samples)
        pbar.refresh()

        # Wrap the factory to inject replay traces
        _original_factory = make_simulator

        def make_simulator(
            sample: dict,
            memory: Optional[MemoryModule] = None,
            trace: Optional[ConversationTrace] = None,
        ):
            sample_id = sample.get("task_id", "unknown")
            trace_data = replay_traces.get(sample_id)
            if trace_data:
                trace = build_replay_trace(trace_data, replay_source, replay_turns=replay_turns)
            return _original_factory(sample, memory=memory, trace=trace)

    if execution_mode == "batched" and cfg.memory.enabled and cfg.memory.source == "continual":
        # Batched execution with continual learning
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
        # Sequential with continual learning
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
        # Parallel execution (default)
        runner = ParallelRunner(
            max_concurrent=cfg.execution.max_concurrent,
            progress_callback=update_progress,
            on_result=save_result_incrementally,
        )
        results = await runner.run(samples, make_simulator, memory)

    pbar.close()

    # Separate valid results from error results (exceptions during conversation)
    valid_results = [r for r in results if "error" not in r.metadata]
    error_results = [r for r in results if "error" in r.metadata]

    # Log user-sim-induced skips (excluded from accuracy denominator entirely)
    num_user_sim_skipped = len(user_sim_skip_results)
    if num_user_sim_skipped:
        logger.info(
            f"{num_user_sim_skipped} samples excluded (user-sim-induced errors in baseline traces)"
        )

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
    avg_user_tokens = sum(_user_output_tokens(r) for r in valid_results) / total if total > 0 else 0

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
            sum(_user_output_tokens(r) for r in task_results) / task_total if task_total > 0 else 0
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
        "user_sim_skipped": num_user_sim_skipped,
        "correct": correct,
        "accuracy": correct / total if total > 0 else 0,
        "average_score": avg_score,
        "total_cost_usd": total_cost,
        "average_turns": avg_turns,
        "average_user_tokens": avg_user_tokens,
        "execution_mode": execution_mode,
        "per_task": per_task_metrics,
    }

    # Add replay provenance to metrics
    if replay_source:
        metrics["replay"] = {
            "source": replay_source,
        }

    # Log overall metrics
    suffixes = []
    if num_errors > 0:
        suffixes.append(f"{num_errors} errors excluded")
    if num_user_sim_skipped > 0:
        suffixes.append(f"{num_user_sim_skipped} user-sim-induced skipped")
    suffix_str = f" ({', '.join(suffixes)})" if suffixes else ""
    logger.info(f"Results: {correct}/{total} correct ({metrics['accuracy']:.2%}){suffix_str}")
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

    # Measured LLM call / token budget for this run, broken down by component
    # (assistant / user sim / system judge / strategy). Snapshotted here, i.e.
    # BEFORE false-negative analysis, so the numbers describe the experiment
    # itself and not the post-hoc adjustment pass. See utils/call_meter.py.
    try:
        from ctx_editor.utils.call_meter import METER

        with open(output_dir / "call_meter.json", "w") as f:
            json.dump(METER.snapshot(), f, indent=2)
    except Exception as e:  # pragma: no cover
        logger.warning(f"Failed to write call_meter.json: {e}")

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
            **dict(cfg.get("metadata", {})),
        },
    )

    # Run batch false negative analysis if enabled
    if fna_enabled and fna_mode == "batch":
        incorrect_results = [r for r in valid_results if not r.is_correct]
        if incorrect_results:
            logger.info(
                f"Running false negative analysis on {len(incorrect_results)} incorrect samples..."
            )
            for r in tqdm(incorrect_results, desc="False negative analysis", unit="sample"):
                try:
                    fn_result = await analyze_sample_inline(r.to_dict(), model_client, fna_model)
                    if fn_result:
                        fn_results.append(fn_result)
                except Exception as e:
                    logger.warning(f"False negative analysis failed for {r.sample_id}: {e}")

    # Save false negative results and report adjusted accuracy
    if fn_results:
        fn_output_path = str(output_dir / "false_negatives.json")
        save_fn_results(fn_results, fn_output_path)
        print_fn_summary(fn_results, correct, total, fna_exclude_non_answer)

        # Compute and log adjusted accuracy
        adj = compute_adjusted_accuracy(correct, total, fn_results, fna_exclude_non_answer)
        metrics["adjusted_accuracy"] = adj["adjusted_accuracy"]
        metrics["adjusted_total"] = adj["adjusted_total"]
        metrics["user_sim_induced"] = adj["user_sim_induced"]
        metrics["non_answer_attempts"] = adj["non_answer_attempts"]
        logger.info(
            f"Adjusted accuracy: {adj['adjusted_correct']}/{adj['adjusted_total']} "
            f"({adj['adjusted_accuracy']:.2%}) "
            f"[{adj['user_sim_induced']} user-sim-induced, "
            f"{adj['non_answer_attempts']} non-answer-attempts excluded={fna_exclude_non_answer}]"
        )

    # Save final memory
    if memory and cfg.memory.get("save_path"):
        memory.save(cfg.memory.save_path)

    # Cross-benchmark-standard run summary. The pre-existing ``results.json``
    # is a list of per-sample dicts; ``run_summary.json`` is the uniform
    # ``{benchmark, experiment_name, metrics, …}`` shape consumed by
    # ``scripts/aggregate_results.py`` across all four benchmarks.
    run_summary = {
        "benchmark": "lic",
        "experiment_name": cfg.get("experiment_name", cfg.experiment.name),
        "strategy": cfg.experiment.name,
        "task": cfg.task.name,
        "model": cfg.model.name,
        "user_mode": cfg.user_mode.name,
        "samples": total,
        "metrics": metrics,
        "total_cost_usd": total_cost,
        "average_turns": avg_turns,
        "output_dir": str(output_dir),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(output_dir / "run_summary.json", "w") as f:
        json.dump(run_summary, f, indent=2)

    # End-of-process meter snapshot (includes false-negative analysis calls).
    try:
        from ctx_editor.utils.call_meter import METER

        with open(output_dir / "call_meter_final.json", "w") as f:
            json.dump(METER.snapshot(), f, indent=2)
    except Exception:  # pragma: no cover
        pass

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
    num_skipped = metrics.get("user_sim_skipped", 0)
    notes = []
    if num_errors > 0:
        notes.append(f"{num_errors} errors excluded")
    if num_skipped > 0:
        notes.append(f"{num_skipped} user-sim-induced skipped")
    note_str = f"  ({', '.join(notes)})" if notes else ""
    summary_lines.append(
        f"Accuracy: {metrics['accuracy']:.2%} "
        f"({metrics['correct']}/{metrics['total_samples']}){note_str}"
    )
    if "adjusted_accuracy" in metrics:
        adj_note = (
            f"  [{metrics['user_sim_induced']} user-sim-induced excluded"
            f", {metrics['non_answer_attempts']} non-answer-attempts]"
        )
        summary_lines.append(
            f"Adjusted Accuracy: {metrics['adjusted_accuracy']:.2%} "
            f"({metrics['correct']}/{metrics['adjusted_total']}){adj_note}"
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
