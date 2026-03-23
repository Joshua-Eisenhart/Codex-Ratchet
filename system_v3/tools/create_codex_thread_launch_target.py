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


def _require_text(value: str, key: str) -> str:
    text = value.strip()
    if not text:
        raise SystemExit(f"missing_{key}")
    return text


def _require_abs_existing_dir(value: str, key: str) -> str:
    text = _require_text(value, key)
    path = Path(text)
    if not path.is_absolute():
        raise SystemExit(f"non_absolute_{key}")
    if not path.exists() or not path.is_dir():
        raise SystemExit(f"invalid_{key}")
    return str(path)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Create one CODEX_THREAD_LAUNCH_TARGET_v1 packet from bounded launch-target metadata."
    )
    parser.add_argument("--thread-class", required=True, choices=sorted(ALLOWED_THREAD_CLASSES))
    parser.add_argument("--workspace-root", required=True)
    parser.add_argument("--launch-surface-title-hint", required=True)
    parser.add_argument("--launch-route", required=True)
    parser.add_argument("--visible-verification-text", required=True)
    parser.add_argument("--composer-ready-observed", required=True, choices=sorted(ALLOWED_COMPOSER_READY))
    parser.add_argument("--composer-ready-hint", required=True)
    parser.add_argument("--source-note", required=True)
    parser.add_argument("--target-status", required=True, choices=sorted(ALLOWED_TARGET_STATUS))
    parser.add_argument("--out-json", required=True)
    args = parser.parse_args(argv)

    launch_route = _require_text(args.launch_route, "launch_route")
    if args.target_status == "READY":
        if args.composer_ready_observed != "YES":
            raise SystemExit("invalid_ready_composer_ready_observed")
        if launch_route in BLOCKED_READY_LAUNCH_ROUTES:
            raise SystemExit("invalid_ready_launch_route")

    packet = {
        "schema": SCHEMA,
        "thread_class": args.thread_class,
        "thread_platform": THREAD_PLATFORM,
        "workspace_root": _require_abs_existing_dir(args.workspace_root, "workspace_root"),
        "launch_surface_title_hint": _require_text(args.launch_surface_title_hint, "launch_surface_title_hint"),
        "launch_route": launch_route,
        "visible_verification_text": _require_text(args.visible_verification_text, "visible_verification_text"),
        "composer_ready_observed": args.composer_ready_observed,
        "composer_ready_hint": _require_text(args.composer_ready_hint, "composer_ready_hint"),
        "source_note": _require_text(args.source_note, "source_note"),
        "target_status": args.target_status,
    }

    out_path = Path(args.out_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(packet, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
