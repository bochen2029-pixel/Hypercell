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

from dataclasses import dataclass, field, fields
from datetime import timedelta
from pathlib import Path
from typing import Any

from ..cell.nucleus import Nucleus
from ..common import clock, ids
from ..conductor.governor import Escrow
from ..conductor.registry import EffectRegistry, effect_id, scope_key
from ..medium.firewall import Trifecta
from .adapters import AdapterError, deliver_outbox, fs_read, scrub, web_fetch, web_search
from .profiles import ANNEX_A, NOT_YET_ADMITTED, GateVerdict, Harm, ProfileRefusal, gate
from .reconcile import Reconciliation, check_probe_admissible, reconcile
from .settle import DEFAULT_MAX_HORIZON, Expectation, WagerRefused, check_losability
from .store import ArtifactStore

_ADAPTERS = {
    "fs.read": fs_read,
    "web.fetch": web_fetch,
    "web.search": web_search,
    "deliver.outbox": deliver_outbox,
}


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
    #: ACT-1. The scoped exactly-once key this act reserved; the registry's join column.
    effect_key: str = ""
    #: Set on the LOSER of a reservation race. Dedup-and-share: the loser cites the winner's work.
    duplicate_of: str | None = None
    #: The losable wager, carried on the receipt so settlement is a fold and not a lookup.
    expectation: dict[str, Any] | None = None
    #: exec | hold | settle -- the phase partition (§3.1).
    phase: str = "exec"

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
            "effect_key": self.effect_key,
            "duplicate_of": self.duplicate_of,
            "expectation": self.expectation,
            "phase": self.phase,
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
        registry: EffectRegistry | None = None,
        max_wager_horizon: timedelta = DEFAULT_MAX_HORIZON,
    ) -> None:
        self.nucleus = nucleus
        self.store = ArtifactStore(home)
        self.escrow = escrow
        self.role_tools = role_tools if role_tools is not None else list(ANNEX_A)
        self.role_harm_ceiling = role_harm_ceiling
        self.role_egress = role_egress if role_egress is not None else ["*"]
        self.standing_access = standing_access or []
        #: The Conductor's effect registry. H1+ REQUIRES it: without a place to reserve the key
        #: there is no exactly-once, and an H1 act that cannot dedup is a double-send waiting for a
        #: crash. H0 runs fine without one -- reads have no effect to deduplicate.
        self.registry = registry
        #: R29. A wager whose deadline is a year out is not a check anybody will act on.
        self.max_wager_horizon = max_wager_horizon

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
        expectation: dict[str, Any] | None = None,
        step_id: str | None = None,
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

        profile = ANNEX_A[capability_ref]
        world_writing = verdict.harm_effective != "H0"

        # ---- step g: the LOSABILITY BATTERY, before anything is reserved or journaled. A wager
        # you find out is unlosable after it has been won has already done its damage.
        if expectation is not None:
            try:
                check_losability(
                    Expectation(**expectation),
                    journal_ts=clock.now_iso(),
                    effect_latency_s=profile.effect_latency_s,
                    max_horizon=self.max_wager_horizon,
                )
            except WagerRefused as refusal:
                return self._write(self._refusal(corr, capability_ref, refusal.reason, refusal.detail, args))
        elif world_writing:
            return self._write(self._refusal(
                corr, capability_ref, "wager_required",
                f"{capability_ref} is {verdict.harm_effective}: a world-write declares a losable "
                "expectation or it does not run. The null is actor self-report, where every act "
                "succeeds because the only party asked is the one with an interest in the answer.",
                args,
            ))

        # ---- step 2: ESCROW. H0 rides a lease so grounding does not serialize.
        resv_id = None
        if self.escrow is not None and self.escrow.leaseable(capability_ref, harm=verdict.harm_effective):
            resv_id = self.escrow.grant_lease(holder=self.nucleus.claim_id, lane=capability_ref).resv_id

        # ---- step 3: EFFECT-RESERVE. Reserve, THEN execute -- never consult, then act (FIX-2).
        effect_key = ""
        if world_writing:
            if self.registry is None:
                return self._write(self._refusal(
                    corr, capability_ref, "no_effect_registry",
                    "H1+ requires the Conductor's effect registry; without a place to reserve the "
                    "key there is no exactly-once, only a double-send waiting for a crash.",
                    args,
                ))
            effect_key = self.effect_key_for(capability_ref, args, step_id=step_id or corr)
            reservation = self.registry.reserve(effect_key, corr, lease=resv_id)
            if reservation.duplicate_of == corr:
                # My own completed act, asked for again. Replay the receipt rather than re-running:
                # an idempotent request must be idempotent all the way down, or every retry loop
                # becomes a second effect.
                if resv_id and self.escrow is not None:
                    self.escrow.release(resv_id, "replayed")
                prior = self.receipt_for(corr)
                if prior is not None:
                    return prior
            if not reservation.won:
                # Dedup-and-SHARE. The loser is refused and told whose receipt to cite, so it can
                # carry the same evidence instead of re-doing the work or inventing a result.
                if resv_id and self.escrow is not None:
                    self.escrow.release(resv_id, "duplicate_effect")
                return self._write(ActReceipt(
                    corr=corr, capability_ref=capability_ref, exec="refused",
                    harm_effective=verdict.harm_effective, harm_derived=verdict.harm_derived,
                    reason="duplicate_effect",
                    detail=f"effect already reserved by {reservation.duplicate_of}; share its evidence",
                    effect_key=effect_key, duplicate_of=reservation.duplicate_of, scrubbed=True,
                ))

        # ---- step 4: JOURNAL(fsync) BEFORE the world is touched.
        self.nucleus.append(
            "action",
            {"verb": "act", "capability_ref": capability_ref, "args": scrub(args), "corr": corr,
             "effect_key": effect_key, "expectation": expectation},
            idem=corr,
            durability="gold",
        )

        # ---- step 5: EXECUTE
        try:
            call_args = dict(args, effect_key=effect_key) if effect_key else args
            content, mime, provenance = _ADAPTERS[capability_ref].execute(call_args)
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
            effect_key=effect_key,
            expectation=expectation,
        )

        # ---- step 7: SETTLE
        if resv_id and self.escrow is not None:
            self.escrow.draw(resv_id, 0.0)
        if effect_key and self.registry is not None:
            # `executed` outlives every lease TTL. The world moved; forgetting that is how you send
            # twice, so this row is never swept.
            self.registry.transition(effect_key, "executed")
        return self._write(receipt, idem=corr)

    @property
    def actor(self) -> str:
        """The acting cell: the cognition principal that mints the `act` (wire.md §3/§6)."""
        return self.nucleus.claim_id

    @property
    def executor_principal(self) -> str:
        """The world-side witness. A **distinct** principal string, because A5 turns on that.

        At T0 the executor is in-process and the distinctness is convention (red-teamed by HC-7-v2
        attempt 8); from Stage-1a the post-ACL checks it mechanically, and a receipt whose witness
        is its own subject is refused.
        """
        return f"{self.nucleus.claim_id}/executor"

    def _refusal(
        self, corr: str, ref: str, reason: str, detail: str, args: dict[str, Any]
    ) -> ActReceipt:
        """A refusal is a receipt. A gate that refuses silently teaches nobody and audits to nothing."""
        return ActReceipt(
            corr=corr, capability_ref=ref, exec="refused", reason=reason, detail=detail,
            provenance=scrub({"args": args}), scrubbed=True,
        )

    def effect_key_for(self, ref: str, args: dict[str, Any], *, step_id: str) -> str:
        """The scoped exactly-once key (§7.1). The SCOPE is the profile's, never the caller's.

        A caller-chosen scope would let a cell opt out of lineage dedup by asking for `instance`,
        which is the double-send with extra steps.
        """
        profile = ANNEX_A[ref]
        eid = effect_id(ref, profile.tool_version, profile.significant(args))
        root = self.registry.root_of(self.nucleus.claim_id) if self.registry else self.nucleus.claim_id
        return scope_key(
            profile.effect_scope,
            claim_id=self.nucleus.claim_id, step_id=step_id,
            lineage_root=root, eid=eid,
            routine_id=ref, slot=step_id,
        )

    # ---------------------------------------------------------------- resume (§8)

    def reconcile_pending(
        self, probe: Any = None
    ) -> list[Reconciliation]:
        """Run §8 for every in-doubt act. **Plural**, because a resident can crash with several.

        Returning only the oldest -- the live v1 single-dict assumption -- strands the rest in doubt
        forever: no probe, no receipt, and an effect registry row that never leaves `reserved`.
        """
        out: list[Reconciliation] = []
        for pend in self.nucleus.pending():
            corr = str(pend.get("corr") or pend.get("idem") or "")
            out.append(reconcile(pend, hold_receipt=self._hold_for(corr), probe=probe))
        return out

    def receipt_for(self, corr: str) -> ActReceipt | None:
        """The receipt this cell already wrote for `corr`, if any. Replay reads it; nothing else."""
        for rec in self.nucleus.records_of_kind("act_receipt"):
            body = rec["body"]
            if str(body.get("corr")) == corr and str(body.get("phase", "exec")) == "exec":
                known = {f.name for f in fields(ActReceipt)}
                return ActReceipt(**{k: v for k, v in body.items() if k in known})
        return None

    def _hold_for(self, corr: str) -> dict[str, Any] | None:
        for rec in self.nucleus.records_of_kind("act_receipt"):
            body = rec["body"]
            if str(body.get("corr")) == corr and str(body.get("phase")) == "hold":
                return rec
        return None

    def admit(self, ref: str) -> None:
        """Profile admission (§8.1 / §10.1). Raises before a cell can ever call an unprobeable H1+."""
        if ref in NOT_YET_ADMITTED:
            raise ProfileRefusal(
                "not_admitted",
                f"{ref} is declared in Annex A but not admitted: its adapter or isolation class has "
                "not landed. Declaring the gap beats leaving it undeclared and tripping over it.",
            )
        check_probe_admissible(ANNEX_A[ref], role_egress=self.role_egress)

    def _write(self, receipt: ActReceipt, *, idem: str | None = None) -> ActReceipt:
        """Every outcome is journaled — an ok, a failure, and above all a refusal.

        The principals are stamped HERE, not carried on the dataclass: this is the one place the
        executor's own identity is known and a caller cannot supply it. A receipt that could name
        its own witness would answer the only question an auditor reads it to ask (SEC-2 / A5).
        """
        body = {**receipt.as_body(), "actor": self.actor, "executor": self.executor_principal}
        self.nucleus.append("act_receipt", body, idem=idem or receipt.corr, durability="gold")
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
