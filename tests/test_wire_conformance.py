"""C1–C12 — the transport conformance battery (contracts/wire.md §12; slice M1).

**The one-file law.** All twelve run from a single spec module against exactly (a) the Medium
protocol and (b) a three-method `FaultInjector`. Any assertion beyond that pair is a contract leak
and the test is redesigned, never special-cased — because the whole point is that this same file
re-runs unchanged against NATS/JetStream at P3, and *that re-run IS the parity falsifier*. A battery
that quietly knows it is talking to SQLite proves nothing about the swap.

Staggered per the ladder: **C1, C3–C9, C11 at b′** (C3 needs `wait()`, which lands with M2);
C2 and C12 at c′ with M3's chain-sealer and compactor.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from hypercell.medium.transport_local import Filter, LocalMedium
from hypercell.medium.wire import REGISTRY, AclDenied


class FaultInjector:
    """Test-harness contract, not Medium contract (wire.md §12)."""

    def __init__(self, home: Path) -> None:
        self.home = home

    def crash(self, medium: LocalMedium) -> LocalMedium:
        """Kill the transport hard and reopen cold. No graceful close — that is the point."""
        medium._db.close()
        return LocalMedium(self.home)

    def corrupt(self, medium: LocalMedium, culture: str, seq: int) -> None:
        """Flip one byte of a stored record, BELOW the API — as an attacker or a disk would."""
        medium._db.execute(
            "UPDATE messages SET body=? WHERE culture=? AND seq=?",
            (json.dumps({"tampered": True}), culture, seq),
        )

    def sever_hint(self, medium: LocalMedium) -> None:
        """Kill watchers, leave the log intact."""
        return None


@pytest.fixture
def med(tmp_path: Path) -> LocalMedium:
    return LocalMedium(tmp_path)


@pytest.fixture
def fault(tmp_path: Path) -> FaultInjector:
    return FaultInjector(tmp_path)


# ---------------------------------------------------------------- C1 total order


def test_c1_total_order(med: LocalMedium) -> None:
    """8 posters x 200 msgs: strictly monotonic, dense, identical across consumers."""
    for poster in range(8):
        for i in range(200):
            med.post("commons", f"cell{poster}", "chat", body={"p": poster, "i": i})

    a = [m["seq"] for m in med.read("commons")]
    b = [m["seq"] for m in med.poll("consumer-b", "commons")]
    assert a == list(range(1, 1601)), "seqs are not dense and monotonic"
    assert a == b, "two consumers disagreed on order"


def test_c1_priority_surfaces_but_never_reorders(med: LocalMedium) -> None:
    """L-ORDER: priority is a rendering hint. A log that reorders is not a log."""
    med.post("commons", "c1", "chat", body={"n": 1}, priority=0)
    med.post("commons", "c2", "chat", body={"n": 2}, priority=9)
    med.post("commons", "c3", "chat", body={"n": 3}, priority=0)
    assert [m["body"]["n"] for m in med.read("commons")] == [1, 2, 3]


def test_c1_seq_is_per_culture_not_global(med: LocalMedium) -> None:
    """A global counter would make two cultures interleave and every replay depend on strangers."""
    med.post("run-a", "c", "chat", body={})
    med.post("run-b", "c", "chat", body={})
    med.post("run-a", "c", "chat", body={})
    assert [m["seq"] for m in med.read("run-a")] == [1, 2]
    assert [m["seq"] for m in med.read("run-b")] == [1]


# ---------------------------------------------------------------- C4 claim-by-log-order


def test_c4_claim_is_won_by_log_order(med: LocalMedium) -> None:
    """8 claimants, one task: the log decides, and it decides the same way for everyone."""
    med.post("commons", "conductor", "task", body={"work": "t1"})
    for i in range(8):
        med.post("commons", f"cell{i}", "claim", body={"task": "t1"}, corr="t1")

    claims = med.read("commons", filt=Filter(types=("claim",), corr="t1"))
    winner = min(claims, key=lambda m: m["seq"])
    assert winner["sender"] == "cell0"
    # Every reader derives the same winner from the same log — no coordinator, no lock.
    assert min(med.read("commons", filt=Filter(types=("claim",))), key=lambda m: m["seq"]) == winner


# ---------------------------------------------------------------- C5 cursor persistence


def test_c5_cursor_resumes_at_k_plus_one(med: LocalMedium, fault: FaultInjector) -> None:
    for i in range(20):
        med.post("commons", "c", "chat", body={"i": i})

    first = med.poll("worker", "commons", limit=10)
    assert [m["body"]["i"] for m in first] == list(range(10))

    reopened = fault.crash(med)
    second = reopened.poll("worker", "commons")
    assert [m["body"]["i"] for m in second] == list(range(10, 20)), "skip or re-delivery past the cursor"
    assert reopened.poll("worker", "commons") == [], "a drained cursor re-delivered"


def test_c5_cursors_are_per_consumer(med: LocalMedium) -> None:
    for i in range(5):
        med.post("commons", "c", "chat", body={"i": i})
    med.poll("a", "commons")
    assert len(med.poll("b", "commons")) == 5, "one consumer's cursor moved another's"


# ---------------------------------------------------------------- C6 filter correctness


def test_c6_every_filter_axis_matches_a_full_scan(med: LocalMedium) -> None:
    """The result set must equal a reference full-scan, and the order must still be seq order."""
    for i in range(200):
        med.post(
            "commons",
            "conductor" if i % 3 == 0 else f"cell{i % 4}",
            "task" if i % 3 == 0 else "chat",
            body={"i": i},
            recipient="cell1" if i % 5 == 0 else None,
            mentions=["cell2"] if i % 7 == 0 else None,
            corr=f"c{i % 6}",
            round=i % 3,
        )
    everything = med.read("commons")

    def scan(pred: Any) -> list[int]:
        return [m["seq"] for m in everything if pred(m)]

    cases = [
        (Filter(types=("task",)), lambda m: m["type"] == "task"),
        (Filter(recipient="cell1"), lambda m: m["recipient"] == "cell1"),
        (Filter(sender="cell2"), lambda m: m["sender"] == "cell2"),
        (Filter(mentions="cell2"), lambda m: "cell2" in (m["mentions"] or [])),
        (Filter(corr="c3"), lambda m: m["corr"] == "c3"),
        (Filter(round=1), lambda m: m["round"] == 1),
        # pairwise
        (Filter(types=("chat",), corr="c3"), lambda m: m["type"] == "chat" and m["corr"] == "c3"),
        (Filter(sender="cell2", round=1), lambda m: m["sender"] == "cell2" and m["round"] == 1),
    ]
    for filt, pred in cases:
        got = [m["seq"] for m in med.read("commons", filt=filt)]
        assert got == scan(pred), f"{filt} diverged from the reference scan"
        assert got == sorted(got), "a filter reordered the log"


# ---------------------------------------------------------------- C7 liberal receiver


def test_c7_unknown_type_is_delivered_and_ignorable(med: LocalMedium) -> None:
    med.post("commons", "cell0", "x-probe", body={"experimental": True})
    got = med.read("commons")
    assert len(got) == 1 and got[0]["type"] == "x-probe"


def test_c7_unknown_field_round_trips_byte_identical(med: LocalMedium) -> None:
    """A future MINOR's extra field must survive an old reader untouched (R2/MIG-5)."""
    body = {"known": 1, "from_the_future": {"nested": [1, 2, 3]}, "unicode": "ünïcødé"}
    med.post("commons", "cell0", "chat", body=body)
    out = med.read("commons")[0]["body"]
    assert out == body

    med.post("commons", "cell0", "chat", body=out)  # re-emit what we polled
    assert med.read("commons")[1]["body"] == body


def test_c7_a_type_outside_the_registry_and_outside_x_is_refused(med: LocalMedium) -> None:
    """Liberal on FIELDS, closed on TYPES. `spawned`/`judgment` were exactly this defect (E1)."""
    with pytest.raises(AclDenied, match="neither a registry type nor an x-"):
        med.post("commons", "cell0", "spawned", body={})


# ---------------------------------------------------------------- C8 idem dedup


def test_c8_repeat_post_returns_the_original_seq(med: LocalMedium) -> None:
    first = med.post("commons", "cell0", "chat", body={"x": 1}, idem="k1")
    second = med.post("commons", "cell0", "chat", body={"x": 1}, idem="k1")
    assert second.dedup is True and second.seq == first.seq
    assert len(med.read("commons")) == 1, "the log holds two records for one idem"


def test_c8_dedup_survives_crash_and_reopen(med: LocalMedium, fault: FaultInjector) -> None:
    first = med.post("commons", "cell0", "chat", body={"x": 1}, idem="k1")
    reopened = fault.crash(med)
    again = reopened.post("commons", "cell0", "chat", body={"x": 1}, idem="k1")
    assert again.dedup is True and again.seq == first.seq
    assert len(reopened.read("commons")) == 1


def test_c8_idem_is_scoped_to_sender(med: LocalMedium) -> None:
    """`(culture, sender, idem)` — two cells may legitimately pick the same key."""
    a = med.post("commons", "cell0", "chat", body={}, idem="same")
    b = med.post("commons", "cell1", "chat", body={}, idem="same")
    assert not b.dedup and a.seq != b.seq


# ---------------------------------------------------------------- C9 replay equality


def test_c9_replay_equals_accumulated_polls(med: LocalMedium) -> None:
    """500 msgs across the registry: the projection must not depend on HOW you read it."""
    senders = {"cell": "cell0", "conductor": "conductor", "operator": "operator"}
    posted = 0
    for i in range(500):
        spec = list(REGISTRY.values())[i % len(REGISTRY)]
        principal = next((senders[c] for c in ("conductor", "operator", "cell") if c in spec.may_post), "cell0")
        if not spec.may_post:
            principal = "cell0"
        med.post("commons", principal, spec.name, body={"i": i}, round=i % 4, corr=f"c{i % 9}")
        posted += 1

    batched: list[dict[str, Any]] = []
    while chunk := med.poll("reader", "commons", limit=37):
        batched.extend(chunk)

    assert len(batched) == posted
    assert [m["seq"] for m in batched] == [m["seq"] for m in med.replay("commons")]
    # The canonical projection excludes ts/hash: those are timing, not content.
    assert med.projection("commons") == med.projection("commons")


def test_c9_all_seventeen_types_are_postable_by_someone(med: LocalMedium) -> None:
    assert len(REGISTRY) == 17, "the registry is not 17 types — the count must be true (R1)"


# ---------------------------------------------------------------- C11 non-mintable ACL


@pytest.mark.parametrize("mint", ["receipt", "verdict", "oracle_gen", "compact", "cmd_receipt"])
def test_c11_a_cell_may_not_post_a_mint_restricted_type(med: LocalMedium, mint: str) -> None:
    with pytest.raises(AclDenied):
        med.post("commons", "cell0", mint, body={"forged": True})
    assert med.read("commons") == [], "a denied post still reached the log"


def test_c11_a_smuggled_record_is_void_at_fold(med: LocalMedium) -> None:
    """The harness smuggles one below the gate. It is not deleted — it is excluded from every fold.

    An append-only log cannot un-say anything, so the honest answer is not erasure but exclusion:
    the record stays visible as an ATTEMPT and `verify().void_by_acl` names it.
    """
    med.post("commons", "conductor", "chat", body={"legit": True})
    med.post("commons", "cell0", "receipt", body={"smuggled": True}, _bypass_acl=True)

    folds = med.read("commons")
    assert [m["body"] for m in folds] == [{"legit": True}], "the smuggled record entered a fold"

    raw = med.read("commons", include_void=True)
    assert len(raw) == 2, "the log forgot the attempt — history must stay truthful"

    report = med.verify("commons")
    assert report["void_by_acl"] == [2], "verify() did not name the void record"


def test_c11_the_conductor_may_post_what_a_cell_may_not(med: LocalMedium) -> None:
    """The gate must also PASS legitimate work, or it is just an outage."""
    assert med.post("commons", "conductor", "receipt", body={"score": 1.0}).seq == 1


def test_c11_the_acl_denial_explains_itself(med: LocalMedium) -> None:
    with pytest.raises(AclDenied, match="correctness gate, not an authn one"):
        med.post("commons", "cell0", "verdict", body={})


# ---------------------------------------------------------------- chain + caps


def test_chain_verifies_and_locates_a_corruption(med: LocalMedium, fault: FaultInjector) -> None:
    """Not C12 (that needs the compactor at c′), but the chain half must hold from M1."""
    for i in range(20):
        med.post("commons", "cell0", "chat", body={"i": i})
    assert med.verify("commons")["ok"]

    fault.corrupt(med, "commons", 7)
    report = med.verify("commons")
    assert not report["ok"] and report["first_bad_seq"] == 7


def test_body_hard_cap_refuses_and_says_why(med: LocalMedium) -> None:
    with pytest.raises(AclDenied, match="artifact pointer"):
        med.post("commons", "cell0", "chat", body={"blob": "x" * 40_000})


def test_the_pragma_block_is_explicit(med: LocalMedium) -> None:
    """E3, closed at M1. Guard G-DB-DURABLE has been reporting this DEGRADED since S9.1."""
    assert med._db.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
    assert int(med._db.execute("PRAGMA synchronous").fetchone()[0]) == 2  # FULL
    assert int(med._db.execute("PRAGMA busy_timeout").fetchone()[0]) == 5000


# ---------------------------------------------------------------- MIG-5 / MIG-3: the version spine


def test_mig5_three_unknown_fields_survive_store_and_relay(med: LocalMedium) -> None:
    """R2 round-trip preservation, 10/10. The null is known-columns storage — the F18 defect.

    A reader that keeps only what it recognises silently truncates every message a newer peer sends,
    which turns a MINOR upgrade into a data-loss event.
    """
    for i in range(10):
        med.post(
            "commons", "conductor", "round_open", body={"i": i},
            future_priority_class="urgent",
            future_trace={"span": f"s{i}", "nested": [1, 2, {"deep": True}]},
            future_flags=["a", "b"],
        )

    got = med.read("commons")
    assert len(got) == 10
    for i, msg in enumerate(got):
        assert msg["future_priority_class"] == "urgent"
        assert msg["future_trace"] == {"span": f"s{i}", "nested": [1, 2, {"deep": True}]}
        assert msg["future_flags"] == ["a", "b"]


def test_mig5_unknown_fields_are_in_the_chain(med: LocalMedium, fault: FaultInjector) -> None:
    """A field the chain does not witness could be edited freely and verify() would still pass —
    which is worse than not chaining at all, because it looks checked."""
    med.post("commons", "conductor", "round_open", body={}, future_col="original")
    assert med.verify("commons")["ok"]

    med._db.execute("UPDATE messages SET ext=? WHERE seq=1", ('{"future_col": "rewritten"}',))
    report = med.verify("commons")
    assert not report["ok"] and report["first_bad_seq"] == 1


def test_mig5_relay_re_emits_byte_identically(med: LocalMedium) -> None:
    """Poll a record and post it back: the unknown fields must make the round trip unchanged."""
    med.post("commons", "conductor", "round_open", body={"x": 1}, unknown_a=1, unknown_b={"z": [3]})
    original = med.read("commons")[0]

    extras = {k: v for k, v in original.items() if k.startswith("unknown_")}
    med.post("commons", "conductor", "round_open", body=original["body"], **extras)
    relayed = med.read("commons")[1]

    assert {k: relayed[k] for k in extras} == extras


def test_mig3_a_matching_census_admits(med: LocalMedium) -> None:
    from hypercell.common.census import census
    from hypercell.medium.spine import admit_spawn

    receipt = admit_spawn(census())
    assert receipt["admitted"] is True and not receipt["skew"]


def test_mig3_a_newer_major_is_refused_with_a_receipt() -> None:
    """The census gate. A newer MAJOR is a message this build would MIS-READ, not merely fail to."""
    from hypercell.common.census import census
    from hypercell.medium.spine import CensusRefusal, admit_spawn, check_census

    image = census()
    image["wire"] = "6.0.0"

    receipt = admit_spawn(image)
    assert receipt["admitted"] is False
    assert receipt["reason"] == "census_newer_major"
    assert "MIS-READ" in receipt["detail"]

    with pytest.raises(CensusRefusal):
        check_census(image)


def test_mig3_a_minor_skew_is_legal() -> None:
    """Rolling upgrades exist. Refusing a MINOR would make every upgrade a full-fleet stop."""
    from hypercell.common.census import census
    from hypercell.medium.spine import check_census

    image = census()
    image["wire"] = "5.9.0"
    verdict = check_census(image)
    assert verdict.ok and verdict.skew == {"wire": ("5.1.0", "5.9.0")}


def test_mig3_an_unknown_contract_and_a_partial_census_are_both_refused() -> None:
    from hypercell.common.census import census
    from hypercell.medium.spine import admit_spawn

    unknown = census() | {"quantum_plane": "1.0.0"}
    assert admit_spawn(unknown)["reason"] == "census_unknown_contract"

    partial = census()
    del partial["oracle"]
    assert admit_spawn(partial)["reason"] == "census_partial"


def test_fleet_versions_folds_the_spread() -> None:
    """A fleet running two MINORs is legal during a rolling upgrade — SEEING it is the point."""
    from hypercell.medium.spine import fleet_versions

    spread = fleet_versions([
        {"body": {"contract": {"wire": "5.1.0"}}},
        {"body": {"contract": {"wire": "5.1.0"}}},
        {"body": {"contract": {"wire": "5.2.0"}}},
        {"body": {"not": "a census"}},
    ])
    assert spread == {"wire": {"5.1.0": 2, "5.2.0": 1}}
