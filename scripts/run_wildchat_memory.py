#!/usr/bin/env python3
"""WildChat S1.5 with memory learning (train/eval split).

Two-phase design:
1. Train: Run S1.5 (no memory) on a subset of turns, learn a cheatsheet offline.
2. Eval: Run S1.5 with frozen memory on the remaining turns. Compare to S1.5 without memory.

Both phases use existing AO/FC responses from a prior Phase 2 run.

Usage:
    python scripts/run_wildchat_memory.py \
        --phase2-dir outputs/huang_eval/phase2/2026-03-29/21-43-34 \
        --phase1-dir outputs/huang_eval/phase1/2026-03-24/02-22-57 \
        --model deepseek/deepseek-v3.2 --judge-model gpt-5-mini \
        --train-split 0.33 --seed 42
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

    def _winner_str(j, cond_win, cond_lose):
        w = j.get("quality_winner", "?")
        if w == cond_win:
            return f"{cond_win.upper()} wins"
        elif w == cond_lose:
            return f"{cond_lose.upper()} wins"
        return "Tie"

    prompt = _TAKEAWAY_PROMPT.format(
        conversation_id=turn_result.get("conversation_id", "?"),
        turn_index=turn_result.get("turn_index", "?"),
        turn_type=turn_result.get("turn_type", "?"),
        conversation_context=conversation_context[:8000],
        task_spec=s15_analysis.get("user_intent", "(not available)"),
        aligned=s15_analysis.get("aligned", "(not available)"),
        issues=s15_analysis.get("issues", "(not available)"),
        edited=s15_analysis.get("edited", "?"),
        s15_vs_ao=_winner_str(ao_vs_s15, "s15", "ao"),
        s15_vs_fc=_winner_str(fc_vs_s15, "s15", "fc"),
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
    takeaway_parts = [f"From turn {i}:\n{t}" for i, t in enumerate(takeaways, 1)]

    prompt = _UNIFY_PROMPT.format(
        current_cheatsheet=current,
        takeaways="\n\n".join(takeaway_parts),
    )

    response = await model_client.generate(
        messages=[{"role": "user", "content": prompt}],
        model=model,
        temperature=0.3,
        timeout=60,
    )
    return response.content.strip()


async def run_s15_batch(
    indices: list[int],
    phase2_results: list[dict],
    conversations: dict,
    model_client,
    judge_client,
    model: str,
    judge_model: str,
    memory: CheatsheetMemory | None,
    rng: random.Random,
    output_dir: Path,
    label: str,
) -> list[dict]:
    """Run S1.5 + judging on a batch of turns in parallel."""
    turn_rngs = [random.Random(rng.randint(0, 2**32)) for _ in indices]

    async def process_turn(idx, turn_rng):
        orig = phase2_results[idx]
        conv_id = orig["conversation_id"]
        turn_index = orig["turn_index"]

        conv = conversations.get(conv_id)
        if not conv:
            return None

        turns = conv["turns"]

        try:
            s15_response, s15_analysis = await generate_s15(
                turns, turn_index, model_client, model, model,
                memory=memory,
            )
        except Exception as e:
            logger.error(f"[{label}] S1.5 failed {conv_id}:{turn_index}: {e}")
            return None

        ao_response = orig.get("ao_response", "")
        fc_response = orig.get("fc_response", "")

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
        except Exception as e:
            logger.error(f"[{label}] Judging failed {conv_id}:{turn_index}: {e}")
            return None

        result = {
            "conversation_id": conv_id,
            "turn_index": turn_index,
            "turn_type": orig.get("turn_type", "unknown"),
            "split": label,
            "s15_response": s15_response[:1000],
            "s15_analysis": s15_analysis,
            "ao_response": ao_response[:1000],
            "fc_response": fc_response[:1000],
            "memory_version": memory.version if memory else -1,
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
            "timestamp": datetime.now().isoformat(),
        }

        ao_w = ao_vs_s15.quality_winner
        fc_w = fc_vs_s15.quality_winner
        logger.info(f"  [{label}] {conv_id[:15]}:{turn_index} | AO:{ao_w} FC:{fc_w}")
        return result

    tasks = [process_turn(idx, rng) for idx, rng in zip(indices, turn_rngs)]
    results = await asyncio.gather(*tasks)
    valid = [r for r in results if r is not None]

    # Save incrementally
    with open(output_dir / "turn_results.jsonl", "a") as f:
        for r in valid:
            f.write(json.dumps(r) + "\n")

    return valid


def print_metrics(results: list[dict], label: str):
    """Print win rate metrics for a set of results."""
    for key in ["ao_vs_s15", "fc_vs_s15"]:
        cond1, _, cond2 = key.partition("_vs_")
        counts = defaultdict(int)
        by_type = defaultdict(lambda: defaultdict(int))
        for rec in results:
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
        print(f"  {cond1.upper()} vs {cond2.upper()} (n={n}): "
              f"{cond1.upper()} {c1/n:.1%}, {cond2.upper()} {c2/n:.1%}, Tie {t/n:.1%}")
        for tt in sorted(by_type):
            tc = by_type[tt]
            tn = sum(tc.values())
            print(f"    {tt} (n={tn}): {cond2.upper()} {tc.get(cond2,0)/tn:.1%}")


async def run_experiment(
    phase2_dir: str,
    phase1_dir: str,
    model: str,
    judge_model: str,
    train_split: float = 0.33,
    seed: int = 42,
    memory_path: str | None = None,
):
    """Run train/eval memory experiment."""
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
        "judge_model": judge_model,
        "train_split": train_split,
        "seed": seed,
        "memory_path": memory_path,
        "timestamp": datetime.now().isoformat(),
    }
    with open(output_dir / "config.json", "w") as f:
        json.dump(config, f, indent=2)

    logger.info(f"Output: {output_dir}")
    logger.info(f"Respondent/analyzer: {model}, Judge: {judge_model}")

    # Initialize clients
    model_client = get_model_client(model)
    judge_client = get_model_client(judge_model) if judge_model != model else model_client

    # Split turns
    rng = random.Random(seed)
    indices = list(range(len(phase2_results)))
    rng.shuffle(indices)

    n_train = int(len(indices) * train_split)
    train_indices = indices[:n_train]
    eval_indices = indices[n_train:]
    logger.info(f"Split: {len(train_indices)} train, {len(eval_indices)} eval")

    # ============================================================
    # PHASE 1: Train -- S1.5 without memory, learn cheatsheet
    # ============================================================
    logger.info(f"\n{'='*60}\nPHASE: TRAIN (no memory, {len(train_indices)} turns)\n{'='*60}")

    train_rng = random.Random(seed + 1)
    train_results = await run_s15_batch(
        train_indices, phase2_results, conversations,
        model_client, judge_client, model, judge_model,
        memory=None, rng=train_rng, output_dir=output_dir, label="train",
    )

    print(f"\n--- Train results (no memory, n={len(train_results)}) ---")
    print_metrics(train_results, "train")

    # Learn memory from train results
    memory = CheatsheetMemory.load(memory_path) if memory_path else CheatsheetMemory(_content="")

    logger.info(f"Learning memory from {len(train_results)} train turns...")

    # Reflect on all train turns in parallel
    async def _reflect(result):
        conv = conversations[result["conversation_id"]]
        context = format_conversation_context(conv["turns"], result["turn_index"])
        return await reflect_on_turn(result, context, model_client, model)

    takeaways = list(await asyncio.gather(*[_reflect(r) for r in train_results]))

    # Unify into memory
    new_content = await unify_takeaways(memory, takeaways, model_client, model)
    memory.update(new_content)
    memory.save(str(output_dir / "memory_trained.json"))
    logger.info(f"Memory learned: v{memory.version}, {len(memory.content.split())} words")
    logger.info(f"Memory content:\n{memory.content[:500]}...")

    # ============================================================
    # PHASE 2a: Eval -- S1.5 WITHOUT memory (baseline)
    # ============================================================
    logger.info(f"\n{'='*60}\nPHASE: EVAL BASELINE (no memory, {len(eval_indices)} turns)\n{'='*60}")

    eval_rng_baseline = random.Random(seed + 2)
    eval_baseline_results = await run_s15_batch(
        eval_indices, phase2_results, conversations,
        model_client, judge_client, model, judge_model,
        memory=None, rng=eval_rng_baseline, output_dir=output_dir, label="eval_baseline",
    )

    # ============================================================
    # PHASE 2b: Eval -- S1.5 WITH frozen memory
    # ============================================================
    logger.info(f"\n{'='*60}\nPHASE: EVAL MEMORY (frozen memory v{memory.version}, {len(eval_indices)} turns)\n{'='*60}")

    eval_rng_memory = random.Random(seed + 2)  # Same seed for same judge randomization
    eval_memory_results = await run_s15_batch(
        eval_indices, phase2_results, conversations,
        model_client, judge_client, model, judge_model,
        memory=memory, rng=eval_rng_memory, output_dir=output_dir, label="eval_memory",
    )

    # ============================================================
    # Results
    # ============================================================
    print(f"\n{'='*60}")
    print(f"WILDCHAT MEMORY EXPERIMENT: {model}")
    print(f"Judge: {judge_model}")
    print(f"{'='*60}")

    print(f"\n--- Train (no memory, n={len(train_results)}) ---")
    print_metrics(train_results, "train")

    print(f"\n--- Eval BASELINE (no memory, n={len(eval_baseline_results)}) ---")
    print_metrics(eval_baseline_results, "eval_baseline")

    print(f"\n--- Eval MEMORY (frozen v{memory.version}, n={len(eval_memory_results)}) ---")
    print_metrics(eval_memory_results, "eval_memory")

    print(f"\nMemory: {len(memory.content.split())} words")
    print(f"Output: {output_dir}")
    print(f"{'='*60}\n")

    # Save summary
    def _win_rates(results, key):
        cond1, _, cond2 = key.partition("_vs_")
        counts = defaultdict(int)
        for r in results:
            j = r.get("judgments", {}).get(key)
            if j:
                counts[j["quality_winner"]] += 1
        n = sum(counts.values())
        if n == 0:
            return {}
        return {f"{cond1}_wins": counts.get(cond1, 0)/n, f"{cond2}_wins": counts.get(cond2, 0)/n, "tie": counts.get("tie", 0)/n, "n": n}

    summary = {
        "model": model,
        "judge_model": judge_model,
        "train_split": train_split,
        "n_train": len(train_results),
        "n_eval": len(eval_baseline_results),
        "memory_words": len(memory.content.split()),
        "train": {k: _win_rates(train_results, k) for k in ["ao_vs_s15", "fc_vs_s15"]},
        "eval_baseline": {k: _win_rates(eval_baseline_results, k) for k in ["ao_vs_s15", "fc_vs_s15"]},
        "eval_memory": {k: _win_rates(eval_memory_results, k) for k in ["ao_vs_s15", "fc_vs_s15"]},
    }
    with open(output_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="WildChat S1.5 memory: train/eval split")
    parser.add_argument("--phase2-dir", required=True,
                        help="Phase 2 output dir with existing AO/FC/S1.5 results")
    parser.add_argument("--phase1-dir", required=True,
                        help="Phase 1 output dir with conversations/")
    parser.add_argument("--model", default="gpt-5-mini",
                        help="Model for S1.5 generation and analysis")
    parser.add_argument("--judge-model", default="gpt-5-mini",
                        help="Model for pairwise judging (can differ from respondent)")
    parser.add_argument("--train-split", type=float, default=0.33,
                        help="Fraction of turns for training (default: 0.33)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--memory-path", default=None,
                        help="Path to pre-existing memory to start from")

    args = parser.parse_args()
    asyncio.run(run_experiment(
        phase2_dir=args.phase2_dir,
        phase1_dir=args.phase1_dir,
        model=args.model,
        judge_model=args.judge_model,
        train_split=args.train_split,
        seed=args.seed,
        memory_path=args.memory_path,
    ))


if __name__ == "__main__":
    main()
