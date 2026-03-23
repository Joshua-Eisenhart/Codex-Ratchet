#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ALLOWED_THREAD_CLASSES = {"A2_WORKER", "A1_WORKER"}
ALLOWED_CAPTURE_METHODS = {"MANUAL_OPERATOR", "PLAYWRIGHT_CAPTURE"}
ALLOWED_COMPOSER_READY = {"YES", "NO"}
ALLOWED_TARGET_STATUS = {"READY", "STALE", "UNVERIFIED"}
THREAD_PLATFORM = "CODEX_DESKTOP"


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


def _derive_target_status(
    route: str,
    title: str,
    verification: str,
    composer_ready: str,
    target_status_override: str | None,
) -> str:
    if target_status_override:
        return _require_enum(target_status_override, ALLOWED_TARGET_STATUS, "target_status_override")
    if route != "NONE" and title and verification and composer_ready == "YES":
        return "READY"
    return "UNVERIFIED"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Create one BROWSER_CODEX_THREAD_TARGET_v1 from one observed browser capture record."
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
    if schema != "BROWSER_CODEX_THREAD_CAPTURE_RECORD_v1":
        raise SystemExit(f"invalid_schema:{schema}")

    thread_id = _require_text(record, "target_thread_id")
    thread_class = _require_enum(_require_text(record, "thread_class"), ALLOWED_THREAD_CLASSES, "thread_class")
    thread_title = _require_text(record, "thread_title_observed")
    thread_route = _require_text(record, "thread_url_or_route_observed")
    verification_text = _require_text(record, "visible_verification_text_observed")
    composer_ready = _require_enum(
        _require_text(record, "composer_ready_observed"), ALLOWED_COMPOSER_READY, "composer_ready_observed"
    )
    _require_text(record, "observed_at")
    _require_enum(_require_text(record, "capture_method"), ALLOWED_CAPTURE_METHODS, "capture_method")
    source_note = _require_text(record, "source_note")

    workspace_root = _text(args.workspace_root)
    if not workspace_root:
        raise SystemExit("missing_workspace_root")

    composer_ready_hint = _text(args.composer_ready_hint)
    if not composer_ready_hint:
        raise SystemExit("missing_composer_ready_hint")

    target_status = _derive_target_status(
        route=thread_route,
        title=thread_title,
        verification=verification_text,
        composer_ready=composer_ready,
        target_status_override=args.target_status_override,
    )

    packet = {
        "schema": "BROWSER_CODEX_THREAD_TARGET_v1",
        "target_thread_id": thread_id,
        "thread_class": thread_class,
        "thread_platform": THREAD_PLATFORM,
        "workspace_root": workspace_root,
        "thread_title_hint": thread_title,
        "thread_url_or_route": thread_route,
        "visible_verification_text": verification_text,
        "composer_ready_hint": composer_ready_hint,
        "source_capture_record": source_note,
        "target_status": target_status,
    }

    out_path = Path(args.out_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(packet, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
