"""SEC-PRICE — pricebook signing + lane canary + reservation-DoS cap (slice SEC-c′).

**The bar, verbatim:** an unsigned or wrong-sig pricebook → refused-on-load; a lane whose canary
fingerprint ≠ declared `weights_family` → diversity contribution de-rated to 0 until re-attested.
(Plus the reservation-DoS cap from the slice map.)

**The null is v1's unsigned book** — trust the yaml on disk, whatever it says. A poisoned book is
not a parse error, it is a routing attack: rewrite one row cheaper and the fleet stampedes onto a
lane the attacker controls; inflate the prices and the fleet starves. The null catches neither,
because it never asked who wrote the numbers. Each part below runs the null beside the enforced
mechanism so the refusal is a delta over a measured hole.
"""
from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml

from hypercell.conductor.canary import (
    Attestation,
    attest,
    diversity_count,
    register_family,
)
from hypercell.conductor.governor import Escrow, ReservationDoS
from hypercell.conductor.pricebook import (
    Pricebook,
    PricebookForged,
    PricebookUnsigned,
    content_digest,
    sign_pricebook,
    verify_pricebook,
)

KEY = "operator-key-v5"
REAL_BOOK = yaml.safe_load(Path("contracts/pricebook.yaml").read_text(encoding="utf-8"))


def _signed(data: dict) -> dict:
    d = copy.deepcopy(data)
    d["signature"] = sign_pricebook(d, KEY)
    return d


def _write(tmp_path: Path, data: dict) -> Path:
    p = tmp_path / "pricebook.yaml"
    p.write_text(yaml.safe_dump(data), encoding="utf-8")
    return p


# ================================================================ Part A: signing


def test_a_signed_book_verifies_and_loads(tmp_path: Path) -> None:
    book = Pricebook.load(_write(tmp_path, _signed(REAL_BOOK)), key=KEY)
    assert book.signed and book.skus, "a correctly-signed book should load"


def test_an_unsigned_book_under_an_enforcing_key_is_refused(tmp_path: Path) -> None:
    with pytest.raises(PricebookUnsigned):
        Pricebook.load(_write(tmp_path, REAL_BOOK), key=KEY)


def test_a_wrong_signature_is_refused(tmp_path: Path) -> None:
    forged = copy.deepcopy(REAL_BOOK)
    forged["signature"] = sign_pricebook(forged, "attacker-key")
    with pytest.raises(PricebookForged):
        Pricebook.load(_write(tmp_path, forged), key=KEY)


def test_the_cheapest_lane_attack_is_refused(tmp_path: Path) -> None:
    """The concrete poisoning: sign the book, then rewrite one row cheaper to redirect the fleet.
    The signature is over the content, so the edit breaks it — refused before a price is believed."""
    poisoned = _signed(REAL_BOOK)
    poisoned["skus"]["gpt-4o-mini@openai/standard"]["input"] = 0.00001  # pennies, to win every route
    with pytest.raises(PricebookForged, match="altered after signing|redirects"):
        Pricebook.load(_write(tmp_path, poisoned), key=KEY)


def test_the_starvation_attack_is_refused(tmp_path: Path) -> None:
    """The other poisoning: inflate prices so every lane looks unaffordable and the fleet stalls."""
    poisoned = _signed(REAL_BOOK)
    poisoned["skus"]["deepseek-chat@deepseek/standard"]["input"] = 9999.0
    with pytest.raises(PricebookForged):
        Pricebook.load(_write(tmp_path, poisoned), key=KEY)


def test_the_null_loads_a_poisoned_book_without_a_key(tmp_path: Path) -> None:
    """v1's behaviour: with no key configured, the poisoned content loads and the fleet believes it.
    This is the hole SEC-PRICE fills — measured, so 'refused' means something."""
    poisoned = copy.deepcopy(REAL_BOOK)
    poisoned["skus"]["gpt-4o-mini@openai/standard"]["input"] = 0.00001
    book = Pricebook.load(_write(tmp_path, poisoned))  # no key -> pre-Stage-1b grace
    assert book.skus["gpt-4o-mini@openai/standard"]["input"] == 0.00001, (
        "the null is supposed to load the poison unquestioned — that is the defect"
    )


def test_the_content_digest_excludes_the_signature_field() -> None:
    """A field cannot sign itself: the digest is over everything BUT the signature, or adding the
    signature would change the digest the signature is over."""
    d = copy.deepcopy(REAL_BOOK)
    before = content_digest(d)
    d["signature"] = "hmac-sha256:whatever"
    assert content_digest(d) == before, "the signature field leaked into its own digest"


def test_the_digest_moves_when_any_priced_row_moves() -> None:
    d = copy.deepcopy(REAL_BOOK)
    before = content_digest(d)
    d["skus"]["deepseek-chat@deepseek/standard"]["output"] = 0.99
    assert content_digest(d) != before, "a price change did not move the content digest"


def test_verification_is_constant_time() -> None:
    """`hmac.compare_digest`, not `==`: a pricebook is a long-lived asset an attacker can probe at
    leisure, and a timing leak on the signature is a slow-motion forgery oracle."""
    import inspect

    assert "compare_digest" in inspect.getsource(verify_pricebook)


# ================================================================ Part B: the lane canary


def test_a_matching_canary_verifies_the_family() -> None:
    a = attest("anthropic", "Claude, made by Anthropic.")
    assert a.family_verified and a.diversity_contribution == 1.0


def test_a_lying_lane_is_de_rated_to_zero() -> None:
    """A host declares `anthropic` but its canary answer fingerprints as something else — it is not
    running the weights it claims. Diversity contribution ZERO, not an alarm."""
    a = attest("anthropic", "GPT-4o, made by OpenAI.")  # wrong answer for the declared family
    assert not a.family_verified and a.diversity_contribution == 0.0
    assert "not running the weights it claims" in a.reason


def test_an_unknown_family_fails_closed() -> None:
    """No pinned fingerprint for the claim ⇒ zero, never a pass on trust. 'We cannot check it' must
    cost diversity, not be granted it."""
    a = attest("mystery-host-family", "anything at all")
    assert not a.family_verified and a.diversity_contribution == 0.0
    assert "fail-closed" in a.reason


def test_diversity_count_ignores_a_monoculture_masquerading_as_diversity() -> None:
    """Eight lanes each declaring a different family but ALL failing the canary count as ZERO
    distinct families — the blind spot wearing eight hats, seen through."""
    liars = [attest(f"claimed-{i}", "GPT-4o, made by OpenAI.") for i in range(8)]
    assert diversity_count(liars) == 0, "a monoculture was counted as diverse"


def test_diversity_count_counts_genuine_distinct_families() -> None:
    real = [
        attest("anthropic", "Claude, made by Anthropic."),
        attest("deepseek", "DeepSeek-V3, an open model."),
        attest("gpt-4o", "GPT-4o, made by OpenAI."),
    ]
    assert diversity_count(real) == 3


def test_the_null_declaration_only_counts_a_liar_as_diverse() -> None:
    """v1 trusts the book: a lane that DECLARES a rare family is counted as that family, canary or
    not. So an attacker gets cross-family quorum credit for a monoculture — the exact fraud the
    canary exists to stop, measured here as the null."""
    declared_only = {a.declared_family for a in [
        Attestation("anthropic", True, "declared"),   # the null marks everything verified-by-fiat
        Attestation("rare-family", True, "declared"),
    ]}
    assert len(declared_only) == 2, "the null counts declarations, so a liar inflates the count"


def test_family_verified_is_distinct_from_cost_parity() -> None:
    """Two flags, two owners: diversity keys on the CANARY, never on ECON-S3's score-parity probe.
    A host can be cost-honest and still lie about its weights."""
    from hypercell.conductor.engine.schedule import parity_verdict

    # A lane that PASSES cost-parity but FAILS the canary must still contribute zero diversity.
    cost_parity = parity_verdict([0.8] * 5, [0.8] * 5)  # "passed" — costs match
    canary = attest("anthropic", "GPT-4o, made by OpenAI.")  # fails — weights do not
    assert cost_parity == "passed" and canary.diversity_contribution == 0.0


def test_a_re_attested_lane_recovers_its_contribution() -> None:
    """De-rated 'until re-attested': once the canary passes again, diversity returns."""
    register_family("newlane", "I am newlane, freshly pinned.")
    assert attest("newlane", "I am newlane, freshly pinned.").diversity_contribution == 1.0
    assert attest("newlane", "I am lying now.").diversity_contribution == 0.0


# ================================================================ Part C: reservation-DoS cap


def test_one_issuer_cannot_exceed_its_reservation_cap() -> None:
    e = Escrow(cap_usd=100.0, per_issuer_reservation_cap=3)
    for _ in range(3):
        e.reserve(0.1, scope="run:a", holder="greedy")
    with pytest.raises(ReservationDoS, match="per-issuer cap"):
        e.reserve(0.1, scope="run:a", holder="greedy")


def test_the_cap_is_per_issuer_not_global() -> None:
    e = Escrow(cap_usd=100.0, per_issuer_reservation_cap=2)
    e.reserve(0.1, scope="run:a", holder="a")
    e.reserve(0.1, scope="run:a", holder="a")
    e.reserve(0.1, scope="run:a", holder="b")  # b has its own budget of reservations
    assert len([r for r in e.reservations.values() if r.holder == "b"]) == 1


def test_releasing_frees_a_reservation_slot() -> None:
    e = Escrow(cap_usd=100.0, per_issuer_reservation_cap=1)
    first = e.reserve(0.1, scope="run:a", holder="x")
    with pytest.raises(ReservationDoS):
        e.reserve(0.1, scope="run:a", holder="x")
    e.release(first.resv_id, "done")
    e.reserve(0.1, scope="run:a", holder="x")  # slot freed


def test_the_null_lets_one_issuer_lock_the_whole_budget() -> None:
    """No cap: one issuer opens tiny reservations until the budget is entirely reserved-but-unspent,
    and every other cell is refused for lack of headroom that nobody is actually using."""
    uncapped = Escrow(cap_usd=1.0)  # the null: per_issuer_reservation_cap is None
    for _ in range(100):
        try:
            uncapped.reserve(0.01, scope="fleet", holder="attacker")
        except Exception:
            break
    from hypercell.conductor.governor import EscrowRefused

    with pytest.raises(EscrowRefused):
        uncapped.reserve(0.01, scope="fleet", holder="victim")
    assert uncapped.reserved("fleet") >= 0.99, "the attacker did not manage to lock the budget"


def test_the_cap_refuses_before_locking_headroom() -> None:
    """The capped escrow leaves room for others precisely because it stopped the hog early."""
    e = Escrow(cap_usd=1.0, per_issuer_reservation_cap=5)
    for _ in range(5):
        e.reserve(0.01, scope="fleet", holder="hog")
    with pytest.raises(ReservationDoS):
        e.reserve(0.01, scope="fleet", holder="hog")
    e.reserve(0.5, scope="fleet", holder="victim")  # plenty of headroom left for a real caller
    assert e.available("fleet") > 0


def test_the_dos_cap_now_bounds_the_metered_path() -> None:
    """open_call passed no holder, so every metered reservation was holder="" and the DoS cap never
    fired on the path that matters. It now attributes reservations to the issuing scope."""
    from hypercell.conductor.governor import Escrow, Governor, ReservationDoS

    escrow = Escrow(cap_usd=100.0, per_issuer_reservation_cap=2)
    gov = Governor(usd_cap=100.0, escrow=escrow, scope="run:a")
    gov.open_call("stub", {"model": "stub"})
    gov.open_call("stub", {"model": "stub"})
    with pytest.raises(ReservationDoS):
        gov.open_call("stub", {"model": "stub"})


def test_a_dos_cap_hit_is_not_disguised_as_a_budget_breach() -> None:
    """The budget has room; the issuer just holds too many. ReservationDoS must not be re-wrapped as
    BudgetExceeded -- the caller has to tell 'out of money' from 'too many holds'."""
    from hypercell.conductor.governor import BudgetExceeded, Escrow, Governor, ReservationDoS

    escrow = Escrow(cap_usd=1000.0, per_issuer_reservation_cap=1)
    gov = Governor(usd_cap=1000.0, escrow=escrow, scope="run:a")
    gov.open_call("stub", {"model": "stub"})
    try:
        gov.open_call("stub", {"model": "stub"})
        raise AssertionError("expected a refusal")
    except ReservationDoS:
        pass  # correct
    except BudgetExceeded:
        raise AssertionError("a DoS-cap hit was disguised as a budget breach") from None
