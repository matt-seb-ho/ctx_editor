#!/usr/bin/env python3
"""Phase 1: Run FC + AO on WildChat conversations, classify turns, judge pairwise.

Identifies AO failure cases (turns where FC > AO on quality) for Phase 2.

Usage:
    python -m ctx_editor.huang_eval.run_phase1 \\
        num_conversations=100 \\
        respondent_model=gpt-5-mini \\
        max_concurrent=5

Or for a multi-seed sweep:
    python -m ctx_editor.huang_eval.run_phase1 --multirun seed=42,43,44

See ``ctx_editor/config/huang_phase1.yaml`` for all knobs.
"""

import asyncio
import json
import logging
import random
from datetime import datetime
from pathlib import Path

import hydra
from dotenv import load_dotenv
from omegaconf import DictConfig, OmegaConf

load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")

from ..models import get_model_client
from .data_loader import load_wildchat_conversations
from .turn_classifier import classify_turn
from .pairwise_judge import judge_pairwise
from .replay import generate_fc, generate_ao
from .aggregate import aggregate_phase1, format_summary, write_breakdown_csv

logger = logging.getLogger(__name__)


async def process_conversation(
    conversation: dict,
    model_client,
    respondent_model: str,
    judge_model: str,
    classifier_model: str,
    results_file: Path,
    rng: random.Random,
) -> list[dict]:
    """Process all eligible turns in a single conversation."""
    turns = conversation["turns"]
    conv_id = conversation["conversation_id"]
    turn_results = []

    # Find user turn indices (skip turn 0 -- no history yet)
    user_turn_indices = [i for i, t in enumerate(turns) if t["role"] == "user"]

    for idx, turn_idx in enumerate(user_turn_indices):
        if idx == 0:
            # Skip first user turn (no prior context to compare)
            continue

        logger.info(f"  Conv {conv_id}: processing turn {idx+1}/{len(user_turn_indices)}")

        try:
            # Generate FC and AO responses in parallel
            fc_task = generate_fc(turns, turn_idx, model_client, respondent_model)
            ao_task = generate_ao(turns, turn_idx, model_client, respondent_model)
            classify_task = classify_turn(turns, turn_idx, model_client, classifier_model)

            fc_response, ao_response, classification = await asyncio.gather(
                fc_task, ao_task, classify_task
            )

            # Judge FC vs AO
            judgment = await judge_pairwise(
                turns=turns,
                turn_index=turn_idx,
                response_1=fc_response,
                response_2=ao_response,
                condition_1="fc",
                condition_2="ao",
                model_client=model_client,
                model=judge_model,
                rng=rng,
            )

            result = {
                "conversation_id": conv_id,
                "turn_index": turn_idx,
                "turn_round": idx + 1,
                "turn_type": classification.turn_type,
                "turn_classification": {
                    "context_dependent_elements": classification.context_dependent_elements,
                    "confidence": classification.confidence,
                },
                "user_message": turns[turn_idx]["content"][:500],
                "fc_response": fc_response,
                "ao_response": ao_response,
                "judgments": {
                    "fc_vs_ao": {
                        "quality_winner": judgment.quality_winner,
                        "ontopic_winner": judgment.ontopic_winner,
                        "quality_justification": judgment.quality_justification,
                        "ontopic_justification": judgment.ontopic_justification,
                        "confidence": judgment.confidence,
                    },
                },
                "timestamp": datetime.now().isoformat(),
            }

            turn_results.append(result)

            # Save incrementally
            with open(results_file, "a") as f:
                f.write(json.dumps(result) + "\n")

        except Exception as e:
            logger.error(f"  Conv {conv_id} turn {turn_idx}: {e}")
            continue

    return turn_results


async def run_phase1(cfg: DictConfig) -> Path:
    """Main Phase 1 execution. ``cfg`` is the Hydra config from huang_phase1.yaml."""
    # Setup output directory
    output_dir = Path(cfg.logging.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    conv_dir = output_dir / "conversations"
    conv_dir.mkdir(exist_ok=True)

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(output_dir / "phase1.log"),
        ],
    )

    # Save the fully-resolved config in BOTH formats:
    #   - config.yaml  (Hydra-native, cross-benchmark standard)
    #   - config.json  (legacy, preserved for tooling that parses it)
    timestamp = datetime.now().strftime("%Y-%m-%d/%H-%M-%S")
    with open(output_dir / "config.yaml", "w") as f:
        f.write(OmegaConf.to_yaml(cfg, resolve=True))
    config_json = OmegaConf.to_container(cfg, resolve=True)
    config_json["timestamp"] = timestamp
    with open(output_dir / "config.json", "w") as f:
        json.dump(config_json, f, indent=2)

    logger.info(f"Phase 1 output: {output_dir}")

    # Load data
    logger.info("Loading WildChat conversations...")
    conversations = load_wildchat_conversations(
        limit=cfg.num_conversations,
        seed=cfg.seed,
        max_scan=cfg.max_scan,
        dataset_name=cfg.dataset,
    )
    logger.info(f"Loaded {len(conversations)} conversations")

    # Save conversations for reference
    for conv in conversations:
        with open(conv_dir / f"{conv['conversation_id'][:50]}.json", "w") as f:
            json.dump(conv, f, indent=2)

    # Setup model client
    model_client = get_model_client(cfg.respondent_model)

    # Results file
    results_file = output_dir / "turn_results.jsonl"
    results_file.touch()

    # Process conversations with concurrency limit
    semaphore = asyncio.Semaphore(cfg.max_concurrent)
    rng = random.Random(cfg.seed)
    all_results = []

    async def process_with_semaphore(conv):
        async with semaphore:
            logger.info(f"Processing conversation {conv['conversation_id'][:30]}... "
                        f"({conv['metadata']['num_rounds']} rounds)")
            return await process_conversation(
                conv, model_client, cfg.respondent_model, cfg.judge_model,
                cfg.classifier_model, results_file, rng,
            )

    tasks = [process_with_semaphore(conv) for conv in conversations]
    results_per_conv = await asyncio.gather(*tasks, return_exceptions=True)

    for r in results_per_conv:
        if isinstance(r, Exception):
            logger.error(f"Conversation failed: {r}")
        elif r:
            all_results.extend(r)

    # Aggregate
    logger.info(f"Aggregating {len(all_results)} turn results...")
    if not all_results:
        # Reload from file in case some were saved incrementally
        all_results = []
        with open(results_file) as f:
            for line in f:
                if line.strip():
                    all_results.append(json.loads(line))

    metrics, ao_failures = aggregate_phase1(all_results)

    # Save outputs
    with open(output_dir / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    with open(output_dir / "ao_failure_turns.json", "w") as f:
        json.dump(ao_failures, f, indent=2)

    write_breakdown_csv(all_results, ["fc_vs_ao"], output_dir / "breakdown_by_type.csv")

    summary = format_summary(metrics)
    with open(output_dir / "summary.txt", "w") as f:
        f.write(summary)

    # Cross-benchmark-standard run summary. Written to ``run_summary.json``
    # rather than ``results.json`` because LiC's ``results.json`` is a list of
    # per-sample dicts (legacy schema). The cross-benchmark aggregator in
    # ``scripts/aggregate_results.py`` prefers ``run_summary.json`` and falls
    # back to per-benchmark conventions when it's missing.
    run_summary = {
        "benchmark": "huang_phase1",
        "experiment_name": cfg.experiment_name,
        "num_conversations": cfg.num_conversations,
        "num_turns": len(all_results),
        "num_ao_failures": len(ao_failures),
        "metrics": metrics,
        "output_dir": str(output_dir),
        "timestamp": timestamp,
    }
    with open(output_dir / "run_summary.json", "w") as f:
        json.dump(run_summary, f, indent=2)

    print(summary)
    logger.info(f"Phase 1 complete. Results in {output_dir}")
    logger.info(f"AO failure turns: {len(ao_failures)} -- use these for Phase 2")

    return output_dir


@hydra.main(config_path="../config", config_name="huang_phase1", version_base=None)
def main(cfg: DictConfig) -> None:
    """Hydra entry point for Phase 1.

    Example invocations:
        python -m ctx_editor.huang_eval.run_phase1
        python -m ctx_editor.huang_eval.run_phase1 num_conversations=30 seed=42
        python -m ctx_editor.huang_eval.run_phase1 --multirun seed=42,43,44
    """
    print(f"\nOutput directory: {cfg.logging.output_dir}\n")
    asyncio.run(run_phase1(cfg))


if __name__ == "__main__":
    main()
