"""Main conversation simulator."""

from typing import TYPE_CHECKING, Any, Optional

from .trace import ConversationTrace
from .types import EvaluationResult, Message, SimulationResult, SimulatorConfig, UsageStats

if TYPE_CHECKING:
    from ..agents.system_agent import SystemAgent
    from ..agents.user_agent import UserAgent
    from ..memory.base import MemoryModule
    from ..models.base import ModelClient
    from ..strategies.base import ContextStrategy

# Prompt wrapper for Option 2 conversation format: render history as string
# inside a single user message rather than as alternating API messages.
ASSISTANT_PROMPT_WRAPPER = """\
Here is the current conversation:

{conversation}

Please respond to the user. Do not include [user] or [assistant] tags in your response."""


class ConversationSimulator:
    """Orchestrates multi-turn conversations for evaluation.

    Uses dependency injection for flexibility in mixing strategies,
    agents, and models.
    """

    def __init__(
        self,
        sample: dict[str, Any],
        task: Any,
        user_agent: "UserAgent",
        system_agent: "SystemAgent",
        model_client: "ModelClient",
        strategy: "ContextStrategy",
        memory: Optional["MemoryModule"] = None,
        config: Optional[SimulatorConfig] = None,
        trace: Optional[ConversationTrace] = None,
    ):
        """Initialize the simulator.

        Args:
            sample: The sample data containing shards and metadata.
            task: The task instance for evaluation.
            user_agent: Agent for simulating user responses.
            system_agent: Agent for verification and answer extraction.
            model_client: Client for model API calls.
            strategy: Strategy for context preparation.
            memory: Optional memory module for context augmentation.
            config: Simulator configuration.
            trace: Optional pre-loaded trace (for replay mode). If provided,
                the simulator will use this trace instead of creating a new one.
        """
        self.sample = sample
        self.task = task
        self.user_agent = user_agent
        self.system_agent = system_agent
        self.model_client = model_client
        self.strategy = strategy
        self.memory = memory
        self.config = config or SimulatorConfig()

        self.usage_stats = UsageStats()
        self.is_completed = False
        self.final_result: Optional[SimulationResult] = None

        if trace is not None:
            # Replay mode: use the pre-loaded trace
            self.trace = trace
        else:
            # Normal mode: create fresh trace with system message
            self.trace = ConversationTrace()
            system_prompt = task.generate_system_prompt(sample)
            self.trace.add_system_message(system_prompt)

    @staticmethod
    def _render_for_assistant(context_messages: list[Message]) -> list[dict[str, str]]:
        """Render context messages into Option 2 format for the API call.

        Instead of passing the conversation as alternating user/assistant API messages,
        we render it as a tagged string inside a single user message. This gives full
        control over formatting and allows injecting arbitrary content (analysis, edited
        context) without worrying about API message alternation requirements.

        Format sent to API:
            [{"role": "system", "content": "..."},
             {"role": "user", "content": "Here is the current conversation:\\n\\n[CONTENT]\\n\\n..."}]
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

    def _build_result_metadata(self, extra: dict[str, Any] | None = None) -> dict[str, Any]:
        """Build metadata dict for SimulationResult, including grounding info.

        Args:
            extra: Additional metadata to include.

        Returns:
            Combined metadata dict with full_spec_q and ground_truth_a if available.
        """
        metadata = {}

        # Include grounding information from sample if available
        if "full_spec_q" in self.sample:
            metadata["full_spec_q"] = self.sample["full_spec_q"]
        if "ground_truth_a" in self.sample:
            metadata["ground_truth_a"] = self.sample["ground_truth_a"]

        # Merge with any extra metadata
        if extra:
            metadata.update(extra)

        return metadata

    @property
    def is_replay(self) -> bool:
        """Whether this simulator is running in replay mode (pre-loaded trace)."""
        return self.trace.provenance is not None

    async def run(self, verbose: bool = False) -> SimulationResult:
        """Run the full conversation simulation.

        If the simulator was initialized with a pre-loaded trace (replay mode),
        delegates to run_final_turn() instead of running the full loop.

        Args:
            verbose: Whether to print conversation progress.

        Returns:
            SimulationResult with evaluation outcome and trace.
        """
        # Replay mode: only regenerate the final assistant turn
        if self.is_replay:
            return await self.run_final_turn(verbose)

        verbose = verbose or self.config.verbose

        shards = self.sample.get("shards", [])
        termination_reason = "max_turns_reached"

        while not self.is_completed and self.trace.num_user_turns < self.config.max_turns:
            # Check if all shards have been revealed - no point continuing
            revealed_shard_ids = set(self.trace.get_revealed_shard_ids())
            if len(revealed_shard_ids) == len(shards) and len(shards) > 0:
                if verbose:
                    print(
                        f"\033[94m[log] all shards revealed ({len(revealed_shard_ids)}/{len(shards)})\033[0m"
                    )
                termination_reason = "all_shards_revealed"
                break

            await self._run_turn(verbose)

            # Check if user budget was exhausted (natural mode)
            if any(log["type"] == "user_budget_exhausted" for log in self.trace.logs):
                termination_reason = "user_budget_exhausted"
                break

        # Ensure we have a result
        if self.final_result is None:
            self.final_result = SimulationResult(
                sample_id=self.sample.get("task_id", "unknown"),
                task_name=(
                    self.task.get_task_name() if hasattr(self.task, "get_task_name") else "unknown"
                ),
                is_correct=False,
                score=0.0,
                num_turns=self.trace.total_user_turns,  # Use total across all resets
                total_cost_usd=self.usage_stats.total_cost_usd(),
                trace=self.trace.to_full_trace(),
                usage_stats=self.usage_stats,
                metadata=self._build_result_metadata({"reason": termination_reason}),
            )

        return self.final_result

    async def run_final_turn(self, verbose: bool = False) -> SimulationResult:
        """Run only the final turn on a pre-loaded trace (replay mode).

        Applies the context strategy, generates assistant response, verifies,
        and evaluates — but does NOT generate a new user message (the last user
        message is already in the trace from the baseline run).

        Args:
            verbose: Whether to print progress.

        Returns:
            SimulationResult with evaluation outcome and trace.
        """
        verbose = verbose or self.config.verbose

        # Apply context strategy
        context_messages = await self.strategy.prepare_context(
            trace=self.trace,
            memory=self.memory,
            model_client=self.model_client,
        )

        # Render and generate assistant response
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

        # Verify the response
        system_cfg = self.config.model_config.system
        verification = await self.system_agent.verify_response(
            trace=self.trace,
            model_client=self.model_client,
            reasoning_effort=system_cfg.reasoning_effort,
        )
        if verification.model_response:
            self.usage_stats.record("system", verification.model_response)

        self.trace.add_log(
            "verification",
            {
                "response_type": verification.response_type,
                "is_answer_attempt": verification.is_answer_attempt,
            },
        )

        # If answer attempt, extract and evaluate
        eval_result = None
        extracted_answer = None
        is_correct = False
        score = 0.0

        if verification.is_answer_attempt:
            extraction = await self.system_agent.extract_answer(
                trace=self.trace,
                model_client=self.model_client,
                reasoning_effort=system_cfg.reasoning_effort,
            )
            for model_response in extraction.model_responses:
                self.usage_stats.record("system", model_response)

            evaluation_return = self.task.evaluator_function(
                extraction.answer,
                self.sample,
            )

            if isinstance(evaluation_return, dict):
                score = evaluation_return.get("score", 0.0)
                is_correct = evaluation_return.get("is_correct", score == 1.0)
            elif isinstance(evaluation_return, tuple):
                is_correct, _ = evaluation_return
                score = 1.0 if is_correct else 0.0
            else:
                is_correct = bool(evaluation_return)
                score = 1.0 if is_correct else 0.0

            eval_result = EvaluationResult(
                is_correct=is_correct,
                score=score,
                extracted_answer=extraction.answer,
                raw_evaluation=evaluation_return if isinstance(evaluation_return, dict) else None,
            )
            extracted_answer = extraction.answer

            self.trace.add_log(
                "answer_evaluation",
                {
                    "extracted_answer": extraction.answer,
                    "is_correct": is_correct,
                    "score": score,
                },
            )

            if verbose:
                icon = "\033[92m✔\033[0m" if is_correct else "\033[91m✘\033[0m"
                print(f"{icon} Score: {score}")

        return SimulationResult(
            sample_id=self.sample.get("task_id", "unknown"),
            task_name=(
                self.task.get_task_name() if hasattr(self.task, "get_task_name") else "unknown"
            ),
            is_correct=is_correct,
            score=score,
            num_turns=self.trace.total_user_turns,
            total_cost_usd=self.usage_stats.total_cost_usd(),
            trace=self.trace.to_full_trace(),
            extracted_answer=extracted_answer,
            evaluation_result=eval_result,
            usage_stats=self.usage_stats,
            metadata=self._build_result_metadata({"replay_mode": True}),
        )

    async def _run_turn(self, verbose: bool = False) -> None:
        """Execute a single conversation turn.

        A turn consists of:
        1. Generate user response
        2. Apply context strategy
        3. Generate assistant response
        4. Verify and potentially evaluate

        Args:
            verbose: Whether to print progress.
        """
        # 1. Generate user response
        user_cfg = self.config.model_config.user
        user_response = await self.user_agent.generate_response(
            trace=self.trace,
            sample=self.sample,
            model_client=self.model_client,
            temperature=user_cfg.temperature,
            reasoning_effort=user_cfg.reasoning_effort,
        )

        self.trace.add_user_message(
            content=user_response.content,
            metadata={"cost_usd": user_response.cost_usd},
        )
        # Track usage for user role
        if user_response.model_response:
            self.usage_stats.record("user", user_response.model_response)

        # Log shard revelation if applicable
        # Note: shard_id of -1 means "no shard revealed" (per user agent prompt)
        if user_response.shard_id is not None and user_response.shard_id != -1:
            self.trace.add_log("shard_revealed", {"shard_id": user_response.shard_id})

        # Budget exhausted (natural mode) — log and return without generating assistant turn
        if user_response.budget_exhausted:
            self.trace.add_log("user_budget_exhausted", {})
            return

        if verbose:
            print(f"\033[94m[user] {user_response.content}\033[0m")

        # 2. Apply context strategy to prepare context
        context_messages = await self.strategy.prepare_context(
            trace=self.trace,
            memory=self.memory,
            model_client=self.model_client,
        )

        # 3. Render as Option 2 format and generate assistant response
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

        # 4. Verify the response
        system_cfg = self.config.model_config.system
        verification = await self.system_agent.verify_response(
            trace=self.trace,
            model_client=self.model_client,
            reasoning_effort=system_cfg.reasoning_effort,
        )
        # Track usage for system role
        if verification.model_response:
            self.usage_stats.record("system", verification.model_response)

        self.trace.add_log(
            "verification",
            {
                "response_type": verification.response_type,
                "is_answer_attempt": verification.is_answer_attempt,
            },
        )

        # 5. If this is an answer attempt, extract and evaluate
        if verification.is_answer_attempt:
            extraction = await self.system_agent.extract_answer(
                trace=self.trace,
                model_client=self.model_client,
                reasoning_effort=system_cfg.reasoning_effort,
            )
            # Track usage for system role (extraction may have multiple attempts)
            for model_response in extraction.model_responses:
                self.usage_stats.record("system", model_response)

            # Evaluate the answer
            evaluation_return = self.task.evaluator_function(
                extraction.answer,
                self.sample,
            )

            # Handle different evaluation return formats
            if isinstance(evaluation_return, dict):
                score = evaluation_return.get("score", 0.0)
                is_correct = evaluation_return.get("is_correct", score == 1.0)
            elif isinstance(evaluation_return, tuple):
                is_correct, feedback = evaluation_return
                score = 1.0 if is_correct else 0.0
            else:
                is_correct = bool(evaluation_return)
                score = 1.0 if is_correct else 0.0

            eval_result = EvaluationResult(
                is_correct=is_correct,
                score=score,
                extracted_answer=extraction.answer,
                raw_evaluation=evaluation_return if isinstance(evaluation_return, dict) else None,
            )

            self.trace.add_log(
                "answer_evaluation",
                {
                    "extracted_answer": extraction.answer,
                    "is_correct": is_correct,
                    "score": score,
                },
            )

            if verbose:
                icon = "\033[92m✔\033[0m" if is_correct else "\033[91m✘\033[0m"
                print(f"{icon} Score: {score}")

            # Only mark as completed if the answer is correct
            # This matches the original LiC behavior - incorrect answers allow
            # the conversation to continue so more shards can be revealed
            if is_correct:
                self.is_completed = True
                self.final_result = SimulationResult(
                    sample_id=self.sample.get("task_id", "unknown"),
                    task_name=(
                        self.task.get_task_name()
                        if hasattr(self.task, "get_task_name")
                        else "unknown"
                    ),
                    is_correct=is_correct,
                    score=score,
                    num_turns=self.trace.total_user_turns,  # Use total across all resets
                    total_cost_usd=self.usage_stats.total_cost_usd(),
                    trace=self.trace.to_full_trace(),
                    extracted_answer=extraction.answer,
                    evaluation_result=eval_result,
                    usage_stats=self.usage_stats,
                    metadata=self._build_result_metadata(),
                )
