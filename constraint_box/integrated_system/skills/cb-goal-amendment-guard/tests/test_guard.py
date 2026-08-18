from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.guard import CHANGED_FIELDS, MAX_STRING_BYTES, OPERATION, OWNER_OPERATION, OWNER_SCHEMA, SCHEMA, guard, verify_payload_receipt, verify_receipt


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "guard.py"


def _payload() -> dict[str, object]:
    return {
        "schema": SCHEMA,
        "operation": OPERATION,
        "target": "goal-1",
        "object_changed": False,
        "success_condition_changed": False,
        "hard_constraints_changed": False,
    }


def _owner_receipt(payload: dict[str, object], changed: list[str], *, signature: bool = False) -> dict[str, object]:
    receipt: dict[str, object] = {
        "schema": OWNER_SCHEMA,
        "receipt_id": "amend-1",
        "owner": "owner-1",
        "source": "owner-ledger://amend-1",
        "target": payload["target"],
        "operation": OWNER_OPERATION,
        "changed": changed,
        "statement": "Owner explicitly changes the named fields.",
    }
    if signature:
        receipt["signature"] = "external-signature-1"
    else:
        body = json.dumps(receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
        receipt["digest"] = hashlib.sha256(body.encode("utf-8")).hexdigest()
    return receipt


def _owner_sha(receipt: dict[str, object]) -> str:
    body = json.dumps(receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def test_unchanged_is_strict_audit_only() -> None:
    receipt = guard(_payload())
    assert receipt["status"] == "UNCHANGED"
    assert receipt["changed"] == []
    assert receipt["owner_amendment_bound"] is False
    assert receipt["promotion_allowed"] is False
    assert receipt["audit_only"] is True
    assert receipt["proposal_only"] is True
    assert receipt["writes_performed"] is False
    assert receipt["provider_call_receipt"] is None
    assert verify_receipt(receipt)
    assert verify_payload_receipt(_payload(), receipt)


def test_missing_flags_and_unlicensed_changes_fail_closed() -> None:
    missing = _payload()
    del missing["hard_constraints_changed"]
    receipt = guard(missing)
    assert receipt["reason"] == "REFUSE_CHANGE_FLAGS"
    changed = _payload()
    changed["object_changed"] = True
    assert guard(changed)["reason"] == "REFUSE_UNLICENSED_AMENDMENT"
    discovered = _payload()
    discovered["discovered_better_objective"] = "raise the score"
    assert guard(discovered)["status"] == "PROPOSED"
    assert guard(discovered)["reason"] == "HOLD_OWNER_AMENDMENT"


def test_external_owner_receipt_requires_exact_binding_and_digest_or_signature() -> None:
    payload = _payload()
    payload["object_changed"] = True
    payload["owner_amendment_receipt"] = _owner_receipt(payload, ["object"])
    receipt = guard(
        payload,
        trusted_owner_receipt_sha256=_owner_sha(payload["owner_amendment_receipt"]),
        trusted_owner="owner-1",
        trusted_source="owner-ledger://amend-1",
    )
    assert receipt["status"] == "UNCHANGED"
    assert receipt["owner_amendment_bound"] is True
    assert receipt["owner_amendment_binding_sha256"]
    signature_payload = _payload()
    signature_payload["object_changed"] = True
    signature_payload["owner_amendment_receipt"] = _owner_receipt(signature_payload, ["object"], signature=True)
    assert guard(
        signature_payload,
        trusted_owner_receipt_sha256=_owner_sha(signature_payload["owner_amendment_receipt"]),
    )["status"] == "UNCHANGED"
    wrong_digest = copy.deepcopy(payload)
    wrong_digest["owner_amendment_receipt"]["digest"] = "0" * 64
    assert guard(wrong_digest)["reason"] == "REFUSE_OWNER_RECEIPT_DIGEST"
    wrong_target = copy.deepcopy(payload)
    wrong_target["owner_amendment_receipt"]["target"] = "goal-2"
    assert guard(wrong_target)["reason"] == "REFUSE_OWNER_RECEIPT_BINDING"


def test_self_declared_owner_or_authorized_is_not_proof() -> None:
    payload = _payload()
    payload["object_changed"] = True
    owner = _owner_receipt(payload, ["object"])
    owner["authorized"] = True
    payload["owner_amendment_receipt"] = owner
    assert guard(payload)["reason"] == "REFUSE_OWNER_AUTHORITY_UNPROVEN"
    self_source = _payload()
    self_source["object_changed"] = True
    owner = _owner_receipt(self_source, ["object"], signature=True)
    owner["source"] = "self"
    self_source["owner_amendment_receipt"] = owner
    assert guard(self_source)["reason"] == "REFUSE_OWNER_AUTHORITY_UNPROVEN"
    malformed = _payload()
    malformed["object_changed"] = True
    bad_owner = _owner_receipt(malformed, ["object"])
    bad_owner["changed"] = "object"
    malformed["owner_amendment_receipt"] = bad_owner
    assert guard(malformed)["reason"] == "REFUSE_OWNER_RECEIPT_SHAPE"


def test_fake_signature_without_out_of_band_trust_refuses() -> None:
    payload = _payload()
    payload["object_changed"] = True
    payload["owner_amendment_receipt"] = _owner_receipt(payload, ["object"], signature=True)
    assert guard(payload)["reason"] == "REFUSE_OWNER_AUTHORITY_UNPROVEN"


def test_trusted_receipt_sha_owner_source_and_replay_are_exact() -> None:
    payload = _payload()
    payload["object_changed"] = True
    owner = _owner_receipt(payload, ["object"], signature=True)
    payload["owner_amendment_receipt"] = owner
    expected = _owner_sha(owner)
    trusted_receipt = guard(payload, trusted_owner_receipt_sha256=expected)
    assert trusted_receipt["status"] == "UNCHANGED"
    assert verify_receipt(trusted_receipt, payload, trusted_owner_receipt_sha256=expected)
    embedded = copy.deepcopy(payload)
    embedded["receipt"] = trusted_receipt
    assert guard(embedded, trusted_owner_receipt_sha256=expected) == trusted_receipt
    assert guard(payload, trusted_owner_receipt_sha256="0" * 64)["reason"] == "REFUSE_OWNER_RECEIPT_DIGEST"
    assert guard(payload, trusted_owner_receipt_sha256=expected, trusted_owner="other")["reason"] == "REFUSE_OWNER_RECEIPT_BINDING"
    replay = copy.deepcopy(payload)
    replay["operation"] = "other-operation.v1"
    assert guard(replay, trusted_owner_receipt_sha256=expected)["reason"] == "REFUSE_OPERATION_MISMATCH"


def test_unchanged_request_never_authenticates_embedded_owner() -> None:
    payload = _payload()
    payload["owner_amendment_receipt"] = _owner_receipt(payload, [], signature=True)
    receipt = guard(payload)
    assert receipt["status"] == "UNCHANGED"
    assert receipt["owner_amendment_bound"] is False
    assert receipt["owner_amendment_binding_sha256"] is None


def test_exact_identity_unknown_keys_and_strict_cancellation() -> None:
    assert guard([])["reason"] == "REFUSE_MALFORMED_INPUT"
    bad_schema = _payload()
    bad_schema["schema"] = "other.v1"
    assert guard(bad_schema)["reason"] == "REFUSE_SCHEMA_MISMATCH"
    bad_operation = _payload()
    bad_operation["operation"] = "refuse_unlicensed_object_change"
    assert guard(bad_operation)["reason"] == "REFUSE_OPERATION_MISMATCH"
    alias = _payload()
    alias["operation_id"] = "alias"
    assert guard(alias)["reason"] == "REFUSE_UNKNOWN_KEY"
    provider = _payload()
    provider["provider"] = "model"
    assert guard(provider)["reason"] == "REFUSE_UNKNOWN_KEY"
    conflict = _payload()
    conflict["target_id"] = "goal-1"
    assert guard(conflict)["reason"] == "REFUSE_TARGET_CONFLICT"
    bad_cancel = _payload()
    bad_cancel["cancelled"] = "true"
    assert guard(bad_cancel)["reason"] == "REFUSE_CANCEL_TYPE"
    promoted = _payload()
    promoted["promotion_allowed"] = True
    assert guard(promoted)["reason"] == "REFUSE_AUTHORITY_SHAPED"


def test_operation_replay_receipt_binding_and_tamper_fail() -> None:
    payload = _payload()
    first = guard(payload)
    assert first == guard(copy.deepcopy(payload))
    embedded = copy.deepcopy(payload)
    embedded["receipt"] = first
    assert guard(embedded) == first
    changed_target = copy.deepcopy(embedded)
    changed_target["target"] = "goal-2"
    assert guard(changed_target)["reason"] == "REFUSE_RECEIPT_TAMPER"
    changed_operation = copy.deepcopy(embedded)
    changed_operation["operation"] = "other.v1"
    assert guard(changed_operation)["reason"] == "REFUSE_OPERATION_MISMATCH"
    tampered = copy.deepcopy(first)
    tampered["proposal_only"] = False
    assert not verify_receipt(tampered)
    forged = copy.deepcopy(payload)
    forged["receipt"] = tampered
    assert guard(forged)["reason"] == "REFUSE_RECEIPT_TAMPER"


def test_bounds_and_cancellation_no_write() -> None:
    oversized = _payload()
    oversized["discovered_better_objective"] = "x" * (MAX_STRING_BYTES + 1)
    assert guard(oversized)["reason"] == "REFUSE_INPUT_BOUNDS"
    cancelled = _payload()
    cancelled["cancelled"] = True
    receipt = guard(cancelled)
    assert receipt["status"] == "CANCELLED_NO_AUTHORITY"
    assert receipt["cancellation_state"] == "CANCELLED"
    assert receipt["writes_performed"] is False


def test_cli_accepts_explicit_json_without_writing(tmp_path: Path) -> None:
    before = sorted(tmp_path.iterdir())
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--payload", json.dumps(_payload())],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert json.loads(proc.stdout)["status"] == "UNCHANGED"
    assert sorted(tmp_path.iterdir()) == before


def test_cli_rejects_12k_depth_without_traceback() -> None:
    raw = "[" * 12000 + "0" + "]" * 12000
    proc = subprocess.run([sys.executable, str(SCRIPT), "--json", raw], check=False, capture_output=True, text=True)
    assert proc.returncode == 2
    assert "Traceback" not in proc.stderr
    assert json.loads(proc.stdout)["reason"] == "REFUSE_MALFORMED_JSON"


def test_cli_requires_and_accepts_out_of_band_owner_receipt_sha(tmp_path: Path) -> None:
    payload = _payload()
    payload["object_changed"] = True
    payload["owner_amendment_receipt"] = _owner_receipt(payload, ["object"], signature=True)
    raw = json.dumps(payload, separators=(",", ":"))
    expected = _owner_sha(payload["owner_amendment_receipt"])
    denied = subprocess.run([sys.executable, str(SCRIPT), "--json", raw], cwd=tmp_path, check=False, capture_output=True, text=True)
    assert denied.returncode == 2
    assert json.loads(denied.stdout)["reason"] == "REFUSE_OWNER_AUTHORITY_UNPROVEN"
    allowed = subprocess.run(
        [sys.executable, str(SCRIPT), "--json", raw, "--owner-receipt-sha256", expected, "--owner-receipt-owner", "owner-1", "--owner-receipt-source", "owner-ledger://amend-1"],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )
    assert allowed.returncode == 0
    assert json.loads(allowed.stdout)["status"] == "UNCHANGED"
