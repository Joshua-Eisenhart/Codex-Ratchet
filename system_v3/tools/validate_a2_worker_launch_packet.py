#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SCHEMA = "A2_WORKER_LAUNCH_PACKET_v1"
THREAD_CLASS = "A2_WORKER"
MODE = "A2_ONLY"
ALLOWED_ROLE_TYPES = {
    "A2_BRAIN_REFRESH",
    "A2_HIGH_REFINERY_PASS",
    "A2_HIGH_FAMILY_ROUTING_PASS",
    "A2_QUEUE_INTEGRITY_AUDIT",
    "A2_RUN_FOLDER_CLEANUP_PREP",
    "A2_BOOT/PROCEDURE_BUILD",
    "A2_EXTERNAL_RETURN_AUDIT_CAPTURE",
    "A2_DELTA_CONSOLIDATION",
}


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


def validate(packet: dict) -> dict:
    errors: list[str] = []

    if packet.get("schema") != SCHEMA:
        errors.append("invalid_schema")
    if packet.get("thread_class") != THREAD_CLASS:
        errors.append("invalid_thread_class")
    if packet.get("mode") != MODE:
        errors.append("invalid_mode")

    for key in ("model", "dispatch_id", "role_label", "role_scope", "bounded_scope", "prompt_to_send", "stop_rule"):
        if not _is_nonempty_text(packet.get(key)):
            errors.append(f"missing_{key}")

    role_type = packet.get("role_type")
    if role_type not in ALLOWED_ROLE_TYPES:
        errors.append("invalid_role_type")

    _require_abs_existing(packet.get("required_a2_boot"), "required_a2_boot", errors)

    source_artifacts = packet.get("source_artifacts")
    if not isinstance(source_artifacts, list) or not source_artifacts:
        errors.append("invalid_source_artifacts")
    else:
        for index, value in enumerate(source_artifacts, start=1):
            _require_abs_existing(value, f"source_artifacts[{index}]", errors)

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

    prompt_to_send = packet.get("prompt_to_send")
    if _is_nonempty_text(prompt_to_send):
        normalized_prompt = _normalize_text(str(prompt_to_send))
        for key in ("dispatch_id", "role_label", "role_type", "role_scope", "required_a2_boot", "stop_rule"):
            value = packet.get(key)
            if _is_nonempty_text(value) and _normalize_text(str(value)) not in normalized_prompt:
                errors.append(f"prompt_to_send_missing:{key}")
        if isinstance(source_artifacts, list):
            for index, value in enumerate(source_artifacts, start=1):
                if _is_nonempty_text(value) and _normalize_text(str(value)) not in normalized_prompt:
                    errors.append(f"prompt_to_send_missing:source_artifacts[{index}]")

    return {
        "schema": "A2_WORKER_LAUNCH_PACKET_VALIDATION_RESULT_v1",
        "valid": not errors,
        "errors": errors,
        "thread_class": packet.get("thread_class", ""),
        "mode": packet.get("mode", ""),
        "packet_schema": packet.get("schema", ""),
        "role_type": packet.get("role_type", ""),
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Validate one machine-readable A2_WORKER_LAUNCH_PACKET_v1."
    )
    parser.add_argument("--packet-json", required=True)
    args = parser.parse_args(argv)

    result = validate(_load_json(Path(args.packet_json)))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
