"""The Medium factory. hypercell owns the wire contract; the transport is swappable.

P0/P1: LocalMedium (single-node durable log). P3: a NATS/JetStream transport behind the same shape.
"""
from __future__ import annotations

from pathlib import Path

from .firewall import PostPolicy
from .transport_local import LocalMedium


def open_medium(home: Path | str, *, policy: PostPolicy | None = None) -> LocalMedium:
    """`policy` carries the post-ACL's conditional rows (R14), resolved from the frozen manifest.

    Reachable through the factory because this is the documented entry point: a policy you can only
    set by constructing the transport directly is a policy nobody sets.
    """
    return LocalMedium(home, policy=policy)
