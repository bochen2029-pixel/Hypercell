"""The lane-family canary — declaration is a claim; the canary is the reality (slice SEC-c′).

The pricebook's `weights_family` is the diversity axis (A6): the oracle's quorum solver and the
router's diversity floor count DISTINCT families, because a swarm of eight cells all secretly running
the same weights has one blind spot wearing eight hats. But for a third-party host, `weights_family`
is a **claim** — hosts reroute backends silently, quantize, and pin old revisions — so a signed book
attests only what the operator *believes* a lane runs, never what it *actually* runs.

So **lane-family attestation := signed declaration AND runtime canary** (identity-firewall §B). The
signed book is Part A of this slice; this module is the canary: a per-round known-answer /
tokenizer-fingerprint probe that checks a lane's actual output against its declared family. A
mismatch **de-rates that lane's diversity contribution to ZERO** — not an alarm, a zero — until it
re-attests. And **fail-closed**: a claimed family with no pinned fingerprint contributes zero too,
because "we cannot check it" must cost diversity, not be granted it on trust.

**Two flags, two owners.** `family_verified` (this canary, the DIVERSITY axis) is distinct from
`parity_verified` (ECON-S3's cost-parity probe). Diversity-counting keys on `family_verified` and
NEVER on the score-parity probe — a host can be cost-honest and still be lying about its weights.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass


def fingerprint(probe_response: str) -> str:
    """The fingerprint of a lane's answer to the pinned probe.

    A known-answer test: the fabric sends one pinned probe and hashes the exact response. Different
    weights families answer with characteristic token boundaries and phrasings, so the hash is a
    family signature. (A tokenizer-fingerprint variant — hashing the tokenization of a fixed string
    — is the same shape with a different observable; the pinned corpus below would carry those
    hashes instead.)
    """
    return "sha256:" + hashlib.sha256(probe_response.strip().encode("utf-8")).hexdigest()


#: The pinned known-answer corpus: family → the fingerprint of its answer to the canary probe.
#: Pinned like controls (oracle.md SEC-2). A family absent here cannot be attested and fails closed.
#: In production these are measured against first-party lanes and frozen; here they are seeded so the
#: attestation logic — match, mismatch, unknown — is drillable without a live model.
_KNOWN: dict[str, str] = {
    "anthropic": fingerprint("Claude, made by Anthropic."),
    "deepseek": fingerprint("DeepSeek-V3, an open model."),
    "gpt-4o": fingerprint("GPT-4o, made by OpenAI."),
    "llama": fingerprint("Llama, from Meta."),
}


@dataclass(frozen=True)
class Attestation:
    """The canary's verdict on one lane. `family_verified` is the only thing diversity may count."""

    declared_family: str
    family_verified: bool
    reason: str

    @property
    def diversity_contribution(self) -> float:
        """1.0 only when the canary confirmed the declared family; 0.0 otherwise (the de-rate law)."""
        return 1.0 if self.family_verified else 0.0


def register_family(family: str, canonical_answer: str) -> None:
    """Pin a family's known answer (test/operator setup). Frozen like a control once set."""
    _KNOWN[family] = fingerprint(canonical_answer)


def attest(declared_family: str, probe_response: str) -> Attestation:
    """Check a lane's actual answer against its declared family. Fail-closed on the unknown.

    The three outcomes are the whole point: MATCH (the lane runs what it claims — diversity 1.0),
    MISMATCH (a host lying about its weights — diversity 0.0, the monoculture caught), and UNKNOWN
    (no pinned fingerprint for the claim — diversity 0.0, because an uncheckable claim is not a
    verified one).
    """
    expected = _KNOWN.get(declared_family)
    if expected is None:
        return Attestation(declared_family, False,
                           f"no pinned fingerprint for claimed family '{declared_family}'; "
                           "fail-closed (an uncheckable claim earns no diversity)")
    if fingerprint(probe_response) == expected:
        return Attestation(declared_family, True, "canary fingerprint matches the declared family")
    return Attestation(declared_family, False,
                       f"canary fingerprint does NOT match declared '{declared_family}'; the lane is "
                       "not running the weights it claims — diversity de-rated to zero until re-attested")


def diversity_count(attestations: list[Attestation]) -> int:
    """Distinct families among VERIFIED lanes only (the oracle's diversity floor input).

    A monoculture masquerading as diversity — eight lanes all declaring different families but
    failing the canary — counts as ZERO distinct families, not eight. This is what makes the
    cross-family quorum a measurement rather than a trust-me.
    """
    return len({a.declared_family for a in attestations if a.family_verified})
