#!/usr/bin/env python
"""LAYER-1 — the layer law, mechanically (ARCHITECTURE §3.3; slice S-KG-3).

```
L4 SURFACES · L3 CONDUCTOR · L2 MEDIUM · L1 CELL · L0 SUBSTRATE
strata: common/ (types, ids, clock, protocol interfaces) · cognition/ (tissue adapters)
```

**C1 — imports point down, strata excepted.** Strata import nothing but `common`; a layer imports
only strata and *strictly lower* layers.

**C2 — verb ownership.** Surfaces compile intents to CommandEnvelopes. They MUST NOT call L1
constructors, L2 `post()`, or L3 engine functions directly.

The null this replaces is an import-direction rule that lives in a README. This one is checked three
ways — static import, function-body import, and string module reference — because a layer violation
that hides inside `importlib.import_module("...")` is still a layer violation, and a checker that
only reads the top of the file teaches people to move their imports down a few lines.

`act/` is L3: the act plane is executed by the executor principal (runner-N / a conductor resolver),
and its pipeline legitimately reads cell state, the Medium's tag law, and the conductor's escrow.
"""
from __future__ import annotations

import ast
import sys
from dataclasses import dataclass
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src" / "hypercell"

#: Layer rank. Strata are not layers — they sit below everything and may be imported by all.
LAYERS: dict[str, int] = {
    "substrate": 0,
    "cell": 10,
    "medium": 20,
    "conductor": 30,
    # The act plane sits ABOVE the conductor: its pipeline draws on the escrow, and nothing in the
    # conductor depends on act. Ranks are spaced so a plane can be inserted without renumbering.
    "act": 35,
    "surfaces": 40,
}
STRATA = frozenset({"common", "cognition"})

#: C2's live corpus (ARCHITECTURE §3.3): surfaces reaching past the command plane. These go green at
#: e′ with SUR-s1's CommandEnvelope ingress; until then the count must not GROW.
C2_BASELINE = 12


@dataclass
class Violation:
    clause: str
    where: str
    detail: str
    fix: str


def _package_of(path: Path) -> str | None:
    rel = path.relative_to(SRC).parts
    return rel[0] if len(rel) > 1 or rel[0].endswith(".py") is False else None


def _rank(pkg: str | None) -> int | None:
    return LAYERS.get(pkg or "")


def _targets(node: ast.AST, module_pkg: str) -> list[str]:
    """Every package this node references — static, function-body, or by string."""
    out: list[str] = []
    if isinstance(node, ast.ImportFrom):
        # `from .x import y` (level 1) is a sibling INSIDE this package and crosses nothing.
        # Only `from ..pkg import y` (level >= 2) leaves the package, and that is the edge we police.
        if node.level >= 2 and node.module:
            out.append(node.module.split(".")[0])
        elif node.module and node.module.startswith("hypercell."):
            out.append(node.module.split(".")[1])
    elif isinstance(node, ast.Import):
        for alias in node.names:
            if alias.name.startswith("hypercell."):
                out.append(alias.name.split(".")[1])
    elif isinstance(node, ast.Call):
        # importlib.import_module("hypercell.medium.x") and __import__ — a string is still an edge.
        fn = node.func
        name = getattr(fn, "attr", None) or getattr(fn, "id", None)
        if name in ("import_module", "__import__"):
            for arg in node.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    parts = arg.value.split(".")
                    if parts[0] == "hypercell" and len(parts) > 1:
                        out.append(parts[1])
                    elif parts[0] in LAYERS:
                        out.append(parts[0])
    return out


def check_c1() -> list[Violation]:
    """Imports point down. Strata import nothing but `common`."""
    out: list[Violation] = []
    for path in sorted(SRC.rglob("*.py")):
        pkg = path.relative_to(SRC).parts[0]
        if pkg.endswith(".py"):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        here = _rank(pkg)

        for node in ast.walk(tree):
            for target in _targets(node, pkg):
                if target == pkg or target == "common":
                    continue
                where = f"{path.relative_to(SRC)}:{getattr(node, 'lineno', 0)}"

                if pkg in STRATA and target not in STRATA:
                    out.append(Violation(
                        "C1", where, f"stratum '{pkg}' imports '{target}'",
                        "a stratum imports nothing but `common` — move the shared type into common/",
                    ))
                    continue
                if here is None or target in STRATA:
                    continue
                there = _rank(target)
                if there is not None and there >= here:
                    out.append(Violation(
                        "C1", where, f"{pkg}(L{here}) imports {target}(L{there})",
                        "imports point DOWN. If both need the same vocabulary, it belongs in a "
                        "stratum (common/), not in the higher layer.",
                    ))
    return out


def check_c2() -> list[Violation]:
    """Surfaces must not call L1 constructors, L2 `post()`, or L3 engine functions directly."""
    forbidden = {
        "build_cell": "an L1 constructor",
        "post": "an L2 Medium write",
        "run_tournament": "an L3 engine function",
        "run_drive": "an L3 engine function",
        "run_fanout": "an L3 engine function",
    }
    out: list[Violation] = []
    for path in sorted((SRC / "surfaces").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
            if name in forbidden:
                out.append(Violation(
                    "C2", f"{path.relative_to(SRC)}:{node.lineno}",
                    f"surface calls {name}() — {forbidden[name]}",
                    "compile the intent to a CommandEnvelope and post it; the command plane "
                    "executes (lands at e′ with SUR-s1)",
                ))
    return out


def main() -> int:
    c1, c2 = check_c1(), check_c2()

    if c1:
        print(f"LAYER-1 C1: FAIL — {len(c1)} forbidden edge(s)\n")
        for v in c1:
            print(f"  {v.where}\n    {v.detail}\n    fix: {v.fix}")
    else:
        print("LAYER-1 C1: PASS — every import points down")

    # C2 is a KNOWN-RED baseline, not a pass/fail gate, until the command plane lands at e′.
    # Reporting it as green would be a lie; failing CI on it would block the ladder's own order.
    # So the rule is: the count must never GROW.
    status = "at baseline" if len(c2) <= C2_BASELINE else "GROWING"
    print(f"\nLAYER-1 C2: {len(c2)}/{C2_BASELINE} known surface->engine calls ({status})")
    if len(c2) > C2_BASELINE:
        print("  C2 regressed — a NEW surface violation was added:")
        for v in c2:
            print(f"    {v.where}  {v.detail}")
        return 1
    return 1 if c1 else 0


if __name__ == "__main__":
    sys.exit(main())
