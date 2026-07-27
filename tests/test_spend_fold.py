"""RESUME-$1 — spend-as-fold (slice S-KG-4).

**The bar, verbatim:** kill -9 mid-drive, resume: the resumed run cannot exceed the original cap;
folded spend equals the pre-crash ledger sum (F16 regression).

**The null is the RAM meter** — `self.spent = 0.0` plus `+=`. A number that remembers its ceiling
and forgets its history on every restart, so the cap renews itself on every crash. F16 was this
bug live; ECON-L8 closed the escrow half at ECON-S2; this slice closes the Governor half: `spent`
is now a FOLD over the escrow ledger, taken at construction, and the fresh-instance pattern in
`drive.py` becomes fold-hydration for free.

The reservation classes complete here too (BUILD §3, S-KG-4 row):
- `res:sync` folds to zero on resume — but its COMMITTED spend survives; only the held remainder
  evaporates, because an interrupted sync call bills nothing the receipts didn't already book.
- `res:durable` carries the provider `batch_id` through the fold and settles ONLY via
  `settle_durable(receipt_corr=...)` — a receipted H0 reconciliation act, never a bare assertion.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

from hypercell.conductor.governor import FLEET, Escrow, EscrowRefused, Governor
from hypercell.conductor.ledger import EscrowLedger

CAP = 1.0


class _Result:
    model, prompt_tokens, completion_tokens = "gpt-4o-mini", 20_000, 2_000
    cache_read_tokens = cache_write_tokens = 0
    api_reported_usd = None


def _spend_once(gov: Governor) -> float:
    resv_id = gov.open_call(
        "openai", {"model": "gpt-4o-mini", "max_tokens": 2_000, "est_prompt_tokens": 20_000}
    )
    return gov.close_call(resv_id, "openai", _Result())


# ================================================================ the null, measured


def test_the_null_ram_meter_forgets_its_spending_on_restart() -> None:
    """F16's shape in four lines: same cap, new process, full budget again."""
    before = Governor(usd_cap=CAP)  # no escrow: the RAM meter, i.e. the null
    before._spent_ram = 0.95

    after = Governor(usd_cap=CAP)  # "restart"
    assert after.spent == 0.0, "the null is supposed to forget -- that is the point of it"
    assert before.usd_cap == after.usd_cap, "...while remembering its ceiling. The cap renews itself."


# ================================================================ spent is a fold


def test_governor_spent_is_a_fold_taken_at_construction(tmp_path: Path) -> None:
    """A fresh Governor over a resumed home already knows what the dead process spent."""
    first_escrow = Escrow(cap_usd=CAP, home=tmp_path, fsync=False)
    first = Governor(usd_cap=CAP, escrow=first_escrow, scope="run:a")
    spent = sum(_spend_once(first) for _ in range(3))
    assert spent > 0

    resumed_escrow = Escrow(cap_usd=CAP, home=tmp_path, fsync=False)
    resumed_escrow.reconcile()
    resumed = Governor(usd_cap=CAP, escrow=resumed_escrow, scope="run:a")
    assert resumed.spent == pytest.approx(spent), "the fold does not equal the pre-crash spend"


def test_spend_fold_reports_both_logs(tmp_path: Path) -> None:
    """The two numbers RE-4's certificate must reconcile, visible side by side already."""
    escrow = Escrow(cap_usd=CAP, home=tmp_path, fsync=False)
    gov = Governor(usd_cap=CAP, escrow=escrow, scope="run:a")
    _spend_once(gov)

    fold = gov.spend_fold()
    assert fold["escrow_committed_usd"] == pytest.approx(fold["usd_effective"]), (
        "the span-side sum and the escrow-ledger fold disagree in the SAME process; "
        "RE-4's two-log agreement would be dead on arrival"
    )


def test_the_ram_mode_keeps_its_old_equality() -> None:
    """Without an escrow the property falls back to the RAM sum — the null, honestly labelled."""
    gov = Governor(usd_cap=CAP)
    gov.record("openai", _Result())  # type: ignore[arg-type]
    assert gov.spend_fold()["usd_effective"] == pytest.approx(gov.spent)


# ================================================================ reservation classes


def test_res_sync_folds_to_zero_but_its_committed_spend_survives(tmp_path: Path) -> None:
    """An interrupted sync call bills nothing the receipts didn't book; a finished one stays booked."""
    first = Escrow(cap_usd=CAP, home=tmp_path, fsync=False)
    done = first.reserve(0.2, scope="run:a", cls="res:sync")
    first.commit(done.resv_id, 0.15)
    first.reserve(0.3, scope="run:a", cls="res:sync")  # in flight at the crash

    resumed = Escrow(cap_usd=CAP, home=tmp_path, fsync=False)
    resumed.reconcile()

    assert resumed.committed(FLEET) == pytest.approx(0.15), "committed sync spend evaporated"
    assert resumed.reserved(FLEET) == pytest.approx(0.0), "a held sync reservation survived resume"
    assert resumed.available(FLEET) == pytest.approx(CAP - 0.15)


def test_res_durable_carries_its_batch_id_through_the_fold(tmp_path: Path) -> None:
    """A resume must know WHICH provider object to reconcile — an in-doubt batch with no handle
    is un-reconcilable by construction."""
    first = Escrow(cap_usd=CAP, home=tmp_path, fsync=False)
    resv = first.reserve(0.4, scope="run:a", cls="res:durable", batch_id="batch_abc123")

    resumed = Escrow(cap_usd=CAP, home=tmp_path, fsync=False)
    resumed.reconcile()

    held = {r.resv_id: r for r in resumed.still_held()}
    assert resv.resv_id in held, "the durable leg did not survive resume as STILL-HELD"
    assert held[resv.resv_id].batch_id == "batch_abc123", "the batch handle was lost in the fold"


def test_res_durable_settles_only_through_a_receipted_reconciliation_act(tmp_path: Path) -> None:
    """No corr, no settlement: an unreceipted number here is actor self-report with a ledger."""
    escrow = Escrow(cap_usd=CAP, home=tmp_path, fsync=False)
    resv = escrow.reserve(0.4, scope="run:a", cls="res:durable", batch_id="batch_abc123")

    with pytest.raises(EscrowRefused, match="settle_durable"):
        escrow.commit(resv.resv_id, 0.2)  # the bare-assertion path is closed
    with pytest.raises(EscrowRefused, match="receipted reconciliation act"):
        escrow.settle_durable(resv.resv_id, 0.2, receipt_corr="")

    settled = escrow.settle_durable(resv.resv_id, 0.2, receipt_corr="act_batch_probe_1")
    assert settled.state == "SETTLED" and settled.committed == pytest.approx(0.2)

    on_disk = [r for r in EscrowLedger(tmp_path, fsync=False).records() if r["kind"] == "commit"]
    assert on_disk and on_disk[-1]["receipt_corr"] == "act_batch_probe_1", (
        "the settlement does not name its evidence; an auditor cannot walk from money to receipt"
    )


def test_settle_durable_refuses_the_wrong_class(tmp_path: Path) -> None:
    escrow = Escrow(cap_usd=CAP, home=tmp_path, fsync=False)
    resv = escrow.reserve(0.1, scope="run:a", cls="res:sync")
    with pytest.raises(EscrowRefused, match="batch-leg path"):
        escrow.settle_durable(resv.resv_id, 0.1, receipt_corr="act_x")


# ================================================================ RESUME-$1: the REAL kill


@pytest.mark.slow
def test_a_really_killed_spender_resumes_inside_the_original_cap(tmp_path: Path) -> None:
    """The bar, on a real corpse. The child spends through the real metered path with fsync ON,
    holds one more reservation, and is TerminateProcess'd with no handlers and no flush.

    Three assertions carry RESUME-$1:
      1. folded spend == the pre-crash truth the child wrote down (F16 regression);
      2. the resumed run cannot exceed the ORIGINAL cap — it gets the remainder, not a fresh cap;
      3. the interrupted in-flight reservation folded to zero (res:sync law), so the crash costs
         no phantom headroom either.
    """
    from bench.drills.econ_kill9 import CALLS, CAP_USD, SENTINEL

    proc = subprocess.Popen(
        [sys.executable, "-m", "bench.drills.econ_kill9", str(tmp_path)],
        cwd=Path(__file__).resolve().parent.parent,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    try:
        deadline = time.time() + 60
        while not (tmp_path / SENTINEL).exists():
            if proc.poll() is not None:
                _, err = proc.communicate()
                pytest.fail(f"the child died early:\n{err.decode(errors='replace')[-2000:]}")
            if time.time() > deadline:
                pytest.fail("the child never reached its sentinel")
            time.sleep(0.05)
        proc.kill()  # no handlers run, nothing is flushed
    finally:
        proc.wait(timeout=30)

    truth = json.loads((tmp_path / SENTINEL).read_text(encoding="utf-8"))
    assert truth["committed"] > 0, "the child recorded no spend; the drill measured nothing"

    resumed_escrow = Escrow(cap_usd=CAP_USD, home=tmp_path)
    assert resumed_escrow.needs_reconcile, "the resumed escrow did not notice the corpse's ledger"
    resumed_escrow.reconcile()
    resumed = Governor(usd_cap=CAP_USD, escrow=resumed_escrow, scope="run:kill9")

    # Snapshot the corpse's ledger BEFORE this test writes its own probe records into it —
    # otherwise the assertions below count their own footprint as the child's.
    corpse_records = list(EscrowLedger(tmp_path, fsync=False).records())

    # (1) folded spend equals the pre-crash ledger sum.
    assert resumed.spent == pytest.approx(truth["committed"]), (
        f"fold says ${resumed.spent}, the corpse's last words say ${truth['committed']}"
    )
    ledger_sum = sum(
        float(r.get("usd", 0.0)) for r in corpse_records if r["kind"] in ("commit", "draw")
    )
    assert resumed.spent == pytest.approx(ledger_sum), "the fold disagrees with the raw ledger sum"

    # And the child spent through the REAL path: one reserve per call plus the interrupted one.
    reserves = [r for r in corpse_records if r["kind"] == "reserve"]
    assert len(reserves) == CALLS + 1, "the child did not exercise the metered path per call"

    # (2) the resumed run gets the REMAINDER, never a fresh cap.
    remaining = CAP_USD - resumed.spent
    with pytest.raises(EscrowRefused):
        resumed_escrow.reserve(remaining + 0.01, scope="run:kill9")
    resumed_escrow.reserve(remaining * 0.5, scope="run:kill9")  # inside the remainder: fine

    # (3) the interrupted in-flight reservation folded to zero — the only live hold is our probe.
    assert resumed_escrow.reserved(FLEET) == pytest.approx(remaining * 0.5), (
        "a phantom reservation from the dead process survived reconcile"
    )
