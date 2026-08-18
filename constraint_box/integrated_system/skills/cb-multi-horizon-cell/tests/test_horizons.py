from __future__ import annotations

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.horizons import horizons, replay, verify_receipt


def payload() -> dict[str, object]:
    return {
        "schema": "constraintbox.multi-horizon.v1",
        "operation_id": "cb-multi-horizon-cell.v1",
        "target": "strategy-1",
        "operation": "cb-multi-horizon-cell.v1",
        "immediate": "effect now",
        "downstream": "effect later",
        "maintenance": "cost bounded",
        "long_horizon": "what persists",
    }


def test_positive_scan_binds_all_horizons_without_impact_claim() -> None:
    receipt = horizons(payload())
    assert receipt["status"] == "SCANNED"
    assert set(receipt["horizons"]) == {"immediate", "downstream", "maintenance", "long_horizon"}
    assert receipt["target_binding"] == {"target": "strategy-1"}
    assert receipt["promotion_allowed"] is False
    assert receipt["writes_performed"] is False
    assert "impact" in receipt["claim_ceiling"]
    assert verify_receipt(receipt)


def test_missing_long_horizon_holds() -> None:
    bad = payload()
    bad.pop("long_horizon")
    receipt = horizons(bad)
    assert receipt["reason"] == "HOLD_HORIZON"
    assert receipt["missing"] == ["long_horizon"]
    assert verify_receipt(receipt)


def test_bad_target_and_authority_field_refuse() -> None:
    bad_target = payload()
    bad_target["target"] = ""
    assert horizons(bad_target)["reason"] == "REFUSE_TARGET_REQUIRED"
    authority = payload()
    authority["decision"] = "choose"
    assert horizons(authority)["status"] == "REFUSE"


def test_replay_and_tamper_checks() -> None:
    first = horizons(payload())
    assert replay(copy.deepcopy(payload()), first)["status"] == "REPLAY_MATCH"
    tampered = copy.deepcopy(first)
    tampered["horizons"]["immediate"] = "changed"
    assert not verify_receipt(tampered)
    assert replay(payload(), tampered)["reason"] == "REFUSE_RECEIPT_TAMPER"


def test_cancellation_is_no_write(tmp_path: Path) -> None:
    sentinel = tmp_path / "sentinel"
    sentinel.write_text("unchanged", encoding="utf-8")
    cancelled = payload()
    cancelled["cancelled"] = True
    receipt = horizons(cancelled)
    assert receipt["status"] == "CANCELLED_NO_AUTHORITY"
    assert receipt["receipt_written"] is False
    assert receipt["writes_performed"] is False
    assert sentinel.read_text(encoding="utf-8") == "unchanged"
    assert verify_receipt(receipt)


def test_complete_exact_horizons_reject_blank_unknown_and_case_variants() -> None:
    blank = payload()
    blank["maintenance"] = "  "
    assert horizons(blank)["reason"] == "REFUSE_HORIZON_TYPE"
    unknown = payload()
    unknown["Maintenance"] = "duplicate"
    assert horizons(unknown)["reason"] == "REFUSE_UNKNOWN_KEY"
    schema_case = payload()
    schema_case["Schema"] = schema_case.pop("schema")
    assert horizons(schema_case)["reason"] == "REFUSE_UNKNOWN_KEY"
    alias = payload()
    alias["operation_id"] = "alias"
    assert horizons(alias)["reason"] == "REFUSE_OPERATION_MISMATCH"
    provider = payload()
    provider["provider"] = "model"
    assert horizons(provider)["reason"] == "REFUSE_UNKNOWN_KEY"
    oversized = payload()
    oversized["immediate"] = "x" * 9000
    assert horizons(oversized)["reason"] == "REFUSE_INPUT_BOUNDS"


def test_embedded_receipt_identity_and_cancellation_alias_are_bound() -> None:
    receipt = horizons(payload())
    embedded = payload()
    embedded["receipt"] = copy.deepcopy(receipt)
    assert horizons(embedded)["status"] == "SCANNED"
    tampered = copy.deepcopy(receipt)
    tampered["target"] = "other"
    embedded["receipt"] = tampered
    assert horizons(embedded)["reason"] == "REFUSE_RECEIPT_TAMPER"
    alias = payload()
    alias["cancel_requested"] = True
    assert horizons(alias)["status"] == "REFUSE"


def test_operation_id_is_required_and_exact() -> None:
    missing = payload()
    del missing["operation_id"]
    assert horizons(missing)["reason"] == "REFUSE_OPERATION_ID_REQUIRED"
    wrong = payload()
    wrong["operation_id"] = "alias"
    assert horizons(wrong)["reason"] == "REFUSE_OPERATION_MISMATCH"
