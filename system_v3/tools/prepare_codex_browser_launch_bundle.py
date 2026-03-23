#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from build_codex_thread_launch_playwright_plan import main as build_plan_main
from execute_codex_thread_launch_playwright_plan import main as execute_plan_main


def _bundle_paths(handoff_path: Path, out_dir: Path) -> tuple[Path, Path, Path]:
    stem = handoff_path.stem
    return (
        out_dir / f"{stem}__LAUNCH_PLAN.json",
        out_dir / f"{stem}__LAUNCH_PROOF.json",
        out_dir / f"{stem}__COMMAND_LOG.json",
    )


def _result_path(handoff_path: Path, out_dir: Path) -> Path:
    return out_dir / f"{handoff_path.stem}__BUNDLE_RESULT.json"


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"missing_input:{path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid_json:{path}:{exc.lineno}:{exc.colno}") from exc


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Prepare one bounded browser-launch bundle from a launch handoff plus launch target."
    )
    parser.add_argument("--launch-handoff-json", required=True)
    parser.add_argument("--launch-target-json", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--session", default="codex-thread-launch")
    parser.add_argument("--plan-mode", choices=["validate_only", "real_send_once"], default="validate_only")
    parser.add_argument("--allow-real-send", action="store_true")
    parser.add_argument("--cmd-timeout-sec", type=int)
    args = parser.parse_args(argv)

    handoff_path = Path(args.launch_handoff_json)
    target_path = Path(args.launch_target_json)
    out_dir = Path(args.out_dir)
    if not handoff_path.is_absolute():
        raise SystemExit("non_absolute_launch_handoff_json")
    if not target_path.is_absolute():
        raise SystemExit("non_absolute_launch_target_json")
    if not out_dir.is_absolute():
        raise SystemExit("non_absolute_out_dir")

    plan_path, proof_path, log_path = _bundle_paths(handoff_path, out_dir)
    result_path = _result_path(handoff_path, out_dir)

    build_rc = build_plan_main(
        [
            "--launch-handoff-json",
            str(handoff_path),
            "--launch-target-json",
            str(target_path),
            "--out-json",
            str(plan_path),
            "--session",
            args.session,
            "--plan-mode",
            args.plan_mode,
        ]
    )

    plan = _load_json(plan_path)
    execute_args = [
        "--plan-json",
        str(plan_path),
        "--out-proof-json",
        str(proof_path),
        "--out-command-log-json",
        str(log_path),
    ]
    if args.allow_real_send:
        execute_args.append("--allow-real-send")
    if args.cmd_timeout_sec is not None:
        execute_args.extend(["--cmd-timeout-sec", str(args.cmd_timeout_sec)])
    execute_rc = execute_plan_main(execute_args)
    proof = _load_json(proof_path)

    proof_status = proof.get("launch_status")
    proof_detail = proof.get("detail")
    if plan.get("plan_status") != "READY":
        status = "BLOCKED"
    elif proof_status == "LAUNCH_FAILED":
        status = "FAILED"
    elif proof_status == "LAUNCH_SUCCESS":
        status = "READY"
    elif (
        proof_status == "LAUNCH_BLOCKED"
        and proof_detail == "browser_launch_not_attempted_validate_only"
    ):
        status = "READY"
    elif proof_status == "LAUNCH_BLOCKED":
        status = "BLOCKED"
    else:
        status = "FAILED"

    result = {
        "schema": "CODEX_BROWSER_LAUNCH_BUNDLE_RESULT_v1",
        "status": status,
        "plan_json": str(plan_path),
        "proof_json": str(proof_path),
        "command_log_json": str(log_path),
        "plan_status": plan.get("plan_status", ""),
        "proof_status": proof.get("launch_status", ""),
        "proof_detail": proof.get("detail", ""),
        "cmd_timeout_sec": args.cmd_timeout_sec,
        "build_rc": build_rc,
        "execute_rc": execute_rc,
    }

    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "READY" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
