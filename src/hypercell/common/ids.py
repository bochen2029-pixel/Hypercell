"""Identity: ULID-ish sortable ids, short ids, and the stable claim-id (contracts/nucleus.md).

A cell is a durable identity, not a process. The claim-id (`run/role/index`) is what a nucleus volume
binds to; `hc resume` re-binds it to a fresh instance. Instance-ids are ephemeral per process.
"""
from __future__ import annotations

import os
import secrets
import string
import time

_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_ALNUM = string.ascii_lowercase + string.digits


def _b32(n: int, length: int) -> str:
    out: list[str] = []
    for _ in range(length):
        out.append(_CROCKFORD[n & 31])
        n >>= 5
    return "".join(reversed(out))


def new_id(prefix: str = "") -> str:
    """A ULID: 48-bit ms time (sortable) + 80-bit randomness, Crockford base32 (26 chars)."""
    ms = time.time_ns() // 1_000_000
    rand = int.from_bytes(os.urandom(10), "big")
    ulid = _b32(ms, 10) + _b32(rand, 16)
    return f"{prefix}{ulid}" if prefix else ulid


def short_id(n: int = 8) -> str:
    """A short collision-resistant handle, [a-z0-9]. ~2.8e12 combos at n=8."""
    return "".join(secrets.choice(_ALNUM) for _ in range(n))


def instance_id() -> str:
    """One ephemeral cell instantiation."""
    return new_id("i_")


def claim_id(run: str, role: str, index: int) -> str:
    """The stable identity a nucleus binds to. Survives crash/reboot; `hc resume` re-binds it."""
    return f"{run}/{role}/{index}"
