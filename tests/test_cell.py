from __future__ import annotations

from pathlib import Path

import pytest

from hypercell.cell.nucleus import Nucleus
from hypercell.cell.runtime import Cell
from hypercell.cognition.mock import MockCognition
from hypercell.common.types import Role


def _cell(tmp_path: Path, claim: str = "r1/ask/0") -> tuple[Cell, MockCognition]:
    cog = MockCognition()
    return Cell(Role(name="ask", prompt="sys"), Nucleus(tmp_path, claim), cog), cog


async def test_ask_returns_text(tmp_path: Path) -> None:
    cell, cog = _cell(tmp_path)
    out = await cell.ask("hello world", idem="a1")
    assert "hello world" in out
    assert cog.calls == 1
    cell.nucleus.close()


async def test_exactly_once(tmp_path: Path) -> None:
    cell, cog = _cell(tmp_path)
    out1 = await cell.ask("q", idem="same")
    out2 = await cell.ask("q", idem="same")  # already completed -> stored, no new call
    assert out1 == out2
    assert cog.calls == 1
    cell.nucleus.close()


async def test_crash_then_resume(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # HC-2: kill a cell mid-run; a fresh instance resumes from the nucleus, exactly once.
    cell, cog = _cell(tmp_path, "r1/ask/1")
    monkeypatch.setenv("HYPERCELL_CRASH_BEFORE_OUTCOME", "1")
    with pytest.raises(SystemExit):
        await cell.ask("recover me", idem="a1")
    assert cog.calls == 0  # crashed before cognition ran
    assert cell.nucleus.pending()  # N1': pending() is a list; a stranded action is in it
    cell.nucleus.close()  # simulate process death

    monkeypatch.delenv("HYPERCELL_CRASH_BEFORE_OUTCOME")
    # a brand-new instance re-binds the same claim-id (as `hc resume` would) and finishes the work.
    cog2 = MockCognition()
    cell2 = Cell(Role(name="ask", prompt="sys"), Nucleus(tmp_path, "r1/ask/1"), cog2)
    out = await cell2.resume_pending()
    assert out is not None and "recover me" in out
    assert cog2.calls == 1  # completed exactly once on resume
    assert cell2.nucleus.pending() == []
    cell2.nucleus.close()
