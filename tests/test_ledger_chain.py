"""NUC-1 — hash chain + genesis (ARCHITECTURE §15; slice N1′), and the canon it rests on.

The bar: **flip any byte in any record and `verify` names the first bad seq**, 100% over a fuzz
suite; a forged `forked_from` fails child verify.

The null this kills: the live unchained ledger — v1 today, where a mid-file edit is invisible.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from hypercell.common import ledger as L
from hypercell.common.canon import canon, digest
from hypercell.common.census import census

# ---------------------------------------------------------------- the canon (RFC 8785)


def test_keys_sort_and_separators_are_canonical() -> None:
    assert canon({"b": 1, "a": 2}) == '{"a":2,"b":1}'
    assert canon([1, 2, 3]) == "[1,2,3]"


def test_absent_and_null_are_identical() -> None:
    """wire.md §5.1: an omitted field and an explicit null MUST hash the same."""
    assert canon({"a": 1, "b": None}) == canon({"a": 1})
    assert digest({"a": 1, "b": None}) == digest({"a": 1})


def test_numbers_serialize_as_ecmascript() -> None:
    assert canon(1.0) == "1"  # not "1.0"
    assert canon(0.0) == "0"
    assert canon(-0.0) == "0"
    assert canon(1.5) == "1.5"
    assert canon(100) == "100"


def test_canon_refuses_what_it_cannot_reproduce() -> None:
    """Refusing beats emitting bytes another implementation might spell differently."""
    for bad in (float("nan"), float("inf"), float("-inf")):
        with pytest.raises(ValueError):
            canon(bad)
    with pytest.raises(ValueError):
        canon(2**53)  # beyond IEEE-754 exact integers
    with pytest.raises(TypeError):
        canon({"a": {1, 2}})  # a set has no canonical JSON form


def test_unicode_keys_sort_by_utf16_code_unit_not_code_point() -> None:
    """JCS §3.2.3 sorts by UTF-16 code unit; Python's default sorts by code point. They DISAGREE.

    U+1F600 encodes as the surrogate pair D83D DE00, and 0xD83D < 0xFFFF — so JCS puts the emoji
    FIRST, while sorting by code point (128512 > 65535) would put U+FFFF first. A chain that got
    this backwards would still verify against itself and fail against every other implementation,
    which is the worst possible failure mode: silent, local, and only visible at a boundary.
    """
    emoji, bmp_max = "\U0001f600", "￿"
    out = canon({emoji: 1, bmp_max: 2})
    assert out.index(f'"{emoji}"') < out.index(f'"{bmp_max}"'), "JCS order"
    assert sorted([emoji, bmp_max]) == [bmp_max, emoji], "code-point order is the opposite"


# ---------------------------------------------------------------- genesis


def _ledger(tmp_path: Path, claim: str = "r1/role/0") -> L.Ledger:
    return L.Ledger(tmp_path / "ledger.jsonl", claim_id=claim)


def test_genesis_is_seq_one_gold_and_carries_the_census(tmp_path: Path) -> None:
    lg = _ledger(tmp_path)
    assert lg.genesis(census()) == 1
    rec = next(lg.records())
    assert rec["seq"] == 1 and rec["kind"] == "genesis"
    assert rec["body"]["contract"]["wire"] == "5.1.0"
    assert len(rec["body"]["contract"]) == 9, "the census is the 9-tuple (pairing law H2)"


def test_genesis_is_exactly_once(tmp_path: Path) -> None:
    lg = _ledger(tmp_path)
    lg.genesis(census())
    with pytest.raises(ValueError, match="exactly once"):
        lg.genesis(census())


def test_genesis_refuses_an_empty_census(tmp_path: Path) -> None:
    """A ledger that cannot say which contract versions wrote it is not migratable (G3)."""
    with pytest.raises(ValueError, match="census"):
        _ledger(tmp_path).genesis({})


def test_anchor_is_claim_bound(tmp_path: Path) -> None:
    """Two cells must not share a chain prefix, or one could replay the other's head."""
    assert L.anchor("r1/role/0") != L.anchor("r1/role/1")


# ---------------------------------------------------------------- NUC-1: the fuzz suite


def _seed(tmp_path: Path, n: int = 8) -> L.Ledger:
    lg = _ledger(tmp_path)
    lg.genesis(census())
    for i in range(n):
        lg.append("percept", {"i": i, "text": f"record {i}"})
    lg.flush()
    return lg


def test_clean_chain_verifies(tmp_path: Path) -> None:
    lg = _seed(tmp_path)
    report = lg.verify_chain()
    assert report.ok and report.checked == 9 and report.first_bad_seq is None


@pytest.mark.parametrize("target_seq", list(range(1, 10)))
def test_flipping_any_record_is_caught_and_named(tmp_path: Path, target_seq: int) -> None:
    """The bar, one record at a time: every seq, corrupted, must be named as the FIRST bad seq."""
    path = tmp_path / "ledger.jsonl"
    lg = _seed(tmp_path)
    assert lg.verify_chain().ok

    lines = path.read_text(encoding="utf-8").splitlines()
    rec = json.loads(lines[target_seq - 1])
    rec["body"] = {**rec["body"], "tampered": True} if isinstance(rec["body"], dict) else "tampered"
    lines[target_seq - 1] = json.dumps(rec, ensure_ascii=False)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    reopened = L.Ledger(path, claim_id="r1/role/0")
    report = reopened.verify_chain()
    assert not report.ok
    assert report.first_bad_seq == target_seq, f"named {report.first_bad_seq}, tampered {target_seq}"
    assert "does not chain" in report.reason


def test_flipping_a_stored_hash_is_caught(tmp_path: Path) -> None:
    """Rewriting the chain column itself must not launder the edit."""
    path = tmp_path / "ledger.jsonl"
    _seed(tmp_path, n=3)
    lines = path.read_text(encoding="utf-8").splitlines()
    rec = json.loads(lines[2])
    rec["hash"] = "sha256:" + "00" * 32
    lines[2] = json.dumps(rec)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    report = L.Ledger(path, claim_id="r1/role/0").verify_chain()
    assert not report.ok and report.first_bad_seq == 3


def test_deleting_a_middle_record_is_caught(tmp_path: Path) -> None:
    """Excision breaks the chain at the successor — you cannot quietly drop history."""
    path = tmp_path / "ledger.jsonl"
    _seed(tmp_path, n=5)
    lines = path.read_text(encoding="utf-8").splitlines()
    del lines[2]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    report = L.Ledger(path, claim_id="r1/role/0").verify_chain()
    assert not report.ok


def test_forged_forked_from_fails_child_verify(tmp_path: Path) -> None:
    """Lineage is in-chain: rewriting who a child forked from breaks its own genesis."""
    path = tmp_path / "ledger.jsonl"
    child = L.Ledger(path, claim_id="r1/role/1")
    child.genesis(census(), forked_from={"claim": "r1/role/0", "at_seq": 4, "head_hash": "sha256:" + "ab" * 32})
    child.append("percept", {"i": 0})
    child.flush()
    assert child.verify_chain().ok

    lines = path.read_text(encoding="utf-8").splitlines()
    rec = json.loads(lines[0])
    rec["body"]["forked_from"]["claim"] = "r1/role/9"  # forge the parent
    lines[0] = json.dumps(rec, ensure_ascii=False)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    report = L.Ledger(path, claim_id="r1/role/1").verify_chain()
    assert not report.ok and report.first_bad_seq == 1


# ---------------------------------------------------------------- torn tail + durability


def test_torn_tail_is_truncated_and_the_prefix_still_verifies(tmp_path: Path) -> None:
    """A process killed mid-append leaves half a line. A half-record is not a record."""
    path = tmp_path / "ledger.jsonl"
    _seed(tmp_path, n=4)
    with open(path, "a", encoding="utf-8") as f:
        f.write('{"seq": 6, "kind": "percept", "body": {"i": ')  # no newline: torn

    reopened = L.Ledger(path, claim_id="r1/role/0")
    assert reopened.seq == 5, "the torn record must not count"
    assert reopened.verify_chain().ok, "everything before the tear still verifies"
    assert not path.read_text(encoding="utf-8").endswith('"i": ')


def test_append_after_torn_tail_recovery_chains_correctly(tmp_path: Path) -> None:
    """Recovery must restore the head hash, not just the seq — else the next append forks silently."""
    path = tmp_path / "ledger.jsonl"
    _seed(tmp_path, n=3)
    with open(path, "a", encoding="utf-8") as f:
        f.write('{"seq": 5, "partial"')

    reopened = L.Ledger(path, claim_id="r1/role/0")
    reopened.append("percept", {"after": "recovery"})
    reopened.flush()
    assert reopened.verify_chain().ok


def test_gold_is_durable_on_return_standard_rides_the_buffer(tmp_path: Path) -> None:
    """Two laws, one group-commit (nucleus.md §4)."""
    path = tmp_path / "ledger.jsonl"
    lg = L.Ledger(path, claim_id="r1/role/0")
    lg.genesis(census())  # gold: on disk immediately

    lg.append("percept", {"i": 1}, durability="standard")
    assert path.read_text(encoding="utf-8").count("\n") == 1, "standard writes ride the buffer"

    lg.append("outcome", {"text": "x"}, durability="gold")
    assert path.read_text(encoding="utf-8").count("\n") == 3, "gold flushes itself and the buffer"


def test_records_sees_buffered_writes(tmp_path: Path) -> None:
    """The log is one thing: a buffered record is not invisible to its own reader."""
    lg = _ledger(tmp_path)
    lg.genesis(census())
    lg.append("percept", {"i": 1}, durability="standard")
    assert [r["seq"] for r in lg.records()] == [1, 2]


def test_sealed_segment_carries_range_and_head(tmp_path: Path) -> None:
    """Sealing is what makes an old segment cheap to trust without re-reading its predecessors."""
    lg = _seed(tmp_path, n=3)
    head = lg.head_hash
    sealed = lg.seal_segment()
    meta = json.loads(sealed.with_suffix(".meta.json").read_text(encoding="utf-8"))
    assert meta["lo"] == 1 and meta["hi"] == 4 and meta["head_hash"] == head
    assert meta["construction"] == "hypercell/nucleus-chain/1"


# ---------------------------------------------------------------- honest epoch


def test_pre_chain_records_adopt_the_chain_without_backdating(tmp_path: Path) -> None:
    """HONEST-EPOCH: earlier records stay immutable-but-unhashed and the genesis SAYS so.

    Back-dating hashes over bytes nobody witnessed would be the fabric lying about its own past.
    """
    path = tmp_path / "ledger.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        for i in (1, 2):
            legacy = {"seq": i, "ts": "2026-07-01T00:00:00.000Z", "kind": "percept", "body": {"i": i}}
            f.write(json.dumps(legacy) + "\n")

    lg = L.Ledger(path, claim_id="r1/role/0")
    assert lg.seq == 2
    lg.adopt_chain(census(), at_seq=3)
    lg.append("percept", {"i": 3})
    lg.flush()

    report = lg.verify_chain()
    assert report.ok, report.reason
    assert report.checked == 2, "only post-adoption records are chain-checked; the past is labeled"


# ---------------------------------------------------------------- sealing must not break verify


def test_chain_still_verifies_across_a_sealed_segment(tmp_path: Path) -> None:
    """A sealed segment is still history, and `verify` must walk through it.

    Regression: sealing used to hide the segment from `records()`, so `verify_chain` restarted at
    the anchor and reported a FALSE tamper on an untouched log. A guard that cries wolf is worse
    than no guard, because nobody believes the real alarm.
    """
    lg = _seed(tmp_path, n=3)
    lg.seal_segment()
    lg.append("percept", {"i": "after-seal"})
    lg.flush()

    report = lg.verify_chain()
    assert report.ok, report.reason
    assert report.checked == 5, "the sealed records must be walked, not skipped"


def test_reopening_a_sealed_ledger_continues_the_chain(tmp_path: Path) -> None:
    """Regression: reopen after sealing used to reset to seq 0 and re-issue sealed numbers."""
    path = tmp_path / "ledger.jsonl"
    lg = _seed(tmp_path, n=3)
    sealed_head, sealed_seq = lg.head_hash, lg.seq
    lg.seal_segment()

    reopened = L.Ledger(path, claim_id="r1/role/0")
    assert reopened.seq == sealed_seq, "sequence must continue past sealed history"
    assert reopened.head_hash == sealed_head, "head must continue past sealed history"

    reopened.append("percept", {"i": "next"})
    reopened.flush()
    assert reopened.verify_chain().ok


def test_tamper_inside_a_sealed_segment_is_still_caught(tmp_path: Path) -> None:
    """Sealing must not launder an edit — read-only is a permission, not a proof."""
    lg = _seed(tmp_path, n=3)
    sealed = lg.seal_segment()
    lg.append("percept", {"i": "after"})
    lg.flush()
    assert lg.verify_chain().ok

    import os as _os

    _os.chmod(sealed, 0o644)
    lines = sealed.read_text(encoding="utf-8").splitlines()
    rec = json.loads(lines[2])
    rec["body"]["text"] = "rewritten history"
    lines[2] = json.dumps(rec, ensure_ascii=False)
    sealed.write_text("\n".join(lines) + "\n", encoding="utf-8")

    report = L.Ledger(tmp_path / "ledger.jsonl", claim_id="r1/role/0").verify_chain()
    assert not report.ok and report.first_bad_seq == 3


def test_records_spans_segments_in_seq_order(tmp_path: Path) -> None:
    lg = _seed(tmp_path, n=2)
    lg.seal_segment()
    lg.append("percept", {"i": 99})
    lg.flush()
    assert [r["seq"] for r in lg.records()] == [1, 2, 3, 4]
