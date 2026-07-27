"""PREFLIGHT-1 + AS-GATE — the class-3 battery (slice S9.2).

**PREFLIGHT-1's bar:** inject each lived F4 failure (2nd containerd; `FORWARD DROP`; WSL2 idle-off;
missing RuntimeClass; image not in k3s ns) → the matching guard fires; and `G-GVISOR` /
`G-NETPOL-ENFORCED` require the **smoke/canary probe, not the declaration**.

**The null is v1's assume-and-flap** — a declared RuntimeClass trusted without a smoke pod, a
declared NetworkPolicy trusted unenforced. Both nulls are measured below: the declaration is
present and the thing it declares does not work, which is the most dangerous shape a control can
take because the manifest reads correct.

**AS-GATE's bar:** on stock k3s a `SandboxClaim` must bind a warm gVisor pod in **< 2 s** with a
surviving + snapshottable PVC to be adopted; until then the StatefulSet + ledger-fork mechanism
stands and the CRD is refused. Recorded every run — evidence-gated, never faith-gated.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from hypercell.substrate import k3s
from hypercell.substrate.as_gate import (
    BIND_BUDGET_S,
    AdoptionProbe,
    decide_backend,
    probe_sandbox_claim,
)
from hypercell.substrate.k3s import run_preflight
from hypercell.substrate.preflight import GUARDS, GuardResult

DPRIME = tuple(sorted(g.id for g in GUARDS.values() if g.land == "d'"))
MANIFEST = Path("deploy/k3s/sandbox.yaml")


def _fake_kubectl(monkeypatch: pytest.MonkeyPatch, responses: dict[str, tuple[bool, str]]) -> None:
    """Replace the cluster with a scripted one. Keyed by the first distinguishing argument."""
    def fake(*args: str, timeout: float = 10.0) -> tuple[bool, str]:
        key = next((a for a in args if a in responses), None)
        return responses.get(key or "", (True, ""))
    monkeypatch.setattr(k3s, "_kubectl", fake)


# ================================================================ the battery exists


def test_the_d_prime_battery_registers_all_seven_guards() -> None:
    assert DPRIME == (
        "G-FORWARD-ACCEPT", "G-GVISOR", "G-IMAGE-IN-K3S", "G-IPTABLES-PRESENT",
        "G-NETPOL-ENFORCED", "G-ONE-RUNTIME", "G-PVC-SURVIVES",
    )


def test_every_non_green_guard_carries_an_operator_fix() -> None:
    """A guard that reports a problem without a fix has told the operator they are stuck."""
    with pytest.raises(ValueError, match="no operator fix"):
        GuardResult("G-TEST", "RED", "something is broken")


def test_the_isolation_guards_are_spine() -> None:
    """Spine guards HALT the fabric on RED. gVisor, the deny-all and the nucleus volume each
    caused a lived corruption or would let untrusted code out — 'continue anyway' is not offered."""
    spine = {g.id for g in GUARDS.values() if g.land == "d'" and g.spine}
    assert spine == {"G-GVISOR", "G-NETPOL-ENFORCED", "G-PVC-SURVIVES"}


# ================================================================ the null: assume-and-flap


def test_the_null_trusts_a_declared_runtimeclass_that_does_not_work(monkeypatch) -> None:
    """v1's shape: the RuntimeClass object exists, so v1 called it good. The smoke pod then runs on
    the HOST kernel and nothing notices — a class-3 claim with no sandbox under it."""
    _fake_kubectl(monkeypatch, {
        "runtimeclass": (True, "runsc"),                       # declared, correctly
        "run": (True, "5.15.0-91-generic\n"),                  # ...but the pod sees the host kernel
    })
    result = k3s.g_gvisor(Path("."))
    assert result.state == "RED", "the declaration was trusted without the smoke pod"
    assert "HOST kernel" in result.detail


def test_the_null_trusts_a_declared_netpol_that_is_not_enforced(monkeypatch) -> None:
    """The policy object exists; the CNI ignores it. The manifest reads correct and every workload
    has full egress — which is worse than no policy, because this one is believed."""
    _fake_kubectl(monkeypatch, {
        "networkpolicy": (True, "networkpolicy.networking.k8s.io/deny-all"),
        "run": (True, "<html>example</html>"),                 # the probe pod reached the internet
    })
    result = k3s.g_netpol_enforced(Path("."))
    assert result.state == "RED"
    assert "not enforcing NetworkPolicy" in result.detail
    assert "worse than none, because it is believed" in result.fix


def test_gvisor_green_requires_the_smoke_pod_to_report_gvisor(monkeypatch) -> None:
    _fake_kubectl(monkeypatch, {
        "runtimeclass": (True, "runsc"),
        "run": (True, "4.4.0 gVisor 20260716.0\n"),
    })
    assert k3s.g_gvisor(Path(".")).state == "GREEN"


def test_netpol_green_requires_the_canary_to_fail_to_reach_out(monkeypatch) -> None:
    _fake_kubectl(monkeypatch, {
        "networkpolicy": (True, "networkpolicy.networking.k8s.io/deny-all"),
        "run": (True, ""),                                     # the probe got nothing: policy holds
    })
    assert k3s.g_netpol_enforced(Path(".")).state == "GREEN"


# ================================================================ the lived F4 failures, injected


def test_f4_missing_runtimeclass_fires_g_gvisor(monkeypatch) -> None:
    _fake_kubectl(monkeypatch, {"runtimeclass": (True, "")})
    result = k3s.g_gvisor(Path("."))
    assert result.state == "RED" and "no RuntimeClass" in result.detail


def test_f4_a_runtimeclass_pointing_at_the_wrong_handler_fires(monkeypatch) -> None:
    _fake_kubectl(monkeypatch, {"runtimeclass": (True, "runc")})
    result = k3s.g_gvisor(Path("."))
    assert result.state == "RED" and "not runsc" in result.detail


def test_f4_a_second_containerd_fires_g_one_runtime(monkeypatch) -> None:
    """Two runtimes: images build into one and pods run from the other, so a digest pin gates
    nothing and 'which build is running' has no single answer."""
    _fake_kubectl(monkeypatch, {"nodes": (True, "containerd://1.7.11 docker://24.0.7")})
    result = k3s.g_one_runtime(Path("."))
    assert result.state == "DEGRADED" and "multiple container runtimes" in result.detail


def test_f4_image_not_in_the_k3s_namespace_fires(monkeypatch) -> None:
    _fake_kubectl(monkeypatch, {"nodes": (True, "docker.io/library/busybox:latest")})
    result = k3s.g_image_in_k3s(Path("."))
    assert result.state == "DEGRADED" and "no sandbox-harness image" in result.detail


def test_f4_an_image_pinned_by_tag_not_digest_fires(monkeypatch) -> None:
    """A tag can be repointed under a running fleet, and then the build you verified is not the
    build that ran (E28)."""
    _fake_kubectl(monkeypatch, {"nodes": (True, "hypercell/sandbox-harness:latest")})
    result = k3s.g_image_in_k3s(Path("."))
    assert result.state == "DEGRADED" and "TAG, not digest" in result.detail


def test_f4_an_emptydir_backed_nucleus_claim_fires_g_pvc_survives(monkeypatch) -> None:
    """A cell's nucleus IS its identity. On a volume that does not survive a restart the cell is
    resurrected empty — the exact corruption resume refuses to accept."""
    _fake_kubectl(monkeypatch, {"pvc": (True, "nucleus-r1=emptyDir ")})
    result = k3s.g_pvc_survives(Path("."))
    assert result.state == "RED" and "does not survive" in result.detail


def test_f4_no_pvcs_at_all_fires(monkeypatch) -> None:
    _fake_kubectl(monkeypatch, {"pvc": (True, "")})
    assert k3s.g_pvc_survives(Path(".")).state == "RED"


def test_f4_forward_drop_with_no_cni_rules_fires(monkeypatch, tmp_path: Path) -> None:
    """The lived F4 PREFLIGHT-1 names: a bare `FORWARD DROP` severs pod networking while the
    control plane still looks healthy."""
    monkeypatch.setattr(k3s.shutil, "which", lambda _n: "/sbin/iptables")
    monkeypatch.setattr(k3s.Path, "exists", lambda self: True)

    class _Proc:
        stdout = "Chain FORWARD (policy DROP)\ntarget  prot opt source  destination\n"

    monkeypatch.setattr(k3s.subprocess, "run", lambda *a, **k: _Proc())
    result = k3s.g_forward_accept(Path("."))
    assert result.state == "DEGRADED" and "severed" in result.detail


def test_forward_accept_fires_as_a_policy_bypass(monkeypatch) -> None:
    monkeypatch.setattr(k3s.shutil, "which", lambda _n: "/sbin/iptables")
    monkeypatch.setattr(k3s.Path, "exists", lambda self: True)

    class _Proc:
        stdout = "Chain FORWARD (policy ACCEPT)\n"

    monkeypatch.setattr(k3s.subprocess, "run", lambda *a, **k: _Proc())
    result = k3s.g_forward_accept(Path("."))
    assert result.state == "DEGRADED" and "bypass NetworkPolicy" in result.detail


# ================================================================ unreachable is not absent


def test_an_unreachable_cluster_is_unproven_never_broken(monkeypatch) -> None:
    """The distinction the whole battery rests on: 'we cannot ask' is DEGRADED (unproven), not RED
    (broken) and never GREEN (fine). A missing kubectl is not a missing gVisor."""
    _fake_kubectl(monkeypatch, {
        "runtimeclass": (False, "kubectl not on PATH"),
        "networkpolicy": (False, "kubectl not on PATH"),
        "nodes": (False, "connection refused"),
        "pvc": (False, "connection refused"),
    })
    for fn in (k3s.g_gvisor, k3s.g_netpol_enforced, k3s.g_one_runtime, k3s.g_pvc_survives):
        result = fn(Path("."))
        assert result.state == "DEGRADED", f"{result.id} reported {result.state} for an absent cluster"
        assert "UNPROVEN" in result.detail or "unreachable" in result.detail


# ================================================================ the honest class ladder


def _results(states: dict[str, str]) -> dict[str, GuardResult]:
    return {
        gid: GuardResult(gid, st, "d", fix="f" if st != "GREEN" else "")
        for gid, st in states.items()
    }


def test_no_cluster_means_class_1_not_class_2() -> None:
    """The subtle honesty: reading an unreachable cluster as 'container isolation, just not gVisor'
    would invent a containment boundary out of a missing binary."""
    all_unproven = _results(dict.fromkeys(DPRIME, "DEGRADED"))
    assert k3s._honest_class(all_unproven) == 1


def test_containers_without_gvisor_is_class_2() -> None:
    states = dict.fromkeys(DPRIME, "GREEN")
    states["G-GVISOR"] = "DEGRADED"
    assert k3s._honest_class(_results(states)) == 2


def test_everything_green_is_class_3() -> None:
    assert k3s._honest_class(_results(dict.fromkeys(DPRIME, "GREEN"))) == 3


def test_an_unenforced_netpol_drops_below_class_3() -> None:
    """Untrusted code with egress is not contained, whatever the runtime says."""
    states = dict.fromkeys(DPRIME, "GREEN")
    states["G-NETPOL-ENFORCED"] = "RED"
    assert k3s._honest_class(_results(states)) < 3


def test_this_box_claims_no_more_than_it_can_prove() -> None:
    """The real battery on the real machine. With no cluster the honest answer is class 1."""
    report = run_preflight(".hypercellstate", lands=("a'", "d'"))
    assert report.max_honest_sandbox_class <= 1, (
        f"claimed class {report.max_honest_sandbox_class} with no cluster present"
    )
    assert report.verdict in ("DEGRADED", "RED")


def test_the_a_prime_land_alone_still_reports_class_1() -> None:
    report = run_preflight(".hypercellstate", lands=("a'",))
    assert report.max_honest_sandbox_class == 1


# ================================================================ AS-GATE


def test_a_fast_bind_with_a_surviving_snapshottable_pvc_is_adopted() -> None:
    probe = AdoptionProbe(bind_s=0.8, pvc_survives=True, pvc_snapshottable=True)
    assert probe.adopted and decide_backend(probe).backend == "sandboxclaim-crd"


def test_a_slow_bind_refuses_the_crd() -> None:
    probe = AdoptionProbe(bind_s=BIND_BUDGET_S + 0.01, pvc_survives=True, pvc_snapshottable=True)
    assert not probe.adopted
    assert decide_backend(probe).backend == "statefulset+ledger-fork"
    assert "over the" in probe.reason


@pytest.mark.parametrize("survives,snapshot", [(False, True), (True, False), (False, False)])
def test_a_pvc_that_fails_either_clause_refuses_the_crd(survives: bool, snapshot: bool) -> None:
    """Any one clause failing is a refusal, not a caveat: a claim backend whose volumes do not
    survive is a backend that loses nuclei."""
    probe = AdoptionProbe(bind_s=0.5, pvc_survives=survives, pvc_snapshottable=snapshot)
    assert not probe.adopted and decide_backend(probe).backend == "statefulset+ledger-fork"


def test_the_null_adopting_before_the_probe_is_refused() -> None:
    """With no cluster there is no evidence, so there is no adoption. An absent cluster must never
    read as a passing probe."""
    probe = probe_sandbox_claim(runner=None)
    assert not probe.reached and not probe.adopted
    assert decide_backend(probe).backend == "statefulset+ledger-fork"
    assert "unproven" in probe.reason


def test_the_gate_records_its_evidence_every_run() -> None:
    """Evidence-gated, never faith-gated: the decision carries the numbers it rests on, so a cluster
    that qualified in March and regressed in July stops qualifying in July."""
    record = decide_backend(AdoptionProbe(bind_s=1.2, pvc_survives=True, pvc_snapshottable=True))
    body = record.as_body()
    assert body["adopted"] and body["bind_s"] == 1.2 and body["bar_s"] == BIND_BUDGET_S
    assert body["backend"] == "sandboxclaim-crd" and body["reason"]


# ================================================================ the manifests


def _docs() -> list[dict]:
    return [d for d in yaml.safe_load_all(MANIFEST.read_text(encoding="utf-8")) if d]


def test_the_sandbox_manifest_declares_the_three_mechanisms() -> None:
    kinds = {d["kind"] for d in _docs()}
    assert {"RuntimeClass", "NetworkPolicy", "Namespace", "Pod"} <= kinds


def test_the_runtimeclass_points_at_runsc() -> None:
    rc = next(d for d in _docs() if d["kind"] == "RuntimeClass")
    assert rc["handler"] == "runsc"


def test_the_netpol_denies_both_directions_for_every_pod() -> None:
    """An empty podSelector matches every pod; naming both policy types with no rules denies both."""
    np = next(d for d in _docs() if d["kind"] == "NetworkPolicy")
    assert np["spec"]["podSelector"] == {}
    assert set(np["spec"]["policyTypes"]) == {"Ingress", "Egress"}
    assert "ingress" not in np["spec"] and "egress" not in np["spec"]


def test_the_namespace_enforces_restricted_pss_not_merely_warns() -> None:
    """A namespace that only WARNS about privileged pods is a namespace that runs them."""
    ns = next(d for d in _docs() if d["kind"] == "Namespace")
    assert ns["metadata"]["labels"]["pod-security.kubernetes.io/enforce"] == "restricted"


def test_the_pod_template_is_hardened_and_digest_pinned() -> None:
    pod = next(d for d in _docs() if d["kind"] == "Pod")
    spec = pod["spec"]
    assert spec["runtimeClassName"] == "gvisor"
    assert spec["automountServiceAccountToken"] is False
    assert spec["securityContext"]["runAsNonRoot"] is True

    container = spec["containers"][0]
    sec = container["securityContext"]
    assert sec["allowPrivilegeEscalation"] is False
    assert sec["readOnlyRootFilesystem"] is True
    assert sec["capabilities"]["drop"] == ["ALL"]
    assert "@sha256:" in container["image"], "the sandbox image is not digest-pinned"


def test_only_out_and_tmp_are_writable() -> None:
    """A writable root would let a candidate hide bytes outside the seal, and the seal is what makes
    differential re-attribution sound."""
    pod = next(d for d in _docs() if d["kind"] == "Pod")
    mounts = {m["mountPath"] for m in pod["spec"]["containers"][0]["volumeMounts"]}
    assert mounts == {"/out", "/tmp"}
    assert all("emptyDir" in v for v in pod["spec"]["volumes"])
