"""`fs.read` — the local read channel. No network, no credentials, one refusal that matters."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from . import AdapterError, scrub


def execute(args: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    """Read a file inside the sandbox root. Escaping the root is the whole threat model here."""
    root = Path(os.environ.get("HYPERCELL_FS_ROOT", ".")).resolve()
    target = (root / str(args["path"])).resolve()

    # A path that resolves outside the root is refused whatever it looks like: `..`, a symlink, an
    # absolute path, or a clever mix. Resolving FIRST and comparing after is the only check that
    # survives all three.
    if not target.is_relative_to(root):
        raise AdapterError(f"path escapes the sandbox root: {args['path']}")
    if not target.is_file():
        raise AdapterError(f"no such file: {args['path']}")

    content = target.read_text(encoding="utf-8", errors="replace")
    provenance = scrub({"channel": "tool_result", "adapter": "fs.read", "path": str(target.relative_to(root))})
    return content, "text/plain", provenance
