#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from run_a2_controller_launch_from_packet import build_result as build_gate_result
from validate_a2_controller_launch_packet import validate as validate_packet


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"missing_input:{path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid_json:{path}:{exc.lineno}:{exc.colno}") from exc


def _require_abs_existing(path_str: str, field: str) -> str:
    path = Path(path_str)
    if not path.is_absolute():
        raise SystemExit(f"non_absolute_{field}")
    if not path.exists():
        raise SystemExit(f"missing_path_{field}:{path}")
    return str(path)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_handoff(packet_path: Path, packet: dict, send_text_path: Path) -> dict:
    return {
        "schema": "A2_CONTROLLER_LAUNCH_HANDOFF_v1",
        "source_packet_json": str(packet_path),
        "thread_class": packet["thread_class"],
        "role_label": "C0",
        "role_type": "A2_CONTROLLER",
        "role_scope": packet["initial_bounded_scope"],
        "model": packet["model"],
        "mode": packet["mode"],
        "primary_corpus": packet["primary_corpus"],
        "state_record": packet["state_record"],
        "current_primary_lane": packet["current_primary_lane"],
        "current_a1_queue_status": packet["current_a1_queue_status"],
        "stop_rule": packet["stop_rule"],
        "dispatch_rule": packet["dispatch_rule"],
        "send_text_path": str(send_text_path),
        "send_text_sha256": _sha256_file(send_text_path),
        "operator_steps": [
            "Open one fresh Codex thread for C0.",
            f"Set model to {packet['model']}.",
            f"Paste the full send text from {send_text_path}.",
            "Send it once.",
            "Do not queue repeated plain go ons.",
            "After one bounded controller result, stop and relaunch or dispatch as directed.",
        ],
        "monitor_route": {
            "mode": "direct_controller_result_read",
            "owner_surface": "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/27_MASTER_CONTROLLER_THREAD_PROCESS__v1.md",
            "next_reader": "current operator or replacement controller",
        },
        "closeout_route": {
            "mode": "manual_controller_stop",
            "state_refresh_target": "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_CONTROLLER_STATE_RECORD__CURRENT__v1.md",
            "execution_log_target": "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/CURRENT_EXECUTION_STATE__2026_03_10__v1.md",
        },
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Build one operator-ready A2 controller launch handoff packet."
    )
    parser.add_argument("--packet-json", required=True)
    parser.add_argument("--send-text", required=True)
    parser.add_argument("--out-json", required=True)
    args = parser.parse_args(argv)

    packet_path = Path(args.packet_json)
    send_text_path = Path(args.send_text)
    out_path = Path(args.out_json)
    if not packet_path.is_absolute():
        raise SystemExit("non_absolute_packet_json")
    if not out_path.is_absolute():
        raise SystemExit("non_absolute_out_json")
    _require_abs_existing(str(send_text_path), "send_text")

    packet = _load_json(packet_path)
    validation_result = validate_packet(packet)
    gate_result = build_gate_result(packet, validation_result)
    if gate_result.get("status") != "LAUNCH_READY":
        raise SystemExit(f"packet_not_launch_ready:{gate_result.get('status','UNKNOWN')}")

    handoff = build_handoff(packet_path, packet, send_text_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(handoff, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(handoff, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
