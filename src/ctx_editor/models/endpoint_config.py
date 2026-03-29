"""Configuration dataclasses for multi-endpoint load balancing."""

from dataclasses import dataclass, field
from typing import Any, Literal, Optional


@dataclass
class EndpointConfig:
    """Configuration for a single API endpoint."""

    name: str
    type: Literal["azure", "openai", "openrouter"]
    supported_models: list[str]
    max_concurrent: int = 10
    priority: int = 1  # Lower = higher priority

    # OpenAI-specific
    api_key_env: Optional[str] = None

    # Azure-specific
    endpoint: Optional[str] = None
    api_version: str = "2024-10-21"
    auth_method: Literal["azure_cli", "api_key"] = "azure_cli"


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
