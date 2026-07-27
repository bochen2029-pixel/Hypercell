"""ECON-UCB-1 — the dollar-UCB (slice ECON-S3).

**The bar, verbatim:** dollar-UCB reaches target at ≤60% of pull-UCB spend; allocation invariant
under currency re-scale ×100.

**The null is pull-count UCB** — the live v1 `ucb1`, kept in `schedule.py` and run side by side
here, because "≤60% of the null's spend" is only a measurement while the null still runs. Its
defect in one sentence: exploration priced in pulls subsidises whichever arm burns money fastest.

The A/B environment is deterministic on purpose. Two arms tell the whole story: a pricey lane that
scores high fast, and a budget lane at a tenth the price that gets there in a few more pulls. The
null pays for the fast answer because pulls are its only currency; the dollar index buys the same
target for a fraction, because dollars are the currency that actually runs out.
"""
from __future__ import annotations

from collections.abc import Callable
from datetime import date
from pathlib import Path

import pytest

from hypercell.conductor.engine.router import CellAd, route
from hypercell.conductor.engine.schedule import (
    Arm,
    RunBook,
    advance_generation,
    charge,
    dollar_ucb,
    open_null_reservation,
    parity_verdict,
    prune_2d,
    resurrect_on_cost_flip,
    ucb1,
)
from hypercell.conductor.governor import Escrow
from hypercell.conductor.pricebook import Pricebook, PricebookError, UnknownLane
from hypercell.conductor.quote import quote_pull

TARGET = 0.85

#: The environment: per-pull cost and a deterministic quality curve per arm.
COSTS = {"pricey": 0.10, "budget": 0.01}
CURVES: dict[str, Callable[[int], float]] = {
    "pricey": lambda k: min(0.92, 0.50 + 0.20 * k),  # 0.70, 0.90 — fast and expensive
    "budget": lambda k: min(0.88, 0.30 + 0.12 * k),  # 0.42 ... 0.88 at k=5 — slow and cheap
}


def _simulate(
    picker: Callable[[list[Arm], RunBook], Arm | None],
    costs: dict[str, float],
    *,
    max_pulls: int = 60,
) -> tuple[float, list[str], float]:
    """Run one allocator against the environment. Returns (spend, pull sequence, best score)."""
    arms = [Arm(name=n) for n in COSTS]
    book = RunBook()
    spend, seq = 0.0, []
    for _ in range(max_pulls):
        arm = picker(arms, book)
        assert arm is not None
        arm.visits += 1
        score = CURVES[arm.name](arm.visits)
        charge(arm, costs[arm.name], attribution="candidate", book=book)
        spend += costs[arm.name]
        arm.best = max(arm.best, score)
        seq.append(arm.name)
        if max(a.best for a in arms) >= TARGET:
            break
    return spend, seq, max(a.best for a in arms)


# ================================================================ the bar


def test_dollar_ucb_reaches_the_target_at_most_60_percent_of_the_nulls_spend() -> None:
    null_spend, _, null_best = _simulate(lambda arms, _b: ucb1(arms), COSTS)
    dollar_spend, _, dollar_best = _simulate(
        lambda arms, book: dollar_ucb(arms, e_hat=COSTS, book=book), COSTS
    )

    assert null_best >= TARGET and dollar_best >= TARGET, "an allocator failed to reach the target"
    ratio = dollar_spend / null_spend
    assert ratio <= 0.60, (
        f"dollar-UCB spent ${dollar_spend:.4f} vs the null's ${null_spend:.4f} "
        f"({ratio:.0%}); the bar is <=60%"
    )


def test_the_allocation_is_invariant_under_a_currency_rescale_x100() -> None:
    """Exact-sequence equality, not an approximation. v2's `ln USD_total` bare is repealed as
    dimensionally unsound precisely because it fails this drill."""
    _, seq_usd, _ = _simulate(lambda arms, book: dollar_ucb(arms, e_hat=COSTS, book=book), COSTS)

    cents = {n: c * 100 for n, c in COSTS.items()}
    _, seq_cents, _ = _simulate(lambda arms, book: dollar_ucb(arms, e_hat=cents, book=book), cents)

    assert seq_usd == seq_cents, "re-denominating the currency changed the allocation"


def test_v2s_repealed_formula_really_does_fail_the_rescale() -> None:
    """The repeal, measured: `ln(USD_total)` bare moves under x100, so exploration moves."""
    import math

    usd_total, cents_total = 0.05, 5.0
    assert math.log(max(1.0, usd_total)) != math.log(max(1.0, cents_total)), (
        "the dimensionally-unsound bonus happened to agree; the repeal drill needs a new witness"
    )


# ================================================================ the R5 attribution fork


def test_apparatus_spend_never_burns_the_arm() -> None:
    """The fork's entire content is an equality: the index before == the index after."""
    arms = [Arm(name="a", best=0.5, usd_candidate=0.05), Arm(name="b", best=0.4, usd_candidate=0.05)]
    book = RunBook(production_usd=0.10)
    before = dollar_ucb(arms, e_hat={"a": 0.01, "b": 0.01}, book=book)

    charge(arms[0], 0.50, attribution="apparatus", book=book)  # the grader broke, expensively
    after = dollar_ucb(arms, e_hat={"a": 0.01, "b": 0.01}, book=book)

    assert before is after, "an apparatus failure changed the allocation; the fork is not a fork"
    assert arms[0].usd_candidate == pytest.approx(0.05), "apparatus dollars burned the arm"
    assert book.apparatus_usd == pytest.approx(0.50), "the run-level ledger missed the apparatus cost"
    assert book.production_usd == pytest.approx(0.10), "apparatus spend advanced the exploration clock"


def test_candidate_spend_does_burn_the_arm() -> None:
    """The positive control: the same dollars under the other attribution DO move the index."""
    arms = [Arm(name="a", best=0.5, usd_candidate=0.05), Arm(name="b", best=0.5, usd_candidate=0.05)]
    book = RunBook(production_usd=0.10)
    charge(arms[0], 0.50, attribution="candidate", book=book)

    assert arms[0].usd_candidate == pytest.approx(0.55)
    assert book.production_usd == pytest.approx(0.60)
    picked = dollar_ucb(arms, e_hat={"a": 0.01, "b": 0.01}, book=book)
    assert picked is arms[1], "the heavily-charged arm kept winning; candidate spend is not burning"


# ================================================================ the index's edges


def test_an_unquoted_live_arm_raises_rather_than_defaults() -> None:
    with pytest.raises(KeyError, match="allocates by fiction"):
        dollar_ucb([Arm(name="a"), Arm(name="b")], e_hat={"a": 0.01}, book=RunBook())


def test_a_uniformly_free_world_delegates_to_the_pull_count_null() -> None:
    """A dollar-denominated exploration clock cannot tick when nothing costs anything. Pull-count
    UCB is the equal-price limit of the index, so at zero the null IS the formula. Found live:
    drive's stub lane is priced $0, and the first arm to score was never dethroned."""
    arms = [Arm(name="a", visits=3, best=0.9), Arm(name="b", visits=0)]
    free = {"a": 0.0, "b": 0.0}
    assert dollar_ucb(arms, e_hat=free, book=RunBook()) is ucb1(arms), (
        "the free-world allocation diverged from the pull-count limit"
    )
    assert dollar_ucb(arms, e_hat=free, book=RunBook()).name == "b", (
        "the unvisited arm was never explored in the free world -- the exact live failure"
    )


def test_a_mixed_free_and_priced_world_still_decides_without_dividing_by_zero() -> None:
    mixed = {"a": 0.0, "b": 0.10}
    picked = dollar_ucb([Arm(name="a"), Arm(name="b")], e_hat=mixed, book=RunBook())
    assert picked is not None  # floored at 1% of the cheapest paid lane; finite, deterministic


def test_allocation_never_selects() -> None:
    """A cheap arm gets more TRIES, never a discount on the bar: the index may prefer `budget`
    all day while the champion — max score, computed where champions are computed — is `pricey`."""
    arms = [Arm(name="pricey", best=0.92, usd_candidate=0.2), Arm(name="budget", best=0.70, usd_candidate=0.02)]
    book = RunBook(production_usd=0.22)
    allocated = dollar_ucb(arms, e_hat=COSTS, book=book)
    champion = max(arms, key=lambda a: a.best)

    assert allocated.name == "budget", "the index stopped favouring the cheap explorer"
    assert champion.name == "pricey", "allocation leaked into selection"


# ================================================================ 2-D prune / resurrection


def test_prune_2d_spares_the_cheapest_lane_the_1d_prune_would_kill() -> None:
    """The cheap arm is behind BECAUSE it has been given less money — it is the arm the dollar
    index most wants to keep probing, and the run's cheapest way to be wrong."""
    arms = [
        Arm(name="champ", best=0.9, usd_candidate=0.3),
        Arm(name="mid", best=0.5, usd_candidate=0.2),     # behind, not cheapest -> pruned
        Arm(name="cheap", best=0.4, usd_candidate=0.02),  # behind, cheapest -> spared
    ]
    e_hat = {"champ": 0.05, "mid": 0.05, "cheap": 0.005}
    newly = prune_2d(arms, champion_best=0.9, e_hat=e_hat, margin=0.2)

    assert [a.name for a in newly] == ["mid"]
    assert not arms[2].pruned, "the exploration floor was pruned on score alone"


def test_prune_2d_never_prunes_an_unspent_arm() -> None:
    arms = [Arm(name="champ", best=0.9, usd_candidate=0.3), Arm(name="cold", best=0.0)]
    newly = prune_2d(arms, champion_best=0.9, e_hat={"champ": 0.01, "cold": 0.05}, margin=0.2)
    assert newly == [], "an arm was condemned on evidence it was never funded to produce"


def test_a_generation_bump_lifts_prunes_and_stales_scores() -> None:
    """A verdict earned under gen N is not evidence under gen N+1 — the grader changed."""
    arms = [Arm(name="a", best=0.9, gen=1), Arm(name="b", best=0.3, gen=1, pruned=True)]
    back = advance_generation(arms, gen=2)

    assert [a.name for a in back] == ["b"]
    assert not arms[1].pruned and arms[0].best == 0.0 and arms[0].gen == 2, (
        "an old grader reached forward in time"
    )


def test_a_cost_flip_resurrects_the_newly_cheapest_arm_only() -> None:
    arms = [
        Arm(name="live", best=0.9),
        Arm(name="was_pricey", best=0.3, pruned=True, usd_candidate=0.1),
        Arm(name="still_pricey", best=0.2, pruned=True, usd_candidate=0.1),
    ]
    # The pricebook moved: the pruned arm's lane is now the cheapest in the run.
    e_hat = {"live": 0.05, "was_pricey": 0.001, "still_pricey": 0.20}
    back = resurrect_on_cost_flip(arms, e_hat=e_hat)

    assert [a.name for a in back] == ["was_pricey"]
    assert arms[2].pruned, "an arm resurrected without its condition changing"


# ================================================================ the parity probe (A6)


def test_the_parity_probe_is_pending_until_five_pulls() -> None:
    assert parity_verdict([0.8] * 4, [0.8] * 4) == "pending"


def test_parity_passes_within_eps_and_fails_beyond() -> None:
    assert parity_verdict([0.80, 0.82, 0.79, 0.81, 0.80], [0.80] * 5, eps=0.05) == "passed"
    assert parity_verdict([0.60, 0.55, 0.58, 0.61, 0.57], [0.80] * 5, eps=0.05) == "failed", (
        "a host quantizing its weights passed parity; the blind spot no longer follows the weights"
    )


# ================================================================ null-arm reservations


def test_null_reservations_are_taken_at_run_open_with_named_holders() -> None:
    escrow = Escrow(cap_usd=1.0)
    matched = open_null_reservation(
        escrow, mode="matched", scope="run:a", matched_usd=0.2, floor_usd=0.01
    )
    assert matched.holder == "null:matched" and matched.worst == pytest.approx(0.2)

    floor = open_null_reservation(
        escrow, mode="floor", scope="run:a", matched_usd=0.2, floor_usd=0.01
    )
    assert floor.holder == "null:floor+audit" and floor.worst == pytest.approx(0.01)
    assert escrow.reserved("run:a") == pytest.approx(0.21), "the null's budget was not set aside"


# ================================================================ quote_pull


def _book(as_of: str) -> Pricebook:
    return Pricebook(
        {
            "version": "test",
            "defaults": {"max_age_days": 30, "stale_mult": 1.25, "refuse_after": 2.0},
            "skus": {
                "m@p/standard": {
                    "input": 1.0, "output": 2.0, "as_of": as_of,
                    "source": "test", "verified": True, "weights_family": "test",
                }
            },
        }
    )


def test_quote_pull_prices_the_expected_tokens_off_the_dated_row() -> None:
    q = quote_pull(_book(date.today().isoformat()), model="m", provider="p",
                   est_in=1_000_000, est_out=500_000)
    assert q.usd_expected == pytest.approx(1.0 * 1.0 + 0.5 * 2.0)
    assert not q.stale and q.age_days == 0


def test_a_stale_row_quotes_dearer_never_cheaper() -> None:
    from datetime import timedelta

    old = (date.today() - timedelta(days=45)).isoformat()
    q = quote_pull(_book(old), model="m", provider="p", est_in=1_000_000, est_out=0)
    assert q.stale and q.usd_expected == pytest.approx(1.0 * 1.25), (
        "a lane nobody re-priced got cheaper instead of dearer"
    )


def test_a_row_past_the_refusal_threshold_raises() -> None:
    from datetime import timedelta

    ancient = (date.today() - timedelta(days=100)).isoformat()
    with pytest.raises(PricebookError, match="rumour"):
        quote_pull(_book(ancient), model="m", provider="p")


def test_an_unknown_lane_raises_rather_than_guesses() -> None:
    with pytest.raises(UnknownLane):
        quote_pull(_book(date.today().isoformat()), model="nosuch", provider="p")


def test_the_batch_seam_fields_exist_and_are_honestly_none() -> None:
    """ECON-S4/BATCH builds against these; an undeclared seam is one nobody can build against."""
    q = quote_pull(_book(date.today().isoformat()), model="m", provider="p")
    assert q.window_close_eta is None and q.expiry_at is None


# ================================================================ the router's price term


def test_the_router_breaks_ties_toward_the_cheaper_lane() -> None:
    ads = [CellAd(cell="a", capabilities=["x"]), CellAd(cell="b", capabilities=["x"])]
    got = route(["x"], ads, usd={"a": 0.10, "b": 0.01})
    assert got is not None and got.cell == "b"


def test_coverage_still_trumps_price() -> None:
    """A router that chose cheapness over capability would save dollars by buying failures."""
    ads = [
        CellAd(cell="cheap_partial", capabilities=["x"]),
        CellAd(cell="pricey_full", capabilities=["x", "y"]),
    ]
    got = route(["x", "y"], ads, usd={"cheap_partial": 0.001, "pricey_full": 1.0})
    assert got is not None and got.cell == "pricey_full"


def test_an_unpriced_cell_ranks_most_expensive_among_its_ties() -> None:
    ads = [CellAd(cell="priced", capabilities=["x"]), CellAd(cell="mystery", capabilities=["x"])]
    got = route(["x"], ads, usd={"priced": 0.50})
    assert got is not None and got.cell == "priced", "an unknown price was treated as a cheap price"


def test_the_priceless_call_still_routes_exactly_as_before() -> None:
    ads = [CellAd(cell="a", capabilities=["x"], load=2), CellAd(cell="b", capabilities=["x"], load=1)]
    got = route(["x"], ads)
    assert got is not None and got.cell == "b"


# ================================================================ drive integration


@pytest.mark.asyncio
async def test_drive_still_converges_with_the_dollar_index_wired(tmp_path: Path) -> None:
    """The stub world exercises the delegation branch end-to-end through the real loop."""
    from tests.test_drive import CORRECT, ORACLE, _cell

    from hypercell.conductor.engine.drive import run_drive

    cells = [_cell(tmp_path, "arm0", CORRECT)]
    res = await run_drive(
        run_id="ucb1", goal="ipv4", oracle_cmd=ORACLE, home=str(tmp_path),
        provider="stub", model="stub", max_steps=6, stable_k=1, cells=cells,
    )
    assert res.converged and res.champion_arm == "arm0"
