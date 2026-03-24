"""Classify conversation turns per Huang et al. taxonomy.

Categories:
- new_ask: standalone prompt, no dependency on prior context
- feedback: user provides concrete, actionable feedback on prior response
- no_feedback: user references prior response without concrete feedback
  (this is the ~33% where AO struggles)
"""

import json
import logging
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models.base import ModelClient

logger = logging.getLogger(__name__)

_PROMPT_DIR = Path(__file__).parent / "prompts"
_CLASSIFIER_PROMPT = (_PROMPT_DIR / "turn_classifier.txt").read_text()


@dataclass
class TurnClassification:
    turn_index: int
    turn_type: str  # "new_ask" | "feedback" | "no_feedback"
    context_dependent_elements: list[str]
    confidence: int
    raw_output: str


def _format_conversation_context(
    turns: list[dict[str, str]],
    up_to_index: int,
) -> str:
    """Format conversation turns up to (but not including) the target turn."""
    parts = []
    for msg in turns[:up_to_index]:
        parts.append(f"[{msg['role']}]\n{msg['content']}")
    return "\n\n".join(parts) if parts else "(No prior context)"


def _parse_json(text: str) -> dict | None:
    """Extract JSON from LLM response."""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        pass
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.split("\n")
        if lines[-1].strip() == "```":
            lines = lines[1:-1]
        else:
            lines = lines[1:]
        stripped = "\n".join(lines)
        try:
            return json.loads(stripped)
        except (json.JSONDecodeError, TypeError):
            pass
    start = text.find("{")
    if start != -1:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start : i + 1])
                    except (json.JSONDecodeError, TypeError):
                        break
    return None


async def classify_turn(
    turns: list[dict[str, str]],
    turn_index: int,
    model_client: "ModelClient",
    model: str = "gpt-5",
) -> TurnClassification:
    """Classify a single turn using Huang's classifier prompt.

    Args:
        turns: Full conversation turns list.
        turn_index: Index of the user turn to classify (must be a user turn).
        model_client: Model client for API calls.
        model: Model to use for classification.

    Returns:
        TurnClassification with turn type and metadata.
    """
    current_turn = turns[turn_index]
    assert current_turn["role"] == "user", f"Turn {turn_index} is not a user turn"

    context_str = _format_conversation_context(turns, turn_index)

    prompt = _CLASSIFIER_PROMPT.replace(
        "{conversation_context}", context_str
    ).replace(
        "{current_round_prompt}", current_turn["content"]
    )

    response = await model_client.generate(
        messages=[{"role": "user", "content": prompt}],
        model=model,
        temperature=0.0,
        timeout=30,
    )

    parsed = _parse_json(response.content)

    if parsed and "category" in parsed:
        turn_type = parsed["category"]
        if turn_type not in ("new_ask", "feedback", "no_feedback"):
            logger.warning(f"Unexpected turn type '{turn_type}', defaulting to 'feedback'")
            turn_type = "feedback"
        return TurnClassification(
            turn_index=turn_index,
            turn_type=turn_type,
            context_dependent_elements=parsed.get("context_dependent_elements", []),
            confidence=parsed.get("confidence", 0),
            raw_output=response.content,
        )

    logger.warning(f"Failed to parse classifier output for turn {turn_index}")
    return TurnClassification(
        turn_index=turn_index,
        turn_type="feedback",  # safe default
        context_dependent_elements=[],
        confidence=0,
        raw_output=response.content,
    )
