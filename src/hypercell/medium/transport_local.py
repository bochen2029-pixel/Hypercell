"""The Medium — local durable transport (contracts/wire.md). Single-node SQLite log.

hypercell owns the protocol; the transport is rented and pluggable. P0/P1 use this local log; P3 swaps
to NATS/JetStream behind the same interface. The append-only log is the stigmergic blackboard.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from ..common import clock


class LocalMedium:
    def __init__(self, home: Path | str) -> None:
        self.dir = Path(home) / "_medium"
        self.dir.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(self.dir / "medium.db")
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute(
            """CREATE TABLE IF NOT EXISTS messages(
                 seq INTEGER PRIMARY KEY, ts TEXT, culture TEXT, sender TEXT, recipient TEXT,
                 type TEXT, round INTEGER, body TEXT, artifact TEXT)"""
        )
        self._db.commit()

    def post(
        self,
        culture: str,
        sender: str,
        msg_type: str,
        *,
        body: Any = None,
        recipient: str | None = None,
        round: int | None = None,
        artifact: dict[str, Any] | None = None,
    ) -> int:
        cur = self._db.execute(
            "INSERT INTO messages(ts,culture,sender,recipient,type,round,body,artifact) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (
                clock.now_iso(),
                culture,
                sender,
                recipient,
                msg_type,
                round,
                json.dumps(body, ensure_ascii=False) if body is not None else None,
                json.dumps(artifact, ensure_ascii=False) if artifact else None,
            ),
        )
        self._db.commit()
        return int(cur.lastrowid or 0)

    def submissions(self, culture: str, round: int) -> list[dict[str, Any]]:
        rows = self._db.execute(
            "SELECT sender, body, artifact FROM messages "
            "WHERE culture=? AND type='submission' AND round=? ORDER BY seq",
            (culture, round),
        ).fetchall()
        out: list[dict[str, Any]] = []
        for sender, body, artifact in rows:
            out.append(
                {
                    "sender": sender,
                    "body": json.loads(body) if body else None,
                    "artifact": json.loads(artifact) if artifact else None,
                }
            )
        return out

    def replay(self, culture: str) -> list[dict[str, Any]]:
        rows = self._db.execute(
            "SELECT seq, ts, sender, type, round, body FROM messages WHERE culture=? ORDER BY seq",
            (culture,),
        ).fetchall()
        return [
            {
                "seq": s,
                "ts": t,
                "sender": snd,
                "type": ty,
                "round": rd,
                "body": json.loads(b) if b else None,
            }
            for s, t, snd, ty, rd, b in rows
        ]

    def close(self) -> None:
        self._db.close()
