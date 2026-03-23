#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SCHEMA = "CODEX_THREAD_LAUNCH_TARGET_v1"
THREAD_PLATFORM = "CODEX_DESKTOP"
ALLOWED_THREAD_CLASSES = {"A2_CONTROLLER", "A2_WORKER", "A1_WORKER"}
ALLOWED_COMPOSER_READY = {"YES", "NO"}
ALLOWED_TARGET_STATUS = {"READY", "STALE", "UNVERIFIED"}
BLOCKED_READY_LAUNCH_ROUTES = {"NONE", "about:blank"}


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"missing_input:{path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid_json:{path}:{exc.lineno}:{exc.colno}") from exc


def _is_nonempty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_abs_existing_dir(value: object) -> bool:
    if not _is_nonempty_text(value):
        return False
    path = Path(str(value).strip())
    return path.is_absolute() and path.exists() and path.is_dir()


def validate(packet: dict) -> dict:
    errors: list[str] = []

    if packet.get("schema") != SCHEMA:
        errors.append("invalid_schema")
    if packet.get("thread_platform") != THREAD_PLATFORM:
        errors.append("invalid_thread_platform")
    if packet.get("thread_class") not in ALLOWED_THREAD_CLASSES:
        errors.append("invalid_thread_class")
    if packet.get("composer_ready_observed") not in ALLOWED_COMPOSER_READY:
        errors.append("invalid_composer_ready_observed")
    if packet.get("target_status") not in ALLOWED_TARGET_STATUS:
        errors.append("invalid_target_status")

    for key in (
        "launch_surface_title_hint",
        "launch_route",
        "visible_verification_text",
        "composer_ready_hint",
        "source_note",
    ):
        if not _is_nonempty_text(packet.get(key)):
            errors.append(f"missing_{key}")
    if not _is_abs_existing_dir(packet.get("workspace_root")):
        errors.append("invalid_workspace_root")

    route = str(packet.get("launch_route", "")).strip()
    if packet.get("target_status") == "READY":
        if route in BLOCKED_READY_LAUNCH_ROUTES:
            errors.append("invalid_ready_launch_route")
        if packet.get("composer_ready_observed") != "YES":
            errors.append("invalid_ready_composer_ready_observed")

    return {
        "schema": "CODEX_THREAD_LAUNCH_TARGET_VALIDATION_RESULT_v1",
        "valid": not errors,
        "errors": errors,
        "thread_class": packet.get("thread_class", ""),
        "target_status": packet.get("target_status", ""),
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Validate one CODEX_THREAD_LAUNCH_TARGET_v1 packet."
    )
    parser.add_argument("--target-json", required=True)
    parser.add_argument("--out-json")
    args = parser.parse_args(argv)

    result = validate(_load_json(Path(args.target_json)))
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
