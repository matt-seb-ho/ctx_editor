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

# Default (generic) prompts
PROMPTS = {
    "default": {
        "segment": (PROMPTS_DIR / "sharding_segment.txt").read_text(),
        "conversational": (PROMPTS_DIR / "sharding_conversational.txt").read_text(),
        "verification": (PROMPTS_DIR / "sharding_verification.txt").read_text(),
    },
    "code": {
        "segment": (PROMPTS_DIR / "sharding_segment_code.txt").read_text(),
        "conversational": (PROMPTS_DIR / "sharding_conversational_code.txt").read_text(),
        "verification": (PROMPTS_DIR / "sharding_verification.txt").read_text(),  # reuse generic
    },
}

# Active prompts (set based on --task flag and shard count args)
SEGMENT_PROMPT = None
CONVERSATIONAL_PROMPT = None
VERIFICATION_PROMPT = None


def set_active_prompts(task: str, target_shards: int = 0, max_shards: int = 0):
    global SEGMENT_PROMPT, CONVERSATIONAL_PROMPT, VERIFICATION_PROMPT
    prompt_set = PROMPTS.get(task, PROMPTS["default"])

    # Build guidance strings based on shard count config
    segment_text = prompt_set["segment"]
    conversational_text = prompt_set["conversational"]

    if target_shards > 0:
        # Replace the Minimalistic rule with a coarse-grouping rule
        for old_rule in [
            "- [Minimalistic] You should split the information in the segments to as small as possible. "
            "If you have a compound expression (X and Y), you should split it into two segments. "
            "Each segment should represent a unit of information.",
            "- [Minimalistic] You should split the information in the segments as small as possible. "
            "If you have a compound expression (X and Y), you should split it into two segments. "
            "Each segment should represent a unit of information.",
        ]:
            segment_text = segment_text.replace(
                old_rule,
                f"- [Coarse grouping] You MUST produce approximately {target_shards} segments "
                f"(no more than {max_shards or target_shards + 3}). "
                "Group related information together into meaningful chunks rather than splitting "
                "into fine-grained atomic units. For example: combine all constraints into one segment, "
                "combine all examples into one segment, merge a step description with its details. "
                "Each segment should represent a coherent topic, not a single atomic fact.",
            )
        segment_guidance = ""
    else:
        segment_guidance = ""

    if max_shards > 0:
        conversational_guidance = (
            f"- [Shard limit] CRITICAL: The total number of shards (initial shard + follow-up shards) "
            f"MUST be between {target_shards or max_shards - 3} and {max_shards}. "
            "Aggressively merge segments to stay within this limit. Combine all constraints into one shard, "
            "all examples into one shard, and group related algorithmic steps together. "
            "If you have more segments than the limit, you MUST merge until you are within the limit."
        )
    elif target_shards > 0:
        conversational_guidance = (
            f"- [Target count] Aim for approximately {target_shards} shards total "
            "(including the initial shard). Merge related segments to reach this target."
        )
    else:
        conversational_guidance = ""

    SEGMENT_PROMPT = segment_text.replace("{segment_guidance}", segment_guidance)
    CONVERSATIONAL_PROMPT = conversational_text.replace(
        "{conversational_guidance}", conversational_guidance
    )
    VERIFICATION_PROMPT = prompt_set["verification"]


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

    # Pass through any extra fields (e.g., LCB metadata, test cases, starter_code)
    passthrough_keys = {
        "question_title",
        "question_content",
        "platform",
        "contest_id",
        "contest_date",
        "starter_code",
        "difficulty",
        "public_test_cases",
        "private_test_cases",
        "metadata",
        "source",
    }
    for key in passthrough_keys:
        if key in item:
            output[key] = item[key]

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
    shard_info = ""
    if args.target_shards > 0:
        shard_info += f", target_shards={args.target_shards}"
    if args.max_shards > 0:
        shard_info += f", max_shards={args.max_shards}"
    print(
        f"Processing {len(items)} items with model={args.model}, "
        f"concurrency={concurrency}, timeout={timeout}s{shard_info}"
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
    parser.add_argument(
        "--task",
        default="default",
        choices=list(PROMPTS.keys()),
        help="Task type for prompt routing (default: default)",
    )
    parser.add_argument(
        "--target-shards",
        type=int,
        default=0,
        help="Target number of shards per item (0 = off, original behavior)",
    )
    parser.add_argument(
        "--max-shards",
        type=int,
        default=0,
        help="Hard max number of shards per item (0 = off, no limit)",
    )
    args = parser.parse_args()

    set_active_prompts(args.task, target_shards=args.target_shards, max_shards=args.max_shards)
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
