"""The effect registry and lineage index — two Conductor folds (contracts/act.md §7).

**The null is `(claim_id, step_id)` alone.** That key is exactly-once *per cell*, which is the wrong
grain the moment a cell can fork: eight siblings branched from one parent each compute a different
`claim_id`, so each one sends the email. The cell-scoped key is not weaker exactly-once — it is
exactly-once about the wrong noun.

So the key is **scoped** (§7.1):

* `instance` — `(claim_id, step_id)`. Fires again per branch, **by design**: a checkpoint or a
  self-post should happen once per branch, and suppressing it would strand the fork.
* `lineage` — `(lineage_root, effect_id)`. Set-once across the whole fork tree. This is the H1+
  world-write key: sends, payments, deliveries.
* `slot` — `(routine_id, scheduled_slot)`. One fire per scheduled slot; a missed slot is not pending.

Two properties this module exists to hold:

* **Reserve-then-execute, never consult-then-act** (FIX-2). `reserve()` is an atomic
  insert-if-absent, so the TOCTOU window between "is this taken?" and "take it" does not exist. Two
  siblings racing on the same key produce exactly one winner, decided by the database rather than by
  an ordering nobody controls.
* **Dedup-and-SHARE, not dedup-and-fail.** The loser is refused with `duplicate_of: <winner>` and
  then waits for the winner's receipt so it can cite the same evidence. A sibling that merely failed
  would have to either re-do the work or lie about it.

The live tables are a **serving copy**, rebuilt from the log on start (A13): truth is the records, and
a registry that could not be regenerated would be a second source of truth about who did what.
"""
from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from ..common.canon import canon_bytes

EffectScope = Literal["instance", "lineage", "slot"]
EffectState = Literal["reserved", "held", "executed", "settled"]


def effect_id(capability_ref: str, tool_version: str, sig_args: dict[str, Any]) -> str:
    """`sha256(capability_ref ‖ tool_version ‖ JCS(sig_args))` over effect-SIGNIFICANT args only.

    The per-field marking in the profile is what makes this work in both directions. Volatile args
    (a request id, a timestamp) must not enter, or two attempts at the same send would compute
    different keys and dedup would silently stop working — **spurious uniqueness**. And cosmetic
    args must not be the only thing that differs, or a retry loop could **evade** dedup by changing
    a comment. Concurrent fork siblings compute the same key because they hash the same significant
    facts, which is the entire mechanism.
    """
    payload = canon_bytes(
        {"capability_ref": capability_ref, "tool_version": tool_version, "args": sig_args}
    )
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def scope_key(
    scope: EffectScope,
    *,
    claim_id: str = "",
    step_id: str = "",
    lineage_root: str = "",
    eid: str = "",
    routine_id: str = "",
    slot: str = "",
) -> str:
    """The dedup key for a scope. Rendered as a string so one table serves all three shapes."""
    if scope == "instance":
        return f"instance:{claim_id}:{step_id}"
    if scope == "lineage":
        return f"lineage:{lineage_root}:{eid}"
    if scope == "slot":
        return f"slot:{routine_id}:{slot}"
    raise ValueError(f"unknown effect_scope '{scope}'")


@dataclass(frozen=True)
class Reservation:
    """The outcome of `reserve()`. `won` is the only thing a caller may branch on."""

    key: str
    act_id: str
    won: bool
    duplicate_of: str | None = None
    state: EffectState = "reserved"


@dataclass(frozen=True)
class Lineage:
    claim_id: str
    root_id: str
    parent_id: str | None
    forked_at_seq: int | None


class EffectRegistry:
    """`effects(scope_key → {act_id, state, receipt_seq, lease, grant_cmd_id})`, plus the lineage fold."""

    def __init__(self, home: Path | str) -> None:
        self.dir = Path(home) / "_conductor"
        self.dir.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(self.dir / "effects.db", isolation_level=None)
        self._db.execute("PRAGMA journal_mode=WAL")
        # FULL, not NORMAL: unlike the nucleus index this is NOT a render of one local log -- it is
        # the arbiter of who won a race, and a lost reservation row means two siblings both believe
        # they may send. Durability here IS the dedup guarantee.
        self._db.execute("PRAGMA synchronous=FULL")
        self._db.execute("PRAGMA busy_timeout=5000")
        self._db.executescript(
            """
            CREATE TABLE IF NOT EXISTS effects(
              key TEXT PRIMARY KEY, act_id TEXT NOT NULL, state TEXT NOT NULL,
              receipt_seq INTEGER, lease TEXT, grant_cmd_id TEXT, reserved_at REAL);
            CREATE TABLE IF NOT EXISTS lineage(
              claim_id TEXT PRIMARY KEY, root_id TEXT NOT NULL, parent_id TEXT, forked_at_seq INTEGER);
            """
        )

    # ---------------------------------------------------------------- reservation (§7.3)

    def reserve(
        self,
        key: str,
        act_id: str,
        *,
        lease: str | None = None,
        rebind_after_s: float | None = None,
    ) -> Reservation:
        """Atomic insert-if-absent. **Reserve, then execute** — never consult, then act.

        The whole TOCTOU class is closed by letting the PRIMARY KEY decide. A read-then-write leaves
        a window in which two siblings both see "absent" and both proceed, and that window is
        exactly where a double-send lives.

        `rebind_after_s` handles crash window **W2** (reserved, then died before journaling). Without
        it the key is held forever by an act that will never run, and the delivery is simply LOST —
        which is a different bug from a double-send, not a safer one. The re-bind is guarded twice:
        only a `reserved` row (never `held`/`executed`/`settled`, where the world may already have
        moved), and the `state='reserved'` predicate rides in the UPDATE's WHERE clause so a
        concurrent transition wins the race instead of being clobbered.
        """
        cur = self._db.execute(
            "INSERT OR IGNORE INTO effects(key,act_id,state,lease,reserved_at) "
            "VALUES(?,?,'reserved',?,julianday('now'))",
            (key, act_id, lease),
        )
        if cur.rowcount == 1:
            return Reservation(key=key, act_id=act_id, won=True)

        row = self._db.execute(
            "SELECT act_id, state, (julianday('now') - reserved_at) * 86400.0 FROM effects WHERE key=?",
            (key,),
        ).fetchone()
        winner, state, age = (str(row[0]), str(row[1]), float(row[2] or 0.0)) if row else ("?", "reserved", 0.0)

        if winner == act_id and state == "reserved":
            # The same act re-attempting its own reservation: re-binding, not losing.
            return Reservation(key=key, act_id=act_id, won=True, state=state)  # type: ignore[arg-type]
        if winner == act_id:
            # The same act, but the effect already reached `{state}`. This is a REPLAY, not a
            # resume: the world has moved and re-running would move it twice. The caller is handed
            # its own act_id back so it can tell "I already did this" from "a sibling beat me", and
            # answer a repeated request with the receipt it already wrote.
            return Reservation(
                key=key, act_id=act_id, won=False, duplicate_of=act_id, state=state  # type: ignore[arg-type]
            )

        if state == "reserved" and rebind_after_s is not None and age > rebind_after_s:
            taken = self._db.execute(
                "UPDATE effects SET act_id=?, lease=?, reserved_at=julianday('now') "
                "WHERE key=? AND state='reserved'",
                (act_id, lease, key),
            )
            if taken.rowcount == 1:
                return Reservation(key=key, act_id=act_id, won=True)

        return Reservation(
            key=key, act_id=act_id, won=False, duplicate_of=winner, state=state  # type: ignore[arg-type]
        )

    def transition(
        self,
        key: str,
        state: EffectState,
        *,
        receipt_seq: int | None = None,
        grant_cmd_id: str | None = None,
    ) -> None:
        """Advance a reservation. `held → executed` is what consumes an H3 grant (§6.5)."""
        self._db.execute(
            "UPDATE effects SET state=?, receipt_seq=COALESCE(?,receipt_seq), "
            "grant_cmd_id=COALESCE(?,grant_cmd_id) WHERE key=?",
            (state, receipt_seq, grant_cmd_id, key),
        )

    def get(self, key: str) -> dict[str, Any] | None:
        row = self._db.execute(
            "SELECT key,act_id,state,receipt_seq,lease,grant_cmd_id FROM effects WHERE key=?", (key,)
        ).fetchone()
        if not row:
            return None
        cols = ("key", "act_id", "state", "receipt_seq", "lease", "grant_cmd_id")
        return dict(zip(cols, row, strict=True))

    def release(self, key: str) -> None:
        """Drop a reservation. Only ever for an orphan whose lease expired (W1/W2)."""
        self._db.execute("DELETE FROM effects WHERE key=?", (key,))

    def sweep(self, *, older_than_s: float) -> list[str]:
        """Expire `reserved` rows whose lease TTL ran out — W2's orphan path.

        Only `reserved` rows. An `executed` row must outlive every TTL, because the world already
        moved and forgetting that is precisely how you send twice.
        """
        rows = self._db.execute(
            "SELECT key FROM effects WHERE state='reserved' "
            "AND (julianday('now') - reserved_at) * 86400.0 > ?",
            (older_than_s,),
        ).fetchall()
        keys = [str(r[0]) for r in rows]
        for k in keys:
            self.release(k)
        return keys

    # ---------------------------------------------------------------- the lineage fold (§7.2)

    def note_lineage(
        self, claim_id: str, *, parent_id: str | None = None, forked_at_seq: int | None = None
    ) -> Lineage:
        """Fold one genesis record. A root's `root_id` is itself; a child inherits its parent's."""
        root = claim_id
        if parent_id:
            parent = self.lineage_of(parent_id)
            root = parent.root_id if parent else parent_id
        self._db.execute(
            "INSERT OR REPLACE INTO lineage(claim_id,root_id,parent_id,forked_at_seq) VALUES(?,?,?,?)",
            (claim_id, root, parent_id, forked_at_seq),
        )
        return Lineage(claim_id, root, parent_id, forked_at_seq)

    def lineage_of(self, claim_id: str) -> Lineage | None:
        row = self._db.execute(
            "SELECT claim_id,root_id,parent_id,forked_at_seq FROM lineage WHERE claim_id=?",
            (claim_id,),
        ).fetchone()
        return Lineage(str(row[0]), str(row[1]), row[2], row[3]) if row else None

    def root_of(self, claim_id: str) -> str:
        """The lineage root, or the claim itself for a cell that never forked.

        Defaulting to the claim is what lets an unforked cell use the `lineage` scope before any
        fork has happened, rather than requiring every run to pre-register a root.
        """
        found = self.lineage_of(claim_id)
        return found.root_id if found else claim_id

    # ---------------------------------------------------------------- rebuild (A13)

    def rebuild_from(self, records: list[dict[str, Any]]) -> int:
        """Regenerate both folds from log records. The live tables are a SERVING COPY, not truth.

        Takes `genesis` records (lineage) and `action`/`act_receipt` records (effects), in seq order.
        A registry that could not be rebuilt would be a second source of truth about who did what,
        and the two would diverge on the first crash.
        """
        self._db.execute("DELETE FROM effects")
        self._db.execute("DELETE FROM lineage")
        n = 0
        for rec in records:
            kind = str(rec.get("kind") or rec.get("type") or "")
            body = rec.get("body") or {}
            if not isinstance(body, dict):
                continue
            if kind == "genesis":
                forked = body.get("forked_from") or {}
                self.note_lineage(
                    str(body.get("claim_id", "")),
                    parent_id=str(forked.get("claim")) if forked.get("claim") else None,
                    forked_at_seq=forked.get("seq"),
                )
                n += 1
            elif kind in ("action", "act", "act_receipt") and body.get("effect_key"):
                key, act_id = str(body["effect_key"]), str(body.get("corr", ""))
                self.reserve(key, act_id)
                if kind == "act_receipt" and body.get("exec") == "ok":
                    self.transition(key, "executed", receipt_seq=rec.get("seq"))
                n += 1
        return n

    def close(self) -> None:
        self._db.close()
