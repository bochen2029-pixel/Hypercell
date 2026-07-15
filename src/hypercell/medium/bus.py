"""The Medium factory. hypercell owns the wire contract; the transport is swappable.

P0/P1: LocalMedium (single-node durable log). P3: a NATS/JetStream transport behind the same shape.
"""
from __future__ import annotations

from pathlib import Path

from .transport_local import LocalMedium


def open_medium(home: Path | str) -> LocalMedium:
    return LocalMedium(home)
