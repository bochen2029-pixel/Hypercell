"""H0 adapters — the three structurally read-only channels GROUND-0 ships.

Each returns `(content, mime, provenance)`. **Provenance is scrubbed before it leaves here**
(ACT-SCRUB-1): an adapter knows its own credentials, and a receipt must not.

`web.search` and `web.fetch` resolve against a **hermetic fixture corpus** when
`HYPERCELL_GROUNDED_CORPUS` points at one. That is not only a test convenience — it is how the
grounding drills stay deterministic and how a developer runs the act plane with no network and no
keys. Live HTTP is the same code path with a different resolver.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

CORPUS_ENV = "HYPERCELL_GROUNDED_CORPUS"

#: Credential shapes scrubbed out of provenance before a receipt ever sees them.
_SECRET = re.compile(
    r"(?i)(bearer\s+\S+|sk-[A-Za-z0-9_-]{12,}|gh[pousr]_[A-Za-z0-9]{12,}|AKIA[0-9A-Z]{16}"
    r"|(api[_-]?key|token|secret|password|access_token)=[^&\s]+)"
)

_SECRET_KEY = re.compile(r"(?i)\b(authorization|api[_-]?key|token|secret|password|cookie|session)\b")


class AdapterError(Exception):
    """The world did not answer. A receipt still gets written — a failed act is an act."""


def scrub(value: Any) -> Any:
    """Remove credential bytes from anything bound for a receipt or an evidence bundle.

    Adapters hold keys; receipts must not. The scrub runs at the adapter boundary rather than at the
    receipt writer, because by the time a value reaches a writer it may already have been copied
    somewhere else — and an append-only log cannot un-say a secret (L-REDACT-BEFORE-CANON).
    """
    if isinstance(value, str):
        return _SECRET.sub("[SCRUBBED]", value)
    if isinstance(value, dict):
        return {k: ("[SCRUBBED]" if _SECRET_KEY.search(k) else scrub(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [scrub(v) for v in value]
    return value


def corpus_dir() -> Path | None:
    raw = os.environ.get(CORPUS_ENV)
    return Path(raw) if raw and Path(raw).exists() else None
