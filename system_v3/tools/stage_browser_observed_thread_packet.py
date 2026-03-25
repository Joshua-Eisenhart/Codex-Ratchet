import os
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


ALLOWED_THREAD_CLASSES = {"A2_WORKER", "A1_WORKER"}
ALLOWED_COMPOSER_READY = {"YES", "NO"}
ALLOWED_CAPTURE_METHODS = {"MANUAL_OPERATOR", "PLAYWRIGHT_CAPTURE"}
ALLOWED_READY_HINTS = {"READY", "UNVERIFIED"}
DEFAULT_SINK_DIR = Path(
    os.environ.get("CODEX_RATCHET_ROOT", ".") + "/work/audit_tmp/browser_thread_observations"
)


def _require_text(value: str, key: str) -> str:
    text = value.strip()
    if not text:
        raise SystemExit(f"missing_{key}")
    return text


def _safe_thread_id(thread_id: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in thread_id)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Stage one browser observed-thread sink packet into the repo-held staging directory."
    )
    parser.add_argument("--target-thread-id", required=True)
    parser.add_argument("--thread-class", required=True, choices=sorted(ALLOWED_THREAD_CLASSES))
    parser.add_argument("--thread-title-observed", required=True)
    parser.add_argument("--thread-url-or-route-observed", required=True)
    parser.add_argument("--visible-verification-text-observed", required=True)
    parser.add_argument("--composer-ready-observed", required=True, choices=sorted(ALLOWED_COMPOSER_READY))
    parser.add_argument("--capture-method", required=True, choices=sorted(ALLOWED_CAPTURE_METHODS))
    parser.add_argument("--source-note", required=True)
    parser.add_argument("--workspace-root", default=os.environ.get("CODEX_RATCHET_ROOT", ".") + "")
    parser.add_argument("--composer-ready-hint", required=True, choices=sorted(ALLOWED_READY_HINTS))
    parser.add_argument("--observed-at")
    parser.add_argument("--out-json")
    args = parser.parse_args(argv)

    observed_at = args.observed_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    thread_id = _require_text(args.target_thread_id, "target_thread_id")
    packet = {
        "target_thread_id": thread_id,
        "thread_class": args.thread_class,
        "thread_title_observed": _require_text(args.thread_title_observed, "thread_title_observed"),
        "thread_url_or_route_observed": _require_text(
            args.thread_url_or_route_observed, "thread_url_or_route_observed"
        ),
        "visible_verification_text_observed": _require_text(
            args.visible_verification_text_observed, "visible_verification_text_observed"
        ),
        "composer_ready_observed": args.composer_ready_observed,
        "observed_at": observed_at,
        "capture_method": args.capture_method,
        "source_note": _require_text(args.source_note, "source_note"),
        "workspace_root": _require_text(args.workspace_root, "workspace_root"),
        "composer_ready_hint": args.composer_ready_hint,
    }

    if args.out_json:
        out_path = Path(args.out_json)
    else:
        stamp = observed_at.replace(":", "").replace("-", "")
        out_path = DEFAULT_SINK_DIR / f"browser_observed_thread__{_safe_thread_id(thread_id)}__{stamp}.json"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
