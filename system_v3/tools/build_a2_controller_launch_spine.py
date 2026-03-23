#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from build_a2_controller_launch_handoff import build_handoff
from build_a2_controller_send_text_companion import build_companion
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


def build_spine(
    *,
    packet_path: Path,
    packet: dict,
    gate_result_path: Path,
    gate_result: dict,
    companion_path: Path,
    companion: dict,
    handoff_path: Path,
    handoff: dict,
) -> dict:
    validation_result = validate_packet(packet)
    expected_gate_result = build_gate_result(packet, validation_result)
    if gate_result != expected_gate_result:
        raise SystemExit("launch_gate_result_content_mismatch")

    send_text_path = _require_abs_existing(str(companion.get("send_text_path", "")), "send_text_path")
    expected_companion = build_companion(packet_path, packet, send_text_path)
    if companion != expected_companion:
        raise SystemExit("send_text_companion_content_mismatch")

    expected_handoff = build_handoff(packet_path, packet, send_text_path)
    if handoff != expected_handoff:
        raise SystemExit("launch_handoff_content_mismatch")

    return {
        "schema": "A2_CONTROLLER_LAUNCH_SPINE_v1",
        "launch_packet_json": str(packet_path),
        "launch_gate_result_json": str(gate_result_path),
        "send_text_companion_json": str(companion_path),
        "launch_handoff_json": str(handoff_path),
        "launch_packet_sha256": _sha256_file(packet_path),
        "launch_gate_result_sha256": _sha256_file(gate_result_path),
        "send_text_companion_sha256": _sha256_file(companion_path),
        "launch_handoff_sha256": _sha256_file(handoff_path),
        "send_text_path": str(send_text_path),
        "send_text_sha256": str(companion["send_text_sha256"]),
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
        "launch_gate_status": gate_result["status"],
        "launch_gate_valid": gate_result["valid"],
        "allowed_first_actions": list(gate_result["allowed_first_actions"]),
        "queue_helper_mode": companion["queue_helper_mode"],
        "handoff_role_label": handoff["role_label"],
        "handoff_role_type": handoff["role_type"],
        "handoff_role_scope": handoff["role_scope"],
        "monitor_mode": handoff["monitor_route"]["mode"],
        "closeout_mode": handoff["closeout_route"]["mode"],
        "read_path_count": len(companion["read_paths"]),
        "operator_step_count": len(handoff["operator_steps"]),
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Build one derived A2 controller launch spine object from the current packet, gate result, send-text companion, and handoff."
    )
    parser.add_argument("--packet-json", required=True)
    parser.add_argument("--gate-result-json", required=True)
    parser.add_argument("--send-text-companion-json", required=True)
    parser.add_argument("--handoff-json", required=True)
    parser.add_argument("--out-json", required=True)
    args = parser.parse_args(argv)

    packet_path = _require_abs_existing(args.packet_json, "packet_json")
    gate_result_path = _require_abs_existing(args.gate_result_json, "gate_result_json")
    companion_path = _require_abs_existing(args.send_text_companion_json, "send_text_companion_json")
    handoff_path = _require_abs_existing(args.handoff_json, "handoff_json")
    out_path = Path(args.out_json)
    if not out_path.is_absolute():
        raise SystemExit("non_absolute_out_json")

    packet = _load_json(packet_path)
    gate_result = _load_json(gate_result_path)
    companion = _load_json(companion_path)
    handoff = _load_json(handoff_path)

    spine = build_spine(
        packet_path=packet_path,
        packet=packet,
        gate_result_path=gate_result_path,
        gate_result=gate_result,
        companion_path=companion_path,
        companion=companion,
        handoff_path=handoff_path,
        handoff=handoff,
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(spine, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(spine, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
