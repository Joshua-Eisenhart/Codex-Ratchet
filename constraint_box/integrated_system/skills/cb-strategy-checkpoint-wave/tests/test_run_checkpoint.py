from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT.parent
sys.path.insert(0, str(ROOT))

from scripts.run_checkpoint import (  # noqa: E402
    CHILD_IDS,
    DISPOSITIONS,
    PRECEDENCE,
    run_packet,
    verify_integrity,
    verify_receipt,
)
import scripts.run_checkpoint as runner  # noqa: E402


FIXTURE = ROOT / "fixtures" / "positive_packet.json"
RUNNER = ROOT / "scripts" / "run_checkpoint.py"


def packet() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_positive_runs_four_distinct_children_and_is_model_free() -> None:
    value = run_packet(packet(), skills_root=SKILLS_ROOT)
    assert value["status"] == "COMPLETE"
    assert value["checkpoint_disposition"] == "reject_local_optimum"
    assert value["child_order"] == list(CHILD_IDS)
    assert value["launched_child_order"] == list(CHILD_IDS)
    assert value["not_launched_child_ids"] == []
    assert set(value["child_receipts"]) == set(CHILD_IDS)
    assert len({row["operation"] for row in value["children"]}) == 4
    assert value["route_truth_label"] == "NOT_FULL/model_free"
    assert value["model_free"] is True
    assert value["mmm_preload_applicable"] is False
    assert value["provider_receipt_applicable"] is False
    assert value["provider_call_receipt"] is None
    assert value["mmm_preload_receipts"] == []
    assert value["promotion_allowed"] is False
    assert value["winner_selected"] is False
    assert value["voting_performed"] is False
    assert value["expected_source_set_sha256"] == runner.source_set_sha256(SKILLS_ROOT)
    assert value["source_set_sha256"] == value["expected_source_set_sha256"]
    assert verify_receipt(value, packet(), skills_root=SKILLS_ROOT)
    integrity = verify_integrity(value, skills_root=SKILLS_ROOT)
    assert integrity["integrity_valid"] is True
    assert integrity["semantic_verified"] is False
    assert integrity["decision_claim"] is None


def test_exact_replay_is_byte_stable() -> None:
    assert run_packet(packet(), skills_root=SKILLS_ROOT) == run_packet(copy.deepcopy(packet()), skills_root=SKILLS_ROOT)


def test_precedence_is_explicit_and_owner_boundary_wins() -> None:
    value = run_packet(packet(), skills_root=SKILLS_ROOT)
    assert value["disposition_precedence"] == list(PRECEDENCE)
    changed = packet()
    candidate = ROOT / "fixtures" / "candidate_receipt.json"
    # The fixture is source-bound; a mutation of the source is a refusal, not
    # an invented owner amendment.  The table itself remains inspectable.
    assert value["checkpoint_disposition"] in DISPOSITIONS
    assert candidate.is_file()


def test_parent_cancellation_is_terminal_and_does_not_launch_children() -> None:
    value = packet()
    value["cancel_requested"] = True
    receipt = run_packet(value, skills_root=SKILLS_ROOT)
    assert receipt["status"] == "CANCELLED"
    assert receipt["checkpoint_disposition"] == "cancelled"
    assert receipt["cancellation_state"] == "CANCELLED"
    assert receipt["children"] == []
    assert receipt["launched_child_order"] == []
    assert receipt["not_launched_child_ids"] == list(CHILD_IDS)
    assert verify_receipt(receipt, value, skills_root=SKILLS_ROOT)


def test_missing_rebound_and_tampered_child_inputs_refuse_before_launch() -> None:
    missing = packet()
    del missing["child_inputs"]["recency"]
    result = run_packet(missing, skills_root=SKILLS_ROOT)
    assert result["status"] == "REFUSE"
    assert result["launched_child_order"] == []

    rebound = packet()
    rebound["child_inputs"]["expansion"]["target_id"] = "other-target"
    result = run_packet(rebound, skills_root=SKILLS_ROOT)
    assert result["status"] == "REFUSE"
    assert "REBOUND" in str(result["reason"])

    tampered = packet()
    tampered["child_inputs"]["repair_vs_object"]["evidence"] = ["metric"]
    result = run_packet(tampered, skills_root=SKILLS_ROOT)
    assert result["status"] == "REFUSE"
    assert result["launched_child_order"] == []


def test_path_escape_and_artifact_source_drift_fail_closed() -> None:
    escaped = packet()
    escaped["before_repair"]["path"] = "../outside.json"
    result = run_packet(escaped, skills_root=SKILLS_ROOT)
    assert result["status"] == "REFUSE"
    assert "PATH_ESCAPE" in str(result["reason"])

    drifted = packet()
    drifted["after_repair"]["sha256"] = "0" * 64
    result = run_packet(drifted, skills_root=SKILLS_ROOT)
    assert result["status"] == "REFUSE"
    assert "SOURCE_DRIFT" in str(result["reason"])


def test_child_and_definition_source_drift_fail_closed() -> None:
    temp = SKILLS_ROOT / ".test-source-copy"
    if temp.exists():
        shutil.rmtree(temp)
    try:
        shutil.copytree(SKILLS_ROOT, temp)
        child_source = temp / "cb-impact-vs-output-auditor" / "scripts" / "classify.py"
        child_source.write_text(child_source.read_text(encoding="utf-8") + "\n# source drift\n", encoding="utf-8")
        result = run_packet(packet(), skills_root=temp)
        assert result["status"] == "REFUSE"
        assert "SOURCE" in str(result["reason"])

        shutil.rmtree(temp)
        shutil.copytree(SKILLS_ROOT, temp)
        definition = temp / ROOT.name / "wave.json"
        value = json.loads(definition.read_text(encoding="utf-8"))
        value["purpose"] = "changed"
        definition.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")
        result = run_packet(packet(), skills_root=temp)
        assert result["status"] == "REFUSE"
        assert "SOURCE_SET_DRIFT" in str(result["reason"])
    finally:
        if temp.exists():
            shutil.rmtree(temp)


def test_recency_flip_without_evidence_refuses() -> None:
    # The projection is sealed on disk, so use a copied skill tree and alter
    # both projection file and packet binding.  The child then sees a real
    # flip with no causal evidence and the parent fails closed.
    temp = SKILLS_ROOT / ".test-recency-copy"
    if temp.exists():
        shutil.rmtree(temp)
    try:
        shutil.copytree(SKILLS_ROOT, temp)
        candidate_root = temp / ROOT.name
        current = candidate_root / "fixtures" / "current_projection.json"
        value = json.loads(current.read_text(encoding="utf-8"))
        value["decision"] = "stop"
        unsigned = {key: item for key, item in value.items() if key != "projection_sha256"}
        import hashlib

        value["projection_sha256"] = hashlib.sha256(json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()
        current.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        changed = packet()
        changed["current_projection"]["sha256"] = hashlib.sha256(current.read_bytes()).hexdigest()
        changed["child_inputs"]["recency"]["current"] = value
        changed["child_inputs"]["recency"]["causal_evidence"] = None
        result = run_packet(changed, skills_root=temp)
        assert result["status"] == "REFUSE"
        assert "RECENCY_FLIP" in str(result["reason"])
    finally:
        if temp.exists():
            shutil.rmtree(temp)


def test_parent_tamper_is_detected() -> None:
    receipt = run_packet(packet(), skills_root=SKILLS_ROOT)
    altered = copy.deepcopy(receipt)
    altered["checkpoint_disposition"] = "continue_candidate"
    assert not verify_receipt(altered, packet(), skills_root=SKILLS_ROOT)


def _reseal(value: dict) -> dict:
    unsigned = copy.deepcopy(value)
    unsigned.pop("receipt_sha256", None)
    unsigned.pop("receipt_self_sha256", None)
    raw = json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    import hashlib

    value["receipt_sha256"] = hashlib.sha256(raw).hexdigest()
    value["receipt_self_sha256"] = value["receipt_sha256"]
    return value


def test_forged_refuse_and_cancel_cannot_verify_against_exact_packet() -> None:
    positive = packet()
    actual = run_packet(positive, skills_root=SKILLS_ROOT)

    forged_refuse = copy.deepcopy(actual)
    forged_refuse.update(
        {
            "status": "REFUSE",
            "reason": "forged",
            "checkpoint_disposition": None,
            "disposition": None,
            "disposition_reason": None,
            "children": [],
            "child_receipts": {},
            "findings": {},
            "launched_child_order": [],
            "not_launched_child_ids": list(CHILD_IDS),
            "decision_flags": {},
        }
    )
    assert not verify_receipt(_reseal(forged_refuse), positive, skills_root=SKILLS_ROOT)

    forged_cancel = copy.deepcopy(actual)
    forged_cancel.update(
        {
            "status": "CANCELLED",
            "reason": "forged",
            "checkpoint_disposition": "cancelled",
            "disposition": "cancelled",
            "disposition_reason": "CANCELLATION_REQUESTED",
            "cancellation_state": "CANCELLED",
            "children": [],
            "child_receipts": {},
            "findings": {},
            "launched_child_order": [],
            "not_launched_child_ids": list(CHILD_IDS),
            "decision_flags": {},
        }
    )
    assert not verify_receipt(_reseal(forged_cancel), positive, skills_root=SKILLS_ROOT)
    cancelled_packet = copy.deepcopy(positive)
    cancelled_packet["cancel_requested"] = True
    assert not verify_receipt(_reseal(forged_cancel), cancelled_packet, skills_root=SKILLS_ROOT)


def test_packet_bound_hashes_and_immutable_candidate_flags_are_checked() -> None:
    value = run_packet(packet(), skills_root=SKILLS_ROOT)
    for field in (
        "context_epoch_digest",
        "branch_memory_snapshot_sha256",
        "current_projection_sha256",
        "ablated_projection_sha256",
    ):
        altered = copy.deepcopy(value)
        altered[field] = "0" * 64
        assert not verify_receipt(_reseal(altered), packet(), skills_root=SKILLS_ROOT)
        assert verify_integrity(_reseal(copy.deepcopy(altered)), skills_root=SKILLS_ROOT)["integrity_valid"] is False
    altered = copy.deepcopy(value)
    altered["candidate_state"] = "NEW_CANDIDATE"
    assert not verify_receipt(_reseal(altered), packet(), skills_root=SKILLS_ROOT)
    altered = copy.deepcopy(value)
    altered["promotion_allowed"] = True
    assert not verify_receipt(_reseal(altered), packet(), skills_root=SKILLS_ROOT)


def test_no_packet_never_makes_a_semantic_or_routing_claim_and_integrity_is_exact() -> None:
    value = run_packet(packet(), skills_root=SKILLS_ROOT)
    assert verify_receipt(value, skills_root=SKILLS_ROOT) is False

    forged = copy.deepcopy(value)
    forged["status"] = "REFUSE"
    forged["checkpoint_disposition"] = None
    forged["disposition"] = None
    forged["disposition_reason"] = None
    forged["children"] = []
    forged["child_receipts"] = {}
    forged["findings"] = {}
    forged["launched_child_order"] = []
    forged["not_launched_child_ids"] = list(CHILD_IDS)
    forged["decision_flags"] = {}
    forged = _reseal(forged)
    assert verify_receipt(forged, skills_root=SKILLS_ROOT) is False
    assert verify_integrity(forged, skills_root=SKILLS_ROOT)["integrity_valid"] is True

    unknown = copy.deepcopy(value)
    unknown["unreviewed_metadata"] = "must refuse"
    unknown = _reseal(unknown)
    assert verify_integrity(unknown, skills_root=SKILLS_ROOT)["integrity_valid"] is False


def test_source_set_timing_drift_is_not_baselined_after_entry(monkeypatch) -> None:
    calls: list[int] = []
    original = runner._assert_expected_source_set

    def drift_after_entry(root, expected):
        calls.append(1)
        if len(calls) == 2:
            raise runner.CandidateRefusal("REFUSE_SOURCE_SET_DRIFT")
        return original(root, expected)

    monkeypatch.setattr(runner, "_assert_expected_source_set", drift_after_entry)
    result = run_packet(packet(), skills_root=SKILLS_ROOT)
    assert result["status"] == "REFUSE"
    assert result["reason"] == "REFUSE_SOURCE_SET_DRIFT"
    assert result["launched_child_order"] == []


def test_copied_root_runner_is_confined_and_mutated_rebound_is_explicit(tmp_path: Path) -> None:
    temp = SKILLS_ROOT / ".test-runner-copy"
    if temp.exists():
        shutil.rmtree(temp)
    try:
        shutil.copytree(SKILLS_ROOT, temp)
        clean = run_packet(packet(), skills_root=temp)
        assert clean["status"] == "COMPLETE"
        import hashlib

        copied_runner = temp / ROOT.name / "scripts" / "run_checkpoint.py"
        copied_runner.write_text(copied_runner.read_text(encoding="utf-8") + "\n# copied runner mutation\n", encoding="utf-8")
        stale = run_packet(packet(), skills_root=temp)
        assert stale["status"] == "REFUSE"
        assert "SOURCE_SET" in str(stale["reason"])

        rebound = packet()
        rebound["expected_source_set_sha256"] = runner.source_set_sha256(temp)
        supplied = run_packet(rebound, skills_root=temp)
        assert supplied["status"] == "COMPLETE"
        assert supplied["source_hashes"]["runner"] == hashlib.sha256(copied_runner.read_bytes()).hexdigest()
        assert supplied["source_hashes"]["runner"] != hashlib.sha256((ROOT / "scripts" / "run_checkpoint.py").read_bytes()).hexdigest()
        assert verify_receipt(supplied, rebound, skills_root=temp)
    finally:
        if temp.exists():
            shutil.rmtree(temp)


def test_cli_normalizes_delegated_runner_exception_without_traceback(tmp_path: Path) -> None:
    copied_root = tmp_path / "skills"
    shutil.copytree(SKILLS_ROOT, copied_root)
    copied_runner = copied_root / ROOT.name / "scripts" / "run_checkpoint.py"
    original = copied_runner.read_text(encoding="utf-8")
    marker = '        root = _skills_root(skills_root)\n        delegated = _delegate_runner(root, "run_packet")'
    assert marker in original
    copied_runner.write_text(
        original.replace(marker, '        raise RuntimeError("delegated identity leak")\n' + marker, 1),
        encoding="utf-8",
    )
    output = tmp_path / "refusal.json"
    process = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--packet",
            str(FIXTURE),
            "--root",
            str(copied_root),
            "--out",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert process.returncode == 2
    assert process.stderr == ""
    summary = json.loads(process.stdout)
    assert summary["status"] == "REFUSE"
    assert "SUPPLIED_RUNNER_EXCEPTION" in summary["reason"]
    receipt = json.loads(output.read_text(encoding="utf-8"))
    assert receipt["status"] == "REFUSE"
    assert "SUPPLIED_RUNNER_EXCEPTION" in receipt["reason"]


def test_cli_normalizes_delegated_candidate_refusal_class_identity(tmp_path: Path) -> None:
    copied_root = tmp_path / "skills"
    shutil.copytree(SKILLS_ROOT, copied_root)
    copied_runner = copied_root / ROOT.name / "scripts" / "run_checkpoint.py"
    original = copied_runner.read_text(encoding="utf-8")
    marker = 'def run_packet(packet: Any, *, skills_root: Path | None = None) -> dict[str, Any]:\n    root: Path | None = None'
    copied_runner.write_text(
        original.replace(marker, marker.split("\n", 1)[0] + '\n    raise CandidateRefusal("delegated class identity leak")\n    root: Path | None = None', 1),
        encoding="utf-8",
    )
    process = subprocess.run(
        [sys.executable, str(RUNNER), "--packet", str(FIXTURE), "--root", str(copied_root)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert process.returncode == 2
    assert process.stderr == ""
    summary = json.loads(process.stdout)
    assert summary["status"] == "REFUSE"
    assert summary["reason"] == "REFUSE_SUPPLIED_RUNNER_DELEGATED"


def test_cli_normalizes_delegated_prewrite_exception_without_traceback(tmp_path: Path) -> None:
    copied_root = tmp_path / "skills"
    shutil.copytree(SKILLS_ROOT, copied_root)
    copied_runner = copied_root / ROOT.name / "scripts" / "run_checkpoint.py"
    original = copied_runner.read_text(encoding="utf-8")
    marker = '    root = _skills_root(skills_root)\n    delegated = _delegate_runner(root, "_prewrite_attest")'
    assert marker in original
    copied_runner.write_text(
        original.replace(marker, '    raise RuntimeError("delegated prewrite leak")\n' + marker, 1),
        encoding="utf-8",
    )
    rebound = packet()
    rebound["expected_source_set_sha256"] = runner.source_set_sha256(copied_root)
    packet_path = tmp_path / "packet.json"
    packet_path.write_text(json.dumps(rebound, sort_keys=True) + "\n", encoding="utf-8")
    output = tmp_path / "refusal.json"
    process = subprocess.run(
        [sys.executable, str(RUNNER), "--packet", str(packet_path), "--root", str(copied_root), "--out", str(output)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert process.returncode == 2
    assert process.stderr == ""
    summary = json.loads(process.stdout)
    assert summary["status"] == "REFUSE"
    assert "SUPPLIED_RUNNER_EXCEPTION:_prewrite_attest:RuntimeError" in summary["reason"]
    receipt = json.loads(output.read_text(encoding="utf-8"))
    assert receipt["status"] == "REFUSE"
    assert "SUPPLIED_RUNNER_EXCEPTION:_prewrite_attest:RuntimeError" in receipt["reason"]


def test_source_attestation_runs_before_each_child_and_preserves_prefix(monkeypatch) -> None:
    calls: list[int] = []
    original = runner._assert_source_attestation

    def wrapped(*args, **kwargs):
        calls.append(1)
        return original(*args, **kwargs)

    monkeypatch.setattr(runner, "_assert_source_attestation", wrapped)
    result = run_packet(packet(), skills_root=SKILLS_ROOT)
    assert result["status"] == "COMPLETE"
    assert len(calls) == (2 * len(CHILD_IDS)) + 3

    calls.clear()

    def drift_on_second(*args, **kwargs):
        calls.append(1)
        if len(calls) == 2:
            raise runner.CandidateRefusal("REFUSE_SOURCE_DRIFT")
        return original(*args, **kwargs)

    monkeypatch.setattr(runner, "_assert_source_attestation", drift_on_second)
    result = run_packet(packet(), skills_root=SKILLS_ROOT)
    assert result["status"] == "REFUSE"
    assert result["reason"] == "REFUSE_SOURCE_DRIFT"
    assert result["launched_child_order"] == [CHILD_IDS[0]]
    assert [row["child_id"] for row in result["children"]] == [CHILD_IDS[0]]
    assert result["not_launched_child_ids"] == list(CHILD_IDS[1:])


def test_numeric_repair_causality_ignores_candidate_label_and_handles_ties() -> None:
    value = run_packet(packet(), skills_root=SKILLS_ROOT)
    assert value["decision_flags"]["repair_causality"] == "proxy_severance"
    assert value["checkpoint_disposition"] == "reject_local_optimum"
    assert value["candidate_state"] == "INACTIVE"

    flags = {
        "owner_amendment_needed": True,
        "repair_regressed": True,
        "split_target": True,
        "recency_flip": True,
        "older_rival_dominates": True,
        "scope_expanded": True,
        "sunk_cost_defense": True,
        "stop_better": True,
    }
    assert runner._compile_disposition(flags) == "request_owner_amendment"
    assert runner._compile_disposition(flags, cancelled=True) == "cancelled"
    flags["owner_amendment_needed"] = False
    assert runner._compile_disposition(flags) == "revert_repair"
    flags["repair_regressed"] = False
    assert runner._compile_disposition(flags) == "split_target"


def test_trusted_definition_tree_validator_passes() -> None:
    validator = SKILLS_ROOT / "cb-wave-author" / "scripts" / "validate_wave.py"
    import subprocess

    process = subprocess.run(
        [sys.executable, str(validator), str(ROOT / "wave.json")],
        check=False,
        capture_output=True,
        text=True,
    )
    assert process.returncode == 0
    assert json.loads(process.stdout)["disposition"] == "WAVE_DEFINITION_VALID"
