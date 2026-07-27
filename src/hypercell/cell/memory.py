"""Memory-as-tool — five verbs, two registers, and the register wall (contracts/nucleus.md §6).

Membrane-internal tools; never advertised on the Medium.

**The register wall is write-time CODE, not a prompt.** `factual` means every citation chain
terminates in something the cell actually *witnessed* — a percept from the operator, the Medium or a
tool; or the outcome of an `act`, which is receipt-backed. `narrative` is model-authored lossy
compression: legal, useful, and cite-blocked in oracle-facing artifacts.

**What factual means, stated honestly: auditable-to-terminal, never *true*.** A factual memory citing
a poisoned `percept{trust: external}` is legitimately *witnessed*; its content is still untrusted
input. What the wall guarantees is that the provenance class of every claim is mechanical — recall
lines and evidence bundles surface each terminal's trust tag, so a "fact" grounded only in external
content is *visibly* so. The wall stops a cell inventing provenance. It cannot stop the world lying.

The default register is `narrative` on purpose: **a sloppy cell mints style, never fake facts.**
And rejection is never a silent downgrade — the caller gets a typed error with the offending path and
MAY re-file as narrative, deliberately.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal
from urllib.parse import urlparse

from .nucleus import Nucleus

Register = Literal["factual", "narrative"]

#: Closure depth ceiling (nucleus.md §6.1 rule 3). Cycles are impossible by construction: a ref must
#: point strictly backwards, so the walk is a DAG and this bounds work, not correctness.
MAX_DEPTH = 8

#: The warrant-class (non-mintable) set — the mint-restricted types that CERTIFY a boundary crossing.
#: **`contracts/wire.md` §3 is the home**; this module cites it and never re-derives it.
WARRANT_CLASS = frozenset({"receipt", "act_receipt", "verdict", "command", "cmd_receipt"})

#: A percept is a terminal only when the fabric witnessed where it came from.
WITNESSED_SOURCES = frozenset({"operator", "medium", "tool"})

#: Kinds that are model-authored or fabric-internal. Citing one as grounding mints trust inside the
#: fabric, which is exactly the thing a warrant may not do.
DECISION_KINDS = frozenset({"decision", "checkpoint", "frame", "consolidation", "action"})


class RegisterError(Exception):
    """A refused factual assert. Carries the typed code and the path that failed."""

    def __init__(self, code: str, message: str, path: list[int] | None = None) -> None:
        super().__init__(f"{code}: {message}" + (f" (path {path})" if path else ""))
        self.code = code
        self.path = path or []


@dataclass
class Terminal:
    """One end of a citation chain, with the trust tag that rides it into every bundle."""

    seq: int
    kind: str
    trust: str
    locator: str
    detail: str = ""


@dataclass
class RecallHit:
    seq: int
    content: str
    register: Register
    refs: list[int] = field(default_factory=list)
    xrefs: list[str] = field(default_factory=list)
    terminals: list[Terminal] = field(default_factory=list)
    superseded_by: int | None = None


class Memory:
    """The five verbs over one nucleus. Six record kinds; every write is journaled."""

    def __init__(self, nucleus: Nucleus, *, pin_budget: int = 0) -> None:
        self.nucleus = nucleus
        self.pin_budget = pin_budget

    # ---------------------------------------------------------------- the wall

    def _terminal_of(self, rec: dict[str, Any]) -> Terminal | None:
        """A terminal, or None if this record is not one. Trust tags ride from the record."""
        kind, body = rec["kind"], rec["body"]
        if not isinstance(body, dict):
            return None

        if kind == "percept" and body.get("source") in WITNESSED_SOURCES:
            source = str(body["source"])
            return Terminal(
                seq=rec["seq"],
                kind="percept",
                # The firewall contract owns tag STAMPING; this contract owns their propagation.
                trust=str(body.get("trust", source)),
                locator=f"nucleus://{self.nucleus.claim_id}/{rec['seq']}",
                detail=f"source={source}",
            )

        # Only the OUTCOME of an act is a terminal. The action that requested it is an intent, and an
        # intent is not evidence — the receipt is.
        if kind == "outcome" and body.get("verb") == "act":
            return Terminal(
                seq=rec["seq"],
                kind="act_receipt",
                trust="receipted",
                locator=str(body.get("corr") or f"nucleus://{self.nucleus.claim_id}/{rec['seq']}"),
                detail="act outcome",
            )
        return None

    def _walk(self, refs: list[int], this_seq: int) -> list[Terminal]:
        """Depth-bounded closure walk. Returns the terminals; raises the typed error on refusal."""
        terminals: list[Terminal] = []
        visited: set[int] = set()
        stack: list[tuple[int, list[int]]] = [(r, [r]) for r in reversed(refs)]

        while stack:
            seq, path = stack.pop()
            if len(path) > MAX_DEPTH:
                raise RegisterError("E_REG_TOO_DEEP", f"citation chain exceeds depth {MAX_DEPTH}", path)
            if seq in visited:
                continue
            visited.add(seq)

            rec = self.nucleus.record(seq)
            if rec is None:
                raise RegisterError("E_REG_BAD_REF", f"ref {seq} does not exist", path)

            terminal = self._terminal_of(rec)
            if terminal is not None:
                terminals.append(terminal)
                continue

            body = rec["body"] if isinstance(rec["body"], dict) else {}
            if rec["kind"] == "memory.assert" and body.get("register") == "factual":
                # Factual chains are allowed: a fact may rest on a fact, so long as the bottom is
                # something witnessed.
                for r2 in rec.get("refs", []):
                    stack.append((int(r2), [*path, int(r2)]))
                continue

            raise RegisterError(
                "E_REG_DECISION_REF",
                f"seq {seq} is {self._decision_reason(rec)} — self-citation mints trust inside the fabric",
                path,
            )
        return terminals

    @staticmethod
    def _decision_reason(rec: dict[str, Any]) -> str:
        kind = rec["kind"]
        body = rec["body"] if isinstance(rec["body"], dict) else {}
        if kind == "action":
            return f"an action{{verb: {body.get('verb', '?')}}} (an intent, not evidence)"
        if kind == "outcome":
            return f"the outcome of {body.get('verb', 'a model verb')} (model text)"
        if kind == "memory.assert":
            return "a narrative assert (model-authored compression)"
        if kind in DECISION_KINDS:
            return f"a {kind} record (fabric-internal)"
        return f"a {kind} record, which is not a legal terminal"

    def _validate_xrefs(self, xrefs: list[str]) -> list[Terminal]:
        out: list[Terminal] = []
        for x in xrefs:
            parsed = urlparse(x)
            if parsed.scheme == "act":
                out.append(Terminal(seq=-1, kind="act_receipt", trust="receipted", locator=x))
                continue
            if parsed.scheme == "medium":
                # Admissible only if the referenced type CERTIFIES a crossing. Another model's
                # assertion — submission, chat, status — is never grounding.
                kind = (parsed.fragment or parsed.path.rsplit("/", 1)[-1] or "").split(":")[-1]
                if kind not in WARRANT_CLASS:
                    raise RegisterError(
                        "E_REG_DECISION_REF",
                        f"medium xref {x} names type '{kind or '?'}', which is not warrant-class "
                        f"{sorted(WARRANT_CLASS)} — another model's assertion is not grounding",
                    )
                out.append(Terminal(seq=-1, kind=kind, trust="medium", locator=x))
                continue
            if parsed.scheme in ("http", "https"):
                raise RegisterError(
                    "E_REG_DECISION_REF",
                    f"raw URL {x} is not evidence — cite the act://corr of the fetch that "
                    "retrieved it, so the bytes are receipted",
                )
            raise RegisterError("E_REG_BAD_REF", f"xref scheme '{parsed.scheme}' is not citable")
        return out

    def validate_factual(self, refs: list[int], xrefs: list[str], this_seq: int) -> list[Terminal]:
        """VALIDATE-FACTUAL-ASSERT (nucleus.md §6.1). Atomic with the append that follows it."""
        if not refs and not xrefs:
            raise RegisterError("E_REG_NO_REFS", "a factual assert must cite something")
        for r in refs:
            if not 1 <= r < this_seq:
                raise RegisterError(
                    "E_REG_BAD_REF",
                    f"ref {r} is not in [1, {this_seq}) — only the past is citable",
                    [r],
                )
        return self._walk(refs, this_seq) + self._validate_xrefs(xrefs)

    # ---------------------------------------------------------------- the five verbs

    def remember(
        self,
        content: str,
        *,
        register: Register = "narrative",
        refs: list[int] | None = None,
        xrefs: list[str] | None = None,
        entities: list[str] | None = None,
        valid_from: str | None = None,
        valid_to: str | None = None,
    ) -> int:
        """File a memory. `factual` requires validated grounding; the default is `narrative`."""
        refs, xrefs = list(refs or []), list(xrefs or [])
        body: dict[str, Any] = {"content": content, "register": register, "xrefs": xrefs}
        if entities:
            body["entities"] = entities
        if valid_from:
            body["valid_from"] = valid_from
        if valid_to:
            body["valid_to"] = valid_to

        if register == "factual":
            # Validated against the seq this record WILL take. Raising here means nothing is
            # appended: the nucleus never silently downgrades a refused fact to narrative.
            terminals = self.validate_factual(refs, xrefs, self.nucleus.ledger.seq + 1)
            body["terminals"] = [
                {"seq": t.seq, "kind": t.kind, "trust": t.trust, "locator": t.locator} for t in terminals
            ]
        return self.nucleus.append("memory.assert", body, refs=refs, durability="gold")

    def recall(
        self,
        query: str = "",
        *,
        k: int = 10,
        register: Register | None = None,
        as_of: int | None = None,
    ) -> list[RecallHit]:
        """A journaled read: returns memories WITH provenance, and records that it happened."""
        superseded: dict[int, int] = {}
        for rec in self.nucleus.records_of_kind("memory.supersede"):
            superseded[int(rec["body"]["target"])] = rec["seq"]
        for rec in self.nucleus.records_of_kind("memory.retract"):
            superseded[int(rec["body"]["target"])] = rec["seq"]
        forgotten = {int(r["body"]["target"]) for r in self.nucleus.records_of_kind("memory.forget")}

        hits: list[RecallHit] = []
        for rec in self.nucleus.records_of_kind("memory.assert"):
            if as_of is not None and rec["seq"] > as_of:
                continue
            if rec["seq"] in forgotten:
                continue  # a render tombstone; the ledger still retains it
            body = rec["body"]
            if register is not None and body.get("register") != register:
                continue
            if query and query.lower() not in str(body.get("content", "")).lower():
                continue
            hits.append(
                RecallHit(
                    seq=rec["seq"],
                    content=str(body.get("content", "")),
                    register=body.get("register", "narrative"),
                    refs=list(rec.get("refs", [])),
                    xrefs=list(body.get("xrefs", [])),
                    terminals=[Terminal(**t) for t in body.get("terminals", [])],
                    superseded_by=superseded.get(rec["seq"]),
                )
            )

        hits = hits[-k:] if k else hits
        self.nucleus.append(
            "memory.recall",
            {"query": query, "k": k, "register": register, "as_of": as_of, "hits": [h.seq for h in hits]},
        )
        return hits

    def revise(self, target: int, content: str | None = None, mode: str = "supersede") -> int:
        """Atomic correction. The old version stays queryable as-of the past — history is not edited."""
        if mode not in ("supersede", "retract"):
            raise ValueError("mode is 'supersede' or 'retract'")
        if self.nucleus.record(target) is None:
            raise RegisterError("E_REG_BAD_REF", f"cannot revise seq {target}: no such record", [target])
        body: dict[str, Any] = {"target": target}
        if content is not None:
            body["content"] = content
        return self.nucleus.append(f"memory.{mode}", body, refs=[target], durability="gold")

    def forget(self, target: int, reason: str) -> int:
        """A render tombstone. The ledger retains the record — true erasure is the firewall's job."""
        return self.nucleus.append(
            "memory.forget", {"target": target, "reason": reason}, refs=[target], durability="gold"
        )

    def pin(self, target: int, *, on: bool = True, order: int | None = None) -> int:
        """Consolidation-immune and S0-eligible. Over budget refuses — unpin something first."""
        if on:
            pinned = {
                int(r["body"]["target"]) for r in self.nucleus.records_of_kind("memory.pin") if r["body"].get("on")
            }
            unpinned = {
                int(r["body"]["target"])
                for r in self.nucleus.records_of_kind("memory.pin")
                if not r["body"].get("on")
            }
            live = pinned - unpinned
            if target not in live and len(live) >= self.pin_budget:
                raise RegisterError(
                    "E_PIN_BUDGET",
                    f"pin budget is {self.pin_budget} and {len(live)} are pinned; unpin one first",
                )
        body: dict[str, Any] = {"target": target, "on": on}
        if order is not None:
            body["order"] = order
        return self.nucleus.append("memory.pin", body, refs=[target], durability="gold")
