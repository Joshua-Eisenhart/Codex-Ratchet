#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ALLOWED_THREAD_CLASSES = {"A2_WORKER", "A1_WORKER", "A2_CONTROLLER"}
ALLOWED_A1_ROLES = {"A1_ROSETTA", "A1_PROPOSAL", "A1_PACKAGING"}
ALLOWED_NEXT_STEPS = {"STOP", "ONE_MORE_BOUNDED_PASS_NEEDED"}
RUNNER_OUTPUTS = {
    "STOP_NOW": "RUNNER_OUTPUT__STOP",
    "ROUTE_TO_CLOSEOUT": "RUNNER_OUTPUT__CLOSEOUT",
    "MANUAL_REVIEW_REQUIRED": "RUNNER_OUTPUT__MANUAL_REVIEW",
    "SEND_ONE_GO_ON": "RUNNER_OUTPUT__SENDER_PACKET",
}


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"missing_input:{path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid_json:{path}:{exc.lineno}:{exc.colno}") from exc


def _missing_required(result: dict) -> list[str]:
    required = ["thread_class", "role_and_scope", "what_you_read", "what_you_updated", "next_step"]
    missing: list[str] = []
    for key in required:
        value = result.get(key)
        if value is None:
            missing.append(key)
            continue
        if isinstance(value, str) and not value.strip():
            missing.append(key)
            continue
        if isinstance(value, list) and not value:
            if key == "what_you_updated" and result.get("what_you_updated_is_bounded_no_change") is True:
                continue
            missing.append(key)
            continue
        if isinstance(value, dict) and not value:
            missing.append(key)
    return missing


def _build_sender_packet(result: dict) -> dict:
    next_pass = result.get("if_one_more_pass", {})
    return {
        "schema": "AUTO_GO_ON_SENDER_PACKET_v1",
        "target_thread_id": result["target_thread_id"],
        "thread_class": result["thread_class"],
        "message_to_send": "go on",
        "expected_return_shape": result.get("expected_return_shape", ""),
        "stop_condition": next_pass.get("stop_condition", ""),
        "continuation_count": result.get("continuation_count", 0),
        "source_decision_record": result.get("source_decision_record", ""),
        "boot_surface": result.get("boot_surface", ""),
        "bounded_scope": next_pass.get("next_step", ""),
    }


def _decision(decision: str, reason: str, result: dict) -> dict:
    payload = {
        "schema": "AUTO_GO_ON_RUNNER_OUTPUT_v1",
        "decision": decision,
        "runner_output": RUNNER_OUTPUTS[decision],
        "reason": reason,
        "auto_go_on_allowed": decision == "SEND_ONE_GO_ON",
        "thread_class": result.get("thread_class", ""),
        "continuation_count": result.get("continuation_count", 0),
    }
    if decision == "SEND_ONE_GO_ON":
        payload["sender_packet"] = _build_sender_packet(result)
    return payload


def evaluate(result: dict) -> dict:
    thread_class = result.get("thread_class", "")
    if thread_class not in ALLOWED_THREAD_CLASSES:
        return _decision("MANUAL_REVIEW_REQUIRED", "missing_or_unknown_thread_class", result)

    if thread_class == "A2_CONTROLLER":
        return _decision("MANUAL_REVIEW_REQUIRED", "controller_auto_continue_blocked", result)

    missing = _missing_required(result)
    if missing:
        return _decision("ROUTE_TO_CLOSEOUT", f"missing_required_fields:{','.join(missing)}", result)

    next_step = result.get("next_step", "")
    if next_step not in ALLOWED_NEXT_STEPS:
        return _decision("MANUAL_REVIEW_REQUIRED", "invalid_next_step", result)

    if next_step == "STOP":
        return _decision("STOP_NOW", "thread_returned_stop", result)

    if_one_more = result.get("if_one_more_pass")
    if not isinstance(if_one_more, dict) or not if_one_more:
        return _decision("ROUTE_TO_CLOSEOUT", "missing_if_one_more_pass", result)

    for key in ("next_step", "touches", "stop_condition"):
        value = if_one_more.get(key)
        if key == "touches":
            if not isinstance(value, list) or not value:
                return _decision("ROUTE_TO_CLOSEOUT", "missing_exact_touches", result)
        elif not isinstance(value, str) or not value.strip():
            return _decision("ROUTE_TO_CLOSEOUT", f"missing_{key}", result)

    blocked_flags = result.get("blocked_case_flags", [])
    if blocked_flags:
        return _decision("ROUTE_TO_CLOSEOUT", f"blocked_case:{','.join(blocked_flags)}", result)

    continuation_count = result.get("continuation_count", 0)
    if not isinstance(continuation_count, int):
        return _decision("MANUAL_REVIEW_REQUIRED", "invalid_continuation_count", result)
    if continuation_count >= 1:
        return _decision("MANUAL_REVIEW_REQUIRED", "continuation_ceiling_reached", result)

    if thread_class == "A1_WORKER":
        role_and_scope = result.get("role_and_scope", {})
        role = role_and_scope.get("role", "") if isinstance(role_and_scope, dict) else ""
        if role not in ALLOWED_A1_ROLES:
            return _decision("ROUTE_TO_CLOSEOUT", "a1_role_purity_failed", result)

    sender_required = ["target_thread_id", "source_decision_record", "boot_surface", "expected_return_shape"]
    missing_sender = [key for key in sender_required if not result.get(key)]
    if missing_sender:
        return _decision("MANUAL_REVIEW_REQUIRED", f"missing_sender_fields:{','.join(missing_sender)}", result)

    return _decision("SEND_ONE_GO_ON", "all_auto_go_on_gates_passed", result)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Apply the auto-go-on rule to one normalized thread-result JSON.")
    parser.add_argument("--result-json", required=True, help="Path to one normalized thread-result JSON file.")
    args = parser.parse_args(argv)

    result = _load_json(Path(args.result_json))
    print(json.dumps(evaluate(result), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
