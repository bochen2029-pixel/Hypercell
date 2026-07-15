"""UCB1 allocation over arms (approaches) (constitution §6). Spend attention where it pays off.

value = arm best; explore bonus = c * sqrt(ln N / visits). Unvisited arms are pulled first.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class Arm:
    name: str
    visits: int = 0
    best: float = 0.0
    pruned: bool = False


def ucb1(arms: list[Arm], c: float = 1.414) -> Arm | None:
    live = [a for a in arms if not a.pruned]
    if not live:
        return None
    unvisited = [a for a in live if a.visits == 0]
    if unvisited:
        return unvisited[0]
    total = sum(a.visits for a in live)
    return max(live, key=lambda a: a.best + c * math.sqrt(math.log(max(1, total)) / a.visits))


def prune_dominated(arms: list[Arm], champion_best: float, margin: float = 0.2) -> list[Arm]:
    """Arms the champion dominates by `margin` (pull them no more). Returns the newly-pruned arms."""
    newly: list[Arm] = []
    for a in arms:
        if not a.pruned and a.visits > 0 and a.best + margin < champion_best:
            a.pruned = True
            newly.append(a)
    return newly
