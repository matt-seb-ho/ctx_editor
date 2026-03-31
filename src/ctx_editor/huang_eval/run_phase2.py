#!/usr/bin/env python3
"""Phase 2: Run S3 (and optionally S1.5) on AO failure turns from Phase 1.

Takes Phase 1 output, selects turns where AO lost to FC on quality,
and runs our context editing methods to demonstrate recovery.

Usage:
    python -m ctx_editor.huang_eval.run_phase2 \
        --phase1-dir outputs/huang_eval/phase1/2026-03-24/12-00-00 \
        --respondent-model gpt-5-mini \
        --judge-model gpt-5 \
        --analyzer-model gpt-5-mini
"""

import argparse
import asyncio
import json
import logging
import random
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")

from ..models import get_model_client
from .pairwise_judge import judge_pairwise
from .replay import generate_ao, generate_fc, generate_s2, generate_s3, generate_s15
from .aggregate import aggregate_phase2, load_turn_results, format_summary, write_breakdown_csv

logger = logging.getLogger(__name__)


def load_phase1_data(phase1_dir: Path) -> tuple[list[dict], list[dict], dict]:
    """Load Phase 1 results, AO failure turns, and conversation data.

    Returns:
        (phase1_results, ao_failures, conversations_by_id)
    """
    phase1_results = load_turn_results(phase1_dir / "turn_results.jsonl")

    with open(phase1_dir / "ao_failure_turns.json") as f:
        ao_failures = json.load(f)

    # Load conversations
    conversations = {}
    conv_dir = phase1_dir / "conversations"
    if conv_dir.exists():
        for conv_file in conv_dir.glob("*.json"):
            with open(conv_file) as f:
                conv = json.load(f)
                conversations[conv["conversation_id"]] = conv

    return phase1_results, ao_failures, conversations


async def process_failure_turn(
    conversation: dict,
    turn_index: int,
    turn_type: str,
    phase1_result: dict | None,
    model_client,
    respondent_model: str,
    judge_model: str,
    analyzer_model: str,
    run_s15: bool,
    memory=None,
    run_s2: bool,
    regenerate_baselines: bool,
    results_file: Path,
    rng: random.Random,
) -> dict | None:
    """Process a single AO failure turn with S3 (and optionally S1.5 and/or S2)."""
    turns = conversation["turns"]
    conv_id = conversation["conversation_id"]

    try:
        # We need the AO response for comparison. Regenerate or use cached.
        if not regenerate_baselines and phase1_result and "ao_response" in phase1_result:
            ao_response = phase1_result["ao_response"]
            fc_response = phase1_result.get("fc_response", "")
        else:
            # Regenerate AO/FC with the respondent model
            ao_response, fc_response = await asyncio.gather(
                generate_ao(turns, turn_index, model_client, respondent_model),
                generate_fc(turns, turn_index, model_client, respondent_model),
            )

        # Generate S3 response
        s3_response, s3_analysis = await generate_s3(
            turns, turn_index, model_client, respondent_model, analyzer_model,
        )

        # Judge: AO vs S3, FC vs S3
        ao_vs_s3 = await judge_pairwise(
            turns, turn_index, ao_response, s3_response, "ao", "s3",
            model_client, judge_model, rng,
        )
        fc_vs_s3 = await judge_pairwise(
            turns, turn_index, fc_response, s3_response, "fc", "s3",
            model_client, judge_model, rng,
        )

        result = {
            "conversation_id": conv_id,
            "turn_index": turn_index,
            "turn_type": turn_type,
            "user_message": turns[turn_index]["content"][:500],
            "ao_response": ao_response[:1000],
            "fc_response": fc_response[:1000],
            "s3_response": s3_response[:1000],
            "s3_analysis": s3_analysis,
            "judgments": {
                "ao_vs_s3": {
                    "quality_winner": ao_vs_s3.quality_winner,
                    "ontopic_winner": ao_vs_s3.ontopic_winner,
                    "quality_justification": ao_vs_s3.quality_justification,
                    "ontopic_justification": ao_vs_s3.ontopic_justification,
                    "confidence": ao_vs_s3.confidence,
                },
                "fc_vs_s3": {
                    "quality_winner": fc_vs_s3.quality_winner,
                    "ontopic_winner": fc_vs_s3.ontopic_winner,
                    "quality_justification": fc_vs_s3.quality_justification,
                    "ontopic_justification": fc_vs_s3.ontopic_justification,
                    "confidence": fc_vs_s3.confidence,
                },
            },
            "timestamp": datetime.now().isoformat(),
        }

        # Optionally run S1.5
        if run_s15:
            s15_response, s15_analysis = await generate_s15(
                turns, turn_index, model_client, respondent_model, analyzer_model,
                memory=memory,
            )
            ao_vs_s15 = await judge_pairwise(
                turns, turn_index, ao_response, s15_response, "ao", "s15",
                model_client, judge_model, rng,
            )
            fc_vs_s15 = await judge_pairwise(
                turns, turn_index, fc_response, s15_response, "fc", "s15",
                model_client, judge_model, rng,
            )
            result["s15_response"] = s15_response            result["s15_analysis"] = s15_analysis
            result["judgments"]["ao_vs_s15"] = {
                "quality_winner": ao_vs_s15.quality_winner,
                "ontopic_winner": ao_vs_s15.ontopic_winner,
                "quality_justification": ao_vs_s15.quality_justification,
                "ontopic_justification": ao_vs_s15.ontopic_justification,
                "confidence": ao_vs_s15.confidence,
            }
            result["judgments"]["fc_vs_s15"] = {
                "quality_winner": fc_vs_s15.quality_winner,
                "ontopic_winner": fc_vs_s15.ontopic_winner,
                "quality_justification": fc_vs_s15.quality_justification,
                "ontopic_justification": fc_vs_s15.ontopic_justification,
                "confidence": fc_vs_s15.confidence,
            }

        # Optionally run S2 (gated context edit with v11 analyzer)
        if run_s2:
            s2_response, s2_analysis = await generate_s2(
                turns, turn_index, model_client, respondent_model, analyzer_model,
            )
            ao_vs_s2 = await judge_pairwise(
                turns, turn_index, ao_response, s2_response, "ao", "s2",
                model_client, judge_model, rng,
            )
            fc_vs_s2 = await judge_pairwise(
                turns, turn_index, fc_response, s2_response, "fc", "s2",
                model_client, judge_model, rng,
            )
            result["s2_response"] = s2_response            result["s2_analysis"] = s2_analysis
            result["judgments"]["ao_vs_s2"] = {
                "quality_winner": ao_vs_s2.quality_winner,
                "ontopic_winner": ao_vs_s2.ontopic_winner,
                "quality_justification": ao_vs_s2.quality_justification,
                "ontopic_justification": ao_vs_s2.ontopic_justification,
                "confidence": ao_vs_s2.confidence,
            }
            result["judgments"]["fc_vs_s2"] = {
                "quality_winner": fc_vs_s2.quality_winner,
                "ontopic_winner": fc_vs_s2.ontopic_winner,
                "quality_justification": fc_vs_s2.quality_justification,
                "ontopic_justification": fc_vs_s2.ontopic_justification,
                "confidence": fc_vs_s2.confidence,
            }

        # Save incrementally
        with open(results_file, "a") as f:
            f.write(json.dumps(result) + "\n")

        return result

    except Exception as e:
        logger.error(f"Conv {conv_id} turn {turn_index}: {e}")
        return None


async def run_phase2(args):
    """Main Phase 2 execution."""
    phase1_dir = Path(args.phase1_dir)
    if not phase1_dir.exists():
        logger.error(f"Phase 1 directory not found: {phase1_dir}")
        return

    # Setup output directory
    timestamp = datetime.now().strftime("%Y-%m-%d/%H-%M-%S")
    output_dir = Path(args.output_dir.format(timestamp=timestamp))
    output_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(output_dir / "phase2.log"),
        ],
    )

    # Save config
    config = vars(args)
    config["timestamp"] = timestamp
    with open(output_dir / "config.json", "w") as f:
        json.dump(config, f, indent=2)

    logger.info(f"Phase 2 output: {output_dir}")
    logger.info(f"Loading Phase 1 data from {phase1_dir}")

    # Load Phase 1 data
    phase1_results, ao_failures, conversations = load_phase1_data(phase1_dir)
    logger.info(f"Phase 1: {len(phase1_results)} turn results, {len(ao_failures)} AO failures")

    # Override turns list if a custom file is provided
    if args.turns_file:
        with open(args.turns_file) as f:
            ao_failures = json.load(f)
        logger.info(f"Using custom turns file: {args.turns_file} ({len(ao_failures)} turns)")

    if not ao_failures:
        logger.warning("No turns to process. Nothing to do.")
        return

    # Limit if requested
    if args.max_turns and len(ao_failures) > args.max_turns:
        rng = random.Random(args.seed)
        ao_failures = rng.sample(ao_failures, args.max_turns)
        logger.info(f"Sampled {len(ao_failures)} failure turns")

    # Build lookup for Phase 1 results
    p1_lookup = {}
    for r in phase1_results:
        key = (r["conversation_id"], r["turn_index"])
        p1_lookup[key] = r

    # Filter to failures where we have conversation data
    valid_failures = []
    for f in ao_failures:
        if f["conversation_id"] in conversations:
            valid_failures.append(f)
        else:
            logger.warning(f"Conversation {f['conversation_id'][:30]} not found, skipping")

    logger.info(f"Processing {len(valid_failures)} AO failure turns")

    # Setup model client
    model_client = get_model_client(args.respondent_model)

    results_file = output_dir / "turn_results.jsonl"
    results_file.touch()

    rng = random.Random(args.seed)
    semaphore = asyncio.Semaphore(args.max_concurrent)
    all_results = []

    async def process_with_semaphore(failure):
        async with semaphore:
            conv = conversations[failure["conversation_id"]]
            p1_result = p1_lookup.get(
                (failure["conversation_id"], failure["turn_index"])
            )
            logger.info(
                f"Processing {failure['conversation_id'][:20]}... "
                f"turn {failure['turn_index']} ({failure.get('turn_type', '?')})"
            )
            return await process_failure_turn(
                conversation=conv,
                turn_index=failure["turn_index"],
                turn_type=failure.get("turn_type", "unknown"),
                phase1_result=p1_result,
                model_client=model_client,
                respondent_model=args.respondent_model,
                judge_model=args.judge_model,
                analyzer_model=args.analyzer_model,
                run_s15=args.run_s15,
                run_s2=args.run_s2,
                regenerate_baselines=getattr(args, "regenerate_baselines", False),
                results_file=results_file,
                rng=rng,
            )

    tasks = [process_with_semaphore(f) for f in valid_failures]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for r in results:
        if isinstance(r, Exception):
            logger.error(f"Turn failed: {r}")
        elif r:
            all_results.append(r)

    # Aggregate
    if not all_results:
        all_results = load_turn_results(results_file)

    metrics = aggregate_phase2(all_results)

    # Also load Phase 1 metrics for combined summary
    phase1_metrics_path = phase1_dir / "metrics.json"
    phase1_metrics = {}
    if phase1_metrics_path.exists():
        with open(phase1_metrics_path) as f:
            phase1_metrics = json.load(f)

    with open(output_dir / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    pair_keys = ["ao_vs_s3", "fc_vs_s3"]
    if args.run_s15:
        pair_keys.extend(["ao_vs_s15", "fc_vs_s15"])
    if args.run_s2:
        pair_keys.extend(["ao_vs_s2", "fc_vs_s2"])
    write_breakdown_csv(all_results, pair_keys, output_dir / "breakdown_by_type.csv")

    summary = format_summary(phase1_metrics, metrics)
    with open(output_dir / "summary.txt", "w") as f:
        f.write(summary)

    print(summary)
    logger.info(f"Phase 2 complete. Results in {output_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Phase 2: S3 evaluation on AO failure turns"
    )
    parser.add_argument("--phase1-dir", required=True,
                        help="Path to Phase 1 output directory")
    parser.add_argument("--respondent-model", default="gpt-5-mini",
                        help="Model for generating responses")
    parser.add_argument("--judge-model", default="gpt-5",
                        help="Model for pairwise judging")
    parser.add_argument("--analyzer-model", default="gpt-5-mini",
                        help="Model for S3 analyzer + compaction")
    parser.add_argument("--max-concurrent", type=int, default=5,
                        help="Max concurrent turn processing")
    parser.add_argument("--max-turns", type=int, default=None,
                        help="Max failure turns to process (None = all)")
    parser.add_argument("--turns-file", default=None,
                        help="Custom turns JSON file (overrides ao_failure_turns.json)")
    parser.add_argument("--run-s15", action="store_true",
                        help="Also run S1.5 (programmatic reset) alongside S3")
    parser.add_argument("--run-s2", action="store_true",
                        help="Also run S2 (gated context edit with v11 analyzer)")
    parser.add_argument("--regenerate-baselines", action="store_true",
                        help="Regenerate AO/FC with respondent model instead of using Phase 1 cache")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", default="outputs/huang_eval/phase2/{timestamp}",
                        help="Output directory (supports {timestamp})")

    args = parser.parse_args()
    asyncio.run(run_phase2(args))


if __name__ == "__main__":
    main()
