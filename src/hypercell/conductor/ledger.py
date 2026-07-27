"""The conductor-private escrow ledger — RESERVE / COMMIT / RELEASE (the C-4 ruling's home).

**The null is a RAM-held `committed` total** — the live L8 leak. A counter in a process is a claim
about money that dies with the process, and what dies with it is always the *spent* side: on resume
the fabric remembers its cap and forgets its spending, so it grants itself the whole budget again.
The failure is silent, it is in the generous direction, and it happens exactly when someone is
already having a bad day.

So spend is a **fold**. Every reservation event is appended here and fsynced before the escrow acts
on it, and the live reservation table is rebuilt by replaying this file. Three consequences worth
stating:

* **Durable-before-act.** The record lands before the money is considered held. A crash between the
  two costs a reservation that is held-but-unused, which the sweeper reconciles. The other order
  would cost a reservation that was used but never recorded, and nothing can recover that.
* **The fold is the truth, the table is a cache.** `Escrow.committed()` reads the table because it
  is fast, but the table is only ever what the records say. There is no path that writes one without
  the other.
* **Conductor-private.** This is not the fleet log and never crosses the Medium: it holds the
  operator's money, not the run's history. (`common/ledger.py` is the *chain engine*, a different
  thing that happens to share a noun — see the LEDGER-HOMES note in BUILD.md §10.)
"""
from __future__ import annotations

import json
import os
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from ..common import clock

RecordKind = Literal["reserve", "commit", "release", "draw", "sweep", "reconcile"]


@dataclass
class EscrowState:
    """What a fold over the records says is true right now."""

    reservations: dict[str, dict[str, Any]] = field(default_factory=dict)
    #: Set when the fold saw records from a previous process — i.e. this is a RESUME.
    resumed: bool = False
    replayed: int = 0


class EscrowLedger:
    """Append-only, fsync'd, fold-rebuildable. The only durable home for reservation events."""

    def __init__(self, home: Path | str, *, fsync: bool = True) -> None:
        self.dir = Path(home) / "_conductor"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.path = self.dir / "escrow.jsonl"
        # A test escrow that fsyncs 16×N times is slow enough that nobody runs the drill. The
        # DEFAULT is durable; turning it off is a decision a caller has to type.
        self.fsync = fsync
        self._fh = open(self.path, "a", encoding="utf-8")

    def append(self, kind: RecordKind, **fields: Any) -> dict[str, Any]:
        """Write one event and make it durable BEFORE the caller acts on it."""
        record: dict[str, Any] = {"kind": kind, "ts": clock.now_iso(), **fields}
        self._fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        self._fh.flush()
        if self.fsync:
            os.fsync(self._fh.fileno())
        return record

    def records(self) -> Iterator[dict[str, Any]]:
        """Every event, oldest first. A torn final line is dropped — a half-record is not a record."""
        if not self.path.exists():
            return
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                if not line.endswith("\n"):
                    break
                text = line.strip()
                if not text:
                    continue
                try:
                    yield json.loads(text)
                except json.JSONDecodeError:
                    break

    def fold(self) -> EscrowState:
        """Rebuild the reservation table from the records alone. No RAM state survives a restart.

        `resumed` is the flag ECON-L8 turns on: a fold that found prior records means this process
        did not open the budget, it *inherited* one, and it may not reserve until it has reconciled
        what it inherited.
        """
        state = EscrowState()
        for rec in self.records():
            state.replayed += 1
            kind, rid = str(rec.get("kind")), str(rec.get("resv_id", ""))
            if kind == "reserve":
                state.reservations[rid] = {
                    "resv_id": rid, "scope": rec.get("scope", "fleet"), "cls": rec.get("cls", "res:sync"),
                    "worst": float(rec.get("worst", 0.0)), "committed": 0.0, "state": "HELD",
                    "lane": rec.get("lane", ""), "holder": rec.get("holder", ""),
                    "opened_at": rec.get("opened_at", 0.0), "ttl_s": float(rec.get("ttl_s", 300.0)),
                    "batch_id": str(rec.get("batch_id", "")),
                }
            elif kind in ("commit", "draw") and rid in state.reservations:
                state.reservations[rid]["committed"] += float(rec.get("usd", 0.0))
                if kind == "commit":
                    state.reservations[rid]["state"] = "SETTLED"
            elif kind == "release" and rid in state.reservations:
                state.reservations[rid]["state"] = "RELEASED"
        state.resumed = state.replayed > 0
        return state

    def close(self) -> None:
        self._fh.close()
