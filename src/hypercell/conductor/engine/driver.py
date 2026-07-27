"""The ONE driver — a topology is a policy row, never a loop (contracts/run.md; slice RE-1).

    Topology := (dispatch_policy, feedback_policy, tick_end_policy, termination_unit, verdict_kind)

`run_tournament` / `run_drive` / `run_fanout` as sibling code paths are **REPEALED**. They stay as
thin entry points that fill in a policy row; the counting, the champion rule and the convergence
predicate live here, once.

**F14, killed by construction.** Both live loops incremented `stable` on events the contract
excludes. `topology.py` incremented it when a round produced *zero valid candidates*; `drive.py`
incremented it on an *INVALID* grading. So a run whose oracle was simply broken accrued stability
and could "converge" on a stale champion with nothing having been graded at all.

`stable_k` has exactly one meaning here: **consecutive VALID scoring events with no champion
improvement, under one generation.** An INVALID event is excluded — it neither increments nor
resets, because it is not evidence in either direction. That is the whole of the tri-state: INVALID
is *excluded*, never a zero score that poisons a ranking and never a tick that buys convergence.

**F24** — the terminal argument for one driver: with two loops there were two definitions, and no
amount of care keeps two definitions equal. With one, "identical VALID-event counting across all
convergent rows" is not a property to test for; it is the same code.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from ...common.types import Outcome

DispatchPolicy = Literal["all", "ucb", "single"]
FeedbackPolicy = Literal["none", "peers", "packets"]
TickEndPolicy = Literal["round", "step"]
TerminationUnit = Literal["rounds", "steps"]
VerdictKind = Literal["verified", "verified-with-residual", "synthesis"]


@dataclass(frozen=True)
class Topology:
    """A policy ROW. Adding a topology means adding a row, never another loop."""

    name: str
    dispatch: DispatchPolicy = "all"
    feedback: FeedbackPolicy = "peers"
    tick_end: TickEndPolicy = "round"
    termination_unit: TerminationUnit = "rounds"
    verdict_kind: VerdictKind = "verified"


TOPOLOGIES: dict[str, Topology] = {
    "tournament": Topology("tournament", dispatch="all", feedback="peers", termination_unit="rounds"),
    # `hc drive` is CLI sugar for tournament x {dispatch: ucb} — not a second engine.
    "drive": Topology("drive", dispatch="ucb", feedback="none", tick_end="step", termination_unit="steps"),
    "fanout": Topology("fanout", dispatch="all", feedback="none", verdict_kind="synthesis"),
}


@dataclass(frozen=True)
class ScoringEvent:
    """One graded candidate. `outcome` is authoritative; `score` is only ever the tiebreak."""

    who: str
    outcome: Outcome
    score: float
    at: int = 0

    @property
    def valid(self) -> bool:
        """INVALID is EXCLUDED — not a zero score, and not a tick toward stability."""
        return self.outcome is not Outcome.invalid

    @property
    def rank(self) -> tuple[bool, float]:
        # Outcome first: a `passed` at 0.7 beats a `gate` at 0.99, because the exit code is ground
        # truth and the score is the model's opinion of itself (HC-7).
        return (self.outcome is Outcome.passed, self.score)


@dataclass
class Convergence:
    """The ONE convergence state. Every topology folds its events through this."""

    target: float = 1.0
    stable_k: int = 2

    champion: ScoringEvent | None = None
    stable: int = 0
    valid_events: int = 0
    invalid_events: int = 0

    history: list[ScoringEvent] = field(default_factory=list)

    def observe(self, events: list[ScoringEvent]) -> None:
        """Fold one tick's gradings. **Only VALID events move `stable`, in either direction.**"""
        self.history.extend(events)

        valid = [e for e in events if e.valid]
        self.invalid_events += len(events) - len(valid)
        if not valid:
            # A tick that graded nothing is not evidence of stability. Incrementing here is exactly
            # the F14 defect: a broken oracle would buy convergence one empty round at a time.
            return

        self.valid_events += len(valid)
        best = max(valid, key=lambda e: e.rank)
        prev = self.champion.rank if self.champion else (False, -1.0)

        if best.rank > prev:
            self.champion = best
            self.stable = 0
        else:
            self.stable += 1

    @property
    def converged(self) -> bool:
        """Outcome authoritative, score at target, and `stable_k` consecutive VALID no-improvements."""
        c = self.champion
        return (
            c is not None
            and c.outcome is Outcome.passed
            and c.score >= self.target
            and self.stable >= self.stable_k
        )

    def reason(self) -> str:
        if self.converged:
            return "converged"
        if self.champion is None:
            return "no valid champion (every candidate was INVALID)"
        if self.champion.outcome is not Outcome.passed:
            return f"champion has outcome {self.champion.outcome.value}, not passed"
        if self.champion.score < self.target:
            return f"champion score {self.champion.score:.4f} below target {self.target:.4f}"
        return f"stability {self.stable}/{self.stable_k} VALID events"
