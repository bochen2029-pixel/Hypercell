from __future__ import annotations

from pathlib import Path
from typing import Any

from hypercell.cell.nucleus import Nucleus
from hypercell.cell.runtime import Cell
from hypercell.cognition.base import Cognition, CompletionResult, Messages
from hypercell.common.types import Role
from hypercell.conductor.engine.topology import run_tournament

ORACLE = "python oracles/ipv4_check.py"

CORRECT = (
    "def is_valid(s):\n"
    "    parts = s.split('.')\n"
    "    if len(parts) != 4:\n"
    "        return False\n"
    "    for p in parts:\n"
    "        if not p.isascii() or not p.isdigit():\n"
    "            return False\n"
    "        if len(p) > 1 and p[0] == '0':\n"
    "            return False\n"
    "        if int(p) > 255:\n"
    "            return False\n"
    "    return True\n"
)
BUGGY = "def is_valid(s):\n    return s.count('.') == 3\n"
BUGGY2 = (
    "def is_valid(s):\n"
    "    parts = s.split('.')\n"
    "    return len(parts) == 4 and all(p.isdigit() and int(p) <= 255 for p in parts)\n"
)


class StubCognition(Cognition):
    """Returns a fixed canned candidate (deterministic tournament, no network)."""

    def __init__(self, text: str) -> None:
        self.name = "stub"
        self._text = text
        self.calls = 0

    async def complete(self, messages: Messages, **params: Any) -> CompletionResult:
        self.calls += 1
        return CompletionResult(text=self._text, model="stub")


def _stub_cell(tmp_path: Path, name: str, code: str) -> Cell:
    return Cell(Role(name=name, prompt="produce"), Nucleus(tmp_path, f"t/{name}/0"), StubCognition(code))


async def test_tournament_converges_on_the_verified_candidate(tmp_path: Path) -> None:
    cells = [
        _stub_cell(tmp_path, "c0", BUGGY),
        _stub_cell(tmp_path, "c1", CORRECT),
        _stub_cell(tmp_path, "c2", BUGGY2),
    ]
    res = await run_tournament(
        run_id="t1", goal="ipv4", oracle_cmd=ORACLE, home=str(tmp_path),
        provider="stub", model="stub", n=3, rounds=2, stable_k=1, cells=cells,
    )
    assert res.champion is not None
    assert res.champion.cell == "c1"
    assert res.champion.score == 1.0
    assert res.converged is True


async def test_diversity_beats_identical(tmp_path: Path) -> None:
    # HC-4: an identical roster (all the same buggy candidate) cannot reach the target;
    # a diverse roster (one correct candidate among them) does.
    identical = [_stub_cell(tmp_path, f"i{i}", BUGGY) for i in range(3)]
    r_ident = await run_tournament(
        run_id="ti", goal="ipv4", oracle_cmd=ORACLE, home=str(tmp_path),
        provider="stub", model="stub", n=3, rounds=2, stable_k=1, cells=identical,
    )
    diverse = [
        _stub_cell(tmp_path, "d0", BUGGY),
        _stub_cell(tmp_path, "d1", CORRECT),
        _stub_cell(tmp_path, "d2", BUGGY2),
    ]
    r_div = await run_tournament(
        run_id="td", goal="ipv4", oracle_cmd=ORACLE, home=str(tmp_path),
        provider="stub", model="stub", n=3, rounds=2, stable_k=1, cells=diverse,
    )
    assert r_ident.champion is not None and r_div.champion is not None
    assert r_div.champion.score == 1.0
    assert r_div.champion.score > r_ident.champion.score
