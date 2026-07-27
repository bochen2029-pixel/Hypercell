"""Evidence resolution and the deterministic grounding validator (GROUND-1).

A cited claim is checkable or it is decoration. This module answers one question mechanically:
**does this `act://` citation actually support this quote?**

Four fabrication classes, and what catches each:

| class | caught by |
|---|---|
| forged `act://` — a citation to an act that never happened | receipt lookup: no receipt, no warrant |
| digest mismatch — the stored bytes are not the bytes cited | re-hash the artifact against the receipt |
| quote-not-in-source — the quote does not appear in the fetched content | substring check over the artifact |
| irrelevant-ref — the source is real but says nothing about the claim | entailment sampling (a model judge) |

The first three are **deterministic and free**, which is why they run on every citation. Entailment
costs a model call, so it runs on a sampled fraction ρ — and any deterministic catch drives ρ to 1.0
for that cell, because a cell caught fabricating once has earned full inspection.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

from .executor import ActExecutor
from .store import ArtifactStore

Verdict = Literal["grounded", "forged_act", "digest_mismatch", "quote_absent", "unchecked"]

#: Normalise whitespace before matching: a quote that survives a line-wrap is still the same quote,
#: and refusing it would train cells to cite less rather than to cite better.
_WS = re.compile(r"\s+")


def _norm(text: str) -> str:
    return _WS.sub(" ", text).strip().lower()


@dataclass(frozen=True)
class Citation:
    """One claim and the act it rests on."""

    claim: str
    act_uri: str
    quote: str = ""


@dataclass
class GroundingReport:
    checked: int = 0
    grounded: int = 0
    findings: list[tuple[Citation, Verdict, str]] = field(default_factory=list)
    stained: bool = False

    @property
    def ok(self) -> bool:
        return not self.stained

    @property
    def rho_next(self) -> float:
        """Any catch drives the entailment sample rate to 1.0 — one fabrication earns full inspection."""
        return 1.0 if self.stained else 0.2


def validate(
    citations: list[Citation], *, executor: ActExecutor, store: ArtifactStore | None = None
) -> GroundingReport:
    """Run the three deterministic checks over every citation. Cheap enough to never sample."""
    store = store or executor.store
    report = GroundingReport()

    for cite in citations:
        report.checked += 1

        receipt = executor.receipt(cite.act_uri)
        if receipt is None or receipt.exec != "ok":
            # A citation to an act that never succeeded is the cleanest fabrication there is.
            report.findings.append((cite, "forged_act", f"no successful act receipt for {cite.act_uri}"))
            report.stained = True
            continue

        if not receipt.sha256 or not store.verify(receipt.sha256):
            report.findings.append(
                (cite, "digest_mismatch", f"stored bytes for {receipt.artifact_uri} do not re-hash")
            )
            report.stained = True
            continue

        if cite.quote:
            artifact = store.get(receipt.sha256)
            source = _norm(artifact.read_text()) if artifact else ""
            if _norm(cite.quote) not in source:
                report.findings.append(
                    (cite, "quote_absent", "the quote does not appear in the fetched source")
                )
                report.stained = True
                continue

        report.grounded += 1
        report.findings.append((cite, "grounded", "digest verified; quote present in source"))

    return report


def extract_citations(text: str) -> list[Citation]:
    """Pull `act://` citations out of an answer.

    Recognised form: `"quoted text" [act://corr]`, or a bare `[act://corr]` for a ref-only citation.
    Ref-only is legal and cheaper — it skips the quote check but still proves the fetch happened.
    """
    out: list[Citation] = []
    for match in re.finditer(r'(?:"([^"]{1,400})"\s*)?\[(act://[A-Za-z0-9_\-]+)\]', text):
        quote, uri = match.group(1) or "", match.group(2)
        out.append(Citation(claim=quote or uri, act_uri=uri, quote=quote))
    return out
