"""Configuration dataclasses for multi-endpoint load balancing."""

from dataclasses import dataclass, field
from typing import Any, Literal, Optional, Union


@dataclass
class EndpointConfig:
    """Configuration for a single API endpoint."""

    name: str
    type: Literal["azure", "openai", "openrouter", "azure_foundry"]
    # Either a list of model names (each gets endpoint-level max_concurrent),
    # or a dict mapping model name -> per-model concurrency cap. Mixed forms
    # are not supported; pick one per endpoint.
    supported_models: Union[list[str], dict[str, int]]
    max_concurrent: int = 10
    priority: int = 1  # Lower = higher priority

    # OpenAI-specific
    api_key_env: Optional[str] = None

    # Azure-specific
    endpoint: Optional[str] = None
    api_version: str = "2024-10-21"
    auth_method: Literal["azure_cli", "api_key", "azure_identity"] = "azure_cli"

    # Azure Foundry-specific: AAD scope to request bearer tokens for.
    # Defaults to Cognitive Services / AI Services scope used by Foundry.
    aad_scope: str = "https://cognitiveservices.azure.com/.default"

    def get_model_capacities(self) -> dict[str, int]:
        """Return {model: concurrency_cap}, resolving list form to max_concurrent."""
        if isinstance(self.supported_models, dict):
            return dict(self.supported_models)
        return {m: self.max_concurrent for m in self.supported_models}

    def model_names(self) -> list[str]:
        """Return the list of supported model names regardless of form."""
        if isinstance(self.supported_models, dict):
            return list(self.supported_models.keys())
        return list(self.supported_models)


@dataclass
class LoadBalancerConfig:
    """Configuration for the endpoint load balancer."""

    endpoints: list[EndpointConfig] = field(default_factory=list)
    routing_strategy: Literal["round_robin", "least_loaded", "priority"] = "round_robin"
    fallback_enabled: bool = True
    max_retries_per_endpoint: int = 2

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LoadBalancerConfig":
        """Create config from dictionary (e.g., from Hydra/OmegaConf)."""
        endpoints = [EndpointConfig(**ep) for ep in data.get("endpoints", [])]
        return cls(
            endpoints=endpoints,
            routing_strategy=data.get("routing_strategy", "round_robin"),
            fallback_enabled=data.get("fallback_enabled", True),
            max_retries_per_endpoint=data.get("max_retries_per_endpoint", 2),
        )
