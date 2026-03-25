import os
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from validate_codex_thread_launch_target import validate as validate_target
from validate_codex_thread_launch_handoff import validate as validate_handoff


PWCLI = os.path.expanduser("~/.codex") + "/skills/playwright/scripts/playwright_cli.sh"
ALLOWED_PLAN_MODES = {"validate_only", "real_send_once"}
BLOCKED_LAUNCH_ROUTES = {"NONE", "about:blank"}


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"missing_input:{path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid_json:{path}:{exc.lineno}:{exc.colno}") from exc


def _problems(handoff: dict, target: dict, plan_mode: str) -> list[str]:
    problems: list[str] = []
    send_text_path = Path(str(handoff.get("send_text_path", "")).strip())
    if not send_text_path.is_absolute() or not send_text_path.exists():
        problems.append("missing_send_text_path")
    if target.get("thread_class") != handoff.get("thread_class"):
        problems.append("thread_class_mismatch")
    if target.get("target_status") != "READY":
        problems.append("launch_target_not_ready")
    launch_route = str(target.get("launch_route", "")).strip()
    if not launch_route or launch_route in BLOCKED_LAUNCH_ROUTES:
        problems.append("missing_launch_route")
    if plan_mode not in ALLOWED_PLAN_MODES:
        problems.append("invalid_plan_mode")
    return problems


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Build one Playwright launch plan for a fresh Codex thread launch handoff."
    )
    parser.add_argument("--launch-handoff-json", required=True)
    parser.add_argument("--launch-target-json", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--session", default="codex-thread-launch")
    parser.add_argument("--plan-mode", choices=sorted(ALLOWED_PLAN_MODES), default="validate_only")
    args = parser.parse_args(argv)

    handoff_path = Path(args.launch_handoff_json)
    target_path = Path(args.launch_target_json)
    out_path = Path(args.out_json)
    if not handoff_path.is_absolute():
        raise SystemExit("non_absolute_launch_handoff_json")
    if not target_path.is_absolute():
        raise SystemExit("non_absolute_launch_target_json")
    if not out_path.is_absolute():
        raise SystemExit("non_absolute_out_json")

    handoff = _load_json(handoff_path)
    target = _load_json(target_path)
    handoff_validation = validate_handoff(handoff)
    target_validation = validate_target(target)
    problems = list(handoff_validation.get("errors", []))
    problems.extend(target_validation.get("errors", []))
    problems.extend(_problems(handoff, target, args.plan_mode))

    if problems:
        plan = {
            "schema": "CODEX_THREAD_LAUNCH_PLAYWRIGHT_PLAN_v1",
            "plan_status": "BLOCKED",
            "detail": ",".join(dict.fromkeys(problems)),
            "thread_class": handoff.get("thread_class", ""),
            "role_label": handoff.get("role_label", ""),
            "role_type": handoff.get("role_type", ""),
            "launch_route": target.get("launch_route", ""),
            "launch_target_json": str(target_path),
            "visible_verification_text": target.get("visible_verification_text", ""),
            "send_text_path": handoff.get("send_text_path", ""),
            "session": args.session,
            "plan_mode": args.plan_mode,
            "commands": [],
            "source_launch_handoff": str(handoff_path),
        }
    else:
        commands = [
            [PWCLI, "--session", args.session, "open", target["launch_route"], "--headed"],
            [PWCLI, "--session", args.session, "snapshot"],
        ]
        if args.plan_mode == "real_send_once":
            commands.extend(
                [
                    ["TYPE_SEND_TEXT_FROM_FILE", handoff["send_text_path"]],
                    [PWCLI, "--session", args.session, "press", "Enter"],
                    [PWCLI, "--session", args.session, "snapshot"],
                ]
            )
        plan = {
            "schema": "CODEX_THREAD_LAUNCH_PLAYWRIGHT_PLAN_v1",
            "plan_status": "READY",
            "detail": "playwright_launch_plan_ready" if args.plan_mode == "validate_only" else "playwright_real_launch_plan_ready",
            "thread_class": handoff.get("thread_class", ""),
            "role_label": handoff.get("role_label", ""),
            "role_type": handoff.get("role_type", ""),
            "launch_route": target["launch_route"],
            "launch_target_json": str(target_path),
            "visible_verification_text": target.get("visible_verification_text", ""),
            "send_text_path": handoff.get("send_text_path", ""),
            "session": args.session,
            "plan_mode": args.plan_mode,
            "commands": commands,
            "source_launch_handoff": str(handoff_path),
        }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(plan, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
