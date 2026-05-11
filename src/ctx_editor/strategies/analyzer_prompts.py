"""Single source of truth for analyzer prompt versions.

The ``ConversationAnalyzer`` supports several prompt versions, each combining a
specific *flow* (single-query / two-query / soft-attention / s1-simplified) with
specific *templates* (filename stems under ``strategies/prompts/``). Historically
the version → flow + templates mapping was an ``if/elif`` chain inside
``ConversationAnalyzer.__init__`` and ``analyze()``. This module lifts it out so:

- Adding a new version (e.g. ``v12``) is a single dict entry here.
- ``ConversationAnalyzer`` itself stays small — it just dispatches by ``flow``.
- Every benchmark (LiC, CollabLLM, Huang eval, future) names the same versions.
- A registry-aware lister/validator can be used in tests, configs, and tooling.

Template files live in ``strategies/prompts/<name>.txt``. The filename stems are
stored here, not the file contents — files stay versioned on disk to make diffs
easy.

See ``docs/strategy_name_history.md`` for the rename map and
``docs/experiment_organization_audit.md`` for the phased refactor plan.
"""

from dataclasses import dataclass
from typing import Literal

# Flows supported by ``ConversationAnalyzer``. Each maps to one private
# ``_analyze_*`` method on the analyzer class.
AnalyzerFlow = Literal[
    "two_query",          # hard-attention: Query 1 sees user msgs only
    "two_query_soft",     # soft-attention: Query 1 sees full conversation
    "single_query_combined",  # one combined task spec + comparison prompt
    "single_query_s1",    # simplified header-format (Azure content-filter safe)
    "single_query_legacy",    # original v4/v5 single-prompt format
]


@dataclass(frozen=True)
class AnalyzerPromptVersion:
    """Specification for one analyzer prompt version.

    Attributes:
        name: Stable identifier (e.g. ``"v8"``). This is what callers pass as
            ``ConversationAnalyzer(prompt_version=...)`` and what appears in
            Hydra configs as ``analyzer_prompt_version``.
        flow: Which analyzer method handles this version.
        task_spec_template: Filename stem (under ``strategies/prompts/``) for
            the task-spec prompt. Required for two-query flows.
        compare_template: Filename stem for the comparison prompt. Required for
            two-query flows.
        single_template: Filename stem for the single combined prompt. Required
            for single-query flows.
        description: Short human-readable note. Surface in docs / `--help`.
    """

    name: str
    flow: AnalyzerFlow
    task_spec_template: str | None = None
    compare_template: str | None = None
    single_template: str | None = None
    description: str = ""


# Registry of all known analyzer prompt versions. Add new versions here.
ANALYZER_PROMPT_REGISTRY: dict[str, AnalyzerPromptVersion] = {
    "v4": AnalyzerPromptVersion(
        name="v4",
        flow="single_query_legacy",
        single_template="analyzer_v4",
        description="Original single-query analysis prompt. Kept for backward compat.",
    ),
    "v5": AnalyzerPromptVersion(
        name="v5",
        flow="single_query_legacy",
        single_template="analyzer_v5",
        description="Single-query analysis with free-form assessment between user_intent and edit_action.",
    ),
    "v6": AnalyzerPromptVersion(
        name="v6",
        flow="two_query",
        task_spec_template="analyzer_v6_task_spec",
        compare_template="analyzer_v6_compare",
        description="First two-query (hard-attention) analyzer. Q1=user msgs only → task spec.",
    ),
    "v7": AnalyzerPromptVersion(
        name="v7",
        flow="two_query",
        task_spec_template="analyzer_v7_task_spec",
        compare_template="analyzer_v7_compare",
        description="v6 refined; tighter task spec extraction.",
    ),
    "v8": AnalyzerPromptVersion(
        name="v8",
        flow="two_query",
        task_spec_template="analyzer_v8_task_spec",
        compare_template="analyzer_v8_compare",
        description="Current production two-query analyzer. <aligned>/<issues> structured output.",
    ),
    "v9": AnalyzerPromptVersion(
        name="v9",
        flow="two_query",
        task_spec_template="analyzer_v8_task_spec",  # reuses v8 task spec
        compare_template="analyzer_v9_compare",
        description="v8 spec + v9 compare adding <corrective_direction>.",
    ),
    "v11": AnalyzerPromptVersion(
        name="v11",
        flow="two_query",
        task_spec_template="analyzer_v8_task_spec",  # reuses v8 task spec
        compare_template="analyzer_v11_compare",
        description="v8 spec + v11 compare with mid-task reflection framing (generalized from tau2 v10). Used by Huang eval S2.",
    ),
    "v8_soft": AnalyzerPromptVersion(
        name="v8_soft",
        flow="two_query_soft",
        task_spec_template="analyzer_v8_soft_spec",
        compare_template="analyzer_v8_compare",
        description="Soft-attention ablation: Q1 sees full conversation (not just user msgs). Isolates the value of hard attention.",
    ),
    "v8_soft_cot": AnalyzerPromptVersion(
        name="v8_soft_cot",
        flow="two_query_soft",
        task_spec_template="analyzer_v8_soft_spec_cot",
        compare_template="analyzer_v8_compare",
        description="Soft-attention with explicit CoT decontamination in Q1.",
    ),
    "v8_single": AnalyzerPromptVersion(
        name="v8_single",
        flow="single_query_combined",
        single_template="analyzer_v8_single",
        description="Single-query ablation of v8: combines task spec + comparison in one prompt. Tests whether two-query separation matters.",
    ),
    "s1": AnalyzerPromptVersion(
        name="s1",
        flow="single_query_s1",
        single_template="s1_analysis",
        description="Simplified single-query header-format (TASK SPECIFICATION:/ALIGNED:/ISSUES:). Avoids Azure content-filter jailbreak triggers. Used by CollabLLM.",
    ),
}


DEFAULT_ANALYZER_VERSION = "v8"


def get_version(name: str) -> AnalyzerPromptVersion:
    """Look up an analyzer prompt version. Raises ``ValueError`` on unknown name."""
    if name not in ANALYZER_PROMPT_REGISTRY:
        available = ", ".join(sorted(ANALYZER_PROMPT_REGISTRY))
        raise ValueError(
            f"Unknown analyzer prompt version {name!r}. Available: {available}"
        )
    return ANALYZER_PROMPT_REGISTRY[name]


def list_versions() -> list[str]:
    """Return all registered analyzer prompt versions, sorted."""
    return sorted(ANALYZER_PROMPT_REGISTRY)
