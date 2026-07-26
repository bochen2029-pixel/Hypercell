"""NUC-9 — the record ladder and the read-barrier (ARCHITECTURE §15; slice N1′).

The bar: `hc ask` writes **exactly 2** nucleus records; **d0 writes 0**; byte overhead ≤ 1 KB +
bodies; and the read-barrier means a re-issued idem returns the stored outcome with **zero**
cognition calls — **including `produce`**, which is F17.

The null this kills: the live 5-record ask ceremony (E19), and a `produce` path that re-spent a
provider call every time it was re-issued because its guard lived at the call site instead of the
seam.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from hypercell.cell.loop import VerbExecutor
from hypercell.cell.nucleus import Nucleus
from hypercell.cell.runtime import Cell
from hypercell.cognition.mock import MockCognition
from hypercell.common.types import Depth, Role


def _cell(tmp_path: Path, claim: str = "r1/ask/0", depth: Depth = Depth.d1) -> tuple[Cell, MockCognition]:
    cog = MockCognition()
    role = Role(name="ask", prompt="sys", depth=depth)
    nucleus = None if depth is Depth.d0 else Nucleus(tmp_path, claim)
    return Cell(role, nucleus, cog), cog


def _kinds(n: Nucleus) -> list[str]:
    return [str(r["kind"]) for r in n.ledger.records()]


# ---------------------------------------------------------------- the ladder


async def test_ask_writes_exactly_two_records(tmp_path: Path) -> None:
    """E19 repealed: action + outcome, and nothing else. No percept, no checkpoints."""
    cell, _ = _cell(tmp_path)
    await cell.ask("hello", idem="a1")
    assert _kinds(cell.nucleus) == ["genesis", "action", "outcome"]
    cell.nucleus.close()


async def test_produce_writes_exactly_two_records(tmp_path: Path) -> None:
    cell, _ = _cell(tmp_path)
    await cell.produce("build a thing", [], idem="p1")
    assert _kinds(cell.nucleus) == ["genesis", "action", "outcome"]
    cell.nucleus.close()


async def test_outcome_is_gold(tmp_path: Path) -> None:
    """The outcome IS the exactly-once guarantee; if it is not durable, a crash re-spends the call."""
    cell, _ = _cell(tmp_path)
    await cell.ask("q", idem="a1")
    # gold flushes on write, so the record is on disk without any explicit flush from the test
    on_disk = (tmp_path / "r1/ask/0/ledger.jsonl").read_text(encoding="utf-8")
    assert on_disk.count("\n") == 3
    cell.nucleus.close()


async def test_byte_overhead_under_1kb_per_record(tmp_path: Path) -> None:
    """NUC-9's byte bar: ≤ 1 KB of envelope on top of the bodies."""
    cell, _ = _cell(tmp_path)
    await cell.ask("x", idem="a1")
    total = (tmp_path / "r1/ask/0/ledger.jsonl").stat().st_size
    bodies = sum(len(str(r["body"])) for r in cell.nucleus.ledger.records())
    assert total - bodies < 1024 * 3, f"envelope overhead {total - bodies}B over 3 records"
    cell.nucleus.close()


# ---------------------------------------------------------------- d0 writes nothing


async def test_d0_writes_zero_records(tmp_path: Path) -> None:
    """A reflex cell has no memory by definition — so it has no ledger to write to."""
    cell, cog = _cell(tmp_path, "r1/reflex/0", depth=Depth.d0)
    out = await cell.ask("hello", idem="a1")
    assert out and cog.calls == 1
    assert cell.nucleus is None, "a reflex cell has no nucleus to write to"
    assert not list(tmp_path.rglob("ledger.jsonl")), "d0 wrote a ledger; the bar is ZERO records"


async def test_d0_has_no_read_barrier_because_it_has_no_memory(tmp_path: Path) -> None:
    """Honest consequence: d0 re-issues DO re-spend. Memory is what buys exactly-once."""
    cell, cog = _cell(tmp_path, "r1/reflex/1", depth=Depth.d0)
    await cell.ask("q", idem="same")
    await cell.ask("q", idem="same")
    assert cog.calls == 2


# ---------------------------------------------------------------- the read-barrier


async def test_read_barrier_ask_zero_calls_on_replay(tmp_path: Path) -> None:
    cell, cog = _cell(tmp_path)
    first = await cell.ask("q", idem="same")
    before = len(_kinds(cell.nucleus))
    second = await cell.ask("q", idem="same")
    assert first == second
    assert cog.calls == 1, "the barrier must cost zero cognition calls"
    assert len(_kinds(cell.nucleus)) == before, "and write zero new records"
    cell.nucleus.close()


async def test_read_barrier_produce_zero_calls_on_replay_F17(tmp_path: Path) -> None:
    """**F17, closed.** Before N1′ `produce` had no barrier: this test failed by spending twice."""
    cell, cog = _cell(tmp_path)
    first = await cell.produce("goal", [], idem="p1")
    before = len(_kinds(cell.nucleus))
    second = await cell.produce("goal", [], idem="p1")
    assert first == second
    assert cog.calls == 1, "produce re-spent a provider call — F17 has regressed"
    assert len(_kinds(cell.nucleus)) == before, "produce wrote a second outcome — F17 has regressed"
    cell.nucleus.close()


async def test_barrier_survives_process_death(tmp_path: Path) -> None:
    """Exactly-once is across processes, not just within one — that is the whole point."""
    cell, cog = _cell(tmp_path, "r1/ask/2")
    out1 = await cell.ask("durable?", idem="d1")
    cell.nucleus.close()

    cog2 = MockCognition()
    cell2 = Cell(Role(name="ask", prompt="sys"), Nucleus(tmp_path, "r1/ask/2"), cog2)
    out2 = await cell2.ask("durable?", idem="d1")
    assert out1 == out2 and cog2.calls == 0
    cell2.nucleus.close()


async def test_executor_reports_replay(tmp_path: Path) -> None:
    """A caller can distinguish "did the work" from "already had it"."""
    n = Nucleus(tmp_path, "r1/x/0")
    calls = 0

    async def run() -> dict[str, object]:
        nonlocal calls
        calls += 1
        return {"text": "hi"}

    ex = VerbExecutor(n, Depth.d1)
    a = await ex.execute("ask", run, idem="k")
    b = await ex.execute("ask", run, idem="k")
    assert a.replayed is False and b.replayed is True and calls == 1
    n.close()


# ---------------------------------------------------------------- crash mid-verb


async def test_crash_between_action_and_outcome_is_resumable_for_any_verb(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The drill hook sits at the seam, so it drills every verb — not only `ask`."""
    cell, cog = _cell(tmp_path, "r1/prod/0")
    monkeypatch.setenv("HYPERCELL_CRASH_BEFORE_OUTCOME", "produce")
    with pytest.raises(SystemExit):
        await cell.produce("make it", [], idem="p9")
    assert cog.calls == 0
    assert [p["idem"] for p in cell.nucleus.pending()] == ["p9"]
    cell.nucleus.close()

    monkeypatch.delenv("HYPERCELL_CRASH_BEFORE_OUTCOME")
    cog2 = MockCognition()
    cell2 = Cell(Role(name="ask", prompt="sys"), Nucleus(tmp_path, "r1/prod/0"), cog2)
    out = await cell2.resume_pending()
    assert out is not None and cog2.calls == 1
    assert cell2.nucleus.pending() == []
    cell2.nucleus.close()


async def test_the_ledger_verifies_after_a_normal_run(tmp_path: Path) -> None:
    """Whatever the ladder writes, the chain over it must still verify."""
    cell, _ = _cell(tmp_path)
    await cell.ask("one", idem="a1")
    await cell.produce("two", [], idem="p1")
    report = cell.nucleus.verify()
    assert report.ok, report.reason
    cell.nucleus.close()
