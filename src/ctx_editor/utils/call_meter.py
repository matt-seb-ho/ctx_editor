"""Process-global LLM call/token meter.

Added 2026-07-29 for the T1 "matched call budget" experiment: reviewers asked
for *measured* per-arm call and token counts rather than an assertion that two
strategies cost the same. Every OpenAI-compatible response funnels through
``OpenAIModelClient._parse_response``, which is the single choke point where we
record.

Attribution uses a :mod:`contextvars` tag so that async tasks running
concurrently do not clobber each other's labels. Components set the tag around
their own ``generate`` calls (``user``, ``system``, ``strategy``,
``fn_analysis``); anything unlabelled is the assistant turn, which is the
default.

Nothing here raises: a metering failure must never break an experiment.
"""

from __future__ import annotations

import contextvars
import threading
from contextlib import contextmanager
from typing import Any, Iterator, Optional

_TAG: contextvars.ContextVar[str] = contextvars.ContextVar(
    "ctx_editor_call_tag", default="assistant"
)


def _empty() -> dict[str, Any]:
    return {
        "calls": 0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "cached_prompt_tokens": 0,
        "cost_usd": 0.0,
    }


class CallMeter:
    """Thread-safe accumulator of LLM call counts and token usage."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.by_tag: dict[str, dict[str, Any]] = {}
        self.by_model: dict[str, dict[str, Any]] = {}
        self.total: dict[str, Any] = _empty()

    def record(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        cached_prompt_tokens: int = 0,
        cost_usd: float = 0.0,
        tag: Optional[str] = None,
    ) -> None:
        try:
            tag = tag or _TAG.get()
            with self._lock:
                for bucket in (
                    self.by_tag.setdefault(tag, _empty()),
                    self.by_model.setdefault(model, _empty()),
                    self.total,
                ):
                    bucket["calls"] += 1
                    bucket["prompt_tokens"] += int(prompt_tokens or 0)
                    bucket["completion_tokens"] += int(completion_tokens or 0)
                    bucket["total_tokens"] += int(total_tokens or 0)
                    bucket["cached_prompt_tokens"] += int(cached_prompt_tokens or 0)
                    bucket["cost_usd"] += float(cost_usd or 0.0)
        except Exception:  # pragma: no cover - metering must never break a run
            pass

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "total": dict(self.total),
                "by_tag": {k: dict(v) for k, v in self.by_tag.items()},
                "by_model": {k: dict(v) for k, v in self.by_model.items()},
            }

    def reset(self) -> None:
        with self._lock:
            self.by_tag.clear()
            self.by_model.clear()
            self.total = _empty()


METER = CallMeter()


@contextmanager
def call_tag(tag: str) -> Iterator[None]:
    """Label every LLM call made inside this block (same task/coroutine)."""
    token = _TAG.set(tag)
    try:
        yield
    finally:
        _TAG.reset(token)


def current_tag() -> str:
    return _TAG.get()
