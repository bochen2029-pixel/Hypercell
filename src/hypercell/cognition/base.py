"""The cognition seam: rent the model, own the loop (constitution A4).

A cell's brain is an interchangeable `Cognition` behind one interface. Provider is config, not code
(HC-6). Concrete adapters live beside this file; `registry.build_cognition()` resolves a ProviderConfig
to one.
"""
from __future__ import annotations

import abc
from typing import Any

from pydantic import BaseModel, ConfigDict

Messages = list[dict[str, str]]  # OpenAI chat shape: [{"role": "user", "content": "..."}]


class CompletionResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    text: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    raw: dict[str, Any] | None = None


class Cognition(abc.ABC):
    """The one interface every provider adapter implements."""

    name: str

    @abc.abstractmethod
    async def complete(self, messages: Messages, **params: Any) -> CompletionResult:
        """Rented cognition: messages in, a completion out. Never closes a loop by itself."""
        raise NotImplementedError
