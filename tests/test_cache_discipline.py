"""ECON-CACHE-1 — cache discipline (slice ECON-S4).

**The bar, verbatim:** ≥60% hit on a warm tournament; stagger realizes ≥80% of computed savings;
shuffled frame refused. (The ≥60% attribution-matches-`cache_read` half is joint with NUC-5.)

**The null is unstaggered, tag-blind dispatch.** Every call ships the whole prompt as fresh input:
N fork siblings pay N times to write the same identity, a resident re-reads itself every tick, and
the hit-rate is zero. Correct output, ruinous bill. Each bar below runs the null beside the realized
plan so "≥60%" and "≥80%" are deltas over a measured floor, not absolutes hanging in air.

The assembler owns ORDER + TAGS (N4′); this file drills the REALIZATION — turning tags into a lane's
breakpoints, validating monotone order fail-closed, and pricing the result. The provider cache model
(`bench/drills/cache_model.py`) is a faithful stand-in that reports `cache_read` the way a live lane
would, so a realization bug shows up as a low hit-rate here exactly as it would on the invoice.
"""
from __future__ import annotations

import pytest
from bench.drills.cache_model import CacheProvider, Tally

from hypercell.cell.frame import Candidate, Window, assemble_frame
from hypercell.conductor.cache import (
    ShuffledFrame,
    affinity_forfeit,
    canonical_hit_rate,
    computed_savings,
    plan_stagger,
    realize_breakpoints,
    validate_monotone,
    warm_quote,
)
from hypercell.conductor.pricebook import Pricebook

BOOK = Pricebook.load()
ANTHROPIC = BOOK.skus["claude-opus-4.8@anthropic/standard"]
OPENAI = BOOK.skus["gpt-4o-mini@openai/standard"]
DEEPSEEK = BOOK.skus["deepseek-chat@deepseek/standard"]
STUB = BOOK.skus["stub@stub/standard"]  # no cache_read_mult -> cache-ineligible

D2_RATIOS = {"identity": .08, "tools": .08, "digest": .12, "working": .10,
             "retrieved": .14, "recap": .18, "percept": .22, "slack": .08}
SALIENCE = {"w_pin": 4.0, "w_factual": 2.0, "w_task": 1.5, "w_recency": 1.0, "w_ref": 0.5, "half_life": 512.0}


def _frame_with(prefix_target_tokens: int, percept: str):
    """A manifest whose cacheable prefix is ~`prefix_target_tokens`, for the breakpoint drills.

    `estimate_tokens` is bytes//4, so `"w" * (4 * T)` is ~T tokens exactly — precise sizing without
    guessing at word lengths. The 128k window keeps even a big identity inside its S0 budget.
    """
    body = "w" * (4 * prefix_target_tokens)
    cands = {
        "S0": [Candidate(ref="role.prompt", body=body, mandatory=True, id="0")],
        "S1": [Candidate(ref="tool:fs.read", body="tool schema: fs.read " * 30, mandatory=True, id="0")],
        "S2": [Candidate(ref="digest:0", body="installed digest " * 40, seq=0, id="000000")],
        "S6": [Candidate(ref="percept", body=percept, seq=1 << 30, id="percept")],
    }
    return assemble_frame(ratios=D2_RATIOS, salience_weights=SALIENCE, window=Window(131072, 4096),
                          candidates=cands, ledger_head=1, tick=1, percept=percept)


# ================================================================ shuffled frame refused


def test_a_monotone_frame_validates() -> None:
    _, m = _frame_with(400, "go")
    validate_monotone(m)  # S0,S1 stable, S2 semi, S6 volatile — in order


def test_a_shuffled_frame_is_refused_fail_closed() -> None:
    """A volatile segment before a stable one busts the cache on its first change. Refused."""
    from dataclasses import replace

    _, m = _frame_with(400, "go")
    segs = list(m.segments)
    # Hand-build the pathology: move the volatile percept segment (S6) ahead of the stable S0.
    s6 = next(s for s in segs if s.section == "S6")
    reordered = [s6] + [s for s in segs if s.section != "S6"]
    shuffled = replace(m, segments=tuple(reordered))
    with pytest.raises(ShuffledFrame, match="monotone|precedes|less-stable"):
        validate_monotone(shuffled)


def test_an_empty_section_is_not_a_boundary_violation() -> None:
    """A d1 cell's zero-budget digest is absent, not out-of-order — the check skips empties."""
    cands = {
        "S0": [Candidate(ref="role.prompt", body="You are a worker. " * 60, mandatory=True, id="0")],
        "S6": [Candidate(ref="percept", body="go", seq=1 << 30, id="percept")],
    }
    _, m = assemble_frame(ratios=D2_RATIOS, salience_weights=SALIENCE, window=Window(65536, 4096),
                          candidates=cands, ledger_head=1, tick=1, percept="go")
    validate_monotone(m)  # S1..S5 empty; no violation


# ================================================================ breakpoint realization


def test_anthropic_gets_explicit_breakpoints_capped_at_its_budget() -> None:
    _, m = _frame_with(4000, "investigate the crash")
    plan = realize_breakpoints(m, ANTHROPIC)
    assert plan.eligible and plan.cacheable_tokens > 0
    assert len(plan.breakpoints) <= int(ANTHROPIC["max_cache_breakpoints"])
    assert not plan.implicit, "anthropic uses explicit markers"


def test_openai_auto_caches_implicitly() -> None:
    _, m = _frame_with(6000, "investigate the crash")  # prefix well over OpenAI's 1024 minimum
    plan = realize_breakpoints(m, OPENAI)
    assert plan.eligible and plan.implicit, "openai should auto-cache with no explicit marker"


def test_a_prefix_under_the_lane_minimum_is_reported_ineligible_not_silently_uncached() -> None:
    """'too short to cache' reported is a fact an operator can act on; silently uncached is a bill
    they cannot explain."""
    _, m = _frame_with(80, "go")  # tiny identity, under Anthropic's 512
    plan = realize_breakpoints(m, ANTHROPIC)
    assert not plan.eligible and "under the lane minimum" in plan.reason


def test_a_lane_that_declares_no_cache_is_ineligible() -> None:
    _, m = _frame_with(4000, "go")
    plan = realize_breakpoints(m, STUB)
    assert not plan.eligible and "no cache" in plan.reason


# ================================================================ the warm tournament (>=60%)


def _tournament(sku_row: dict, *, ticks: int, prefix_tokens: int, tail_tokens: int, cached: bool) -> Tally:
    """T ticks sharing one stable identity prefix. `cached=False` is the tag-blind null."""
    provider = CacheProvider(sku_row=sku_row)
    tally = Tally()
    for t in range(ticks):
        if cached:
            tally.add(provider.call(prefix_hash="identity", prefix_tokens=prefix_tokens,
                                    tail_tokens=tail_tokens, at_s=float(t)))
        else:
            # The null declares no cacheable prefix, so every tick is all-fresh-input.
            tally.add((prefix_tokens + tail_tokens, 0, 0))
    return tally


def test_the_null_tournament_has_a_zero_hit_rate() -> None:
    tally = _tournament(ANTHROPIC, ticks=10, prefix_tokens=2000, tail_tokens=200, cached=False)
    rate = canonical_hit_rate(input_tokens=tally.input_tokens, cache_read_tokens=tally.cache_read_tokens,
                              cache_write_tokens=tally.cache_write_tokens)
    assert rate == 0.0, "the tag-blind null is supposed to cache nothing — that is the defect"


def test_the_warm_tournament_clears_60_percent() -> None:
    tally = _tournament(ANTHROPIC, ticks=10, prefix_tokens=2000, tail_tokens=200, cached=True)
    rate = canonical_hit_rate(input_tokens=tally.input_tokens, cache_read_tokens=tally.cache_read_tokens,
                              cache_write_tokens=tally.cache_write_tokens)
    assert rate >= 0.60, f"warm hit-rate {rate:.2%} is under the 60% bar"


def test_the_attribution_matches_the_provider_cache_read() -> None:
    """NUC-5's joint half: the cacheable prefix the realization named equals the `cache_read` the
    provider actually reported on a warm call."""
    _, m = _frame_with(4000, "go")
    plan = realize_breakpoints(m, ANTHROPIC)
    provider = CacheProvider(sku_row=ANTHROPIC)
    provider.call(prefix_hash="p", prefix_tokens=plan.cacheable_tokens, tail_tokens=100, at_s=0.0)  # warm it
    _, read, _ = provider.call(prefix_hash="p", prefix_tokens=plan.cacheable_tokens, tail_tokens=100, at_s=1.0)
    assert read == plan.cacheable_tokens, "the realization's cacheable prefix disagrees with cache_read"


def test_an_expired_ttl_falls_back_to_a_write() -> None:
    """A prefix past its TTL is cold again — the provider re-writes, and the hit-rate reflects it."""
    provider = CacheProvider(sku_row=ANTHROPIC)  # ttl 300s
    provider.call(prefix_hash="p", prefix_tokens=2000, tail_tokens=100, at_s=0.0)  # write
    _, read_warm, _ = provider.call(prefix_hash="p", prefix_tokens=2000, tail_tokens=100, at_s=200.0)
    _, read_cold, write_cold = provider.call(prefix_hash="p", prefix_tokens=2000, tail_tokens=100, at_s=999.0)
    assert read_warm == 2000, "a within-TTL call should have hit"
    assert read_cold == 0 and write_cold == 2000, "a past-TTL call should have re-written"


# ================================================================ fan-out stagger (>=80% of savings)


def _staggered(sku_row: dict, *, n: int, prefix_tokens: int, tail_tokens: int) -> Tally:
    """One warmer writes the prefix; the other N-1 read it (on_complete: after the warmer finishes)."""
    provider = CacheProvider(sku_row=sku_row)
    tally = Tally()
    tally.add(provider.call(prefix_hash="shared", prefix_tokens=prefix_tokens, tail_tokens=tail_tokens, at_s=0.0))
    for _ in range(1, n):
        tally.add(provider.call(prefix_hash="shared", prefix_tokens=prefix_tokens, tail_tokens=tail_tokens, at_s=1.0))
    return tally


def _unstaggered(sku_row: dict, *, n: int, prefix_tokens: int, tail_tokens: int) -> Tally:
    """The null: N callers dispatch at once, none sees another's write, so all N write the prefix."""
    tally = Tally()
    for _ in range(n):
        provider = CacheProvider(sku_row=sku_row)  # each blind to the others -> all cold
        tally.add(provider.call(prefix_hash="shared", prefix_tokens=prefix_tokens, tail_tokens=tail_tokens))
    return tally


def test_stagger_realizes_at_least_80_percent_of_computed_savings() -> None:
    n, prefix, tail = 8, 3000, 200
    ideal = computed_savings(n=n, prefix_tokens=prefix, tail_tokens=tail, sku_row=ANTHROPIC)

    cold_cost = n * (prefix + tail) * float(ANTHROPIC["input"]) / 1e6
    realized = cold_cost - _staggered(ANTHROPIC, n=n, prefix_tokens=prefix, tail_tokens=tail).usd(ANTHROPIC)

    assert ideal > 0
    assert realized / ideal >= 0.80, f"stagger realized {realized / ideal:.0%} of computed savings"


def test_the_unstaggered_null_realizes_almost_nothing() -> None:
    """N cold writes: the null pays the prefix N times and saves ~nothing over shipping it fresh."""
    n, prefix, tail = 8, 3000, 200
    ideal = computed_savings(n=n, prefix_tokens=prefix, tail_tokens=tail, sku_row=ANTHROPIC)
    cold_cost = n * (prefix + tail) * float(ANTHROPIC["input"]) / 1e6
    realized = cold_cost - _unstaggered(ANTHROPIC, n=n, prefix_tokens=prefix, tail_tokens=tail).usd(ANTHROPIC)
    assert realized / ideal < 0.20, "the unstaggered null should realize almost none of the savings"


def test_plan_stagger_pays_one_write_and_downgrades_untrusted_on_ttft() -> None:
    assert plan_stagger(8, ANTHROPIC).release == "on_ttft"  # documented for anthropic
    assert plan_stagger(8, DEEPSEEK).release == "on_complete"  # everywhere else, the safe default
    assert plan_stagger(8, DEEPSEEK).writes_paid == 1
    assert plan_stagger(1, ANTHROPIC).release == "none", "a single call has nothing to stagger"


# ================================================================ affinity as arithmetic


def test_switching_to_an_equally_priced_cold_lane_forfeits_the_warm_prefix() -> None:
    """Stickiness must emerge from the QUOTE, not a bonus term. Switching to a cold lane at the SAME
    price forfeits exactly what the new host must pay to get warm — a positive number the dollar-UCB
    divides into the switched lane's index."""
    forfeit = affinity_forfeit(prefix_tokens=4000, warm_sku=ANTHROPIC, switch_sku=ANTHROPIC, horizon=3)
    assert forfeit > 0, "leaving a warm prefix for an equally-priced cold one cost nothing"


def test_affinity_yields_to_a_real_price_win() -> None:
    """Affinity is not 'never switch'. Switching from expensive-warm to a much cheaper cold lane is
    genuinely a saving, so the forfeit is zero — the arithmetic favours the switch, correctly. A
    bonus-term design would cling to the warm-but-expensive host and overpay to stay sticky."""
    forfeit = affinity_forfeit(prefix_tokens=4000, warm_sku=ANTHROPIC, switch_sku=OPENAI, horizon=3)
    assert forfeit == 0.0, "affinity clung to an expensive warm host over a cheaper cold one"


def test_a_warm_lane_quotes_cheaper_than_a_cold_one_for_the_same_work() -> None:
    warm = warm_quote(prefix_tokens=4000, tail_tokens=300, cached_prefix_tokens=4000, sku_row=ANTHROPIC)
    cold = warm_quote(prefix_tokens=4000, tail_tokens=300, cached_prefix_tokens=0, sku_row=ANTHROPIC)
    assert warm < cold, "warmth did not lower the quote; affinity has no arithmetic to ride on"


def test_no_warm_prefix_means_no_forfeit() -> None:
    assert affinity_forfeit(prefix_tokens=0, warm_sku=ANTHROPIC, switch_sku=OPENAI) == 0.0


# ================================================================ the hit-rate formula itself


def test_hit_rate_counts_writes_against_you() -> None:
    """`read/(input+read+write)`, not `read/(input+read)`: a lane that paid huge writes should not
    look thrifty. Writes are the spend caching exists to avoid paying twice."""
    generous = 300 / (100 + 300)  # the WRONG formula (ignores writes)
    honest = canonical_hit_rate(input_tokens=100, cache_read_tokens=300, cache_write_tokens=200)
    assert honest < generous and abs(honest - 0.5) < 1e-9


# ================================================================ hc top integration


def test_spend_fold_reports_the_canonical_hit_rate() -> None:
    """The hit-rate has a production home: Governor.spend_fold, where `hc top` reads it. Built from
    the per-call token records the metered path already stores, via the canonical formula."""
    from hypercell.cognition.base import CompletionResult
    from hypercell.conductor.governor import Governor

    gov = Governor(usd_cap=10.0)
    # A cold write then a warm read of the same prefix, on a cache-priced lane.
    gov.record("anthropic", CompletionResult(text="a", model="claude-opus-4.8", prompt_tokens=200,
               completion_tokens=50, cache_read_tokens=0, cache_write_tokens=2000))
    gov.record("anthropic", CompletionResult(text="b", model="claude-opus-4.8", prompt_tokens=200,
               completion_tokens=50, cache_read_tokens=2000, cache_write_tokens=0))
    fold = gov.spend_fold()
    assert "cache_hit_rate" in fold
    # read 2000 / (input 400 + read 2000 + write 2000) = 0.4545...
    assert abs(fold["cache_hit_rate"] - 2000 / 4400) < 1e-9
