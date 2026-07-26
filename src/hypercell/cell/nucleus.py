"""The nucleus: a cell's private, persistent self (contracts/nucleus.md).

The **ledger is truth**; the SQLite index is a disposable render, rebuilt from the ledger on every
open so a stale or missing index is never trusted (A13). Identity binds to the stable claim-id, not
to the process. Resume is reconstruction + idempotency, never deterministic replay.

Since N1′ the ledger is **hash-chained and genesis-anchored** (`common/ledger.py`): every record
chains to its predecessor, seq 1 carries the contract census, and `verify()` names the first record
that does not re-derive. Tamper-evidence is a property of the log now, not a promise in a doc.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from ..common.census import census as contract_census
from ..common.ledger import Durability, Ledger, VerifyReport
from .membrane import redact


class Nucleus:
    def __init__(self, home: Path | str, claim_id: str) -> None:
        self.claim_id = claim_id
        # claim_id is "run/role/index" -> nested dirs under home (the volume binding).
        self.dir = Path(home) / claim_id
        self.dir.mkdir(parents=True, exist_ok=True)
        self.ledger_path = self.dir / "ledger.jsonl"
        self.index_path = self.dir / "index.db"

        pre_existing = self.ledger_path.exists()
        self.ledger = Ledger(self.ledger_path, claim_id=claim_id)

        self._db = sqlite3.connect(self.index_path)
        # Explicit pragmas, not defaults: WAL for concurrent readers, a real busy_timeout so a
        # contended index waits instead of raising, and FULL so the render survives a hard kill.
        # (Guard G-DB-DURABLE exists because defaults are not a durability contract -- E3.)
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA synchronous=FULL")
        self._db.execute("PRAGMA busy_timeout=5000")
        self._init_index()

        if self.ledger.seq == 0:
            # A fresh nucleus is anchored at birth: seq 1, gold, carrying the census.
            self.ledger.genesis(contract_census())
        elif pre_existing and not self._has_genesis():
            # A pre-chain ledger from before N1'. It adopts the chain HONESTLY: earlier records stay
            # immutable-but-unhashed and the genesis says so, rather than back-dating hashes over
            # bytes nobody witnessed (the HONEST-EPOCH pattern, nucleus.md §1).
            self.ledger.adopt_chain(contract_census(), at_seq=self.ledger.seq + 1)

        self.rebuild()

    # ---------------------------------------------------------------- index (a render, not truth)

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

    def _has_genesis(self) -> bool:
        return any(r.get("kind") == "genesis" for r in self.ledger.records(hi=1))

    def _max_seq(self) -> int:
        row = self._db.execute("SELECT MAX(seq) FROM ledger").fetchone()
        return int(row[0]) if row and row[0] is not None else 0

    def rebuild(self) -> int:
        """Regenerate the index from the ledger alone (no model). Proves the index is derivable."""
        self._db.execute("DELETE FROM ledger")
        n = 0
        for r in self.ledger.records():
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
        return n

    # ---------------------------------------------------------------- writing

    def append(
        self,
        kind: str,
        body: Any,
        *,
        idem: str | None = None,
        refs: list[int] | None = None,
        durability: Durability = "standard",
    ) -> int:
        """Append one chained record to the ledger (truth), then mirror it into the index (render).

        Redaction runs HERE, before the ledger canonicalizes and hashes anything
        (L-REDACT-BEFORE-CANON). An append-only log cannot un-say a secret, so the only correct
        place to catch one is before the append.
        """
        body, secrets = redact(body)
        if secrets:
            # The redaction is itself a fact about the record — an auditor must be able to see that
            # something was removed, without the removed thing being recoverable.
            body = {"red": secrets, **body} if isinstance(body, dict) else body
        seq = self.ledger.append(kind, body, idem=idem, refs=refs, durability=durability)
        self._db.execute(
            "INSERT INTO ledger(seq,ts,kind,idem,body,refs) VALUES(?,?,?,?,?,?)",
            (
                seq,
                self._last_ts(seq),
                kind,
                idem,
                json.dumps(body, ensure_ascii=False),
                json.dumps(refs or []),
            ),
        )
        self._db.commit()
        return seq

    def _last_ts(self, seq: int) -> str:
        for r in self.ledger.records(lo=seq, hi=seq):
            return str(r["ts"])
        return ""

    def checkpoint(self, state: dict[str, Any]) -> int:
        """Working-state snapshot for long d1/d2 loops.

        NOT part of the adhoc ladder: `hc ask` is action + outcome and nothing else (NUC-9). Resume
        reconstructs from `pending()`, never from a checkpoint.
        """
        return self.append("checkpoint", state)

    # ---------------------------------------------------------------- reading

    def resume(self) -> dict[str, Any] | None:
        """The last checkpointed working state (context reconstruction on wake)."""
        row = self._db.execute(
            "SELECT body FROM ledger WHERE kind='checkpoint' ORDER BY seq DESC LIMIT 1"
        ).fetchone()
        if not row:
            return None
        state: dict[str, Any] = json.loads(row[0])
        return state

    def record(self, seq: int) -> dict[str, Any] | None:
        """One record by seq, off the index. The ref-closure walk leans on this being cheap."""
        row = self._db.execute(
            "SELECT seq, ts, kind, idem, body, refs FROM ledger WHERE seq=?", (seq,)
        ).fetchone()
        if not row:
            return None
        return {
            "seq": int(row[0]),
            "ts": row[1],
            "kind": row[2],
            "idem": row[3],
            "body": json.loads(row[4]),
            "refs": json.loads(row[5] or "[]"),
        }

    def records_of_kind(self, kind: str) -> list[dict[str, Any]]:
        rows = self._db.execute(
            "SELECT seq FROM ledger WHERE kind=? ORDER BY seq", (kind,)
        ).fetchall()
        return [r for r in (self.record(int(s[0])) for s in rows) if r is not None]

    def outcome_for(self, idem: str) -> Any | None:
        """**The read-barrier.** The completed outcome for an idem, or None. The exactly-once guard.

        Every verb consults this before spending a cognition call — see `cell/loop.py`, which is the
        one place that consultation happens.
        """
        row = self._db.execute(
            "SELECT body FROM ledger WHERE kind='outcome' AND idem=? ORDER BY seq DESC LIMIT 1",
            (idem,),
        ).fetchone()
        return json.loads(row[0]) if row else None

    def pending(self) -> list[dict[str, Any]]:
        """Every action whose outcome never landed, oldest first (nucleus.md: `pending()` → list).

        A list, not a single record: a d2 resident can have several verbs in flight when the box
        dies, and returning only the oldest silently strands the rest.
        """
        rows = self._db.execute(
            "SELECT seq, idem, body FROM ledger WHERE kind='action' ORDER BY seq"
        ).fetchall()
        out: list[dict[str, Any]] = []
        for seq, idem, body in rows:
            if idem and self.outcome_for(idem) is None:
                b: dict[str, Any] = json.loads(body)
                out.append({"idem": idem, "seq": int(seq), **b})
        return out

    def verify(self, lo: int | None = None, hi: int | None = None) -> VerifyReport:
        """Re-derive the chain. On tamper, `first_bad_seq` names the first record that fails."""
        return self.ledger.verify_chain(lo, hi)

    @property
    def head_hash(self) -> str:
        return self.ledger.head_hash

    def close(self) -> None:
        self.ledger.close()
        self._db.close()
