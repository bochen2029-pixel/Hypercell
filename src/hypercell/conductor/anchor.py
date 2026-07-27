"""The anchor log — an external trust point for the chain (wire.md §5.4; slice M3, falsifier W3).

**The null is an unanchored chain.** A hash chain proves a log is *self-consistent*: change one
record and every downstream hash stops matching. But an attacker who can rewrite the log bytes can
also recompute the stored hashes, and then `verify()` passes — the chain is perfectly consistent
about a history that never happened. Tamper-evidence against an editor who can edit *everything*
requires a copy of the truth the editor does not hold.

That copy is this file: an append-only, fsync'd JSONL of `{seq, hash, ts}` checkpoints per culture,
written (a) every `anchor_every` messages (default 64), (b) at every **D-gold** message, and (c) at
every `compact` record. It is small — one short line per checkpoint, not per message — and it is
the thing a byte-rewrite cannot silently fix, because rewriting the log does not rewrite the anchor.

Three duties, one mechanism (§5.4):

1. **Tamper-evidence with an external trust point.** `verify()` matches every anchor against the
   recomputed chain. A rewrite that keeps the chain self-consistent still collides here.
2. **The gold durability edge.** A D-gold post returns only after its anchor entry is fsync'd, so
   gold never has its only copy inside a transport's lax-fsync window.
3. **Honest degradation.** Anchor file lost ⇒ the chain is still self-consistent, and `verify()`
   says **"consistent, unanchored"** rather than "ok". A verifier that cannot tell the difference
   between "checked against an external point" and "checked against itself" is reporting a weaker
   guarantee than its caller thinks it bought.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..common import clock

#: Checkpoint cadence. Every message would make the anchor a second copy of the log (and a second
#: fsync per post); too sparse and a rewrite has a long window to hide in. 64 is the contract default.
DEFAULT_ANCHOR_EVERY = 64


@dataclass(frozen=True)
class AnchorEntry:
    seq: int
    hash: str
    ts: str
    reason: str  # cadence | gold | compact


@dataclass
class AnchorReport:
    """What the anchors say about a chain. `unanchored` is a THIRD state, never folded into ok."""

    ok: bool
    checked: int
    #: True when there is no anchor file at all: the chain may be self-consistent, but nothing
    #: external corroborates it. Callers MUST NOT read this as ok — that is the whole point.
    unanchored: bool = False
    mismatches: list[dict[str, Any]] = field(default_factory=list)

    @property
    def verdict(self) -> str:
        if self.unanchored:
            return "consistent, unanchored"
        return "anchored" if self.ok else "ANCHOR MISMATCH"


class AnchorLog:
    """One culture's anchor file. Append-only, fsync'd before the caller is told the write landed."""

    def __init__(self, home: Path | str, culture: str, *, anchor_every: int = DEFAULT_ANCHOR_EVERY,
                 fsync: bool = True) -> None:
        self.dir = Path(home) / "_anchor"
        self.dir.mkdir(parents=True, exist_ok=True)
        # A culture name can contain `/` (run-scoped rooms); the file name must stay one path
        # segment, so separators are folded. Distinctness is preserved because `culture` also rides
        # INSIDE every entry — the file name is an index, never the identity.
        self.culture = culture
        self.path = self.dir / f"{culture.replace('/', '~')}.jsonl"
        self.anchor_every = anchor_every
        self.fsync = fsync
        self._since = 0

    # ---------------------------------------------------------------- writing

    def note(self, seq: int, chain_hash: str, *, gold: bool = False, compact: bool = False) -> AnchorEntry | None:
        """Offer a (seq, hash) checkpoint. Returns the entry if one was written, else None.

        Gold and compact records anchor UNCONDITIONALLY and synchronously — the durability edge and
        the anchor-before-effect law both depend on the entry being on disk before the caller
        proceeds. Everything else anchors on the cadence.
        """
        self._since += 1
        due = gold or compact or self._since >= self.anchor_every
        if not due:
            return None

        reason = "gold" if gold else ("compact" if compact else "cadence")
        entry = AnchorEntry(seq=seq, hash=chain_hash, ts=clock.now_iso(), reason=reason)
        self._append(entry)
        self._since = 0
        return entry

    def _append(self, entry: AnchorEntry) -> None:
        """Write and fsync. The fsync is not optional for gold, so it is not optional here."""
        line = json.dumps(
            {"seq": entry.seq, "hash": entry.hash, "ts": entry.ts,
             "culture": self.culture, "reason": entry.reason},
            ensure_ascii=False,
        )
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
            f.flush()
            if self.fsync:
                os.fsync(f.fileno())

    # ---------------------------------------------------------------- reading / checking

    def entries(self) -> list[AnchorEntry]:
        """Every checkpoint, oldest first. A torn final line is dropped — a half-anchor is not one."""
        if not self.path.exists():
            return []
        out: list[AnchorEntry] = []
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                if not line.endswith("\n"):
                    break
                text = line.strip()
                if not text:
                    continue
                try:
                    rec = json.loads(text)
                except json.JSONDecodeError:
                    break
                out.append(AnchorEntry(int(rec["seq"]), str(rec["hash"]), str(rec.get("ts", "")),
                                       str(rec.get("reason", "cadence"))))
        return out

    def check(
        self, hashes_by_seq: dict[int, str], *, compacted_spans: list[tuple[int, int]] | None = None
    ) -> AnchorReport:
        """Match every anchor against the log's CURRENT hash at that seq.

        `hashes_by_seq` comes from the live log. A rewrite that recomputed the chain leaves the log
        self-consistent and every anchored seq disagreeing — which is exactly the class of tamper a
        chain alone cannot see.

        **A missing anchored seq is a mismatch UNLESS a compacted span covers it.** Compaction
        legitimately deletes anchored records (a cadence anchor lands every 64 messages, and chatter
        evaporates), and the `compact` record's own anchor is what covers the hole thereafter
        (§9.2 step 7). But the excuse is narrow on purpose: a seq that is simply absent, with no
        compact record claiming it, stays a mismatch — otherwise deletion would erase the evidence
        of deletion, and "the anchor does not match because the record is gone" would be a
        self-issued licence to lose records. (Found end to end: the first real compaction deleted
        two anchored seqs and the anchors correctly-but-uselessly cried tamper.)
        """
        entries = self.entries()
        if not entries:
            return AnchorReport(ok=True, checked=0, unanchored=True)

        spans = compacted_spans or []

        def covered(seq: int) -> bool:
            return any(a <= seq <= b for a, b in spans)

        mismatches = [
            {"seq": e.seq, "anchored": e.hash, "found": hashes_by_seq.get(e.seq), "reason": e.reason}
            for e in entries
            if hashes_by_seq.get(e.seq) != e.hash and not (e.seq not in hashes_by_seq and covered(e.seq))
        ]
        return AnchorReport(ok=not mismatches, checked=len(entries), mismatches=mismatches)
