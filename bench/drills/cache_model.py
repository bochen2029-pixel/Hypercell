"""A faithful provider cache model — the deterministic stand-in ECON-CACHE-1 measures against.

There is no live Anthropic/OpenAI adapter with cache params yet (the BUILD row lists them "as they
land"), so the ≥60%-hit and stagger-savings bars are measured against this model: a provider that
honors a breakpoint plan and reports `(input, cache_read, cache_write)` the way the real ones do.
It is not a mock that returns canned numbers — it implements the provider contract we are realizing
against (write-on-cold, read-on-warm, TTL expiry, minimum cacheable length, refresh-on-hit), so a
bug in the realization shows up here as a low hit-rate exactly as it would on the invoice.

Deterministic: the caller passes `at_s` (a logical clock), never a wall clock, so a replay is a
replay.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

_DEFAULT_MIN_CACHEABLE = 1024
_DEFAULT_TTL_S = 300


@dataclass
class CacheProvider:
    """Models one lane's prefix cache. `call` returns the token accounting a real provider would."""

    sku_row: dict[str, Any]
    _warm: dict[str, float] = field(default_factory=dict)  # prefix_hash -> expiry (logical seconds)

    def call(
        self, *, prefix_hash: str, prefix_tokens: int, tail_tokens: int, at_s: float = 0.0
    ) -> tuple[int, int, int]:
        """(input, cache_read, cache_write) for one call. The prefix is cached; the tail never is."""
        row = self.sku_row
        min_cacheable = int(row.get("cache_min_prompt_tokens", _DEFAULT_MIN_CACHEABLE))
        if "cache_read_mult" not in row or prefix_tokens < min_cacheable:
            # Cache-ineligible: the whole prompt is fresh input, every call. This is also the NULL
            # (tag-blind dispatch) when the caller declines to declare a cacheable prefix at all.
            return (prefix_tokens + tail_tokens, 0, 0)

        ttl = float(row.get("cache_ttl_s", _DEFAULT_TTL_S))
        expiry = self._warm.get(prefix_hash)
        warm = expiry is not None and expiry > at_s
        if warm:
            if row.get("cache_ttl_refresh_on_hit"):
                self._warm[prefix_hash] = at_s + ttl
            return (tail_tokens, prefix_tokens, 0)  # HIT: read the prefix, pay input only for the tail
        self._warm[prefix_hash] = at_s + ttl
        return (tail_tokens, 0, prefix_tokens)  # MISS: write the prefix, pay input only for the tail


@dataclass
class Tally:
    input_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0

    def add(self, triple: tuple[int, int, int]) -> None:
        self.input_tokens += triple[0]
        self.cache_read_tokens += triple[1]
        self.cache_write_tokens += triple[2]

    def usd(self, sku_row: dict[str, Any]) -> float:
        in_price = float(sku_row["input"]) / 1e6
        read_mult = float(sku_row.get("cache_read_mult", 1.0))
        write_mult = float(sku_row.get("cache_write_mult", 1.0))
        return (
            self.input_tokens * in_price
            + self.cache_read_tokens * in_price * read_mult
            + self.cache_write_tokens * in_price * write_mult
        )
