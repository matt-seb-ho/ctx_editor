"""Context modification strategies.

The AC3 family is the canonical set of context-edit operations:

- ``AC3AugmentStrategy``  (alias: ``AppendAnalysisStrategy``)
- ``AC3ResetStrategy``    (alias: ``ContextEditV2Strategy``) — "Gated-Reset" is
  this class with ``min_turns`` / ``max_resets`` set.
- ``AC3RewriteStrategy``  (alias: ``ContextCompactionStrategy``)

Prior-work baselines used for comparison: ``BaselineStrategy``,
``AssistantOmitStrategy``, ``ERGORestartStrategy``, plus the legacy aliases in
``prior_work_baselines``.

Superseded experimental strategies live under ``strategies.legacy`` and are
re-exported here for backwards compatibility only.

See ``docs/strategy_name_history.md`` for the full rename map.
"""

from .analyzer import ConversationAnalyzer
from .append_analysis import AC3AugmentStrategy, AppendAnalysisStrategy
from .assistant_omit import AssistantOmitStrategy
from .base import ContextStrategy
from .baseline import BaselineStrategy
from .context_compaction import AC3RewriteStrategy, ContextCompactionStrategy
from .context_edit_v2 import AC3ResetStrategy, ContextEditV2Strategy
from .ergo_restart import ERGORestartStrategy
from .legacy import (
    AgenticEditStrategy,
    ContextEditStrategy,
    ReflectionStrategy,
)
from .prior_work_baselines import ConcatenateUserStrategy, OmitAssistantStrategy

__all__ = [
    # Protocol
    "ContextStrategy",
    # AC3 canonical names
    "AC3AugmentStrategy",
    "AC3ResetStrategy",
    "AC3RewriteStrategy",
    # Baselines
    "BaselineStrategy",
    "AssistantOmitStrategy",
    "ERGORestartStrategy",
    "ConcatenateUserStrategy",
    "OmitAssistantStrategy",
    # Shared analyzer
    "ConversationAnalyzer",
    # Backwards-compatible aliases (predate AC3 naming)
    "AppendAnalysisStrategy",
    "ContextEditV2Strategy",
    "ContextCompactionStrategy",
    # Legacy strategies (kept for historical reproducibility)
    "AgenticEditStrategy",
    "ContextEditStrategy",
    "ReflectionStrategy",
]
