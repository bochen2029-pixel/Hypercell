"""The Medium — local durable transport, T0 (contracts/wire.md §10). Single-node SQLite log.

hypercell owns the protocol; the transport is rented and pluggable. P3 swaps to NATS/JetStream
behind the same interface, and the C1–C12 battery re-runs unchanged against it — that re-run IS the
parity falsifier.

**M1 completes three lived defects.**

* **E3 — the pragma block.** This file used to set `journal_mode=WAL` and nothing else, so
  durability was whatever SQLite defaulted to that release. Guard `G-DB-DURABLE` has been reporting
  it DEGRADED since slice S9.1. It is now explicit: WAL, `synchronous=FULL` (gold cannot rest on a
  default), and a real `busy_timeout` so a contended Medium waits instead of raising.
* **E1 — the count must be true.** Thirteen columns became sixteen, and the registry moved to
  `medium/wire.py` as ONE source instead of three drifting copies.
* **E2 — receipts stay in-process.** Receipts, verdicts and presence now post as registry types, so
  every constitutional fold can actually read them.

**Per-culture dense seq.** `seq` is dense within a culture, assigned under the same transaction as
the insert. Gaps appear only via `compact`. A global counter would make two cultures interleave and
every replay would depend on unrelated traffic.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..common import clock
from ..common.canon import canon_bytes
from ..common.ledger import chain_step, leaf
from .wake import Doorbell, WakeStats, wait
from .wire import BODY_HARD_CAP, AclDenied, check_acl, is_known

#: Per-culture chain anchor (wire.md §5.2). Chain-versioned, never wire-versioned: a wire semver
#: bump must not re-anchor existing chains.
MEDIUM_CHAIN_CONSTRUCTION = b"hypercell/medium-chain/1"


@dataclass(frozen=True)
class Posted:
    """What `post()` returns. `dedup` distinguishes "wrote it" from "already had it" (C8)."""

    seq: int
    culture: str
    hash: str
    dedup: bool = False


@dataclass(frozen=True)
class Filter:
    """Poll axes (§7.2). Every axis is a pure predicate over the envelope — no body parsing."""

    types: tuple[str, ...] | None = None
    recipient: str | None = None
    sender: str | None = None
    mentions: str | None = None
    corr: str | None = None
    round: int | None = None


def _anchor(culture: str) -> bytes:
    import hashlib

    return hashlib.sha256(MEDIUM_CHAIN_CONSTRUCTION + b"\x00" + culture.encode("utf-8")).digest()


class LocalMedium:
    """T0. One SQLite file, one dense sequence per culture, one chain per culture."""

    def __init__(self, home: Path | str) -> None:
        self.dir = Path(home) / "_medium"
        self.dir.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(self.dir / "medium.db", isolation_level=None)
        # ---- the pragma block (E3). Explicit, because defaults are not a durability contract.
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA synchronous=FULL")
        self._db.execute("PRAGMA busy_timeout=5000")
        self._db.execute("PRAGMA foreign_keys=ON")
        self._init()
        self._doorbell = Doorbell(home)

    def _init(self) -> None:
        self._db.executescript(
            """
            CREATE TABLE IF NOT EXISTS messages(
              culture TEXT NOT NULL, seq INTEGER NOT NULL,
              ts TEXT, sender TEXT, recipient TEXT, type TEXT,
              reply_to INTEGER, round INTEGER, priority INTEGER DEFAULT 0,
              origin TEXT, idem TEXT, corr TEXT, mentions TEXT,
              body TEXT, artifact TEXT, hash TEXT,
              void_by_acl INTEGER DEFAULT 0,
              PRIMARY KEY (culture, seq));
            CREATE UNIQUE INDEX IF NOT EXISTS idx_idem ON messages(culture, sender, idem)
              WHERE idem IS NOT NULL;
            CREATE INDEX IF NOT EXISTS idx_type ON messages(culture, type);
            CREATE INDEX IF NOT EXISTS idx_corr ON messages(culture, corr);
            CREATE TABLE IF NOT EXISTS cursors(
              consumer TEXT NOT NULL, culture TEXT NOT NULL, seq INTEGER NOT NULL,
              PRIMARY KEY (consumer, culture));
            """
        )

    # ---------------------------------------------------------------- posting

    def _head(self, culture: str) -> tuple[int, bytes]:
        row = self._db.execute(
            "SELECT seq, hash FROM messages WHERE culture=? ORDER BY seq DESC LIMIT 1", (culture,)
        ).fetchone()
        if not row:
            return 0, _anchor(culture)
        return int(row[0]), bytes.fromhex(str(row[1]).removeprefix("sha256:"))

    def post(
        self,
        culture: str,
        sender: str,
        msg_type: str,
        *,
        body: Any = None,
        recipient: str | None = None,
        reply_to: int | None = None,
        round: int | None = None,
        priority: int = 0,
        origin: str | None = None,
        idem: str | None = None,
        corr: str | None = None,
        mentions: list[str] | None = None,
        artifact: dict[str, Any] | None = None,
        _bypass_acl: bool = False,
    ) -> Posted:
        """Append one record. Enforces the ACL, the body cap, idem dedup, and the chain.

        `_bypass_acl` exists for ONE reason: C11 requires a harness that smuggles a record past the
        client gate, so the void-at-fold path can be proven to work. Production callers never set it,
        and a record admitted this way is marked `void_by_acl` in the same insert.
        """
        if not is_known(msg_type):
            raise AclDenied(f"'{msg_type}' is neither a registry type nor an x- extension")

        void = False
        if _bypass_acl:
            from .wire import void_at_fold

            void = void_at_fold(msg_type, sender)
        else:
            check_acl(msg_type, sender)

        encoded = json.dumps(body, ensure_ascii=False) if body is not None else None
        if encoded is not None and len(encoded.encode("utf-8")) > BODY_HARD_CAP:
            raise AclDenied(
                f"body is {len(encoded)}B, over the {BODY_HARD_CAP}B hard cap — post an artifact "
                "pointer instead; the Medium is a log, not a blob store"
            )

        cur = self._db.execute("BEGIN IMMEDIATE")
        try:
            if idem is not None:
                row = self._db.execute(
                    "SELECT seq, hash FROM messages WHERE culture=? AND sender=? AND idem=?",
                    (culture, sender, idem),
                ).fetchone()
                if row:
                    # C8: the SAME seq comes back. A second post is not a second record.
                    self._db.execute("COMMIT")
                    return Posted(seq=int(row[0]), culture=culture, hash=str(row[1]), dedup=True)

            head_seq, head_hash = self._head(culture)
            seq = head_seq + 1
            record = {
                "seq": seq,
                "ts": clock.now_iso(),
                "culture": culture,
                "sender": sender,
                "recipient": recipient,
                "type": msg_type,
                "reply_to": reply_to,
                "round": round,
                "priority": priority,
                "origin": origin,
                "idem": idem,
                "corr": corr,
                "mentions": mentions,
                "body": body,
                "artifact": artifact,
            }
            new_hash = "sha256:" + chain_step(head_hash, leaf(record)).hex()
            self._db.execute(
                "INSERT INTO messages(culture,seq,ts,sender,recipient,type,reply_to,round,priority,"
                "origin,idem,corr,mentions,body,artifact,hash,void_by_acl)"
                " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    culture, seq, record["ts"], sender, recipient, msg_type, reply_to, round, priority,
                    origin, idem, corr,
                    json.dumps(mentions) if mentions else None,
                    encoded,
                    json.dumps(artifact, ensure_ascii=False) if artifact else None,
                    new_hash,
                    1 if void else 0,
                ),
            )
            self._db.execute("COMMIT")
        except Exception:
            self._db.execute("ROLLBACK")
            raise
        del cur
        # Ring AFTER the commit: a bell for a record that then rolls back would wake a reader to
        # find nothing, and a hint that lies is worse than a hint that is slow.
        self._doorbell.ring(culture)
        return Posted(seq=seq, culture=culture, hash=new_hash)

    # ---------------------------------------------------------------- reading

    @staticmethod
    def _row_to_msg(row: Any) -> dict[str, Any]:
        return {
            "culture": row[0], "seq": int(row[1]), "ts": row[2], "sender": row[3],
            "recipient": row[4], "type": row[5], "reply_to": row[6], "round": row[7],
            "priority": row[8], "origin": row[9], "idem": row[10], "corr": row[11],
            "mentions": json.loads(row[12]) if row[12] else None,
            "body": json.loads(row[13]) if row[13] else None,
            "artifact": json.loads(row[14]) if row[14] else None,
            "hash": row[15],
            "void_by_acl": bool(row[16]),
        }

    def read(
        self, culture: str, *, since: int = 0, filt: Filter | None = None, include_void: bool = False
    ) -> list[dict[str, Any]]:
        """Records after `since`, in **seq order always** — priority surfaces, it never reorders."""
        rows = self._db.execute(
            "SELECT culture,seq,ts,sender,recipient,type,reply_to,round,priority,origin,idem,corr,"
            "mentions,body,artifact,hash,void_by_acl FROM messages "
            "WHERE culture=? AND seq>? ORDER BY seq",
            (culture, since),
        ).fetchall()
        out = [self._row_to_msg(r) for r in rows]
        if not include_void:
            # Void-at-fold: present in the log, absent from every constitutional fold.
            out = [m for m in out if not m["void_by_acl"]]
        return [m for m in out if _matches(m, filt)] if filt else out

    def poll(
        self, consumer: str, culture: str, *, filt: Filter | None = None, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """Cursor-advancing read. C5: resumes at k+1 exactly — no skip, no re-delivery."""
        row = self._db.execute(
            "SELECT seq FROM cursors WHERE consumer=? AND culture=?", (consumer, culture)
        ).fetchone()
        since = int(row[0]) if row else 0

        batch = self.read(culture, since=since, filt=filt)
        if limit is not None:
            batch = batch[:limit]
        if batch:
            self._db.execute(
                "INSERT INTO cursors(consumer,culture,seq) VALUES(?,?,?) "
                "ON CONFLICT(consumer,culture) DO UPDATE SET seq=excluded.seq",
                (consumer, culture, batch[-1]["seq"]),
            )
        return batch

    def replay(self, culture: str, *, lo: int = 1, hi: int | None = None) -> list[dict[str, Any]]:
        msgs = self.read(culture, since=lo - 1)
        return [m for m in msgs if hi is None or m["seq"] <= hi]

    def submissions(self, culture: str, round: int) -> list[dict[str, Any]]:
        return self.read(culture, filt=Filter(types=("submission",), round=round))

    # ---------------------------------------------------------------- integrity

    def verify(self, culture: str) -> dict[str, Any]:
        """Re-derive the per-culture chain. Names the first bad seq and every void-at-fold record."""
        head = _anchor(culture)
        void: list[int] = []
        for msg in self.read(culture, include_void=True):
            if msg["void_by_acl"]:
                void.append(msg["seq"])
            record = {k: msg[k] for k in (
                "seq", "ts", "culture", "sender", "recipient", "type", "reply_to", "round",
                "priority", "origin", "idem", "corr", "mentions", "body", "artifact",
            )}
            expected = "sha256:" + chain_step(head, leaf(record)).hex()
            if expected != msg["hash"]:
                return {"ok": False, "first_bad_seq": msg["seq"], "void_by_acl": void}
            head = bytes.fromhex(expected.removeprefix("sha256:"))
        return {"ok": True, "first_bad_seq": None, "void_by_acl": void}

    def projection(self, culture: str) -> bytes:
        """The canonical projection C9 compares — excludes `ts`/`hash`, which are timing, not content."""
        msgs = [
            {k: m[k] for k in ("seq", "culture", "sender", "recipient", "type", "body", "round", "corr")}
            for m in self.read(culture)
        ]
        return canon_bytes(msgs)

    def data_version(self) -> int:
        """SQLite bumps this whenever ANOTHER connection commits — the fallback's whole basis."""
        row = self._db.execute("PRAGMA data_version").fetchone()
        return int(row[0]) if row else 0

    def wait(
        self,
        consumer: str,
        culture: str,
        *,
        filt: Filter | None = None,
        timeout_s: float = 5.0,
        fallback_tick_s: float = 0.05,
    ) -> tuple[list[dict[str, Any]], WakeStats]:
        """Block until matching records arrive, then advance the cursor (C3, W1).

        A waiting cell makes no model calls: waiting is pure I/O and never touches the cognition
        seam. A sleeping cell costs a stat() per tick and nothing else.
        """
        return wait(
            check=lambda: self.poll(consumer, culture, filt=filt),
            doorbell=self._doorbell,
            culture=culture,
            data_version=self.data_version,
            timeout_s=timeout_s,
            fallback_tick_s=fallback_tick_s,
        )

    def sever_hint(self) -> None:
        """Kill the doorbell, leave the log intact. The fallback must still deliver everything."""
        self._doorbell.sever()

    def close(self) -> None:
        self._db.close()


def _matches(msg: dict[str, Any], filt: Filter) -> bool:
    if filt.types is not None and msg["type"] not in filt.types:
        return False
    if filt.recipient is not None and msg["recipient"] != filt.recipient:
        return False
    if filt.sender is not None and msg["sender"] != filt.sender:
        return False
    if filt.corr is not None and msg["corr"] != filt.corr:
        return False
    if filt.round is not None and msg["round"] != filt.round:
        return False
    if filt.mentions is not None and filt.mentions not in (msg["mentions"] or []):
        return False
    return True
