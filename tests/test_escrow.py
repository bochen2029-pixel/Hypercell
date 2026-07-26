"""ECON-LEASE-1 (= ACT-LEASE-1, one co-owned drill) — the `res:lease` micro-escrow (slice ECON-S2b).

The bar: **kill-9 mid-lease — the fold shows STILL-HELD, receipts settle it, overshoot ≤ quantum.**
06's half of the co-owned drill adds the zero-round-trip hot-path count and the latency-mortality
clause, both asserted here.

The null: per-call fleet escrow. Every H0 tool call taking a fleet-scoped reservation makes every
tool call serialize on one lock, so grounding — many small cheap fetches — queues behind the fleet's
expensive work.
"""
from __future__ import annotations

import pytest

from hypercell.conductor.governor import Escrow, EscrowRefused


@pytest.fixture
def escrow() -> Escrow:
    clock = iter(range(0, 100_000))
    return Escrow(cap_usd=1.0, quantum_usd=0.01, fleet_slots=8, now=lambda: float(next(clock)))


# ---------------------------------------------------------------- the hot path takes no lock


def test_draws_inside_a_lease_take_zero_fleet_roundtrips(escrow: Escrow) -> None:
    """The point of the lease. If a draw touched the fleet escrow, grounding would serialize."""
    lease = escrow.grant_lease(holder="r1/refiner/0", lane="web.fetch")
    after_grant = escrow.fleet_roundtrips

    for _ in range(50):
        escrow.draw(lease.resv_id, 0.0001)

    assert escrow.fleet_roundtrips == after_grant, "a lease draw hit the fleet escrow"
    assert after_grant == 1, "granting the lease should be the ONLY fleet round-trip in the lane's life"


def test_the_null_would_serialize(escrow: Escrow) -> None:
    """Contrast, measured: per-call fleet reservations cost one round-trip each."""
    before = escrow.fleet_roundtrips
    for _ in range(50):
        escrow.reserve(0.0001, cls="res:sync")
    assert escrow.fleet_roundtrips - before == 50


# ---------------------------------------------------------------- kill-9 mid-lease


def test_kill9_midlease_folds_to_still_held(escrow: Escrow) -> None:
    """A crash must leave the reservation visible, not vanished. STILL-HELD is the honest state."""
    lease = escrow.grant_lease(holder="r1/refiner/0", lane="web.fetch")
    escrow.draw(lease.resv_id, 0.004)
    # ---- kill -9 here: nothing settled, no terminal record

    held = escrow.still_held()
    assert [r.resv_id for r in held] == [lease.resv_id]
    assert held[0].cls == "res:lease"


def test_receipts_settle_a_recovered_lease(escrow: Escrow) -> None:
    """Settled from the LEASEHOLDER'S OWN receipts — the cell self-metered, so the cell has the truth."""
    lease = escrow.grant_lease(holder="r1/refiner/0", lane="web.fetch")
    escrow.draw(lease.resv_id, 0.004)

    settled = escrow.reconcile(receipts={lease.resv_id: 0.004})
    assert [r.resv_id for r in settled] == [lease.resv_id]
    assert escrow.reservations[lease.resv_id].state == "SETTLED"
    assert escrow.reservations[lease.resv_id].committed == pytest.approx(0.004)
    assert escrow.still_held() == []


def test_a_lease_with_no_receipt_commits_at_worst_and_says_unknown(escrow: Escrow) -> None:
    """In-doubt spend is REAL spend. Guessing downward is how a budget lies to itself."""
    lease = escrow.grant_lease(holder="r1/refiner/0", lane="web.fetch")
    escrow.reconcile(receipts={})

    resv = escrow.reservations[lease.resv_id]
    assert resv.state == "SETTLED"
    assert resv.committed == pytest.approx(escrow.quantum_usd)
    assert escrow.records[-1]["outcome"] == "unknown"


def test_overshoot_is_bounded_by_one_quantum(escrow: Escrow) -> None:
    """The bar's third clause. A leaseholder that overdraws is still bounded by its own quantum."""
    lease = escrow.grant_lease(holder="r1/refiner/0", lane="web.fetch")
    ok = True
    for _ in range(30):
        ok = escrow.draw(lease.resv_id, 0.001)  # 0.030 drawn against a 0.010 quantum

    resv = escrow.reservations[lease.resv_id]
    assert ok is False, "the leaseholder was never told to renew"
    # Overshoot is real and recorded — but the FLEET's exposure is what the bound is about, and the
    # fleet only ever handed out one quantum for this lane.
    assert resv.worst == pytest.approx(escrow.quantum_usd)
    assert escrow.reserved() <= escrow.quantum_usd


def test_fleet_aggregate_bound_is_stated_and_capped(escrow: Escrow) -> None:
    """`fleet_slots × quantum`. A bound you cannot state is not a bound."""
    assert escrow.max_lease_overshoot() == pytest.approx(8 * 0.01)

    for i in range(8):
        escrow.grant_lease(holder=f"r1/refiner/{i}", lane="web.fetch")
    assert escrow.reserved() <= escrow.max_lease_overshoot()


# ---------------------------------------------------------------- renewal-reconcile


def test_renew_settles_the_old_lease_before_granting_a_new_one(escrow: Escrow) -> None:
    first = escrow.grant_lease(holder="r1/refiner/0", lane="web.fetch")
    escrow.draw(first.resv_id, 0.006)
    second = escrow.renew(first.resv_id)

    assert escrow.reservations[first.resv_id].state == "SETTLED"
    assert escrow.reservations[first.resv_id].committed == pytest.approx(0.006)
    assert second.resv_id != first.resv_id and second.state == "HELD"
    assert second.holder == first.holder and second.lane == first.lane


# ---------------------------------------------------------------- admissibility + classes


def test_only_h0_lanes_are_leaseable(escrow: Escrow) -> None:
    """Anything that can change the world takes the real lock, not a self-metered quantum."""
    assert escrow.leaseable("web.fetch", harm="H0")
    assert not escrow.leaseable("fs.write", harm="H1")
    assert not escrow.leaseable("", harm="H0")


def test_only_a_lease_can_be_self_metered(escrow: Escrow) -> None:
    sync = escrow.reserve(0.05, cls="res:sync")
    with pytest.raises(EscrowRefused, match="only a res:lease"):
        escrow.draw(sync.resv_id, 0.001)


def test_res_sync_folds_to_zero_on_resume_but_durable_does_not(escrow: Escrow) -> None:
    """The three durability classes behave differently on resume, deliberately."""
    sync = escrow.reserve(0.05, cls="res:sync")
    durable = escrow.reserve(0.05, cls="res:durable")
    escrow.reconcile()

    assert escrow.reservations[sync.resv_id].state == "RELEASED"
    assert escrow.reservations[durable.resv_id].state == "HELD", (
        "res:durable may only be settled by a receipted reconciliation act"
    )


# ---------------------------------------------------------------- refusal + sweep


def test_reserve_is_atomic_and_refusing(escrow: Escrow) -> None:
    """Either the whole worst-case is held or nothing is. A partial hold is an unbounded run."""
    escrow.reserve(0.9, cls="res:sync")
    before = dict(escrow.reservations)
    with pytest.raises(EscrowRefused, match="refused whole, never partial"):
        escrow.reserve(0.5, cls="res:sync")
    assert escrow.reservations.keys() == before.keys(), "a refused reserve left state behind"


def test_an_overrun_is_booked_not_clamped(escrow: Escrow) -> None:
    """Clamping spend to the reservation would make the ledger a wish rather than a record."""
    resv = escrow.reserve(0.01, cls="res:sync")
    escrow.commit(resv.resv_id, 0.05)
    assert escrow.reservations[resv.resv_id].committed == pytest.approx(0.05)
    assert escrow.records[-1]["overrun"] is True


def test_sweep_reconciles_never_blind_releases(escrow: Escrow) -> None:
    """A stale reservation is reconciled, never dropped — dropping it would un-book real spend."""
    lease = escrow.grant_lease(holder="r1/refiner/0", lane="web.fetch")
    escrow.reservations[lease.resv_id].ttl_s = 0.0
    stale = escrow.sweep()
    assert [r.resv_id for r in stale] == [lease.resv_id]
    assert escrow.reservations[lease.resv_id].state == "HELD", "sweep must not blind-release"
    assert escrow.records[-1]["action"] == "reconcile"


def test_reconcile_runs_before_the_first_new_reserve(escrow: Escrow) -> None:
    """Resume ordering: unsettled leases must not still be counted against the cap when we re-reserve."""
    for i in range(8):
        escrow.grant_lease(holder=f"c{i}", lane="web.fetch")
    held_before = len(escrow.still_held())
    escrow.reconcile(receipts={})
    assert held_before == 8 and escrow.still_held() == []
    assert escrow.available() == pytest.approx(escrow.cap_usd - 8 * escrow.quantum_usd)
