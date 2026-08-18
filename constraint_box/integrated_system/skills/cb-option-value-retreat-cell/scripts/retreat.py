#!/usr/bin/env python3
"""Strict deterministic reversible-probe and retreat-map proposal cell."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from typing import Any


SCHEMA = "constraintbox.option-retreat.v1"
OPERATION = "cb-option-value-retreat-cell.v1"
EXPECTED_OPERATION = OPERATION
CLAIM_CEILING = "option and retreat map only; no commitment, authority, activation, or promotion claim"
REQUIRED = ("reversible_probes", "irreversible_commitments", "hold_conditions", "retreat_conditions", "preserved_options")
MAX_INPUT_BYTES = 64 * 1024
MAX_DEPTH = 8
MAX_NODES = 512
MAX_STRING_BYTES = 8 * 1024
_PROBE_KEYS = frozenset({"name", "scope", "reversible", "undo_operation", "restored_state_check"})
_PROBE_SCOPES = frozenset({"read_only", "local_scratch"})
_CONDITION_KEYS = frozenset({"commitment", "condition"})
_IRREVERSIBLE_WORDS = frozenset({"ship", "rollout", "deploy", "release", "publish", "commit", "delete", "push", "remove", "overwrite", "promote", "activate", "execute"})
_FORBIDDEN_KEYS = frozenset({
    "promotion_allowed", "activated", "model_free", "audit_only", "proposal_only", "writes_performed",
    "write_performed", "provider_call_receipt", "claim_ceiling", "authority", "activate", "activation",
    "activation_allowed", "promote", "approved", "admit", "decision", "verdict", "disposition",
    "winner", "selected", "selected_strategy", "vote", "gate", "gate_activated", "truth_disposition",
    "apply", "commit", "execute", "write",
})
_REQUEST_KEYS = frozenset({"schema", "operation", "operation_id", "target", "target_id", "cancelled", "receipt", *REQUIRED, *_FORBIDDEN_KEYS})
_RECEIPT_KEYS = frozenset({
    "schema", "operation", "operation_id", "target", "target_id", "target_binding", "status", "reason",
    "claim_ceiling", "promotion_allowed", "activated", "model_free", "provider_call_receipt", "audit_only",
    "proposal_only", "writes_performed", "receipt_written", "cancellation_state", "input_sha256", "output_kind",
    "missing", "malformed", "map", "receipt_sha256", "receipt_self_sha256",
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
        return len(value) <= 128 and all(_bounded(item, depth=depth + 1, state=state) for item in value)
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


def _action_token(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    return any(token in _IRREVERSIBLE_WORDS for token in re.findall(r"[a-z0-9]+", value.casefold()))


def _names(value: Any, *, allow_empty: bool = False) -> tuple[bool, list[str]]:
    if not isinstance(value, list) or (not allow_empty and not value):
        return False, []
    if len({item.casefold() for item in value if isinstance(item, str)}) != len(value) or any(not _nonblank(item) for item in value):
        return False, []
    return True, [item.strip() for item in value]


def _probe(value: Any) -> tuple[bool, Any, str | None]:
    if _nonblank(value):
        return False, value, "REFUSE_HIDDEN_IRREVERSIBILITY" if _action_token(value) else "REFUSE_PROBE_TYPE"
    if not isinstance(value, dict) or set(value) != _PROBE_KEYS:
        return False, value, "REFUSE_PROBE_TYPE"
    if not _nonblank(value.get("name")) or type(value.get("reversible")) is not bool:
        return False, value, "REFUSE_PROBE_TYPE"
    if value.get("scope") not in _PROBE_SCOPES:
        return False, value, "REFUSE_PROBE_SCOPE"
    if value["reversible"] is not True:
        return False, value, "REFUSE_HIDDEN_IRREVERSIBILITY"
    if not _nonblank(value.get("undo_operation")) or not _nonblank(value.get("restored_state_check")):
        return False, value, "REFUSE_PROBE_TYPE"
    if any(_action_token(value[field]) for field in ("name", "undo_operation", "restored_state_check")):
        return False, value, "REFUSE_HIDDEN_IRREVERSIBILITY"
    return True, {
        "name": value["name"].strip(), "scope": value["scope"], "reversible": True,
        "undo_operation": value["undo_operation"].strip(), "restored_state_check": value["restored_state_check"].strip(),
    }, None


def _condition(value: Any) -> tuple[bool, Any]:
    if _nonblank(value):
        return True, value.strip()
    if isinstance(value, dict) and set(value) == _CONDITION_KEYS and _nonblank(value.get("commitment")) and _nonblank(value.get("condition")):
        return True, {"commitment": value["commitment"].strip(), "condition": value["condition"].strip()}
    return False, value


def _base_output(payload: Any) -> dict[str, Any]:
    source = payload if isinstance(payload, dict) else {}
    raw_target = source.get("target") if _nonblank(source.get("target")) else source.get("target_id")
    target = raw_target.strip() if _nonblank(raw_target) else None
    result: dict[str, Any] = {
        "schema": SCHEMA, "operation": OPERATION, "operation_id": OPERATION, "target": target,
        "target_binding": {"target": target} if target is not None else {}, "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": False, "activated": False, "model_free": True, "provider_call_receipt": None,
        "audit_only": True, "proposal_only": True, "writes_performed": False, "receipt_written": False,
        "input_sha256": _input_digest(source) if isinstance(source, dict) else None,
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
    if receipt.get("status") not in {"MAPPED", "HOLD", "REFUSE", "CANCELLED_NO_AUTHORITY"}:
        return False
    if not isinstance(receipt.get("reason"), (str, type(None))):
        return False
    if "missing" in receipt and (not isinstance(receipt["missing"], list) or any(not _nonblank(item) for item in receipt["missing"])):
        return False
    if "malformed" in receipt and (not isinstance(receipt["malformed"], list) or any(not _nonblank(item) for item in receipt["malformed"])):
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
    if receipt.get("status") == "MAPPED":
        mapped = receipt.get("map")
        if not isinstance(mapped, dict) or set(mapped) != set(REQUIRED):
            return False
        if not isinstance(mapped["reversible_probes"], list) or not mapped["reversible_probes"]:
            return False
        if any(not _probe(item)[0] for item in mapped["reversible_probes"]):
            return False
        if not _names(mapped["irreversible_commitments"], allow_empty=True)[0]:
            return False
        if not _names(mapped["hold_conditions"])[0] or not _names(mapped["preserved_options"])[0]:
            return False
        if not isinstance(mapped["retreat_conditions"], list) or not mapped["retreat_conditions"] or any(not _condition(item)[0] for item in mapped["retreat_conditions"]):
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


def _request_reason(payload: Any) -> tuple[str | None, list[str] | None, dict[str, Any] | None]:
    if not isinstance(payload, dict):
        return "REFUSE_MALFORMED_INPUT", None, None
    if not _bounded(payload):
        return "REFUSE_INPUT_BOUNDS", None, None
    if _canonical(payload) is None:
        return "REFUSE_INPUT_BOUNDS", None, None
    unknown = sorted(set(payload) - _REQUEST_KEYS)
    if unknown:
        return "REFUSE_UNKNOWN_KEY", unknown, None
    if payload.get("schema") != SCHEMA:
        return "REFUSE_SCHEMA_MISMATCH", None, None
    if payload.get("operation") != OPERATION:
        return "REFUSE_OPERATION_MISMATCH", None, None
    if "operation_id" not in payload:
        return "REFUSE_OPERATION_ID_REQUIRED", None, None
    if payload["operation_id"] != OPERATION:
        return "REFUSE_OPERATION_MISMATCH", None, None
    if ("target" in payload and not _nonblank(payload.get("target"))) or ("target" not in payload and not _nonblank(payload.get("target_id"))):
        return "REFUSE_TARGET_REQUIRED", None, None
    if "target_id" in payload and "target" in payload:
        return "REFUSE_TARGET_CONFLICT", None, None
    if "target_id" in payload and not _nonblank(payload["target_id"]):
        return "REFUSE_TARGET_REQUIRED", None, None
    if "cancelled" in payload and not isinstance(payload["cancelled"], bool):
        return "REFUSE_CANCEL_TYPE", None, None
    if any(key in payload for key in _FORBIDDEN_KEYS):
        return "REFUSE_AUTHORITY_SHAPED", None, None
    if "receipt" in payload and not isinstance(payload["receipt"], dict):
        return "REFUSE_RECEIPT_SHAPE", None, None
    if payload.get("cancelled", False):
        return None, None, None
    missing = [key for key in REQUIRED if key not in payload]
    if missing:
        return "HOLD_RETREAT_MAP", missing, None
    normalized: dict[str, Any] = {}
    ok, probes = (isinstance(payload["reversible_probes"], list), [])
    if ok:
        for item in payload["reversible_probes"]:
            valid, normalized_item, probe_reason = _probe(item)
            if not valid:
                return probe_reason, None, None
            probes.append(normalized_item)
        if not probes:
            return "REFUSE_PROBE_TYPE", ["reversible_probes"], None
    else:
        return "REFUSE_PROBE_TYPE", ["reversible_probes"], None
    names_ok, commitments = _names(payload["irreversible_commitments"], allow_empty=True)
    if not names_ok:
        return "REFUSE_RETREAT_TYPE", ["irreversible_commitments"], None
    for key in ("hold_conditions", "preserved_options"):
        valid, values = _names(payload[key])
        if not valid:
            return "REFUSE_RETREAT_TYPE", [key], None
        normalized[key] = values
    if not isinstance(payload["retreat_conditions"], list) or not payload["retreat_conditions"]:
        if commitments:
            return "HOLD_REVERSIBILITY", None, None
        return "REFUSE_RETREAT_TYPE", ["retreat_conditions"], None
    conditions: list[Any] = []
    for item in payload["retreat_conditions"]:
        valid, condition = _condition(item)
        if not valid:
            return "REFUSE_RETREAT_TYPE", ["retreat_conditions"], None
        conditions.append(condition)
    if commitments:
        covered: set[str] = set()
        for condition in conditions:
            if isinstance(condition, dict):
                covered.add(condition["commitment"].casefold())
            else:
                text = condition.casefold()
                covered.update(name.casefold() for name in commitments if name.casefold() in text)
        if set(name.casefold() for name in commitments) - covered:
            return "REFUSE_RETREAT_LINK", None, None
        if not normalized["preserved_options"]:
            return "REFUSE_OPTION_LINK", None, None
    normalized["reversible_probes"] = probes
    normalized["irreversible_commitments"] = commitments
    normalized["retreat_conditions"] = conditions
    return None, None, normalized


def _guard(payload: Any) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    reason, details, normalized = _request_reason(payload)
    if reason:
        return None, _finish(payload, status="HOLD" if reason in {"HOLD_RETREAT_MAP", "HOLD_REVERSIBILITY"} else "REFUSE", reason=reason, missing=details if reason == "HOLD_RETREAT_MAP" else None, malformed=details if reason.startswith("REFUSE_") else None)
    assert isinstance(payload, dict)
    embedded = payload.get("receipt")
    if embedded is not None and not verify_payload_receipt(payload, embedded):
        return None, _finish(payload, status="REFUSE", reason="REFUSE_RECEIPT_TAMPER")
    if payload.get("cancelled", False):
        return None, _finish(payload, status="CANCELLED_NO_AUTHORITY", reason="CANCELLED_NO_AUTHORITY")
    return {**payload, "_normalized": normalized}, None


def retreat(payload: Any) -> dict[str, Any]:
    payload, refusal = _guard(payload)
    if refusal is not None:
        return refusal
    assert payload is not None
    normalized = payload["_normalized"]
    source = {key: value for key, value in payload.items() if key != "_normalized"}
    return _finish(source, status="MAPPED", reason=None, output_kind="PROPOSAL", map=normalized)


def replay(payload: dict[str, Any], prior: dict[str, Any] | None = None) -> dict[str, Any]:
    current = retreat(payload)
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
        receipt = retreat(payload)
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    return 0 if receipt["status"] in {"MAPPED", "CANCELLED_NO_AUTHORITY"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
