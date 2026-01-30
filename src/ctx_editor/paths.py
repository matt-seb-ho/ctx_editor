"""Path constants for ctx_editor package."""

from pathlib import Path

# Package root directory
PACKAGE_DIR = Path(__file__).parent

# Prompts directory
PROMPTS_DIR = PACKAGE_DIR / "prompts"

PROJECT_ROOT = PACKAGE_DIR.parent.parent  # ctx_editor repo root
