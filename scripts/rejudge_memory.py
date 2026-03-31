#!/usr/bin/env python3
"""Re-judge memory experiment turn results with a different judge model.

Takes existing turn_results.jsonl from a memory experiment and re-runs
pairwise judging (AO vs S1.5, FC vs S1.5) using a specified judge model.
Does not regenerate any responses.

Usage:
    python scripts/rejudge_memory.py \
        --memory-dir outputs/huang_eval/memory/2026-03-30/13-57-16 \
        --phase1-dir outputs/huang_eval/phase1/2026-03-24/02-22-57 \
        --judge-model gpt-5 --seed 42
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

logger = get_logger("rejudge_memory")


def load_conversations(phase1_dir: str) -> dict[str, list[dict]]:
    conv_dir = Path(phase1_dir) / "conversations"
    conversations = {}
    for f in conv_dir.glob("*.json"):
        with open(f) as fh:
            data = json.load(fh)
        conversations[data["conversation_id"]] = data.get("turns", [])
    return conversations


async def rejudge(
    memory_dir: str,
    phase1_dir: str,
    judge_model: str,
    max_concurrent: int = 5,
    seed: int = 42,
):
    # Load data
    with open(Path(memory_dir) / "turn_results.jsonl") as f:
        turn_results = [json.loads(l) for l in f if l.strip()]
    conversations = load_conversations(phase1_dir)
    original_config = json.load(open(Path(memory_dir) / "config.json"))
    original_model = original_config.get("model", "unknown")

    logger.info(f"Loaded {len(turn_results)} turns from {memory_dir}")
    logger.info(f"Original respondent: {original_model}, new judge: {judge_model}")

    # Setup output
    timestamp = datetime.now().strftime("%Y-%m-%d/%H-%M-%S")
    output_dir = Path(f"outputs/huang_eval/rejudge_memory/{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(str(output_dir), level=20)

    config = {
        "memory_source": memory_dir,
        "phase1_source": phase1_dir,
        "original_respondent": original_model,
        "original_judge": original_config.get("judge_model", original_model),
        "new_judge": judge_model,
        "seed": seed,
        "timestamp": datetime.now().isoformat(),
    }
    with open(output_dir / "config.json", "w") as f:
        json.dump(config, f, indent=2)

    judge_client = get_model_client(judge_model)
    semaphore = asyncio.Semaphore(max_concurrent)

    rng = random.Random(seed)
    turn_seeds = [rng.randint(0, 2**32) for _ in range(len(turn_results))]

    async def rejudge_one(idx: int, rec: dict) -> dict:
        async with semaphore:
            conv_id = rec["conversation_id"]
            turn_index = rec["turn_index"]
            turns = conversations.get(conv_id, [])

            if not turns:
                logger.warning(f"No conversation for {conv_id}, skipping")
                return rec

            turn_rng = random.Random(turn_seeds[idx])

            ao_response = rec.get("ao_response", "")
            fc_response = rec.get("fc_response", "")
            s15_response = rec.get("s15_response", "")

            new_judgments = {}
            try:
                ao_vs_s15, fc_vs_s15 = await asyncio.gather(
                    judge_pairwise(
                        turns, turn_index, ao_response, s15_response, "ao", "s15",
                        judge_client, judge_model, turn_rng,
                    ),
                    judge_pairwise(
                        turns, turn_index, fc_response, s15_response, "fc", "s15",
                        judge_client, judge_model, turn_rng,
                    ),
                )
                for key, j in [("ao_vs_s15", ao_vs_s15), ("fc_vs_s15", fc_vs_s15)]:
                    new_judgments[key] = {
                        "quality_winner": j.quality_winner,
                        "quality_justification": j.quality_justification,
                        "ontopic_winner": j.ontopic_winner,
                        "ontopic_justification": j.ontopic_justification,
                        "confidence": j.confidence,
                    }
            except Exception as e:
                logger.error(f"Judge failed for {conv_id}:{turn_index}: {e}")
                for key in ["ao_vs_s15", "fc_vs_s15"]:
                    new_judgments[key] = {
                        "quality_winner": "tie", "ontopic_winner": "tie",
                        "quality_justification": f"error: {e}",
                        "ontopic_justification": f"error: {e}",
                        "confidence": 0.0,
                    }

            new_rec = dict(rec)
            new_rec["judgments"] = new_judgments
            new_rec["judge_model"] = judge_model

            ao_w = new_judgments["ao_vs_s15"]["quality_winner"]
            fc_w = new_judgments["fc_vs_s15"]["quality_winner"]
            split = rec.get("split", "?")
            logger.info(f"  [{split}] {conv_id[:15]}:{turn_index} | AO:{ao_w} FC:{fc_w}")
            return new_rec

    tasks = [rejudge_one(i, rec) for i, rec in enumerate(turn_results)]
    results = await asyncio.gather(*tasks)

    # Write results
    with open(output_dir / "turn_results.jsonl", "w") as f:
        for rec in results:
            f.write(json.dumps(rec) + "\n")

    # Print metrics by split
    splits = sorted(set(r.get("split", "all") for r in results))

    print(f"\n{'='*60}")
    print(f"RE-JUDGING COMPLETE")
    print(f"{'='*60}")
    print(f"Original respondent: {original_model}")
    print(f"Original judge: {config['original_judge']}")
    print(f"New judge: {judge_model}")
    print(f"Turns: {len(results)}")
    print()

    summary = {
        "original_respondent": original_model,
        "original_judge": config["original_judge"],
        "new_judge": judge_model,
        "n": len(results),
    }

    for split in splits:
        split_recs = [r for r in results if r.get("split", "all") == split]
        if not split_recs:
            continue

        print(f"--- {split} (n={len(split_recs)}) ---")
        summary[split] = {}

        for key in ["ao_vs_s15", "fc_vs_s15"]:
            cond1, _, cond2 = key.partition("_vs_")
            counts = defaultdict(int)
            by_type = defaultdict(lambda: defaultdict(int))

            for rec in split_recs:
                j = rec.get("judgments", {}).get(key)
                if not j:
                    continue
                counts[j["quality_winner"]] += 1
                by_type[rec["turn_type"]][j["quality_winner"]] += 1

            n = sum(counts.values())
            if n == 0:
                continue

            c1 = counts.get(cond1, 0)
            c2 = counts.get(cond2, 0)
            t = counts.get("tie", 0)
            print(f"  {cond1.upper()} vs {cond2.upper()}: "
                  f"{cond1.upper()} {c1/n:.1%}, {cond2.upper()} {c2/n:.1%}, Tie {t/n:.1%}")
            for tt in sorted(by_type):
                tc = by_type[tt]
                tn = sum(tc.values())
                print(f"    {tt} (n={tn}): {cond2.upper()} {tc.get(cond2,0)/tn:.1%}")

            summary[split][key] = {
                f"{cond1}_wins": c1/n, f"{cond2}_wins": c2/n, "tie": t/n, "n": n,
            }
        print()

    with open(output_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(f"Output: {output_dir}")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="Re-judge memory experiment with different judge")
    parser.add_argument("--memory-dir", required=True, help="Memory experiment output dir")
    parser.add_argument("--phase1-dir", required=True, help="Phase 1 dir with conversations/")
    parser.add_argument("--judge-model", required=True, help="Judge model")
    parser.add_argument("--max-concurrent", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)

    args = parser.parse_args()
    asyncio.run(rejudge(
        memory_dir=args.memory_dir,
        phase1_dir=args.phase1_dir,
        judge_model=args.judge_model,
        max_concurrent=args.max_concurrent,
        seed=args.seed,
    ))


if __name__ == "__main__":
    main()
