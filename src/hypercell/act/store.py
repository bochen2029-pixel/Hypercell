"""The content-addressed artifact store — evidence that cannot be edited after the fact.

Every byte an act brings back from the world is stored under `sha256(content)`. Two properties
follow, and both are load-bearing for GROUND-1:

* **A citation is a hash, so a citation cannot drift.** If the stored bytes change, the address
  changes, and the old address resolves to nothing. There is no "the page said that yesterday".
* **Identical content stores once.** Two cells fetching the same page share the artifact, which
  makes the digest a genuine identity rather than a per-fetch accident.

`act://<corr>` is the *receipt* pointer (what happened); `artifact://sha256=<hex>` is the *content*
pointer (what came back). Keeping them separate is what lets an evidence bundle prove a quote
without replaying the fetch.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Artifact:
    sha256: str
    bytes_len: int
    mime: str
    path: Path

    @property
    def uri(self) -> str:
        return f"artifact://sha256={self.sha256}"

    def read_text(self) -> str:
        return self.path.read_text(encoding="utf-8", errors="replace")


class ArtifactStore:
    """Write-once, addressed by content. A re-put of identical bytes is a no-op, not a duplicate."""

    def __init__(self, home: Path | str) -> None:
        self.dir = Path(home) / "_artifacts"
        self.dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def digest(content: str | bytes) -> str:
        raw = content.encode("utf-8") if isinstance(content, str) else content
        return hashlib.sha256(raw).hexdigest()

    def _paths(self, sha: str) -> tuple[Path, Path]:
        shard = self.dir / sha[:2]
        return shard / sha, shard / f"{sha}.meta.json"

    def put(self, content: str | bytes, *, mime: str = "text/plain") -> Artifact:
        raw = content.encode("utf-8") if isinstance(content, str) else content
        sha = self.digest(raw)
        blob, meta = self._paths(sha)
        blob.parent.mkdir(parents=True, exist_ok=True)
        if not blob.exists():
            blob.write_bytes(raw)
            meta.write_text(json.dumps({"sha256": sha, "bytes": len(raw), "mime": mime}), encoding="utf-8")
        return Artifact(sha256=sha, bytes_len=len(raw), mime=mime, path=blob)

    def get(self, sha_or_uri: str) -> Artifact | None:
        sha = sha_or_uri.removeprefix("artifact://sha256=").removeprefix("sha256:")
        blob, meta = self._paths(sha)
        if not blob.exists():
            return None
        info = json.loads(meta.read_text(encoding="utf-8")) if meta.exists() else {}
        return Artifact(
            sha256=sha,
            bytes_len=int(info.get("bytes", blob.stat().st_size)),
            mime=str(info.get("mime", "text/plain")),
            path=blob,
        )

    def verify(self, sha_or_uri: str) -> bool:
        """Re-hash the stored bytes. A store that never re-checks itself is a store you must trust."""
        art = self.get(sha_or_uri)
        return art is not None and self.digest(art.path.read_bytes()) == art.sha256
