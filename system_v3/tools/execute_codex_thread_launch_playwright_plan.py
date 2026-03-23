#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


PWCLI = "/Users/joshuaeisenhart/.codex/skills/playwright/scripts/playwright_cli.sh"
PLAN_SCHEMA = "CODEX_THREAD_LAUNCH_PLAYWRIGHT_PLAN_v1"
PROOF_SCHEMA = "CODEX_THREAD_LAUNCH_PROOF_PACKET_v1"
DEFAULT_CMD_TIMEOUT_SEC = 20
BLOCKED_LAUNCH_ROUTES = {"NONE", "about:blank"}


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"missing_input:{path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid_json:{path}:{exc.lineno}:{exc.colno}") from exc


def _proof(
    plan: dict,
    *,
    status: str,
    detail: str,
    sent_at: str = "NONE",
    snapshot_path: str = "NONE",
) -> dict:
    return {
        "schema": PROOF_SCHEMA,
        "thread_class": plan.get("thread_class", ""),
        "role_label": plan.get("role_label", ""),
        "role_type": plan.get("role_type", ""),
        "execution_path": "PATH_BROWSER_AUTOMATED",
        "launch_status": status,
        "sent_at": sent_at,
        "source_launch_handoff": plan.get("source_launch_handoff", ""),
        "send_text_path": plan.get("send_text_path", ""),
        "detail": detail,
        "snapshot_path": snapshot_path,
    }


def _run_cmd(cmd: list[str], *, log: list[dict], timeout_sec: int) -> None:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec)
    except subprocess.TimeoutExpired as exc:
        log.append(
            {
                "cmd": cmd,
                "returncode": "TIMEOUT",
                "stdout": (exc.stdout or "")[-1000:],
                "stderr": (exc.stderr or "")[-1000:],
                "timeout_sec": timeout_sec,
            }
        )
        raise RuntimeError(f"command_timeout:{cmd[0]}:{timeout_sec}") from exc

    log.append(
        {
            "cmd": cmd,
            "returncode": proc.returncode,
            "stdout": proc.stdout[-1000:],
            "stderr": proc.stderr[-1000:],
            "timeout_sec": timeout_sec,
        }
    )
    if proc.returncode != 0:
        raise RuntimeError(f"command_failed:{cmd[0]}:{proc.returncode}")
    return proc.stdout


def _normalize_text(value: str) -> str:
    return " ".join(value.split()).strip().lower()


def _snapshot_contains_verification(snapshot_output: str, verification_text: str) -> bool:
    return _normalize_text(verification_text) in _normalize_text(snapshot_output)


def _validate_plan(plan: dict) -> list[str]:
    problems: list[str] = []
    if plan.get("schema") != PLAN_SCHEMA:
        problems.append("invalid_plan_schema")
    if plan.get("plan_status") != "READY":
        problems.append("plan_not_ready")
    if plan.get("plan_mode") not in {"validate_only", "real_send_once"}:
        problems.append("invalid_plan_mode")
    route = plan.get("launch_route", "")
    if not isinstance(route, str) or not route.strip() or route in BLOCKED_LAUNCH_ROUTES:
        problems.append("missing_launch_route")
    verification_text = plan.get("visible_verification_text", "")
    if not isinstance(verification_text, str) or not verification_text.strip():
        problems.append("missing_visible_verification_text")
    send_text_path = Path(str(plan.get("send_text_path", "")).strip())
    if not send_text_path.is_absolute() or not send_text_path.exists():
        problems.append("missing_send_text_path")
    return problems


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Execute one bounded Playwright launch plan and emit one launch proof packet."
    )
    parser.add_argument("--plan-json", required=True)
    parser.add_argument("--out-proof-json", required=True)
    parser.add_argument("--out-command-log-json")
    parser.add_argument("--allow-real-send", action="store_true")
    parser.add_argument("--cmd-timeout-sec", type=int, default=DEFAULT_CMD_TIMEOUT_SEC)
    args = parser.parse_args(argv)

    plan_path = Path(args.plan_json)
    out_proof_path = Path(args.out_proof_json)
    out_log_path = Path(args.out_command_log_json) if args.out_command_log_json else None

    plan = _load_json(plan_path)
    problems = _validate_plan(plan)
    command_log: list[dict] = []

    if problems:
        proof = _proof(plan, status="LAUNCH_BLOCKED", detail=",".join(dict.fromkeys(problems)))
    elif plan.get("plan_mode") == "real_send_once" and not args.allow_real_send:
        proof = _proof(plan, status="LAUNCH_BLOCKED", detail="real_launch_requires_explicit_enable")
    else:
        session = plan.get("session", "codex-thread-launch")
        route = plan["launch_route"]
        snapshot_path = "NONE"
        try:
            _run_cmd([PWCLI, "--session", session, "open", route, "--headed"], log=command_log, timeout_sec=args.cmd_timeout_sec)
            snapshot_stdout = _run_cmd(
                [PWCLI, "--session", session, "snapshot"],
                log=command_log,
                timeout_sec=args.cmd_timeout_sec,
            )
            snapshot_path = "PLAYWRIGHT_SESSION_SNAPSHOT"
            if not _snapshot_contains_verification(snapshot_stdout, str(plan.get("visible_verification_text", ""))):
                proof = _proof(
                    plan,
                    status="LAUNCH_BLOCKED",
                    detail="visible_verification_text_not_found_in_snapshot",
                    snapshot_path=snapshot_path,
                )
            elif plan.get("plan_mode") == "real_send_once":
                send_text = Path(plan["send_text_path"]).read_text(encoding="utf-8")
                _run_cmd([PWCLI, "--session", session, "type", send_text], log=command_log, timeout_sec=args.cmd_timeout_sec)
                _run_cmd([PWCLI, "--session", session, "press", "Enter"], log=command_log, timeout_sec=args.cmd_timeout_sec)
                _run_cmd([PWCLI, "--session", session, "snapshot"], log=command_log, timeout_sec=args.cmd_timeout_sec)
                proof = _proof(
                    plan,
                    status="LAUNCH_SUCCESS",
                    detail="browser_real_launch_once_completed",
                    sent_at=datetime.now(timezone.utc).isoformat(),
                    snapshot_path=snapshot_path,
                )
            else:
                proof = _proof(
                    plan,
                    status="LAUNCH_BLOCKED",
                    detail="browser_launch_not_attempted_validate_only",
                    snapshot_path=snapshot_path,
                )
        except Exception as exc:  # noqa: BLE001
            proof = _proof(plan, status="LAUNCH_FAILED", detail=str(exc), snapshot_path=snapshot_path)

    out_proof_path.parent.mkdir(parents=True, exist_ok=True)
    out_proof_path.write_text(json.dumps(proof, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if out_log_path is not None:
        out_log_path.parent.mkdir(parents=True, exist_ok=True)
        out_log_path.write_text(json.dumps(command_log, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps(proof, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
