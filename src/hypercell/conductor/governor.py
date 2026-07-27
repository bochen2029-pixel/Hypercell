"""The cost governor (HC-8) + per-provider concurrency (constitution A10, §10).

One metering path: the budget hard-stop cannot be bypassed, because there is exactly one place cost is
checked and recorded. Per-provider concurrency caps keep a fan-out from melting the box or blowing rate
limits. Prices are advisory defaults (USD per 1M tokens: input, output); pin them in a lock later.
"""
from __future__ import annotations

import asyncio
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar, Literal

from ..cognition.base import CompletionResult
from .ledger import EscrowLedger
from .pricebook import Pricebook, Purpose, Quote, UnknownLane, default_pricebook

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
    #: The provider-side handle a `res:durable` leg settles against (a batch id, an async job id).
    #: Carried on the reservation and in the ledger record so a RESUME knows which provider object
    #: to reconcile -- an in-doubt batch with no handle is un-reconcilable by construction.
    batch_id: str = ""
    opened_at: float = 0.0
    ttl_s: float = 300.0

    @property
    def headroom(self) -> float:
        return max(0.0, self.worst - self.committed)

    @property
    def overshoot(self) -> float:
        """Spend beyond the quantum. Bounded by construction; measured anyway."""
        return max(0.0, self.committed - self.worst)


#: The fleet scope, which every other scope nests inside. A run cap that did not also draw down the
#: fleet would let N runs each spend the whole budget -- the shape the ECON-2 drill exists to catch.
FLEET = "fleet"


def scope_chain(scope: str) -> tuple[str, ...]:
    """Every scope a charge on `scope` must be counted against, innermost first.

    Scopes are `fleet`, `run:<id>` and `purpose:<name>`, and they NEST. A reserve on `run:a` holds
    against `run:a` and against `fleet`, because the operator's cap is a statement about total money
    and not about any single run's share of it. Flat scopes -- one cap applied independently to
    every string -- are not a weaker version of this; they are the absence of a fleet cap wearing
    its name.
    """
    return (scope,) if scope == FLEET else (scope, FLEET)


@dataclass(frozen=True)
class Admission:
    """The receipt for a group reserve: what was admitted, what was not, and why (ECON-S2).

    A group that partly fits is the interesting case. Silently admitting the part that fits would
    start work the caller believes is fully funded; silently refusing the whole would waste headroom
    that exists. So the escrow admits what fits, says so, and lets the caller decide.
    """

    admitted: list[Reservation] = field(default_factory=list)
    refused: list[tuple[str, float, str]] = field(default_factory=list)

    @property
    def whole(self) -> bool:
        return not self.refused

    @property
    def total_admitted(self) -> float:
        return sum(r.worst for r in self.admitted)


class NotReconciled(EscrowRefused):
    """A resumed escrow tried to reserve before reconciling what it inherited (ECON-L8)."""


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
        home: Path | str | None = None,
        scope_caps: dict[str, float] | None = None,
        fsync: bool = True,
    ) -> None:
        self.cap_usd = cap_usd
        self.quantum_usd = quantum_usd
        self.fleet_slots = fleet_slots
        self._now = now
        #: Per-scope ceilings. Absent an entry a scope inherits the fleet cap, which bounds it but
        #: does not carve it out -- `fleet` is always the binding one.
        self.scope_caps = dict(scope_caps or {})
        self.reservations: dict[str, Reservation] = {}
        self.records: list[dict[str, Any]] = []
        #: Interactions with the fleet-scoped escrow. ECON-LEASE-1 asserts a lease draw adds none.
        self.fleet_roundtrips = 0
        #: Concurrency. The 16-way ECON-2 drill runs real threads, and `committed <= cap` under
        #: concurrency is not a property you get from a read-then-write on a dict.
        self._lock = threading.RLock()
        self._seq = 0

        #: Durable home. Without one this is the RAM meter -- the very null ECON-L8 names -- so the
        #: in-memory mode is available but must be asked for by leaving `home` out.
        self.ledger = EscrowLedger(home, fsync=fsync) if home is not None else None
        self._needs_reconcile = False
        if self.ledger is not None:
            self._hydrate()

    # ---------------------------------------------------------------- one escrow per home

    _BY_HOME: ClassVar[dict[str, Escrow]] = {}
    _BY_HOME_LOCK: ClassVar[threading.Lock] = threading.Lock()

    @classmethod
    def for_home(cls, home: Path | str, *, cap_usd: float = 1.0, **kw: Any) -> Escrow:
        """The ONE live escrow for a home. Constructing two over one file splits the cap.

        Measured before fixing: instance B hydrated at $0.90, instance A then spent to $0.95, and
        B still enforced against $0.90 -- two tables, one file, each blind to the other's LIVE
        reservations until a restart. Jointly they can exceed the cap each believes it holds.

        Within a process this registry closes that. ACROSS processes the file is append-shared and
        durable, but live mutual visibility waits for S-KG-4's fold-hydration; until then one
        process per home is the honest deployment shape. The first opener fixes the fleet cap; a
        later caller with a different number gets the existing instance and must express its own
        limit as a SCOPE cap (drive() does exactly that).
        """
        key = str(Path(home).resolve())
        with cls._BY_HOME_LOCK:
            inst = cls._BY_HOME.get(key)
            if inst is None:
                inst = cls(cap_usd=cap_usd, home=home, **kw)
                cls._BY_HOME[key] = inst
            return inst

    # ---------------------------------------------------------------- resume (ECON-L8)

    def _hydrate(self) -> None:
        """Rebuild the reservation table from the ledger. Spend is a fold, never a counter."""
        assert self.ledger is not None
        state = self.ledger.fold()
        for rid, row in state.reservations.items():
            self.reservations[rid] = Reservation(
                resv_id=rid, scope=str(row["scope"]), cls=row["cls"], worst=float(row["worst"]),
                committed=float(row["committed"]), state=row["state"],
                lane=str(row["lane"]), holder=str(row["holder"]),
                # NOT the recorded opened_at: that was the DEAD process's time.monotonic(),
                # whose epoch is undefined across processes by spec. A TTL computed against a
                # foreign epoch can sweep instantly or never. Rebasing restarts the clock, which
                # errs toward holding a stale reservation slightly longer -- and reconcile(), not
                # the sweeper, is the resume path's real cleanup anyway.
                opened_at=self._now(), ttl_s=float(row["ttl_s"]),
                batch_id=str(row.get("batch_id", "")),
            )
        self._seq = len(self.reservations)
        # A fold that found records means this process INHERITED a budget rather than opening one.
        # Until it reconciles, it does not know what it already owes, and a reserve made in that
        # state is the L8 leak: the cap remembered, the spending forgotten.
        self._needs_reconcile = state.resumed

    @property
    def needs_reconcile(self) -> bool:
        return self._needs_reconcile

    def _record(self, kind: str, **fields: Any) -> None:
        """One write path for both homes, so the RAM list can never disagree with the file."""
        entry = {"kind": kind, **fields}
        self.records.append(entry)
        if self.ledger is not None:
            self.ledger.append(kind, **fields)  # type: ignore[arg-type]

    # ---------------------------------------------------------------- scope accounting

    def _in_scope(self, scope: str) -> list[Reservation]:
        """Every reservation that charges `scope` — including inner scopes nested inside it."""
        return [r for r in self.reservations.values() if scope in scope_chain(r.scope)]

    def cap_for(self, scope: str = FLEET) -> float:
        return self.scope_caps.get(scope, self.cap_usd)

    def reserved(self, scope: str = FLEET) -> float:
        return sum(r.headroom for r in self._in_scope(scope) if r.state == "HELD")

    def committed(self, scope: str = FLEET) -> float:
        return sum(r.committed for r in self._in_scope(scope))

    def available(self, scope: str = FLEET) -> float:
        """Headroom left in `scope` — bounded by every scope it nests inside, not just its own.

        Taking the MINIMUM is the whole nesting rule: a run with $10 of its own cap left cannot
        spend it when the fleet has $2, or the fleet cap would be advice.
        """
        return min(
            self.cap_for(s) - self.committed(s) - self.reserved(s) for s in scope_chain(scope)
        )

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
        batch_id: str = "",
    ) -> Reservation:
        """Atomic and refusing: either the whole `worst` is held, or nothing is and we raise.

        Reserving the WORST case before the call is the F6 fix. The null checked `spent >= cap`
        before a call whose price it could not know, so the last call always went over: a $0.0005
        cap stopped at $0.0006. You cannot hard-stop on a number you only learn afterwards.
        """
        with self._lock:
            if self._needs_reconcile:
                raise NotReconciled(
                    "this escrow was resumed from a ledger and has not reconciled yet. It knows its "
                    "cap and not yet its spending, and reserving in that state is the L8 leak: the "
                    "budget renews itself on every crash. Call reconcile() first."
                )
            self.fleet_roundtrips += 1
            if worst > self.available(scope):
                raise EscrowRefused(
                    f"reserve ${worst:.4f} on scope '{scope}' exceeds available "
                    f"${self.available(scope):.4f} (cap ${self.cap_for(scope):.4f}) — refused whole, "
                    "never partial"
                )
            self._seq += 1
            resv = Reservation(
                resv_id=f"rsv_{self._seq:06d}",
                scope=scope,
                cls=cls,
                worst=worst,
                lane=lane,
                holder=holder,
                opened_at=self._now(),
                ttl_s=ttl_s,
                batch_id=batch_id,
            )
            # Durable BEFORE held. A crash between the two costs a reservation that is held and
            # unused, which the sweeper reconciles; the other order costs one that was used and
            # never recorded, and nothing recovers that.
            self._record("reserve", resv_id=resv.resv_id, cls=cls, worst=worst, scope=scope,
                         lane=lane, holder=holder, opened_at=resv.opened_at, ttl_s=ttl_s,
                         batch_id=batch_id)
            self.reservations[resv.resv_id] = resv
            return resv

    def reserve_group(
        self, requests: list[tuple[str, float]], *, scope: str = FLEET,
        cls: ReservationClass = "res:sync",
    ) -> Admission:
        """Reserve several at once, admitting what fits. Returns the partial-admission receipt.

        Taken under ONE lock so the group sees a single view of the budget: a competing reserve
        interleaved halfway through would make the receipt describe a state that never existed.
        Requests are honoured in the order given -- the caller's priority, not the escrow's opinion
        of it.
        """
        admitted: list[Reservation] = []
        refused: list[tuple[str, float, str]] = []
        with self._lock:
            for name, worst in requests:
                try:
                    admitted.append(self.reserve(worst, scope=scope, cls=cls, holder=name))
                except NotReconciled:
                    raise  # not a funding refusal: the escrow does not know its own state yet
                except EscrowRefused as exc:
                    refused.append((name, worst, str(exc)))
        return Admission(admitted=admitted, refused=refused)

    def commit(self, resv_id: str, usd: float) -> Reservation:
        """Settle. Committing more than `worst` is an OVERRUN — committed anyway, and flagged."""
        with self._lock:
            resv = self.reservations[resv_id]
            if resv.cls == "res:durable":
                raise EscrowRefused(
                    f"{resv_id} is res:durable: a batch leg settles ONLY through settle_durable(), "
                    "carrying the corr of a receipted H0 reconciliation act. A bare commit here "
                    "would be the fabric asserting what the provider did without having asked it."
                )
            resv.committed += usd
            resv.state = "SETTLED"
            # In-doubt spend is REAL spend. An overrun is booked and indicts the estimator; it is
            # never quietly clamped to the reservation, which would make the ledger a wish.
            self._record("commit", resv_id=resv_id, usd=usd, overrun=resv.committed > resv.worst)
            return resv

    def settle_durable(self, resv_id: str, usd: float, *, receipt_corr: str) -> Reservation:
        """Settle a `res:durable` leg from a RECEIPTED reconciliation act (act.md §8, money twin).

        The batch leg's truth lives provider-side. The only honest way to learn it is an H0 act —
        the provider usage/batch query — which is gated, journaled and receipted like any act. The
        receipt's corr rides in the ledger record, so an auditor can walk from the settlement to
        the evidence that justified it. No corr, no settlement: an unreceipted number here would be
        actor self-report wearing an accountant's hat.
        """
        if not receipt_corr:
            raise EscrowRefused(
                "a res:durable settles only from a receipted reconciliation act; without the "
                "receipt corr the settlement would be an assertion, not an observation"
            )
        with self._lock:
            resv = self.reservations[resv_id]
            if resv.cls != "res:durable":
                raise EscrowRefused(f"{resv_id} is {resv.cls}; settle_durable is the batch-leg path")
            resv.committed += usd
            resv.state = "SETTLED"
            self._record("commit", resv_id=resv_id, usd=usd, receipt_corr=receipt_corr,
                         overrun=resv.committed > resv.worst)
            return resv

    def release(self, resv_id: str, reason: str) -> Reservation:
        with self._lock:
            resv = self.reservations[resv_id]
            resv.state = "RELEASED"
            self._record("release", resv_id=resv_id, reason=reason)
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
        with self._lock:
            resv = self.reservations[resv_id]
            if resv.cls != "res:lease":
                raise EscrowRefused(f"{resv_id} is {resv.cls}; only a res:lease is self-metered")
            resv.committed += usd
            self._record("draw", resv_id=resv_id, usd=usd)
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
        # Clear the gate FIRST: the settling below reserves nothing, but `commit`/`release` run
        # through the same object and a resumed escrow must be able to finish its own recovery.
        self._needs_reconcile = False
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
            self._record("sweep", resv_id=resv.resv_id, action="reconcile")
        return stale


class Governor:
    def __init__(
        self,
        usd_cap: float = 1.0,
        per_provider_concurrency: dict[str, int] | None = None,
        *,
        pricebook: Pricebook | None = None,
        escrow: Escrow | None = None,
        scope: str = FLEET,
    ) -> None:
        self.usd_cap = usd_cap
        #: The durable, fleet-scoped budget. Without one the cap is a RAM counter that forgets its
        #: spending on every restart while remembering its ceiling -- the L8 leak, in the generous
        #: direction. `drive()` and the commander both supply one now.
        self.escrow = escrow
        self.scope = scope
        self._spent_ram = 0.0
        self.spend_records: list[dict[str, Any]] = []
        self._book = pricebook or default_pricebook()
        self._sems: dict[str, asyncio.Semaphore] = {
            p: asyncio.Semaphore(n) for p, n in (per_provider_concurrency or {}).items()
        }

    @property
    def book(self) -> Pricebook:
        """The dated pricebook — the quote plane's read seam (ECON-S3). Read-only by convention."""
        return self._book

    @property
    def spent(self) -> float:
        """Spend as a FOLD, never a counter (S-KG-4; the F16/G5 fix).

        With an escrow this reads the durable fold: `committed(scope)`, rebuilt from the escrow
        ledger on construction — so a freshly-built Governor over a resumed home already KNOWS what
        the dead process spent. The null was `self.spent = 0.0` + `+=`: a number that remembered
        its ceiling and forgot its history on every restart, which is how a cap renews itself on
        every crash. Without an escrow (bare tests only) it falls back to the RAM sum, which is the
        null, kept only so the no-escrow mode stays honest about what it is.
        """
        if self.escrow is not None:
            return self.escrow.committed(self.scope)
        return self._spent_ram

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
        """The hard-stop: raise BEFORE spending once the cap is reached.

        Kept, and no longer the only guard. On its own this is F6: it can only compare what has
        already been spent, so it lets through a call it cannot price and discovers the overshoot
        afterwards. `open_call` is what makes the stop exact.
        """
        spent = self.escrow.committed(self.scope) if self.escrow is not None else self.spent
        cap = self.escrow.cap_for(self.scope) if self.escrow is not None else self.usd_cap
        if spent >= cap:
            raise BudgetExceeded(f"budget hard-stop: spent ${spent:.4f} >= cap ${cap:.4f}")

    # ---------------------------------------------------------------- reserve-before-call (F6)

    def worst_case_usd(self, params: dict[str, Any]) -> float:
        """The pessimistic ceiling for one call, priced off the dated book.

        Deliberately pessimistic: it assumes the model emits `max_tokens`; the prompt estimate is
        the caller's, and the metered path supplies a chars/4 floor when none is given. An
        estimate that errs LOW would still reintroduce the
        overshoot it exists to prevent, and an over-reservation costs only headroom that is
        released seconds later. N4' sharpens this with `est_tokens_total` from the frame manifest.
        """
        max_out = int(params.get("max_tokens") or params.get("max_output_tokens") or 4096)
        est_in = int(params.get("est_prompt_tokens") or 8192)
        sku = Pricebook.sku_key(str(params.get("model", "")), str(params.get("provider", "")))
        row = self._book.skus.get(sku)
        if row is None:
            # No priced row: reserve the whole remaining headroom rather than guess a number. An
            # unknown price is not a cheap price (the deleted `_PRICE` fallback taught us that).
            # This is deliberately crippling -- one such call fills the budget -- because a fabric
            # that cannot price a lane should stop, not proceed at a number it made up.
            return max(0.0, self.escrow.cap_for(self.scope) if self.escrow else self.usd_cap)
        return est_in / 1e6 * float(row["input"]) + max_out / 1e6 * float(row["output"])

    def open_call(self, provider: str, params: dict[str, Any]) -> str | None:
        """Hold the worst case before the call. Raises `BudgetExceeded` when it will not fit."""
        self.check()
        if self.escrow is None:
            return None
        worst = self.worst_case_usd({**params, "provider": provider})
        try:
            return self.escrow.reserve(worst, scope=self.scope, cls="res:sync").resv_id
        except EscrowRefused as exc:
            raise BudgetExceeded(
                f"the worst case for this call (${worst:.4f}) does not fit the remaining headroom "
                f"(${self.escrow.available(self.scope):.4f}). Refused BEFORE the call, which is the "
                f"whole difference from the null: {exc}"
            ) from exc

    def close_call(self, resv_id: str | None, provider: str, result: Any) -> float:
        """Settle at the truth. The held remainder goes straight back to the scope."""
        if result is None:
            # The call never answered. Release rather than commit: holding headroom for work that
            # produced nothing starves the run, and booking a cost for it would be a lie.
            if resv_id is not None and self.escrow is not None:
                self.escrow.release(resv_id, "call did not complete")
            return 0.0
        try:
            usd = self.record(provider, result)
        except UnknownLane:
            # The call HAPPENED and cannot be priced. In-doubt spend is real spend: settle the
            # reservation at its worst case -- never release, never guess low -- then re-raise so
            # the unpriceable lane stays loud (it is deliberately crippling; see worst_case_usd).
            # Releasing here would leak real spend out of the cap; swallowing would hide the lane.
            if resv_id is not None and self.escrow is not None:
                self.escrow.commit(resv_id, self.escrow.reservations[resv_id].worst)
            raise
        if resv_id is not None and self.escrow is not None:
            self.escrow.commit(resv_id, usd)
        return usd

    def record(self, provider: str, result: CompletionResult, *, purpose: Purpose = "production") -> float:
        """Book the spend and keep the SPEND record. The fold, not a RAM counter, is the truth."""
        quote = self.quote(provider, result)
        self._spent_ram += quote.usd_effective
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
        # The cache hit-rate is the `hc top` number ECON-CACHE-1 bars at >=60% (ARCH §7): a fold
        # over the per-call token records, using the canonical `read/(input+read+write)` formula so
        # a lane that paid huge writes cannot look thrifty. A low rate indicts frame ORDERING first.
        from .cache import canonical_hit_rate

        tok_in = sum(int(r["tokens"]["prompt"]) for r in self.spend_records)
        tok_read = sum(int(r["tokens"]["cache_read"]) for r in self.spend_records)
        tok_write = sum(int(r["tokens"]["cache_write"]) for r in self.spend_records)
        fold: dict[str, Any] = {
            "usd_effective": total,
            "usd_reserved": reserved,
            "calls": len(self.spend_records),
            "pricebook_version": self._book.version,
            "cache_hit_rate": canonical_hit_rate(
                input_tokens=tok_in, cache_read_tokens=tok_read, cache_write_tokens=tok_write
            ),
        }
        if self.escrow is not None:
            # The DURABLE side of the two-log agreement RE-4 will certify: span cost{} sums on one
            # side, this escrow-ledger fold on the other. Carried here so `hc top`-class surfaces
            # can already show both numbers next to each other.
            fold["escrow_committed_usd"] = self.escrow.committed(self.scope)
        return fold

    def semaphore(self, provider: str) -> asyncio.Semaphore | None:
        return self._sems.get(provider)


# `MeteredCognition` lives in `cognition/metered.py` since S-KG-3: it is a Cognition wrapper, so it
# belongs in the cognition stratum, and keeping it here made the metering seam import L3 -- a
# forbidden edge LAYER-1 caught. `Governor` satisfies `common.meter.Meter` structurally, with no
# inheritance and no registration; callers import the seam directly, so ONE-METER-1 can see them.
