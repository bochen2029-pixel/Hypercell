from __future__ import annotations

from pathlib import Path
from typing import Any

from hypercell.cell.nucleus import Nucleus
from hypercell.cell.runtime import Cell
from hypercell.cognition.base import Cognition, CompletionResult, Messages
from hypercell.common.types import ProviderConfig, Role
from hypercell.conductor.engine.drive import run_drive

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


class StubCognition(Cognition):
    def __init__(self, text: str) -> None:
        self.name = "stub"
        self._text = text

    async def complete(self, messages: Messages, **params: Any) -> CompletionResult:
        return CompletionResult(text=self._text, model="stub")


def _cell(tmp_path: Path, name: str, code: str) -> Cell:
    # The role must declare the lane it ACTUALLY runs on. Before ECON-S1 this fixture left the
    # default deepseek provider in place while serving a stub, and nothing noticed; the pricebook
    # now refuses `stub@deepseek/standard` because a role claiming one lane and running another is
    # a mispriced run waiting to happen.
    role = Role(name=name, prompt="p", provider=ProviderConfig(provider="stub", model="stub"))
    return Cell(role, Nucleus(tmp_path, f"d/{name}/0"), StubCognition(code))


async def test_drive_converges_on_correct_arm(tmp_path: Path) -> None:
    cells = [
        _cell(tmp_path, "arm0", BUGGY),
        _cell(tmp_path, "arm1", CORRECT),
        _cell(tmp_path, "arm2", BUGGY),
    ]
    res = await run_drive(
        run_id="d1", goal="ipv4", oracle_cmd=ORACLE, home=str(tmp_path),
        provider="stub", model="stub", max_steps=12, stable_k=1, cells=cells,
    )
    assert res.champion_arm == "arm1"
    assert res.champion_score == 1.0
    assert res.converged is True
    assert res.spent_usd == 0.0  # stub cognition is free; the governor recorded zero
