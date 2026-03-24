#!/usr/bin/env python3
"""Phase 1: Run FC + AO on WildChat conversations, classify turns, judge pairwise.

Identifies AO failure cases (turns where FC > AO on quality) for Phase 2.

Usage:
    python -m ctx_editor.huang_eval.run_phase1 \
        --num-conversations 100 \
        --respondent-model gpt-5-mini \
        --judge-model gpt-5 \
        --max-concurrent 5
"""

import argparse
import asyncio
import json
import logging
import random
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

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
                "fc_response": fc_response[:1000],
                "ao_response": ao_response[:1000],
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


async def run_phase1(args):
    """Main Phase 1 execution."""
    # Setup output directory
    timestamp = datetime.now().strftime("%Y-%m-%d/%H-%M-%S")
    output_dir = Path(args.output_dir.format(timestamp=timestamp))
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

    # Save config
    config = vars(args)
    config["timestamp"] = timestamp
    with open(output_dir / "config.json", "w") as f:
        json.dump(config, f, indent=2)

    logger.info(f"Phase 1 output: {output_dir}")

    # Load data
    logger.info("Loading WildChat conversations...")
    conversations = load_wildchat_conversations(
        limit=args.num_conversations,
        seed=args.seed,
        max_scan=args.max_scan,
        dataset_name=args.dataset,
    )
    logger.info(f"Loaded {len(conversations)} conversations")

    # Save conversations for reference
    for conv in conversations:
        with open(conv_dir / f"{conv['conversation_id'][:50]}.json", "w") as f:
            json.dump(conv, f, indent=2)

    # Setup model client
    model_client = get_model_client(args.respondent_model)

    # Results file
    results_file = output_dir / "turn_results.jsonl"
    results_file.touch()

    # Process conversations with concurrency limit
    semaphore = asyncio.Semaphore(args.max_concurrent)
    rng = random.Random(args.seed)
    all_results = []

    async def process_with_semaphore(conv):
        async with semaphore:
            logger.info(f"Processing conversation {conv['conversation_id'][:30]}... "
                        f"({conv['metadata']['num_rounds']} rounds)")
            return await process_conversation(
                conv, model_client, args.respondent_model, args.judge_model,
                args.classifier_model, results_file, rng,
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

    print(summary)
    logger.info(f"Phase 1 complete. Results in {output_dir}")
    logger.info(f"AO failure turns: {len(ao_failures)} -- use these for Phase 2")

    return output_dir


def main():
    parser = argparse.ArgumentParser(
        description="Phase 1: FC+AO evaluation on WildChat conversations"
    )
    parser.add_argument("--num-conversations", type=int, default=100,
                        help="Number of conversations to evaluate")
    parser.add_argument("--respondent-model", default="gpt-5-mini",
                        help="Model for generating responses")
    parser.add_argument("--judge-model", default="gpt-5",
                        help="Model for pairwise judging")
    parser.add_argument("--classifier-model", default="gpt-5",
                        help="Model for turn classification")
    parser.add_argument("--max-concurrent", type=int, default=5,
                        help="Max concurrent conversations")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-scan", type=int, default=10000,
                        help="Max rows to scan from WildChat")
    parser.add_argument("--dataset", default="allenai/WildChat-1M",
                        help="HuggingFace dataset name")
    parser.add_argument("--output-dir", default="outputs/huang_eval/phase1/{timestamp}",
                        help="Output directory (supports {timestamp})")

    args = parser.parse_args()
    asyncio.run(run_phase1(args))


if __name__ == "__main__":
    main()
