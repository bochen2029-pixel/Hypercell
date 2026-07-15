"""OpenAI-compatible cognition adapter — covers most providers with one implementation.

DeepSeek, Cerebras, GLM (Zhipu/z.ai), Kimi (Moonshot), Qwen (DashScope), Grok (xAI), OpenAI all speak the
`/chat/completions` shape. Anthropic and Gemini get thin adapters (their own files) behind the same seam.
"""
from __future__ import annotations

from typing import Any

import httpx

from .base import Cognition, CompletionResult, Messages


class OpenAICompatCognition(Cognition):
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        name: str = "openai-compat",
        default_params: dict[str, Any] | None = None,
        timeout: float = 120.0,
    ) -> None:
        self.name = name
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._default_params = default_params or {}
        self._timeout = timeout

    async def complete(self, messages: Messages, **params: Any) -> CompletionResult:
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            **self._default_params,
            **params,
        }
        headers = {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(
                f"{self._base_url}/chat/completions", json=payload, headers=headers
            )
            resp.raise_for_status()
            data: dict[str, Any] = resp.json()
        choice = data["choices"][0]["message"]["content"] or ""
        usage = data.get("usage", {}) or {}
        return CompletionResult(
            text=choice,
            model=data.get("model", self._model),
            prompt_tokens=int(usage.get("prompt_tokens", 0)),
            completion_tokens=int(usage.get("completion_tokens", 0)),
            raw=data,
        )
