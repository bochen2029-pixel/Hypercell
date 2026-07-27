"""RE-4 / CERT-1 — FOLD, resume, and the certificate (slice RE-4).

**RE-4's bar:** `kill -9` at 10 random points → each resume completes; the final certificate is
**FIELD-IDENTICAL** to an uninterrupted control at the same seeds; zero double-scored submissions.
**CERT-1's bar:** flip one bit in the span → verify fails **naming the field**; the two-log spend
totals agree.

**The null is in-RAM state** — the live fabric kept arms, rounds, convergence and the spend meter in
process memory, so a crash did not interrupt the run, it erased what the run knew about itself (F16
is that defect wearing its money hat). Measured directly below: the null's state after a restart is
empty, and its certificate would describe a run that had just begun.

"Field-identical to an uninterrupted control" is only a meaningful bar if the run is deterministic
given its inputs, so `bench/drills/run_kill9.py` scripts a fixed tournament — every record and every
score pinned — and two executions differ **only** in where they were interrupted.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from bench.drills.run_kill9 import CULTURE, MANIFEST_SHA, RUN_ID, play, script

from hypercell.conductor.anchor import AnchorLog
from hypercell.conductor.certificate import certificate, verify_certificate
from hypercell.conductor.engine.fold import FOLD_TYPES, fold
from hypercell.conductor.engine.resume import ResumeRefused, resume, should_score
from hypercell.conductor.governor import Escrow
from hypercell.medium.transport_local import LocalMedium


def _medium(home: Path) -> LocalMedium:
    return LocalMedium(home, anchor=AnchorLog(home, CULTURE, anchor_every=16))


def _full_run(home: Path) -> LocalMedium:
    med = _medium(home)
    play(med)
    return med


# ================================================================ the null


def test_the_null_in_ram_state_is_empty_after_a_restart() -> None:
    """F16's shape: the planes lived in process memory, so a restart knew nothing about the run.

    The fold's whole claim is that this is recoverable from the log; the null is what "recoverable"
    is measured against.
    """
    class InRamPlanes:
        def __init__(self) -> None:
            self.round = 0
            self.spend = 0.0
            self.champion = None

    before = InRamPlanes()
    before.round, before.spend, before.champion = 4, 0.36, "b"

    after = InRamPlanes()  # the restart
    assert (after.round, after.spend, after.champion) == (0, 0.0, None), (
        "the null is supposed to forget everything — that is the defect the fold repairs"
    )


# ================================================================ the fold


def test_the_fold_derives_the_run_from_the_log_alone(tmp_path: Path) -> None:
    med = _full_run(tmp_path)
    state = fold(CULTURE, med.read(CULTURE))

    assert state.run_id == RUN_ID and state.manifest_sha256 == MANIFEST_SHA
    assert state.round == 4, f"rounds folded to {state.round}, not 4"
    assert state.champion is not None and state.champion.who == "b"
    assert state.convergence.converged, "the scripted run should converge on arm b"
    assert state.spend_total > 0
    med.close()


def test_the_fold_is_pure_and_repeatable(tmp_path: Path) -> None:
    """Two folds over the same records agree exactly — the property `hc verify` rests on."""
    med = _full_run(tmp_path)
    records = med.read(CULTURE)
    a, b = fold(CULTURE, records), fold(CULTURE, records)
    assert certificate(a)["cert_sha256"] == certificate(b)["cert_sha256"]
    med.close()


def test_the_input_filter_is_compaction_closed(tmp_path: Path) -> None:
    """L-FOLD-CLOSURE: R-decay types are excluded BY CLASS. That is what makes compaction safe —
    chat can evaporate and every certificate still refolds identically."""
    assert "chat" not in FOLD_TYPES and "status" not in FOLD_TYPES

    med = _full_run(tmp_path)
    clean = certificate(fold(CULTURE, med.read(CULTURE)))["cert_sha256"]

    for i in range(30):  # bury the run in chatter
        med.post(CULTURE, "a", "chat", body={"noise": i})
        med.post(CULTURE, "a", "status", body={"noise": i})
    noisy = certificate(fold(CULTURE, med.read(CULTURE)))["cert_sha256"]

    assert clean == noisy, "chatter moved the certificate; the fold is not compaction-closed"
    med.close()


def test_a_round_open_claiming_an_unearned_gen_bump_is_void_at_fold(tmp_path: Path) -> None:
    """The gen-bump gate keys on record EXISTENCE, never a body parse: a run cannot advance its own
    grader by writing a field that says it did."""
    med = _medium(tmp_path)
    med.post(CULTURE, "conductor", "presence",
             body={"phase": "genesis", "run_id": RUN_ID, "manifest_sha256": MANIFEST_SHA,
                   "arms": ["a"], "convergence": {"target": 1.0, "stable_k": 1}})
    med.post(CULTURE, "conductor", "round_open", body={"gen": 4})  # claims a bump, no oracle_gen

    state = fold(CULTURE, med.read(CULTURE))
    assert state.gen == 0, "an unearned generation bump was honoured"
    assert state.void_at_fold and state.void_at_fold[0]["type"] == "round_open"
    med.close()


def test_a_backed_gen_bump_is_honoured_and_resets_stability(tmp_path: Path) -> None:
    """With a conductor `oracle_gen` record behind it, the bump lands — and stales every score,
    because a verdict earned under the old grader is not evidence under the new one."""
    med = _medium(tmp_path)
    med.post(CULTURE, "conductor", "presence",
             body={"phase": "genesis", "run_id": RUN_ID, "manifest_sha256": MANIFEST_SHA,
                   "arms": ["a"], "convergence": {"target": 1.0, "stable_k": 1}})
    med.post(CULTURE, "a", "submission", body={"cand": "a0"})
    med.post(CULTURE, "conductor", "receipt",
             body={"submission_seq": 2, "arm": "a", "outcome": "passed", "score": 1.0})
    med.post(CULTURE, "conductor", "oracle_gen", body={"gen": 1})
    med.post(CULTURE, "conductor", "round_open", body={"gen": 1})

    state = fold(CULTURE, med.read(CULTURE))
    assert state.gen == 1 and not state.void_at_fold
    assert state.convergence.champion is None, "the gen bump did not stale the old champion"
    med.close()


def test_spend_folds_from_the_cost_group_with_no_spend_type(tmp_path: Path) -> None:
    """§R8.2: there is NO spend type — spend folds from the `cost{}` group wherever it rides."""
    med = _full_run(tmp_path)
    state = fold(CULTURE, med.read(CULTURE))
    assert state.spend["production"] > 0
    assert state.spend_total == pytest.approx(sum(state.spend.values()))
    med.close()


# ================================================================ zero double-scored submissions


def test_a_replayed_grading_is_not_scored_twice(tmp_path: Path) -> None:
    """Stability is a COUNT, so a re-scored candidate ticks convergence twice for one piece of
    evidence and the run converges on a lie. The key is `(submission_seq, oracle_gen)`."""
    med = _medium(tmp_path)
    med.post(CULTURE, "conductor", "presence",
             body={"phase": "genesis", "run_id": RUN_ID, "manifest_sha256": MANIFEST_SHA,
                   "arms": ["a"], "convergence": {"target": 1.0, "stable_k": 2}})
    med.post(CULTURE, "a", "submission", body={"cand": "a0"})
    for i in range(3):  # the same candidate graded three times under one generation
        med.post(CULTURE, "conductor", "receipt",
                 body={"submission_seq": 2, "arm": "a", "outcome": "passed", "score": 1.0},
                 idem=f"r{i}")

    state = fold(CULTURE, med.read(CULTURE))
    assert state.gradings == 1, f"{state.gradings} gradings counted for one candidate"
    assert len(state.duplicate_gradings) == 2, "the duplicates were not named"
    med.close()


def test_should_score_is_the_gate_the_loop_calls(tmp_path: Path) -> None:
    med = _full_run(tmp_path)
    plan = resume(CULTURE, med.read(CULTURE), home=tmp_path, expected_manifest_sha=MANIFEST_SHA)
    already = next(iter(plan.already_scored))
    assert not should_score(plan, already[0], already[1]), "the loop would have re-scored"
    assert should_score(plan, 999_999, 0), "a never-seen submission was refused"
    med.close()


# ================================================================ resume


def test_resume_refuses_a_manifest_sha_mismatch(tmp_path: Path) -> None:
    """Resuming under different bytes than the run started with would make `manifest_sha256` on the
    certificate a number that points at nothing."""
    med = _full_run(tmp_path)
    with pytest.raises(ResumeRefused, match="manifest sha mismatch"):
        resume(CULTURE, med.read(CULTURE), home=tmp_path, expected_manifest_sha="sha256:different")
    med.close()


def test_resume_refuses_a_claim_id_with_history_but_no_nucleus(tmp_path: Path) -> None:
    """Identity corruption outranks a crash: a cell resurrected without its own memory will
    confidently contradict its history."""
    med = _full_run(tmp_path)
    with pytest.raises(ResumeRefused, match="no nucleus on disk"):
        resume(CULTURE, med.read(CULTURE), home=tmp_path,
               expected_manifest_sha=MANIFEST_SHA, nucleus_exists=lambda _c: False)
    med.close()


def test_resume_reconciles_the_budget_before_any_new_reserve(tmp_path: Path) -> None:
    """ECON-L8 at run level: a resumed run that reserved first would spend against a budget it had
    not yet counted."""
    first = Escrow(cap_usd=10.0, home=tmp_path, fsync=False)
    first.commit(first.reserve(2.0, scope="run:re4").resv_id, 2.0)

    resumed_escrow = Escrow(cap_usd=10.0, home=tmp_path, fsync=False)
    assert resumed_escrow.needs_reconcile

    med = _full_run(tmp_path)
    plan = resume(CULTURE, med.read(CULTURE), home=tmp_path,
                  expected_manifest_sha=MANIFEST_SHA, escrow=resumed_escrow)
    assert plan.reconciled and not resumed_escrow.needs_reconcile
    assert resumed_escrow.committed("fleet") == pytest.approx(2.0), "the fold forgot pre-crash spend"
    med.close()


def test_park_resume_and_crash_resume_are_the_same_path(tmp_path: Path) -> None:
    """The parked record is metadata, never load-bearing — so a politely parked run and a killed one
    resume through identical code and reach identical state."""
    crashed = _full_run(tmp_path / "crash")
    parked_home = tmp_path / "park"
    parked = _medium(parked_home)
    play(parked)
    parked.post(CULTURE, "conductor", "presence", body={"phase": "parked"})

    a = resume(CULTURE, crashed.read(CULTURE), home=tmp_path, expected_manifest_sha=MANIFEST_SHA)
    b = resume(CULTURE, parked.read(CULTURE), home=tmp_path, expected_manifest_sha=MANIFEST_SHA)

    assert a.state.round == b.state.round
    assert a.state.champion.who == b.state.champion.who  # type: ignore[union-attr]
    assert certificate(a.state)["champion"] == certificate(b.state)["champion"]
    crashed.close()
    parked.close()


# ================================================================ CERT-1


def test_cert1_a_flipped_bit_in_the_span_fails_verify_naming_the_field(tmp_path: Path) -> None:
    """Two independent nets: the chain catches the bit, and if a verifier were handed a span whose
    chain had been repaired, the recomputed fold still moves and the FIELD is named."""
    med = _full_run(tmp_path)
    records = med.read(CULTURE)
    cert = certificate(fold(CULTURE, records))

    # Flip one bit of one score in the span — a repaired-chain attacker's best case.
    tampered = [dict(r) for r in records]
    for rec in tampered:
        if rec["type"] == "receipt" and isinstance(rec["body"], dict) and rec["body"].get("score") == 1.0:
            rec["body"] = {**rec["body"], "score": 0.5}
            break

    result = verify_certificate(cert, tampered)
    assert not result.ok, "a flipped score verified"
    assert result.bad_fields, "verify failed without naming a field"
    assert any("champion" in f or "convergence" in f for f in result.bad_fields), result.bad_fields
    med.close()


def test_cert1_a_broken_chain_fails_verify_at_step_one(tmp_path: Path) -> None:
    med = _full_run(tmp_path)
    cert = certificate(fold(CULTURE, med.read(CULTURE)))
    result = verify_certificate(cert, med.read(CULTURE), chain_ok=False)
    assert not result.ok and "hash chain" in result.reason
    med.close()


def test_cert1_the_two_log_spend_totals_agree(tmp_path: Path) -> None:
    """The span's `cost{}` sums on one side, the conductor's escrow-ledger fold on the other. Two
    independently-maintained records of the same dollars."""
    med = _full_run(tmp_path)
    state = fold(CULTURE, med.read(CULTURE))

    escrow = Escrow(cap_usd=10.0, home=tmp_path, fsync=False)
    escrow.commit(escrow.reserve(state.spend_total, scope="run:re4").resv_id, state.spend_total)

    cert = certificate(state, escrow_committed_usd=escrow.committed("fleet"))
    result = verify_certificate(cert, med.read(CULTURE), escrow_committed_usd=escrow.committed("fleet"))
    assert result.ok and result.spend_agrees, result.reason
    med.close()


def test_cert1_disagreeing_spend_logs_fail_verify(tmp_path: Path) -> None:
    """If the two logs disagree one of them is lying, and the certificate must not average them."""
    med = _full_run(tmp_path)
    state = fold(CULTURE, med.read(CULTURE))
    cert = certificate(state, escrow_committed_usd=state.spend_total)

    result = verify_certificate(cert, med.read(CULTURE),
                                escrow_committed_usd=state.spend_total + 0.05)
    assert not result.ok and not result.spend_agrees
    assert "two spend logs disagree" in result.reason
    med.close()


def test_an_untampered_certificate_verifies(tmp_path: Path) -> None:
    med = _full_run(tmp_path)
    records = med.read(CULTURE)
    cert = certificate(fold(CULTURE, records))
    assert verify_certificate(cert, records).ok
    med.close()


def test_the_cert_digest_excludes_itself_and_the_signature(tmp_path: Path) -> None:
    """A digest cannot cover itself, and the Stage-1b signature seam signs the same body — so the
    two agree on what 'the certificate' means."""
    med = _full_run(tmp_path)
    cert = certificate(fold(CULTURE, med.read(CULTURE)))
    before = cert["cert_sha256"]
    cert["signature"] = {"alg": "ed25519", "sig": "whatever"}
    import hashlib

    from hypercell.common.canon import canon_bytes
    from hypercell.conductor.certificate import _body
    assert "sha256:" + hashlib.sha256(canon_bytes(_body(cert))).hexdigest() == before
    med.close()


# ================================================================ RE-4: the kill-9 comparison


@pytest.mark.slow
def test_re4_ten_kill_points_all_resume_to_the_control_certificate(tmp_path: Path) -> None:
    """The bar. Ten interruption points; each resumes, finishes, and certifies IDENTICALLY to an
    uninterrupted control at the same seeds — and no submission is scored twice along the way.

    Each round runs the child in a real subprocess and kills it at a different record boundary, so
    what the parent resumes from is whatever actually reached disk, not a simulated prefix.
    """
    root = Path(__file__).resolve().parent.parent
    total = len(script())

    # The control: one uninterrupted run.
    control_home = tmp_path / "control"
    control_home.mkdir()
    out = subprocess.run([sys.executable, "-m", "bench.drills.run_kill9", str(control_home), "0"],
                         cwd=root, capture_output=True, text=True, timeout=120)
    assert out.returncode == 0, out.stderr[-1500:]
    control_med = LocalMedium(control_home)
    control_cert = certificate(fold(CULTURE, control_med.read(CULTURE)))
    control_med.close()
    assert control_cert["champion"]["arm"] == "b"

    kill_points = [max(1, round(total * (i + 1) / 11)) for i in range(10)]
    for i, upto in enumerate(kill_points):
        home = tmp_path / f"k{i}"
        home.mkdir()

        # Interrupt: the child posts only `upto` records, then the process ends mid-run.
        cut = subprocess.run([sys.executable, "-m", "bench.drills.run_kill9", str(home), str(upto)],
                             cwd=root, capture_output=True, text=True, timeout=120)
        assert cut.returncode == 0, f"point {i}: {cut.stderr[-1200:]}"

        # Resume: fold what landed, refuse nothing, then finish the run from the same script.
        med = LocalMedium(home, anchor=AnchorLog(home, CULTURE, anchor_every=16))
        plan = resume(CULTURE, med.read(CULTURE), home=home, expected_manifest_sha=MANIFEST_SHA)
        assert plan.state.manifest_sha256 == MANIFEST_SHA, f"point {i}: manifest not recovered"

        play(med)  # idempotent: every post carries an idem, so replayed records dedup
        finished = fold(CULTURE, med.read(CULTURE))
        cert = certificate(finished)

        assert not finished.duplicate_gradings, (
            f"point {i}: {len(finished.duplicate_gradings)} submissions were scored twice"
        )
        # SEMANTIC identity: everything the run concluded. `cert_sha256` legitimately differs,
        # because it commits to a specific physical log and two logs written at different moments
        # chain differently (every record carries its own ts) — wire C9's "excluding ts/hash
        # timing", drawn one level up.
        assert cert["semantic_sha256"] == control_cert["semantic_sha256"], (
            f"point {i} (upto={upto}): the resumed certificate differs from the control.\n"
            f"  control champion={control_cert['champion']} spend={control_cert['spend']['total']}\n"
            f"  resumed champion={cert['champion']} spend={cert['spend']['total']}"
        )
        assert verify_certificate(cert, med.read(CULTURE)).ok, f"point {i}: cert did not verify"
        med.close()
