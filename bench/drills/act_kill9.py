"""The kill-9 harness: a real process, really killed, in the irreducible window (ACT-SETTLE-1).

Every other crash-window drill in `tests/test_act_world_write.py` *models* the crash — it arranges
the on-disk state a dead process would have left and reasons from there. That is worth doing and it
is not the same claim. This one starts an actual child, lets it touch the world, and has the parent
kill it with no cleanup, no handlers and no flush. What survives is what was durable.

The window is **W4** (`execute → receipt`), and W4 is irreducible: you cannot fsync a receipt before
the world has answered. So it is not a window the fabric can shrink its way out of — the probe is
the only answer, which is exactly why act.md §8 makes probes mandatory at H1+.

Run standalone:  `python -m bench.drills.act_kill9 <home>`  (the child half; the parent is the test)
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

CORR = "act_killed_mid_flight"
SENTINEL = "delivered.flag"


def child(home: Path) -> None:
    """Deliver for real, announce it, then hang so the parent can kill us before the receipt."""
    os.environ["HYPERCELL_OUTBOX"] = str(home / "outbox")

    from hypercell.act.adapters import deliver_outbox
    from hypercell.act.executor import ActExecutor
    from hypercell.cell.nucleus import Nucleus
    from hypercell.conductor.registry import EffectRegistry

    registry = EffectRegistry(home)
    nucleus = Nucleus(home, "r1/agent/0")
    executor = ActExecutor(
        nucleus=nucleus, home=home, registry=registry, role_harm_ceiling="H1"
    )

    delivery = {"to": "ops@example.test", "subject": "the one message", "body": "sent once"}
    key = executor.effect_key_for("deliver.outbox", delivery, step_id="step-1")

    # The pipeline by hand, so we can stop precisely inside W4 rather than near it.
    registry.reserve(key, CORR)
    nucleus.append(
        "action",
        {"verb": "act", "corr": CORR, "capability_ref": "deliver.outbox", "effect_key": key},
        idem=CORR,
        durability="gold",
    )
    deliver_outbox.execute(dict(delivery, effect_key=key))
    registry.transition(key, "executed")

    # The world has moved and nothing has written the receipt. Tell the parent, then wait to die.
    (home / SENTINEL).write_text(key, encoding="utf-8")
    while True:  # pragma: no cover - the parent kills us here
        time.sleep(0.05)


if __name__ == "__main__":  # pragma: no cover - driven as a subprocess
    child(Path(sys.argv[1]))
