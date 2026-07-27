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
import math
from dataclasses import dataclass, field
from typing import Any, Literal

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


# ============================================================================ N4' -- the ASSEMBLER
#
# The SEC-a' code above answers "can foreign text reach the control region?" (no, structurally).
# The code below answers a different question over the same bytes: "is this frame DETERMINISTIC,
# and does its stable prefix stay byte-identical across ticks so the provider can cache it?" That
# is the cache seam (nucleus.md §7), and it is where the economics plane predicts hits and
# attributes misses. One file, two rungs, two concerns that never share a mechanism.
#
# The null is P0's `messages=[system, user]` ad-hoc concat: correct output, zero cache discipline,
# no manifest, no way to answer "why did the cell not know X at tick t?". Every tick rebuilds the
# whole prompt from scratch and pays to re-read its own unchanged identity.

Stability = Literal["stable", "semi", "volatile"]

#: The seven sections and their stability classes (§7.1). Order is load-bearing: the frame is
#: assembled S0..S6, and cache stability is a property of that order (stable prefix first).
SECTION_ORDER = ("S0", "S1", "S2", "S3", "S4", "S5", "S6")
SECTION_NAME = {
    "S0": "identity", "S1": "tools", "S2": "digest", "S3": "working",
    "S4": "retrieved", "S5": "recap", "S6": "percept",
}
SECTION_STABILITY: dict[str, Stability] = {
    "S0": "stable", "S1": "stable", "S2": "semi",
    "S3": "volatile", "S4": "volatile", "S5": "volatile", "S6": "volatile",
}
#: The ratio vector's field order (role.md §3). Slack is the eighth, budgeted but not a section.
RATIO_KEYS = ("identity", "tools", "digest", "working", "retrieved", "recap", "percept", "slack")
_RATIO_TO_SECTION = dict(zip(("S0", "S1", "S2", "S3", "S4", "S5", "S6"), RATIO_KEYS[:7], strict=True))

#: Spillover re-offers leftover budget to VOLATILE sections only, in this fixed order (§7.2 step 6).
#: Spilling into S2 would break the semi-stable prefix between installs, so S2 is absent by law.
SPILLOVER_ORDER = ("S6", "S4", "S5")

ASSEMBLER_VERSION = "assembler/1"
SALIENCE_VERSION = "salience/1"
ESTIMATOR_VERSION = "estimator/bytes4-1"

#: Fixed segment delimiter (§7.2 step 8). A control char that cannot occur in normal prompt text,
#: so the byte-coverage law (`concat(items) == frame minus delimiters`) is decidable by a plain
#: string strip. RS = U+241E is a visible symbol for the ASCII record separator and will never
#: appear in model-facing prose.
SEG_DELIM = "␞"


class FrameError(Exception):
    """The frame cannot be assembled honestly (§7.2 steps 5, 7). Operator-visible, never silent.

    Two causes, both refusals rather than truncations: a mandatory section (S0/S1/S2) over its
    budget is a ROLE-MANIFEST error the caller must fix at spawn/pin/install (a silent runtime drop
    of the identity would be a cell quietly forgetting who it is), and an identity-plus-first-page
    that cannot fit the window at all is a frame that was never viable.
    """


@dataclass(frozen=True)
class Window:
    """The context budget for one tick. `W_use = context - max_output - 256` (the reserve)."""

    context: int
    max_output: int = 4096

    @property
    def usable(self) -> int:
        return self.context - self.max_output - 256


@dataclass(frozen=True)
class Candidate:
    """One item offered to a section before packing. The assembler never invents these -- a gather
    step reads them from the nucleus, so the assembler itself stays a pure function of its inputs
    (which is what makes the 100-replay determinism bar a property and not a hope)."""

    ref: str
    body: str
    seq: int = 0
    id: str = ""
    mandatory: bool = False
    pinned: bool = False
    register: str = ""  # "factual" | "narrative" | ""
    entities: tuple[str, ...] = ()
    recall_count: int = 0


@dataclass(frozen=True)
class PackedItem:
    ref: str
    tokens: int
    salience: float
    body: str


@dataclass(frozen=True)
class Drop:
    ref: str
    tokens: int
    salience: float
    reason: str


@dataclass(frozen=True)
class Segment:
    name: str
    section: str
    stability: Stability
    sha256: str
    tokens: int
    items: tuple[PackedItem, ...]
    dropped: tuple[Drop, ...]


@dataclass(frozen=True)
class FrameManifest:
    """The durable record of one assembly (§7.2 step 9). `append kind=frame`, standard durability.

    Everything the economics plane needs to predict a cache hit, reserve exactly, and attribute a
    miss to its cause lives here: `segments[].sha256` (which segment first differed), the two
    prefix hashes (stable never moves; semi moves only at installs), and `est_tokens_total` (the
    number ECON-S2's worst-case pricer was guessing at with chars/4 until this landed).
    """

    tick: int
    ledger_head: int
    window: dict[str, int]
    segments: tuple[Segment, ...]
    prefix_hash_stable: str
    prefix_hash_semi: str
    est_tokens_total: int
    versions: dict[str, str]
    digest: str

    def segment(self, section: str) -> Segment | None:
        return next((s for s in self.segments if s.section == section), None)

    def knows(self, ref: str) -> Literal["kept", "dropped", "never-gathered"]:
        """The §7.5 audit query: 'why did the cell not know X at tick t?' in one lookup.

        kept -> X was in the frame. dropped -> gathered but lost to budget (the manifest records
        the losing salience). never-gathered -> DERIVE_Q did not name it; not in the frame and the
        reason is upstream of packing.
        """
        for seg in self.segments:
            if any(it.ref == ref for it in seg.items):
                return "kept"
        for seg in self.segments:
            if any(d.ref == ref for d in seg.dropped):
                return "dropped"
        return "never-gathered"


def estimate_tokens(body: str) -> int:
    """The versioned token estimator (§7.3). `bytes/4` floor when the lane's tokenizer is unknown.

    A floor, deliberately: it errs toward OVER-counting, so the budget packs conservatively and the
    step-10 re-run at 0.9 absorbs the rare undershoot. A ceiling would overflow the window silently,
    which is the one failure the assembler exists to prevent.
    """
    return max(1, len(body.encode("utf-8")) // 4)


def _content_words(text: str) -> set[str]:
    #: The stopword list is bundled and versioned (DERIVE_Q, §7.3). Kept deliberately small and
    #: dependency-free: a query builder that pulls in a language model is a query builder that can
    #: be prompt-injected by the percept it is meant to summarise.
    stop = {
        "the", "a", "an", "and", "or", "but", "of", "to", "in", "on", "for", "with", "is", "are",
        "was", "were", "be", "this", "that", "it", "as", "at", "by", "from", "i", "you", "we",
    }
    words = "".join(c.lower() if c.isalnum() else " " for c in text).split()
    return {w for w in words if len(w) > 2 and w not in stop}


def derive_q(percept: str, working_entities: tuple[str, ...]) -> frozenset[str]:
    """DERIVE_Q(P, S3): content words of the percept union entity keys of open tasks (§7.3).

    Assembly never asks a model what to recall -- that would put an un-audited model call on the
    deterministic path, and the whole point of the manifest is that assembly is reproducible from
    the ledger alone. A model that wants more calls the `recall` verb mid-tick, journaled.
    """
    return frozenset(_content_words(percept) | {e.lower() for e in working_entities})


def salience_v1(
    item: Candidate, *, working_entities: frozenset[str], head: int, weights: dict[str, float]
) -> float:
    """SALIENCE_v1 (§7.3). Rounded to 6 places so the pack ORDER is identical across machines.

    Float determinism is the subtle NUC-5 trap: `exp`/`ln` can differ by a ULP across builds, and
    if two items' raw salience straddle that ULP they swap in the sort and the frame bytes diverge.
    Rounding before the sort key removes the straddle; the (seq, id) tiebreak removes the rest.
    """
    ent = item.entities
    jac = 0.0
    if ent and working_entities:
        es = {e.lower() for e in ent}
        jac = len(es & working_entities) / len(es | working_entities)
    # `max(0, ...)`: an item newer than the ledger head (the percept, not yet journaled) is as
    # recent as anything can be — recency 1.0 — never a future age that overflows `exp`.
    age = max(0, head - item.seq)
    recency = math.exp(-age / max(1.0, weights.get("half_life", 512.0)))
    score = (
        weights.get("w_pin", 4.0) * (1.0 if item.pinned else 0.0)
        + weights.get("w_factual", 2.0) * (1.0 if item.register == "factual" else 0.0)
        + weights.get("w_task", 1.5) * jac
        + weights.get("w_recency", 1.0) * recency
        + weights.get("w_ref", 0.5) * math.log1p(item.recall_count)
    )
    return round(score, 6)


def _render_item(section: str, it: PackedItem) -> str:
    """One item's frame bytes. Provenance rides in-band for data sections so a forged block still
    arrives labelled; the identity and tools sections are the cell's own and carry no such prefix."""
    if section in ("S0", "S1"):
        return it.body
    return f"[{SECTION_NAME[section]} · {it.ref}]\n{it.body}"


def _segment_bytes(section: str, items: list[PackedItem]) -> str:
    return SEG_DELIM.join(_render_item(section, it) for it in items)


def _seg_sha(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def assemble_frame(
    *,
    ratios: dict[str, float],
    salience_weights: dict[str, float],
    window: Window,
    candidates: dict[str, list[Candidate]],
    ledger_head: int,
    tick: int,
    percept: str = "",
    working_entities: tuple[str, ...] = (),
) -> tuple[str, FrameManifest]:
    """ASSEMBLE (nucleus.md §7.2), the pure deterministic core. Returns (frame_bytes, manifest).

    Pure: same (candidates, ratios, weights, window, head, percept) ⇒ byte-identical frame, on any
    machine, every replay. The nucleus I/O -- gathering the candidates at ledger head h -- is the
    caller's job (`gather_candidates`), so the thing the determinism bar measures has no hidden
    inputs. `assemble_frame` reads no clock, no filesystem, no model.
    """
    w_use = window.usable
    budget = {s: math.floor(ratios.get(_RATIO_TO_SECTION[s], 0.0) * w_use) for s in SECTION_ORDER}
    slack = w_use - sum(budget.values())

    q = derive_q(percept, working_entities)
    working = frozenset(e.lower() for e in working_entities) | q

    packed: dict[str, list[PackedItem]] = {s: [] for s in SECTION_ORDER}
    dropped: dict[str, list[Drop]] = {s: [] for s in SECTION_ORDER}
    spill: dict[str, list[tuple[Candidate, int, float]]] = {s: [] for s in SECTION_ORDER}

    for section in SECTION_ORDER:
        offered = candidates.get(section, [])
        scored: list[tuple[Candidate, int, float]] = []
        for cand in offered:
            tok = estimate_tokens(cand.body)
            sal = math.inf if cand.mandatory else salience_v1(
                cand, working_entities=working, head=ledger_head, weights=salience_weights
            )
            scored.append((cand, tok, sal))
        # Within a section: salience desc, then seq desc, then id asc (§7.2 step 5).
        scored.sort(key=lambda t: (-t[2], -t[0].seq, t[0].id))

        used = 0
        cap = budget[section]
        for cand, tok, sal in scored:
            fits = used + tok <= cap
            if sal == math.inf and not fits and SECTION_STABILITY[section] != "volatile":
                # A mandatory stable/semi item that does not fit is a ROLE-MANIFEST error, not a
                # runtime drop (§7.2 step 5 HYSTERESIS). The identity does not get quietly cut.
                raise FrameError(
                    f"section {section} ({SECTION_NAME[section]}) mandatory items exceed budget "
                    f"{cap} tok at tick {tick}; fix the role manifest at spawn/pin/install time, "
                    "never drop identity silently at runtime"
                )
            if fits or sal == math.inf:
                packed[section].append(PackedItem(cand.ref, tok, sal, cand.body))
                used += tok
            elif SECTION_STABILITY[section] == "volatile":
                spill[section].append((cand, tok, sal))  # eligible for spillover (step 6)
            else:
                dropped[section].append(Drop(cand.ref, tok, sal, "budget"))

    # Step 6: spillover -- leftover slack re-offered to volatile sections in fixed order.
    for section in SPILLOVER_ORDER:
        for cand, tok, sal in spill[section]:
            if tok <= slack:
                packed[section].append(PackedItem(cand.ref, tok, sal, cand.body))
                slack -= tok
            else:
                dropped[section].append(Drop(cand.ref, tok, sal, "budget"))
    # A volatile section outside the spillover order keeps its leftovers as drops (defensive; the
    # three volatile sections that can overflow are exactly the spillover set today).
    for section in SECTION_ORDER:
        if section not in SPILLOVER_ORDER:
            for cand, tok, sal in spill[section]:
                dropped[section].append(Drop(cand.ref, tok, sal, "budget"))

    # Step 7: the frame must at least seat identity + the first page of percept.
    s0_tok = sum(it.tokens for it in packed["S0"])
    s6_first = packed["S6"][0].tokens if packed["S6"] else 0
    if s0_tok + s6_first > w_use:
        raise FrameError(
            f"identity ({s0_tok} tok) + first percept page ({s6_first} tok) exceeds the usable "
            f"window ({w_use} tok) at tick {tick}; this frame was never viable"
        )

    # Fail-closed on a body that contains the segment delimiter. U+241E in content would forge a
    # segment boundary — the same in-band-escape hazard SEC-a' refused for the TRUST frame, here for
    # the CACHE frame: an injected boundary makes "frame minus delimiters == concat(items)" false,
    # so the manifest could no longer account for every byte. A percept carrying this control char is
    # pathological; refusing the tick is honest where silently mis-accounting it is not. (The c′
    # audit caught this: a body with U+241E broke byte-coverage rather than being rejected.)
    for section in SECTION_ORDER:
        for it in packed[section]:
            if SEG_DELIM in it.body:
                raise FrameError(
                    f"item '{it.ref}' in {SECTION_NAME[section]} contains the segment delimiter "
                    "(U+241E); it would forge a segment boundary and break byte-coverage. Refused."
                )

    # Step 8: join sections with fixed delimiters; compute per-segment bytes + hashes.
    segments: list[Segment] = []
    frame_parts: list[str] = []
    for section in SECTION_ORDER:
        items = packed[section]
        seg_text = _segment_bytes(section, items)
        frame_parts.append(seg_text)
        segments.append(
            Segment(
                name=SECTION_NAME[section], section=section, stability=SECTION_STABILITY[section],
                sha256=_seg_sha(seg_text), tokens=sum(it.tokens for it in items),
                items=tuple(items), dropped=tuple(dropped[section]),
            )
        )
    frame = SEG_DELIM.join(frame_parts)

    # Step 9: the prefix hashes. Stable = S0+S1; semi = S0+S1+S2. Computed over the SAME segment
    # hashes that entered the frame, so "the prefix the provider caches" and "the prefix the
    # manifest attests" are the same string by construction -- not two computations that disagree.
    by = {s.section: s for s in segments}

    def prefix(sections: tuple[str, ...]) -> str:
        return _seg_sha(SEG_DELIM.join(by[s].sha256 for s in sections))

    est_total = sum(seg.tokens for seg in segments)
    manifest = FrameManifest(
        tick=tick, ledger_head=ledger_head,
        window={"context": window.context, "max_output": window.max_output, "W_use": w_use},
        segments=tuple(segments),
        prefix_hash_stable=prefix(("S0", "S1")),
        prefix_hash_semi=prefix(("S0", "S1", "S2")),
        est_tokens_total=est_total,
        versions={"assembler": ASSEMBLER_VERSION, "salience": SALIENCE_VERSION, "estimator": ESTIMATOR_VERSION},
        digest="sha256:" + hashlib.sha256(frame.encode("utf-8")).hexdigest(),
    )
    return frame, manifest


def byte_coverage_holds(frame: str, manifest: FrameManifest) -> bool:
    """The NUC-5 byte-coverage law: `concat(manifest items) == frame minus delimiters`.

    Every byte the model reads is accounted for by exactly one manifest item -- nothing enters the
    frame that the manifest does not name, and nothing the manifest names is missing from the frame.
    A frame with un-manifested bytes is one the economics plane cannot attribute and the audit
    query cannot answer over.
    """
    from_items = "".join(
        _render_item(seg.section, it) for seg in manifest.segments for it in seg.items
    )
    return frame.replace(SEG_DELIM, "") == from_items


# ---------------------------------------------------------------------------- gather (the I/O half)
#
# `assemble_frame` is pure; SOMETHING has to read the nucleus at ledger head h and offer it the
# candidates. That is this half, kept separate on purpose: the determinism bar measures the pure
# core, and a gather that reads a clock or a half-built memory subsystem cannot contaminate it.
# Sections whose subsystem has not landed (S2 digests, S4 recall) gather empty today; the d1 ratio
# table budgets them at zero anyway, so an empty gather and a zero budget agree.


def gather_candidates(
    *,
    role: Any,
    percept: str,
    checkpoint_state: dict[str, Any] | None = None,
    pending: list[dict[str, Any]] | None = None,
    recap_records: list[dict[str, Any]] | None = None,
    digests: list[tuple[str, str]] | None = None,
    recalled: list[Candidate] | None = None,
    pins: list[tuple[str, str]] | None = None,
) -> dict[str, list[Candidate]]:
    """Offer each section its candidates (nucleus.md §7.2 step 3). Pure over its arguments.

    S0 identity and S1 tools are MANDATORY (salience +inf, never budget-dropped). S3/S5/S6 are
    volatile. S2/S4 accept what the memory subsystems provide and default empty — the honest state
    until consolidation and recall land, and the reason the d1 table zeroes their budget.
    """
    out: dict[str, list[Candidate]] = {s: [] for s in SECTION_ORDER}

    # S0 identity: the role prompt (mandatory head) then pins in pin order (also mandatory).
    out["S0"].append(Candidate(ref="role.prompt", body=role.prompt, mandatory=True, id="0"))
    for i, (ref, body) in enumerate(pins or [], start=1):
        out["S0"].append(Candidate(ref=ref, body=body, mandatory=True, pinned=True, id=f"{i:03d}"))

    # S1 tools: one mandatory item per declared tool, in ROLE ORDER (byte-stable across ticks).
    for i, tool in enumerate(getattr(role, "tools", []) or []):
        out["S1"].append(Candidate(ref=f"tool:{tool}", body=f"tool schema: {tool}", mandatory=True, id=f"{i:03d}"))

    # S2 digest: installed digests oldest->newest, semi-stable (changes only at installs).
    for i, (ref, body) in enumerate(digests or []):
        out["S2"].append(Candidate(ref=ref, body=body, seq=i, id=f"{i:06d}"))

    # S3 working: last checkpoint.state + open tasks (pending()).
    if checkpoint_state:
        out["S3"].append(Candidate(ref="checkpoint.state", body=_compact(checkpoint_state), seq=0, id="state"))
    for p in pending or []:
        out["S3"].append(
            Candidate(ref=f"task:{p.get('idem', p.get('corr', ''))}", body=_compact(p),
                      seq=int(p.get("seq", 0)), id=str(p.get("idem", "")))
        )

    # S4 retrieved: recall results with provenance (empty until the recall subsystem lands).
    out["S4"].extend(recalled or [])

    # S5 recap: last recap_k io records verbatim, oldest->newest.
    for r in recap_records or []:
        out["S5"].append(
            Candidate(ref=f"io:{r.get('seq', '')}", body=_compact(r), seq=int(r.get("seq", 0)),
                      id=str(r.get("seq", "")))
        )

    # S6 percept: the new input (single page; pagination is a later refinement).
    if percept:
        out["S6"].append(Candidate(ref="percept", body=percept, seq=1 << 30, id="percept"))
    return out


def _compact(obj: Any) -> str:
    """A record rendered to stable bytes for the frame. Canonical, so the same state is the same
    bytes every tick — a working-set that reordered its own keys would churn the volatile prefix."""
    if isinstance(obj, str):
        return obj
    return canon_bytes(obj).decode("utf-8")


def manifest_as_body(m: FrameManifest) -> dict[str, Any]:
    """The `frame` record body (§7.2 step 10). Segments carry their sha + item refs, never the item
    BODIES — the bytes live in the frame the model saw; the manifest attests them, it does not
    duplicate them (a manifest that copied the bodies would be a second place for them to drift)."""
    return {
        "tick": m.tick,
        "ledger_head": m.ledger_head,
        "window": m.window,
        "segments": [
            {
                "name": s.name, "section": s.section, "class": s.stability, "sha256": s.sha256,
                "tokens": s.tokens,
                "items": [{"ref": it.ref, "tokens": it.tokens, "salience": _sal(it.salience)} for it in s.items],
                "dropped": [{"ref": d.ref, "tokens": d.tokens, "salience": _sal(d.salience), "reason": d.reason}
                            for d in s.dropped],
            }
            for s in m.segments
        ],
        "prefix_hash_stable": m.prefix_hash_stable,
        "prefix_hash_semi": m.prefix_hash_semi,
        "est_tokens_total": m.est_tokens_total,
        "versions": m.versions,
        "digest": m.digest,
    }


def _sal(x: float) -> float | str:
    return "inf" if x == math.inf else x


def frame_tick(
    nucleus: Any, role: Any, percept: str, window: Window, *, tick: int
) -> tuple[str, FrameManifest]:
    """Assemble a frame for one tick against a live nucleus, and JOURNAL the manifest (`kind=frame`).

    The thin I/O wrapper: read the nucleus at its ledger head, gather, assemble (pure), append the
    manifest at standard durability. The append is what makes the §7.5 audit query answerable later
    from the ledger alone — an assembly that left no `frame` record is one nobody can ask about.
    """
    head = nucleus.ledger.seq
    last_ckpt = _last_checkpoint(nucleus)
    # `k` guards the -0 slice trap: `records[-0:]` is `records[:]`, the WHOLE list, so a recap_k of
    # 0 would recap EVERYTHING instead of nothing (the c′ audit caught this). `[-k:] if k else []`.
    k = role.recap_k()
    io_records = nucleus.records_of_kind("action") if hasattr(nucleus, "records_of_kind") else []
    recap = io_records[-k:] if k else []
    candidates = gather_candidates(
        role=role, percept=percept,
        checkpoint_state=last_ckpt, pending=nucleus.pending() if hasattr(nucleus, "pending") else [],
        recap_records=recap,
    )
    frame, manifest = assemble_frame(
        ratios=role.frame_ratios(), salience_weights=role.frame_salience(),
        window=window, candidates=candidates, ledger_head=head, tick=tick, percept=percept,
    )
    nucleus.append("frame", manifest_as_body(manifest), durability="standard")
    return frame, manifest


def _last_checkpoint(nucleus: Any) -> dict[str, Any] | None:
    if not hasattr(nucleus, "records_of_kind"):
        return None
    ckpts = nucleus.records_of_kind("checkpoint")
    if not ckpts:
        return None
    body = ckpts[-1].get("body", {})
    return body if isinstance(body, dict) else None
