#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


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
    result_path = out_dir / "codex_browser_launch_bundle_from_observed_surface__result.json"
    result_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Create one launch-surface capture record, convert it to one launch target packet, "
            "and prepare one bounded browser-launch bundle."
        )
    )
    parser.add_argument("--launch-handoff-json", required=True)
    parser.add_argument("--workspace-root", required=True)
    parser.add_argument("--composer-ready-hint", required=True)
    parser.add_argument("--thread-class", required=True)
    parser.add_argument("--launch-surface-title-observed", required=True)
    parser.add_argument("--launch-route-observed", required=True)
    parser.add_argument("--visible-verification-text-observed", required=True)
    parser.add_argument("--composer-ready-observed", required=True)
    parser.add_argument("--observed-at", required=True)
    parser.add_argument("--capture-method", required=True)
    parser.add_argument("--source-note", required=True)
    parser.add_argument("--plan-mode", default="validate_only", choices=["validate_only", "real_send_once"])
    parser.add_argument("--session", default="codex-thread-launch")
    parser.add_argument("--allow-real-send", action="store_true")
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args(argv)

    tool_dir = Path(__file__).resolve().parent
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    capture_json = out_dir / "codex_thread_launch_surface_capture_record.json"
    target_json = out_dir / "codex_thread_launch_target.json"
    capture_validation_json = out_dir / "codex_thread_launch_surface_capture_record__validation.json"
    target_validation_json = out_dir / "codex_thread_launch_target__validation.json"
    bundle_result_json = out_dir / f"{Path(args.launch_handoff_json).stem}__BUNDLE_RESULT.json"

    _run(
        [
            sys.executable,
            str(tool_dir / "create_codex_thread_launch_surface_capture_record.py"),
            "--thread-class",
            args.thread_class,
            "--launch-surface-title-observed",
            args.launch_surface_title_observed,
            "--launch-route-observed",
            args.launch_route_observed,
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
            str(tool_dir / "validate_codex_thread_launch_surface_capture_record.py"),
            "--capture-record-json",
            str(capture_json),
            "--out-json",
            str(capture_validation_json),
        ]
    )

    _run(
        [
            sys.executable,
            str(tool_dir / "create_codex_thread_launch_target_from_capture_record.py"),
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
    bundle_rc = _run(bundle_args, allowed_returncodes={0, 1})

    result = {
        "schema": "CODEX_BROWSER_LAUNCH_FROM_OBSERVED_SURFACE_RESULT_v1",
        "status": "READY" if bundle_rc == 0 else "BLOCKED",
        "launch_handoff_json": args.launch_handoff_json,
        "capture_record_json": str(capture_json),
        "capture_validation_json": str(capture_validation_json),
        "launch_target_json": str(target_json),
        "target_validation_json": str(target_validation_json),
        "bundle_result_json": str(bundle_result_json),
        "out_dir": str(out_dir),
        "bundle_rc": bundle_rc,
    }
    _write_result(out_dir, result)

    print(str(out_dir))
    return bundle_rc


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
