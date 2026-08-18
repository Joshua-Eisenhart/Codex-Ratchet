from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.check_budget import MAX_BUDGET, OPERATION, SCHEMA, check_budget, verify_payload_receipt, verify_receipt


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_budget.py"


def _payload() -> dict[str, object]:
    return {
        "schema": SCHEMA,
        "operation": OPERATION,
        "target": "loop-1",
        "satisfice": "seed ADMIT",
        "diminishing_return": "no_improve",
        "stop": "ENOUGH",
        "cancellation_obeys": True,
        "time_budget": 10,
        "compute_budget": 100,
        "resource_budget": 4,
        "retry_budget": 1,
    }


def test_bounded_receipt_echoes_and_binds_all_dimensions() -> None:
    receipt = check_budget(_payload())
    assert receipt["status"] == "BOUNDED"
    assert receipt["budgets"] == {
        "time_budget": 10,
        "compute_budget": 100,
        "resource_budget": 4,
        "retry_budget": 1,
    }
    assert receipt["budget_binding_sha256"]
    assert receipt["promotion_allowed"] is False
    assert receipt["audit_only"] is True
    assert receipt["proposal_only"] is True
    assert receipt["writes_performed"] is False
    assert receipt["provider_call_receipt"] is None
    assert verify_receipt(receipt)
    assert verify_receipt(receipt, _payload())
    assert verify_payload_receipt(_payload(), receipt)


def test_resource_and_other_budget_dimensions_are_required() -> None:
    missing = _payload()
    del missing["resource_budget"]
    receipt = check_budget(missing)
    assert receipt["status"] == "HOLD"
    assert receipt["reason"] == "HOLD_BUDGET_INCOMPLETE"
    assert "resource_budget" in receipt["missing"]
    for key in ("time_budget", "compute_budget", "retry_budget"):
        candidate = _payload()
        del candidate[key]
        assert check_budget(candidate)["reason"] == "HOLD_BUDGET_INCOMPLETE"


def test_budget_types_and_bounds_are_reason_specific() -> None:
    non_bool = _payload()
    non_bool["cancellation_obeys"] = "true"
    assert check_budget(non_bool)["reason"] == "REFUSE_BUDGET_TYPE"
    negative = _payload()
    negative["resource_budget"] = -1
    assert check_budget(negative)["reason"] == "REFUSE_BUDGET_BOUND"
    over = _payload()
    over["time_budget"] = MAX_BUDGET + 1
    assert check_budget(over)["reason"] == "REFUSE_BUDGET_BOUND"
    resist = _payload()
    resist["resist_one_more_round"] = True
    assert check_budget(resist)["reason"] == "REFUSE_INFINITE_OPTIMIZATION"


def test_exact_schema_operation_target_unknown_and_authority_refuse() -> None:
    assert check_budget([])["reason"] == "REFUSE_MALFORMED_INPUT"
    bad_schema = _payload()
    bad_schema["schema"] = "other.v1"
    assert check_budget(bad_schema)["reason"] == "REFUSE_SCHEMA_MISMATCH"
    bad_op = _payload()
    bad_op["operation"] = "require_stop_and_cancel"
    assert check_budget(bad_op)["reason"] == "REFUSE_OPERATION_MISMATCH"
    alias = _payload()
    alias["operation_id"] = "budget-1"
    assert check_budget(alias)["reason"] == "REFUSE_UNKNOWN_KEY"
    provider = _payload()
    provider["provider"] = "model"
    assert check_budget(provider)["reason"] == "REFUSE_UNKNOWN_KEY"
    conflict = _payload()
    conflict["target_id"] = "loop-1"
    assert check_budget(conflict)["reason"] == "REFUSE_TARGET_CONFLICT"
    authority = _payload()
    authority["promotion_allowed"] = True
    assert check_budget(authority)["reason"] == "REFUSE_AUTHORITY_SHAPED"


def test_strict_cancellation_resistance_and_no_write() -> None:
    resist = _payload()
    resist["cancellation_obeys"] = False
    assert check_budget(resist)["reason"] == "REFUSE_CANCEL_RESIST"
    bad_cancel = _payload()
    bad_cancel["cancelled"] = 1
    assert check_budget(bad_cancel)["reason"] == "REFUSE_CANCEL_TYPE"
    cancelled = _payload()
    cancelled["cancelled"] = True
    receipt = check_budget(cancelled)
    assert receipt["status"] == "CANCELLED_NO_AUTHORITY"
    assert receipt["cancellation_state"] == "CANCELLED"
    assert receipt["writes_performed"] is False


def test_depth_size_replay_and_embedded_receipt_tamper() -> None:
    deep = _payload()
    value: object = "x"
    for _ in range(12):
        value = [value]
    deep["satisfice"] = value
    assert check_budget(deep)["reason"] == "REFUSE_INPUT_BOUNDS"
    first = check_budget(_payload())
    assert first == check_budget(copy.deepcopy(_payload()))
    embedded = _payload()
    embedded["receipt"] = first
    assert check_budget(embedded) == first
    changed = copy.deepcopy(first)
    changed["budgets"]["resource_budget"] = MAX_BUDGET
    forged = _payload()
    forged["receipt"] = changed
    assert check_budget(forged)["reason"] == "REFUSE_RECEIPT_TAMPER"


def test_cli_accepts_explicit_json_without_writing(tmp_path: Path) -> None:
    before = sorted(tmp_path.iterdir())
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--input", json.dumps(_payload())],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert json.loads(proc.stdout)["status"] == "BOUNDED"
    assert sorted(tmp_path.iterdir()) == before


def test_cli_rejects_12k_depth_without_traceback() -> None:
    raw = "[" * 12000 + "0" + "]" * 12000
    proc = subprocess.run([sys.executable, str(SCRIPT), "--json", raw], check=False, capture_output=True, text=True)
    assert proc.returncode == 2
    assert "Traceback" not in proc.stderr
    assert json.loads(proc.stdout)["reason"] == "REFUSE_MALFORMED_JSON"
