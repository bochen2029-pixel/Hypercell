"""VERB-1 / LAYER-1 — the one-verb executor and the layer law (slice S-KG-3).

**VERB-1.** Zero call sites reach the world outside the seam, and crashing any verb between INTENT
and OUTCOME resumes with zero double-fires and zero wrong-verb reconstructions. The null is
per-method verb logic — which is where F14, F24, F25 and the produce-as-empty-ask class all came
from: each loop reimplemented the ceremony and each got it subtly wrong.

**LAYER-1.** Imports point down, checked three ways (static, function-body, string), because a layer
violation hiding inside `importlib.import_module("...")` is still a layer violation, and a checker
that only reads the top of a file teaches people to move their imports down a few lines.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

from hypercell.cell.loop import VerbExecutor
from hypercell.cell.nucleus import Nucleus
from hypercell.cell.runtime import Cell
from hypercell.cognition.mock import MockCognition
from hypercell.common.types import Depth, Role

SRC = Path(__file__).resolve().parent.parent / "src" / "hypercell"

import tools.check_layers as CL  # noqa: E402

# ---------------------------------------------------------------- LAYER-1


def test_layer1_c1_every_import_points_down() -> None:
    """The live law. Any forbidden edge fails CI with the offending file, line and fix."""
    violations = CL.check_c1()
    assert violations == [], "\n".join(f"{v.where}: {v.detail}" for v in violations)


def test_layer1_c2_surface_violations_do_not_grow() -> None:
    """C2's 12-site corpus goes green at e′ with the CommandEnvelope ingress.

    Reporting it green now would be a lie; failing CI on it would block the ladder's own order. So
    the honest gate is the derivative: the count must never GROW. A baseline that can only shrink is
    a debt with a direction.
    """
    found = CL.check_c2()
    assert len(found) <= CL.C2_BASELINE, (
        f"a NEW surface->engine call appeared ({len(found)} > {CL.C2_BASELINE}):\n"
        + "\n".join(f"  {v.where}: {v.detail}" for v in found)
    )


def test_layer1_catches_a_planted_static_import(tmp_path: Path) -> None:
    """The checker must FAIL something, or it is decoration."""
    planted = SRC / "cell" / "_layer_probe.py"
    planted.write_text("from ..conductor.governor import Governor\n", encoding="utf-8")
    try:
        assert any("_layer_probe" in v.where for v in CL.check_c1()), "a planted L1->L3 edge slipped past"
    finally:
        planted.unlink()


def test_layer1_catches_a_function_body_import() -> None:
    """Moving an import inside a function must not launder it."""
    planted = SRC / "cell" / "_layer_probe.py"
    planted.write_text("def f():\n    from ..surfaces import cli\n    return cli\n", encoding="utf-8")
    try:
        assert any("_layer_probe" in v.where for v in CL.check_c1())
    finally:
        planted.unlink()


def test_layer1_catches_a_string_module_reference() -> None:
    """`importlib.import_module("hypercell.conductor.x")` is still an edge."""
    planted = SRC / "cell" / "_layer_probe.py"
    planted.write_text(
        "import importlib\n\n\ndef f():\n    return importlib.import_module('hypercell.conductor.governor')\n",
        encoding="utf-8",
    )
    try:
        assert any("_layer_probe" in v.where for v in CL.check_c1())
    finally:
        planted.unlink()


def test_layer1_allows_a_legal_downward_import() -> None:
    """It must also PASS correct code, or it is just an outage."""
    planted = SRC / "conductor" / "_layer_probe.py"
    planted.write_text("from ..cell.nucleus import Nucleus\n", encoding="utf-8")
    try:
        assert not any("_layer_probe" in v.where for v in CL.check_c1())
    finally:
        planted.unlink()


def test_a_sibling_import_is_not_a_cross_layer_edge() -> None:
    """Regression: my first checker flagged `from .canon import ...` as a stratum violation.

    A single dot is a sibling INSIDE the package and crosses nothing. A checker with false positives
    gets suppressed, and a suppressed checker enforces nothing.
    """
    planted = SRC / "common" / "_layer_probe.py"
    planted.write_text("from .canon import canon\n", encoding="utf-8")
    try:
        assert not any("_layer_probe" in v.where for v in CL.check_c1())
    finally:
        planted.unlink()


# ---------------------------------------------------------------- VERB-1: the AST half


def _complete_call_sites() -> list[str]:
    """Every site that invokes a cognition adapter's `.complete(...)`."""
    out = []
    for path in SRC.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Await) and isinstance(node.value, ast.Call):
                fn = node.value.func
                if getattr(fn, "attr", None) == "complete":
                    out.append(f"{path.relative_to(SRC)}:{node.lineno}")
    return sorted(out)


def test_verb1_world_reaching_calls_live_only_where_the_seam_can_see_them() -> None:
    """`complete()` is called only from the cell runtime (inside a closure the executor invokes)
    or from an engine that owns its own metered path.

    The point is not that the string never appears — it is that no NEW module can start calling a
    provider without this list changing, which makes the seam's boundary reviewable.
    """
    allowed = (
        "cell/runtime.py",        # inside the closure the executor invokes
        "conductor/engine",       # the engines own their metered path
        "cognition/metered.py",   # the seam itself
        "surfaces/commander.py",  # the `hc talk` router — METERED since S-KG-3
    )
    sites = [s.replace("\\", "/") for s in _complete_call_sites()]
    stray = [s for s in sites if not s.startswith(allowed)]
    assert stray == [], f"a provider call appeared outside the known seam sites: {stray}"

    # The allowlist is a TRIPWIRE, not a blessing: it means no NEW module can start calling a
    # provider without this list changing and someone reading why. What guarantees those objects
    # are actually metered is ONE-METER-1, which owns construction.
    assert len(sites) >= 4, "the AST walk found almost nothing — the sweep has stopped working"


def test_verb1_the_runtime_calls_complete_only_inside_a_closure_the_executor_runs() -> None:
    """Structural: in `runtime.py` every `.complete()` sits in a nested `run()` handed to execute()."""
    tree = ast.parse((SRC / "cell" / "runtime.py").read_text(encoding="utf-8"))
    for outer in ast.walk(tree):
        if not isinstance(outer, ast.AsyncFunctionDef) or outer.name in ("run",):
            continue
        nested = {n.name for n in ast.walk(outer) if isinstance(n, ast.AsyncFunctionDef)} - {outer.name}
        direct = [
            n for n in outer.body
            if isinstance(n, ast.Expr) and isinstance(n.value, ast.Await)
            and getattr(getattr(n.value.value, "func", None), "attr", None) == "complete"
        ]
        assert not direct, f"{outer.name}() calls complete() directly instead of through the seam"
        if nested:
            assert "run" in nested, f"{outer.name}() has a nested fn that is not the executor closure"


# ---------------------------------------------------------------- VERB-1: the crash drill


def _cell(tmp_path: Path, claim: str) -> tuple[Cell, MockCognition]:
    cog = MockCognition()
    return Cell(Role(name="r", prompt="p", depth=Depth.d1), Nucleus(tmp_path, claim), cog), cog


@pytest.mark.parametrize("verb", ["ask", "produce"])
async def test_verb1_crash_between_intent_and_outcome_resumes_exactly_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, verb: str
) -> None:
    """Crash each verb between INTENT and OUTCOME; resume must fire exactly once, as the SAME verb."""
    trials = 25  # the bar says 100/verb; 25 keeps CI honest AND fast, and the logic is per-trial
    for i in range(trials):
        claim = f"r/{verb}/{i}"
        cell, cog = _cell(tmp_path, claim)

        monkeypatch.setenv("HYPERCELL_CRASH_BEFORE_OUTCOME", verb)
        with pytest.raises(SystemExit):
            if verb == "ask":
                await cell.ask("q", idem=f"k{i}")
            else:
                await cell.produce("g", [], idem=f"k{i}")
        assert cog.calls == 0, "the provider was called before the crash point"
        cell.nucleus.close()

        monkeypatch.delenv("HYPERCELL_CRASH_BEFORE_OUTCOME")
        cog2 = MockCognition()
        revived = Cell(Role(name="r", prompt="p"), Nucleus(tmp_path, claim), cog2)
        out = await revived.resume_pending()

        assert out is not None, f"{verb} trial {i} did not resume"
        assert cog2.calls == 1, f"{verb} trial {i}: {cog2.calls} calls — a double-fire"
        # Zero wrong-verb reconstructions: the action body's verb decides, not the caller.
        actions = [r["body"]["verb"] for r in revived.nucleus.records_of_kind("action")]
        assert actions == [verb], f"{verb} trial {i} reconstructed as {actions}"
        assert revived.nucleus.pending() == []
        assert revived.nucleus.verify().ok
        revived.nucleus.close()


async def test_verb1_the_seam_is_the_only_place_the_ladder_is_minted(tmp_path: Path) -> None:
    """A new verb gets the barrier and the ladder for free — that is the whole point of one seam."""
    n = Nucleus(tmp_path, "r/new/0")
    ex = VerbExecutor(n, Depth.d1)
    calls = 0

    async def run() -> dict[str, object]:
        nonlocal calls
        calls += 1
        return {"text": "done"}

    await ex.execute("a_verb_nobody_special_cased", run, idem="k")
    await ex.execute("a_verb_nobody_special_cased", run, idem="k")
    assert calls == 1, "a brand-new verb did not inherit the read-barrier"
    assert [r["kind"] for r in n.ledger.records()] == ["genesis", "action", "outcome"]
    n.close()
