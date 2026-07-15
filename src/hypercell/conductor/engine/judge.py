"""The judge plane: an external oracle made of independent LLM judges (Externality for prose).

For open tasks with no runnable checker, N independent judges score a candidate against the
goal, and their median is the score (the spread is surfaced as evidence). Judges are separate
from the producers — a cell never scores its own work (contracts/oracle.md, HC-4).

MVP judges share the base provider with distinct critical rubrics at temperature 0. Pass a
different provider/model for true cross-family judging, which is the strongest guard against a
shared blind spot (the DeepSeek isdigit/٤ lesson from P1).
"""
from __future__ import annotations

import asyncio
import re
import statistics

from ...cognition.base import Cognition
from ...common.types import Outcome, Receipt

_SCORE_RE = re.compile(r"SCORE:\s*([0-9]+(?:\.[0-9]+)?)", re.I)

_JUDGE_ANGLES = [
    "Judge above all for factual correctness and grounding; penalize unsupported claims hard.",
    "Judge for completeness; penalize anything that dodges part of the goal.",
    "Judge for clarity and usefulness to the operator; penalize vagueness and filler.",
    "Judge adversarially; find the single biggest flaw and mark it down for it.",
    "Judge for concision and signal-to-noise; penalize padding.",
]


def _judge_system(angle: str) -> str:
    return (
        "You are an impartial, skeptical judge scoring ONE candidate answer against a goal. "
        f"{angle} Rate it 0 to 10 (10 = excellent: correct, complete, grounded; 0 = wrong or useless). "
        "Be strict and independent. Reply with EXACTLY one line 'SCORE: <0-10>' then one short reason."
    )


async def judge_score(cog: Cognition, *, goal: str, candidate_text: str, judges: int = 3) -> Receipt:
    """Score one candidate with `judges` independent judges sharing `cog`. Median -> 0..1.

    Returns a Receipt in the same shape run_oracle produces, so it drops into the tournament.
    """
    async def one(j: int) -> float | None:
        try:
            res = await cog.complete(
                [
                    {"role": "system", "content": _judge_system(_JUDGE_ANGLES[j % len(_JUDGE_ANGLES)])},
                    {
                        "role": "user",
                        "content": f"GOAL:\n{goal}\n\nCANDIDATE:\n{candidate_text[:6000]}\n\nScore it now.",
                    },
                ],
                temperature=0.0,
            )
        except Exception:
            return None
        m = _SCORE_RE.search(res.text or "")
        if not m:
            return None
        return max(0.0, min(10.0, float(m.group(1))))

    raw = await asyncio.gather(*[one(j) for j in range(max(1, judges))])
    scores = [s for s in raw if s is not None]
    if not scores:
        return Receipt(
            submission_seq=-1, outcome=Outcome.invalid, score=0.0,
            graded_by="judge-panel", evidence="no judge scores parsed",
        )
    agg = round(statistics.median(scores) / 10.0, 4)
    return Receipt(
        submission_seq=-1, outcome=Outcome.passed, score=agg,
        graded_by=f"judge-panel(n={len(scores)})", evidence=f"scores={scores}",
    )
