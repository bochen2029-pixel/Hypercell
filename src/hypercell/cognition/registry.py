"""Resolve a ProviderConfig to a live Cognition. Swap the provider by config, never by code (HC-6).

Base URLs are best-effort defaults and are overridable per role via `provider.base_url`. Keys are read
from the env var named by `provider.key_ref` (default `<PROVIDER>_API_KEY`) or the substrate secret store.
"""
from __future__ import annotations

import os

from ..common.types import ProviderConfig

# OpenAI-compatible endpoints. Override per role with provider.base_url when a region/edition differs.
PROVIDER_DEFAULTS: dict[str, str] = {
    "deepseek": "https://api.deepseek.com/v1",
    "cerebras": "https://api.cerebras.ai/v1",
    "glm": "https://api.z.ai/api/paas/v4",
    "kimi": "https://api.moonshot.cn/v1",
    "qwen": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
    "grok": "https://api.x.ai/v1",
    "openai": "https://api.openai.com/v1",
    # anthropic / gemini use thin native adapters (their own files) behind the same seam.
}


def resolve_key(cfg: ProviderConfig) -> str:
    ref = cfg.key_ref or f"{cfg.provider.upper()}_API_KEY"
    key = os.environ.get(ref)
    if not key:
        raise RuntimeError(
            f"no API key for provider '{cfg.provider}': set env var '{ref}' (see .env.example)"
        )
    return key


# `build_cognition` USED TO LIVE HERE and constructed adapters directly. It moved to
# `cognition/metered.py` at slice S-KG-3 so there is exactly ONE construction site, which
# ONE-METER-1 enforces by AST. The null it replaces is per-call-site wrapping: whoever forgets to
# wrap gets free tokens, and that is where F25 came from -- a judge panel spun up its own adapters
# and every judge dollar went unbooked.
