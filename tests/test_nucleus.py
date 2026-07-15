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
    n = Nucleus(tmp_path, "r1/role/0")
    n.append("action", {"verb": "ask", "prompt": "p"}, idem="a1")
    p = n.pending()
    assert p is not None and p["idem"] == "a1" and p["prompt"] == "p"
    n.append("outcome", {"text": "x"}, idem="a1")
    assert n.pending() is None
    n.close()


def test_rebuild_from_ledger(tmp_path: Path) -> None:
    n = Nucleus(tmp_path, "r1/role/0")
    for i in range(5):
        n.append("percept", {"i": i})
    n.close()
    # reopen: the index is rebuilt from the ledger (truth) on open.
    n2 = Nucleus(tmp_path, "r1/role/0")
    assert n2._max_seq() == 5
    assert n2.rebuild() == 5
    n2.close()
