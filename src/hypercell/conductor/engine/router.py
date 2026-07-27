"""Capability / content routing - the MoE gate (constitution §6). Route a subtask to the best-fit cell.

Rank by capability coverage -> liveness -> lowest load. `claim` semantics (steal from a stale holder)
land with the task queue in P2+; this is the placement half of the scheduler.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CellAd:
    cell: str
    capabilities: list[str] = field(default_factory=list)
    live: bool = True
    load: int = 0


def coverage(needs: list[str], ad: CellAd) -> float:
    if not needs:
        return 1.0
    need = set(needs)
    return len(need & set(ad.capabilities)) / len(need)


def route(
    needs: list[str], ads: list[CellAd], *, usd: dict[str, float] | None = None
) -> CellAd | None:
    """The gate: coverage, then liveness, then load — then PRICE (ECON-S3).

    The price term is a tiebreak, deliberately last: routing exists to put work where it can be
    done, and a router that chose cheapness over capability would save dollars by buying failures.
    Between two cells that cover the need equally at equal load, the cheaper lane wins. `usd` maps
    cell -> quoted next-pull cost (`conductor/quote.quote_pull`); a cell missing from the map ranks
    as the MOST expensive among its ties — an unknown price is not a cheap price.
    """
    candidates = [a for a in ads if a.live and coverage(needs, a) > 0]
    if not candidates:
        return None
    prices = usd or {}
    worst = max(prices.values(), default=0.0) + 1.0
    return max(
        candidates,
        key=lambda a: (coverage(needs, a), -a.load, -prices.get(a.cell, worst)),
    )
