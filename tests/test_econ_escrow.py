"""ECON-2 / ECON-L8 — the fleet escrow (slice ECON-S2).

**ECON-2** — reserve/commit/release/reconcile. Null: the live per-run RAM `Governor`. The bar: a
16-concurrent overshoot drill with `committed ≤ cap` **in every trial, every scope**, under
crash / 429 / batch-cancel injection; and **the F6 replay stops at $0.0004–0.0005**.

**ECON-L8** — reconcile-before-first-reserve on resume. Null: RAM-held `committed`, the live leak.
The bar: crash + resume mid-run refuses past remaining headroom.

F6 is the measurement this rung exists for: a live budget hard-stop tripped at **$0.0006 against a
$0.0005 cap** — a one-call overshoot. The cause is structural, not a rounding slip. `check()`
compares a counter to a cap *before* a call whose price it cannot know, so the last call always goes
over and the "hard stop" reports a breach it failed to prevent. You cannot hard-stop on a number you
only learn afterwards.
"""
from __future__ import annotations

import concurrent.futures
import random
from pathlib import Path
from typing import Any

import pytest

from hypercell.conductor.governor import (
    FLEET,
    BudgetExceeded,
    Escrow,
    EscrowRefused,
    Governor,
    NotReconciled,
    scope_chain,
)
from hypercell.conductor.ledger import EscrowLedger

CAP = 1.0


def _escrow(home: Path | None = None, **kw: Any) -> Escrow:
    return Escrow(cap_usd=kw.pop("cap_usd", CAP), home=home, fsync=False, **kw)


# ================================================================ the null, measured


def test_the_null_overshoots_because_it_prices_after_the_call() -> None:
    """F6, replayed on the null's own logic: a $0.0005 cap, six steps, and a $0.0006 stop.

    Nothing here is a bug in the arithmetic. The counter is right, the comparison is right, and the
    overshoot is guaranteed anyway — because the only moment the null can act is before it knows
    the price.
    """
    cap = 0.0005
    # Six steps. Five small ones leave $0.0001 of headroom; the sixth is a bigger call, and its
    # size is exactly the thing the null cannot know before admitting it.
    costs = [0.00008] * 5 + [0.0002]

    spent = 0.0
    calls = 0
    for cost in costs:
        if spent >= cap:  # the null's hard-stop, in full
            break
        spent += cost  # ...and only now does it learn what that call cost
        calls += 1

    assert calls == 6, f"the F6 replay is 6 steps; got {calls}"
    assert round(spent, 8) == 0.0006, f"the F6 replay lands on $0.0006; got ${round(spent, 8)}"
    assert spent > cap, "the null exceeded its cap, which is F6 exactly"
    assert round(spent - cap, 8) == 0.0001, "the overshoot is the un-priced remainder of one call"


def test_the_escrow_stops_the_same_replay_inside_the_cap() -> None:
    """The bar: $0.0004–0.0005. Reserving the worst case first is the whole difference."""
    cap = 0.0005
    costs = [0.00008] * 5 + [0.0002]
    escrow = _escrow(cap_usd=cap)

    spent = 0.0
    for cost in costs:
        try:
            # The worst case is held FIRST. The sixth call's $0.0002 does not fit the $0.0001 left,
            # so it is refused before it happens rather than reported after.
            resv = escrow.reserve(cost, scope=FLEET)
        except EscrowRefused:
            break
        escrow.commit(resv.resv_id, cost)
        spent += cost

    assert 0.0004 <= round(spent, 8) <= 0.0005, f"stopped at ${round(spent, 8)}, outside the ECON-2 band"
    assert escrow.committed(FLEET) <= cap, "committed exceeded the cap"


# ================================================================ ECON-2: every scope


def test_scopes_nest_so_a_run_cannot_outspend_the_fleet() -> None:
    """The live escrow gave every scope string the FULL cap, and reported fleet committed = $0.

    Two runs of $0.90 against a $1.00 fleet cap both went through. That is not a loose bound, it is
    the absence of a fleet cap wearing its name.
    """
    escrow = _escrow()
    first = escrow.reserve(0.9, scope="run:a")
    escrow.commit(first.resv_id, 0.9)

    assert escrow.committed(FLEET) == pytest.approx(0.9), "an inner scope's spend did not reach the fleet"
    with pytest.raises(EscrowRefused):
        escrow.reserve(0.9, scope="run:b")


def test_scope_chain_names_every_scope_a_charge_lands_on() -> None:
    assert scope_chain(FLEET) == (FLEET,)
    assert scope_chain("run:a") == ("run:a", FLEET)
    assert scope_chain("purpose:judge") == ("purpose:judge", FLEET)


def test_a_scope_cap_binds_without_carving_up_the_fleet() -> None:
    """A run cap limits that run; it never grants it money the fleet does not have."""
    escrow = _escrow(scope_caps={"run:a": 0.2})
    escrow.commit(escrow.reserve(0.2, scope="run:a").resv_id, 0.2)
    with pytest.raises(EscrowRefused):
        escrow.reserve(0.01, scope="run:a")  # its own cap is spent
    escrow.reserve(0.5, scope="run:b")  # ...but the fleet still has room for another run

    tight = _escrow(cap_usd=0.1, scope_caps={"run:a": 10.0})
    with pytest.raises(EscrowRefused):
        tight.reserve(1.0, scope="run:a")  # a generous run cap cannot exceed a small fleet


@pytest.mark.parametrize("scope", [FLEET, "run:a", "purpose:judge"])
def test_sixteen_concurrent_reservers_never_breach_the_cap(scope: str) -> None:
    """The 16-way drill. `committed ≤ cap` in every trial — a property a dict read-then-write
    does not give you, however carefully the arithmetic is written."""
    for trial in range(8):
        escrow = _escrow()
        rng = random.Random(trial)

        def one(i: int, e: Escrow = escrow, r: random.Random = rng) -> float:
            try:
                resv = e.reserve(0.1, scope=scope)
            except EscrowRefused:
                return 0.0
            e.commit(resv.resv_id, 0.1)
            return 0.1

        with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
            got = sum(pool.map(one, range(16)))

        assert escrow.committed(scope) <= CAP + 1e-9, (
            f"trial {trial}, scope {scope}: committed ${escrow.committed(scope)} over cap ${CAP}"
        )
        assert escrow.committed(FLEET) <= CAP + 1e-9, "the fleet total breached even if the scope did not"
        assert got == pytest.approx(escrow.committed(scope))


@pytest.mark.parametrize("injection", ["crash", "429", "batch-cancel"])
def test_the_cap_holds_under_injected_failure(injection: str) -> None:
    """Crash / 429 / batch-cancel, 16-way. A failure path that forgets to release is a slow leak;
    one that forgets to commit is a fast one. Both show up as `committed > cap` eventually."""
    escrow = _escrow()

    def one(i: int) -> None:
        try:
            resv = escrow.reserve(0.1, scope="run:a")
        except EscrowRefused:
            return
        if injection == "crash" and i % 3 == 0:
            return  # died holding the reservation; the sweeper's problem, not an overshoot
        if injection == "429" and i % 4 == 0:
            escrow.release(resv.resv_id, "429 from provider")
            return
        if injection == "batch-cancel" and i % 5 == 0:
            escrow.release(resv.resv_id, "batch canceled")
            return
        escrow.commit(resv.resv_id, 0.1)

    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
        list(pool.map(one, range(16)))

    for scope in ("run:a", FLEET):
        assert escrow.committed(scope) <= CAP + 1e-9, f"{injection}: {scope} breached the cap"
    assert escrow.reserved(FLEET) + escrow.committed(FLEET) <= CAP + 1e-9, (
        f"{injection}: held + committed exceeds the cap, so the next reserve would over-grant"
    )


def test_a_released_reservation_returns_its_headroom() -> None:
    escrow = _escrow()
    resv = escrow.reserve(0.9, scope="run:a")
    assert escrow.available(FLEET) == pytest.approx(0.1)
    escrow.release(resv.resv_id, "not needed")
    assert escrow.available(FLEET) == pytest.approx(1.0)


def test_an_overrun_is_booked_and_never_clamped() -> None:
    """In-doubt spend is REAL spend. Clamping to the reservation would make the ledger a wish."""
    escrow = _escrow()
    resv = escrow.reserve(0.1, scope="run:a")
    escrow.commit(resv.resv_id, 0.25)

    assert escrow.committed("run:a") == pytest.approx(0.25)
    assert escrow.reservations[resv.resv_id].overshoot == pytest.approx(0.15)
    assert any(r["kind"] == "commit" and r["overrun"] for r in escrow.records), (
        "an overrun was booked without being flagged; it indicts the estimator and must be visible"
    )


# ================================================================ ECON-2: partial admission


def test_a_group_reserve_admits_what_fits_and_says_what_did_not() -> None:
    """Silently admitting the part that fits starts work the caller thinks is fully funded;
    silently refusing the whole wastes headroom that exists. So: admit, and hand back a receipt."""
    escrow = _escrow()
    admission = escrow.reserve_group([("arm0", 0.6), ("arm1", 0.6), ("arm2", 0.3)])

    assert [r.holder for r in admission.admitted] == ["arm0", "arm2"]
    assert [name for name, _, _ in admission.refused] == ["arm1"]
    assert not admission.whole and admission.total_admitted == pytest.approx(0.9)


def test_a_group_that_fits_entirely_is_whole() -> None:
    admission = _escrow().reserve_group([("arm0", 0.2), ("arm1", 0.2)])
    assert admission.whole and len(admission.admitted) == 2


def test_a_group_reserve_never_breaches_the_cap() -> None:
    escrow = _escrow()
    escrow.reserve_group([(f"arm{i}", 0.3) for i in range(10)])
    assert escrow.reserved(FLEET) <= CAP + 1e-9


# ================================================================ ECON-L8: resume


def test_a_resumed_escrow_refuses_to_reserve_before_it_reconciles(tmp_path: Path) -> None:
    """The L8 leak in one assertion: the cap survives the crash, the spending must too."""
    first = _escrow(tmp_path)
    first.commit(first.reserve(0.8, scope="run:a").resv_id, 0.8)

    resumed = _escrow(tmp_path)
    assert resumed.needs_reconcile, "the resumed escrow did not notice it had inherited a budget"
    with pytest.raises(NotReconciled):
        resumed.reserve(0.01, scope="run:a")

    resumed.reconcile()
    assert resumed.committed(FLEET) == pytest.approx(0.8), "the fold forgot the pre-crash spend"


def test_a_resumed_run_refuses_past_the_REMAINING_headroom(tmp_path: Path) -> None:
    """The bar, verbatim. Under the null the resumed run gets the whole cap back."""
    first = _escrow(tmp_path)
    first.commit(first.reserve(0.8, scope="run:a").resv_id, 0.8)

    resumed = _escrow(tmp_path)
    resumed.reconcile()
    assert resumed.available(FLEET) == pytest.approx(0.2)

    resumed.reserve(0.15, scope="run:a")  # inside what is left
    with pytest.raises(EscrowRefused):
        resumed.reserve(0.5, scope="run:a")  # would have fitted a fresh cap; does not fit this one


def test_the_null_would_have_granted_the_whole_cap_again(tmp_path: Path) -> None:
    """The measurement that makes the bound mean something."""
    first = _escrow(tmp_path)
    first.commit(first.reserve(0.8, scope="run:a").resv_id, 0.8)

    ram_only = Escrow(cap_usd=CAP)  # no home: the RAM meter, i.e. the null
    assert ram_only.available(FLEET) == pytest.approx(1.0), (
        "the null starts every process with a full budget, whatever was spent before"
    )
    assert ram_only.reserve(0.9, scope="run:a").worst == pytest.approx(0.9)

    resumed = _escrow(tmp_path)
    resumed.reconcile()
    with pytest.raises(EscrowRefused):
        resumed.reserve(0.9, scope="run:a")


def test_spend_is_a_fold_over_the_records_not_a_counter(tmp_path: Path) -> None:
    escrow = _escrow(tmp_path)
    for _ in range(5):
        escrow.commit(escrow.reserve(0.1, scope="run:a").resv_id, 0.1)

    folded = EscrowLedger(tmp_path, fsync=False).fold()
    assert folded.replayed == 10, "five reserve+commit pairs should be ten records"
    total = sum(r["committed"] for r in folded.reservations.values())
    assert total == pytest.approx(escrow.committed(FLEET))


def test_the_record_lands_before_the_money_is_considered_held(tmp_path: Path) -> None:
    """Durable-before-act. The other order loses a reservation that was USED but never written."""
    escrow = _escrow(tmp_path)
    resv = escrow.reserve(0.3, scope="run:a")

    on_disk = list(EscrowLedger(tmp_path, fsync=False).records())
    assert any(r["kind"] == "reserve" and r["resv_id"] == resv.resv_id for r in on_disk), (
        "the reservation was held in RAM before it was durable"
    )


def test_a_torn_final_record_is_dropped_not_guessed(tmp_path: Path) -> None:
    escrow = _escrow(tmp_path)
    escrow.commit(escrow.reserve(0.2, scope="run:a").resv_id, 0.2)
    path = tmp_path / "_conductor" / "escrow.jsonl"
    with open(path, "a", encoding="utf-8") as f:
        f.write('{"kind": "reserve", "resv_id": "rsv_torn", "wor')

    resumed = _escrow(tmp_path)
    resumed.reconcile()
    assert "rsv_torn" not in resumed.reservations
    assert resumed.committed(FLEET) == pytest.approx(0.2)


# ================================================================ the metered path (F6's home)


class _Result:
    model, prompt_tokens, completion_tokens = "gpt-4o-mini", 1000, 500
    cache_read_tokens = cache_write_tokens = 0
    api_reported_usd = None


def test_the_governor_reserves_before_the_call_and_settles_after(tmp_path: Path) -> None:
    escrow = _escrow(tmp_path)
    gov = Governor(usd_cap=CAP, escrow=escrow, scope="run:a")

    resv_id = gov.open_call("openai", {"model": "gpt-4o-mini", "max_tokens": 500})
    assert resv_id is not None
    assert escrow.reserved("run:a") > 0, "nothing was held before the call"

    gov.close_call(resv_id, "openai", _Result())
    assert escrow.reserved("run:a") == pytest.approx(0.0), "the held remainder was not returned"
    assert escrow.committed("run:a") > 0


def test_a_call_that_never_answers_releases_rather_than_books(tmp_path: Path) -> None:
    """Holding headroom for work that produced nothing starves the run; booking it would be a lie."""
    escrow = _escrow(tmp_path)
    gov = Governor(usd_cap=CAP, escrow=escrow, scope="run:a")

    resv_id = gov.open_call("openai", {"model": "gpt-4o-mini", "max_tokens": 500})
    assert gov.close_call(resv_id, "openai", None) == 0.0
    assert escrow.reserved("run:a") == pytest.approx(0.0)
    assert escrow.committed("run:a") == pytest.approx(0.0)


def test_an_unpriceable_lane_reserves_the_whole_budget_rather_than_guessing(tmp_path: Path) -> None:
    """Deliberately crippling. A fabric that cannot price a lane should stop, not invent a number —
    the deleted `_PRICE` fallback guessed $(0.5, 1.5) and every downstream total inherited it."""
    escrow = _escrow(tmp_path)
    gov = Governor(usd_cap=CAP, escrow=escrow, scope="run:a")

    first = gov.open_call("nosuch", {"model": "nosuch-model", "max_tokens": 100})
    assert escrow.reserved("run:a") == pytest.approx(CAP)
    with pytest.raises(BudgetExceeded):
        gov.open_call("nosuch", {"model": "nosuch-model", "max_tokens": 100})
    assert first is not None


def test_the_hard_stop_refuses_BEFORE_the_call_not_after(tmp_path: Path) -> None:
    """The one-sentence difference from F6."""
    escrow = _escrow(tmp_path, cap_usd=0.0005)
    gov = Governor(usd_cap=0.0005, escrow=escrow, scope="run:a")

    with pytest.raises(BudgetExceeded, match="Refused BEFORE the call"):
        while True:
            rid = gov.open_call("openai", {"model": "gpt-4o-mini", "max_tokens": 4096})
            gov.close_call(rid, "openai", _Result())

    assert escrow.committed("run:a") <= 0.0005, "the call that would have breached was let through"
