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


# ---------------------------------------------------------------------------- Stage-1a: the post-ACL


@dataclass(frozen=True)
class PostPolicy:
    """The run-scoped facts the post-ACL's conditional rows consult (R14).

    **Medium-side state, never a post argument.** A conditional row a caller can widen by passing a
    flag is not an access control, it is a suggestion. `self_clocked_cultures` is set by the
    conductor from the FROZEN manifest (`conductor/manifest.py`), so the declaration is a property
    of the bytes the run started with rather than of whoever happens to be posting.
    """

    self_clocked_cultures: frozenset[str] = frozenset()


#: Rooms a cell may not name. `_ops` is the operator's room -- only authenticated surface principals
#: address it (identity-firewall §10 M13); `_fleet` carries conductor-only decision records (R22).
#: `commons` is reserved as a NAME, not closed: it is the public room, and closing it would leave
#: members nowhere to speak.
_ROOM_PRINCIPALS: dict[str, frozenset[str]] = {
    "_ops": frozenset({"conductor", "operator", "surface"}),
    "_fleet": frozenset({"conductor", "operator"}),
}

#: A `round_open` carrying one of these advances the trust generation, which a self-clocking culture
#: may never do for itself -- that is the whole point of the conditional row.
_GENERATION_KEYS = ("gen", "generation", "oracle_gen")


def check_post(
    culture: str,
    sender: str,
    msg_type: str,
    *,
    body: Any = None,
    policy: PostPolicy | None = None,
) -> None:
    """The Stage-1a post-ACL: who may mint what, and where. Raises `AclDenied`.

    **The mint-principal is the ACL key** (identity-firewall §B.9): who may witness a thing is
    decided by *type*, never by parsing a body `subject`. The null this replaces is v1's
    sender-trusting `is_directive` -- a predicate that asked the message who sent it and believed
    the answer, which in a multi-pod deployment is no check at all.

    Two homes, no second copy: `wire.REGISTRY` is the registration/grammar home and the ONE
    privilege source of truth (wire.md §3, R14); this function states the security law OVER those
    rows -- the three conditional ones and the reserved rooms -- and never re-defines them.
    """
    from .wire import CONDITIONAL_ROWS, AclDenied, check_acl, classify

    cls = classify(sender)

    if msg_type in CONDITIONAL_ROWS and cls != "conductor":
        # The only rows this function may read WIDER than the flat table, and only against the
        # frozen manifest. `check_acl` fails closed on them by design, so the conditional is
        # resolved here instead of there -- a standalone `check_acl` stays the safe answer.
        _check_conditional(culture, cls, msg_type, body, policy or PostPolicy())
    else:
        # The flat per-type row. Everything below narrows it; nothing below widens it.
        check_acl(msg_type, sender)

    allowed_here = _ROOM_PRINCIPALS.get(culture)
    if allowed_here is not None and cls not in allowed_here:
        raise AclDenied(
            f"a '{cls}' principal may not name the '{culture}' room "
            f"(allowed: {sorted(allowed_here)}). Naming a room is addressing it: a cell that can "
            "post to the operator's room can impersonate the operator's own channel."
        )

    if msg_type == "presence" and _phase(body) == "genesis":
        # Non-genesis phases (announce/spawned/depart) are open to any member -- a cell must be able
        # to say it has arrived. Genesis is the culture coming into existence, which is not a claim a
        # member gets to make about itself.
        if cls not in ("conductor", "operator"):
            raise AclDenied(
                f"a '{cls}' principal may not mint presence{{phase: genesis}} "
                "(allowed: ['conductor', 'operator']); later phases are open to any member"
            )

    if msg_type == "act_receipt":
        _check_act_receipt(sender, body, cls)


def _check_conditional(
    culture: str, cls: str, msg_type: str, body: Any, policy: PostPolicy
) -> None:
    """Resolve a conditional privilege row (R14) against the frozen manifest.

    Today that is `round_open` alone: conductor by default, self-clocked only where the run manifest
    declares it, and then **never carrying a generation bump**. Clocking your own rounds is
    scheduling; advancing the trust generation is a conductor act, and a culture that could do both
    could grade itself.
    """
    from .wire import AclDenied

    if culture not in policy.self_clocked_cultures:
        raise AclDenied(
            f"a '{cls}' principal may not post '{msg_type}' in '{culture}': self-clocking is only "
            "available where the FROZEN run manifest declares it (R14)"
        )
    carried = [k for k in _GENERATION_KEYS if isinstance(body, dict) and k in body]
    if carried:
        raise AclDenied(
            f"a self-clocked '{msg_type}' may never carry a generation bump (found {carried}). "
            "A culture may schedule itself; it may not promote itself."
        )


def _phase(body: Any) -> str:
    return str(body.get("phase", "")) if isinstance(body, dict) else ""


def _check_act_receipt(sender: str, body: Any, cls: str) -> None:
    """A5: **no act reports itself.** The acting cell mints `act`; the executor mints the receipt.

    The flat row already keeps the cell CLASS out. This adds the identity half, which the class
    check cannot see: that the receipt names the principal actually posting it, and that the
    principal is not the cell whose act it reports. Without it, `runner-1` could witness `runner-2`'s
    work, which is the F3 spoof one level up -- a compromised principal writing world-witnesses for
    somebody else.
    """
    from .wire import AclDenied

    if not isinstance(body, dict):
        return

    named = body.get("executor")
    if isinstance(named, str) and named and named != sender:
        raise AclDenied(
            f"'{sender}' posted an act_receipt attributed to executor '{named}'. A witness signs "
            "its own name or it is not a witness."
        )

    actor = body.get("actor")
    if isinstance(actor, str) and actor and _same_cell(actor, sender):
        raise AclDenied(
            f"'{sender}' may not mint the act_receipt for its own act (actor '{actor}'): no act "
            f"reports itself (A5). The acting cell mints `act`; a distinct executor principal "
            f"mints the world-side receipt. Class '{cls}' does not exempt it."
        )


def _same_cell(actor: str, sender: str) -> bool:
    """Is `sender` the acting cell itself, rather than a distinct principal acting for it?

    `r1/refiner/0` and `r1/refiner/0` are the same cell; `r1/refiner/0/executor` is the in-process
    executor, which at T0 is convention (red-teamed by HC-7-v2 attempt 8) and at Stage-1a+ is a
    distinct principal the ACL can see. Distinctness is the whole mechanism, so it is compared
    exactly rather than by prefix.
    """
    return actor == sender
