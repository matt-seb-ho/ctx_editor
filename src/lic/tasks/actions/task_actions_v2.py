from lic.paths import get_prompt_path
from lic.tasks.actions.task_actions import TaskActions


class TaskActionsV2(TaskActions):
    """V2 actions task: bakes the 'accumulate' instruction into the system prompt.

    The BFCL evaluator extracts the assistant's final-turn response and parses it
    for the full set of function calls. In a multi-turn sharded conversation, the
    vanilla model tends to emit only the function call most relevant to the
    latest shard, so the final turn ends up missing earlier calls and is graded
    wrong. The v2 system prompt explicitly tells the assistant that each
    response must re-emit the consolidated list of all function calls satisfying
    every user request so far. See docs/mar21_bug_discovery.md.
    """

    _initialized_once = False

    def __init__(self):
        super().__init__()
        with open(get_prompt_path("prompts/actions/actions_system_prompt_v2.txt"), "r") as f:
            self.system_prompt = f.read()
        if not TaskActionsV2._initialized_once:
            print("[TaskActionsV2] active — system prompt includes accumulate instruction")
            TaskActionsV2._initialized_once = True

    def get_task_name(self):
        return "actions"
