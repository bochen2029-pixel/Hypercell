"""The drive - the self-driving machine (constitution §6). schedule x route -> dispatch -> score -> loop.

A budget-bounded, UCB-scheduled convergence: each step expands the most promising approach (arm) with a
cell, scores it against the external oracle, and repeats until converged / budget hard-stop / max-steps.
Unlike the tournament (all cells every round), the drive spends attention where the bandit says it pays.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ...cell.runtime import Cell, build_cell
from ...cognition.metered import MeteredCognition
from ...common import ids
from ...common.types import Outcome, ProviderConfig, Role
from ...medium.bus import open_medium
from ..governor import BudgetExceeded, Governor
from .converge import run_oracle
from .driver import TOPOLOGIES, Convergence, ScoringEvent
from .schedule import Arm, ucb1
from .topology import _ANGLES


@dataclass
class DriveStep:
    step: int
    arm: str
    score: float
    outcome: Outcome


@dataclass
class DriveResult:
    run_id: str
    champion_arm: str | None
    champion_score: float
    converged: bool
    steps: int
    spent_usd: float
    stopped_reason: str
    history: list[DriveStep] = field(default_factory=list)


async def run_drive(
    *,
    run_id: str,
    goal: str,
    oracle_cmd: str,
    home: str,
    provider: str,
    model: str,
    n_arms: int = 4,
    max_steps: int = 12,
    target: float = 1.0,
    stable_k: int = 2,
    usd_cap: float = 1.0,
    per_provider_concurrency: dict[str, int] | None = None,
    base_prompt: str | None = None,
    cells: list[Cell] | None = None,
) -> DriveResult:
    base_prompt = base_prompt or (
        "You are a cell in a swarm solving a shared goal. Produce ONE solution artifact. "
        "Output ONLY the artifact (for code: the source), with no prose and no markdown fences."
    )
    gov = Governor(usd_cap=usd_cap, per_provider_concurrency=per_provider_concurrency or {})
    culture = f"drive-{run_id}"
    medium = open_medium(home)
    sandbox = Path(home) / "_sandbox" / run_id
    sandbox.mkdir(parents=True, exist_ok=True)

    if cells is None:
        cells = []
        for i in range(n_arms):
            role = Role(
                name=f"arm{i}",
                prompt=base_prompt + "\n\nYour angle: " + _ANGLES[i % len(_ANGLES)],
                provider=ProviderConfig(
                    provider=provider, model=model, params={"temperature": 0.2 + 0.15 * (i % 5)}
                ),
            )
            cells.append(build_cell(home, ids.claim_id(run_id, role.name, 0), role))
    # meter every cell through the ONE governor path (the hard-stop cannot be bypassed).
    for c in cells:
        c.cognition = MeteredCognition(c.cognition, c.role.provider.provider, gov)

    arms = [Arm(name=c.role.name) for c in cells]
    by_name = {c.role.name: c for c in cells}
    champion_arm: str | None = None
    champion_score = -1.0
    best_code: dict[str, str] = {}
    history: list[DriveStep] = []
    converged = False
    conv = Convergence(target=target, stable_k=stable_k)
    _row = TOPOLOGIES["drive"]  # = tournament x {dispatch: ucb}; sugar, not a second engine
    reason = "max-steps"

    for step in range(1, max_steps + 1):
        arm = ucb1(arms)
        if arm is None:
            reason = "no-arms"
            break
        cell = by_name[arm.name]
        try:
            code = await cell.produce(goal, list(best_code.values()))
        except BudgetExceeded:
            reason = "budget"
            break
        sdir = sandbox / f"s{step}"
        sdir.mkdir(parents=True, exist_ok=True)
        path = sdir / f"{arm.name}.py"
        path.write_text(code, encoding="utf-8")
        medium.post(culture, arm.name, "submission", round=step, body={"code": code},
                    artifact={"path": str(path)})
        receipt = run_oracle(oracle_cmd, str(path))
        arm.visits += 1
        if receipt.outcome != Outcome.invalid and receipt.score > arm.best:
            arm.best = receipt.score
            best_code[arm.name] = code
        history.append(DriveStep(step=step, arm=arm.name, score=receipt.score, outcome=receipt.outcome))

        # ONE driver (RE-1). This used to increment `stable` on an INVALID grading, which the
        # tri-state EXCLUDES: an error is not evidence in either direction, and letting it accrue
        # stability meant a failing oracle could converge the run on a stale champion — F14.
        conv.observe([ScoringEvent(arm.name, receipt.outcome, receipt.score, at=step)])
        if conv.champion is not None:
            champion_arm = conv.champion.who
            champion_score = conv.champion.score
        if conv.converged:
            converged = True
            reason = "converged"
            medium.post(culture, "conductor", "verdict",
                        body={"champion": champion_arm, "score": champion_score})
            break

    for c in cells:
        if c.nucleus is not None:   # a d0 cell has no nucleus to close (NUC-9)
            c.nucleus.close()
    medium.close()
    return DriveResult(
        run_id=run_id, champion_arm=champion_arm, champion_score=max(0.0, champion_score),
        converged=converged, steps=len(history), spent_usd=round(gov.spent, 6),
        stopped_reason=reason, history=history,
    )
