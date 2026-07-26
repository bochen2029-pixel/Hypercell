"""CONTRACT-HDR-1 — the contract header gate drill (ARCHITECTURE §15; slice S-KG-1).

Two halves, and the second matters more:

* the nine real contracts MUST pass, and
* a **deliberately broken** contract MUST fail — a gate that cannot fail is not a gate, it is
  decoration that makes everyone feel checked.

The null: unversioned prose headers (the live v0.1 DRAFT state, where nothing was migratable — G3).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from tools import check_contracts as cc

CONFORMING = """# CONTRACT: widget — the widget plane

**Version:** `widget/5.1.0` · **Status:** RATIFIED · **Date:** 2026-07-25
**Pairing (H2):** `Widget` (noun) · **Emit/read (H4):** strict-emit / liberal-read ·
**Operator boundary (R5):** strict-both
**Schema mirror:** `contracts/schemas/widget.schema.json`
**Migrates from:** v0.1 stub (live repo)
**Falsifiers:** [WIDGET-1]

## §1 · Body
Body text mentioning nothing header-ish.
"""


def _write(tmp: Path, name: str, text: str, schema_version: str | None = "5.1.0") -> None:
    (tmp / "contracts").mkdir(parents=True, exist_ok=True)
    (tmp / "contracts" / "schemas").mkdir(parents=True, exist_ok=True)
    (tmp / "contracts" / f"{name}.md").write_text(text, encoding="utf-8")
    if schema_version is not None:
        (tmp / "contracts" / "schemas" / f"{name}.schema.json").write_text(
            json.dumps({"$id": f"hypercell/contracts/{name}/{schema_version}", "type": "object"}),
            encoding="utf-8",
        )


@pytest.fixture
def sandbox(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the gate at a synthetic one-contract world so failures are constructible."""
    monkeypatch.setattr(cc, "REPO", tmp_path)
    monkeypatch.setattr(cc, "CONTRACTS", tmp_path / "contracts")
    monkeypatch.setattr(cc, "SCHEMAS", tmp_path / "contracts" / "schemas")
    monkeypatch.setattr(cc, "THE_NINE", ("widget",))
    return tmp_path


# ---------------------------------------------------------------- the real contracts


def test_the_nine_real_contracts_conform() -> None:
    """The shipped constitution passes its own gate."""
    report = cc.check()
    assert report.ok, "\n".join(f"{f.contract}: {f.problem}" for f in report.findings)


def test_inventory_is_closed_at_nine() -> None:
    assert len(cc.THE_NINE) == 9, "the pairing law (H2) closes the inventory at nine"
    for name in cc.THE_NINE:
        assert (cc.CONTRACTS / f"{name}.md").exists()
        assert (cc.SCHEMAS / f"{name}.schema.json").exists()


def test_schemas_dir_is_not_empty() -> None:
    """G3, the lived defect: `contracts/schemas/` was planned in B1 and never created."""
    assert len(list(cc.SCHEMAS.glob("*.schema.json"))) == 9


# ---------------------------------------------------------------- the gate must FAIL things


def test_conforming_synthetic_passes(sandbox: Path) -> None:
    _write(sandbox, "widget", CONFORMING)
    assert cc.check().ok


@pytest.mark.parametrize(
    ("fact", "line"),
    [
        ("version", "**Version:** `widget/5.1.0` · **Status:** RATIFIED · **Date:** 2026-07-25"),
        ("schema_mirror", "**Schema mirror:** `contracts/schemas/widget.schema.json`"),
        ("migrates_from", "**Migrates from:** v0.1 stub (live repo)"),
        ("falsifiers", "**Falsifiers:** [WIDGET-1]"),
        ("operator_boundary", "**Operator boundary (R5):** strict-both"),
    ],
)
def test_removing_any_fact_fails_the_gate(sandbox: Path, fact: str, line: str) -> None:
    """Delete one header fact at a time; the gate must name exactly that fact."""
    _write(sandbox, "widget", CONFORMING.replace(line, ""))
    report = cc.check()
    assert not report.ok, f"gate passed a contract with no `{fact}`"
    assert any(fact in f.problem for f in report.findings), [f.problem for f in report.findings]


def test_version_bump_without_mirror_regen_fails(sandbox: Path) -> None:
    """The other half of the law: a bump whose mirror stayed behind is G3 wearing a newer number."""
    _write(sandbox, "widget", CONFORMING.replace("widget/5.1.0", "widget/5.2.0"), schema_version="5.1.0")
    report = cc.check()
    assert not report.ok
    assert any("5.2.0" in f.problem and "5.1.0" in f.problem for f in report.findings)


def test_missing_mirror_fails(sandbox: Path) -> None:
    _write(sandbox, "widget", CONFORMING, schema_version=None)
    report = cc.check()
    assert not report.ok
    assert any("schema mirror" in f.problem for f in report.findings)


def test_unparseable_mirror_fails(sandbox: Path) -> None:
    _write(sandbox, "widget", CONFORMING)
    (sandbox / "contracts" / "schemas" / "widget.schema.json").write_text("{not json", encoding="utf-8")
    report = cc.check()
    assert not report.ok
    assert any("not valid JSON" in f.problem for f in report.findings)


def test_missing_contract_file_fails(sandbox: Path) -> None:
    report = cc.check()  # nothing written at all
    assert not report.ok
    assert any("does not exist" in f.problem for f in report.findings)


# ---------------------------------------------------------------- R23: facts, not typography


def test_yaml_block_header_conforms(sandbox: Path) -> None:
    """The fenced YAML form is conforming."""
    yaml_style = """# CONTRACT: widget

```yaml
contract: widget
version: 5.1.0
status: RATIFIED
pairing: Widget
emit_read: strict-emit / liberal-read
operator_boundary: strict-both
schema_mirror: contracts/schemas/widget.schema.json
migrates_from: v0.1 stub
falsifiers: [WIDGET-1]
```

## §1 · Body
"""
    _write(sandbox, "widget", yaml_style)
    assert cc.check().ok


def test_prose_header_conforms_too(sandbox: Path) -> None:
    """R23: a contract whose header is readable prose is a conforming contract.

    A gate that failed this would be enforcing typography, not constitution.
    """
    _write(sandbox, "widget", CONFORMING)  # bold-prose form
    assert cc.check().ok


def test_body_mentions_do_not_satisfy_a_header_fact(sandbox: Path) -> None:
    """Scoping matters: a fact buried in the body must not satisfy a *header* requirement."""
    broken = CONFORMING.replace("**Falsifiers:** [WIDGET-1]", "") + "\n**Falsifiers:** [WIDGET-1]\n"
    _write(sandbox, "widget", broken)
    report = cc.check()
    assert not report.ok
    assert any("falsifiers" in f.problem for f in report.findings)


def test_every_finding_carries_a_fix(sandbox: Path) -> None:
    """Same discipline as the preflight: no failure without a way out of it."""
    _write(sandbox, "widget", CONFORMING.replace("**Falsifiers:** [WIDGET-1]", ""))
    for f in cc.check().findings:
        assert f.fix.strip(), f"{f.contract}: {f.problem} — no fix offered"

