#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


SCHEMA = "A2_CONTROLLER_LAUNCH_PACKET_v1"
THREAD_CLASS = "A2_CONTROLLER"
MODE = "CONTROLLER_ONLY"


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"missing_input:{path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid_json:{path}:{exc.lineno}:{exc.colno}") from exc


def _load_text(path: Path) -> str:
    if not path.exists():
        raise SystemExit(f"missing_input:{path}")
    return path.read_text(encoding="utf-8")


def _is_nonempty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _normalize_text(value: str) -> str:
    text = value.replace("`", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


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

    for key in (
        "model",
        "current_primary_lane",
        "current_a1_queue_status",
        "stop_rule",
        "dispatch_rule",
        "initial_bounded_scope",
    ):
        if not _is_nonempty_text(packet.get(key)):
            errors.append(f"missing_{key}")

    for key in ("primary_corpus", "state_record", "boot_surface"):
        _require_abs_existing(packet.get(key), key, errors)

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

    state_record_value = packet.get("state_record")
    if _is_nonempty_text(state_record_value):
        state_record_path = Path(str(state_record_value).strip())
        if state_record_path.exists():
            state_text = _normalize_text(_load_text(state_record_path))
            for key in ("primary_corpus", "current_primary_lane", "current_a1_queue_status"):
                value = packet.get(key)
                if _is_nonempty_text(value) and _normalize_text(str(value)) not in state_text:
                    errors.append(f"state_record_mismatch:{key}")

    return {
        "schema": "A2_CONTROLLER_LAUNCH_PACKET_VALIDATION_RESULT_v1",
        "valid": not errors,
        "errors": errors,
        "thread_class": packet.get("thread_class", ""),
        "mode": packet.get("mode", ""),
        "packet_schema": packet.get("schema", ""),
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Validate one machine-readable A2_CONTROLLER_LAUNCH_PACKET_v1."
    )
    parser.add_argument("--packet-json", required=True)
    args = parser.parse_args(argv)

    result = validate(_load_json(Path(args.packet_json)))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
