"""SEC-2 — the Stage-1a post-ACL (slice SEC-b′).

**The bar, verbatim (ARCH §15):** a non-conductor minting `receipt`/`verdict`/`oracle_gen`/`command`,
or any cell naming `_ops` → **refused 100/100**; a member `presence{phase}`/`chat`/`submission` →
**passes 100/100**; a member-posted `act_receipt` passes ONLY where the member is the executor
principal, else refused.

**The null is v1's sender-trusting `is_directive`** (`cell/membrane.py`) — a predicate that asks the
message who sent it and believes the answer. It is run side by side below, because "the gate refused
100/100" is not a bound unless you know what got through before it existed. The trigger for Stage-1a
has already fired: v1 is multi-pod, so a cell CAN forge `sender=operator`, and under the null that
forgery is not merely undetected, it is obeyed.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from hypercell.cell.membrane import is_directive
from hypercell.common.types import Message, MessageType
from hypercell.medium.firewall import PostPolicy, check_post
from hypercell.medium.transport_local import LocalMedium
from hypercell.medium.wire import CONDITIONAL_ROWS, REGISTRY, AclDenied, check_acl, classify

PRIVILEGED = ("receipt", "verdict", "oracle_gen", "command")
CELLS = [f"r1/candidate/{i}" for i in range(25)]


def _refused(**kw: object) -> bool:
    try:
        check_post(**kw)  # type: ignore[arg-type]
    except AclDenied:
        return True
    return False


# ---------------------------------------------------------------- the null, measured first


def _null_gate(culture: str, sender: str, msg_type: str, **_: object) -> None:
    """v1's post gate, in full. It is empty because v1 HAS no post gate.

    Not a strawman: `is_directive` is the only security predicate v1 owns, and it is a *read*-time
    question asked of a message's own self-declared `origin`. Nothing is consulted when a record is
    written. Writing the null as an empty function is the honest encoding of that.
    """


def test_the_null_admits_every_privileged_mint() -> None:
    """The number the ACL has to beat: 100 attempts, 100 admitted."""
    admitted = sum(
        _null_gate("commons", cell, t) is None for cell in CELLS for t in PRIVILEGED
    )
    assert admitted == 100, "the null is supposed to admit all 100 — that is the point of it"


def test_the_null_cannot_see_the_forgery_because_it_asks_the_message() -> None:
    """One assertion for the whole defect: swap the sender, get the same answer.

    A cell mints a `command` and writes `origin="operator"` in it. `is_directive` says yes — the
    same yes it gives the operator's own command, because it never looks at who sent it. In a
    single-pod v1 that was a convention nobody could break; v1 is multi-pod now, which is why
    Stage-1a is a P2.5 deliverable rather than a P3 one.
    """
    forged = Message(type=MessageType.command, sender="r1/candidate/0", origin="operator", body="")
    genuine = Message(type=MessageType.command, sender="operator", origin="operator", body="")
    assert is_directive(forged) == is_directive(genuine) is True, (
        "the null distinguishes the forgery after all — then it is not the null"
    )

    # And the post-ACL, on the same two messages.
    assert _refused(culture="commons", sender=forged.sender, msg_type="command", body={})
    assert not _refused(culture="commons", sender=genuine.sender, msg_type="command", body={})


def test_the_null_had_no_row_to_enforce_for_five_of_the_privileged_types() -> None:
    """v1's vocabulary is 12 types; the registry is 17. You cannot ACL a type you cannot name.

    `oracle_gen`, `act_receipt`, `cmd_receipt` and `compact` are all privileged or mint-restricted
    in the v5 table and simply do not exist in v1 — so "v1 refused 0/100" understates it. There was
    nothing there to refuse with.
    """
    v1_vocabulary = {m.value for m in MessageType}
    unnameable = {t for t in REGISTRY if t not in v1_vocabulary}
    assert {"oracle_gen", "act_receipt", "cmd_receipt", "compact"} <= unnameable
    for t in unnameable & set(PRIVILEGED):
        assert _refused(culture="commons", sender=CELLS[0], msg_type=t, body={})


# ---------------------------------------------------------------- refused 100/100


def test_a_cell_minting_a_privileged_type_is_refused_100_of_100() -> None:
    refusals = sum(
        _refused(culture="commons", sender=cell, msg_type=t, body={})
        for cell in CELLS
        for t in PRIVILEGED
    )
    assert refusals == 100, f"{100 - refusals} of 100 privileged mints got through"


def test_any_cell_naming_the_ops_room_is_refused_100_of_100() -> None:
    """`_ops` is the operator's room. A cell that can post there can impersonate that channel."""
    open_types = ("chat", "status", "presence", "claim")
    attempts = [(c, t) for c in CELLS for t in open_types]
    assert len(attempts) == 100
    refusals = sum(_refused(culture="_ops", sender=c, msg_type=t, body={}) for c, t in attempts)
    assert refusals == 100, f"{100 - refusals} of 100 cells reached the operator's room"

    # The same posts in the public room are fine: the room is the refusal, not the type.
    assert not any(_refused(culture="commons", sender=c, msg_type=t, body={}) for c, t in attempts)


def test_the_fleet_room_is_conductor_side_too() -> None:
    assert _refused(culture="_fleet", sender="r1/candidate/0", msg_type="chat", body={})
    assert not _refused(culture="_fleet", sender="conductor", msg_type="status", body={})


def test_an_unregistered_sender_classes_as_a_cell_and_is_refused() -> None:
    """Least trust for the unrecognised: the failure mode of guessing wrong must be a refusal."""
    for odd in ("", "operator ", "Conductor", "conductor/", "runner", "surface", "../operator"):
        assert classify(odd) == "cell", f"'{odd}' classed as something other than a cell"
        assert _refused(culture="commons", sender=odd, msg_type="receipt", body={})


# ---------------------------------------------------------------- passes 100/100


def test_member_chatter_passes_100_of_100() -> None:
    """The gate has to let the fabric work. A firewall that refuses everything is not a firewall."""
    shapes: list[tuple[str, dict[str, object]]] = [
        ("presence", {"phase": "announce"}),
        ("presence", {"phase": "spawned"}),
        ("presence", {"phase": "depart"}),
        ("chat", {"text": "hello"}),
        ("submission", {"round": 1, "artifact": "art://x"}),
    ]
    attempts = [(c, t, b) for c in CELLS[:20] for t, b in shapes]
    assert len(attempts) == 100
    passed = sum(not _refused(culture="commons", sender=c, msg_type=t, body=b) for c, t, b in attempts)
    assert passed == 100, f"{100 - passed} of 100 legitimate member posts were refused"


# ---------------------------------------------------------------- presence{phase}, the conditional row


def test_presence_genesis_is_conductor_or_operator_only() -> None:
    """A culture coming into existence is not a claim a member makes about itself."""
    for cell in CELLS[:10]:
        assert _refused(culture="commons", sender=cell, msg_type="presence", body={"phase": "genesis"})
    for privileged in ("conductor", "operator"):
        assert not _refused(
            culture="commons", sender=privileged, msg_type="presence", body={"phase": "genesis"}
        )


def test_a_bodyless_presence_is_not_treated_as_genesis() -> None:
    """Fail-closed must not mean fail-useless: absent phase is a later phase, not genesis."""
    assert not _refused(culture="commons", sender="r1/candidate/0", msg_type="presence", body=None)


# ---------------------------------------------------------------- round_open, the conditional row (R14)


def test_round_open_is_conductor_only_unless_the_manifest_declares_self_clocking() -> None:
    assert _refused(culture="run-a", sender="r1/candidate/0", msg_type="round_open", body={})

    declared = PostPolicy(self_clocked_cultures=frozenset({"run-a"}))
    assert not _refused(
        culture="run-a", sender="r1/candidate/0", msg_type="round_open", body={}, policy=declared
    )
    # The declaration is per-culture, not global.
    assert _refused(
        culture="run-b", sender="r1/candidate/0", msg_type="round_open", body={}, policy=declared
    )


@pytest.mark.parametrize("key", ["gen", "generation", "oracle_gen"])
def test_a_self_clocked_round_open_may_never_carry_a_generation_bump(key: str) -> None:
    """Clocking your own rounds is scheduling. Advancing the generation is grading yourself."""
    declared = PostPolicy(self_clocked_cultures=frozenset({"run-a"}))
    assert _refused(
        culture="run-a", sender="r1/candidate/0", msg_type="round_open",
        body={key: 2}, policy=declared,
    )
    # The conductor keeps the right the culture does not have.
    assert not _refused(culture="run-a", sender="conductor", msg_type="round_open", body={key: 2})


def test_the_self_clock_declaration_is_not_a_post_argument(tmp_path: Path) -> None:
    """A conditional row a caller can widen by passing a flag is a suggestion, not an ACL.

    The policy lives on the Medium, set from the FROZEN manifest — so there is no argument a
    poster can supply that turns its own row on.
    """
    med = LocalMedium(tmp_path)
    with pytest.raises(AclDenied):
        med.post("run-a", "r1/candidate/0", "round_open", body={})

    import inspect

    params = set(inspect.signature(med.post).parameters)
    assert "policy" not in params and "self_clocked" not in params, (
        "post() takes the self-clock decision as an argument; a caller could then grant it to itself"
    )
    assert not med.post("run-a", "conductor", "round_open", body={}).dedup


# ---------------------------------------------------------------- act_receipt: no act reports itself


def test_the_executor_principal_may_mint_the_act_receipt() -> None:
    assert not _refused(
        culture="commons", sender="r1/refiner/0/executor", msg_type="act_receipt",
        body={"actor": "r1/refiner/0", "executor": "r1/refiner/0/executor", "exec": "ok"},
    )
    assert not _refused(
        culture="commons", sender="runner-3", msg_type="act_receipt",
        body={"actor": "r1/refiner/0", "executor": "runner-3", "exec": "ok"},
    )


def test_the_acting_cell_may_not_mint_the_receipt_for_its_own_act() -> None:
    """A5. Under the null this is the F3 spoof one level up: a compromised cell writing its own
    world-witnesses, which is precisely what an auditor reads the receipt to rule out."""
    assert _refused(
        culture="commons", sender="r1/refiner/0", msg_type="act_receipt",
        body={"actor": "r1/refiner/0", "exec": "ok"},
    )


def test_an_executor_may_not_witness_another_executors_work() -> None:
    """A witness signs its own name or it is not a witness."""
    assert _refused(
        culture="commons", sender="runner-3", msg_type="act_receipt",
        body={"actor": "r1/refiner/0", "executor": "runner-7", "exec": "ok"},
    )


def test_a_distinct_principal_is_what_makes_the_receipt_worth_anything() -> None:
    """The in-process executor is a DISTINCT principal string; that distinctness is the mechanism."""
    body = {"actor": "r1/refiner/0", "executor": "r1/refiner/0", "exec": "ok"}
    assert _refused(culture="commons", sender="r1/refiner/0", msg_type="act_receipt", body=body)


# ---------------------------------------------------------------- the rule is live, not dormant


def test_a_real_receipt_from_the_real_executor_satisfies_the_real_ACL(tmp_path: Path) -> None:
    """The rule reads `actor`/`executor` off the body — so something must actually put them there.

    A predicate that consults fields nobody writes is dormant, and dormant checks read as coverage
    while enforcing nothing (F26). This runs a genuine act through `ActExecutor` and feeds the
    receipt it wrote to the gate that will carry it onto the Medium at ACT-1.
    """
    from hypercell.act.executor import ActExecutor
    from hypercell.cell.nucleus import Nucleus

    nucleus = Nucleus(tmp_path, "r1/refiner/0")
    ex = ActExecutor(nucleus=nucleus, home=tmp_path)
    ex.act("fs.read", {"path": "ipv4-spec.txt"}, harm_declared="H0")

    written = [r for r in nucleus.records_of_kind("act_receipt")]
    assert written, "the act wrote no receipt"
    body = written[-1]["body"]
    assert body["actor"] == "r1/refiner/0"
    assert body["executor"] == "r1/refiner/0/executor"

    # The witness may post it; the subject may not.
    assert not _refused(
        culture="commons", sender=body["executor"], msg_type="act_receipt", body=body
    )
    assert _refused(culture="commons", sender=body["actor"], msg_type="act_receipt", body=body)
    nucleus.close()


# ---------------------------------------------------------------- the two homes stay two homes


def test_the_security_law_never_widens_a_row_the_table_did_not_mark_conditional() -> None:
    """wire.REGISTRY is the ONE privilege table (R14); the firewall states the law OVER it.

    Fuzz every type against every principal class: wherever the flat row refuses, the post-ACL must
    also refuse — *except* on rows the table itself marks `CONDITIONAL_ROWS`, which is how a row
    like "conductor by default, unless the frozen manifest says otherwise" is expressed at all.
    A security predicate that could quietly open a door the table closed would make the table a
    comment; one that can only open doors the table marked openable is a law.
    """
    senders = {
        "cell": "r1/candidate/0", "conductor": "conductor", "operator": "operator",
        "executor": "runner-1", "surface": "surface:cli",
    }
    checked = 0
    for msg_type in REGISTRY:
        for cls, sender in senders.items():
            assert classify(sender) == cls
            try:
                check_acl(msg_type, sender)
            except AclDenied:
                # Widest possible policy: if a row can be widened at all, this finds it.
                everything = PostPolicy(self_clocked_cultures=frozenset({"commons"}))
                refused = _refused(
                    culture="commons", sender=sender, msg_type=msg_type, body={}, policy=everything
                )
                if msg_type in CONDITIONAL_ROWS:
                    continue  # declared openable by the table; the row above proves it stays shut by default
                assert refused, f"the post-ACL WIDENED the '{msg_type}' row for a '{cls}' principal"
                checked += 1
    assert checked >= 40, f"only {checked} refusing rows exercised; the fuzz is not covering the table"


def test_only_the_declared_conditional_rows_are_widenable() -> None:
    """The firewall's widening branch is keyed off the table's own list, so drift is impossible.

    If someone adds a conditional row to `wire.py` and forgets the law here, or writes a law for a
    row the table never marked, this fails rather than shipping a door nobody documented.
    """
    assert CONDITIONAL_ROWS == frozenset({"round_open"})

    everything = PostPolicy(self_clocked_cultures=frozenset({"commons"}))
    widened = {
        t
        for t in REGISTRY
        if _refused(culture="commons", sender="r1/candidate/0", msg_type=t, body={})
        != _refused(culture="commons", sender="r1/candidate/0", msg_type=t, body={}, policy=everything)
    }
    assert widened == CONDITIONAL_ROWS, f"policy widened {widened}, table declares {set(CONDITIONAL_ROWS)}"


def test_an_x_extension_is_still_delivered_and_ignorable() -> None:
    """C7's liberal receiver survives the ACL: unknown-but-legal is not the same as forbidden."""
    assert not _refused(culture="commons", sender="r1/candidate/0", msg_type="x-vendor-thing", body={})


# ---------------------------------------------------------------- C11: smuggled past the gate


def test_a_record_smuggled_past_the_gate_is_void_at_fold(tmp_path: Path) -> None:
    """The void set must be exactly the refused set, or a smuggled record finds the gap between them."""
    med = LocalMedium(tmp_path)
    with pytest.raises(AclDenied):
        med.post("commons", "r1/candidate/0", "receipt", body={"grade": "pass"})

    posted = med.post("commons", "r1/candidate/0", "receipt", body={"grade": "pass"}, _bypass_acl=True)
    row = med._db.execute(
        "SELECT void_by_acl FROM messages WHERE culture='commons' AND seq=?", (posted.seq,)
    ).fetchone()
    assert row and row[0], "a smuggled privileged mint was not marked void at fold"


def test_void_at_fold_and_the_gate_are_one_predicate() -> None:
    """`wire.void_at_fold` is C11's vocabulary; it must not be a second, weaker opinion."""
    from hypercell.medium.wire import void_at_fold

    cases = [
        ("commons", "r1/candidate/0", "receipt", {}),
        ("commons", "r1/candidate/0", "chat", {}),
        ("_ops", "r1/candidate/0", "chat", {}),
        ("commons", "r1/candidate/0", "presence", {"phase": "genesis"}),
        ("commons", "r1/candidate/0", "presence", {"phase": "announce"}),
        ("commons", "r1/refiner/0", "act_receipt", {"actor": "r1/refiner/0"}),
        ("commons", "conductor", "receipt", {}),
    ]
    for culture, sender, msg_type, body in cases:
        assert void_at_fold(msg_type, sender, culture=culture, body=body) == _refused(
            culture=culture, sender=sender, msg_type=msg_type, body=body
        ), f"void_at_fold disagrees with the gate on {msg_type} from {sender} in {culture}"


def test_voidness_uses_the_SAME_predicate_as_the_gate(tmp_path: Path) -> None:
    """The conditional rows count too: a smuggled `_ops` post is void, not merely impolite."""
    med = LocalMedium(tmp_path)
    posted = med.post("_ops", "r1/candidate/0", "chat", body={"text": "hi"}, _bypass_acl=True)
    row = med._db.execute(
        "SELECT void_by_acl FROM messages WHERE culture='_ops' AND seq=?", (posted.seq,)
    ).fetchone()
    assert row and row[0], (
        "voidness was decided by a weaker predicate than the gate — the gap between 'refused' "
        "and 'does not count' is what a smuggled record is looking for"
    )
