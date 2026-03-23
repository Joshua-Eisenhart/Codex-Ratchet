#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SCHEMA = "CODEX_THREAD_LAUNCH_SURFACE_CAPTURE_RECORD_v1"
THREAD_PLATFORM = "CODEX_DESKTOP"
ALLOWED_THREAD_CLASSES = {"A2_CONTROLLER", "A2_WORKER", "A1_WORKER"}
ALLOWED_CAPTURE_METHODS = {"MANUAL_OPERATOR", "PLAYWRIGHT_CAPTURE"}
ALLOWED_COMPOSER_READY = {"YES", "NO"}
ALLOWED_TARGET_STATUS = {"READY", "STALE", "UNVERIFIED"}
BLOCKED_LAUNCH_ROUTES = {"NONE", "about:blank"}


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"missing_input:{path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid_json:{path}:{exc.lineno}:{exc.colno}") from exc


def _text(value: object) -> str:
    return str(value).strip() if value is not None else ""


def _require_text(record: dict, key: str) -> str:
    value = _text(record.get(key))
    if not value:
        raise SystemExit(f"missing_{key}")
    return value


def _require_enum(value: str, allowed: set[str], key: str) -> str:
    if value not in allowed:
        raise SystemExit(f"invalid_{key}:{value}")
    return value


def _require_abs_existing_dir(value: str, key: str) -> str:
    text = _text(value)
    if not text:
        raise SystemExit(f"missing_{key}")
    path = Path(text)
    if not path.is_absolute():
        raise SystemExit(f"non_absolute_{key}")
    if not path.exists() or not path.is_dir():
        raise SystemExit(f"invalid_{key}")
    return str(path)


def _derive_target_status(
    *,
    route: str,
    title: str,
    verification: str,
    composer_ready: str,
) -> str:
    if route not in BLOCKED_LAUNCH_ROUTES and title and verification and composer_ready == "YES":
        return "READY"
    return "UNVERIFIED"


def _resolve_target_status(
    *,
    route: str,
    title: str,
    verification: str,
    composer_ready: str,
    target_status_override: str | None,
) -> str:
    natural_status = _derive_target_status(
        route=route,
        title=title,
        verification=verification,
        composer_ready=composer_ready,
    )
    if not target_status_override:
        return natural_status

    override = _require_enum(target_status_override, ALLOWED_TARGET_STATUS, "target_status_override")
    if override == "READY" and natural_status != "READY":
        raise SystemExit("invalid_ready_target_status_override")
    return override


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Create one CODEX_THREAD_LAUNCH_TARGET_v1 from one observed launch-surface capture record."
    )
    parser.add_argument("--capture-record-json", required=True)
    parser.add_argument("--workspace-root", required=True)
    parser.add_argument("--composer-ready-hint", required=True)
    parser.add_argument("--target-status-override", choices=sorted(ALLOWED_TARGET_STATUS))
    parser.add_argument("--out-json", required=True)
    args = parser.parse_args(argv)

    record_path = Path(args.capture_record_json)
    record = _load_json(record_path)

    schema = _text(record.get("schema"))
    if schema != SCHEMA:
        raise SystemExit(f"invalid_schema:{schema}")

    thread_class = _require_enum(_require_text(record, "thread_class"), ALLOWED_THREAD_CLASSES, "thread_class")
    launch_title = _require_text(record, "launch_surface_title_observed")
    launch_route = _require_text(record, "launch_route_observed")
    verification_text = _require_text(record, "visible_verification_text_observed")
    composer_ready = _require_enum(
        _require_text(record, "composer_ready_observed"), ALLOWED_COMPOSER_READY, "composer_ready_observed"
    )
    _require_text(record, "observed_at")
    _require_enum(_require_text(record, "capture_method"), ALLOWED_CAPTURE_METHODS, "capture_method")
    _require_text(record, "source_note")

    workspace_root = _require_abs_existing_dir(args.workspace_root, "workspace_root")

    composer_ready_hint = _text(args.composer_ready_hint)
    if not composer_ready_hint:
        raise SystemExit("missing_composer_ready_hint")

    target_status = _resolve_target_status(
        route=launch_route,
        title=launch_title,
        verification=verification_text,
        composer_ready=composer_ready,
        target_status_override=args.target_status_override,
    )

    packet = {
        "schema": "CODEX_THREAD_LAUNCH_TARGET_v1",
        "thread_class": thread_class,
        "thread_platform": THREAD_PLATFORM,
        "workspace_root": workspace_root,
        "launch_surface_title_hint": launch_title,
        "launch_route": launch_route,
        "visible_verification_text": verification_text,
        "composer_ready_observed": composer_ready,
        "composer_ready_hint": composer_ready_hint,
        "source_note": str(record_path),
        "target_status": target_status,
    }

    out_path = Path(args.out_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(packet, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
