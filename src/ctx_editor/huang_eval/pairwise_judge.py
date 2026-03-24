"""Pairwise LLM judge per Huang et al. methodology.

Compares two responses on Quality and On-Topic dimensions.
Randomizes A/B assignment to avoid position bias.
"""

import json
import logging
import random
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models.base import ModelClient

logger = logging.getLogger(__name__)

_PROMPT_DIR = Path(__file__).parent / "prompts"
_JUDGE_PROMPT = (_PROMPT_DIR / "pairwise_judge.txt").read_text()


@dataclass
class PairwiseJudgment:
    quality_winner: str  # condition name (e.g. "fc", "ao", "s3") or "tie"
    ontopic_winner: str  # condition name or "tie"
    quality_justification: str
    ontopic_justification: str
    confidence: float
    position_assignment: dict  # {"A": condition_name, "B": condition_name}
    raw_output: str


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


def _format_context(turns: list[dict[str, str]]) -> str:
    """Format conversation turns for the judge."""
    parts = []
    for msg in turns:
        parts.append(f"[{msg['role']}]\n{msg['content']}")
    return "\n\n".join(parts) if parts else "(No prior context)"


async def judge_pairwise(
    turns: list[dict[str, str]],
    turn_index: int,
    response_1: str,
    response_2: str,
    condition_1: str,
    condition_2: str,
    model_client: "ModelClient",
    model: str = "gpt-5",
    rng: random.Random | None = None,
) -> PairwiseJudgment:
    """Run pairwise comparison of two responses using Huang's judge prompt.

    Args:
        turns: Full conversation turns list (original).
        turn_index: Index of the user turn these responses answer.
        response_1: First response to compare.
        response_2: Second response to compare.
        condition_1: Name of first condition (e.g. "fc").
        condition_2: Name of second condition (e.g. "ao").
        model_client: Model client for API calls.
        model: Judge model.
        rng: Random instance for position randomization.

    Returns:
        PairwiseJudgment with winners mapped back to condition names.
    """
    if rng is None:
        rng = random.Random()

    # Count rounds
    user_turns = [i for i, t in enumerate(turns) if t["role"] == "user"]
    round_num = user_turns.index(turn_index) + 1 if turn_index in user_turns else 1
    total_rounds = len(user_turns)

    # Randomize position to avoid bias
    if rng.random() < 0.5:
        first_resp, second_resp = response_1, response_2
        assignment = {"A": condition_1, "B": condition_2}
    else:
        first_resp, second_resp = response_2, response_1
        assignment = {"A": condition_2, "B": condition_1}

    # Build context strings -- judge sees full original context
    context_str = _format_context(turns[:turn_index])

    prompt = (_JUDGE_PROMPT
        .replace("{round_num}", str(round_num))
        .replace("{total_rounds}", str(total_rounds))
        .replace("{context_for_a}", context_str)
        .replace("{first_resp}", first_resp)
        .replace("{context_for_b}", context_str)
        .replace("{second_resp}", second_resp)
    )

    response = await model_client.generate(
        messages=[{"role": "user", "content": prompt}],
        model=model,
        temperature=0.0,
        timeout=60,
    )

    parsed = _parse_json(response.content)

    if parsed and "quality_winner" in parsed:
        # Map A/B back to condition names
        def _map_winner(raw: str) -> str:
            raw = raw.strip().upper()
            if raw == "TIE":
                return "tie"
            if raw in ("A", "B"):
                return assignment[raw]
            return "tie"

        return PairwiseJudgment(
            quality_winner=_map_winner(parsed.get("quality_winner", "tie")),
            ontopic_winner=_map_winner(parsed.get("ontopic_winner", "tie")),
            quality_justification=parsed.get("quality_justification", ""),
            ontopic_justification=parsed.get("ontopic_justification", ""),
            confidence=float(parsed.get("confidence", 0.5)),
            position_assignment=assignment,
            raw_output=response.content,
        )

    logger.warning(f"Failed to parse judge output for turn {turn_index}")
    return PairwiseJudgment(
        quality_winner="tie",
        ontopic_winner="tie",
        quality_justification="parse_error",
        ontopic_justification="parse_error",
        confidence=0.0,
        position_assignment=assignment,
        raw_output=response.content,
    )
