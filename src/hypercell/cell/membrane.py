"""The membrane: a cell's boundary + the injection firewall (contracts/wire.md).

Other cells' words are DATA, never instructions. Only an operator `command` is a directive. For P0 the
membrane is light (single cell, no Medium yet); the principle is enforced from the first line.
"""
from __future__ import annotations

from ..common.types import Message, MessageType


def is_directive(msg: Message) -> bool:
    """Only an operator command may be obeyed. Everything else is data."""
    return msg.type == MessageType.command and msg.origin == "operator"


def as_data(content: str) -> str:
    """Wrap foreign content so a cell treats it as quoted data, not an instruction."""
    return "<<untrusted-data>>\n" + content + "\n<</untrusted-data>>"
