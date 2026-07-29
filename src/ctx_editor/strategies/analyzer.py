"""Conversation analyzer — first-class analysis component.

Generates structured analysis of a multi-turn conversation via two steps:
1. Task spec construction (from user messages only — hard attention)
2. Critical comparison of the task spec against the assistant's actual work

This is the central mechanism that S1 (append analysis) and S2 (context edit)
strategies both rely on. The analysis is designed as an independent review —
framed as if a third party is analyzing a conversation, to avoid biasing the
model toward or against the assistant's prior outputs.

Key design: when generating A_i for turn i, the input does NOT contain
previous analyses A_j (j < i). The analyzer always sees the raw conversation.

Prompts are loaded from strategies/prompts/ for easy versioning.
"""

import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from ..utils.logging import get_logger
from .analyzer_prompts import (
    ANALYZER_PROMPT_REGISTRY,
    DEFAULT_ANALYZER_VERSION,
    AnalyzerPromptVersion,
    get_version,
)

if TYPE_CHECKING:
    from ..core.trace import ConversationTrace
    from ..memory.base import MemoryModule
    from ..models.base import ModelClient

logger = get_logger("analyzer")

_PROMPT_DIR = Path(__file__).parent / "prompts"

MEMORY_SECTION_TEMPLATE = """\
<cheatsheet>
The following cheatsheet contains strategies, common pitfalls, and lessons learned from \
previous similar tasks. Use your discretion to decide which points are relevant — not all \
will apply.

{memory_content}
</cheatsheet>
"""

# Compliance rules appended after the memory section to reinforce key constraints.
# These address observed anti-patterns where the analyzer contradicts its own cheatsheet.
COMPLIANCE_RULES = """\
<compliance_rules>
Critical rules for your analysis output — violations of these will degrade downstream quality:
1. NEVER suggest or recommend that the assistant ask the user for clarification, confirmation, \
or disambiguation. The user cannot be asked questions in this environment. If there are \
ambiguities, apply deterministic defaults and document them as "assumed."
2. The user_intent/task_spec must contain ONLY requirements explicitly stated by the user. \
Do not add columns, fields, or deliverables that the user did not request. A filtering \
condition (e.g., "with 2+ treatments") is NOT a projection requirement.
3. In <issues>, describe WHAT is wrong and the minimal fix. Do not prescribe specific \
implementation patterns (e.g., specific SQL forms) — let the assistant choose HOW to fix it.
</compliance_rules>
"""

# Trivial issues content that means "no edit needed"
_NO_ISSUES_PATTERNS = re.compile(
    r"^(none\.?|no issues\.?|nothing\.?|n/a\.?|no problems\.?|no concerns\.?)$",
    re.IGNORECASE,
)


def _load_prompt(name: str) -> str:
    """Load a prompt template from file."""
    path = _PROMPT_DIR / f"{name}.txt"
    return path.read_text()


def _has_substantive_issues(issues_text: str) -> bool:
    """Determine if the issues section contains real problems vs. 'None'."""
    stripped = issues_text.strip()
    if not stripped:
        return False
    return not _NO_ISSUES_PATTERNS.match(stripped)


@dataclass
class AnalysisResult:
    """Structured result from conversation analysis."""

    user_intent: str  # Clean task spec from user messages only
    aligned: str  # What the assistant got right
    issues: str  # What contradicts the task spec
    raw_output: str  # Full output from comparison query
    corrective_direction: str = ""  # v9+: what to do differently (optional)

    @property
    def needs_edit(self) -> bool:
        """Whether the issues section contains substantive problems."""
        return _has_substantive_issues(self.issues)

    @property
    def context_assessment(self) -> str:
        """Combined assessment (aligned + issues) for downstream consumers."""
        parts = []
        if self.aligned:
            parts.append(f"What looks right so far:\n{self.aligned}")
        if self.issues:
            parts.append(f"What needs to change:\n{self.issues}")
        return "\n\n".join(parts)

    # --- backward compatibility ---
    @property
    def approach_evaluation(self) -> str:
        """Alias for context_assessment (used by S1 append strategy)."""
        return self.context_assessment

    @property
    def pivot_needed(self) -> bool:
        """Alias for needs_edit."""
        return self.needs_edit

    @property
    def edit_action(self) -> str:
        """Derive action level from issues content."""
        return "major" if self.needs_edit else "none"

    @property
    def has_structured_output(self) -> bool:
        """Whether the analysis produced structured output."""
        return bool(self.user_intent)


class ConversationAnalyzer:
    """Generates structured analysis of multi-turn conversations.

    The set of supported prompt versions and the flow each uses lives in
    :mod:`ctx_editor.strategies.analyzer_prompts`. To add a new version
    (e.g. ``v12``), add an entry to ``ANALYZER_PROMPT_REGISTRY`` there — no
    changes to this class are needed unless you also introduce a new *flow*.

    Flows currently supported (see ``AnalyzerFlow``):

    - ``two_query`` (v6/v7/v8/v9/v11): hard-attention; Q1 sees user msgs only.
    - ``two_query_soft`` (v8_soft, v8_soft_cot): Q1 sees full conversation.
    - ``single_query_combined`` (v8_single): one prompt does spec + comparison.
    - ``single_query_s1`` (s1): simplified header-format, content-filter safe.
    - ``single_query_legacy`` (v4, v5): original single-prompt format.
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        timeout: int = 300,
        max_tokens: Optional[int] = None,
        reasoning_effort: Optional[str] = None,
        prompt_version: str = DEFAULT_ANALYZER_VERSION,
    ):
        self.model = model
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.reasoning_effort = reasoning_effort
        self.prompt_version = prompt_version

        # Look up the version in the registry; raises if unknown.
        self._version_spec: AnalyzerPromptVersion = get_version(prompt_version)

        # Load templates based on the flow. Each flow uses a different subset
        # of fields on the version spec; the spec encodes which are required.
        flow = self._version_spec.flow
        if flow in ("two_query", "two_query_soft"):
            self._task_spec_template = _load_prompt(self._version_spec.task_spec_template)
            self._compare_template = _load_prompt(self._version_spec.compare_template)
        elif flow == "single_query_combined":
            self._single_combined_template = _load_prompt(self._version_spec.single_template)
        elif flow in ("single_query_s1", "single_query_legacy"):
            self._prompt_template = _load_prompt(self._version_spec.single_template)

    async def _generate(self, prompt: str, model_client: "ModelClient") -> str:
        """Run a single LLM generation."""
        generate_kwargs: dict = {
            "messages": [{"role": "user", "content": prompt}],
            "model": self.model,
            "temperature": 0.0,
            "timeout": self.timeout,
        }
        if self.max_tokens:
            generate_kwargs["max_tokens"] = self.max_tokens
        if self.reasoning_effort:
            generate_kwargs["reasoning_effort"] = self.reasoning_effort

        from ..utils.call_meter import call_tag

        with call_tag("strategy"):
            response = await model_client.generate(**generate_kwargs)
        return response.content

    # --- v6: two-query flow ---

    async def _analyze_v6(
        self,
        trace: "ConversationTrace",
        model_client: "ModelClient",
        memory: Optional["MemoryModule"] = None,
        spec_only: bool = False,
        memory_target_query: str = "compare",
        enforce_compliance: bool = False,
    ) -> AnalysisResult:
        """Two-query analysis with hard attention separation.

        Query 1: User messages only → task spec (no assistant contamination)
        Query 2: Task spec + full conversation → critical comparison

        If spec_only=True, only runs Query 1 and returns empty aligned/issues.

        memory_target_query controls where memory is injected:
          "compare" (default) — Query 2 only (original behavior)
          "spec" — Query 1 only
          "both" — both queries

        enforce_compliance: if True, append compliance rules after memory section
          in Query 2 to prevent clarification-seeking and over-specification.
        """
        # Include ALL user messages across resets (deduplicated) so the task spec
        # query always builds from the complete set of user information.
        user_messages_str = trace.get_user_messages_string(all_unique=True)
        system_message_str = trace.system_message.content if trace.system_message else ""
        conversation_str = trace.get_conversation_string(skip_system=False)
        conversation_str = self._strip_edit_notes(conversation_str)

        # Memory for Query 1 (task spec)
        spec_memory_section = ""
        if memory and memory.content and memory_target_query in ("spec", "both"):
            spec_memory_section = MEMORY_SECTION_TEMPLATE.format(
                memory_content=memory.content
            )

        # Query 1: Build task spec from user messages + system message context
        spec_prompt = self._task_spec_template.format_map(
            defaultdict(str, {
                "user_messages": user_messages_str,
                "system_message": system_message_str,
                "memory_section": spec_memory_section,
            })
        )
        spec_output = await self._generate(spec_prompt, model_client)

        task_spec = self._extract_tag(spec_output, "task_spec")
        if not task_spec:
            logger.warning(
                "Task spec extraction: <task_spec> tag not found, using raw output. "
                f"Output preview: {spec_output[:150]!r}"
            )
            task_spec = spec_output.strip()

        # spec_only: skip Query 2, return task spec with empty comparison
        if spec_only:
            return AnalysisResult(
                user_intent=task_spec,
                aligned="",
                issues="",
                raw_output=f"--- TASK SPEC (spec_only) ---\n{spec_output}",
            )

        # Memory for Query 2 (comparison)
        memory_section = ""
        if memory and memory.content and memory_target_query in ("compare", "both"):
            memory_section = MEMORY_SECTION_TEMPLATE.format(memory_content=memory.content)
        if enforce_compliance:
            memory_section += "\n" + COMPLIANCE_RULES

        compare_prompt = self._compare_template.format_map(
            defaultdict(
                str,
                {
                    "task_spec": task_spec,
                    "conversation": conversation_str,
                    "memory_section": memory_section,
                },
            )
        )
        compare_output = await self._generate(compare_prompt, model_client)

        aligned = self._extract_tag(compare_output, "aligned")
        issues = self._extract_tag(compare_output, "issues")
        corrective_direction = self._extract_tag(compare_output, "corrective_direction")

        # Fallback: if the model didn't use XML tags, try section-header parsing
        if not aligned and not issues:
            logger.warning(
                "Comparison extraction: <aligned>/<issues> tags not found, "
                f"trying section-header fallback. Output preview: {compare_output[:150]!r}"
            )
            aligned, issues = self._parse_numbered_comparison(compare_output)
            if not aligned and not issues:
                logger.error(
                    "Comparison extraction: both XML and section-header parsing failed. "
                    "Analysis will return empty aligned/issues. "
                    f"Full output: {compare_output[:300]!r}"
                )

        return AnalysisResult(
            user_intent=task_spec,
            aligned=aligned,
            issues=issues,
            raw_output=f"--- TASK SPEC ---\n{spec_output}\n\n--- COMPARISON ---\n{compare_output}",
            corrective_direction=corrective_direction,
        )

    # --- v8_soft: two-query, but Query 1 sees full conversation ---

    async def _analyze_v8_soft(
        self,
        trace: "ConversationTrace",
        model_client: "ModelClient",
        memory: Optional["MemoryModule"] = None,
        spec_only: bool = False,
        memory_target_query: str = "compare",
    ) -> AnalysisResult:
        """Two-query analysis WITHOUT hard attention separation.

        Same as _analyze_v6 except Query 1 sees the full conversation
        (user + assistant messages) instead of user messages only.
        Isolates the effect of hiding assistant messages from the spec query.

        Also used by v8_soft_cot (CoT decontamination variant).
        """
        system_message_str = trace.system_message.content if trace.system_message else ""
        conversation_str = trace.get_conversation_string(skip_system=False)
        conversation_str = self._strip_edit_notes(conversation_str)

        # Memory for Query 1 (task spec) — enabled for spec_curation memory experiments
        spec_memory_section = ""
        if memory and memory.content and memory_target_query in ("spec", "both"):
            spec_memory_section = MEMORY_SECTION_TEMPLATE.format(
                memory_content=memory.content
            )

        # Query 1: Build task spec from FULL conversation (soft attention)
        spec_prompt = self._task_spec_template.format_map(
            defaultdict(str, {
                "conversation": conversation_str,
                "system_message": system_message_str,
                "memory_section": spec_memory_section,
            })
        )
        spec_output = await self._generate(spec_prompt, model_client)

        task_spec = self._extract_tag(spec_output, "task_spec")
        if not task_spec:
            logger.warning(
                "v8_soft task spec extraction: <task_spec> tag not found, using raw output. "
                f"Output preview: {spec_output[:150]!r}"
            )
            task_spec = spec_output.strip()

        # spec_only: skip Query 2, return task spec with empty comparison
        if spec_only:
            label = "soft_cot" if self.prompt_version == "v8_soft_cot" else "soft"
            return AnalysisResult(
                user_intent=task_spec,
                aligned="",
                issues="",
                raw_output=f"--- TASK SPEC ({label}, spec_only) ---\n{spec_output}",
            )

        # Query 2: Compare task spec against full conversation (same as v6/v8)
        memory_section = ""
        if memory and memory.content and memory_target_query in ("compare", "both"):
            memory_section = MEMORY_SECTION_TEMPLATE.format(memory_content=memory.content)

        compare_prompt = self._compare_template.format_map(
            defaultdict(
                str,
                {
                    "task_spec": task_spec,
                    "conversation": conversation_str,
                    "memory_section": memory_section,
                },
            )
        )
        compare_output = await self._generate(compare_prompt, model_client)

        aligned = self._extract_tag(compare_output, "aligned")
        issues = self._extract_tag(compare_output, "issues")

        if not aligned and not issues:
            logger.warning(
                "v8_soft comparison extraction: <aligned>/<issues> tags not found, "
                f"trying section-header fallback. Output preview: {compare_output[:150]!r}"
            )
            aligned, issues = self._parse_numbered_comparison(compare_output)

        label = "soft_cot" if self.prompt_version == "v8_soft_cot" else "soft"
        return AnalysisResult(
            user_intent=task_spec,
            aligned=aligned,
            issues=issues,
            raw_output=f"--- TASK SPEC ({label}) ---\n{spec_output}\n\n--- COMPARISON ---\n{compare_output}",
        )

    # --- v8_single: single-query ablation ---

    async def _analyze_v8_single(
        self,
        trace: "ConversationTrace",
        model_client: "ModelClient",
        memory: Optional["MemoryModule"] = None,
    ) -> AnalysisResult:
        """Single-query analysis ablation for v8.

        Combines task spec construction and comparison into one prompt.
        The model sees the full conversation (including assistant messages)
        when building the task spec — no hard attention separation.
        """
        system_message_str = trace.system_message.content if trace.system_message else ""
        conversation_str = trace.get_conversation_string(skip_system=False)
        conversation_str = self._strip_edit_notes(conversation_str)

        memory_section = ""
        if memory and memory.content:
            memory_section = MEMORY_SECTION_TEMPLATE.format(memory_content=memory.content)

        prompt = self._single_combined_template.format_map(
            defaultdict(
                str,
                {
                    "system_message": system_message_str,
                    "conversation": conversation_str,
                    "memory_section": memory_section,
                },
            )
        )
        output = await self._generate(prompt, model_client)

        task_spec = self._extract_tag(output, "task_spec")
        aligned = self._extract_tag(output, "aligned")
        issues = self._extract_tag(output, "issues")

        if not task_spec:
            logger.warning(
                "v8_single: <task_spec> tag not found. "
                f"Output preview: {output[:150]!r}"
            )

        # Fallback for aligned/issues
        if not aligned and not issues:
            logger.warning(
                "v8_single: <aligned>/<issues> tags not found, "
                f"trying section-header fallback. Output preview: {output[:150]!r}"
            )
            aligned, issues = self._parse_numbered_comparison(output)

        return AnalysisResult(
            user_intent=task_spec,
            aligned=aligned,
            issues=issues,
            raw_output=f"--- SINGLE QUERY ---\n{output}",
        )

    # --- s1: simplified single-query (no XML, avoids content filter) ---

    async def _analyze_s1(
        self,
        trace: "ConversationTrace",
        model_client: "ModelClient",
        memory: Optional["MemoryModule"] = None,
    ) -> AnalysisResult:
        """Simplified single-query analysis without XML tags.

        Uses header-based format (TASK SPECIFICATION: / ALIGNED: / ISSUES:)
        to avoid Azure content filter jailbreak detection.
        """
        conversation_str = trace.get_conversation_string(skip_system=False)
        conversation_str = self._strip_edit_notes(conversation_str)

        memory_section = ""
        if memory and memory.content:
            memory_section = MEMORY_SECTION_TEMPLATE.format(memory_content=memory.content)

        prompt = self._prompt_template.format_map(
            defaultdict(
                str,
                {
                    "conversation": conversation_str,
                    "memory_section": memory_section,
                },
            )
        )
        output = await self._generate(prompt, model_client)

        # Parse header-based format
        task_spec = ""
        aligned = ""
        issues = ""

        # Extract TASK SPECIFICATION section
        spec_match = re.search(
            r"TASK SPECIFICATION:\s*\n(.*?)(?=\nALIGNED:|\Z)", output, re.DOTALL
        )
        if spec_match:
            task_spec = spec_match.group(1).strip()

        # Extract ALIGNED section
        aligned_match = re.search(
            r"ALIGNED:\s*\n(.*?)(?=\nISSUES:|\Z)", output, re.DOTALL
        )
        if aligned_match:
            aligned = aligned_match.group(1).strip()

        # Extract ISSUES section
        issues_match = re.search(
            r"ISSUES:\s*\n(.*?)$", output, re.DOTALL
        )
        if issues_match:
            issues = issues_match.group(1).strip()

        return AnalysisResult(
            user_intent=task_spec,
            aligned=aligned,
            issues=issues,
            raw_output=f"--- S1 ANALYSIS ---\n{output}",
        )

    # --- single-query flow (v4, v5) ---

    async def _analyze_single(
        self,
        trace: "ConversationTrace",
        model_client: "ModelClient",
        memory: Optional["MemoryModule"] = None,
    ) -> AnalysisResult:
        """Single-query analysis (v4, v5 backward compat)."""
        conversation_str = trace.get_conversation_string(skip_system=False)
        conversation_str = self._strip_edit_notes(conversation_str)
        user_messages_str = trace.get_user_messages_string()

        memory_section = ""
        if memory and memory.content:
            memory_section = MEMORY_SECTION_TEMPLATE.format(memory_content=memory.content)

        prompt = self._prompt_template.format_map(
            defaultdict(
                str,
                {
                    "conversation": conversation_str,
                    "user_messages": user_messages_str,
                    "memory_section": memory_section,
                },
            )
        )
        output = await self._generate(prompt, model_client)
        return self._parse_single_output(output)

    # --- public API ---

    async def analyze(
        self,
        trace: "ConversationTrace",
        model_client: "ModelClient",
        memory: Optional["MemoryModule"] = None,
        spec_only: bool = False,
        memory_target_query: str = "compare",
        enforce_compliance: bool = False,
        *,
        cache: Optional["AnalysisCache"] = None,  # noqa: F821 - quoted forward-ref
        cache_provenance: Optional[dict] = None,
    ) -> AnalysisResult:
        """Analyze the current conversation state.

        Dispatches to v6 (two-query) or single-query based on prompt_version.
        If spec_only=True, only runs Query 1 (task spec) and skips Query 2.
        memory_target_query: "compare" (default), "spec", or "both".
        enforce_compliance: if True, append compliance rules to Query 2 prompt.

        If ``cache`` is provided, look up by content hash before running and
        store the result for re-use across strategies that share the same
        (prefix, analyzer model, prompt version, knobs) tuple. Use this for
        last-turn replay where Augment / Reset / Gated-Reset / Rewrite all
        share the same prefix and would otherwise issue redundant analyzer
        queries.
        """
        cache_key = None
        if cache is not None:
            from .analysis_cache import AnalysisCache  # local import to avoid cycles
            trace_hash = AnalysisCache._hash_trace(trace)
            cache_key = AnalysisCache.make_key(
                trace_hash=trace_hash,
                analyzer_model=self.model,
                prompt_version=self.prompt_version,
                spec_only=spec_only,
                memory_target_query=memory_target_query,
                enforce_compliance=enforce_compliance,
                memory_present=memory is not None,
            )
            hit = cache.lookup(cache_key)
            if hit is not None:
                return hit

        flow = self._version_spec.flow
        if flow == "two_query":
            result = await self._analyze_v6(
                trace, model_client, memory, spec_only=spec_only,
                memory_target_query=memory_target_query,
                enforce_compliance=enforce_compliance,
            )
        elif flow == "two_query_soft":
            result = await self._analyze_v8_soft(
                trace, model_client, memory, spec_only=spec_only,
                memory_target_query=memory_target_query,
            )
        elif flow == "single_query_combined":
            result = await self._analyze_v8_single(trace, model_client, memory)
        elif flow == "single_query_s1":
            result = await self._analyze_s1(trace, model_client, memory)
        else:
            result = await self._analyze_single(trace, model_client, memory)

        if cache is not None and cache_key is not None:
            try:
                cache.store(
                    cache_key,
                    result,
                    key_inputs={
                        "analyzer_model": self.model,
                        "prompt_version": self.prompt_version,
                        "spec_only": bool(spec_only),
                        "memory_target_query": memory_target_query,
                        "enforce_compliance": bool(enforce_compliance),
                        "memory_present": memory is not None,
                    },
                    provenance=cache_provenance or {},
                )
            except Exception:
                # Cache failures must never break the experiment.
                pass

        return result

    # --- parsing helpers ---

    @staticmethod
    def _extract_tag(text: str, tag: str) -> str:
        """Extract content from an XML tag."""
        match = re.search(rf"<{tag}>(.*?)</{tag}>", text, re.DOTALL)
        return match.group(1).strip() if match else ""

    @staticmethod
    def _parse_single_output(text: str) -> AnalysisResult:
        """Parse output from single-query prompts (v4, v5, legacy)."""
        user_match = re.search(r"<user_intent>(.*?)</user_intent>", text, re.DOTALL)
        action_match = re.search(r"<edit_action>(.*?)</edit_action>", text, re.DOTALL)

        # Try tagged assessment sections
        assess_match = re.search(r"<context_assessment>(.*?)</context_assessment>", text, re.DOTALL)
        if not assess_match:
            assess_match = re.search(
                r"<approach_evaluation>(.*?)</approach_evaluation>", text, re.DOTALL
            )

        # v5: free-form assessment between </user_intent> and <edit_action>
        if not assess_match and user_match and action_match:
            between = text[user_match.end() : action_match.start()].strip()
            if between:
                assess_match = type("Match", (), {"group": lambda self, n: between})()

        # Parse edit action for legacy
        if action_match:
            action_str = action_match.group(1).strip().lower()
            for level in ("major", "minor", "none"):
                if level in action_str:
                    action_str = level
                    break
            else:
                action_str = "none"
        else:
            pivot_match = re.search(r"<pivot_decision>(.*?)</pivot_decision>", text, re.DOTALL)
            if pivot_match:
                pivot_str = pivot_match.group(1).strip().lower()
                action_str = "major" if pivot_str.startswith("yes") else "none"
            else:
                action_str = "none"

        user_intent = user_match.group(1).strip() if user_match else ""
        assessment = assess_match.group(1).strip() if assess_match else ""

        # Map single-query output to AnalysisResult
        # For single-query, we put the full assessment in issues if edit is needed,
        # otherwise in aligned
        if action_str != "none":
            return AnalysisResult(
                user_intent=user_intent, aligned="", issues=assessment, raw_output=text
            )
        return AnalysisResult(
            user_intent=user_intent, aligned=assessment, issues="", raw_output=text
        )

    @staticmethod
    def _parse_numbered_comparison(text: str) -> tuple[str, str]:
        """Parse comparison output in numbered-question format.

        Handles output like:
            1. ALIGNED: ...
            2. ISSUES: ...

        Also handles variations like "1. ALIGNED -", "1) ALIGNED:", "ALIGNED:", etc.
        Returns (aligned, issues) tuple.
        """
        aligned = ""
        issues = ""

        # Try to find ALIGNED and ISSUES sections by header
        aligned_match = re.search(
            r"(?:1[\.\)]\s*)?ALIGNED[:\s\-]+(.+?)(?=(?:2[\.\)]\s*)?ISSUES[:\s\-]|\Z)",
            text,
            re.DOTALL | re.IGNORECASE,
        )
        issues_match = re.search(
            r"(?:2[\.\)]\s*)?ISSUES[:\s\-]+(.+?)$",
            text,
            re.DOTALL | re.IGNORECASE,
        )

        if aligned_match:
            aligned = aligned_match.group(1).strip()
        if issues_match:
            issues = issues_match.group(1).strip()

        return aligned, issues

    @staticmethod
    def _strip_edit_notes(text: str) -> str:
        """Strip <context_edit_notes> blocks from conversation text."""
        return re.sub(
            r"\s*<context_edit_notes>.*?</context_edit_notes>",
            "",
            text,
            flags=re.DOTALL,
        )
