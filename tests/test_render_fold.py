"""NUC-2 / NUC-7 — the render fold and the write-amplification bars (slice N3′).

**NUC-2** — render fold + in-render cursor. Null: rebuild-on-every-open (live `nucleus.py`).
Two local rebuilds and a second-machine rebuild must produce identical digests over a 10 K fixture;
**open p95 ≤ 100 ms at 100 K records warm**; and `verify()` catches a corrupted render 10/10.

**NUC-7** — tier bars. Null: fsync-always plus a synchronous mirror. Append p50 ≤ 10 ms and
p95 ≤ 50 ms; **≤ 1 durable write per standard flush, ≤ 2 per gold**; and a breach shows up as
`degraded-persistence` rather than as a fabric that is quietly slow.

The cursor is the whole slice: rebuild-on-every-open costs O(history) each time, so a cell gets
slower every day it stays alive. That is the one thing a long-lived resident must not do.
"""
from __future__ import annotations

import json
import shutil
import statistics
import time
from pathlib import Path

import pytest

from hypercell.cell.nucleus import Nucleus
from hypercell.common.census import census
from hypercell.common.ledger import Ledger


def _seed(home: Path, claim: str, n: int) -> None:
    """Build an n-record chained ledger straight through the engine, no index in the way."""
    path = home / claim / "ledger.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    lg = Ledger(path, claim_id=claim)
    lg.genesis(census())
    for i in range(n):
        lg.append("percept", {"i": i, "text": f"record {i}"})
    lg.close()


# ---------------------------------------------------------------- NUC-2: the cursor


def test_a_warm_open_folds_nothing(tmp_path: Path) -> None:
    """The property the whole slice is for: reopening does not re-read history."""
    n = Nucleus(tmp_path, "r/c/0")
    for i in range(50):
        n.append("percept", {"i": i})
    head = n.ledger.seq
    n.close()

    reopened = Nucleus(tmp_path, "r/c/0")
    assert reopened.cursor() == head
    assert reopened.fold() == 0, "a warm open folded records it had already folded"
    assert reopened._max_seq() == head
    reopened.close()


def test_an_open_folds_only_what_is_new(tmp_path: Path) -> None:
    """Records appended behind the render's back are folded — and only those."""
    n = Nucleus(tmp_path, "r/c/0")
    n.append("percept", {"i": 0})
    n.close()

    # Another writer appends straight to the ledger; the render knows nothing about it.
    lg = Ledger(tmp_path / "r/c/0" / "ledger.jsonl", claim_id="r/c/0")
    for i in range(5):
        lg.append("percept", {"late": i})
    lg.close()

    reopened = Nucleus(tmp_path, "r/c/0")
    assert reopened.fold() == 0, "the open should already have folded them"
    assert reopened._max_seq() == reopened.ledger.seq
    reopened.close()


def test_a_deleted_index_still_costs_only_speed(tmp_path: Path) -> None:
    """A13: the render is derivable. Losing it must lose nothing but time."""
    _seed(tmp_path, "r/c/0", 200)
    first = Nucleus(tmp_path, "r/c/0")
    digest, head = first.render_digest(), first.ledger.seq
    first.close()

    (tmp_path / "r/c/0" / "index.db").unlink()
    rebuilt = Nucleus(tmp_path, "r/c/0")
    assert rebuilt.render_digest() == digest and rebuilt._max_seq() == head
    rebuilt.close()


# ---------------------------------------------------------------- NUC-2: digest agreement


def test_two_local_rebuilds_and_a_second_machine_agree(tmp_path: Path) -> None:
    """The bar: 2x local + 1x second-machine rebuild produce identical digests over 10 K records."""
    _seed(tmp_path / "a", "r/c/0", 10_000)

    n1 = Nucleus(tmp_path / "a", "r/c/0")
    d1 = n1.render_digest()
    n1.rebuild()
    d2 = n1.render_digest()
    n1.close()

    # "Second machine": a different path, a cold index, the same ledger bytes.
    (tmp_path / "b" / "r/c/0").mkdir(parents=True)
    shutil.copy(tmp_path / "a" / "r/c/0" / "ledger.jsonl", tmp_path / "b" / "r/c/0" / "ledger.jsonl")
    n2 = Nucleus(tmp_path / "b", "r/c/0")
    d3 = n2.render_digest()
    n2.close()

    assert d1 == d2 == d3, "the fold is not deterministic across rebuilds or machines"


def test_the_digest_ignores_timestamps_and_row_order(tmp_path: Path) -> None:
    """Otherwise "identical rebuild" would be a statement about SQLite, not about the fold."""
    _seed(tmp_path, "r/c/0", 20)
    n = Nucleus(tmp_path, "r/c/0")
    before = n.render_digest()

    # Rewrite every ts in the render. Content is untouched, so the digest must not move.
    n._db.execute("UPDATE ledger SET ts='1999-01-01T00:00:00.000Z'")
    n._db.commit()
    assert n.render_digest() == before
    n.close()


def test_the_digest_moves_when_content_moves(tmp_path: Path) -> None:
    _seed(tmp_path, "r/c/0", 20)
    n = Nucleus(tmp_path, "r/c/0")
    before = n.render_digest()
    n._db.execute("UPDATE ledger SET body=? WHERE seq=5", (json.dumps({"tampered": True}),))
    n._db.commit()
    assert n.render_digest() != before
    n.close()


# ---------------------------------------------------------------- NUC-2: corruption, 10/10


@pytest.mark.parametrize("target", list(range(1, 11)))
def test_verify_render_catches_a_corrupted_render(tmp_path: Path, target: int) -> None:
    """10/10 — every seq, corrupted, must be caught by the recorded digest."""
    _seed(tmp_path, "r/c/0", 20)
    n = Nucleus(tmp_path, "r/c/0")
    n.close()

    reopened = Nucleus(tmp_path, "r/c/0")
    ok, why = reopened.verify_render()
    assert ok, why

    reopened._db.execute("UPDATE ledger SET body=? WHERE seq=?", (json.dumps({"bad": target}), target))
    reopened._db.commit()
    ok, why = reopened.verify_render()
    assert not ok and "render corrupted" in why
    reopened.close()


def test_a_corrupted_render_does_not_impugn_the_LEDGER(tmp_path: Path) -> None:
    """The render is a render. Corrupting it must not make the chain look tampered."""
    _seed(tmp_path, "r/c/0", 20)
    n = Nucleus(tmp_path, "r/c/0")
    n.close()

    reopened = Nucleus(tmp_path, "r/c/0")
    reopened._db.execute("UPDATE ledger SET body='{}' WHERE seq=3")
    reopened._db.commit()

    assert not reopened.verify_render()[0], "the render corruption went unnoticed"
    assert reopened.verify().ok, "a bad render made the LEDGER look tampered"
    reopened.close()


# ---------------------------------------------------------------- NUC-2: the 100 K open bar


@pytest.mark.slow
def test_open_p95_under_100ms_at_100k_records_warm(tmp_path: Path) -> None:
    """The bar, at the stated scale. Warm means the cursor is at head, so the open folds nothing."""
    _seed(tmp_path, "r/c/0", 100_000)

    cold = time.perf_counter()
    first = Nucleus(tmp_path, "r/c/0")
    cold_s = time.perf_counter() - cold
    assert first.cursor() == first.ledger.seq
    first.close()

    latencies: list[float] = []
    for _ in range(20):
        started = time.perf_counter()
        n = Nucleus(tmp_path, "r/c/0")
        latencies.append((time.perf_counter() - started) * 1000)
        assert n.fold() == 0
        n._db.close()
        n.ledger.close()

    p95 = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies)
    print(f"\n  100K records: cold open {cold_s:.2f}s, warm open p95 {p95:.1f} ms")
    assert p95 <= 100.0, f"warm open p95 {p95:.1f} ms exceeds the 100 ms bar at 100K records"


# ---------------------------------------------------------------- NUC-7: write amplification


def _durable_writes(monkeypatch: pytest.MonkeyPatch) -> list[int]:
    """Count fsyncs. The bar is about DURABLE writes, so counting anything else would be theatre."""
    import os as _os

    calls: list[int] = []
    real = _os.fsync

    def counted(fd: int) -> None:
        calls.append(fd)
        real(fd)

    monkeypatch.setattr(_os, "fsync", counted)
    return calls


def test_at_most_one_durable_write_per_standard_flush(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Standard records ride the group-commit: many appends, ONE fsync when it drains."""
    n = Nucleus(tmp_path, "r/c/0")
    n.close()

    reopened = Nucleus(tmp_path, "r/c/0")
    calls = _durable_writes(monkeypatch)
    for i in range(32):
        reopened.append("percept", {"i": i}, durability="standard")
    assert calls == [], "a standard append fsynced; that is fsync-always, the null"

    reopened.ledger.flush()
    assert len(calls) == 1, f"{len(calls)} durable writes for one flush; the bar is 1"
    reopened.close()


def test_at_most_two_durable_writes_per_gold(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Gold is durable on return. The bar allows two: the record, and the buffer it drained."""
    n = Nucleus(tmp_path, "r/c/0")
    n.close()

    reopened = Nucleus(tmp_path, "r/c/0")
    calls = _durable_writes(monkeypatch)
    reopened.append("percept", {"pending": True}, durability="standard")
    reopened.append("outcome", {"text": "gold"}, durability="gold")
    assert 1 <= len(calls) <= 2, f"{len(calls)} durable writes for one gold; the bar is <= 2"
    reopened.close()


def test_append_p50_and_p95_within_the_tier_bars(tmp_path: Path) -> None:
    """p50 <= 10 ms, p95 <= 50 ms amortized. A 1 K bench, exactly as the preflight runs it."""
    n = Nucleus(tmp_path, "r/c/0")
    latencies: list[float] = []
    for i in range(1_000):
        started = time.perf_counter()
        n.append("percept", {"i": i})
        latencies.append((time.perf_counter() - started) * 1000)
    n.close()

    p50 = statistics.median(latencies)
    p95 = statistics.quantiles(latencies, n=20)[18]
    print(f"\n  append p50 {p50:.2f} ms, p95 {p95:.2f} ms")
    assert p50 <= 10.0, f"append p50 {p50:.2f} ms exceeds the 10 ms d1 bar"
    assert p95 <= 50.0, f"append p95 {p95:.2f} ms exceeds the 50 ms bar"


def test_the_digest_is_not_recomputed_on_the_append_path(tmp_path: Path) -> None:
    """Stamping the digest per append would be O(history) per write — the amplification NUC-7 bounds.

    So an append clears the digest and the cursor advances; the digest is stamped on fold or close.
    A reader that finds no digest is told so, rather than being handed a stale one.
    """
    n = Nucleus(tmp_path, "r/c/0")
    n.append("percept", {"i": 1})
    ok, why = n.verify_render()
    assert not ok and "not stamped" in why, "the append path stamped a digest"

    n.close()
    reopened = Nucleus(tmp_path, "r/c/0")
    assert reopened.verify_render()[0], "close did not stamp the digest"
    reopened.close()


def test_a_breach_is_visible_rather_than_silent(tmp_path: Path) -> None:
    """NUC-7's last clause: a breach shows as `degraded-persistence`, never as a fabric quietly slow.

    G-FSYNC already measures the box and reports DEGRADED with a fix string; this asserts the two
    halves agree on what "too slow" means, so the guard and the tier bar cannot drift apart.
    """
    from hypercell.substrate.k3s import _FSYNC_P50_BUDGET_MS, g_fsync

    assert _FSYNC_P50_BUDGET_MS == 10.0, "the guard's budget drifted from NUC-7's d1 append bar"
    result = g_fsync(tmp_path)
    assert result.state in {"GREEN", "DEGRADED"}
    if result.state == "DEGRADED":
        assert result.fix, "a degraded persistence report with no fix is a silent breach"
