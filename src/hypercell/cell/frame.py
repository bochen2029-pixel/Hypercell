"""`frame_v1` — the deterministic frame assembler (contracts/identity-firewall.md; slice SEC-a′).

Every token block placed into a cell's context carries a `trust_tag` assigned from the channel its
bytes arrived on. The assembler is the thing that makes that structural rather than stylistic.

**Why structural separation and not delimiters.** v1 wrapped foreign text in
`<<untrusted-data>> … <</untrusted-data>>` and concatenated everything into one string. That is a
*string* boundary, and a string boundary can be forged: content containing the closing marker walks
straight out of its own fence and the next line reads as operator instruction. No amount of cleverer
delimiters fixes this — the attacker gets to write the bytes.

So `frame_v1` never concatenates control and data into one buffer. Control blocks and data blocks
live in **separate structures** all the way to the provider API, where they become separate messages.
There is no in-band escape sequence because there is no in-band. `as_data()` survives as a redundant
render — belt and braces — but it is no longer what carries the guarantee.

The assembly algorithm, numbered and versioned:

1. Pull the operator directive (if any) from the `command` channel → `trust_tag: control`. **At most
   one** control directive per frame: the active command.
2. Pull every other block as `trust_tag: data`, each carrying its provenance.
3. A `data` block MUST NOT be promotable to `control` by its own content.
4. `own_nucleus` factual memories are data with a `trust_floor` from their terminal trust tags.
5. The assembled frame is hashable, so a percept is reproducible.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

from ..common.canon import canon_bytes
from ..common.trust import CONTROL_CHANNEL, Channel, TrustTag, assign_tag, strip_supplied_provenance

FRAME_VERSION = "frame_v1"


@dataclass(frozen=True)
class Provenance:
    channel: Channel
    source_ref: str = ""
    trust_floor: str = "external"


@dataclass(frozen=True)
class FrameBlock:
    """One unit of context assembly. The tag is assigned, never supplied."""

    trust_tag: TrustTag
    provenance: Provenance
    body: str
    fenced: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "trust_tag": self.trust_tag,
            "provenance": {
                "channel": self.provenance.channel,
                "source_ref": self.provenance.source_ref,
                "trust_floor": self.provenance.trust_floor,
            },
            "fenced": self.fenced,
            "body": self.body,
        }


@dataclass(frozen=True)
class Frame:
    """An assembled frame. `control` and `data` are separate fields — that separation IS the law."""

    identity: str
    control: FrameBlock | None
    data: list[FrameBlock] = field(default_factory=list)
    version: str = FRAME_VERSION

    @property
    def digest(self) -> str:
        payload = {
            "version": self.version,
            "identity": self.identity,
            "control": self.control.as_dict() if self.control else None,
            "data": [b.as_dict() for b in self.data],
        }
        return "sha256:" + hashlib.sha256(canon_bytes(payload)).hexdigest()

    def render_messages(self) -> list[dict[str, str]]:
        """Render to provider messages. **Control and data never share a message.**

        The structural guarantee is the *message boundary*, not the role name: text inside a JSON
        string cannot escape into a sibling message object, however it is written. A forged closing
        fence is just more characters in a value.

        Layout: identity as `system`; each data block as its own `user` message carrying its
        provenance, so a block whose text perfectly forges a system prompt still arrives labelled as
        what it is; and the operator directive **last**, unadorned, because it is the actual request
        and recency is where models look for it.

        The directive is a `user` message rather than a second `system` one for a plain reason: a
        request with no user turn is rejected by several OpenAI-compatible providers, and a security
        design that cannot make an API call is not deployed, which makes it worth nothing.
        """
        messages: list[dict[str, str]] = [{"role": "system", "content": self.identity}]
        for block in self.data:
            messages.append(
                {
                    "role": "user",
                    "content": (
                        f"[{block.provenance.channel} · trust={block.provenance.trust_floor}"
                        f"{' · ' + block.provenance.source_ref if block.provenance.source_ref else ''}]\n"
                        f"{block.body}"
                    ),
                }
            )
        if self.control is not None:
            messages.append({"role": "user", "content": self.control.body})
        return messages

    @property
    def control_text(self) -> str:
        """Everything the model will read as instruction. What SEC-1 asserts injections cannot enter."""
        parts = [self.identity]
        if self.control is not None:
            parts.append(self.control.body)
        return "\n".join(parts)


def assemble(
    *,
    identity: str,
    command: str | None = None,
    command_ref: str = "",
    blocks: list[tuple[Channel, str, str]] | None = None,
) -> Frame:
    """Assemble `frame_v1`. `blocks` are `(channel, source_ref, body)` triples.

    A caller cannot hand in a control block: the tag comes from the channel, and the only control
    channel is the operator command, which arrives as `command`. That is not a convention this
    function follows — it is the only shape the signature permits.
    """
    control: FrameBlock | None = None
    if command is not None:
        control = FrameBlock(
            trust_tag="control",
            provenance=Provenance(channel=CONTROL_CHANNEL, source_ref=command_ref, trust_floor="operator"),
            body=command,
            fenced=False,
        )

    data: list[FrameBlock] = []
    for channel, source_ref, body in blocks or []:
        # Step 3, mechanically: whatever the channel claims to be, a non-command channel yields
        # `data`. An unknown channel also yields `data` (fail-closed).
        tag = assign_tag(channel)
        if tag == "control":
            # Reachable only if a caller passes the command channel in `blocks`. It is still not
            # promoted: control has exactly one source, and this is not it.
            tag = "data"
        clean_body, _ = strip_supplied_provenance({"body": body})
        data.append(
            FrameBlock(
                trust_tag=tag,
                provenance=Provenance(
                    channel=channel,
                    source_ref=source_ref,
                    trust_floor="operator" if channel == "own_nucleus" else "external",
                ),
                body=str(clean_body.get("body", body)) if isinstance(clean_body, dict) else body,
            )
        )

    return Frame(identity=identity, control=control, data=data)


# ---------------------------------------------------------------------------- the null, kept honest

FENCE_OPEN = "<<untrusted-data>>"
FENCE_CLOSE = "<</untrusted-data>>"


def render_string_wrap_null(identity: str, command: str | None, bodies: list[str]) -> str:
    """**The null**: v1's `as_data()` string wrap, concatenated into one buffer.

    Kept in the tree on purpose. SEC-1 runs the same injection battery against this and against
    `frame_v1`, and the bar requires that this one LEAKS — a null that never loses is not a null,
    it is a second implementation nobody is measuring.
    """
    parts = [identity]
    if command is not None:
        parts.append(command)
    for body in bodies:
        parts.append(f"{FENCE_OPEN}\n{body}\n{FENCE_CLOSE}")
    return "\n".join(parts)


def escapes_the_fence(rendered: str, needle: str) -> bool:
    """Did `needle` end up OUTSIDE a fence in the concatenated render?

    This is the measurement SEC-1 uses on the null: split the buffer on the fence markers and ask
    whether the injected directive landed in a region the model will read as instruction.
    """
    depth = 0
    for line in rendered.splitlines():
        stripped = line.strip()
        if stripped == FENCE_OPEN:
            depth += 1
            continue
        if stripped == FENCE_CLOSE:
            depth = max(0, depth - 1)
            continue
        if depth == 0 and needle in line:
            return True
    return False
