"""Fan-out: spin up N cells that each answer a goal, then a coordinator synthesizes.

The literal "spin up / fan out N agents to do X" — a parallel exploration over the Medium,
oracle-free, for open-ended tasks (brainstorm, research, ideation). Its convergent sibling is
the tournament (topology.py), which needs an external oracle to converge on a champion.

Each cell keeps its own nucleus (SQLite ledger); all cells post to the shared Medium so the
viewer shows the swarm live.
"""
from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

from ...cell.runtime import build_cell
from ...common.types import ProviderConfig, Role
from ...medium.transport_local import LocalMedium

# Seeded diversity (constitution: diversity-or-mediocrity) — distinct angles so N cells don't
# herd to one answer.
_ANGLES = [
    "Be bold and unconventional; surface the non-obvious options.",
    "Be rigorous and precise; justify each claim.",
    "Optimize for simplicity and clarity.",
    "Reason from first principles.",
    "Take the contrarian view; challenge the obvious answer.",
    "Be practical and concrete; give something immediately usable.",
]


async def run_fanout(
    *,
    run_id: str,
    goal: str,
    home: str,
    provider: str,
    model: str,
    n: int = 5,
    synthesize: bool = True,
    on_event: Callable[[str, dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Spin up `n` cells on `goal`; `on_event(kind, data)` fires live (spawned/done/...)."""
    def emit(kind: str, **data: Any) -> None:
        if on_event:
            try:
                on_event(kind, data)
            except Exception:
                pass

    med = LocalMedium(home)
    culture = f"run-{run_id}"
    n = max(1, min(n, 30))
    med.post(culture, "conductor", "round_open", body={"goal": goal, "mode": "fanout", "n": n}, round=1)
    emit("start", n=n, culture=culture)

    async def one(i: int) -> dict[str, str]:
        temp = round(0.4 + 0.12 * (i % 6), 2)
        cid = f"cell{i}"
        # post the cell's arrival BEFORE it thinks, so the viewer shows the fleet appear at once.
        # `presence`, not an invented "spawned": a type outside the registry is E1 regrowing.
        med.post(culture, cid, "presence", body={"phase": "arrive", "angle": _ANGLES[i % len(_ANGLES)]}, round=1)
        emit("spawned", cell=cid)
        role = Role(
            name=f"explorer{i}",
            prompt=(
                f"You are {cid}, one of {n} agents in a hypercell swarm working the same goal. "
                f"{_ANGLES[i % len(_ANGLES)]} Answer the goal directly and concisely."
            ),
            provider=ProviderConfig(provider=provider, model=model, params={"temperature": temp}),
        )
        cell = build_cell(home, f"{run_id}/explorer/{i}", role)
        try:
            ans = await cell.ask(goal)
        except Exception as e:  # one cell failing must not sink the swarm
            ans = f"({cid} failed: {e})"
        med.post(culture, cid, "submission", body={"answer": ans}, round=1)
        emit("done", cell=cid, chars=len(ans))
        return {"cell": cid, "answer": ans}

    answers = await asyncio.gather(*[one(i) for i in range(n)])

    synthesis: str | None = None
    if synthesize and len(answers) > 1:
        emit("synthesizing", cells=len(answers))
        joined = "\n\n".join(f"[{a['cell']}]\n{a['answer']}" for a in answers)
        srole = Role(
            name="coordinator",
            prompt=(
                "You are the coordinator cell of a hypercell swarm. Synthesize the agents' answers "
                "into one best response for the operator: note where they agree, fold in the strongest "
                "distinct ideas, and drop the weak ones. Be direct; do not mention the cells by number."
            ),
            provider=ProviderConfig(provider=provider, model=model),
        )
        scell = build_cell(home, f"{run_id}/coordinator/0", srole)
        try:
            synthesis = await scell.ask(f"GOAL:\n{goal}\n\nSWARM ANSWERS:\n{joined}")
        except Exception as e:
            synthesis = f"(synthesis failed: {e})"
        # A synthesis IS a verdict kind (wire.md §3.1), and a verdict is conductor-only.
    med.post(culture, "conductor", "verdict", body={"kind": "synthesis", "text": synthesis}, round=2)

    med.close()
    return {"run_id": run_id, "culture": culture, "answers": answers, "synthesis": synthesis}
