"""The ACT-PIPELINE — the only path to the world (contracts/act.md §6).

    composed → 1 GATE → 2 ESCROW → 3 EFFECT-RESERVE → 4 JOURNAL(fsync) → 5 EXECUTE → 6 RECEIPT → 7 SETTLE
                 └─ REFUSE (any gate predicate) → act_receipt{refused, reason}

Two things about that diagram are the whole design.

**JOURNAL comes before EXECUTE.** The intent is durable before the world is touched, so a crash
between them leaves a record saying "we were about to do this" rather than silence. Silence is
indistinguishable from never having tried, and that ambiguity is what makes exactly-once impossible.

**Refusals are receipts.** A refused act writes an `act_receipt{exec: refused, reason}` exactly like
a successful one. A gate that refuses silently teaches nobody and audits to nothing — you cannot
later ask "how often does this fire?" of an event that left no trace.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..cell.nucleus import Nucleus
from ..common import ids
from ..conductor.governor import Escrow
from ..medium.firewall import Trifecta
from .adapters import AdapterError, fs_read, scrub, web_fetch, web_search
from .profiles import ANNEX_A, GateVerdict, Harm, ProfileRefusal, gate
from .store import ArtifactStore

_ADAPTERS = {"fs.read": fs_read, "web.fetch": web_fetch, "web.search": web_search}


@dataclass
class ActReceipt:
    """What happened, or what was refused and why. Both are receipts."""

    corr: str
    capability_ref: str
    exec: str  # ok | refused | failed
    harm_effective: Harm = "H0"
    harm_derived: Harm = "H0"
    reason: str = ""
    detail: str = ""
    artifact_uri: str | None = None
    sha256: str | None = None
    provenance: dict[str, Any] = field(default_factory=dict)
    cost: dict[str, Any] = field(default_factory=dict)
    scrubbed: bool = False

    @property
    def uri(self) -> str:
        return f"act://{self.corr}"

    def as_body(self) -> dict[str, Any]:
        return {
            "verb": "act",
            "corr": self.corr,
            "capability_ref": self.capability_ref,
            "exec": self.exec,
            "harm_effective": self.harm_effective,
            "harm_derived": self.harm_derived,
            "reason": self.reason,
            "detail": self.detail,
            "artifact": self.artifact_uri,
            "sha256": self.sha256,
            "provenance": self.provenance,
            "cost": self.cost,
            "scrubbed": self.scrubbed,
        }


class ActExecutor:
    """Runs the H0 leg of the pipeline. H1+ journals and holds; that lands with ACT-1 at b′."""

    def __init__(
        self,
        nucleus: Nucleus,
        *,
        home: Path | str = ".",
        escrow: Escrow | None = None,
        role_tools: list[str] | None = None,
        role_harm_ceiling: Harm = "H0",
        role_egress: list[str] | None = None,
        standing_access: list[str] | None = None,
    ) -> None:
        self.nucleus = nucleus
        self.store = ArtifactStore(home)
        self.escrow = escrow
        self.role_tools = role_tools if role_tools is not None else list(ANNEX_A)
        self.role_harm_ceiling = role_harm_ceiling
        self.role_egress = role_egress if role_egress is not None else ["*"]
        self.standing_access = standing_access or []

    # ---------------------------------------------------------------- the acquired-trifecta fold

    def acquired_trifecta(self) -> Trifecta:
        """A FOLD over this cell's exec-ok receipts since spawn — a log query, not a monitor.

        `untrusted_content` is ACQUIRED on the first world-content fetch, so a cell that has already
        read the web carries that leg into every later gate whether or not anyone remembered to
        update a flag.
        """
        legs = Trifecta()
        for rec in self.nucleus.records_of_kind("act_receipt"):
            body = rec["body"]
            if body.get("exec") != "ok":
                continue
            profile = ANNEX_A.get(str(body.get("capability_ref", "")))
            if profile is not None:
                legs = legs | profile.trifecta
        return legs

    # ---------------------------------------------------------------- the pipeline

    def act(
        self,
        capability_ref: str,
        args: dict[str, Any],
        *,
        harm_declared: Harm = "H0",
        idem: str | None = None,
        waiver: str | None = None,
    ) -> ActReceipt:
        corr = idem or ids.new_id("act_")

        # ---- step 1: GATE. Every refusal below writes a receipt and touches nothing.
        try:
            verdict: GateVerdict = gate(
                capability_ref=capability_ref,
                args=args,
                harm_declared=harm_declared,
                role_tools=self.role_tools,
                role_harm_ceiling=self.role_harm_ceiling,
                role_egress=self.role_egress,
                acquired=self.acquired_trifecta(),
                standing_access=self.standing_access,
                waiver=waiver,
            )
        except ProfileRefusal as refusal:
            return self._write(
                ActReceipt(
                    corr=corr,
                    capability_ref=capability_ref,
                    exec="refused",
                    reason=refusal.reason,
                    detail=refusal.detail,
                    provenance=scrub({"args": args}),
                    scrubbed=True,
                )
            )

        # ---- step 2/3: ESCROW + EFFECT-RESERVE. H0 rides a lease so grounding does not serialize.
        resv_id = None
        if self.escrow is not None and self.escrow.leaseable(capability_ref, harm=verdict.harm_effective):
            resv_id = self.escrow.grant_lease(holder=self.nucleus.claim_id, lane=capability_ref).resv_id

        # ---- step 4: JOURNAL(fsync) BEFORE the world is touched.
        self.nucleus.append(
            "action",
            {"verb": "act", "capability_ref": capability_ref, "args": scrub(args), "corr": corr},
            idem=corr,
            durability="gold",
        )

        # ---- step 5: EXECUTE
        try:
            content, mime, provenance = _ADAPTERS[capability_ref].execute(args)
        except (AdapterError, KeyError, OSError) as exc:
            return self._write(
                ActReceipt(
                    corr=corr,
                    capability_ref=capability_ref,
                    exec="failed",
                    harm_effective=verdict.harm_effective,
                    harm_derived=verdict.harm_derived,
                    reason="adapter_error",
                    detail=str(exc),
                    scrubbed=True,
                ),
                idem=corr,
            )

        # ---- step 6: RECEIPT, with the bytes content-addressed so the citation cannot drift
        artifact = self.store.put(content, mime=mime)
        receipt = ActReceipt(
            corr=corr,
            capability_ref=capability_ref,
            exec="ok",
            harm_effective=verdict.harm_effective,
            harm_derived=verdict.harm_derived,
            artifact_uri=artifact.uri,
            sha256=artifact.sha256,
            provenance=scrub(provenance),
            cost={"resv_id": resv_id} if resv_id else {},
            scrubbed=True,
        )

        # ---- step 7: SETTLE
        if resv_id and self.escrow is not None:
            self.escrow.draw(resv_id, 0.0)
        return self._write(receipt, idem=corr)

    def _write(self, receipt: ActReceipt, *, idem: str | None = None) -> ActReceipt:
        """Every outcome is journaled — an ok, a failure, and above all a refusal."""
        self.nucleus.append("act_receipt", receipt.as_body(), idem=idem or receipt.corr, durability="gold")
        return receipt

    # ---------------------------------------------------------------- reading back

    def receipt(self, corr_or_uri: str) -> ActReceipt | None:
        corr = corr_or_uri.removeprefix("act://")
        for rec in self.nucleus.records_of_kind("act_receipt"):
            if rec["body"].get("corr") == corr:
                body = rec["body"]
                return ActReceipt(
                    corr=corr,
                    capability_ref=body.get("capability_ref", ""),
                    exec=body.get("exec", ""),
                    harm_effective=body.get("harm_effective", "H0"),
                    harm_derived=body.get("harm_derived", "H0"),
                    reason=body.get("reason", ""),
                    detail=body.get("detail", ""),
                    artifact_uri=body.get("artifact"),
                    sha256=body.get("sha256"),
                    provenance=body.get("provenance", {}),
                    cost=body.get("cost", {}),
                    scrubbed=bool(body.get("scrubbed")),
                )
        return None
