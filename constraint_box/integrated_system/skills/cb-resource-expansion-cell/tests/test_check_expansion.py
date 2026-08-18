from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.check_expansion import AXES, OPERATION, check_expansion, verify_receipt


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_expansion.py"


def _inside() -> dict:
    axes = {
        "tools": ["sha256"],
        "write_scope": ["receipts/management_plane"],
        "compute": 1,
        "time": 10,
        "persistence": ["ledger.jsonl"],
        "permissions": ["read"],
        "external_actions": [],
    }
    return {"target_id": "estate-1", "operation_id": OPERATION, "authorized": axes, "used": copy.deepcopy(axes)}


def test_inside_authorization_is_bounded() -> None:
    receipt = check_expansion(_inside())
    assert receipt["status"] == "INSIDE"
    assert receipt["expanded"] == []
    assert receipt["target_binding"]["target_id"] == "estate-1"
    assert receipt["promotion_allowed"] is False
    assert verify_receipt(receipt)


def test_write_scope_expansion_refuses_specific_reason() -> None:
    payload = _inside()
    payload["used"] = copy.deepcopy(payload["used"])
    payload["used"]["write_scope"] = ["receipts/management_plane", "/etc"]
    receipt = check_expansion(payload)
    assert receipt["status"] == "REFUSE"
    assert receipt["reason"] == "REFUSE_SCOPE_EXPANSION"
    assert receipt["expanded"] == [{"write_scope": ["/etc"]}]


def test_missing_axis_holds_specific_reason() -> None:
    payload = _inside()
    del payload["used"]["time"]
    receipt = check_expansion(payload)
    assert receipt["status"] == "HOLD"
    assert receipt["reason"] == "HOLD_AXIS_MISSING"
    assert receipt["missing"] == "time"


def test_malformed_and_authority_inputs_refuse() -> None:
    assert check_expansion(None)["reason"] == "REFUSE_MALFORMED_INPUT"
    assert check_expansion({**_inside(), "promotion_allowed": True})["reason"] == "REFUSE_AUTHORITY_SHAPED"
    assert check_expansion({**_inside(), "execute": True})["reason"] == "REFUSE_AUTHORITY_SHAPED"
    assert check_expansion({**_inside(), "unknown": "x"})["reason"] == "REFUSE_UNKNOWN_INPUT"
    assert check_expansion({**_inside(), "operation_id": "other"})["reason"] == "REFUSE_OPERATION_MISMATCH"
    payload = _inside()
    payload["used"]["compute"] = [1]
    assert check_expansion(payload)["reason"] == "REFUSE_AXIS_TYPE"
    payload = _inside()
    payload["authorized"]["new_axis"] = []
    assert check_expansion(payload)["reason"] == "REFUSE_UNKNOWN_AXIS"
    payload = _inside()
    payload["used"]["compute"] = 1.0
    assert check_expansion(payload)["reason"] == "REFUSE_AXIS_TYPE"
    payload = _inside()
    payload["used"]["compute"] = 10**100
    assert check_expansion(payload)["reason"] == "REFUSE_AXIS_OUT_OF_BOUNDS"
    payload = _inside()
    payload["authorized"]["compute"] = -1
    assert check_expansion(payload)["reason"] == "REFUSE_AXIS_OUT_OF_BOUNDS"
    payload = _inside()
    payload["used"]["time"] = -1
    assert check_expansion(payload)["reason"] == "REFUSE_AXIS_OUT_OF_BOUNDS"


def test_replay_is_byte_stable() -> None:
    assert check_expansion(_inside()) == check_expansion(copy.deepcopy(_inside()))


def test_cancellation_is_passive_and_no_write(tmp_path: Path) -> None:
    receipt = check_expansion({**_inside(), "cancel_requested": True})
    assert receipt["status"] == "CANCELLED"
    assert receipt["writes_performed"] is False
    assert receipt["receipt_written"] is False
    assert "receipt_sha256" not in receipt
    assert sorted(tmp_path.iterdir()) == []


def test_receipt_tamper_is_detectable() -> None:
    receipt = check_expansion(_inside())
    tampered = copy.deepcopy(receipt)
    tampered["expanded"] = [{"time": {"authorized": 1, "used": 999}}]
    assert not verify_receipt(tampered)


def test_receipt_binds_current_input_identity_and_immutable_bounds() -> None:
    payload = _inside()
    receipt = check_expansion(payload)
    assert verify_receipt(receipt, payload, target="estate-1", operation=OPERATION)
    assert not verify_receipt(receipt, {**payload, "target_id": "other"})
    altered = copy.deepcopy(receipt)
    altered["writes_performed"] = True
    assert not verify_receipt(altered)


def test_verifier_rehashes_changed_same_target_input_and_rejects_conflicts() -> None:
    payload = _inside()
    receipt = check_expansion(payload)
    old_digest = receipt["input_sha256"]
    changed = copy.deepcopy(payload)
    changed["used"]["time"] = 9
    assert not verify_receipt(receipt, changed, input_sha256=old_digest)
    assert not verify_receipt(receipt, changed, current_input_sha256=old_digest)
    assert not verify_receipt(receipt, payload, input_sha256=old_digest, current_input_sha256="0" * 64)
    assert not verify_receipt(receipt, payload, target="estate-1", target_id="other")


def test_cli_accepts_explicit_json(tmp_path: Path) -> None:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--json", json.dumps(_inside())],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert json.loads(proc.stdout)["status"] == "INSIDE"
    assert sorted(tmp_path.iterdir()) == []
