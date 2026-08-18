from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import scripts.run_integrity as runner  # noqa: E402
from scripts.run_integrity import (  # noqa: E402
    CHILD_IDS,
    INPUT_SCHEMA,
    PARENT_OPERATION,
    WAVE_ID,
    run_packet,
    verify_receipt,
)


ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT.parent
FIXTURE = ROOT / "fixtures" / "positive_packet.json"
RUNNER = ROOT / "scripts" / "run_integrity.py"


def _packet() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_positive_runs_all_nine_and_is_self_bound() -> None:
    packet = _packet()
    receipt = run_packet(packet)
    assert receipt["status"] == "COMPLETE"
    assert receipt["child_order"] == list(CHILD_IDS)
    assert receipt["launched_child_order"] == list(CHILD_IDS)
    assert receipt["not_launched_child_ids"] == []
    assert len(receipt["children"]) == 9
    assert set(receipt["child_receipts"]) == set(CHILD_IDS)
    assert receipt["route_truth"] == "NOT_FULL"
    assert receipt["route_truth_label"] == "NOT_FULL/model_free"
    assert receipt["model_free"] is True
    assert receipt["mmm_preload_applicable"] is False
    assert receipt["provider_receipt_applicable"] is False
    assert receipt["not_applicable"] == ["mmm_preload_receipts", "provider_call_receipts"]
    assert receipt["not_applicable_labels"] == {
        "mmm_preload_receipts": "NOT_APPLICABLE_MODEL_FREE",
        "provider_call_receipts": "NOT_APPLICABLE_MODEL_FREE",
    }
    assert receipt["writes_performed"] is False
    assert receipt["receipt_written"] is False
    assert receipt["expected_source_set_sha256"] == _packet()["expected_source_set_sha256"]
    assert receipt["source_set_sha256"] == receipt["expected_source_set_sha256"]
    assert receipt["promotion_allowed"] is False
    assert receipt["winner_selected"] is False
    assert verify_receipt(receipt)
    assert verify_receipt(receipt, packet)
    operations = [row["operation_id"] for row in receipt["children"]]
    assert len(operations) == len(set(operations)) == 9


def test_reason_specific_severance_finding_is_retained_without_parent_winner() -> None:
    packet = _packet()
    packet["child_inputs"]["severance"].update(
        {"intervention": "delete hard cases", "proxy_before": 10, "proxy_after": 12, "object_before": 1, "object_after": 0}
    )
    receipt = run_packet(packet)
    assert receipt["status"] == "COMPLETE"
    assert receipt["child_receipts"]["severance"]["status"] == "SEVERED"
    assert any(item.get("child_id") == "severance" for item in receipt["contradictions"])
    assert receipt["winner_selected"] is False
    assert verify_receipt(receipt, packet)


def test_boundary_packet_shape_refuses_before_any_child() -> None:
    packet = _packet()
    packet["extra"] = True
    receipt = run_packet(packet)
    assert receipt["status"] == "REFUSE"
    assert receipt["launched_child_order"] == []
    assert receipt["not_launched_child_ids"] == list(CHILD_IDS)

    malformed = _packet()
    malformed["target"] = ""
    receipt = run_packet(malformed)
    assert receipt["status"] == "REFUSE"
    assert receipt["launched_child_order"] == []


def test_caller_bound_source_set_is_required_and_exact() -> None:
    missing = _packet()
    del missing["expected_source_set_sha256"]
    receipt = run_packet(missing)
    assert receipt["status"] == "REFUSE"
    assert receipt["launched_child_order"] == []

    mismatch = _packet()
    mismatch["expected_source_set_sha256"] = "0" * 64
    receipt = run_packet(mismatch)
    assert receipt["status"] == "REFUSE"
    assert "SOURCE_SET" in str(receipt["reason"])
    assert receipt["launched_child_order"] == []


def test_parent_immutable_flags_and_not_applicable_labels_reject_reseal() -> None:
    receipt = run_packet(_packet())
    mutations = {
        "not_applicable": ["provider_call_receipts"],
        "not_applicable_labels": {"provider_call_receipts": "OTHER"},
        "writes_performed": True,
        "receipt_written": True,
        "provider_dispatch_proved": True,
        "provider_receipt_applicable": True,
        "mmm_preload_applicable": True,
        "model_free": False,
        "route_truth": "FULL",
        "route_truth_label": "FULL/provider",
        "claim_ceiling": "promotion",
    }
    for field, value in mutations.items():
        tampered = copy.deepcopy(receipt)
        tampered[field] = value
        unsigned = copy.deepcopy(tampered)
        unsigned.pop("receipt_sha256", None)
        unsigned.pop("receipt_self_sha256", None)
        tampered["receipt_sha256"] = runner.digest(unsigned)
        tampered["receipt_self_sha256"] = tampered["receipt_sha256"]
        assert not verify_receipt(tampered, _packet()), field


def test_object_card_and_context_schemas_are_exact() -> None:
    unknown_card = _packet()
    unknown_card["object_card"]["extra"] = True
    receipt = run_packet(unknown_card)
    assert receipt["status"] == "REFUSE"
    assert "OBJECT_CARD_UNKNOWN" in str(receipt["reason"])
    assert receipt["launched_child_order"] == []

    bad_card_type = _packet()
    bad_card_type["object_card"]["hard_constraints"] = "not-a-list"
    receipt = run_packet(bad_card_type)
    assert receipt["status"] == "REFUSE"
    assert "OBJECT_CARD_HARD_CONSTRAINTS_TYPE" in str(receipt["reason"])

    unknown_context = _packet()
    unknown_context["context"]["extra"] = "unknown"
    receipt = run_packet(unknown_context)
    assert receipt["status"] == "REFUSE"
    assert "CONTEXT_UNKNOWN" in str(receipt["reason"])

    bad_context_type = _packet()
    bad_context_type["context"]["disagreements"] = {"not": "a list"}
    receipt = run_packet(bad_context_type)
    assert receipt["status"] == "REFUSE"
    assert "CONTEXT_DISAGREEMENTS_TYPE" in str(receipt["reason"])


def test_child_input_unknown_field_refuses_before_launch() -> None:
    packet = _packet()
    packet["child_inputs"]["impact"]["unexpected"] = True
    receipt = run_packet(packet)
    assert receipt["status"] == "REFUSE"
    assert "CHILD_INPUT_UNKNOWN" in str(receipt["reason"])
    assert receipt["launched_child_order"] == []


def test_exact_replay_is_byte_stable() -> None:
    first = run_packet(_packet())
    second = run_packet(copy.deepcopy(_packet()))
    assert first == second


def test_parent_cancellation_stops_without_child_launch_or_success() -> None:
    packet = _packet()
    packet["cancel_requested"] = True
    receipt = run_packet(packet)
    assert receipt["status"] == "CANCELLED"
    assert receipt["cancellation_state"] == "CANCELLED"
    assert receipt["children"] == []
    assert receipt["launched_child_order"] == []
    assert receipt["not_launched_child_ids"] == list(CHILD_IDS)
    assert receipt["promotion_allowed"] is False
    assert verify_receipt(receipt, packet)


def test_child_cancellation_keeps_prefix_and_never_launches_later_siblings() -> None:
    packet = _packet()
    packet["child_inputs"]["severance"]["cancel_requested"] = True
    receipt = run_packet(packet)
    assert receipt["status"] == "CANCELLED"
    assert receipt["launched_child_order"] == ["proxy_map", "regimes", "severance"]
    assert receipt["not_launched_child_ids"] == list(CHILD_IDS[3:])
    assert receipt["children"][-1]["terminal_state"] == "CANCELLED"
    assert verify_receipt(receipt, packet)


def test_each_leaf_cancellation_has_actual_hash_and_replay_verifies() -> None:
    for child_id in CHILD_IDS:
        packet = _packet()
        cancel_key = "cancel_requested" if child_id in CHILD_IDS[:5] else "cancelled"
        packet["child_inputs"][child_id][cancel_key] = True
        receipt = run_packet(packet)
        assert receipt["status"] == "CANCELLED"
        row = receipt["children"][-1]
        assert row["receipt_sha256"] == runner.digest(row["receipt"])
        assert verify_receipt(receipt, packet)


def test_forged_cancelled_dict_is_not_accepted_as_leaf_receipt() -> None:
    original_definition = runner._definition

    def patched_definition(current_root: Path):
        definition, definition_path, configs, validator_path = original_definition(current_root)
        config = configs["proxy_map"]
        original_function = config["function"]

        def forged(payload):
            value = original_function({**payload, "cancel_requested": True})
            value["reason"] = "forged"
            return value

        config["function"] = forged
        return definition, definition_path, configs, validator_path

    runner._definition = patched_definition
    try:
        receipt = run_packet(_packet())
    finally:
        runner._definition = original_definition
    assert receipt["status"] == "REFUSE"
    assert receipt["launched_child_order"] == ["proxy_map"]
    assert "CANCELLATION_BINDING" in str(receipt["reason"])


def test_resealed_child_rebinding_is_rejected() -> None:
    packet = _packet()
    receipt = run_packet(packet)
    rebound = copy.deepcopy(receipt)
    rebound["children"][0]["skill"] = "cb-goodhart-regime-cell"
    unsigned = copy.deepcopy(rebound)
    unsigned.pop("receipt_sha256", None)
    unsigned.pop("receipt_self_sha256", None)
    rebound["receipt_sha256"] = runner.digest(unsigned)
    rebound["receipt_self_sha256"] = rebound["receipt_sha256"]
    assert not verify_receipt(rebound, packet)

    extra = copy.deepcopy(receipt)
    extra["winner"] = "proxy_map"
    unsigned = copy.deepcopy(extra)
    unsigned.pop("receipt_sha256", None)
    unsigned.pop("receipt_self_sha256", None)
    extra["receipt_sha256"] = runner.digest(unsigned)
    extra["receipt_self_sha256"] = extra["receipt_sha256"]
    assert not verify_receipt(extra, packet)

    rebound = copy.deepcopy(receipt)
    rebound["children"][1]["operation_id"] = "cb-proxy-severance-cell.v1"
    unsigned = copy.deepcopy(rebound)
    unsigned.pop("receipt_sha256", None)
    unsigned.pop("receipt_self_sha256", None)
    rebound["receipt_sha256"] = runner.digest(unsigned)
    rebound["receipt_self_sha256"] = rebound["receipt_sha256"]
    assert not verify_receipt(rebound, packet)


def test_missing_extra_and_rebound_child_sets_refuse_before_launch() -> None:
    missing = _packet()
    del missing["child_inputs"]["impact"]
    receipt = run_packet(missing)
    assert receipt["status"] == "REFUSE"
    assert receipt["launched_child_order"] == []

    extra = _packet()
    extra["child_inputs"]["extra"] = {}
    receipt = run_packet(extra)
    assert receipt["status"] == "REFUSE"
    assert receipt["launched_child_order"] == []

    rebound = _packet()
    rebound["child_inputs"]["regimes"]["target_id"] = "other-target"
    receipt = run_packet(rebound)
    assert receipt["status"] == "REFUSE"
    assert "REBOUND" in str(receipt["reason"])
    assert receipt["launched_child_order"] == []


def test_parent_and_child_receipt_tamper_is_detected() -> None:
    packet = _packet()
    receipt = run_packet(packet)
    tampered = copy.deepcopy(receipt)
    tampered["children"][0]["status"] = "PROMOTED"
    assert not verify_receipt(tampered, packet)

    tampered_child = copy.deepcopy(receipt)
    tampered_child["child_receipts"]["severance"]["object_delta"] = 99
    assert not verify_receipt(tampered_child, packet)


def _copy_skills(tmp_path: Path) -> Path:
    root = tmp_path / "skills"
    root.mkdir(parents=True)
    for name in ("cb-objective-integrity-wave", "cb-wave-author"):
        shutil.copytree(SKILLS_ROOT / name, root / name)
    for child in (
        "cb-object-proxy-mapper",
        "cb-goodhart-regime-cell",
        "cb-proxy-severance-cell",
        "cb-optimizer-adversary-cell",
        "cb-resource-expansion-cell",
        "cb-externality-horizon-cell",
        "cb-termination-budget-cell",
        "cb-goal-amendment-guard",
        "cb-impact-vs-output-auditor",
    ):
        shutil.copytree(SKILLS_ROOT / child, root / child)
    return root


def test_preexecution_parent_skill_runner_validator_mutations_refuse(tmp_path: Path) -> None:
    for index, relative in enumerate(
        (
            "cb-objective-integrity-wave/SKILL.md",
            "cb-objective-integrity-wave/scripts/run_integrity.py",
            "cb-wave-author/scripts/validate_wave.py",
        )
    ):
        root = _copy_skills(tmp_path / str(index))
        target = root / relative
        target.write_text(target.read_text(encoding="utf-8") + "\n# pre-execution mutation\n", encoding="utf-8")
        receipt = run_packet(_packet(), skills_root=root)
        assert receipt["status"] == "REFUSE"
        assert receipt["launched_child_order"] == []
        assert "SOURCE_SET" in str(receipt["reason"]) or "DRIFT" in str(receipt["reason"])


def test_source_and_definition_drift_refuse_on_fresh_run(tmp_path: Path) -> None:
    root = _copy_skills(tmp_path)
    packet = _packet()
    child_source = root / "cb-proxy-severance-cell" / "scripts" / "sever.py"
    child_source.write_text(child_source.read_text(encoding="utf-8") + "\n# drift\n", encoding="utf-8")
    receipt = run_packet(packet, skills_root=root)
    assert receipt["status"] == "REFUSE"
    assert "SOURCE_DRIFT" in str(receipt["reason"])

    root = _copy_skills(tmp_path / "definition")
    definition = root / "cb-objective-integrity-wave" / "wave.json"
    value = json.loads(definition.read_text(encoding="utf-8"))
    value["purpose"] = "changed"
    definition.write_text(json.dumps(value), encoding="utf-8")
    receipt = run_packet(packet, skills_root=root)
    assert receipt["status"] == "REFUSE"
    assert "DEFINITION_SOURCE_DRIFT" in str(receipt["reason"])


def test_source_drift_during_run_preserves_prefix_and_stops(tmp_path: Path) -> None:
    root = _copy_skills(tmp_path)
    original_definition = runner._definition

    def patched_definition(current_root: Path):
        definition, definition_path, configs, validator_path = original_definition(current_root)
        config = configs["proxy_map"]
        original_function = config["function"]
        source = config["script_path"]

        def mutate_after_child(payload):
            result = original_function(payload)
            source.write_text(source.read_text(encoding="utf-8") + "\n# mid-run drift\n", encoding="utf-8")
            return result

        config["function"] = mutate_after_child
        return definition, definition_path, configs, validator_path

    runner._definition = patched_definition
    try:
        receipt = run_packet(_packet(), skills_root=root)
    finally:
        runner._definition = original_definition
    assert receipt["status"] == "REFUSE"
    assert receipt["launched_child_order"] == ["proxy_map"]
    assert receipt["not_launched_child_ids"] == list(CHILD_IDS[1:])
    assert len(receipt["children"]) == 1
    assert "SOURCE_DRIFT" in str(receipt["reason"])


def test_final_source_drift_refuses_parent_success_after_full_prefix(tmp_path: Path) -> None:
    root = _copy_skills(tmp_path)
    original_definition = runner._definition

    def patched_definition(current_root: Path):
        definition, definition_path, configs, validator_path = original_definition(current_root)
        config = configs["impact"]
        original_function = config["function"]
        source = config["script_path"]

        def mutate_after_last_child(payload):
            result = original_function(payload)
            source.write_text(source.read_text(encoding="utf-8") + "\n# final drift\n", encoding="utf-8")
            return result

        config["function"] = mutate_after_last_child
        return definition, definition_path, configs, validator_path

    runner._definition = patched_definition
    try:
        receipt = run_packet(_packet(), skills_root=root)
    finally:
        runner._definition = original_definition
    assert receipt["status"] == "REFUSE"
    assert receipt["launched_child_order"] == list(CHILD_IDS)
    assert receipt["not_launched_child_ids"] == []
    assert len(receipt["children"]) == 9
    assert "SOURCE_DRIFT" in str(receipt["reason"])


def test_prewrite_attestation_rejects_late_source_drift(tmp_path: Path) -> None:
    root = _copy_skills(tmp_path)
    packet = _packet()
    receipt = run_packet(packet, skills_root=root)
    source = root / "cb-objective-integrity-wave" / "scripts" / "run_integrity.py"
    source.write_text(source.read_text(encoding="utf-8") + "\n# late drift\n", encoding="utf-8")
    try:
        runner._prewrite_attest(receipt, skills_root=root)
    except runner.CandidateRefusal as exc:
        assert "SOURCE_DRIFT" in str(exc)
    else:
        raise AssertionError("late source drift was accepted before parent write")


def test_symlinked_child_source_is_a_path_escape(tmp_path: Path) -> None:
    root = _copy_skills(tmp_path)
    child_source = root / "cb-object-proxy-mapper" / "scripts" / "map_proxy.py"
    child_source.unlink()
    child_source.symlink_to(root / "outside.py")
    receipt = run_packet(_packet(), skills_root=root)
    assert receipt["status"] == "REFUSE"
    assert "SYMLINK_PATH" in str(receipt["reason"])
    assert receipt["launched_child_order"] == []


def test_trusted_definition_tree_validator_passes() -> None:
    proc = subprocess.run(
        [sys.executable, str(SKILLS_ROOT / "cb-wave-author" / "scripts" / "validate_wave.py"), str(ROOT / "wave.json")],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    result = json.loads(proc.stdout)
    assert result["disposition"] == "WAVE_DEFINITION_VALID"


def test_cli_writes_only_explicit_parent_receipt(tmp_path: Path) -> None:
    out = tmp_path / "receipt.json"
    proc = subprocess.run(
        [sys.executable, str(RUNNER), "--packet", str(FIXTURE), "--out", str(out)],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    receipt = json.loads(out.read_text(encoding="utf-8"))
    assert receipt["status"] == "COMPLETE"
    assert not list(tmp_path.glob("**/provider*"))


def test_cli_rejects_duplicate_json_keys(tmp_path: Path) -> None:
    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text('{"schema":"x","schema":"y"}', encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(RUNNER), "--packet", str(duplicate)],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2
    assert json.loads(proc.stdout)["status"] == "REFUSE"


def test_packet_identity_fields_are_exact() -> None:
    packet = _packet()
    assert packet["schema"] == INPUT_SCHEMA
    assert packet["wave_id"] == WAVE_ID
    assert packet["operation"] == PARENT_OPERATION
    packet["child_inputs"]["impact"]["target"] = "other-target"
    receipt = run_packet(packet)
    assert receipt["status"] == "REFUSE"
    assert receipt["launched_child_order"] == []
