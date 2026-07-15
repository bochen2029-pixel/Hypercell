"""The cost governor (HC-8) + per-provider concurrency (constitution A10, §10).

One metering path: the budget hard-stop cannot be bypassed, because there is exactly one place cost is
checked and recorded. Per-provider concurrency caps keep a fan-out from melting the box or blowing rate
limits. Prices are advisory defaults (USD per 1M tokens: input, output); pin them in a lock later.
"""
from __future__ import annotations

import asyncio
from typing import Any

from ..cognition.base import Cognition, CompletionResult, Messages

_PRICE: dict[str, tuple[float, float]] = {
    "deepseek": (0.14, 0.28),
    "cerebras": (0.60, 0.60),
    "openai": (0.15, 0.60),
    "glm": (0.20, 0.20),
    "kimi": (0.15, 0.60),
    "qwen": (0.20, 0.60),
    "grok": (2.00, 10.00),
    "anthropic": (3.00, 15.00),
    "gemini": (0.30, 2.50),
    "mock": (0.0, 0.0),
    "echo": (0.0, 0.0),
    "stub": (0.0, 0.0),
}


class BudgetExceeded(RuntimeError):
    pass


class Governor:
    def __init__(
        self, usd_cap: float = 1.0, per_provider_concurrency: dict[str, int] | None = None
    ) -> None:
        self.usd_cap = usd_cap
        self.spent = 0.0
        self._sems: dict[str, asyncio.Semaphore] = {
            p: asyncio.Semaphore(n) for p, n in (per_provider_concurrency or {}).items()
        }

    def price(self, provider: str, result: CompletionResult) -> float:
        pin, pout = _PRICE.get(provider, (0.5, 1.5))
        return result.prompt_tokens / 1e6 * pin + result.completion_tokens / 1e6 * pout

    def check(self) -> None:
        """The hard-stop: raise BEFORE spending once the cap is reached."""
        if self.spent >= self.usd_cap:
            raise BudgetExceeded(
                f"budget hard-stop: spent ${self.spent:.4f} >= cap ${self.usd_cap:.4f}"
            )

    def record(self, provider: str, result: CompletionResult) -> float:
        cost = self.price(provider, result)
        self.spent += cost
        return cost

    def semaphore(self, provider: str) -> asyncio.Semaphore | None:
        return self._sems.get(provider)


class MeteredCognition(Cognition):
    """Wrap any Cognition: enforce the hard-stop before, meter cost after, cap concurrency around."""

    def __init__(self, inner: Cognition, provider: str, gov: Governor) -> None:
        self.name = f"metered:{inner.name}"
        self._inner = inner
        self._provider = provider
        self._gov = gov

    async def complete(self, messages: Messages, **params: Any) -> CompletionResult:
        self._gov.check()  # the single hard-stop, before any spend
        sem = self._gov.semaphore(self._provider)
        if sem is not None:
            async with sem:
                result = await self._inner.complete(messages, **params)
        else:
            result = await self._inner.complete(messages, **params)
        self._gov.record(self._provider, result)
        return result
