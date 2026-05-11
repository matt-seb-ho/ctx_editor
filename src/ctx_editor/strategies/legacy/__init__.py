"""Legacy / superseded strategies.

These are kept for historical comparison and reproducibility of older experiments.
They are not part of the current AC3 lineup and should not be used in new work.

- AgenticEditStrategy: separate decision-prompt gating, superseded by AC3GatedResetStrategy
- ContextEditStrategy (v1): unconditional rewrite, superseded by AC3RewriteStrategy
- ReflectionStrategy: reflection-only append, superseded by AC3AugmentStrategy
"""

from .agentic_edit import AgenticEditStrategy
from .context_edit import ContextEditStrategy
from .reflection import ReflectionStrategy

__all__ = [
    "AgenticEditStrategy",
    "ContextEditStrategy",
    "ReflectionStrategy",
]
