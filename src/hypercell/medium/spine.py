"""The version spine — census-in-genesis, the spawn gate, and `fleet_versions()` (slice S-KG-2).

Two mechanisms, one idea: **a fleet must be able to say what versions it is running, and refuse
what it cannot read.**

* **MIG-5 / R2 reader liberality.** An envelope carrying fields this build has never heard of must
  survive store-and-relay **byte-identically**. The null is known-columns storage — a reader that
  keeps only what it recognises, which silently truncates every message a newer peer sends and makes
  a MINOR upgrade a data-loss event. That was F18.
* **MIG-3 census gate.** A spawn whose image declares an unknown contract, or a **newer MAJOR** than
  this build can read, is REFUSED with a receipt. The null is trust-the-image: admit it and hope.
  Hope is not a migration strategy, and a cell that silently mis-parses a newer envelope corrupts
  folds nobody will trace back to the upgrade.

The asymmetry between them is deliberate and is the whole of R2: **liberal on fields, strict on
MAJORs.** An unknown *field* is a message from the future you can safely carry; an unknown *MAJOR*
is a message from the future you would mis-read.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..common.census import CENSUS


class CensusRefusal(Exception):
    """A spawn refused by the census gate. Refusals are receipts (MIG-3)."""

    def __init__(self, reason: str, detail: str) -> None:
        super().__init__(f"refused/{reason}: {detail}")
        self.reason = reason
        self.detail = detail


def _major(version: str) -> int:
    try:
        return int(str(version).split(".")[0])
    except (ValueError, IndexError):
        raise CensusRefusal("census_unparseable", f"'{version}' is not a semver") from None


@dataclass(frozen=True)
class CensusVerdict:
    ok: bool
    reason: str = ""
    detail: str = ""
    skew: dict[str, tuple[str, str]] | None = None  # contract -> (local, image)


def check_census(image: dict[str, str], local: dict[str, str] | None = None) -> CensusVerdict:
    """The spawn gate. A MINOR skew is legal; an unknown contract or a newer MAJOR is not.

    A partial census is refused too: a nine-tuple with a hole cannot be reasoned about, and
    accepting it would mean guessing which contract the image left out.
    """
    mine = dict(local or CENSUS)

    missing = sorted(set(mine) - set(image))
    if missing:
        raise CensusRefusal(
            "census_partial",
            f"the image census omits {missing}. A nine-tuple with a hole cannot be reasoned about — "
            "admitting it would mean guessing which contract was left out.",
        )

    unknown = sorted(set(image) - set(mine))
    if unknown:
        raise CensusRefusal(
            "census_unknown_contract",
            f"the image declares contracts this build has never heard of: {unknown}. "
            "Upgrade the conductor before admitting cells that speak more than it does.",
        )

    skew: dict[str, tuple[str, str]] = {}
    for name, image_version in image.items():
        local_version = mine[name]
        if image_version == local_version:
            continue
        skew[name] = (local_version, image_version)
        if _major(image_version) > _major(local_version):
            raise CensusRefusal(
                "census_newer_major",
                f"'{name}' is {image_version} in the image but {local_version} here. A newer MAJOR "
                "is a message this build would MIS-READ, not merely fail to read — refusing is the "
                "only outcome that cannot corrupt a fold.",
            )

    return CensusVerdict(ok=True, skew=skew or None)


def admit_spawn(image: dict[str, str], *, local: dict[str, str] | None = None) -> dict[str, Any]:
    """Gate a spawn and return the receipt body — for admission AND for refusal.

    A refusal that leaves no record is a refusal nobody can count, and "how often does this fire?"
    is the first question anyone asks of a gate.
    """
    try:
        verdict = check_census(image, local)
    except CensusRefusal as refusal:
        return {
            "kind": "spawn_admission",
            "admitted": False,
            "reason": refusal.reason,
            "detail": refusal.detail,
            "image_census": dict(image),
        }
    return {
        "kind": "spawn_admission",
        "admitted": True,
        "skew": {k: {"local": v[0], "image": v[1]} for k, v in (verdict.skew or {}).items()},
        "image_census": dict(image),
    }


def fleet_versions(records: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    """Fold `presence`/genesis records into the fleet's version spread.

    `{contract: {version: count}}`. A fleet running two MINORs of `wire` is legal and normal during a
    rolling upgrade; seeing it is how an operator knows the upgrade is half-done rather than stuck.
    """
    spread: dict[str, dict[str, int]] = {}
    for rec in records:
        body = rec.get("body")
        if not isinstance(body, dict):
            continue
        census = body.get("contract") or body.get("census")
        if not isinstance(census, dict):
            continue
        for name, version in census.items():
            spread.setdefault(str(name), {}).setdefault(str(version), 0)
            spread[str(name)][str(version)] += 1
    return spread
