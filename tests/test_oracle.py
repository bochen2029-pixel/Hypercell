from __future__ import annotations

from pathlib import Path

from hypercell.common.types import Outcome
from hypercell.conductor.engine.converge import run_oracle

ORACLE = "python oracles/ipv4_check.py"

CORRECT = """
def is_valid(s):
    parts = s.split('.')
    if len(parts) != 4:
        return False
    for p in parts:
        if not p.isascii() or not p.isdigit():
            return False
        if len(p) > 1 and p[0] == '0':
            return False
        if int(p) > 255:
            return False
    return True
"""


def test_oracle_pass(tmp_path: Path) -> None:
    cand = tmp_path / "good.py"
    cand.write_text(CORRECT, encoding="utf-8")
    r = run_oracle(ORACLE, str(cand))
    assert r.outcome == Outcome.passed
    assert r.score == 1.0


def test_oracle_miss_is_gate(tmp_path: Path) -> None:
    cand = tmp_path / "bad.py"
    cand.write_text("def is_valid(s):\n    return s.count('.') == 3\n", encoding="utf-8")
    r = run_oracle(ORACLE, str(cand))
    assert r.outcome == Outcome.gate  # a real negative result, not INVALID
    assert 0.0 < r.score < 1.0


def test_oracle_error_is_invalid(tmp_path: Path) -> None:
    cand = tmp_path / "broken.py"
    cand.write_text("this is not python !!!\n", encoding="utf-8")
    r = run_oracle(ORACLE, str(cand))
    assert r.outcome == Outcome.invalid  # exit 2 -> excluded, never a zero score in the ranking
