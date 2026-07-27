"""Second-machine frame replay: assemble a fixed spec in a FRESH interpreter and print the digest.

NUC-5 asks for "100 replays + second machine ⇒ identical frame digests". The 100 replays prove
in-process determinism; this proves it across a process boundary — a genuinely separate Python
invocation with its own hash seed, its own import order, its own memory — which is the honest
reading of "second machine" short of a second host. `assemble_frame` is a pure function, so if it
is truly deterministic the two digests are identical; if some hidden input (a clock, a set
iteration order, a float ULP) leaked in, they diverge here and nowhere else.

Run:  python -m bench.drills.frame_replay
"""
from __future__ import annotations

from hypercell.cell.frame import Candidate, Window, assemble_frame

#: A fixed, deliberately churn-prone spec: many items per section, entities that drive salience,
#: a mix of mandatory and scored. If ordering depended on anything non-deterministic, this spec
#: (with its salience ties and multiple sections) is where it would show.
SPEC: dict[str, list[Candidate]] = {
    "S0": [Candidate(ref="role.prompt", body="You are a careful refiner.", mandatory=True, id="0")],
    "S1": [Candidate(ref=f"tool:{t}", body=f"tool schema: {t}", mandatory=True, id=f"{i:03d}")
           for i, t in enumerate(["fs.read", "web.fetch", "web.search"])],
    "S2": [Candidate(ref=f"digest:{i}", body=f"installed digest {i} " * 8, seq=i, id=f"{i:06d}")
           for i in range(3)],
    "S3": [Candidate(ref=f"task:{i}", body=f"open task {i} about parser and lexer", seq=100 + i,
                     id=f"t{i}", entities=("parser", "lexer")) for i in range(4)],
    "S5": [Candidate(ref=f"io:{i}", body=f"recap record {i} " * 4, seq=200 + i, id=f"{i:04d}",
                     register="factual", recall_count=i) for i in range(6)],
    "S6": [Candidate(ref="percept", body="Investigate the parser crash on nested input.",
                     seq=1 << 30, id="percept", entities=("parser",))],
}

RATIOS = {"identity": .08, "tools": .08, "digest": .12, "working": .10,
          "retrieved": .14, "recap": .18, "percept": .22, "slack": .08}
SALIENCE = {"w_pin": 4.0, "w_factual": 2.0, "w_task": 1.5, "w_recency": 1.0, "w_ref": 0.5, "half_life": 512.0}


def digest() -> str:
    _, manifest = assemble_frame(
        ratios=RATIOS, salience_weights=SALIENCE, window=Window(context=16384, max_output=2048),
        candidates={k: list(v) for k, v in SPEC.items()}, ledger_head=250, tick=7,
        percept="Investigate the parser crash on nested input.", working_entities=("parser", "lexer"),
    )
    return manifest.digest


if __name__ == "__main__":  # pragma: no cover - driven as a subprocess
    print(digest())
