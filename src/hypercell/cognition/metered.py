"""The single metering path — the ONE place a provider adapter is constructed (ONE-METER-1).

**The null is per-call-site wrapping**, and it is the defect F25 came from: whoever forgets to wrap
gets free tokens, silently. A judge panel spun up its own adapters and every judge dollar went
unbooked — not because anyone disabled metering, but because metering was something each call site
had to *remember*.

So construction moved here. `ONE-METER-1` is an AST check, not a convention: it walks the tree and
fails CI if any module outside this file constructs a provider adapter. A rule a linter can enforce
does not depend on anyone remembering it.

The seam is deliberately thin — resolve config to an adapter, wrap it in the governor — because
anything else living here would give call sites a reason to bypass it.
"""
from __future__ import annotations

from typing import Any

from ..common.meter import Meter
from ..common.types import ProviderConfig
from .base import Cognition, CompletionResult, Messages
from .mock import MockCognition
from .openai_compat import OpenAICompatCognition
from .registry import PROVIDER_DEFAULTS, resolve_key

#: The adapter classes ONE-METER-1 guards. Adding one here without adding it to the check would be
#: the hole this whole slice closes, so the drill reads THIS tuple rather than a copy of it.
ADAPTER_CLASSES = ("OpenAICompatCognition", "MockCognition")


def build_adapter(cfg: ProviderConfig) -> Cognition:
    """Resolve a ProviderConfig to a live adapter. **The only legal construction site.**"""
    provider = cfg.provider.lower()
    if provider in ("mock", "echo"):
        return MockCognition(model=cfg.model or "mock", name=provider)
    if provider in ("anthropic", "gemini"):
        raise NotImplementedError(
            f"provider '{provider}' needs its thin native adapter (P0.2 TODO); "
            "the OpenAI-compatible providers work today."
        )
    base_url = cfg.base_url or PROVIDER_DEFAULTS.get(provider)
    if not base_url:
        raise RuntimeError(
            f"provider '{provider}' has no base_url: set provider.base_url on the role, or add a "
            f"default. The fabric will not guess an endpoint."
        )
    return OpenAICompatCognition(
        base_url=base_url,
        api_key=resolve_key(cfg),
        model=cfg.model,
        name=cfg.provider,
        default_params=cfg.params,
    )


def metered(cfg: ProviderConfig, gov: Meter | None = None) -> Cognition:
    """Build an adapter and wrap it in the governor. The path every cognition call takes.

    Passing `gov=None` returns the bare adapter, which is legal for a smoke test and NOT legal in a
    run — the governor is what makes the hard-stop unbypassable, and a run without one is a run
    whose budget is a suggestion.
    """
    inner = build_adapter(cfg)
    return inner if gov is None else MeteredCognition(inner, cfg.provider.lower(), gov, cfg.model)


class MeteredCognition(Cognition):
    """Wrap any Cognition: enforce the hard-stop before, meter cost after, cap concurrency around."""

    def __init__(self, inner: Cognition, provider: str, gov: Meter, model: str = "") -> None:
        self.name = f"metered:{inner.name}"
        self._inner = inner
        self._provider = provider
        self._gov = gov
        #: The estimator needs the lane to price it. Carried with the call rather than stashed on
        #: the governor: a "last model seen" field is a race the first concurrent run would find.
        self._model = model or getattr(inner, "model", "")

    async def complete(self, messages: Messages, **params: Any) -> CompletionResult:
        # RESERVE the worst case, then call, then settle at the truth. `check()` alone was F6: it
        # compares a counter to a cap before a call it cannot price, so the last call goes over and
        # the hard-stop reports the breach it failed to prevent.
        resv_id = self._gov.open_call(self._provider, {**params, "model": self._model})
        try:
            sem = self._gov.semaphore(self._provider)
            if sem is not None:
                async with sem:
                    result = await self._inner.complete(messages, **params)
            else:
                result = await self._inner.complete(messages, **params)
        except BaseException:
            # The call did not happen (or did not answer). Release rather than commit: holding
            # headroom for work that produced nothing starves the run for no reason.
            self._gov.close_call(resv_id, self._provider, None)
            raise
        cost = self._gov.close_call(resv_id, self._provider, result)
        # F26 closed: `cost_usd` was declared in v1 and never populated. The receipt now carries a
        # real number, priced off a dated book.
        return result.model_copy(update={"cost_usd": cost})
