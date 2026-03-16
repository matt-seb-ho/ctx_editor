"""Dynamic data loaders for CollabLLM evaluation datasets."""

from typing import Any


def load_collabllm_math_hard(
    limit: int | None = None,
    split: str = "test",
) -> list[dict[str, Any]]:
    """Load MATH-Hard dataset from HuggingFace and convert to our sample format.

    Args:
        limit: Maximum number of samples to load. None for all.
        split: Dataset split to use (train/test).

    Returns:
        List of sample dicts with keys: task_id, task, task_desc,
        single_turn_prompt, single_turn_completion, single_turn_metadata.
    """
    from datasets import load_dataset

    ds = load_dataset("lighteval/MATH-Hard", split=split)

    samples = []
    for i, row in enumerate(ds):
        if limit and i >= limit:
            break
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

    return samples


COLLABLLM_DATASETS = {
    "math-hard": {
        "loader": load_collabllm_math_hard,
        "task_desc": "question answering",
        "extract_type": "answer",
    },
}


def load_collabllm_dataset(
    dataset_name: str,
    limit: int | None = None,
    split: str = "test",
) -> list[dict[str, Any]]:
    """Load a CollabLLM dataset by name.

    Args:
        dataset_name: Name of the dataset (e.g., "math-hard").
        limit: Maximum number of samples.
        split: Dataset split.

    Returns:
        List of sample dicts.
    """
    if dataset_name not in COLLABLLM_DATASETS:
        raise ValueError(
            f"Unknown dataset '{dataset_name}'. "
            f"Available: {list(COLLABLLM_DATASETS.keys())}"
        )
    loader = COLLABLLM_DATASETS[dataset_name]["loader"]
    return loader(limit=limit, split=split)
