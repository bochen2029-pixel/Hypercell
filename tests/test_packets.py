"""RE-3 — per-case feedback packets (ARCHITECTURE §15; slice RE-3).

The bar, and it is a COMPARISON, not an assertion about one run: a single-family roster with a
planted blind spot converges within 2 rounds of the failing case first appearing in a packet, while
the same roster with feedback OFF plateaus.

**The null is code-only pollination — what the live P1 run does.** It hands each round the previous
round's candidate *code*. That works when the roster disagrees, and fails exactly when you need it
most: a single-family roster is wrong the same way, so showing them each other's answers shows them
their own mistake N times. That is F1.

The fix is to show them the **case**, not the code. A failing case is external evidence: it did not
come from the models, which is why it survives a blind spot they share — and why the packet enters
the frame as `tool_result` rather than `peer_message`.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from hypercell.cell.nucleus import Nucleus
from hypercell.cell.runtime import Cell
from hypercell.cognition.base import CompletionResult, Messages
from hypercell.common.types import ProviderConfig, Role
from hypercell.conductor.engine.packets import MAX_CASES, Case, build_packet, extract_cases

# The planted blind spot: every cell in this family forgets that "1.2.3.4." (trailing dot) is
# invalid. No amount of looking at each other's code reveals it — they all agree.
BLIND_SPOT = "1.2.3.4."


class SingleFamilyCell:
    """A whole weights family, modelled honestly: they share one blind spot and one fix.

    It writes the buggy answer forever UNLESS it is shown the specific failing case. Seeing a peer's
    code does nothing, because the peer has the same bug — which is the entire point of F1.
    """

    name = "family"

    def __init__(self) -> None:
        self.calls = 0
        self.saw_case = False

    async def complete(self, messages: Messages, **params: Any) -> CompletionResult:
        self.calls += 1
        blob = "\n".join(m.get("content", "") for m in messages)
        # A peer's *code* never mentions the case — only the checker's evidence does.
        if BLIND_SPOT in blob:
            self.saw_case = True
        text = "CORRECT" if self.saw_case else "BUGGY"
        return CompletionResult(text=text, model="mock", prompt_tokens=1, completion_tokens=1)


def _cell(tmp_path: Path, name: str, cog: SingleFamilyCell) -> Cell:
    role = Role(name=name, prompt="p", provider=ProviderConfig(provider="stub", model="stub"))
    return Cell(role, Nucleus(tmp_path, f"f/{name}/0"), cog)  # type: ignore[arg-type]


# ---------------------------------------------------------------- the F1 replant


async def test_f1_replant_feedback_on_beats_code_only_pollination(tmp_path: Path) -> None:
    """The bar. Same roster, same blind spot, same rounds — the only difference is the packet.

    OFF plateaus because every peer's code carries the same bug. ON converges because the checker's
    failing case is evidence none of them could have produced.
    """
    # ---- feedback OFF: code-only pollination (the live P1 behavior, and the null)
    off = SingleFamilyCell()
    cell_off = _cell(tmp_path / "off", "c0", off)
    peer_code = "BUGGY"  # what a same-family peer produced last round
    for _ in range(5):
        out = await cell_off.produce("validate an ipv4", [peer_code, peer_code], idem=None)
        peer_code = out
    assert out == "BUGGY", "code-only pollination escaped a blind spot it should not have"
    cell_off.nucleus.close()

    # ---- feedback ON: the same roster, plus the checker's failing case
    on = SingleFamilyCell()
    cell_on = _cell(tmp_path / "on", "c0", on)
    first = await cell_on.produce("validate an ipv4", ["BUGGY"], idem="r1")
    assert first == "BUGGY", "round 1 has no packet yet — nothing has failed to report"

    packet = build_packet(
        [
            {
                "body": {
                    "outcome": "gate",
                    "subject": {"cell": "c0", "round": 1},
                    "evidence": f"FAIL: input={BLIND_SPOT} expected=invalid got=valid",
                }
            }
        ],
        round=1,
    )
    second = await cell_on.produce("validate an ipv4", ["BUGGY"], packet=packet.render(), idem="r2")

    assert second == "CORRECT", "the packet did not carry the case through"
    # "<= 2 rounds after the case first appears in a packet" — it landed in the very next one.
    cell_on.nucleus.close()


async def test_the_packet_arrives_as_a_tool_result_not_a_peer_message(tmp_path: Path) -> None:
    """Provenance matters: peer text is opinion, a checker's case is a fact about the world."""
    cog = SingleFamilyCell()
    captured: list[Messages] = []

    async def capture(messages: Messages, **params: Any) -> CompletionResult:
        captured.append(messages)
        return CompletionResult(text="x", model="mock")

    cog.complete = capture  # type: ignore[method-assign]
    cell = _cell(tmp_path, "c0", cog)
    await cell.produce("goal", ["peer code"], packet="FAILING CASES\n- input=1.2.3.4.", idem="k")

    blocks = [m["content"] for m in captured[0] if m["role"] == "user"]
    packet_block = next(b for b in blocks if "FAILING CASES" in b)
    peer_block = next(b for b in blocks if "peer code" in b)
    assert packet_block.startswith("[tool_result")
    assert peer_block.startswith("[peer_message")
    cell.nucleus.close()


# ---------------------------------------------------------------- extracting cases


@pytest.mark.parametrize(
    "evidence",
    [
        "FAIL: input=1.2.3.4. expected=invalid got=valid",
        "CASE 1.2.3.4. -> accepted",
        "checking...\ninput: 1.2.3.4. expected: invalid got: valid\n",
    ],
)
def test_common_checker_shapes_are_understood(evidence: str) -> None:
    cases = extract_cases(evidence, source="c0")
    assert cases, f"no case extracted from {evidence!r}"
    assert any("1.2.3.4." in c.text for c in cases)


def test_unmatched_output_is_dropped_not_guessed_at() -> None:
    """A mis-parsed 'case' is noise wearing evidence's clothes — dropping beats guessing."""
    assert extract_cases("all good\nran 12 checks in 0.4s\nSCORE=1.0") == []


def test_a_passing_receipt_contributes_nothing() -> None:
    """A candidate that passed has nothing to teach the round."""
    packet = build_packet(
        [{"body": {"outcome": "passed", "evidence": "FAIL: this should be ignored"}}], round=1
    )
    assert packet.empty


def test_the_same_failure_from_five_cells_is_ONE_case(tmp_path: Path) -> None:
    """A single-family roster failing identically is one piece of evidence reported five times.

    Printing it five times would crowd out the other four failures that might have broken the tie.
    """
    receipts = [
        {
            "body": {
                "outcome": "gate",
                "subject": {"cell": f"c{i}"},
                "evidence": f"FAIL: input={BLIND_SPOT} expected=invalid got=valid",
            }
        }
        for i in range(5)
    ]
    packet = build_packet(receipts, round=1)
    assert len(packet.cases) == 1


def test_distinct_failures_are_all_carried_up_to_the_cap() -> None:
    receipts = [
        {"body": {"outcome": "gate", "subject": {"cell": f"c{i}"}, "evidence": f"FAIL: case-{i}"}}
        for i in range(10)
    ]
    packet = build_packet(receipts, round=1)
    assert len(packet.cases) == MAX_CASES, "the cap did not bind"
    assert len({c.text for c in packet.cases}) == MAX_CASES


def test_the_packet_names_which_cell_surfaced_a_case() -> None:
    """Provenance inside the packet too: an operator reading it can go back to the candidate."""
    packet = build_packet(
        [{"body": {"outcome": "gate", "subject": {"cell": "c3"}, "evidence": "FAIL: x"}}], round=2
    )
    assert "surfaced by c3" in packet.render()
    assert "round 2" in packet.render()


def test_the_packet_frames_itself_as_evidence_not_instruction() -> None:
    """It enters as DATA. The header says what it is so the model reads it as a fact, not an order."""
    text = build_packet(
        [{"body": {"outcome": "gate", "subject": {"cell": "c0"}, "evidence": "FAIL: x"}}], round=1
    ).render()
    assert "checker output, not opinions" in text


def test_case_render_is_stable() -> None:
    assert Case("input=1 expected=2", source="c1").render() == "- input=1 expected=2   (surfaced by c1)"
    assert Case("bare").render() == "- bare"
