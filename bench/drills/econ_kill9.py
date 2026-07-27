"""The kill-9 MONEY harness: a real process, really killed, mid-metered-spend (RESUME-$1).

The ECON drills model their crashes — they arrange ledger states and reason from there, and they
run `fsync=False` for speed. Both facts are stated in the ledger, and both mean those drills prove
the fold logic, not the durability. This harness proves the durability: a child process spends
through the REAL metered path (Governor.open_call → close_call over the dated pricebook) with
fsync ON, then opens one more reservation and hangs; the parent kills it with no handlers and no
flush. What the resumed escrow knows is exactly what the fsync'd ledger holds.

F16's regression lives here: the live v1 bug was a resumed run whose RAM meter forgot its spending
and granted itself the whole budget again. The bar: the resumed run cannot exceed the original
cap, and folded spend equals the pre-crash ledger sum.

Run standalone:  `python -m bench.drills.econ_kill9 <home>`  (the child half; the parent is the test)
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

SENTINEL = "spent.flag"
CAP_USD = 1.0
SCOPE = "run:kill9"
CALLS = 3


class _Result:
    """A completion the pricebook can price, with no network. The metered path neither knows nor
    cares that no provider was called — which is the point: the money path is fully exercised."""

    model = "gpt-4o-mini"
    prompt_tokens, completion_tokens = 20_000, 2_000
    cache_read_tokens = cache_write_tokens = 0
    api_reported_usd = None


def child(home: Path) -> None:
    from hypercell.conductor.governor import Escrow, Governor

    escrow = Escrow(cap_usd=CAP_USD, home=home)  # fsync=True: the default IS the drill
    governor = Governor(usd_cap=CAP_USD, escrow=escrow, scope=SCOPE)

    for _ in range(CALLS):
        resv_id = governor.open_call(
            "openai", {"model": "gpt-4o-mini", "max_tokens": 2_000, "est_prompt_tokens": 20_000}
        )
        governor.close_call(resv_id, "openai", _Result())

    # One more reservation, held and never settled — the in-flight call the crash interrupts.
    governor.open_call(
        "openai", {"model": "gpt-4o-mini", "max_tokens": 2_000, "est_prompt_tokens": 20_000}
    )

    # Tell the parent what the truth was at the moment of death, then wait to die.
    (home / SENTINEL).write_text(
        json.dumps({"committed": escrow.committed("fleet"), "spent": governor.spent}),
        encoding="utf-8",
    )
    while True:  # pragma: no cover - the parent kills us here
        time.sleep(0.05)


if __name__ == "__main__":  # pragma: no cover - driven as a subprocess
    child(Path(sys.argv[1]))
