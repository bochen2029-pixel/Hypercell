"""RE-1 — one driver (ARCHITECTURE §15; slice RE-1).

The bar: identical VALID-event counting across all convergent rows; F14, F24 and F25 each
UNREPRODUCIBLE by construction; 29/29 green before and after.

The null is the three live loops. Two of them counted `stable` differently, and **both counted
events the tri-state excludes**:

* `topology.py` incremented stability when a round produced ZERO valid candidates;
* `drive.py` incremented it on an INVALID grading.

So a run whose oracle was simply broken accrued stability and could "converge" on a stale champion
with nothing having been graded. `stable_k` now has one meaning — *consecutive VALID scoring events
with no champion improvement* — and it has one meaning because it has one implementation.
"""
from __future__ import annotations

import random

import pytest

from hypercell.common.types import Outcome
from hypercell.conductor.engine.driver import TOPOLOGIES, Convergence, ScoringEvent


def ev(who: str, outcome: Outcome, score: float, at: int = 0) -> ScoringEvent:
    return ScoringEvent(who, outcome, score, at)


PASS, GATE, INVALID = Outcome.passed, Outcome.gate, Outcome.invalid


# ---------------------------------------------------------------- F14: INVALID never buys stability


def test_an_all_invalid_tick_does_not_move_stability() -> None:
    """The topology.py half of F14: a round that graded NOTHING is not evidence of stability."""
    c = Convergence(target=1.0, stable_k=2)
    c.observe([ev("a", PASS, 1.0)])
    assert c.stable == 0 and not c.converged

    for _ in range(10):
        c.observe([ev("a", INVALID, 0.0), ev("b", INVALID, 0.0)])

    assert c.stable == 0, "a broken oracle bought stability one empty tick at a time"
    assert not c.converged
    assert c.invalid_events == 20 and c.valid_events == 1


def test_a_single_invalid_grading_does_not_move_stability() -> None:
    """The drive.py half of F14: an INVALID is not evidence in EITHER direction."""
    c = Convergence(target=1.0, stable_k=2)
    c.observe([ev("a", PASS, 1.0)])
    c.observe([ev("a", INVALID, 0.0)])
    c.observe([ev("a", INVALID, 0.0)])
    assert c.stable == 0 and not c.converged


def test_valid_no_improvement_events_are_what_count() -> None:
    c = Convergence(target=1.0, stable_k=2)
    c.observe([ev("a", PASS, 1.0)])
    assert c.stable == 0
    c.observe([ev("b", GATE, 0.5)])   # valid, no improvement
    assert c.stable == 1 and not c.converged
    c.observe([ev("b", GATE, 0.5)])
    assert c.stable == 2 and c.converged


def test_an_invalid_interleaved_with_valid_events_is_simply_skipped() -> None:
    """Excluded means excluded: the INVALID neither resets the run nor counts toward it."""
    clean = Convergence(target=1.0, stable_k=2)
    for events in ([ev("a", PASS, 1.0)], [ev("b", GATE, 0.4)], [ev("b", GATE, 0.4)]):
        clean.observe(events)

    noisy = Convergence(target=1.0, stable_k=2)
    for events in (
        [ev("a", PASS, 1.0)],
        [ev("x", INVALID, 0.0)],
        [ev("b", GATE, 0.4)],
        [ev("x", INVALID, 0.0)],
        [ev("b", GATE, 0.4)],
    ):
        noisy.observe(events)

    assert clean.converged == noisy.converged is True
    assert clean.stable == noisy.stable, "INVALID events perturbed the count"


def test_an_improvement_resets_stability() -> None:
    c = Convergence(target=0.5, stable_k=2)
    c.observe([ev("a", PASS, 0.6)])
    c.observe([ev("a", PASS, 0.6)])
    assert c.stable == 1
    c.observe([ev("b", PASS, 0.9)])  # better champion
    assert c.stable == 0 and not c.converged


# ---------------------------------------------------------------- the champion rule


def test_outcome_is_authoritative_and_score_is_only_the_tiebreak() -> None:
    """A `passed` at 0.7 beats a `gate` at 0.99: the exit code is ground truth (HC-7)."""
    c = Convergence()
    c.observe([ev("high-but-gated", GATE, 0.99), ev("passed", PASS, 0.70)])
    assert c.champion is not None and c.champion.who == "passed"


def test_a_run_of_only_invalids_has_no_champion_and_says_so() -> None:
    c = Convergence()
    c.observe([ev("a", INVALID, 0.0), ev("b", INVALID, 0.0)])
    assert c.champion is None and not c.converged
    assert "every candidate was INVALID" in c.reason()


def test_reason_explains_a_non_convergence() -> None:
    """An operator asking "why didn't it converge?" gets an answer, not a boolean."""
    c = Convergence(target=1.0, stable_k=3)
    c.observe([ev("a", PASS, 1.0)])
    c.observe([ev("a", PASS, 1.0)])
    assert "stability 1/3" in c.reason()

    below = Convergence(target=0.9)
    below.observe([ev("a", PASS, 0.5)])
    assert "below target" in below.reason()

    gated = Convergence(target=0.1)
    gated.observe([ev("a", GATE, 0.5)])
    assert "not passed" in gated.reason()


# ---------------------------------------------------------------- F24: one definition, by construction


@pytest.mark.parametrize("row", ["tournament", "drive", "fanout"])
def test_every_topology_is_a_policy_row_over_the_same_counter(row: str) -> None:
    """`run_tournament`/`run_drive`/`run_fanout` as sibling code paths are REPEALED."""
    topo = TOPOLOGIES[row]
    assert topo.name == row
    assert topo.termination_unit in ("rounds", "steps")


def test_drive_is_tournament_with_a_dispatch_policy() -> None:
    """`hc drive` is CLI sugar for tournament x {dispatch: ucb} — not a second engine."""
    assert TOPOLOGIES["drive"].dispatch == "ucb"
    assert TOPOLOGIES["tournament"].dispatch == "all"


def test_identical_counting_across_convergent_rows_over_a_fuzz() -> None:
    """F24's terminal argument: with ONE implementation this is not a property to test for.

    Two convergent rows fed the same event stream cannot disagree, because there is no second
    counter to disagree with. The fuzz asserts the invariant a reader would want checked anyway —
    and, more usefully, that stability never exceeds the number of VALID events that could have
    produced it.
    """
    rng = random.Random(20260726)
    for trial in range(300):
        events = [
            [
                ev(f"c{rng.randrange(3)}", rng.choice([PASS, GATE, INVALID]), round(rng.random(), 3))
                for _ in range(rng.randrange(1, 4))
            ]
            for _ in range(rng.randrange(1, 8))
        ]
        a, b = Convergence(target=0.5, stable_k=2), Convergence(target=0.5, stable_k=2)
        for tick in events:
            a.observe(tick)
            b.observe(list(tick))

        assert (a.stable, a.converged, a.valid_events) == (b.stable, b.converged, b.valid_events), trial
        assert a.stable <= a.valid_events, (
            f"trial {trial}: stability {a.stable} exceeds the {a.valid_events} VALID events that "
            "could have produced it — an excluded event moved the counter"
        )


def test_the_old_loops_would_have_failed_this() -> None:
    """The null, reconstructed: increment `stable` on every tick regardless of validity.

    This is what both live loops did. Run it against a stream of pure INVALIDs and it converges on
    a champion that nothing re-graded — the exact failure F14 names.
    """
    c = Convergence(target=1.0, stable_k=2)
    c.observe([ev("a", PASS, 1.0)])

    old_stable = 0
    for _ in range(5):  # five ticks where the oracle only ever errored
        c.observe([ev("a", INVALID, 0.0)])
        old_stable += 1  # the null's rule: else-branch increments, whatever the outcome

    assert old_stable >= c.stable_k, "the reconstruction of the null is not exercising the bug"
    assert c.stable == 0, "the driver reproduced F14"
    assert not c.converged, "the driver converged on evidence the tri-state excludes"
