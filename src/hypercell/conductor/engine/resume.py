"""`hc resume` — culture-wide, fold-based (run.md §R8.2; slice RE-4).

**Park-resume and crash-resume are THE SAME CODE PATH.** The parked record is metadata, never
load-bearing: a run that was politely parked and a run whose process was killed mid-grading are the
same situation as far as the log is concerned, and having two paths would mean the rarely-exercised
one (crash) is the one you find out about at 3am.

The sequence is ordered, and each step is a refusal point rather than a best-effort:

1. **The frozen manifest.** `presence{phase:genesis}` pins it; a sha mismatch REFUSES. Resuming a
   run under different bytes than it started with would make `manifest_sha256` on the certificate a
   number that points at nothing.
2. **Re-bind every claim-id.** A claim-id with prior receipts but an ABSENT nucleus is a **refusal**,
   never an empty re-bind — identity corruption outranks a crash. An empty nucleus under a live
   identity is a cell that will confidently contradict its own history.
3. **FOLD.** The state the crash interrupted, re-derived from the log.
4. **`econ.reconcile()` BEFORE the first new reserve.** The ECON-L8 gate, at the run level: a
   resumed run that reserved first would be spending against a budget it had not yet counted.
5. **Idempotent re-scoring** keyed `(submission_seq, oracle_gen)`; a pending gen-bump regrades
   survivors first, because a verdict earned under the old grader is not evidence under the new one.
6. Re-enter the drive loop.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .fold import PlanesState, fold


class ResumeRefused(Exception):
    """Resume stopped rather than proceeding on a state it could not trust."""


@dataclass
class ResumePlan:
    """What resume derived and what it must do before the loop restarts."""

    state: PlanesState
    claim_ids: list[str] = field(default_factory=list)
    regrade_required: list[int] = field(default_factory=list)
    reconciled: bool = False

    @property
    def already_scored(self) -> set[tuple[int, int]]:
        """The idempotence key set. The loop consults this before grading anything."""
        return self.state.scored


def derive_claim_ids(state: PlanesState) -> list[str]:
    """Every claim-id this run addressed, from the fold. Sorted, so re-binding order is stable."""
    return sorted(state.arms)


def resume(
    culture: str,
    records: list[dict[str, Any]],
    *,
    home: Path | str,
    expected_manifest_sha: str | None = None,
    nucleus_exists: Any = None,
    escrow: Any = None,
) -> ResumePlan:
    """Run §R8.2's resume sequence. Raises `ResumeRefused` at any step it cannot honour.

    `nucleus_exists(claim_id) -> bool` is injected so the refusal can be drilled without a
    filesystem, and so this module does not need to know how nuclei are stored.
    """
    state = fold(culture, records)

    # ---- step 1: the frozen manifest.
    if not state.manifest_sha256:
        raise ResumeRefused(
            f"culture '{culture}' has no presence{{phase:genesis}} record: there is no frozen "
            "manifest to resume under, and a run is its manifest"
        )
    if expected_manifest_sha is not None and expected_manifest_sha != state.manifest_sha256:
        raise ResumeRefused(
            f"manifest sha mismatch: the log says {state.manifest_sha256}, the caller expects "
            f"{expected_manifest_sha}. Resuming under different bytes would make the certificate's "
            "manifest_sha256 point at nothing."
        )

    # ---- step 2: re-bind claim-ids; refuse an absent nucleus that has history.
    claim_ids = derive_claim_ids(state)
    if nucleus_exists is not None:
        for claim_id in claim_ids:
            arm = state.arms[claim_id]
            if (arm.scored or arm.produced) and not nucleus_exists(claim_id):
                raise ResumeRefused(
                    f"claim-id '{claim_id}' has prior work in the log but no nucleus on disk. "
                    "Refused rather than re-bound empty: a cell resurrected without its own memory "
                    "will confidently contradict its history, and identity corruption outranks a crash."
                )

    plan = ResumePlan(state=state, claim_ids=claim_ids)

    # ---- step 4: reconcile the budget BEFORE any new reserve (ECON-L8, at run level).
    if escrow is not None:
        if getattr(escrow, "needs_reconcile", False):
            escrow.reconcile()
        plan.reconciled = True

    # ---- step 5: a pending gen-bump means survivors regrade first.
    plan.regrade_required = [
        sub_seq for (sub_seq, gen) in sorted(state.scored) if gen < state.gen
    ]
    return plan


def should_score(plan: ResumePlan, submission_seq: int, gen: int) -> bool:
    """The idempotence gate the drive loop calls before grading (§R8.2 step 5).

    `(submission_seq, oracle_gen)`: the same candidate under the same grader is scored once, ever.
    Stability is a COUNT, so a re-scored candidate does not merely waste a call — it ticks
    convergence twice for one piece of evidence, and the run converges on a lie.
    """
    return (submission_seq, gen) not in plan.already_scored
