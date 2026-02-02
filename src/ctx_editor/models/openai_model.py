"""OpenAI model client implementation."""

import asyncio
import os
from typing import Any, Optional

from openai import AsyncAzureOpenAI, AsyncOpenAI

from ..core.types import ModelResponse, ReasoningEffort
from .base import BaseModelClient, format_messages
from .setup_azure_oai_client import setup_azure_oai_client


class OpenAIModelClient(BaseModelClient):
    """Async OpenAI/Azure model client."""

    _gpt5_temp_warned: bool = False  # Class-level flag to warn only once

    def __init__(self):
        """Initialize the OpenAI client."""
        if os.getenv("USE_AZURE_OAI", "false").lower() == "true":
            print("Using Azure OpenAI")
            self.client = setup_azure_oai_client()
        else:
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            self.client = AsyncOpenAI(api_key=api_key)

    async def generate(
        self,
        messages: list[dict],
        model: str = "gpt-4o-mini",
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        timeout: int = 30,
        max_retries: int = 3,
        variables: Optional[dict[str, str]] = None,
        is_json: bool = False,
        reasoning_effort: Optional[ReasoningEffort] = None,
    ) -> ModelResponse:
        """Generate a response from OpenAI.

        Args:
            messages: List of message dictionaries.
            model: Model identifier.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retries on failure.
            variables: Optional variables to substitute in the prompt.
            is_json: Whether to request JSON output.
            reasoning_effort: Reasoning effort level for reasoning models.

        Returns:
            ModelResponse with generated content and metadata.
        """
        messages = format_messages(list(messages), variables or {})

        # Enforce temperature=1.0 for gpt-5 models (API requirement)
        if model.startswith("gpt-5") and temperature != 1.0:
            if not OpenAIModelClient._gpt5_temp_warned:
                import logging

                logging.getLogger("ctx_editor").warning(
                    f"gpt-5 models require temperature=1.0, overriding {temperature} -> 1.0"
                )
                OpenAIModelClient._gpt5_temp_warned = True
            temperature = 1.0

        # Handle o1 models that don't support system messages
        if model.startswith("o1") and len(messages) > 1:
            if messages[0]["role"] == "system" and messages[1]["role"] == "user":
                system_content = messages[0]["content"]
                messages[1]["content"] = (
                    f"System Message: {system_content}\n{messages[1]['content']}"
                )
                messages = messages[1:]

        kwargs: dict[str, Any] = {}
        if is_json:
            kwargs["response_format"] = {"type": "json_object"}
        if reasoning_effort:
            kwargs["reasoning_effort"] = reasoning_effort

        last_error = None
        for attempt in range(max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    timeout=timeout,
                    max_completion_tokens=max_tokens,
                    temperature=temperature,
                    **kwargs,
                )
                break
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    await asyncio.sleep(2**attempt)  # Exponential backoff
        else:
            raise RuntimeError(f"Failed after {max_retries} attempts: {last_error}")

        response_dict = response.model_dump()
        usage = response_dict["usage"]

        prompt_tokens_cached = 0
        if "prompt_tokens_details" in usage and usage["prompt_tokens_details"]:
            prompt_tokens_cached = usage["prompt_tokens_details"].get("cached_tokens", 0)

        total_usd = self._calculate_cost(
            model=model,
            prompt_tokens=usage["prompt_tokens"],
            completion_tokens=usage["completion_tokens"],
            prompt_tokens_cached=prompt_tokens_cached,
        )

        return ModelResponse(
            content=response_dict["choices"][0]["message"]["content"],
            total_tokens=usage["total_tokens"],
            prompt_tokens=usage["prompt_tokens"],
            completion_tokens=usage["completion_tokens"],
            prompt_tokens_cached=prompt_tokens_cached,
            total_usd=total_usd,
            raw_response=response_dict,
        )
