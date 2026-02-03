"""Multi-endpoint load balancer for OpenAI API clients."""

import asyncio
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Union

from openai import AsyncAzureOpenAI, AsyncOpenAI

from .endpoint_config import EndpointConfig, LoadBalancerConfig

logger = logging.getLogger("ctx_editor.load_balancer")


@dataclass
class ManagedEndpoint:
    """An endpoint with its client and concurrency control."""

    config: EndpointConfig
    client: Union[AsyncOpenAI, AsyncAzureOpenAI]
    semaphore: asyncio.Semaphore
    active_requests: int = 0
    total_requests: int = 0
    failed_requests: int = 0

    @property
    def load(self) -> float:
        """Current load as fraction of max capacity."""
        return self.active_requests / self.config.max_concurrent if self.config.max_concurrent > 0 else 0.0


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
            managed = ManagedEndpoint(
                config=ep_config,
                client=client,
                semaphore=asyncio.Semaphore(ep_config.max_concurrent),
            )
            self.endpoints.append(managed)
            logger.info(
                f"Initialized endpoint '{ep_config.name}' "
                f"(type={ep_config.type}, max_concurrent={ep_config.max_concurrent}, "
                f"models={ep_config.supported_models})"
            )

            # Build model -> endpoints mapping
            for model in ep_config.supported_models:
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
            # Find endpoint with lowest current load
            return min(endpoints, key=lambda ep: ep.load)

        elif strategy == "priority":
            # Return first available (already sorted by priority)
            for ep in endpoints:
                if ep.active_requests < ep.config.max_concurrent:
                    return ep
            # All at capacity, return first (highest priority)
            return endpoints[0]

        return endpoints[0]

    async def execute_with_endpoint(
        self,
        model: str,
        operation: Callable[..., Any],
        **kwargs: Any,
    ) -> Any:
        """Execute an operation with automatic endpoint selection and fallback.

        Args:
            model: Model name for endpoint selection.
            operation: Async function that takes (client, **kwargs) and returns result.
            **kwargs: Arguments to pass to operation.

        Returns:
            Result from the operation.

        Raises:
            ValueError: If no endpoints support the model.
            RuntimeError: If all endpoints fail.
        """
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

            try:
                async with endpoint.semaphore:
                    endpoint.active_requests += 1
                    try:
                        logger.debug(
                            f"Executing on endpoint '{endpoint.config.name}' "
                            f"(active={endpoint.active_requests}/{endpoint.config.max_concurrent})"
                        )
                        result = await operation(endpoint.client, **kwargs)
                        endpoint.total_requests += 1
                        return result
                    finally:
                        endpoint.active_requests -= 1

            except Exception as e:
                last_error = e
                endpoint.failed_requests += 1
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
        """Get statistics for all endpoints."""
        return {
            ep.config.name: {
                "type": ep.config.type,
                "supported_models": ep.config.supported_models,
                "max_concurrent": ep.config.max_concurrent,
                "active_requests": ep.active_requests,
                "total_requests": ep.total_requests,
                "failed_requests": ep.failed_requests,
                "load": ep.load,
            }
            for ep in self.endpoints
        }
