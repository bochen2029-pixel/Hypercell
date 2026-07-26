"""hc — the fleet-commander CLI (P0). Command the fabric over SSH.

  hc ask "..." [--provider mock] [--model M] [--role FILE] [--claim ID] [--idem K]
  hc resume --claim ID [--provider mock]
  hc fleet [ls]
  hc provider set NAME
  hc preflight [--json]
"""
from __future__ import annotations

import asyncio
import os
from pathlib import Path

import typer

from ..cell.runtime import build_cell, load_role
from ..common import ids
from ..common.types import ProviderConfig

app = typer.Typer(no_args_is_help=True, add_completion=False, help="hypercell — command a fleet of AI cells.")


@app.callback()
def _bootstrap() -> None:
    """Load .env (provider keys) before any command; existing env vars win."""
    from ..common.config import load_env

    load_env()


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
def verify(
    claim: str = typer.Option(..., "--claim", help="the claim-id whose nucleus chain to verify"),
) -> None:
    """Re-derive a nucleus hash chain (NUC-1). On tamper, names the FIRST bad seq — the tamper point."""
    from ..cell.nucleus import Nucleus

    n = Nucleus(_home(), claim)
    try:
        report = n.verify()
        if report.ok:
            typer.echo(f"chain OK  {claim}  ({report.checked} records)  head={n.head_hash[:23]}...")
            raise typer.Exit(0)
        where = f" at seq {report.first_bad_seq}" if report.first_bad_seq is not None else ""
        typer.echo(f"chain BROKEN  {claim}{where}\n  {report.reason}")
        raise typer.Exit(1)
    finally:
        n.close()


@app.command()
def preflight(
    as_json: bool = typer.Option(False, "--json", help="emit the status{kind:preflight} body instead of text"),
) -> None:
    """Probe the box before trusting it with gold (ARCHITECTURE §11; falsifier PREFLIGHT-LITE-1).

    Exit code is the verdict, so CI and the day-1 golden path can gate on it:
    0 = GREEN, 1 = DEGRADED (runs proceed, labelled), 2 = RED (a spine guard failed; the fabric halts).
    """
    import json as _json

    from ..substrate.k3s import run_preflight
    from ..substrate.preflight import render

    report = run_preflight(_home())
    typer.echo(_json.dumps(report.as_status_body(), indent=2) if as_json else render(report))
    raise typer.Exit({"GREEN": 0, "DEGRADED": 1, "RED": 2}[report.verdict])


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


_DEFAULT_MODELS = {
    "deepseek": "deepseek-chat",
    "cerebras": "llama-3.3-70b",
    "openai": "gpt-4o-mini",
    "glm": "glm-4.5-flash",
    "kimi": "moonshot-v1-8k",
    "qwen": "qwen-plus",
    "grok": "grok-2",
}


def _default_model(provider: str) -> str:
    if provider in ("mock", "echo"):
        return "mock"
    return _DEFAULT_MODELS.get(provider, "default")


@app.command()
def run(
    topology: str = typer.Argument("tournament", help="tournament (P1)"),
    goal: str = typer.Option(..., "--goal", "-g", help="the shared goal"),
    oracle: str = typer.Option("", "--oracle", help="checker cmd for CHECKABLE tasks (else use --judge N)"),
    judge: int = typer.Option(0, "--judge", help="judge-panel size for OPEN tasks (0 = require --oracle)"),
    n: int = typer.Option(4, "--n", help="number of cells"),
    rounds: int = typer.Option(3, "--rounds"),
    provider: str = typer.Option("deepseek", "--provider", "-p"),
    model: str | None = typer.Option(None, "--model", "-m"),
    run_id: str | None = typer.Option(None, "--run"),
    diversify: bool = typer.Option(True, "--diversify/--identical", help="seed diversity (HC-4)"),
    target: float = typer.Option(1.0, "--target"),
) -> None:
    from ..conductor.engine.topology import run_tournament

    if topology != "tournament":
        typer.echo(f"topology '{topology}' is not implemented yet (P1 = tournament).")
        raise typer.Exit(2)
    if not oracle and judge <= 0:
        typer.echo("give a scorer: --oracle '<cmd>' for checkable tasks, or --judge N for open tasks.")
        raise typer.Exit(2)
    if judge > 0 and target >= 1.0:
        target = 0.9  # judges rarely give a perfect 10; converge at a strong-consensus bar
    rid = run_id or ids.short_id(6)
    res = asyncio.run(
        run_tournament(
            run_id=rid, goal=goal, oracle_cmd=oracle, home=_home(),
            provider=provider, model=model or _default_model(provider),
            n=n, rounds=rounds, target=target, diversify=diversify, judge=judge,
        )
    )
    typer.echo(
        f"run {rid}: {res.rounds_run} rounds, {len(res.history)} candidates, "
        f"{'diverse' if diversify else 'identical'} roster of {n}"
        + (f", judged by a panel of {judge}" if judge else "")
    )
    if res.champion is not None:
        flag = "CONVERGED" if res.converged else "best-so-far"
        typer.echo(
            f"champion: {res.champion.cell} @ round {res.champion.round} "
            f"score={res.champion.score:.4f} [{flag}]"
        )
        typer.echo(f"artifact: {res.champion.path}")
    else:
        typer.echo("no valid champion (all candidates were INVALID)")


@app.command()
def apply(file: str = typer.Option(..., "-f", "--file", help="a run manifest yaml")) -> None:
    import yaml

    from ..common.types import RunManifest
    from ..conductor.engine.topology import run_tournament

    data = yaml.safe_load(Path(file).read_text(encoding="utf-8"))
    m = RunManifest.model_validate(data)
    provider, model, base_prompt = "deepseek", "deepseek-chat", None
    if m.roster:
        rr = load_role(m.roster[0].role)
        provider, model, base_prompt = rr.provider.provider, rr.provider.model, rr.prompt
    n = sum(e.count for e in m.roster) or 4
    res = asyncio.run(
        run_tournament(
            run_id=m.run_id, goal=m.goal, oracle_cmd=str(m.oracle.get("cmd", "")), home=_home(),
            provider=provider, model=model, n=n, rounds=m.termination.max_rounds,
            target=float(m.oracle.get("target", 1.0)), stable_k=m.termination.stable_k,
            diversify=m.seed_diversity, base_prompt=base_prompt,
        )
    )
    if res.champion is not None:
        typer.echo(
            f"run {m.run_id}: champion {res.champion.cell} score={res.champion.score:.4f} "
            f"({'converged' if res.converged else 'best-so-far'}) -> {res.champion.path}"
        )
    else:
        typer.echo(f"run {m.run_id}: no valid champion")


@app.command()
def replay(run: str = typer.Option(..., "--run", help="the run id to replay")) -> None:
    from ..medium.bus import open_medium

    med = open_medium(_home())
    for msg in med.replay(f"run-{run}"):
        rd = f"r{msg['round']}" if msg["round"] else "-"
        typer.echo(f"[{msg['seq']:>3}] {rd:>3} {msg['sender']:<10} {msg['type']}")
    med.close()


@app.command()
def drive(
    goal: str = typer.Option(..., "--goal", "-g", help="the shared goal"),
    oracle: str = typer.Option(..., "--oracle", help="external falsifier cmd"),
    arms: int = typer.Option(4, "--arms", help="number of approaches (cells)"),
    max_steps: int = typer.Option(12, "--max-steps"),
    provider: str = typer.Option("deepseek", "--provider", "-p"),
    model: str | None = typer.Option(None, "--model", "-m"),
    usd_cap: float = typer.Option(1.0, "--usd-cap", help="budget hard-stop (HC-8)"),
    run_id: str | None = typer.Option(None, "--run"),
    target: float = typer.Option(1.0, "--target"),
) -> None:
    """The self-driving machine: UCB-scheduled, budget-bounded convergence."""
    from ..conductor.engine.drive import run_drive

    rid = run_id or ids.short_id(6)
    res = asyncio.run(
        run_drive(
            run_id=rid, goal=goal, oracle_cmd=oracle, home=_home(),
            provider=provider, model=model or _default_model(provider),
            n_arms=arms, max_steps=max_steps, usd_cap=usd_cap, target=target,
        )
    )
    typer.echo(
        f"drive {rid}: {res.steps} steps, spent ${res.spent_usd:.4f}, stopped={res.stopped_reason}"
    )
    if res.champion_arm is not None:
        flag = "CONVERGED" if res.converged else "best-so-far"
        typer.echo(f"champion: {res.champion_arm} score={res.champion_score:.4f} [{flag}]")


@app.command()
def talk(
    provider: str = typer.Option("deepseek", "--provider", "-p", help="the fleet's default provider"),
    model: str | None = typer.Option(None, "--model", "-m"),
    watch: bool = typer.Option(True, "--watch/--no-watch", help="auto-launch the live Medium viewer"),
) -> None:
    """Talk to your fleet in plain English — say 'spin up N agents to do X'. No flags to memorize."""
    from ..surfaces.commander import talk_loop

    asyncio.run(talk_loop(_home(), provider, model or _default_model(provider), watch=watch))


if __name__ == "__main__":
    app()
