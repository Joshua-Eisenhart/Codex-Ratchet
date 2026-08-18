from __future__ import annotations

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.sequence import sequence, replay, verify_receipt


def payload() -> dict[str, object]:
    return {
        "schema": "constraintbox.dependency-sequence.v1",
        "operation_id": "cb-dependency-sequence-cell.v1",
        "target": "plan-1",
        "operation": "cb-dependency-sequence-cell.v1",
        "steps": [
            {"id": "prepare", "prerequisites": [], "information_value": 1},
            {"id": "probe", "prerequisites": ["prepare"], "information_value": 9},
            {"id": "compare", "prerequisites": ["probe"], "information_value": 4},
        ],
    }


def test_positive_sequence_respects_prerequisites_before_information_value() -> None:
    receipt = sequence(payload())
    assert receipt["status"] == "SEQUENCED"
    assert receipt["order"] == ["prepare", "probe", "compare"]
    assert receipt["ordering_basis"] == "prerequisites_then_information_value"
    assert receipt["promotion_allowed"] is False
    assert receipt["writes_performed"] is False
    assert verify_receipt(receipt)


def test_empty_steps_holds_and_attractiveness_refuses() -> None:
    empty = {key: value for key, value in payload().items() if key != "steps"}
    assert sequence(empty)["reason"] == "HOLD_NO_STEPS"
    bad = payload()
    bad["ordered_by"] = "attractiveness"
    assert sequence(bad)["reason"] == "REFUSE_ATTRACTIVENESS_ORDER"


def test_cycle_and_unknown_prerequisite_are_structural_refusals() -> None:
    cycle = payload()
    cycle["steps"] = [
        {"id": "a", "prerequisites": ["b"], "information_value": 1},
        {"id": "b", "prerequisites": ["a"], "information_value": 2},
    ]
    assert sequence(cycle)["reason"] == "REFUSE_DEPENDENCY_CYCLE"
    unknown = payload()
    unknown["steps"] = [{"id": "a", "prerequisites": ["missing"], "information_value": 1}]
    assert sequence(unknown)["reason"] == "REFUSE_UNKNOWN_PREREQUISITE"


def test_replay_and_tamper_checks() -> None:
    first = sequence(payload())
    assert replay(copy.deepcopy(payload()), first)["status"] == "REPLAY_MATCH"
    tampered = copy.deepcopy(first)
    tampered["order"] = ["compare", "probe", "prepare"]
    assert not verify_receipt(tampered)
    assert replay(payload(), tampered)["reason"] == "REFUSE_RECEIPT_TAMPER"


def test_cancellation_is_no_write(tmp_path: Path) -> None:
    sentinel = tmp_path / "sentinel"
    sentinel.write_text("unchanged", encoding="utf-8")
    cancelled = payload()
    cancelled["cancelled"] = True
    receipt = sequence(cancelled)
    assert receipt["status"] == "CANCELLED_NO_AUTHORITY"
    assert receipt["receipt_written"] is False
    assert receipt["writes_performed"] is False
    assert sentinel.read_text(encoding="utf-8") == "unchanged"
    assert verify_receipt(receipt)


def test_duplicate_unknown_cycle_and_id_tie_attacks() -> None:
    duplicate = payload()
    duplicate["steps"].append({"id": "probe", "prerequisites": [], "information_value": 1})
    assert sequence(duplicate)["reason"] == "REFUSE_DUPLICATE_STEP"
    unknown = payload()
    unknown["steps"][1]["prerequisites"] = ["missing"]
    assert sequence(unknown)["reason"] == "REFUSE_UNKNOWN_PREREQUISITE"
    cycle = payload()
    cycle["steps"] = [
        {"id": "a", "prerequisites": ["b"], "information_value": 1},
        {"id": "b", "prerequisites": ["a"], "information_value": 1},
    ]
    assert sequence(cycle)["reason"] == "REFUSE_DEPENDENCY_CYCLE"
    tied = payload()
    tied["steps"] = [
        {"id": "b", "prerequisites": [], "information_value": 1},
        {"id": "a", "prerequisites": [], "information_value": 1},
    ]
    reversed_tied = copy.deepcopy(tied)
    reversed_tied["steps"] = list(reversed(reversed_tied["steps"]))
    assert sequence(tied)["order"] == sequence(reversed_tied)["order"] == ["a", "b"]


def test_strict_step_shape_ordering_case_bounds_and_embedded_receipt_attacks() -> None:
    malformed = payload()
    malformed["steps"][0]["extra"] = True
    assert sequence(malformed)["reason"] == "REFUSE_STEP_TYPE"
    attractive = payload()
    attractive["ordered_by"] = "AtTrAcTiVeNeSs"
    assert sequence(attractive)["reason"] == "REFUSE_ATTRACTIVENESS_ORDER"
    oversized = payload()
    oversized["steps"][0]["id"] = "x" * 9000
    assert sequence(oversized)["reason"] == "REFUSE_INPUT_BOUNDS"
    receipt = sequence(payload())
    embedded = payload()
    embedded["receipt"] = copy.deepcopy(receipt)
    assert sequence(embedded)["status"] == "SEQUENCED"
    tampered = copy.deepcopy(receipt)
    tampered["operation_id"] = "other"
    embedded["receipt"] = tampered
    assert sequence(embedded)["reason"] == "REFUSE_RECEIPT_TAMPER"


def test_operation_id_is_required_and_exact() -> None:
    missing = payload()
    del missing["operation_id"]
    assert sequence(missing)["reason"] == "REFUSE_OPERATION_ID_REQUIRED"
    wrong = payload()
    wrong["operation_id"] = "alias"
    assert sequence(wrong)["reason"] == "REFUSE_OPERATION_MISMATCH"
