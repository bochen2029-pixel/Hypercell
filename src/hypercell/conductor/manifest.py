"""Manifest freeze — a run is governed by the bytes it started with (slice RE-2).

**The null is live behavior: re-read the yaml on every open.** So an operator who edits `run.yaml`
while a run is parked — or who edits it a week later and resumes — silently changes the rules the
run has already been playing by. Rounds one and two ran under one target and stable_k; round three
runs under another; the certificate reports a single manifest that never existed as a whole.

That is not a hypothetical about carelessness. Editing a config file is the most natural thing an
operator does, and nothing in the old design told them it mattered.

So `hc apply` **freezes**: the exact bytes are written once, hashed, and every later open reads the
frozen copy. Two consequences, both deliberate:

* **A resume runs under the frozen bytes**, whatever the file on disk now says.
* **Re-applying a MUTATED file under the same `run_id` is REFUSED.** Not silently re-frozen, not
  merged — refused, with the two digests printed. A run id names a run, and a run is its manifest;
  changing one while keeping the other would make `manifest_sha256` on the certificate a number that
  points at nothing.

Re-applying an IDENTICAL file is fine and idempotent — replaying a command must not be an error, or
every retry becomes a decision.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from ..common import clock


class ManifestConflict(Exception):
    """A re-apply whose bytes differ from the frozen manifest for this run_id."""


@dataclass(frozen=True)
class FrozenManifest:
    run_id: str
    sha256: str
    raw: str
    frozen_at: str

    @property
    def data(self) -> dict[str, Any]:
        """The parsed manifest — parsed from the FROZEN bytes, never from the file on disk."""
        parsed = yaml.safe_load(self.raw)
        return parsed if isinstance(parsed, dict) else {}


def digest(raw: str) -> str:
    """Over the raw bytes, not the parsed structure.

    Deliberate: two files that parse the same but differ in comments or key order are still
    different manifests to an auditor reading them, and the operator's intent lives in the bytes.
    """
    return "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _dir(home: Path | str, run_id: str) -> Path:
    return Path(home) / "_runs" / run_id


def frozen_path(home: Path | str, run_id: str) -> Path:
    return _dir(home, run_id) / "manifest.frozen.yaml"


def load_frozen(home: Path | str, run_id: str) -> FrozenManifest | None:
    path = frozen_path(home, run_id)
    if not path.exists():
        return None
    raw = path.read_text(encoding="utf-8")
    meta_path = path.with_suffix(".meta.yaml")
    meta = yaml.safe_load(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    return FrozenManifest(
        run_id=run_id,
        sha256=str(meta.get("sha256") or digest(raw)),
        raw=raw,
        frozen_at=str(meta.get("frozen_at", "")),
    )


def freeze(home: Path | str, run_id: str, raw: str) -> FrozenManifest:
    """Freeze these bytes for this run_id, or refuse if a DIFFERENT manifest is already frozen."""
    incoming = digest(raw)
    existing = load_frozen(home, run_id)

    if existing is not None:
        if existing.sha256 == incoming:
            return existing  # idempotent: replaying a command must not be an error
        raise ManifestConflict(
            f"run '{run_id}' is already frozen under {existing.sha256[:23]}... but the file now "
            f"hashes to {incoming[:23]}.... A run id names a run, and a run IS its manifest — "
            f"re-applying mutated bytes under the same id would make the certificate's "
            f"manifest_sha256 point at something that never ran. Use a new run_id, or restore the "
            f"frozen copy at {frozen_path(home, run_id)}."
        )

    target = frozen_path(home, run_id)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(raw, encoding="utf-8")
    frozen_at = clock.now_iso()
    target.with_suffix(".meta.yaml").write_text(
        yaml.safe_dump({"run_id": run_id, "sha256": incoming, "frozen_at": frozen_at}),
        encoding="utf-8",
    )
    return FrozenManifest(run_id=run_id, sha256=incoming, raw=raw, frozen_at=frozen_at)


def apply_file(home: Path | str, path: Path | str) -> FrozenManifest:
    """Read a manifest file and freeze it. The only door into a run."""
    raw = Path(path).read_text(encoding="utf-8")
    parsed = yaml.safe_load(raw)
    if not isinstance(parsed, dict) or not parsed.get("run_id"):
        raise ManifestConflict(f"{path} has no run_id; a manifest without one cannot be frozen")
    return freeze(home, str(parsed["run_id"]), raw)


def open_run(home: Path | str, run_id: str) -> FrozenManifest:
    """Open an existing run under its FROZEN bytes. Never re-reads the operator's file."""
    frozen = load_frozen(home, run_id)
    if frozen is None:
        raise ManifestConflict(
            f"no frozen manifest for run '{run_id}' — apply it first. Resuming from whatever the "
            "yaml says today is the behaviour this slice exists to remove."
        )
    return frozen


def verify(home: Path | str, run_id: str) -> tuple[bool, str]:
    """`hc verify`: do the frozen bytes still hash to what was recorded at apply time?"""
    frozen = load_frozen(home, run_id)
    if frozen is None:
        return False, f"no frozen manifest for run '{run_id}'"
    actual = digest(frozen.raw)
    if actual != frozen.sha256:
        return False, f"frozen manifest was edited in place: recorded {frozen.sha256}, now {actual}"
    return True, f"manifest frozen at {frozen.frozen_at}, {frozen.sha256[:23]}..."
