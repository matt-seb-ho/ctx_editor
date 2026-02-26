from lic.tasks.actions import TaskActions
from lic.tasks.aime import TaskAIME
from lic.tasks.code import TaskCode, TaskCodeV2
# from lic.tasks.data2text import TaskData2Text
from lic.tasks.database import TaskDatabase, TaskDatabaseV2
from lic.tasks.math import TaskMath, TaskMathV2
# from lic.tasks.summary import TaskSummary
# from lic.tasks.translation import TaskTranslation


def get_task(task_name, version=None):
    kwargs = {}
    if version is not None:
        kwargs["version"] = version

    if task_name == "database":
        return TaskDatabase(**kwargs)
    elif task_name == "database_v2":
        return TaskDatabaseV2(**kwargs)
    elif task_name == "code":
        return TaskCode(**kwargs)
    elif task_name == "code_v2":
        return TaskCodeV2(**kwargs)
    # elif task_name == "translation":
    #     return TaskTranslation(**kwargs)
    # elif task_name == "summary":
    #     return TaskSummary(**kwargs)
    # elif task_name == "data2text":
    #     return TaskData2Text(**kwargs)
    elif task_name == "math":
        return TaskMath(**kwargs)
    elif task_name == "math_v2":
        return TaskMathV2(**kwargs)
    elif task_name == "aime":
        return TaskAIME(**kwargs)
    elif task_name.startswith("actions"):
        return TaskActions(**kwargs)
    else:
        raise ValueError(f"Task {task_name} not supported")


if __name__ == "__main__":
    task = get_task("data2text")
    print(len(task.get_samples()))
