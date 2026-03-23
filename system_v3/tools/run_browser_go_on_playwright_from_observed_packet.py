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
            "Run the browser go-on Playwright chain from one staged observed-thread packet "
            "plus one sender packet."
        )
    )
    parser.add_argument("--sender-packet-json", required=True)
    parser.add_argument("--observed-packet-json", required=True)
    parser.add_argument("--plan-mode", default="validate_only", choices=["validate_only", "real_send_once"])
    parser.add_argument("--session", default="codex-go-on")
    parser.add_argument("--prior-proof-json")
    parser.add_argument("--allow-real-send", action="store_true")
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args(argv)

    tool_dir = Path(__file__).resolve().parent
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    observed_packet = _load_json(Path(args.observed_packet_json))
    _require_fields(observed_packet)
    if args.plan_mode == "real_send_once" and not args.prior_proof_json:
        raise SystemExit("missing_prior_proof_for_real_send_once")

    capture_json = out_dir / "browser_capture_record.json"
    target_json = out_dir / "browser_target_packet.json"
    plan_json = out_dir / "browser_go_on_playwright_plan.json"
    proof_json = out_dir / "browser_go_on_proof_packet.json"
    command_log_json = out_dir / "browser_go_on_command_log.json"

    _run(
        [
            sys.executable,
            str(tool_dir / "create_browser_codex_thread_capture_record.py"),
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
            observed_packet["workspace_root"],
            "--composer-ready-hint",
            observed_packet["composer_ready_hint"],
            "--out-json",
            str(target_json),
        ]
    )

    build_cmd = [
        sys.executable,
        str(tool_dir / "build_browser_go_on_playwright_plan.py"),
        "--sender-packet-json",
        args.sender_packet_json,
        "--target-packet-json",
        str(target_json),
        "--out-json",
        str(plan_json),
        "--session",
        args.session,
        "--proof-json",
        str(proof_json),
        "--plan-mode",
        args.plan_mode,
    ]
    if args.plan_mode == "real_send_once":
        build_cmd.extend(["--prior-proof-json", args.prior_proof_json])
    _run(build_cmd)

    exec_cmd = [
        sys.executable,
        str(tool_dir / "execute_browser_go_on_playwright_plan.py"),
        "--plan-json",
        str(plan_json),
        "--out-proof-json",
        str(proof_json),
        "--out-command-log-json",
        str(command_log_json),
    ]
    if args.allow_real_send:
        exec_cmd.append("--allow-real-send")
    _run(exec_cmd)

    print(str(proof_json))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
