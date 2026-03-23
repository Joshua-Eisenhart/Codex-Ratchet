#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        sys.stderr.write(result.stderr)
        raise SystemExit(result.returncode)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Create one browser capture record, convert it to one browser target packet, "
            "and run the browser go-on helper in one bounded wrapper."
        )
    )
    parser.add_argument("--sender-packet-json", required=True)
    parser.add_argument("--workspace-root", required=True)
    parser.add_argument("--composer-ready-hint", required=True)
    parser.add_argument("--target-thread-id", required=True)
    parser.add_argument("--thread-class", required=True)
    parser.add_argument("--thread-title-observed", required=True)
    parser.add_argument("--thread-url-or-route-observed", required=True)
    parser.add_argument("--visible-verification-text-observed", required=True)
    parser.add_argument("--composer-ready-observed", required=True)
    parser.add_argument("--observed-at", required=True)
    parser.add_argument("--capture-method", required=True)
    parser.add_argument("--source-note", required=True)
    parser.add_argument("--helper-mode", default="validate_only", choices=["validate_only", "blocked_proof"])
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args(argv)

    tool_dir = Path(__file__).resolve().parent
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    capture_json = out_dir / "browser_capture_record.json"
    target_json = out_dir / "browser_target_packet.json"
    proof_json = out_dir / "browser_go_on_proof_packet.json"

    _run(
        [
            sys.executable,
            str(tool_dir / "create_browser_codex_thread_capture_record.py"),
            "--target-thread-id",
            args.target_thread_id,
            "--thread-class",
            args.thread_class,
            "--thread-title-observed",
            args.thread_title_observed,
            "--thread-url-or-route-observed",
            args.thread_url_or_route_observed,
            "--visible-verification-text-observed",
            args.visible_verification_text_observed,
            "--composer-ready-observed",
            args.composer_ready_observed,
            "--observed-at",
            args.observed_at,
            "--capture-method",
            args.capture_method,
            "--source-note",
            args.source_note,
            "--out-json",
            str(capture_json),
        ]
    )

    _run(
        [
            sys.executable,
            str(tool_dir / "create_browser_target_from_capture_record.py"),
            "--capture-record-json",
            str(capture_json),
            "--workspace-root",
            args.workspace_root,
            "--composer-ready-hint",
            args.composer_ready_hint,
            "--out-json",
            str(target_json),
        ]
    )

    _run(
        [
            sys.executable,
            str(tool_dir / "browser_go_on_helper.py"),
            "--sender-packet-json",
            args.sender_packet_json,
            "--target-packet-json",
            str(target_json),
            "--out-json",
            str(proof_json),
            "--mode",
            args.helper_mode,
        ]
    )

    print(str(proof_json))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
