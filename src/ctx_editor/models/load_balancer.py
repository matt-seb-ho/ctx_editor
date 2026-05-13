"""Multi-endpoint load balancer for OpenAI API clients."""

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Union

from openai import AsyncAzureOpenAI, AsyncOpenAI

from .endpoint_config import EndpointConfig, LoadBalancerConfig

logger = logging.getLogger("ctx_editor.load_balancer")


def make_azure_identity_token_provider(
    scope: str = "https://cognitiveservices.azure.com/.default",
    refresh_skew_seconds: int = 300,
) -> Callable[[], Any]:
    """Return an async callable that yields a cached AAD bearer token.

    Mirrors the auth pattern used in scripts/test_non_oai.py: a chained
    AzureCliCredential -> ManagedIdentityCredential. The returned callable is
    suitable as the ``api_key`` argument to ``openai.AsyncOpenAI``, which
    invokes it to populate the Authorization header on each request.
    """
    from azure.identity import (
        AzureCliCredential,
        ChainedTokenCredential,
        ManagedIdentityCredential,
    )

    credential = ChainedTokenCredential(
        AzureCliCredential(),
        ManagedIdentityCredential(),
    )

    cache: dict[str, Any] = {"token": None, "expires_on": 0}
    lock = asyncio.Lock()

    async def _provider() -> str:
        async with lock:
            now = time.time()
            if cache["token"] is None or now >= cache["expires_on"] - refresh_skew_seconds:
                # get_token is sync; offload so we don't block the event loop.
                access = await asyncio.to_thread(credential.get_token, scope)
                cache["token"] = access.token
                cache["expires_on"] = access.expires_on
            return cache["token"]

    return _provider


@dataclass
class ManagedEndpoint:
    """An endpoint with its client and per-model concurrency control."""

    config: EndpointConfig
    client: Union[AsyncOpenAI, AsyncAzureOpenAI]
    # Per-model semaphores + counters: each (endpoint, model) pair has its own
    # concurrency cap, so e.g. dl-openai-1 can hold 40 in-flight gpt-5.4 requests
    # while only allowing 10 in-flight gpt-5 requests.
    model_semaphores: dict[str, asyncio.Semaphore] = field(default_factory=dict)
    model_active: dict[str, int] = field(default_factory=dict)
    model_total: dict[str, int] = field(default_factory=dict)
    model_failed: dict[str, int] = field(default_factory=dict)

    @property
    def active_requests(self) -> int:
        """Sum of in-flight requests across all models on this endpoint."""
        return sum(self.model_active.values())

    @property
    def total_requests(self) -> int:
        return sum(self.model_total.values())

    @property
    def failed_requests(self) -> int:
        return sum(self.model_failed.values())

    def load_for(self, model: str) -> float:
        """Per-model load as fraction of that model's capacity on this endpoint."""
        cap = self.config.get_model_capacities().get(model, self.config.max_concurrent)
        if cap <= 0:
            return 1.0
        return self.model_active.get(model, 0) / cap

    def capacity_for(self, model: str) -> int:
        return self.config.get_model_capacities().get(model, self.config.max_concurrent)


class EndpointLoadBalancer:
    """Manages multiple OpenAI endpoints with load balancing."""

    def __init__(self, config: LoadBalancerConfig):
        """Initialize with configuration.

        Args:
            config: Load balancer configuration with endpoint definitions.
        """
        self.config = config
        self.endpoints: list[ManagedEndpoint] = []
        self._model_to_endpoints: dict[str, list[ManagedEndpoint]] = {}
        self._round_robin_counters: dict[str, int] = {}
        self._lock = asyncio.Lock()

        self._initialize_endpoints()

    def _initialize_endpoints(self) -> None:
        """Create clients for all configured endpoints."""
        for ep_config in self.config.endpoints:
            client = self._create_client(ep_config)
            capacities = ep_config.get_model_capacities()
            model_semaphores = {m: asyncio.Semaphore(cap) for m, cap in capacities.items()}
            managed = ManagedEndpoint(
                config=ep_config,
                client=client,
                model_semaphores=model_semaphores,
                model_active={m: 0 for m in capacities},
                model_total={m: 0 for m in capacities},
                model_failed={m: 0 for m in capacities},
            )
            self.endpoints.append(managed)
            logger.info(
                f"Initialized endpoint '{ep_config.name}' "
                f"(type={ep_config.type}, models={capacities})"
            )

            # Build model -> endpoints mapping
            for model in ep_config.model_names():
                if model not in self._model_to_endpoints:
                    self._model_to_endpoints[model] = []
                    self._round_robin_counters[model] = 0
                self._model_to_endpoints[model].append(managed)

        # Sort endpoints by priority for each model
        for model in self._model_to_endpoints:
            self._model_to_endpoints[model].sort(key=lambda ep: ep.config.priority)

        logger.info(
            f"Load balancer initialized with {len(self.endpoints)} endpoints, "
            f"supporting models: {list(self._model_to_endpoints.keys())}"
        )

    def _create_client(self, config: EndpointConfig) -> Union[AsyncOpenAI, AsyncAzureOpenAI]:
        """Create an async client for the endpoint."""
        if config.type == "openai":
            api_key = os.environ.get(config.api_key_env or "OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    f"API key not found for endpoint '{config.name}': "
                    f"env var '{config.api_key_env or 'OPENAI_API_KEY'}' not set"
                )
            return AsyncOpenAI(api_key=api_key)

        elif config.type == "azure_foundry":
            # Azure AI Foundry exposes an OpenAI-v1 compatible endpoint at
            # {endpoint}/openai/v1/. Auth is an AAD bearer token (the OpenAI
            # client uses it as the api_key, becoming the Authorization header).
            if not config.endpoint:
                raise ValueError(
                    f"azure_foundry endpoint '{config.name}' requires 'endpoint' to be set"
                )
            base_url = config.endpoint if config.endpoint.endswith("/") else config.endpoint + "/"
            if config.auth_method == "api_key":
                api_key = os.environ.get(config.api_key_env or "AZURE_FOUNDRY_API_KEY")
                if not api_key:
                    raise ValueError(
                        f"API key not found for Azure Foundry endpoint '{config.name}': "
                        f"env var '{config.api_key_env or 'AZURE_FOUNDRY_API_KEY'}' not set"
                    )
                return AsyncOpenAI(api_key=api_key, base_url=base_url)
            # Default: AAD identity (CLI -> Managed Identity)
            token_provider = make_azure_identity_token_provider(scope=config.aad_scope)
            return AsyncOpenAI(api_key=token_provider, base_url=base_url)

        elif config.type == "openrouter":
            api_key = os.environ.get(config.api_key_env or "OPENROUTER_API_KEY")
            if not api_key:
                raise ValueError(
                    f"API key not found for OpenRouter endpoint '{config.name}': "
                    f"env var '{config.api_key_env or 'OPENROUTER_API_KEY'}' not set"
                )
            return AsyncOpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1",
            )

        elif config.type == "azure":
            if config.auth_method == "azure_cli":
                from azure.identity import AzureCliCredential, get_bearer_token_provider

                token_provider = get_bearer_token_provider(
                    AzureCliCredential(),
                    "https://cognitiveservices.azure.com/.default",
                )
                return AsyncAzureOpenAI(
                    azure_endpoint=config.endpoint,
                    azure_ad_token_provider=token_provider,
                    api_version=config.api_version,
                )
            else:  # api_key auth
                api_key = os.environ.get(config.api_key_env)
                if not api_key:
                    raise ValueError(
                        f"API key not found for Azure endpoint '{config.name}': "
                        f"env var '{config.api_key_env}' not set"
                    )
                return AsyncAzureOpenAI(
                    azure_endpoint=config.endpoint,
                    api_key=api_key,
                    api_version=config.api_version,
                )

        raise ValueError(f"Unknown endpoint type: {config.type}")

    def get_endpoints_for_model(self, model: str) -> list[ManagedEndpoint]:
        """Get all endpoints that support a model."""
        return self._model_to_endpoints.get(model, [])

    async def select_endpoint(self, model: str) -> Optional[ManagedEndpoint]:
        """Select the best endpoint for a model based on routing strategy.

        Args:
            model: Model name to route.

        Returns:
            Selected endpoint or None if no endpoints support the model.
        """
        endpoints = self.get_endpoints_for_model(model)
        if not endpoints:
            return None

        strategy = self.config.routing_strategy

        if strategy == "round_robin":
            async with self._lock:
                counter = self._round_robin_counters[model]
                endpoint = endpoints[counter % len(endpoints)]
                self._round_robin_counters[model] = counter + 1
                return endpoint

        elif strategy == "least_loaded":
            # Find endpoint with lowest per-model load. With unequal per-model
            # capacities (e.g. dl-openai-1 has 4x gpt-5.4 quota of dl-openai-3),
            # this naturally yields traffic split proportional to those caps.
            return min(endpoints, key=lambda ep: ep.load_for(model))

        elif strategy == "priority":
            # Return first available (already sorted by priority)
            for ep in endpoints:
                if ep.model_active.get(model, 0) < ep.capacity_for(model):
                    return ep
            # All at capacity, return first (highest priority)
            return endpoints[0]

        return endpoints[0]

    async def execute_with_endpoint(
        self,
        operation: Callable[..., Any],
        **kwargs: Any,
    ) -> Any:
        """Execute an operation with automatic endpoint selection and fallback.

        Args:
            operation: Async function that takes (client, **kwargs) and returns result.
            **kwargs: Arguments to pass to operation. Must include 'model' key.

        Returns:
            Result from the operation.

        Raises:
            ValueError: If no endpoints support the model.
            RuntimeError: If all endpoints fail.
        """
        model = kwargs.get("model")
        if not model:
            raise ValueError("'model' must be provided in kwargs")

        endpoints = self.get_endpoints_for_model(model)
        if not endpoints:
            available_models = list(self._model_to_endpoints.keys())
            raise ValueError(
                f"No endpoints configured for model '{model}'. "
                f"Available models: {available_models}"
            )

        last_error = None
        tried_endpoints: set[str] = set()
        max_attempts = len(endpoints) * self.config.max_retries_per_endpoint

        for attempt in range(max_attempts):
            endpoint = await self.select_endpoint(model)

            # Track which endpoints we've tried
            if not self.config.fallback_enabled and endpoint.config.name in tried_endpoints:
                break
            tried_endpoints.add(endpoint.config.name)

            sem = endpoint.model_semaphores.get(model)
            if sem is None:
                # Defensive: model should have been registered in init; fall through.
                last_error = ValueError(
                    f"Endpoint '{endpoint.config.name}' has no semaphore for model '{model}'"
                )
                continue
            try:
                async with sem:
                    endpoint.model_active[model] = endpoint.model_active.get(model, 0) + 1
                    try:
                        logger.debug(
                            f"Executing '{model}' on '{endpoint.config.name}' "
                            f"(active={endpoint.model_active[model]}/{endpoint.capacity_for(model)})"
                        )
                        result = await operation(endpoint.client, **kwargs)
                        endpoint.model_total[model] = endpoint.model_total.get(model, 0) + 1
                        return result
                    finally:
                        endpoint.model_active[model] -= 1

            except Exception as e:
                last_error = e
                endpoint.model_failed[model] = endpoint.model_failed.get(model, 0) + 1
                logger.warning(
                    f"Request failed on endpoint '{endpoint.config.name}': {e}"
                )

                if not self.config.fallback_enabled:
                    raise

                # Brief pause before retry
                await asyncio.sleep(0.1)

        raise RuntimeError(
            f"All endpoints failed for model '{model}' after {max_attempts} attempts. "
            f"Tried endpoints: {tried_endpoints}. Last error: {last_error}"
        )

    def get_stats(self) -> dict[str, Any]:
        """Get statistics for all endpoints, including per-model breakdown."""
        return {
            ep.config.name: {
                "type": ep.config.type,
                "model_capacities": ep.config.get_model_capacities(),
                "max_concurrent": ep.config.max_concurrent,
                "active_requests": ep.active_requests,
                "total_requests": ep.total_requests,
                "failed_requests": ep.failed_requests,
                "per_model": {
                    m: {
                        "capacity": ep.capacity_for(m),
                        "active": ep.model_active.get(m, 0),
                        "total": ep.model_total.get(m, 0),
                        "failed": ep.model_failed.get(m, 0),
                        "load": ep.load_for(m),
                    }
                    for m in ep.config.model_names()
                },
            }
            for ep in self.endpoints
        }
