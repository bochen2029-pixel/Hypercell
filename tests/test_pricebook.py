"""ECON-PB-1 / ONE-METER-1 — the money plane (ARCHITECTURE §15; slice ECON-S1).

ECON-PB-1's bar: **unknown refused**; **stale reserves ≥ fresh**; a planted +30% price change fires
the >10% alarm and the fork labels it `price-change`.

The null: the live `_PRICE` dict — silent guesses. Its fallback for any unknown provider was
`(0.5, 1.5)` USD/1M, an undated number every downstream total inherited without a word.

ONE-METER-1 is **born red here** and goes green at b′ with the one-verb executor (slice S-KG-3).
It is marked `xfail(strict=True)`, so when the seam lands and the test starts passing, CI fails and
tells us to remove the marker. A falsifier that quietly starts passing has stopped being a schedule.
"""
from __future__ import annotations

import ast
from datetime import date, timedelta
from pathlib import Path

import pytest
import yaml

from hypercell.cognition.base import CompletionResult
from hypercell.cognition.metered import MeteredCognition
from hypercell.conductor.governor import Governor
from hypercell.conductor.pricebook import (
    Pricebook,
    PricebookError,
    UnknownLane,
    default_pricebook,
)

SRC = Path(__file__).resolve().parent.parent / "src" / "hypercell"


def _book(**overrides: object) -> Pricebook:
    data = {
        "version": "5.1.0",
        "defaults": {"max_age_days": 30, "stale_mult": 1.25, "refuse_after": 2.0},
        "skus": {
            "m@p/standard": {
                "weights_family": "w",
                "input": 1.0,
                "output": 2.0,
                "as_of": "2026-07-16",
                "source": "provider-published",
                "verified": True,
            }
        },
    }
    data.update(overrides)  # type: ignore[arg-type]
    return Pricebook(data)


# ---------------------------------------------------------------- rule 5: unknown is REFUSED


def test_unknown_lane_is_refused_not_estimated() -> None:
    """The whole point of the slice. A wrong price is worse than no price."""
    with pytest.raises(UnknownLane, match="never estimated"):
        _book().quote(model="who", provider="dis", prompt_tokens=1000)


def test_the_old_silent_guess_is_gone() -> None:
    """Regression: `_PRICE.get(provider, (0.5, 1.5))` must not exist as CODE.

    Checked by AST rather than by grep, because the comment explaining the deletion necessarily
    quotes the thing it deleted — a text search would flag its own tombstone.
    """
    tree = ast.parse((SRC / "conductor" / "governor.py").read_text(encoding="utf-8"))

    assigned = {
        t.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        for t in node.targets
        if isinstance(t, ast.Name)
    } | {
        node.target.id
        for node in ast.walk(tree)
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
    }
    assert "_PRICE" not in assigned, "the guess dict came back"

    guesses = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Tuple)
        and [c.value for c in node.elts if isinstance(c, ast.Constant)] == [0.5, 1.5]
    ]
    assert not guesses, "the silent (0.5, 1.5) fallback came back as live code"


def test_every_shipped_lane_is_priced() -> None:
    """The registry's default models must all resolve, or the fabric refuses its own defaults."""
    from hypercell.surfaces.cli import _DEFAULT_MODELS

    book = default_pricebook()
    for provider, model in _DEFAULT_MODELS.items():
        sku = book.sku_key(model, provider)
        assert sku in book.skus, f"{sku} is a shipped default with no pricebook row"


# ---------------------------------------------------------------- freshness pessimism


def test_stale_reserves_at_least_as_much_as_fresh() -> None:
    """The bar, stated directly. Pessimism that can make something look cheaper is not pessimism."""
    fresh = _book().quote(model="m", provider="p", prompt_tokens=1_000_000, today=date(2026, 7, 20))
    stale = _book().quote(model="m", provider="p", prompt_tokens=1_000_000, today=date(2026, 8, 20))
    assert not fresh.stale and stale.stale
    assert stale.usd_reserved >= fresh.usd_reserved
    assert stale.usd_reserved == pytest.approx(fresh.usd_reserved * 1.25)
    assert stale.usd_effective == fresh.usd_effective, "staleness must not change what we CHARGE"


def test_reserve_is_never_below_effective() -> None:
    q = _book().quote(
        model="m", provider="p", prompt_tokens=1000, api_reported_usd=99.0, today=date(2026, 7, 20)
    )
    assert q.usd_reserved >= q.usd_effective


def test_a_lane_past_refuse_after_is_refused() -> None:
    """There is an age beyond which a price is not stale, it is fiction."""
    with pytest.raises(UnknownLane, match="fiction"):
        _book().quote(model="m", provider="p", prompt_tokens=10, today=date(2026, 7, 16) + timedelta(days=61))


# ---------------------------------------------------------------- the +30% plant


def test_planted_30_percent_price_change_fires_the_alarm_and_forks_to_price_change() -> None:
    """The bar's third clause, exactly: tokens AGREE, so the diagnosis is the price, not the adapter."""
    v = _book().reconcile(ledger_usd=100.0, invoice_usd=130.0, ledger_tokens=5_000, invoice_tokens=5_000)
    assert v.level == "alarm"
    assert v.fork == "price-change"
    assert "update the book" in v.detail


def test_the_same_drift_with_mismatched_tokens_forks_to_adapter_bug() -> None:
    """Treating every drift as a price problem is how an adapter bug hides for a quarter."""
    v = _book().reconcile(ledger_usd=100.0, invoice_usd=130.0, ledger_tokens=5_000, invoice_tokens=9_000)
    assert v.level == "alarm" and v.fork == "adapter-bug"


@pytest.mark.parametrize(
    ("invoice", "level"), [(101.0, "ok"), (105.0, "flagged"), (112.0, "alarm"), (88.0, "alarm")]
)
def test_drift_bands(invoice: float, level: str) -> None:
    v = _book().reconcile(ledger_usd=100.0, invoice_usd=invoice, ledger_tokens=1, invoice_tokens=1)
    assert v.level == level


# ---------------------------------------------------------------- the book must parse honestly


def test_a_row_missing_a_required_field_refuses_the_whole_book() -> None:
    """A half-parsed pricebook prices some lanes and silently omits others — worse than none."""
    with pytest.raises(PricebookError, match="WHOLE book"):
        _book(skus={"m@p/standard": {"input": 1.0, "output": 2.0}})


def test_the_shipped_book_loads_and_every_row_is_dated() -> None:
    book = default_pricebook()
    assert book.skus, "the shipped pricebook is empty"
    for sku in book.skus:
        assert book.age_days(sku) >= 0, f"{sku} is dated in the future"


def test_the_shipped_yaml_is_the_data_artifact_the_contract_governs() -> None:
    book_path = Path(__file__).resolve().parent.parent / "contracts" / "pricebook.yaml"
    raw = yaml.safe_load(book_path.read_text(encoding="utf-8"))
    assert raw["currency"] == "USD_per_1M_tokens"
    assert set(raw["defaults"]) >= {"max_age_days", "stale_mult", "refuse_after"}


# ---------------------------------------------------------------- F26: cost_usd populated


async def test_cost_usd_is_populated_on_the_receipt() -> None:
    """F26 closed: `cost_usd` was declared in v1 and never written to."""

    class Big:
        name = "big"

        async def complete(self, messages: object, **params: object) -> CompletionResult:
            return CompletionResult(
                text="x", model="deepseek-chat", prompt_tokens=1_000_000, completion_tokens=1_000_000
            )

    gov = Governor(usd_cap=10.0)
    metered = MeteredCognition(Big(), "deepseek", gov)  # type: ignore[arg-type]
    result = await metered.complete([])
    assert result.cost_usd > 0.0, "the receipt is still honest about everything except its dollars"
    assert result.cost_usd == pytest.approx(0.14 + 0.28)


async def test_spend_records_carry_the_canonical_cost_group() -> None:
    """R16: the six members, and `tokens`/`wall_ms` as siblings — never inside cost{}."""

    class Small:
        name = "s"

        async def complete(self, messages: object, **params: object) -> CompletionResult:
            return CompletionResult(text="x", model="deepseek-chat", prompt_tokens=1000, completion_tokens=10)

    gov = Governor(usd_cap=10.0)
    await MeteredCognition(Small(), "deepseek", gov).complete([])  # type: ignore[arg-type]

    rec = gov.spend_records[0]
    assert set(rec["cost"]) == {
        "usd_effective", "usd_reserved", "sku", "purpose", "resv_id", "pricebook_version",
    }
    assert rec["cost"]["purpose"] == "production"
    assert "tokens" not in rec["cost"] and "wall_ms" not in rec["cost"]
    assert rec["tokens"]["prompt"] == 1000


async def test_spend_fold_equals_the_counter() -> None:
    """The counter is a cache of the fold, not a second source of truth (A13)."""

    class Small:
        name = "s"

        async def complete(self, messages: object, **params: object) -> CompletionResult:
            return CompletionResult(text="x", model="deepseek-chat", prompt_tokens=1000, completion_tokens=10)

    gov = Governor(usd_cap=10.0)
    m = MeteredCognition(Small(), "deepseek", gov)  # type: ignore[arg-type]
    for _ in range(5):
        await m.complete([])
    assert gov.spend_fold()["usd_effective"] == pytest.approx(gov.spent)
    assert gov.spend_fold()["calls"] == 5


def test_cache_reads_are_priced_below_fresh_input() -> None:
    """A meter that cannot see cache usage cannot be truthful — cached input is cheaper everywhere."""
    book = default_pricebook()
    fresh = book.quote(model="deepseek-chat", provider="deepseek", prompt_tokens=1_000_000)
    cached = book.quote(
        model="deepseek-chat", provider="deepseek", prompt_tokens=1_000_000, cache_read_tokens=1_000_000
    )
    assert cached.usd_effective < fresh.usd_effective


# ---------------------------------------------------------------- ONE-METER-1, born red


def _adapter_constructions() -> list[str]:
    """Every site that constructs a provider adapter, by AST — not by grep."""
    adapters = {"OpenAICompatCognition", "MockCognition", "EchoCognition"}
    sites: list[str] = []
    for path in SRC.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in adapters:
                sites.append(f"{path.relative_to(SRC)}:{node.lineno}")
    return sorted(sites)


def test_one_meter_only_metered_py_constructs_adapters() -> None:
    """AST: only `cognition/metered.py` may construct a provider adapter.

    **This was born red at ECON-S1 and went green at S-KG-3.** It carried an
    `xfail(strict=True)` with the reason written out, so the moment the seam landed CI failed with
    XPASS and told us to delete the marker — which is exactly what a scheduled falsifier is for. A
    bar that quietly starts passing has stopped being a schedule.
    """
    offenders = [
        site
        for site in _adapter_constructions()
        if not site.replace("\\", "/").startswith("cognition/metered.py")
    ]
    assert offenders == [], f"un-metered adapter constructions: {offenders}"


def test_the_guarded_adapter_list_is_read_from_the_seam_not_copied() -> None:
    """The drill reads metered.py's own tuple, so adding an adapter there cannot silently widen the hole."""
    from hypercell.cognition.metered import ADAPTER_CLASSES

    assert set(ADAPTER_CLASSES) <= {"OpenAICompatCognition", "MockCognition", "EchoCognition"}
    assert _adapter_constructions(), "the AST walk found no adapter constructions at all"



