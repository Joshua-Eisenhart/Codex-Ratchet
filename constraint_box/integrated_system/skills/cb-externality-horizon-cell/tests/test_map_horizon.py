from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.map_horizon import HORIZONS, MAX_STRING_BYTES, OPERATION, SCHEMA, map_horizon, verify_payload_receipt, verify_receipt


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "map_horizon.py"


def _payload() -> dict[str, object]:
    return {
        "schema": SCHEMA,
        "operation": OPERATION,
        "target": "object-1",
        **{key: "none" for key in HORIZONS},
    }


def test_positive_maps_only_displaced_horizons_and_binds_immutable_fields() -> None:
    payload = _payload()
    payload["evidence_quality"] = "failures erased from context"
    receipt = map_horizon(payload)
    assert receipt["status"] == "MAPPED"
    assert receipt["displaced"] == ["evidence_quality"]
    assert receipt["target"] == payload["target"]
    assert receipt["operation"] == OPERATION
    assert receipt["audit_only"] is True
    assert receipt["proposal_only"] is True
    assert receipt["promotion_allowed"] is False
    assert receipt["writes_performed"] is False
    assert receipt["provider_call_receipt"] is None
    assert verify_receipt(receipt)
    assert verify_receipt(receipt, payload)
    assert verify_payload_receipt(payload, receipt)


def test_missing_and_malformed_horizons_are_reason_specific() -> None:
    missing = _payload()
    del missing["wider_system"]
    receipt = map_horizon(missing)
    assert receipt["status"] == "HOLD"
    assert receipt["reason"] == "HOLD_HORIZON_MISSING"
    malformed = _payload()
    malformed["maintainers"] = None
    assert map_horizon(malformed)["reason"] == "REFUSE_HORIZON_TYPE"


def test_exact_schema_operation_target_and_unknown_keys_are_fail_closed() -> None:
    assert map_horizon([])["reason"] == "REFUSE_MALFORMED_INPUT"
    wrong_schema = _payload()
    wrong_schema["schema"] = "other.v1"
    assert map_horizon(wrong_schema)["reason"] == "REFUSE_SCHEMA_MISMATCH"
    wrong_operation = _payload()
    wrong_operation["operation"] = "map_displaced_costs"
    assert map_horizon(wrong_operation)["reason"] == "REFUSE_OPERATION_MISMATCH"
    alias = _payload()
    alias["operation_id"] = "alias"
    assert map_horizon(alias)["reason"] == "REFUSE_UNKNOWN_KEY"
    provider = _payload()
    provider["provider"] = "model"
    assert map_horizon(provider)["reason"] == "REFUSE_UNKNOWN_KEY"
    conflict = _payload()
    conflict["target_id"] = "object-1"
    assert map_horizon(conflict)["reason"] == "REFUSE_TARGET_CONFLICT"
    missing_target = _payload()
    del missing_target["target"]
    assert map_horizon(missing_target)["reason"] == "REFUSE_TARGET_REQUIRED"


def test_strict_cancellation_and_authority_inputs_refuse() -> None:
    malformed = _payload()
    malformed["cancelled"] = "false"
    assert map_horizon(malformed)["reason"] == "REFUSE_CANCEL_TYPE"
    promoted = _payload()
    promoted["promotion_allowed"] = True
    assert map_horizon(promoted)["reason"] == "REFUSE_AUTHORITY_SHAPED"


def test_depth_and_size_guard_runs_before_canonicalization() -> None:
    oversized = _payload()
    oversized["future_runs"] = "x" * (MAX_STRING_BYTES + 1)
    assert map_horizon(oversized)["reason"] == "REFUSE_INPUT_BOUNDS"
    deep = _payload()
    value: object = "x"
    for _ in range(12):
        value = [value]
    deep["future_runs"] = value
    assert map_horizon(deep)["reason"] == "REFUSE_INPUT_BOUNDS"


def test_replay_and_embedded_receipt_bind_current_payload() -> None:
    payload = _payload()
    first = map_horizon(payload)
    assert first == map_horizon(copy.deepcopy(payload))
    embedded = copy.deepcopy(payload)
    embedded["receipt"] = first
    assert map_horizon(embedded) == first
    changed_target = copy.deepcopy(embedded)
    changed_target["target"] = "object-2"
    assert map_horizon(changed_target)["reason"] == "REFUSE_RECEIPT_TAMPER"
    changed_receipt = copy.deepcopy(first)
    changed_receipt["proposal_only"] = False
    forged = copy.deepcopy(payload)
    forged["receipt"] = changed_receipt
    assert map_horizon(forged)["reason"] == "REFUSE_RECEIPT_TAMPER"


def test_cancellation_is_terminal_no_write() -> None:
    payload = _payload()
    payload["cancelled"] = True
    receipt = map_horizon(payload)
    assert receipt["status"] == "CANCELLED_NO_AUTHORITY"
    assert receipt["cancellation_state"] == "CANCELLED"
    assert receipt["writes_performed"] is False


def test_cli_accepts_explicit_json_without_writing(tmp_path: Path) -> None:
    before = sorted(tmp_path.iterdir())
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--json", json.dumps(_payload())],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert json.loads(proc.stdout)["status"] == "MAPPED"
    assert sorted(tmp_path.iterdir()) == before


def test_cli_rejects_duplicate_json_keys() -> None:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--json", '{"schema":"constraintbox.externality-horizon.v1","schema":"other.v1"}'],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2
    assert json.loads(proc.stdout)["reason"] == "REFUSE_MALFORMED_JSON"


def test_cli_rejects_12k_depth_without_traceback() -> None:
    raw = "[" * 12000 + "0" + "]" * 12000
    proc = subprocess.run([sys.executable, str(SCRIPT), "--json", raw], check=False, capture_output=True, text=True)
    assert proc.returncode == 2
    assert "Traceback" not in proc.stderr
    assert json.loads(proc.stdout)["reason"] == "REFUSE_MALFORMED_JSON"
