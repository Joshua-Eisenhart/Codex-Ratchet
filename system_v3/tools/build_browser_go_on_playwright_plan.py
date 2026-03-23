#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PWCLI = "/Users/joshuaeisenhart/.codex/skills/playwright/scripts/playwright_cli.sh"
ALLOWED_MESSAGE = "go on"
ALLOWED_THREAD_CLASS = {"A2_WORKER", "A1_WORKER"}
ALLOWED_PLATFORM = "CODEX_DESKTOP"
ALLOWED_PLAN_MODES = {"validate_only", "real_send_once"}


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"missing_input:{path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid_json:{path}:{exc.lineno}:{exc.colno}") from exc


def _validate(sender: dict, target: dict) -> list[str]:
    problems: list[str] = []
    if sender.get("message_to_send") != ALLOWED_MESSAGE:
        problems.append("blocked_message")
    if sender.get("thread_class") not in ALLOWED_THREAD_CLASS:
        problems.append("blocked_sender_thread_class")
    if target.get("thread_class") not in ALLOWED_THREAD_CLASS:
        problems.append("blocked_target_thread_class")
    if target.get("thread_platform") != ALLOWED_PLATFORM:
        problems.append("blocked_thread_platform")
    if target.get("target_status") != "READY":
        problems.append("target_not_ready")
    if sender.get("target_thread_id") != target.get("target_thread_id"):
        problems.append("thread_id_mismatch")
    if sender.get("thread_class") != target.get("thread_class"):
        problems.append("thread_class_mismatch")
    return problems


def _validate_prior_proof_packet(proof: dict, sender: dict, target: dict) -> list[str]:
    problems: list[str] = []
    required = [
        "target_thread_id",
        "thread_class",
        "execution_path",
        "send_status",
        "message_sent",
        "detail",
        "continuation_count",
    ]
    for key in required:
        value = proof.get(key)
        if value is None:
            problems.append(f"missing_prior_proof_{key}")
            continue
        if isinstance(value, str) and not value.strip():
            problems.append(f"missing_prior_proof_{key}")

    if proof.get("execution_path") != "PATH_BROWSER_AUTOMATED":
        problems.append("invalid_prior_proof_execution_path")
    if proof.get("send_status") != "SEND_BLOCKED":
        problems.append("prior_proof_not_validate_blocked")
    if proof.get("detail") != "browser_send_not_attempted_validate_only":
        problems.append("prior_proof_not_validate_only")
    if proof.get("message_sent") != "NONE":
        problems.append("prior_proof_message_not_none")
    if proof.get("target_thread_id") != sender.get("target_thread_id"):
        problems.append("prior_proof_thread_id_mismatch")
    if proof.get("thread_class") != sender.get("thread_class"):
        problems.append("prior_proof_thread_class_mismatch")
    if proof.get("continuation_count") != sender.get("continuation_count"):
        problems.append("prior_proof_continuation_count_mismatch")

    visible_verification_text = target.get("visible_verification_text", "")
    if not isinstance(visible_verification_text, str) or not visible_verification_text.strip():
        problems.append("missing_visible_verification_text")

    composer_hint = target.get("composer_ready_hint")
    if composer_hint != "COMPOSER_READY_OBSERVED":
        problems.append("composer_not_observed_ready")

    return problems


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Emit one bounded Playwright execution plan from sender + target go-on packets."
    )
    parser.add_argument("--sender-packet-json", required=True)
    parser.add_argument("--target-packet-json", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--session", default="codex-go-on")
    parser.add_argument("--proof-json", default="NONE")
    parser.add_argument("--prior-proof-json")
    parser.add_argument("--plan-mode", choices=sorted(ALLOWED_PLAN_MODES), default="validate_only")
    args = parser.parse_args(argv)

    sender_path = Path(args.sender_packet_json)
    target_path = Path(args.target_packet_json)
    out_path = Path(args.out_json)

    sender = _load_json(sender_path)
    target = _load_json(target_path)
    prior_proof = _load_json(Path(args.prior_proof_json)) if args.prior_proof_json else None
    problems = _validate(sender, target)

    route = target.get("thread_url_or_route", "NONE")
    if route == "NONE":
        problems.append("missing_thread_route")

    if args.plan_mode == "real_send_once":
        if prior_proof is None:
            problems.append("missing_prior_validate_only_proof")
        else:
            problems.extend(_validate_prior_proof_packet(prior_proof, sender, target))

    if problems:
        plan = {
            "schema": "BROWSER_GO_ON_PLAYWRIGHT_PLAN_v1",
            "plan_status": "BLOCKED",
            "detail": ",".join(dict.fromkeys(problems)),
            "target_thread_id": sender.get("target_thread_id", ""),
            "thread_class": sender.get("thread_class", ""),
            "session": args.session,
            "route": route,
            "verification_text": target.get("visible_verification_text", ""),
            "message_to_send": sender.get("message_to_send", ""),
            "proof_json": args.proof_json,
            "prior_proof_json": args.prior_proof_json or "NONE",
            "plan_mode": args.plan_mode,
            "stop_condition": sender.get("stop_condition", ""),
            "commands": [],
            "source_sender_packet": str(sender_path),
            "source_target_packet": str(target_path),
        }
    else:
        commands = [
            [PWCLI, "--session", args.session, "open", route, "--headed"],
            [PWCLI, "--session", args.session, "snapshot"],
        ]
        if args.plan_mode == "real_send_once":
            commands.extend(
                [
                    [PWCLI, "--session", args.session, "snapshot"],
                    ["SEND_STEP_PLACEHOLDER", "go on"],
                ]
            )
        plan = {
            "schema": "BROWSER_GO_ON_PLAYWRIGHT_PLAN_v1",
            "plan_status": "READY",
            "detail": "playwright_plan_ready" if args.plan_mode == "validate_only" else "playwright_real_send_plan_ready",
            "target_thread_id": sender.get("target_thread_id", ""),
            "thread_class": sender.get("thread_class", ""),
            "session": args.session,
            "route": route,
            "verification_text": target.get("visible_verification_text", ""),
            "message_to_send": sender.get("message_to_send", ""),
            "proof_json": args.proof_json,
            "prior_proof_json": args.prior_proof_json or "NONE",
            "plan_mode": args.plan_mode,
            "stop_condition": sender.get("stop_condition", ""),
            "commands": commands,
            "source_sender_packet": str(sender_path),
            "source_target_packet": str(target_path),
        }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(plan, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
