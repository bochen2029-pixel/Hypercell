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

import json
import os
import platform
import shutil
import sqlite3
import statistics
import subprocess
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
    else:
        max_class = _honest_class(by_id)

    return PreflightReport(
        verdict=verdict,
        results=results,
        max_honest_sandbox_class=max_class,
        lands=lands,
        halted=bool(spine_red),
        guards_failed=failed,
    )


#: The guards that must be GREEN for each rung of the isolation ladder (S9.2). Class 3 is the only
#: rung untrusted code may use, so it is the only one that needs every isolation guard.
_CLASS_2_GUARDS = ("G-ONE-RUNTIME", "G-IMAGE-IN-K3S", "G-PVC-SURVIVES")
_CLASS_3_GUARDS = _CLASS_2_GUARDS + ("G-GVISOR", "G-NETPOL-ENFORCED", "G-IPTABLES-PRESENT")


def _honest_class(by_id: dict[str, GuardResult]) -> int:
    """The highest sandbox class this box can HONESTLY claim, from which guards are actually green.

    Driven by the specific guards rather than by the overall verdict, because those are different
    questions. A box with no cluster at all fails every d' guard as "unproven" -- and the honest
    answer there is class 1 (local process, same as the a' land), NOT class 2. Reading an
    unreachable cluster as "container isolation, just not gVisor" would be inventing a containment
    boundary out of a missing binary, which is precisely the lie this battery exists to prevent.
    """
    def green(gids: tuple[str, ...]) -> bool:
        return all(gid in by_id and by_id[gid].state == "GREEN" for gid in gids)

    if green(_CLASS_3_GUARDS):
        return 3
    if green(_CLASS_2_GUARDS):
        return 2
    return 1


# ============================================================================ the d' battery (S9.2)
#
# Seven guards that decide whether class 3 is HONESTLY available. The a' guards above protect the
# box; these protect the claim that untrusted code is contained.
#
# The design rule is the same one the a' land follows, and it matters more here: where a fact is
# UNPROVABLE the guard says DEGRADED ("unproven"), never GREEN. A class-3 claim that rests on an
# unproven guard is exactly the lie the preflight exists to prevent -- and unlike a slow fsync,
# nobody finds out it was wrong until a candidate is already outside.
#
# **Present-but-broken is a real state.** A RuntimeClass object whose containerd handler does not
# exist is created happily and then fails every pod that names it. So G-GVISOR smoke-tests a real
# pod rather than reading the object: only the smoke pod is trusted.

#: How long a guard waits on a cluster call before calling it unproven. A preflight that hangs is a
#: preflight nobody runs, and "slow" is not a state the report has.
_KUBECTL_TIMEOUT_S = 10.0

#: The sandbox namespace the class-3 manifests create (deploy/k3s/sandbox.yaml).
SANDBOX_NS = "hypercell-sandbox"


def _kubectl(*args: str, timeout: float = _KUBECTL_TIMEOUT_S) -> tuple[bool, str]:
    """Run kubectl. Returns `(reached_cluster, output)`.

    `(False, reason)` means the cluster could not be reached at all -- no binary, no config, a
    timeout. That is deliberately distinct from `(True, "")`, which means the cluster answered and
    the thing is genuinely absent. Guards must not report a missing kubectl as a missing gVisor.
    """
    exe = shutil.which("kubectl")
    if exe is None:
        return False, "kubectl not on PATH"
    try:
        proc = subprocess.run(
            [exe, *args], capture_output=True, text=True, timeout=timeout, check=False
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"kubectl did not answer: {exc}"
    if proc.returncode != 0:
        err = (proc.stderr or "").strip().splitlines()
        first = err[0] if err else f"exit {proc.returncode}"
        if "refused" in first.lower() or "unable to connect" in first.lower() or "no such host" in first.lower():
            return False, first
        return True, ""  # the cluster answered; the object is simply not there
    return True, proc.stdout


def _unreachable(gid: str, why: str, fix: str) -> GuardResult:
    """The one honest verdict when there is no cluster to ask: unproven, never fine, never broken."""
    return GuardResult(
        gid, "DEGRADED",
        f"cluster unreachable ({why}); container isolation is UNPROVEN from this box",
        fix=fix,
    )


@guard("G-GVISOR", land="d'", spine=True)
def g_gvisor(_home: Path) -> GuardResult:
    """A pod naming RuntimeClass `gvisor` actually runs under runsc.

    Smoke-tested, not read. The RuntimeClass object existing proves only that someone typed it: if
    containerd has no `runsc` handler the object is still there and every class-3 pod stays Pending.
    The probe asks a running pod what kernel it sees -- gVisor answers with its own version string,
    and the host kernel does not.
    """
    reached, out = _kubectl("get", "runtimeclass", "gvisor", "-o", "jsonpath={.handler}")
    if not reached:
        return _unreachable(
            "G-GVISOR", out,
            fix="class 3 requires a reachable k3s cluster with the gVisor RuntimeClass; until then "
            "the fabric is bounded to class 1 (local process) -- apply deploy/k3s/sandbox.yaml",
        )
    if not out.strip():
        return GuardResult(
            "G-GVISOR", "RED",
            "no RuntimeClass named 'gvisor'; nothing can run at class 3",
            fix="kubectl apply -f deploy/k3s/sandbox.yaml, and add the runsc handler to containerd's "
            "config-v3.toml.tmpl on every node",
        )
    if out.strip() != "runsc":
        return GuardResult(
            "G-GVISOR", "RED",
            f"RuntimeClass 'gvisor' maps to handler '{out.strip()}', not runsc",
            fix="point the RuntimeClass at the runsc handler; a class-3 claim resting on a different "
            "runtime is a claim about a sandbox that is not there",
        )

    reached, uname = _kubectl(
        "run", "hypercell-gvisor-smoke", "-n", SANDBOX_NS, "--rm", "-i", "--restart=Never",
        "--overrides=" + json.dumps({"spec": {"runtimeClassName": "gvisor"}}),
        "--image=busybox", "--command", "--", "uname", "-r", timeout=60.0,
    )
    if not reached:
        return GuardResult(
            "G-GVISOR", "DEGRADED",
            "the RuntimeClass exists but the smoke pod could not be run; runsc is UNPROVEN",
            fix="run the smoke pod by hand and read the scheduling error: a RuntimeClass whose "
            "handler is missing from containerd fails every pod that names it",
        )
    if "gvisor" not in uname.lower():
        return GuardResult(
            "G-GVISOR", "RED",
            f"the smoke pod reports kernel '{uname.strip()[:60]}' -- that is the HOST kernel, not runsc",
            fix="the pod ran outside gVisor: fix containerd's runsc handler. Until the smoke pod "
            "reports a gVisor kernel, untrusted code has no sandbox",
        )
    return GuardResult("G-GVISOR", "GREEN", f"smoke pod ran under runsc ({uname.strip()[:40]})")


@guard("G-NETPOL-ENFORCED", land="d'", spine=True)
def g_netpol_enforced(_home: Path) -> GuardResult:
    """The deny-all NetworkPolicy exists AND the CNI enforces it.

    A NetworkPolicy is an object, not a firewall. On a cluster whose CNI ignores policy (flannel
    without a policy controller), every deny-all is decorative and every workload has full egress
    while the manifest says otherwise -- the most dangerous shape a control can take.
    """
    reached, out = _kubectl("get", "networkpolicy", "deny-all", "-n", SANDBOX_NS, "-o", "name")
    if not reached:
        return _unreachable(
            "G-NETPOL-ENFORCED", out,
            fix="apply deploy/k3s/sandbox.yaml and run a CNI that enforces NetworkPolicy; without "
            "enforcement the trifecta's egress leg is cut only on paper",
        )
    if not out.strip():
        return GuardResult(
            "G-NETPOL-ENFORCED", "RED",
            f"no deny-all NetworkPolicy in {SANDBOX_NS}; sandboxed workloads have full egress",
            fix="kubectl apply -f deploy/k3s/sandbox.yaml",
        )
    reached, probe = _kubectl(
        "run", "hypercell-netpol-smoke", "-n", SANDBOX_NS, "--rm", "-i", "--restart=Never",
        "--image=busybox", "--command", "--", "wget", "-T", "3", "-q", "-O-", "https://example.com",
        timeout=45.0,
    )
    if reached and probe.strip():
        return GuardResult(
            "G-NETPOL-ENFORCED", "RED",
            "a sandbox pod reached the public internet despite the deny-all policy; the CNI is "
            "not enforcing NetworkPolicy",
            fix="run a policy-enforcing CNI (k3s: --flannel-backend=none plus Calico, or enable the "
            "built-in policy controller); a deny-all nobody enforces is worse than none, because it "
            "is believed",
        )
    return GuardResult(
        "G-NETPOL-ENFORCED", "GREEN", "deny-all present and a probe pod could not reach the internet"
    )


@guard("G-ONE-RUNTIME", land="d'")
def g_one_runtime(_home: Path) -> GuardResult:
    """Exactly one container runtime on the node.

    Two runtimes means two answers to "what is running", and the one the preflight probed is not
    necessarily the one the kubelet used. The lived shape is a docker daemon left beside containerd:
    images build into one and pods run from the other, so a digest pin gates nothing.
    """
    reached, out = _kubectl("get", "nodes", "-o", "jsonpath={.items[*].status.nodeInfo.containerRuntimeVersion}")
    if not reached:
        return _unreachable(
            "G-ONE-RUNTIME", out,
            fix="with no cluster there is no runtime to disambiguate; class 3 stays unavailable",
        )
    runtimes = {r.split("://")[0] for r in out.split() if r}
    if len(runtimes) > 1:
        return GuardResult(
            "G-ONE-RUNTIME", "DEGRADED",
            f"nodes report multiple container runtimes: {sorted(runtimes)}",
            fix="standardise on containerd across every node; with two runtimes a digest pin gates "
            "only one of them and 'which build is running' has no single answer",
        )
    if not runtimes:
        return GuardResult(
            "G-ONE-RUNTIME", "DEGRADED", "no node reported a container runtime version",
            fix="check that nodes are Ready and reporting nodeInfo; an unreadable runtime is unproven",
        )
    return GuardResult("G-ONE-RUNTIME", "GREEN", f"one runtime across all nodes: {runtimes.pop()}")


@guard("G-FORWARD-ACCEPT", land="d'")
def g_forward_accept(_home: Path) -> GuardResult:
    """The host FORWARD chain does not default-ACCEPT.

    A default-ACCEPT FORWARD chain routes pod traffic around NetworkPolicy on some CNI paths: the
    policy is loaded, the packets do not traverse it. Docker sets this on install, which is why the
    check exists at all.
    """
    chains = Path("/proc/net/ip_tables_names")
    if not chains.exists():
        return GuardResult(
            "G-FORWARD-ACCEPT", "DEGRADED",
            f"no netfilter tables visible on {platform.system()}; FORWARD policy is UNPROVEN",
            fix="run the fabric on a Linux node and re-check `iptables -L FORWARD`; on a host whose "
            "FORWARD chain default-ACCEPTs, pod egress can bypass NetworkPolicy entirely",
        )
    exe = shutil.which("iptables")
    if exe is None:
        return GuardResult(
            "G-FORWARD-ACCEPT", "DEGRADED", "iptables not on PATH; FORWARD policy unproven",
            fix="install iptables (or nft with the iptables shim) so the preflight can read the "
            "FORWARD chain default",
        )
    try:
        proc = subprocess.run([exe, "-L", "FORWARD", "-n"], capture_output=True, text=True,
                              timeout=_KUBECTL_TIMEOUT_S, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return GuardResult(
            "G-FORWARD-ACCEPT", "DEGRADED", f"could not read the FORWARD chain: {exc}",
            fix="run the preflight with permission to read iptables (CAP_NET_ADMIN or root)",
        )
    out = proc.stdout or ""
    head = out.splitlines()[:1]
    policy = head[0] if head else ""

    if "policy ACCEPT" in policy:
        return GuardResult(
            "G-FORWARD-ACCEPT", "DEGRADED",
            "the host FORWARD chain default-ACCEPTs; pod egress may bypass NetworkPolicy",
            fix="set the FORWARD policy to DROP (docker sets ACCEPT on install) and let the CNI "
            "insert its own accept rules; otherwise the deny-all is routed around",
        )
    if "policy DROP" in policy and "cni" not in out.lower() and "flannel" not in out.lower():
        # The OTHER lived F4 shape, and the one PREFLIGHT-1 names: a bare `FORWARD DROP` with no CNI
        # accept rules under it does not harden the fabric, it severs it -- every pod-to-pod packet
        # dies and the symptom looks like an application bug for a day. Both directions of this
        # chain's misconfiguration are failures; only the causes differ.
        return GuardResult(
            "G-FORWARD-ACCEPT", "DEGRADED",
            "FORWARD default-DROPs with no CNI accept rules beneath it; pod networking is severed",
            fix="let the CNI install its FORWARD accept rules (restart the CNI daemonset), or the "
            "cluster drops every pod-to-pod packet while looking healthy from the control plane",
        )
    return GuardResult(
        "G-FORWARD-ACCEPT", "GREEN", f"FORWARD chain safe ({policy.strip()[:48] or 'policy read'})"
    )


@guard("G-IPTABLES-PRESENT", land="d'")
def g_iptables_present(_home: Path) -> GuardResult:
    """Netfilter tooling exists at all. Without it a CNI cannot program policy, so nothing enforces."""
    if shutil.which("iptables") or shutil.which("nft"):
        which = "iptables" if shutil.which("iptables") else "nft"
        return GuardResult("G-IPTABLES-PRESENT", "GREEN", f"netfilter tooling present ({which})")
    return GuardResult(
        "G-IPTABLES-PRESENT", "DEGRADED",
        f"neither iptables nor nft found on {platform.system()}; a CNI cannot program NetworkPolicy",
        fix="install iptables (or nftables); without netfilter the deny-all policy has nothing to "
        "compile down to and egress is unrestricted",
    )


@guard("G-IMAGE-IN-K3S", land="d'")
def g_image_in_k3s(_home: Path) -> GuardResult:
    """The sandbox image is present in the cluster's own image store, by DIGEST.

    A pod that has to pull at admission time depends on a registry being up and on the tag still
    meaning what it meant. Digest-pinned and pre-imported, the image a run uses is the image the
    run was verified against -- which is what makes "which build is running" answerable (E28).
    """
    reached, out = _kubectl("get", "nodes", "-o", "jsonpath={.items[*].status.images[*].names}")
    if not reached:
        return _unreachable(
            "G-IMAGE-IN-K3S", out,
            fix="import the digest-pinned sandbox image into the cluster store before running "
            "class-3 work (S9.4's nerdctl pipeline)",
        )
    if "sandbox-harness" not in out:
        return GuardResult(
            "G-IMAGE-IN-K3S", "DEGRADED",
            "no sandbox-harness image in the cluster image store; pods would pull at admission",
            fix="build and import the harness image by digest (nerdctl build + ctr images import), "
            "then pin the digest in deploy/k3s/sandbox.yaml",
        )
    if "sandbox-harness@sha256:" not in out:
        return GuardResult(
            "G-IMAGE-IN-K3S", "DEGRADED",
            "sandbox-harness is present but referenced by TAG, not digest",
            fix="pin the image by digest: a tag can be repointed under a running fleet, and then "
            "the build you verified is not the build that ran",
        )
    return GuardResult("G-IMAGE-IN-K3S", "GREEN", "digest-pinned sandbox-harness present in the store")


@guard("G-PVC-SURVIVES", land="d'", spine=True)
def g_pvc_survives(_home: Path) -> GuardResult:
    """The nucleus volume outlives its pod.

    A cell's nucleus IS its identity (the chained ledger). On an emptyDir-backed claim a pod restart
    silently resurrects the cell with an empty history -- exactly the empty-nucleus-under-live-identity
    corruption that resume REFUSES to accept. Cheaper to catch here than at 3am.
    """
    reached, out = _kubectl(
        "get", "pvc", "-A", "-o",
        "jsonpath={range .items[*]}{.metadata.name}={.spec.storageClassName} {end}",
    )
    if not reached:
        return _unreachable(
            "G-PVC-SURVIVES", out,
            fix="class 3 needs persistent nucleus volumes; with no cluster the fabric stays on local "
            "disk at class 1, which is honest and safe",
        )
    if not out.strip():
        return GuardResult(
            "G-PVC-SURVIVES", "RED",
            "no PersistentVolumeClaims found; a pod restart would resurrect cells with empty nuclei",
            fix="provision a real StorageClass (k3s: local-path) and bind each cell's nucleus to a "
            "PVC; an empty nucleus under a live claim-id is identity corruption, and resume refuses it",
        )
    if "=emptyDir" in out or "= " in out:
        return GuardResult(
            "G-PVC-SURVIVES", "RED",
            "a nucleus claim has no storage class; its data does not survive a pod restart",
            fix="bind every nucleus PVC to a persisting StorageClass -- the ledger is the cell's "
            "identity, and losing it is worse than losing the pod",
        )
    return GuardResult("G-PVC-SURVIVES", "GREEN", "nucleus claims are bound to persisting storage")
