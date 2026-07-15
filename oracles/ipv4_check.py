#!/usr/bin/env python3
"""Example EXTERNAL falsifier for the ipv4 run (contracts/oracle.md).

The keystone rule in one file: ground truth comes from outside the model, the conductor runs it, and the
exit code is a tri-state — a crash is INVALID (excluded), never a zero score that poisons the ranking.

Usage:  python oracles/ipv4_check.py <candidate.py>
Prints: SCORE=<0..1>   on stdout
Exit:   0 = all pass · 1 = a real miss (SCORE < 1) · 2 = error / unloadable candidate -> INVALID
"""
from __future__ import annotations

import importlib.util
import sys

# The hidden battery. Note the non-ASCII digit case ('٤') — the exact class of bug a self-grading swarm
# misses and an external oracle catches.
CASES: list[tuple[str, bool]] = [
    ("0.0.0.0", True), ("255.255.255.255", True), ("192.168.1.1", True),
    ("1.2.3.4", True), ("10.0.0.255", True),
    ("256.1.1.1", False), ("1.1.1", False), ("1.1.1.1.1", False),
    ("01.1.1.1", False), ("1.1.1.-1", False), ("a.b.c.d", False),
    ("1.1.1.256", False), ("", False), ("1.1.1.٤", False),
]


def _load(path: str):
    spec = importlib.util.spec_from_file_location("candidate", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    if len(sys.argv) != 2:
        print("SCORE=0.0")
        print("usage: ipv4_check.py <candidate.py>", file=sys.stderr)
        return 2
    try:
        is_valid = _load(sys.argv[1]).is_valid
    except Exception as e:  # unloadable / no is_valid -> INVALID (exit 2), not a zero score
        print("SCORE=0.0")
        print(f"error: {e}", file=sys.stderr)
        return 2
    passed = 0
    for s, want in CASES:
        try:
            got: bool | None = bool(is_valid(s))
        except Exception:
            got = None
        if got == want:
            passed += 1
    score = passed / len(CASES)
    print(f"SCORE={score:.4f}")
    return 0 if passed == len(CASES) else 1


if __name__ == "__main__":
    sys.exit(main())
