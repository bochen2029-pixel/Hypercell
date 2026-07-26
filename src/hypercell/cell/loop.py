"""The one-verb executor — the kernel seam every verb passes through (contracts/nucleus.md §3).

**Why this file exists.** Before N1′ each verb wrote its own records and did its own idempotency
check. `ask()` consulted the read-barrier; `produce()` did not — so a re-issued `produce` spent a
second cognition call and appended a second outcome. That is F17, and it was invisible precisely
because the guard lived at the call site instead of at the seam.

So the guard moved here, once:

* **the read-barrier is consulted exactly once, for every verb** — a completed `idem` returns its
  stored outcome with **zero** cognition calls (NUC-9);
* **the record ladder is minted exactly once** — `action{idem}` then `outcome{idem}`, two records,
  which is the whole of `hc ask` (NUC-9; the live 5-record ceremony is E19 and is repealed);
* **d0 writes nothing** — a reflex cell has no memory by definition, so it has no ledger to write to
  and no barrier to consult.

Adding a verb means calling `execute()`. It does not mean re-implementing any of the above, which is
the point: `VERB-1` can assert that no verb bypasses this seam because there is only one seam.
"""
from __future__ import annotations

import os
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from ..common import ids
from ..common.types import Depth
from .nucleus import Nucleus


@dataclass(frozen=True)
class VerbResult:
    """What a verb produced, and whether producing it cost anything.

    `replayed=True` means the read-barrier answered and no provider was called — the caller can
    tell "we did the work" from "we already had the answer", which a bare return value cannot.
    """

    body: dict[str, Any]
    idem: str
    replayed: bool = False
    seq: int | None = None

    @property
    def text(self) -> str:
        return str(self.body.get("text", ""))


class VerbExecutor:
    """Executes one verb against one nucleus. The only place a verb becomes records."""

    def __init__(self, nucleus: Nucleus | None, depth: Depth = Depth.d1) -> None:
        self.nucleus = nucleus
        self.depth = depth

    @property
    def journaling(self) -> bool:
        """d0 is a reflex: a bare provider call with no memory, and therefore no records at all."""
        return self.depth is not Depth.d0 and self.nucleus is not None

    async def execute(
        self,
        verb: str,
        run: Callable[[], Awaitable[dict[str, Any]]],
        *,
        idem: str | None = None,
        action: dict[str, Any] | None = None,
    ) -> VerbResult:
        """Run one verb under the read-barrier and the two-record ladder.

        `run` is the side-effecting half (the provider call). It is invoked at most once per `idem`,
        ever — across processes, across crashes, across reboots.
        """
        idem = idem or ids.new_id(f"{verb}_")

        if not self.journaling:
            return VerbResult(body=await run(), idem=idem)

        assert self.nucleus is not None  # narrowed by `journaling`

        # ---- THE READ-BARRIER. Every verb, one place, before any spend.
        stored = self.nucleus.outcome_for(idem)
        if stored is not None:
            return VerbResult(body=dict(stored), idem=idem, replayed=True)

        body = {"verb": verb, **(action or {})}
        self.nucleus.append("action", body, idem=idem)

        # Drill hook (HC-2): die AFTER the action, BEFORE the outcome — the crash-mid-verb case a
        # resume has to survive. Kept at the seam so it drills every verb, not just `ask`.
        crash = os.environ.get("HYPERCELL_CRASH_BEFORE_OUTCOME")
        if crash and crash in ("1", idem, verb):
            raise SystemExit(f"drill: crashed before outcome ({verb}/{idem})")

        outcome = await run()
        # Gold: the outcome IS the exactly-once guarantee. If it is not durable before we return,
        # a crash here re-spends the call on resume -- which is the bug the barrier exists to kill.
        seq = self.nucleus.append("outcome", outcome, idem=idem, durability="gold")
        return VerbResult(body=outcome, idem=idem, seq=seq)

    def pending(self) -> list[dict[str, Any]]:
        """Actions whose outcome never landed. Empty at d0 — nothing was ever written."""
        return self.nucleus.pending() if self.journaling and self.nucleus else []
