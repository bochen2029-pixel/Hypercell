#!/usr/bin/env python
"""CONTRACT-HDR-1 -- the contract header gate (ARCHITECTURE §15; slice S-KG-1).

The null this kills: the live v0.1 DRAFT state, where a contract could not say what version it was,
so nothing was migratable (G3).

Two things are checked, and only two:

1. **The nine header FACTS are present** in every contract -- `contract, version, status, pairing,
   emit_read, operator_boundary, schema_mirror, migrates_from, falsifiers`. Per **R23** the gate
   checks *presence of the facts*, stated either as the fenced YAML block or as labeled prose. A
   gate that failed readable prose would be enforcing typography, not constitution.

2. **A version bump ships with its regenerated mirror.** The contract's semver and its
   `schemas/<name>.schema.json` must agree. Bumping one without the other is the lived G3 defect
   wearing a newer number.

Run standalone (`python tools/check_contracts.py`) or via pytest (`tests/test_contract_headers.py`).
Exit 0 = every contract conforms; exit 1 = at least one does not, with the reason named.
"""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONTRACTS = REPO / "contracts"
SCHEMAS = CONTRACTS / "schemas"

#: The closed inventory (H2). Exactly nine separately-versioned contract artifacts exist.
THE_NINE = (
    "wire",
    "nucleus",
    "role",
    "run",
    "oracle",
    "act",
    "pricebook",
    "command",
    "identity-firewall",
)

#: Each fact and the spellings that state it. YAML key, bold prose label, or an equivalent phrasing --
#: all three are conforming, because the law is the fact, not the serialization (R23).
FACT_PATTERNS: dict[str, tuple[str, ...]] = {
    # NB: every pattern is matched against a lowercased header, so every pattern is lowercase.
    "contract": (r"^\s*contract\s*:", r"\*\*contract\b", r"^#\s*contract\s*:"),
    "version": (r"^\s*version\s*:", r"\*\*version\b", r"^\s*semver\s*:", r"\*\*semver\b"),
    "status": (r"^\s*status\s*:", r"\*\*status\b"),
    "pairing": (r"^\s*pairing\s*:", r"\*\*pairing\b", r"\*\*pairs with\b"),
    "emit_read": (r"^\s*emit_read\s*:", r"\*\*emit/read\b", r"\*\*emit_read\b"),
    "operator_boundary": (r"^\s*operator_boundary\s*:", r"\*\*operator boundary\b"),
    "schema_mirror": (r"^\s*schema_mirror\s*:", r"\*\*schema mirror\b", r"schemas/[\w-]+\.schema\.json"),
    # "what this replaces" has four house spellings across the nine. All four state the same fact,
    # so all four conform -- widening this list is R23 working, not the gate going soft.
    "migrates_from": (
        r"^\s*migrates_from\s*:",
        r"\*\*migrates from\b",
        r"\*\*migration from\b",
        r"\*\*replaces\b",
        r"^\s*replaces\s*:",
        r"\*\*supersedes\b",
        r"^\s*supersedes\s*:",
    ),
    "falsifiers": (r"^\s*falsifiers\s*:", r"\*\*falsifiers\b"),
}

_SEMVER = re.compile(r"(\d+\.\d+\.\d+)")


@dataclass
class Finding:
    contract: str
    problem: str
    fix: str


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.findings

    def add(self, contract: str, problem: str, fix: str) -> None:
        self.findings.append(Finding(contract, problem, fix))


def header_of(text: str) -> str:
    """The header block is everything before the first body section.

    Scoping the scan matters: searching the whole file would let a fact mentioned in passing in the
    body satisfy a header requirement, which is precisely the sloppiness the gate exists to prevent.
    """
    match = re.search(r"^##\s", text, re.MULTILINE)
    return text[: match.start()] if match else text


def missing_facts(header: str) -> list[str]:
    lowered = header.lower()
    missing = []
    for fact, patterns in FACT_PATTERNS.items():
        if not any(re.search(p, lowered, re.MULTILINE) for p in patterns):
            missing.append(fact)
    return missing


def declared_version(header: str) -> str | None:
    m = _SEMVER.search(header)
    return m.group(1) if m else None


def mirror_version(schema: dict[str, object]) -> str | None:
    """The mirror's own version -- from `$id` (…/<name>/<semver>) or a top-level `version`."""
    for key in ("$id", "version"):
        raw = schema.get(key)
        if isinstance(raw, str):
            m = _SEMVER.search(raw)
            if m:
                return m.group(1)
    return None


def check() -> Report:
    report = Report()

    for name in THE_NINE:
        path = CONTRACTS / f"{name}.md"
        if not path.exists():
            report.add(
                name,
                f"{path.relative_to(REPO)} does not exist",
                "write the contract; the inventory is closed at nine (H2)",
            )
            continue

        text = path.read_text(encoding="utf-8")
        header = header_of(text)

        for fact in missing_facts(header):
            report.add(
                name,
                f"header states no `{fact}`",
                f"add a `{fact}` fact to {name}.md's header -- as a YAML key or a labeled prose line "
                f"(R23: either is conforming)",
            )

        # --- the mirror must exist and agree on version
        schema_path = SCHEMAS / f"{name}.schema.json"
        if not schema_path.exists():
            report.add(
                name,
                f"no schema mirror at {schema_path.relative_to(REPO)}",
                "generate the mirror; a contract without one is unversionable in the census (G3)",
            )
            continue

        try:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            report.add(name, f"{schema_path.name} is not valid JSON: {exc}", "regenerate the mirror")
            continue

        cv, mv = declared_version(header), mirror_version(schema)
        if cv is None:
            report.add(name, "header declares no semver", "state `version: <MAJOR>.<MINOR>.<PATCH>`")
        elif mv is None:
            report.add(name, f"{schema_path.name} declares no version", "put the semver in the mirror's $id")
        elif cv != mv:
            report.add(
                name,
                f"contract is {cv} but its mirror is {mv}",
                "regenerate the mirror in the SAME commit as the bump -- a version bump without its "
                "mirror is the lived G3 defect wearing a newer number",
            )

    return report


def main() -> int:
    report = check()
    if report.ok:
        print(f"CONTRACT-HDR-1: PASS -- {len(THE_NINE)} contracts, nine header facts each, mirrors in lockstep")
        return 0

    print(f"CONTRACT-HDR-1: FAIL -- {len(report.findings)} problem(s)\n")
    current = ""
    for f in report.findings:
        if f.contract != current:
            print(f"  {f.contract}.md")
            current = f.contract
        print(f"    - {f.problem}")
        print(f"      fix: {f.fix}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
