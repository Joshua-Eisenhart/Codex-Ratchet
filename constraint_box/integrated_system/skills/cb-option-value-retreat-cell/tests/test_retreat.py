from __future__ import annotations

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.retreat import retreat, replay, verify_receipt


def payload() -> dict[str, object]:
    return {
        "schema": "constraintbox.option-retreat.v1",
        "operation_id": "cb-option-value-retreat-cell.v1",
        "target": "strategy-1",
        "operation": "cb-option-value-retreat-cell.v1",
        "reversible_probes": [{"name": "unit check", "scope": "read_only", "reversible": True, "undo_operation": "reset fixture", "restored_state_check": "fixture digest matches"}],
        "irreversible_commitments": [],
        "hold_conditions": ["missing evidence"],
        "retreat_conditions": ["probe fails"],
        "preserved_options": ["stop"],
    }


def test_positive_map_is_non_authoritative() -> None:
    receipt = retreat(payload())
    assert receipt["status"] == "MAPPED"
    assert set(receipt["map"]) == {"reversible_probes", "irreversible_commitments", "hold_conditions", "retreat_conditions", "preserved_options"}
    assert receipt["target_binding"] == {"target": "strategy-1"}
    assert receipt["promotion_allowed"] is False
    assert receipt["writes_performed"] is False
    assert verify_receipt(receipt)


def test_irreversible_without_retreat_holds() -> None:
    bad = payload()
    bad["irreversible_commitments"] = ["promote pack"]
    bad["retreat_conditions"] = []
    receipt = retreat(bad)
    assert receipt["reason"] == "HOLD_REVERSIBILITY"
    assert receipt["promotion_allowed"] is False
    assert verify_receipt(receipt)


def test_missing_field_and_authority_field_refuse_or_hold() -> None:
    missing = payload()
    missing.pop("preserved_options")
    assert retreat(missing)["reason"] == "HOLD_RETREAT_MAP"
    authority = payload()
    authority["selected_strategy"] = "commit"
    assert retreat(authority)["status"] == "REFUSE"


def test_replay_and_tamper_checks() -> None:
    first = retreat(payload())
    assert replay(copy.deepcopy(payload()), first)["status"] == "REPLAY_MATCH"
    tampered = copy.deepcopy(first)
    tampered["map"]["preserved_options"] = ["changed"]
    assert not verify_receipt(tampered)
    assert replay(payload(), tampered)["reason"] == "REFUSE_RECEIPT_TAMPER"


def test_cancellation_is_no_write(tmp_path: Path) -> None:
    sentinel = tmp_path / "sentinel"
    sentinel.write_text("unchanged", encoding="utf-8")
    cancelled = payload()
    cancelled["cancelled"] = True
    receipt = retreat(cancelled)
    assert receipt["status"] == "CANCELLED_NO_AUTHORITY"
    assert receipt["receipt_written"] is False
    assert receipt["writes_performed"] is False
    assert sentinel.read_text(encoding="utf-8") == "unchanged"
    assert verify_receipt(receipt)


def test_probe_boolean_name_hidden_irreversibility_and_link_attacks() -> None:
    bad_probe = payload()
    bad_probe["reversible_probes"] = [{"name": "probe", "scope": "read_only", "reversible": False, "undo_operation": "reset", "restored_state_check": "digest"}]
    assert retreat(bad_probe)["reason"] == "REFUSE_HIDDEN_IRREVERSIBILITY"
    malformed_probe = payload()
    malformed_probe["reversible_probes"] = [{"name": "probe", "scope": "read_only", "reversible": "true", "undo_operation": "reset", "restored_state_check": "digest"}]
    assert retreat(malformed_probe)["reason"] == "REFUSE_PROBE_TYPE"
    hidden = payload()
    hidden["reversible_probes"] = ["push-production"]
    assert retreat(hidden)["reason"] == "REFUSE_HIDDEN_IRREVERSIBILITY"
    unlinked = payload()
    unlinked["irreversible_commitments"] = ["ship"]
    unlinked["retreat_conditions"] = ["stop if evidence fails"]
    assert retreat(unlinked)["reason"] == "REFUSE_RETREAT_LINK"
    linked = payload()
    linked["irreversible_commitments"] = ["ship"]
    linked["retreat_conditions"] = [{"commitment": "ship", "condition": "stop if evidence fails"}]
    assert retreat(linked)["status"] == "MAPPED"


def test_unknown_case_variant_bounds_and_embedded_receipt_attacks() -> None:
    for key in ("Schema", "schema_version", "unknown"):
        bad = payload()
        bad[key] = 1
        assert retreat(bad)["status"] == "REFUSE"
    oversized = payload()
    oversized["hold_conditions"] = ["x" * 9000]
    assert retreat(oversized)["reason"] == "REFUSE_INPUT_BOUNDS"
    receipt = retreat(payload())
    embedded = payload()
    embedded["receipt"] = copy.deepcopy(receipt)
    assert retreat(embedded)["status"] == "MAPPED"
    tampered = copy.deepcopy(receipt)
    tampered["writes_performed"] = True
    embedded["receipt"] = tampered
    assert retreat(embedded)["reason"] == "REFUSE_RECEIPT_TAMPER"


def test_operation_id_is_required_and_exact() -> None:
    missing = payload()
    del missing["operation_id"]
    assert retreat(missing)["reason"] == "REFUSE_OPERATION_ID_REQUIRED"
    wrong = payload()
    wrong["operation_id"] = "alias"
    assert retreat(wrong)["reason"] == "REFUSE_OPERATION_MISMATCH"
