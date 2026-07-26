"""Tool profiles (Annex A) and the derived-harm gate — GATE step 1 (contracts/act.md §6.1).

**The null this kills: trust the declaration.** A cell that says "this is an H0 read" and then sends
a POST with a body and a cookie has not lied to a person, it has lied to a predicate — so the
predicate stops asking and starts deriving. Harm is computed from the *shape of the request*:

    harm_derived := profile.harm_floor ⊔ shape(args)

Non-GET/HEAD method, a body, a cell-scoped credential, or state addressing all raise it.

Then the rule that makes the wager cell-authored (adjudication #4):

    declared < derived  ⇒  REFUSE (`reason: harm_derived`)

**never a silent promotion.** Quietly upgrading the harm class and proceeding would be the fabric
deciding, on the cell's behalf, to do something riskier than the cell agreed to. The cell must
re-compose and re-declare, or not act.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Literal

from ..medium.firewall import Trifecta

Harm = Literal["H0", "H1", "H2", "H3"]
_ORDER: dict[Harm, int] = {"H0": 0, "H1": 1, "H2": 2, "H3": 3}

#: Structurally read-only. Anything else is, by shape, capable of changing the world.
READ_METHODS = frozenset({"GET", "HEAD"})

#: Credential shapes a CELL must never supply. The Membrane injects read-scoped credentials; a
#: cell-authored one is an escalation wearing a header.
_CREDENTIAL_KEYS = re.compile(r"(?i)\b(authorization|api[_-]?key|token|secret|password|cookie|session)\b")
_CREDENTIAL_VALUES = re.compile(
    r"(?i)(bearer\s+\S{8,}|sk-[A-Za-z0-9_-]{12,}|gh[pousr]_[A-Za-z0-9]{12,}|AKIA[0-9A-Z]{16})"
)

#: Query/path shapes that address mutable server state rather than a document.
_STATE_ADDRESSING = re.compile(r"(?i)(^|[?&/])(action|cmd|command|exec|delete|update|create|mutate)=")


class ProfileRefusal(Exception):
    """A refused act. Carries the machine reason the receipt must record."""

    def __init__(self, reason: str, detail: str) -> None:
        super().__init__(f"refused/{reason}: {detail}")
        self.reason = reason
        self.detail = detail


def harm_max(a: Harm, b: Harm) -> Harm:
    return a if _ORDER[a] >= _ORDER[b] else b


@dataclass(frozen=True)
class ToolProfile:
    """One Annex A row. `admission_certified` marks adapters whose shape the fabric vouches for."""

    ref: str
    harm_floor: Harm = "H0"
    methods: frozenset[str] = field(default_factory=lambda: READ_METHODS)
    egress_hosts: tuple[str, ...] = ()
    trifecta: Trifecta = field(default_factory=Trifecta)
    admission_certified: bool = False
    args_schema: tuple[str, ...] = ()

    def validate_args(self, args: dict[str, Any]) -> None:
        unknown = sorted(set(args) - set(self.args_schema))
        if self.args_schema and unknown:
            raise ProfileRefusal("args_schema", f"{self.ref} does not accept {unknown}")


#: The three H0 profiles GROUND-0 ships. `web.search`/`web.fetch` reach the world; `fs.read` does not.
ANNEX_A: dict[str, ToolProfile] = {
    "web.search": ToolProfile(
        ref="web.search",
        harm_floor="H0",
        egress_hosts=("*",),
        trifecta=Trifecta(untrusted_content=True, external_comms=True),
        admission_certified=True,
        args_schema=("query", "k"),
    ),
    "web.fetch": ToolProfile(
        ref="web.fetch",
        harm_floor="H0",
        egress_hosts=("*",),
        trifecta=Trifecta(untrusted_content=True, external_comms=True),
        args_schema=("url", "method", "body", "headers"),
    ),
    "fs.read": ToolProfile(
        ref="fs.read",
        harm_floor="H0",
        trifecta=Trifecta(untrusted_content=True),
        args_schema=("path",),
    ),
}


def shape_harm(args: dict[str, Any]) -> tuple[Harm, list[str]]:
    """Derive harm from the REQUEST SHAPE. Returns `(harm, reasons)` — the receipt records both."""
    reasons: list[str] = []
    harm: Harm = "H0"

    method = str(args.get("method", "GET")).upper()
    if method not in READ_METHODS:
        harm = harm_max(harm, "H1")
        reasons.append(f"method={method} is not GET/HEAD")

    if args.get("body"):
        harm = harm_max(harm, "H1")
        reasons.append("a body is present; a read carries no body")

    headers = args.get("headers") or {}
    if isinstance(headers, dict):
        for key, value in headers.items():
            if _CREDENTIAL_KEYS.search(str(key)) or _CREDENTIAL_VALUES.search(str(value)):
                harm = harm_max(harm, "H1")
                reasons.append(f"cell-supplied credential in header '{key}'")
                break

    blob = " ".join(str(v) for v in args.values() if isinstance(v, (str, int, float)))
    if _CREDENTIAL_VALUES.search(blob) or _CREDENTIAL_KEYS.search(str(args.get("url", ""))):
        harm = harm_max(harm, "H1")
        reasons.append("cell-supplied credential in the request line")
    if _STATE_ADDRESSING.search(str(args.get("url", ""))):
        harm = harm_max(harm, "H1")
        reasons.append("the target addresses mutable state, not a document")

    return harm, reasons


@dataclass(frozen=True)
class GateVerdict:
    harm_effective: Harm
    harm_derived: Harm
    reasons: list[str]


def gate(
    *,
    capability_ref: str,
    args: dict[str, Any],
    harm_declared: Harm,
    role_tools: list[str],
    role_harm_ceiling: Harm = "H1",
    role_egress: list[str] | None = None,
    acquired: Trifecta | None = None,
    standing_access: list[str] | None = None,
    waiver: str | None = None,
) -> GateVerdict:
    """GATE, step 1 — static, in-process, and in the order act.md §6.1 sets out."""
    # (a) the capability resolves and the role holds it
    profile = ANNEX_A.get(capability_ref)
    if profile is None:
        raise ProfileRefusal("unknown_capability", f"'{capability_ref}' is not in Annex A")
    if capability_ref not in role_tools:
        raise ProfileRefusal("not_in_role", f"the role does not hold '{capability_ref}'")

    # (b) args validate; cell-supplied credentials are refused outright
    profile.validate_args(args)

    # (c) derive harm from the shape
    harm_derived, reasons = shape_harm(args)
    harm_derived = harm_max(profile.harm_floor, harm_derived)

    # (d) declared < derived => REFUSE. Never a silent promotion: the wager must be cell-authored.
    if _ORDER[harm_declared] < _ORDER[harm_derived]:
        raise ProfileRefusal(
            "harm_derived",
            f"declared {harm_declared} but the request shape derives {harm_derived} "
            f"({'; '.join(reasons)}). Re-compose and re-declare — the fabric will not promote it for you.",
        )
    harm_effective = harm_max(harm_declared, harm_derived)

    # (e) the role's ceiling binds
    if _ORDER[harm_effective] > _ORDER[role_harm_ceiling]:
        raise ProfileRefusal(
            "harm_ceiling", f"{harm_effective} exceeds the role ceiling {role_harm_ceiling}"
        )

    # (f) egress target within the role's allowlist
    if profile.egress_hosts and (url := str(args.get("url", ""))):
        host = url.split("://", 1)[-1].split("/", 1)[0].split(":")[0]
        allow = role_egress or []
        if not any(a == "*" or host == a or (a.startswith("*.") and host.endswith(a[1:])) for a in allow):
            raise ProfileRefusal("egress", f"host '{host}' is not in the role egress allowlist {allow}")

    # (h) the trifecta step — a FOLD, so acquisition since spawn counts
    legs = profile.trifecta | (acquired or Trifecta()) | Trifecta(private_data=bool(standing_access))
    if legs.holds_all_three and not waiver:
        raise ProfileRefusal(
            "trifecta",
            "this act would complete {private_data, untrusted_content, external_comms}; "
            "an exfiltration pipeline is refused regardless of intent",
        )

    return GateVerdict(harm_effective=harm_effective, harm_derived=harm_derived, reasons=reasons)
