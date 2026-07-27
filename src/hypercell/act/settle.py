"""The losable wager: battery, resolver registry, settlement daemon (contracts/act.md §4).

**The null is actor self-report** — the cell says whether its act worked. That is not a weak grading
signal, it is no signal: the one party with an interest in the answer is the only party asked. Every
run then reports success, and the record of a run that went badly looks exactly like the record of
one that went well.

A wager fixes that by being **losable**. An act at H1+ declares, before it runs, a check that an
independent resolver will run later and that *can come back FAILS*. Four rules make that real
(§4.1), and all four are enforced at the gate rather than at settlement — a wager you discover is
unlosable only after it has been won has already done its damage:

1. the kind is registered and its args are schema-valid;
2. **non-tautology** — the expected set may not cover the kind's codomain. A wager that cannot lose
   is not a wager, and `expect: [200..599]` is the shape that sneaks past a reviewer;
3. **independence** — the check reads world/Medium/artifact observables only, never the actor's own
   assertion (A5, one level up: no act grades itself);
4. **window** — journal-ts + expected latency < `resolve_by` ≤ `role.max_wager_horizon`.

Settlement is Conductor-side and cognition-free: on start it re-derives the unsettled set **from the
log** rather than from a queue it kept in memory, so a daemon that died mid-sweep resumes without
having lost anything. A cell never settles its own wager.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Literal

from ..common import clock

Outcome = Literal["HOLDS", "FAILS", "UNDECIDABLE"]
Settlement = Literal["ok", "miss", "expired", "unsettled"]

#: `role.max_wager_horizon` default (R29). A wager nobody can remember the reason for is not a check.
DEFAULT_MAX_HORIZON = timedelta(days=7)


class WagerRefused(Exception):
    """The losability battery refused. Carries the machine reason the receipt records."""

    def __init__(self, reason: str, detail: str) -> None:
        super().__init__(f"refused/{reason}: {detail}")
        self.reason = reason
        self.detail = detail


@dataclass(frozen=True)
class ResolverKind:
    """One row of the resolver registry (§4.2).

    `codomain` is what makes the non-tautology rule computable: without knowing the full set of
    answers the kind can give, "the expectation covers everything" is not a question you can ask.

    `late_check` declares whether a post-deadline answer still counts. Only `valid` for a **monotone**
    observable — an email delivered stays delivered — and the default is `expired`, because honesty
    is worth more here than generosity. A late check on a non-monotone observable would let a wager
    be won by a world that has since changed its mind.
    """

    kind: str
    codomain: frozenset[str]
    required_args: tuple[str, ...]
    late_check: Literal["valid", "expired"] = "expired"
    reads_actor_assertion: bool = False


#: The initial kinds (§4.2). `manual` is legal only where an operator is already in the loop (H2/H3).
RESOLVERS: dict[str, ResolverKind] = {
    "http_status": ResolverKind(
        "http_status", frozenset(str(c) for c in range(100, 600)), ("url", "expect")
    ),
    "content_digest": ResolverKind("content_digest", frozenset({"match", "differ"}), ("url", "sha256")),
    "dns_resolves": ResolverKind("dns_resolves", frozenset({"yes", "no"}), ("name",)),
    "file_exists": ResolverKind("file_exists", frozenset({"yes", "no"}), ("uri", "sha256")),
    "medium_query": ResolverKind("medium_query", frozenset({"yes", "no"}), ("filter", "count")),
    "oracle_cmd": ResolverKind("oracle_cmd", frozenset({"pass", "fail"}), ("checker",)),
    "manual": ResolverKind("manual", frozenset({"yes", "no"}), ("prompt",), late_check="valid"),
}


@dataclass(frozen=True)
class Expectation:
    """The wager itself. `on_miss` names a consequence, never an implicit rollback."""

    kind: str
    args: dict[str, Any]
    resolve_by: str
    on_miss: str = "flag"
    resolver: str = "conductor"

    @property
    def expects(self) -> frozenset[str]:
        raw = self.args.get("expect", self.args.get("expects", []))
        if isinstance(raw, (str, int)):
            raw = [raw]
        return frozenset(str(v) for v in (raw or []))


def check_losability(
    exp: Expectation,
    *,
    journal_ts: str,
    effect_latency_s: float = 0.0,
    max_horizon: timedelta = DEFAULT_MAX_HORIZON,
) -> None:
    """Gate step g. All four rules MUST hold; each failure names itself. (§4.1)"""
    spec = RESOLVERS.get(exp.kind)
    if spec is None:
        raise WagerRefused("wager_kind", f"'{exp.kind}' is not in the resolver registry")

    missing = [a for a in spec.required_args if a not in exp.args]
    if missing:
        raise WagerRefused("wager_args", f"{exp.kind} requires {missing}")

    if spec.reads_actor_assertion:
        raise WagerRefused(
            "wager_independence",
            f"'{exp.kind}' consults the actor's own assertion; a check the actor writes is not a check",
        )

    expected = exp.expects
    if expected and expected >= spec.codomain:
        raise WagerRefused(
            "wager_tautology",
            f"{exp.kind} expects all {len(spec.codomain)} of its possible answers; a wager that "
            "cannot lose is not a wager",
        )

    _check_window(exp, journal_ts=journal_ts, effect_latency_s=effect_latency_s, max_horizon=max_horizon)


def _check_window(
    exp: Expectation, *, journal_ts: str, effect_latency_s: float, max_horizon: timedelta
) -> None:
    journaled = _parse(journal_ts)
    deadline = _parse(exp.resolve_by)
    earliest = journaled + timedelta(seconds=effect_latency_s)
    if deadline <= earliest:
        raise WagerRefused(
            "wager_window",
            f"resolve_by {exp.resolve_by} is not after the effect can land ({earliest.isoformat()}); "
            "a check that runs before the effect could arrive always FAILS, which is not a wager either",
        )
    if deadline > journaled + max_horizon:
        raise WagerRefused(
            "wager_horizon",
            f"resolve_by {exp.resolve_by} exceeds max_wager_horizon ({max_horizon}) from the journal",
        )


def _parse(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def _due(resolve_by: str, now: str) -> bool:
    """Deadline comparison by PARSED time, never by string.

    The gate accepts both `...Z` and `...+00:00` spellings (fromisoformat does), so the fold must
    too: a lexicographic compare across the two formats mis-orders them, and a wager whose deadline
    never reads as due is a wager that silently always wins. Unparseable input counts as due, so it
    gets graded (and expires) LOUDLY instead of floating forever.
    """
    try:
        return _parse(resolve_by) <= _parse(now)
    except ValueError:
        return True


# ---------------------------------------------------------------------------- settlement (§4.3)


@dataclass
class Settler:
    """The settlement daemon. Conductor-side, cognition-free, fold-derived.

    `probes` maps a resolver kind to the function that runs it. Injected rather than imported so a
    drill can plant a will-hold, a will-miss and a resolver-down without a network — and so the
    daemon itself stays registry logic with no opinion about the world.
    """

    probes: dict[str, Callable[[Expectation], Outcome]] = field(default_factory=dict)
    #: How far behind the deadline a sweep may be and still count as on time.
    #:
    #: Without a grace window `late_check` would be dead law: `unsettled` only yields wagers whose
    #: `resolve_by` has already passed, so a strict `now > resolve_by` makes EVERY check late and
    #: every non-monotone wager `expired` -- including the ones that plainly held. Grace draws the
    #: line where the contract means it: a prompt sweep grades normally, a daemon that was down for
    #: hours does not get to grade a non-monotone observable that may have changed since.
    late_grace_s: float = 300.0

    def unsettled(self, records: list[dict[str, Any]], *, now: str | None = None) -> list[dict[str, Any]]:
        """Re-derive `{acts | exec ok ∧ expectation ∧ resolve_by ≤ now ∧ no settle receipt}` FROM THE LOG.

        From the log, not from a queue: a daemon that kept its worklist in memory loses it on
        restart, and the wagers it was holding would silently never be graded — which looks exactly
        like every wager winning.
        """
        stamp = now or clock.now_iso()
        settled = {
            str(r["body"].get("corr"))
            for r in records
            if _kind(r) == "act_receipt" and str(r.get("body", {}).get("phase")) == "settle"
        }
        out = []
        for rec in records:
            body = rec.get("body") or {}
            if _kind(rec) != "act_receipt" or body.get("exec") != "ok":
                continue
            exp = body.get("expectation")
            if not isinstance(exp, dict) or str(body.get("corr")) in settled:
                continue
            if _due(str(exp.get("resolve_by", "")), stamp):
                out.append(rec)
        return out

    def settle_one(self, rec: dict[str, Any], *, now: str | None = None) -> dict[str, Any]:
        """Grade one act. Returns the `act_receipt{phase: settle}` body.

        A resolver that is DOWN produces `UNDECIDABLE`, and an undecidable check past its deadline
        `expired`s rather than passing. The asymmetry is deliberate: a check nobody could run is not
        evidence that the thing worked.
        """
        body = rec["body"]
        exp = Expectation(**{k: v for k, v in body["expectation"].items() if k in Expectation.__annotations__})
        spec = RESOLVERS[exp.kind]
        stamp = now or clock.now_iso()

        probe = self.probes.get(exp.kind)
        outcome: Outcome = probe(exp) if probe else "UNDECIDABLE"

        try:
            late = _parse(stamp) > _parse(exp.resolve_by) + timedelta(seconds=self.late_grace_s)
        except ValueError:
            late = True  # an unparseable deadline cannot vouch for timeliness; expired beats guessed
        if outcome == "HOLDS":
            result: Settlement = "ok" if (not late or spec.late_check == "valid") else "expired"
        elif outcome == "FAILS":
            result = "miss"
        else:
            result = "expired"

        settled = {
            "verb": "act",
            "corr": body["corr"],
            "phase": "settle",
            "exec": body.get("exec", "ok"),
            "settlement": result,
            "graded_by": f"resolver:{exp.kind}",
            "resolved_at": stamp,
            "capability_ref": body.get("capability_ref", ""),
            # The actor rides along so `wager_ledger` can attribute per (claim, lane) from settle
            # receipts ALONE. Without this the fold keyed on "" for every production record -- a
            # rule reading a field nobody writes, which is the F26 shape one more time.
            "actor": body.get("actor", ""),
        }
        if result == "miss":
            # `on_miss` names a consequence; it never rolls anything back. Compensation is a NEW act
            # with its own gate and its own wager, because "undo" is a fiction at H1+ -- the world
            # does not have a previous version.
            settled["on_miss"] = exp.on_miss
            settled["on_miss_fired"] = True
        return settled

    def sweep(self, records: list[dict[str, Any]], *, now: str | None = None) -> list[dict[str, Any]]:
        return [self.settle_one(r, now=now) for r in self.unsettled(records, now=now)]


def wager_ledger(records: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, int]]:
    """A fold over settle receipts: `(claim, capability_ref) → {wagers, won, lost, expired}`.

    **Observability, never auto-kill** (v2 §13). A miss rate is a thing an operator should be shown,
    not a trigger that silently retires a cell: the fabric would then be grading cells on a signal
    they cannot appeal, using a resolver that might itself be broken.
    """
    out: dict[tuple[str, str], dict[str, int]] = {}
    for rec in records:
        body = rec.get("body") or {}
        if _kind(rec) != "act_receipt" or body.get("phase") != "settle":
            continue
        key = (str(rec.get("claim", body.get("actor", ""))), str(body.get("capability_ref", "")))
        tally = out.setdefault(key, {"wagers": 0, "won": 0, "lost": 0, "expired": 0})
        tally["wagers"] += 1
        tally[{"ok": "won", "miss": "lost", "expired": "expired"}[str(body["settlement"])]] += 1
    return out


def _kind(rec: dict[str, Any]) -> str:
    return str(rec.get("kind") or rec.get("type") or "")
