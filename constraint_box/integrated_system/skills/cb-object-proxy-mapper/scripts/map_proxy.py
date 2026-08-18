#!/usr/bin/env python3
"""Deterministically map an object/proxy chain without granting authority."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from typing import Any


SCHEMA = "constraintbox.object-proxy-map.v1"
OPERATION = "cb-object-proxy-mapper.v1"
CLAIM_CEILING = (
    "bounded object-to-proxy mapping proposal only; preserves/losses are "
    "reported, not semantic truth or promotion"
)
REQUIRED = ("object", "proxy", "measurement", "consumer", "allowed_inference")
ALLOWED = {"operation_id", "target", "target_id", *REQUIRED, "preserves", "loses", "cancel_requested"}
AUTHORITY_KEYS = {
    "authority", "promotion_allowed", "activate", "activation", "activated", "activation_allowed",
    "approve", "approved", "admit", "commit", "commit_allowed", "execute", "executed",
    "execute_allowed", "promote", "write", "writes", "write_allowed", "provider", "provider_call",
    "model", "models",
}
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


def _canonical(value: Any) -> str | None:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    except (TypeError, ValueError, RecursionError):
        return None


def _digest(value: Any) -> str | None:
    raw = _canonical(value)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest() if raw is not None else None


def _is_digest(value: Any) -> bool:
    return isinstance(value, str) and bool(_HEX64.fullmatch(value))


def _authority_reason(value: Any) -> str | None:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).strip().lower() in AUTHORITY_KEYS:
                return "REFUSE_AUTHORITY_SHAPED"
            nested = _authority_reason(item)
            if nested:
                return nested
    elif isinstance(value, list):
        for item in value:
            nested = _authority_reason(item)
            if nested:
                return nested
    return None


def _identity(card: dict[str, Any]) -> dict[str, Any]:
    if card.get("operation_id") != OPERATION:
        raise ValueError("REFUSE_OPERATION_MISMATCH")
    target = card.get("target")
    target_id = card.get("target_id")
    if target is not None and (not isinstance(target, str) or not target.strip()):
        raise ValueError("REFUSE_MALFORMED_INPUT")
    if target_id is not None and (not isinstance(target_id, str) or not target_id.strip()):
        raise ValueError("REFUSE_MALFORMED_INPUT")
    if target is None and target_id is None:
        raise ValueError("REFUSE_TARGET_REQUIRED")
    target_value = target.strip() if isinstance(target, str) else target_id.strip()
    target_id_value = target_id.strip() if isinstance(target_id, str) else None
    if target_id_value is not None and target_id_value != target_value:
        raise ValueError("REFUSE_TARGET_MISMATCH")
    binding = {"target": target_value}
    if target_id_value is not None:
        binding["target_id"] = target_id_value
    return {"operation_id": OPERATION, "target": target_value, "target_binding": binding}


def _finish(card: Any, *, status: str, reason: str | None = None, seal: bool = True, **fields: Any) -> dict[str, Any]:
    payload = card if isinstance(card, dict) else {}
    try:
        identity = _identity(payload)
    except ValueError:
        identity = {"operation_id": OPERATION, "target": None, "target_binding": {}}
    result: dict[str, Any] = {
        "schema": SCHEMA,
        "operation": OPERATION,
        "operation_id": identity["operation_id"],
        "target": identity["target"],
        "target_binding": identity["target_binding"],
        "status": status,
        "reason": reason,
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": False,
        "activated": False,
        "model_free": True,
        "provider_call_receipt": None,
        "writes_performed": False,
        "receipt_written": False if not seal else True,
        "cancellation_state": "CANCELLED" if status == "CANCELLED" else "NOT_REQUESTED",
        "input_sha256": _digest(payload),
    }
    result.update(identity["target_binding"])
    result.update(fields)
    if not seal:
        return result
    unsigned = dict(result)
    unsigned.pop("receipt_sha256", None)
    unsigned.pop("receipt_self_sha256", None)
    receipt_sha = _digest(unsigned)
    result["receipt_sha256"] = receipt_sha
    result["receipt_self_sha256"] = receipt_sha
    return result


def verify_receipt(
    receipt: dict[str, Any],
    current_input: Any | None = None,
    *,
    input_sha256: str | None = None,
    current_input_sha256: str | None = None,
    target: str | None = None,
    target_id: str | None = None,
    operation: str | None = None,
) -> bool:
    """Verify self-digest plus current input, identity, and immutable bounds."""

    if not isinstance(receipt, dict) or receipt.get("schema") != SCHEMA:
        return False
    if receipt.get("status") == "CANCELLED":
        return False
    if receipt.get("operation") != OPERATION or receipt.get("operation_id") != OPERATION:
        return False
    if not isinstance(receipt.get("target"), str) or not receipt["target"].strip():
        return False
    if receipt.get("target_id") is not None and receipt.get("target_id") != receipt.get("target"):
        return False
    expected_binding = {"target": receipt["target"]}
    if receipt.get("target_id") is not None:
        expected_binding["target_id"] = receipt["target_id"]
    if receipt.get("target_binding") != expected_binding:
        return False
    if receipt.get("promotion_allowed") is not False or receipt.get("activated") is not False:
        return False
    if receipt.get("model_free") is not True or receipt.get("cancellation_state") != "NOT_REQUESTED":
        return False
    if receipt.get("writes_performed") is not False or receipt.get("receipt_written") is not True:
        return False
    if "provider_call_receipt" not in receipt or receipt.get("provider_call_receipt") is not None or receipt.get("claim_ceiling") != CLAIM_CEILING:
        return False
    if not _is_digest(receipt.get("input_sha256")):
        return False
    expected = receipt.get("receipt_sha256")
    if not isinstance(expected, str) or expected != receipt.get("receipt_self_sha256"):
        return False
    unsigned = dict(receipt)
    unsigned.pop("receipt_sha256", None)
    unsigned.pop("receipt_self_sha256", None)
    if _digest(unsigned) != expected:
        return False
    if current_input is not None:
        computed_input_sha256 = _digest(current_input)
        if computed_input_sha256 is None:
            return False
        if input_sha256 is not None and input_sha256 != computed_input_sha256:
            return False
        if current_input_sha256 is not None and current_input_sha256 != computed_input_sha256:
            return False
        if input_sha256 is not None and current_input_sha256 is not None and input_sha256 != current_input_sha256:
            return False
        if computed_input_sha256 != receipt.get("input_sha256"):
            return False
        if isinstance(current_input, dict):
            try:
                current_identity = _identity(current_input)
            except ValueError:
                return False
            if current_identity["target"] != receipt.get("target"):
                return False
            if current_identity["operation_id"] != receipt.get("operation_id"):
                return False
    if current_input is None and input_sha256 is not None and input_sha256 != receipt.get("input_sha256"):
        return False
    if current_input is None and current_input_sha256 is not None and current_input_sha256 != receipt.get("input_sha256"):
        return False
    if target is not None and target_id is not None and target != target_id:
        return False
    verifier_target = target if target is not None else target_id
    if verifier_target is not None and verifier_target != receipt.get("target"):
        return False
    if operation is not None and operation != receipt.get("operation"):
        return False
    return True


def _guard(card: Any) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    if not isinstance(card, dict):
        return None, _finish({}, status="REFUSE", reason="REFUSE_MALFORMED_INPUT")
    if _digest(card) is None:
        return None, _finish(card, status="REFUSE", reason="REFUSE_MALFORMED_INPUT")
    authority = _authority_reason(card)
    if authority:
        return None, _finish(card, status="REFUSE", reason=authority)
    if "operation" in card:
        return None, _finish(card, status="REFUSE", reason="REFUSE_OPERATION_MISMATCH")
    unknown = sorted(set(card) - ALLOWED)
    if unknown:
        return None, _finish(card, status="REFUSE", reason="REFUSE_UNKNOWN_INPUT", unknown=unknown)
    try:
        identity = _identity(card)
    except ValueError as exc:
        return None, _finish(card, status="REFUSE", reason=str(exc))
    if "cancel_requested" in card and not isinstance(card["cancel_requested"], bool):
        return None, _finish(card, status="REFUSE", reason="REFUSE_MALFORMED_INPUT", field="cancel_requested", target=identity["target"])
    if card.get("cancel_requested") is True:
        return None, _finish(card, status="CANCELLED", reason="CANCELLED_NO_AUTHORITY", seal=False)
    for key in REQUIRED:
        value = card.get(key)
        if value and not isinstance(value, str):
            return None, _finish(card, status="REFUSE", reason="REFUSE_MALFORMED_INPUT", field=key, target=identity["target"])
    for key in ("preserves", "loses"):
        if key in card and (not isinstance(card[key], list) or any(not isinstance(item, str) for item in card[key])):
            return None, _finish(card, status="REFUSE", reason="REFUSE_MALFORMED_INPUT", field=key, target=identity["target"])
    return card, None


def map_proxy(card: Any) -> dict[str, Any]:
    card, refusal = _guard(card)
    if refusal is not None:
        return refusal
    assert card is not None
    missing = [key for key in REQUIRED if not card.get(key)]
    if missing:
        return _finish(card, status="HOLD", reason="HOLD_CHAIN_INCOMPLETE", missing=missing)
    return _finish(
        card,
        status="MAPPED",
        reason=None,
        output_kind="PROPOSAL",
        chain={key: card[key] for key in REQUIRED},
        preserves=card.get("preserves") or [],
        loses=card.get("loses") or [],
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", "--input", "--card", dest="raw", required=True)
    args = parser.parse_args()
    try:
        card = json.loads(args.raw)
    except json.JSONDecodeError:
        receipt = _finish({}, status="REFUSE", reason="REFUSE_MALFORMED_JSON")
    else:
        receipt = map_proxy(card)
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    return 0 if receipt["status"] == "MAPPED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
