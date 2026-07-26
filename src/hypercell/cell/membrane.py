"""The membrane: a cell's boundary + the injection firewall (contracts/wire.md).

Other cells' words are DATA, never instructions. Only an operator `command` is a directive. For P0 the
membrane is light (single cell, no Medium yet); the principle is enforced from the first line.
"""
from __future__ import annotations

import re
from typing import Any

from ..common.types import Message, MessageType


def is_directive(msg: Message) -> bool:
    """Only an operator command may be obeyed. Everything else is data."""
    return msg.type == MessageType.command and msg.origin == "operator"


def as_data(content: str) -> str:
    """Wrap foreign content so a cell treats it as quoted data, not an instruction."""
    return "<<untrusted-data>>\n" + content + "\n<</untrusted-data>>"


# ---------------------------------------------------------------------------- redaction (N2′)

#: Credential shapes worth catching before they are written down. Deliberately conservative: a
#: false positive costs a redacted string in a log, a false negative costs a leaked key forever.
_SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("openai", re.compile(r"\bsk-[A-Za-z0-9_-]{16,}")),
    ("anthropic", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{16,}")),
    ("bearer", re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/-]{16,}=*")),
    ("aws", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("github", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{16,}")),
    ("private-key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("env-assign", re.compile(r"(?i)\b(?:api[_-]?key|secret|token|password|passwd)\s*[=:]\s*\S{8,}")),
    ("url-userinfo", re.compile(r"\b[a-z][a-z0-9+.-]*://[^\s/@]+:[^\s/@]+@")),
)

REDACTED = "[REDACTED:{kind}]"


def redact(value: Any) -> tuple[Any, list[str]]:
    """Strip credential-shaped text. Returns `(clean, kinds_found)`.

    **L-REDACT-BEFORE-CANON (MUST).** This runs BEFORE the record is canonicalized and hashed, so
    the leaf — and therefore the chain, the anchor, and every Merkle root over it — is computed over
    post-redaction bytes only. **The chain never witnesses a secret.**

    The placement is not a preference. An append-only log cannot un-say a secret: once a key is in
    the ledger it is in every replica, every backup and every verified hash forever, and `verify()`
    would then require the secret to re-derive the chain. The only correct place is before the
    append. [SECURITY-SEAM: redaction]
    """
    found: list[str] = []

    def _scrub(v: Any) -> Any:
        if isinstance(v, str):
            out = v
            for kind, pattern in _SECRET_PATTERNS:
                if pattern.search(out):
                    found.append(kind)
                    out = pattern.sub(REDACTED.format(kind=kind), out)
            return out
        if isinstance(v, dict):
            return {k: _scrub(x) for k, x in v.items()}
        if isinstance(v, list):
            return [_scrub(x) for x in v]
        return v

    return _scrub(value), sorted(set(found))
