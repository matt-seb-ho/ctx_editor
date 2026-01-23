"""Base model client protocol and utilities."""

import json
import re
from abc import ABC, abstractmethod
from typing import Any, Optional, Protocol, runtime_checkable

from ..core.types import ModelResponse


def format_messages(messages: list[dict], variables: dict[str, str]) -> list[dict]:
    """Format messages by replacing [[KEY]] placeholders with values.

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
            for key, value in variables.items():
                key_string = f"[[{key}]]"
                if key_string in msg["content"]:
                    msg["content"] = msg["content"].replace(key_string, value)
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

        # Cost per 1000 tokens (input, output)
        pricing = {
            "gpt-4o-mini": (0.00015, 0.0006),
            "gpt-4o": (0.0025, 0.01),
            "gpt-4.5-preview": (0.075, 0.150),
            "gpt-3.5-turbo": (0.0005, 0.0015),
            "o1-mini": (0.003, 0.012),
            "o1-preview": (0.015, 0.06),
            "o1": (0.015, 0.06),
            "claude-3-5-sonnet": (0.003, 0.015),
            "claude-3-opus": (0.015, 0.075),
            "claude-3-haiku": (0.00025, 0.00125),
        }

        # Find matching pricing
        inp_cost, out_cost = 0.0, 0.0
        for name, costs in pricing.items():
            if base_model.startswith(name):
                inp_cost, out_cost = costs
                break

        # Apply cache discount (50%)
        cache_discount = 0.5
        prompt_tokens_non_cached = prompt_tokens - prompt_tokens_cached
        total = (
            (prompt_tokens_non_cached + prompt_tokens_cached * cache_discount)
            / 1000
            * inp_cost
            + completion_tokens / 1000 * out_cost
        )

        # Apply batch discount (50%)
        if is_batch:
            total *= 0.5

        return total
