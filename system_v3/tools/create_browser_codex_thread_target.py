#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ALLOWED_THREAD_CLASSES = {"A2_WORKER", "A1_WORKER"}
ALLOWED_TARGET_STATUS = {"READY", "STALE", "UNVERIFIED"}
THREAD_PLATFORM = "CODEX_DESKTOP"


def _require_text(value: str, key: str) -> str:
    text = value.strip()
    if not text:
        raise SystemExit(f"missing_{key}")
    return text


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Create one BROWSER_CODEX_THREAD_TARGET_v1 packet from bounded Codex thread metadata."
    )
    parser.add_argument("--target-thread-id", required=True)
    parser.add_argument("--thread-class", required=True, choices=sorted(ALLOWED_THREAD_CLASSES))
    parser.add_argument("--workspace-root", required=True)
    parser.add_argument("--thread-title-hint", required=True)
    parser.add_argument("--thread-url-or-route", required=True)
    parser.add_argument("--visible-verification-text", required=True)
    parser.add_argument("--composer-ready-hint", required=True)
    parser.add_argument("--source-capture-record", required=True)
    parser.add_argument("--target-status", required=True, choices=sorted(ALLOWED_TARGET_STATUS))
    parser.add_argument("--out-json", required=True)
    args = parser.parse_args(argv)

    packet = {
        "schema": "BROWSER_CODEX_THREAD_TARGET_v1",
        "target_thread_id": _require_text(args.target_thread_id, "target_thread_id"),
        "thread_class": args.thread_class,
        "thread_platform": THREAD_PLATFORM,
        "workspace_root": _require_text(args.workspace_root, "workspace_root"),
        "thread_title_hint": _require_text(args.thread_title_hint, "thread_title_hint"),
        "thread_url_or_route": _require_text(args.thread_url_or_route, "thread_url_or_route"),
        "visible_verification_text": _require_text(
            args.visible_verification_text, "visible_verification_text"
        ),
        "composer_ready_hint": _require_text(args.composer_ready_hint, "composer_ready_hint"),
        "source_capture_record": _require_text(args.source_capture_record, "source_capture_record"),
        "target_status": args.target_status,
    }

    out_path = Path(args.out_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(packet, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
