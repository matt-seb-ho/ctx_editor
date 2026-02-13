"""Tasks module - bridges to LIC task implementations.

This module provides access to task implementations from the LIC codebase.
After installing with `pip install -e .`, both ctx_editor and lic packages
are available without path manipulation.
"""

try:
    from lic.tasks import get_task
    from lic.tasks.tasks import (
        TaskActions,
        TaskAIME,
        TaskCode,
        TaskData2Text,
        TaskDatabase,
        TaskMath,
        TaskSummary,
        TaskTranslation,
    )
except ImportError:
    # Fallback: define a minimal interface
    def get_task(task_name: str, version: str = None):
        """Get a task by name - fallback implementation."""
        raise ImportError(
            f"Could not import task {task_name}. "
            "Please ensure the package is installed with `pip install -e .`"
        )

    TaskDatabase = None
    TaskMath = None
    TaskAIME = None
    TaskCode = None
    TaskSummary = None
    TaskData2Text = None
    TaskActions = None
    TaskTranslation = None

__all__ = [
    "get_task",
    "TaskDatabase",
    "TaskMath",
    "TaskAIME",
    "TaskCode",
    "TaskSummary",
    "TaskData2Text",
    "TaskActions",
    "TaskTranslation",
]
