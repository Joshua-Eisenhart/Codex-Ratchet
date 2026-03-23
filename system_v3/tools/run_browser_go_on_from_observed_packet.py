#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


REQUIRED_PACKET_FIELDS = [
    "target_thread_id",
    "thread_class",
    "thread_title_observed",
    "thread_url_or_route_observed",
    "visible_verification_text_observed",
    "composer_ready_observed",
    "observed_at",
    "capture_method",
    "source_note",
    "workspace_root",
    "composer_ready_hint",
]


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"missing_input:{path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid_json:{path}:{exc.lineno}:{exc.colno}") from exc


def _require_fields(packet: dict) -> None:
    missing: list[str] = []
    for key in REQUIRED_PACKET_FIELDS:
        value = packet.get(key)
        if value is None:
            missing.append(key)
        elif isinstance(value, str) and not value.strip():
            missing.append(key)
    if missing:
        raise SystemExit("missing_packet_fields:" + ",".join(missing))


def _run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        sys.stderr.write(result.stderr)
        raise SystemExit(result.returncode)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run the browser go-on helper chain from one staged observed-thread packet "
            "plus one sender packet."
        )
    )
    parser.add_argument("--sender-packet-json", required=True)
    parser.add_argument("--observed-packet-json", required=True)
    parser.add_argument("--helper-mode", default="validate_only", choices=["validate_only", "blocked_proof"])
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args(argv)

    tool_dir = Path(__file__).resolve().parent
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    observed_packet = _load_json(Path(args.observed_packet_json))
    _require_fields(observed_packet)

    _run(
        [
            sys.executable,
            str(tool_dir / "run_browser_go_on_from_observed_thread.py"),
            "--sender-packet-json",
            args.sender_packet_json,
            "--workspace-root",
            observed_packet["workspace_root"],
            "--composer-ready-hint",
            observed_packet["composer_ready_hint"],
            "--target-thread-id",
            observed_packet["target_thread_id"],
            "--thread-class",
            observed_packet["thread_class"],
            "--thread-title-observed",
            observed_packet["thread_title_observed"],
            "--thread-url-or-route-observed",
            observed_packet["thread_url_or_route_observed"],
            "--visible-verification-text-observed",
            observed_packet["visible_verification_text_observed"],
            "--composer-ready-observed",
            observed_packet["composer_ready_observed"],
            "--observed-at",
            observed_packet["observed_at"],
            "--capture-method",
            observed_packet["capture_method"],
            "--source-note",
            observed_packet["source_note"],
            "--helper-mode",
            args.helper_mode,
            "--out-dir",
            str(out_dir),
        ]
    )

    print(str(out_dir / "browser_go_on_proof_packet.json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
