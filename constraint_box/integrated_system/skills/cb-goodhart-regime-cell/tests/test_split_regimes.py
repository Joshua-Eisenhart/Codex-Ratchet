from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.split_regimes import OPERATION, split_regimes, verify_receipt


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "split_regimes.py"


def _payload() -> dict:
    return {
        "target_id": "estate-1",
        "operation_id": OPERATION,
        "regressional": "PASS",
        "extremal": "FAIL",
        "causal": "PASS",
        "adversarial": "PASS",
    }


def test_split_reports_each_regime_and_failed_reason() -> None:
    receipt = split_regimes(_payload())
    assert receipt["status"] == "REGIMES_SPLIT"
    assert receipt["failed"] == ["extremal"]
    assert receipt["results"]["causal"] == "PASS"
    assert receipt["target_binding"]["target_id"] == "estate-1"
    assert receipt["promotion_allowed"] is False
    assert verify_receipt(receipt)


def test_collapsed_score_refuses_specific_reason() -> None:
    receipt = split_regimes({"operation_id": OPERATION, "target_id": "estate-1", "proxy_risk": 0.4})
    assert receipt["status"] == "REFUSE"
    assert receipt["reason"] == "REFUSE_COLLAPSED_SCORE"


def test_missing_regime_holds_specific_reason() -> None:
    receipt = split_regimes({"operation_id": OPERATION, "target_id": "estate-1", "regressional": "PASS"})
    assert receipt["status"] == "HOLD"
    assert receipt["reason"] == "HOLD_REGIME_MISSING"
    assert "adversarial" in receipt["missing"]


def test_malformed_and_authority_inputs_refuse() -> None:
    assert split_regimes(None)["reason"] == "REFUSE_MALFORMED_INPUT"
    assert split_regimes({**_payload(), "promotion_allowed": True})["reason"] == "REFUSE_AUTHORITY_SHAPED"
    assert split_regimes({**_payload(), "causal": {"status": "PASS"}})["reason"] == "REFUSE_MALFORMED_INPUT"
    assert split_regimes({**_payload(), "execute": True})["reason"] == "REFUSE_AUTHORITY_SHAPED"
    assert split_regimes({**_payload(), "unknown": "x"})["reason"] == "REFUSE_UNKNOWN_INPUT"
    assert split_regimes({**_payload(), "operation_id": "other"})["reason"] == "REFUSE_OPERATION_MISMATCH"
    assert split_regimes({**_payload(), "causal": None})["reason"] == "REFUSE_MALFORMED_INPUT"
    assert split_regimes({**_payload(), "causal": " "})["reason"] == "REFUSE_EMPTY_REGIME"


def test_replay_is_byte_stable() -> None:
    assert split_regimes(_payload()) == split_regimes(copy.deepcopy(_payload()))


def test_cancellation_is_passive_and_no_write(tmp_path: Path) -> None:
    receipt = split_regimes({**_payload(), "cancel_requested": True})
    assert receipt["status"] == "CANCELLED"
    assert receipt["cancellation_state"] == "CANCELLED"
    assert receipt["writes_performed"] is False
    assert receipt["receipt_written"] is False
    assert "receipt_sha256" not in receipt
    assert sorted(tmp_path.iterdir()) == []


def test_receipt_tamper_is_detectable() -> None:
    receipt = split_regimes(_payload())
    mutated = copy.deepcopy(receipt)
    mutated["failed"] = []
    assert not verify_receipt(mutated)


def test_receipt_binds_current_input_identity_and_immutable_bounds() -> None:
    payload = _payload()
    receipt = split_regimes(payload)
    assert verify_receipt(receipt, payload, target="estate-1", operation=OPERATION)
    assert not verify_receipt(receipt, {**payload, "target_id": "other"})
    altered = copy.deepcopy(receipt)
    altered["provider_call_receipt"] = {"status": "called"}
    assert not verify_receipt(altered)


def test_verifier_rehashes_changed_same_target_input_and_rejects_conflicts() -> None:
    payload = _payload()
    receipt = split_regimes(payload)
    old_digest = receipt["input_sha256"]
    changed = {**payload, "causal": "changed"}
    assert not verify_receipt(receipt, changed, input_sha256=old_digest)
    assert not verify_receipt(receipt, changed, current_input_sha256=old_digest)
    assert not verify_receipt(receipt, payload, input_sha256=old_digest, current_input_sha256="0" * 64)
    assert not verify_receipt(receipt, payload, target="estate-1", target_id="other")


def test_cli_accepts_explicit_json(tmp_path: Path) -> None:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--json", json.dumps(_payload())],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert json.loads(proc.stdout)["status"] == "REGIMES_SPLIT"
    assert sorted(tmp_path.iterdir()) == []
