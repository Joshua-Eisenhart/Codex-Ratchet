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
    result_path = out_dir / "codex_browser_launch_from_capture_record__result.json"
    result_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run the fresh-thread browser-launch chain from one staged launch-surface capture record "
            "plus one launch handoff."
        )
    )
    parser.add_argument("--launch-handoff-json", required=True)
    parser.add_argument("--capture-record-json", required=True)
    parser.add_argument("--workspace-root", required=True)
    parser.add_argument("--composer-ready-hint", required=True)
    parser.add_argument("--plan-mode", default="validate_only", choices=["validate_only", "real_send_once"])
    parser.add_argument("--session", default="codex-thread-launch")
    parser.add_argument("--allow-real-send", action="store_true")
    parser.add_argument("--cmd-timeout-sec", type=int)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args(argv)

    tool_dir = Path(__file__).resolve().parent
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    capture_validation_json = out_dir / "codex_thread_launch_surface_capture_record__validation.json"
    target_validation_json = out_dir / "codex_thread_launch_target__validation.json"
    bundle_result_json = out_dir / f"{Path(args.launch_handoff_json).stem}__BUNDLE_RESULT.json"

    capture_packet = _load_json(Path(args.capture_record_json))
    capture_validation_rc = _run(
        [
            sys.executable,
            str(tool_dir / "validate_codex_thread_launch_surface_capture_record.py"),
            "--capture-record-json",
            args.capture_record_json,
            "--out-json",
            str(capture_validation_json),
        ],
        allowed_returncodes={0, 1},
    )
    if capture_validation_rc != 0:
        result = {
            "schema": "CODEX_BROWSER_LAUNCH_FROM_CAPTURE_RECORD_RESULT_v1",
            "status": "BLOCKED",
            "detail": "invalid_capture_record",
            "launch_handoff_json": args.launch_handoff_json,
            "capture_record_json": args.capture_record_json,
            "capture_validation_json": str(capture_validation_json),
            "launch_target_json": "NONE",
            "target_validation_json": "NONE",
            "bundle_result_json": "NONE",
            "out_dir": str(out_dir),
            "capture_validation_rc": capture_validation_rc,
            "bundle_rc": 1,
        }
        _write_result(out_dir, result)
        print(str(out_dir))
        return 1
    _require_fields(capture_packet)

    target_json = out_dir / "codex_thread_launch_target.json"
    _run(
        [
            sys.executable,
            str(tool_dir / "create_codex_thread_launch_target_from_capture_record.py"),
            "--capture-record-json",
            args.capture_record_json,
            "--workspace-root",
            args.workspace_root,
            "--composer-ready-hint",
            args.composer_ready_hint,
            "--out-json",
            str(target_json),
        ]
    )
    target_validation_rc = _run(
        [
            sys.executable,
            str(tool_dir / "validate_codex_thread_launch_target.py"),
            "--target-json",
            str(target_json),
            "--out-json",
            str(target_validation_json),
        ],
        allowed_returncodes={0, 1},
    )

    bundle_args = [
        sys.executable,
        str(tool_dir / "prepare_codex_browser_launch_bundle.py"),
        "--launch-handoff-json",
        args.launch_handoff_json,
        "--launch-target-json",
        str(target_json),
        "--out-dir",
        str(out_dir),
        "--session",
        args.session,
        "--plan-mode",
        args.plan_mode,
    ]
    if args.allow_real_send:
        bundle_args.append("--allow-real-send")
    if args.cmd_timeout_sec is not None:
        bundle_args.extend(["--cmd-timeout-sec", str(args.cmd_timeout_sec)])
    bundle_rc = _run(bundle_args, allowed_returncodes={0, 1})

    result = {
        "schema": "CODEX_BROWSER_LAUNCH_FROM_CAPTURE_RECORD_RESULT_v1",
        "status": "READY" if bundle_rc == 0 else "BLOCKED",
        "launch_handoff_json": args.launch_handoff_json,
        "capture_record_json": args.capture_record_json,
        "capture_validation_json": str(capture_validation_json),
        "launch_target_json": str(target_json),
        "target_validation_json": str(target_validation_json),
        "bundle_result_json": str(bundle_result_json),
        "out_dir": str(out_dir),
        "capture_validation_rc": capture_validation_rc,
        "target_validation_rc": target_validation_rc,
        "cmd_timeout_sec": args.cmd_timeout_sec,
        "bundle_rc": bundle_rc,
    }
    _write_result(out_dir, result)

    print(str(out_dir))
    return bundle_rc


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
