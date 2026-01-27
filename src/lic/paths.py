"""Path utilities for the lic package."""

from pathlib import Path

LIC_ROOT = Path(__file__).parent
PROJECT_ROOT = LIC_ROOT.parent.parent  # ctx_editor repo root


def get_data_path(relative_path: str) -> Path:
    """Get absolute path to a data file.

    Args:
        relative_path: Path relative to project root (e.g., "data/spider/databases/")

    Returns:
        Absolute path to the data file/directory.
    """
    return PROJECT_ROOT / relative_path


def get_prompt_path(relative_path: str) -> Path:
    """Get absolute path to a prompt file.

    Args:
        relative_path: Path relative to src/lic (e.g., "prompts/math/math_full_prompt.txt")

    Returns:
        Absolute path to the prompt file.
    """
    return LIC_ROOT / relative_path
