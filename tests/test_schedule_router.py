from __future__ import annotations

from hypercell.conductor.engine.router import CellAd, route
from hypercell.conductor.engine.schedule import Arm, prune_dominated, ucb1


def test_ucb1_pulls_unvisited_first() -> None:
    arms = [Arm("a"), Arm("b", visits=5, best=0.9)]
    got = ucb1(arms)
    assert got is not None and got.name == "a"


def test_ucb1_prefers_high_value_when_all_visited() -> None:
    arms = [Arm("a", visits=10, best=0.9), Arm("b", visits=10, best=0.2)]
    got = ucb1(arms)
    assert got is not None and got.name == "a"


def test_prune_dominated() -> None:
    arms = [Arm("a", visits=3, best=1.0), Arm("b", visits=3, best=0.2)]
    newly = prune_dominated(arms, champion_best=1.0, margin=0.2)
    assert [a.name for a in newly] == ["b"]
    assert arms[1].pruned is True
    got = ucb1(arms)
    assert got is not None and got.name == "a"  # the pruned arm is excluded


def test_route_picks_best_coverage() -> None:
    ads = [CellAd("a", ["python"]), CellAd("b", ["python", "tests", "cuda"])]
    got = route(["python", "tests"], ads)
    assert got is not None and got.cell == "b"


def test_route_load_tiebreak() -> None:
    ads = [CellAd("a", ["python"], load=5), CellAd("b", ["python"], load=1)]
    got = route(["python"], ads)
    assert got is not None and got.cell == "b"


def test_route_excludes_dead_and_uncovered() -> None:
    assert route(["python"], [CellAd("a", ["python"], live=False)]) is None
    assert route(["rust"], [CellAd("a", ["python"])]) is None
