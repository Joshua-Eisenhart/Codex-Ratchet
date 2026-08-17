"""Immutable host-event capture and result-integrity contract.

This module records transport facts.  It does not select an operation or grant
authority.  The v1 result schema can only relay, withhold, or cancel an event
as non-authoritative plumbing.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CAPTURE_ROOT = ROOT / "receipts" / "hook_adapter" / "captures"
CAPTURE_SCHEMA = "constraintbox.hook_capture.v1"
RESULT_SCHEMA = "constraintbox.hook_controller_result.v1"
CLAIM_CEILING = "immutable host-event capture and non-authoritative relay only"


class CaptureError(RuntimeError):
    def __init__(self, reason_code: str, detail: str) -> None:
        super().__init__(detail)
        self.reason_code = reason_code
        self.detail = detail


def canonical_json(value: Any) -> bytes:
    """CB JSON v1 identity rule; changing it requires a new schema."""
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise CaptureError("REFUSE_CAPTURE_REQUEST_NOT_CANONICAL_JSON", str(exc)) from exc


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _event_name(payload: dict[str, Any]) -> str:
    return str(
        payload.get("hook_event_name")
        or payload.get("hookEventName")
        or payload.get("event")
        or payload.get("type")
        or "unknown"
    )


def _stable_capture_material(
    payload: dict[str, Any], *, host: str, command: str
) -> tuple[dict[str, Any], bytes]:
    request_bytes = canonical_json(payload)
    command_bytes = command.encode("utf-8")
    material = {
        "schema": CAPTURE_SCHEMA,
        "host": str(host),
        "event": _event_name(payload),
        "request_sha256": _sha256_bytes(request_bytes),
        "request_size": len(request_bytes),
        "command_sha256": _sha256_bytes(command_bytes),
        "command_size": len(command_bytes),
    }
    return material, request_bytes


def _capture_id(material: dict[str, Any]) -> str:
    return _sha256_bytes(canonical_json(material))


def _read_canonical_capture(path: Path) -> tuple[dict[str, Any], bytes]:
    if path.is_symlink():
        raise CaptureError("REFUSE_CAPTURE_RECEIPT_SYMLINK", str(path))
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise CaptureError("REFUSE_CAPTURE_RECEIPT_UNREADABLE", str(exc)) from exc
    if not isinstance(value, dict):
        raise CaptureError("REFUSE_CAPTURE_RECEIPT_NOT_OBJECT", str(path))
    expected = canonical_json(value) + b"\n"
    if raw != expected:
        raise CaptureError("REFUSE_CAPTURE_RECEIPT_NOT_CANONICAL", str(path))
    return value, raw


def _write_once(path: Path, raw: bytes) -> bool:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags, 0o600)
    except FileExistsError:
        return False
    try:
        view = memoryview(raw)
        written = 0
        while written < len(view):
            amount = os.write(descriptor, view[written:])
            if amount <= 0:
                raise OSError("short capture write")
            written += amount
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return True


def capture_event(
    payload: dict[str, Any],
    *,
    host: str,
    command: str,
    capture_root: Path | None = None,
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise CaptureError("REFUSE_CAPTURE_PAYLOAD_NOT_OBJECT", type(payload).__name__)
    material, _request_bytes = _stable_capture_material(payload, host=host, command=command)
    capture_id = _capture_id(material)
    body = {
        **material,
        "capture_id": capture_id,
        "captured_at_unix": time.time(),
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": False,
    }
    root = capture_root or DEFAULT_CAPTURE_ROOT
    try:
        root.mkdir(parents=True, exist_ok=True, mode=0o700)
        path = root / f"{capture_id}.json"
        raw = canonical_json(body) + b"\n"
        created = _write_once(path, raw)
    except OSError as exc:
        raise CaptureError("REFUSE_CAPTURE_RECEIPT_WRITE_FAILED", str(exc)) from exc

    if not created:
        existing, raw = _read_canonical_capture(path)
        for key, value in {**material, "capture_id": capture_id}.items():
            if existing.get(key) != value:
                raise CaptureError("REFUSE_CAPTURE_IDENTITY_COLLISION", key)
        body = existing

    return {
        **body,
        "capture_receipt_path": str(path),
        "capture_receipt_sha256": _sha256_bytes(raw),
    }


def verify_capture(
    capture: dict[str, Any],
    *,
    payload: dict[str, Any],
    host: str,
    command: str,
) -> dict[str, Any]:
    material, _request_bytes = _stable_capture_material(payload, host=host, command=command)
    expected_id = _capture_id(material)
    if capture.get("capture_id") != expected_id:
        raise CaptureError("REFUSE_CAPTURE_ID_MISMATCH", expected_id)
    try:
        path = Path(str(capture["capture_receipt_path"]))
    except KeyError as exc:
        raise CaptureError("REFUSE_CAPTURE_RECEIPT_MISSING", "path") from exc
    body, raw = _read_canonical_capture(path)
    for key, value in {**material, "capture_id": expected_id}.items():
        if body.get(key) != value:
            raise CaptureError("REFUSE_CAPTURE_RECEIPT_MISMATCH", key)
    if capture.get("capture_receipt_sha256") != _sha256_bytes(raw):
        raise CaptureError("REFUSE_CAPTURE_RECEIPT_DIGEST_MISMATCH", str(path))
    return capture


def make_transport_result(
    capture: dict[str, Any], *, action: str = "relay"
) -> dict[str, Any]:
    mapping = {
        "relay": (True, "RELAY_UNAUTHORITY"),
        "withhold": (False, "WITHHOLD_UNAUTHORITY"),
        "cancelled": (False, "CANCELLED"),
    }
    if action not in mapping:
        raise CaptureError("REFUSE_CONTROLLER_ACTION_UNKNOWN", action)
    allow, disposition = mapping[action]
    body = {
        "schema": RESULT_SCHEMA,
        "capture_id": capture["capture_id"],
        "request_sha256": capture["request_sha256"],
        "command_sha256": capture["command_sha256"],
        "capture_receipt_sha256": capture["capture_receipt_sha256"],
        "action": action,
        "allow": allow,
        "authoritative": False,
        "disposition": disposition,
        "reason_code": disposition,
        "promotion_allowed": False,
    }
    body["controller_result_sha256"] = _sha256_bytes(canonical_json(body))
    return body


def validate_controller_result(
    capture: dict[str, Any], result: dict[str, Any]
) -> dict[str, Any]:
    required = {
        "schema",
        "capture_id",
        "request_sha256",
        "command_sha256",
        "capture_receipt_sha256",
        "action",
        "allow",
        "authoritative",
        "disposition",
        "reason_code",
        "promotion_allowed",
        "controller_result_sha256",
    }
    if not isinstance(result, dict) or set(result) != required:
        raise CaptureError("REFUSE_CONTROLLER_RESULT_SHAPE", "exact fields required")
    if result["schema"] != RESULT_SCHEMA:
        raise CaptureError("REFUSE_CONTROLLER_RESULT_SCHEMA", str(result["schema"]))
    for key in (
        "capture_id",
        "request_sha256",
        "command_sha256",
        "capture_receipt_sha256",
    ):
        if result[key] != capture[key]:
            raise CaptureError("REFUSE_CONTROLLER_RESULT_BINDING_MISMATCH", key)
    expected = make_transport_result(capture, action=str(result["action"]))
    if result != expected:
        raise CaptureError("REFUSE_CONTROLLER_RESULT_MISMATCH", "result")
    return dict(result)


def capture_and_validate(
    payload: dict[str, Any],
    *,
    host: str,
    command: str,
    capture_root: Path | None = None,
    controller: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    capture = capture_event(
        payload,
        host=host,
        command=command,
        capture_root=capture_root,
    )
    verify_capture(capture, payload=payload, host=host, command=command)
    if controller is None:
        raise CaptureError("REFUSE_CONTROLLER_MISSING", "no controller result consumer")
    try:
        result = controller(capture)
    except CaptureError:
        raise
    except Exception as exc:
        raise CaptureError("REFUSE_CONTROLLER_FAILURE", type(exc).__name__) from exc
    verify_capture(capture, payload=payload, host=host, command=command)
    return capture, validate_controller_result(capture, result)
