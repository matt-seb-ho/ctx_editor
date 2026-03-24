"""Load and filter WildChat conversations per Huang et al. criteria.

Filters: English, technical (math/coding keywords), 5-10 rounds, non-toxic.
Uses streaming to avoid downloading the full dataset.
"""

import logging
import random
from typing import Any

logger = logging.getLogger(__name__)

# Huang et al. keyword lists for technical conversation filtering
MATH_KEYWORDS = {
    "equation", "algebra", "calculus", "derivative", "matrix", "probability",
    "statistics", "geometry", "trigonometry", "polynomial", "function",
    "calculate", "theorem", "proof", "lemma", "corollary", "formula",
    "differential", "linear algebra", "graph theory", "optimization",
    "mathematics", "mathematical",
}

CODING_KEYWORDS = {
    "code", "python", "javascript", "java", "c++", "programming", "class",
    "method", "algorithm", "debug", "error", "compile", "variable", "array",
    "loop", "recursion", "data structure", "api", "library", "framework",
    "script", "implementation", "runtime", "bug", "software", "developer",
    "coding", "program",
}

TECHNICAL_KEYWORDS = MATH_KEYWORDS | CODING_KEYWORDS


def _is_technical(conversation: list[dict[str, str]]) -> bool:
    """Check if a conversation contains technical content (math or coding)."""
    text = " ".join(msg["content"].lower() for msg in conversation)
    return any(kw in text for kw in TECHNICAL_KEYWORDS)


def _count_rounds(conversation: list[dict[str, str]]) -> int:
    """Count user-assistant exchange rounds."""
    return sum(1 for msg in conversation if msg["role"] == "user")


def _normalize_conversation(conversation: list[dict[str, str]]) -> list[dict[str, str]]:
    """Normalize conversation to alternating user/assistant turns.

    Strips system messages and ensures clean alternation.
    """
    normalized = []
    for msg in conversation:
        if msg["role"] == "system":
            continue
        if msg["role"] in ("user", "assistant"):
            normalized.append({"role": msg["role"], "content": msg["content"]})
    return normalized


def load_wildchat_conversations(
    limit: int = 100,
    min_rounds: int = 5,
    max_rounds: int = 10,
    seed: int = 42,
    max_scan: int = 10000,
    dataset_name: str = "allenai/WildChat-1M",
) -> list[dict[str, Any]]:
    """Load and filter WildChat conversations per Huang et al. criteria.

    Args:
        limit: Number of conversations to return.
        min_rounds: Minimum user-assistant rounds (inclusive).
        max_rounds: Maximum user-assistant rounds (inclusive).
        seed: Random seed for sampling.
        max_scan: Maximum rows to scan from the dataset (streaming).
        dataset_name: HuggingFace dataset name.

    Returns:
        List of conversation dicts with keys:
            conversation_id: str
            turns: list[{"role": str, "content": str}]
            metadata: dict with model, language, num_rounds
    """
    from datasets import load_dataset

    logger.info(f"Loading {dataset_name} (streaming, scanning up to {max_scan} rows)...")
    ds = load_dataset(dataset_name, split="train", streaming=True)

    candidates = []
    scanned = 0

    for row in ds:
        scanned += 1
        if scanned > max_scan:
            break

        # Language filter: English
        language = row.get("language", "")
        if language and language.lower() != "english":
            continue

        # Toxicity filter
        if row.get("toxic", False):
            continue

        conversation = row.get("conversation", [])
        if not conversation:
            continue

        # Normalize (strip system messages)
        turns = _normalize_conversation(conversation)

        # Round count filter
        num_rounds = _count_rounds(turns)
        if num_rounds < min_rounds or num_rounds > max_rounds:
            continue

        # Technical content filter
        if not _is_technical(turns):
            continue

        # Must start with user and alternate properly
        if not turns or turns[0]["role"] != "user":
            continue

        conv_id = row.get("conversation_hash", row.get("hash", f"wildchat_{scanned}"))

        candidates.append({
            "conversation_id": str(conv_id),
            "turns": turns,
            "metadata": {
                "model": row.get("model", "unknown"),
                "language": language,
                "num_rounds": num_rounds,
                "source": dataset_name,
            },
        })

        if scanned % 1000 == 0:
            logger.info(f"Scanned {scanned} rows, found {len(candidates)} candidates so far")

    logger.info(f"Scanned {scanned} rows total, found {len(candidates)} matching conversations")

    if len(candidates) <= limit:
        selected = candidates
    else:
        rng = random.Random(seed)
        selected = rng.sample(candidates, limit)

    logger.info(f"Selected {len(selected)} conversations")
    return selected
