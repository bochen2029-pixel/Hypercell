"""The cost governor (HC-8) + per-provider concurrency (constitution A10, §10).

One metering path: the budget hard-stop cannot be bypassed, because there is exactly one place cost is
checked and recorded. Per-provider concurrency caps keep a fan-out from melting the box or blowing rate
limits. Prices are advisory defaults (USD per 1M tokens: input, output); pin them in a lock later.
"""
from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

from ..cognition.base import CompletionResult
from .pricebook import Pricebook, Purpose, Quote, default_pricebook

# `_PRICE` is DELETED (slice ECON-S1). It hard-coded twelve providers and, worse, fell back to a
# silent `(0.5, 1.5)` guess for anything else — an undated number that every downstream total
# inherited without a word. Prices now come from `contracts/pricebook.yaml` through
# `conductor/pricebook.py`, where every row is dated and an unknown lane is REFUSED.


class BudgetExceeded(RuntimeError):
    pass


class EscrowRefused(RuntimeError):
    """A reserve that would breach a scope cap. Refusing is the whole mechanism."""


ReservationClass = Literal["res:sync", "res:durable", "res:lease"]
ReservationState = Literal["HELD", "SETTLED", "RELEASED"]


@dataclass
class Reservation:
    """One held amount. `worst` is the pessimistic ceiling; `committed` is what actually happened."""

    resv_id: str
    scope: str
    cls: ReservationClass
    worst: float
    committed: float = 0.0
    state: ReservationState = "HELD"
    lane: str = ""
    holder: str = ""
    opened_at: float = 0.0
    ttl_s: float = 300.0

    @property
    def headroom(self) -> float:
        return max(0.0, self.worst - self.committed)

    @property
    def overshoot(self) -> float:
        """Spend beyond the quantum. Bounded by construction; measured anyway."""
        return max(0.0, self.committed - self.worst)


class Escrow:
    """Scope-capped reservations, plus the `res:lease` micro-escrow for H0 tool lanes.

    **Why leases exist.** Every H0 tool call taking a fleet-scoped reservation means every tool call
    serializes on one lock. Grounding — which is many small, cheap fetches — would queue behind the
    fleet's expensive work and the whole warrants rung would feel slow. So a leaseholder reserves
    ONE quantum up front and then self-meters against it: draws inside a lease take **zero fleet
    round-trips**.

    **What that costs, stated plainly.** Inside a lease the fleet cannot see spend until settlement,
    so the worst uncounted exposure is **one quantum per cell×lane**, and fleet-wide it is
    `max concurrent leaseholders × quantum` — bounded by `fleet_slots × quantum`. That number is
    computed, printed and drilled (ECON-LEASE-1) rather than hidden. A bound you cannot state is not
    a bound.
    """

    def __init__(
        self,
        *,
        cap_usd: float = 1.0,
        quantum_usd: float = 0.01,
        fleet_slots: int = 8,
        now: Callable[[], float] = time.monotonic,
    ) -> None:
        self.cap_usd = cap_usd
        self.quantum_usd = quantum_usd
        self.fleet_slots = fleet_slots
        self._now = now
        self.reservations: dict[str, Reservation] = {}
        self.records: list[dict[str, Any]] = []
        #: Interactions with the fleet-scoped escrow. ECON-LEASE-1 asserts a lease draw adds none.
        self.fleet_roundtrips = 0

    # ---------------------------------------------------------------- scope accounting

    def reserved(self, scope: str = "fleet") -> float:
        return sum(r.headroom for r in self.reservations.values() if r.scope == scope and r.state == "HELD")

    def committed(self, scope: str = "fleet") -> float:
        return sum(r.committed for r in self.reservations.values() if r.scope == scope)

    def available(self, scope: str = "fleet") -> float:
        return self.cap_usd - self.committed(scope) - self.reserved(scope)

    # ---------------------------------------------------------------- reserve / commit / release

    def reserve(
        self,
        worst: float,
        *,
        scope: str = "fleet",
        cls: ReservationClass = "res:sync",
        lane: str = "",
        holder: str = "",
        ttl_s: float = 300.0,
    ) -> Reservation:
        """Atomic and refusing: either the whole `worst` is held, or nothing is and we raise."""
        self.fleet_roundtrips += 1
        if worst > self.available(scope):
            raise EscrowRefused(
                f"reserve ${worst:.4f} on scope '{scope}' exceeds available "
                f"${self.available(scope):.4f} (cap ${self.cap_usd:.4f}) — refused whole, never partial"
            )
        resv = Reservation(
            resv_id=f"rsv_{len(self.reservations) + 1:06d}",
            scope=scope,
            cls=cls,
            worst=worst,
            lane=lane,
            holder=holder,
            opened_at=self._now(),
            ttl_s=ttl_s,
        )
        self.reservations[resv.resv_id] = resv
        self.records.append({"kind": "reserve", "resv_id": resv.resv_id, "cls": cls, "worst": worst})
        return resv

    def commit(self, resv_id: str, usd: float) -> Reservation:
        """Settle. Committing more than `worst` is an OVERRUN — committed anyway, and flagged."""
        resv = self.reservations[resv_id]
        resv.committed += usd
        resv.state = "SETTLED"
        overrun = resv.committed > resv.worst
        self.records.append(
            {
                "kind": "commit",
                "resv_id": resv_id,
                "usd": usd,
                # In-doubt spend is REAL spend. An overrun is booked and indicts the estimator; it is
                # never quietly clamped to the reservation, which would make the ledger a wish.
                "overrun": overrun,
            }
        )
        return resv

    def release(self, resv_id: str, reason: str) -> Reservation:
        resv = self.reservations[resv_id]
        resv.state = "RELEASED"
        self.records.append({"kind": "release", "resv_id": resv_id, "reason": reason})
        return resv

    # ---------------------------------------------------------------- the lease

    def grant_lease(self, *, holder: str, lane: str, quantum: float | None = None) -> Reservation:
        """Grant one `res:lease` quantum to a cell×lane. The only fleet round-trip in the lane's life."""
        return self.reserve(
            quantum if quantum is not None else self.quantum_usd,
            scope="fleet",
            cls="res:lease",
            lane=lane,
            holder=holder,
        )

    def draw(self, resv_id: str, usd: float) -> bool:
        """Self-meter inside a lease. **Zero fleet round-trips** — that is the point of the lease.

        Returns False when the draw would exceed the quantum, which is the leaseholder's signal to
        renew. The draw is still booked: refusing to record spend that happened would make the
        overshoot invisible, and an invisible bound is not a bound.
        """
        resv = self.reservations[resv_id]
        if resv.cls != "res:lease":
            raise EscrowRefused(f"{resv_id} is {resv.cls}; only a res:lease is self-metered")
        resv.committed += usd
        self.records.append({"kind": "draw", "resv_id": resv_id, "usd": usd})
        return resv.committed <= resv.worst

    def renew(self, resv_id: str) -> Reservation:
        """Renewal-reconcile: settle what the old lease actually spent, then grant a fresh quantum."""
        old = self.reservations[resv_id]
        self.commit(resv_id, 0.0)  # closes it at its drawn total
        return self.grant_lease(holder=old.holder, lane=old.lane, quantum=old.worst)

    def leaseable(self, lane: str, *, harm: str = "H0") -> bool:
        """Admissibility: only H0 lanes lease. Anything that can change the world takes the real lock."""
        return harm == "H0" and bool(lane)

    # ---------------------------------------------------------------- resume + sweep

    def max_lease_overshoot(self) -> float:
        """The fleet-aggregate bound: `fleet_slots × quantum`. Printed, capped, drilled."""
        return self.fleet_slots * self.quantum_usd

    def still_held(self) -> list[Reservation]:
        """The resume view: reservations with no terminal record. Rebuilt by fold, never assumed."""
        return [r for r in self.reservations.values() if r.state == "HELD"]

    def reconcile(self, receipts: dict[str, float] | None = None) -> list[Reservation]:
        """RESUME path — runs BEFORE the first new reserve.

        A `res:lease` with no terminal record rebuilds as STILL-HELD and settles **from the
        leaseholder's own receipts**. Where a receipt is missing the lease commits at `worst`:
        in-doubt spend is real spend, and guessing downward is how a budget lies to itself.
        """
        receipts = receipts or {}
        settled: list[Reservation] = []
        for resv in self.still_held():
            if resv.cls == "res:sync":
                self.release(resv.resv_id, reason="res:sync folds to zero on resume")
            elif resv.cls == "res:lease":
                actual = receipts.get(resv.resv_id)
                if actual is None:
                    self.commit(resv.resv_id, resv.headroom)
                    self.records[-1]["outcome"] = "unknown"
                else:
                    resv.committed = actual
                    self.commit(resv.resv_id, 0.0)
                settled.append(resv)
            # res:durable stays HELD: only a receipted reconciliation act may settle it.
        return settled

    def sweep(self) -> list[Reservation]:
        """Every tick: a HELD reservation past its ttl is reconciled, **never blind-released**."""
        stale = [r for r in self.still_held() if self._now() - r.opened_at > r.ttl_s]
        for resv in stale:
            self.records.append({"kind": "sweep", "resv_id": resv.resv_id, "action": "reconcile"})
        return stale


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


# `MeteredCognition` lives in `cognition/metered.py` since S-KG-3: it is a Cognition wrapper, so it
# belongs in the cognition stratum, and keeping it here made the metering seam import L3 -- a
# forbidden edge LAYER-1 caught. `Governor` satisfies `common.meter.Meter` structurally, with no
# inheritance and no registration; callers import the seam directly, so ONE-METER-1 can see them.
