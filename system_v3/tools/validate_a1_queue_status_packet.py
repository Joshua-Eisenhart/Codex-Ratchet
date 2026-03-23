#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from a1_queue_ready_integrity import validate_ready_queue_artifact_coherence


SCHEMA = "A1_QUEUE_STATUS_PACKET_v1"
ALLOWED_QUEUE_STATUSES = {
    "NO_WORK",
    "READY_FROM_NEW_A2_HANDOFF",
    "READY_FROM_EXISTING_FUEL",
    "READY_FROM_A2_PREBUILT_BATCH",
    "BLOCKED_MISSING_BOOT",
    "BLOCKED_MISSING_ARTIFACTS",
}
READY_QUEUE_STATUSES = {
    "READY_FROM_NEW_A2_HANDOFF",
    "READY_FROM_EXISTING_FUEL",
    "READY_FROM_A2_PREBUILT_BATCH",
}
BLOCKED_QUEUE_STATUSES = {
    "BLOCKED_MISSING_BOOT",
    "BLOCKED_MISSING_ARTIFACTS",
}
READY_SURFACE_KINDS = {
    "A1_WORKER_LAUNCH_PACKET",
    "A1_LAUNCH_BUNDLE",
}
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


def _require_existing_list(value: object, key: str, errors: list[str], *, required: bool) -> None:
    if value is None:
        value = []
    if not isinstance(value, list):
        errors.append(f"invalid_{key}")
        return
    if required and not value:
        errors.append(f"missing_{key}")
        return
    for index, item in enumerate(value, start=1):
        _require_abs_existing(item, f"{key}[{index}]", errors)


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


def _unexpected_ready_fields(packet: dict, errors: list[str]) -> None:
    ready_text_keys = (
        "dispatch_id",
        "target_a1_role",
        "required_a1_boot",
        "bounded_scope",
        "prompt_to_send",
        "stop_rule",
        "ready_surface_kind",
        "ready_packet_json",
        "ready_bundle_result_json",
        "ready_send_text_companion_json",
        "ready_launch_spine_json",
        "family_slice_json",
    )
    ready_list_keys = ("a1_reload_artifacts", "source_a2_artifacts")
    ready_int_keys = ("go_on_count", "go_on_budget")
    for key in ready_text_keys:
        if _is_nonempty_text(packet.get(key)):
            errors.append(f"unexpected_{key}_for_no_work")
    for key in ready_list_keys:
        value = packet.get(key)
        if value not in (None, []):
            errors.append(f"unexpected_{key}_for_no_work")
    for key in ready_int_keys:
        if key in packet and packet.get(key) not in (None, 0):
            errors.append(f"unexpected_{key}_for_no_work")


def validate(packet: dict) -> dict:
    errors: list[str] = []

    if packet.get("schema") != SCHEMA:
        errors.append("invalid_schema")

    queue_status = packet.get("queue_status")
    if queue_status not in ALLOWED_QUEUE_STATUSES:
        errors.append("invalid_queue_status")

    if not _is_nonempty_text(packet.get("reason")):
        errors.append("missing_reason")

    if queue_status == "NO_WORK":
        _unexpected_ready_fields(packet, errors)
        if packet.get("missing") not in (None, []):
            errors.append("unexpected_missing_for_no_work")
    elif queue_status in BLOCKED_QUEUE_STATUSES:
        missing = packet.get("missing")
        if not isinstance(missing, list) or not missing:
            errors.append("missing_missing")
        else:
            for index, item in enumerate(missing, start=1):
                if not _is_nonempty_text(item):
                    errors.append(f"invalid_missing[{index}]")
    elif queue_status in READY_QUEUE_STATUSES:
        for key in ("dispatch_id", "target_a1_role", "bounded_scope", "prompt_to_send", "stop_rule"):
            if not _is_nonempty_text(packet.get(key)):
                errors.append(f"missing_{key}")

        _require_abs_existing(packet.get("required_a1_boot"), "required_a1_boot", errors)
        _require_existing_list(packet.get("a1_reload_artifacts", []), "a1_reload_artifacts", errors, required=False)
        _require_existing_list(packet.get("source_a2_artifacts"), "source_a2_artifacts", errors, required=True)
        _require_abs_existing(packet.get("family_slice_json"), "family_slice_json", errors)
        _require_abs_existing(packet.get("ready_packet_json"), "ready_packet_json", errors)

        surface_kind = packet.get("ready_surface_kind")
        if surface_kind not in READY_SURFACE_KINDS:
            errors.append("invalid_ready_surface_kind")
        elif surface_kind == "A1_LAUNCH_BUNDLE":
            _require_abs_existing(packet.get("ready_bundle_result_json"), "ready_bundle_result_json", errors)
            _require_abs_existing(
                packet.get("ready_send_text_companion_json"),
                "ready_send_text_companion_json",
                errors,
            )
            _require_abs_existing(packet.get("ready_launch_spine_json"), "ready_launch_spine_json", errors)
        else:
            if _is_nonempty_text(packet.get("ready_bundle_result_json")):
                _require_abs_existing(packet.get("ready_bundle_result_json"), "ready_bundle_result_json", errors)
            if _is_nonempty_text(packet.get("ready_send_text_companion_json")):
                errors.append("unexpected_ready_send_text_companion_json_for_packet_mode")
            if _is_nonempty_text(packet.get("ready_launch_spine_json")):
                errors.append("unexpected_ready_launch_spine_json_for_packet_mode")

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

        errors.extend(validate_ready_queue_artifact_coherence(packet))

    return {
        "schema": "A1_QUEUE_STATUS_PACKET_VALIDATION_RESULT_v1",
        "valid": not errors,
        "errors": errors,
        "queue_status": packet.get("queue_status", ""),
        "packet_schema": packet.get("schema", ""),
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Validate one machine-readable A1_QUEUE_STATUS_PACKET_v1.")
    parser.add_argument("--packet-json", required=True)
    args = parser.parse_args(argv)

    result = validate(_load_json(Path(args.packet_json)))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
