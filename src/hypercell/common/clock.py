"""Time discipline: the Medium and the nucleus stamp time, never the cell (contracts/wire.md)."""
from __future__ import annotations

import time
from datetime import UTC, datetime


def now_iso() -> str:
    """UTC ISO-8601 with milliseconds, e.g. 2026-07-15T05:03:48.123Z."""
    dt = datetime.now(UTC)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


def mono() -> float:
    """Monotonic seconds for within-epoch ordering (resets across boots; use with a boot id)."""
    return time.monotonic()
