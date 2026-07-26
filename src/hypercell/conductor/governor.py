"""The cost governor (HC-8) + per-provider concurrency (constitution A10, §10).

One metering path: the budget hard-stop cannot be bypassed, because there is exactly one place cost is
checked and recorded. Per-provider concurrency caps keep a fan-out from melting the box or blowing rate
limits. Prices are advisory defaults (USD per 1M tokens: input, output); pin them in a lock later.
"""
from __future__ import annotations

import asyncio
from typing import Any

from ..cognition.base import Cognition, CompletionResult, Messages
from .pricebook import Pricebook, Purpose, Quote, default_pricebook

# `_PRICE` is DELETED (slice ECON-S1). It hard-coded twelve providers and, worse, fell back to a
# silent `(0.5, 1.5)` guess for anything else — an undated number that every downstream total
# inherited without a word. Prices now come from `contracts/pricebook.yaml` through
# `conductor/pricebook.py`, where every row is dated and an unknown lane is REFUSED.


class BudgetExceeded(RuntimeError):
    pass


class Governor:
    def __init__(
        self,
        usd_cap: float = 1.0,
        per_provider_concurrency: dict[str, int] | None = None,
        *,
        pricebook: Pricebook | None = None,
    ) -> None:
        self.usd_cap = usd_cap
        self.spent = 0.0
        self.spend_records: list[dict[str, Any]] = []
        self._book = pricebook or default_pricebook()
        self._sems: dict[str, asyncio.Semaphore] = {
            p: asyncio.Semaphore(n) for p, n in (per_provider_concurrency or {}).items()
        }

    def quote(self, provider: str, result: CompletionResult) -> Quote:
        """Price one completion off the dated book. Raises `UnknownLane` rather than guessing."""
        return self._book.quote(
            model=result.model,
            provider=provider,
            prompt_tokens=result.prompt_tokens,
            completion_tokens=result.completion_tokens,
            cache_read_tokens=result.cache_read_tokens,
            cache_write_tokens=result.cache_write_tokens,
            api_reported_usd=result.api_reported_usd,
        )

    def check(self) -> None:
        """The hard-stop: raise BEFORE spending once the cap is reached."""
        if self.spent >= self.usd_cap:
            raise BudgetExceeded(
                f"budget hard-stop: spent ${self.spent:.4f} >= cap ${self.usd_cap:.4f}"
            )

    def record(self, provider: str, result: CompletionResult, *, purpose: Purpose = "production") -> float:
        """Book the spend and keep the SPEND record. The fold, not a RAM counter, is the truth."""
        quote = self.quote(provider, result)
        self.spent += quote.usd_effective
        self.spend_records.append(
            {
                "kind": "spend",
                "cost": quote.cost_group(purpose=purpose),
                # Siblings, never cost{} members (R16): measurement is not money.
                "tokens": {
                    "prompt": result.prompt_tokens,
                    "completion": result.completion_tokens,
                    "cache_read": result.cache_read_tokens,
                    "cache_write": result.cache_write_tokens,
                },
                "stale_price": quote.stale,
                "price_age_days": quote.age_days,
            }
        )
        return quote.usd_effective

    def spend_fold(self) -> dict[str, Any]:
        """Σ over the SPEND records. Equals `self.spent` — the counter is a cache of this, not a source."""
        total = sum(float(r["cost"]["usd_effective"]) for r in self.spend_records)
        reserved = sum(float(r["cost"]["usd_reserved"]) for r in self.spend_records)
        return {
            "usd_effective": total,
            "usd_reserved": reserved,
            "calls": len(self.spend_records),
            "pricebook_version": self._book.version,
        }

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
        cost = self._gov.record(self._provider, result)
        # F26 closed: `cost_usd` was declared in v1 and never populated. The receipt now carries a
        # real number, priced off a dated book.
        return result.model_copy(update={"cost_usd": cost})
