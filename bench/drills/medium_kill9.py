"""The W4 gold-durability harness: a real process, really killed, mid-traffic.

W4's bar has no null — "durability has no null; the bar is absolute." A `kill -9` storm mid-traffic
must lose **zero gold**, and every loss must be a contiguous **chatter-only suffix** (§5.4
prefix-durability). Modelling that would prove nothing: the whole claim is about what survives when
the process does not get to run another instruction, so the process has to actually not.

The child posts interleaved chatter and gold at `synchronous=FULL`, announces each gold post's seq
to a sentinel file (fsync'd, so the parent's expectation is itself durable), and keeps going until
the parent kills it. What the parent then finds in the reopened log is the measurement.

Run:  `python -m bench.drills.medium_kill9 <home>`  (the child half; the parent is the test)
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

CULTURE = "commons"
SENTINEL = "gold.jsonl"


def child(home: Path) -> None:
    from hypercell.conductor.anchor import AnchorLog
    from hypercell.medium.transport_local import LocalMedium

    anchor = AnchorLog(home, CULTURE, anchor_every=16)
    med = LocalMedium(home, anchor=anchor)
    sentinel = open(home / SENTINEL, "a", encoding="utf-8")

    i = 0
    while True:  # pragma: no cover - the parent kills us mid-loop
        i += 1
        # Interleave: several chatter, then one gold. The chatter is what MAY be lost; the gold is
        # what may not. A crash lands somewhere random in this pattern, which is the point.
        med.post(CULTURE, "r1/c/0", "chat", body={"i": i})
        med.post(CULTURE, "r1/c/0", "status", body={"i": i})
        posted = med.post(CULTURE, "conductor", "receipt", body={"i": i, "grade": "pass"},
                          idem=f"gold-{i}")
        # Record the gold seq only AFTER post() returned — which, for gold, is after the anchor
        # fsync. So every seq in this file is one the fabric CLAIMED was durable.
        sentinel.write(json.dumps({"seq": posted.seq, "idem": f"gold-{i}", "hash": posted.hash}) + "\n")
        sentinel.flush()
        os.fsync(sentinel.fileno())


if __name__ == "__main__":  # pragma: no cover - driven as a subprocess
    child(Path(sys.argv[1]))
