"""hc talk — the natural-language commander. Command the fleet in plain English.

You say "spin up 6 agents and figure out X" or "fan out and nail this"; a router model turns
it into a fleet action (fanout / converge / ask / status) and runs it, then reports back. This
is the Homeworld-fleet-commander surface: talk, don't memorize flags.
"""
from __future__ import annotations

import json
import re
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any

from ..cognition.registry import build_cognition
from ..common import ids
from ..common.types import ProviderConfig

_CHAT = (
    "You are hypercell, a sovereign swarm-compute fabric the operator commands like a fleet. "
    "Reply to the operator in one or two short, warm sentences. If they are just chatting, chat "
    "back and nudge them: they can say things like 'spin up 6 agents to research X'."
)


def _n_from_text(text: str) -> int | None:
    """Pull the agent/cell count the operator actually said ('spin up 2 agents', '6 cells')."""
    m = re.search(r"(\d{1,3})\s*(?:agents?|cells?|explorers?|workers?)", text, re.I)
    if not m:
        m = re.search(r"(?:spin\s*up|fan\s*out|spawn|launch|deploy)\s*(\d{1,3})", text, re.I)
    return int(m.group(1)) if m else None


def _port_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        return s.connect_ex((host, port)) == 0


def _ensure_viewer(home: str, port: int = 8799) -> str:
    """Make sure the Medium exists and the viewer is up, so the operator watches live."""
    from ..medium.transport_local import LocalMedium

    LocalMedium(home).close()  # creates <home>/_medium/medium.db if absent
    url = f"http://127.0.0.1:{port}/"
    if _port_open("127.0.0.1", port):
        return f"viewer already up -> {url}"
    viewer = Path(__file__).resolve().parents[3] / "tools" / "medium_viewer.py"
    if not viewer.exists():
        return f"(viewer not found at {viewer}; run it manually)"
    try:
        flags = subprocess.CREATE_NEW_PROCESS_GROUP if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP") else 0
        subprocess.Popen(
            [sys.executable, str(viewer), "--home", home, "--port", str(port)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=flags,
        )
        return f"viewer launched -> {url}  (watch the fleet here)"
    except Exception as e:
        return f"(couldn't auto-launch viewer: {e}; run: python tools/medium_viewer.py)"

_SYSTEM = """You are the command interpreter for hypercell, a sovereign swarm-compute fabric.
The operator commands a fleet of AI "cells" by talking to you in plain English. Translate each
message into EXACTLY ONE action, returned as a single JSON object (no prose around it):

- "fanout": spin up N cells that each independently answer a goal; a coordinator then
  synthesizes. Use for brainstorming, research, exploration, or any "spin up / fan out N agents
  to do X". params: {"goal": str, "n": int}. Default n=5.
- "converge": N cells iteratively COMPETE to solve a checkable task, scored to a champion by an
  external oracle (a shell command). Use ONLY when the operator gives or clearly implies a
  verifiable checker. params: {"goal": str, "n": int, "rounds": int, "oracle": str}.
- "ask": one cell answers quickly. params: {"prompt": str}.
- "status": report what the fleet / Medium is doing. params: {}.
- "chat": just reply or ask a clarifying question; no fleet action. params: {"say": str}.

Always include a short first-person "say" narrating what you're about to do (e.g. "Spinning up
6 cells on that."). Prefer "fanout" whenever the operator wants to spin up / fan out agents on
an open-ended task. Return ONLY the JSON object."""


def _parse(text: str) -> dict[str, Any]:
    t = text.strip()
    if "```" in t:  # unwrap a fenced block if the model added one
        parts = t.split("```")
        t = parts[1] if len(parts) >= 2 else t
        if t.lstrip().lower().startswith("json"):
            t = t.lstrip()[4:]
    a, b = t.find("{"), t.rfind("}")
    if a >= 0 and b > a:
        try:
            obj = json.loads(t[a : b + 1])
            if isinstance(obj, dict):
                return obj
        except Exception:
            pass
    return {"action": "chat", "say": text.strip()}


async def _route(router: Any, user: str) -> dict[str, Any]:
    res = await router.complete(
        [{"role": "system", "content": _SYSTEM}, {"role": "user", "content": user}],
        temperature=0,
    )
    return _parse(res.text)


async def talk_loop(home: str, provider: str, model: str, watch: bool = True) -> None:
    try:  # LLM output (and our own glyphs) is UTF-8; don't die on a cp1252 console.
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    except Exception:
        pass
    router = build_cognition(ProviderConfig(provider=provider, model=model))
    print(f"hypercell commander  |  provider={provider}  |  home={home}")
    if watch:
        print(f"  {_ensure_viewer(home)}")
    print('Talk to your fleet in plain English. e.g. "spin up 6 agents to research X".')
    print("(Ctrl-C or 'exit' to quit)\n")

    while True:
        try:
            user = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nbye.")
            return
        if not user:
            continue
        if user.lower() in ("exit", "quit", "bye"):
            print("bye.")
            return

        try:
            act = await _route(router, user)
        except Exception as e:
            print(f"hypercell> (couldn't reach the router: {e})\n")
            continue

        action = str(act.get("action") or "chat").lower()

        # chit-chat: actually reply, so it never feels dead.
        if action == "chat":
            try:
                r = await router.complete(
                    [{"role": "system", "content": _CHAT}, {"role": "user", "content": user}],
                    temperature=0.6,
                )
                print(f"hypercell> {r.text.strip()}\n")
            except Exception as e:
                print(f"hypercell> (here, but couldn't compose a reply: {e})\n")
            continue

        say = str(act.get("say") or "")
        if say:
            print(f"hypercell> {say}")
        try:
            await _dispatch(action, act, user, home, provider, model)
        except Exception as e:
            print(f"hypercell> (that action failed: {e})")
        print()


async def _dispatch(
    action: str, act: dict[str, Any], user: str, home: str, provider: str, model: str
) -> None:
    if action == "chat":
        return

    if action == "ask":
        from ..cell.runtime import build_cell, load_role

        r = load_role(None).model_copy(
            update={"provider": ProviderConfig(provider=provider, model=model)}
        )
        cell = build_cell(home, "adhoc/ask/0", r)
        print(await cell.ask(str(act.get("prompt", user))))
        return

    if action == "fanout":
        from ..conductor.engine.fanout import run_fanout

        rid = ids.short_id(6)
        n = max(1, min(int(act.get("n") or _n_from_text(user) or 5), 30))
        goal = str(act.get("goal", user))
        print(f"  run {rid}: spinning up {n} cells over the Medium  (watch: http://127.0.0.1:8799)")

        def prog(kind: str, data: dict[str, Any]) -> None:
            if kind == "spawned":
                print(f"    + {data['cell']} spawned", flush=True)
            elif kind == "done":
                print(f"    * {data['cell']} answered ({data['chars']} chars)", flush=True)
            elif kind == "synthesizing":
                print("    ~ coordinator synthesizing the swarm...", flush=True)

        fres = await run_fanout(
            run_id=rid, goal=goal, home=home, provider=provider, model=model, n=n, on_event=prog
        )
        if fres.get("synthesis"):
            print(f"\n=== SYNTHESIS ({n} cells -> coordinator) ===\n{fres['synthesis']}")
        else:
            for a in fres["answers"]:
                print(f"\n[{a['cell']}]\n{a['answer']}")
        return

    if action == "converge":
        oracle = act.get("oracle")
        if not oracle:
            print(
                "  Converging needs an external checker (oracle). Give me one — e.g. "
                "'oracle: python oracles/ipv4_check.py' — or say 'fan out' to just brainstorm."
            )
            return
        from ..conductor.engine.topology import run_tournament

        rid = ids.short_id(6)
        n = max(1, min(int(act.get("n") or _n_from_text(user) or 6), 30))
        rounds = int(act.get("rounds", 3) or 3)
        print(f"  run {rid}: tournament, {n} cells x {rounds} rounds, oracle='{oracle}'...")
        tres = await run_tournament(
            run_id=rid, goal=str(act.get("goal", user)), oracle_cmd=str(oracle),
            home=home, provider=provider, model=model, n=n, rounds=rounds,
        )
        if tres.champion is not None:
            flag = "CONVERGED" if tres.converged else "best-so-far"
            print(f"\nchampion {tres.champion.cell} score={tres.champion.score:.4f} [{flag}] -> {tres.champion.path}")
        else:
            print("\nno valid champion (all candidates INVALID).")
        return

    if action == "status":
        from ..medium.transport_local import LocalMedium

        med = LocalMedium(home)
        try:
            recent = med._db.execute(
                "SELECT culture, count(*), max(round), max(ts) FROM messages "
                "GROUP BY culture ORDER BY max(ts) DESC LIMIT 8"
            ).fetchall()
        finally:
            med.close()
        if not recent:
            print("  fleet idle — no runs yet.")
        else:
            print("  recent runs:")
            for cult, msgs, rnd, ts in recent:
                print(f"    {cult}: {msgs} messages, {rnd or 0} rounds (last {ts})")
        return

    print(f"  (unknown action '{action}')")
