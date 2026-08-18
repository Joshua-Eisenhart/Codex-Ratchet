from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.attack import ATTACKS, OPERATION, attack, verify_receipt


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "attack.py"


def _blocked() -> dict:
    return {
        "target_id": "estate-1",
        "operation_id": OPERATION,
        "attempts": {key: "BLOCKED" for key in ATTACKS},
    }


def test_all_blocked_is_bounded_audit() -> None:
    receipt = attack(_blocked())
    assert receipt["status"] == "BLOCKED"
    assert receipt["succeeded"] == []
    assert receipt["target_binding"]["target_id"] == "estate-1"
    assert receipt["promotion_allowed"] is False
    assert verify_receipt(receipt)


def test_test_deletion_success_refuses_specific_reason() -> None:
    payload = _blocked()
    payload["attempts"]["test_deletion"] = "SUCCEEDED"
    receipt = attack(payload)
    assert receipt["status"] == "REFUSE"
    assert receipt["reason"] == "REFUSE_ADVERSARY_SUCCESS"
    assert receipt["succeeded"] == ["test_deletion"]


def test_missing_attack_holds_specific_reason() -> None:
    receipt = attack({"operation_id": OPERATION, "target_id": "estate-1", "attempts": {"reward_hacking": "BLOCKED"}})
    assert receipt["status"] == "HOLD"
    assert receipt["reason"] == "HOLD_ATTACK_COVERAGE"
    assert "receipt_forgery" in receipt["missing"]


def test_malformed_and_authority_inputs_refuse() -> None:
    assert attack([])["reason"] == "REFUSE_MALFORMED_INPUT"
    assert attack({**_blocked(), "promotion_allowed": True})["reason"] == "REFUSE_AUTHORITY_SHAPED"
    assert attack({**_blocked(), "commit": True})["reason"] == "REFUSE_AUTHORITY_SHAPED"
    assert attack({**_blocked(), "unknown": "x"})["reason"] == "REFUSE_UNKNOWN_INPUT"
    assert attack({**_blocked(), "operation_id": "other"})["reason"] == "REFUSE_OPERATION_MISMATCH"
    bad = _blocked()
    bad["attempts"]["test_deletion"] = {"status": "BLOCKED"}
    assert attack(bad)["reason"] == "REFUSE_ATTACK_STATUS"
    bad = _blocked()
    bad["attempts"]["not_an_attack"] = "BLOCKED"
    assert attack(bad)["reason"] == "REFUSE_UNKNOWN_ATTACK"
    bad = _blocked()
    bad["attempts"]["test_deletion"] = "MAYBE"
    assert attack(bad)["reason"] == "REFUSE_ATTACK_STATUS"


def test_replay_is_byte_stable() -> None:
    assert attack(_blocked()) == attack(copy.deepcopy(_blocked()))


def test_cancellation_is_passive_and_no_write(tmp_path: Path) -> None:
    receipt = attack({**_blocked(), "cancel_requested": True})
    assert receipt["status"] == "CANCELLED"
    assert receipt["writes_performed"] is False
    assert receipt["receipt_written"] is False
    assert "receipt_sha256" not in receipt
    assert sorted(tmp_path.iterdir()) == []


def test_receipt_tamper_is_detectable() -> None:
    receipt = attack(_blocked())
    tampered = copy.deepcopy(receipt)
    tampered["succeeded"] = ["reward_hacking"]
    assert not verify_receipt(tampered)


def test_succeeded_order_is_canonical() -> None:
    payload = _blocked()
    payload["attempts"]["resist_cancellation"] = "SUCCEEDED"
    payload["attempts"]["reward_hacking"] = "SUCCEEDED"
    assert attack(payload)["succeeded"] == ["reward_hacking", "resist_cancellation"]


def test_receipt_binds_current_input_identity_and_immutable_bounds() -> None:
    payload = _blocked()
    receipt = attack(payload)
    assert verify_receipt(receipt, payload, target="estate-1", operation=OPERATION)
    assert not verify_receipt(receipt, {**payload, "target_id": "other"})
    altered = copy.deepcopy(receipt)
    altered["provider_call_receipt"] = {"called": True}
    assert not verify_receipt(altered)


def test_verifier_rehashes_changed_same_target_input_and_rejects_conflicts() -> None:
    payload = _blocked()
    receipt = attack(payload)
    old_digest = receipt["input_sha256"]
    changed = copy.deepcopy(payload)
    changed["attempts"]["reward_hacking"] = "SUCCEEDED"
    assert not verify_receipt(receipt, changed, input_sha256=old_digest)
    assert not verify_receipt(receipt, changed, current_input_sha256=old_digest)
    assert not verify_receipt(receipt, payload, input_sha256=old_digest, current_input_sha256="0" * 64)
    assert not verify_receipt(receipt, payload, target="estate-1", target_id="other")


def test_cli_accepts_explicit_json(tmp_path: Path) -> None:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--json", json.dumps(_blocked())],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert json.loads(proc.stdout)["status"] == "BLOCKED"
    assert sorted(tmp_path.iterdir()) == []
