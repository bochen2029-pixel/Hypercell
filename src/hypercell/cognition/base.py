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
    # Cache usage is priced differently from fresh input on every provider that offers it, so a
    # meter that cannot see it cannot be truthful. Captured here, priced by conductor/pricebook.py.
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    #: The provider's OWN number when it reports one. It is the invoice; our arithmetic is a
    #: prediction of it, so where they disagree this wins and the gap becomes reconciliation input.
    api_reported_usd: float | None = None
    #: Populated by the metering path (F26: dormant in v1 — every receipt was honest about
    #: everything except its dollars).
    cost_usd: float = 0.0
    raw: dict[str, Any] | None = None


class Cognition(abc.ABC):
    """The one interface every provider adapter implements."""

    name: str

    @abc.abstractmethod
    async def complete(self, messages: Messages, **params: Any) -> CompletionResult:
        """Rented cognition: messages in, a completion out. Never closes a loop by itself."""
        raise NotImplementedError
