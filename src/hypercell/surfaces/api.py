"""The Conductor HTTP surface (P0). Command the fabric over SSH/HTTP.

  POST /ask    {prompt, provider?, model?, role?, claim_id?, idem?} -> {claim_id, text}
  POST /resume {claim_id, provider?, model?}                        -> {claim_id, text}
  GET  /fleet                                                       -> {fleet: [claim-ids]}
  GET  /health
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

from ..cell.runtime import build_cell, load_role
from ..common.types import ProviderConfig

app = FastAPI(title="hypercell conductor", version="0.1.0")


def _home() -> str:
    return os.environ.get("HYPERCELL_HOME", ".hypercellstate")


class AskReq(BaseModel):
    prompt: str
    provider: str = "mock"
    model: str | None = None
    role: str | None = None
    claim_id: str = "adhoc/ask/0"
    idem: str | None = None


class ResumeReq(BaseModel):
    claim_id: str
    provider: str = "mock"
    model: str | None = None


def _role_with_provider(role_path: str | None, provider: str, model: str | None) -> Any:
    role = load_role(role_path)
    default_model = "mock" if provider in ("mock", "echo") else role.provider.model
    prov = ProviderConfig(provider=provider, model=model or default_model)
    return role.model_copy(update={"provider": prov})


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "hypercell-conductor"}


@app.post("/ask")
async def ask(req: AskReq) -> dict[str, Any]:
    role = _role_with_provider(req.role, req.provider, req.model)
    cell = build_cell(_home(), req.claim_id, role)
    text = await cell.ask(req.prompt, idem=req.idem)
    return {"claim_id": req.claim_id, "text": text}


@app.post("/resume")
async def resume(req: ResumeReq) -> dict[str, Any]:
    role = _role_with_provider(None, req.provider, req.model)
    cell = build_cell(_home(), req.claim_id, role)
    text = await cell.resume_pending()
    return {"claim_id": req.claim_id, "text": text, "resumed": text is not None}


@app.get("/fleet")
async def fleet() -> dict[str, Any]:
    home = Path(_home())
    claims: list[str] = []
    if home.exists():
        for p in home.rglob("ledger.jsonl"):
            claims.append(str(p.parent.relative_to(home)).replace("\\", "/"))
    return {"fleet": sorted(claims)}
