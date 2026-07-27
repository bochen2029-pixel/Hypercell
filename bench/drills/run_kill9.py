"""The RE-4 harness: a scripted run, killed at a random point, resumed, certified.

RE-4's bar is a comparison, not a survival check: the certificate produced after `kill -9` at ten
random points must be **field-identical** to an uninterrupted control at the same seeds. So the run
has to be deterministic given a seed — no wall-clock, no randomness the seed does not control — or
"identical" would be measuring the weather.

The child posts a scripted tournament into a real Medium (chain, anchors, gold durability all live),
stopping after `--upto` records so the parent can choose a kill point. `--upto 0` means "post the
whole run", which is the control. The parent then folds whatever landed, resumes, finishes the run,
and certifies — and the certificate must match the control's.

Run:  `python -m bench.drills.run_kill9 <home> <upto>`
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

CULTURE = "run-re4"
RUN_ID = "re4"
MANIFEST_SHA = "sha256:manifest-re4"

#: The scripted run. Deterministic by construction: every record and every score is fixed here, so
#: two executions differ only in where they were interrupted.
ARMS = ["a", "b", "c"]
ROUNDS = 4


def script() -> list[dict[str, Any]]:
    """The full sequence of posts, as (sender, type, body) triples in order."""
    out: list[dict[str, Any]] = [{
        "sender": "conductor", "type": "presence",
        "body": {
            "phase": "genesis", "run_id": RUN_ID, "manifest_sha256": MANIFEST_SHA,
            "topology": "tournament", "arms": ARMS,
            "convergence": {"target": 1.0, "stable_k": 2},
        },
    }]
    # Scores rise deterministically; arm 'b' wins and then holds, so stability accrues.
    scores = {"a": [0.4, 0.6, 0.6, 0.6], "b": [0.7, 1.0, 1.0, 1.0], "c": [0.2, 0.3, 0.3, 0.3]}
    for r in range(ROUNDS):
        out.append({"sender": "conductor", "type": "round_open", "body": {"round": r + 1}})
        for arm in ARMS:
            out.append({"sender": arm, "type": "submission", "body": {"cand": f"{arm}{r}", "round": r + 1}})
        for arm in ARMS:
            score = scores[arm][r]
            out.append({
                "sender": "conductor", "type": "receipt",
                "body": {
                    "arm": arm, "score": score,
                    "outcome": "passed" if score >= 1.0 else "gate",
                    # submission_seq is filled in at post time (it is a real seq), see `play`.
                    "_sub_for": f"{arm}{r}",
                    "cost": {"usd_effective": 0.01, "purpose": "production", "sku": "stub@stub/standard"},
                },
            })
    out.append({"sender": "conductor", "type": "verdict",
                "body": {"champion": "b", "score": 1.0, "evidence": []}})
    return out


def play(med: Any, upto: int = 0) -> int:
    """Post the script (or its first `upto` records). Returns how many were posted.

    Receipts carry the REAL seq of the submission they grade, resolved here — the fold's idempotence
    key is `(submission_seq, gen)`, so a fabricated seq would make the key meaningless.
    """
    sub_seqs: dict[str, int] = {}
    posted = 0
    for i, item in enumerate(script()):
        if upto and i >= upto:
            break
        body = dict(item["body"])
        if item["type"] == "submission":
            res = med.post(CULTURE, item["sender"], "submission", body=body,
                           idem=f"sub-{body['cand']}")
            sub_seqs[str(body["cand"])] = res.seq
            posted += 1
            continue
        if item["type"] == "receipt":
            cand = str(body.pop("_sub_for"))
            body["submission_seq"] = sub_seqs.get(cand, 0)
            med.post(CULTURE, item["sender"], "receipt", body=body, idem=f"rec-{cand}")
            posted += 1
            continue
        med.post(CULTURE, item["sender"], item["type"], body=body,
                 idem=f"{item['type']}-{i}")
        posted += 1
    return posted


def child(home: Path, upto: int) -> None:  # pragma: no cover - driven as a subprocess
    from hypercell.conductor.anchor import AnchorLog
    from hypercell.medium.transport_local import LocalMedium

    med = LocalMedium(home, anchor=AnchorLog(home, CULTURE, anchor_every=16))
    n = play(med, upto=upto)
    med.close()
    print(n)


if __name__ == "__main__":  # pragma: no cover - driven as a subprocess
    child(Path(sys.argv[1]), int(sys.argv[2]))
