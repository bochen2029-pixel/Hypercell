from __future__ import annotations

import pytest
from pydantic import ValidationError

from hypercell.common import ids
from hypercell.common.types import Depth, Message, MessageType, Role, RunManifest


def test_role_roundtrip() -> None:
    r = Role(name="refiner", depth=Depth.d1, prompt="hi", capabilities=["code"])
    r2 = Role.model_validate(r.model_dump())
    assert r2 == r
    assert r2.depth == Depth.d1


def test_role_is_frozen() -> None:
    r = Role(name="x")
    with pytest.raises((ValidationError, TypeError, AttributeError)):
        r.name = "y"  # type: ignore[misc]


def test_message_defaults() -> None:
    m = Message(sender="c1", body="hello")
    assert m.type == MessageType.chat
    assert m.recipient is None and m.seq is None


def test_claim_id_is_stable() -> None:
    assert ids.claim_id("r7", "refiner", 3) == "r7/refiner/3"
    assert ids.claim_id("r7", "refiner", 3) == ids.claim_id("r7", "refiner", 3)


def test_ulid_and_short_id() -> None:
    a, b = ids.new_id(), ids.new_id()
    assert len(a) == 26 and a != b
    assert a < b  # ULIDs are time-sortable
    assert len(ids.short_id()) == 8


def test_run_manifest_defaults() -> None:
    rm = RunManifest(run_id="r1", goal="do x")
    assert rm.seed_diversity is True
    assert rm.topology.value == "tournament"
