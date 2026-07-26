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

    def record(self, provider: str, result: Any) -> float:
        """Book what a completed call cost. Returns the effective USD."""
        ...

    def semaphore(self, provider: str) -> asyncio.Semaphore | None:
        """The per-provider concurrency cap, or None when this provider is uncapped."""
        ...
