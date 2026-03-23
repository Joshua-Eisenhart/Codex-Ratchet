#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ALLOWED_THREAD_CLASSES = {"A2_WORKER", "A1_WORKER"}
ALLOWED_COMPOSER_READY = {"YES", "NO"}
ALLOWED_CAPTURE_METHODS = {"MANUAL_OPERATOR", "PLAYWRIGHT_CAPTURE"}


def _require_text(value: str, key: str) -> str:
    text = value.strip()
    if not text:
        raise SystemExit(f"missing_{key}")
    return text


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Create one BROWSER_CODEX_THREAD_CAPTURE_RECORD_v1 from bounded observed thread metadata."
    )
    parser.add_argument("--target-thread-id", required=True)
    parser.add_argument("--thread-class", required=True, choices=sorted(ALLOWED_THREAD_CLASSES))
    parser.add_argument("--thread-title-observed", required=True)
    parser.add_argument("--thread-url-or-route-observed", required=True)
    parser.add_argument("--visible-verification-text-observed", required=True)
    parser.add_argument(
        "--composer-ready-observed", required=True, choices=sorted(ALLOWED_COMPOSER_READY)
    )
    parser.add_argument("--observed-at", required=True)
    parser.add_argument("--capture-method", required=True, choices=sorted(ALLOWED_CAPTURE_METHODS))
    parser.add_argument("--source-note", required=True)
    parser.add_argument("--out-json", required=True)
    args = parser.parse_args(argv)

    record = {
        "schema": "BROWSER_CODEX_THREAD_CAPTURE_RECORD_v1",
        "target_thread_id": _require_text(args.target_thread_id, "target_thread_id"),
        "thread_class": args.thread_class,
        "thread_title_observed": _require_text(args.thread_title_observed, "thread_title_observed"),
        "thread_url_or_route_observed": _require_text(
            args.thread_url_or_route_observed, "thread_url_or_route_observed"
        ),
        "visible_verification_text_observed": _require_text(
            args.visible_verification_text_observed, "visible_verification_text_observed"
        ),
        "composer_ready_observed": args.composer_ready_observed,
        "observed_at": _require_text(args.observed_at, "observed_at"),
        "capture_method": args.capture_method,
        "source_note": _require_text(args.source_note, "source_note"),
    }

    out_path = Path(args.out_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
