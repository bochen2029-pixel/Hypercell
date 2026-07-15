"""An offline, deterministic cognition adapter — the island floor and the test double.

No network, no key. Used by tests and the crash-resume drill, and available as a local fallback so no
cell hard-requires a cloud tier to close its loop (constitution: the island floor).
"""
from __future__ import annotations

from typing import Any

from .base import Cognition, CompletionResult, Messages


class MockCognition(Cognition):
    def __init__(self, model: str = "mock", name: str = "mock") -> None:
        self.name = name
        self._model = model
        self.calls = 0  # lets tests assert exactly-once (a resumed, completed act is never re-called)

    async def complete(self, messages: Messages, **params: Any) -> CompletionResult:
        self.calls += 1
        last_user = next(
            (m.get("content", "") for m in reversed(messages) if m.get("role") == "user"), ""
        )
        text = f"[mock:{self._model}] {last_user.strip()[:400]}"
        return CompletionResult(
            text=text,
            model=self._model,
            prompt_tokens=len(str(messages)) // 4,
            completion_tokens=len(text) // 4,
        )
