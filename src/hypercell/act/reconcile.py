"""The `unknown` reconciliation procedure — never blind-retry (contracts/act.md §8).

**The null is blind retry.** A resumed cell finds an `action` with no `outcome`, cannot tell whether
the world moved, and re-sends. That is the double-send, and it is worse than it looks: the crash
window it lives in (W4 — the effect landed, the receipt did not) is **irreducible**. You cannot fsync
a receipt before the world answers. So the fabric cannot make in-doubt states rare enough to ignore;
it can only handle them.

The procedure, in order, and the order is the content:

0. **Hold check.** A live `act_receipt{phase: hold}` for this corr means the act is legitimately
   HELD, not in doubt. Resume the countdown from the log and stop — probing here would treat a
   waiting act as a crashed one, and parking it would silently cancel an operator's pending decision.
1. **Do not re-execute.** Look up the profile's reconcile probe: an H0 read that decides whether the
   effect landed.
2. Run it as a full H0 act — gated, receipted, metered. A probe that skipped the pipeline would be
   an unaudited world-touch performed during recovery, which is when you can least afford one.
3. Grade: found → `ok` (`graded_by: resolver:reconcile`); provably absent → `invalid`, and retry is
   legal on the SAME idem; undeterminable → stays `unknown`, and then either the provider's own
   idempotency key carries the re-send or the act **parks to an operator**. The fabric never guesses.

**Probe admission is structural, checked at profile admission, not at reconcile time.** The probe
must be `harm_floor == H0` with egress inside the role's allowlist. A mutating probe would recurse
the in-doubt problem — you would need a probe for the probe — so it is read-only turtles all the way
down. **A profile with no admissible probe is inadmissible at H1+**: if you cannot find out what
happened, you do not get to do it.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

from .profiles import ANNEX_A, Harm, ProfileRefusal, ToolProfile

ProbeAnswer = Literal["found", "absent", "undeterminable"]
Disposition = Literal["held", "ok", "invalid", "unknown", "parked"]


class ProbeInadmissible(Exception):
    """A profile offered a probe that cannot be trusted to be read-only."""


@dataclass(frozen=True)
class Reconciliation:
    """What resume decided about one in-doubt act, and why."""

    corr: str
    disposition: Disposition
    reason: str
    graded_by: str = ""
    retry_idem: str | None = None
    probe_evidence: dict[str, Any] | None = None

    @property
    def may_retry(self) -> bool:
        """Only a **provably absent** effect may be retried. `unknown` never authorizes a re-send."""
        return self.disposition == "invalid"


def check_probe_admissible(profile: ToolProfile, *, role_egress: list[str]) -> None:
    """Structural admission (§8.1). Called when a profile is admitted, never when it is used.

    Checking at use-time would mean discovering during recovery that you have no way to find out
    what happened — the one moment the answer is load-bearing.
    """
    if profile.harm_floor == "H0":
        return  # an H0 profile touches nothing that needs probing

    probe = profile.reconcile_probe
    if not probe:
        raise ProbeInadmissible(
            f"{profile.ref} is H1+ with no reconcile probe. If you cannot find out whether it "
            "happened, you do not get to do it: every H1+ act has an irreducible in-doubt window."
        )
    probe_profile = ANNEX_A.get(probe)
    if probe_profile is None:
        raise ProbeInadmissible(f"{profile.ref} names probe '{probe}', which is not in Annex A")
    if probe_profile.harm_floor != "H0":
        raise ProbeInadmissible(
            f"{profile.ref}'s probe '{probe}' is {probe_profile.harm_floor}, not H0. A mutating "
            "probe recurses the in-doubt problem -- you would need a probe for the probe."
        )
    if "*" not in role_egress:
        outside = [h for h in probe_profile.egress_hosts if h != "*" and h not in role_egress]
        if outside or ("*" in probe_profile.egress_hosts and "*" not in role_egress):
            raise ProbeInadmissible(
                f"{profile.ref}'s probe '{probe}' reaches {outside or ['*']}, outside the role's "
                "allowlist. A probe that needs egress the role lacks cannot run when it is needed."
            )


def reconcile(
    in_doubt: dict[str, Any],
    *,
    hold_receipt: dict[str, Any] | None = None,
    probe: Callable[[dict[str, Any]], tuple[ProbeAnswer, dict[str, Any]]] | None = None,
    profile: ToolProfile | None = None,
) -> Reconciliation:
    """Run §8 for one pending action. Pure decision logic: the caller runs the probe act."""
    corr = str(in_doubt.get("corr") or in_doubt.get("idem") or "")

    # ---- step 0: the hold check, BEFORE anything else touches the world.
    if hold_receipt and _hold_is_live(hold_receipt):
        return Reconciliation(
            corr=corr,
            disposition="held",
            reason="a live hold receipt exists; this act is waiting, not in doubt. Resume the "
                   "countdown from the log -- the timestamps come from the Medium, never from the "
                   "process that died.",
        )

    ref = str(in_doubt.get("capability_ref", ""))
    profile = profile or ANNEX_A.get(ref)
    if profile is None:
        return Reconciliation(corr, "parked", f"no profile for '{ref}'; an operator decides")

    # ---- step 1/2: do not re-execute. Probe.
    if probe is None:
        return Reconciliation(
            corr, "parked", f"'{ref}' offers no reconcile probe at H1+; parked to _ops rather than guessed"
        )
    answer, evidence = probe(in_doubt)

    # ---- step 3: grade.
    if answer == "found":
        return Reconciliation(
            corr, "ok", "probe found the effect", graded_by="resolver:reconcile", probe_evidence=evidence
        )
    if answer == "absent":
        # Same idem, attempt+1. A NEW idem here would defeat the dedup that just proved its worth.
        return Reconciliation(
            corr, "invalid", "probe proves the effect never landed; retry is legal on the same idem",
            graded_by="resolver:reconcile", retry_idem=corr, probe_evidence=evidence,
        )
    if profile.retry_safe == "provider_idem":
        # The provider's own idempotency key IS the probe: a re-send it has already seen is a no-op
        # on its side, so re-sending answers the question instead of gambling on it.
        return Reconciliation(
            corr, "unknown", "undeterminable, but the provider dedups on our key: re-send is safe",
            retry_idem=corr, probe_evidence=evidence,
        )
    return Reconciliation(
        corr, "parked",
        "undeterminable and the provider does not dedup: parked to an operator (_ops task). "
        "The fabric never guesses -- a coin flip here is a double-send half the time.",
        probe_evidence=evidence,
    )


def _hold_is_live(receipt: dict[str, Any]) -> bool:
    body = receipt.get("body", receipt)
    if str(body.get("phase")) != "hold":
        return False
    hold = body.get("hold") or {}
    return not hold.get("escalated") and not body.get("canceled")


def admit_profile(profile: ToolProfile, *, role_egress: list[str]) -> ToolProfile:
    """Admission-time gate, so an inadmissible profile never reaches a cell (raises ProfileRefusal)."""
    try:
        check_probe_admissible(profile, role_egress=role_egress)
    except ProbeInadmissible as exc:
        raise ProfileRefusal("probe_inadmissible", str(exc)) from exc
    return profile


def harm_needs_probe(harm: Harm) -> bool:
    return harm != "H0"
