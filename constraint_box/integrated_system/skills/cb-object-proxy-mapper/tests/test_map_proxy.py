from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.map_proxy import OPERATION, map_proxy, verify_receipt


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "map_proxy.py"


def _card() -> dict:
    return {
        "target_id": "seed-1",
        "operation_id": OPERATION,
        "object": "finite Light seed F",
        "proxy": "estate score",
        "measurement": "score_estate.py",
        "consumer": "self-loop keep",
        "allowed_inference": "score rose under an unchanged Light gate",
        "preserves": ["valid_v1 count"],
        "loses": ["semantic correctness"],
    }


def test_maps_full_chain_and_binds_identity() -> None:
    receipt = map_proxy(_card())
    assert receipt["status"] == "MAPPED"
    assert receipt["operation_id"] == OPERATION
    assert receipt["target_binding"]["target_id"] == "seed-1"
    assert "semantic correctness" in receipt["loses"]
    assert receipt["promotion_allowed"] is False
    assert verify_receipt(receipt)


def test_incomplete_chain_holds_with_reason() -> None:
    receipt = map_proxy({"operation_id": OPERATION, "target_id": "seed-1", "object": "F"})
    assert receipt["status"] == "HOLD"
    assert receipt["reason"] == "HOLD_CHAIN_INCOMPLETE"
    assert set(receipt["missing"]) == {"proxy", "measurement", "consumer", "allowed_inference"}
    assert receipt["promotion_allowed"] is False


def test_malformed_and_authority_shaped_inputs_refuse() -> None:
    assert map_proxy([])["reason"] == "REFUSE_MALFORMED_INPUT"
    assert map_proxy({**_card(), "promotion_allowed": True})["reason"] == "REFUSE_AUTHORITY_SHAPED"
    assert map_proxy({**_card(), "activated": True})["reason"] == "REFUSE_AUTHORITY_SHAPED"
    assert map_proxy({**_card(), "write": True})["reason"] == "REFUSE_AUTHORITY_SHAPED"
    assert map_proxy({**_card(), "unknown": "x"})["reason"] == "REFUSE_UNKNOWN_INPUT"
    assert map_proxy({**_card(), "operation_id": "other"})["reason"] == "REFUSE_OPERATION_MISMATCH"
    assert map_proxy({**_card(), "operation": OPERATION})["reason"] == "REFUSE_OPERATION_MISMATCH"


def test_boundary_empty_and_bad_list_refuse() -> None:
    assert map_proxy({**_card(), "object": ""})["reason"] == "HOLD_CHAIN_INCOMPLETE"
    assert map_proxy({**_card(), "target_id": " "})["reason"] == "REFUSE_MALFORMED_INPUT"
    assert map_proxy({**_card(), "target": "seed-2"})["reason"] == "REFUSE_TARGET_MISMATCH"
    assert map_proxy({**_card(), "proxy": 5})["reason"] == "REFUSE_MALFORMED_INPUT"
    assert map_proxy({**_card(), "loses": "semantic correctness"})["reason"] == "REFUSE_MALFORMED_INPUT"


def test_replay_is_byte_stable() -> None:
    first = map_proxy(_card())
    second = map_proxy(copy.deepcopy(_card()))
    assert first == second


def test_cancellation_is_no_authority_and_no_write(tmp_path: Path) -> None:
    before = sorted(tmp_path.iterdir())
    receipt = map_proxy({**_card(), "cancel_requested": True})
    assert receipt["status"] == "CANCELLED"
    assert receipt["cancellation_state"] == "CANCELLED"
    assert receipt["writes_performed"] is False
    assert receipt["receipt_written"] is False
    assert "receipt_sha256" not in receipt
    assert sorted(tmp_path.iterdir()) == before


def test_receipt_tamper_is_detectable() -> None:
    receipt = map_proxy(_card())
    tampered = copy.deepcopy(receipt)
    tampered["status"] = "PROMOTED"
    assert not verify_receipt(tampered)


def test_receipt_binds_current_input_identity_and_immutable_bounds() -> None:
    card = _card()
    receipt = map_proxy(card)
    assert verify_receipt(receipt, card, target="seed-1", operation=OPERATION)
    assert not verify_receipt(receipt, {**card, "target_id": "other"})
    assert not verify_receipt(receipt, card, target="other")
    altered = copy.deepcopy(receipt)
    altered["writes_performed"] = True
    assert not verify_receipt(altered)


def test_verifier_rehashes_changed_same_target_input_and_rejects_conflicts() -> None:
    card = _card()
    receipt = map_proxy(card)
    old_digest = receipt["input_sha256"]
    changed = {**card, "allowed_inference": "changed"}
    assert not verify_receipt(receipt, changed, input_sha256=old_digest)
    assert not verify_receipt(receipt, changed, current_input_sha256=old_digest)
    assert not verify_receipt(receipt, card, input_sha256=old_digest, current_input_sha256="0" * 64)
    assert not verify_receipt(receipt, card, target="seed-1", target_id="other")


def test_cli_accepts_explicit_json_without_writing(tmp_path: Path) -> None:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--json", json.dumps(_card())],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert json.loads(proc.stdout)["status"] == "MAPPED"
    assert sorted(tmp_path.iterdir()) == []
