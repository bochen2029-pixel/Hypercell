"""The nucleus: a cell's private, persistent self (contracts/nucleus.md).

Ledger (append-only JSONL) is truth; index (SQLite) is a disposable render, rebuildable from the ledger.
Identity binds to the stable claim-id, not the process. Resume is reconstruction + idempotency, never
deterministic replay.
"""
from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any

from ..common import clock


class Nucleus:
    def __init__(self, home: Path | str, claim_id: str) -> None:
        self.claim_id = claim_id
        # claim_id is "run/role/index" -> nested dirs under home (the volume binding).
        self.dir = Path(home) / claim_id
        self.dir.mkdir(parents=True, exist_ok=True)
        self.ledger_path = self.dir / "ledger.jsonl"
        self.index_path = self.dir / "index.db"
        self._db = sqlite3.connect(self.index_path)
        self._db.execute("PRAGMA journal_mode=WAL")
        self._init_index()
        # rebuild the index from the ledger on open, so a stale/missing index is never trusted.
        if self.ledger_path.exists():
            self.rebuild()
        self._seq = self._max_seq()

    def _init_index(self) -> None:
        self._db.executescript(
            """
            CREATE TABLE IF NOT EXISTS ledger(
              seq INTEGER PRIMARY KEY, ts TEXT, kind TEXT, idem TEXT, body TEXT, refs TEXT);
            CREATE INDEX IF NOT EXISTS idx_idem ON ledger(idem);
            CREATE INDEX IF NOT EXISTS idx_kind ON ledger(kind);
            """
        )
        self._db.commit()

    def _max_seq(self) -> int:
        row = self._db.execute("SELECT MAX(seq) FROM ledger").fetchone()
        return int(row[0]) if row and row[0] is not None else 0

    def append(
        self,
        kind: str,
        body: Any,
        *,
        idem: str | None = None,
        refs: list[int] | None = None,
    ) -> int:
        """Append one record to the ledger (truth, fsync'd) then mirror into the index."""
        self._seq += 1
        rec = {
            "seq": self._seq,
            "ts": clock.now_iso(),
            "kind": kind,
            "idem": idem,
            "body": body,
            "refs": refs or [],
        }
        with open(self.ledger_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
        self._db.execute(
            "INSERT INTO ledger(seq,ts,kind,idem,body,refs) VALUES(?,?,?,?,?,?)",
            (
                rec["seq"],
                rec["ts"],
                kind,
                idem,
                json.dumps(body, ensure_ascii=False),
                json.dumps(refs or []),
            ),
        )
        self._db.commit()
        return self._seq

    def checkpoint(self, state: dict[str, Any]) -> int:
        return self.append("checkpoint", state)

    def resume(self) -> dict[str, Any] | None:
        """The last checkpointed working state (context reconstruction on wake)."""
        row = self._db.execute(
            "SELECT body FROM ledger WHERE kind='checkpoint' ORDER BY seq DESC LIMIT 1"
        ).fetchone()
        if not row:
            return None
        state: dict[str, Any] = json.loads(row[0])
        return state

    def outcome_for(self, idem: str) -> Any | None:
        """The completed outcome for an idempotency key, or None. This is the exactly-once guard."""
        row = self._db.execute(
            "SELECT body FROM ledger WHERE kind='outcome' AND idem=? ORDER BY seq DESC LIMIT 1",
            (idem,),
        ).fetchone()
        return json.loads(row[0]) if row else None

    def pending(self) -> dict[str, Any] | None:
        """An action whose outcome never landed (the crash-mid-run case). None if all settled."""
        rows = self._db.execute(
            "SELECT idem, body FROM ledger WHERE kind='action' ORDER BY seq"
        ).fetchall()
        for idem, body in rows:
            if idem and self.outcome_for(idem) is None:
                b: dict[str, Any] = json.loads(body)
                b["idem"] = idem
                return b
        return None

    def rebuild(self) -> int:
        """Regenerate the index from the ledger alone (no model). Proves the index is derivable."""
        self._db.execute("DELETE FROM ledger")
        n = 0
        with open(self.ledger_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                r = json.loads(line)
                self._db.execute(
                    "INSERT OR REPLACE INTO ledger(seq,ts,kind,idem,body,refs) VALUES(?,?,?,?,?,?)",
                    (
                        r["seq"],
                        r["ts"],
                        r["kind"],
                        r.get("idem"),
                        json.dumps(r["body"], ensure_ascii=False),
                        json.dumps(r.get("refs", [])),
                    ),
                )
                n += 1
        self._db.commit()
        self._seq = self._max_seq()
        return n

    def close(self) -> None:
        self._db.close()
