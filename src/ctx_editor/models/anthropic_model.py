"""Anthropic model client implementation."""

import asyncio
import os
from typing import Any, Optional

from ..core.types import ModelResponse
from .base import BaseModelClient, format_messages


class AnthropicModelClient(BaseModelClient):
    """Async Anthropic model client."""

    def __init__(self):
        """Initialize the Anthropic client."""
        try:
            from anthropic import AsyncAnthropic
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        self.client = AsyncAnthropic(api_key=api_key)

    async def generate(
        self,
        messages: list[dict],
        model: str = "claude-3-5-sonnet-20241022",
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        timeout: int = 30,
        max_retries: int = 3,
        variables: Optional[dict[str, str]] = None,
        is_json: bool = False,
    ) -> ModelResponse:
        """Generate a response from Anthropic.

        Args:
            messages: List of message dictionaries.
            model: Model identifier.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retries on failure.
            variables: Optional variables to substitute in the prompt.
            is_json: Whether to request JSON output.

        Returns:
            ModelResponse with generated content and metadata.
        """
        messages = format_messages(list(messages), variables or {})

        # Extract system message for Anthropic API
        system_content = None
        api_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_content = msg["content"]
            else:
                api_messages.append(msg)

        # Default max tokens if not specified
        if max_tokens is None:
            max_tokens = 4096

        # Add JSON instruction if needed
        if is_json and api_messages:
            last_msg = api_messages[-1]
            if last_msg["role"] == "user":
                last_msg["content"] += "\n\nRespond with valid JSON only."

        last_error = None
        for attempt in range(max_retries):
            try:
                kwargs: dict[str, Any] = {
                    "model": model,
                    "messages": api_messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                }
                if system_content:
                    kwargs["system"] = system_content

                response = await self.client.messages.create(**kwargs)
                break
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    await asyncio.sleep(2**attempt)
        else:
            raise RuntimeError(f"Failed after {max_retries} attempts: {last_error}")

        # Extract content from response
        content = ""
        for block in response.content:
            if block.type == "text":
                content += block.text

        usage = response.usage
        prompt_tokens = usage.input_tokens
        completion_tokens = usage.output_tokens

        # Anthropic pricing (per 1M tokens, convert to per 1K)
        pricing = {
            "claude-3-5-sonnet": (3.0, 15.0),
            "claude-3-opus": (15.0, 75.0),
            "claude-3-haiku": (0.25, 1.25),
            "claude-3-5-haiku": (1.0, 5.0),
        }

        inp_cost, out_cost = 0.003, 0.015  # Default to Sonnet
        for name, costs in pricing.items():
            if name in model:
                inp_cost, out_cost = costs[0] / 1000, costs[1] / 1000
                break

        total_usd = (prompt_tokens / 1000 * inp_cost) + (completion_tokens / 1000 * out_cost)

        return ModelResponse(
            content=content,
            total_tokens=prompt_tokens + completion_tokens,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            prompt_tokens_cached=0,
            total_usd=total_usd,
            raw_response=response.model_dump() if hasattr(response, "model_dump") else None,
        )
