"""Dynamic data loaders for CollabLLM evaluation datasets."""

import random
from typing import Any


def load_collabllm_math_hard(
    limit: int | None = None,
    split: str = "test",
    seed: int = 42,
) -> list[dict[str, Any]]:
    """Load MATH-Hard dataset from HuggingFace and convert to our sample format.

    Args:
        limit: Maximum number of samples to load. None for all.
        split: Dataset split to use (train/test).
        seed: Random seed for subsampling.

    Returns:
        List of sample dicts with keys: task_id, task, task_desc,
        single_turn_prompt, single_turn_completion, single_turn_metadata.
    """
    from datasets import load_dataset

    ds = load_dataset("lighteval/MATH-Hard", split=split)

    samples = []
    for i, row in enumerate(ds):
        samples.append(
            {
                "task_id": f"math-hard/{i}",
                "task": "collabllm_math",
                "task_desc": "question answering",
                "single_turn_prompt": row["problem"],
                "single_turn_completion": row["solution"],
                "single_turn_metadata": {
                    "level": row.get("level", ""),
                    "type": row.get("type", ""),
                },
            }
        )

    if limit and limit < len(samples):
        rng = random.Random(seed)
        samples = rng.sample(samples, limit)

    return samples


def load_collabllm_bigcodebench(
    limit: int | None = None,
    split: str = "v0.1.2",
    seed: int = 42,
) -> list[dict[str, Any]]:
    """Load BigCodeBench dataset from HuggingFace and convert to our sample format.

    Uses the bigcode/bigcodebench dataset (same as CollabLLM paper).

    Args:
        limit: Maximum number of samples to load. None for all.
        split: Dataset version/split (default: v0.1.2).
        seed: Random seed for subsampling.

    Returns:
        List of sample dicts.
    """
    from datasets import load_dataset

    ds = load_dataset("bigcode/bigcodebench", split=split)

    samples = []
    for i, row in enumerate(ds):
        # BigCodeBench has: task_id, instruct_prompt, canonical_solution, test, etc.
        task_id = row.get("task_id", f"bigcodebench/{i}")
        # Use instruct_prompt as the problem statement (what CollabLLM uses)
        prompt = row.get("instruct_prompt", "") or row.get("complete_prompt", "")
        solution = row.get("canonical_solution", "")

        samples.append(
            {
                "task_id": f"bigcodebench/{task_id}",
                "task": "collabllm_code",
                "task_desc": "coding",
                "single_turn_prompt": prompt,
                "single_turn_completion": solution,
                "single_turn_metadata": {
                    "source": "bigcodebench",
                },
            }
        )

    if limit and limit < len(samples):
        rng = random.Random(seed)
        samples = rng.sample(samples, limit)

    return samples


COLLABLLM_DATASETS = {
    "math-hard": {
        "loader": load_collabllm_math_hard,
        "task_desc": "question answering",
        "extract_type": "answer",
        "default_split": "test",
    },
    "bigcodebench": {
        "loader": load_collabllm_bigcodebench,
        "task_desc": "coding",
        "extract_type": "code",
        "default_split": "v0.1.2",
    },
}


def load_collabllm_dataset(
    dataset_name: str,
    limit: int | None = None,
    split: str | None = None,
) -> list[dict[str, Any]]:
    """Load a CollabLLM dataset by name.

    Args:
        dataset_name: Name of the dataset (e.g., "math-hard", "bigcodebench").
        limit: Maximum number of samples.
        split: Dataset split. If None, uses the dataset's default split.

    Returns:
        List of sample dicts.
    """
    if dataset_name not in COLLABLLM_DATASETS:
        raise ValueError(
            f"Unknown dataset '{dataset_name}'. "
            f"Available: {list(COLLABLLM_DATASETS.keys())}"
        )
    dataset_info = COLLABLLM_DATASETS[dataset_name]
    loader = dataset_info["loader"]
    effective_split = split or dataset_info.get("default_split", "test")
    return loader(limit=limit, split=effective_split)
