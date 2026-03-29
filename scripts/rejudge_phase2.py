#!/usr/bin/env python3
"""Re-judge Phase 2 turn results with a different judge model.

Takes existing turn_results.jsonl (with generated responses) and re-runs
pairwise judging using a specified judge model. Does not regenerate responses.

Usage:
    python scripts/rejudge_phase2.py \
        --phase2-dir outputs/huang_eval/phase2/2026-03-29/04-56-00 \
        --phase1-dir outputs/huang_eval/phase1/2026-03-24/02-22-57 \
        --judge-model gpt-5 \
        --max-concurrent 5 --seed 42
"""

import argparse
import asyncio
import json
import random
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(".env")

from ctx_editor.huang_eval.pairwise_judge import judge_pairwise
from ctx_editor.models import get_model_client
from ctx_editor.utils.logging import setup_logging, get_logger

logger = get_logger("rejudge")


def load_conversations(phase1_dir: str) -> dict[str, list[dict]]:
    """Load conversation turns from Phase 1 conversations directory."""
    conv_dir = Path(phase1_dir) / "conversations"
    conversations = {}
    for f in conv_dir.glob("*.json"):
        with open(f) as fh:
            data = json.load(fh)
        conv_id = data.get("conversation_id", f.stem)
        conversations[conv_id] = data.get("turns", [])
    return conversations


def load_turn_results(phase2_dir: str) -> list[dict]:
    """Load existing turn results."""
    results = []
    with open(Path(phase2_dir) / "turn_results.jsonl") as f:
        for line in f:
            if line.strip():
                results.append(json.loads(line))
    return results


async def rejudge(
    phase2_dir: str,
    phase1_dir: str,
    judge_model: str,
    max_concurrent: int = 5,
    seed: int = 42,
):
    """Re-judge all turn results with a new judge model."""
    # Load data
    turn_results = load_turn_results(phase2_dir)
    conversations = load_conversations(phase1_dir)
    logger.info(f"Loaded {len(turn_results)} turn results, {len(conversations)} conversations")

    # Setup output
    timestamp = datetime.now().strftime("%Y-%m-%d/%H-%M-%S")
    original_model = json.load(open(Path(phase2_dir) / "config.json")).get("respondent_model", "unknown")
    output_dir = Path(f"outputs/huang_eval/rejudge/{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(str(output_dir), level=20)

    logger.info(f"Re-judging {len(turn_results)} turns")
    logger.info(f"Original respondent: {original_model}")
    logger.info(f"New judge: {judge_model}")
    logger.info(f"Output: {output_dir}")

    # Save config
    config = {
        "phase2_source": phase2_dir,
        "phase1_source": phase1_dir,
        "original_respondent": original_model,
        "judge_model": judge_model,
        "seed": seed,
        "max_concurrent": max_concurrent,
        "timestamp": datetime.now().isoformat(),
    }
    with open(output_dir / "config.json", "w") as f:
        json.dump(config, f, indent=2)

    # Create judge client -- use get_model_client with the judge model name
    # but we need a client that can talk to the judge model's provider
    judge_client = get_model_client(judge_model)

    semaphore = asyncio.Semaphore(max_concurrent)
    rng = random.Random(seed)
    # Pre-generate per-turn seeds so concurrency doesn't affect randomization
    turn_seeds = [rng.randint(0, 2**32) for _ in range(len(turn_results))]

    async def rejudge_one(idx: int, rec: dict) -> dict:
        async with semaphore:
            conv_id = rec["conversation_id"]
            turn_index = rec["turn_index"]
            turns = conversations.get(conv_id, [])

            if not turns:
                logger.warning(f"No conversation found for {conv_id}, skipping")
                return rec

            turn_rng = random.Random(turn_seeds[idx])

            # Determine which comparisons to run
            comparisons = []
            if rec.get("s3_response"):
                comparisons.append(("ao", "s3", rec["ao_response"], rec["s3_response"]))
                comparisons.append(("fc", "s3", rec["fc_response"], rec["s3_response"]))
            if rec.get("s15_response"):
                comparisons.append(("ao", "s15", rec["ao_response"], rec["s15_response"]))
                comparisons.append(("fc", "s15", rec["fc_response"], rec["s15_response"]))
            if rec.get("s2_response"):
                comparisons.append(("ao", "s2", rec["ao_response"], rec["s2_response"]))
                comparisons.append(("fc", "s2", rec["fc_response"], rec["s2_response"]))

            new_judgments = {}
            for cond1, cond2, resp1, resp2 in comparisons:
                key = f"{cond1}_vs_{cond2}"
                try:
                    judgment = await judge_pairwise(
                        turns=turns,
                        turn_index=turn_index,
                        response_1=resp1,
                        response_2=resp2,
                        condition_1=cond1,
                        condition_2=cond2,
                        model_client=judge_client,
                        model=judge_model,
                        rng=turn_rng,
                    )
                    new_judgments[key] = {
                        "quality_winner": judgment.quality_winner,
                        "quality_justification": judgment.quality_justification,
                        "ontopic_winner": judgment.ontopic_winner,
                        "ontopic_justification": judgment.ontopic_justification,
                        "confidence": judgment.confidence,
                    }
                except Exception as e:
                    logger.error(f"Judge failed for {conv_id} turn {turn_index} {key}: {e}")
                    new_judgments[key] = {
                        "quality_winner": "tie",
                        "ontopic_winner": "tie",
                        "quality_justification": f"error: {e}",
                        "ontopic_justification": f"error: {e}",
                        "confidence": 0.0,
                    }

            # Return updated record
            new_rec = dict(rec)
            new_rec["judgments"] = new_judgments
            new_rec["judge_model"] = judge_model

            tag = " | ".join(
                f"{k}: {v['quality_winner']}" for k, v in new_judgments.items()
            )
            logger.info(f"  [{conv_id}:{turn_index}] {tag}")
            return new_rec

    # Run all
    tasks = [rejudge_one(i, rec) for i, rec in enumerate(turn_results)]
    results = await asyncio.gather(*tasks)

    # Write results
    with open(output_dir / "turn_results.jsonl", "w") as f:
        for rec in results:
            f.write(json.dumps(rec) + "\n")

    # Compute metrics
    comparison_keys = set()
    for rec in results:
        comparison_keys.update(rec.get("judgments", {}).keys())

    print(f"\n{'='*60}")
    print(f"RE-JUDGING COMPLETE")
    print(f"{'='*60}")
    print(f"Original respondent: {original_model}")
    print(f"Judge model: {judge_model}")
    print(f"Turns: {len(results)}")
    print()

    for key in sorted(comparison_keys):
        cond1, _, cond2 = key.partition("_vs_")
        quality_counts = defaultdict(int)
        ontopic_counts = defaultdict(int)
        by_type = defaultdict(lambda: defaultdict(int))
        n = 0

        for rec in results:
            j = rec.get("judgments", {}).get(key)
            if not j:
                continue
            n += 1
            quality_counts[j["quality_winner"]] += 1
            ontopic_counts[j["ontopic_winner"]] += 1
            by_type[rec["turn_type"]][j["quality_winner"]] += 1

        if n == 0:
            continue

        print(f"--- {cond1.upper()} vs {cond2.upper()} (n={n}) ---")
        c1q = quality_counts.get(cond1, 0)
        c2q = quality_counts.get(cond2, 0)
        tq = quality_counts.get("tie", 0)
        print(f"  quality: {cond1.upper()} wins {c1q/n:.1%}, {cond2.upper()} wins {c2q/n:.1%}, Tie {tq/n:.1%}")

        c1o = ontopic_counts.get(cond1, 0)
        c2o = ontopic_counts.get(cond2, 0)
        to_ = ontopic_counts.get("tie", 0)
        print(f"  ontopic: {cond1.upper()} wins {c1o/n:.1%}, {cond2.upper()} wins {c2o/n:.1%}, Tie {to_/n:.1%}")

        # By turn type
        for tt in sorted(by_type.keys()):
            counts = by_type[tt]
            tt_n = sum(counts.values())
            c1 = counts.get(cond1, 0)
            c2 = counts.get(cond2, 0)
            t = counts.get("tie", 0)
            print(f"    {tt} (n={tt_n}): {cond1.upper()} {c1/tt_n:.1%}, {cond2.upper()} {c2/tt_n:.1%}, Tie {t/tt_n:.1%}")
        print()

    print(f"Output: {output_dir}")
    print(f"{'='*60}\n")

    # Save summary
    summary = {"judge_model": judge_model, "original_respondent": original_model, "n": len(results)}
    for key in sorted(comparison_keys):
        cond1, _, cond2 = key.partition("_vs_")
        quality_counts = defaultdict(int)
        for rec in results:
            j = rec.get("judgments", {}).get(key)
            if j:
                quality_counts[j["quality_winner"]] += 1
        n = sum(quality_counts.values())
        if n > 0:
            summary[key] = {
                f"{cond1}_wins": quality_counts.get(cond1, 0) / n,
                f"{cond2}_wins": quality_counts.get(cond2, 0) / n,
                "tie": quality_counts.get("tie", 0) / n,
                "n": n,
            }
    with open(output_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Re-judge Phase 2 results with a different judge model")
    parser.add_argument("--phase2-dir", required=True, help="Phase 2 output directory with turn_results.jsonl")
    parser.add_argument("--phase1-dir", required=True, help="Phase 1 output directory with conversations/")
    parser.add_argument("--judge-model", required=True, help="Model to use as judge")
    parser.add_argument("--max-concurrent", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)

    args = parser.parse_args()
    asyncio.run(rejudge(
        phase2_dir=args.phase2_dir,
        phase1_dir=args.phase1_dir,
        judge_model=args.judge_model,
        max_concurrent=args.max_concurrent,
        seed=args.seed,
    ))


if __name__ == "__main__":
    main()
