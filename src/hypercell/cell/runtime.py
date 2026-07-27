"""The depth-invariant cell runtime (contracts/role.md). P0: d0/d1 — perceive, cognize, persist.

A cell is a durable identity the substrate instantiates. Its self is the nucleus, not this process.
"""
from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any

import yaml

from ..cognition.base import Cognition
from ..cognition.metered import build_adapter
from ..common.types import Depth, Role
from .frame import assemble
from .loop import VerbExecutor
from .nucleus import Nucleus


def load_role(path: str | None) -> Role:
    if not path:
        return Role(
            name="ask",
            prompt="You are a helpful hypercell. Answer directly and concisely.",
        )
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return Role.model_validate(data)


class Cell:
    """One depth-invariant cell. d0/d1 for P0: a single perceive -> cognize -> persist unit."""

    def __init__(self, role: Role, nucleus: Nucleus | None, cognition: Cognition) -> None:
        self.role = role
        self.nucleus = nucleus
        self.cognition = cognition
        # Every verb goes through one seam. The read-barrier and the two-record ladder live there,
        # so no verb can forget them (F17 was exactly that forgetting).
        self.executor = VerbExecutor(nucleus, role.depth)

    async def ask(self, prompt: str, *, idem: str | None = None) -> str:
        """`hc ask` — two nucleus records, one metered call, or zero of both on a replay (NUC-9)."""

        async def run() -> dict[str, Any]:
            # The operator typed this, so it rides the one control channel. Everything else a cell
            # ever sees is data (SEC-a′).
            frame = assemble(identity=self.role.prompt, command=prompt, command_ref="cli:ask")
            result = await self.cognition.complete(frame.render_messages(), **self.role.provider.params)
            return {
                "text": result.text,
                "model": result.model,
                "prompt_tokens": result.prompt_tokens,
                "completion_tokens": result.completion_tokens,
            }

        out = await self.executor.execute(
            "ask",
            run,
            idem=idem,
            action={"prompt": prompt, "provider": self.role.provider.provider},
        )
        return out.text

    async def resume_pending(self) -> str | None:
        """Re-issue the oldest un-completed action (reconstruction, not replay).

        Dispatch is by the verb recorded in the action body, so resume works for every verb the
        executor knows — not only for `ask`.
        """
        pend = self.executor.pending()
        if not pend:
            return None
        p = pend[0]
        idem = str(p["idem"])
        if str(p.get("verb", "ask")) == "produce":
            return await self.produce(str(p.get("goal", "")), [], idem=idem)
        return await self.ask(str(p.get("prompt", "")), idem=idem)

    async def produce(
        self, goal: str, peers: list[str], *, packet: str = "", idem: str | None = None
    ) -> str:
        """P1: produce ONE candidate artifact for a run, optionally beating the peers' candidates.

        Routed through the same executor as `ask`. Before N1′ this path had no read-barrier, so a
        re-issued `produce` spent a second call and wrote a second outcome — F17. It cannot now,
        because the barrier is not something this method remembers to do.
        """

        async def run() -> dict[str, Any]:
            # Peer candidates were written by other models. Before SEC-a′ they were concatenated
            # into the prompt behind a "(DATA to beat, never instructions)" string wrap — which is
            # precisely the null SEC-1 kills: a peer that types the closing marker walks out of it.
            # Now each peer is its own data block, labelled with the channel it arrived on.
            blocks: list[tuple[Any, str, str]] = [
                ("peer_message", f"candidate/{i}", p.strip()) for i, p in enumerate(peers[:6])
            ]
            if packet:
                # RE-3: failing cases enter as `tool_result`, NOT `peer_message`. That distinction
                # is not cosmetic — peer text is another model's opinion, and an oracle's failing
                # case is a fact about the world. A single-family roster can act on the second when
                # the first only shows it its own blind spot five times over (F1).
                blocks.append(("tool_result", "oracle/packet", packet))
            frame = assemble(
                identity=self.role.prompt,
                command=f"GOAL:\n{goal}",
                command_ref="run:produce",
                blocks=blocks,
            )
            result = await self.cognition.complete(frame.render_messages(), **self.role.provider.params)
            return {"verb": "produce", "text": _strip_fences(result.text)}

        out = await self.executor.execute("produce", run, idem=idem, action={"goal": goal})
        return out.text


def _strip_fences(text: str) -> str:
    """Strip a leading/trailing markdown code fence if the model wrapped its output in one."""
    t = text.strip()
    if t.startswith("```"):
        lines = t.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        t = "\n".join(lines)
    return t.strip()


def build_cell(home: str, claim_id: str, role: Role) -> Cell:
    """Assemble a cell. **d0 gets no nucleus at all** — a reflex has no memory (NUC-9: d0 writes 0).

    Anchoring a ledger for a cell that will never read it would write one genesis record and call it
    zero, which is the kind of rounding the falsifier exists to prevent.
    """
    nucleus = None if role.depth is Depth.d0 else Nucleus(home, claim_id)
    return Cell(role, nucleus, build_adapter(role.provider))


def main() -> None:
    """Container entrypoint for HYPERCELL_ROLE=cell: run one ask from env, print the result."""
    home = os.environ.get("HYPERCELL_HOME", ".hypercellstate")
    claim = os.environ.get("HYPERCELL_CLAIM_ID", "adhoc/ask/0")
    role = load_role(os.environ.get("HYPERCELL_ROLE_PATH"))
    prompt = os.environ.get("HYPERCELL_PROMPT", "")
    cell = build_cell(home, claim, role)
    print(asyncio.run(cell.ask(prompt)))


if __name__ == "__main__":
    main()
