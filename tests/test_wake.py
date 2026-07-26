"""C3 / W1 — WAKE (contracts/wire.md §8; slice M2).

C3's bar: a waiter in `wait(types=[round_open])` — (a) p95 post→wake ≤ 200 ms on T0 over 100
trials; (b) after `sever_hint()`, still received within one fallback tick — **zero loss, slower
only**.

W1 adds: the token meter is flat over an idle hour — *a sleeping cell is zero LLM tokens.*

**The null is the `data_version` slow-poll, and it is MANDATORY.** That inversion is the design:
the correctness path is the one that cannot break, and the fast path (the doorbell) is allowed to
fail. Building it the other way round — a load-bearing fast path with a fallback bolted on — is how
systems acquire silent message loss.
"""
from __future__ import annotations

import statistics
import threading
import time
from pathlib import Path

import pytest

from hypercell.medium.transport_local import Filter, LocalMedium
from hypercell.medium.wake import Doorbell, wait
from hypercell.medium.wire import AclDenied


@pytest.fixture
def med(tmp_path: Path) -> LocalMedium:
    return LocalMedium(tmp_path)


ROUND_OPEN = Filter(types=("round_open",))


def _post_soon(home: Path, delay_s: float = 0.01, body: dict | None = None) -> threading.Thread:
    """Post from a SEPARATE connection, which is what production does anyway.

    SQLite objects are thread-bound, so the poster opens its own `LocalMedium` on the same home.
    That is not a test workaround — in the fabric the poster is a different process from the waiter,
    and `PRAGMA data_version` only moves for commits made on ANOTHER connection. A single-connection
    drill would never exercise the fallback at all.
    """

    def go() -> None:
        time.sleep(delay_s)
        writer = LocalMedium(home)
        writer.post("commons", "conductor", "round_open", body=body or {"goal": "g"}, round=1)
        writer.close()

    t = threading.Thread(target=go, daemon=True)
    t.start()
    return t


# ---------------------------------------------------------------- C3(a): latency


def test_c3a_p95_post_to_wake_under_200ms(med: LocalMedium, tmp_path: Path) -> None:
    """100 trials. The bar is p95 <= 200 ms on T0."""
    latencies: list[float] = []
    for i in range(100):
        started = time.monotonic()
        t = _post_soon(tmp_path, delay_s=0.001, body={"i": i})
        got, stats = med.wait("waiter", "commons", filt=ROUND_OPEN, timeout_s=2.0)
        latencies.append((time.monotonic() - started) * 1000)
        t.join()
        assert got, f"trial {i} woke with nothing"

    p95 = statistics.quantiles(latencies, n=20)[18]
    assert p95 <= 200.0, f"p95 {p95:.1f} ms exceeds the 200 ms T0 bar"


def test_records_already_present_return_immediately(med: LocalMedium) -> None:
    """A waiter must not sleep for something already in the log."""
    med.post("commons", "conductor", "round_open", body={"goal": "g"})
    got, stats = med.wait("w", "commons", filt=ROUND_OPEN, timeout_s=1.0)
    assert got and stats.woke_by == "immediate"


def test_the_doorbell_is_what_makes_it_fast(med: LocalMedium, tmp_path: Path) -> None:
    t = _post_soon(tmp_path, delay_s=0.005)
    got, stats = med.wait("w", "commons", filt=ROUND_OPEN, timeout_s=2.0, fallback_tick_s=5.0)
    t.join()
    assert got and stats.woke_by == "doorbell", "the fast path did not fire"


# ---------------------------------------------------------------- C3(b): severed hint


def test_c3b_severed_hint_still_delivers_zero_loss(med: LocalMedium, tmp_path: Path) -> None:
    """The bar, exactly: kill the hint and everything still arrives — slower only, never lost."""
    med.sever_hint()
    t = _post_soon(tmp_path, delay_s=0.005, body={"after": "sever"})
    got, stats = med.wait("w", "commons", filt=ROUND_OPEN, timeout_s=2.0, fallback_tick_s=0.05)
    t.join()

    assert got, "a severed doorbell lost a message — the fallback is not load-bearing"
    assert got[0]["body"] == {"after": "sever"}
    assert stats.woke_by == "fallback"


def test_c3b_severed_hint_delivers_within_one_fallback_tick(med: LocalMedium, tmp_path: Path) -> None:
    med.sever_hint()
    tick = 0.05
    t = _post_soon(tmp_path, delay_s=0.001)
    started = time.monotonic()
    got, _ = med.wait("w", "commons", filt=ROUND_OPEN, timeout_s=2.0, fallback_tick_s=tick)
    elapsed = time.monotonic() - started
    t.join()
    assert got and elapsed <= tick * 4, f"took {elapsed * 1000:.0f} ms, over one fallback tick"


def test_no_message_is_lost_across_a_burst_with_the_hint_severed(med: LocalMedium) -> None:
    """The property that matters is COMPLETENESS, not latency: every record must be delivered once."""
    med.sever_hint()
    for i in range(50):
        med.post("commons", "conductor", "round_open", body={"i": i}, round=1)

    seen: list[int] = []
    while True:
        got, _ = med.wait("w", "commons", filt=ROUND_OPEN, timeout_s=0.2, fallback_tick_s=0.01)
        if not got:
            break
        seen.extend(m["body"]["i"] for m in got)
    assert seen == list(range(50)), "the fallback dropped or duplicated records"


# ---------------------------------------------------------------- the hint may fail, never lie


def test_a_doorbell_that_cannot_write_does_not_break_a_post(tmp_path: Path) -> None:
    """A hint that can fail a post is worse than no hint at all."""
    med = LocalMedium(tmp_path)
    med._doorbell.dir = tmp_path / "does" / "not" / "exist"  # writes will raise OSError
    assert med.post("commons", "conductor", "round_open", body={"x": 1}).seq == 1


def test_the_bell_rings_after_the_commit_not_before(tmp_path: Path) -> None:
    """A bell for a record that then rolls back would wake a reader to find nothing.

    A hint that LIES is worse than one that is slow, so the ring happens strictly after COMMIT.
    """
    med = LocalMedium(tmp_path)
    bell = Doorbell(tmp_path)
    before = bell.token("commons")
    with pytest.raises(AclDenied):
        med.post("commons", "cell0", "verdict", body={})  # never reaches the insert
    assert bell.token("commons") == before, "a refused post rang the bell"


# ---------------------------------------------------------------- W1: zero-token sleep


def test_a_waiting_cell_burns_no_model_tokens(med: LocalMedium) -> None:
    """W1: the token meter is flat over idle. Waiting is pure I/O; it never enters the seam."""
    from hypercell.cognition.mock import MockCognition

    cog = MockCognition()
    got, stats = med.wait("w", "commons", filt=ROUND_OPEN, timeout_s=0.15, fallback_tick_s=0.02)
    assert got == []
    assert cog.calls == 0, "a sleeping cell called a model"
    assert stats.ticks > 0, "the waiter never actually ticked"


def test_wait_returns_empty_on_timeout_rather_than_raising(med: LocalMedium) -> None:
    """A timeout is a normal outcome for a waiter — nothing arrived, which is information."""
    got, stats = med.wait("w", "commons", filt=ROUND_OPEN, timeout_s=0.1)
    assert got == [] and stats.woke_by == "timeout"


def test_wait_advances_the_cursor_so_a_waiter_never_re_reads(med: LocalMedium) -> None:
    med.post("commons", "conductor", "round_open", body={"i": 1})
    first, _ = med.wait("w", "commons", filt=ROUND_OPEN, timeout_s=0.5)
    second, _ = med.wait("w", "commons", filt=ROUND_OPEN, timeout_s=0.1)
    assert len(first) == 1 and second == []


# ---------------------------------------------------------------- the fallback in isolation


def test_the_fallback_alone_is_sufficient() -> None:
    """The null, run with no doorbell at all: correct, always available, slow. That is the point."""
    box: list[dict] = []
    got, stats = wait(
        check=lambda: list(box),
        doorbell=None,
        data_version=lambda: len(box),
        timeout_s=1.0,
        fallback_tick_s=0.01,
    )
    assert got == [] and stats.woke_by == "timeout"

    box.append({"seq": 1})
    got, stats = wait(
        check=lambda: list(box), doorbell=None, data_version=lambda: len(box), timeout_s=1.0
    )
    assert got and stats.woke_by == "immediate"
