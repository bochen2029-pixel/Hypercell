"""The box-guard battery — the `a'` land (ARCHITECTURE §11; falsifier PREFLIGHT-LITE-1, slice S9.1).

These seven guards protect the **live single-box SQLite Medium today**, with no k3s anywhere. The
module is named for the substrate it will eventually gate: the `d'` k3s battery (G-ONE-RUNTIME,
G-FORWARD-ACCEPT, G-GVISOR, G-PVC-SURVIVES, ...) joins these at slice S9.2 and gates class
escalation. Until then, running the `a'` land alone is legal and honest — it simply bounds
`max_honest_sandbox_class` to 1, because box guards prove nothing about container isolation.

Each guard reports what it *actually checked*. Where a platform makes a fact unprovable, the guard
says DEGRADED ("unproven"), never GREEN ("fine") and never RED ("broken") — the whole point of the
preflight is that the box stops lying about itself.
"""
from __future__ import annotations

import os
import platform
import sqlite3
import statistics
import time
from pathlib import Path

from .preflight import GUARDS, GuardResult, Land, PreflightReport, guard, worst

#: Filesystems that corrupt SQLite WAL or break its locking. The lived defect is `/mnt/c` (drvfs).
_UNSAFE_FSTYPES = frozenset(
    {"drvfs", "9p", "v9fs", "cifs", "smbfs", "smb3", "nfs", "nfs4", "vboxsf", "fuse.sshfs", "virtiofs"}
)

#: NUC-7's d1 append budget. fsync p50 above this makes gold-durability slow, not unsafe.
_FSYNC_P50_BUDGET_MS = 10.0


def _is_wsl() -> bool:
    try:
        return "microsoft" in Path("/proc/version").read_text(encoding="utf-8", errors="ignore").lower()
    except OSError:
        return False


def _fstype_of(path: Path) -> tuple[str, str] | None:
    """Longest-prefix match against /proc/mounts → (mount_point, fstype). None where unreadable."""
    try:
        lines = Path("/proc/mounts").read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return None
    target = str(path.resolve())
    best: tuple[str, str] | None = None
    for line in lines:
        parts = line.split()
        if len(parts) < 3:
            continue
        mount, fstype = parts[1], parts[2]
        if target == mount or target.startswith(mount.rstrip("/") + "/"):
            if best is None or len(mount) > len(best[0]):
                best = (mount, fstype)
    return best


@guard("G-DBLOCAL", land="a'", spine=True)
def g_dblocal(home: Path) -> GuardResult:
    """The Medium and every nucleus MUST sit on a native local filesystem. WAL corrupts elsewhere."""
    resolved = str(home.resolve())
    mount = _fstype_of(home)
    if mount is not None:
        mount_point, fstype = mount
        if fstype in _UNSAFE_FSTYPES:
            return GuardResult(
                "G-DBLOCAL",
                "RED",
                f"HYPERCELL_HOME={resolved} is on {fstype} (mounted at {mount_point}) -- SQLite WAL corrupts here",
                fix=f"move HYPERCELL_HOME onto native storage, e.g. export HYPERCELL_HOME=$HOME/.hypercell "
                f"(never {mount_point})",
            )
        return GuardResult("G-DBLOCAL", "GREEN", f"{resolved} on {fstype} (local, mounted at {mount_point})")

    # No /proc/mounts — a non-Linux host. We can still catch the unambiguously fatal case.
    if resolved.startswith("\\\\") or resolved.startswith("//"):
        return GuardResult(
            "G-DBLOCAL",
            "RED",
            f"HYPERCELL_HOME={resolved} is a UNC/network path -- SQLite locking is unreliable there",
            fix="move HYPERCELL_HOME onto a local disk (a real drive letter or POSIX path)",
        )
    return GuardResult(
        "G-DBLOCAL",
        "DEGRADED",
        f"cannot read /proc/mounts on {platform.system()}; filesystem type of {resolved} unproven",
        fix="run the fabric on Linux/WSL2 where the filesystem type is checkable, or verify by hand "
        "that HYPERCELL_HOME is not a network or drvfs mount",
    )


@guard("G-DB-DURABLE", land="a'", spine=True)
def g_db_durable(home: Path) -> GuardResult:
    """WAL + an explicit `synchronous` + `busy_timeout`. Defaults are not a durability contract (E3)."""
    from .. import medium  # local import: substrate must not pull the Medium into module import order

    src_path = Path(medium.__file__).parent / "transport_local.py"
    try:
        src = src_path.read_text(encoding="utf-8")
    except OSError:
        src = ""

    declares_sync = "pragma synchronous" in src.lower()
    declares_busy = "busy_timeout" in src.lower()

    journal = ""
    db = home / "_medium" / "medium.db"
    if db.exists():
        try:
            conn = sqlite3.connect(db)
            try:
                row = conn.execute("PRAGMA journal_mode").fetchone()
                journal = str(row[0]).lower() if row else ""
            finally:
                conn.close()
        except sqlite3.Error as exc:  # a Medium we cannot even open is itself the finding
            return GuardResult(
                "G-DB-DURABLE",
                "RED",
                f"cannot open the Medium at {db}: {exc}",
                fix="check permissions and filesystem health on HYPERCELL_HOME; a Medium that will not "
                "open cannot be trusted to hold gold",
            )

    missing = [n for n, ok in (("synchronous", declares_sync), ("busy_timeout", declares_busy)) if not ok]
    if missing:
        return GuardResult(
            "G-DB-DURABLE",
            "DEGRADED",
            f"{src_path.name} sets no explicit {' or '.join(missing)} pragma"
            + (f"; live db journal_mode={journal}" if journal else "; Medium not yet created"),
            fix="set the connection pragmas explicitly in the Medium: journal_mode=WAL, "
            "synchronous=FULL for gold commits (NORMAL for chatter), and a busy_timeout -- "
            "SQLite defaults are not a durability contract (E3)",
        )
    if journal and journal != "wal":
        return GuardResult(
            "G-DB-DURABLE",
            "DEGRADED",
            f"live Medium journal_mode={journal}, expected wal",
            fix="PRAGMA journal_mode=WAL on the Medium connection",
        )
    return GuardResult(
        "G-DB-DURABLE",
        "GREEN",
        f"pragmas declared in {src_path.name}" + (f"; live journal_mode={journal}" if journal else ""),
    )


@guard("G-CLOCK", land="a'")
def g_clock(_home: Path) -> GuardResult:
    """Monotonic clock sane and tracking wall time. ULID ordering and lease expiry both rest on this."""
    m0, w0 = time.monotonic(), time.time()
    time.sleep(0.05)
    m1, w1 = time.monotonic(), time.time()
    dm, dw = m1 - m0, w1 - w0

    if dm <= 0:
        return GuardResult(
            "G-CLOCK",
            "RED",
            f"monotonic clock did not advance over a 50 ms sleep (delta={dm:.6f}s)",
            fix="the host's monotonic clock is broken; ULID ordering and lease expiry are unsafe -- "
            "reboot the VM or fix the hypervisor clock source",
        )
    skew_ms = abs(dw - dm) * 1000.0
    if skew_ms > 100.0:
        return GuardResult(
            "G-CLOCK",
            "DEGRADED",
            f"wall clock and monotonic disagree by {skew_ms:.0f} ms over a 50 ms window "
            "(host sleep/resume or an NTP step mid-probe)",
            fix="enable time sync on the host (WSL2: `sudo hwclock -s` after resume, or run "
            "systemd-timesyncd); re-run the preflight once the clock settles",
        )
    return GuardResult("G-CLOCK", "GREEN", f"monotonic advances; wall-vs-monotonic skew {skew_ms:.1f} ms")


@guard("G-CGROUP", land="a'")
def g_cgroup(_home: Path) -> GuardResult:
    """Memory controller present and enforcing. WSL2 shipped without it -- pod limits were theater."""
    v2 = Path("/sys/fs/cgroup/cgroup.controllers")
    if v2.exists():
        try:
            controllers = v2.read_text(encoding="utf-8").split()
        except OSError:
            controllers = []
        if "memory" in controllers:
            return GuardResult("G-CGROUP", "GREEN", "cgroup v2 memory controller present and delegated")
        return GuardResult(
            "G-CGROUP",
            "DEGRADED",
            f"cgroup v2 present but memory not delegated (controllers: {' '.join(controllers) or 'none'})",
            fix="delegate the memory controller: echo '+memory' > /sys/fs/cgroup/cgroup.subtree_control "
            "(WSL2 may need `kernelCommandLine = cgroup_enable=memory` in .wslconfig)",
        )

    if Path("/sys/fs/cgroup/memory/memory.limit_in_bytes").exists():
        return GuardResult("G-CGROUP", "GREEN", "cgroup v1 memory controller present")

    if not Path("/sys/fs/cgroup").exists():
        return GuardResult(
            "G-CGROUP",
            "DEGRADED",
            f"no cgroup filesystem on {platform.system()}; memory limits are unenforceable here",
            fix="run the fabric on Linux/WSL2 with cgroups enabled -- without them, every pod memory "
            "limit is advisory and a runaway cell can take the box",
        )
    return GuardResult(
        "G-CGROUP",
        "DEGRADED",
        "cgroup filesystem present but no memory controller found",
        fix="enable the memory cgroup controller (kernel boot arg cgroup_enable=memory); until then "
        "memory limits do not bind",
    )


@guard("G-FSYNC", land="a'")
def g_fsync(home: Path) -> GuardResult:
    """fsync p50 within the d1 append budget. Slow fsync makes gold-durability slow, not unsafe."""
    home.mkdir(parents=True, exist_ok=True)
    probe = home / ".preflight_fsync_probe"
    samples: list[float] = []
    try:
        fd = os.open(probe, os.O_CREAT | os.O_WRONLY | os.O_TRUNC)
        try:
            for i in range(11):
                os.write(fd, b"hypercell-preflight\n")
                t0 = time.perf_counter()
                os.fsync(fd)
                dt = (time.perf_counter() - t0) * 1000.0
                if i:  # discard the first -- it pays for file creation, not for fsync
                    samples.append(dt)
        finally:
            os.close(fd)
    except OSError as exc:
        return GuardResult(
            "G-FSYNC",
            "RED",
            f"cannot write or fsync under {home}: {exc}",
            fix="make HYPERCELL_HOME writable by the fabric user; a Medium that cannot fsync cannot "
            "hold gold at all",
        )
    finally:
        probe.unlink(missing_ok=True)

    p50 = statistics.median(samples)
    if p50 > _FSYNC_P50_BUDGET_MS:
        return GuardResult(
            "G-FSYNC",
            "DEGRADED",
            f"fsync p50 {p50:.1f} ms exceeds the d1 append budget of {_FSYNC_P50_BUDGET_MS:.0f} ms",
            fix="move HYPERCELL_HOME to faster local storage, or accept slower gold commits -- "
            "correctness is unaffected, throughput is not",
        )
    return GuardResult("G-FSYNC", "GREEN", f"fsync p50 {p50:.1f} ms (budget {_FSYNC_P50_BUDGET_MS:.0f} ms)")


@guard("G-LOCAL-FLOOR", land="a'")
def g_local_floor(_home: Path) -> GuardResult:
    """The terminal degrade-ladder lane. Without a reachable local model there is no floor to fall to."""
    base = os.environ.get("HYPERCELL_LOCAL_BASE_URL") or os.environ.get("LOCAL_BASE_URL")
    if not base:
        return GuardResult(
            "G-LOCAL-FLOOR",
            "DEGRADED",
            "no local lane configured (HYPERCELL_LOCAL_BASE_URL unset)",
            fix="point HYPERCELL_LOCAL_BASE_URL at a local OpenAI-compatible server (llama.cpp, "
            "ollama, vLLM) so the degrade ladder has a terminal rung that costs no dollars and "
            "needs no network",
        )
    try:
        import httpx

        resp = httpx.get(base.rstrip("/") + "/models", timeout=2.0)
    except Exception as exc:  # noqa: BLE001 -- any failure to reach the floor is the same finding
        return GuardResult(
            "G-LOCAL-FLOOR",
            "DEGRADED",
            f"local lane {base} unreachable: {type(exc).__name__}",
            fix=f"start the local model server at {base}, or unset HYPERCELL_LOCAL_BASE_URL so the "
            "fabric stops claiming a floor it does not have",
        )
    if resp.status_code >= 500:
        return GuardResult(
            "G-LOCAL-FLOOR",
            "DEGRADED",
            f"local lane {base} answered {resp.status_code}",
            fix=f"check the model server at {base} is serving an OpenAI-compatible /models endpoint",
        )
    return GuardResult("G-LOCAL-FLOOR", "GREEN", f"local lane reachable at {base}")


@guard("G-UPTIME-REGIME", land="a'", spine=True)
def g_uptime_regime(_home: Path) -> GuardResult:
    """No idle-poweroff. A VM that sleeps under a running fabric drops leases and flaps k3s."""
    if not _is_wsl():
        return GuardResult("G-UPTIME-REGIME", "GREEN", f"{platform.system()} host -- no WSL idle timer applies")

    users = Path("/mnt/c/Users")
    if users.exists():
        try:
            for user_dir in users.iterdir():
                cfg = user_dir / ".wslconfig"
                if not cfg.exists():
                    continue
                normalised = cfg.read_text(encoding="utf-8", errors="ignore").replace(" ", "").lower()
                if "vmidletimeout=-1" in normalised:
                    return GuardResult("G-UPTIME-REGIME", "GREEN", f"vmIdleTimeout=-1 in {cfg}")
                if "vmidletimeout=" in normalised:
                    return GuardResult(
                        "G-UPTIME-REGIME",
                        "RED",
                        f"{cfg} sets a finite vmIdleTimeout -- the VM will power off under a running fabric",
                        fix=f"set vmIdleTimeout=-1 under [wsl2] in {cfg}, then `wsl --shutdown` and restart",
                    )
        except OSError:
            pass

    return GuardResult(
        "G-UPTIME-REGIME",
        "DEGRADED",
        "WSL2 detected but .wslconfig could not be read -- idle-poweroff regime unproven",
        fix="set vmIdleTimeout=-1 under [wsl2] in %USERPROFILE%\\.wslconfig (or run a keepalive), "
        "then `wsl --shutdown`; an idle poweroff drops every lease the fabric holds",
    )


def run_preflight(home: Path | str | None = None, lands: tuple[Land, ...] = ("a'",)) -> PreflightReport:
    """Run every guard in `lands`. A probe, never state (A13) -- re-run it, never resume it."""
    root = Path(home) if home is not None else Path(os.environ.get("HYPERCELL_HOME", ".hypercellstate"))
    specs = [s for s in GUARDS.values() if s.land in lands]
    results = [s.fn(root) for s in sorted(specs, key=lambda s: s.id)]

    by_id = {r.id: r for r in results}
    failed = [r.id for r in results if r.state != "GREEN"]
    spine_red = [s.id for s in specs if s.spine and by_id[s.id].state == "RED"]
    verdict = worst([r.state for r in results])

    if spine_red:
        max_class = 0
    elif "d'" not in lands:
        # Box guards say nothing about container isolation. Claiming >=2 here would be the exact
        # dishonesty PARITY-1 exists to catch, so the a'-only ceiling is local-process isolation.
        max_class = 1
    else:  # pragma: no cover -- the d' battery lands at slice S9.2
        max_class = 3 if verdict == "GREEN" else 2

    return PreflightReport(
        verdict=verdict,
        results=results,
        max_honest_sandbox_class=max_class,
        lands=lands,
        halted=bool(spine_red),
        guards_failed=failed,
    )
