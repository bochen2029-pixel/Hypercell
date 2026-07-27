"""Retention & compaction — evaporation with a Merkle-sound memory (wire.md §9; falsifier C12).

**The null is no compaction**: the log only grows. Safe, unbounded, and wrong in a way that takes
months to hurt — a blackboard nobody ever wipes locks the colony onto its earliest trails, because
every cell conditioning on the visible log sees a decade of chatter weighted equally with today's.
On an append-only blackboard **chatter decay IS the pheromone-evaporation parameter**; without it
you do not get a durable memory, you get a stuck one.

Evaporation is not amnesia. What evaporates is the *working set*; the audit path survives as Merkle
roots plus (optionally) archived envelopes, so a certificate still refolds and an archived record
can still be proven to have been there. Three laws carry that:

* **Anchor-before-effect** — fsync-before-effect applied to forgetting. The `compact` record is
  posted and anchored BEFORE a single row is deleted. A crash between the two leaves rows that are
  provably inside a compacted span (`zombies[]`), which housekeeping re-deletes; the reverse order
  would delete records whose only remaining evidence had not landed yet.
* **The pin rule** — R-decay and R-run rows are eligible only after the culture's terminal verdict.
  An open run pins its own span, because a run that is still going is still using its own history.
* **The cite-pin (keeper-aware delete)** — any record inside the evidence closure of a retained
  verdict SURVIVES, whatever its type or age. A keeper inside a span splits the span, and the chain
  reconnects per run. Promotion is a FOLD over verdict `evidence[]`, never a row mutation: a
  citation makes a record a keeper by being *read*, so nothing has to remember to mark it.

The Merkle construction is **RFC 6962** with domain separation (`0x00` leaf, `0x01` node) — the
prefixes are what stop a node hash from being replayed as a leaf hash, and the reason this is not
"just a hash tree".
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

#: R-forever: the provenance skeleton. Never eligible, at any age, in any culture (§9.1).
R_FOREVER = frozenset({
    "receipt", "verdict", "oracle_gen", "command", "compact", "cmd_receipt", "act_receipt", "act",
})
#: R-decay: TTL then dropped/archived. Everything else with a run scope is R-run.
R_DECAY = frozenset({"chat", "status"})

#: Default TTLs (§9.1). From the culture's genesis `retention_policy` in a full build.
DEFAULT_TTL_S: dict[str, float] = {"chat": 7 * 24 * 3600.0, "status": 24 * 3600.0}


# ---------------------------------------------------------------------------- RFC 6962 Merkle


def leaf_hash(data: bytes) -> bytes:
    """`sha256(0x00 || data)`. The domain prefix is not decoration: without it a node hash could be
    presented as a leaf hash and an inclusion proof would accept a subtree as a record."""
    return hashlib.sha256(b"\x00" + data).digest()


def node_hash(left: bytes, right: bytes) -> bytes:
    """`sha256(0x01 || left || right)`."""
    return hashlib.sha256(b"\x01" + left + right).digest()


def merkle_root(leaves: list[bytes]) -> bytes:
    """RFC 6962 root over pre-hashed leaves. Odd nodes carry up UNDUPLICATED.

    Duplicating an odd node (the Bitcoin convention) makes two different leaf-sets share a root,
    which is precisely the ambiguity an inclusion proof must not have.
    """
    if not leaves:
        return hashlib.sha256(b"").digest()
    level = list(leaves)
    while len(level) > 1:
        nxt: list[bytes] = []
        for i in range(0, len(level) - 1, 2):
            nxt.append(node_hash(level[i], level[i + 1]))
        if len(level) % 2:
            nxt.append(level[-1])  # carry, never duplicate
        level = nxt
    return level[0]


def inclusion_proof(leaves: list[bytes], index: int) -> list[tuple[str, bytes]]:
    """The audit path for `leaves[index]`: [(side, sibling_hash), ...], bottom-up."""
    if not 0 <= index < len(leaves):
        raise IndexError(f"leaf {index} is outside a tree of {len(leaves)}")
    path: list[tuple[str, bytes]] = []
    level = list(leaves)
    idx = index
    while len(level) > 1:
        nxt: list[bytes] = []
        for i in range(0, len(level) - 1, 2):
            if i == idx:
                path.append(("right", level[i + 1]))
            elif i + 1 == idx:
                path.append(("left", level[i]))
            nxt.append(node_hash(level[i], level[i + 1]))
        if len(level) % 2:
            nxt.append(level[-1])
            if idx == len(level) - 1:
                pass  # carried untouched; no sibling at this level
        idx //= 2 if idx < (len(level) // 2) * 2 else 1
        idx = min(idx, len(nxt) - 1)
        level = nxt
    return path


def verify_inclusion(leaf: bytes, path: list[tuple[str, bytes]], root: bytes) -> bool:
    """Re-fold the audit path and compare to the root."""
    cur = leaf
    for side, sibling in path:
        cur = node_hash(sibling, cur) if side == "left" else node_hash(cur, sibling)
    return cur == root


# ---------------------------------------------------------------------------- the algorithm


@dataclass(frozen=True)
class Run:
    """One maximal contiguous eligible span. `chain` reconnects the hole for `verify()`."""

    frm: int
    to: int
    count: int
    merkle_root: str
    chain_prev: str  # hash at frm-1 (the last retained record before the hole)
    chain_post: str  # hash at to    (the last record INSIDE the hole)

    def as_dict(self) -> dict[str, Any]:
        return {
            "from": self.frm, "to": self.to, "count": self.count,
            "merkle_root": self.merkle_root,
            "chain": {"prev": self.chain_prev, "post": self.chain_post},
        }


@dataclass
class CompactionPlan:
    """What compaction WOULD do. Computed before anything is posted or deleted, so the caller can
    anchor the record first and delete second — the anchor-before-effect law needs the plan to
    exist as a value, not as a side effect."""

    runs: list[Run] = field(default_factory=list)
    by_type: dict[str, int] = field(default_factory=dict)
    keepers: list[int] = field(default_factory=list)
    archive_ref: str | None = None

    @property
    def eligible_seqs(self) -> list[int]:
        return [s for r in self.runs for s in range(r.frm, r.to + 1)]

    def as_body(self, kind: str) -> dict[str, Any]:
        return {
            "kind": kind,
            "runs": [r.as_dict() for r in self.runs],
            "by_type": dict(self.by_type),
            "archive_ref": self.archive_ref,
        }


def retention_class(msg: dict[str, Any]) -> str:
    """R-forever | R-decay | R-run, from the type (and harm, for the act pair)."""
    t = str(msg.get("type", ""))
    if t in ("act", "act_receipt"):
        # H0 acts are R-run; H1+ are provenance and never evaporate (§9.1).
        body = msg.get("body")
        harm = str(body.get("harm_effective", "H0")) if isinstance(body, dict) else "H0"
        return "R-forever" if harm != "H0" else "R-run"
    if t in R_FOREVER:
        return "R-forever"
    if t in R_DECAY:
        return "R-decay"
    if t == "presence":
        body = msg.get("body")
        phase = str(body.get("phase", "")) if isinstance(body, dict) else ""
        return "R-forever" if phase == "genesis" else "R-run"
    return "R-run"


def evidence_closure(messages: list[dict[str, Any]]) -> set[int]:
    """Every seq cited by a retained `verdict`'s evidence — the cite-pins.

    A FOLD over verdict bodies, never a stored flag: a record becomes a keeper by being cited, so
    nothing needs to have remembered to mark it at write time. `medium://<culture>/<seq>` and bare
    integers are both accepted, because the evidence scheme grew a URI form after the first cites
    were written and an audit must survive its own vocabulary changing.
    """
    pinned: set[int] = set()
    for msg in messages:
        if str(msg.get("type")) != "verdict":
            continue
        body = msg.get("body")
        if not isinstance(body, dict):
            continue
        for item in body.get("evidence", []) or []:
            ref = item.get("locator", item) if isinstance(item, dict) else item
            if isinstance(ref, int):
                pinned.add(ref)
            elif isinstance(ref, str) and ref.startswith("medium://"):
                tail = ref.rsplit("/", 1)[-1]
                if tail.isdigit():
                    pinned.add(int(tail))
    return pinned


def plan_compaction(
    messages: list[dict[str, Any]],
    *,
    now_s: float,
    sealed_head: int,
    has_open_run: bool,
    ttl_s: dict[str, float] | None = None,
    age_s: dict[int, float] | None = None,
) -> CompactionPlan:
    """Steps 1–3: select the eligible set, partition into maximal contiguous runs, root each one.

    Returns an EMPTY plan when the culture has an open run — the pin rule, and the one case where
    doing nothing is the whole correct answer.
    """
    plan = CompactionPlan()
    if has_open_run:
        return plan

    ttl = {**DEFAULT_TTL_S, **(ttl_s or {})}
    pinned = evidence_closure(messages)
    by_seq = {int(m["seq"]): m for m in messages}

    eligible: list[int] = []
    for msg in messages:
        seq = int(msg["seq"])
        cls = retention_class(msg)
        if cls == "R-forever" or seq > sealed_head:
            continue
        if seq in pinned:
            plan.keepers.append(seq)  # the cite-pin: survives whatever its type or age
            continue
        aged = (age_s or {}).get(seq, 0.0)
        if cls == "R-decay" and aged < ttl.get(str(msg.get("type")), 0.0):
            continue  # not yet expired
        eligible.append(seq)
        plan.by_type[str(msg.get("type"))] = plan.by_type.get(str(msg.get("type")), 0) + 1

    # Step 2: maximal contiguous runs. A keeper inside a span SPLITS it, which falls out of
    # contiguity for free — that is why the split is not a special case anywhere below.
    for frm, to in _contiguous(sorted(eligible)):
        leaves = [leaf_hash(_canon_leaf(by_seq[s])) for s in range(frm, to + 1)]
        prev = by_seq.get(frm - 1, {}).get("hash", "") if frm > 1 else "genesis"
        plan.runs.append(
            Run(frm=frm, to=to, count=to - frm + 1,
                merkle_root="sha256:" + merkle_root(leaves).hex(),
                chain_prev=str(prev), chain_post=str(by_seq[to].get("hash", "")))
        )
    return plan


def _contiguous(seqs: list[int]) -> list[tuple[int, int]]:
    runs: list[tuple[int, int]] = []
    for s in seqs:
        if runs and s == runs[-1][1] + 1:
            runs[-1] = (runs[-1][0], s)
        else:
            runs.append((s, s))
    return runs


def _canon_leaf(msg: dict[str, Any]) -> bytes:
    """The bytes a Merkle leaf commits to: the record's stored chain hash.

    Committing to the CHAIN hash rather than re-canonicalising the envelope means the Merkle root
    and the chain agree by construction — an archived record proves membership against the same
    number `verify()` was already checking, so the two mechanisms cannot drift into disagreeing
    about the same record.
    """
    return str(msg.get("hash", "")).encode("utf-8")


def archive_runs(
    home: Path | str, culture: str, plan: CompactionPlan, messages: list[dict[str, Any]], *, date: str
) -> str:
    """Step 4: append the runs' full envelopes to `archive/<culture>/<date>.jsonl` and fsync.

    Written BEFORE the compact record is posted, so the archive can never be the thing that is
    missing when the record says it exists.
    """
    import os

    adir = Path(home) / "_archive" / culture.replace("/", "~")
    adir.mkdir(parents=True, exist_ok=True)
    path = adir / f"{date}.jsonl"
    wanted = set(plan.eligible_seqs)
    with open(path, "a", encoding="utf-8") as f:
        for msg in messages:
            if int(msg["seq"]) in wanted:
                f.write(json.dumps(msg, ensure_ascii=False, default=str) + "\n")
        f.flush()
        os.fsync(f.fileno())
    return str(path)


def read_archive(home: Path | str, culture: str, date: str) -> list[dict[str, Any]]:
    path = Path(home) / "_archive" / culture.replace("/", "~") / f"{date}.jsonl"
    if not path.exists():
        return []
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                out.append(json.loads(line))
    return out


def prove_archived(archived: list[dict[str, Any]], run: Run, seq: int) -> tuple[list[tuple[str, bytes]], bytes, bytes]:
    """An inclusion proof that `seq` was in `run`. Returns (path, leaf, root)."""
    in_run = [m for m in archived if run.frm <= int(m["seq"]) <= run.to]
    in_run.sort(key=lambda m: int(m["seq"]))
    leaves = [leaf_hash(_canon_leaf(m)) for m in in_run]
    idx = next(i for i, m in enumerate(in_run) if int(m["seq"]) == seq)
    root = bytes.fromhex(run.merkle_root.removeprefix("sha256:"))
    return inclusion_proof(leaves, idx), leaves[idx], root


def find_zombies(retained_seqs: list[int], compact_records: list[dict[str, Any]]) -> list[int]:
    """Rows provably inside a compacted span — a crash between step 5 and step 6 (§9.2).

    Reported rather than silently re-deleted here: `verify()` names them and housekeeping acts. A
    verifier that quietly cleaned up would be mutating the log it is supposed to be auditing.
    """
    spans: list[tuple[int, int]] = []
    for rec in compact_records:
        body = rec.get("body")
        if not isinstance(body, dict):
            continue
        for run in body.get("runs", []) or []:
            spans.append((int(run["from"]), int(run["to"])))
    return [s for s in retained_seqs if any(a <= s <= b for a, b in spans)]


# ---------------------------------------------------------------------------- the driver


def compact(
    medium: Any,
    culture: str,
    *,
    home: Path | str,
    now_s: float = 0.0,
    has_open_run: bool = False,
    age_s: dict[int, float] | None = None,
    policy: str = "archive",
    date: str = "0000-00-00",
    ttl_s: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Run §9.2 end to end: plan → archive → post+anchor the record → THEN delete. Idempotent.

    The step order is the whole safety argument. Archiving before posting means the record can never
    describe an archive that does not exist; posting-and-anchoring before deleting means the
    evidence of a deletion is durable before the deletion happens. Reversing either turns a crash
    into unrecoverable loss instead of a re-runnable interruption.
    """
    messages = medium.read(culture)
    sealed_head = max((int(m["seq"]) for m in messages), default=0)
    plan = plan_compaction(
        messages, now_s=now_s, sealed_head=sealed_head, has_open_run=has_open_run,
        ttl_s=ttl_s, age_s=age_s,
    )
    if not plan.runs:
        return {"compacted": 0, "runs": [], "reason": "nothing eligible (pin rule or no expiry)"}

    # Step 4: archive first -- the record must never point at bytes that are not there yet.
    if policy == "archive":
        plan.archive_ref = archive_runs(home, culture, plan, messages, date=date)

    # Step 5: ONE compact record, D-gold, so posting it anchors it (the transport's post path
    # anchors `compact` unconditionally).
    posted = medium.post(culture, "conductor", "compact", body=plan.as_body(policy))

    # Step 6: only NOW is deletion safe.
    deleted = medium.delete_range(culture, plan.eligible_seqs)
    return {
        "compacted": deleted,
        "runs": [r.as_dict() for r in plan.runs],
        "keepers": plan.keepers,
        "compact_seq": posted.seq,
        "archive_ref": plan.archive_ref,
    }
