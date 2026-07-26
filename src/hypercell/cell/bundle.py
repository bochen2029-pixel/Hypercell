"""The evidence-bundle exporter — privacy-preserving walkability (contracts/nucleus.md §6.2).

A3 keeps the nucleus private: the oracle cannot walk `nucleus://` refs. So at submission time the
membrane packages every cited memory plus its terminal ref-closure content-hashes as **one artifact**.
The oracle validates hashes and samples entailment with **zero nucleus access**; `nucleus://` stays an
operator-audit pointer, and `hc peek` checks bundle-vs-ledger byte equality — a mismatch at audit is a
fabricated warrant, the L-NO-NAKED-CLAIMS stain.

Two refusals are structural here, not advisory:

* **`register: narrative` is refused at packaging.** A narrative citation never reaches the wire.
  The block keys on the register, never on refs-absence, because a well-cited piece of model prose is
  still model prose.
* **A cited memory with no terminals is refused.** A bundle whose "evidence" bottoms out in nothing
  is a naked claim wearing an artifact's clothes.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from ..common.canon import canon_bytes
from .memory import Memory, RecallHit


class BundleError(Exception):
    """Refused at packaging. The submission does not go out."""


@dataclass(frozen=True)
class EvidenceBundle:
    claim: str
    ledger_head: dict[str, Any]
    cited: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {"claim": self.claim, "ledger_head": self.ledger_head, "cited": self.cited}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @property
    def sha256(self) -> str:
        """Over the canonical form, so the oracle and the cell agree on what was submitted."""
        return "sha256:" + hashlib.sha256(canon_bytes(self.to_dict())).hexdigest()


def _content_hash(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def export_bundle(memory: Memory, cited: list[RecallHit], *, claim: str | None = None) -> EvidenceBundle:
    """Package cited memories for the wire. Refuses narrative and refuses ungrounded claims."""
    nucleus = memory.nucleus
    claim_id = claim or nucleus.claim_id

    narrative = [h.seq for h in cited if h.register == "narrative"]
    if narrative:
        raise BundleError(
            f"refusing to package narrative memories {narrative}: a narrative citation never reaches "
            "the wire. Re-file the claim as factual with real grounding, or drop the citation."
        )

    ungrounded = [h.seq for h in cited if not h.terminals]
    if ungrounded:
        raise BundleError(
            f"refusing to package memories {ungrounded} with no terminal refs: evidence that bottoms "
            "out in nothing is a naked claim (L-NO-NAKED-CLAIMS)."
        )

    packaged: list[dict[str, Any]] = []
    for hit in cited:
        terminal_refs = []
        for t in hit.terminals:
            rec = nucleus.record(t.seq) if t.seq > 0 else None
            payload = json.dumps(rec["body"], ensure_ascii=False, sort_keys=True) if rec else t.locator
            terminal_refs.append(
                {
                    "kind": t.kind,
                    "locator": t.locator,
                    "sha256": _content_hash(payload),
                    # The trust tag rides the bundle: a "fact" grounded only in external content is
                    # VISIBLY so, to the oracle and to the operator.
                    "trust": t.trust,
                }
            )
        packaged.append(
            {
                "memory_id": f"m_{hit.seq:012d}",
                "register": hit.register,
                "content": hit.content,
                "asserted_seq": hit.seq,
                "terminal_refs": terminal_refs,
            }
        )

    return EvidenceBundle(
        claim=claim_id,
        ledger_head={"seq": nucleus.ledger.seq, "hash": nucleus.head_hash},
        cited=packaged,
    )


def verify_bundle(memory: Memory, bundle: EvidenceBundle) -> tuple[bool, str]:
    """`hc peek`'s check: bundle-vs-ledger byte equality. A mismatch at audit is a fabricated warrant."""
    nucleus = memory.nucleus
    for item in bundle.cited:
        seq = int(item["asserted_seq"])
        rec = nucleus.record(seq)
        if rec is None:
            return False, f"cited memory at seq {seq} is not in the ledger"
        if str(rec["body"].get("content", "")) != item["content"]:
            return False, f"seq {seq}: bundle content differs from the ledger — fabricated warrant"
        for tref in item["terminal_refs"]:
            t_rec = nucleus.record(int(tref["locator"].rsplit("/", 1)[-1])) if tref["locator"].startswith(
                "nucleus://"
            ) else None
            if t_rec is None:
                continue  # act:// and medium:// terminals are verified by the oracle, not locally
            payload = json.dumps(t_rec["body"], ensure_ascii=False, sort_keys=True)
            if _content_hash(payload) != tref["sha256"]:
                return False, f"terminal {tref['locator']}: content hash differs from the ledger"
    return True, "bundle matches the ledger"
