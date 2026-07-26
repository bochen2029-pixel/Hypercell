"""RUN-M1 — manifest freeze (ARCHITECTURE §15; slice RE-2).

The bar: apply → mutate the yaml → resume runs under the FROZEN bytes and `hc verify` passes;
re-applying the mutated file under the same run_id is REFUSED.

The null is live behavior — re-read the file on every open. An operator editing `run.yaml` while a
run is parked silently changes the rules the run has already been playing by, and the certificate
then reports a single manifest that never existed as a whole.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from hypercell.conductor.manifest import (
    ManifestConflict,
    apply_file,
    digest,
    freeze,
    load_frozen,
    open_run,
    verify,
)

MANIFEST = """
run_id: ipv4-r2
goal: implement is_valid(s)
topology: tournament
termination:
  max_rounds: 3
  stable_k: 2
"""


@pytest.fixture
def manifest_file(tmp_path: Path) -> Path:
    p = tmp_path / "run.yaml"
    p.write_text(MANIFEST, encoding="utf-8")
    return p


# ---------------------------------------------------------------- the bar


def test_a_resume_runs_under_the_frozen_bytes(tmp_path: Path, manifest_file: Path) -> None:
    """The whole slice, in one test: mutate the file, reopen, get the ORIGINAL rules."""
    frozen = apply_file(tmp_path, manifest_file)
    assert frozen.data["termination"]["stable_k"] == 2

    manifest_file.write_text(MANIFEST.replace("stable_k: 2", "stable_k: 99"), encoding="utf-8")

    reopened = open_run(tmp_path, "ipv4-r2")
    assert reopened.data["termination"]["stable_k"] == 2, "the resume read the operator's edit"
    assert reopened.sha256 == frozen.sha256
    ok, why = verify(tmp_path, "ipv4-r2")
    assert ok, why


def test_re_applying_a_mutated_file_under_the_same_run_id_is_refused(
    tmp_path: Path, manifest_file: Path
) -> None:
    """Refused, not silently re-frozen and not merged — with both digests named."""
    apply_file(tmp_path, manifest_file)
    manifest_file.write_text(MANIFEST.replace("max_rounds: 3", "max_rounds: 30"), encoding="utf-8")

    with pytest.raises(ManifestConflict) as e:
        apply_file(tmp_path, manifest_file)
    assert "already frozen" in str(e.value)
    assert "a run IS its manifest" in str(e.value)


def test_re_applying_an_identical_file_is_idempotent(tmp_path: Path, manifest_file: Path) -> None:
    """Replaying a command must not be an error, or every retry becomes a decision."""
    first = apply_file(tmp_path, manifest_file)
    second = apply_file(tmp_path, manifest_file)
    assert first.sha256 == second.sha256 and first.frozen_at == second.frozen_at


# ---------------------------------------------------------------- what the digest covers


def test_the_digest_is_over_raw_bytes_not_the_parsed_structure(tmp_path: Path) -> None:
    """Two files that PARSE the same but read differently are different manifests to an auditor."""
    a = "run_id: r\ngoal: g\n"
    b = "goal: g\nrun_id: r\n"  # same mapping, different bytes
    assert yaml.safe_load(a) == yaml.safe_load(b)
    assert digest(a) != digest(b)

    freeze(tmp_path, "r", a)
    with pytest.raises(ManifestConflict):
        freeze(tmp_path, "r", b)


def test_a_comment_only_change_is_still_a_different_manifest(tmp_path: Path) -> None:
    """The operator's intent lives in the bytes, and a comment is intent."""
    freeze(tmp_path, "r", "run_id: r\ngoal: g\n")
    with pytest.raises(ManifestConflict):
        freeze(tmp_path, "r", "run_id: r\ngoal: g  # now with a rationale\n")


# ---------------------------------------------------------------- verify + edge cases


def test_verify_catches_an_edit_to_the_frozen_copy_itself(tmp_path: Path, manifest_file: Path) -> None:
    """Freezing is not a lock: someone can still edit the frozen file. verify() must see it."""
    apply_file(tmp_path, manifest_file)
    frozen = load_frozen(tmp_path, "ipv4-r2")
    assert frozen is not None

    from hypercell.conductor.manifest import frozen_path

    frozen_path(tmp_path, "ipv4-r2").write_text(MANIFEST + "\nsmuggled: true\n", encoding="utf-8")
    ok, why = verify(tmp_path, "ipv4-r2")
    assert not ok and "edited in place" in why


def test_opening_a_run_that_was_never_applied_is_refused(tmp_path: Path) -> None:
    with pytest.raises(ManifestConflict, match="apply it first"):
        open_run(tmp_path, "never-applied")


def test_a_manifest_without_a_run_id_cannot_be_frozen(tmp_path: Path) -> None:
    p = tmp_path / "bad.yaml"
    p.write_text("goal: g\n", encoding="utf-8")
    with pytest.raises(ManifestConflict, match="no run_id"):
        apply_file(tmp_path, p)


def test_two_run_ids_freeze_independently(tmp_path: Path) -> None:
    freeze(tmp_path, "a", "run_id: a\n")
    freeze(tmp_path, "b", "run_id: b\n")
    assert load_frozen(tmp_path, "a").data["run_id"] == "a"  # type: ignore[union-attr]
    assert load_frozen(tmp_path, "b").data["run_id"] == "b"  # type: ignore[union-attr]
