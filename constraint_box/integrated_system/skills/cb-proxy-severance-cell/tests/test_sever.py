from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.sever import OPERATION, sever, verify_receipt


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "sever.py"


def _trial() -> dict:
    return {
        "target_id": "estate-1",
        "operation_id": OPERATION,
        "intervention": "delete hard cases",
        "proxy_before": 10,
        "proxy_after": 12,
        "object_before": 1,
        "object_after": 0,
    }


def test_score_up_object_down_is_severed() -> None:
    receipt = sever(_trial())
    assert receipt["status"] == "SEVERED"
    assert receipt["proxy_delta"] == 2.0
    assert receipt["object_delta"] == -1.0
    assert receipt["target_binding"]["target_id"] == "estate-1"
    assert receipt["promotion_allowed"] is False
    assert verify_receipt(receipt)


def test_both_rise_is_not_severance() -> None:
    trial = _trial()
    trial["object_after"] = 2
    assert sever(trial)["status"] == "NOT_FOUND"


def test_missing_measures_holds_specific_reason() -> None:
    receipt = sever({"operation_id": OPERATION, "target_id": "estate-1", "intervention": "probe", "proxy_before": 1})
    assert receipt["status"] == "HOLD"
    assert receipt["reason"] == "HOLD_MEASURES"


def test_malformed_and_authority_inputs_refuse() -> None:
    assert sever(None)["reason"] == "REFUSE_MALFORMED_INPUT"
    assert sever({**_trial(), "promotion_allowed": True})["reason"] == "REFUSE_AUTHORITY_SHAPED"
    assert sever({**_trial(), "execute": True})["reason"] == "REFUSE_AUTHORITY_SHAPED"
    assert sever({**_trial(), "unknown": "x"})["reason"] == "REFUSE_UNKNOWN_INPUT"
    assert sever({**_trial(), "operation_id": "other"})["reason"] == "REFUSE_OPERATION_MISMATCH"
    assert sever({**_trial(), "proxy_before": "10"})["reason"] == "REFUSE_MEASURE_TYPE"
    assert sever({**_trial(), "proxy_before": True})["reason"] == "REFUSE_MEASURE_TYPE"
    assert sever({**_trial(), "proxy_before": float("nan")})["reason"] == "REFUSE_MALFORMED_INPUT"
    assert sever({**_trial(), "proxy_before": 10**100})["reason"] == "REFUSE_MEASURE_OUT_OF_BOUNDS"
    assert sever({**_trial(), "intervention": " "})["reason"] == "REFUSE_INTERVENTION_REQUIRED"


def test_replay_is_byte_stable() -> None:
    assert sever(_trial()) == sever(copy.deepcopy(_trial()))


def test_cancellation_is_no_authority_and_no_write(tmp_path: Path) -> None:
    receipt = sever({**_trial(), "cancel_requested": True})
    assert receipt["status"] == "CANCELLED"
    assert receipt["writes_performed"] is False
    assert receipt["receipt_written"] is False
    assert "receipt_sha256" not in receipt
    assert sorted(tmp_path.iterdir()) == []


def test_receipt_tamper_is_detectable() -> None:
    receipt = sever(_trial())
    tampered = copy.deepcopy(receipt)
    tampered["proxy_delta"] = 999
    assert not verify_receipt(tampered)


def test_receipt_binds_current_input_identity_and_immutable_bounds() -> None:
    trial = _trial()
    receipt = sever(trial)
    assert verify_receipt(receipt, trial, target="estate-1", operation=OPERATION)
    assert not verify_receipt(receipt, {**trial, "target_id": "other"})
    altered = copy.deepcopy(receipt)
    altered["claim_ceiling"] = "promote"
    assert not verify_receipt(altered)


def test_verifier_rehashes_changed_same_target_input_and_rejects_conflicts() -> None:
    trial = _trial()
    receipt = sever(trial)
    old_digest = receipt["input_sha256"]
    changed = {**trial, "intervention": "different"}
    assert not verify_receipt(receipt, changed, input_sha256=old_digest)
    assert not verify_receipt(receipt, changed, current_input_sha256=old_digest)
    assert not verify_receipt(receipt, trial, input_sha256=old_digest, current_input_sha256="0" * 64)
    assert not verify_receipt(receipt, trial, target="estate-1", target_id="other")


def test_cli_accepts_explicit_json(tmp_path: Path) -> None:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--json", json.dumps(_trial())],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert json.loads(proc.stdout)["status"] == "SEVERED"
    assert sorted(tmp_path.iterdir()) == []
