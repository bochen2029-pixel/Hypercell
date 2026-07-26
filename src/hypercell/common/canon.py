"""RFC 8785 (JCS) canonical JSON — the ONE canon, shared by the Medium chain and every nucleus.

The hash chain is only tamper-evident if two independent implementations agree, byte for byte, on
what a record *is*. That agreement is this module. `contracts/wire.md` §5.1 is its one home:

    leaf_n = sha256( canon(record sans `hash`/`sig`) )

Three rules do the work:

* **keys sort by UTF-16 code unit**, not by Python code point — they differ above the BMP, and a
  chain that disagrees there is a chain that fails on emoji;
* **absent and null are identical** — `None` values are dropped, so an omitted field and an
  explicit null hash the same (wire.md §5.1);
* **numbers serialize as ECMAScript would**, so `1.0` is `1` and never `1.0`.

Where a value cannot be canonicalized unambiguously — NaN, Infinity, or an integer beyond IEEE-754's
exact range — this module **raises** rather than emitting bytes another implementation might
reproduce differently. A chain that silently disagrees is worse than one that refuses to form.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any

#: Beyond this, IEEE-754 doubles (what JSON numbers *are*) can no longer represent every integer,
#: so two implementations may disagree on the value itself, never mind its spelling.
_MAX_EXACT_INT = 2**53 - 1

#: JCS mandates these two-character escapes and \u00xx for the remaining control characters.
_ESCAPES = {
    0x08: "\\b",
    0x09: "\\t",
    0x0A: "\\n",
    0x0C: "\\f",
    0x0D: "\\r",
    0x22: '\\"',
    0x5C: "\\\\",
}

_EXP = re.compile(r"^(-?)(\d)(?:\.(\d+))?e([+-])(\d+)$")


def _utf16_key(s: str) -> tuple[int, ...]:
    """Sort key over UTF-16 code units (JCS §3.2.3). Non-BMP chars sort as their surrogate pair."""
    raw = s.encode("utf-16-be")
    return tuple(int.from_bytes(raw[i : i + 2], "big") for i in range(0, len(raw), 2))


def _string(s: str) -> str:
    out = ['"']
    for ch in s:
        cp = ord(ch)
        if cp in _ESCAPES:
            out.append(_ESCAPES[cp])
        elif cp < 0x20:
            out.append(f"\\u{cp:04x}")
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def _number(v: int | float) -> str:
    """ECMAScript `Number::toString` for the values JSON can carry."""
    if isinstance(v, int):
        if abs(v) > _MAX_EXACT_INT:
            raise ValueError(
                f"integer {v} exceeds IEEE-754 exact range (2^53-1); JSON numbers are doubles, so "
                "no two implementations can be trusted to agree on it — carry it as a string"
            )
        return str(v)

    if v != v or v in (float("inf"), float("-inf")):
        raise ValueError(f"{v!r} is not representable in JSON; canon refuses to guess")

    if v == 0.0:
        return "0"  # ES6 renders -0 as "0" too
    if v.is_integer() and abs(v) < 1e21:
        return str(int(v))

    text = repr(v)
    m = _EXP.match(text)
    if m:
        # Python spells exponents "1e+21"/"1e-07"; ECMAScript spells them "1e+21"/"1e-7" — the
        # mantissa agrees, only the zero-padded exponent differs.
        sign, lead, frac, esign, digits = m.groups()
        mantissa = f"{lead}.{frac}" if frac else lead
        return f"{sign}{mantissa}e{esign}{int(digits)}"
    return text


def _value(v: Any) -> str:
    if v is None:
        return "null"
    if v is True:
        return "true"
    if v is False:
        return "false"
    if isinstance(v, str):
        return _string(v)
    if isinstance(v, (int, float)):
        return _number(v)
    if isinstance(v, (list, tuple)):
        return "[" + ",".join(_value(x) for x in v) + "]"
    if isinstance(v, dict):
        # Absent == null (wire.md §5.1): drop None members so an omitted field and an explicit
        # null produce identical bytes, and therefore an identical leaf.
        items = [(k, x) for k, x in v.items() if x is not None]
        for k, _ in items:
            if not isinstance(k, str):
                raise ValueError(f"object key {k!r} is not a string; JSON objects are string-keyed")
        items.sort(key=lambda kv: _utf16_key(kv[0]))
        return "{" + ",".join(f"{_string(k)}:{_value(x)}" for k, x in items) + "}"
    raise TypeError(f"{type(v).__name__} has no canonical JSON form; convert it before hashing")


def canon(value: Any) -> str:
    """The canonical JSON text of `value` (RFC 8785). Deterministic across implementations."""
    return _value(value)


def canon_bytes(value: Any) -> bytes:
    """`canon` as UTF-8 — what actually gets hashed."""
    return canon(value).encode("utf-8")


def digest(value: Any) -> bytes:
    """sha256 over the canonical form. The raw 32 bytes, for chaining."""
    return hashlib.sha256(canon_bytes(value)).digest()
