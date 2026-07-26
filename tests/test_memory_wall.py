"""NUC-4 — the register wall + evidence bundles (ARCHITECTURE §15; slice N2′).

The bar: **0 false accepts over 10 K generated invalid asserts** across eight classes
(decision · ask-outcome · narrative · self · future · 9-deep · submission-xref · raw-URL); the valid
set accepts; the exporter emits **0 narrative citations** over a fuzzed corpus; and terminal trust
tags are present on every bundle terminal.

The null this kills: prompt-level discipline — asking the model nicely not to invent provenance.
"""
from __future__ import annotations

import random
from pathlib import Path

import pytest

from hypercell.cell.bundle import BundleError, export_bundle, verify_bundle
from hypercell.cell.memory import MAX_DEPTH, Memory, RegisterError
from hypercell.cell.nucleus import Nucleus


@pytest.fixture
def mem(tmp_path: Path) -> Memory:
    return Memory(Nucleus(tmp_path, "r1/refiner/0"), pin_budget=2)


def _witnessed(m: Memory, source: str = "tool", trust: str | None = None) -> int:
    """A legal terminal: something the fabric actually witnessed."""
    body = {"source": source, "content": "observed bytes"}
    if trust:
        body["trust"] = trust
    return m.nucleus.append("percept", body)


def _act_outcome(m: Memory) -> int:
    """The other legal terminal: a receipt-backed world result."""
    return m.nucleus.append("outcome", {"verb": "act", "corr": "act://01HZZ", "text": "fetched"}, idem="x1")


# ---------------------------------------------------------------- the valid set MUST accept


def test_factual_on_a_witnessed_percept_accepts(mem: Memory) -> None:
    p = _witnessed(mem)
    seq = mem.remember("the file has 401 lines", register="factual", refs=[p])
    rec = mem.nucleus.record(seq)
    assert rec is not None and rec["body"]["register"] == "factual"
    assert rec["body"]["terminals"][0]["trust"] == "tool"


def test_factual_on_an_act_outcome_accepts(mem: Memory) -> None:
    a = _act_outcome(mem)
    seq = mem.remember("the endpoint returned 200", register="factual", refs=[a])
    assert mem.nucleus.record(seq)["body"]["terminals"][0]["kind"] == "act_receipt"  # type: ignore[index]


def test_factual_chains_through_factual_accepts(mem: Memory) -> None:
    """A fact may rest on a fact, so long as the bottom is witnessed."""
    p = _witnessed(mem)
    f1 = mem.remember("base fact", register="factual", refs=[p])
    f2 = mem.remember("derived fact", register="factual", refs=[f1])
    assert mem.nucleus.record(f2) is not None


def test_narrative_needs_no_refs(mem: Memory) -> None:
    """The default register is narrative on purpose: a sloppy cell mints style, never fake facts."""
    assert mem.remember("I feel this went well") > 0
    assert mem.nucleus.record(mem.nucleus.ledger.seq)["body"]["register"] == "narrative"  # type: ignore[index]


def test_act_xref_and_warrant_class_medium_xref_accept(mem: Memory) -> None:
    assert mem.remember("receipted", register="factual", xrefs=["act://01HZZ"]) > 0
    assert mem.remember("crossed", register="factual", xrefs=["medium://commons/42#verdict"]) > 0


def test_depth_exactly_8_accepts(mem: Memory) -> None:
    """The boundary is inclusive: <= 8 passes, 9 fails. Off-by-one here silently narrows the wall."""
    seq = _witnessed(mem)
    for _ in range(MAX_DEPTH - 1):
        seq = mem.remember("link", register="factual", refs=[seq])
    assert mem.nucleus.record(seq) is not None


# ---------------------------------------------------------------- the eight invalid classes


def test_class_decision_is_refused(mem: Memory) -> None:
    d = mem.nucleus.append("decision", {"chose": "b"})
    with pytest.raises(RegisterError) as e:
        mem.remember("because we decided", register="factual", refs=[d])
    assert e.value.code == "E_REG_DECISION_REF"


def test_class_ask_outcome_is_refused(mem: Memory) -> None:
    """Model text is not evidence — self-citation mints trust inside the fabric."""
    o = mem.nucleus.append("outcome", {"verb": "ask", "text": "the answer is 42"}, idem="a1")
    with pytest.raises(RegisterError) as e:
        mem.remember("the answer is 42", register="factual", refs=[o])
    assert e.value.code == "E_REG_DECISION_REF"


def test_class_narrative_ref_is_refused(mem: Memory) -> None:
    n = mem.remember("a vibe", register="narrative")
    with pytest.raises(RegisterError) as e:
        mem.remember("grounded in a vibe", register="factual", refs=[n])
    assert e.value.code == "E_REG_DECISION_REF"


def test_class_self_reference_is_refused(mem: Memory) -> None:
    with pytest.raises(RegisterError) as e:
        mem.remember("I cite myself", register="factual", refs=[mem.nucleus.ledger.seq + 1])
    assert e.value.code == "E_REG_BAD_REF"


def test_class_future_reference_is_refused(mem: Memory) -> None:
    with pytest.raises(RegisterError) as e:
        mem.remember("I cite tomorrow", register="factual", refs=[9999])
    assert e.value.code == "E_REG_BAD_REF"


def test_class_nine_deep_is_refused(mem: Memory) -> None:
    seq = _witnessed(mem)
    for _ in range(MAX_DEPTH - 1):
        seq = mem.remember("link", register="factual", refs=[seq])
    # one hop past the ceiling
    deep = mem.remember("link", register="factual", refs=[seq])
    with pytest.raises(RegisterError) as e:
        mem.remember("too far", register="factual", refs=[deep])
    assert e.value.code == "E_REG_TOO_DEEP"


def test_class_submission_xref_is_refused(mem: Memory) -> None:
    """Another model's assertion is never grounding, however well-formed the URI."""
    with pytest.raises(RegisterError) as e:
        mem.remember("peer said so", register="factual", xrefs=["medium://commons/42#submission"])
    assert e.value.code == "E_REG_DECISION_REF"
    assert "warrant-class" in str(e.value)


def test_class_raw_url_is_refused(mem: Memory) -> None:
    with pytest.raises(RegisterError) as e:
        mem.remember("the web says", register="factual", xrefs=["https://example.com/page"])
    assert e.value.code == "E_REG_DECISION_REF"
    assert "act://" in str(e.value)


def test_no_refs_at_all_is_refused(mem: Memory) -> None:
    with pytest.raises(RegisterError) as e:
        mem.remember("trust me", register="factual")
    assert e.value.code == "E_REG_NO_REFS"


# ---------------------------------------------------------------- the fuzz suite: 10 K, zero accepts


def test_ten_thousand_invalid_asserts_zero_false_accepts(mem: Memory) -> None:
    """The bar, at volume. Every generated invalid assert MUST be refused with a typed error."""
    rng = random.Random(20260725)

    good_percept = _witnessed(mem)
    legal_chain = mem.remember("base", register="factual", refs=[good_percept])
    decision = mem.nucleus.append("decision", {"chose": "x"})
    ask_out = mem.nucleus.append("outcome", {"verb": "ask", "text": "model text"}, idem="fz")
    produce_out = mem.nucleus.append("outcome", {"verb": "produce", "text": "candidate"}, idem="fz2")
    narrative = mem.remember("style", register="narrative")
    checkpoint = mem.nucleus.append("checkpoint", {"state": "mid"})

    deep = _witnessed(mem)
    for _ in range(MAX_DEPTH):
        deep = mem.remember("link", register="factual", refs=[deep])

    def generate() -> tuple[list[int], list[str]]:
        cls = rng.randrange(8)
        if cls == 0:
            return [decision], []
        if cls == 1:
            return [rng.choice([ask_out, produce_out])], []
        if cls == 2:
            return [narrative], []
        if cls == 3:  # self / not-yet-written
            return [mem.nucleus.ledger.seq + rng.randrange(1, 5)], []
        if cls == 4:  # future
            return [rng.randrange(50_000, 90_000)], []
        if cls == 5:  # 9-deep
            return [deep], []
        if cls == 6:
            kind = rng.choice(["submission", "chat", "status", "task", "announce"])
            return [], [f"medium://commons/{rng.randrange(1, 999)}#{kind}"]
        scheme = rng.choice(["https", "http"])
        return [], [f"{scheme}://example.com/{rng.randrange(1, 999)}"]

    accepted: list[tuple[list[int], list[str]]] = []
    codes: dict[str, int] = {}
    extra = [checkpoint, legal_chain]  # a legal ref mixed in must NOT rescue an illegal one

    for i in range(10_000):
        refs, xrefs = generate()
        if i % 3 == 0 and refs:
            refs = [*refs, extra[i % 2]]
        try:
            mem.remember(f"invalid #{i}", register="factual", refs=refs, xrefs=xrefs)
            accepted.append((refs, xrefs))
        except RegisterError as err:
            codes[err.code] = codes.get(err.code, 0) + 1

    assert not accepted, f"FALSE ACCEPTS ({len(accepted)}): {accepted[:5]}"
    assert sum(codes.values()) == 10_000
    assert set(codes) >= {"E_REG_DECISION_REF", "E_REG_BAD_REF", "E_REG_TOO_DEEP"}, codes


def test_a_refusal_writes_nothing(mem: Memory) -> None:
    """Rejection is not a silent downgrade — and it is not a half-written record either."""
    before = mem.nucleus.ledger.seq
    with pytest.raises(RegisterError):
        mem.remember("nope", register="factual", refs=[])
    assert mem.nucleus.ledger.seq == before
    assert mem.nucleus.verify().ok


# ---------------------------------------------------------------- the other four verbs


def test_revise_keeps_the_past_queryable(mem: Memory) -> None:
    p = _witnessed(mem)
    f = mem.remember("401 lines", register="factual", refs=[p])
    mem.revise(f, "402 lines")
    hits = {h.seq: h for h in mem.recall()}
    assert hits[f].superseded_by is not None, "the old version stays, marked"


def test_forget_tombstones_the_render_but_the_ledger_retains(mem: Memory) -> None:
    n = mem.remember("regrettable")
    mem.forget(n, reason="operator asked")
    assert all(h.seq != n for h in mem.recall())
    assert mem.nucleus.record(n) is not None, "true erasure is the firewall's job, not forget()'s"


def test_pin_budget_refuses_over_cap(mem: Memory) -> None:
    a, b, c = mem.remember("a"), mem.remember("b"), mem.remember("c")
    mem.pin(a)
    mem.pin(b)
    with pytest.raises(RegisterError) as e:
        mem.pin(c)
    assert e.value.code == "E_PIN_BUDGET"
    mem.pin(a, on=False)
    assert mem.pin(c) > 0, "unpinning frees the budget"


def test_recall_is_journaled(mem: Memory) -> None:
    """A read that leaves no trace cannot be audited."""
    mem.remember("something")
    before = mem.nucleus.ledger.seq
    mem.recall("something")
    assert mem.nucleus.ledger.seq == before + 1
    assert mem.nucleus.record(mem.nucleus.ledger.seq)["kind"] == "memory.recall"  # type: ignore[index]


# ---------------------------------------------------------------- the bundle


def test_bundle_carries_trust_tags_on_every_terminal(mem: Memory) -> None:
    p = _witnessed(mem, source="medium", trust="external")
    f = mem.remember("the page said X", register="factual", refs=[p])
    hits = [h for h in mem.recall() if h.seq == f]
    b = export_bundle(mem, hits)
    assert b.cited[0]["terminal_refs"][0]["trust"] == "external", (
        "a fact grounded only in external content must be VISIBLY so"
    )
    assert b.ledger_head["hash"] == mem.nucleus.head_hash
    assert b.sha256.startswith("sha256:")


def test_exporter_refuses_narrative(mem: Memory) -> None:
    mem.remember("just a feeling")
    hits = mem.recall()
    with pytest.raises(BundleError, match="narrative"):
        export_bundle(mem, hits)


def test_exporter_emits_zero_narrative_over_a_fuzzed_corpus(mem: Memory) -> None:
    """The bar's second half: not one narrative citation escapes to the wire."""
    rng = random.Random(7)
    p = _witnessed(mem)
    for i in range(200):
        if rng.random() < 0.5:
            mem.remember(f"fact {i}", register="factual", refs=[p])
        else:
            mem.remember(f"story {i}", register="narrative")

    all_hits = mem.recall(k=0)
    with pytest.raises(BundleError):
        export_bundle(mem, all_hits)  # the mixed corpus must be refused wholesale

    factual_only = [h for h in all_hits if h.register == "factual"]
    bundle = export_bundle(mem, factual_only)
    assert len(bundle.cited) == len(factual_only)
    assert all(c["register"] == "factual" for c in bundle.cited)


def test_bundle_verifies_against_the_ledger_and_catches_fabrication(mem: Memory) -> None:
    p = _witnessed(mem)
    f = mem.remember("real claim", register="factual", refs=[p])
    bundle = export_bundle(mem, [h for h in mem.recall() if h.seq == f])
    ok, why = verify_bundle(mem, bundle)
    assert ok, why

    forged = type(bundle)(
        claim=bundle.claim,
        ledger_head=bundle.ledger_head,
        cited=[{**bundle.cited[0], "content": "a claim I never filed"}],
    )
    ok, why = verify_bundle(mem, forged)
    assert not ok and "fabricated warrant" in why


# ---------------------------------------------------------------- L-REDACT-BEFORE-CANON


def test_a_secret_never_reaches_the_ledger(mem: Memory) -> None:
    """An append-only log cannot un-say a secret, so it must never learn one.

    The chain is computed over post-redaction bytes: `verify()` must never require a secret to
    re-derive a log.
    """
    key = "sk-ant-api03-ZZZZZZZZZZZZZZZZZZZZZZZZZZZZ"
    mem.nucleus.append("percept", {"source": "tool", "content": f"export ANTHROPIC_API_KEY={key}"})

    # Standard appends ride the group-commit, so the bytes are not on disk until they drain. Flush
    # before reading them: "the key is absent" is also true of an EMPTY file, so without this the
    # test could pass by measuring nothing.
    mem.nucleus.ledger.flush()

    raw = mem.nucleus.ledger_path.read_text(encoding="utf-8")
    assert key not in raw, "the raw key reached the ledger bytes"
    assert "[REDACTED:" in raw
    assert mem.nucleus.verify().ok, "the chain must verify over post-redaction bytes"


def test_redaction_is_itself_recorded(mem: Memory) -> None:
    """An auditor must see that something was removed, without it being recoverable."""
    seq = mem.nucleus.append("percept", {"source": "tool", "content": "Bearer abcdefghijklmnopqrstuvwxyz012345"})
    rec = mem.nucleus.record(seq)
    assert rec is not None and "bearer" in rec["body"]["red"]


def test_ordinary_content_is_untouched(mem: Memory) -> None:
    """Over-redaction would quietly corrupt the record. Conservative, not indiscriminate."""
    text = "the function returns 401 lines and a sketch of sk- prefixes in prose"
    seq = mem.nucleus.append("percept", {"source": "tool", "content": text})
    assert mem.nucleus.record(seq)["body"]["content"] == text  # type: ignore[index]
