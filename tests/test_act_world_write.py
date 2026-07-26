"""ACT-1 — the world-write tier (CELL-4/NUC-6 · ACT-SETTLE-1 · DELIVER-1 · GX-1(b) · ACT-LEASE-1).

**CELL-4/NUC-6** — scoped exactly-once. Null: `(claim, step_id)` only. `{W0..W5,W3h} × {H0,H1} ×
{instance,lineage,slot}` × 100 + an 8-sibling fork race: zero double-fires on lineage/slot; every
in-doubt lands `unknown` → reconciles to ok/invalid/parked, never a blind re-exec; instance re-fires
per branch (positive control); the race gives 1 executor, 7 sharing via `duplicate_of`.

**ACT-SETTLE-1** — wagers grade. Null: actor self-report. Planted will-hold / will-miss /
resolver-down → ok / miss / expired; the ledger folds {1,1,1}; a miss fires `on_miss`; an executor
killed mid-flight reconciles to `ok` via probe with zero re-executions.

**DELIVER-1** — delivery-is-an-act. Null: direct file write. Crash at each window → zero
double-sends, manifest digest-verified, narration only from receipts.

**GX-1(b)** — the H1 warrant kit: idem + a losable default expectation + a non-mintable receipt.
`code.run@sandbox`'s class-3 leg is d′'s (seat 09's isolation + sealed `/out`); the profile is
declared and explicitly NOT admitted, and a drill below holds that gap open on purpose.

**ACT-LEASE-1** — re-run WIRED: the leases ECON-S2b proved in isolation, now on the H1 path.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from hypercell.act.adapters import deliver_outbox
from hypercell.act.executor import ActExecutor
from hypercell.act.profiles import ANNEX_A, NOT_YET_ADMITTED, ProfileRefusal
from hypercell.act.reconcile import ProbeInadmissible, check_probe_admissible, reconcile
from hypercell.act.settle import (
    RESOLVERS,
    Expectation,
    Settler,
    WagerRefused,
    check_losability,
    wager_ledger,
)
from hypercell.cell.nucleus import Nucleus
from hypercell.conductor.governor import Escrow
from hypercell.conductor.registry import EffectRegistry, effect_id, scope_key
from hypercell.medium.wire import NON_MINTABLE, AclDenied, check_acl

WINDOWS = ["W0", "W1", "W2", "W3", "W3h", "W4", "W5"]
SCOPES = ["instance", "lineage", "slot"]


def _by(hours: int = 1) -> str:
    return (datetime.now(UTC) + timedelta(hours=hours)).isoformat().replace("+00:00", "Z")


def _just_passed() -> str:
    """A deadline that has only just gone by — what a promptly-sweeping daemon actually sees."""
    return (datetime.now(UTC) - timedelta(seconds=1)).isoformat().replace("+00:00", "Z")


def _wager(**over: Any) -> dict[str, Any]:
    base = {
        "kind": "file_exists",
        "args": {"uri": "outbox://x", "sha256": "abc", "expect": ["yes"]},
        "resolve_by": _by(),
        "on_miss": "flag",
    }
    base.update(over)
    return base


DELIVERY = {"to": "ops@example.test", "subject": "the one message", "body": "sent once"}


@dataclass
class Rig:
    home: Path
    registry: EffectRegistry
    outbox: Path

    def cell(self, claim: str, *, escrow: Escrow | None = None) -> ActExecutor:
        nucleus = Nucleus(self.home, claim)
        return ActExecutor(
            nucleus=nucleus, home=self.home, registry=self.registry,
            role_harm_ceiling="H1", escrow=escrow,
        )

    @property
    def deliveries(self) -> list[dict[str, Any]]:
        return deliver_outbox.sent(self.outbox)


@pytest.fixture
def rig(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Rig:
    outbox = tmp_path / "outbox"
    monkeypatch.setenv(deliver_outbox.OUTBOX_ENV, str(outbox))
    return Rig(home=tmp_path, registry=EffectRegistry(tmp_path), outbox=outbox)


# ================================================================ CELL-4/NUC-6: the null, measured


def test_the_null_key_double_fires_once_per_fork_sibling(rig: Rig) -> None:
    """`(claim_id, step_id)` is exactly-once about the WRONG NOUN.

    Eight siblings forked from one parent each compute a different `claim_id`, so the null key is
    distinct eight times and the message goes out eight times. Nothing is broken in the null's own
    terms — that is what makes it dangerous.
    """
    null_keys = {f"instance:r1/agent/{i}:step-1" for i in range(8)}
    assert len(null_keys) == 8, "the null would fire once per sibling"

    root = rig.registry.root_of("r1/agent/0")
    eid = effect_id("deliver.outbox", "1", ANNEX_A["deliver.outbox"].significant(DELIVERY))
    lineage_keys = {scope_key("lineage", lineage_root=root, eid=eid) for _ in range(8)}
    assert len(lineage_keys) == 1, "the lineage key must collapse the fork tree to one"


# ================================================================ CELL-4/NUC-6: the fork race


def test_eight_siblings_race_one_executes_seven_share(rig: Rig) -> None:
    """The bar: 1 executes, 7 share via `duplicate_of`, and all 8 hold the same evidence ref.

    Dedup-and-SHARE, not dedup-and-fail. A sibling that merely failed would have to re-do the work
    or invent a result; a sibling handed the winner's corr can cite the same evidence honestly.
    """
    siblings = []
    for i in range(8):
        rig.registry.note_lineage(f"r1/agent/{i}", parent_id="r1/agent/root" if i else None)
    rig.registry.note_lineage("r1/agent/root")
    for i in range(8):
        rig.registry.note_lineage(f"r1/agent/{i}", parent_id="r1/agent/root")
        siblings.append(rig.cell(f"r1/agent/{i}"))

    receipts = [s.act("deliver.outbox", DELIVERY, harm_declared="H1", expectation=_wager())
                for s in siblings]

    executed = [r for r in receipts if r.exec == "ok"]
    shared = [r for r in receipts if r.reason == "duplicate_effect"]
    assert len(executed) == 1, f"{len(executed)} siblings executed; the world got {len(executed)} messages"
    assert len(shared) == 7, f"{len(shared)} siblings shared; the other {7 - len(shared)} did what?"
    assert len(rig.deliveries) == 1, "more than one message reached the outbox"

    winner = executed[0].corr
    assert {r.duplicate_of for r in shared} == {winner}, "the losers do not agree on who won"
    assert {r.effect_key for r in receipts} == {executed[0].effect_key}, "siblings computed different keys"


def test_every_sibling_can_cite_the_same_evidence(rig: Rig) -> None:
    """8 nuclei, one evidence ref. Sharing is only real if the loser can point at the artifact."""
    for i in range(8):
        rig.registry.note_lineage(f"r1/agent/{i}", parent_id="r1/agent/root")
    cells = [rig.cell(f"r1/agent/{i}") for i in range(8)]
    receipts = [c.act("deliver.outbox", DELIVERY, harm_declared="H1", expectation=_wager()) for c in cells]

    winner = next(r for r in receipts if r.exec == "ok")
    for r in receipts:
        ref = r.corr if r.exec == "ok" else r.duplicate_of
        assert ref == winner.corr, "a sibling cannot reach the winning receipt"


# ================================================================ CELL-4/NUC-6: the scope matrix


@pytest.mark.parametrize("scope", SCOPES)
def test_the_scope_decides_whether_a_fork_re_fires(rig: Rig, scope: str) -> None:
    """`instance` re-fires per branch (the positive control); `lineage`/`slot` do not."""
    eid = effect_id("deliver.outbox", "1", DELIVERY)
    keys = {
        scope_key(scope, claim_id=f"r1/agent/{i}", step_id="step-1",
                  lineage_root="r1/agent/root", eid=eid, routine_id="nightly", slot="2026-07-26")
        for i in range(8)
    }
    if scope == "instance":
        assert len(keys) == 8, "instance must re-fire per branch, or a fork strands its checkpoints"
    else:
        assert len(keys) == 1, f"{scope} let a fork produce {len(keys)} distinct keys"


def test_a_hundred_racing_reservations_yield_exactly_one_winner(rig: Rig) -> None:
    """100 attempts per scope, the count the bar asks for, measured on the registry itself."""
    for scope in ("lineage", "slot"):
        key = scope_key(scope, lineage_root="root", eid="e", routine_id="nightly", slot="s")
        wins = sum(rig.registry.reserve(key, f"act_{i}").won for i in range(100))
        assert wins == 1, f"{scope}: {wins} winners out of 100 attempts"

    instance_wins = sum(
        rig.registry.reserve(scope_key("instance", claim_id=f"c{i}", step_id="s"), f"act_{i}").won
        for i in range(100)
    )
    assert instance_wins == 100, "instance is per-branch; suppressing it would strand the fork"


def test_a_volatile_arg_can_neither_break_dedup_nor_evade_it() -> None:
    """Both directions bite, which is why the marking is per-field rather than a blanket rule."""
    profile = ANNEX_A["deliver.outbox"]
    a = dict(DELIVERY, request_id="req-1")
    b = dict(DELIVERY, request_id="req-2")
    assert effect_id("deliver.outbox", "1", profile.significant(a)) == effect_id(
        "deliver.outbox", "1", profile.significant(b)
    ), "a volatile arg broke dedup: two attempts at one send would both go out"

    c = dict(DELIVERY, body="a different message")
    assert effect_id("deliver.outbox", "1", profile.significant(a)) != effect_id(
        "deliver.outbox", "1", profile.significant(c)
    ), "a significant arg was ignored: dedup would suppress a genuinely different send"


def test_a_tool_version_bump_reopens_the_key() -> None:
    """A tool that changed what it DOES must not inherit the 'already done' of its predecessor."""
    assert effect_id("deliver.outbox", "1", DELIVERY) != effect_id("deliver.outbox", "2", DELIVERY)


# ================================================================ CELL-4/NUC-6: the crash windows


@pytest.mark.parametrize("window", WINDOWS)
def test_no_crash_window_produces_a_double_send(rig: Rig, window: str) -> None:
    """{W0..W5, W3h} — the resume behaviour per §7.4. The outbox is the ground truth."""
    cell = rig.cell("r1/agent/0")
    key = cell.effect_key_for("deliver.outbox", DELIVERY, step_id="step-1")
    # A resume re-attempts the SAME semantic act, so it carries the corr from its own journal --
    # that is what distinguishes "me, again" from "a sibling racing me" at the registry.
    corr = "act_crashed"

    if window == "W0":
        pass  # nothing on disk; the resumed actor simply re-attempts
    elif window == "W1":
        pass  # escrow only; the registry is untouched, so resume is a clean attempt
    elif window in ("W2", "W3", "W3h"):
        # Reserved (and for W3/W3h journaled) by an actor that then died before touching the world.
        rig.registry.reserve(key, corr)
    elif window in ("W4", "W5"):
        # The effect LANDED. This is the irreducible window: you cannot fsync a receipt before the
        # world answers, which is exactly why probes are mandatory at H1+.
        rig.registry.reserve(key, corr)
        deliver_outbox.execute(dict(DELIVERY, effect_key=key))
        rig.registry.transition(key, "executed")
        cell.nucleus.append(
            "act_receipt",
            {"verb": "act", "corr": corr, "capability_ref": "deliver.outbox", "exec": "ok",
             "effect_key": key, "phase": "exec"},
            idem=corr, durability="gold",
        )

    resumed = cell.act("deliver.outbox", DELIVERY, harm_declared="H1",
                       idem=corr, expectation=_wager())

    assert len(rig.deliveries) == 1, (
        f"{window}: {len(rig.deliveries)} messages reached the world -- a double-send, or a "
        f"delivery LOST to a reservation nobody could reclaim. Neither is safer than the other."
    )
    if window in ("W4", "W5"):
        assert resumed.exec == "ok", f"{window}: the replay did not return the original receipt"
        assert resumed.corr == corr


def test_w2_orphan_rebinds_rather_than_stranding_the_delivery(rig: Rig) -> None:
    """W2's other leg: a reservation held by an actor that died before journaling.

    Refusing forever would turn a double-send bug into a lost-message bug, which is a different
    failure, not a safer one. Re-bind is allowed only for a `reserved` row past its TTL — never for
    one that reached `executed`, where the world already moved.
    """
    key = "lineage:root:sha256:deadbeef"
    rig.registry.reserve(key, "act_dead")
    assert not rig.registry.reserve(key, "act_live").won, "re-bound instantly; the holder may still be alive"

    rebound = rig.registry.reserve(key, "act_live", rebind_after_s=-1.0)
    assert rebound.won, "a long-dead reservation stranded the delivery forever"
    assert rig.registry.get(key)["act_id"] == "act_live"

    rig.registry.transition(key, "executed")
    assert not rig.registry.reserve(key, "act_third", rebind_after_s=-1.0).won, (
        "an EXECUTED effect was re-bound; the world already moved and this is a double-send"
    )


def test_the_sweep_never_expires_an_executed_effect(rig: Rig) -> None:
    reserved, executed = "lineage:root:a", "lineage:root:b"
    rig.registry.reserve(reserved, "act_1")
    rig.registry.reserve(executed, "act_2")
    rig.registry.transition(executed, "executed")

    swept = rig.registry.sweep(older_than_s=-1.0)
    assert swept == [reserved]
    assert rig.registry.get(executed) is not None, "forgetting an executed effect is how you send twice"


# ================================================================ CELL-4/NUC-6: never blind-retry


def test_an_in_doubt_act_is_never_blindly_re_executed(rig: Rig) -> None:
    """The whole §8 point: `unknown` authorizes nothing. Only a PROVABLY absent effect may retry."""
    outcomes = {}
    for answer in ("found", "absent", "undeterminable"):
        result = reconcile(
            {"corr": "act_1", "capability_ref": "deliver.outbox"},
            probe=lambda _pend, a=answer: (a, {"probed": a}),
        )
        outcomes[answer] = result

    assert outcomes["found"].disposition == "ok"
    assert outcomes["found"].graded_by == "resolver:reconcile"
    assert not outcomes["found"].may_retry

    assert outcomes["absent"].disposition == "invalid"
    assert outcomes["absent"].may_retry
    assert outcomes["absent"].retry_idem == "act_1", "a retry must reuse the idem, or dedup is defeated"

    assert outcomes["undeterminable"].disposition == "parked"
    assert not outcomes["undeterminable"].may_retry, "an unknown effect was cleared for re-execution"


def test_provider_idem_is_the_one_safe_re_send(rig: Rig) -> None:
    """Where the provider dedups on our key, a re-send ANSWERS the question instead of gambling."""
    from dataclasses import replace

    profile = replace(ANNEX_A["deliver.outbox"], retry_safe="provider_idem")
    result = reconcile(
        {"corr": "act_1", "capability_ref": "deliver.outbox"},
        probe=lambda _p: ("undeterminable", {}),
        profile=profile,
    )
    assert result.disposition == "unknown" and result.retry_idem == "act_1"


def test_step_zero_stops_a_held_act_from_being_probed_or_parked(rig: Rig) -> None:
    """A waiting act is not a crashed one. Probing it treats a pending decision as a failure."""
    held = {"body": {"corr": "act_1", "phase": "hold", "hold": {"until": _by()}}}
    probed = []
    result = reconcile(
        {"corr": "act_1", "capability_ref": "deliver.outbox"},
        hold_receipt=held,
        probe=lambda p: (probed.append(p), ("found", {}))[1],
    )
    assert result.disposition == "held" and probed == [], "step 0 ran the probe anyway"

    escalated = {"body": {"corr": "act_1", "phase": "hold", "hold": {"escalated": "H3"}}}
    assert reconcile(
        {"corr": "act_1", "capability_ref": "deliver.outbox"},
        hold_receipt=escalated, probe=lambda _p: ("found", {}),
    ).disposition == "ok", "an escalated hold is no longer live and must not block reconciliation"


def test_pending_is_plural_so_a_multi_flight_crash_strands_nobody(rig: Rig) -> None:
    """NUC-6's nucleus half. The live v1 single-dict return is a single-flight assumption."""
    cell = rig.cell("r1/agent/0")
    for i in range(3):
        cell.nucleus.append("action", {"verb": "act", "corr": f"act_{i}",
                                       "capability_ref": "deliver.outbox"}, idem=f"act_{i}",
                            durability="gold")

    pend = cell.nucleus.pending()
    assert len(pend) == 3, f"{len(pend)} of 3 in-flight acts surfaced; the rest are stranded"

    results = cell.reconcile_pending(probe=lambda _p: ("absent", {}))
    assert len(results) == 3 and all(r.disposition == "invalid" for r in results)


# ================================================================ probe admission (structural)


def test_an_h1_profile_without_an_admissible_probe_is_inadmissible() -> None:
    """If you cannot find out whether it happened, you do not get to do it."""
    from dataclasses import replace

    no_probe = replace(ANNEX_A["deliver.outbox"], reconcile_probe="")
    with pytest.raises(ProbeInadmissible, match="no reconcile probe"):
        check_probe_admissible(no_probe, role_egress=["*"])


def test_a_mutating_probe_is_refused_because_it_recurses_the_problem() -> None:
    from dataclasses import replace

    mutating = replace(ANNEX_A["deliver.outbox"], reconcile_probe="deliver.outbox")
    with pytest.raises(ProbeInadmissible, match="recurses"):
        check_probe_admissible(mutating, role_egress=["*"])


def test_an_h0_profile_needs_no_probe() -> None:
    """Read-only turtles all the way down: the bottom turtle does not need one."""
    check_probe_admissible(ANNEX_A["fs.read"], role_egress=[])


def test_the_undelivered_sandbox_leg_is_declared_and_refused_rather_than_silent(rig: Rig) -> None:
    """GX-1(b)'s remaining leg is d′'s. An undeclared gap is one nobody trips over until it matters."""
    assert "code.run@sandbox" in ANNEX_A and "code.run@sandbox" in NOT_YET_ADMITTED
    cell = rig.cell("r1/agent/0")
    with pytest.raises(ProfileRefusal, match="not_admitted"):
        cell.admit("code.run@sandbox")


# ================================================================ ACT-SETTLE-1: the losable wager


def test_the_null_is_actor_self_report_and_it_always_wins() -> None:
    """Under the null the actor grades itself, so every act succeeds and the record is worthless."""
    self_reported = [{"corr": f"act_{i}", "exec": "ok", "note": "worked"} for i in range(100)]
    assert all(r["exec"] == "ok" for r in self_reported)
    assert not any("graded_by" in r for r in self_reported), (
        "the null produces 100 successes and zero independent gradings"
    )


def test_a_wager_that_cannot_lose_is_refused_at_the_gate() -> None:
    """Non-tautology (rule 2). `expect: [100..599]` is the shape that sneaks past a reviewer."""
    everything = Expectation(
        kind="http_status",
        args={"url": "https://x.test", "expect": [str(c) for c in range(100, 600)]},
        resolve_by=_by(),
    )
    with pytest.raises(WagerRefused, match="wager_tautology"):
        check_losability(everything, journal_ts=datetime.now(UTC).isoformat())


def test_the_four_battery_rules_each_refuse_on_their_own() -> None:
    now = datetime.now(UTC)
    stamp = now.isoformat()

    with pytest.raises(WagerRefused, match="wager_kind"):
        check_losability(Expectation("astrology", {}, _by()), journal_ts=stamp)

    with pytest.raises(WagerRefused, match="wager_args"):
        check_losability(Expectation("http_status", {"url": "x"}, _by()), journal_ts=stamp)

    # Window: a deadline before the effect can even land always FAILS -- not a wager either.
    with pytest.raises(WagerRefused, match="wager_window"):
        check_losability(
            Expectation("http_status", {"url": "x", "expect": ["200"]},
                        (now + timedelta(seconds=1)).isoformat()),
            journal_ts=stamp, effect_latency_s=60.0,
        )

    with pytest.raises(WagerRefused, match="wager_horizon"):
        check_losability(
            Expectation("http_status", {"url": "x", "expect": ["200"]}, _by(hours=24 * 30)),
            journal_ts=stamp,
        )


def test_a_check_that_reads_the_actors_own_assertion_is_refused() -> None:
    """Independence (rule 3) — A5 one level up: no act grades itself."""
    from dataclasses import replace

    RESOLVERS["self_report"] = replace(RESOLVERS["oracle_cmd"], kind="self_report",
                                       reads_actor_assertion=True)
    try:
        with pytest.raises(WagerRefused, match="wager_independence"):
            check_losability(
                Expectation("self_report", {"checker": "me"}, _by()),
                journal_ts=datetime.now(UTC).isoformat(),
            )
    finally:
        del RESOLVERS["self_report"]


def test_a_world_write_with_no_wager_at_all_is_refused(rig: Rig) -> None:
    cell = rig.cell("r1/agent/0")
    receipt = cell.act("deliver.outbox", DELIVERY, harm_declared="H1")
    assert receipt.exec == "refused" and receipt.reason == "wager_required"
    assert rig.deliveries == [], "an ungraded world-write reached the world"


def test_planted_wagers_settle_ok_miss_expired_and_the_ledger_folds_1_1_1() -> None:
    """The bar's exact shape: three planted outcomes, three settlements, a {1,1,1} fold."""
    planted = {"will_hold": "HOLDS", "will_miss": "FAILS", "resolver_down": "UNDECIDABLE"}
    records = [
        {
            "kind": "act_receipt", "seq": i, "claim": "r1/agent/0",
            "body": {
                "corr": f"act_{name}", "exec": "ok", "capability_ref": "deliver.outbox",
                "expectation": {"kind": "oracle_cmd", "args": {"checker": name}, "resolve_by": _just_passed(),
                                "on_miss": "flag"},
            },
        }
        for i, name in enumerate(planted, start=1)
    ]
    settler = Settler(probes={"oracle_cmd": lambda exp: planted[str(exp.args["checker"])]})  # type: ignore[return-value]

    settled = settler.sweep(records)
    assert [s["settlement"] for s in settled] == ["ok", "miss", "expired"]
    assert all(s["graded_by"] == "resolver:oracle_cmd" for s in settled)

    miss = next(s for s in settled if s["settlement"] == "miss")
    assert miss["on_miss_fired"] and miss["on_miss"] == "flag", "a lost wager fired no consequence"

    ledger = wager_ledger([{"kind": "act_receipt", "claim": "r1/agent/0", "body": s} for s in settled])
    assert ledger[("r1/agent/0", "deliver.outbox")] == {"wagers": 3, "won": 1, "lost": 1, "expired": 1}


def test_a_resolver_that_is_down_expires_rather_than_passes() -> None:
    """A check nobody could run is not evidence that the thing worked."""
    rec = {
        "kind": "act_receipt", "seq": 1,
        "body": {"corr": "act_1", "exec": "ok", "capability_ref": "deliver.outbox",
                 "expectation": {"kind": "http_status",
                                 "args": {"url": "https://down.test", "expect": ["200"]},
                                 "resolve_by": _just_passed()}},
    }
    assert Settler(probes={}).settle_one(rec)["settlement"] == "expired"


def test_settlement_is_re_derived_from_the_log_not_from_a_queue() -> None:
    """A daemon that kept its worklist in memory loses it on restart — and silently.

    The wagers it was holding then never grade, which looks exactly like every wager winning.
    """
    base = {"corr": "act_1", "exec": "ok", "capability_ref": "deliver.outbox",
            "expectation": {"kind": "oracle_cmd", "args": {"checker": "c"},
                            "resolve_by": _just_passed()}}
    records: list[dict[str, Any]] = [{"kind": "act_receipt", "seq": 1, "body": base}]

    settler = Settler(probes={"oracle_cmd": lambda _e: "HOLDS"})  # type: ignore[return-value]
    assert len(settler.unsettled(records)) == 1, "a fresh daemon did not re-derive the open wager"

    records.append({"kind": "act_receipt", "seq": 2,
                    "body": {"corr": "act_1", "phase": "settle", "settlement": "ok",
                             "capability_ref": "deliver.outbox"}})
    assert settler.unsettled(records) == [], "an already-settled wager would be graded twice"


def test_a_wager_whose_deadline_has_not_arrived_is_left_alone() -> None:
    rec = {"kind": "act_receipt", "seq": 1,
           "body": {"corr": "act_1", "exec": "ok", "capability_ref": "deliver.outbox",
                    "expectation": {"kind": "oracle_cmd", "args": {"checker": "c"},
                                    "resolve_by": _by(hours=6)}}}
    assert Settler(probes={"oracle_cmd": lambda _e: "FAILS"}).unsettled([rec]) == []  # type: ignore[return-value]


def test_an_executor_killed_mid_flight_reconciles_via_probe_with_zero_re_executions(rig: Rig) -> None:
    """The bar's 4th act: killed mid-flight, reconciliation lands `ok`, the world is touched once."""
    cell = rig.cell("r1/agent/0")
    key = cell.effect_key_for("deliver.outbox", DELIVERY, step_id="step-1")

    # The effect landed and the process died before the receipt (W4, irreducible).
    rig.registry.reserve(key, "act_killed")
    deliver_outbox.execute(dict(DELIVERY, effect_key=key))
    rig.registry.transition(key, "executed")
    cell.nucleus.append("action", {"verb": "act", "corr": "act_killed", "effect_key": key,
                                   "capability_ref": "deliver.outbox"},
                        idem="act_killed", durability="gold")

    def probe(pend: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        """A real H0 read of the outbox — the profile's declared reconcile probe."""
        entries = deliver_outbox.read_manifest(rig.outbox)["entries"]
        found = str(pend["effect_key"]) in entries
        return ("found" if found else "absent", {"manifest_entries": len(entries)})

    results = cell.reconcile_pending(probe=probe)  # type: ignore[arg-type]
    assert len(results) == 1
    assert results[0].disposition == "ok" and results[0].graded_by == "resolver:reconcile"
    assert len(rig.deliveries) == 1, "reconciliation re-executed the act"


# ================================================================ DELIVER-1


def test_the_null_direct_file_write_double_sends_on_a_crash(rig: Rig) -> None:
    """Null: write the file, then record it. Crash between the two and you cannot tell."""
    naive = rig.outbox / "naive"
    naive.mkdir(parents=True)
    for attempt in range(2):  # the crash: the "record it" step never ran, so the retry re-writes
        (naive / f"msg-{attempt}.json").write_text(json.dumps(DELIVERY), encoding="utf-8")
    assert len(list(naive.glob("msg-*.json"))) == 2, "the null sent it twice and nothing noticed"


def test_the_outbox_refuses_the_second_send_at_the_filesystem(rig: Rig) -> None:
    """`os.link` is atomic and fails if the name is taken. That failure is the feature.

    The reservation lives in the Conductor's database and the delivery lives on a filesystem: a
    guarantee spanning two stores must be held on both sides or it is held on neither.
    """
    key = "lineage:root:sha256:abc"
    deliver_outbox.execute(dict(DELIVERY, effect_key=key))
    with pytest.raises(deliver_outbox.DoubleSend):
        deliver_outbox.execute(dict(DELIVERY, effect_key=key))
    assert len(rig.deliveries) == 1


@pytest.mark.parametrize("window", WINDOWS)
def test_no_delivery_window_produces_a_double_send_and_the_manifest_verifies(
    rig: Rig, window: str
) -> None:
    key = f"lineage:root:{window}"
    if window in ("W4", "W5"):
        deliver_outbox.execute(dict(DELIVERY, effect_key=key))
    try:
        deliver_outbox.execute(dict(DELIVERY, effect_key=key))
    except deliver_outbox.DoubleSend:
        pass
    assert len(rig.deliveries) == 1, f"{window}: {len(rig.deliveries)} deliveries"
    ok, why = deliver_outbox.verify_outbox(rig.outbox)
    assert ok, f"{window}: {why}"


def test_a_tampered_outbox_entry_is_caught_by_the_manifest(rig: Rig) -> None:
    deliver_outbox.execute(dict(DELIVERY, effect_key="lineage:root:a"))
    entry = rig.outbox / deliver_outbox.sent(rig.outbox)[0]["entry"]
    entry.write_text('{"to":"attacker@example.test"}', encoding="utf-8")

    ok, why = deliver_outbox.verify_outbox(rig.outbox)
    assert not ok and "does not match its manifest digest" in why


def test_a_manifest_entry_deleted_from_disk_is_caught(rig: Rig) -> None:
    deliver_outbox.execute(dict(DELIVERY, effect_key="lineage:root:a"))
    (rig.outbox / deliver_outbox.sent(rig.outbox)[0]["entry"]).unlink()
    ok, why = deliver_outbox.verify_outbox(rig.outbox)
    assert not ok and "missing" in why


def test_the_manifest_digest_is_order_independent(rig: Rig) -> None:
    """Two identical outboxes must agree, whatever order they were filled in."""
    for k in ("b", "a", "c"):
        deliver_outbox.execute(dict(DELIVERY, subject=k, effect_key=f"lineage:root:{k}"))
    first = deliver_outbox.read_manifest(rig.outbox)["digest"]

    entries = deliver_outbox.read_manifest(rig.outbox)["entries"]
    reversed_order = dict(reversed(list(entries.items())))
    assert deliver_outbox.manifest_digest(reversed_order) == first


def test_narration_comes_from_the_manifest_never_from_the_journal(rig: Rig) -> None:
    """An intention that crashed before the link landed is not a delivery.

    Narrating from intentions is how a fabric tells a user it sent something it did not.
    """
    cell = rig.cell("r1/agent/0")
    cell.nucleus.append("action", {"verb": "act", "corr": "act_ghost",
                                   "capability_ref": "deliver.outbox"},
                        idem="act_ghost", durability="gold")

    assert cell.nucleus.pending(), "the journal holds an intention"
    assert deliver_outbox.sent(rig.outbox) == [], "narration reported a send that never left"


# ================================================================ GX-1(b) + ACT-LEASE-1


def test_the_h1_warrant_kit_is_complete_on_a_real_act(rig: Rig) -> None:
    """idem + a losable expectation + a non-mintable receipt, end to end."""
    cell = rig.cell("r1/agent/0")
    receipt = cell.act("deliver.outbox", DELIVERY, harm_declared="H1",
                       idem="act_fixed", expectation=_wager())

    assert receipt.exec == "ok"
    assert receipt.corr == "act_fixed", "the idem must be the act's identity, not a fresh id"
    assert receipt.expectation and receipt.expectation["kind"] == "file_exists"
    assert receipt.effect_key.startswith("lineage:"), "an H1 world-write took a per-instance key"

    # Non-mintable: the acting cell may not post its own act_receipt (SEC-b′ made this mechanical).
    assert "act_receipt" in NON_MINTABLE
    with pytest.raises(AclDenied):
        check_acl("act_receipt", "r1/agent/0")


def test_a_replayed_idem_returns_the_original_receipt_not_a_second_effect(rig: Rig) -> None:
    """Asking twice for the same act must give the same ANSWER, not an error and not a second send.

    A refusal would be safe for the world and wrong for the caller: a retry loop that gets
    `refused` cannot tell "already done" from "not allowed", so it either gives up on work that
    succeeded or escalates something that needs no attention.
    """
    cell = rig.cell("r1/agent/0")
    first = cell.act("deliver.outbox", DELIVERY, harm_declared="H1", idem="act_x", expectation=_wager())
    second = cell.act("deliver.outbox", DELIVERY, harm_declared="H1", idem="act_x", expectation=_wager())

    assert first.exec == "ok" and second.exec == "ok"
    assert second.corr == first.corr and second.sha256 == first.sha256
    assert len(rig.deliveries) == 1, "the replay sent a second message"


def test_a_sibling_is_refused_where_a_replay_is_served(rig: Rig) -> None:
    """The two cases must stay distinguishable: same act = replay, different act = duplicate."""
    for i in range(2):
        rig.registry.note_lineage(f"r1/agent/{i}", parent_id="r1/agent/root")
    first = rig.cell("r1/agent/0").act(
        "deliver.outbox", DELIVERY, harm_declared="H1", idem="act_mine", expectation=_wager()
    )
    sibling = rig.cell("r1/agent/1").act(
        "deliver.outbox", DELIVERY, harm_declared="H1", idem="act_theirs", expectation=_wager()
    )
    assert first.exec == "ok"
    assert sibling.exec == "refused" and sibling.duplicate_of == "act_mine"


def test_leases_are_live_on_the_h1_path_not_only_in_the_escrow_unit(rig: Rig) -> None:
    """ACT-LEASE-1, re-run WIRED. ECON-S2b proved the escrow; this proves the act plane uses it."""
    escrow = Escrow(cap_usd=10.0)
    cell = rig.cell("r1/agent/0", escrow=escrow)
    receipt = cell.act("deliver.outbox", DELIVERY, harm_declared="H1", expectation=_wager())

    assert receipt.exec == "ok"
    if escrow.leaseable("deliver.outbox", harm="H1"):
        assert receipt.cost.get("resv_id"), "the H1 act ran without booking its lease"
    assert escrow.still_held() == [], "a completed act left its lease held"


def test_a_losing_sibling_releases_its_lease(rig: Rig) -> None:
    """Otherwise seven refused siblings each strand a reservation the sweeper has to find."""
    escrow = Escrow(cap_usd=10.0)
    for i in range(2):
        rig.registry.note_lineage(f"r1/agent/{i}", parent_id="r1/agent/root")
    winner = rig.cell("r1/agent/0", escrow=escrow)
    loser = rig.cell("r1/agent/1", escrow=escrow)

    assert winner.act("deliver.outbox", DELIVERY, harm_declared="H1", expectation=_wager()).exec == "ok"
    refused = loser.act("deliver.outbox", DELIVERY, harm_declared="H1", expectation=_wager())

    assert refused.reason == "duplicate_effect"
    assert escrow.still_held() == [], "the losing sibling kept its lease"


# ================================================================ the registry is a serving copy


def test_the_registry_rebuilds_from_the_log(rig: Rig) -> None:
    """A13. A registry that could not be regenerated is a second source of truth about who did what."""
    cell = rig.cell("r1/agent/0")
    receipt = cell.act("deliver.outbox", DELIVERY, harm_declared="H1", expectation=_wager())
    key = receipt.effect_key

    records = list(cell.nucleus.ledger.records())
    before = rig.registry.get(key)
    rig.registry.rebuild_from(records)
    after = rig.registry.get(key)

    assert before and after and after["key"] == before["key"]
    assert after["state"] == "executed", "the rebuild forgot that the world had already moved"


def test_a_receipt_names_its_own_effect_key(rig: Rig) -> None:
    """The registry's join column. Without it a rebuild cannot tell which reservation a receipt closed."""
    cell = rig.cell("r1/agent/0")
    receipt = cell.act("deliver.outbox", DELIVERY, harm_declared="H1", expectation=_wager())
    body = cell.nucleus.records_of_kind("act_receipt")[-1]["body"]
    assert body["effect_key"] == receipt.effect_key != ""


# ================================================================ the kill-9 harness (a REAL kill)


@pytest.mark.slow
def test_a_really_killed_executor_reconciles_to_ok_with_zero_re_executions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every other window drill MODELS the crash. This one kills a real process in W4.

    No cleanup, no handlers, no flush — what survives is what was durable. W4 is irreducible (you
    cannot fsync a receipt before the world answers), so the probe is the only way back, which is
    why act.md §8 makes probes mandatory at H1+.
    """
    import subprocess
    import sys

    from bench.drills.act_kill9 import CORR, SENTINEL

    monkeypatch.setenv(deliver_outbox.OUTBOX_ENV, str(tmp_path / "outbox"))
    proc = subprocess.Popen(
        [sys.executable, "-m", "bench.drills.act_kill9", str(tmp_path)],
        cwd=Path(__file__).resolve().parent.parent,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    try:
        deadline = time.time() + 60
        while not (tmp_path / SENTINEL).exists():
            if proc.poll() is not None:
                out, err = proc.communicate()
                pytest.fail(f"the child died before delivering:\n{err.decode(errors='replace')[-2000:]}")
            if time.time() > deadline:
                pytest.fail("the child never reached the delivery")
            time.sleep(0.05)
        proc.kill()  # SIGKILL / TerminateProcess: no handlers run, nothing is flushed
    finally:
        proc.wait(timeout=30)

    # ---- resume, in this process, from what the dead one left on disk.
    registry = EffectRegistry(tmp_path)
    cell = ActExecutor(
        nucleus=Nucleus(tmp_path, "r1/agent/0"), home=tmp_path,
        registry=registry, role_harm_ceiling="H1",
    )
    outbox = tmp_path / "outbox"
    assert len(deliver_outbox.sent(outbox)) == 1, "the child did not actually deliver"

    pend = cell.nucleus.pending()
    assert [p["corr"] for p in pend] == [CORR], "the in-doubt act did not survive the kill"

    def probe(p: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        entries = deliver_outbox.read_manifest(outbox)["entries"]
        return ("found" if str(p["effect_key"]) in entries else "absent", {"entries": len(entries)})

    results = cell.reconcile_pending(probe=probe)  # type: ignore[arg-type]
    assert [r.disposition for r in results] == ["ok"]
    assert results[0].graded_by == "resolver:reconcile"
    assert len(deliver_outbox.sent(outbox)) == 1, "recovery re-executed the act"

    ok, why = deliver_outbox.verify_outbox(outbox)
    assert ok, f"the outbox did not survive the kill intact: {why}"


# ================================================================ session-audit regressions


def test_an_unadmitted_profile_is_refused_at_the_gate_not_failed_at_the_adapter(rig: Rig) -> None:
    """`adapter_error` looks transient; `not_admitted` names the truth. The registry declared the
    gap -- the pipeline must refuse in its name, not stumble over the missing adapter."""
    cell = rig.cell("r1/agent/0")
    receipt = cell.act("code.run@sandbox", {"source": "print(1)"}, harm_declared="H1")
    assert receipt.exec == "refused"
    assert receipt.reason == "not_admitted", f"the gap is hiding behind '{receipt.reason}'"


def test_an_orphan_blob_is_caught_by_verify(rig: Rig) -> None:
    """The crash window between os.link and the manifest rewrite leaves a REAL delivery narration
    cannot see. One-directional verification read exactly that loss as 'clean'."""
    deliver_outbox.execute(dict(DELIVERY, effect_key="lineage:root:recorded"))
    (rig.outbox / "00deadbeef00deadbeef00deadbeef00.json").write_text(
        json.dumps({"to": "ops@example.test", "effect_key": "lineage:root:orphan"}),
        encoding="utf-8",
    )
    ok, why = deliver_outbox.verify_outbox(rig.outbox)
    assert not ok and "not in the manifest" in why


def test_a_settle_receipt_carries_the_actor_so_the_ledger_can_attribute() -> None:
    """wager_ledger keys on (claim, lane) -- and settle receipts carried no actor, so every
    production key was ("", lane). A fold reading a field nobody writes is the F26 shape."""
    rec = {
        "kind": "act_receipt", "seq": 1,
        "body": {"corr": "act_1", "exec": "ok", "capability_ref": "deliver.outbox",
                 "actor": "r1/agent/0",
                 "expectation": {"kind": "oracle_cmd", "args": {"checker": "c"},
                                 "resolve_by": _just_passed()}},
    }
    settled = Settler(probes={"oracle_cmd": lambda _e: "HOLDS"}).settle_one(rec)  # type: ignore[dict-item]
    assert settled["actor"] == "r1/agent/0", "the settle receipt lost the actor"

    ledger = wager_ledger([{"kind": "act_receipt", "body": settled}])
    assert ("r1/agent/0", "deliver.outbox") in ledger, "attribution fell back to the empty key"


def test_a_deadline_in_either_iso_spelling_counts_as_due() -> None:
    """fromisoformat accepts `...Z` and `...+00:00`; a lexicographic compare across the two
    mis-orders them, and a wager whose deadline never reads as due silently always wins."""
    plus_style = (datetime.now(UTC) - timedelta(seconds=5)).isoformat()  # ...+00:00
    assert "+00:00" in plus_style
    rec = {
        "kind": "act_receipt", "seq": 1,
        "body": {"corr": "act_1", "exec": "ok", "capability_ref": "deliver.outbox",
                 "expectation": {"kind": "oracle_cmd", "args": {"checker": "c"},
                                 "resolve_by": plus_style}},
    }
    due = Settler(probes={}).unsettled([rec])
    assert len(due) == 1, "the +00:00 spelling never became due under string comparison"
