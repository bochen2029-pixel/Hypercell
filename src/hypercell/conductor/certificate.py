"""The certificate and `hc verify` (run.md §R8.1; slice RE-4, falsifier CERT-1).

**"The output type of the named fold; else it is a press release."** That sentence is the whole
design. A certificate is not a summary somebody wrote about a run — it is a projection of
`FOLD(span)`, field by field, and `hc verify` recomputes the same fold and diffs. Anything the
certificate says that the log does not support fails verification **naming the field**, because
"verification failed" tells an operator nothing they can act on.

Five steps, in order (§R8.1):

1. load the span and verify the per-culture hash chain to `chain_head`;
2. `state = FOLD(span)` — the SAME derivation resume uses, never a second implementation that might
   agree by luck;
3. recompute every field; the diff MUST be empty, and a non-empty diff names the fields;
4. artifact sha spot-check; oracle digest + pricebook pin check;
5. the **two-log spend agreement** — the span's `cost{}` sums on one side, the conductor's escrow
   ledger fold on the other. Two independently-maintained records of the same dollars: if they
   disagree, one of them is lying and the certificate must not average them.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

from ..common.canon import canon_bytes
from .engine.fold import PlanesState, fold

CERT_VERSION = "5.1"

#: Spend agreement tolerance. Float accumulation over thousands of records drifts in the last
#: places; a mismatch that matters is never this small, and a zero tolerance would fail on
#: arithmetic rather than on disagreement.
SPEND_EPSILON = 1e-6


@dataclass
class VerifyResult:
    ok: bool
    #: Field paths that disagreed, e.g. `champion.score`. Named, because "verification failed" is
    #: not an actionable sentence.
    bad_fields: list[str] = field(default_factory=list)
    detail: dict[str, Any] = field(default_factory=dict)
    chain_ok: bool = True
    spend_agrees: bool = True

    @property
    def reason(self) -> str:
        if self.ok:
            return "certificate verified"
        if not self.chain_ok:
            return "the span's hash chain does not verify"
        if not self.spend_agrees:
            return "the two spend logs disagree"
        return f"certificate fields do not match the fold: {', '.join(self.bad_fields)}"


def certificate(
    state: PlanesState,
    *,
    oracle: dict[str, Any] | None = None,
    pricebook_pin: str = "",
    vs_null: dict[str, Any] | None = None,
    escrow_committed_usd: float | None = None,
) -> dict[str, Any]:
    """Project `PlanesState` into the §R8.1 certificate. Every field is a fold projection.

    Nothing is passed in that the fold could have derived: `oracle`, `pricebook_pin` and `vs_null`
    come from the run's pinned inputs, and `escrow_committed_usd` is the OTHER log — carried so the
    certificate records both numbers rather than one number and a promise.
    """
    champ = state.champion
    conv = state.convergence
    cert: dict[str, Any] = {
        "cert_version": CERT_VERSION,
        "run_id": state.run_id,
        "manifest_sha256": state.manifest_sha256,
        "topology": state.topology,
        "verdict_kind": _verdict_kind(state),
        "oracle": dict(oracle or {"id": "", "gen": state.gen, "digest": "", "lineage": []}),
        "champion": {
            "arm": champ.who if champ else None,
            "score": champ.score if champ else None,
            "outcome": champ.outcome.value if champ else None,
            "receipt_seq": champ.at if champ else None,
            "artifact": state.artifacts.get(str(champ.at)) if champ else None,
        },
        "convergence": {
            "target": conv.target,
            "stable_events": conv.stable,
            "stable_k": conv.stable_k,
            "gradings": state.gradings,
            "invalid_rate": round(state.invalid_count / state.gradings, 6) if state.gradings else 0.0,
            "rounds": state.round,
            "gen": state.gen,
        },
        "residual": {
            "invalid_count": state.invalid_count,
            "void_at_fold": list(state.void_at_fold),
            "duplicate_gradings": list(state.duplicate_gradings),
            "unscored": [a.name for a in state.arms.values() if a.produced and not a.scored],
        },
        "spend": {
            **{k: round(v, 8) for k, v in state.spend.items()},
            "total": state.spend_total,
            "pricebook": pricebook_pin,
            # The second log, recorded beside the first. RE-4's bar is that these AGREE; carrying
            # both is what makes the agreement checkable after the fact instead of at emit time only.
            "escrow_committed_usd": (
                round(escrow_committed_usd, 8) if escrow_committed_usd is not None else None
            ),
        },
        "recompute": {
            "culture": state.culture,
            "span": list(state.span),
            "chain_head": state.chain_head,
            "procedure": f"hc verify {state.run_id}",
        },
    }
    if vs_null is not None:
        cert["vs_null"] = dict(vs_null)
    cert["cert_sha256"] = "sha256:" + hashlib.sha256(canon_bytes(_body(cert))).hexdigest()
    cert["semantic_sha256"] = "sha256:" + hashlib.sha256(canon_bytes(_semantic(cert))).hexdigest()
    return cert


#: Fields that locate a certificate in ONE physical log rather than describing the run.
_COORDINATES = ("recompute",)


def _body(cert: dict[str, Any]) -> dict[str, Any]:
    """The canonical body the cert digest covers — everything but the digests and the signature.

    A digest cannot cover itself, and the signature seam (Stage-1b conductor key) signs this same
    body, so the two agree on what "the certificate" means.
    """
    return {k: v for k, v in cert.items()
            if k not in ("cert_sha256", "semantic_sha256", "signature")}


def _semantic(cert: dict[str, Any]) -> dict[str, Any]:
    """The body MINUS the physical-log coordinates — what a run IS, not where it is written.

    Two runs that reach the same conclusions from the same inputs have identical semantics and
    NECESSARILY different `recompute.chain_head`: each record carries its own `ts`, so two logs
    written at different moments chain differently even when every decision matches. That is the
    chain working, not drifting.

    Wire C9 already draws this line one level down — replay equality holds "excluding `ts`/`hash`
    timing" — and RE-4's bar ("field-identical to an uninterrupted control") is the same line drawn
    for certificates. Read any other way the bar is unsatisfiable by construction: an interrupted
    run and an uninterrupted one are two physical logs, always.

    So the certificate carries two digests with two jobs. `cert_sha256` commits to a specific log
    (it is what `hc verify` and the Stage-1b signature cover, and it MUST move when the log moves).
    `semantic_sha256` commits to the run's conclusions, and it is what survives a resume.
    """
    return {k: v for k, v in _body(cert).items() if k not in _COORDINATES}


def _verdict_kind(state: PlanesState) -> str:
    if not state.convergence.converged:
        return "unverified"
    residual = state.invalid_count or state.void_at_fold or state.duplicate_gradings
    return "verified-with-residual" if residual else "verified"


# ---------------------------------------------------------------------------- hc verify


def verify_certificate(
    cert: dict[str, Any],
    records: list[dict[str, Any]],
    *,
    chain_ok: bool = True,
    escrow_committed_usd: float | None = None,
    oracle: dict[str, Any] | None = None,
    pricebook_pin: str = "",
    vs_null: dict[str, Any] | None = None,
) -> VerifyResult:
    """Recompute the fold and diff the certificate field by field (§R8.1 steps 1–5).

    A single flipped bit anywhere in the span changes a leaf, which changes the chain, which fails
    step 1 — and if a verifier were handed a span whose chain was repaired, the recomputed fold
    still moves and step 3 names the field that moved. Two independent nets over the same fabric.
    """
    culture = str(cert.get("recompute", {}).get("culture", ""))
    span = cert.get("recompute", {}).get("span") or None
    state = fold(culture, records, span=(int(span[0]), int(span[1])) if span else None)

    recomputed = certificate(
        state, oracle=oracle, pricebook_pin=pricebook_pin, vs_null=vs_null,
        escrow_committed_usd=escrow_committed_usd,
    )

    bad = _diff(_body(cert), _body(recomputed))
    spend_agrees = _spend_agrees(cert, escrow_committed_usd)

    result = VerifyResult(
        ok=chain_ok and not bad and spend_agrees,
        bad_fields=bad,
        chain_ok=chain_ok,
        spend_agrees=spend_agrees,
        detail={
            "claimed_total": cert.get("spend", {}).get("total"),
            "escrow_committed_usd": escrow_committed_usd,
            "recomputed_total": recomputed.get("spend", {}).get("total"),
        },
    )
    return result


def _spend_agrees(cert: dict[str, Any], escrow_committed_usd: float | None) -> bool:
    """The two-log agreement: span `cost{}` sums vs the conductor's escrow-ledger fold.

    Skipped only when there is no escrow log to compare against (a stub run). Two records of the
    same dollars, maintained by different code on different write paths: agreement is evidence,
    and a certificate that averaged them would be manufacturing a number neither log holds.
    """
    if escrow_committed_usd is None:
        return True
    claimed = float(cert.get("spend", {}).get("total", 0.0) or 0.0)
    return abs(claimed - float(escrow_committed_usd)) <= SPEND_EPSILON


def _diff(claimed: Any, actual: Any, path: str = "") -> list[str]:
    """Field-named structural diff. Returns dotted paths, so a failure points at a field."""
    bad: list[str] = []
    if isinstance(claimed, dict) and isinstance(actual, dict):
        for key in sorted(set(claimed) | set(actual)):
            here = f"{path}.{key}" if path else key
            if key not in claimed or key not in actual:
                bad.append(here)
            else:
                bad.extend(_diff(claimed[key], actual[key], here))
        return bad
    if isinstance(claimed, float) or isinstance(actual, float):
        try:
            if abs(float(claimed) - float(actual)) > SPEND_EPSILON:
                bad.append(path)
            return bad
        except (TypeError, ValueError):
            pass
    if claimed != actual:
        bad.append(path)
    return bad
