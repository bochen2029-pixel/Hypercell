"""Run topologies over the primitives (contracts/run.md). P1: the tournament.

Fan out N cells -> an external oracle scores each candidate -> champion (max score) -> cross-pollinate
over the Medium -> converge on target + stability. Seeded diversity is mandatory (HC-4).
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ...cell.runtime import Cell, build_cell
from ...common import ids
from ...common.types import Outcome, ProviderConfig, Role
from ...medium.bus import open_medium
from ...medium.transport_local import LocalMedium
from ..governor import BudgetExceeded, Governor, MeteredCognition
from .converge import run_oracle


@dataclass
class Candidate:
    cell: str
    round: int
    path: str
    score: float
    outcome: Outcome


@dataclass
class TournamentResult:
    run_id: str
    champion: Candidate | None
    converged: bool
    rounds_run: int
    history: list[Candidate] = field(default_factory=list)


# Seeded diversity (HC-4): distinct temperatures + angle hints per roster slot.
_ANGLES = [
    "Favor correctness and edge cases above all.",
    "Favor simplicity and readability.",
    "Think adversarially: enumerate how a naive version fails, then avoid each failure.",
    "Favor strict validation; reject anything not provably valid.",
    "Favor a minimal, well-tested core.",
]
_TEMPS = [0.2, 0.5, 0.8, 0.35, 0.65, 0.9]


def _roster(n: int, provider: str, model: str, base_prompt: str, diversify: bool) -> list[Role]:
    roles: list[Role] = []
    for i in range(n):
        params: dict[str, Any] = {}
        prompt = base_prompt
        if diversify:
            params["temperature"] = _TEMPS[i % len(_TEMPS)]
            prompt = base_prompt + "\n\nYour angle: " + _ANGLES[i % len(_ANGLES)]
        roles.append(
            Role(
                name=f"cell{i}",
                prompt=prompt,
                provider=ProviderConfig(provider=provider, model=model, params=params),
            )
        )
    return roles


async def _produce_and_score(
    cell: Cell,
    goal: str,
    peers: list[str],
    sandbox: Path,
    rnd: int,
    oracle_cmd: str,
    medium: LocalMedium,
    culture: str,
) -> Candidate:
    try:
        code = await cell.produce(goal, peers)
    except BudgetExceeded:
        return Candidate(cell=cell.role.name, round=rnd, path="", score=0.0, outcome=Outcome.invalid)
    rdir = sandbox / f"r{rnd}"
    rdir.mkdir(parents=True, exist_ok=True)
    path = rdir / f"{cell.role.name}.py"
    path.write_text(code, encoding="utf-8")
    medium.post(
        culture, cell.role.name, "submission", round=rnd, body={"code": code},
        artifact={"path": str(path)},
    )
    receipt = run_oracle(oracle_cmd, str(path))
    return Candidate(
        cell=cell.role.name, round=rnd, path=str(path), score=receipt.score, outcome=receipt.outcome
    )


async def run_tournament(
    *,
    run_id: str,
    goal: str,
    oracle_cmd: str,
    home: str,
    provider: str,
    model: str,
    n: int = 4,
    rounds: int = 3,
    target: float = 1.0,
    stable_k: int = 2,
    diversify: bool = True,
    base_prompt: str | None = None,
    cells: list[Cell] | None = None,
    governor: Governor | None = None,
) -> TournamentResult:
    """Run a tournament. `cells` may be supplied (tests inject stub-cognition cells); else built here."""
    base_prompt = base_prompt or (
        "You are a cell in a swarm solving a shared goal. Produce ONE solution artifact. "
        "Output ONLY the artifact (for code: the source), with no prose and no markdown fences."
    )
    culture = f"run-{run_id}"
    medium = open_medium(home)
    sandbox = Path(home) / "_sandbox" / run_id
    sandbox.mkdir(parents=True, exist_ok=True)

    if cells is None:
        roles = _roster(n, provider, model, base_prompt, diversify)
        cells = [build_cell(home, ids.claim_id(run_id, r.name, 0), r) for r in roles]
    if governor is not None:
        for c in cells:
            c.cognition = MeteredCognition(c.cognition, c.role.provider.provider, governor)

    medium.post(culture, "conductor", "round_open", body={"goal": goal}, round=1)

    champion: Candidate | None = None
    history: list[Candidate] = []
    stable = 0
    converged = False
    rounds_run = 0

    for rnd in range(1, rounds + 1):
        rounds_run = rnd
        peers: list[str] = []
        if rnd > 1:
            peers = [
                s["body"]["code"]
                for s in medium.submissions(culture, rnd - 1)
                if s.get("body") and s["body"].get("code")
            ]
        cands: list[Candidate] = list(
            await asyncio.gather(
                *(
                    _produce_and_score(c, goal, peers, sandbox, rnd, oracle_cmd, medium, culture)
                    for c in cells
                )
            )
        )
        history.extend(cands)
        valid = [c for c in cands if c.outcome != Outcome.invalid]  # INVALID excluded (tri-state)
        round_best = max(valid, key=lambda c: (c.outcome == Outcome.passed, c.score), default=None)
        prev = (champion.outcome == Outcome.passed, champion.score) if champion else (False, -1.0)
        if round_best is not None and (round_best.outcome == Outcome.passed, round_best.score) > prev:
            champion = round_best
            stable = 0
        else:
            stable += 1
        if (
            champion is not None
            and champion.outcome == Outcome.passed  # outcome is authoritative (exit-code, HC-7)
            and champion.score >= target
            and stable >= stable_k
        ):
            converged = True
            medium.post(
                culture, "conductor", "verdict",
                body={"champion": champion.cell, "score": champion.score, "round": champion.round},
            )
            break

    for c in cells:
        c.nucleus.close()
    medium.close()
    return TournamentResult(
        run_id=run_id, champion=champion, converged=converged, rounds_run=rounds_run, history=history
    )
