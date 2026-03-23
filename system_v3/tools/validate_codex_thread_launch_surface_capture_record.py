#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SCHEMA = "CODEX_THREAD_LAUNCH_SURFACE_CAPTURE_RECORD_v1"
ALLOWED_THREAD_CLASSES = {"A2_CONTROLLER", "A2_WORKER", "A1_WORKER"}
ALLOWED_COMPOSER_READY = {"YES", "NO"}
ALLOWED_CAPTURE_METHODS = {"MANUAL_OPERATOR", "PLAYWRIGHT_CAPTURE"}


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"missing_input:{path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid_json:{path}:{exc.lineno}:{exc.colno}") from exc


def _is_nonempty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate(packet: dict) -> dict:
    errors: list[str] = []

    if packet.get("schema") != SCHEMA:
        errors.append("invalid_schema")
    if packet.get("thread_class") not in ALLOWED_THREAD_CLASSES:
        errors.append("invalid_thread_class")
    if packet.get("composer_ready_observed") not in ALLOWED_COMPOSER_READY:
        errors.append("invalid_composer_ready_observed")
    if packet.get("capture_method") not in ALLOWED_CAPTURE_METHODS:
        errors.append("invalid_capture_method")

    for key in (
        "launch_surface_title_observed",
        "launch_route_observed",
        "visible_verification_text_observed",
        "observed_at",
        "source_note",
    ):
        if not _is_nonempty_text(packet.get(key)):
            errors.append(f"missing_{key}")

    return {
        "schema": "CODEX_THREAD_LAUNCH_SURFACE_CAPTURE_RECORD_VALIDATION_RESULT_v1",
        "valid": not errors,
        "errors": errors,
        "thread_class": packet.get("thread_class", ""),
        "capture_method": packet.get("capture_method", ""),
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Validate one CODEX_THREAD_LAUNCH_SURFACE_CAPTURE_RECORD_v1 packet."
    )
    parser.add_argument("--capture-record-json", required=True)
    parser.add_argument("--out-json")
    args = parser.parse_args(argv)

    result = validate(_load_json(Path(args.capture_record_json)))
    if args.out_json:
        out_path = Path(args.out_json)
        if not out_path.is_absolute():
            raise SystemExit("non_absolute_out_json")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
