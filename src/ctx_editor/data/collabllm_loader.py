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
        code_prompt = row.get("code_prompt", "")
        solution = row.get("canonical_solution", "")

        samples.append(
            {
                "task_id": f"bigcodebench/{task_id}",
                "task": "collabllm_code",
                "task_desc": "coding",
                "single_turn_prompt": prompt,
                "single_turn_completion": code_prompt + solution,
                "single_turn_metadata": {
                    "source": "bigcodebench",
                    "entry_point": row.get("entry_point", ""),
                    "test": row.get("test", ""),
                    "extraction_requirement": (
                        "Your extraction should be executable code without any "
                        "the need of processing. You should start with the "
                        f"following code:\n\n{code_prompt}\n"
                    ),
                },
            }
        )

    if limit and limit < len(samples):
        rng = random.Random(seed)
        samples = rng.sample(samples, limit)

    return samples


def load_collabllm_medium(
    limit: int | None = None,
    split: str = "test",
    seed: int = 42,
) -> list[dict[str, Any]]:
    """Load Medium doc edit dataset (MediumDocEdit-Chat from CollabLLM paper).

    Loads Medium articles from HuggingFace, filters to short articles (<=512 tokens),
    and formats as document editing tasks.

    Args:
        limit: Maximum number of samples to load. None for all.
        split: Which split to return ("test" or "train").
        seed: Random seed for subsampling.

    Returns:
        List of sample dicts.
    """
    import tiktoken
    from datasets import load_dataset

    raw = load_dataset("Kamaljp/medium_articles")
    full = [row for row in raw["train"] if row.get("timestamp") is not None]
    full.sort(key=lambda x: x["timestamp"])

    # Match CollabLLM's split ratios
    n_total = len(full)
    n_test = int(n_total * 0.005)
    n_train = int(n_total * 0.020)

    recent = full[-(n_train + n_test) :]
    random.Random(42).shuffle(recent)  # deterministic split

    test_set = set(id(row) for row in recent[:n_test])
    train_set = set(id(row) for row in recent[n_test:])

    encoding = tiktoken.get_encoding("cl100k_base")

    samples = []
    for row in recent:
        tokens = len(encoding.encode(row["text"], disallowed_special=()))
        if tokens > 512:
            continue

        is_test = id(row) in test_set
        row_split = "test" if is_test else "train"
        if row_split != split:
            continue

        title = row["title"]
        prompt = f"Please write an article in less than 500 words about:\n\n{title}\n\n{row['text']}"

        samples.append(
            {
                "task_id": f"medium/{len(samples)}",
                "task": "collabllm_doc",
                "task_desc": "document editing",
                "single_turn_prompt": prompt,
                "single_turn_completion": row["text"],
                "single_turn_metadata": {
                    "source": "medium",
                    "title": title,
                    "url": row.get("url", ""),
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
        "extract_type": "runnable code",
        "eval_method": "pass_rate",
        "default_split": "v0.1.2",
    },
    "medium": {
        "loader": load_collabllm_medium,
        "task_desc": "document editing",
        "extract_type": "document",
        "eval_method": "conversation_judge",
        "default_split": "test",
    },
}


def load_collabllm_dataset(
    dataset_name: str,
    limit: int | None = None,
    split: str | None = None,
    seed: int = 42,
) -> list[dict[str, Any]]:
    """Load a CollabLLM dataset by name.

    Args:
        dataset_name: Name of the dataset (e.g., "math-hard", "bigcodebench").
        limit: Maximum number of samples.
        split: Dataset split. If None, uses the dataset's default split.
        seed: Random seed for the subsample draw. Defaults to 42, which is the
            value that was previously hardcoded in every loader — so omitting
            this argument reproduces all pre-2026-07-29 runs exactly.

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
    return loader(limit=limit, split=effective_split, seed=seed)
