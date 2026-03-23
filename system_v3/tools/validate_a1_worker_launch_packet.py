#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SCHEMA = "A1_WORKER_LAUNCH_PACKET_v1"
THREAD_CLASS = "A1_WORKER"
MODE = "PROPOSAL_ONLY"
ALLOWED_QUEUE_STATUSES = {
    "READY_FROM_NEW_A2_HANDOFF",
    "READY_FROM_EXISTING_FUEL",
    "READY_FROM_A2_PREBUILT_BATCH",
}
ALLOWED_ROLES = {"A1_ROSETTA", "A1_PROPOSAL", "A1_PACKAGING"}
ALLOWED_VALIDATION_REQUESTED_MODES = {"jsonschema", "local_pydantic", "auto"}
ALLOWED_VALIDATION_RESOLVED_MODES = {"jsonschema", "local_pydantic"}
ALLOWED_VALIDATION_SOURCES = {"jsonschema_plus_runtime_semantics", "local_pydantic_audit"}


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"missing_input:{path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid_json:{path}:{exc.lineno}:{exc.colno}") from exc


def _is_nonempty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _normalize_text(value: str) -> str:
    return " ".join(value.replace("`", " ").split())


def _require_abs_existing(value: object, key: str, errors: list[str]) -> None:
    if not _is_nonempty_text(value):
        errors.append(f"missing_{key}")
        return
    path = Path(str(value).strip())
    if not path.is_absolute():
        errors.append(f"non_absolute_{key}")
        return
    if not path.exists():
        errors.append(f"missing_path_{key}:{path}")


def _validate_requested_validation_provenance(
    value: object,
    *,
    requested_mode: str,
    errors: list[str],
) -> None:
    if value in (None, {}):
        return
    if not isinstance(value, dict):
        errors.append("invalid_family_slice_validation_requested_provenance")
        return
    mode = str(value.get("mode", "")).strip()
    if mode not in ALLOWED_VALIDATION_REQUESTED_MODES:
        errors.append("invalid_family_slice_validation_requested_provenance_mode")
    if requested_mode and mode and mode != requested_mode:
        errors.append("family_slice_validation_requested_provenance_mode_mismatch")


def _validate_resolved_validation_provenance(
    value: object,
    *,
    resolved_mode: str,
    validation_source: str,
    errors: list[str],
) -> None:
    if value in (None, {}):
        return
    if not isinstance(value, dict):
        errors.append("invalid_family_slice_validation_resolved_provenance")
        return
    mode = str(value.get("mode", "")).strip()
    source = str(value.get("source", "")).strip()
    if mode not in ALLOWED_VALIDATION_RESOLVED_MODES:
        errors.append("invalid_family_slice_validation_resolved_provenance_mode")
    if source not in ALLOWED_VALIDATION_SOURCES:
        errors.append("invalid_family_slice_validation_resolved_provenance_source")
    if resolved_mode and mode and mode != resolved_mode:
        errors.append("family_slice_validation_resolved_provenance_mode_mismatch")
    if validation_source and source and source != validation_source:
        errors.append("family_slice_validation_resolved_provenance_source_mismatch")


def validate(packet: dict) -> dict:
    errors: list[str] = []

    if packet.get("schema") != SCHEMA:
        errors.append("invalid_schema")
    if packet.get("thread_class") != THREAD_CLASS:
        errors.append("invalid_thread_class")
    if packet.get("mode") != MODE:
        errors.append("invalid_mode")

    for key in ("model", "dispatch_id", "bounded_scope", "prompt_to_send", "stop_rule"):
        if not _is_nonempty_text(packet.get(key)):
            errors.append(f"missing_{key}")

    queue_status = packet.get("queue_status")
    if queue_status not in ALLOWED_QUEUE_STATUSES:
        errors.append("invalid_queue_status")

    target_role = packet.get("target_a1_role")
    if target_role not in ALLOWED_ROLES:
        errors.append("invalid_target_a1_role")

    _require_abs_existing(packet.get("required_a1_boot"), "required_a1_boot", errors)

    source_artifacts = packet.get("source_a2_artifacts")
    if not isinstance(source_artifacts, list) or not source_artifacts:
        errors.append("invalid_source_a2_artifacts")
    else:
        for index, value in enumerate(source_artifacts, start=1):
            _require_abs_existing(value, f"source_a2_artifacts[{index}]", errors)

    reload_artifacts = packet.get("a1_reload_artifacts", [])
    if reload_artifacts is None:
        reload_artifacts = []
    if not isinstance(reload_artifacts, list):
        errors.append("invalid_a1_reload_artifacts")
    else:
        for index, value in enumerate(reload_artifacts, start=1):
            _require_abs_existing(value, f"a1_reload_artifacts[{index}]", errors)

    for key in ("go_on_count", "go_on_budget"):
        value = packet.get(key)
        if not isinstance(value, int):
            errors.append(f"invalid_{key}")
            continue
        if value < 0:
            errors.append(f"negative_{key}")

    if isinstance(packet.get("go_on_count"), int) and isinstance(packet.get("go_on_budget"), int):
        if packet["go_on_count"] > packet["go_on_budget"]:
            errors.append("go_on_count_exceeds_budget")

    requested_mode = str(packet.get("family_slice_validation_requested_mode", "")).strip()
    resolved_mode = str(packet.get("family_slice_validation_resolved_mode", "")).strip()
    validation_source = str(packet.get("family_slice_validation_source", "")).strip()
    requested_provenance = packet.get("family_slice_validation_requested_provenance")
    resolved_provenance = packet.get("family_slice_validation_resolved_provenance")
    if requested_mode or resolved_mode or validation_source:
        if requested_mode not in ALLOWED_VALIDATION_REQUESTED_MODES:
            errors.append("invalid_family_slice_validation_requested_mode")
        if resolved_mode not in ALLOWED_VALIDATION_RESOLVED_MODES:
            errors.append("invalid_family_slice_validation_resolved_mode")
        if validation_source not in ALLOWED_VALIDATION_SOURCES:
            errors.append("invalid_family_slice_validation_source")
        if not requested_mode:
            errors.append("missing_family_slice_validation_requested_mode")
        if not resolved_mode:
            errors.append("missing_family_slice_validation_resolved_mode")
        if not validation_source:
            errors.append("missing_family_slice_validation_source")
        if requested_mode != "auto" and requested_mode and resolved_mode and requested_mode != resolved_mode:
            errors.append("family_slice_validation_mode_mismatch")
    if requested_mode or requested_provenance:
        if not requested_provenance:
            errors.append("missing_family_slice_validation_requested_provenance")
        _validate_requested_validation_provenance(
            requested_provenance,
            requested_mode=requested_mode,
            errors=errors,
        )
    if resolved_mode or validation_source or resolved_provenance:
        if not resolved_provenance:
            errors.append("missing_family_slice_validation_resolved_provenance")
        _validate_resolved_validation_provenance(
            resolved_provenance,
            resolved_mode=resolved_mode,
            validation_source=validation_source,
            errors=errors,
        )

    prompt_to_send = packet.get("prompt_to_send")
    if _is_nonempty_text(prompt_to_send):
        normalized_prompt = _normalize_text(str(prompt_to_send))
        for key in ("target_a1_role", "required_a1_boot", "stop_rule"):
            value = packet.get(key)
            if _is_nonempty_text(value) and _normalize_text(str(value)) not in normalized_prompt:
                errors.append(f"prompt_to_send_missing:{key}")
        if isinstance(source_artifacts, list):
            for index, value in enumerate(source_artifacts, start=1):
                if _is_nonempty_text(value) and _normalize_text(str(value)) not in normalized_prompt:
                    errors.append(f"prompt_to_send_missing:source_a2_artifacts[{index}]")
        if isinstance(reload_artifacts, list):
            for index, value in enumerate(reload_artifacts, start=1):
                if _is_nonempty_text(value) and _normalize_text(str(value)) not in normalized_prompt:
                    errors.append(f"prompt_to_send_missing:a1_reload_artifacts[{index}]")

    return {
        "schema": "A1_WORKER_LAUNCH_PACKET_VALIDATION_RESULT_v1",
        "valid": not errors,
        "errors": errors,
        "thread_class": packet.get("thread_class", ""),
        "mode": packet.get("mode", ""),
        "packet_schema": packet.get("schema", ""),
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Validate one machine-readable A1_WORKER_LAUNCH_PACKET_v1."
    )
    parser.add_argument("--packet-json", required=True)
    args = parser.parse_args(argv)

    result = validate(_load_json(Path(args.packet_json)))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
