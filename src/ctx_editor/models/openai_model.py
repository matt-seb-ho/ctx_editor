"""OpenAI model client implementation."""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Union

from openai import AsyncAzureOpenAI, AsyncOpenAI

from ..core.types import ModelResponse, ReasoningEffort
from .base import BaseModelClient, format_messages
from .endpoint_config import LoadBalancerConfig
from .load_balancer import EndpointLoadBalancer

# Module-level path for logging content filter errors. Set via
# set_content_filter_log_path() before running an experiment.
_content_filter_log_path: Optional[Path] = None
_cf_logger = logging.getLogger("ctx_editor.content_filter")


def set_content_filter_log_path(path: Union[str, Path]) -> None:
    """Configure where content filter errors are written (JSONL)."""
    global _content_filter_log_path
    _content_filter_log_path = Path(path)
    _content_filter_log_path.parent.mkdir(parents=True, exist_ok=True)


def _log_content_filter_error(messages: list[dict], error: Exception, model: str) -> None:
    """Append a content filter incident to the JSONL log file and emit a warning."""
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "model": model,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "request_messages": messages,
    }
    # Try to extract Azure's content_filter_result detail if present
    if hasattr(error, "body") and isinstance(error.body, dict):
        entry["error_body"] = error.body

    _cf_logger.warning(
        f"Azure content filter triggered on model={model}. "
        f"Messages count={len(messages)}. See content_filter_errors.jsonl for full request."
    )

    if _content_filter_log_path is not None:
        with open(_content_filter_log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
    else:
        # Fallback: log at WARNING with truncated messages so it's not lost
        _cf_logger.warning(f"Content filter request (no log file configured): {entry}")


def _is_content_filter_error(e: Exception) -> bool:
    """Return True if the exception is an Azure content filter rejection."""
    try:
        from openai import BadRequestError

        if isinstance(e, BadRequestError):
            # SDK exposes error.code as a direct property (most reliable)
            if getattr(e, "code", None) == "content_filter":
                return True
            # Fallback: body is {"error": {"code": ..., "innererror": ...}}
            body = getattr(e, "body", None) or {}
            error = body.get("error", {}) or {}
            code = error.get("code", "") or ""
            if "content_filter" in code.lower():
                return True
            inner = error.get("innererror", {}) or {}
            if "content_filter" in str(inner).lower():
                return True
    except ImportError:
        pass
    return False


class OpenAIModelClient(BaseModelClient):
    """Async OpenAI/Azure model client with optional load balancing."""

    _gpt5_temp_warned: bool = False  # Class-level flag to warn only once

    def __init__(
        self,
        load_balancer_config: Optional[LoadBalancerConfig] = None,
        base_url: Optional[str] = None,
        api_key_env: Optional[str] = None,
        auth_method: str = "api_key",
        aad_scope: str = "https://cognitiveservices.azure.com/.default",
    ):
        """Initialize the OpenAI client.

        Args:
            load_balancer_config: Optional load balancer configuration.
                If provided with endpoints, enables multi-endpoint load balancing.
                If None, uses single-endpoint mode (backward compatible).
            base_url: Optional base URL for OpenAI-compatible APIs (e.g. OpenRouter,
                Azure AI Foundry).
            api_key_env: Environment variable name for the API key when using base_url
                with ``auth_method="api_key"``.
            auth_method: Either ``"api_key"`` (default) or ``"azure_identity"``. The
                latter is for Azure AI Foundry's OpenAI-v1 endpoint: a chained
                AzureCliCredential -> ManagedIdentityCredential is used to fetch a
                bearer token, refreshed on demand.
            aad_scope: AAD scope to request bearer tokens for when using
                ``auth_method="azure_identity"``.
        """
        self.load_balancer: Optional[EndpointLoadBalancer] = None
        self.client: Optional[Union[AsyncOpenAI, AsyncAzureOpenAI]] = None

        if load_balancer_config and load_balancer_config.endpoints:
            # Multi-endpoint mode
            self.load_balancer = EndpointLoadBalancer(load_balancer_config)
        elif base_url:
            # Custom base URL mode (e.g. OpenRouter, Azure AI Foundry)
            if auth_method == "azure_identity":
                from .load_balancer import make_azure_identity_token_provider

                base_url_normalized = base_url if base_url.endswith("/") else base_url + "/"
                token_provider = make_azure_identity_token_provider(scope=aad_scope)
                self.client = AsyncOpenAI(api_key=token_provider, base_url=base_url_normalized)
            else:
                api_key = os.environ.get(api_key_env or "OPENAI_API_KEY")
                if not api_key:
                    raise ValueError(
                        f"API key not found: env var '{api_key_env or 'OPENAI_API_KEY'}' not set"
                    )
                self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        else:
            # Single-endpoint mode (backward compatible)
            if os.getenv("USE_AZURE_OAI", "false").lower() == "true":
                print("Using Azure OpenAI")
                from .setup_azure_oai_client import setup_azure_oai_client

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
        timeout: int = 300,
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
            response = await self._generate_with_load_balancer(max_retries, **kwargs)
        else:
            response = await self._generate_single_client(max_retries, **kwargs)

        return self._parse_response(response, model)

    async def _generate_with_load_balancer(self, max_retries: int, **kwargs: Any) -> Any:
        """Generate using load-balanced endpoints."""

        async def call_api(client: Union[AsyncOpenAI, AsyncAzureOpenAI], **kw: Any) -> Any:
            last_error = None
            for attempt in range(max_retries):
                try:
                    return await client.chat.completions.create(**kw)
                except Exception as e:
                    if _is_content_filter_error(e):
                        _log_content_filter_error(kw.get("messages", []), e, kw.get("model", "unknown"))
                        raise
                    last_error = e
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2**attempt)
            raise last_error

        return await self.load_balancer.execute_with_endpoint(
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
                if _is_content_filter_error(e):
                    _log_content_filter_error(kwargs.get("messages", []), e, kwargs.get("model", "unknown"))
                    raise
                last_error = e
                if attempt < max_retries - 1:
                    await asyncio.sleep(2**attempt)
        raise RuntimeError(f"Failed after {max_retries} attempts: {last_error}")

    def _parse_response(self, response: Any, model: str) -> ModelResponse:
        """Parse API response into ModelResponse."""
        response_dict = response.model_dump()
        # Some Foundry-hosted non-OpenAI models (e.g. DeepSeek-V4-Flash) may
        # return usage=None or omit prompt_tokens_details. Coerce missing
        # fields to zero rather than crashing.
        usage = response_dict.get("usage") or {}

        prompt_tokens_cached = 0
        details = usage.get("prompt_tokens_details") if isinstance(usage, dict) else None
        if details:
            prompt_tokens_cached = details.get("cached_tokens", 0) or 0

        prompt_tokens = usage.get("prompt_tokens", 0) or 0
        completion_tokens = usage.get("completion_tokens", 0) or 0
        total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens) or 0

        total_usd = self._calculate_cost(
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            prompt_tokens_cached=prompt_tokens_cached,
        )

        return ModelResponse(
            content=response_dict["choices"][0]["message"]["content"],
            total_tokens=total_tokens,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            prompt_tokens_cached=prompt_tokens_cached,
            total_usd=total_usd,
            raw_response=response_dict,
        )

    def get_load_balancer_stats(self) -> Optional[dict[str, Any]]:
        """Get load balancer statistics if available."""
        if self.load_balancer:
            return self.load_balancer.get_stats()
        return None
