"""The converge plane: the external oracle, run coordinator-side (contracts/oracle.md).

Ground truth from outside the model. Exit tri-state honored: 0 pass, 1 gate (a real miss), 2 error ->
INVALID (excluded, never a zero score that poisons the ranking). Cells never score their own work.
"""
from __future__ import annotations

import re
import subprocess
import sys

from ...common.types import Outcome, Receipt

_SCORE_RE = re.compile(r"SCORE=([0-9]*\.?[0-9]+)")


def run_oracle(cmd: str, candidate_path: str, *, timeout: float = 60.0) -> Receipt:
    parts = cmd.split()
    if parts and parts[0] in ("python", "python3"):
        parts[0] = sys.executable
    try:
        proc = subprocess.run(  # noqa: S603
            [*parts, candidate_path], capture_output=True, text=True, timeout=timeout
        )
    except subprocess.TimeoutExpired:
        return Receipt(
            submission_seq=-1, outcome=Outcome.invalid, score=0.0, graded_by=cmd, evidence="timeout"
        )
    except OSError as e:
        return Receipt(
            submission_seq=-1, outcome=Outcome.invalid, score=0.0, graded_by=cmd, evidence=str(e)
        )
    # the oracle prints its SCORE last; take the LAST match so untrusted candidate stdout can't spoof it.
    matches = _SCORE_RE.findall(proc.stdout or "")
    score = float(matches[-1]) if matches else 0.0
    if proc.returncode == 2:
        outcome = Outcome.invalid  # error / crash -> excluded, NOT a zero score
    elif proc.returncode == 0:
        outcome = Outcome.passed
    else:
        outcome = Outcome.gate  # a real negative result
    return Receipt(
        submission_seq=-1,
        outcome=outcome,
        score=score,
        graded_by=cmd,
        evidence=(proc.stdout or "").strip()[:400],
    )
