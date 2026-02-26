import re
from typing import Any, Dict

from lic.paths import get_prompt_path
from lic.tasks.math.task_math import TaskMath


class TaskMathV2(TaskMath):
    _initialized_once = False
    """V2 task evaluator for math (GSM8K) tasks.

    Changes from V1:
    - System prompt instructs the model to highlight its final answer as
      **ANSWER: N** (no units).
    - answer_extraction_strategy changed to "task_specific":
        extract_answer() tries **ANSWER: N** first, then \\boxed{} for
        backward compat, then falls back to the V1 numeric regex.
    - evaluator_function: integer coercion — answers like "2.00" are treated as
      "2" (all GSM8K answers are integers).  Genuinely non-integer floats like
      "2.3657" are marked wrong immediately rather than being compared as strings.
    """

    def __init__(self):
        super().__init__()
        with open(get_prompt_path("prompts/math/math_system_prompt_v2.txt"), "r") as f:
            self.system_prompt = f.read()
        self.answer_extraction_strategy = "task_specific"
        if not TaskMathV2._initialized_once:
            print("[TaskMathV2] active — task_specific extraction + integer coercion")
            TaskMathV2._initialized_once = True

    def extract_answer(self, text: str) -> str:
        """Try **ANSWER: N** first, then \\boxed{} for back-compat, then numeric regex."""
        # Primary: extract from **ANSWER: N** pattern
        answer_matches = re.findall(r"\*\*ANSWER:\s*(.+?)\*\*", text)
        if answer_matches:
            return answer_matches[-1].strip()

        # Back-compat: extract content from the last \boxed{...}
        boxed_matches = re.findall(r"\\boxed\{([^}]*)\}", text)
        if boxed_matches:
            return boxed_matches[-1].strip()

        # Fallback: same regex V1 uses inside evaluator_function
        try:
            matches = re.findall(r"(-?[$0-9.,]{2,})|(-?[0-9]+)", text)
            if matches:
                return [m for m in matches[-1] if m][0]
        except Exception:
            pass
        return ""

    def evaluator_function(self, extracted_answer: str, sample: Dict[str, Any]) -> dict:
        regexes_to_ignore = [",", "\\$", "(?s).*#### ", "\\.$"]

        gold = sample["answer"].split("####")[1].strip().lower()

        try:
            extracted_answer = extracted_answer.strip()
            # Pull the last number-like token out of the extracted answer
            matches = re.findall(r"(-?[$0-9.,]{2,})|(-?[0-9]+)", extracted_answer)
            if not matches:
                raise ValueError("no numeric token found")
            extracted_answer = [m for m in matches[-1] if m][0]
        except Exception:
            return {
                "score": 0.0,
                "error": f"Answer could not be extracted: {repr(extracted_answer)}",
            }

        # Strip $ and , before trying float parse
        cleaned = re.sub(r"[$,]", "", extracted_answer)
        try:
            as_float = float(cleaned)
            if as_float == int(as_float):
                # Integer-valued float (e.g. 2.0, 2.00) — coerce to int string
                extracted_answer = str(int(as_float))
            else:
                # Genuinely non-integer (e.g. 2.3657) — wrong immediately for GSM8K
                return {"score": 0.0, "error": f"Non-integer answer: {repr(extracted_answer)}"}
        except ValueError:
            pass  # not parseable as float; let the string comparison handle it

        for regex in regexes_to_ignore:
            extracted_answer = re.sub(regex, "", extracted_answer)
            gold = re.sub(regex, "", gold)

        score = 1.0 if extracted_answer == gold else 0.0
        return {"score": score}
