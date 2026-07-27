from __future__ import annotations

from pathlib import Path

from hypercell.cell.nucleus import Nucleus


def test_append_checkpoint_resume(tmp_path: Path) -> None:
    n = Nucleus(tmp_path, "r1/role/0")
    n.append("percept", {"prompt": "p"})
    n.checkpoint({"state": "pending", "idem": "a1"})
    n.checkpoint({"state": "done", "idem": "a1"})
    assert n.resume() == {"state": "done", "idem": "a1"}
    n.close()


def test_idempotency_outcome(tmp_path: Path) -> None:
    n = Nucleus(tmp_path, "r1/role/0")
    assert n.outcome_for("a1") is None
    n.append("action", {"verb": "ask"}, idem="a1")
    assert n.outcome_for("a1") is None  # an action is not an outcome
    n.append("outcome", {"text": "done"}, idem="a1")
    assert n.outcome_for("a1") == {"text": "done"}
    n.close()


def test_pending_detection(tmp_path: Path) -> None:
    # N1': pending() returns a LIST (nucleus.md) -- a d2 resident can have several verbs in flight
    # when the box dies, and returning only the oldest silently strands the rest.
    n = Nucleus(tmp_path, "r1/role/0")
    n.append("action", {"verb": "ask", "prompt": "p"}, idem="a1")
    p = n.pending()
    assert len(p) == 1 and p[0]["idem"] == "a1" and p[0]["prompt"] == "p"
    n.append("outcome", {"text": "x"}, idem="a1")
    assert n.pending() == []
    n.close()


def test_pending_reports_every_stranded_verb(tmp_path: Path) -> None:
    """Two actions in flight, one settled: the survivor list is exactly the unsettled one."""
    n = Nucleus(tmp_path, "r1/role/0")
    n.append("action", {"verb": "ask", "prompt": "one"}, idem="a1")
    n.append("action", {"verb": "produce", "goal": "two"}, idem="a2")
    assert [p["idem"] for p in n.pending()] == ["a1", "a2"]
    n.append("outcome", {"text": "done"}, idem="a1")
    assert [p["idem"] for p in n.pending()] == ["a2"]
    n.close()


def test_rebuild_from_ledger(tmp_path: Path) -> None:
    n = Nucleus(tmp_path, "r1/role/0")
    for i in range(5):
        n.append("percept", {"i": i})
    n.close()
    # reopen: the index is rebuilt from the ledger (truth) on open.
    # Since N1' the ledger is anchored, so seq 1 is genesis and the five appends are 2..6.
    n2 = Nucleus(tmp_path, "r1/role/0")
    assert n2._max_seq() == 6
    assert n2.rebuild() == 6
    n2.close()


def test_the_index_is_a_render_not_a_durability_store(tmp_path: Path) -> None:
    """The ledger is truth; the index is rebuilt from it on every open.

    So the index runs at synchronous=NORMAL, not FULL. Fsyncing a render buys nothing that cannot
    be regenerated and costs a real sync per record — paying for durability twice is not twice as
    safe, just slower. Deleting the index entirely must lose nothing.
    """
    n = Nucleus(tmp_path, "r1/render/0")
    for i in range(5):
        n.append("percept", {"i": i})
    head, seq = n.head_hash, n.ledger.seq
    n.close()

    (tmp_path / "r1/render/0" / "index.db").unlink()

    rebuilt = Nucleus(tmp_path, "r1/render/0")
    assert rebuilt.ledger.seq == seq and rebuilt.head_hash == head
    assert rebuilt._max_seq() == seq, "the index did not regenerate from the ledger"
    assert rebuilt.verify().ok
    rebuilt.close()
