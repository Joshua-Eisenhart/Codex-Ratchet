#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from build_a2_controller_send_text_from_packet import ACTIVE_CONTEXT_SURFACES, GOVERNING_SURFACES, build_send_text
from run_a2_controller_launch_from_packet import build_result as build_gate_result
from validate_a2_controller_launch_packet import validate as validate_packet


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"missing_input:{path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid_json:{path}:{exc.lineno}:{exc.colno}") from exc


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _require_abs_existing(path_str: str, field: str) -> Path:
    path = Path(path_str)
    if not path.is_absolute():
        raise SystemExit(f"non_absolute_{field}")
    if not path.exists():
        raise SystemExit(f"missing_path_{field}:{path}")
    return path


def build_companion(packet_path: Path, packet: dict, send_text_path: Path) -> dict:
    return {
        "schema": "A2_CONTROLLER_SEND_TEXT_COMPANION_v1",
        "source_packet_json": str(packet_path),
        "send_text_path": str(send_text_path),
        "send_text_sha256": _sha256_file(send_text_path),
        "model": packet["model"],
        "thread_class": packet["thread_class"],
        "mode": packet["mode"],
        "primary_corpus": packet["primary_corpus"],
        "state_record": packet["state_record"],
        "current_primary_lane": packet["current_primary_lane"],
        "current_a1_queue_status": packet["current_a1_queue_status"],
        "go_on_count": packet["go_on_count"],
        "go_on_budget": packet["go_on_budget"],
        "stop_rule": packet["stop_rule"],
        "dispatch_rule": packet["dispatch_rule"],
        "initial_bounded_scope": packet["initial_bounded_scope"],
        "governing_surfaces": list(GOVERNING_SURFACES),
        "active_context_surfaces": list(ACTIVE_CONTEXT_SURFACES),
        "read_paths": list(GOVERNING_SURFACES) + [packet["state_record"]] + list(ACTIVE_CONTEXT_SURFACES),
        "queue_helper_mode": "a1_queue_helper_auto" if "a1? queue answer" in str(packet.get("initial_bounded_scope", "")) else "none",
        "required_closeout_fields": [
            "current phase",
            "what was read/updated",
            "whether to stay on Medium or switch models",
            "exactly how many more go on prompts I should queue",
            "what the next go on will do",
        ],
        "first_task_requirements": [
            "refresh weighted controller state from the files above",
            "strongest active lane",
            "second strongest active lane",
            "weakest active lane",
            "highest-value bounded controller action",
            "do not assume prior chat history",
        ],
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Build one derived A2 controller send-text companion object from the current packet and send text.")
    parser.add_argument("--packet-json", required=True)
    parser.add_argument("--send-text", required=True)
    parser.add_argument("--out-json", required=True)
    args = parser.parse_args(argv)

    packet_path = _require_abs_existing(args.packet_json, "packet_json")
    send_text_path = _require_abs_existing(args.send_text, "send_text")
    out_path = Path(args.out_json)
    if not out_path.is_absolute():
        raise SystemExit("non_absolute_out_json")

    packet = _load_json(packet_path)
    validation_result = validate_packet(packet)
    gate_result = build_gate_result(packet, validation_result)
    if gate_result.get("status") != "LAUNCH_READY":
        raise SystemExit(f"packet_not_launch_ready:{gate_result.get('status','UNKNOWN')}")

    expected_text = build_send_text(packet)
    actual_text = send_text_path.read_text(encoding="utf-8")
    if actual_text != expected_text:
        raise SystemExit("send_text_content_mismatch")

    companion = build_companion(packet_path, packet, send_text_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(companion, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(companion, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
