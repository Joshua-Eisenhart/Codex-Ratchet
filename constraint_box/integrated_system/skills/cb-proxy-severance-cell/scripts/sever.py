#!/usr/bin/env python3
"""Find a proxy/object severance in one explicit numeric trial."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from typing import Any


SCHEMA = "constraintbox.proxy-severance.v1"
OPERATION = "cb-proxy-severance-cell.v1"
CLAIM_CEILING = (
    "bounded intervention observation only; a proxy/object severance is a "
    "Goodhart negative, not a semantic verdict or promotion"
)
MEASURES = ("proxy_before", "proxy_after", "object_before", "object_after")
MAX_MEASURE = 1_000_000_000_000.0
ALLOWED = {"operation_id", "target", "target_id", "intervention", *MEASURES, "cancel_requested"}
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


def _identity(trial: dict[str, Any]) -> dict[str, Any]:
    if trial.get("operation_id") != OPERATION:
        raise ValueError("REFUSE_OPERATION_MISMATCH")
    target = trial.get("target")
    target_id = trial.get("target_id")
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


def _finish(trial: Any, *, status: str, reason: str | None = None, seal: bool = True, **fields: Any) -> dict[str, Any]:
    source = trial if isinstance(trial, dict) else {}
    try:
        identity = _identity(source)
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
        "input_sha256": _digest(source),
    }
    result.update(identity["target_binding"])
    result.update(fields)
    if not seal:
        return result
    unsigned = dict(result)
    unsigned.pop("receipt_sha256", None)
    unsigned.pop("receipt_self_sha256", None)
    value = _digest(unsigned)
    result["receipt_sha256"] = value
    result["receipt_self_sha256"] = value
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
                identity = _identity(current_input)
            except ValueError:
                return False
            if identity["target"] != receipt.get("target") or identity["operation_id"] != receipt.get("operation_id"):
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


def _guard(trial: Any) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    if not isinstance(trial, dict):
        return None, _finish({}, status="REFUSE", reason="REFUSE_MALFORMED_INPUT")
    if _digest(trial) is None:
        return None, _finish(trial, status="REFUSE", reason="REFUSE_MALFORMED_INPUT")
    authority = _authority_reason(trial)
    if authority:
        return None, _finish(trial, status="REFUSE", reason=authority)
    if "operation" in trial:
        return None, _finish(trial, status="REFUSE", reason="REFUSE_OPERATION_MISMATCH")
    unknown = sorted(set(trial) - ALLOWED)
    if unknown:
        return None, _finish(trial, status="REFUSE", reason="REFUSE_UNKNOWN_INPUT", unknown=unknown)
    try:
        identity = _identity(trial)
    except ValueError as exc:
        return None, _finish(trial, status="REFUSE", reason=str(exc))
    if "cancel_requested" in trial and not isinstance(trial["cancel_requested"], bool):
        return None, _finish(trial, status="REFUSE", reason="REFUSE_MALFORMED_INPUT", field="cancel_requested", target=identity["target"])
    if trial.get("cancel_requested") is True:
        return None, _finish(trial, status="CANCELLED", reason="CANCELLED_NO_AUTHORITY", seal=False)
    intervention = trial.get("intervention")
    if not isinstance(intervention, str) or not intervention.strip():
        return None, _finish(trial, status="REFUSE", reason="REFUSE_INTERVENTION_REQUIRED", target=identity["target"])
    return trial, None


def _measure(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("REFUSE_MEASURE_TYPE")
    if isinstance(value, int) and abs(value) > MAX_MEASURE:
        raise OverflowError("REFUSE_MEASURE_OUT_OF_BOUNDS")
    try:
        numeric = float(value)
    except (OverflowError, ValueError, TypeError):
        raise OverflowError("REFUSE_MEASURE_OUT_OF_BOUNDS") from None
    if not math.isfinite(numeric) or abs(numeric) > MAX_MEASURE:
        raise OverflowError("REFUSE_MEASURE_OUT_OF_BOUNDS")
    return numeric


def sever(trial: Any) -> dict[str, Any]:
    trial, refusal = _guard(trial)
    if refusal is not None:
        return refusal
    assert trial is not None
    missing = [key for key in MEASURES if key not in trial]
    if missing:
        return _finish(trial, status="HOLD", reason="HOLD_MEASURES", missing=missing, output_kind="AUDIT")
    try:
        values = {key: _measure(trial[key]) for key in MEASURES}
    except (TypeError, OverflowError) as exc:
        return _finish(trial, status="REFUSE", reason=str(exc), output_kind="AUDIT")
    proxy_delta = values["proxy_after"] - values["proxy_before"]
    object_delta = values["object_after"] - values["object_before"]
    found = values["proxy_after"] > values["proxy_before"] and values["object_after"] <= values["object_before"]
    return _finish(
        trial,
        status="SEVERED" if found else "NOT_FOUND",
        reason=None,
        output_kind="AUDIT",
        intervention=trial["intervention"],
        proxy_delta=proxy_delta,
        object_delta=object_delta,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", "--input", "--trial", dest="raw", required=True)
    args = parser.parse_args()
    try:
        trial = json.loads(args.raw)
    except json.JSONDecodeError:
        receipt = _finish({}, status="REFUSE", reason="REFUSE_MALFORMED_JSON")
    else:
        receipt = sever(trial)
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    return 0 if receipt["status"] in {"SEVERED", "NOT_FOUND"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
