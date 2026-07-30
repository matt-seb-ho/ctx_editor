"""Entanglement-controlled user simulation agent.

This is the core of the "entanglement knob" evaluation (Philippe's proposal). A standard
LiC ``UserAgent`` reveals shards that are INDEPENDENT of the assistant's turns — the "independent
communication" extreme. Real conversations are not like that: users phrase turns relative to what
the assistant just said ("no, reverse that", "use the value you got"). We expose that dependence
as an explicit, controllable knob so we can study context-management strategies across the whole
spectrum on a SINGLE benchmark.

Key invariant: entanglement changes ONLY the phrasing/interpretability of a shard reveal, never
the underlying task or ground-truth answer. The revealed shard's full information is always
conveyed; at higher levels it is simply expressed in a way that depends on the assistant's most
recent reply. Each generated turn also carries a ``decontextualized`` self-contained paraphrase,
used only to validate that the knob moved interpretability (not intent).
"""

import json
from typing import TYPE_CHECKING, Any, Optional

from ..core.types import ReasoningEffort
from ..paths import PROMPTS_DIR
from .user_agent import UserAgent, UserResponse

if TYPE_CHECKING:
    from ..core.trace import ConversationTrace
    from ..models.base import ModelClient


ENTANGLED_USER_PROMPT = (PROMPTS_DIR / "entanglement_user_agent.txt").read_text()


# Ordinal entanglement levels. Level 0 = standard LiC (delegates to the parent UserAgent).
# Levels 1-3 rewrite the shard reveal to depend on the assistant's most recent reply to an
# increasing degree. `name` is a short handle; `instructions` are injected into the prompt.
ENTANGLEMENT_LEVELS: dict[int, dict[str, str]] = {
    0: {
        "name": "independent",
        "instructions": (
            "Speak as if the assistant had said nothing relevant. Your message must be fully "
            "self-contained: a reader with NO access to the assistant's reply should understand it "
            "completely. Do not use pronouns or references that point at the assistant's reply."
        ),
    },
    1: {
        "name": "light-anaphora",
        "instructions": (
            "Lightly tie your message to the assistant's last reply using anaphora or acknowledgement "
            "(\"ok that makes sense, and also ...\", \"right, plus ...\"). The core information is "
            "still mostly recoverable on its own; the dependence is cosmetic. Use at most one "
            "pronoun/reference pointing back at the assistant."
        ),
    },
    2: {
        "name": "referential",
        "instructions": (
            "Phrase your message by REFERRING to specific things the assistant introduced — a value "
            "it computed, an option it listed, a variable/step it named (\"use the number you got for "
            "the second year\", \"go with your option B but ...\"). Without the assistant's reply, a "
            "reader could not resolve which value/option/entity you mean, though the shape of your "
            "request is visible. Still convey all of the shard's information."
        ),
    },
    3: {
        "name": "relative-elliptical",
        "instructions": (
            "Make your message a RELATIVE OPERATION or CORRECTION on the assistant's last reply — "
            "elliptical and uninterpretable WITHOUT it (\"no, reverse that\", \"the other one, not "
            "the one you used\", \"drop your last step and do it for the correct value instead\"). "
            "WITHOUT the assistant's reply a reader should be unable to recover what you mean. BUT "
            "with the assistant's reply present, your message plus that reply must still pin down the "
            "ENTIRE shard exactly — anchor with an ordinal, a name, or the correct quantity so nothing "
            "is left to guesswork. Elliptical, not vague: the dependence is on the assistant's turn, "
            "never on the reader having to infer missing shard content."
        ),
    },
}

MAX_LEVEL = max(ENTANGLEMENT_LEVELS)


class EntanglementUserAgent(UserAgent):
    """User agent that reveals shards with a controllable degree of entanglement.

    Args:
        task: The task instance.
        model: Model used for user simulation.
        entanglement_level: Integer 0..3. 0 reproduces standard LiC behavior.
    """

    def __init__(
        self,
        task: Any,
        model: str = "gpt-4o-mini",
        entanglement_level: int = 0,
        prompt_file: Optional[str] = None,
    ):
        super().__init__(task=task, model=model, prompt_file=prompt_file)
        if entanglement_level not in ENTANGLEMENT_LEVELS:
            raise ValueError(
                f"entanglement_level must be one of {sorted(ENTANGLEMENT_LEVELS)}, "
                f"got {entanglement_level}"
            )
        self.entanglement_level = entanglement_level
        self.entangled_prompt = ENTANGLED_USER_PROMPT

    async def generate_response(
        self,
        trace: "ConversationTrace",
        sample: dict[str, Any],
        model_client: "ModelClient",
        temperature: float = 1.0,
        reasoning_effort: Optional[ReasoningEffort] = None,
    ) -> UserResponse:
        num_user_msgs = trace.num_user_turns

        # Level 0, the first turn (no assistant turn to entangle with yet), or pre-defined-prompt
        # tasks fall back to the standard independent behavior.
        no_assistant_yet = trace.last_assistant_message is None
        if self.entanglement_level == 0 or num_user_msgs == 0 or no_assistant_yet:
            return await super().generate_response(
                trace, sample, model_client, temperature, reasoning_effort
            )

        revealed_shard_ids = trace.get_revealed_shard_ids()
        shards = sample["shards"][1:]
        shards_revealed = [s for s in shards if s["shard_id"] in revealed_shard_ids]
        shards_not_revealed = [s for s in shards if s["shard_id"] not in revealed_shard_ids]

        if not shards_not_revealed:
            return UserResponse(
                content="I've shared all the relevant information I have.",
                shard_id=None,
                cost_usd=0.0,
            )

        level_cfg = ENTANGLEMENT_LEVELS[self.entanglement_level]
        conversation_str = trace.get_conversation_string(skip_system=True)
        prompt = self.entangled_prompt.format(
            conversation_so_far=conversation_str,
            shards_revealed=json.dumps(shards_revealed),
            shards_not_revealed=json.dumps(shards_not_revealed),
            entanglement_level=self.entanglement_level,
            entanglement_name=level_cfg["name"],
            entanglement_instructions=level_cfg["instructions"],
        )

        from ..utils.call_meter import call_tag

        with call_tag("user"):
            response = await model_client.generate_json(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=temperature,
                reasoning_effort=reasoning_effort,
            )

        result = response.content
        return UserResponse(
            content=result.get("response", ""),
            shard_id=result.get("shard_id"),
            cost_usd=response.total_usd,
            model_response=response,
            entanglement_level=self.entanglement_level,
            decontextualized=result.get("decontextualized"),
        )
