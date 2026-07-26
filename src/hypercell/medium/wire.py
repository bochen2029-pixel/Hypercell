"""The wire tables — ONE source for the envelope, the registry, the ACL (contracts/wire.md).

Every table the Medium enforces lives here and nowhere else. The reason is E1: v1 kept the type
list in three places and they drifted, so a "12-type registry" was really three different registries
that agreed on most days.

Three laws this module encodes:

* **16 fixed columns.** Anything beyond the set is a wire MAJOR bump, not a convenience.
* **The ACL is a correctness mechanism, not a security one.** Authenticating a sender is seat 10's
  identity ladder; this gate runs regardless, at every stage, because a `receipt` posted by a cell
  is wrong even when the cell is honest — it is a claim the cell is not entitled to make.
* **Void-at-fold.** A record that slips past the client gate is not deleted (an append-only log
  cannot un-say anything). It is *excluded from every constitutional fold* and named by
  `verify().void_by_acl`. The log stays truthful about what was attempted.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

Durability = Literal["gold", "chatter"]
Retention = Literal["forever", "run", "decay"]

#: The 16 fixed columns, in order (§2). `sig` and `redactions` are RESERVED, not present.
COLUMNS = (
    "seq", "ts", "culture", "sender", "recipient", "type", "reply_to", "round",
    "priority", "origin", "idem", "corr", "mentions", "body", "artifact", "hash",
)

#: Reserved culture names (R22). `_fleet` sits beside `_ops` for conductor-only decision records.
RESERVED_CULTURES = frozenset({"commons", "_ops", "_fleet"})

#: Soft cap warns; hard cap refuses and tells you to use an artifact.
BODY_SOFT_CAP = 4 * 1024
BODY_HARD_CAP = 32 * 1024


@dataclass(frozen=True)
class TypeSpec:
    name: str
    may_post: frozenset[str]  # principal CLASSES; empty = any
    durability: Durability
    retention: Retention
    meaning: str


def _t(name: str, may: tuple[str, ...], dur: Durability, ret: Retention, meaning: str) -> TypeSpec:
    return TypeSpec(name, frozenset(may), dur, ret, meaning)


#: The 17-type registry (§3). Principal classes: cell | conductor | operator | executor | surface.
REGISTRY: dict[str, TypeSpec] = {
    s.name: s
    for s in (
        _t("presence", (), "chatter", "run", "arrival/departure; genesis is conductor/operator only"),
        _t("chat", (), "chatter", "decay", "freeform; DATA, never instruction"),
        _t("status", (), "chatter", "decay", "progress/blocked/metric/preflight note; DATA"),
        _t("task", ("conductor", "operator"), "chatter", "run", "claimable work"),
        _t("claim", (), "chatter", "run", "log-derived CAS on a task or named resource"),
        _t("submission", ("cell",), "chatter", "run", "a candidate; round set; evidence[]"),
        _t("receipt", ("conductor",), "gold", "forever", "the oracle's grading of a submission/act/intake"),
        _t("round_open", ("conductor",), "chatter", "run", "opens round N"),
        _t("verdict", ("conductor",), "gold", "forever", "closes a run; kind + vs_null"),
        _t("handoff", ("cell",), "gold", "run", "state package for a successor"),
        _t("command", ("operator", "conductor", "surface"), "gold", "forever", "the ONLY instruction-bearing type"),
        _t("cmd_receipt", ("conductor",), "gold", "forever", "the command plane's ack/result"),
        _t("act", ("cell",), "chatter", "run", "world-touching intent"),
        _t("act_receipt", ("conductor", "executor"), "gold", "forever", "what the world did — never the acting cell"),
        _t("oracle_gen", ("conductor",), "gold", "forever", "a trust-plane growth event"),
        _t("oracle_gap", ("cell",), "chatter", "run", "receipt-contradicting evidence; DATA-class hint"),
        _t("compact", ("conductor",), "gold", "forever", "a retention event: dropped/archived spans + Merkle roots"),
    )
}

#: Rows whose privilege is CONDITIONAL, not flat (R14). A table of principal classes cannot express
#: "conductor by default, unless the bytes the run froze declare otherwise", so those rows are
#: resolved by the security law in `firewall.check_post` — the ONE place allowed to read a row wider
#: than this table does, and only against the frozen manifest, never against the poster. Listing
#: them here keeps the table the source of truth: the firewall asserts membership before widening,
#: so the two cannot drift apart in silence.
CONDITIONAL_ROWS = frozenset({"round_open"})

#: The warrant-class set — mint-restricted types that CERTIFY a boundary crossing (§3, the HOME).
#: `oracle_gen`/`compact` are mint-restricted but certify no crossing, so they are excluded.
NON_MINTABLE = frozenset({"receipt", "act_receipt", "verdict", "command", "cmd_receipt"})


class AclDenied(Exception):
    """The client gate refused the post. C11's expected answer."""


class MediumBusy(Exception):
    """Backpressure, stated explicitly rather than by silently dropping (C10)."""


def classify(sender: str) -> str:
    """Principal class from the sender string. **Unregistered senders class as `cell`** (least trust)."""
    if sender == "operator":
        return "operator"
    if sender == "conductor":
        return "conductor"
    if sender.startswith("runner-") or sender.endswith("/executor"):
        return "executor"
    if sender.startswith("surface:"):
        return "surface"
    return "cell"


def is_known(msg_type: str) -> bool:
    """`x-*` is an extension: unknown but legal, delivered and ignorable (C7 liberal receiver)."""
    return msg_type in REGISTRY or msg_type.startswith("x-")


def check_acl(msg_type: str, sender: str) -> None:
    """The client gate. Raises `AclDenied`; a record that gets past it anyway is void-at-fold."""
    if msg_type.startswith("x-"):
        return
    spec = REGISTRY.get(msg_type)
    if spec is None:
        raise AclDenied(f"'{msg_type}' is not in the registry and is not an x- extension")
    if spec.may_post and classify(sender) not in spec.may_post:
        raise AclDenied(
            f"a '{classify(sender)}' principal may not post '{msg_type}' "
            f"(allowed: {sorted(spec.may_post)}). This is a correctness gate, not an authn one: "
            f"the claim is one this principal is not entitled to make, however honest it is."
        )


def durability_of(msg_type: str, body: Any = None) -> Durability:
    """Gold or chatter. H0 acts ride chatter; H1+ acts are gold, so the body decides for `act`."""
    spec = REGISTRY.get(msg_type)
    if spec is None:
        return "chatter"
    if msg_type in ("act", "act_receipt") and isinstance(body, dict):
        return "chatter" if str(body.get("harm_effective", "H0")) == "H0" else "gold"
    if msg_type == "presence" and isinstance(body, dict) and body.get("forked_from"):
        return "gold"
    return spec.durability


def void_at_fold(
    msg_type: str, sender: str, *, culture: str = "commons", body: Any = None, policy: Any = None
) -> bool:
    """Would this record be excluded from every constitutional fold? (C11's second half.)

    Delegates to the Stage-1a post-ACL rather than re-deciding with the flat row, so **the void set
    is exactly the refused set**. Two predicates would leave a gap between "the gate refuses it" and
    "it does not count", and that gap is the whole prize for a record smuggled past the gate.

    Imported locally: `firewall` states the security law over this table, so it imports this module,
    not the other way round.
    """
    from .firewall import check_post

    try:
        check_post(culture, sender, msg_type, body=body, policy=policy)
    except AclDenied:
        return True
    return False
