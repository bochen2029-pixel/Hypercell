"""The Stage-0 firewall — the tag law and the lethal-trifecta gate (contracts/identity-firewall.md).

**The firewall is not a filter that inspects content.** It never asks "does this text look like an
instruction?" — that question has no reliable answer, and every system that has tried to answer it
has been defeated by an encoding trick. It labels *provenance*, structurally, from the channel the
bytes arrived on. Content is then free to say whatever it likes, because nothing it says can change
what it is.

Two rules carry the whole design:

* **Tags are transport-ASSIGNED** — envelope metadata like `seq` and `ts`, set by the Membrane,
  **never a body convention and never sender-suppliable**. If a tag could be read from a message
  body or a self-declared `origin`, the old sender-trusting bug would simply regrow one level up,
  inside the frame.
* **Fail-closed.** An unknown or absent channel is `data`, never `control` (B.0.1). The failure mode
  of guessing wrong in the safe direction is a refused instruction; in the unsafe direction it is an
  attacker's text executing.

There is exactly one control channel. Everything else — peer messages, tool results, retrieved
pages, act results, the cell's own memories — is data.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# The tag VOCABULARY is a stratum (`common/trust.py`) so L1 may speak it without importing L2 --
# LAYER-1 clause C1. Enforcement -- deciding at ingress what a message actually is -- stays here.
from ..common.trust import (  # noqa: F401  (re-exported: medium is the tag law's public face)
    ACQUIRED_CHANNELS,
    CONTROL_CHANNEL,
    FORGEABLE_FIELDS,
    Channel,
    TrustTag,
    assign_tag,
    strip_supplied_provenance,
)

# ---------------------------------------------------------------------------- the lethal trifecta


class TrifectaRefusal(Exception):
    """Refused: the role would hold all three legs at once. `refused/trifecta`."""

    def __init__(self, legs: Trifecta, stage: str) -> None:
        super().__init__(
            f"refused/trifecta at {stage}: private_data={legs.private_data}, "
            f"untrusted_content={legs.untrusted_content}, external_comms={legs.external_comms} — "
            "a role that reads private data, ingests untrusted content, and can talk to an unpinned "
            "destination is an exfiltration pipeline regardless of intent"
        )
        self.legs = legs
        self.stage = stage


@dataclass(frozen=True)
class Trifecta:
    """Three booleans, computed structurally, never by a classifier."""

    private_data: bool = False
    untrusted_content: bool = False
    external_comms: bool = False

    @property
    def holds_all_three(self) -> bool:
        return self.private_data and self.untrusted_content and self.external_comms

    def __or__(self, other: Trifecta) -> Trifecta:
        """Folds are monotone: a leg that became true never becomes false again within a life."""
        return Trifecta(
            private_data=self.private_data or other.private_data,
            untrusted_content=self.untrusted_content or other.untrusted_content,
            external_comms=self.external_comms or other.external_comms,
        )

    def dominates(self, other: Trifecta) -> bool:
        """True when `self` claims at least as much as `other` on every leg."""
        return (
            self.private_data >= other.private_data
            and self.untrusted_content >= other.untrusted_content
            and self.external_comms >= other.external_comms
        )


def spawn_trifecta(
    *,
    standing_access: list[str] | None = None,
    tool_profiles: list[dict[str, Any]] | None = None,
    egress: list[str] | None = None,
) -> Trifecta:
    """Leg 1 — spawn time. Computed from the role manifest plus the tool-profile trifecta annex."""
    profiles = tool_profiles or []
    return Trifecta(
        private_data=bool(standing_access) or any(p.get("private_data") for p in profiles),
        untrusted_content=any(p.get("untrusted_content") for p in profiles),
        # An egress allowlist is a PIN. An empty-but-present allowlist pins nothing reachable;
        # a wildcard or a profile that can post anywhere is an unpinned destination.
        external_comms=any(p.get("external_comms") for p in profiles) or _unpinned(egress),
    )


def _unpinned(egress: list[str] | None) -> bool:
    return any(host in ("*", "") or host.startswith("*") for host in (egress or []))


def ingress_trifecta(
    declared: Trifecta,
    *,
    received_peer_output: bool = False,
    operator_memory_grant: bool = False,
    exec_ok_receipts: int = 0,
    egress_grants: list[str] | None = None,
) -> Trifecta:
    """Leg 2 — ingress time. **All three booleans are folds, re-evaluated at every ingress.**

    Spawn booleans go stale the moment content is acquired, and not only `untrusted_content`: a
    cross-pollination or handoff packet completes the trifecta as surely as a fetch does. Computing
    only the leg you expected to move is how a gate passes something it should have caught.
    """
    return declared | Trifecta(
        private_data=received_peer_output or operator_memory_grant,
        untrusted_content=exec_ok_receipts > 0,
        external_comms=bool(egress_grants),
    )


def gate(legs: Trifecta, *, stage: str, waiver: str | None = None) -> Trifecta:
    """Refuse when the fold shows all three, regardless of which channel set the third."""
    if legs.holds_all_three and not waiver:
        raise TrifectaRefusal(legs, stage)
    return legs


def check_declaration(declared: Trifecta, recomputed: Trifecta) -> None:
    """The declared profile trifecta is **ADVISORY**; the gate recomputes and wins.

    A profile that under-declares is not merely inaccurate — under-declaration is the shape an
    attack takes, so it is refused rather than corrected.
    """
    if not declared.dominates(recomputed):
        raise TrifectaRefusal(recomputed, "declaration weaker than recomputation")
