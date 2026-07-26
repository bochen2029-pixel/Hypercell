"""WAKE — the doorbell, the fallback, and the zero-token sleep (contracts/wire.md §8; slice M2).

**The null is the fallback, and the fallback is mandatory.** `data_version` slow-polling always
works: SQLite bumps that counter whenever another connection commits, so a waiter can always
discover new records without any cooperation from the poster. It is simply slow.

The doorbell is a *hint* layered on top — one file per culture, touched on every post, checked with
a `stat()` instead of a query. When it works, wake is fast. When it is severed, the fallback still
fires and the only thing lost is latency. That is the property C3 pins: **zero loss, slower only.**

Designing it the other way round — a fast path that is load-bearing and a fallback bolted on — is
how systems acquire silent message loss. Here the correctness path is the one that cannot break,
and the fast path is allowed to fail.

**Zero-token sleep (W1).** A waiting cell burns no model tokens, because waiting is pure I/O and
never enters the cognition seam at all. A sleeping cell costs a `stat()` per tick and nothing else.
That is structural, not a policy anyone has to remember.
"""
from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

#: Doorbell tick — a stat() on one file. Cheap enough to run hot.
HINT_TICK_S = 0.002

#: Fallback tick — the `data_version` poll. This is the NULL: correct, always available, slow.
FALLBACK_TICK_S = 0.05


class Doorbell:
    """One file per culture, touched on post. A hint, never the carrier of a message."""

    def __init__(self, home: Path | str) -> None:
        self.dir = Path(home) / "_medium" / "doorbell"
        self.dir.mkdir(parents=True, exist_ok=True)
        self._severed = False

    def _path(self, culture: str) -> Path:
        return self.dir / f"{culture.replace('/', '_')}.bell"

    def ring(self, culture: str) -> None:
        """Called by `post()`. Best-effort by design: a failed ring must never fail a post."""
        if self._severed:
            return
        try:
            self._path(culture).write_text(str(time.time_ns()), encoding="utf-8")
        except OSError:
            pass  # the fallback will carry it; a doorbell that can break a post is worse than none

    def token(self, culture: str) -> str:
        # A severed doorbell is DEAF as well as mute. `sever_hint()` means "kill watchers", and in a
        # real fleet the writer is a different process that keeps ringing regardless — so severing
        # only the ring would leave this reader still hearing bells and would never exercise the
        # fallback at all.
        if self._severed:
            return ""
        try:
            return self._path(culture).read_text(encoding="utf-8")
        except OSError:
            return ""

    def sever(self) -> None:
        """C3(b) / `sever_hint()`: kill the hint in both directions; leave the log intact."""
        self._severed = True


@dataclass
class WakeStats:
    """What actually woke us. Useful in a drill, and honest in production telemetry."""

    woke_by: str = "timeout"  # doorbell | fallback | immediate | timeout
    waited_s: float = 0.0
    ticks: int = 0


def wait(
    *,
    check: Callable[[], list[dict[str, Any]]],
    doorbell: Doorbell | None = None,
    culture: str = "commons",
    data_version: Callable[[], int] | None = None,
    timeout_s: float = 5.0,
    hint_tick_s: float = HINT_TICK_S,
    fallback_tick_s: float = FALLBACK_TICK_S,
) -> tuple[list[dict[str, Any]], WakeStats]:
    """Block until `check()` returns records, or until `timeout_s`.

    `check` is the only thing that ever decides a message arrived. The doorbell and `data_version`
    decide only *when to look* — so a broken hint costs latency and can never cost a message.
    """
    stats = WakeStats()
    started = time.monotonic()

    found = check()
    if found:
        stats.woke_by = "immediate"
        return found, stats

    bell_token = doorbell.token(culture) if doorbell else ""
    version = data_version() if data_version else 0
    next_fallback = started + fallback_tick_s

    while time.monotonic() - started < timeout_s:
        time.sleep(hint_tick_s)
        stats.ticks += 1
        now = time.monotonic()

        rang = doorbell is not None and doorbell.token(culture) != bell_token
        due = now >= next_fallback
        if due:
            next_fallback = now + fallback_tick_s

        # The fallback also fires when `data_version` moved, which is what makes it the NULL: it
        # needs nothing from the writer.
        moved = False
        if due and data_version is not None:
            current = data_version()
            moved, version = current != version, current

        if rang or moved or due:
            found = check()
            if found:
                stats.woke_by = "doorbell" if rang else "fallback"
                stats.waited_s = time.monotonic() - started
                return found, stats
            if rang and doorbell is not None:
                bell_token = doorbell.token(culture)

    stats.waited_s = time.monotonic() - started
    return [], stats
