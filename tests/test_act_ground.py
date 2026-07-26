"""GROUND-0's falsifiers — ACT-GATE-1, ACT-SCRUB-1, GROUND-1, GX-1(a) (slice GROUND-0).

* **ACT-GATE-1** — 20 disguised mutations → 100% `refused/harm_derived`, zero executions, every
  refusal a receipt. Null: trust the declaration.
* **ACT-SCRUB-1** — planted adapter keys as query/body/header carriers across 3 profiles → **zero
  credential bytes** in any receipt or evidence bundle. Null: raw provenance.
* **GROUND-1** — the seeded-fabrication classes: forged `act://` caught 100% at post-gate;
  digest-mismatch and quote-not-in-source caught 10/10. Null: `none` mode.
* **GX-1(a)** — the act channel exists end-to-end and produces a warranted, cited answer.

GX-2 (warrant affordability, a token-ratio bar) and GROUND-2 (the dial beating an honest declared
baseline on judged classes) are **measurement drills over real model runs at scale**. The mechanism
they measure is built here; the numbers require a live bench, and inventing them in a unit test
would be exactly the fabrication this slice exists to prevent. They are recorded as outstanding in
the build ledger rather than faked green.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from hypercell.act.adapters import scrub
from hypercell.act.evidence import Citation, extract_citations, validate
from hypercell.act.executor import ActExecutor
from hypercell.act.profiles import ANNEX_A, ProfileRefusal, gate, shape_harm
from hypercell.act.store import ArtifactStore
from hypercell.cell.nucleus import Nucleus
from hypercell.conductor.governor import Escrow
from hypercell.medium.firewall import Trifecta

CORPUS = Path(__file__).resolve().parent.parent / "bench" / "fixtures" / "grounded-corpus"


@pytest.fixture
def ex(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ActExecutor:
    monkeypatch.setenv("HYPERCELL_GROUNDED_CORPUS", str(CORPUS))
    monkeypatch.setenv("HYPERCELL_FS_ROOT", str(CORPUS))
    return ActExecutor(Nucleus(tmp_path, "r1/refiner/0"), home=tmp_path, role_harm_ceiling="H0")


# ---------------------------------------------------------------- ACT-GATE-1: 20 disguised mutations


def _mutations() -> list[tuple[str, dict[str, object]]]:
    """Twenty acts that LOOK like reads. Each declares H0; each is shaped like a write."""
    m: list[tuple[str, dict[str, object]]] = []
    for i in range(4):  # GET + auth
        auth = {"Authorization": "Bearer abcdefgh12345678"}
        m.append((f"get-auth-{i}", {"url": f"https://example.test/p{i}", "headers": auth}))
    for i in range(4):  # GET + body
        m.append((f"get-body-{i}", {"url": f"https://example.test/p{i}", "body": '{"delete": true}'}))
    for i in range(4):  # POST declared H0
        m.append((f"post-as-h0-{i}", {"url": f"https://example.test/p{i}", "method": "POST"}))
    for i in range(4):  # state-addressing args
        m.append((f"state-addr-{i}", {"url": f"https://example.test/p?action=delete&id={i}"}))
    for i in range(4):  # cell-supplied cookie / session
        cookie = {"Cookie": "session=deadbeefdeadbeef"}
        m.append((f"cell-cookie-{i}", {"url": f"https://example.test/p{i}", "headers": cookie}))
    assert len(m) == 20
    return m


MUTATIONS = _mutations()


@pytest.mark.parametrize("name,args", MUTATIONS, ids=[n for n, _ in MUTATIONS])
def test_disguised_mutation_is_refused_harm_derived(ex: ActExecutor, name: str, args: dict[str, object]) -> None:
    """100% refused, zero executions — and the refusal names `harm_derived`, not something vague."""
    receipt = ex.act("web.fetch", args, harm_declared="H0")
    assert receipt.exec == "refused"
    assert receipt.reason == "harm_derived", f"{name} refused for the wrong reason: {receipt.reason}"
    assert receipt.artifact_uri is None, "a refused act produced an artifact — it executed"


def test_all_twenty_refused_and_every_refusal_is_a_receipt(ex: ActExecutor) -> None:
    """A gate that refuses silently teaches nobody and audits to nothing."""
    for _, args in MUTATIONS:
        ex.act("web.fetch", args, harm_declared="H0")

    receipts = ex.nucleus.records_of_kind("act_receipt")
    assert len(receipts) == 20, "not every refusal was journaled"
    assert all(r["body"]["exec"] == "refused" for r in receipts)
    assert all(r["body"]["reason"] == "harm_derived" for r in receipts)
    # Nothing was journaled as an *action*: a refusal happens before JOURNAL, so nothing was attempted.
    assert ex.nucleus.records_of_kind("action") == []


def test_declared_below_derived_is_never_silently_promoted() -> None:
    """The wager must be cell-authored (adjudication #4). Promotion would decide FOR the cell."""
    with pytest.raises(ProfileRefusal, match="will not promote it for you"):
        gate(
            capability_ref="web.fetch",
            args={"url": "https://x.test/a", "method": "DELETE"},
            harm_declared="H0",
            role_tools=["web.fetch"],
            role_harm_ceiling="H3",
        )


def test_an_honestly_declared_mutation_still_meets_the_ceiling() -> None:
    """Declaring H1 honestly is legal — until the role's ceiling says otherwise."""
    verdict = gate(
        capability_ref="web.fetch",
        args={"url": "https://x.test/a", "method": "POST"},
        harm_declared="H1",
        role_tools=["web.fetch"],
        role_harm_ceiling="H1",
        role_egress=["x.test"],
    )
    assert verdict.harm_effective == "H1"
    with pytest.raises(ProfileRefusal, match="harm_ceiling"):
        gate(
            capability_ref="web.fetch",
            args={"url": "https://x.test/a", "method": "POST"},
            harm_declared="H1",
            role_tools=["web.fetch"],
            role_harm_ceiling="H0",
            role_egress=["x.test"],
        )


def test_gate_predicate_order_is_normative() -> None:
    """The ceiling (e) is checked BEFORE egress (f), so a ceiling breach reports as a ceiling breach.

    Order matters for the operator, not the outcome: both refuse, but only one of them tells you the
    actual problem. A gate that reports the second reason it found trains you to fix the wrong thing.
    """
    with pytest.raises(ProfileRefusal, match="harm_ceiling"):
        gate(
            capability_ref="web.fetch",
            args={"url": "https://nowhere.test/a", "method": "POST"},
            harm_declared="H1",
            role_tools=["web.fetch"],
            role_harm_ceiling="H0",
            role_egress=[],  # would ALSO fail egress; the ceiling must win because it is checked first
        )


def test_shape_harm_explains_itself(ex: ActExecutor) -> None:
    """Every derivation carries its reason — an unexplained refusal cannot be argued with."""
    harm, reasons = shape_harm({"url": "https://x.test/a?action=delete", "method": "POST", "body": "x"})
    assert harm == "H1"
    assert len(reasons) >= 3


def test_gate_refuses_a_capability_the_role_does_not_hold(ex: ActExecutor) -> None:
    ex.role_tools = ["fs.read"]
    assert ex.act("web.fetch", {"url": "https://example.test/ipv4-spec"}).reason == "not_in_role"


def test_gate_refuses_an_unknown_capability(ex: ActExecutor) -> None:
    assert ex.act("shell.exec", {"cmd": "rm -rf /"}).reason == "unknown_capability"


def test_egress_allowlist_binds(ex: ActExecutor) -> None:
    ex.role_egress = ["allowed.test"]
    assert ex.act("web.fetch", {"url": "https://evil.test/x"}).reason == "egress"


# ---------------------------------------------------------------- the trifecta step at the gate


def test_the_gate_refuses_when_the_act_would_complete_the_trifecta(ex: ActExecutor) -> None:
    """web.fetch carries untrusted_content + external_comms; standing access supplies the third."""
    ex.standing_access = ["operator-memory"]
    receipt = ex.act("web.fetch", {"url": "https://example.test/ipv4-spec"})
    assert receipt.exec == "refused" and receipt.reason == "trifecta"


def test_acquired_trifecta_is_a_fold_over_receipts_not_a_flag(ex: ActExecutor) -> None:
    """Ingress re-evaluation as a log query, zero monitors (act.md §6.1h)."""
    assert ex.acquired_trifecta() == Trifecta()
    ex.act("fs.read", {"path": "ipv4-spec.txt"})
    assert ex.acquired_trifecta().untrusted_content, "reading the world did not register as acquisition"


# ---------------------------------------------------------------- ACT-SCRUB-1


PLANTED = "sk-ant-api03-PLANTEDKEYPLANTEDKEYPLANTED"


def test_no_credential_bytes_reach_any_receipt_across_three_profiles(ex: ActExecutor) -> None:
    """Plant a key as a query, body and header carrier on all three profiles. Zero bytes survive."""
    ex.role_harm_ceiling = "H1"  # so the credential-shaped acts reach EXECUTE rather than the gate
    ex.act("web.fetch", {"url": f"https://example.test/ipv4-spec?api_key={PLANTED}"}, harm_declared="H1")
    hdrs = {"Authorization": f"Bearer {PLANTED}"}
    ex.act("web.fetch", {"url": "https://example.test/ipv4-spec", "headers": hdrs}, harm_declared="H1")
    ex.act("web.search", {"query": f"ipv4 {PLANTED}"}, harm_declared="H1")
    ex.act("fs.read", {"path": f"ipv4-spec.txt#{PLANTED}"}, harm_declared="H1")

    # Receipts are gold and so already durable, but say it anyway: "the credential is absent" is
    # also true of an empty file, and a scrub test that can pass by measuring nothing is not a test.
    ex.nucleus.ledger.flush()

    raw = ex.nucleus.ledger_path.read_text(encoding="utf-8")
    assert PLANTED not in raw, "a planted credential reached the ledger bytes"
    assert "[SCRUBBED]" in raw or "[REDACTED:" in raw, "nothing recorded that a scrub happened"
    for rec in ex.nucleus.records_of_kind("act_receipt"):
        assert PLANTED not in str(rec["body"])
        assert rec["body"]["scrubbed"] is True


def test_scrub_handles_query_body_and_header_carriers() -> None:
    assert PLANTED not in str(scrub({"url": f"https://x/?token={PLANTED}"}))
    assert PLANTED not in str(scrub({"body": f"secret={PLANTED}"}))
    assert PLANTED not in str(scrub({"headers": {"Authorization": f"Bearer {PLANTED}"}}))
    assert scrub({"headers": {"Cookie": "session=abc"}})["headers"]["Cookie"] == "[SCRUBBED]"


def test_scrub_leaves_ordinary_content_intact() -> None:
    """Over-scrubbing would quietly corrupt evidence, which is its own kind of fabrication."""
    text = "The RFC says four octets separated by dots."
    assert scrub(text) == text


# ---------------------------------------------------------------- GX-1(a): the channel works


def test_the_h0_channel_works_end_to_end(ex: ActExecutor) -> None:
    """GX-1(a): compose → gate → journal → execute → receipt, with content-addressed bytes."""
    receipt = ex.act("fs.read", {"path": "ipv4-spec.txt"})
    assert receipt.exec == "ok"
    assert receipt.sha256 and receipt.artifact_uri
    assert ex.store.verify(receipt.sha256)
    assert "four octets" in ex.store.get(receipt.sha256).read_text()  # type: ignore[union-attr]

    kinds = [r["kind"] for r in ex.nucleus.ledger.records()]
    assert kinds.index("action") < kinds.index("act_receipt"), "JOURNAL must precede the RECEIPT"


def test_journal_precedes_execute(ex: ActExecutor) -> None:
    """A crash between them must leave a record, not silence — silence is indistinguishable from never trying."""
    ex.act("web.fetch", {"url": "https://example.test/sqlite-wal"})
    action = ex.nucleus.records_of_kind("action")[0]
    assert action["body"]["verb"] == "act"
    assert action["seq"] < ex.nucleus.records_of_kind("act_receipt")[0]["seq"]


def test_a_failed_act_is_still_a_receipt(ex: ActExecutor) -> None:
    receipt = ex.act("web.fetch", {"url": "https://example.test/not-in-corpus"})
    assert receipt.exec == "failed" and receipt.reason == "adapter_error"
    assert ex.nucleus.records_of_kind("act_receipt")[0]["body"]["exec"] == "failed"


def test_fs_read_refuses_to_escape_its_root(ex: ActExecutor) -> None:
    """Resolve first, compare after — the only check that survives `..`, symlinks and absolutes."""
    assert ex.act("fs.read", {"path": "../../../etc/passwd"}).exec == "failed"


def test_h0_acts_ride_a_lease(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """ECON-S2b meets GROUND-0: grounding does not serialize on the fleet escrow."""
    monkeypatch.setenv("HYPERCELL_GROUNDED_CORPUS", str(CORPUS))
    escrow = Escrow(cap_usd=1.0, quantum_usd=0.01)
    ex = ActExecutor(Nucleus(tmp_path, "r1/g/0"), home=tmp_path, escrow=escrow, role_harm_ceiling="H0")
    for _ in range(5):
        ex.act("web.fetch", {"url": "https://example.test/rfc8785"})
    assert escrow.fleet_roundtrips == 5, "one lease grant per act; draws are free"


# ---------------------------------------------------------------- GROUND-1: fabrication classes


def test_forged_act_uri_is_caught_100_percent(ex: ActExecutor) -> None:
    """A citation to an act that never happened is the cleanest fabrication there is."""
    cites = [Citation(claim=f"c{i}", act_uri=f"act://FORGED{i:04d}") for i in range(10)]
    report = validate(cites, executor=ex)
    assert report.grounded == 0
    assert all(v == "forged_act" for _, v, _ in report.findings)
    assert report.stained and report.rho_next == 1.0


def test_quote_not_in_source_is_caught_10_of_10(ex: ActExecutor) -> None:
    receipt = ex.act("fs.read", {"path": "rfc8785.txt"})
    cites = [
        Citation(claim=f"c{i}", act_uri=receipt.uri, quote=f"the spec plainly states fabrication {i}")
        for i in range(10)
    ]
    report = validate(cites, executor=ex)
    assert report.grounded == 0
    assert all(v == "quote_absent" for _, v, _ in report.findings)


def test_digest_mismatch_is_caught(ex: ActExecutor) -> None:
    """Edit the stored bytes and the citation stops resolving — that is what content-addressing buys."""
    receipt = ex.act("fs.read", {"path": "sqlite-wal.txt"})
    art = ex.store.get(receipt.sha256 or "")
    assert art is not None
    art.path.write_text("rewritten after the fact", encoding="utf-8")

    report = validate([Citation("c", receipt.uri, quote="rewritten after the fact")], executor=ex)
    assert [v for _, v, _ in report.findings] == ["digest_mismatch"]
    assert report.stained


def test_a_true_citation_is_grounded(ex: ActExecutor) -> None:
    """The validator must also PASS honest work, or cells learn to stop citing."""
    receipt = ex.act("fs.read", {"path": "ipv4-spec.txt"})
    report = validate(
        [Citation("octets", receipt.uri, quote="four octets separated by dots")], executor=ex
    )
    assert report.ok and report.grounded == 1
    assert report.rho_next == 0.2


def test_refused_and_failed_acts_cannot_be_cited(ex: ActExecutor) -> None:
    """Only an exec-ok receipt is a warrant. A refusal is a record, not a source."""
    refused = ex.act("web.fetch", {"url": "https://example.test/x", "method": "POST"})
    report = validate([Citation("c", refused.uri)], executor=ex)
    assert [v for _, v, _ in report.findings] == ["forged_act"]


def test_citation_extraction_reads_quote_and_ref_only_forms() -> None:
    text = 'The RFC says "four octets separated by dots" [act://01ABC] and see also [act://01DEF].'
    cites = extract_citations(text)
    assert len(cites) == 2
    assert cites[0].quote == "four octets separated by dots"
    assert cites[1].quote == "" and cites[1].act_uri == "act://01DEF"


def test_whitespace_normalised_quotes_still_match(ex: ActExecutor) -> None:
    """A quote that survived a line-wrap is the same quote; refusing it trains cells to cite less."""
    receipt = ex.act("fs.read", {"path": "ipv4-spec.txt"})
    report = validate(
        [Citation("c", receipt.uri, quote="four   octets\n  separated by dots")], executor=ex
    )
    assert report.ok


# ---------------------------------------------------------------- the store


def test_identical_content_stores_once(tmp_path: Path) -> None:
    store = ArtifactStore(tmp_path)
    a = store.put("same bytes")
    b = store.put("same bytes")
    assert a.sha256 == b.sha256 and a.path == b.path


def test_the_annex_ships_exactly_the_three_h0_profiles() -> None:
    assert set(ANNEX_A) == {"web.search", "web.fetch", "fs.read"}
    assert all(p.harm_floor == "H0" for p in ANNEX_A.values())
