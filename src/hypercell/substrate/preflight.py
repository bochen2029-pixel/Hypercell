"""The Substrate Preflight — guard registry and report (ARCHITECTURE §11; falsifier PREFLIGHT-LITE-1).

A preflight is a **probe, not state** (A13): it is re-run at Conductor start and before any
class-escalating run, and never resumed stale. Nothing here is durable; the *report* is what becomes
fold-visible, embedded inline in the admission decision record.

Every guard answers three things — what it checked, what state that leaves the box in, and **how the
operator fixes it**. A guard that fails without a fix string trains nobody, so `fix` is required on
any non-GREEN result.

Guards are registered by *land* (the build rung that mints them): the `a'` box guards protect the
live SQLite Medium today with no k3s anywhere; the `d'` battery gates class escalation and lands
with the isolation rung. Running only the `a'` land is legal and honest -- it just bounds
`max_honest_sandbox_class` (§11 admission law).
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

State = Literal["GREEN", "DEGRADED", "RED"]
Land = Literal["a'", "d'"]

#: State ordering, worst-last — used to fold many guard states into one verdict.
_SEVERITY: dict[State, int] = {"GREEN": 0, "DEGRADED": 1, "RED": 2}


@dataclass(frozen=True)
class GuardResult:
    """One guard's verdict. `fix` MUST be non-empty when state is not GREEN."""

    id: str
    state: State
    detail: str
    fix: str = ""

    def __post_init__(self) -> None:
        if self.state != "GREEN" and not self.fix:
            raise ValueError(f"guard {self.id} returned {self.state} with no operator fix string")


@dataclass(frozen=True)
class GuardSpec:
    id: str
    land: Land
    #: Spine guards halt the fabric on RED (§11 admission law) — each one caused a lived
    #: crash-loop or a corruption, so "continue anyway" is not offered.
    spine: bool
    fn: Callable[[Path], GuardResult]


GUARDS: dict[str, GuardSpec] = {}


def guard(gid: str, *, land: Land, spine: bool = False) -> Callable[
    [Callable[[Path], GuardResult]], Callable[[Path], GuardResult]
]:
    """Register a box guard under `gid`. Re-registration is refused -- ids are stable handles."""

    def deco(fn: Callable[[Path], GuardResult]) -> Callable[[Path], GuardResult]:
        if gid in GUARDS:
            raise ValueError(f"duplicate guard id {gid}")
        GUARDS[gid] = GuardSpec(id=gid, land=land, spine=spine, fn=fn)
        return fn

    return deco


@dataclass(frozen=True)
class PreflightReport:
    """The probe's output. `digest` is what an admission decision record embeds inline."""

    verdict: State
    results: list[GuardResult]
    max_honest_sandbox_class: int
    lands: tuple[Land, ...]
    halted: bool = False
    guards_failed: list[str] = field(default_factory=list)

    @property
    def digest(self) -> str:
        """Stable over (id, state) pairs -- detail strings carry paths and timings that legitimately vary."""
        canon = json.dumps(
            [[r.id, r.state] for r in sorted(self.results, key=lambda r: r.id)],
            separators=(",", ":"),
        )
        return "sha256:" + hashlib.sha256(canon.encode("utf-8")).hexdigest()

    def as_status_body(self) -> dict[str, object]:
        """The `status{kind:preflight}` body posted to `_ops` (advisory, R-decay is fine)."""
        return {
            "kind": "preflight",
            "verdict": self.verdict,
            "digest": self.digest,
            "max_honest_sandbox_class": self.max_honest_sandbox_class,
            "lands": list(self.lands),
            "halted": self.halted,
            "guards_failed": list(self.guards_failed),
            "guards": [{"id": r.id, "state": r.state, "detail": r.detail, "fix": r.fix} for r in self.results],
        }

    def admission_stanza(self) -> dict[str, object]:
        """What every admission decision record carries inline, so folds read the box's honesty."""
        return {"digest": self.digest, "verdict": self.verdict, "guards_failed": list(self.guards_failed)}


def worst(states: list[State]) -> State:
    """Fold guard states into one verdict. Empty folds to GREEN -- nothing checked, nothing claimed."""
    return max(states, key=lambda s: _SEVERITY[s]) if states else "GREEN"


def render(report: PreflightReport) -> str:
    """Operator-facing text. The fix string is the point -- print it where it is read."""
    lines = [f"Substrate Preflight: {report.verdict}  (lands: {', '.join(report.lands)})"]
    for r in report.results:
        mark = {"GREEN": "ok  ", "DEGRADED": "WARN", "RED": "FAIL"}[r.state]
        lines.append(f"  [{mark}] {r.id:<20} {r.detail}")
        if r.state != "GREEN":
            lines.append(f"           fix: {r.fix}")
    lines.append(f"  max_honest_sandbox_class = {report.max_honest_sandbox_class}")
    if report.halted:
        lines.append("  HALTED -- a spine guard is RED. Fix the above before the fabric will run.")
    return "\n".join(lines)
