"""The `Meter` protocol — what the metering seam needs, without knowing who provides it.

`cognition/metered.py` must enforce the budget hard-stop, but it is a **stratum** and the Governor
lives at L3. Under LAYER-1 clause C1 a stratum imports nothing but `common`, so an import of
`conductor` there is a forbidden edge — LAYER-1 caught exactly that.

The fix is the one the layer law anticipates by describing `common/` as "types, ids, clock,
**protocol interfaces**": the seam depends on the *shape* of a meter, and the Conductor's `Governor`
satisfies that shape structurally. No inheritance, no registration — just a protocol, which is what
lets a lower stratum call upward-provided behaviour without knowing the layer above exists.
"""
from __future__ import annotations

import asyncio
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Meter(Protocol):
    """The budget hard-stop, the per-provider concurrency cap, and the spend record."""

    def check(self) -> None:
        """Raise BEFORE any spend once the cap is reached. The hard-stop that cannot be bypassed."""
        ...

    def open_call(self, provider: str, params: dict[str, Any]) -> str | None:
        """RESERVE the worst case before the call. Returns a reservation id, or None if unfunded.

        This is the half `check()` cannot do. `check()` compares a counter against a cap *before* a
        call whose price it does not yet know, so the last call always goes over -- F6 measured it
        as $0.0006 against a $0.0005 cap. You cannot hard-stop on a number you learn afterwards, so
        the escrow holds the pessimistic ceiling first and settles the truth after.
        """
        ...

    def close_call(self, resv_id: str | None, provider: str, result: Any) -> float:
        """Settle the reservation at what actually happened and book the spend."""
        ...

    def record(self, provider: str, result: Any) -> float:
        """Book what a completed call cost. Returns the effective USD."""
        ...

    def semaphore(self, provider: str) -> asyncio.Semaphore | None:
        """The per-provider concurrency cap, or None when this provider is uncapped."""
        ...
