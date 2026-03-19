"""LLM-based evaluation metrics matching CollabLLM's approach.

All judge/extraction calls go through our async ModelClient for consistent
usage tracking, retry logic, and load balancing.
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from ..models.base import ModelClient

logger = logging.getLogger(__name__)

# Load prompt templates
_PROMPTS_DIR = Path(__file__).parent.parent / "prompts" / "collabllm"
EXTRACT_COMPLETION_PROMPT = (_PROMPTS_DIR / "extract_completion.txt").read_text()
ACCURACY_JUDGE_PROMPT = (_PROMPTS_DIR / "accuracy_judge.txt").read_text()
INTERACTIVITY_JUDGE_PROMPT = (_PROMPTS_DIR / "interactivity_judge.txt").read_text()


def _parse_json_response(text: str) -> dict | None:
    """Extract JSON from an LLM response, handling markdown fences and edge cases."""
    # Try direct parse first
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        pass

    # Try stripping markdown code fences
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

    # Try finding JSON object in text (handle nested braces)
    start = text.find("{")
    if start != -1:
        # Find matching closing brace
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

    # Last resort: try to extract key-value pairs manually
    # This handles cases where triple quotes break JSON
    result = {}
    for key in ["thought", "final_completion", "accuracy", "interactivity", "response",
                 "current_answer", "current_problem"]:
        pattern = f'"{key}"'
        idx = text.find(pattern)
        if idx == -1:
            pattern = f"'{key}'"
            idx = text.find(pattern)
        if idx != -1:
            # Find the value after the colon
            colon_idx = text.find(":", idx + len(pattern))
            if colon_idx != -1:
                # Try to find a string value
                rest = text[colon_idx + 1:].strip()
                if rest.startswith('"""'):
                    end = rest.find('"""', 3)
                    if end != -1:
                        result[key] = rest[3:end]
                elif rest.startswith('"'):
                    # Find end of string (handle escapes)
                    i = 1
                    while i < len(rest):
                        if rest[i] == "\\" and i + 1 < len(rest):
                            i += 2
                        elif rest[i] == '"':
                            break
                        else:
                            i += 1
                    if i < len(rest):
                        try:
                            result[key] = json.loads(rest[:i + 1])
                        except (json.JSONDecodeError, TypeError):
                            result[key] = rest[1:i]
                elif rest[0].isdigit() or rest[0] == "-":
                    # Numeric value
                    num_str = ""
                    for c in rest:
                        if c.isdigit() or c in ".-":
                            num_str += c
                        else:
                            break
                    try:
                        result[key] = float(num_str) if "." in num_str else int(num_str)
                    except ValueError:
                        pass

    return result if result else None


def _format_messages_for_prompt(messages: list[dict[str, str]]) -> str:
    """Format messages as CollabLLM-style chat history string.

    Produces: **Role**: content lines, matching CollabLLM's parse_messages().
    """
    parts = []
    for msg in messages:
        role = msg.get("role", "unknown")
        if role == "system":
            continue
        content = msg.get("content", "")
        parts.append(f"**{role.capitalize()}**: {content}")
    return "\n".join(parts)


async def extract_completion(
    messages: list[dict[str, str]],
    extract_type: str,
    model_client: "ModelClient",
    model: str,
    max_tokens: int = 4000,
    max_retries: int = 3,
    metadata: dict | None = None,
) -> str | None:
    """Extract the final answer/document from a multi-turn conversation.

    Uses CollabLLM's extraction prompt to pull out the final artifact.

    Args:
        metadata: Optional sample metadata. If it contains 'extraction_requirement',
            this is passed to the extraction prompt (used by BigCodeBench to
            ensure extracted code starts with the required code prefix).

    Returns:
        The extracted completion string, or None if extraction fails.
    """
    chat_history = _format_messages_for_prompt(messages)
    extraction_req = ""
    if metadata and metadata.get("extraction_requirement"):
        extraction_req = "Addtional requirement:\n" + metadata["extraction_requirement"]
    prompt = EXTRACT_COMPLETION_PROMPT.format(
        extract_type=extract_type,
        chat_history=chat_history,
        extraction_requirement=extraction_req,
    )

    for attempt in range(max_retries):
        try:
            response = await model_client.generate(
                messages=[{"role": "user", "content": prompt}],
                model=model,
                temperature=0.0,
                max_tokens=max_tokens,
            )
            parsed = _parse_json_response(response.content)
            if parsed and "final_completion" in parsed:
                return parsed["final_completion"], response
            else:
                # Fallback: if we can't parse JSON, try to extract the last
                # assistant message content as the completion
                logger.warning(
                    f"extract_completion attempt {attempt + 1}: "
                    f"JSON parse failed, raw response: {response.content[:200]}..."
                )
        except Exception as e:
            logger.warning(f"extract_completion attempt {attempt + 1} failed: {e}")

    # Last resort: extract the last assistant message directly
    for msg in reversed(messages):
        if msg.get("role") == "assistant":
            logger.warning("extract_completion: falling back to last assistant message")
            return msg["content"], None

    logger.error("extract_completion failed after all retries")
    return None, None


async def judge_accuracy(
    single_turn_prompt: str,
    groundtruth: str,
    completion: str,
    model_client: "ModelClient",
    model: str,
    max_retries: int = 3,
) -> tuple[float, Any]:
    """Judge accuracy of a completion against ground truth via LLM.

    Returns:
        Tuple of (accuracy_score, model_response). Score is 1.0 or 0.0,
        or -1.0 if evaluation fails.
    """
    prompt = ACCURACY_JUDGE_PROMPT.format(
        single_turn_prompt=single_turn_prompt.strip(),
        groundtruth=groundtruth.strip(),
        completion=completion.strip(),
    )

    for attempt in range(max_retries):
        try:
            response = await model_client.generate(
                messages=[{"role": "user", "content": prompt}],
                model=model,
                temperature=0.0,
                max_tokens=1000,
            )
            parsed = _parse_json_response(response.content)
            if parsed and "accuracy" in parsed:
                return float(parsed["accuracy"]), response
        except Exception as e:
            logger.warning(f"judge_accuracy attempt {attempt + 1} failed: {e}")

    logger.error("judge_accuracy failed after all retries")
    return -1.0, None


async def judge_interactivity(
    messages: list[dict[str, str]],
    model_client: "ModelClient",
    model: str,
    max_retries: int = 3,
) -> tuple[float, Any]:
    """Judge interactivity of a conversation via LLM.

    Returns:
        Tuple of (interactivity_score, model_response). Score in [0, 1],
        or -1.0 if evaluation fails.
    """
    chat_history = "\n".join(
        f"{m['role'].capitalize()}: {m['content']}"
        for m in messages
        if m.get("role") != "system"
    )
    prompt = INTERACTIVITY_JUDGE_PROMPT.format(chat_history=chat_history)

    for attempt in range(max_retries):
        try:
            response = await model_client.generate(
                messages=[{"role": "user", "content": prompt}],
                model=model,
                temperature=0.0,
                max_tokens=1000,
            )
            parsed = _parse_json_response(response.content)
            if parsed and "interactivity" in parsed:
                return float(parsed["interactivity"]), response
        except Exception as e:
            logger.warning(f"judge_interactivity attempt {attempt + 1} failed: {e}")

    logger.error("judge_interactivity failed after all retries")
    return -1.0, None


def judge_pass_rate(
    completion: str,
    metadata: dict[str, Any],
) -> float:
    """Judge code correctness by executing against test cases.

    Uses BigCodeBench's untrusted_check to run the extracted code against
    the problem's test suite. This matches CollabLLM's evaluation for code tasks.

    Args:
        completion: Extracted code string.
        metadata: Must contain 'test' (unittest code) and 'entry_point' (function name).

    Returns:
        1.0 if all tests pass, 0.0 otherwise.
    """
    from bigcodebench.eval import untrusted_check

    test_code = metadata.get("test", "")
    entry_point = metadata.get("entry_point", "")

    if not test_code or not entry_point:
        logger.error("judge_pass_rate: missing 'test' or 'entry_point' in metadata")
        return -1.0

    try:
        res = untrusted_check(
            completion,
            test_code,
            entry_point,
            max_as_limit=300 * 1024,
            max_data_limit=300 * 1024,
            max_stack_limit=300 * 1024,
            min_time_limit=60,
            gt_time_limit=60,
        )
        passed = res[0] == "pass"
        info = res[1] if len(res) > 1 else ""
        if not passed:
            logger.info(f"judge_pass_rate: test failed for {entry_point}: {str(info)[:200]}")
        return float(passed)
    except Exception as e:
        logger.error(f"judge_pass_rate: execution error: {e}")
        return 0.0


def count_assistant_tokens(messages: list[dict[str, str]]) -> int:
    """Count approximate token count of assistant messages.

    Uses a simple word-based approximation (tokens ~= words * 1.3).
    """
    total = 0
    for msg in messages:
        if msg.get("role") == "assistant":
            # Rough approximation: 1 token ~ 0.75 words
            words = len(msg.get("content", "").split())
            total += int(words * 1.3)
    return total


@dataclass
class CollabLLMEvalResult:
    """Result of CollabLLM evaluation on a conversation."""

    accuracy: float = -1.0
    interactivity: float = -1.0
    assistant_tokens: int = 0
    extracted_answer: str | None = None
    eval_cost_usd: float = 0.0


@dataclass
class CollabLLMEvaluator:
    """Runs CollabLLM-style evaluation on a completed conversation.

    Extracts final answer, then judges accuracy and interactivity.

    eval_method controls how accuracy is judged:
    - "llm_judge" (default): LLM compares extracted answer vs ground truth
    - "pass_rate": Execute extracted code against test cases (for BigCodeBench)
    """

    model: str = "gpt-4o-mini"
    extract_type: str = "answer"
    eval_method: str = "llm_judge"
    max_tokens: int = 4000

    async def evaluate(
        self,
        messages: list[dict[str, str]],
        single_turn_prompt: str,
        single_turn_completion: str,
        model_client: "ModelClient",
        metadata: dict[str, Any] | None = None,
    ) -> CollabLLMEvalResult:
        """Run full evaluation on a conversation.

        Args:
            messages: The full conversation as list of role/content dicts.
            single_turn_prompt: Original problem/question.
            single_turn_completion: Ground truth answer.
            model_client: Model client for LLM calls.
            metadata: Sample metadata (contains test cases, entry_point for code).

        Returns:
            CollabLLMEvalResult with all metrics.
        """
        result = CollabLLMEvalResult()
        result.assistant_tokens = count_assistant_tokens(messages)

        # Extract final completion (pass metadata for extraction_requirement)
        extracted, extract_resp = await extract_completion(
            messages=messages,
            extract_type=self.extract_type,
            model_client=model_client,
            model=self.model,
            max_tokens=self.max_tokens,
            metadata=metadata,
        )
        if extract_resp:
            result.eval_cost_usd += extract_resp.total_usd
        result.extracted_answer = extracted

        # Judge accuracy (only if extraction succeeded)
        if extracted:
            if self.eval_method == "pass_rate" and metadata:
                # Code evaluation: run against test cases
                accuracy = judge_pass_rate(extracted, metadata)
                result.accuracy = accuracy
            else:
                # LLM judge (default, used for math/QA)
                accuracy, acc_resp = await judge_accuracy(
                    single_turn_prompt=single_turn_prompt,
                    groundtruth=single_turn_completion,
                    completion=extracted,
                    model_client=model_client,
                    model=self.model,
                )
                if acc_resp:
                    result.eval_cost_usd += acc_resp.total_usd
                result.accuracy = accuracy

        # Judge interactivity
        interactivity, itr_resp = await judge_interactivity(
            messages=messages,
            model_client=model_client,
            model=self.model,
        )
        if itr_resp:
            result.eval_cost_usd += itr_resp.total_usd
        result.interactivity = interactivity

        return result
