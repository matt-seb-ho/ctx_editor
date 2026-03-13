"""Conversation analyzer — first-class analysis component.

Generates structured analysis of a multi-turn conversation, focusing on:
1. Understanding user intent (from user messages only)
2. Evaluating the assistant's approach (errors, assumptions, direction)
3. Deciding whether a pivot/backtrack is warranted

This is the central mechanism that S1 (append analysis) and S2 (context edit)
strategies both rely on. The analysis is designed as an independent review —
framed as if a third party is analyzing a conversation, to avoid biasing the
model toward or against the assistant's prior outputs.

Key design: when generating A_i for turn i, the input does NOT contain
previous analyses A_j (j < i). The analyzer always sees the raw conversation.
"""

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..core.trace import ConversationTrace
    from ..memory.base import MemoryModule
    from ..models.base import ModelClient


ANALYSIS_PROMPT = """\
You are an independent reviewer analyzing a conversation between a user and an AI assistant.

<conversation>
{conversation}
</conversation>

{memory_section}

Often in multi-turn conversations, an AI agent makes assumptions early on to start \
tackling an underspecified question, but then over-commits to those initial ideas even \
as later user messages suggest going another direction. The agent gets distracted by its \
prior outputs and is unlikely to backtrack on an incorrect partial solution.

Your job is to critically analyze this conversation, looking specifically for this \
behavior and determining whether the user's messages suggest that a change of direction \
could be useful.

Provide your analysis in this exact format:

<user_intent>
Collate ONLY information from the user's messages. Include:
- The user's goal/question
- All requirements, constraints, and specifications the user has provided
- Any examples, clarifications, or corrections from the user

Do NOT include the assistant's interpretations, assumptions, or invented details.
If the user didn't specify something, leave it unspecified — do not fill it in from \
the assistant's choices.
If the user provided concrete examples, include them verbatim.
</user_intent>

<approach_evaluation>
Critically evaluate the assistant's current approach:

1. ERRORS: Specific mistakes in the assistant's solution. Check whether the output \
format/structure matches what the user asked for.

2. UNGROUNDED ASSUMPTIONS: Assumptions the assistant introduced that the user never \
stated. Only flag these if they are likely causing incorrect behavior.

3. CORRECTIVE DIRECTION: Based on errors found and the user's examples/constraints, \
state specifically what the assistant should do differently. If the user provided \
examples, use them to determine the correct interpretation.

If the assistant's approach is broadly correct with minor issues, say so. If it has \
fundamental problems, say so clearly. Do not flag ambiguity unless it's causing errors.
</approach_evaluation>

<pivot_decision>
Does the assistant need to fundamentally change its approach?
Answer "yes" if the assistant is on a wrong path (building on incorrect assumptions, \
ignoring user corrections, repeating similar wrong outputs).
Answer "no" if the approach is reasonable and making progress, even if imperfect.
</pivot_decision>"""

MEMORY_SECTION_TEMPLATE = """\
<cheatsheet>
Use this cheatsheet to guide your analysis — it contains lessons learned from similar tasks:
{memory_content}
</cheatsheet>
"""


@dataclass
class AnalysisResult:
    """Structured result from conversation analysis."""

    user_intent: str
    approach_evaluation: str
    pivot_needed: bool
    raw_output: str

    @property
    def has_structured_output(self) -> bool:
        """Whether the analysis produced structured XML output."""
        return bool(self.user_intent) and bool(self.approach_evaluation)


class ConversationAnalyzer:
    """Generates structured analysis of multi-turn conversations.

    The analyzer is framed as an independent third-party review to avoid
    biasing the model. It produces three components:
    - User intent (what the user actually asked for)
    - Approach evaluation (what's wrong with the assistant's approach)
    - Pivot decision (whether a fundamental direction change is needed)
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        timeout: int = 60,
        max_tokens: Optional[int] = None,
        reasoning_effort: Optional[str] = None,
    ):
        self.model = model
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.reasoning_effort = reasoning_effort

    @staticmethod
    def _parse_output(text: str) -> AnalysisResult:
        """Parse structured XML output from the analyzer."""
        user_match = re.search(r"<user_intent>(.*?)</user_intent>", text, re.DOTALL)
        eval_match = re.search(
            r"<approach_evaluation>(.*?)</approach_evaluation>", text, re.DOTALL
        )
        pivot_match = re.search(
            r"<pivot_decision>(.*?)</pivot_decision>", text, re.DOTALL
        )

        user_intent = user_match.group(1).strip() if user_match else ""
        approach_eval = eval_match.group(1).strip() if eval_match else ""
        pivot_str = pivot_match.group(1).strip().lower() if pivot_match else "no"
        pivot_needed = pivot_str.startswith("yes")

        return AnalysisResult(
            user_intent=user_intent,
            approach_evaluation=approach_eval,
            pivot_needed=pivot_needed,
            raw_output=text,
        )

    @staticmethod
    def _strip_edit_notes(text: str) -> str:
        """Strip <context_edit_notes> blocks from conversation text.

        After a context reset, the system message contains edit notes that
        (a) are not part of the raw conversation and (b) trigger Azure's
        jailbreak content filter due to nested instruction patterns.
        """
        return re.sub(
            r"\s*<context_edit_notes>.*?</context_edit_notes>",
            "",
            text,
            flags=re.DOTALL,
        )

    def _build_prompt(
        self,
        trace: "ConversationTrace",
        memory: Optional["MemoryModule"] = None,
    ) -> str:
        """Build the analysis prompt from the conversation trace.

        Important: this uses the raw conversation WITHOUT previous analyses
        or edit notes, so the analyzer always sees the original exchange.
        """
        conversation_str = trace.get_conversation_string(skip_system=False)
        # Remove any <context_edit_notes> left from prior resets to avoid
        # content filter triggers and keep the analyzer's input clean.
        conversation_str = self._strip_edit_notes(conversation_str)

        memory_section = ""
        if memory and memory.content:
            memory_section = MEMORY_SECTION_TEMPLATE.format(
                memory_content=memory.content
            )

        return ANALYSIS_PROMPT.format(
            conversation=conversation_str,
            memory_section=memory_section,
        )

    async def analyze(
        self,
        trace: "ConversationTrace",
        model_client: "ModelClient",
        memory: Optional["MemoryModule"] = None,
    ) -> AnalysisResult:
        """Analyze the current conversation state.

        Args:
            trace: Conversation trace (not mutated).
            model_client: Model client for generation.
            memory: Optional memory module for guidance.

        Returns:
            Structured analysis result.
        """
        prompt = self._build_prompt(trace, memory)

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
        return self._parse_output(response.content)
