"""Shared types and dataclasses for the context editor system."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal, Optional
from enum import Enum


class MessageRole(str, Enum):
    """Enum for message roles in a conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    LOG = "log"


# Type alias for agent roles used in model configuration
AgentRole = Literal["user", "assistant", "system", "ctx_editor"]

# Type alias for reasoning effort levels
ReasoningEffort = Literal["minimal", "low", "medium", "high"]


@dataclass
class RoleConfig:
    """Configuration for a specific agent role's model settings."""
    model: str = "gpt-4o-mini"
    max_tokens: int = 2000
    temperature: float = 1.0
    reasoning_effort: Optional[ReasoningEffort] = None

    def is_reasoning_model(self) -> bool:
        """Check if this role uses a reasoning model."""
        return any(m in self.model for m in ["o1", "o3", "deepseek-r1"])

    def get_effective_max_tokens(self) -> int:
        """Get effective max tokens, adjusting for reasoning models."""
        if self.is_reasoning_model():
            return max(self.max_tokens, 16000)
        return self.max_tokens


@dataclass
class ModelConfig:
    """Configuration for all model roles in the system.

    Allows specifying different models, token budgets, and reasoning efforts
    for different agent roles (user simulator, assistant, system operations,
    context editor).
    """
    user: RoleConfig = field(default_factory=lambda: RoleConfig(model="gpt-4o-mini", max_tokens=1000))
    assistant: RoleConfig = field(default_factory=lambda: RoleConfig(model="gpt-4o", max_tokens=2000))
    system: RoleConfig = field(default_factory=lambda: RoleConfig(model="gpt-4o-mini", max_tokens=1000, temperature=0.0))
    ctx_editor: RoleConfig = field(default_factory=lambda: RoleConfig(model="gpt-4o-mini", max_tokens=4000))

    def get_role_config(self, role: AgentRole) -> RoleConfig:
        """Get configuration for a specific role."""
        return getattr(self, role)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModelConfig":
        """Create ModelConfig from a dictionary (e.g., from Hydra config)."""
        role_configs = {}
        for role in ["user", "assistant", "system", "ctx_editor"]:
            if role in data:
                role_data = data[role]
                if isinstance(role_data, dict):
                    role_configs[role] = RoleConfig(**role_data)
                elif isinstance(role_data, str):
                    # Backward compatibility: if just a model name string
                    role_configs[role] = RoleConfig(model=role_data)
        return cls(**role_configs)


@dataclass
class Message:
    """A single message in a conversation."""
    role: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format for API calls."""
        return {"role": self.role, "content": self.content}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Message":
        """Create a Message from a dictionary."""
        return cls(
            role=data["role"],
            content=data["content"],
            metadata=data.get("metadata", {}),
            timestamp=data.get("timestamp"),
        )


@dataclass
class RoleUsageStats:
    """Usage statistics for a single role."""
    num_requests: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    cached_tokens: int = 0
    cost_usd: float = 0.0

    def record(self, response: "ModelResponse") -> None:
        """Record usage from a model response."""
        self.num_requests += 1
        self.input_tokens += response.prompt_tokens
        self.output_tokens += response.completion_tokens
        self.cached_tokens += response.prompt_tokens_cached
        # reasoning_tokens would come from response if available
        if response.raw_response and "usage" in response.raw_response:
            usage = response.raw_response["usage"]
            if "completion_tokens_details" in usage:
                details = usage["completion_tokens_details"]
                self.reasoning_tokens += details.get("reasoning_tokens", 0)
        self.cost_usd += response.total_usd

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "num_requests": self.num_requests,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "reasoning_tokens": self.reasoning_tokens,
            "cached_tokens": self.cached_tokens,
            "cost_usd": self.cost_usd,
        }


@dataclass
class UsageStats:
    """Aggregated usage statistics across all roles."""
    user: RoleUsageStats = field(default_factory=RoleUsageStats)
    assistant: RoleUsageStats = field(default_factory=RoleUsageStats)
    system: RoleUsageStats = field(default_factory=RoleUsageStats)
    ctx_editor: RoleUsageStats = field(default_factory=RoleUsageStats)

    def record(self, role: AgentRole, response: "ModelResponse") -> None:
        """Record usage for a specific role."""
        getattr(self, role).record(response)

    def total_cost_usd(self) -> float:
        """Get total cost across all roles."""
        return self.user.cost_usd + self.assistant.cost_usd + self.system.cost_usd + self.ctx_editor.cost_usd

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "user": self.user.to_dict(),
            "assistant": self.assistant.to_dict(),
            "system": self.system.to_dict(),
            "ctx_editor": self.ctx_editor.to_dict(),
            "total_cost_usd": self.total_cost_usd(),
        }


@dataclass
class VerificationResult:
    """Result of verifying an assistant response."""
    response_type: str  # "answer_attempt", "clarification", "partial_answer", etc.
    is_answer_attempt: bool = False
    cost_usd: float = 0.0
    raw_response: Optional[dict[str, Any]] = None
    model_response: Optional["ModelResponse"] = None  # For detailed usage tracking

    def __post_init__(self):
        self.is_answer_attempt = self.response_type == "answer_attempt"


@dataclass
class EvaluationResult:
    """Result of evaluating an extracted answer."""
    is_correct: bool
    score: float
    extracted_answer: str
    feedback: Optional[str] = None
    raw_evaluation: Optional[dict[str, Any]] = None


@dataclass
class SimulatorConfig:
    """Configuration for the conversation simulator."""
    max_turns: int = 20
    model_config: ModelConfig = field(default_factory=ModelConfig)
    verbose: bool = False
    include_trace_history: bool = False  # Include full history in trace output (for context editing)

    # Backward compatibility properties
    @property
    def assistant_model(self) -> str:
        return self.model_config.assistant.model

    @property
    def user_model(self) -> str:
        return self.model_config.user.model

    @property
    def system_model(self) -> str:
        return self.model_config.system.model

    @property
    def temperature(self) -> float:
        return self.model_config.assistant.temperature


@dataclass
class SimulationResult:
    """Result of a complete conversation simulation."""
    sample_id: str
    task_name: str
    is_correct: bool
    score: float
    num_turns: int
    total_cost_usd: float
    trace: dict[str, Any]  # Contains 'messages', 'logs', and optionally 'history'
    extracted_answer: Optional[str] = None
    evaluation_result: Optional[EvaluationResult] = None
    usage_stats: Optional[UsageStats] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "sample_id": self.sample_id,
            "task_name": self.task_name,
            "is_correct": self.is_correct,
            "score": self.score,
            "num_turns": self.num_turns,
            "total_cost_usd": self.total_cost_usd,
            "extracted_answer": self.extracted_answer,
            "trace": self.trace,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }
        if self.usage_stats:
            result["usage_stats"] = self.usage_stats.to_dict()
        return result


@dataclass
class ModelResponse:
    """Response from a model API call."""
    content: str
    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    prompt_tokens_cached: int = 0
    total_usd: float = 0.0
    raw_response: Optional[dict[str, Any]] = None

    def to_message(self, role: str = "assistant") -> Message:
        """Convert to a Message object."""
        return Message(
            role=role,
            content=self.content,
            metadata={"cost_usd": self.total_usd},
        )
