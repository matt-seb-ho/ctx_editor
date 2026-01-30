"""Miscellaneous helper utilities."""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Union


def load_env_vars(filepath: str = ".env") -> None:
    """Load environment variables from a file.

    Args:
        filepath: Path to the .env file.
    """
    env_path = Path(filepath)
    if not env_path.exists():
        return

    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                # Remove 'export' if present
                if line.startswith("export "):
                    line = line[7:].strip()

                # Split on first '=' only
                if "=" in line:
                    key, value = line.split("=", 1)
                    # Remove quotes around the value
                    value = value.strip("'\"")
                    os.environ[key.strip()] = value


def load_prompt(
    prompt_file: str,
    base_dir: Optional[str] = None,
    variables: Optional[dict[str, str]] = None,
) -> str:
    """Load a prompt from a file and optionally substitute variables.

    Args:
        prompt_file: Path to the prompt file.
        base_dir: Base directory for relative paths.
        variables: Optional dict of variables to substitute (e.g., {"KEY": "value"}).

    Returns:
        The prompt content with variables substituted.
    """
    if base_dir:
        prompt_path = Path(base_dir) / prompt_file
    else:
        prompt_path = Path(prompt_file)

    with open(prompt_path, "r", encoding="utf-8") as f:
        content = f.read()

    if variables:
        for key, value in variables.items():
            content = content.replace(f"[[{key}]]", value)

    return content


def date_str() -> str:
    """Get the current datetime as a formatted string.

    Returns:
        Datetime string in YYYY-MM-DD HH:MM:SS format.
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def extract_conversation(
    trace: list[dict],
    to_str: bool = False,
    skip_system: bool = False,
    only_last_turn: bool = False,
) -> Union[list[dict], str]:
    """Extract the conversation messages from a trace.

    Args:
        trace: The full trace including logs.
        to_str: Whether to return as a formatted string.
        skip_system: Whether to skip the system message.
        only_last_turn: Whether to only return messages after the last user turn.

    Returns:
        List of message dicts or formatted string.
    """
    keep_roles = ["assistant", "user"]
    if not skip_system:
        keep_roles.insert(0, "system")

    real_conversation = [msg for msg in trace if msg.get("role") in keep_roles]

    if only_last_turn:
        user_turn_idxs = [i for i, msg in enumerate(real_conversation) if msg["role"] == "user"]
        if user_turn_idxs:
            last_user_turn_idx = user_turn_idxs[-1]
            real_conversation = real_conversation[last_user_turn_idx + 1 :]

    # Keep only role and content
    real_conversation = [
        {"role": msg["role"], "content": msg["content"]} for msg in real_conversation
    ]

    if to_str:
        return "\n\n".join([f"[{msg['role']}] {msg['content']}" for msg in real_conversation])
    return real_conversation
