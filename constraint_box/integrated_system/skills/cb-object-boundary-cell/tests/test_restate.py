from __future__ import annotations

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.restate import restate, replay, verify_receipt


def card() -> dict[str, object]:
    return {
        "target": "object-1",
        "schema": "constraintbox.object-boundary.v1",
        "operation": "cb-object-boundary-cell.v1",
        "operation_id": "cb-object-boundary-cell.v1",
        "object": "bounded object",
        "invariants": ["preserve identity"],
        "non_objectives": ["activation"],
        "forbidden_substitutions": ["winner"],
        "amendment_authority": "owner-only",
    }


def test_positive_restate_binds_target_and_keeps_claim_ceiling() -> None:
    receipt = restate(card())
    assert receipt["status"] == "RESTATED"
    assert receipt["boundary"]["object"] == "bounded object"
    assert receipt["target_binding"] == {"target": "object-1"}
    assert receipt["promotion_allowed"] is False
    assert receipt["writes_performed"] is False
    assert "truth" in receipt["claim_ceiling"]
    assert verify_receipt(receipt)


def test_missing_boundary_field_holds_with_source_reason() -> None:
    payload = {**card(), "non_objectives": None}
    payload.pop("non_objectives")
    receipt = restate(payload)
    assert receipt["status"] == "HOLD"
    assert receipt["reason"] == "HOLD_BOUNDARY"
    assert "non_objectives" in receipt["missing"]
    assert verify_receipt(receipt)


def test_authority_and_bad_binding_are_refused() -> None:
    authority = card()
    authority["winner"] = "object-1"
    assert restate(authority)["status"] == "REFUSE"
    bad_operation = card()
    bad_operation["operation"] = "activate"
    assert restate(bad_operation)["reason"] == "REFUSE_OPERATION_MISMATCH"


def test_replay_and_receipt_tamper_are_deterministic() -> None:
    first = restate(card())
    second = restate(copy.deepcopy(card()))
    assert first["receipt_sha256"] == second["receipt_sha256"]
    assert replay(card(), first)["status"] == "REPLAY_MATCH"
    tampered = copy.deepcopy(first)
    tampered["boundary"]["object"] = "changed"
    assert not verify_receipt(tampered)
    assert replay(card(), tampered)["reason"] == "REFUSE_RECEIPT_TAMPER"


def test_cancellation_is_no_write_and_does_not_emit_boundary(tmp_path: Path) -> None:
    sentinel = tmp_path / "sentinel"
    sentinel.write_text("unchanged", encoding="utf-8")
    payload = card()
    payload["cancelled"] = True
    receipt = restate(payload)
    assert receipt["status"] == "CANCELLED_NO_AUTHORITY"
    assert receipt["cancellation_state"] == "CANCELLED"
    assert receipt["receipt_written"] is False
    assert receipt["writes_performed"] is False
    assert sentinel.read_text(encoding="utf-8") == "unchanged"
    assert verify_receipt(receipt)


def test_strict_schema_case_variant_bounds_and_activation_attacks() -> None:
    for key in ("Schema", "schema_version", "unknown"):
        bad = card()
        bad[key] = 1
        assert restate(bad)["status"] == "REFUSE"
    bad_operation = card()
    bad_operation["operation"] = "CB-OBJECT-BOUNDARY-CELL.V1"
    assert restate(bad_operation)["reason"] == "REFUSE_OPERATION_MISMATCH"
    activation = card()
    activation["operation"] = "activate"
    assert restate(activation)["status"] == "REFUSE"
    oversized = card()
    oversized["object"] = "x" * 9000
    assert restate(oversized)["reason"] == "REFUSE_INPUT_BOUNDS"
    deep = card()
    nested: object = "x"
    for _ in range(10):
        nested = [nested]
    deep["invariants"] = [nested]
    assert restate(deep)["reason"] == "REFUSE_INPUT_BOUNDS"


def test_embedded_receipt_is_bound_to_input_identity_and_immutable_flags() -> None:
    receipt = restate(card())
    embedded = card()
    embedded["receipt"] = copy.deepcopy(receipt)
    assert restate(embedded)["status"] == "RESTATED"
    tampered = copy.deepcopy(receipt)
    tampered["target"] = "other"
    embedded["receipt"] = tampered
    assert restate(embedded)["reason"] == "REFUSE_RECEIPT_TAMPER"
    cancelled_alias = card()
    cancelled_alias["cancel_requested"] = True
    assert restate(cancelled_alias)["status"] == "REFUSE"


def test_operation_id_is_required_and_exact() -> None:
    missing = card()
    del missing["operation_id"]
    assert restate(missing)["reason"] == "REFUSE_OPERATION_ID_REQUIRED"
    wrong = card()
    wrong["operation_id"] = "alias"
    assert restate(wrong)["reason"] == "REFUSE_OPERATION_MISMATCH"
