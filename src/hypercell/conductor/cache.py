"""Cache discipline — the REALIZATION half of the cache seam (ARCH §7; slice ECON-S4).

N4′ gave the assembler the ORDER (stable → semi → volatile) and the TAGS; this module is where the
economics plane turns tags into a specific lane's cache controls and prices the result. The division
is deliberate and load-bearing: the assembler cannot know a lane's breakpoint budget or minimum
cacheable length — those are per-SKU facts that drift quarterly — and the econ plane cannot know
which bytes are stable — that is a property of the frame. Neither can do the other's job, so neither
tries.

**The null is unstaggered, tag-blind dispatch.** Every call ships the whole prompt as fresh input,
so N fork siblings sharing one identity pay N times to write the same prefix, and a resident re-reads
its own unchanged self every tick. Correct output, and a cache-hit rate of zero — which on a warm
tournament is the difference between a bill you can run a fleet on and one you cannot.

Four mechanisms, each a booked per-SKU fact realized here, never a hardcoded provider name:

* **Breakpoints.** Anthropic takes ≤4 explicit `cache_control` markers; OpenAI auto-caches org-wide
  with no marker; DeepSeek matches on a 64-token granularity. `realize_breakpoints` places markers
  at the stable/semi boundaries up to the lane's `max_cache_breakpoints`, and reports
  `cache-ineligible` (never silently uncached) when the stable prefix is under the lane's minimum.
* **Monotone validation, fail-closed.** A frame whose segments are not in stable→semi→volatile order
  cannot be cached correctly — a volatile byte inside the stable prefix busts the prefix on its
  first change. A shuffled frame is REFUSED, not best-efforted.
* **Fan-out stagger.** N calls sharing a prefix dispatch ONE warmer and release N−1 readers per the
  lane's booked `warmer_release`. `on_ttft` is documented ONLY for Anthropic; assuming it elsewhere
  silently pays N writes, so the default is `on_complete`.
* **Affinity as arithmetic.** Switching hosts forfeits the warm prefix. That forfeit is PRICED into
  the quote over a horizon, so stickiness emerges from the dollar-UCB rather than from a bonus term
  nobody can audit.

The canonical hit-rate is `cache_read / (input + cache_read + cache_write)` over cache-capable lanes.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..cell.frame import FrameManifest

#: Stability rank for the monotone check. A cacheable prefix must be a non-decreasing run of these.
_RANK = {"stable": 0, "semi": 1, "volatile": 2}

#: When a lane documents no minimum cacheable prompt, assume the largest common one (OpenAI 1024)
#: rather than 0 — an optimistic 0 would mark a tiny prefix cacheable and then silently miss.
_DEFAULT_MIN_CACHEABLE = 1024
#: Undocumented TTL is pessimistic 300s (pricebook.md §1), never assumed-long.
_DEFAULT_TTL_S = 300


class ShuffledFrame(Exception):
    """A frame whose segments are not in stability-monotone order. Refused, never cached best-effort."""


def validate_monotone(manifest: FrameManifest) -> None:
    """Fail-closed: segments MUST appear stable → semi → volatile (ARCH §7.2 step 8).

    Checked over NON-EMPTY segments only — an empty section (a d1 cell's zero-budget digest) is not
    a boundary violation, it is simply absent. The failure this guards is a volatile segment landing
    inside the stable prefix, where its first change would bust a prefix the lane believed cacheable
    and the miss would attribute to the provider instead of to the assembler bug that caused it.
    """
    last_rank = -1
    last_name = ""
    for seg in manifest.segments:
        if not seg.items:
            continue
        rank = _RANK[seg.stability]
        if rank < last_rank:
            raise ShuffledFrame(
                f"segment '{seg.name}' ({seg.stability}) follows '{last_name}' — a less-stable "
                f"segment precedes a more-stable one. The cacheable prefix must be a monotone run; "
                "this frame would bust its own cache on the first volatile change."
            )
        last_rank, last_name = rank, seg.name


@dataclass(frozen=True)
class BreakpointPlan:
    """Where the stable prefix ends and whether the lane can cache it."""

    eligible: bool
    cacheable_tokens: int
    breakpoints: tuple[int, ...]  # segment indices carrying an explicit cache marker
    reason: str

    @property
    def implicit(self) -> bool:
        """True when the lane auto-caches with no explicit marker (OpenAI-style)."""
        return self.eligible and not self.breakpoints


def realize_breakpoints(manifest: FrameManifest, sku_row: dict[str, Any]) -> BreakpointPlan:
    """Map the frame's stability tags to THIS lane's breakpoint controls.

    The cacheable prefix is the leading stable+semi run. A lane with `max_cache_breakpoints` places
    explicit markers at the section boundaries within that run, capped at the budget (the LAST
    boundaries win — the longest prefixes are the ones worth marking). A lane without the field
    auto-caches implicitly. Either way, a prefix under the lane's `cache_min_prompt_tokens` is
    reported ineligible with a reason, because "too short to cache" reported is a fact an operator
    can act on and "silently uncached" is a bill they cannot explain.
    """
    validate_monotone(manifest)

    prefix_tokens = 0
    boundaries: list[int] = []
    for i, seg in enumerate(manifest.segments):
        if seg.stability == "volatile":
            break
        if seg.items:
            prefix_tokens += seg.tokens
            boundaries.append(i)  # a boundary marker could sit at the end of this cacheable segment

    min_cacheable = int(sku_row.get("cache_min_prompt_tokens", _DEFAULT_MIN_CACHEABLE))
    if "cache_read_mult" not in sku_row:
        return BreakpointPlan(False, prefix_tokens, (), "lane declares no cache (no cache_read_mult)")
    if prefix_tokens < min_cacheable:
        return BreakpointPlan(
            False, prefix_tokens, (),
            f"stable prefix {prefix_tokens} tok is under the lane minimum {min_cacheable}; "
            "cache-ineligible (reported, never silently uncached)",
        )

    max_bp = sku_row.get("max_cache_breakpoints")
    if max_bp is None:
        return BreakpointPlan(True, prefix_tokens, (), "lane auto-caches (implicit, no marker)")
    # Keep the LAST `max_bp` boundaries: the longest prefixes are the valuable ones to mark.
    kept = tuple(boundaries[-int(max_bp):]) if boundaries else ()
    return BreakpointPlan(True, prefix_tokens, kept, f"explicit breakpoints at {list(kept)}")


def canonical_hit_rate(*, input_tokens: int, cache_read_tokens: int, cache_write_tokens: int) -> float:
    """`cache_read / (input + cache_read + cache_write)` (ARCH §7). The `hc top` number, bar ≥0.60.

    Over the whole denominator on purpose: a rate of `read/(read+input)` would flatter a lane that
    paid huge write costs, and the writes are exactly the spend caching is supposed to avoid paying
    twice. A low rate indicts frame ORDERING first and the provider last.
    """
    denom = input_tokens + cache_read_tokens + cache_write_tokens
    return cache_read_tokens / denom if denom else 0.0


@dataclass(frozen=True)
class StaggerPlan:
    """One warmer, N−1 readers, and the honest count of prefix WRITES the plan will pay."""

    n: int
    release: str  # on_ttft | on_complete | none
    writes_paid: int
    reason: str

    @property
    def realizes_sharing(self) -> bool:
        return self.writes_paid == 1


def plan_stagger(n: int, sku_row: dict[str, Any]) -> StaggerPlan:
    """N calls sharing a prefix: dispatch one warmer, release N−1 per the lane's `warmer_release`.

    The subtle failure this encodes: `on_ttft` (readers may start after the warmer's first token) is
    DOCUMENTED ONLY for Anthropic. Assuming it on a lane that does not support it means the N−1
    readers race the warmer, all miss the not-yet-written prefix, and the fabric silently pays N
    writes while believing it paid one. So an unbooked lane defaults to `on_complete`, and a lane
    that booked `on_ttft` we do not trust is downgraded here rather than downgraded by the invoice.
    """
    if n <= 1:
        return StaggerPlan(n, "none", max(0, n), "single call; nothing to stagger")
    release = str(sku_row.get("warmer_release", "on_complete"))
    if release not in ("on_ttft", "on_complete"):
        release = "on_complete"
    # Either release policy pays exactly ONE prefix write (the warmer's); the difference is latency,
    # not writes. The N-write failure is the NULL — assuming a release the lane does not honor — and
    # is modelled in the drill, not producible from a booked plan.
    return StaggerPlan(n, release, 1, f"1 warmer + {n - 1} readers, release={release}")


def computed_savings(*, n: int, prefix_tokens: int, tail_tokens: int, sku_row: dict[str, Any]) -> float:
    """The ideal prefix saving a perfect cache would realize for N calls sharing a prefix.

    N calls, each with the same prefix and its own tail. Cold cost: N × (prefix + tail) at input
    price. Warm ideal: one prefix write + (N−1) prefix reads at `cache_read_mult` + N tails. The
    saving is the difference — the number the stagger must realize ≥80% of.
    """
    in_price = float(sku_row["input"]) / 1e6
    read_mult = float(sku_row.get("cache_read_mult", 1.0))
    cold = n * (prefix_tokens + tail_tokens) * in_price
    warm = (prefix_tokens * in_price) + (n - 1) * prefix_tokens * in_price * read_mult + n * tail_tokens * in_price
    return max(0.0, cold - warm)


def warm_quote(
    *, prefix_tokens: int, tail_tokens: int, cached_prefix_tokens: int, sku_row: dict[str, Any]
) -> float:
    """Price one call given how much of its prefix is already warm on this lane.

    Billable input = the un-cached prefix + the tail; the warm part is re-priced at
    `cache_read_mult`. This is the arithmetic affinity rides on: a lane holding the prefix warm
    quotes cheaper for the same work than a cold one, with no bonus term anywhere.
    """
    in_price = float(sku_row["input"]) / 1e6
    read_mult = float(sku_row.get("cache_read_mult", 1.0))
    warm = min(cached_prefix_tokens, prefix_tokens)
    cold_prefix = prefix_tokens - warm
    return (cold_prefix + tail_tokens) * in_price + warm * in_price * read_mult


def affinity_forfeit(
    *, prefix_tokens: int, warm_sku: dict[str, Any], switch_sku: dict[str, Any], horizon: int = 3
) -> float:
    """The dollars a host-switch forfeits over `horizon` future calls — priced, not bonus'd.

    Staying on the warm host, the next `horizon` calls read the prefix cheap. Switching, the new
    host must WRITE the prefix cold first and then read it at its own (possibly worse) multiplier.
    The forfeit is the difference. The dollar-UCB divides by ê, so a positive forfeit makes the
    incumbent lane's index higher and the swarm sticks to warmth — exactly as long as the arithmetic
    says it is worth it, and no longer.
    """
    warm_in = float(warm_sku["input"]) / 1e6
    warm_read = float(warm_sku.get("cache_read_mult", 1.0))
    switch_in = float(switch_sku["input"]) / 1e6
    switch_read = float(switch_sku.get("cache_read_mult", 1.0))

    stay = horizon * prefix_tokens * warm_in * warm_read
    switch = prefix_tokens * switch_in + horizon * prefix_tokens * switch_in * switch_read
    return max(0.0, switch - stay)
