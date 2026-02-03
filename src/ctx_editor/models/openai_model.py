"""OpenAI model client implementation."""

import asyncio
import os
from typing import Any, Optional, Union

from openai import AsyncAzureOpenAI, AsyncOpenAI

from ..core.types import ModelResponse, ReasoningEffort
from .base import BaseModelClient, format_messages
from .endpoint_config import LoadBalancerConfig
from .load_balancer import EndpointLoadBalancer
from .setup_azure_oai_client import setup_azure_oai_client


class OpenAIModelClient(BaseModelClient):
    """Async OpenAI/Azure model client with optional load balancing."""

    _gpt5_temp_warned: bool = False  # Class-level flag to warn only once

    def __init__(self, load_balancer_config: Optional[LoadBalancerConfig] = None):
        """Initialize the OpenAI client.

        Args:
            load_balancer_config: Optional load balancer configuration.
                If provided with endpoints, enables multi-endpoint load balancing.
                If None, uses single-endpoint mode (backward compatible).
        """
        self.load_balancer: Optional[EndpointLoadBalancer] = None
        self.client: Optional[Union[AsyncOpenAI, AsyncAzureOpenAI]] = None

        if load_balancer_config and load_balancer_config.endpoints:
            # Multi-endpoint mode
            self.load_balancer = EndpointLoadBalancer(load_balancer_config)
        else:
            # Single-endpoint mode (backward compatible)
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

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "timeout": timeout,
            "max_completion_tokens": max_tokens,
            "temperature": temperature,
        }
        if is_json:
            kwargs["response_format"] = {"type": "json_object"}
        if reasoning_effort:
            kwargs["reasoning_effort"] = reasoning_effort

        # Execute with load balancer or single client
        if self.load_balancer:
            response = await self._generate_with_load_balancer(model, max_retries, **kwargs)
        else:
            response = await self._generate_single_client(max_retries, **kwargs)

        return self._parse_response(response, model)

    async def _generate_with_load_balancer(
        self,
        model: str,
        max_retries: int,
        **kwargs: Any,
    ) -> Any:
        """Generate using load-balanced endpoints."""

        async def call_api(client: Union[AsyncOpenAI, AsyncAzureOpenAI], **kw: Any) -> Any:
            last_error = None
            for attempt in range(max_retries):
                try:
                    return await client.chat.completions.create(**kw)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2**attempt)
            raise last_error

        return await self.load_balancer.execute_with_endpoint(
            model=model,
            operation=call_api,
            **kwargs,
        )

    async def _generate_single_client(self, max_retries: int, **kwargs: Any) -> Any:
        """Generate using single client (backward compatible)."""
        last_error = None
        for attempt in range(max_retries):
            try:
                return await self.client.chat.completions.create(**kwargs)
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    await asyncio.sleep(2**attempt)
        raise RuntimeError(f"Failed after {max_retries} attempts: {last_error}")

    def _parse_response(self, response: Any, model: str) -> ModelResponse:
        """Parse API response into ModelResponse."""
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

    def get_load_balancer_stats(self) -> Optional[dict[str, Any]]:
        """Get load balancer statistics if available."""
        if self.load_balancer:
            return self.load_balancer.get_stats()
        return None
