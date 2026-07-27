"""AS-GATE — the agent-sandbox CRD adoption gate (ARCH §11.8; slice S9.2, falsifier AS-GATE).

**The null is importing the CRD as a dependency before it earns it.** Adopting an external CRD is
not a library choice you can back out of on a Tuesday: it becomes the thing claims and parks are
built on, and if it turns out to bind slowly or lose volumes on stock k3s, the fabric has already
grown around it. "It works on GKE" is a claim about somebody else's cluster.

So adoption is **evidence-gated, never faith-gated**. The gate is a probe with a number on it: on
stock k3s (no GKE), a `SandboxClaim` MUST bind a **warm gVisor pod in under 2 seconds** with a PVC
that both survives a pod restart and can be snapshotted. Until that probe passes on the operator's
own cluster, the CRD is **refused** and the StatefulSet + ledger-fork mechanism stands.

The probe result is **recorded every run**, not cached as a one-time blessing: a cluster that
qualified in March and regressed in July should stop qualifying in July. An adoption decision that
outlives the evidence for it is faith wearing a measurement's clothes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

#: The bind-latency bar (§11.8). Above this a claim/park backend makes every fork feel like a
#: deploy, and the mechanism it would replace is faster.
BIND_BUDGET_S = 2.0


@dataclass(frozen=True)
class AdoptionProbe:
    """One measurement of whether the CRD has earned adoption on THIS cluster."""

    bind_s: float | None
    pvc_survives: bool
    pvc_snapshottable: bool
    reached: bool = True
    detail: str = ""

    @property
    def adopted(self) -> bool:
        """All three clauses, or the CRD is refused. Any one failing is a refusal, not a caveat."""
        return (
            self.reached
            and self.bind_s is not None
            and self.bind_s < BIND_BUDGET_S
            and self.pvc_survives
            and self.pvc_snapshottable
        )

    @property
    def reason(self) -> str:
        if not self.reached:
            return f"cluster unreachable: {self.detail or 'no probe'} — CRD refused (unproven)"
        if self.bind_s is None:
            return "SandboxClaim never bound — CRD refused"
        if self.bind_s >= BIND_BUDGET_S:
            return f"SandboxClaim bound in {self.bind_s:.2f}s, over the {BIND_BUDGET_S}s bar — CRD refused"
        if not self.pvc_survives:
            return "the claim's PVC did not survive a pod restart — CRD refused"
        if not self.pvc_snapshottable:
            return "the claim's PVC is not snapshottable — CRD refused"
        return f"adopted: bound in {self.bind_s:.2f}s with a surviving, snapshottable PVC"


@dataclass
class AdoptionRecord:
    """What the gate decided, and on what evidence. Written every run (never cached as a blessing)."""

    backend: str  # "statefulset+ledger-fork" | "sandboxclaim-crd"
    probe: AdoptionProbe
    history: list[dict[str, Any]] = field(default_factory=list)

    def as_body(self) -> dict[str, Any]:
        return {
            "backend": self.backend,
            "adopted": self.probe.adopted,
            "bind_s": self.probe.bind_s,
            "pvc_survives": self.probe.pvc_survives,
            "pvc_snapshottable": self.probe.pvc_snapshottable,
            "bar_s": BIND_BUDGET_S,
            "reason": self.probe.reason,
        }


def decide_backend(probe: AdoptionProbe) -> AdoptionRecord:
    """Choose the claim/park backend from the probe alone.

    The default is the mechanism that already works. A CRD earns its way in by measuring better on
    the operator's own cluster; it does not arrive by being fashionable, and it does not stay by
    having arrived.
    """
    backend = "sandboxclaim-crd" if probe.adopted else "statefulset+ledger-fork"
    return AdoptionRecord(backend=backend, probe=probe)


def probe_sandbox_claim(runner: Any = None) -> AdoptionProbe:
    """Measure a real `SandboxClaim` bind on the live cluster.

    `runner` is injected so the gate can be drilled without a cluster — and so that a box with no
    cluster reports **unreachable** (CRD refused, unproven) rather than a fabricated latency. An
    absent cluster must never read as a passing probe.
    """
    if runner is None:
        return AdoptionProbe(
            bind_s=None, pvc_survives=False, pvc_snapshottable=False,
            reached=False, detail="no cluster runner supplied",
        )
    measured = runner()
    if not isinstance(measured, AdoptionProbe):
        # A runner that returned something else has not measured anything the gate can read, and
        # "unparseable" must fall to refused rather than to adopted.
        return AdoptionProbe(
            bind_s=None, pvc_survives=False, pvc_snapshottable=False,
            reached=False, detail=f"runner returned {type(measured).__name__}, not an AdoptionProbe",
        )
    return measured
