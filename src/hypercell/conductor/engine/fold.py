"""FOLD — one derivation, three consumers (run.md §R8.2; slice RE-4, falsifiers RE-4 · CERT-1).

**The null is in-RAM state.** The live fabric kept the run's planes — arms, rounds, convergence, the
spend meter — in process memory, so a crash did not merely interrupt the run, it *erased what the run
knew about itself*. F16 is that defect wearing its money hat: the meter reset to zero on every
restart. Resume then meant "start again and hope", and a certificate assembled from RAM was a claim
about a process, not about a history.

So resume is **fold, not replay**. `FOLD(culture, span)` re-derives the whole planes state from the
log, and the same derivation serves all three consumers:

* **resume** — re-enter the drive loop with the state the crash interrupted;
* **the certificate** — every field is a projection of this state, so a certificate cannot say
  anything the log does not;
* **`hc verify`** — recompute the fold and diff field-by-field, which is only a real check because
  it is the *same* derivation and not a second implementation that might agree by luck.

Three laws the fold encodes, each of which is a defect if you skip it:

* **Input filter, compaction-closed** (L-FOLD-CLOSURE). Only R-forever ∪ R-run types enter. Chatter
  is excluded *by class*, which is what makes compaction safe: chat can evaporate and every
  certificate still refolds identically, because no certificate ever read it.
* **The gen-bump driver.** A `round_open` bumps the oracle generation ONLY if a conductor
  `oracle_gen` record exists at-or-before its seq. Keys on record EXISTENCE — a fold input — never
  on a body parse, so a run cannot advance its own grader by writing a field claiming it did.
* **Idempotent scoring keyed `(submission_seq, oracle_gen)`.** A resume that re-grades what it
  already graded double-counts convergence; the key is what makes "zero double-scored submissions"
  a property rather than a hope.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ...common.types import Outcome
from .driver import Convergence, ScoringEvent

#: The fold's input filter (§R8.2). COMPACTION-CLOSED: R-decay types (`chat`, `status`) are absent
#: BY CLASS, not by accident — that exclusion is what lets the compactor evaporate chatter without
#: changing a single certificate field.
FOLD_TYPES = frozenset({
    "presence", "round_open", "submission", "receipt", "task", "claim",
    "command", "oracle_gen", "verdict", "compact",
})

#: Spend accumulator keys — the pricebook's `Purpose` values (R16).
PURPOSES = ("production", "verification", "oracle_growth", "tool", "maintenance")


@dataclass
class ArmState:
    name: str
    produced: int = 0
    scored: int = 0
    usd_candidate: float = 0.0


@dataclass
class PlanesState:
    """Everything FOLD derives. The single source resume, the certificate and verify all read."""

    culture: str = ""
    run_id: str = ""
    manifest_sha256: str = ""
    topology: str = "tournament"
    span: tuple[int, int] = (0, 0)
    chain_head: str = ""

    round: int = 0
    gen: int = 0
    arms: dict[str, ArmState] = field(default_factory=dict)
    artifacts: dict[str, dict[str, Any]] = field(default_factory=dict)
    convergence: Convergence = field(default_factory=Convergence)

    spend: dict[str, float] = field(default_factory=lambda: dict.fromkeys(PURPOSES, 0.0))
    #: `(submission_seq, gen)` pairs already graded. The idempotence key: a resume that re-scores
    #: what it already scored would double-count convergence, and stability is a COUNT.
    scored: set[tuple[int, int]] = field(default_factory=set)
    #: Gradings that arrived for an already-scored (submission, gen) — named, so "zero double-scored"
    #: is observable rather than merely intended.
    duplicate_gradings: list[int] = field(default_factory=list)

    claims: dict[str, str] = field(default_factory=dict)
    lifecycle: list[str] = field(default_factory=list)
    verdict: dict[str, Any] | None = None
    #: Records the fold REFUSED to honour, with why. A void input is not a silent skip: an operator
    #: reading a run that did not converge needs to see the round_open that claimed a gen bump it
    #: had not earned.
    void_at_fold: list[dict[str, Any]] = field(default_factory=list)

    invalid_count: int = 0
    gradings: int = 0

    @property
    def spend_total(self) -> float:
        return round(sum(self.spend.values()), 8)

    @property
    def champion(self) -> ScoringEvent | None:
        return self.convergence.champion


def fold(culture: str, records: list[dict[str, Any]], *, span: tuple[int, int] | None = None) -> PlanesState:
    """FOLD(culture, span) → PlanesState. Pure over the records; reads no clock and no process state.

    Purity is the whole mechanism: if the fold consulted anything outside the span, a certificate
    could differ between two machines holding the same log, and `hc verify` would be checking the
    verifier's environment rather than the run's history.
    """
    in_span = [
        r for r in records
        if (span is None or span[0] <= int(r["seq"]) <= span[1])
        and str(r.get("type")) in FOLD_TYPES
        and not r.get("void_by_acl")
    ]
    state = PlanesState(culture=culture)
    if in_span:
        state.span = (int(in_span[0]["seq"]), int(in_span[-1]["seq"]))
        state.chain_head = str(in_span[-1].get("hash", ""))

    # Pre-scan the conductor's `oracle_gen` seqs. The gen-bump gate keys on record EXISTENCE, so it
    # needs to know which seqs hold one before it can judge a round_open that cites one.
    gen_seqs = sorted(
        int(r["seq"]) for r in in_span
        if str(r.get("type")) == "oracle_gen" and str(r.get("sender")) == "conductor"
    )

    for rec in in_span:
        seq = int(rec["seq"])
        rtype = str(rec.get("type"))
        raw_body = rec.get("body")
        body: dict[str, Any] = raw_body if isinstance(raw_body, dict) else {}
        sender = str(rec.get("sender", ""))

        if rtype == "presence":
            _fold_presence(state, seq, body, sender)
        elif rtype == "round_open":
            _fold_round_open(state, seq, body, gen_seqs)
        elif rtype == "submission":
            arm = state.arms.setdefault(sender, ArmState(name=sender))
            arm.produced += 1
            state.artifacts[str(body.get("cand", seq))] = {
                "ref": f"medium://{culture}/{seq}",
                "sha256": str((rec.get("artifact") or {}).get("sha256", "")),
                "seq": seq,
            }
        elif rtype == "receipt":
            _fold_receipt(state, seq, body)
        elif rtype in ("task", "claim"):
            _fold_claim(state, seq, rtype, body, sender)
        elif rtype == "oracle_gen":
            state.lifecycle.append(f"oracle_gen@{seq}")
        elif rtype == "verdict":
            state.verdict = {"seq": seq, **body}

        # Spend folds from the cost{} field-group wherever it rides — there is NO spend type
        # (§R8.2). Doing it here rather than per-branch means a cost group on a new record class
        # is accounted the day it appears, instead of the day someone remembers to add a branch.
        _fold_cost(state, body)

    return state


def _fold_presence(state: PlanesState, seq: int, body: dict[str, Any], sender: str) -> None:
    phase = str(body.get("phase", ""))
    if phase == "genesis":
        # Run-open: pin the manifest. Everything downstream is measured against these bytes.
        state.run_id = str(body.get("run_id", state.run_id))
        state.manifest_sha256 = str(body.get("manifest_sha256", state.manifest_sha256))
        state.topology = str(body.get("topology", state.topology))
        conv = body.get("convergence") or {}
        state.convergence = Convergence(
            target=float(conv.get("target", 1.0)), stable_k=int(conv.get("stable_k", 2))
        )
        for arm in body.get("arms", []) or []:
            state.arms.setdefault(str(arm), ArmState(name=str(arm)))
    elif phase == "spawned":
        state.lifecycle.append(f"fork@{seq}:{sender}")
        state.arms.setdefault(sender, ArmState(name=sender))
    elif phase in ("parked", "resumed"):
        state.lifecycle.append(f"{phase}@{seq}")


def _fold_round_open(state: PlanesState, seq: int, body: dict[str, Any], gen_seqs: list[int]) -> None:
    """A round opens. A gen bump requires a conductor `oracle_gen` record at-or-before this seq.

    The gate keys on record EXISTENCE, never on the body's claim (R14, s6-15). A `round_open` whose
    body says `gen: 4` with no such record behind it is VOID-AT-FOLD — otherwise a run could
    advance its own grader by asserting that it had, which is the trust plane conceding the one
    thing it exists to hold.
    """
    claims_bump = body.get("oracle_gen") is not None or body.get("gen") is not None
    if claims_bump:
        backing = [g for g in gen_seqs if g <= seq]
        if not backing:
            state.void_at_fold.append({
                "seq": seq, "type": "round_open",
                "why": "claims a generation bump with no conductor oracle_gen record at-or-before it",
            })
            return
        state.gen += 1
        # A gen bump stales every score: the grader changed, so what it graded is no longer
        # evidence. Champion and stability reset; survivors are regrade-required.
        state.convergence = Convergence(
            target=state.convergence.target, stable_k=state.convergence.stable_k
        )
    state.round += 1


def _fold_receipt(state: PlanesState, seq: int, body: dict[str, Any]) -> None:
    """A grading. ORDER IS SEMANTIC: stability counts non-improving VALID events, in log order."""
    sub_seq = int(body.get("submission_seq", 0) or 0)
    key = (sub_seq, state.gen)
    if sub_seq and key in state.scored:
        # Already graded under this generation. Re-scoring would tick stability twice for one
        # candidate, and stability is a COUNT — the resume path's whole correctness rests here.
        state.duplicate_gradings.append(seq)
        return
    if sub_seq:
        state.scored.add(key)

    outcome = _outcome(str(body.get("outcome", "invalid")))
    who = str(body.get("arm") or body.get("who") or "")
    event = ScoringEvent(who=who, outcome=outcome, score=float(body.get("score", 0.0) or 0.0), at=seq)
    state.convergence.observe([event])
    state.gradings += 1
    if outcome is Outcome.invalid:
        state.invalid_count += 1
    if who:
        arm = state.arms.setdefault(who, ArmState(name=who))
        arm.scored += 1


def _fold_claim(state: PlanesState, seq: int, rtype: str, body: dict[str, Any], sender: str) -> None:
    """Claims adjudicate by LOG ORDER: the first claimant on a task wins, and the log says who."""
    if rtype == "claim":
        task = str(body.get("task", ""))
        if task and task not in state.claims:
            state.claims[task] = sender


def _fold_cost(state: PlanesState, body: dict[str, Any]) -> None:
    cost = body.get("cost")
    if not isinstance(cost, dict):
        return
    purpose = str(cost.get("purpose", "production"))
    if purpose not in state.spend:
        state.spend[purpose] = 0.0
    state.spend[purpose] += float(cost.get("usd_effective", 0.0) or 0.0)


def _outcome(raw: str) -> Outcome:
    try:
        return Outcome(raw)
    except ValueError:
        return Outcome.invalid
