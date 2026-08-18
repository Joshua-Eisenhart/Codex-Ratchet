#!/usr/bin/env python3
"""Strict, deterministic termination-budget proposal/audit leaf."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from typing import Any


SCHEMA = "constraintbox.termination-budget.v1"
OPERATION = "cb-termination-budget-cell.v1"
CLAIM_CEILING = "termination budget audit only; no execution or cancellation authority"
REQUIRED = (
    "satisfice",
    "diminishing_return",
    "stop",
    "cancellation_obeys",
    "time_budget",
    "compute_budget",
    "resource_budget",
    "retry_budget",
)
MAX_BUDGET = 1_000_000
MAX_INPUT_BYTES = 64 * 1024
MAX_DEPTH = 8
MAX_NODES = 512
MAX_STRING_BYTES = 8 * 1024
_BUDGETS = ("time_budget", "compute_budget", "resource_budget", "retry_budget")
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
_REQUEST_KEYS = frozenset(
    {
        "schema",
        "operation",
        "target",
        "target_id",
        "cancelled",
        "receipt",
        "resist_one_more_round",
        *REQUIRED,
        *_FORBIDDEN_KEYS,
    }
)
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
        "missing",
        "malformed",
        "retry_budget",
        "time_budget",
        "compute_budget",
        "resource_budget",
        "budgets",
        "budget_binding_sha256",
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
    if not isinstance(receipt.get("status"), str) or receipt["status"] not in {"BOUNDED", "HOLD", "REFUSE", "CANCELLED_NO_AUTHORITY"}:
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
    for key in _BUDGETS:
        if key in receipt and (not isinstance(receipt[key], int) or isinstance(receipt[key], bool) or receipt[key] < 0 or receipt[key] > MAX_BUDGET):
            return False
    for key in ("missing", "malformed"):
        if key in receipt and (not isinstance(receipt[key], list) or any(not isinstance(item, str) for item in receipt[key])):
            return False
    if "budgets" in receipt:
        if not isinstance(receipt["budgets"], dict) or set(receipt["budgets"]) != set(_BUDGETS):
            return False
        if any(not isinstance(receipt["budgets"][key], int) or isinstance(receipt["budgets"][key], bool) or receipt["budgets"][key] < 0 or receipt["budgets"][key] > MAX_BUDGET for key in _BUDGETS):
            return False
        if receipt.get("budget_binding_sha256") != _digest(receipt["budgets"]):
            return False
        if any(receipt.get(key) != receipt["budgets"].get(key) for key in _BUDGETS):
            return False
    if "budget_binding_sha256" in receipt and (not isinstance(receipt["budget_binding_sha256"], str) or len(receipt["budget_binding_sha256"]) != 64):
        return False
    if receipt.get("status") == "BOUNDED" and not {"budgets", "budget_binding_sha256", *_BUDGETS} <= set(receipt):
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
    budgets = {key: payload[key] for key in _BUDGETS}
    if not (
        receipt["target"] == payload["target"]
        and receipt["operation"] == payload["operation"]
        and receipt["input_sha256"] == _input_digest(payload)
        and receipt.get("budgets") == budgets
        and receipt.get("budget_binding_sha256") == _digest(budgets)
    ):
        return False
    return receipt == check_budget(_input_view(payload))


def _request_valid(payload: Any) -> bool:
    if not isinstance(payload, dict) or not _bounded(payload) or set(payload) - _REQUEST_KEYS:
        return False
    if payload.get("schema") != SCHEMA or payload.get("operation") != OPERATION:
        return False
    if not isinstance(payload.get("target"), str) or not payload["target"].strip() or "target_id" in payload:
        return False
    if "cancelled" in payload and not isinstance(payload["cancelled"], bool):
        return False
    if any(key in payload for key in _FORBIDDEN_KEYS):
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
    missing = [key for key in REQUIRED if key not in payload]
    if missing:
        return "HOLD_BUDGET_INCOMPLETE", missing
    for key in ("satisfice", "diminishing_return", "stop"):
        if not isinstance(payload[key], str) or not payload[key].strip():
            return "REFUSE_BUDGET_TYPE", [key]
    if not isinstance(payload["cancellation_obeys"], bool):
        return "REFUSE_BUDGET_TYPE", ["cancellation_obeys"]
    for key in _BUDGETS:
        value = payload[key]
        if not isinstance(value, int) or isinstance(value, bool) or value < 0 or value > MAX_BUDGET:
            return "REFUSE_BUDGET_BOUND", [key]
    if "resist_one_more_round" in payload and not isinstance(payload["resist_one_more_round"], bool):
        return "REFUSE_RESIST_TYPE", ["resist_one_more_round"]
    return "", None


def _guard(payload: Any) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    if isinstance(payload, dict) and "receipt" in payload and _request_valid(payload):
        if not verify_payload_receipt(payload, payload["receipt"]):
            return None, _finish(payload, status="REFUSE", reason="REFUSE_RECEIPT_TAMPER")
    reason, details = _request_reason(payload)
    if reason:
        fields = {"missing": details} if reason == "HOLD_BUDGET_INCOMPLETE" else {}
        return None, _finish(payload, status="HOLD" if reason == "HOLD_BUDGET_INCOMPLETE" else "REFUSE", reason=reason, **fields)
    assert isinstance(payload, dict)
    if payload.get("cancellation_obeys") is False:
        return None, _finish(payload, status="REFUSE", reason="REFUSE_CANCEL_RESIST", output_kind="AUDIT")
    if payload.get("cancelled", False):
        return None, _finish(payload, status="CANCELLED_NO_AUTHORITY", reason="CANCELLED_NO_AUTHORITY")
    return payload, None


def check_budget(payload: Any) -> dict[str, Any]:
    payload, refusal = _guard(payload)
    if refusal is not None:
        return refusal
    assert payload is not None
    if payload.get("resist_one_more_round", False):
        return _finish(payload, status="REFUSE", reason="REFUSE_INFINITE_OPTIMIZATION", output_kind="AUDIT")
    budgets = {key: payload[key] for key in _BUDGETS}
    return _finish(
        payload,
        status="BOUNDED",
        reason=None,
        output_kind="PROPOSAL",
        **budgets,
        budgets=budgets,
        budget_binding_sha256=_digest(budgets),
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
    receipt = check_budget(payload) if payload is not None else _finish({}, status="REFUSE", reason="REFUSE_MALFORMED_JSON")
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    return 0 if receipt["status"] == "BOUNDED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
