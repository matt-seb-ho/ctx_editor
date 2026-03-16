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

    v6 (default): Two-query architecture for hard attention separation.
      Query 1 — only sees user messages, produces clean task spec.
      Query 2 — compares task spec against full conversation.
      The edit decision is implicit: substantive content in <issues> = edit needed.

    Older versions (v4, v5) use a single query and are supported for
    backward compatibility.
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        timeout: int = 60,
        max_tokens: Optional[int] = None,
        reasoning_effort: Optional[str] = None,
        prompt_version: str = "v8",
    ):
        self.model = model
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.reasoning_effort = reasoning_effort
        self.prompt_version = prompt_version

        if prompt_version in ("v6", "v7", "v8"):
            self._task_spec_template = _load_prompt(f"analyzer_{prompt_version}_task_spec")
            self._compare_template = _load_prompt(f"analyzer_{prompt_version}_compare")
        else:
            # Single-query prompt (v4, v5)
            self._prompt_template = _load_prompt(f"analyzer_{prompt_version}")

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

        response = await model_client.generate(**generate_kwargs)
        return response.content

    # --- v6: two-query flow ---

    async def _analyze_v6(
        self,
        trace: "ConversationTrace",
        model_client: "ModelClient",
        memory: Optional["MemoryModule"] = None,
    ) -> AnalysisResult:
        """Two-query analysis with hard attention separation.

        Query 1: User messages only → task spec (no assistant contamination)
        Query 2: Task spec + full conversation → critical comparison
        """
        # Include compacted conversation content (from prior S2 resets) so the
        # task spec query sees the previously-extracted task spec + new user messages.
        user_messages_str = trace.get_user_messages_string(include_compacted=True)
        conversation_str = trace.get_conversation_string(skip_system=False)
        conversation_str = self._strip_edit_notes(conversation_str)

        # Query 1: Build task spec from user messages only
        spec_prompt = self._task_spec_template.format_map(
            defaultdict(str, {"user_messages": user_messages_str})
        )
        spec_output = await self._generate(spec_prompt, model_client)

        task_spec = self._extract_tag(spec_output, "task_spec")
        if not task_spec:
            logger.warning(
                "Task spec extraction: <task_spec> tag not found, using raw output. "
                f"Output preview: {spec_output[:150]!r}"
            )
            task_spec = spec_output.strip()

        # Query 2: Compare task spec against full conversation
        memory_section = ""
        if memory and memory.content:
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
    ) -> AnalysisResult:
        """Analyze the current conversation state.

        Dispatches to v6 (two-query) or single-query based on prompt_version.
        """
        if self.prompt_version in ("v6", "v7", "v8"):
            return await self._analyze_v6(trace, model_client, memory)
        return await self._analyze_single(trace, model_client, memory)

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
