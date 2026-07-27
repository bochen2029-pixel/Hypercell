"""Allocation over arms: the dollar-UCB (ARCH §7; slice ECON-S3).

**The null is pull-count UCB** — the v1 `ucb1` below, kept intact and labelled, because ECON-UCB-1
runs the two side by side. Pull-count UCB treats every pull as costing the same thing, which is
false by an order of magnitude across lanes: it will happily spend ten expensive pulls learning
what one cheap arm could have told it, and its "exploration" is a subsidy for whichever arm burns
money fastest.

**The v5 index (normative; unit-invariant).** v2's formula (`ln USD_total` bare) is repealed as
dimensionally unsound — a currency re-scale would change exploration. v5 measures everything in
units of the cheapest pull:

    u0        = min over live lanes of quote(reference_frame).usd_expected    # per round
    n~_a      = max(usd_a, u0) / u0
    N~        = max(USD_production_total, u0) / u0
    index(a)  = ( best(a) + c * sqrt(ln N~ / n~_a) ) / max(e^(a), 0.01 * u0)

where `usd_a` counts only `attribution: candidate` spend — **apparatus-INVALID spend commits to the
run's ledger but never burns the arm** (the R5 fork: phase-A/candidate failure burns the arm;
phase-B/apparatus failure books to run-level `apparatus_usd`) — `best(a)` is the arm's max score
under the CURRENT oracle generation, and `e^(a)` is the quoted next-pull cost. Dividing by e^ makes
the index score-per-expected-dollar; flooring at `0.01*u0` keeps it finite.

Scale all dollars by k and: u0, usd_a, e^ scale by k; n~ and N~ are ratios and do not move; the
index scales by 1/k **uniformly across arms**, so the argmax — the allocation — is invariant.
ECON-UCB-1 drills the x100 re-scale as an exact-sequence equality, not an approximation.

Cold start needs no special case: an unpulled arm has `usd_a = 0`, so `n~_a` floors at 1 and the
bonus is finite — an expensive cold arm competes at `bonus / e^` and loses to a cheap arm that is
already producing, which is the point. Ties break toward the cheaper lane, then by name, so the
allocation is deterministic.

**Allocation never selects.** Champion selection stays in `converge`, outcome-authoritative and
pure-score: a cheap arm gets more TRIES, never a discount on the bar. This module exposes no
selection API on purpose.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Literal

Attribution = Literal["candidate", "apparatus"]


@dataclass
class Arm:
    name: str
    visits: int = 0
    best: float = 0.0
    pruned: bool = False
    #: Dollars of `attribution: candidate` spend — the ONLY spend that burns the arm (R5).
    usd_candidate: float = 0.0
    #: The oracle generation `best` was scored under. A gen bump stales every score.
    gen: int = 0
    #: Set when this arm is a third-party host riding beside a reference lane until the parity
    #: probe passes (A6: identical weights, identical distribution — exploration dollars must not
    #: re-learn posted facts).
    parity_of: str | None = None


@dataclass
class RunBook:
    """The run-level dollar ledger the R5 fork writes to.

    `production_usd` feeds N~ (the exploration clock). `apparatus_usd` is real money — it commits
    to the escrow like everything else — but it advances no arm's n~ and no exploration clock:
    a broken grader must cost the OPERATOR visibly, not cost some arm its standing.
    """

    production_usd: float = 0.0
    apparatus_usd: float = 0.0


def charge(arm: Arm, usd: float, *, attribution: Attribution, book: RunBook) -> None:
    """Book one step's dollars with the R5 attribution fork.

    candidate: burns the arm (its n~ advances) and feeds the production total.
    apparatus: books run-level only. The arm's index is UNCHANGED by a grader that failed —
    a drill asserts that equality, because "unchanged" is the entire content of the fork.
    """
    if attribution == "candidate":
        arm.usd_candidate += usd
        book.production_usd += usd
    else:
        book.apparatus_usd += usd


def dollar_ucb(
    arms: list[Arm],
    *,
    e_hat: dict[str, float],
    book: RunBook,
    c: float = 1.414,
) -> Arm | None:
    """The v5 index. Returns the arm to pull next, or None when nothing is live.

    `e_hat` maps arm name -> quoted next-pull cost (`conductor/quote.quote_pull`). Every live arm
    must be quoted: allocating an unquoted arm would divide by a guess, and an unknown price is not
    a cheap price. Missing quotes raise rather than default.
    """
    live = [a for a in arms if not a.pruned]
    if not live:
        return None
    unquoted = [a.name for a in live if a.name not in e_hat]
    if unquoted:
        raise KeyError(
            f"no quote for live arm(s) {unquoted}: an index divided by a guess allocates by "
            "fiction. Quote every lane or prune the arm."
        )

    if max(e_hat[a.name] for a in live) == 0.0:
        # Every live lane is FREE — the stub world. A dollar-denominated exploration clock cannot
        # tick when nothing costs anything (usd_a stays 0 forever, so the first scorer would win
        # every round unchallenged — measured: drive's arm0 was never dethroned). Pull-count UCB is
        # the equal-price limit of this index and the only honest reading at zero, so the null IS
        # the formula here. Production never enters this branch: the local floor is a pricebook row
        # priced at electricity (ARCH §7), so a real lane is never $0.
        return ucb1(live, c)

    # A mixed world (some free, some priced — stubs beside real lanes) floors the free quotes at
    # 1% of the cheapest PAID lane, so the unit stays meaningful and nothing divides by zero.
    positive = min(p for a in live if (p := e_hat[a.name]) > 0)
    costs = {a.name: (e_hat[a.name] or 0.01 * positive) for a in live}

    u0 = min(costs.values())
    n_total = max(book.production_usd, u0) / u0

    def index(a: Arm) -> float:
        n_a = max(a.usd_candidate, u0) / u0
        bonus = c * math.sqrt(math.log(n_total) / n_a) if n_total > 1.0 else 0.0
        return (a.best + bonus) / max(costs[a.name], 0.01 * u0)

    # Deterministic: highest index, ties to the cheaper lane, then to the earlier name.
    return max(live, key=lambda a: (index(a), -costs[a.name], _neg_name(a.name)))


def _neg_name(name: str) -> tuple[int, ...]:
    """Descending-name tiebreak encoded for use inside a max() key."""
    return tuple(-ord(ch) for ch in name)


# ---------------------------------------------------------------------------- 2-D prune / resurrect


def prune_2d(
    arms: list[Arm], *, champion_best: float, e_hat: dict[str, float], margin: float = 0.2
) -> list[Arm]:
    """Prune on BOTH dimensions: behind on score AND not the cheapest way to keep exploring.

    One-dimensional score pruning (the v1 `prune_dominated`) kills the cheap arm that is behind
    *because it has been given less money* — which is the arm the dollar-UCB most wants to keep
    probing. So the cheapest live lane is never pruned on score alone: it is the run's exploration
    floor, and its pulls cost the least of any way to be wrong.
    """
    live = [a for a in arms if not a.pruned]
    if not live:
        return []
    floor = min(e_hat.get(a.name, math.inf) for a in live)
    newly: list[Arm] = []
    for a in live:
        behind = a.usd_candidate > 0 and a.best + margin < champion_best
        cheapest = e_hat.get(a.name, math.inf) <= floor
        if behind and not cheapest:
            a.pruned = True
            newly.append(a)
    return newly


def advance_generation(arms: list[Arm], *, gen: int) -> list[Arm]:
    """An oracle generation bump stales every score: prunes lift, bests reset (resurrection #1).

    A verdict earned under gen N is not evidence under gen N+1 — the grader changed. Keeping an
    arm pruned on a stale condemnation would let an old grader reach forward in time.
    """
    resurrected: list[Arm] = []
    for a in arms:
        if a.gen != gen:
            if a.pruned:
                a.pruned = False
                resurrected.append(a)
            a.best = 0.0
            a.gen = gen
    return resurrected


def resurrect_on_cost_flip(arms: list[Arm], *, e_hat: dict[str, float]) -> list[Arm]:
    """A pruned arm that has become the strictly cheapest lane comes back (resurrection #2).

    The 2-D prune spared the cheapest lane; if prices move and a pruned arm NOW holds that spot,
    the condition it was pruned under no longer describes the world. Cost regimes change under the
    fabric — a pricebook update is exactly such an event — and a prune list that cannot notice is
    a decision made by an out-of-date market.
    """
    live_costs = [e_hat.get(a.name, math.inf) for a in arms if not a.pruned]
    if not live_costs:
        return []
    floor = min(live_costs)
    back: list[Arm] = []
    for a in arms:
        if a.pruned and e_hat.get(a.name, math.inf) < floor:
            a.pruned = False
            back.append(a)
    return back


# ---------------------------------------------------------------------------- the parity probe (A6)


def parity_verdict(
    host_scores: list[float], reference_scores: list[float], *, pulls: int = 5, eps: float = 0.05
) -> Literal["pending", "passed", "failed"]:
    """A third-party host rides as its OWN arm exactly until the 5-pull parity probe passes.

    A6: identical weights produce the same output distribution — the blind spot follows the
    weights — so once parity holds, keeping the host as a separate arm would spend exploration
    dollars re-learning a posted fact. Until it holds, the host's claim of "same model" is exactly
    that, a claim: hosts quantize, truncate context, and pin old revisions, and the probe is how a
    claim becomes a measurement.
    """
    paired = min(len(host_scores), len(reference_scores))
    if paired < pulls:
        return "pending"
    h = host_scores[:pulls]
    r = reference_scores[:pulls]
    delta = sum(abs(a - b) for a, b in zip(h, r, strict=True)) / pulls
    return "passed" if delta <= eps else "failed"


# ---------------------------------------------------------------------------- null-arm reservations


def open_null_reservation(
    escrow: Any,
    *,
    mode: Literal["matched", "floor"],
    scope: str,
    matched_usd: float,
    floor_usd: float,
) -> Any:
    """Reserve the null arm's budget AT RUN OPEN (ECON-S3's null modes).

    `matched`: the null is funded like a production arm, so "the swarm beat the null" is never
    "the swarm outspent the null" wearing a lab coat. `floor`: the null runs on the local-floor
    lane with an audit reservation set aside up front — cheaper, and the audit hold is what keeps
    the comparison honest later. Reserving at OPEN is the content: a null funded from leftovers is
    funded by whatever the production arms did not want, which biases every comparison against it.
    """
    if mode == "matched":
        return escrow.reserve(matched_usd, scope=scope, holder="null:matched")
    return escrow.reserve(floor_usd, scope=scope, holder="null:floor+audit")


# ---------------------------------------------------------------------------- the null, kept intact


def ucb1(arms: list[Arm], c: float = 1.414) -> Arm | None:
    """Pull-count UCB1 — **the null ECON-UCB-1 measures against**, kept verbatim from v1.

    Not deleted, because "dollar-UCB reaches the target at <=60% of pull-UCB spend" is only a
    measurement while the thing it beats still runs. Every pull weighs the same here, which is the
    defect: exploration priced in pulls subsidises whichever arm burns money fastest.
    """
    live = [a for a in arms if not a.pruned]
    if not live:
        return None
    unvisited = [a for a in live if a.visits == 0]
    if unvisited:
        return unvisited[0]
    total = sum(a.visits for a in live)
    return max(live, key=lambda a: a.best + c * math.sqrt(math.log(max(1, total)) / a.visits))


def prune_dominated(arms: list[Arm], champion_best: float, margin: float = 0.2) -> list[Arm]:
    """The v1 one-dimensional prune. Superseded by `prune_2d` for new callers; kept because the
    old drills pin its behaviour and because it documents what the 2-D version fixes."""
    newly: list[Arm] = []
    for a in arms:
        if not a.pruned and a.visits > 0 and a.best + margin < champion_best:
            a.pruned = True
            newly.append(a)
    return newly
