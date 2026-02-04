"""Main conversation simulator."""

from typing import TYPE_CHECKING, Any, Optional

from .trace import ConversationTrace
from .types import EvaluationResult, Message, SimulationResult, SimulatorConfig, UsageStats

if TYPE_CHECKING:
    from ..agents.system_agent import SystemAgent
    from ..agents.user_agent import UserAgent
    from ..cheatsheet.cheatsheet import Cheatsheet
    from ..models.base import ModelClient
    from ..strategies.base import ContextStrategy


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
        cheatsheet: Optional["Cheatsheet"] = None,
        config: Optional[SimulatorConfig] = None,
    ):
        """Initialize the simulator.

        Args:
            sample: The sample data containing shards and metadata.
            task: The task instance for evaluation.
            user_agent: Agent for simulating user responses.
            system_agent: Agent for verification and answer extraction.
            model_client: Client for model API calls.
            strategy: Strategy for context preparation.
            cheatsheet: Optional cheatsheet for context augmentation.
            config: Simulator configuration.
        """
        self.sample = sample
        self.task = task
        self.user_agent = user_agent
        self.system_agent = system_agent
        self.model_client = model_client
        self.strategy = strategy
        self.cheatsheet = cheatsheet
        self.config = config or SimulatorConfig()

        self.trace = ConversationTrace()
        self.usage_stats = UsageStats()
        self.is_completed = False
        self.final_result: Optional[SimulationResult] = None

        # Initialize with system message
        system_prompt = task.generate_system_prompt(sample)
        self.trace.add_system_message(system_prompt)

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

    async def run(self, verbose: bool = False) -> SimulationResult:
        """Run the full conversation simulation.

        Args:
            verbose: Whether to print conversation progress.

        Returns:
            SimulationResult with evaluation outcome and trace.
        """
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

        # Ensure we have a result
        if self.final_result is None:
            self.final_result = SimulationResult(
                sample_id=self.sample.get("task_id", "unknown"),
                task_name=self.task.get_task_name()
                if hasattr(self.task, "get_task_name")
                else "unknown",
                is_correct=False,
                score=0.0,
                num_turns=self.trace.total_user_turns,  # Use total across all resets
                total_cost_usd=self.usage_stats.total_cost_usd(),
                trace=self.trace.to_full_trace(),
                usage_stats=self.usage_stats,
                metadata=self._build_result_metadata({"reason": termination_reason}),
            )

        return self.final_result

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

        if verbose:
            print(f"\033[94m[user] {user_response.content}\033[0m")

        # 2. Apply context strategy to prepare context
        context_messages = await self.strategy.prepare_context(
            trace=self.trace,
            cheatsheet=self.cheatsheet,
            model_client=self.model_client,
        )

        # Convert to dict format for API call
        messages_for_api = [
            msg.to_dict() if isinstance(msg, Message) else msg for msg in context_messages
        ]

        # 3. Generate assistant response using role config
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
        verification = await self.system_agent.verify_response(
            trace=self.trace,
            model_client=self.model_client,
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
                    task_name=self.task.get_task_name()
                    if hasattr(self.task, "get_task_name")
                    else "unknown",
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
