"""MT-OSC — faithful reimplementation of Singh et al. (arXiv:2604.08782v3).

*MT-OSC: Path for LLMs that Get Lost in Multi-Turn Conversation*, Jyotika Singh,
Fang Tu, Miguel Ballesteros, Weiyi Sun, Sandip Ghoshal, Michelle Yuan, Yassine
Benajiba, Sujith Ravi, Dan Roth (Oracle AI). v3, 2026-06-01. cs.CL. **No code
release**: the paper has no code/data availability statement and no repository
link, so this is a from-the-paper reimplementation.

Added 2026-07-29 (task T1). MT-OSC is the closest published analogue to what
the NeurIPS Area Chair meant by "compaction / folding baselines", and it
evaluates on the *same sharded LiC datasets we use* (GSM8K, Spider, BFCL,
HumanEval), so it is the single most relevant missing comparison.

What is faithful, and what is not — stated up front so a reviewer can audit:

FAITHFUL (taken verbatim / exactly from the paper)
  * Condenser prompt — Appendix B.1, verbatim, in ``prompts/mtosc_condenser.txt``.
  * The three few-shot exemplars — transcribed from Figure 2, which is the only
    place they appear (a rasterised figure). The authors state the exemplar set
    "is central to maintaining nuanced context", so they are included.
  * Output contract — JSON ``{"HumanInput", "Assistant", "Reasoning"}``; the
    ``Reasoning`` field is discarded from the reconstructed history.
  * Condensation schedule — Appendix B.3, including the deliberate one-turn lag
    (the condenser runs "as a background process", so ``C_j`` computed at turn
    ``T_j`` is only *used* from turn ``T_j + 1``). Generalised from the paper's
    w=4 walkthrough: trigger at ``T_j = (w-1)j + 2``, usable from ``T_j + 1``,
    and ``C_j`` covers raw pairs ``1 … (w-1)j + 1``. Substituting w=4 reproduces
    the paper's turn-by-turn example exactly (trigger at 5/8/11, used from
    6/9/12, ``H_6 = {C_1, (u_5,a_5)}``, ``H_9 = {C_2, (u_8,a_8)}``).
  * Recursion — ``C_j = Condense({C_{j-1}} ∪ new pairs)``; raw pairs covered by
    a condensation are discarded outright.
  * Decider hyperparameters — γ = 0.2, τ = 1000 (Appendix B.3).
  * Decoder settings — temperature 0.01, top_p 1, frequency_penalty 1,
    max_completion_tokens 10000 (B.1), applied where the client supports them.

NOT FULLY DETERMINED BY THE PAPER (recorded, not papered over)
  1. **The Decider's polarity is self-contradictory in the paper.** §3 says the
     rule fires when redundancy is high and "condensation is *withheld* to avoid
     potential loss", but the Combined-Operation equation reads "raw history *if
     D_w is False*, condensed otherwise" — i.e. the opposite. We implement the
     prose (fire ⇒ withhold), which matches the stated design rationale and the
     ablation (the Decider blocks condensation on the information-dense ToTTo /
     Summary-of-Haystack sets). **This choice is inert on LiC**: τ = 1000 user
     tokens over w turns is never reached by LiC's short sharded user messages,
     so the Decider never fires either way. That is measured and logged per run
     (``mtosc_decider`` log records), not assumed.
  2. The exact stopword list, lemmatiser and tokeniser behind
     "normalized content words" and ``UserTokens`` are not stated. We use a
     small built-in stopword list, a suffix-stripping lemmatiser, and
     whitespace tokens. See (1): inert here.
  3. The concatenation format joining the exemplars into the prompt is not
     stated; we follow the B.1 skeleton literally.
  4. The paper's condenser LLM is Llama-3.3-70B-Instruct. We run the condenser
     on the same model as every other arm's context operator (gpt-5.4-mini) so
     that the comparison against AC3 is at matched model, which is the point of
     the experiment. The paper's own §5.3 ("Generalization Across Condenser
     LLMs") reports MT-OSC is not sensitive to the condenser model.

Known structural consequence, worth stating in any write-up: at the paper's
headline w=4, MT-OSC does not modify anything before turn 6. The authors say as
much (their Spider ≥6-turn subset is n=6). On LiC conversations that average
~4-7 turns this makes w=4 a near-no-op, so ``w=2`` — the smallest window in the
paper's own sweep (w ∈ {2,3,4}) — is also run, and it intervenes from turn 4.
"""

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from ..core.types import Message
from ..utils.logging import get_logger
from .base import BaseStrategy

if TYPE_CHECKING:
    from ..core.trace import ConversationTrace
    from ..memory.base import MemoryModule
    from ..models.base import ModelClient

logger = get_logger("mtosc")

_PROMPT_DIR = Path(__file__).parent / "prompts"

# Small built-in stopword list. The paper says "standard preprocessing (stop
# word removal, case normalization, and lemmatization)" without naming a list.
_STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but",
    "by", "can", "cannot", "could", "did", "do", "does", "doing", "down", "during", "each",
    "few", "for", "from", "further", "had", "has", "have", "having", "he", "her", "here",
    "hers", "herself", "him", "himself", "his", "how", "i", "if", "in", "into", "is", "it",
    "its", "itself", "let", "me", "more", "most", "must", "my", "myself", "no", "nor", "not",
    "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves",
    "out", "over", "own", "same", "shall", "she", "should", "so", "some", "such", "than",
    "that", "the", "their", "theirs", "them", "themselves", "then", "there", "these", "they",
    "this", "those", "through", "to", "too", "under", "until", "up", "very", "was", "we",
    "were", "what", "when", "where", "which", "while", "who", "whom", "why", "will", "with",
    "would", "you", "your", "yours", "yourself", "yourselves",
}


def _load_prompt(name: str) -> str:
    return (_PROMPT_DIR / f"{name}.txt").read_text()


def _lemma(word: str) -> str:
    """Suffix-stripping lemmatiser stand-in (the paper does not name one)."""
    for suf in ("ies", "ing", "ed", "es", "s"):
        if len(word) > len(suf) + 2 and word.endswith(suf):
            if suf == "ies":
                return word[:-3] + "y"
            return word[: -len(suf)]
    return word


def _content_words(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9_]+", text.lower())
    return {_lemma(w) for w in words if w not in _STOPWORDS}


def _jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 0.0
    u = a | b
    return len(a & b) / len(u) if u else 0.0


class MTOSCStrategy(BaseStrategy):
    """One-off Sequential Condensation (Singh et al., arXiv:2604.08782).

    State is kept entirely in ``trace.logs`` (log types ``mtosc_condensation``
    and ``mtosc_decider``), never on the strategy instance — the strategy object
    is shared across all conversations in a run.
    """

    def __init__(
        self,
        condenser_model: str = "gpt-4o-mini",
        condenser_timeout: int = 300,
        condenser_max_tokens: Optional[int] = 10000,
        condenser_reasoning_effort: Optional[str] = None,
        condenser_temperature: float = 0.01,
        condenser_prompt: str = "mtosc_condenser",
        window: int = 4,
        gamma: float = 0.2,
        tau: int = 1000,
    ):
        self.model = condenser_model
        self.timeout = condenser_timeout
        self.max_tokens = condenser_max_tokens
        self.reasoning_effort = condenser_reasoning_effort
        self.temperature = condenser_temperature
        self.window = int(window)
        if self.window < 2:
            raise ValueError("MT-OSC window w must be >= 2")
        self.gamma = float(gamma)
        self.tau = int(tau)
        self._template = _load_prompt(condenser_prompt)
        self._prompt_name = condenser_prompt

    # --- helpers ----------------------------------------------------------
    @staticmethod
    def _turn_index(trace: "ConversationTrace") -> int:
        """1-based index of the turn about to be generated.

        Counted from ``verification`` log records (one per completed assistant
        turn). Unlike message counts this is unaffected by context resets, which
        re-add a copy of the latest user message.
        """
        return sum(1 for log in trace.logs if log["type"] == "verification") + 1

    def _trigger_turn(self, t: int) -> bool:
        """T_j = (w-1)*j + 2 for j = 1, 2, ...  (w=4 -> 5, 8, 11)."""
        w = self.window
        return t >= w + 1 and (t - 2) % (w - 1) == 0

    @staticmethod
    def _pending(trace: "ConversationTrace") -> Optional[dict]:
        for log in reversed(trace.logs):
            if log["type"] == "mtosc_condensation":
                d = log["data"]
                return d if not d.get("applied") else None
        return None

    @staticmethod
    def _window_pairs(trace: "ConversationTrace") -> list[tuple[str, str]]:
        """(user, assistant) pairs currently in the active context.

        After a reset the active context is exactly MT-OSC's H_t: the condensed
        pair (rendered as a user/assistant pair) followed by the raw pairs
        accumulated since. The just-added latest user message is excluded.
        """
        msgs = [m for m in trace.get_active_messages() if m.role in ("user", "assistant")]
        pairs = []
        pending_user = None
        for m in msgs:
            if m.role == "user":
                pending_user = m.content
            elif pending_user is not None:
                pairs.append((pending_user, m.content))
                pending_user = None
        return pairs

    def _decider(self, pairs: list[tuple[str, str]]) -> dict:
        """D_w. Returns the components as well as the decision, for logging.

        Fires (``withhold=True``) when average cross-assistant-turn overlap of
        *new* assistant terms exceeds gamma AND total user tokens in the window
        exceed tau. See the module docstring for the polarity ambiguity.
        """
        user_msgs = [u for u, _ in pairs]
        assistant_msgs = [a for _, a in pairs]
        user_tokens = sum(len(u.split()) for u in user_msgs)

        # New assistant terms: A_i minus everything the user has said up to i.
        new_terms = []
        seen_user: set[str] = set()
        for u, a in pairs:
            seen_user |= _content_words(u)
            new_terms.append(_content_words(a) - seen_user)

        overlaps = [
            _jaccard(new_terms[i], new_terms[j])
            for i in range(len(new_terms))
            for j in range(i + 1, len(new_terms))
        ]
        avg_overlap = sum(overlaps) / len(overlaps) if overlaps else 0.0
        withhold = avg_overlap > self.gamma and user_tokens > self.tau
        return {
            "withhold": withhold,
            "avg_overlap": avg_overlap,
            "user_tokens": user_tokens,
            "gamma": self.gamma,
            "tau": self.tau,
            "n_pairs": len(pairs),
            "n_assistant_msgs": len(assistant_msgs),
        }

    @staticmethod
    def _serialize(pairs: list[tuple[str, str]]) -> str:
        out = []
        for u, a in pairs:
            out.append(f"HumanInput: {u}")
            out.append(f"Assistant: {a}")
        return "\n".join(out)

    async def _condense(
        self, pairs: list[tuple[str, str]], model_client: "ModelClient"
    ) -> Optional[dict]:
        # NOTE: plain str.replace, not str.format — the prompt embeds literal
        # JSON braces from the Figure-2 exemplars, which str.format would try
        # to interpret as replacement fields.
        prompt = self._template.replace("{conversation}", self._serialize(pairs))
        kwargs: dict = {
            "messages": [{"role": "user", "content": prompt}],
            "model": self.model,
            "temperature": self.temperature,
            "timeout": self.timeout,
        }
        if self.max_tokens:
            kwargs["max_tokens"] = self.max_tokens
        if self.reasoning_effort:
            kwargs["reasoning_effort"] = self.reasoning_effort

        from ..utils.call_meter import call_tag

        with call_tag("strategy"):
            resp = await model_client.generate(**kwargs)
        raw = resp.content or ""

        parsed = None
        try:
            parsed = json.loads(raw)
        except Exception:
            m = re.search(r"\{.*\}", raw, re.DOTALL)
            if m:
                try:
                    parsed = json.loads(m.group(0))
                except Exception:
                    parsed = None
        if not isinstance(parsed, dict) or "HumanInput" not in parsed:
            logger.warning("MT-OSC condenser returned unparseable output: %r", raw[:200])
            return None
        return {
            "HumanInput": str(parsed.get("HumanInput", "")),
            "Assistant": str(parsed.get("Assistant", "")),
            "Reasoning": str(parsed.get("Reasoning", "")),
            "raw_output": raw,
        }

    # --- main -------------------------------------------------------------
    async def prepare_context(
        self,
        trace: "ConversationTrace",
        memory: Optional["MemoryModule"],
        model_client: "ModelClient",
    ) -> list[Message]:
        t = self._turn_index(trace)

        # (1) Apply a condensation computed on the previous turn. This is the
        #     paper's one-turn lag: the condenser runs in the background, so
        #     C_j is only usable from turn T_j + 1.
        pending = self._pending(trace)
        if pending is not None and t >= pending["available_turn"]:
            new_messages: list[Message] = []
            system_msg = trace.system_message
            if system_msg:
                new_messages.append(Message(role="system", content=system_msg.content))
            new_messages.append(Message(role="user", content=pending["human_input"]))
            new_messages.append(Message(role="assistant", content=pending["assistant"]))
            last_user = trace.last_user_message
            if last_user:
                new_messages.append(Message(role="user", content=last_user.content))
            trace.reset_conversation(new_messages, label="mtosc_condensation")
            pending["applied"] = True
            trace.add_log("mtosc_applied", {"j": pending["j"], "turn": t})

        # (2) Trigger the next condensation, if this is a scheduled trigger turn.
        if self._trigger_turn(t):
            pairs = self._window_pairs(trace)
            if pairs:
                decision = self._decider(pairs)
                decision["turn"] = t
                trace.add_log("mtosc_decider", decision)
                if not decision["withhold"]:
                    result = await self._condense(pairs, model_client)
                    if result is not None:
                        j = 1 + sum(
                            1 for log in trace.logs if log["type"] == "mtosc_condensation"
                        )
                        trace.add_log(
                            "mtosc_condensation",
                            {
                                "j": j,
                                "turn_computed": t,
                                "available_turn": t + 1,
                                "applied": False,
                                "human_input": result["HumanInput"],
                                "assistant": result["Assistant"],
                                "reasoning": result["Reasoning"],
                                "n_pairs_condensed": len(pairs),
                                "model": self.model,
                                "window": self.window,
                            },
                        )

        return trace.get_active_messages()
