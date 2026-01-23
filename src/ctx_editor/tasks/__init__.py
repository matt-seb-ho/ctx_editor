"""Tasks module - bridges to LIC task implementations.

This module provides access to task implementations from the LIC codebase.
It can either import directly from the lic module or use local copies.
"""

import sys
from pathlib import Path

# Add LIC to path for imports
_lic_path = Path(__file__).parent.parent.parent / "lic"
if _lic_path.exists() and str(_lic_path) not in sys.path:
    sys.path.insert(0, str(_lic_path))

try:
    from tasks import get_task
    from tasks.tasks import (
        TaskDatabase,
        TaskMath,
        TaskCode,
        TaskSummary,
        TaskData2Text,
        TaskActions,
        TaskTranslation,
    )
except ImportError:
    # Fallback: define a minimal interface
    def get_task(task_name: str, version: str = None):
        """Get a task by name - fallback implementation."""
        raise ImportError(
            f"Could not import task {task_name}. "
            "Please ensure the LIC tasks module is available."
        )

    TaskDatabase = None
    TaskMath = None
    TaskCode = None
    TaskSummary = None
    TaskData2Text = None
    TaskActions = None
    TaskTranslation = None

__all__ = [
    "get_task",
    "TaskDatabase",
    "TaskMath",
    "TaskCode",
    "TaskSummary",
    "TaskData2Text",
    "TaskActions",
    "TaskTranslation",
]
