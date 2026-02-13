#!/usr/bin/env python3
"""Convert single-turn questions into sharded multi-turn instructions.

Implements the 3-phase pipeline from "LLMs Get Lost in Multi-Turn Conversation":
1. Segmentation: Extract atomic content units (ACUs) from the original question
2. Conversational: Rephrase segments into conversational shards
3. Verification: Check that all information is preserved

Usage:
    python scripts/shard_instructions.py input.json -o output.json
    python scripts/shard_instructions.py input.json -o output.json --model gpt-4o --min-segments 3
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Add src to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Load environment variables before importing model
from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

from ctx_editor.models import get_model_client

# Global client instance
client = None

PROMPTS_DIR = PROJECT_ROOT / "prompts"
SEGMENT_PROMPT = (PROMPTS_DIR / "sharding_segment.txt").read_text()
CONVERSATIONAL_PROMPT = (PROMPTS_DIR / "sharding_conversational.txt").read_text()
VERIFICATION_PROMPT = (PROMPTS_DIR / "sharding_verification.txt").read_text()


async def segment_instruction(question: str, model: str, timeout: int = 30) -> dict | None:
    """Phase 1: Segment the instruction into atomic content units."""
    prompt = SEGMENT_PROMPT.format(instruction=question)
    messages = [{"role": "user", "content": prompt}]

    try:
        response = await client.generate(messages, model=model, is_json=True, timeout=timeout)
        return json.loads(response.content)
    except Exception as e:
        print(f"  [segment] Error: {e}")
        return None


async def make_conversational(
    question: str, segments: list[dict], model: str, timeout: int = 30
) -> dict | None:
    """Phase 2: Convert segments into conversational shards."""
    segments_str = json.dumps(segments, indent=2)
    prompt = CONVERSATIONAL_PROMPT.format(question=question, segments=segments_str)
    messages = [{"role": "user", "content": prompt}]

    try:
        response = await client.generate(messages, model=model, is_json=True, timeout=timeout)
        return json.loads(response.content)
    except Exception as e:
        print(f"  [conversational] Error: {e}")
        return None


async def verify_shards(
    question: str, shards_result: dict, model: str, timeout: int = 30
) -> dict | None:
    """Phase 3: Verify that all information is preserved in the shards."""
    shards_str = json.dumps(shards_result, indent=2)
    prompt = VERIFICATION_PROMPT.format(query=question, shards=shards_str)
    messages = [{"role": "user", "content": prompt}]

    try:
        response = await client.generate(messages, model=model, is_json=True, timeout=timeout)
        return json.loads(response.content)
    except Exception as e:
        print(f"  [verification] Error: {e}")
        return None


def format_shards(conv_result: dict) -> list[dict]:
    """Convert the conversational result into the standard shard format."""
    shards = []

    # First shard is the initial intent
    shards.append({"shard_id": 1, "shard": conv_result["initial_shard"]})

    # Remaining shards
    for i, shard_item in enumerate(conv_result.get("shards", []), start=2):
        shards.append({"shard_id": i, "shard": shard_item["shard"]})

    return shards


async def process_item(
    item: dict, model: str, min_segments: int, verify: bool, timeout: int = 30
) -> dict | None:
    """Process a single item through the sharding pipeline.

    Args:
        item: Dict with "question" key (and optionally "answer", "question_id")
        model: Model to use for LLM calls
        min_segments: Minimum number of segments required
        verify: Whether to run verification phase
        timeout: Request timeout in seconds per LLM call

    Returns:
        Processed item with shards added, or None if failed
    """
    question = item["question"]

    # Phase 1: Segmentation
    seg_result = await segment_instruction(question, model, timeout=timeout)
    if not seg_result:
        return None

    segments = seg_result.get("segments", [])
    if len(segments) < min_segments:
        print(f"  [skip] Only {len(segments)} segments (min: {min_segments})")
        return None

    # Phase 2: Conversational
    conv_result = await make_conversational(question, segments, model, timeout=timeout)
    if not conv_result:
        return None

    # Phase 3: Verification (optional)
    if verify:
        ver_result = await verify_shards(question, conv_result, model, timeout=timeout)
        if ver_result and ver_result.get("coverage") == "incomplete":
            print(f"  [warn] Incomplete coverage: {ver_result.get('missing_segment', 'unknown')}")

    # Format output
    shards = format_shards(conv_result)

    output = {
        "question": question,
        "full_spec_q": question,
        "shards": shards,
        "_segments": segments,
    }

    # Preserve original fields
    if "answer" in item:
        output["answer"] = item["answer"]
        output["ground_truth_a"] = item["answer"]
    if "question_id" in item:
        output["task_id"] = item["question_id"]
    if "task" in item:
        output["task"] = item["task"]

    return output


async def main_async(args):
    global client
    client = get_model_client(args.model)

    # Load input
    with open(args.input) as f:
        items = json.load(f)

    if not isinstance(items, list):
        items = [items]

    if args.limit:
        items = items[: args.limit]

    concurrency = args.concurrency
    timeout = args.timeout
    print(
        f"Processing {len(items)} items with model={args.model}, "
        f"concurrency={concurrency}, timeout={timeout}s"
    )

    semaphore = asyncio.Semaphore(concurrency)
    # Use a dict to preserve order: index -> result
    results_map: dict[int, dict] = {}
    failed = 0

    async def process_with_semaphore(idx: int, item: dict):
        nonlocal failed
        qid = item.get("question_id", item.get("task_id", idx))
        async with semaphore:
            print(f"[{idx + 1}/{len(items)}] Processing {qid}...")
            result = await process_item(
                item,
                model=args.model,
                min_segments=args.min_segments,
                verify=not args.no_verify,
                timeout=timeout,
            )
            if result:
                results_map[idx] = result
                print(f"  [{qid}] -> {len(result['shards'])} shards")
            else:
                failed += 1
                print(f"  [{qid}] -> FAILED")

    await asyncio.gather(*[process_with_semaphore(i, item) for i, item in enumerate(items)])

    # Collect results in original order
    results = [results_map[i] for i in sorted(results_map)]

    # Save output
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nDone! {len(results)}/{len(items)} items processed -> {args.output}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert single-turn questions into sharded multi-turn instructions"
    )
    parser.add_argument("input", type=Path, help="Input JSON file with questions")
    parser.add_argument("-o", "--output", type=Path, required=True, help="Output JSON file")
    parser.add_argument(
        "--model", default="gpt-4o-mini", help="Model to use (default: gpt-4o-mini)"
    )
    parser.add_argument(
        "--min-segments", type=int, default=3, help="Minimum segments required (default: 3)"
    )
    parser.add_argument("--no-verify", action="store_true", help="Skip verification phase")
    parser.add_argument("--limit", type=int, help="Process only first N items")
    parser.add_argument(
        "--concurrency", type=int, default=5, help="Max concurrent items (default: 5)"
    )
    parser.add_argument(
        "--timeout", type=int, default=300, help="Timeout per LLM call in seconds (default: 120)"
    )
    args = parser.parse_args()

    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
