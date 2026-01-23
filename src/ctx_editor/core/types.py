"""Shared types and dataclasses for the context editor system."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from enum import Enum


class MessageRole(str, Enum):
    """Enum for message roles in a conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    LOG = "log"


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
class VerificationResult:
    """Result of verifying an assistant response."""
    response_type: str  # "answer_attempt", "clarification", "partial_answer", etc.
    is_answer_attempt: bool = False
    cost_usd: float = 0.0
    raw_response: Optional[dict[str, Any]] = None

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
    assistant_model: str = "gpt-4o-mini"
    user_model: str = "gpt-4o-mini"
    system_model: str = "gpt-4o-mini"
    temperature: float = 1.0
    verbose: bool = False


@dataclass
class SimulationResult:
    """Result of a complete conversation simulation."""
    sample_id: str
    task_name: str
    is_correct: bool
    score: float
    num_turns: int
    total_cost_usd: float
    trace: list[dict[str, Any]]
    extracted_answer: Optional[str] = None
    evaluation_result: Optional[EvaluationResult] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
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
