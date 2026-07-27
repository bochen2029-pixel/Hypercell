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
from ...cognition.base import Cognition
from ...cognition.metered import MeteredCognition, build_adapter
from ...common import ids
from ...common.types import Outcome, ProviderConfig, Role
from ...medium.bus import open_medium
from ...medium.transport_local import Filter, LocalMedium
from ..governor import BudgetExceeded, Governor
from .converge import run_oracle
from .driver import TOPOLOGIES, Convergence, ScoringEvent
from .judge import judge_score
from .packets import build_packet
from .views import view_for


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
    judge_ctx: tuple[Cognition, int] | None = None,
    packet: str = "",
) -> Candidate:
    try:
        code = await cell.produce(goal, peers, packet=packet)
    except BudgetExceeded:
        return Candidate(cell=cell.role.name, round=rnd, path="", score=0.0, outcome=Outcome.invalid)
    rdir = sandbox / f"r{rnd}"
    rdir.mkdir(parents=True, exist_ok=True)
    path = rdir / f"{cell.role.name}.{'md' if judge_ctx else 'py'}"
    path.write_text(code, encoding="utf-8")
    medium.post(
        culture, cell.role.name, "submission", round=rnd, body={"code": code},
        artifact={"path": str(path)},
    )
    if judge_ctx is not None:  # open task: an independent judge panel scores it (Externality for prose)
        jcog, judges = judge_ctx
        receipt = await judge_score(jcog, goal=goal, candidate_text=code, judges=judges)
        graded_by = f"judge-panel/{judges}"
    else:  # checkable task: the external oracle command scores it
        receipt = run_oracle(oracle_cmd, str(path))
        graded_by = "oracle-cmd"

    # E2, fixed at M1: the grading lands on the Medium as a registry `receipt`, posted by the
    # conductor. It used to be an off-registry "judgment" from a cell principal, which meant the
    # oracle's verdict never reached a constitutional fold at all — every certificate and null
    # ledger downstream was folding over a log that had no gradings in it.
    medium.post(
        culture, "conductor", "receipt", round=rnd,
        body={
            "check": "submission",
            "subject": {"cell": cell.role.name, "round": rnd},
            "outcome": receipt.outcome.value if hasattr(receipt.outcome, "value") else str(receipt.outcome),
            "score": receipt.score,
            "graded_by": graded_by,
            "evidence": receipt.evidence,
        },
    )
    return Candidate(
        cell=cell.role.name, round=rnd, path=str(path), score=receipt.score, outcome=receipt.outcome
    )


async def run_tournament(
    *,
    run_id: str,
    goal: str,
    oracle_cmd: str = "",
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
    judge: int = 0,
) -> TournamentResult:
    """Run a tournament. Scoring is an external oracle command, or (judge>0) an independent
    judge panel for open/prose tasks. `cells` may be supplied (tests inject stub cells)."""
    is_judge = judge > 0
    base_prompt = base_prompt or (
        (
            "You are a cell in a swarm answering a shared goal. Produce your single best answer. "
            "Output ONLY the answer, direct and self-contained, with no preamble."
        )
        if is_judge
        else (
            "You are a cell in a swarm solving a shared goal. Produce ONE solution artifact. "
            "Output ONLY the artifact (for code: the source), with no prose and no markdown fences."
        )
    )
    culture = f"run-{run_id}"
    medium = open_medium(home)
    sandbox = Path(home) / "_sandbox" / run_id
    sandbox.mkdir(parents=True, exist_ok=True)

    judge_ctx: tuple[Cognition, int] | None = None
    if is_judge:
        judge_ctx = (build_adapter(ProviderConfig(provider=provider, model=model)), judge)

    if cells is None:
        roles = _roster(n, provider, model, base_prompt, diversify)
        cells = [build_cell(home, ids.claim_id(run_id, r.name, 0), r) for r in roles]
    if governor is not None:
        for c in cells:
            c.cognition = MeteredCognition(c.cognition, c.role.provider.provider, governor)

    medium.post(culture, "conductor", "round_open", body={"goal": goal}, round=1)

    champion: Candidate | None = None
    history: list[Candidate] = []
    converged = False
    conv = Convergence(target=target, stable_k=stable_k)
    _row = TOPOLOGIES["tournament"]
    rounds_run = 0

    for rnd in range(1, rounds + 1):
        rounds_run = rnd
        peers: list[str] = []
        packet_text = ""
        if rnd > 1:
            peers = [
                s["body"]["code"]
                for s in medium.submissions(culture, rnd - 1)
                if s.get("body") and s["body"].get("code")
            ]
            # The packet is a FOLD over the receipts M1 put on the Medium: nothing new is stored,
            # and any auditor can run the same fold.
            prior = medium.read(culture, filt=Filter(types=("receipt",), round=rnd - 1))
            packet = build_packet(prior, round=rnd - 1)
            packet_text = "" if packet.empty else packet.render()
        cands: list[Candidate] = list(
            await asyncio.gather(
                *(
                    _produce_and_score(
                        c, goal,
                        # RE-10: a PARTIAL view. Total view is a broadcast — one confident wrong
                        # answer reached the whole roster in a single round, and every cell was
                        # anchored on it by the next. Each candidate now reaches at most half.
                        view_for(i, peers, n=len(cells), round=rnd),
                        sandbox, rnd, oracle_cmd, medium, culture, judge_ctx,
                        packet=packet_text,
                    )
                    for i, c in enumerate(cells)
                )
            )
        )
        history.extend(cands)
        # ONE driver (RE-1): the counting, the champion rule and the predicate live in driver.py.
        # This used to increment `stable` even when a round produced ZERO valid candidates, so a
        # broken oracle bought convergence one empty round at a time — F14.
        conv.observe([ScoringEvent(c.cell, c.outcome, c.score, at=rnd) for c in cands])
        if conv.champion is not None:
            # Match on (cell, ROUND). Keying by cell name alone would return that cell's LATEST
            # candidate, so a champion won in round 1 would report round 3's artifact path — a
            # certificate pointing at bytes that never won.
            champion = next(
                c for c in history if c.cell == conv.champion.who and c.round == conv.champion.at
            )
        if conv.converged and champion is not None:
            # `converged` implies a champion by construction (the predicate requires outcome
            # `passed`), but narrowing it here keeps that implication CHECKED rather than assumed.
            converged = True
            medium.post(
                culture, "conductor", "verdict",
                body={"champion": champion.cell, "score": champion.score, "round": champion.round},
            )
            break

    for c in cells:
        if c.nucleus is not None:   # a d0 cell has no nucleus to close (NUC-9)
            c.nucleus.close()
    medium.close()
    return TournamentResult(
        run_id=run_id, champion=champion, converged=converged, rounds_run=rounds_run, history=history
    )
