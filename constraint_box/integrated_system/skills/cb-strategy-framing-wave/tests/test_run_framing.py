from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import scripts.run_framing as runner  # noqa: E402
from scripts.run_framing import (  # noqa: E402
    CHILD_IDS,
    INPUT_SCHEMA,
    PARENT_OPERATION,
    WAVE_ID,
    replay,
    run_packet,
    verify_receipt,
)


ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT.parent
FIXTURE = ROOT / "fixtures" / "positive_packet.json"
RUNNER = ROOT / "scripts" / "run_framing.py"


def _packet() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_positive_runs_all_six_and_retains_antichain_and_tensions() -> None:
    packet = _packet()
    receipt = run_packet(packet)
    assert receipt["status"] == "COMPLETE"
    assert receipt["child_order"] == list(CHILD_IDS)
    assert receipt["launched_child_order"] == list(CHILD_IDS)
    assert receipt["not_launched_child_ids"] == []
    assert set(receipt["child_receipts"]) == set(CHILD_IDS)
    assert set(receipt["portfolio_antichain"]) == {
        "direct",
        "alternative",
        "reframe",
        "back",
        "wildcard",
        "stop",
    }
    assert receipt["tensions"]
    assert receipt["disagreements"]
    assert receipt["route_truth"] == "NOT_FULL"
    assert receipt["route_truth_label"] == "NOT_FULL/model_free"
    assert receipt["model_free"] is True
    assert receipt["mmm_preload_applicable"] is False
    assert receipt["provider_receipt_applicable"] is False
    assert receipt["provider_call_receipt"] is None
    assert receipt["mmm_preload_receipts"] == []
    assert receipt["promotion_allowed"] is False
    assert receipt["winner_selected"] is False
    assert verify_receipt(receipt)
    assert verify_receipt(receipt, packet)
    operations = [row["operation_id"] for row in receipt["children"]]
    assert len(operations) == len(set(operations)) == 6
    assert set(receipt["child_input_hashes"]) == set(CHILD_IDS)
    assert set(receipt["child_receipt_hashes"]) == set(CHILD_IDS)
    assert receipt["replay_identity"]["output_digest"] == receipt["output_digest"]


def test_exact_replay_and_replay_api_are_byte_stable() -> None:
    packet = _packet()
    first = run_packet(packet)
    second = run_packet(copy.deepcopy(packet))
    assert first == second
    assert replay(packet, first)["status"] == "REPLAY_MATCH"
    assert replay(packet)["status"] == "REPLAYED"


def test_parent_cancellation_is_terminal_and_launches_no_child() -> None:
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


def test_child_cancellation_keeps_prefix_and_stops_later_siblings() -> None:
    packet = _packet()
    packet["child_inputs"]["horizons"]["cancelled"] = True
    receipt = run_packet(packet)
    assert receipt["status"] == "CANCELLED"
    assert receipt["cancellation_state"] == "CANCELLED"
    assert receipt["launched_child_order"] == ["boundary", "portfolio", "horizons"]
    assert receipt["not_launched_child_ids"] == list(CHILD_IDS[3:])
    assert receipt["children"][-1]["terminal_state"] == "CANCELLED"
    assert verify_receipt(receipt, packet)


def test_each_leaf_cancellation_has_actual_hash_and_replay_verifies() -> None:
    for child_id in CHILD_IDS:
        packet = _packet()
        packet["child_inputs"][child_id]["cancelled"] = True
        receipt = run_packet(packet)
        assert receipt["status"] == "CANCELLED"
        row = receipt["children"][-1]
        assert row["receipt_sha256"] == runner.digest(row["receipt"])
        assert row["receipt_self_sha256"] == row["receipt"]["receipt_sha256"]
        assert verify_receipt(receipt, packet)


def test_forged_cancelled_dict_is_not_accepted_as_leaf_receipt() -> None:
    original_definition = runner._definition

    def patched_definition(current_root: Path):
        definition, definition_path, configs, validator_path = original_definition(current_root)
        config = configs["boundary"]
        original_function = config["function"]

        def forged(payload):
            value = original_function({**payload, "cancelled": True})
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
    assert receipt["launched_child_order"] == ["boundary"]
    assert "CANCELLATION_BINDING" in str(receipt["reason"])


def test_cancellation_source_mutation_after_verified_child_is_refusal(tmp_path: Path) -> None:
    root = _copy_skills(tmp_path)
    original_definition = runner._definition

    def patched_definition(current_root: Path):
        definition, definition_path, configs, validator_path = original_definition(current_root)
        config = configs["boundary"]
        original_function = config["function"]
        source = config["script_path"]

        def mutate_after_cancel(payload):
            result = original_function(payload)
            source.write_text(source.read_text(encoding="utf-8") + "\n# cancellation drift\n", encoding="utf-8")
            return result

        config["function"] = mutate_after_cancel
        return definition, definition_path, configs, validator_path

    runner._definition = patched_definition
    packet = _packet()
    packet["child_inputs"]["boundary"]["cancelled"] = True
    try:
        receipt = run_packet(packet, skills_root=root)
    finally:
        runner._definition = original_definition
    assert receipt["status"] == "REFUSE"
    assert receipt["status"] != "CANCELLED"
    assert receipt["launched_child_order"] == ["boundary"]
    assert receipt["children"][-1]["terminal_state"] == "CANCELLED"
    assert "SOURCE_DRIFT" in str(receipt["reason"])


def test_cancellation_symlink_swap_refuses_before_replay(tmp_path: Path) -> None:
    root = _copy_skills(tmp_path)
    original_definition = runner._definition
    outside = tmp_path / "outside.py"
    outside.write_text("raise RuntimeError('outside source')\n", encoding="utf-8")

    def patched_definition(current_root: Path):
        definition, definition_path, configs, validator_path = original_definition(current_root)
        config = configs["boundary"]
        original_function = config["function"]
        source = config["script_path"]

        def swap_after_cancel(payload):
            result = original_function(payload)
            source.unlink()
            source.symlink_to(outside)
            return result

        config["function"] = swap_after_cancel
        return definition, definition_path, configs, validator_path

    runner._definition = patched_definition
    packet = _packet()
    packet["child_inputs"]["boundary"]["cancelled"] = True
    try:
        receipt = run_packet(packet, skills_root=root)
    finally:
        runner._definition = original_definition
    assert receipt["status"] == "REFUSE"
    assert receipt["status"] != "CANCELLED"
    assert receipt["launched_child_order"] == ["boundary"]
    assert "CANCELLATION_BINDING" in str(receipt["reason"])


def test_missing_extra_duplicate_and_rebound_children_refuse_before_launch() -> None:
    missing = _packet()
    del missing["child_inputs"]["discriminator"]
    receipt = run_packet(missing)
    assert receipt["status"] == "REFUSE"
    assert receipt["launched_child_order"] == []

    extra = _packet()
    extra["child_inputs"]["extra"] = {}
    receipt = run_packet(extra)
    assert receipt["status"] == "REFUSE"
    assert receipt["launched_child_order"] == []

    rebound = _packet()
    rebound["child_inputs"]["portfolio"]["target"] = "other-target"
    receipt = run_packet(rebound)
    assert receipt["status"] == "REFUSE"
    assert "REBOUND" in str(receipt["reason"])
    assert receipt["launched_child_order"] == []

    alias = _packet()
    alias["child_inputs"]["boundary"]["cancel_requested"] = True
    receipt = run_packet(alias)
    assert receipt["status"] == "REFUSE"
    assert receipt["launched_child_order"] == []


def test_object_card_context_and_child_schemas_are_closed() -> None:
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

    child_unknown = _packet()
    child_unknown["child_inputs"]["portfolio"]["unexpected"] = True
    receipt = run_packet(child_unknown)
    assert receipt["status"] == "REFUSE"
    assert "CHILD_INPUT_UNKNOWN" in str(receipt["reason"])
    assert receipt["launched_child_order"] == []


def test_collapsed_portfolio_is_retained_as_child_refusal_not_winner() -> None:
    packet = _packet()
    for key in ("direct", "alternative", "reframe", "back", "wildcard", "stop"):
        packet["child_inputs"]["portfolio"][key] = "same proposal"
    receipt = run_packet(packet)
    assert receipt["status"] == "REFUSE"
    assert "portfolio" in receipt["reason"]
    assert receipt["launched_child_order"] == ["boundary", "portfolio"]
    assert receipt["portfolio_antichain"] is None
    assert receipt["winner_selected"] is False
    assert verify_receipt(receipt, packet)


def test_child_and_parent_receipt_tamper_are_detected() -> None:
    packet = _packet()
    receipt = run_packet(packet)
    tampered = copy.deepcopy(receipt)
    tampered["portfolio_antichain"]["direct"] = "changed"
    assert not verify_receipt(tampered, packet)

    tampered_child = copy.deepcopy(receipt)
    tampered_child["child_receipts"]["sequence"]["order"] = ["changed"]
    assert not verify_receipt(tampered_child, packet)

    embedded = _packet()
    child = run_packet(embedded)["child_receipts"]["boundary"]
    embedded["child_inputs"]["boundary"]["receipt"] = copy.deepcopy(child)
    embedded["child_inputs"]["boundary"]["receipt"]["target"] = "other"
    stopped = run_packet(embedded)
    assert stopped["status"] == "REFUSE"
    assert "boundary" in stopped["reason"]


def test_resealed_terminal_status_and_reason_must_match_verified_rows() -> None:
    packet = _packet()
    receipt = run_packet(packet)
    for status, reason in (
        ("REFUSE", "REFUSE_PREFIX_INCOMPLETE:after_all_children"),
        ("HOLD", "HOLD_CHILD_STATUS:discriminator:HOLD:none"),
        ("COMPLETE", "tampered reason"),
    ):
        tampered = copy.deepcopy(receipt)
        tampered["status"] = status
        tampered["reason"] = reason
        resealed = runner._seal(tampered)
        assert not verify_receipt(resealed, packet)

    truncated = copy.deepcopy(receipt)
    removed = truncated["children"].pop()["child_id"]
    truncated["child_receipts"].pop(removed)
    truncated["child_receipt_hashes"].pop(removed)
    truncated["findings"].pop(removed)
    truncated["launched_child_order"] = list(CHILD_IDS[:-1])
    truncated["not_launched_child_ids"] = [CHILD_IDS[-1]]
    truncated["status"] = "REFUSE"
    truncated["reason"] = "REFUSE_PREFIX_INCOMPLETE:discriminator"
    assert not verify_receipt(runner._seal(truncated), packet)

    cancelled_packet = _packet()
    cancelled_packet["child_inputs"]["boundary"]["cancelled"] = True
    cancelled = run_packet(cancelled_packet)
    tampered_cancel = copy.deepcopy(cancelled)
    tampered_cancel["status"] = "REFUSE"
    tampered_cancel["reason"] = "REFUSE_CHILD_STATUS:boundary:CANCELLED_NO_AUTHORITY:none"
    assert not verify_receipt(runner._seal(tampered_cancel), cancelled_packet)


def _copy_skills(tmp_path: Path) -> Path:
    root = tmp_path / "skills"
    root.mkdir(parents=True)
    for name in ("cb-strategy-framing-wave", "cb-wave-author"):
        shutil.copytree(SKILLS_ROOT / name, root / name)
    for child in (
        "cb-object-boundary-cell",
        "cb-strategy-portfolio-cell",
        "cb-multi-horizon-cell",
        "cb-option-value-retreat-cell",
        "cb-dependency-sequence-cell",
        "cb-strategy-discriminator-cell",
    ):
        shutil.copytree(SKILLS_ROOT / child, root / child)
    return root


def test_source_and_definition_drift_refuse_on_fresh_run(tmp_path: Path) -> None:
    root = _copy_skills(tmp_path)
    child_source = root / "cb-strategy-portfolio-cell" / "scripts" / "portfolio.py"
    child_source.write_text(child_source.read_text(encoding="utf-8") + "\n# drift\n", encoding="utf-8")
    receipt = run_packet(_packet(), skills_root=root)
    assert receipt["status"] == "REFUSE"
    assert "SOURCE_DRIFT" in str(receipt["reason"])

    root = _copy_skills(tmp_path / "definition")
    definition = root / "cb-strategy-framing-wave" / "wave.json"
    value = json.loads(definition.read_text(encoding="utf-8"))
    value["purpose"] = "changed"
    definition.write_text(json.dumps(value), encoding="utf-8")
    receipt = run_packet(_packet(), skills_root=root)
    assert receipt["status"] == "REFUSE"
    assert "DEFINITION_SOURCE_DRIFT" in str(receipt["reason"])


def test_source_drift_during_run_preserves_prefix_and_stops(tmp_path: Path) -> None:
    root = _copy_skills(tmp_path)
    original_definition = runner._definition

    def patched_definition(current_root: Path):
        definition, definition_path, configs, validator_path = original_definition(current_root)
        config = configs["boundary"]
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
    assert receipt["launched_child_order"] == ["boundary"]
    assert receipt["not_launched_child_ids"] == list(CHILD_IDS[1:])
    assert len(receipt["children"]) == 1
    assert "SOURCE_DRIFT" in str(receipt["reason"])
    assert verify_receipt(receipt, _packet(), skills_root=root) is False


def test_final_source_drift_refuses_parent_success_after_full_prefix(tmp_path: Path) -> None:
    root = _copy_skills(tmp_path)
    original_definition = runner._definition

    def patched_definition(current_root: Path):
        definition, definition_path, configs, validator_path = original_definition(current_root)
        config = configs["discriminator"]
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
    assert len(receipt["children"]) == len(CHILD_IDS)
    assert "SOURCE_DRIFT" in str(receipt["reason"])


def test_prewrite_attestation_rejects_late_parent_drift(tmp_path: Path) -> None:
    root = _copy_skills(tmp_path)
    receipt = run_packet(_packet(), skills_root=root)
    parent = root / "cb-strategy-framing-wave" / "SKILL.md"
    parent.write_text(parent.read_text(encoding="utf-8") + "\n# late drift\n", encoding="utf-8")
    try:
        runner._prewrite_attest(receipt, skills_root=root)
    except runner.CandidateRefusal as exc:
        assert "SOURCE_DRIFT" in str(exc) or "PARENT_SKILL" in str(exc)
    else:
        raise AssertionError("late parent drift was accepted before parent write")


def test_prewrite_attestation_rejects_tampered_receipt_fields() -> None:
    receipt = run_packet(_packet())
    for field, value in (
        ("status", "REFUSE"),
        ("launched_child_order", []),
        ("child_input_hashes", {}),
        ("promotion_allowed", True),
    ):
        tampered = copy.deepcopy(receipt)
        tampered[field] = value
        try:
            runner._prewrite_attest(tampered)
        except runner.CandidateRefusal as exc:
            assert "PREWRITE_RECEIPT" in str(exc)
        else:
            raise AssertionError(f"tampered {field} was accepted before parent write")


def test_symlinked_child_source_is_a_path_escape(tmp_path: Path) -> None:
    root = _copy_skills(tmp_path)
    child_source = root / "cb-object-boundary-cell" / "scripts" / "restate.py"
    outside = tmp_path / "outside.py"
    outside.write_text("# outside\n", encoding="utf-8")
    child_source.unlink()
    child_source.symlink_to(outside)
    receipt = run_packet(_packet(), skills_root=root)
    assert receipt["status"] == "REFUSE"
    assert "SYMLINK_PATH" in str(receipt["reason"])
    assert receipt["launched_child_order"] == []


def test_trusted_definition_tree_validator_passes() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(SKILLS_ROOT / "cb-wave-author" / "scripts" / "validate_wave.py"),
            str(ROOT / "wave.json"),
        ],
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
    packet["object_card"]["target"] = "other-target"
    receipt = run_packet(packet)
    assert receipt["status"] == "REFUSE"
    assert receipt["launched_child_order"] == []
