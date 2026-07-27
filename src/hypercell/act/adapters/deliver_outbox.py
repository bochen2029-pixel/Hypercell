"""`deliver.outbox` — delivery is an ACT (contracts/act.md; falsifier DELIVER-1).

**The null is a direct file write.** A cell (or a surface) writes the message out and moves on: no
gate, no receipt, no dedup key, and no way afterwards to answer "did this go out, and once?". Crash
between the write and whatever recorded it and you have a delivery nobody can account for — or two.

Delivery is the cheapest place to see why H1 needs the whole pipeline, because the world remembers
it and the fabric cannot take it back. Three things this adapter does that a file write does not:

* **Two-phase, fsync between.** The payload is written to a temp file and fsynced, then linked into
  the outbox under a name derived from the effect key. `os.link` is atomic and **fails if the name
  already exists**, so the filesystem itself refuses the second send — the crash window between
  "wrote" and "recorded" cannot produce a duplicate, because the second attempt cannot claim the
  name. The directory is fsynced after, so the link survives the power going out.
* **A digest-verified manifest.** Every entry carries the payload's sha256 and the manifest carries
  a digest over all entries in key order. A manifest that disagrees with the files on disk is
  detectable rather than merely wrong, and `verify_outbox()` says which entry drifted.
* **Narration from receipts only.** `sent()` reads the manifest, which is written from the delivery,
  not from an intention. `hc talk` narrating from anything else would let the fabric claim a send
  that never left.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from ...common.canon import canon_bytes
from . import AdapterError, scrub

OUTBOX_ENV = "HYPERCELL_OUTBOX"


class DoubleSend(AdapterError):
    """The same effect key tried to deliver twice. The filesystem refused; so do we, loudly."""


def outbox_dir() -> Path:
    root = Path(os.environ.get(OUTBOX_ENV, "./_outbox"))
    root.mkdir(parents=True, exist_ok=True)
    return root


def _entry_name(effect_key: str) -> str:
    """The filename IS the dedup key, hashed so a key with a slash still names one file."""
    return hashlib.sha256(effect_key.encode("utf-8")).hexdigest()[:32] + ".json"


def execute(args: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    """Deliver once. `effect_key` is supplied by the executor after it wins the reservation.

    The executor has already reserved the key, so under normal operation this cannot collide. The
    link check is here anyway: the reservation lives in the Conductor's database and the delivery
    lives on a filesystem, and a guarantee that spans two stores must be held on both sides or it
    is held on neither.
    """
    root = outbox_dir()
    effect_key = str(args.get("effect_key") or "")
    if not effect_key:
        raise AdapterError("deliver.outbox requires an effect_key; an unkeyed delivery cannot dedup")

    payload = {
        "to": str(args.get("to", "")),
        "subject": str(args.get("subject", "")),
        "body": str(args.get("body", "")),
        "effect_key": effect_key,
    }
    raw = canon_bytes(payload)
    sha = "sha256:" + hashlib.sha256(raw).hexdigest()
    final = root / _entry_name(effect_key)

    # ---- phase 1: durable bytes under a temp name.
    fd, tmp_name = tempfile.mkstemp(dir=root, suffix=".part")
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(raw)
            f.flush()
            os.fsync(f.fileno())

        # ---- phase 2: claim the name. Atomic, and it FAILS if taken -- that failure is the feature.
        try:
            os.link(tmp, final)
        except FileExistsError as exc:
            raise DoubleSend(
                f"a delivery for effect_key {effect_key[:24]}... is already in the outbox. "
                "The filesystem refused the second send; the first one stands."
            ) from exc
        _fsync_dir(root)
    finally:
        tmp.unlink(missing_ok=True)

    _append_manifest(root, effect_key, sha, payload)
    provenance = scrub(
        {"channel": "tool_result", "adapter": "deliver.outbox", "entry": final.name, "sha256": sha}
    )
    return json.dumps({"delivered": True, "sha256": sha, "entry": final.name}), "application/json", provenance


def _fsync_dir(path: Path) -> None:
    """A linked name that is not in a synced directory can vanish on power loss."""
    if os.name == "nt":
        return  # Windows offers no directory handle to fsync; the link itself is journaled by NTFS
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


# ---------------------------------------------------------------------------- the manifest


def manifest_path(root: Path | None = None) -> Path:
    return (root or outbox_dir()) / "manifest.json"


def _append_manifest(root: Path, effect_key: str, sha: str, payload: dict[str, Any]) -> None:
    """Rewrite the manifest with this entry included, then digest the whole thing.

    Rewritten rather than appended: the digest is over all entries in key order, so a partial
    append would leave a manifest whose digest describes a set it does not contain. Rewrite-and-
    replace makes the manifest atomic with respect to its own digest.
    """
    path = manifest_path(root)
    entries = read_manifest(root).get("entries", {})
    entries[effect_key] = {"sha256": sha, "to": payload["to"], "subject": payload["subject"],
                           "entry": _entry_name(effect_key)}
    doc = {"entries": entries, "digest": manifest_digest(entries)}
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def manifest_digest(entries: dict[str, Any]) -> str:
    """Over entries in KEY order — never insertion order, or two identical outboxes would differ."""
    return "sha256:" + hashlib.sha256(canon_bytes(entries)).hexdigest()


def read_manifest(root: Path | None = None) -> dict[str, Any]:
    path = manifest_path(root)
    if not path.exists():
        return {"entries": {}, "digest": manifest_digest({})}
    loaded: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return loaded


def verify_outbox(root: Path | None = None) -> tuple[bool, str]:
    """Does the manifest still describe the disk, in BOTH directions? Names the first drift.

    manifest->disk: a listed entry whose blob is missing or altered. disk->manifest: an ORPHAN blob
    the crash window between `os.link` and the manifest rewrite can leave -- a real delivery that
    narration cannot see, which one-directional verification would read as "clean".

    (The manifest rewrite is single-writer by design at T0: one executor principal per home. When
    the executor becomes a separate concurrent principal at d', the rewrite needs a lock or the
    manifest becomes a fold over the blobs -- the blobs already carry everything it records.)
    """
    root = root or outbox_dir()
    doc = read_manifest(root)
    entries: dict[str, Any] = doc.get("entries", {})

    recomputed = manifest_digest(entries)
    if doc.get("digest") != recomputed:
        recorded = str(doc.get("digest"))
        return False, f"manifest digest drifted: recorded {recorded[:23]}..., recomputed {recomputed[:23]}..."

    for key, meta in sorted(entries.items()):
        blob = root / str(meta["entry"])
        if not blob.exists():
            return False, f"manifest lists {key[:24]}... but {meta['entry']} is missing"
        actual = "sha256:" + hashlib.sha256(blob.read_bytes()).hexdigest()
        if actual != meta["sha256"]:
            return False, f"{meta['entry']} does not match its manifest digest"
    listed = {str(meta["entry"]) for meta in entries.values()}
    for blob in sorted(root.glob("*.json")):
        if blob.name == "manifest.json" or blob.name in listed:
            continue
        return False, (f"{blob.name} is in the outbox but not in the manifest - a delivery "
                       "narration cannot see (crash between link and manifest rewrite)")
    return True, f"outbox clean: {len(entries)} delivered, {recomputed[:23]}..."


def sent(root: Path | None = None) -> list[dict[str, Any]]:
    """What actually went out, read from the manifest — the only thing `hc talk` may narrate from.

    Not from the act journal: a journal records an intention, and an intention that crashed before
    the link landed is not a delivery. Narrating from intentions is how a fabric tells a user it
    sent something it did not.
    """
    entries = read_manifest(root).get("entries", {})
    return [dict(v, effect_key=k) for k, v in sorted(entries.items())]
