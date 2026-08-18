#!/usr/bin/env python3
"""Strict, deterministic artifact/metric/impact proposal/audit leaf."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from typing import Any


SCHEMA = "constraintbox.impact-vs-output.v1"
OPERATION = "cb-impact-vs-output-auditor.v1"
CLAIM_CEILING = "artifact/metric/external classification only; no causal impact claim"
CLAIMS = ("artifact", "metric", "external_condition")
EVIDENCE = frozenset(CLAIMS)
MAX_INPUT_BYTES = 64 * 1024
MAX_DEPTH = 8
MAX_NODES = 512
MAX_STRING_BYTES = 8 * 1024
_FORBIDDEN_KEYS = frozenset(
    {
        "promotion_allowed",
        "activated",
        "model_free",
        "audit_only",
        "proposal_only",
        "writes_performed",
        "provider_call_receipt",
        "claim_ceiling",
        "authority",
        "activate",
        "promote",
        "approved",
        "admit",
        "decision",
        "verdict",
        "disposition",
    }
)
_REQUEST_KEYS = frozenset({"schema", "operation", "target", "target_id", "cancelled", "receipt", "claim", "evidence", *_FORBIDDEN_KEYS})
_RECEIPT_KEYS = frozenset(
    {
        "schema",
        "operation",
        "target",
        "status",
        "reason",
        "claim_ceiling",
        "promotion_allowed",
        "activated",
        "model_free",
        "provider_call_receipt",
        "audit_only",
        "proposal_only",
        "writes_performed",
        "cancellation_state",
        "input_sha256",
        "output_kind",
        "claim",
        "evidence",
        "class",
        "receipt_sha256",
        "receipt_self_sha256",
    }
)


def _account_text(value: str, state: list[int]) -> bool:
    try:
        size = len(value.encode("utf-8"))
    except UnicodeError:
        return False
    if size > MAX_STRING_BYTES:
        return False
    state[1] += size
    return state[1] <= MAX_INPUT_BYTES


def _bounded(value: Any, *, depth: int = 0, state: list[int] | None = None) -> bool:
    state = state if state is not None else [0, 0]
    if len(state) < 2:
        state.append(0)
    state[0] += 1
    if state[0] > MAX_NODES or depth > MAX_DEPTH:
        return False
    if value is None or isinstance(value, bool):
        return True
    if isinstance(value, str):
        return _account_text(value, state)
    if isinstance(value, int):
        return abs(value) <= 10**18
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, list):
        return len(value) <= 128 and all(_bounded(item, depth=depth + 1, state=state) for item in value)
    if isinstance(value, dict):
        return len(value) <= 128 and all(
            isinstance(key, str)
            and _account_text(key, state)
            and _bounded(item, depth=depth + 1, state=state)
            for key, item in value.items()
        )
    return False


def _canonical(value: Any) -> str | None:
    if not _bounded(value):
        return None
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    except (TypeError, ValueError, RecursionError):
        return None


def _digest(value: Any) -> str | None:
    raw = _canonical(value)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest() if raw is not None else None


def _input_view(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if key != "receipt"}


def _input_digest(payload: dict[str, Any]) -> str | None:
    return _digest(_input_view(payload))


def _base_output(payload: Any) -> dict[str, Any]:
    source = payload if isinstance(payload, dict) else {}
    target = source.get("target") if isinstance(source.get("target"), str) else None
    return {
        "schema": SCHEMA,
        "operation": OPERATION,
        "target": target,
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": False,
        "activated": False,
        "model_free": True,
        "provider_call_receipt": None,
        "audit_only": True,
        "proposal_only": True,
        "writes_performed": False,
        "input_sha256": _input_digest(source) if isinstance(source, dict) else None,
    }


def _finish(payload: Any, *, status: str, reason: str | None = None, **fields: Any) -> dict[str, Any]:
    result = _base_output(payload)
    result.update({"status": status, "reason": reason})
    result.update(fields)
    result.setdefault("cancellation_state", "CANCELLED" if status == "CANCELLED_NO_AUTHORITY" else "NOT_REQUESTED")
    unsigned = dict(result)
    receipt_sha = _digest(unsigned)
    result["receipt_sha256"] = receipt_sha
    result["receipt_self_sha256"] = receipt_sha
    return result


def _receipt_shape(receipt: Any) -> bool:
    if not isinstance(receipt, dict) or not _bounded(receipt) or set(receipt) - _RECEIPT_KEYS:
        return False
    if receipt.get("schema") != SCHEMA or receipt.get("operation") != OPERATION:
        return False
    if receipt.get("claim_ceiling") != CLAIM_CEILING:
        return False
    if receipt.get("promotion_allowed") is not False or receipt.get("activated") is not False:
        return False
    if receipt.get("model_free") is not True or receipt.get("audit_only") is not True or receipt.get("proposal_only") is not True:
        return False
    if receipt.get("writes_performed") is not False or receipt.get("provider_call_receipt") is not None:
        return False
    if not isinstance(receipt.get("target"), str) or not receipt["target"].strip():
        return False
    if not isinstance(receipt.get("status"), str) or receipt["status"] not in {"CLASSIFIED", "REFUSE", "CANCELLED_NO_AUTHORITY"}:
        return False
    if receipt.get("reason") is not None and not isinstance(receipt.get("reason"), str):
        return False
    if not isinstance(receipt.get("input_sha256"), str) or len(receipt["input_sha256"]) != 64 or any(char not in "0123456789abcdef" for char in receipt["input_sha256"].lower()):
        return False
    if receipt.get("cancellation_state") not in {"CANCELLED", "NOT_REQUESTED"}:
        return False
    if receipt["cancellation_state"] != ("CANCELLED" if receipt["status"] == "CANCELLED_NO_AUTHORITY" else "NOT_REQUESTED"):
        return False
    if "output_kind" in receipt and not isinstance(receipt["output_kind"], str):
        return False
    if "claim" in receipt and receipt["claim"] not in CLAIMS:
        return False
    if "evidence" in receipt:
        evidence = receipt["evidence"]
        if not isinstance(evidence, list) or not evidence or any(not isinstance(item, str) or item not in EVIDENCE for item in evidence) or len(set(evidence)) != len(evidence):
            return False
    if "class" in receipt and receipt["class"] not in {"artifact_only", "metric_only", "external_condition", "artifact_or_metric_only"}:
        return False
    if receipt.get("status") == "CLASSIFIED" and not {"claim", "evidence", "class", "output_kind"} <= set(receipt):
        return False
    if receipt.get("status") == "CLASSIFIED":
        expected_class = {"artifact": "artifact_only", "metric": "metric_only", "external_condition": "external_condition"}.get(receipt.get("claim"))
        if expected_class is None or receipt.get("class") != expected_class or set(receipt["evidence"]) != {receipt["claim"]}:
            return False
    expected = receipt.get("receipt_sha256")
    if not isinstance(expected, str) or expected != receipt.get("receipt_self_sha256"):
        return False
    unsigned = dict(receipt)
    unsigned.pop("receipt_sha256", None)
    unsigned.pop("receipt_self_sha256", None)
    return _digest(unsigned) == expected


def verify_receipt(receipt: dict[str, Any], candidate: dict[str, Any] | None = None) -> bool:
    if candidate is not None:
        return verify_payload_receipt(candidate, receipt)
    return _receipt_shape(receipt)


def verify_payload_receipt(payload: dict[str, Any], receipt: dict[str, Any]) -> bool:
    if not isinstance(payload, dict) or not _request_valid(payload) or not _receipt_shape(receipt):
        return False
    if not (
        receipt["target"] == payload["target"]
        and receipt["operation"] == payload["operation"]
        and receipt["input_sha256"] == _input_digest(payload)
    ):
        return False
    return receipt == classify(_input_view(payload))


def _request_valid(payload: Any) -> bool:
    if not isinstance(payload, dict) or not _bounded(payload) or set(payload) - _REQUEST_KEYS:
        return False
    if payload.get("schema") != SCHEMA or payload.get("operation") != OPERATION:
        return False
    if not isinstance(payload.get("target"), str) or not payload["target"].strip() or "target_id" in payload:
        return False
    if any(key in payload for key in _FORBIDDEN_KEYS):
        return False
    if "cancelled" in payload and not isinstance(payload["cancelled"], bool):
        return False
    if "receipt" in payload and not isinstance(payload["receipt"], dict):
        return False
    return True


def _request_reason(payload: Any) -> tuple[str, list[str] | None]:
    if not isinstance(payload, dict):
        return "REFUSE_MALFORMED_INPUT", None
    if not _bounded(payload):
        return "REFUSE_INPUT_BOUNDS", None
    unknown = set(payload) - _REQUEST_KEYS
    if unknown:
        return "REFUSE_UNKNOWN_KEY", sorted(str(key) for key in unknown)
    if payload.get("schema") != SCHEMA:
        return "REFUSE_SCHEMA_MISMATCH", None
    if payload.get("operation") != OPERATION:
        return "REFUSE_OPERATION_MISMATCH", None
    if "target_id" in payload:
        return "REFUSE_TARGET_CONFLICT", None
    if not isinstance(payload.get("target"), str) or not payload["target"].strip():
        return "REFUSE_TARGET_REQUIRED", None
    if "cancelled" in payload and not isinstance(payload["cancelled"], bool):
        return "REFUSE_CANCEL_TYPE", None
    if any(key in payload for key in _FORBIDDEN_KEYS):
        return "REFUSE_AUTHORITY_SHAPED", None
    if "receipt" in payload and not isinstance(payload["receipt"], dict):
        return "REFUSE_RECEIPT_SHAPE", None
    claim = payload.get("claim")
    if not isinstance(claim, str) or claim not in CLAIMS:
        return "REFUSE_CLAIM_ENUM", None
    evidence = payload.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        return "REFUSE_EVIDENCE_EMPTY", None
    if any(not isinstance(item, str) or item not in EVIDENCE for item in evidence):
        return "REFUSE_EVIDENCE_ENUM", None
    if len(set(evidence)) != len(evidence):
        return "REFUSE_EVIDENCE_ENUM", None
    if claim == "external_condition" and "external_condition" not in evidence:
        return "REFUSE_OUTPUT_AS_IMPACT", None
    if set(evidence) != {claim}:
        return "REFUSE_EVIDENCE_CLASS_MISMATCH", None
    return "", None


def _guard(payload: Any) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    if isinstance(payload, dict) and "receipt" in payload and _request_valid(payload):
        if not verify_payload_receipt(payload, payload["receipt"]):
            return None, _finish(payload, status="REFUSE", reason="REFUSE_RECEIPT_TAMPER")
    reason, details = _request_reason(payload)
    if reason:
        fields = {"missing": details} if reason == "REFUSE_CHANGE_FLAGS" else {}
        return None, _finish(payload, status="REFUSE", reason=reason, **fields)
    assert isinstance(payload, dict)
    if payload.get("cancelled", False):
        return None, _finish(payload, status="CANCELLED_NO_AUTHORITY", reason="CANCELLED_NO_AUTHORITY")
    return payload, None


def classify(payload: Any) -> dict[str, Any]:
    payload, refusal = _guard(payload)
    if refusal is not None:
        return refusal
    assert payload is not None
    claim = payload["claim"]
    class_name = {"artifact": "artifact_only", "metric": "metric_only", "external_condition": "external_condition"}[claim]
    return _finish(
        payload,
        status="CLASSIFIED",
        reason=None,
        output_kind="AUDIT",
        claim=claim,
        evidence=list(payload["evidence"]),
        **{"class": class_name},
    )


def _load_payload(raw: str) -> Any:
    try:
        oversized = len(raw.encode("utf-8")) > MAX_INPUT_BYTES
    except UnicodeError:
        return None
    if oversized:
        return None
    try:
        def no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
            result: dict[str, Any] = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError("duplicate JSON key")
                result[key] = value
            return result

        return json.loads(raw, object_pairs_hook=no_duplicates, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
    except (TypeError, ValueError, json.JSONDecodeError, RecursionError):
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", "--input", "--payload", dest="raw", required=True)
    args = parser.parse_args()
    payload = _load_payload(args.raw)
    receipt = classify(payload) if payload is not None else _finish({}, status="REFUSE", reason="REFUSE_MALFORMED_JSON")
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    return 0 if receipt["status"] == "CLASSIFIED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
