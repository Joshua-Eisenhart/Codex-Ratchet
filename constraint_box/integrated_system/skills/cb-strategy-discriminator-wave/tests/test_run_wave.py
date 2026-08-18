from __future__ import annotations

import copy
import importlib.util
import json
import shutil
import subprocess
from pathlib import Path


CANDIDATE = Path(__file__).resolve().parents[1]
PRODUCT_ROOT = CANDIDATE.parents[3]
RUNNER_PATH = CANDIDATE / "scripts" / "run_wave.py"
SPEC = importlib.util.spec_from_file_location("strategy_discriminator_wave", RUNNER_PATH)
assert SPEC is not None and SPEC.loader is not None
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


def _raw_packet() -> dict[str, object]:
    return json.loads(
        (CANDIDATE / "fixtures" / "strategy_discriminator_live_input_v1.json").read_text(
            encoding="utf-8"
        )
    )


def fixture_packet() -> dict[str, object]:
    return json.loads(
        (CANDIDATE / "fixtures" / "strategy_discriminator_input_v1.json").read_text(
            encoding="utf-8"
        )
    )


def packet() -> dict[str, object]:
    """Return the portable fixture packet; LIVE is always requested explicitly."""

    return fixture_packet()


def live_packet() -> dict[str, object]:
    """Return the source-checkout packet bound to the current LIVE epoch."""

    return _raw_packet()


def run(value: dict[str, object], *, authority_mode: str = "FIXTURE") -> dict[str, object]:
    return runner.run_packet(value, root=PRODUCT_ROOT, authority_mode=authority_mode)


def _keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return set(value) | {nested for item in value.values() for nested in _keys(item)}
    if isinstance(value, list):
        return {nested for item in value for nested in _keys(item)}
    return set()


def _copy_product(tmp_path: Path) -> Path:
    root = tmp_path / "product"
    skills = root / "constraint_box" / "integrated_system" / "skills"
    skills.parent.mkdir(parents=True)
    shutil.copytree(PRODUCT_ROOT / "constraint_box" / "integrated_system" / "skills", skills)
    config = root / "constraint_box" / "integrated_system" / "config"
    config.mkdir(parents=True)
    shutil.copy2(
        PRODUCT_ROOT / "constraint_box" / "integrated_system" / "config" / "CUMULATIVE_WAVE_SEQUENCE.json",
        config / "CUMULATIVE_WAVE_SEQUENCE.json",
    )
    return root


def _update_hash(value: dict[str, object], key: str, nested_key: str) -> None:
    value[key] = runner.digest(value[nested_key])


def _reseal_retained(value: dict[str, object]) -> str:
    retained = value["retained_cumulative_receipt"]
    assert isinstance(retained, dict)
    value["retained_cumulative_receipt_sha256"] = runner.digest(retained)
    _rebind_child(
        value,
        retained=value["retained_cumulative_receipt_sha256"],
        retained_self=value["retained_cumulative_receipt_self_sha256"],
    )
    return str(value["retained_cumulative_receipt_sha256"])


def _rebind_child(value: dict[str, object], *, profile: str | None = None, retained: str | None = None, candidate: str | None = None, live: str | None = None, run_id: str | None = None, source_set: str | None = None, epoch: str | None = None, frontier: str | None = None, retained_self: str | None = None) -> None:
    children = value["child_inputs"]
    assert isinstance(children, dict)
    for row in children.values():
        assert isinstance(row, dict)
        bindings = row["bindings"]
        assert isinstance(bindings, dict)
        if profile is not None:
            bindings["profile"] = profile
        if retained is not None:
            bindings["retained_cumulative_receipt_sha256"] = retained
        if retained_self is not None:
            bindings["retained_cumulative_receipt_self_sha256"] = retained_self
        if candidate is not None:
            bindings["candidate_order_sha256"] = candidate
        if live is not None:
            bindings["live_order_sha256"] = live
        if run_id is not None:
            bindings["retained_cumulative_run_id"] = run_id
        if source_set is not None:
            bindings["expected_source_set_sha256"] = source_set
        if epoch is not None:
            bindings["context_epoch_sha256"] = epoch
        if frontier is not None:
            bindings["branch_frontier_sha256"] = frontier


def test_definition_is_inactive_and_trusted_validator_accepts_it() -> None:
    definition = json.loads((CANDIDATE / "wave.json").read_text(encoding="utf-8"))
    assert definition["candidate_state"] == "NEW_CANDIDATE"
    assert definition["activated"] is False
    assert definition["promotion_allowed"] is False
    assert [row["id"] for row in definition["children"]] == list(runner.CHILD_IDS)
    assert len({row["operation"] for row in definition["children"]}) == 3
    assert {row["leaf_operation"] for row in definition["children"]} == {runner.LEAF_OPERATION}
    validator = PRODUCT_ROOT / "constraint_box/integrated_system/skills/cb-wave-author/scripts/validate_wave.py"
    proc = subprocess.run(
        ["python3", str(validator), str(CANDIDATE / "wave.json")],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert json.loads(proc.stdout)["disposition"] == "WAVE_DEFINITION_VALID"


def test_candidate_contained_authority_fixture_mode_is_pinned(tmp_path: Path) -> None:
    root = _copy_product(tmp_path)
    result = runner.run_packet(fixture_packet(), root=root, authority_mode="FIXTURE")
    assert result["status"] == "HOLD_ORDER_MISMATCH"
    assert result["authority_receipt_mode"] == "fixture"
    assert result["authority_pointer_mode"] == "fixture"
    assert runner.verify_receipt(result, fixture_packet(), root=root, authority_mode="FIXTURE")

    authority_receipt = root / "constraint_box/integrated_system/skills/cb-strategy-discriminator-wave/fixtures/authority/RECEIPT.json"
    authority_receipt.write_bytes(authority_receipt.read_bytes() + b"\n")
    refused = runner.run_packet(fixture_packet(), root=root, authority_mode="FIXTURE")
    assert refused["status"] == "REFUSE"
    assert refused["reason"] == "REFUSE_AUTHORITY_RECEIPT_RAW_HASH"


def test_source_checkout_live_mode_uses_exact_local_authority() -> None:
    live_receipt = (
        PRODUCT_ROOT
        / "constraint_box/integrated_system/state/receipts/cumulative/"
        / "cumulative-hardening-20260818-2/RECEIPT.json"
    )
    if not live_receipt.is_file():
        refused = runner.run_packet(live_packet(), root=PRODUCT_ROOT, authority_mode="LIVE")
        assert refused["status"] == "REFUSE"
        assert "PATH_RESOLVE" in str(refused["reason"])
        return
    result = runner.run_packet(live_packet(), root=PRODUCT_ROOT, authority_mode="LIVE")
    assert result["status"] == "HOLD_ORDER_MISMATCH"
    assert result["authority_receipt_mode"] == "live"
    assert result["authority_pointer_mode"] == "live"
    assert runner.verify_receipt(result, live_packet(), root=PRODUCT_ROOT, authority_mode="LIVE")


def test_live_authority_symlinks_refuse_without_fixture_fallback(tmp_path: Path) -> None:
    root = _copy_product(tmp_path)
    live_receipt = root / "constraint_box/integrated_system/state/receipts/cumulative/cumulative-hardening-20260818-2/RECEIPT.json"
    live_receipt.parent.mkdir(parents=True, exist_ok=True)
    live_receipt.symlink_to(root / "constraint_box/integrated_system/skills/cb-strategy-discriminator-wave/fixtures/authority/RECEIPT.json")
    refused = runner.run_packet(live_packet(), root=root, authority_mode="LIVE")
    assert refused["status"] == "REFUSE"
    assert "SYMLINK_PATH" in str(refused["reason"])

    root = _copy_product(tmp_path / "pointer")
    live_receipt = root / "constraint_box/integrated_system/state/receipts/cumulative/cumulative-hardening-20260818-2/RECEIPT.json"
    live_receipt.parent.mkdir(parents=True, exist_ok=True)
    live_source = (
        PRODUCT_ROOT
        / "constraint_box/integrated_system/state/receipts/cumulative/"
        / "cumulative-hardening-20260818-2/RECEIPT.json"
    )
    if not live_source.is_file():
        return
    shutil.copy2(
        live_source,
        live_receipt,
    )
    live_pointer = root / "constraint_box/integrated_system/state/CURRENT_EPOCH.json"
    live_pointer.parent.mkdir(parents=True, exist_ok=True)
    live_pointer.symlink_to(root / "constraint_box/integrated_system/skills/cb-strategy-discriminator-wave/fixtures/authority/CURRENT_EPOCH.json")
    refused = runner.run_packet(live_packet(), root=root, authority_mode="LIVE")
    assert refused["status"] == "REFUSE"
    assert "SYMLINK_PATH" in str(refused["reason"])


def test_authority_stale_run_frontier_and_epoch_swap_attacks_refuse(tmp_path: Path) -> None:
    root = _copy_product(tmp_path)
    value = packet()
    retained = value["retained_cumulative_receipt"]
    assert isinstance(retained, dict)
    retained["run_id"] = "stale-run"
    value["retained_cumulative_receipt_sha256"] = runner.digest(retained)
    value["retained_cumulative_run_id"] = "stale-run"
    _rebind_child(value, run_id="stale-run", retained=value["retained_cumulative_receipt_sha256"])
    refused = runner.run_packet(value, root=root, authority_mode="FIXTURE")
    assert refused["status"] == "REFUSE"
    assert refused["reason"] == "REFUSE_AUTHORITY_RECEIPT_BINDING"

    value = fixture_packet()
    value["branch_frontier"]["branch_ids"] = ["live_scheduler_order", "candidate_order"]
    value["branch_frontier"]["open_branch_ids"] = ["live_scheduler_order", "candidate_order"]
    value["branch_frontier_sha256"] = runner.digest(value["branch_frontier"])
    _rebind_child(value, frontier=value["branch_frontier_sha256"])
    refused = runner.run_packet(value, root=root, authority_mode="FIXTURE")
    assert refused["status"] == "REFUSE"
    assert refused["reason"] == "REFUSE_AUTHORITY_FRONTIER_BINDING"

    value = fixture_packet()
    epoch = value["context_epoch"]
    assert isinstance(epoch, dict)
    epoch["epoch_digest"] = "0" * 64
    value["context_epoch_sha256"] = runner.digest(epoch)
    _rebind_child(value, epoch=value["context_epoch_sha256"])
    refused = runner.run_packet(value, root=root, authority_mode="FIXTURE")
    assert refused["status"] == "REFUSE"
    assert refused["reason"] == "REFUSE_AUTHORITY_EPOCH_BINDING"

    epoch_file = root / "constraint_box/integrated_system/skills/cb-strategy-discriminator-wave/fixtures/authority/epoch-00000001.json"
    epoch_value = json.loads(epoch_file.read_text(encoding="utf-8"))
    epoch_value["epoch_digest"] = "0" * 64
    epoch_file.write_text(json.dumps(epoch_value, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    refused = runner.run_packet(fixture_packet(), root=root, authority_mode="FIXTURE")
    assert refused["status"] == "REFUSE"
    assert refused["reason"] == "REFUSE_AUTHORITY_EPOCH_RAW_HASH"


def test_mismatch_runs_three_distinct_parent_operations_and_keeps_frontier() -> None:
    result = run(packet())
    assert result["status"] == "HOLD_ORDER_MISMATCH"
    assert result["reason"] == "HOLD_ORDER_MISMATCH"
    assert result["launched_child_order"] == list(runner.CHILD_IDS)
    assert [row["operation_id"] for row in result["children"]] == [runner.CHILD_OPERATIONS[item] for item in runner.CHILD_IDS]
    assert len({row["operation_id"] for row in result["children"]}) == 3
    assert {row["leaf_operation"] for row in result["children"]} == {runner.LEAF_OPERATION}
    assert result["frontier"]["first_difference_index"] == 2
    assert result["frontier"]["common_prefix"] == ["cb-maintenance-wave", "cb-context-strategy-wave"]
    assert result["frontier"]["selection_counts_used"] is False
    assert result["promotion_allowed"] is False
    assert result["activated"] is False
    assert result["writes_performed"] is False
    assert runner.verify_receipt(result, packet(), root=PRODUCT_ROOT, authority_mode="FIXTURE")
    assert runner.verify_receipt(result, root=PRODUCT_ROOT, authority_mode="FIXTURE")
    assert "winner" not in _keys(result)
    assert "reorder" not in _keys(result)
    assert [row["label"] for row in result["attestations"]] == [
        "preflight",
        "before_child:bind_survivors",
        "after_child:bind_survivors",
        "before_child:name_exact_disagreement",
        "after_child:name_exact_disagreement",
        "before_child:design_finite_observable",
        "after_child:design_finite_observable",
        "after_all_children",
        "prewrite",
    ]
    for row in result["negative_controls"]:
        assert row["passed"] is True
        assert row["receipt_verified"] is True
    assert all(
        row["source_hashes"] == result["source_hashes"]
        for row in result["attestations"]
    )


def test_exact_match_is_the_only_non_hold_order_disposition() -> None:
    value = packet()
    value["candidate_order"] = copy.deepcopy(value["live_order"])
    value["candidate_order_sha256"] = runner.digest(value["candidate_order"])
    value["branch_frontier"]["entries"][0]["order_sha256"] = value["candidate_order_sha256"]
    value["branch_frontier_sha256"] = runner.digest(value["branch_frontier"])
    _rebind_child(value, candidate=value["candidate_order_sha256"])
    _rebind_child(value, frontier=value["branch_frontier_sha256"])
    result = run(value)
    assert result["status"] == "MATCH_OBSERVED"
    assert result["reason"] is None
    assert result["frontier"]["arrays_equal"] is True
    assert result["frontier"]["first_difference_index"] is None
    assert runner.verify_receipt(result, value, root=PRODUCT_ROOT, authority_mode="FIXTURE")


def test_selection_counts_never_enter_order_admission() -> None:
    original = run(packet())
    changed = packet()
    retained = changed["retained_cumulative_receipt"]
    assert isinstance(retained, dict)
    retained["selection_count"] = 999999
    changed["retained_cumulative_receipt_sha256"] = _reseal_retained(changed)
    _rebind_child(changed, retained=changed["retained_cumulative_receipt_sha256"])
    result = run(changed)
    assert result["status"] == original["status"]
    assert result["frontier"] == original["frontier"]
    assert result["selection_counts_used"] is False
    assert result["negative_controls"][-1]["observed_reason"] == "NOT_USED_FOR_ORDER_ADMISSION"


def test_profile_is_bound_and_heavy_alternate_is_read_only() -> None:
    value = packet()
    value["profile"] = "heavy"
    retained = value["retained_cumulative_receipt"]
    assert isinstance(retained, dict)
    retained["profile"] = "heavy"
    value["retained_cumulative_receipt_sha256"] = _reseal_retained(value)
    _rebind_child(
        value,
        profile="heavy",
        retained=value["retained_cumulative_receipt_sha256"],
    )
    result = run(value)
    assert result["status"] == "REFUSE"
    assert result["reason"] == "REFUSE_AUTHORITY_RECEIPT_PROFILE"


def test_source_definition_and_config_drift_refuse_before_children(tmp_path: Path) -> None:
    root = _copy_product(tmp_path)
    value = fixture_packet()
    leaf = root / "constraint_box/integrated_system/skills/cb-strategy-discriminator-cell/scripts/discriminate.py"
    leaf.write_text(leaf.read_text(encoding="utf-8") + "\n# drift\n", encoding="utf-8")
    refused = runner.run_packet(value, root=root, authority_mode="FIXTURE")
    assert refused["status"] == "REFUSE"
    assert "SOURCE_DRIFT" in str(refused["reason"])
    root = _copy_product(tmp_path / "definition")
    definition = root / "constraint_box/integrated_system/skills/cb-strategy-discriminator-wave/wave.json"
    definition.write_text(definition.read_text(encoding="utf-8").replace("non-authoritative", "changed"), encoding="utf-8")
    refused = runner.run_packet(value, root=root, authority_mode="FIXTURE")
    assert refused["status"] == "REFUSE"
    assert "DEFINITION_SOURCE_DRIFT" in str(refused["reason"])
    root = _copy_product(tmp_path / "config")
    config = root / "constraint_box/integrated_system/config/CUMULATIVE_WAVE_SEQUENCE.json"
    config.write_text(config.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    refused = runner.run_packet(value, root=root, authority_mode="FIXTURE")
    assert refused["status"] == "REFUSE"
    assert refused["reason"] == "REFUSE_CONFIG_SOURCE_DRIFT"


def test_embedded_receipt_epoch_frontier_and_live_order_drift_refuse() -> None:
    value = packet()
    retained = value["retained_cumulative_receipt"]
    assert isinstance(retained, dict)
    retained["selection_count"] = 7
    refused = run(value)
    assert refused["status"] == "REFUSE"
    assert refused["reason"] == "REFUSE_RETAINED_RECEIPT_DRIFT"
    value = packet()
    value["live_order"] = ["cb-context-strategy-wave", "cb-maintenance-wave"]
    value["live_order_sha256"] = runner.digest(value["live_order"])
    value["branch_frontier"]["entries"][1]["order_sha256"] = value["live_order_sha256"]
    value["branch_frontier_sha256"] = runner.digest(value["branch_frontier"])
    _rebind_child(value, live=value["live_order_sha256"])
    _rebind_child(value, frontier=value["branch_frontier_sha256"])
    refused = run(value)
    assert refused["status"] == "REFUSE"
    assert refused["reason"] == "REFUSE_LIVE_ORDER_BINDING"


def test_retained_receipt_self_hash_status_lock_and_later_stage_attacks_refuse() -> None:
    value = packet()
    retained = value["retained_cumulative_receipt"]
    assert isinstance(retained, dict)
    retained["receipt_sha256"] = "0" * 64
    value["retained_cumulative_receipt_sha256"] = runner.digest(retained)
    value["retained_cumulative_receipt_self_sha256"] = "0" * 64
    _rebind_child(value, retained=value["retained_cumulative_receipt_sha256"])
    _rebind_child(value, retained_self=value["retained_cumulative_receipt_self_sha256"])
    refused = run(value)
    assert refused["status"] == "REFUSE"
    assert refused["reason"] == "REFUSE_AUTHORITY_RECEIPT_BINDING"

    value = packet()
    retained = value["retained_cumulative_receipt"]
    assert isinstance(retained, dict)
    retained["status"] = "PASS"
    retained_hash = _reseal_retained(value)
    _rebind_child(value, retained=retained_hash)
    refused = run(value)
    assert refused["status"] == "REFUSE"
    assert refused["reason"] == "REFUSE_AUTHORITY_RECEIPT_STATUS"

    value = packet()
    retained = value["retained_cumulative_receipt"]
    assert isinstance(retained, dict)
    retained["source_binding"]["config_path"] = "evil/CUMULATIVE_WAVE_SEQUENCE.json"
    retained_hash = _reseal_retained(value)
    _rebind_child(value, retained=retained_hash)
    refused = run(value)
    assert refused["status"] == "REFUSE"
    assert refused["reason"] == "REFUSE_RETAINED_CONFIG_PATH"

    value = packet()
    retained = value["retained_cumulative_receipt"]
    assert isinstance(retained, dict)
    records = retained["prefixes"][2]["stage_records"]
    assert isinstance(records, list)
    records[2]["executed"] = True
    retained_hash = _reseal_retained(value)
    _rebind_child(value, retained=retained_hash)
    refused = run(value)
    assert refused["status"] == "REFUSE"
    assert refused["reason"] == "REFUSE_RETAINED_PREFIX_3_EXECUTION"

    value = packet()
    retained = value["retained_cumulative_receipt"]
    assert isinstance(retained, dict)
    retained["prefixes"][0]["rounds"][0]["stages"].append(
        {"stage_id": "cb-repair-wave", "status": "PASS", "executed": True}
    )
    retained_hash = _reseal_retained(value)
    _rebind_child(value, retained=retained_hash)
    refused = run(value)
    assert refused["status"] == "REFUSE"
    assert refused["reason"] == "REFUSE_RETAINED_LATER_STAGE_EXECUTED"


def test_parent_cancellation_still_preflights_retained_receipt() -> None:
    value = packet()
    value["cancel_requested"] = True
    retained = value["retained_cumulative_receipt"]
    assert isinstance(retained, dict)
    retained["status"] = "PASS"
    retained_hash = _reseal_retained(value)
    _rebind_child(value, retained=retained_hash)
    refused = run(value)
    assert refused["status"] == "REFUSE"
    assert refused["reason"] == "REFUSE_AUTHORITY_RECEIPT_STATUS"
    assert refused["children"] == []


def test_run_id_and_exact_retained_prefix_topology_attacks_refuse() -> None:
    value = packet()
    value["retained_cumulative_run_id"] = "wrong-run"
    _rebind_child(value, run_id="wrong-run")
    refused = run(value)
    assert refused["status"] == "REFUSE"
    assert refused["reason"] == "REFUSE_RETAINED_RUN_ID_BINDING"

    value = packet()
    retained = value["retained_cumulative_receipt"]
    assert isinstance(retained, dict)
    retained["prefixes"].append(copy.deepcopy(retained["prefixes"][2]))
    retained_hash = _reseal_retained(value)
    _rebind_child(value, retained=retained_hash)
    refused = run(value)
    assert refused["status"] == "REFUSE"
    assert refused["reason"] in {"REFUSE_RETAINED_PREFIX_TOPOLOGY", "REFUSE_RETAINED_PREFIX_SET"}

    value = packet()
    retained = value["retained_cumulative_receipt"]
    assert isinstance(retained, dict)
    retained["prefixes"][0]["stabilized"] = False
    retained_hash = _reseal_retained(value)
    _rebind_child(value, retained=retained_hash)
    refused = run(value)
    assert refused["status"] == "REFUSE"
    assert refused["reason"] == "REFUSE_RETAINED_PREFIX_1_TOPOLOGY"


def test_control_receipts_and_source_set_are_canonical_and_bound() -> None:
    value = packet()
    result = run(value)
    assert result["control_receipts"] == result["negative_controls"]
    assert [row["control_id"] for row in result["control_receipts"]] == list(runner.CONTROL_IDS)
    for row in result["control_receipts"]:
        assert row["source_hashes"] == result["source_hashes"]
        assert row["receipt_sha256"] == row["receipt_self_sha256"]
        assert runner.digest({key: item for key, item in row.items() if key not in {"receipt_sha256", "receipt_self_sha256"}}) == row["receipt_sha256"]
    tampered = copy.deepcopy(result)
    tampered["control_receipts"][0]["observed_reason"] = "forged"
    unsigned = {key: item for key, item in tampered["control_receipts"][0].items() if key not in {"receipt_sha256", "receipt_self_sha256"}}
    tampered["control_receipts"][0]["receipt_sha256"] = runner.digest(unsigned)
    tampered["control_receipts"][0]["receipt_self_sha256"] = tampered["control_receipts"][0]["receipt_sha256"]
    assert not runner.verify_receipt(tampered, value, root=PRODUCT_ROOT, authority_mode="FIXTURE")

    stale = packet()
    stale["expected_source_set_sha256"] = "0" * 64
    _rebind_child(stale, source_set=stale["expected_source_set_sha256"])
    refused = run(stale)
    assert refused["status"] == "REFUSE"
    assert refused["reason"] == "REFUSE_EXPECTED_SOURCE_SET_DRIFT"


def test_context_frontier_schema_and_flag_reseal_attacks_refuse() -> None:
    value = packet()
    epoch = value["context_epoch"]
    assert isinstance(epoch, dict)
    epoch["state"] = "STALE"
    value["context_epoch_sha256"] = runner.digest(epoch)
    _rebind_child(value, epoch=value["context_epoch_sha256"])
    refused = run(value)
    assert refused["status"] == "REFUSE"
    assert refused["reason"] == "REFUSE_CONTEXT_EPOCH_SCHEMA"

    value = packet()
    frontier = value["branch_frontier"]
    assert isinstance(frontier, dict)
    del frontier["activation_allowed"]
    value["branch_frontier_sha256"] = runner.digest(frontier)
    _rebind_child(value, frontier=value["branch_frontier_sha256"])
    refused = run(value)
    assert refused["status"] == "REFUSE"
    assert refused["reason"] == "REFUSE_BRANCH_FRONTIER_SCHEMA"


def test_context_epoch_sequence_parent_self_hash_and_extra_field_attacks_refuse() -> None:
    value = packet()
    epoch = value["context_epoch"]
    assert isinstance(epoch, dict)
    epoch["epoch_sequence"] += 1
    value["context_epoch_sha256"] = runner.digest(epoch)
    _rebind_child(value, epoch=value["context_epoch_sha256"])
    refused = run(value)
    assert refused["status"] == "REFUSE"
    assert refused["reason"] == "REFUSE_AUTHORITY_EPOCH_BINDING"

    value = packet()
    epoch = value["context_epoch"]
    assert isinstance(epoch, dict)
    parent = epoch["parent"]
    assert isinstance(parent, dict)
    parent["sha256"] = "0" * 64
    value["context_epoch_sha256"] = runner.digest(epoch)
    _rebind_child(value, epoch=value["context_epoch_sha256"])
    refused = run(value)
    assert refused["status"] == "REFUSE"
    assert refused["reason"] == "REFUSE_AUTHORITY_EPOCH_BINDING"

    value = packet()
    epoch = value["context_epoch"]
    assert isinstance(epoch, dict)
    epoch["epoch_digest"] = "0" * 64
    value["context_epoch_sha256"] = runner.digest(epoch)
    _rebind_child(value, epoch=value["context_epoch_sha256"])
    refused = run(value)
    assert refused["status"] == "REFUSE"
    assert refused["reason"] == "REFUSE_AUTHORITY_EPOCH_BINDING"

    value = packet()
    value["context_epoch_sha256"] = "0" * 64
    _rebind_child(value, epoch=value["context_epoch_sha256"])
    refused = run(value)
    assert refused["status"] == "REFUSE"
    assert refused["reason"] == "REFUSE_CONTEXT_EPOCH_DRIFT"

    value = packet()
    epoch = value["context_epoch"]
    assert isinstance(epoch, dict)
    epoch["extra"] = "must-refuse"
    value["context_epoch_sha256"] = runner.digest(epoch)
    _rebind_child(value, epoch=value["context_epoch_sha256"])
    refused = run(value)
    assert refused["status"] == "REFUSE"
    assert refused["reason"] == "REFUSE_CONTEXT_EPOCH_SCHEMA"


def test_refusal_preserves_completed_child_prefix(monkeypatch) -> None:
    value = packet()
    original = runner._verify_leaf
    calls = {"count": 0}

    def fail_second(module, payload, receipt):
        calls["count"] += 1
        if calls["count"] == 4:
            return False
        return original(module, payload, receipt)

    monkeypatch.setattr(runner, "_verify_leaf", fail_second)
    refused = run(value)
    assert refused["status"] == "REFUSE"
    assert refused["reason"] == "REFUSE_CHILD_RECEIPT_BINDING:name_exact_disagreement"
    assert refused["launched_child_order"] == ["bind_survivors"]
    assert refused["not_launched_child_ids"] == ["name_exact_disagreement", "design_finite_observable"]
    assert [row["label"] for row in refused["attestations"]][-1] == "before_child:name_exact_disagreement"


def test_prewrite_attestation_blocks_output_when_current_verifier_fails(tmp_path: Path, monkeypatch) -> None:
    output = tmp_path / "receipt.json"
    monkeypatch.setattr(runner, "verify_receipt", lambda *args, **kwargs: False)
    result = runner.run_wave(PRODUCT_ROOT, packet(), out_path=output, authority_mode="FIXTURE")
    assert result["status"] == "REFUSE"
    assert result["reason"] == "REFUSE_PREWRITE_ATTESTATION"
    assert not output.exists()


def test_child_omission_duplication_and_rebinding_refuse_before_launch() -> None:
    value = packet()
    del value["child_inputs"]["design_finite_observable"]
    refused = run(value)
    assert refused["status"] == "REFUSE"
    assert refused["reason"] == "REFUSE_CHILD_SET"
    value = packet()
    value["child_inputs"]["name_exact_disagreement"]["operation_id"] = runner.CHILD_OPERATIONS["bind_survivors"]
    refused = run(value)
    assert refused["status"] == "REFUSE"
    assert refused["reason"] == "REFUSE_CHILD_OPERATION:name_exact_disagreement"
    value = packet()
    value["child_inputs"]["bind_survivors"]["bindings"]["profile"] = "heavy"
    refused = run(value)
    assert refused["status"] == "REFUSE"
    assert refused["reason"] == "REFUSE_CHILD_REBOUND:bind_survivors"


def test_parent_and_child_cancellation_are_terminal_and_non_writing() -> None:
    value = packet()
    value["cancel_requested"] = True
    parent = run(value)
    assert parent["status"] == "CANCELLED"
    assert parent["children"] == []
    assert parent["frontier"] is None
    assert parent["writes_performed"] is False
    assert runner.verify_receipt(parent, value, root=PRODUCT_ROOT, authority_mode="FIXTURE")
    value = packet()
    child = value["child_inputs"]["name_exact_disagreement"]
    assert isinstance(child, dict)
    child["cancel_requested"] = True
    child["leaf_input"]["cancelled"] = True
    result = run(value)
    assert result["status"] == "CANCELLED"
    assert result["launched_child_order"] == ["bind_survivors", "name_exact_disagreement"]
    assert result["not_launched_child_ids"] == ["design_finite_observable"]
    assert result["frontier"] is None
    assert runner.verify_receipt(result, value, root=PRODUCT_ROOT, authority_mode="FIXTURE")


def test_path_escape_tamper_and_replay_are_refused_or_exact() -> None:
    value = packet()
    value["config_path"] = "../outside/CUMULATIVE_WAVE_SEQUENCE.json"
    refused = run(value)
    assert refused["status"] == "REFUSE"
    assert refused["reason"] == "REFUSE_PATH_ESCAPE:config"
    value = packet()
    result = run(value)
    assert runner.replay_receipt(result, value, root=PRODUCT_ROOT, authority_mode="FIXTURE")["status"] == "REPLAY_MATCH"
    assert runner.replay_receipt(result, value, root=PRODUCT_ROOT, authority_mode="FIXTURE")["digest_match"] is True
    tampered = copy.deepcopy(result)
    tampered["children"][0]["receipt"]["probe"]["name"] = "tampered"
    assert not runner.verify_receipt(tampered, value, root=PRODUCT_ROOT, authority_mode="FIXTURE")
    assert runner.replay_receipt(tampered, value, root=PRODUCT_ROOT, authority_mode="FIXTURE")["status"] == "REFUSE"
    tampered = copy.deepcopy(result)
    tampered["children"].append(copy.deepcopy(tampered["children"][0]))
    assert not runner.verify_receipt(tampered, value, root=PRODUCT_ROOT, authority_mode="FIXTURE")


def test_cli_writes_only_requested_receipt(tmp_path: Path) -> None:
    out = tmp_path / "receipt.json"
    proc = subprocess.run(
        [
            "python3",
            str(RUNNER_PATH),
            "--root",
            str(PRODUCT_ROOT),
            "--packet",
            str(CANDIDATE / "fixtures/strategy_discriminator_input_v1.json"),
            "--out",
            str(out),
            "--fixture-mode",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    value = json.loads(out.read_text(encoding="utf-8"))
    assert value["status"] == "HOLD_ORDER_MISMATCH"
    assert not list(tmp_path.glob("**/provider*"))
