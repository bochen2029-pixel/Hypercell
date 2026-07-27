"""`quote()` — the expected cost of the NEXT pull, exposed to the allocation and route planes.

The pricebook (`conductor/pricebook.py`) prices what a call *did* cost; this module prices what a
pull *will* cost, because two consumers need the forward-looking number:

* the **dollar-UCB** divides by it — the index is score-per-expected-dollar, and an index divided
  by a stale or invented number allocates by fiction;
* the **router** breaks ties with it — between two cells that cover a need equally, the cheaper
  lane wins.

`window_close_eta` and `expiry_at` are declared now and `None` until the batch/cache mechanics land
(ECON-S4 / ECON-BATCH-1): the route plane's seam wants the fields to exist before the first caller,
so the batch slice extends a shape instead of inventing one. An undeclared seam is one nobody can
build against.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .pricebook import Pricebook, PricebookError, UnknownLane


@dataclass(frozen=True)
class PullQuote:
    """What the next pull on a lane is expected to cost, and how much to trust the number."""

    sku: str
    usd_expected: float
    stale: bool
    age_days: int
    #: ECON-S4/BATCH seam: when the current batch window closes, and when this quote stops being
    #: honourable. None until the batch mechanics land — declared early so callers can build.
    window_close_eta: str | None = None
    expiry_at: str | None = None


def quote_pull(
    book: Pricebook,
    *,
    model: str,
    provider: str,
    est_in: int = 8192,
    est_out: int = 4096,
    service_tier: str = "standard",
    today: date | None = None,
) -> PullQuote:
    """Price one expected pull off the dated book. Refuses rather than guesses (ECON-PB-1's law).

    A stale row still quotes — multiplied by the book's `stale_mult`, so a lane nobody re-priced
    gets *less* attractive, never silently cheaper — but a row past the refusal threshold raises:
    an index fed a number that old would be allocating on a rumour.
    """
    sku = Pricebook.sku_key(model, provider, service_tier)
    row = book.skus.get(sku)
    if row is None:
        raise UnknownLane(f"no pricebook row for {sku}; the fabric will not quote from memory")

    age = book.age_days(sku, today=today)
    stale = age > book.max_age_days
    if age > book.max_age_days * book.refuse_after:
        raise PricebookError(
            f"{sku} was priced {age} days ago, past the refusal threshold "
            f"({book.max_age_days} x {book.refuse_after}); a quote that old is a rumour, not a price"
        )

    usd = est_in / 1e6 * float(row["input"]) + est_out / 1e6 * float(row["output"])
    if stale:
        usd *= book.stale_mult
    return PullQuote(sku=sku, usd_expected=usd, stale=stale, age_days=age)
