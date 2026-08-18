#!/usr/bin/env python3
"""Strict deterministic prerequisite/information-value sequencing cell."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from typing import Any


SCHEMA = "constraintbox.dependency-sequence.v1"
OPERATION = "cb-dependency-sequence-cell.v1"
EXPECTED_OPERATION = OPERATION
CLAIM_CEILING = "prerequisite-respecting order proposal only; no ranking, winner, authority, activation, or promotion claim"
MAX_INPUT_BYTES = 64 * 1024
MAX_DEPTH = 8
MAX_NODES = 512
MAX_STRING_BYTES = 8 * 1024
MAX_STEPS = 128
_STEP_KEYS = frozenset({"id", "prerequisites", "information_value"})
_FORBIDDEN_KEYS = frozenset({
    "promotion_allowed", "activated", "model_free", "audit_only", "proposal_only", "writes_performed",
    "write_performed", "provider_call_receipt", "claim_ceiling", "authority", "activate", "activation",
    "activation_allowed", "promote", "approved", "admit", "decision", "verdict", "disposition",
    "winner", "selected", "selected_strategy", "vote", "gate", "gate_activated", "truth_disposition",
    "apply", "commit", "execute", "write",
})
_REQUEST_KEYS = frozenset({"schema", "operation", "operation_id", "target", "target_id", "cancelled", "receipt", "ordered_by", "steps", *_FORBIDDEN_KEYS})
_RECEIPT_KEYS = frozenset({
    "schema", "operation", "operation_id", "target", "target_id", "target_binding", "status", "reason",
    "claim_ceiling", "promotion_allowed", "activated", "model_free", "provider_call_receipt", "audit_only",
    "proposal_only", "writes_performed", "receipt_written", "cancellation_state", "input_sha256", "output_kind",
    "missing", "malformed", "order", "ordering_basis", "receipt_sha256", "receipt_self_sha256",
})


def _bounded(value: Any, *, depth: int = 0, state: list[int] | None = None) -> bool:
    state = state or [0]
    state[0] += 1
    if state[0] > MAX_NODES or depth > MAX_DEPTH:
        return False
    if value is None or isinstance(value, bool):
        return True
    if isinstance(value, str):
        return len(value.encode("utf-8")) <= MAX_STRING_BYTES
    if isinstance(value, int):
        return abs(value) <= 10**18
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, list):
        return len(value) <= MAX_STEPS and all(_bounded(item, depth=depth + 1, state=state) for item in value)
    if isinstance(value, dict):
        return len(value) <= 128 and all(
            isinstance(key, str) and len(key.encode("utf-8")) <= MAX_STRING_BYTES
            and _bounded(item, depth=depth + 1, state=state)
            for key, item in value.items()
        )
    return False


def _canonical(value: Any) -> str | None:
    if not _bounded(value):
        return None
    try:
        raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    except (TypeError, ValueError, RecursionError):
        return None
    return raw if len(raw.encode("utf-8")) <= MAX_INPUT_BYTES else None


def _digest(value: Any) -> str | None:
    raw = _canonical(value)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest() if raw is not None else None


def _is_digest(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def _input_digest(payload: dict[str, Any]) -> str | None:
    return _digest({key: value for key, value in payload.items() if key != "receipt"})


def _nonblank(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _base_output(payload: Any) -> dict[str, Any]:
    source = payload if isinstance(payload, dict) else {}
    raw_target = source.get("target") if _nonblank(source.get("target")) else source.get("target_id")
    target = raw_target.strip() if _nonblank(raw_target) else None
    result: dict[str, Any] = {
        "schema": SCHEMA, "operation": OPERATION, "operation_id": OPERATION, "target": target,
        "target_binding": {"target": target} if target is not None else {},
        "claim_ceiling": CLAIM_CEILING, "promotion_allowed": False, "activated": False, "model_free": True,
        "provider_call_receipt": None, "audit_only": True, "proposal_only": True, "writes_performed": False,
        "receipt_written": False, "input_sha256": _input_digest(source) if isinstance(source, dict) else None,
    }
    if isinstance(source.get("target_id"), str):
        result["target_id"] = source["target_id"].strip()
        if target is not None:
            result["target_binding"]["target_id"] = result["target_id"]
    return result


def _finish(payload: Any, *, status: str, reason: str | None = None, **fields: Any) -> dict[str, Any]:
    result = _base_output(payload)
    result.update({"status": status, "reason": reason})
    result.update({key: value for key, value in fields.items() if value is not None})
    cancelled = status == "CANCELLED_NO_AUTHORITY"
    result["cancellation_state"] = "CANCELLED" if cancelled else "NOT_REQUESTED"
    result["receipt_written"] = not cancelled
    unsigned = dict(result)
    value = _digest(unsigned)
    result["receipt_sha256"] = value
    result["receipt_self_sha256"] = value
    return result


def _receipt_shape(receipt: Any) -> bool:
    if not isinstance(receipt, dict) or not _bounded(receipt) or set(receipt) - _RECEIPT_KEYS:
        return False
    immutable = {
        "schema": SCHEMA, "operation": OPERATION, "operation_id": OPERATION, "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": False, "activated": False, "model_free": True, "provider_call_receipt": None,
        "audit_only": True, "proposal_only": True, "writes_performed": False,
    }
    if any(receipt.get(key) != value for key, value in immutable.items()):
        return False
    if not _nonblank(receipt.get("target")):
        return False
    if "target_id" in receipt and (not _nonblank(receipt["target_id"]) or receipt["target_id"] != receipt["target"]):
        return False
    binding = {"target": receipt["target"]}
    if "target_id" in receipt:
        binding["target_id"] = receipt["target_id"]
    if receipt.get("target_binding") != binding:
        return False
    if receipt.get("status") not in {"SEQUENCED", "HOLD", "REFUSE", "CANCELLED_NO_AUTHORITY"}:
        return False
    if not isinstance(receipt.get("reason"), (str, type(None))):
        return False
    if "missing" in receipt and (not isinstance(receipt["missing"], list) or any(not _nonblank(item) for item in receipt["missing"])):
        return False
    if "output_kind" in receipt and receipt["output_kind"] not in {"PROPOSAL", "AUDIT"}:
        return False
    if receipt.get("cancellation_state") not in {"CANCELLED", "NOT_REQUESTED"}:
        return False
    if receipt.get("receipt_written") is not (receipt.get("status") != "CANCELLED_NO_AUTHORITY"):
        return False
    if not _is_digest(receipt.get("input_sha256")):
        return False
    if not isinstance(receipt.get("receipt_written"), bool):
        return False
    if receipt.get("status") == "SEQUENCED":
        order = receipt.get("order")
        if not isinstance(order, list) or not order or any(not _nonblank(item) for item in order) or len(set(order)) != len(order):
            return False
    expected = receipt.get("receipt_sha256")
    if not _nonblank(expected) or expected != receipt.get("receipt_self_sha256"):
        return False
    unsigned = {key: value for key, value in receipt.items() if key not in {"receipt_sha256", "receipt_self_sha256"}}
    return _digest(unsigned) == expected


def verify_receipt(receipt: Any, candidate: dict[str, Any] | None = None) -> bool:
    if candidate is not None:
        if isinstance(receipt, dict) and "receipt_sha256" in receipt and isinstance(candidate, dict) and "receipt_sha256" not in candidate:
            return verify_payload_receipt(candidate, receipt)
        return verify_payload_receipt(receipt, candidate)
    return _receipt_shape(receipt)


def verify_payload_receipt(payload: dict[str, Any], receipt: dict[str, Any]) -> bool:
    if not isinstance(payload, dict) or not _request_valid(payload) or not _receipt_shape(receipt):
        return False
    expected_target = payload.get("target", payload.get("target_id"))
    target_id = payload.get("target_id")
    return (
        receipt["target"] == expected_target.strip()
        and (receipt.get("target_id") == target_id if target_id is not None else "target_id" not in receipt)
        and receipt["operation"] == payload["operation"] == OPERATION
        and receipt["operation_id"] == payload["operation_id"] == OPERATION
        and receipt["input_sha256"] == _input_digest(payload)
    )


def _request_valid(payload: Any) -> bool:
    if not isinstance(payload, dict) or not _bounded(payload) or _canonical(payload) is None or set(payload) - _REQUEST_KEYS:
        return False
    if payload.get("schema") != SCHEMA or payload.get("operation") != OPERATION or payload.get("operation_id") != OPERATION:
        return False
    if ("target" in payload and not _nonblank(payload.get("target"))) or ("target" not in payload and not _nonblank(payload.get("target_id"))):
        return False
    if "target_id" in payload and "target" in payload:
        return False
    if "target_id" in payload and not _nonblank(payload["target_id"]):
        return False
    if "cancelled" in payload and not isinstance(payload["cancelled"], bool):
        return False
    if "receipt" in payload and not isinstance(payload["receipt"], dict):
        return False
    return not any(key in payload for key in _FORBIDDEN_KEYS)


def _step_data(steps: Any) -> tuple[str | None, list[str] | None, dict[str, dict[str, Any]] | None]:
    if not isinstance(steps, list):
        return "REFUSE_STEP_TYPE", None, None
    if not steps:
        return "HOLD_NO_STEPS", None, None
    if len(steps) > MAX_STEPS:
        return "REFUSE_INPUT_BOUNDS", None, None
    by_id: dict[str, dict[str, Any]] = {}
    for step in steps:
        if not isinstance(step, dict) or set(step) != _STEP_KEYS:
            return "REFUSE_STEP_TYPE", None, None
        ident = step["id"]
        prereqs = step["prerequisites"]
        value = step["information_value"]
        if not _nonblank(ident) or not isinstance(prereqs, list) or len(prereqs) > MAX_STEPS or any(not _nonblank(item) for item in prereqs):
            return "REFUSE_STEP_TYPE", None, None
        if type(value) not in {int, float} or isinstance(value, bool) or not math.isfinite(float(value)):
            return "REFUSE_STEP_TYPE", None, None
        ident = ident.strip()
        prereqs = [item.strip() for item in prereqs]
        if ident in by_id:
            return "REFUSE_DUPLICATE_STEP", None, None
        if len(set(prereqs)) != len(prereqs):
            return "REFUSE_DUPLICATE_PREREQUISITE", None, None
        by_id[ident] = {"id": ident, "prerequisites": prereqs, "information_value": value}
    unknown = sorted({dep for step in by_id.values() for dep in step["prerequisites"] if dep not in by_id})
    if unknown:
        return "REFUSE_UNKNOWN_PREREQUISITE", unknown, None
    return None, None, by_id


def _request_reason(payload: Any) -> tuple[str | None, list[str] | None]:
    if not isinstance(payload, dict):
        return "REFUSE_MALFORMED_INPUT", None
    if not _bounded(payload):
        return "REFUSE_INPUT_BOUNDS", None
    if _canonical(payload) is None:
        return "REFUSE_INPUT_BOUNDS", None
    unknown = sorted(set(payload) - _REQUEST_KEYS)
    if unknown:
        return "REFUSE_UNKNOWN_KEY", unknown
    if payload.get("schema") != SCHEMA:
        return "REFUSE_SCHEMA_MISMATCH", None
    if payload.get("operation") != OPERATION:
        return "REFUSE_OPERATION_MISMATCH", None
    if "operation_id" not in payload:
        return "REFUSE_OPERATION_ID_REQUIRED", None
    if payload["operation_id"] != OPERATION:
        return "REFUSE_OPERATION_MISMATCH", None
    if ("target" in payload and not _nonblank(payload.get("target"))) or ("target" not in payload and not _nonblank(payload.get("target_id"))):
        return "REFUSE_TARGET_REQUIRED", None
    if "target_id" in payload and "target" in payload:
        return "REFUSE_TARGET_CONFLICT", None
    if "target_id" in payload and not _nonblank(payload["target_id"]):
        return "REFUSE_TARGET_REQUIRED", None
    if "cancelled" in payload and not isinstance(payload["cancelled"], bool):
        return "REFUSE_CANCEL_TYPE", None
    if any(key in payload for key in _FORBIDDEN_KEYS):
        return "REFUSE_AUTHORITY_SHAPED", None
    if "receipt" in payload and not isinstance(payload["receipt"], dict):
        return "REFUSE_RECEIPT_SHAPE", None
    if payload.get("cancelled", False):
        return None, None
    if "ordered_by" in payload:
        if not isinstance(payload["ordered_by"], str):
            return "REFUSE_ORDERING_TYPE", None
        basis = payload["ordered_by"].strip()
        if basis.casefold() == "attractiveness":
            return "REFUSE_ATTRACTIVENESS_ORDER", None
        if basis.casefold() not in {"information_value", "prerequisites_then_information_value"}:
            return "REFUSE_ORDERING_BASIS", None
    if "steps" not in payload:
        return "HOLD_NO_STEPS", None
    reason, details, _ = _step_data(payload["steps"])
    return reason, details


def _guard(payload: Any) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    reason, details = _request_reason(payload)
    if reason:
        return None, _finish(payload, status="HOLD" if reason == "HOLD_NO_STEPS" else "REFUSE", reason=reason, missing=details if reason == "HOLD_PREREQ" else None)
    assert isinstance(payload, dict)
    embedded = payload.get("receipt")
    if embedded is not None and not verify_payload_receipt(payload, embedded):
        return None, _finish(payload, status="REFUSE", reason="REFUSE_RECEIPT_TAMPER")
    if payload.get("cancelled", False):
        return None, _finish(payload, status="CANCELLED_NO_AUTHORITY", reason="CANCELLED_NO_AUTHORITY")
    return payload, None


def _order(steps: list[dict[str, Any]]) -> tuple[list[str] | None, str | None]:
    by_id = {step["id"]: step for step in steps}
    remaining = set(by_id)
    done: list[str] = []
    while remaining:
        ready = [ident for ident in remaining if all(dep in done for dep in by_id[ident]["prerequisites"])]
        if not ready:
            return None, "REFUSE_DEPENDENCY_CYCLE"
        ready.sort(key=lambda ident: (-float(by_id[ident]["information_value"]), len(by_id[ident]["prerequisites"]), ident))
        chosen = ready[0]
        done.append(chosen)
        remaining.remove(chosen)
    return done, None


def sequence(payload: Any) -> dict[str, Any]:
    payload, refusal = _guard(payload)
    if refusal is not None:
        return refusal
    assert payload is not None
    steps = [{"id": step["id"].strip(), "prerequisites": [dep.strip() for dep in step["prerequisites"]], "information_value": step["information_value"]} for step in payload["steps"]]
    order, error = _order(steps)
    if error:
        return _finish(payload, status="REFUSE", reason=error)
    assert order is not None
    return _finish(payload, status="SEQUENCED", reason=None, output_kind="PROPOSAL", order=order, ordering_basis="prerequisites_then_information_value")


def replay(payload: dict[str, Any], prior: dict[str, Any] | None = None) -> dict[str, Any]:
    current = sequence(payload)
    if prior is None:
        return {"schema": SCHEMA, "status": "REPLAYED", "digest_match": True, "receipt_sha256": current.get("receipt_sha256"), "promotion_allowed": False, "writes_performed": False}
    if not verify_payload_receipt(payload, prior):
        return _finish(payload, status="REFUSE", reason="REFUSE_RECEIPT_TAMPER")
    match = current.get("receipt_sha256") == prior.get("receipt_sha256")
    return {"schema": SCHEMA, "status": "REPLAY_MATCH" if match else "REPLAY_MISMATCH", "digest_match": match, "receipt_sha256": current.get("receipt_sha256"), "promotion_allowed": False, "writes_performed": False}


def _load_payload(raw: str) -> Any:
    if len(raw.encode("utf-8")) > MAX_INPUT_BYTES:
        return None
    def no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate key")
            result[key] = value
        return result
    try:
        return json.loads(raw, object_pairs_hook=no_duplicates, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
    except (TypeError, ValueError, json.JSONDecodeError, RecursionError, UnicodeError):
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", "--input", "--payload", dest="raw", required=True)
    args = parser.parse_args()
    payload = _load_payload(args.raw)
    if payload is None:
        receipt = _finish({}, status="REFUSE", reason="REFUSE_MALFORMED_JSON")
    else:
        receipt = sequence(payload)
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    return 0 if receipt["status"] in {"SEQUENCED", "CANCELLED_NO_AUTHORITY"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
