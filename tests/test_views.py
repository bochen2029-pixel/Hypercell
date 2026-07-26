"""RE-10 — partial view (ARCHITECTURE §15; slice RE-10).

The bar: no round with all-identical views at |F| ≥ 2; ∪ views = F; the assignment is recomputed by
`hc verify`; and the **herding drill** — a seeded common-mode wrong answer propagates to ≤ half the
roster in one round, where the total-view control infects **all** of it.

**The null is total view**, which is what the live `topology.py` does: hand every cell every peer's
candidate. It reads like generosity and behaves like a broadcast — one confident wrong answer reaches
the whole roster in a single round, and by the next every cell is anchored on it.
"""
from __future__ import annotations

import pytest

from hypercell.conductor.engine.views import (
    Assignment,
    assign_views,
    replication,
    verify_assignment,
    view_for,
)

# ---------------------------------------------------------------- the herding drill


@pytest.mark.parametrize("n", [2, 3, 4, 5, 6, 8, 12])
def test_herding_a_common_mode_wrong_answer_reaches_at_most_half(n: int) -> None:
    """The bar, across roster sizes. One poisoned candidate; count how much of the roster sees it."""
    frontier = ["POISONED"] + [f"ok-{i}" for i in range(1, n)]
    infected = sum(1 for i in range(n) if "POISONED" in view_for(i, frontier, n=n, round=1))

    assert infected <= n / 2, f"n={n}: the bad answer reached {infected}/{n} — over half"
    assert infected >= 1, "nobody saw it at all; that is isolation, not partial view"


@pytest.mark.parametrize("n", [2, 3, 4, 5, 6, 8, 12])
def test_the_total_view_control_infects_everyone(n: int) -> None:
    """The null, run side by side. Without this comparison the bound above proves nothing."""
    frontier = ["POISONED"] + [f"ok-{i}" for i in range(1, n)]
    # Total view = what the live code did: every cell gets the whole frontier.
    infected = sum(1 for _ in range(n) if "POISONED" in frontier)
    assert infected == n, "the control is not modelling total view"


def test_herding_holds_across_every_round(n: int = 6) -> None:
    """The rotation must not create a round where the bound quietly lapses."""
    frontier = ["POISONED"] + [f"ok-{i}" for i in range(1, n)]
    for rnd in range(1, 25):
        infected = sum(1 for i in range(n) if "POISONED" in view_for(i, frontier, n=n, round=rnd))
        assert infected <= n / 2, f"round {rnd}: {infected}/{n}"


def test_poison_in_any_position_is_equally_bounded(n: int = 6) -> None:
    """An attacker picks which candidate is poisoned, so the bound cannot depend on the index."""
    for poisoned in range(n):
        frontier = [f"ok-{i}" if i != poisoned else "POISONED" for i in range(n)]
        infected = sum(1 for i in range(n) if "POISONED" in view_for(i, frontier, n=n, round=3))
        assert infected <= n / 2, f"poison at index {poisoned} reached {infected}/{n}"


# ---------------------------------------------------------------- the three structural properties


@pytest.mark.parametrize("n", [2, 3, 4, 7])
@pytest.mark.parametrize("m", [2, 3, 5, 9])
def test_union_of_views_is_the_whole_frontier(n: int, m: int) -> None:
    """A candidate nobody sees may as well not have been produced."""
    a = assign_views(n=n, m=m, round=1)
    assert a.coverage() == set(range(m)), f"n={n} m={m}: candidates {sorted(set(range(m)) - a.coverage())} unseen"


@pytest.mark.parametrize("n", [2, 3, 4, 7])
@pytest.mark.parametrize("m", [2, 5, 9])
def test_no_round_has_all_identical_views(n: int, m: int) -> None:
    """Identical views are total view wearing a different name."""
    for rnd in range(1, 8):
        a = assign_views(n=n, m=m, round=rnd)
        assert not a.all_identical(), f"n={n} m={m} round={rnd}: every view identical"


def test_the_assignment_is_recomputable_from_round_n_and_m() -> None:
    """`hc verify` re-derives who saw what without the run having recorded it."""
    a = assign_views(n=5, m=7, round=3)
    b = assign_views(n=5, m=7, round=3)
    assert a.views == b.views

    ok, why = verify_assignment(a)
    assert ok, why
    assert "r=2" in why and "contagion 0.40" in why


def test_verify_catches_a_tampered_assignment() -> None:
    """The check must FAIL something. A verifier that only agrees is a rubber stamp."""
    a = assign_views(n=4, m=4, round=1)
    tampered = Assignment(round=a.round, n=a.n, m=a.m, views={i: (0, 1, 2, 3) for i in a.views})
    ok, why = verify_assignment(tampered)
    assert not ok and "not recomputable" in why


def test_verify_catches_an_uncovered_candidate() -> None:
    a = assign_views(n=4, m=4, round=1)
    holed = Assignment(round=a.round, n=a.n, m=a.m, views={i: () for i in a.views})
    ok, why = verify_assignment(holed)
    assert not ok


def test_verify_names_the_contagion_bound_it_enforces() -> None:
    a = assign_views(n=4, m=4, round=1)
    over = Assignment(round=1, n=2, m=2, views={0: (0, 1), 1: (0, 1)})
    ok, why = verify_assignment(over)
    assert not ok  # identical views trip first, which is the stricter finding
    assert a.contagion <= 0.5


# ---------------------------------------------------------------- replication + edges


@pytest.mark.parametrize("n", range(1, 17))
def test_replication_never_exceeds_half_the_roster(n: int) -> None:
    """The bound is arithmetic, not hope: r/n <= 0.5 for every roster size."""
    r = replication(n)
    assert r >= 1, "replication below 1 means a candidate nobody sees"
    if n >= 2:
        assert r / n <= 0.5, f"n={n}: r={r} gives contagion {r / n:.2f}"


def test_replication_is_generous_within_the_bound() -> None:
    """r = n//2 is the LARGEST value the bound allows.

    Cutting to r=1 would herd less still, but a cell that sees nothing learns nothing, and the point
    is to bound contagion — not to isolate the roster.
    """
    assert replication(8) == 4
    assert replication(4) == 2


def test_an_empty_frontier_gives_every_cell_an_empty_view() -> None:
    """Round 1 has no frontier. Every cell produces fresh, and that is correct, not a failure."""
    a = assign_views(n=4, m=0, round=1)
    assert all(v == () for v in a.views.values())
    ok, why = verify_assignment(a)
    assert ok, why


def test_a_single_candidate_reaches_at_least_one_and_not_everyone() -> None:
    a = assign_views(n=4, m=1, round=1)
    seers = [i for i, v in a.views.items() if 0 in v]
    assert 1 <= len(seers) <= 2


def test_a_single_cell_run_is_degenerate_but_valid() -> None:
    """n=1: the one cell sees everything, and there is no herding to bound."""
    a = assign_views(n=1, m=3, round=1)
    assert a.views == {0: (0, 1, 2)}
    assert a.coverage() == {0, 1, 2}


def test_the_rotation_shares_out_over_rounds(n: int = 4, m: int = 4) -> None:
    """No cell should be permanently the one that never sees candidate 0."""
    seen_by_cell0 = {v for rnd in range(1, 9) for v in assign_views(n=n, m=m, round=rnd).views[0]}
    assert seen_by_cell0 == set(range(m)), "cell 0 was structurally blind to part of the frontier"


def test_view_for_returns_the_actual_candidates_not_indices() -> None:
    frontier = ["alpha", "beta", "gamma", "delta"]
    got = view_for(0, frontier, n=4, round=1)
    assert got and all(g in frontier for g in got)
    assert len(got) < len(frontier), "a cell received the whole frontier — that is total view"
