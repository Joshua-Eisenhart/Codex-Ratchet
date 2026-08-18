from __future__ import annotations

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.discriminate import discriminate, replay, verify_receipt


def payload() -> dict[str, object]:
    return {
        "schema": "constraintbox.strategy-discriminator.v1",
        "operation_id": "cb-strategy-discriminator-cell.v1",
        "target": "strategy-frontier-1",
        "operation": "cb-strategy-discriminator-cell.v1",
        "strategies": ["direct", "alternative"],
        "disagreement": "whether the observable changes under intervention",
        "probe": {"name": "finite-check", "finite": True, "cost": 2},
    }


def test_positive_designs_probe_without_strategy_selection() -> None:
    receipt = discriminate(payload())
    assert receipt["status"] == "DESIGNED"
    assert receipt["probe"]["name"] == "finite-check"
    assert receipt["strategies"] == ["direct", "alternative"]
    assert "winner" not in receipt
    assert "selected_strategy" not in receipt
    assert receipt["promotion_allowed"] is False
    assert receipt["writes_performed"] is False
    assert verify_receipt(receipt)


def test_candidate_selection_is_cheapest_finite_and_deterministic() -> None:
    candidate_payload = payload()
    candidate_payload.pop("probe")
    candidate_payload["probe_candidates"] = [
        {"name": "expensive", "finite": True, "cost": 5},
        {"name": "cheap", "finite": True, "cost": 1},
    ]
    receipt = discriminate(candidate_payload)
    assert receipt["status"] == "DESIGNED"
    assert receipt["probe"]["name"] == "cheap"
    assert receipt["probe_cost"] == 1
    assert verify_receipt(receipt)


def test_one_strategy_holds_and_nonfinite_probe_refuses() -> None:
    one = payload()
    one["strategies"] = ["direct"]
    assert discriminate(one)["reason"] == "HOLD_NO_DISAGREEMENT"
    nonfinite = payload()
    nonfinite["probe"] = {"name": "unbounded", "finite": False, "cost": 1}
    assert discriminate(nonfinite)["reason"] == "REFUSE_NONFINITE_PROBE"


def test_authority_shaped_input_and_missing_probe_are_safe() -> None:
    authority = payload()
    authority["winner"] = "direct"
    assert discriminate(authority)["status"] == "REFUSE"
    missing = payload()
    missing.pop("probe")
    assert discriminate(missing)["reason"] == "HOLD_NO_PROBE"


def test_replay_and_tamper_checks() -> None:
    first = discriminate(payload())
    assert replay(copy.deepcopy(payload()), first)["status"] == "REPLAY_MATCH"
    tampered = copy.deepcopy(first)
    tampered["probe"]["name"] = "changed"
    assert not verify_receipt(tampered)
    assert replay(payload(), tampered)["reason"] == "REFUSE_RECEIPT_TAMPER"


def test_cancellation_is_no_write(tmp_path: Path) -> None:
    sentinel = tmp_path / "sentinel"
    sentinel.write_text("unchanged", encoding="utf-8")
    cancelled = payload()
    cancelled["cancelled"] = True
    receipt = discriminate(cancelled)
    assert receipt["status"] == "CANCELLED_NO_AUTHORITY"
    assert receipt["receipt_written"] is False
    assert receipt["writes_performed"] is False
    assert sentinel.read_text(encoding="utf-8") == "unchanged"
    assert verify_receipt(receipt)


def test_strategy_distinctness_finite_literal_and_cost_bounds() -> None:
    duplicate = payload()
    duplicate["strategies"] = ["Direct", "direct"]
    assert discriminate(duplicate)["reason"] == "REFUSE_DUPLICATE_STRATEGY"
    empty = payload()
    empty["strategies"] = ["direct", " "]
    assert discriminate(empty)["reason"] == "REFUSE_STRATEGY_TYPE"
    nonliteral = payload()
    nonliteral["probe"] = {"name": "p", "finite": 1, "cost": 1}
    assert discriminate(nonliteral)["reason"] == "REFUSE_NONFINITE_PROBE"
    unbounded = payload()
    unbounded["probe"] = {"name": "p", "finite": True, "cost": 1_000_001}
    assert discriminate(unbounded)["reason"] == "REFUSE_PROBE_COST"
    ambiguous = payload()
    ambiguous["probe_candidates"] = [payload()["probe"]]
    assert discriminate(ambiguous)["reason"] == "REFUSE_PROBE_AMBIGUOUS"


def test_unknown_case_bounds_and_embedded_receipt_attacks() -> None:
    for key in ("Schema", "schema_version", "unknown", "winner"):
        bad = payload()
        bad[key] = 1
        assert discriminate(bad)["status"] == "REFUSE"
    oversized = payload()
    oversized["disagreement"] = "x" * 9000
    assert discriminate(oversized)["reason"] == "REFUSE_INPUT_BOUNDS"
    receipt = discriminate(payload())
    embedded = payload()
    embedded["receipt"] = copy.deepcopy(receipt)
    assert discriminate(embedded)["status"] == "DESIGNED"
    tampered = copy.deepcopy(receipt)
    tampered["activated"] = True
    embedded["receipt"] = tampered
    assert discriminate(embedded)["reason"] == "REFUSE_RECEIPT_TAMPER"


def test_operation_id_is_required_and_exact() -> None:
    missing = payload()
    del missing["operation_id"]
    assert discriminate(missing)["reason"] == "REFUSE_OPERATION_ID_REQUIRED"
    wrong = payload()
    wrong["operation_id"] = "alias"
    assert discriminate(wrong)["reason"] == "REFUSE_OPERATION_MISMATCH"
