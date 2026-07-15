"""The depth-invariant cell runtime (contracts/role.md). P0: d0/d1 — perceive, cognize, persist.

A cell is a durable identity the substrate instantiates. Its self is the nucleus, not this process.
"""
from __future__ import annotations

import asyncio
import os
from pathlib import Path

import yaml

from ..cognition.base import Cognition
from ..cognition.registry import build_cognition
from ..common import ids
from ..common.types import Role
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

    def __init__(self, role: Role, nucleus: Nucleus, cognition: Cognition) -> None:
        self.role = role
        self.nucleus = nucleus
        self.cognition = cognition

    async def ask(self, prompt: str, *, idem: str | None = None) -> str:
        idem = idem or ids.new_id("act_")
        # exactly-once: a completed act (e.g. seen again on resume) returns its stored outcome.
        done = self.nucleus.outcome_for(idem)
        if done is not None:
            return str(done.get("text", ""))

        self.nucleus.append("percept", {"prompt": prompt}, idem=idem)
        self.nucleus.append(
            "action",
            {"verb": "ask", "prompt": prompt, "provider": self.role.provider.provider},
            idem=idem,
        )
        self.nucleus.checkpoint({"state": "pending", "idem": idem})

        # drill hook: die AFTER the pending checkpoint, BEFORE the outcome (crash-mid-run).
        crash = os.environ.get("HYPERCELL_CRASH_BEFORE_OUTCOME")
        if crash and crash in ("1", idem):
            raise SystemExit("drill: crashed before outcome")

        messages = [
            {"role": "system", "content": self.role.prompt},
            {"role": "user", "content": prompt},
        ]
        result = await self.cognition.complete(messages, **self.role.provider.params)
        self.nucleus.append(
            "outcome",
            {
                "text": result.text,
                "model": result.model,
                "prompt_tokens": result.prompt_tokens,
                "completion_tokens": result.completion_tokens,
            },
            idem=idem,
        )
        self.nucleus.checkpoint({"state": "done", "idem": idem})
        return result.text

    async def resume_pending(self) -> str | None:
        """Re-issue any un-completed action from the nucleus (reconstruction, not replay)."""
        p = self.nucleus.pending()
        if p is None:
            return None
        return await self.ask(str(p.get("prompt", "")), idem=str(p.get("idem")))


def build_cell(home: str, claim_id: str, role: Role) -> Cell:
    return Cell(role, Nucleus(home, claim_id), build_cognition(role.provider))


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
