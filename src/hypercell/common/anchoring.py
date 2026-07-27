"""The `Anchoring` protocol — what the Medium needs from the anchor, without importing it.

The anchor log is the **Conductor's** (wire.md §5.4: "The Conductor maintains an anchor log"), and
the Conductor is L3. The Medium is L2, so `medium/transport_local.py` importing
`conductor/anchor.py` would be a forbidden upward edge — LAYER-1 clause C1.

This is the same seam `common/meter.py` opened for the same reason, and the fix the layer law
anticipates by describing `common/` as "types, ids, clock, **protocol interfaces**": the transport
depends on the *shape* of an anchor, and the Conductor's `AnchorLog` satisfies that shape
structurally. No inheritance, no registration — a protocol, which is what lets a lower layer call
upward-provided behaviour without knowing the layer above exists.

A transport with no anchor still works: the chain remains self-consistent, and `verify()` reports
**"consistent, unanchored"** rather than "ok". Optionality is a real deployment mode, not a hole.
"""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Anchoring(Protocol):
    """One checkpoint offer. The implementation decides whether this seq is due for an anchor."""

    def note(self, seq: int, chain_hash: str, *, gold: bool = False, compact: bool = False) -> Any:
        """Offer `(seq, hash)`. MUST write and fsync before returning when `gold` or `compact`.

        The synchronous fsync on gold is the durability edge (§5.4 duty 2): a D-gold post returns
        only after its anchor entry is durable, so gold never has its only copy inside a transport's
        lax-fsync window. Cadence anchors may be buffered; gold and compact may not.
        """
        ...
