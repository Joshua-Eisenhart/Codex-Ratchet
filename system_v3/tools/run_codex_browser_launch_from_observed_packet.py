#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


REQUIRED_PACKET_FIELDS = [
    "thread_class",
    "launch_surface_title_observed",
    "launch_route_observed",
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


def _run(cmd: list[str], *, allowed_returncodes: set[int] | None = None) -> int:
    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if result.stdout:
        sys.stdout.write(result.stdout)
    if result.returncode != 0 and (
        allowed_returncodes is None or result.returncode not in allowed_returncodes
    ):
        sys.stderr.write(result.stderr)
        raise SystemExit(result.returncode)
    return result.returncode


def _write_result(out_dir: Path, payload: dict) -> None:
    result_path = out_dir / "codex_browser_launch_from_observed_packet__result.json"
    result_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run the fresh-thread browser-launch chain from one staged observed launch packet "
            "plus one launch handoff."
        )
    )
    parser.add_argument("--launch-handoff-json", required=True)
    parser.add_argument("--observed-packet-json", required=True)
    parser.add_argument("--plan-mode", default="validate_only", choices=["validate_only", "real_send_once"])
    parser.add_argument("--session", default="codex-thread-launch")
    parser.add_argument("--allow-real-send", action="store_true")
    parser.add_argument("--cmd-timeout-sec", type=int)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args(argv)

    tool_dir = Path(__file__).resolve().parent
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    observed_validation_json = out_dir / "codex_thread_launch_observed_packet__validation.json"
    capture_wrapper_result_json = out_dir / "codex_browser_launch_from_capture_record__result.json"
    capture_validation_json = out_dir / "codex_thread_launch_surface_capture_record__validation.json"
    target_validation_json = out_dir / "codex_thread_launch_target__validation.json"

    observed_packet = _load_json(Path(args.observed_packet_json))
    observed_validation_rc = _run(
        [
            sys.executable,
            str(tool_dir / "validate_codex_thread_launch_observed_packet.py"),
            "--observed-packet-json",
            args.observed_packet_json,
            "--out-json",
            str(observed_validation_json),
        ],
        allowed_returncodes={0, 1},
    )
    if observed_validation_rc != 0:
        result = {
            "schema": "CODEX_BROWSER_LAUNCH_FROM_OBSERVED_PACKET_RESULT_v1",
            "status": "BLOCKED",
            "detail": "invalid_observed_packet",
            "launch_handoff_json": args.launch_handoff_json,
            "observed_packet_json": args.observed_packet_json,
            "observed_validation_json": str(observed_validation_json),
            "capture_record_json": "NONE",
            "capture_wrapper_result_json": "NONE",
            "capture_validation_json": "NONE",
            "target_validation_json": "NONE",
            "out_dir": str(out_dir),
            "observed_validation_rc": observed_validation_rc,
            "wrapper_rc": 1,
        }
        _write_result(out_dir, result)
        print(str(out_dir))
        return 1
    _require_fields(observed_packet)

    capture_json = out_dir / "codex_thread_launch_surface_capture_record.json"
    _run(
        [
            sys.executable,
            str(tool_dir / "create_codex_thread_launch_surface_capture_record.py"),
            "--thread-class",
            observed_packet["thread_class"],
            "--launch-surface-title-observed",
            observed_packet["launch_surface_title_observed"],
            "--launch-route-observed",
            observed_packet["launch_route_observed"],
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

    run_args = [
        sys.executable,
        str(tool_dir / "run_codex_browser_launch_from_capture_record.py"),
        "--launch-handoff-json",
        args.launch_handoff_json,
        "--capture-record-json",
        str(capture_json),
        "--workspace-root",
        observed_packet["workspace_root"],
        "--composer-ready-hint",
        observed_packet["composer_ready_hint"],
        "--plan-mode",
        args.plan_mode,
        "--session",
        args.session,
        "--out-dir",
        str(out_dir),
    ]
    if args.allow_real_send:
        run_args.append("--allow-real-send")
    if args.cmd_timeout_sec is not None:
        run_args.extend(["--cmd-timeout-sec", str(args.cmd_timeout_sec)])
    wrapper_rc = _run(run_args, allowed_returncodes={0, 1})

    result = {
        "schema": "CODEX_BROWSER_LAUNCH_FROM_OBSERVED_PACKET_RESULT_v1",
        "status": "READY" if wrapper_rc == 0 else "BLOCKED",
        "launch_handoff_json": args.launch_handoff_json,
        "observed_packet_json": args.observed_packet_json,
        "observed_validation_json": str(observed_validation_json),
        "capture_record_json": str(capture_json),
        "capture_wrapper_result_json": str(capture_wrapper_result_json),
        "capture_validation_json": str(capture_validation_json),
        "target_validation_json": str(target_validation_json),
        "out_dir": str(out_dir),
        "observed_validation_rc": observed_validation_rc,
        "cmd_timeout_sec": args.cmd_timeout_sec,
        "wrapper_rc": wrapper_rc,
    }
    _write_result(out_dir, result)

    print(str(out_dir))
    return wrapper_rc


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
