#!/usr/bin/env python3
"""WildChat S1.5 with memory learning.

Re-runs S1.5 on Phase 2 AO-failure turns with accumulating memory.
Processes turns sequentially so later turns benefit from lessons learned
from earlier turns. Uses existing AO/FC responses from a prior Phase 2 run.

Usage:
    python scripts/run_wildchat_memory.py \
        --phase2-dir outputs/huang_eval/phase2/2026-03-24/02-54-36 \
        --phase1-dir outputs/huang_eval/phase1/2026-03-24/02-22-57 \
        --model gpt-5-mini --batch-size 5 --seed 42
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
from ctx_editor.huang_eval.replay import generate_s15
from ctx_editor.memory.cheatsheet import CheatsheetMemory
from ctx_editor.models import get_model_client
from ctx_editor.utils.logging import setup_logging, get_logger

logger = get_logger("wildchat_memory")

_PROMPTS_DIR = Path(__file__).parent.parent / "src" / "ctx_editor" / "huang_eval" / "prompts"
_TAKEAWAY_PROMPT = (_PROMPTS_DIR / "wildchat_reflect_takeaways.txt").read_text()
_UNIFY_PROMPT = (
    Path(__file__).parent.parent / "src" / "ctx_editor" / "memory" / "prompts" / "unify_takeaways.txt"
).read_text()


def load_conversations(phase1_dir: str) -> dict[str, dict]:
    """Load conversation data from Phase 1."""
    conv_dir = Path(phase1_dir) / "conversations"
    conversations = {}
    for f in conv_dir.glob("*.json"):
        with open(f) as fh:
            data = json.load(fh)
        conversations[data["conversation_id"]] = data
    return conversations


def load_phase2_results(phase2_dir: str) -> list[dict]:
    """Load existing Phase 2 turn results (for AO/FC responses)."""
    results = []
    with open(Path(phase2_dir) / "turn_results.jsonl") as f:
        for line in f:
            if line.strip():
                results.append(json.loads(line))
    return results


def format_conversation_context(turns: list[dict], turn_index: int) -> str:
    """Format conversation up to turn_index for the reflection prompt."""
    parts = []
    for i, msg in enumerate(turns):
        if i >= turn_index:
            break
        parts.append(f"[{msg['role']}]\n{msg['content']}")
    # Include the target user message
    if turn_index < len(turns):
        parts.append(f"[user]\n{turns[turn_index]['content']}")
    return "\n\n".join(parts)


async def reflect_on_turn(
    turn_result: dict,
    conversation_context: str,
    model_client,
    model: str,
) -> str:
    """Generate takeaways from a single turn result."""
    s15_analysis = turn_result.get("s15_analysis", {})
    judgments = turn_result.get("judgments", {})

    ao_vs_s15 = judgments.get("ao_vs_s15", {})
    fc_vs_s15 = judgments.get("fc_vs_s15", {})

    s15_vs_ao = f"S1.5 {ao_vs_s15.get('quality_winner', '?')}"
    if ao_vs_s15.get("quality_winner") == "s15":
        s15_vs_ao = "S1.5 wins"
    elif ao_vs_s15.get("quality_winner") == "ao":
        s15_vs_ao = "AO wins"
    else:
        s15_vs_ao = "Tie"

    s15_vs_fc = f"S1.5 {fc_vs_s15.get('quality_winner', '?')}"
    if fc_vs_s15.get("quality_winner") == "s15":
        s15_vs_fc = "S1.5 wins"
    elif fc_vs_s15.get("quality_winner") == "fc":
        s15_vs_fc = "FC wins"
    else:
        s15_vs_fc = "Tie"

    prompt = _TAKEAWAY_PROMPT.format(
        conversation_id=turn_result.get("conversation_id", "?"),
        turn_index=turn_result.get("turn_index", "?"),
        turn_type=turn_result.get("turn_type", "?"),
        conversation_context=conversation_context[:8000],
        task_spec=s15_analysis.get("user_intent", "(not available)"),
        aligned=s15_analysis.get("aligned", "(not available)"),
        issues=s15_analysis.get("issues", "(not available)"),
        edited=s15_analysis.get("edited", "?"),
        s15_vs_ao=s15_vs_ao,
        s15_vs_fc=s15_vs_fc,
    )

    response = await model_client.generate(
        messages=[{"role": "user", "content": prompt}],
        model=model,
        temperature=0.3,
        timeout=60,
    )
    return response.content.strip()


async def unify_takeaways(
    memory: CheatsheetMemory,
    takeaways: list[str],
    model_client,
    model: str,
) -> str:
    """Merge takeaways into updated cheatsheet."""
    current = memory.content if memory.content else "(empty)"

    takeaway_parts = []
    for i, t in enumerate(takeaways, 1):
        takeaway_parts.append(f"From turn {i}:\n{t}")
    takeaways_text = "\n\n".join(takeaway_parts)

    prompt = _UNIFY_PROMPT.format(
        current_cheatsheet=current,
        takeaways=takeaways_text,
    )

    response = await model_client.generate(
        messages=[{"role": "user", "content": prompt}],
        model=model,
        temperature=0.3,
        timeout=60,
    )
    return response.content.strip()


async def run_experiment(
    phase2_dir: str,
    phase1_dir: str,
    model: str,
    batch_size: int = 5,
    seed: int = 42,
    memory_path: str | None = None,
):
    """Run S1.5 with memory learning on WildChat AO-failure turns."""
    # Load data
    phase2_results = load_phase2_results(phase2_dir)
    conversations = load_conversations(phase1_dir)
    logger.info(f"Loaded {len(phase2_results)} turn results, {len(conversations)} conversations")

    # Setup output
    timestamp = datetime.now().strftime("%Y-%m-%d/%H-%M-%S")
    output_dir = Path(f"outputs/huang_eval/memory/{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(str(output_dir), level=20)

    config = {
        "phase2_source": phase2_dir,
        "phase1_source": phase1_dir,
        "model": model,
        "batch_size": batch_size,
        "seed": seed,
        "memory_path": memory_path,
        "timestamp": datetime.now().isoformat(),
    }
    with open(output_dir / "config.json", "w") as f:
        json.dump(config, f, indent=2)

    logger.info(f"Output: {output_dir}")
    logger.info(f"Model: {model}, batch_size: {batch_size}")

    # Initialize model client and memory
    model_client = get_model_client(model)
    memory = CheatsheetMemory.load(memory_path) if memory_path else CheatsheetMemory(_content="")

    # Shuffle turns for consistent ordering
    rng = random.Random(seed)
    turns_order = list(range(len(phase2_results)))
    rng.shuffle(turns_order)

    all_results = []
    memory_versions = []  # Track memory evolution

    # Process in batches
    batches = [turns_order[i:i + batch_size] for i in range(0, len(turns_order), batch_size)]

    for batch_num, batch_indices in enumerate(batches, 1):
        logger.info(f"\n--- Batch {batch_num}/{len(batches)} (memory v{memory.version}) ---")
        if memory.content:
            logger.info(f"Memory ({len(memory.content.split())} words): {memory.content[:200]}...")

        batch_results = []
        batch_rng = random.Random(seed + batch_num)

        for idx in batch_indices:
            orig = phase2_results[idx]
            conv_id = orig["conversation_id"]
            turn_index = orig["turn_index"]

            conv = conversations.get(conv_id)
            if not conv:
                logger.warning(f"Conversation {conv_id} not found, skipping")
                continue

            turns = conv["turns"]

            # Generate S1.5 with current memory
            try:
                s15_response, s15_analysis = await generate_s15(
                    turns, turn_index, model_client, model, model,
                    memory=memory,
                )
            except Exception as e:
                logger.error(f"S1.5 generation failed for {conv_id}:{turn_index}: {e}")
                continue

            # Judge against AO and FC (reuse existing baselines from Phase 2)
            ao_response = orig.get("ao_response", "")
            fc_response = orig.get("fc_response", "")

            try:
                ao_vs_s15 = await judge_pairwise(
                    turns, turn_index, ao_response, s15_response, "ao", "s15",
                    model_client, model, batch_rng,
                )
                fc_vs_s15 = await judge_pairwise(
                    turns, turn_index, fc_response, s15_response, "fc", "s15",
                    model_client, model, batch_rng,
                )
            except Exception as e:
                logger.error(f"Judging failed for {conv_id}:{turn_index}: {e}")
                continue

            result = {
                "conversation_id": conv_id,
                "turn_index": turn_index,
                "turn_type": orig.get("turn_type", "unknown"),
                "s15_response": s15_response[:1000],
                "s15_analysis": s15_analysis,
                "ao_response": ao_response[:1000],
                "fc_response": fc_response[:1000],
                "judgments": {
                    "ao_vs_s15": {
                        "quality_winner": ao_vs_s15.quality_winner,
                        "quality_justification": ao_vs_s15.quality_justification,
                        "ontopic_winner": ao_vs_s15.ontopic_winner,
                        "ontopic_justification": ao_vs_s15.ontopic_justification,
                        "confidence": ao_vs_s15.confidence,
                    },
                    "fc_vs_s15": {
                        "quality_winner": fc_vs_s15.quality_winner,
                        "quality_justification": fc_vs_s15.quality_justification,
                        "ontopic_winner": fc_vs_s15.ontopic_winner,
                        "ontopic_justification": fc_vs_s15.ontopic_justification,
                        "confidence": fc_vs_s15.confidence,
                    },
                },
                "memory_version": memory.version,
                "timestamp": datetime.now().isoformat(),
            }

            batch_results.append(result)
            all_results.append(result)

            # Save incrementally
            with open(output_dir / "turn_results.jsonl", "a") as f:
                f.write(json.dumps(result) + "\n")

            ao_winner = ao_vs_s15.quality_winner
            fc_winner = fc_vs_s15.quality_winner
            logger.info(
                f"  [{conv_id[:15]}:{turn_index}] "
                f"vs AO: {ao_winner}, vs FC: {fc_winner} "
                f"(mem v{memory.version})"
            )

        # Learn from this batch
        if batch_results:
            logger.info(f"Learning from {len(batch_results)} turns...")

            # Step 1: Reflect on each turn
            takeaways = []
            for result in batch_results:
                conv_id = result["conversation_id"]
                conv = conversations[conv_id]
                context = format_conversation_context(conv["turns"], result["turn_index"])

                takeaway = await reflect_on_turn(result, context, model_client, model)
                takeaways.append(takeaway)

            # Step 2: Unify into memory
            new_content = await unify_takeaways(memory, takeaways, model_client, model)
            memory.update(new_content)

            memory_versions.append({
                "version": memory.version,
                "batch": batch_num,
                "word_count": len(memory.content.split()),
                "content": memory.content,
                "batch_size": len(batch_results),
            })

            # Save memory checkpoint
            memory.save(str(output_dir / f"memory_v{memory.version}.json"))
            logger.info(f"Memory updated to v{memory.version} ({len(memory.content.split())} words)")

    # Save final memory
    memory.save(str(output_dir / "memory_final.json"))

    # Save memory evolution
    with open(output_dir / "memory_evolution.json", "w") as f:
        json.dump(memory_versions, f, indent=2)

    # Compute metrics
    print(f"\n{'='*60}")
    print(f"WILDCHAT MEMORY EXPERIMENT RESULTS")
    print(f"{'='*60}")
    print(f"Model: {model}")
    print(f"Turns: {len(all_results)}")
    print(f"Batch size: {batch_size}")
    print(f"Final memory version: {memory.version}")
    print()

    for key in ["ao_vs_s15", "fc_vs_s15"]:
        cond1, _, cond2 = key.partition("_vs_")
        quality_counts = defaultdict(int)
        by_type = defaultdict(lambda: defaultdict(int))
        by_mem_version = defaultdict(lambda: defaultdict(int))

        for rec in all_results:
            j = rec.get("judgments", {}).get(key)
            if not j:
                continue
            quality_counts[j["quality_winner"]] += 1
            by_type[rec["turn_type"]][j["quality_winner"]] += 1
            by_mem_version[rec["memory_version"]][j["quality_winner"]] += 1

        n = sum(quality_counts.values())
        if n == 0:
            continue

        c1 = quality_counts.get(cond1, 0)
        c2 = quality_counts.get(cond2, 0)
        t = quality_counts.get("tie", 0)
        print(f"--- {cond1.upper()} vs {cond2.upper()} (n={n}) ---")
        print(f"  quality: {cond1.upper()} wins {c1/n:.1%}, {cond2.upper()} wins {c2/n:.1%}, Tie {t/n:.1%}")

        for tt in sorted(by_type.keys()):
            counts = by_type[tt]
            tt_n = sum(counts.values())
            print(f"    {tt} (n={tt_n}): {cond1.upper()} {counts.get(cond1,0)/tt_n:.1%}, {cond2.upper()} {counts.get(cond2,0)/tt_n:.1%}, Tie {counts.get('tie',0)/tt_n:.1%}")

        # Show by memory version
        print(f"  By memory version:")
        for v in sorted(by_mem_version.keys()):
            counts = by_mem_version[v]
            v_n = sum(counts.values())
            print(f"    v{v} (n={v_n}): {cond2.upper()} wins {counts.get(cond2,0)/v_n:.1%}")
        print()

    # Save summary
    summary = {
        "model": model,
        "n_turns": len(all_results),
        "batch_size": batch_size,
        "final_memory_version": memory.version,
    }
    for key in ["ao_vs_s15", "fc_vs_s15"]:
        cond1, _, cond2 = key.partition("_vs_")
        counts = defaultdict(int)
        for rec in all_results:
            j = rec.get("judgments", {}).get(key)
            if j:
                counts[j["quality_winner"]] += 1
        n = sum(counts.values())
        if n > 0:
            summary[key] = {
                f"{cond1}_wins": counts.get(cond1, 0) / n,
                f"{cond2}_wins": counts.get(cond2, 0) / n,
                "tie": counts.get("tie", 0) / n,
                "n": n,
            }
    with open(output_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(f"Output: {output_dir}")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="WildChat S1.5 with memory learning")
    parser.add_argument("--phase2-dir", required=True,
                        help="Phase 2 output dir with existing AO/FC/S1.5 results")
    parser.add_argument("--phase1-dir", required=True,
                        help="Phase 1 output dir with conversations/")
    parser.add_argument("--model", default="gpt-5-mini",
                        help="Model for S1.5 generation, judging, and memory learning")
    parser.add_argument("--batch-size", type=int, default=5,
                        help="Turns per batch before memory update")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--memory-path", default=None,
                        help="Path to pre-existing memory to start from")

    args = parser.parse_args()
    asyncio.run(run_experiment(
        phase2_dir=args.phase2_dir,
        phase1_dir=args.phase1_dir,
        model=args.model,
        batch_size=args.batch_size,
        seed=args.seed,
        memory_path=args.memory_path,
    ))


if __name__ == "__main__":
    main()
