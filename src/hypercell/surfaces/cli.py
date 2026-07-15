"""hc — the fleet-commander CLI (P0). Command the fabric over SSH.

  hc ask "..." [--provider mock] [--model M] [--role FILE] [--claim ID] [--idem K]
  hc resume --claim ID [--provider mock]
  hc fleet [ls]
  hc provider set NAME
"""
from __future__ import annotations

import asyncio
import os
from pathlib import Path

import typer

from ..cell.runtime import build_cell, load_role
from ..common.types import ProviderConfig

app = typer.Typer(no_args_is_help=True, add_completion=False, help="hypercell — command a fleet of AI cells.")


def _home() -> str:
    return os.environ.get("HYPERCELL_HOME", str(Path(".hypercellstate")))


@app.command()
def ask(
    prompt: str = typer.Argument(..., help="the prompt / command for the cell"),
    provider: str = typer.Option("mock", "--provider", "-p", help="deepseek|cerebras|glm|kimi|qwen|grok|openai|mock"),
    model: str | None = typer.Option(None, "--model", "-m"),
    role: str | None = typer.Option(None, "--role", help="path to a role manifest yaml"),
    claim: str = typer.Option("adhoc/ask/0", "--claim", help="stable claim-id: run/role/index"),
    idem: str | None = typer.Option(None, "--idem", help="idempotency key (exactly-once)"),
) -> None:
    r = load_role(role)
    default_model = "mock" if provider in ("mock", "echo") else r.provider.model
    r = r.model_copy(update={"provider": ProviderConfig(provider=provider, model=model or default_model)})
    cell = build_cell(_home(), claim, r)
    typer.echo(asyncio.run(cell.ask(prompt, idem=idem)))


@app.command()
def resume(
    claim: str = typer.Option(..., "--claim", help="the claim-id to resume"),
    provider: str = typer.Option("mock", "--provider", "-p"),
    model: str | None = typer.Option(None, "--model", "-m"),
) -> None:
    r = load_role(None)
    r = r.model_copy(update={"provider": ProviderConfig(provider=provider, model=model or "mock")})
    cell = build_cell(_home(), claim, r)
    out = asyncio.run(cell.resume_pending())
    typer.echo(out if out is not None else "(nothing pending to resume)")


@app.command("fleet")
def fleet(action: str = typer.Argument("ls", help="ls")) -> None:
    home = Path(_home())
    claims: list[str] = []
    if home.exists():
        for p in home.rglob("ledger.jsonl"):
            claims.append(str(p.parent.relative_to(home)).replace("\\", "/"))
    if not claims:
        typer.echo("(no cells yet)")
        return
    for c in sorted(claims):
        typer.echo(c)


@app.command("provider")
def provider(action: str = typer.Argument("show"), name: str = typer.Argument("")) -> None:
    typer.echo(
        "Set a provider per cell with --provider, or in a role manifest's provider.provider. "
        "Keys live in .env (see .env.example). Swapping is config, not code."
    )


if __name__ == "__main__":
    app()
