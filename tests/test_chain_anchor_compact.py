"""M3 — chain + anchor + retention (falsifiers C2 · C12 · W3 · W4).

**C2** gold durability: 50 chatter then 1 gold; crash the instant `post()` returns; the gold record
is present WITH its hash and any loss is a contiguous chatter-only suffix.
**C12** chain verify + compaction: verify pristine; a corrupted retained record is located at exactly
its seq; verify holds ACROSS the hole; an archived record's inclusion proof validates.
**W3** chain-sealer + anchor: an anchor mismatch detects a byte-rewrite that stored hashes alone
cannot; a D-gold post returns only after the anchor fsync; seal/anchor lag p95 ≤ 250 ms.
**W4** D-gold durability: a `kill -9` storm mid-traffic loses zero gold.

The null for W3 is an **unanchored chain**: self-consistent, and blind to an editor who can rewrite
the stored hashes too. That null is measured directly below — the chain says "ok" about a history
that never happened, and only the anchor catches it. W4 has no null: durability's bar is absolute.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

from hypercell.conductor.anchor import AnchorLog
from hypercell.medium.compactor import (
    Run,
    compact,
    evidence_closure,
    inclusion_proof,
    leaf_hash,
    merkle_root,
    node_hash,
    plan_compaction,
    prove_archived,
    read_archive,
    retention_class,
    verify_inclusion,
)
from hypercell.medium.transport_local import LocalMedium

AGES = {i: 99_999_999.0 for i in range(1, 2000)}  # everything long past its TTL


@pytest.fixture
def med(tmp_path: Path) -> LocalMedium:
    return LocalMedium(tmp_path, anchor=AnchorLog(tmp_path, "commons", anchor_every=8))


# ================================================================ W3: the anchor


def test_the_null_unanchored_chain_says_ok_about_a_rewritten_history(tmp_path: Path) -> None:
    """The measurement that makes the anchor worth its fsync.

    An attacker rewrites a record AND recomputes every downstream hash. The chain is now perfectly
    self-consistent about a history that never happened, and `verify()` — with no anchor — says ok.
    """
    from hypercell.common.ledger import chain_step, leaf
    from hypercell.medium.transport_local import _anchor as culture_anchor

    unanchored = LocalMedium(tmp_path)  # no anchor: the null
    for i in range(6):
        unanchored.post("commons", "r1/c/0", "chat", body={"i": i})
    assert unanchored.verify("commons")["ok"]

    # Rewrite seq 3's body, then recompute seq 3..6's hashes so the chain still walks.
    unanchored._db.execute(
        "UPDATE messages SET body=? WHERE culture='commons' AND seq=3", (json.dumps({"i": "TAMPERED"}),)
    )
    head = culture_anchor("commons")
    for msg in unanchored.read("commons"):
        known = ("seq", "ts", "culture", "sender", "recipient", "type", "reply_to", "round",
                 "priority", "origin", "idem", "corr", "mentions", "body", "artifact")
        rec = {k: msg[k] for k in known}
        new = "sha256:" + chain_step(head, leaf(rec)).hex()
        unanchored._db.execute(
            "UPDATE messages SET hash=? WHERE culture='commons' AND seq=?", (new, msg["seq"])
        )
        head = bytes.fromhex(new.removeprefix("sha256:"))

    after = unanchored.verify("commons")
    assert after["ok"], "the null is supposed to be fooled — a recomputed chain is self-consistent"
    assert after["anchored"] is None, "and it reports no anchoring at all"


def test_the_anchor_catches_the_rewrite_the_chain_cannot(tmp_path: Path) -> None:
    """Same attack, with an anchor. The stored hashes were rewritten; the anchor file was not."""
    from hypercell.common.ledger import chain_step, leaf
    from hypercell.medium.transport_local import _anchor as culture_anchor

    anchored = LocalMedium(tmp_path, anchor=AnchorLog(tmp_path, "commons", anchor_every=2))
    for i in range(6):
        anchored.post("commons", "r1/c/0", "chat", body={"i": i})
    assert anchored.verify("commons")["ok"]

    anchored._db.execute(
        "UPDATE messages SET body=? WHERE culture='commons' AND seq=3", (json.dumps({"i": "TAMPERED"}),)
    )
    head = culture_anchor("commons")
    for msg in anchored.read("commons"):
        known = ("seq", "ts", "culture", "sender", "recipient", "type", "reply_to", "round",
                 "priority", "origin", "idem", "corr", "mentions", "body", "artifact")
        rec = {k: msg[k] for k in known}
        new = "sha256:" + chain_step(head, leaf(rec)).hex()
        anchored._db.execute("UPDATE messages SET hash=? WHERE culture='commons' AND seq=?",
                             (new, msg["seq"]))
        head = bytes.fromhex(new.removeprefix("sha256:"))

    after = anchored.verify("commons")
    assert not after["ok"], "the anchor failed to catch a full byte-and-hash rewrite"
    assert after["anchor_verdict"] == "ANCHOR MISMATCH"
    assert any(m["seq"] >= 3 for m in after["anchor_mismatches"])


def test_a_missing_anchor_file_degrades_honestly_rather_than_passing(tmp_path: Path) -> None:
    """'consistent, unanchored' is a THIRD state. Reporting it as ok would sell a weaker guarantee
    than the caller thinks they bought."""
    log = AnchorLog(tmp_path, "commons")
    report = log.check({1: "sha256:whatever"})
    assert report.unanchored and report.verdict == "consistent, unanchored"
    assert report.checked == 0


def test_a_gold_post_anchors_synchronously_and_cadence_does_not(tmp_path: Path) -> None:
    """The durability edge: gold's anchor entry is on disk before `post()` returns."""
    log = AnchorLog(tmp_path, "commons", anchor_every=1000)  # cadence effectively off
    med = LocalMedium(tmp_path, anchor=log)

    med.post("commons", "r1/c/0", "chat", body={"i": 1})
    assert log.entries() == [], "chatter anchored despite the cadence being far off"

    posted = med.post("commons", "conductor", "receipt", body={"grade": "pass"})
    entries = log.entries()
    assert len(entries) == 1 and entries[0].seq == posted.seq and entries[0].reason == "gold"


def test_the_cadence_anchors_every_n_messages(tmp_path: Path) -> None:
    log = AnchorLog(tmp_path, "commons", anchor_every=4)
    med = LocalMedium(tmp_path, anchor=log)
    for i in range(12):
        med.post("commons", "r1/c/0", "chat", body={"i": i})
    assert [e.seq for e in log.entries()] == [4, 8, 12]


def test_anchor_lag_p95_is_under_250ms(tmp_path: Path) -> None:
    """W3's bound. On T0 the anchor is written inline, so the lag IS the fsync — measured, not
    assumed, because 'inline' is an argument and 250 ms is a number."""
    import statistics

    log = AnchorLog(tmp_path, "commons", anchor_every=1)
    med = LocalMedium(tmp_path, anchor=log)
    lags = []
    for i in range(40):
        started = time.perf_counter()
        med.post("commons", "conductor", "receipt", body={"i": i}, idem=f"g{i}")
        lags.append((time.perf_counter() - started) * 1000)
    p95 = statistics.quantiles(lags, n=20)[18]
    assert p95 <= 250.0, f"anchor lag p95 {p95:.1f} ms exceeds the 250 ms bar"


def test_a_torn_final_anchor_line_is_dropped(tmp_path: Path) -> None:
    log = AnchorLog(tmp_path, "commons", anchor_every=1)
    log.note(1, "sha256:aaa")
    with open(log.path, "a", encoding="utf-8") as f:
        f.write('{"seq": 2, "hash": "sha256:bb')  # torn
    assert [e.seq for e in log.entries()] == [1]


# ================================================================ C2: gold durability


def test_c2_gold_survives_a_crash_the_instant_post_returns(tmp_path: Path) -> None:
    """50 chatter, then 1 gold, then crash. The gold record is present WITH its hash."""
    log = AnchorLog(tmp_path, "commons", anchor_every=64)
    med = LocalMedium(tmp_path, anchor=log)
    for i in range(50):
        med.post("commons", "r1/c/0", "chat", body={"i": i})
    gold = med.post("commons", "conductor", "receipt", body={"grade": "pass"}, idem="g1")
    med._db.close()  # the crash: no clean shutdown, no further writes

    reopened = LocalMedium(tmp_path, anchor=AnchorLog(tmp_path, "commons"))
    rows = reopened.read("commons")
    survivor = next((m for m in rows if m["seq"] == gold.seq), None)
    assert survivor is not None, "the gold record did not survive"
    assert survivor["hash"] == gold.hash, "the gold record survived without its hash"
    assert reopened.verify("commons")["ok"]


def test_c2_any_loss_is_a_contiguous_chatter_only_suffix(tmp_path: Path) -> None:
    """Prefix-durability (§5.4): a gold commit's fsync covers the whole WAL before it, so nothing
    BELOW a surviving gold record can be missing."""
    log = AnchorLog(tmp_path, "commons", anchor_every=64)
    med = LocalMedium(tmp_path, anchor=log)
    for i in range(20):
        med.post("commons", "r1/c/0", "chat", body={"i": i})
    gold = med.post("commons", "conductor", "receipt", body={"grade": "pass"}, idem="g1")
    for i in range(20, 30):
        med.post("commons", "r1/c/0", "chat", body={"i": i})
    med._db.close()

    reopened = LocalMedium(tmp_path)
    seqs = [m["seq"] for m in reopened.read("commons")]
    below_gold = [s for s in seqs if s <= gold.seq]
    assert below_gold == list(range(1, gold.seq + 1)), (
        "a record below the gold commit is missing: the loss was not a suffix"
    )


# ================================================================ C12: verify + compaction


def test_c12a_verify_is_pristine_on_an_untouched_log(med: LocalMedium) -> None:
    for i in range(30):
        med.post("commons", "r1/c/0", "chat", body={"i": i})
    v = med.verify("commons")
    assert v["ok"] and v["first_bad_seq"] is None and v["zombies"] == []


def test_c12b_a_corrupted_retained_record_is_located_at_exactly_its_seq(med: LocalMedium) -> None:
    for i in range(30):
        med.post("commons", "r1/c/0", "chat", body={"i": i})
    med._db.execute("UPDATE messages SET body=? WHERE culture='commons' AND seq=17",
                    (json.dumps({"i": "corrupt"}),))
    v = med.verify("commons")
    assert not v["ok"] and v["first_bad_seq"] == 17


def test_c12c_verify_holds_across_the_hole(med: LocalMedium, tmp_path: Path) -> None:
    """The chain reconnects through a compacted span via the compact record's own `chain.post` —
    itself chained and anchored, so trusting it is not trusting a bare claim."""
    for i in range(40):
        med.post("commons", "r1/c/0", "chat", body={"i": i})
    med.post("commons", "conductor", "verdict", body={"champion": "a", "evidence": []})

    result = compact(med, "commons", home=tmp_path, age_s=AGES)
    assert result["compacted"] > 0

    v = med.verify("commons")
    assert v["ok"], f"verify failed across the hole: {v.get('reason')}"
    assert v["holes_crossed"] >= 1, "no hole was actually crossed; the drill proved nothing"
    assert v["anchored"] is True


def test_c12d_an_archived_record_inclusion_proof_validates(med: LocalMedium, tmp_path: Path) -> None:
    for i in range(20):
        med.post("commons", "r1/c/0", "chat", body={"i": i})
    med.post("commons", "conductor", "verdict", body={"champion": "a", "evidence": []})

    result = compact(med, "commons", home=tmp_path, age_s=AGES, date="2026-07-27")
    archived = read_archive(tmp_path, "commons", "2026-07-27")
    assert archived, "nothing was archived"

    run = Run(**{
        "frm": result["runs"][0]["from"], "to": result["runs"][0]["to"],
        "count": result["runs"][0]["count"], "merkle_root": result["runs"][0]["merkle_root"],
        "chain_prev": result["runs"][0]["chain"]["prev"], "chain_post": result["runs"][0]["chain"]["post"],
    })
    target = run.frm + 1
    path, leaf, root = prove_archived(archived, run, target)
    assert verify_inclusion(leaf, path, root), "the inclusion proof did not validate against merkle_root"

    # And a record that was NOT in the run must not prove into it.
    forged = leaf_hash(b"sha256:not-a-real-record")
    assert not verify_inclusion(forged, path, root), "a forged leaf proved inclusion"


def test_an_unexplained_gap_is_a_failure_not_a_hole(med: LocalMedium) -> None:
    """A record does not simply go missing. Without a compact record claiming the span, a gap is a
    chain failure — otherwise deleting a row would be a way to make verify() stop complaining."""
    for i in range(10):
        med.post("commons", "r1/c/0", "chat", body={"i": i})
    med._db.execute("DELETE FROM messages WHERE culture='commons' AND seq=5")

    v = med.verify("commons")
    assert not v["ok"] and "unexplained gap" in v.get("reason", "")


def test_zombies_are_named_never_silently_cleaned(med: LocalMedium, tmp_path: Path) -> None:
    """A crash between §9.2 steps 5 and 6 leaves rows inside a compacted span. `verify()` names
    them; housekeeping acts. A verifier that cleaned up would be mutating the log it audits."""
    for i in range(20):
        med.post("commons", "r1/c/0", "chat", body={"i": i})
    med.post("commons", "conductor", "verdict", body={"champion": "a", "evidence": []})

    messages = med.read("commons")
    plan = plan_compaction(messages, now_s=0.0, sealed_head=21, has_open_run=False, age_s=AGES)
    med.post("commons", "conductor", "compact", body=plan.as_body("drop"))
    # ...and then the process dies BEFORE step 6. The rows are still there.

    v = med.verify("commons")
    assert v["zombies"], "rows inside a compacted span were not flagged as zombies"
    assert set(v["zombies"]) & set(plan.eligible_seqs)


# ================================================================ the pin rules


def test_an_open_run_pins_its_whole_span(med: LocalMedium) -> None:
    """A run that is still going is still using its own history."""
    for i in range(20):
        med.post("commons", "r1/c/0", "chat", body={"i": i})
    plan = plan_compaction(med.read("commons"), now_s=0.0, sealed_head=20,
                           has_open_run=True, age_s=AGES)
    assert plan.runs == [], "an open run's span was compacted"


def test_a_cite_pinned_record_survives_and_splits_the_span(med: LocalMedium, tmp_path: Path) -> None:
    """The keeper-aware delete: a record cited by a retained verdict survives whatever its type or
    age, and the span reconnects around it as two runs."""
    for i in range(20):
        med.post("commons", "r1/c/0", "chat", body={"i": i})
    med.post("commons", "conductor", "verdict",
             body={"champion": "a", "evidence": [{"locator": "medium://commons/7"}]})

    result = compact(med, "commons", home=tmp_path, age_s=AGES)
    assert 7 in result["keepers"], "the cite-pinned record was not kept"

    survivors = [m["seq"] for m in med.read("commons")]
    assert 7 in survivors, "a cite-pinned record was deleted"
    assert len(result["runs"]) == 2, f"the keeper did not split the span: {result['runs']}"
    assert med.verify("commons")["ok"]


def test_r_forever_types_are_never_eligible(med: LocalMedium) -> None:
    """The provenance skeleton does not evaporate, at any age."""
    assert retention_class({"type": "receipt"}) == "R-forever"
    assert retention_class({"type": "verdict"}) == "R-forever"
    assert retention_class({"type": "chat"}) == "R-decay"
    assert retention_class({"type": "submission"}) == "R-run"
    # H1+ acts are provenance; H0 acts are run-scoped.
    assert retention_class({"type": "act", "body": {"harm_effective": "H1"}}) == "R-forever"
    assert retention_class({"type": "act", "body": {"harm_effective": "H0"}}) == "R-run"
    # genesis presence is provenance; later phases are not.
    assert retention_class({"type": "presence", "body": {"phase": "genesis"}}) == "R-forever"
    assert retention_class({"type": "presence", "body": {"phase": "announce"}}) == "R-run"


def test_an_unexpired_decay_record_is_not_eligible(med: LocalMedium) -> None:
    for i in range(10):
        med.post("commons", "r1/c/0", "chat", body={"i": i})
    med.post("commons", "conductor", "verdict", body={"champion": "a", "evidence": []})
    fresh = plan_compaction(med.read("commons"), now_s=0.0, sealed_head=11,
                            has_open_run=False, age_s={i: 1.0 for i in range(1, 12)})
    assert fresh.runs == [], "chatter was compacted before its TTL elapsed"


def test_evidence_closure_reads_both_locator_spellings() -> None:
    """The evidence scheme grew a URI form after the first cites were written; an audit must survive
    its own vocabulary changing."""
    msgs = [{"type": "verdict", "body": {"evidence": [{"locator": "medium://commons/12"}, 7, "not-a-ref"]}}]
    assert evidence_closure(msgs) == {12, 7}


# ================================================================ RFC 6962


def test_the_merkle_tree_is_domain_separated() -> None:
    """Without the 0x00/0x01 prefixes a node hash could be presented as a leaf hash, and an
    inclusion proof would accept a subtree where a record belongs."""
    data = b"x"
    assert leaf_hash(data) != node_hash(data, data)


def test_an_odd_node_carries_up_undeduplicated() -> None:
    """Duplicating an odd node makes two different leaf-sets share a root — exactly the ambiguity
    an inclusion proof must not have."""
    three = [leaf_hash(bytes([i])) for i in range(3)]
    duplicated = merkle_root(three + [three[-1]])
    carried = merkle_root(three)
    assert carried != duplicated, "the odd node was duplicated Bitcoin-style"


@pytest.mark.parametrize("n", [1, 2, 3, 4, 5, 7, 8, 9, 16, 17, 33])
def test_every_leaf_proves_inclusion_at_every_tree_size(n: int) -> None:
    leaves = [leaf_hash(bytes([i % 256])) for i in range(n)]
    root = merkle_root(leaves)
    for i in range(n):
        assert verify_inclusion(leaves[i], inclusion_proof(leaves, i), root), f"n={n} i={i}"


def test_a_forged_leaf_never_proves_inclusion() -> None:
    leaves = [leaf_hash(bytes([i])) for i in range(9)]
    root = merkle_root(leaves)
    path = inclusion_proof(leaves, 3)
    assert not verify_inclusion(leaf_hash(b"forged"), path, root)
    assert not verify_inclusion(leaves[4], path, root), "a path proved the wrong leaf"


# ================================================================ idempotence


def test_compaction_is_idempotent(med: LocalMedium, tmp_path: Path) -> None:
    """A re-run after a crash must not double-compact or corrupt the chain (§9.2 failure modes)."""
    for i in range(20):
        med.post("commons", "r1/c/0", "chat", body={"i": i})
    med.post("commons", "conductor", "verdict", body={"champion": "a", "evidence": []})

    first = compact(med, "commons", home=tmp_path, age_s=AGES)
    second = compact(med, "commons", home=tmp_path, age_s=AGES)

    assert first["compacted"] > 0
    assert second["compacted"] == 0, "a second compaction deleted more rows"
    assert med.verify("commons")["ok"]


# ================================================================ W4: the real kill-9 storm


@pytest.mark.slow
def test_w4_a_kill_9_storm_loses_zero_gold(tmp_path: Path) -> None:
    """The bar has no null: durability is absolute. So the process really dies, repeatedly.

    Each round spawns a child posting interleaved chatter and gold, kills it with no cleanup, then
    reopens the log and checks two things: every gold seq the child was TOLD was durable is present
    with its hash, and the chain still verifies. Ten rounds rather than a hundred keeps the drill
    inside a test suite's patience; the failure mode it hunts is not rare if it exists at all.
    """
    from bench.drills.medium_kill9 import CULTURE, SENTINEL

    rounds = 10
    total_gold = 0
    for r in range(rounds):
        home = tmp_path / f"r{r}"
        home.mkdir()
        proc = subprocess.Popen(
            [sys.executable, "-m", "bench.drills.medium_kill9", str(home)],
            cwd=Path(__file__).resolve().parent.parent,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        try:
            # Let it get into a rhythm, then kill at an arbitrary point mid-traffic.
            deadline = time.time() + 20
            while not (home / SENTINEL).exists():
                if proc.poll() is not None:
                    _, err = proc.communicate()
                    pytest.fail(f"round {r}: child died early:\n{err.decode(errors='replace')[-1500:]}")
                if time.time() > deadline:
                    pytest.fail(f"round {r}: child never posted gold")
                time.sleep(0.02)
            time.sleep(0.05 + r * 0.01)  # vary the kill point across rounds
            proc.kill()
        finally:
            proc.wait(timeout=30)

        claimed = [
            json.loads(line)
            for line in (home / SENTINEL).read_text(encoding="utf-8").splitlines()
            if line.strip().endswith("}")
        ]
        assert claimed, f"round {r}: no gold was claimed durable"
        total_gold += len(claimed)

        reopened = LocalMedium(home)
        by_seq = {m["seq"]: m for m in reopened.read(CULTURE)}
        for g in claimed:
            survivor = by_seq.get(g["seq"])
            assert survivor is not None, f"round {r}: gold seq {g['seq']} was LOST after post() returned"
            assert survivor["hash"] == g["hash"], f"round {r}: gold seq {g['seq']} lost its hash"

        # Every loss must be a contiguous suffix: nothing below the last surviving gold is missing.
        last_gold = max(g["seq"] for g in claimed)
        seqs = sorted(by_seq)
        assert seqs[: last_gold] == list(range(1, last_gold + 1)), (
            f"round {r}: a record below gold seq {last_gold} is missing — the loss was not a suffix"
        )
        assert reopened.verify(CULTURE)["ok"], f"round {r}: the chain did not verify after the kill"
        reopened.close()

    assert total_gold >= rounds, "the storm did not actually exercise gold posts"
