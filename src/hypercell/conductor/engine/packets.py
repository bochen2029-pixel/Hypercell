"""Evidence packets — per-case feedback, folded from receipts on the Medium (slice RE-3).

**The null is code-only pollination**, which is what the live P1 run does: each round hands cells
the previous round's candidate *code*. That works when the roster disagrees. It fails exactly when
you need it most.

**F1, the lived finding.** A single-family roster shares a blind spot: every cell is wrong the same
way, so showing them each other's answers shows them their own mistake five times. The round plateaus
and the operator watches a swarm confidently converge on nothing. Diversity of *weights* is one
answer (HC-4). This is the other, and it is cheaper: **show them the case, not the code.**

A failing case is concrete, external evidence. It survives a shared blind spot because it did not
come from the models — it came from the oracle, which is why a packet block is tagged
`tool_result` and not `peer_message`. The distinction is not cosmetic: peer text is another model's
opinion, and an oracle's failing case is a fact about the world.

Packets are folded from the `receipt` records M1 put on the Medium. Nothing new is stored, and the
fold is the same one any auditor could run.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

#: Cap per packet. Beyond this the frame is mostly failure list and the cell loses the goal — and
#: repeating the same class of failure ten times teaches nothing the first one did not.
MAX_CASES = 6

#: Common shapes a checker prints for a failing case. Deliberately conservative: an unmatched line
#: is dropped rather than guessed at, because a mis-parsed "case" is noise wearing evidence's clothes.
_CASE_PATTERNS = (
    re.compile(r"(?im)^\s*FAIL[:\s]+(?P<case>.+?)\s*$"),
    re.compile(r"(?im)^\s*CASE\s+(?P<case>.+?)\s*(?:->|=>)\s*(?P<got>.+?)\s*$"),
    re.compile(r"(?im)input[=:]\s*(?P<case>\S+).*?expected[=:]\s*(?P<want>\S+).*?got[=:]\s*(?P<got>\S+)"),
)


@dataclass(frozen=True)
class Case:
    """One failing case, as the oracle reported it."""

    text: str
    source: str = ""  # which cell's candidate surfaced it

    def render(self) -> str:
        return f"- {self.text}" + (f"   (surfaced by {self.source})" if self.source else "")


@dataclass(frozen=True)
class Packet:
    """What a cell is shown between rounds: cases, never code."""

    round: int
    cases: list[Case]

    @property
    def empty(self) -> bool:
        return not self.cases

    def render(self) -> str:
        """The block body. Framed as DATA — it enters as a `tool_result`, never as instruction."""
        head = (
            f"Failing cases found in round {self.round}. These are checker output, not opinions: "
            f"a case here is a fact about your answer, whoever produced it."
        )
        return head + "\n" + "\n".join(c.render() for c in self.cases)


def extract_cases(evidence: str, *, source: str = "") -> list[Case]:
    """Pull per-case failures out of one receipt's evidence. Unmatched lines are dropped.

    **Line-wise, first-pattern-wins.** Scanning the whole blob with each pattern independently made
    one failure match two patterns and become two cases — which defeats the very dedup that stops a
    single-family roster's identical failure from crowding out the four other failures that might
    have broken the tie. A line is one case or it is none.
    """
    if not evidence:
        return []
    seen: set[str] = set()
    out: list[Case] = []
    for line in evidence.splitlines():
        for pattern in _CASE_PATTERNS:
            m = pattern.search(line)
            if not m:
                continue
            parts = [v for v in m.groupdict().values() if v]
            text = " -> ".join(p.strip() for p in parts)
            if text and text.lower() not in seen:
                seen.add(text.lower())
                out.append(Case(text=text, source=source))
            break  # this line is spoken for
    return out


def build_packet(receipts: list[dict[str, Any]], *, round: int, cap: int = MAX_CASES) -> Packet:
    """Fold the round's `receipt` records into one packet.

    Deduplicated across cells on purpose: when a single-family roster fails the same case five times,
    that is ONE piece of evidence reported five times, and printing it five times would crowd out the
    other four failures that might have broken the tie.
    """
    cases: list[Case] = []
    seen: set[str] = set()
    for rec in receipts:
        body = rec.get("body") or {}
        if body.get("outcome") == "passed":
            continue  # a passing candidate has nothing to teach the round
        subject = body.get("subject") or {}
        for case in extract_cases(str(body.get("evidence") or ""), source=str(subject.get("cell", ""))):
            if case.text.lower() in seen:
                continue
            seen.add(case.text.lower())
            cases.append(case)
    return Packet(round=round, cases=cases[:cap])
