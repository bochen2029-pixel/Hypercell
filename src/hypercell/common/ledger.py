"""The append-only chain engine — genesis, hash chain, group-commit, torn-tail (contracts/nucleus.md).

The ledger is **truth**; every index and render is a disposable fold over it (A13). This module owns
four things and nothing else:

* **the chain** — construction per `contracts/wire.md` §5.1, the ONE home. One verifier, two logs:
  the Medium's per-culture chain and every nucleus use the same canon, leaf and step, differing only
  in their anchor constant.
* **genesis** — seq 1, exactly once, gold, carrying the contract census. A ledger that cannot say
  which contract versions wrote it is not migratable (G3).
* **durability classes** — `gold` fsyncs before returning; `standard` rides a group-commit and is
  flushed on close, on the next gold write, or when the buffer fills. Two laws, one group-commit
  (nucleus.md §4).
* **torn-tail recovery** — a process killed mid-append leaves a partial final line. On open that
  line is truncated away, because a half-record is not a record. Everything before it still verifies.

What this module deliberately does NOT do: interpret bodies, know what a `percept` is, or decide
what a cell should write. It is a log, not a policy.
"""
from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from . import clock
from .canon import canon_bytes

#: Chain-versioned, never contract-versioned: a nucleus.md MAJOR bump must not re-anchor existing
#: chains (seat-03 law). Changing THIS constant is what re-anchors them.
NUCLEUS_CHAIN_CONSTRUCTION = b"hypercell/nucleus-chain/1"

Durability = Literal["gold", "standard"]

#: Fields excluded from the leaf. `hash` is the chain column itself; `sig` is reserved (wire.md §2.1).
_NOT_IN_LEAF = ("hash", "sig")

#: Group-commit ceiling. NUC-7's bar is <=1 durable write per standard flush, <=2 per gold.
_GROUP_COMMIT_MAX = 64


def anchor(claim_id: str) -> bytes:
    """`hash_0` for a root cell: sha256(construction || 0x00 || claim_id) — wire.md §5.1 / nucleus §2."""
    return hashlib.sha256(NUCLEUS_CHAIN_CONSTRUCTION + b"\x00" + claim_id.encode("utf-8")).digest()


def leaf(record: dict[str, Any]) -> bytes:
    """The canonical leaf of a record: sha256(canon(record sans hash/sig))."""
    return hashlib.sha256(canon_bytes({k: v for k, v in record.items() if k not in _NOT_IN_LEAF})).digest()


def chain_step(prev: bytes, leaf_digest: bytes) -> bytes:
    """`hash_n = sha256(raw32(hash_n-1) || raw32(leaf_n))` — raw digests concatenated, never hex."""
    return hashlib.sha256(prev + leaf_digest).digest()


def _hex(d: bytes) -> str:
    return "sha256:" + d.hex()


def _unhex(s: str) -> bytes:
    return bytes.fromhex(s.removeprefix("sha256:"))


@dataclass(frozen=True)
class VerifyReport:
    """`verify_chain` result. `first_bad_seq` names the FIRST record that fails — the tamper point."""

    ok: bool
    checked: int
    first_bad_seq: int | None = None
    reason: str = ""


class Ledger:
    """One append-only, hash-chained JSONL log with a group-commit buffer.

    Sequence numbers start at 1 (genesis). `open()` recovers a torn tail, then reads the head hash
    forward, so a crashed writer costs at most its last unfinished record.
    """

    def __init__(self, path: Path | str, *, claim_id: str, anchor_hash: bytes | None = None) -> None:
        self.path = Path(path)
        self.claim_id = claim_id
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._anchor = anchor_hash if anchor_hash is not None else anchor(claim_id)
        self._buffer: list[str] = []
        self._seq = 0
        self._head = self._anchor
        self._recover()

    # ---------------------------------------------------------------- open / recovery

    def _recover(self) -> None:
        """Walk sealed history, then truncate a torn final line. A half-record is not a record."""
        # Sealed segments come first and are immutable, so they need no torn-tail handling — but
        # they DO carry the seq and head we must continue from. Skipping them would restart the
        # chain at the anchor and re-issue sequence numbers already sealed into history.
        for seg in self.segment_files():
            for rec in self._read_file(seg):
                self._seq = int(rec.get("seq", self._seq))
                if isinstance(rec.get("hash"), str):
                    self._head = _unhex(rec["hash"])

        if not self.path.exists():
            return

        raw = self.path.read_bytes()
        if not raw:
            return

        keep_to = 0
        seq, head = self._seq, self._head  # continue from sealed history, not from zero
        for line in raw.splitlines(keepends=True):
            text = line.decode("utf-8", errors="replace")
            if not text.endswith("\n"):
                break  # torn tail: the writer died before the newline landed
            stripped = text.strip()
            if not stripped:
                keep_to += len(line)
                continue
            try:
                rec = json.loads(stripped)
            except json.JSONDecodeError:
                break  # a mangled line ends the trustworthy prefix
            keep_to += len(line)
            seq = int(rec.get("seq", seq))
            if isinstance(rec.get("hash"), str):
                head = _unhex(rec["hash"])

        if keep_to != len(raw):
            with open(self.path, "r+b") as f:
                f.truncate(keep_to)
        self._seq, self._head = seq, head

    # ---------------------------------------------------------------- writing

    @property
    def head_hash(self) -> str:
        return _hex(self._head)

    @property
    def seq(self) -> int:
        return self._seq

    def genesis(self, census: dict[str, str], *, forked_from: dict[str, Any] | None = None) -> int:
        """Write seq 1, exactly once, gold. Refuses a partial census — an unversioned log is G3."""
        if self._seq != 0:
            raise ValueError(f"{self.path} already has {self._seq} record(s); genesis is seq 1, exactly once")
        if not census:
            raise ValueError("genesis requires a contract census; a ledger that cannot say which "
                             "contract versions wrote it is not migratable (G3)")
        body: dict[str, Any] = {"claim_id": self.claim_id, "contract": dict(census)}
        if forked_from is not None:
            body["forked_from"] = forked_from
        return self.append("genesis", body, durability="gold")

    def adopt_chain(self, census: dict[str, str], at_seq: int) -> int:
        """Synthetic genesis for a pre-chain ledger (HONEST-EPOCH, nucleus.md §1).

        Records before `at_seq` stay immutable-but-unhashed and the contract says so, rather than
        pretending tamper-evidence existed before it did.
        """
        body = {"claim_id": self.claim_id, "contract": dict(census), "chain_adopted_at_seq": at_seq}
        return self.append("genesis", body, durability="gold")

    def append(
        self,
        kind: str,
        body: Any,
        *,
        idem: str | None = None,
        refs: list[int] | None = None,
        durability: Durability = "standard",
    ) -> int:
        """Append one chained record. `gold` is durable on return; `standard` rides the group-commit."""
        self._seq += 1
        record: dict[str, Any] = {
            "seq": self._seq,
            "ts": clock.now_iso(),
            "kind": kind,
            "body": body,
        }
        if idem is not None:
            record["idem"] = idem
        if refs:
            record["refs"] = refs

        self._head = chain_step(self._head, leaf(record))
        record["hash"] = _hex(self._head)
        self._buffer.append(json.dumps(record, ensure_ascii=False) + "\n")

        if durability == "gold" or len(self._buffer) >= _GROUP_COMMIT_MAX:
            self.flush(fsync=True)
        return self._seq

    def flush(self, *, fsync: bool = True) -> None:
        """Drain the group-commit buffer. One durable write per flush, not one per record."""
        if not self._buffer:
            return
        payload = "".join(self._buffer)
        self._buffer.clear()
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(payload)
            f.flush()
            if fsync:
                os.fsync(f.fileno())

    # ---------------------------------------------------------------- reading

    def segment_files(self) -> list[Path]:
        """Sealed segments, oldest first. Names are zero-padded, so lexical order IS seq order."""
        seg_dir = self.path.parent / "segments"
        return sorted(seg_dir.glob("*.jsonl")) if seg_dir.exists() else []

    @staticmethod
    def _read_file(path: Path) -> Iterator[dict[str, Any]]:
        if not path.exists():
            return
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    yield json.loads(line)

    def records(self, lo: int | None = None, hi: int | None = None) -> Iterator[dict[str, Any]]:
        """Iterate records in seq order, **across sealed segments and the live file**.

        Spanning segments is not a convenience: `verify_chain` walks from the anchor, so if sealing
        hid history the chain would restart mid-stream and report a false tamper on an untouched
        log. A guard that cries wolf is worse than no guard — nobody believes the real alarm.

        Buffered writes are visible: the log is one thing, not a file plus a pending list.
        """
        self.flush()
        for path in [*self.segment_files(), self.path]:
            for rec in self._read_file(path):
                s = int(rec["seq"])
                if lo is not None and s < lo:
                    continue
                if hi is not None and s > hi:
                    return
                yield rec

    def verify_chain(self, lo: int | None = None, hi: int | None = None) -> VerifyReport:
        """Re-derive every hash. On failure, name the FIRST bad seq — that is the tamper point.

        **The walk always begins at the anchor**, whatever `lo` says. A chain suffix cannot be
        verified on its own: trusting record N's stored `prev` to check record N+1 is circular — an
        attacker who rewrote both would pass. `lo`/`hi` therefore bound which records are *reported*
        on, never where the derivation starts. (Verifying a suffix cheaply is what a sealed
        segment's `head_hash` sidecar is for, and that path is not built yet.)
        """
        self.flush()
        head = self._anchor
        checked = 0
        adopted_at: int | None = None

        for rec in self.records():
            seq = int(rec["seq"])

            if rec.get("kind") == "genesis" and isinstance(rec.get("body"), dict):
                k = rec["body"].get("chain_adopted_at_seq")
                if isinstance(k, int):
                    adopted_at = k

            # Pre-adoption records are immutable-but-unhashed by contract, not by oversight.
            if adopted_at is not None and seq < adopted_at:
                continue
            if rec.get("hash") is None:
                continue

            expected = chain_step(head, leaf(rec))
            if _hex(expected) != rec["hash"]:
                return VerifyReport(
                    ok=False,
                    checked=checked,
                    first_bad_seq=seq,
                    reason=f"record {seq} does not chain: stored {rec['hash'][:23]}..., "
                    f"recomputed {_hex(expected)[:23]}...",
                )
            head = expected
            checked += 1

            if hi is not None and seq >= hi:
                break

        if lo is not None or hi is not None:
            return VerifyReport(ok=True, checked=checked)
        if checked and _hex(head) != self.head_hash:
            return VerifyReport(ok=False, checked=checked, reason="head hash disagrees with the walked chain")
        return VerifyReport(ok=True, checked=checked)

    # ---------------------------------------------------------------- segments

    def seal_segment(self, segments_dir: Path | str | None = None) -> Path:
        """Seal the current log: flush, fsync, write a meta sidecar, make it read-only, rotate.

        Sealing is what makes an old segment cheap to trust — the sidecar carries the range and the
        head hash, so verifying a sealed segment never requires re-reading the ones before it.
        """
        self.flush()
        if not self.path.exists() or self._seq == 0:
            raise ValueError("nothing to seal: the ledger is empty")

        target_dir = Path(segments_dir) if segments_dir else self.path.parent / "segments"
        target_dir.mkdir(parents=True, exist_ok=True)

        # The live file only — `records()` now spans sealed segments, which would give us the first
        # record of all history instead of the first in the file we are about to seal.
        first = next(self._read_file(self.path), None)
        lo = int(first["seq"]) if first else 1
        sealed = target_dir / f"{lo:012d}-{self._seq:012d}.jsonl"

        meta = {
            "claim_id": self.claim_id,
            "lo": lo,
            "hi": self._seq,
            "head_hash": self.head_hash,
            "sealed_at": clock.now_iso(),
            "construction": NUCLEUS_CHAIN_CONSTRUCTION.decode(),
        }
        os.replace(self.path, sealed)
        sealed.with_suffix(".meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        try:
            os.chmod(sealed, 0o444)
        except OSError:  # pragma: no cover — some filesystems refuse; sealing is still valid
            pass
        return sealed

    def close(self) -> None:
        self.flush()
