"""Base model client protocol and utilities."""

import json
import re
from abc import ABC, abstractmethod
from functools import cache
from typing import Any, Optional, Protocol, runtime_checkable

from ..core.types import ModelResponse
from .openai_pricing import OPENAI_PRICING


@cache
def get_model_pricing() -> dict[str, dict[str, float]]:
    # TODO: mix other providers' pricing here
    return OPENAI_PRICING


def format_messages(messages: list[dict], variables: dict[str, str]) -> list[dict]:
    """Format messages by replacing {key} placeholders with values.

    Args:
        messages: List of message dictionaries with 'role' and 'content'.
        variables: Dictionary of key-value pairs to substitute.

    Returns:
        The messages with placeholders replaced.
    """
    if not variables:
        return messages

    # Find the last user message and apply substitutions
    for msg in reversed(messages):
        if msg["role"] == "user":
            # Use format_map to allow partial substitution (missing keys stay as-is)
            try:
                msg["content"] = msg["content"].format(**variables)
            except KeyError:
                # Fall back to format_map for partial substitution
                from string import Formatter

                class SafeDict(dict):
                    def __missing__(self, key):
                        return f"{{{key}}}"

                msg["content"] = msg["content"].format_map(SafeDict(variables))
            break

    return messages


@runtime_checkable
class ModelClient(Protocol):
    """Protocol for model clients."""

    async def generate(
        self,
        messages: list[dict],
        model: str,
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        timeout: int = 30,
        variables: Optional[dict[str, str]] = None,
    ) -> ModelResponse:
        """Generate a response from the model.

        Args:
            messages: List of message dictionaries with 'role' and 'content'.
            model: Model identifier.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            timeout: Request timeout in seconds.
            variables: Optional variables to substitute in the prompt.

        Returns:
            ModelResponse with the generated content and metadata.
        """
        ...

    async def generate_json(
        self,
        messages: list[dict],
        model: str,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        timeout: int = 30,
        variables: Optional[dict[str, str]] = None,
    ) -> ModelResponse:
        """Generate a JSON response from the model.

        Args:
            messages: List of message dictionaries with 'role' and 'content'.
            model: Model identifier.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            timeout: Request timeout in seconds.
            variables: Optional variables to substitute in the prompt.

        Returns:
            ModelResponse with parsed JSON content.
        """
        ...


class BaseModelClient(ABC):
    """Abstract base class for model clients with shared functionality."""

    @abstractmethod
    async def generate(
        self,
        messages: list[dict],
        model: str,
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        timeout: int = 30,
        variables: Optional[dict[str, str]] = None,
    ) -> ModelResponse:
        """Generate a response from the model."""
        pass

    async def generate_json(
        self,
        messages: list[dict],
        model: str,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        timeout: int = 30,
        variables: Optional[dict[str, str]] = None,
    ) -> ModelResponse:
        """Generate a JSON response from the model."""
        response = await self.generate(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            variables=variables,
            is_json=True,
        )
        # Parse JSON from content
        try:
            parsed = json.loads(response.content)
            response.content = parsed
        except json.JSONDecodeError as e:
            # Try to extract JSON from the response
            json_match = re.search(r"\{.*\}", response.content, re.DOTALL)
            if json_match:
                response.content = json.loads(json_match.group())
            else:
                raise ValueError(f"Failed to parse JSON response: {e}")
        return response

    @staticmethod
    def _calculate_cost(
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        prompt_tokens_cached: int = 0,
        is_batch: bool = False,
    ) -> float:
        """Calculate the cost of an API call.

        Args:
            model: Model identifier.
            prompt_tokens: Number of prompt tokens.
            completion_tokens: Number of completion tokens.
            prompt_tokens_cached: Number of cached prompt tokens.
            is_batch: Whether this is a batch API call.

        Returns:
            Cost in USD.
        """
        # Determine base model for fine-tuned models
        base_model = model
        if model.startswith("ft:"):
            base_model = model.split(":")[1]

        # pricing now expressed in USD/1M tokens
        pricing = get_model_pricing()

        # Find matching pricing
        inp_cost = 0.0
        out_cost = 0.0
        cached_inp_cost = 0.0
        matched_name = None
        for name, costs in pricing.items():
            if base_model.startswith(name):
                # go with longest matching prefix
                if matched_name is not None and len(name) < len(matched_name):
                    continue
                matched_name = name
                inp_cost = costs["input"]
                out_cost = costs["output"]
                cached_inp_cost = costs.get("cached_input", None) or inp_cost

        # Apply cache discount (50%)
        prompt_tokens_non_cached = prompt_tokens - prompt_tokens_cached
        total = (
            prompt_tokens_cached * cached_inp_cost
            + prompt_tokens_non_cached * inp_cost
            + completion_tokens * out_cost
        ) / 1_000_000

        # Apply batch discount (50%)
        if is_batch:
            total *= 0.5

        return total
