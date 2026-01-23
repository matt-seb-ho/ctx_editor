"""System agent for verification and answer extraction."""

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional

from ..core.types import VerificationResult
from ..utils.helpers import load_prompt

if TYPE_CHECKING:
    from ..core.trace import ConversationTrace
    from ..models.base import ModelClient


DEFAULT_VERIFICATION_PROMPT = """Analyze the assistant's last response and categorize it.

<initial_query>
[[INITIAL_SHARD]]
</initial_query>

<additional_requirements>
[[SHARDS]]
</additional_requirements>

<last_turn>
[[CONVERSATION_SO_FAR]]
</last_turn>

The answer should be: [[ANSWER_DESCRIPTION]]

Categorize the assistant's response as one of:
- "answer_attempt": The assistant is providing what they believe to be the final answer
- "clarification": The assistant is asking for clarification or more information
- "partial_answer": The assistant is providing partial progress toward the answer
- "other": None of the above

Respond with a JSON object:
{
    "response_type": "answer_attempt" | "clarification" | "partial_answer" | "other",
    "reasoning": "Brief explanation"
}"""


DEFAULT_EXTRACTION_PROMPT_GEN = """Extract the final answer from the assistant's response.

<assistant_response>
[[ASSISTANT_RESPONSE]]
</assistant_response>

The answer should be: [[ANSWER_DESCRIPTION]]

Respond with a JSON object:
{
    "answer": "The extracted answer"
}"""


DEFAULT_EXTRACTION_PROMPT_PREFIX_SUFFIX = """Extract the final answer from the assistant's response by identifying the prefix and suffix that bound it.

<assistant_response>
[[ASSISTANT_RESPONSE]]
</assistant_response>

The answer should be: [[ANSWER_DESCRIPTION]]

Respond with a JSON object:
{
    "answer": "prefix of the answer [...] suffix of the answer"
}

Use [...] to indicate content in between that should be included."""


@dataclass
class ExtractionResult:
    """Result of answer extraction."""
    answer: str
    cost_usd: float = 0.0


class SystemAgent:
    """Agent for verifying assistant responses and extracting answers.

    Adapted from the LIC system_agent.py to work with async model client.
    """

    def __init__(
        self,
        task: Any,
        system_model: str = "gpt-4o-mini",
        sample: Optional[dict[str, Any]] = None,
        verification_prompt_file: Optional[str] = None,
        extraction_prompt_file: Optional[str] = None,
    ):
        """Initialize the system agent.

        Args:
            task: The task instance.
            system_model: Model to use for verification/extraction.
            sample: The sample data.
            verification_prompt_file: Optional custom verification prompt.
            extraction_prompt_file: Optional custom extraction prompt.
        """
        self.task = task
        self.system_model = system_model
        self.sample = sample
        self.task_name = task.get_task_name() if hasattr(task, "get_task_name") else str(task)

        # Get task-specific settings
        self.answer_description = (
            task.get_answer_description()
            if hasattr(task, "get_answer_description")
            else "the final answer"
        )
        self.answer_extraction_strategy = getattr(
            task, "answer_extraction_strategy", "gen"
        )

        self.max_extraction_attempts = 3

        # Load prompts
        if verification_prompt_file:
            self.verification_prompt = load_prompt(verification_prompt_file)
        else:
            self.verification_prompt = DEFAULT_VERIFICATION_PROMPT

        if extraction_prompt_file:
            self.extraction_prompt = load_prompt(extraction_prompt_file)
        elif self.answer_extraction_strategy == "prefix_suffix":
            self.extraction_prompt = DEFAULT_EXTRACTION_PROMPT_PREFIX_SUFFIX
        else:
            self.extraction_prompt = DEFAULT_EXTRACTION_PROMPT_GEN

    async def verify_response(
        self,
        trace: "ConversationTrace",
        model_client: "ModelClient",
    ) -> VerificationResult:
        """Verify the assistant's last response and categorize it.

        Args:
            trace: Current conversation trace.
            model_client: Model client for verification.

        Returns:
            VerificationResult with the response type.
        """
        # Some tasks always treat responses as answer attempts
        if self.task_name in ["summary", "totto", "translation", "data2text"]:
            return VerificationResult(response_type="answer_attempt")

        if not self.sample:
            return VerificationResult(response_type="answer_attempt")

        # Build verification prompt
        initial_query = self.sample["shards"][0]["shard"]
        shards = self.sample["shards"][1:]
        last_turn_text = trace.get_conversation_string(only_last_turn=True)

        prompt = self.verification_prompt.replace(
            "[[CONVERSATION_SO_FAR]]", last_turn_text
        ).replace(
            "[[INITIAL_SHARD]]", initial_query
        ).replace(
            "[[SHARDS]]", json.dumps(shards)
        ).replace(
            "[[ANSWER_DESCRIPTION]]", self.answer_description
        )

        response = await model_client.generate_json(
            messages=[{"role": "user", "content": prompt}],
            model=self.system_model,
            temperature=0.0,
        )

        result = response.content
        return VerificationResult(
            response_type=result.get("response_type", "other"),
            cost_usd=response.total_usd,
            raw_response=result,
        )

    async def extract_answer(
        self,
        trace: "ConversationTrace",
        model_client: "ModelClient",
    ) -> ExtractionResult:
        """Extract the final answer from the assistant's response.

        Args:
            trace: Current conversation trace.
            model_client: Model client for extraction.

        Returns:
            ExtractionResult with the extracted answer.
        """
        # Get the last assistant response
        last_assistant = trace.last_assistant_message
        if not last_assistant:
            return ExtractionResult(answer="", cost_usd=0.0)

        assistant_response = last_assistant.content

        # Full response strategy - just return as-is
        if self.answer_extraction_strategy == "full_response":
            return ExtractionResult(answer=assistant_response, cost_usd=0.0)

        # Task-specific extraction
        if self.answer_extraction_strategy == "task_specific":
            if hasattr(self.task, "extract_answer"):
                answer = self.task.extract_answer(assistant_response)
                return ExtractionResult(answer=answer, cost_usd=0.0)

        # Model-based extraction
        last_turn_text = trace.get_conversation_string(only_last_turn=True)

        extracted_answer = None
        total_cost = 0.0

        for _ in range(self.max_extraction_attempts):
            prompt = self.extraction_prompt.replace(
                "[[ASSISTANT_RESPONSE]]", last_turn_text
            ).replace(
                "[[ANSWER_DESCRIPTION]]", self.answer_description
            )

            response = await model_client.generate_json(
                messages=[{"role": "user", "content": prompt}],
                model=self.system_model,
                temperature=0.0,
            )
            total_cost += response.total_usd

            result = response.content

            if self.answer_extraction_strategy == "gen":
                extracted_answer = result.get("answer", "")
            else:  # prefix_suffix
                extractor_response = result.get("answer", "")
                if "[...]" in extractor_response and extractor_response.count("[...]") == 1:
                    prefix, suffix = extractor_response.split("[...]")
                    prefix, suffix = prefix.strip(), suffix.strip()

                    start_idx = assistant_response.find(prefix)
                    end_idx = assistant_response.rfind(suffix)
                    if start_idx >= 0 and end_idx >= 0:
                        extracted_answer = assistant_response[start_idx:(end_idx + len(suffix))]
                else:
                    extracted_answer = extractor_response

            # Verify extraction is actually from the response
            if extracted_answer and extracted_answer in assistant_response:
                break
            extracted_answer = None

        if extracted_answer is None:
            extracted_answer = ""

        return ExtractionResult(answer=extracted_answer, cost_usd=total_cost)
