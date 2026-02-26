import re

from lic.paths import get_prompt_path
from lic.tasks.code.task_code import TaskCode


class TaskCodeV2(TaskCode):
    _initialized_once = False
    """V2 task evaluator for code tasks.

    Changes from V1:
    - System prompt instructs model to wrap final code in ```python ... ``` fences
    - extract_answer: fixed rfind("import") bug where an import inside a function body
      could cause the slice to start after the last `def`, dropping the function header.
      Fix: only use import_idx as the start anchor when it precedes the last `def`.
    """

    def __init__(self):
        super().__init__()
        with open(get_prompt_path("prompts/lcb/lcb_system_prompt_v2.txt"), "r") as f:
            self.system_prompt_lcb = f.read()
        if not TaskCodeV2._initialized_once:
            print("[TaskCodeV2] active — code-fence prompt + fixed extract_answer")
            TaskCodeV2._initialized_once = True

    def extract_answer(self, text: str) -> str:
        """Extract the last Python function definition from text.

        Same as V1 except the no-code-fence fallback path uses `def_idx` as the
        primary start anchor rather than `import_idx`, so an `import` that appears
        inside a function body does not cause the slice to skip the `def` line.
        """
        # First try to extract Python code blocks from markdown
        code_blocks = re.findall(r"```(?:python)?\s*(.*?)\s*```", text, re.DOTALL)

        if "class Solution" in text:
            return [c for c in code_blocks if "class Solution" in c][-1]

        if code_blocks:
            for block in reversed(code_blocks):
                result = self._extract_function_from_code(block)
                if result:
                    return result
            return ""

        # No code fences — fall back to raw text heuristic.
        text = text.strip()
        if text.startswith("```") or text.startswith("`"):
            text = text[text.find("\n") :].strip()

        def_idx = text.rfind("def")
        import_idx = text.rfind("import")

        # Only treat an `import` as the start anchor when it precedes the last
        # `def`.  If import_idx > def_idx the import lives inside the function
        # body; in that case we start from `def` to avoid cutting the header.
        if def_idx >= 0:
            start_idx = import_idx if (import_idx >= 0 and import_idx < def_idx) else def_idx
        else:
            start_idx = import_idx

        if start_idx >= 0:
            text = text[start_idx:]

        return self._extract_function_from_code(text)
