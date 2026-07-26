from __future__ import annotations

from typing import Any

import pytest

from hypercell.cognition.base import Cognition, CompletionResult, Messages
from hypercell.conductor.governor import BudgetExceeded, Governor, MeteredCognition


class BigCostStub(Cognition):
    def __init__(self) -> None:
        self.name = "big"
        self.calls = 0

    async def complete(self, messages: Messages, **params: Any) -> CompletionResult:
        self.calls += 1
        return CompletionResult(
            text="x", model="deepseek-chat", prompt_tokens=1_000_000, completion_tokens=1_000_000
        )


async def test_budget_hard_stop() -> None:
    # HC-8: once the cap is reached, the next call raises BEFORE it reaches the model.
    gov = Governor(usd_cap=0.001)
    inner = BigCostStub()
    metered = MeteredCognition(inner, "deepseek", gov)
    await metered.complete([])  # spends far past the tiny cap
    assert inner.calls == 1
    assert gov.spent > gov.usd_cap
    with pytest.raises(BudgetExceeded):
        await metered.complete([])
    assert inner.calls == 1  # the hard-stop kept the second call from ever running


def test_price_zero_for_free_tiers() -> None:
    """ECON-S1 renamed price() -> quote(): the answer is now a dated Quote, not a bare float."""
    gov = Governor()
    free = CompletionResult(text="x", model="mock", prompt_tokens=1000, completion_tokens=1000)
    paid = CompletionResult(text="x", model="deepseek-chat", prompt_tokens=1000, completion_tokens=1000)
    assert gov.quote("mock", free).usd_effective == 0.0
    assert gov.quote("deepseek", paid).usd_effective > 0.0


def test_concurrency_semaphore_present_only_when_configured() -> None:
    gov = Governor(per_provider_concurrency={"deepseek": 2})
    assert gov.semaphore("deepseek") is not None
    assert gov.semaphore("cerebras") is None
