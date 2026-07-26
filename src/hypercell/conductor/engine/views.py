"""Partial view — who sees which candidates (slice RE-10).

**The null is total view**, which is what the live `topology.py` does: hand every cell every peer's
candidate. It reads like generosity and behaves like a broadcast. One confident wrong answer reaches
the entire roster in a single round, and the round after that, every cell is anchored on it. That is
herding, and total view is the mechanism.

Partial view replaces it with **replicated assignment**: each candidate is shown to exactly `r` of
the `n` cells, chosen by a deterministic rotation.

Four properties, and the fourth is the one that makes it a falsifier rather than a heuristic:

1. **Bounded contagion.** Each candidate reaches exactly `r` cells, so a common-mode wrong answer
   touches `r/n` of the roster. With `r = max(1, n // 2)` that is at most half, by arithmetic rather
   than by hope.
2. **Nothing is hidden from everyone.** The union of all views is the whole frontier — a candidate
   nobody sees is a candidate that may as well not have been produced.
3. **No round where every view is identical** (given ≥2 candidates). Identical views are total view
   wearing a different name.
4. **Recomputable.** The assignment is a pure function of `(round, n, m)`, so `hc verify` can
   re-derive who saw what without the run having recorded it. An assignment nobody can check is an
   assignment you have to trust.

`r` is generous on purpose. Cutting to `r = 1` would herd less still, but a cell that sees nothing
learns nothing, and the point is to bound contagion — not to isolate the roster.
"""
from __future__ import annotations

from dataclasses import dataclass


def replication(n: int) -> int:
    """How many cells see each candidate. `n // 2` is the most generous value the bound allows."""
    return max(1, n // 2)


@dataclass(frozen=True)
class Assignment:
    """Who sees which frontier indices. Derived, never stored — `hc verify` recomputes it."""

    round: int
    n: int
    m: int
    views: dict[int, tuple[int, ...]]  # cell index -> frontier indices

    @property
    def replication(self) -> int:
        return replication(self.n)

    @property
    def contagion(self) -> float:
        """The fraction of the roster one candidate can reach. The RE-10 bound is <= 0.5."""
        return 0.0 if self.n == 0 else self.replication / self.n

    def coverage(self) -> set[int]:
        return {idx for view in self.views.values() for idx in view}

    def all_identical(self) -> bool:
        return len({v for v in self.views.values()}) <= 1


def assign_views(*, n: int, m: int, round: int = 1) -> Assignment:
    """Deterministically assign `m` candidates across `n` cells.

    Candidate `t` goes to cells `(t + offset + s) mod n` for `s` in `0..r-1`. The per-round offset
    rotates, so no cell is permanently the one that never sees candidate 0 — fairness across rounds
    without giving up determinism within one.
    """
    if n <= 0 or m <= 0:
        return Assignment(round=round, n=max(0, n), m=max(0, m), views={i: () for i in range(max(0, n))})

    r = replication(n)
    offset = round % n
    buckets: dict[int, list[int]] = {i: [] for i in range(n)}
    for t in range(m):
        for s in range(r):
            buckets[(t + offset + s) % n].append(t)

    return Assignment(round=round, n=n, m=m, views={i: tuple(sorted(set(v))) for i, v in buckets.items()})


def view_for(cell_index: int, frontier: list[str], *, n: int, round: int = 1) -> list[str]:
    """The candidates one cell may see this round."""
    assignment = assign_views(n=n, m=len(frontier), round=round)
    return [frontier[i] for i in assignment.views.get(cell_index, ())]


def verify_assignment(assignment: Assignment) -> tuple[bool, str]:
    """`hc verify`'s check: re-derive the assignment and confirm every RE-10 property holds."""
    expected = assign_views(n=assignment.n, m=assignment.m, round=assignment.round)
    if expected.views != assignment.views:
        return False, "the assignment does not re-derive from (round, n, m) — it is not recomputable"

    if assignment.m > 0 and assignment.coverage() != set(range(assignment.m)):
        missing = sorted(set(range(assignment.m)) - assignment.coverage())
        return False, f"candidates {missing} were shown to nobody — produced and then discarded"

    if assignment.m >= 2 and assignment.n >= 2 and assignment.all_identical():
        return False, "every view is identical — that is total view wearing a different name"

    if assignment.contagion > 0.5:
        return False, f"contagion {assignment.contagion:.2f} exceeds the RE-10 bound of 0.5"

    return True, (
        f"round {assignment.round}: {assignment.n} cells, {assignment.m} candidates, "
        f"r={assignment.replication}, contagion {assignment.contagion:.2f}"
    )
