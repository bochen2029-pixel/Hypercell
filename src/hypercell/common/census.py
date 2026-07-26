"""The contract census — the 9-tuple of versions this code implements (contracts/nucleus.md §1).

Every genesis record carries this. A ledger that cannot say which contract versions wrote it is not
migratable, which is the lived G3 defect; and because the census is written *in-chain*, it is
tamper-evident rather than a comment.

`tests/test_contract_headers.py` asserts this dict matches `contracts/*.md` on disk, so bumping a
contract without teaching the code about it fails CI instead of silently writing a lie into every
new ledger.
"""
from __future__ import annotations

from types import MappingProxyType
from typing import Final

#: The closed inventory (pairing law H2) and the version of each that this build implements.
CENSUS: Final[MappingProxyType[str, str]] = MappingProxyType(
    {
        "wire": "5.1.0",
        "nucleus": "5.1.0",
        "role": "5.1.0",
        "run": "5.1.0",
        "oracle": "5.1.0",
        "act": "5.1.0",
        "pricebook": "5.1.0",
        "command": "5.1.0",
        "identity-firewall": "5.1.0",
    }
)


def census() -> dict[str, str]:
    """A mutable copy for embedding in a genesis body."""
    return dict(CENSUS)
