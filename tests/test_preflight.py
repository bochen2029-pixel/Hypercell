"""PREFLIGHT-LITE-1 — the box-guard battery drill (ARCHITECTURE §15; slice S9.1).

The bar: inject each box failure, and the matching guard MUST fire with the right state and a real
operator fix string; `max_honest_sandbox_class` must be correct; **no failure passes silently.**

The null this drill kills: a fabric that boots on `/mnt/c` and silently WAL-corrupts, or claims
gold-durability with no pragmas set.
"""
from __future__ import annotations

import time
from pathlib import Path

import pytest

from hypercell.substrate import k3s
from hypercell.substrate.preflight import GUARDS, GuardResult, PreflightReport, render, worst


@pytest.fixture
def home(tmp_path: Path) -> Path:
    return tmp_path / "hcstate"


# ---------------------------------------------------------------- registry + report invariants


def test_all_a_prime_guards_registered() -> None:
    """The seven box guards S9.1 owes. A missing guard is a hole the preflight cannot see through."""
    expected = {
        "G-DBLOCAL",
        "G-DB-DURABLE",
        "G-CLOCK",
        "G-CGROUP",
        "G-FSYNC",
        "G-LOCAL-FLOOR",
        "G-UPTIME-REGIME",
    }
    assert {gid for gid, spec in GUARDS.items() if spec.land == "a'"} == expected


def test_no_failure_passes_silently(home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Every non-GREEN result carries a fix string — the core of the bar."""
    monkeypatch.delenv("HYPERCELL_LOCAL_BASE_URL", raising=False)
    monkeypatch.delenv("LOCAL_BASE_URL", raising=False)
    report = k3s.run_preflight(home)

    assert report.results, "preflight ran zero guards"
    for r in report.results:
        if r.state != "GREEN":
            assert r.fix.strip(), f"{r.id} failed with no operator fix string"
        assert r.detail.strip(), f"{r.id} reported no detail"
    assert set(report.guards_failed) == {r.id for r in report.results if r.state != "GREEN"}


def test_guard_result_refuses_a_fixless_failure() -> None:
    """The type system enforces the bar: you cannot construct a silent failure."""
    with pytest.raises(ValueError, match="no operator fix"):
        GuardResult("G-TEST", "RED", "something broke")
    GuardResult("G-TEST", "GREEN", "fine")  # GREEN needs no fix


def test_report_digest_is_stable_and_state_sensitive() -> None:
    """Admission records embed the digest; it must move when a guard's state moves, and only then."""
    a = PreflightReport("GREEN", [GuardResult("G-A", "GREEN", "detail one")], 1, ("a'",))
    b = PreflightReport("GREEN", [GuardResult("G-A", "GREEN", "detail two — timings differ")], 1, ("a'",))
    c = PreflightReport("DEGRADED", [GuardResult("G-A", "DEGRADED", "d", fix="f")], 1, ("a'",))
    assert a.digest == b.digest, "digest must not churn on detail text"
    assert a.digest != c.digest, "digest must move when a guard's state moves"


def test_worst_folds_states() -> None:
    assert worst([]) == "GREEN"
    assert worst(["GREEN", "DEGRADED"]) == "DEGRADED"
    assert worst(["DEGRADED", "RED", "GREEN"]) == "RED"


# ---------------------------------------------------------------- injection: G-DBLOCAL


def test_inject_drvfs_home_fires_dblocal_red(home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """HYPERCELL_HOME=/mnt/c — the lived corruption trap. RED, and it must name the fix."""
    monkeypatch.setattr(k3s, "_fstype_of", lambda p: ("/mnt/c", "drvfs"))
    r = k3s.g_dblocal(home)
    assert r.state == "RED"
    assert "drvfs" in r.detail
    assert "HYPERCELL_HOME" in r.fix


def test_inject_network_fs_fires_dblocal_red(home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(k3s, "_fstype_of", lambda p: ("/net/share", "nfs4"))
    assert k3s.g_dblocal(home).state == "RED"


def test_local_ext4_home_is_green(home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(k3s, "_fstype_of", lambda p: ("/", "ext4"))
    r = k3s.g_dblocal(home)
    assert r.state == "GREEN"
    assert r.fix == ""


def test_unprovable_fstype_is_degraded_not_green(home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Unprovable is not fine. A box that cannot check its own filesystem says so."""
    monkeypatch.setattr(k3s, "_fstype_of", lambda p: None)
    r = k3s.g_dblocal(home)
    assert r.state == "DEGRADED"
    assert "unproven" in r.detail


# ---------------------------------------------------------------- injection: G-DB-DURABLE


def test_missing_pragmas_fire_db_durable(home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """E3, live today: the Medium sets WAL and nothing else. The guard must catch it."""
    monkeypatch.setattr(Path, "read_text", lambda self, **kw: 'self._db.execute("PRAGMA journal_mode=WAL")')
    r = k3s.g_db_durable(home)
    assert r.state == "DEGRADED"
    assert "synchronous" in r.detail and "busy_timeout" in r.detail
    assert "E3" in r.fix


def test_declared_pragmas_pass_db_durable(home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """And it must go GREEN once the Medium declares them — a guard that never passes is noise."""
    monkeypatch.setattr(
        Path,
        "read_text",
        lambda self, **kw: 'execute("PRAGMA journal_mode=WAL"); execute("PRAGMA synchronous=FULL"); '
        'execute("PRAGMA busy_timeout=5000")',
    )
    assert k3s.g_db_durable(home).state == "GREEN"


# ---------------------------------------------------------------- injection: G-CLOCK


def test_inject_clock_skew_fires_g_clock(monkeypatch: pytest.MonkeyPatch) -> None:
    """Host sleep/resume: the wall clock jumps while monotonic does not. ULID ordering depends on this."""
    real = time.time
    calls = iter([0.0, 5.0])  # second read lands 5 s in the future — a resume-class step

    def stepped() -> float:
        return real() + next(calls, 5.0)

    monkeypatch.setattr(time, "time", stepped)
    r = k3s.g_clock(Path("."))
    assert r.state == "DEGRADED"
    assert "sleep/resume" in r.detail
    assert "time sync" in r.fix


def test_inject_frozen_monotonic_fires_red(monkeypatch: pytest.MonkeyPatch) -> None:
    """A monotonic clock that does not advance makes leases meaningless — RED, not DEGRADED."""
    monkeypatch.setattr(time, "monotonic", lambda: 1000.0)
    r = k3s.g_clock(Path("."))
    assert r.state == "RED"
    assert "lease" in r.fix


def test_healthy_clock_is_green() -> None:
    assert k3s.g_clock(Path(".")).state == "GREEN"


# ---------------------------------------------------------------- injection: G-CGROUP


def test_missing_memory_cgroup_is_degraded(monkeypatch: pytest.MonkeyPatch) -> None:
    """WSL2 shipped without the memory controller — pod limits were theater and nobody was told."""
    monkeypatch.setattr(Path, "exists", lambda self: False)
    r = k3s.g_cgroup(Path("."))
    assert r.state == "DEGRADED"
    assert "memory" in r.fix.lower()


def test_cgroup_v2_with_memory_is_green(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Path, "exists", lambda self: str(self).replace("\\", "/").endswith("cgroup.controllers"))
    monkeypatch.setattr(Path, "read_text", lambda self, **kw: "cpuset cpu io memory pids")
    assert k3s.g_cgroup(Path(".")).state == "GREEN"


def test_cgroup_v2_without_memory_is_degraded(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Path, "exists", lambda self: str(self).replace("\\", "/").endswith("cgroup.controllers"))
    monkeypatch.setattr(Path, "read_text", lambda self, **kw: "cpuset cpu io pids")
    r = k3s.g_cgroup(Path("."))
    assert r.state == "DEGRADED"
    assert "not delegated" in r.detail


# ---------------------------------------------------------------- injection: G-FSYNC


def test_fsync_measures_and_passes_on_local_disk(home: Path) -> None:
    r = k3s.g_fsync(home)
    assert r.state in {"GREEN", "DEGRADED"}
    assert "p50" in r.detail
    assert not (home / ".preflight_fsync_probe").exists(), "probe file must be cleaned up"


def test_unwritable_home_fires_fsync_red(home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*a: object, **kw: object) -> int:
        raise OSError(13, "Permission denied")

    monkeypatch.setattr(k3s.os, "open", boom)
    r = k3s.g_fsync(home)
    assert r.state == "RED"
    assert "writable" in r.fix


def test_slow_fsync_is_degraded(home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(k3s, "_FSYNC_P50_BUDGET_MS", -1.0)  # any real fsync now exceeds budget
    r = k3s.g_fsync(home)
    assert r.state == "DEGRADED"
    assert "budget" in r.detail


# ---------------------------------------------------------------- injection: G-LOCAL-FLOOR


def test_dead_local_lane_is_degraded(monkeypatch: pytest.MonkeyPatch) -> None:
    """A floor you cannot reach is not a floor. Port 9 discards — nothing will answer."""
    monkeypatch.setenv("HYPERCELL_LOCAL_BASE_URL", "http://127.0.0.1:9")
    r = k3s.g_local_floor(Path("."))
    assert r.state == "DEGRADED"
    assert "unreachable" in r.detail


def test_unconfigured_local_lane_is_degraded(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HYPERCELL_LOCAL_BASE_URL", raising=False)
    monkeypatch.delenv("LOCAL_BASE_URL", raising=False)
    r = k3s.g_local_floor(Path("."))
    assert r.state == "DEGRADED"
    assert "degrade ladder" in r.fix


# ---------------------------------------------------------------- max_honest_sandbox_class


def test_a_prime_only_ceilings_class_at_one(home: Path) -> None:
    """Box guards prove nothing about containers. Claiming >=2 here is what PARITY-1 exists to catch."""
    report = k3s.run_preflight(home)
    assert report.max_honest_sandbox_class == 1
    assert report.lands == ("a'",)


def test_spine_red_halts_and_zeroes_the_class(home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """RED on a spine guard halts the fabric — these caused a lived crash-loop or corruption."""
    monkeypatch.setattr(k3s, "_fstype_of", lambda p: ("/mnt/c", "drvfs"))
    report = k3s.run_preflight(home)
    assert report.verdict == "RED"
    assert report.halted is True
    assert report.max_honest_sandbox_class == 0
    assert "G-DBLOCAL" in report.guards_failed


def test_non_spine_degraded_does_not_halt(home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """DEGRADED is a label, not a stop. The fabric runs and says so on every receipt."""
    monkeypatch.setattr(k3s, "_fstype_of", lambda p: ("/", "ext4"))
    report = k3s.run_preflight(home)
    assert report.halted is False
    assert report.max_honest_sandbox_class == 1


# ---------------------------------------------------------------- fold-visible surfaces


def test_status_body_and_admission_stanza_shapes(home: Path) -> None:
    """The probe posts status{kind:preflight}; admission records embed the stanza inline."""
    report = k3s.run_preflight(home)

    body = report.as_status_body()
    assert body["kind"] == "preflight"
    assert body["digest"] == report.digest
    assert isinstance(body["guards"], list)

    stanza = report.admission_stanza()
    assert set(stanza) == {"digest", "verdict", "guards_failed"}


def test_render_prints_every_fix(home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The fix string is the point — it must reach the operator's terminal."""
    monkeypatch.setattr(k3s, "_fstype_of", lambda p: ("/mnt/c", "drvfs"))
    report = k3s.run_preflight(home)
    text = render(report)
    assert "HALTED" in text
    assert "max_honest_sandbox_class = 0" in text
    for r in report.results:
        if r.state != "GREEN":
            assert r.fix in text, f"{r.id}'s fix never reached the operator"


def test_preflight_is_a_probe_not_state(home: Path) -> None:
    """A13: re-running must re-measure, never resume. Two runs, same states, no persisted artifact."""
    first = k3s.run_preflight(home)
    second = k3s.run_preflight(home)
    assert first.digest == second.digest
    assert not list(home.glob("*preflight*")), "the preflight must not persist state"
