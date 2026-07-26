"""The pricebook — dated prices, freshness pessimism, and no silent guesses (contracts/pricebook.md).

**The null this replaces** is the live `_PRICE` dict, whose fallback for an unknown provider was
`(0.5, 1.5)` USD/1M — a guess that never announced itself. Every total downstream inherited it, and
nothing in the receipt said so. The fabric was honest about everything except its dollars.

Three rules do the work:

* **Unknown lanes are REFUSED, never estimated.** If the book does not price it, the answer is a
  typed refusal, not a number. A wrong price is worse than no price: a refusal stops the run and
  gets fixed, while a plausible number is believed and compounds.
* **Freshness pessimism, upward only.** A row past `max_age_days` is stale: still usable, but its
  *reserve* is multiplied by `stale_mult`. Stale reserves are therefore always ≥ fresh reserves. The
  multiplier never applies downward — pessimism that can make something look cheaper is not
  pessimism.
* **Past `refuse_after × max_age_days` the lane is refused outright.** There is an age beyond which
  a price is not stale, it is fiction.

`usd_effective` is what actually happened; `usd_reserved` is what the escrow held. They are separate
members of the canonical `cost{}` group for a reason — reserving the pessimistic number and charging
the real one is how a budget stays honest without over-charging the operator.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Literal

import yaml

REPO_PRICEBOOK = Path(__file__).resolve().parents[3] / "contracts" / "pricebook.yaml"

#: Required on every SKU row. A row missing any of these does not parse, and a file with such a row
#: is refused WHOLE — a half-parsed pricebook is worse than none, because it prices some lanes and
#: silently omits others.
REQUIRED_FIELDS = ("input", "output", "as_of", "source", "verified", "weights_family")

Purpose = Literal["production", "verification", "oracle_growth", "tool", "maintenance"]


class PricebookError(Exception):
    """The book itself is unusable."""


class UnknownLane(Exception):
    """Rule 5: the book does not price this lane, so the fabric refuses rather than guessing."""


@dataclass(frozen=True)
class Quote:
    """What a call costs, and what should be held against it."""

    sku: str
    usd_effective: float
    usd_reserved: float
    pricebook_version: str
    age_days: int
    stale: bool

    def cost_group(
        self, *, purpose: Purpose = "production", resv_id: str | None = None
    ) -> dict[str, Any]:
        """The canonical `cost{}` group — the six members, and only those (R16).

        `wall_ms` and `tokens` are sibling receipt fields, never members here: mixing measurement
        into money is how a cost group stops being auditable.
        """
        return {
            "usd_effective": round(self.usd_effective, 8),
            "usd_reserved": round(self.usd_reserved, 8),
            "sku": self.sku,
            "purpose": purpose,
            "resv_id": resv_id,
            "pricebook_version": self.pricebook_version,
        }


@dataclass(frozen=True)
class DriftVerdict:
    """`hc econ reconcile`: what the invoice says versus what the ledger booked."""

    drift: float
    level: Literal["ok", "flagged", "alarm"]
    fork: str
    detail: str


class Pricebook:
    def __init__(self, data: dict[str, Any], *, path: Path | None = None) -> None:
        self.path = path
        self.version = str(data.get("version", "0.0.0"))
        defaults = data.get("defaults", {}) or {}
        self.max_age_days = int(defaults.get("max_age_days", 30))
        self.stale_mult = float(defaults.get("stale_mult", 1.25))
        self.refuse_after = float(defaults.get("refuse_after", 2.0))
        self.skus: dict[str, dict[str, Any]] = {}

        for key, row in (data.get("skus") or {}).items():
            missing = [f for f in REQUIRED_FIELDS if f not in (row or {})]
            if missing:
                raise PricebookError(
                    f"SKU row '{key}' is missing {missing}; refusing the WHOLE book. A half-parsed "
                    "pricebook prices some lanes and silently omits others, which is worse than none."
                )
            self.skus[key] = dict(row)

    # ---------------------------------------------------------------- loading

    @classmethod
    def load(cls, path: Path | str | None = None) -> Pricebook:
        p = Path(path) if path else REPO_PRICEBOOK
        if not p.exists():
            raise PricebookError(f"no pricebook at {p}; the fabric will not price from memory")
        try:
            data = yaml.safe_load(p.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise PricebookError(f"{p} does not parse: {exc}") from exc
        if not isinstance(data, dict):
            raise PricebookError(f"{p} is not a mapping")
        return cls(data, path=p)

    # ---------------------------------------------------------------- pricing

    @staticmethod
    def sku_key(model: str, provider: str, service_tier: str = "standard") -> str:
        return f"{model}@{provider}/{service_tier}"

    def age_days(self, sku: str, *, today: date | None = None) -> int:
        row = self.skus[sku]
        as_of = datetime.strptime(str(row["as_of"]), "%Y-%m-%d").date()
        return ((today or date.today()) - as_of).days

    def quote(
        self,
        *,
        model: str,
        provider: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        cache_read_tokens: int = 0,
        cache_write_tokens: int = 0,
        service_tier: str = "standard",
        today: date | None = None,
        api_reported_usd: float | None = None,
    ) -> Quote:
        """Price one call. Refuses unknown and over-age lanes; reserves pessimistically when stale."""
        sku = self.sku_key(model, provider, service_tier)
        if sku not in self.skus:
            raise UnknownLane(
                f"no pricebook row for '{sku}'. Rule 5: an unpriced lane is REFUSED, never estimated "
                f"— add the row (with an as_of date) or run on a priced lane. Known: "
                f"{sorted(self.skus)[:4]}{'...' if len(self.skus) > 4 else ''}"
            )

        row = self.skus[sku]
        age = self.age_days(sku, today=today)
        if age > self.refuse_after * self.max_age_days:
            raise UnknownLane(
                f"pricebook row '{sku}' is {age} days old (limit "
                f"{int(self.refuse_after * self.max_age_days)}). Past this age a price is not stale, "
                "it is fiction — re-verify the row."
            )

        billable_prompt = max(0, prompt_tokens - cache_read_tokens)
        usd = (
            billable_prompt / 1e6 * float(row["input"])
            + completion_tokens / 1e6 * float(row["output"])
            + cache_read_tokens / 1e6 * float(row.get("cache_read", row["input"]))
            + cache_write_tokens / 1e6 * float(row.get("cache_write", row["input"]))
        )

        # The provider's own number wins when it gives one: it is the invoice, and our arithmetic is
        # only ever a prediction of it.
        effective = float(api_reported_usd) if api_reported_usd is not None else usd

        stale = age > self.max_age_days
        reserved = usd * (self.stale_mult if stale else 1.0)
        # Never reserve less than we will charge, whatever the multiplier arithmetic says.
        reserved = max(reserved, effective)

        return Quote(
            sku=sku,
            usd_effective=effective,
            usd_reserved=reserved,
            pricebook_version=self.version,
            age_days=age,
            stale=stale,
        )

    # ---------------------------------------------------------------- reconciliation

    def reconcile(
        self, *, ledger_usd: float, invoice_usd: float, ledger_tokens: int, invoice_tokens: int
    ) -> DriftVerdict:
        """Fold ledger spend against a provider invoice and diagnose the gap.

        The fork matters more than the number: if token totals AGREE the price is wrong (fix the
        book); if they DISAGREE the adapter is under-reporting usage (fix the adapter). Treating
        every drift as a price problem is how an adapter bug hides for a quarter.
        """
        if ledger_usd <= 0:
            return DriftVerdict(0.0, "ok", "none", "no ledger spend to reconcile")

        drift = (invoice_usd - ledger_usd) / ledger_usd
        tokens_match = ledger_tokens == invoice_tokens

        if abs(drift) <= 0.02:
            return DriftVerdict(drift, "ok", "none", f"drift {drift:+.2%} within 2%")
        if abs(drift) <= 0.10:
            return DriftVerdict(
                drift, "flagged", "price-change" if tokens_match else "adapter-bug",
                f"drift {drift:+.2%}: pricebook_drift event, row flagged",
            )
        fork = "price-change" if tokens_match else "adapter-bug"
        detail = (
            f"drift {drift:+.2%} exceeds 10%: row marked stale immediately (rule-3 pessimism "
            f"fleet-wide). Token totals {'match' if tokens_match else 'DIFFER'} ⇒ "
            + (
                "the price is wrong; update the book."
                if tokens_match
                else "the adapter under-reports usage; file an adapter-bug ticket."
            )
        )
        return DriftVerdict(drift, "alarm", fork, detail)


_CACHED: Pricebook | None = None


def default_pricebook() -> Pricebook:
    """The process-wide book. Loaded once; a fabric that re-reads prices mid-run is not auditable."""
    global _CACHED
    if _CACHED is None:
        _CACHED = Pricebook.load()
    return _CACHED
