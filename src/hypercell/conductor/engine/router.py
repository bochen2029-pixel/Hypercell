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


def route(needs: list[str], ads: list[CellAd]) -> CellAd | None:
    """The gate: highest capability coverage, then liveness, then lowest load. None if none covers."""
    candidates = [a for a in ads if a.live and coverage(needs, a) > 0]
    if not candidates:
        return None
    return max(candidates, key=lambda a: (coverage(needs, a), -a.load))
