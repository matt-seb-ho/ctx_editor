import json
import random
import re
from typing import Any, Dict, List

from lic.paths import get_prompt_path
from lic.task_base import Task


# ---------------------------------------------------------------------------
# Answer extraction / comparison helpers
# Adapted from EleutherAI lm-evaluation-harness AIME utils
# (see data/lm_eval_aime/utils.py for the original)
# ---------------------------------------------------------------------------


def _last_boxed_only_string(string: str):
    """Find the last \\boxed{...} or \\fbox{...} occurrence and return it."""
    idx = string.rfind("\\boxed")
    if "\\boxed " in string:
        return "\\boxed " + string.split("\\boxed ")[-1].split("$")[0]
    if idx < 0:
        idx = string.rfind("\\fbox")
        if idx < 0:
            return None

    i = idx
    right_brace_idx = None
    num_left_braces_open = 0
    while i < len(string):
        if string[i] == "{":
            num_left_braces_open += 1
        if string[i] == "}":
            num_left_braces_open -= 1
            if num_left_braces_open == 0:
                right_brace_idx = i
                break
        i += 1

    if right_brace_idx is None:
        return None
    return string[idx : right_brace_idx + 1]


def _remove_boxed(s: str):
    """Remove \\boxed{} wrapper and return the inner content."""
    if "\\boxed " in s:
        left = "\\boxed "
        if s[: len(left)] == left:
            return s[len(left) :]

    left = "\\boxed{"
    if s[: len(left)] == left and s[-1] == "}":
        return s[len(left) : -1]

    return s


def _strip_string(string: str) -> str:
    """Normalise a math string for comparison."""
    string = string.replace("\n", "")
    string = string.replace("\\!", "")
    string = string.replace("\\\\", "\\")
    string = string.replace("tfrac", "frac")
    string = string.replace("dfrac", "frac")
    string = string.replace("\\left", "")
    string = string.replace("\\right", "")
    string = string.replace("^{\\circ}", "")
    string = string.replace("^\\circ", "")
    string = string.replace("\\$", "")
    string = string.replace("\\%", "")
    string = string.replace("%", "")
    string = string.replace(" .", " 0.")
    string = string.replace("{.", "{0.")
    if len(string) == 0:
        return string
    if string[0] == ".":
        string = "0" + string
    if len(string.split("=")) == 2:
        if len(string.split("=")[0]) <= 2:
            string = string.split("=")[1]
    string = string.replace(" ", "")
    return string


def _is_equiv(str1, str2) -> bool:
    """Check if two math strings are equivalent after normalisation."""
    if str1 is None and str2 is None:
        return True
    if str1 is None or str2 is None:
        return False
    try:
        return _strip_string(str1) == _strip_string(str2)
    except Exception:
        return str1 == str2


def extract_boxed_answer(response: str) -> str:
    """Extract an answer from a response, preferring \\boxed{} content.

    Falls back to content between dollar signs, then the raw response.
    """
    # Try \\boxed{} first
    boxed = _last_boxed_only_string(response)
    if boxed is not None:
        try:
            content = _remove_boxed(boxed)
            if content is not None:
                return content
        except (AssertionError, IndexError):
            pass

    # Fall back to $...$ delimited content
    indices = [pos for pos, char in enumerate(response) if char == "$"]
    if len(indices) >= 2:
        return response[indices[0] + 1 : indices[-1]]

    return response


class TaskAIME(Task):
    def __init__(self):
        with open(get_prompt_path("prompts/aime/aime_full_prompt.txt"), "r") as f:
            self.fully_specified_prompt = f.read()
        with open(get_prompt_path("prompts/aime/aime_system_prompt.txt"), "r") as f:
            self.system_prompt = f.read()
        self.seed = 42
        random.seed(self.seed)

        self.answer_extraction_strategy = "task_specific"

    def get_dataset_file(self) -> str:
        return "data/sharded_aime24_5mini.json"

    def get_samples(self, filter="full"):
        with open(self.get_dataset_file(), "r") as f:
            data = json.load(f)
        return data

    def get_task_name(self):
        return "aime"

    def get_answer_description(self) -> str:
        return (
            "The answer should be a non-negative integer (between 000 and 999). "
            "It should be enclosed in \\boxed{}, for example \\boxed{42}."
        )

    def generate_system_prompt(self, sample: Dict[str, Any]) -> str:
        return self.system_prompt

    def extract_answer(self, response: str) -> str:
        """Extract the answer from the assistant's response.

        Used by SystemAgent when answer_extraction_strategy='task_specific'.
        """
        return extract_boxed_answer(response)

    def evaluator_function(self, extracted_answer: str, sample: Dict[str, Any]) -> dict:
        # Get the ground truth from the sample's answer field by extracting from \boxed{}
        ground_truth_answer = sample.get("ground_truth_a", sample["answer"])
        gold = extract_boxed_answer(ground_truth_answer)

        if not extracted_answer or not extracted_answer.strip():
            return {
                "score": 0.0,
                "error": f"No answer extracted from response",
            }

        extracted_clean = extracted_answer.strip()

        # AIME answers are integers 000-999, so try integer comparison first
        try:
            if int(extracted_clean) == int(gold):
                return {"score": 1.0}
        except (ValueError, TypeError):
            pass

        # Fall back to string equivalence with normalisation
        if _is_equiv(extracted_clean, gold):
            return {"score": 1.0}

        return {"score": 0.0}

    def populate_fully_specific_prompt(self, sample: Dict[str, Any]) -> str:
        return self.fully_specified_prompt.replace("[[QUESTION]]", sample["question"])

    def populate_concat_prompt(self, sample: Dict[str, Any]) -> str:
        query = ""
        for shard in sample["shards"]:
            query += f"- {shard['shard']}\n"
        return self.fully_specified_prompt.replace("[[QUESTION]]", query)

    def extract_fully_specific_response(self, response: str, sample: Dict[str, Any]) -> str:
        return response["answer"]

    def process_original_sample(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """Process AIME sample for annotation UI display."""
        return {
            "task_id": sample["task_id"],
            "question": sample["question"],
            "answer": sample["answer"],
        }
