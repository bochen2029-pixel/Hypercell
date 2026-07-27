"""The trust-tag vocabulary — a stratum, importable by every layer (ARCHITECTURE §3.3).

**Why this file exists.** The tag law is enforced by the Membrane at L2, but it is *spoken* by the
frame assembler at L1 and by the act plane at L3. Under clause C1 — imports point down, strata
excepted — L1 may not import L2, so putting the shared vocabulary in `medium/` made `cell/frame.py`
an illegal edge.

The fix is not to weaken the law. It is to notice that a channel name and a trust tag are **types**,
not enforcement: they belong in `common/`, which the layer law describes as "types, ids, clock,
protocol interfaces". `medium/firewall.py` keeps the part that is genuinely the Medium's — deciding,
at ingress, what a message actually is.

LAYER-1 caught this edge in code written three slices earlier, which is what a falsifier is for.
"""
from __future__ import annotations

from typing import Any, Literal

TrustTag = Literal["control", "data"]
Channel = Literal[
    "operator_command",
    "peer_message",
    "tool_result",
    "retrieved_page",
    "act_result",
    "own_nucleus",
]

#: The ONLY source of control tokens. Widening this set is a constitutional change, not a tweak.
CONTROL_CHANNEL: Channel = "operator_command"

#: Channels whose content the cell did not author and did not witness being authored.
ACQUIRED_CHANNELS = frozenset({"peer_message", "tool_result", "retrieved_page", "act_result"})

#: Fields a sender might try to supply to promote itself. Stripped at ingress, always.
FORGEABLE_FIELDS = frozenset({"trust_tag", "trust", "channel", "origin", "provenance", "control"})


def assign_tag(channel: str | None) -> TrustTag:
    """The coarse decision, binary and structural: `control` iff the operator directive channel.

    Absent or unknown ⇒ `data`. Fail-closed is not caution here, it is the only safe default: an
    unrecognised channel is exactly what a novel attack looks like.
    """
    return "control" if channel == CONTROL_CHANNEL else "data"


def strip_supplied_provenance(body: Any) -> tuple[Any, list[str]]:
    """Remove any provenance a sender tried to supply. Returns `(clean, stripped_keys)`.

    A cell cannot write its own `trust_tag` any more than it can write its own `seq`.
    """
    if not isinstance(body, dict):
        return body, []
    stripped = sorted(k for k in body if k in FORGEABLE_FIELDS)
    if not stripped:
        return body, []
    return {k: v for k, v in body.items() if k not in FORGEABLE_FIELDS}, stripped
