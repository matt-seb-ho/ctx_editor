"""CollabLLM conversation simulator.

Follows CollabLLM's evaluation protocol:
- User simulator role-plays as human with access to full problem
- No per-turn verification/extraction (unlike LiC simulator)
- Evaluation happens after conversation ends via LLM judges
- Termination by user signal or max turns
- Option 2 rendering for assistant calls (consistent with our strategies)
"""

from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from .trace import ConversationTrace
from .types import EvaluationResult, Message, SimulationResult, SimulatorConfig, UsageStats

if TYPE_CHECKING:
    from ..agents.collabllm_user_agent import CollabLLMUserAgent
    from ..evaluation.collabllm_metrics import CollabLLMEvaluator
    from ..memory.base import MemoryModule
    from ..models.base import ModelClient
    from ..strategies.base import ContextStrategy

# Load CollabLLM system prompt
_PROMPTS_DIR = Path(__file__).parent.parent / "prompts" / "collabllm"
COLLABLLM_SYSTEM_PROMPT = (_PROMPTS_DIR / "system_prompt.txt").read_text()

# Reuse Option 2 wrapper from existing simulator
ASSISTANT_PROMPT_WRAPPER = """\
Here is the current conversation:

{conversation}

Please respond to the user. Do not include [user] or [assistant] tags in your response."""


class CollabLLMSimulator:
    """Orchestrates CollabLLM-style multi-turn conversations for evaluation.

    Key differences from ConversationSimulator:
    - No SystemAgent or per-turn verification
    - User agent can terminate via signal
    - Evaluation runs after conversation ends (LLM-judged)
    - Uses Option 2 rendering (consistent with our strategies)
    """

    def __init__(
        self,
        sample: dict[str, Any],
        user_agent: "CollabLLMUserAgent",
        model_client: "ModelClient",
        strategy: "ContextStrategy",
        evaluator: "CollabLLMEvaluator",
        memory: Optional["MemoryModule"] = None,
        config: Optional[SimulatorConfig] = None,
        trace: Optional[ConversationTrace] = None,
    ):
        self.sample = sample
        self.user_agent = user_agent
        self.model_client = model_client
        self.strategy = strategy
        self.evaluator = evaluator
        self.memory = memory
        self.config = config or SimulatorConfig()

        self.usage_stats = UsageStats()

        if trace is not None:
            self.trace = trace
        else:
            self.trace = ConversationTrace()
            self.trace.add_system_message(COLLABLLM_SYSTEM_PROMPT)

    @staticmethod
    def _render_for_assistant(context_messages: list[Message]) -> list[dict[str, str]]:
        """Render context messages into Option 2 format for the API call.

        Same as ConversationSimulator._render_for_assistant — renders all
        conversation as a tagged string inside a single user message.
        """
        system_content = None
        conversation_parts = []

        for msg in context_messages:
            if msg.role == "system":
                system_content = msg.content
            else:
                conversation_parts.append(f"[{msg.role}]\n{msg.content}")

        conversation_str = "\n\n".join(conversation_parts)
        user_content = ASSISTANT_PROMPT_WRAPPER.format(conversation=conversation_str)

        api_messages = []
        if system_content:
            api_messages.append({"role": "system", "content": system_content})
        api_messages.append({"role": "user", "content": user_content})

        return api_messages

    async def run(self, verbose: bool = False) -> SimulationResult:
        """Run the full CollabLLM conversation simulation.

        Turn loop:
        1. User agent generates message (may terminate)
        2. Strategy prepares context
        3. Assistant generates response via Option 2 rendering
        4. Repeat until termination or max turns

        After conversation: evaluate via LLM judges.

        Returns:
            SimulationResult with evaluation outcome and trace.
        """
        verbose = verbose or self.config.verbose
        terminated = False
        termination_reason = "max_turns_reached"

        # Each "turn" is a user message + assistant response pair
        # max_turns counts user messages (matching CollabLLM's convention)
        while not terminated and self.trace.num_user_turns < self.config.max_turns:
            # --- USER TURN ---
            user_response = await self.user_agent.generate_response(
                trace=self.trace,
                model_client=self.model_client,
            )

            if user_response.model_response:
                self.usage_stats.record("user", user_response.model_response)

            # Check for termination signal
            if user_response.terminated:
                terminated = True
                termination_reason = "user_terminated"
                if verbose:
                    print(f"\033[94m[user] {user_response.content}\033[0m")
                    print("\033[93m[log] User terminated the conversation\033[0m")
                # Don't add terminated message to trace — it's a meta-signal
                break

            self.trace.add_user_message(
                content=user_response.content,
                metadata={"cost_usd": user_response.cost_usd},
            )

            if verbose:
                print(f"\033[94m[user] {user_response.content}\033[0m")

            # --- STRATEGY ---
            context_messages = await self.strategy.prepare_context(
                trace=self.trace,
                memory=self.memory,
                model_client=self.model_client,
            )

            # --- ASSISTANT TURN ---
            messages_for_api = self._render_for_assistant(context_messages)

            assistant_cfg = self.config.model_config.assistant
            max_tokens = assistant_cfg.get_effective_max_tokens()

            assistant_response = await self.model_client.generate(
                messages=messages_for_api,
                model=assistant_cfg.model,
                temperature=assistant_cfg.temperature,
                max_tokens=max_tokens,
                timeout=assistant_cfg.timeout,
                reasoning_effort=assistant_cfg.reasoning_effort,
            )

            self.trace.add_assistant_message(
                content=assistant_response.content,
                metadata={"cost_usd": assistant_response.total_usd},
            )
            self.usage_stats.record("assistant", assistant_response)

            if verbose:
                print(f"\033[91m[assistant] {assistant_response.content}\033[0m")

        # --- END-OF-CONVERSATION EVALUATION ---
        eval_result = await self._evaluate_conversation()

        return SimulationResult(
            sample_id=self.sample.get("task_id", "unknown"),
            task_name=self.sample.get("task", "collabllm"),
            is_correct=eval_result.is_correct,
            score=eval_result.score,
            num_turns=self.trace.total_user_turns,
            total_cost_usd=self.usage_stats.total_cost_usd(),
            trace=self.trace.to_full_trace(),
            extracted_answer=eval_result.extracted_answer,
            evaluation_result=eval_result,
            usage_stats=self.usage_stats,
            metadata={
                "termination_reason": termination_reason,
                "accuracy": eval_result.raw_evaluation.get("accuracy", -1)
                if eval_result.raw_evaluation
                else -1,
                "interactivity": eval_result.raw_evaluation.get("interactivity", -1)
                if eval_result.raw_evaluation
                else -1,
                "assistant_tokens": eval_result.raw_evaluation.get("assistant_tokens", 0)
                if eval_result.raw_evaluation
                else 0,
            },
        )

    async def _evaluate_conversation(self) -> EvaluationResult:
        """Run end-of-conversation evaluation using CollabLLM metrics."""
        # Build messages list for evaluation (active messages as dicts)
        active_messages = self.trace.get_active_messages()
        messages_for_eval = [
            {"role": msg.role, "content": msg.content} for msg in active_messages
        ]

        eval_result = await self.evaluator.evaluate(
            messages=messages_for_eval,
            single_turn_prompt=self.sample["single_turn_prompt"],
            single_turn_completion=self.sample["single_turn_completion"],
            model_client=self.model_client,
        )

        # Track eval cost in system usage
        if eval_result.eval_cost_usd > 0:
            # Create a synthetic ModelResponse for cost tracking
            from ..core.types import ModelResponse

            synthetic_resp = ModelResponse(
                content="",
                total_usd=eval_result.eval_cost_usd,
            )
            self.usage_stats.record("system", synthetic_resp)

        is_correct = eval_result.accuracy == 1.0
        score = eval_result.accuracy if eval_result.accuracy >= 0 else 0.0

        self.trace.add_log(
            "collabllm_evaluation",
            {
                "accuracy": eval_result.accuracy,
                "interactivity": eval_result.interactivity,
                "assistant_tokens": eval_result.assistant_tokens,
                "extracted_answer": eval_result.extracted_answer,
            },
        )

        return EvaluationResult(
            is_correct=is_correct,
            score=score,
            extracted_answer=eval_result.extracted_answer or "",
            raw_evaluation={
                "accuracy": eval_result.accuracy,
                "interactivity": eval_result.interactivity,
                "assistant_tokens": eval_result.assistant_tokens,
            },
        )
