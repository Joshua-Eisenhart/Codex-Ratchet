#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from run_a1_worker_launch_from_packet import build_result as build_gate_result
from validate_a1_worker_launch_packet import validate as validate_packet


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


def _default_return_text_path(dispatch_id: str, role: str) -> str:
    return f"/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/thread_launch_returns/{dispatch_id}__{role}__return.txt"


def _default_closeout_text_path(dispatch_id: str, role: str) -> str:
    return f"/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/thread_closeout_packets/{dispatch_id}__{role}.txt"


def _default_closeout_json_path(dispatch_id: str, role: str) -> str:
    return f"/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/thread_closeout_packets/{dispatch_id}__{role}.json"


def build_handoff(packet_path: Path, packet: dict, send_text_path: Path) -> dict:
    dispatch_id = packet["dispatch_id"]
    role = packet["target_a1_role"]
    return_text_path = _default_return_text_path(dispatch_id, role)
    closeout_text_path = _default_closeout_text_path(dispatch_id, role)
    closeout_json_path = _default_closeout_json_path(dispatch_id, role)
    return {
        "schema": "A1_WORKER_LAUNCH_HANDOFF_v1",
        "source_packet_json": str(packet_path),
        "thread_class": packet["thread_class"],
        "role_label": dispatch_id,
        "role_type": role,
        "role_scope": packet["bounded_scope"],
        "model": packet["model"],
        "mode": packet["mode"],
        "queue_status": packet["queue_status"],
        "dispatch_id": dispatch_id,
        "required_a1_boot": packet["required_a1_boot"],
        "a1_reload_artifacts": list(packet.get("a1_reload_artifacts", [])),
        "source_a2_artifacts": packet["source_a2_artifacts"],
        "stop_rule": packet["stop_rule"],
        "send_text_path": str(send_text_path),
        "send_text_sha256": _sha256_file(send_text_path),
        "return_capture_path": return_text_path,
        "operator_steps": [
            "Open one fresh Codex thread.",
            f"Set model to {packet['model']}.",
            f"Paste the full send text from {send_text_path}.",
            "Send it once.",
            f"Save the bounded return to {return_text_path}.",
            "If the lane runs long or drifts, route it through the monitor and closeout path below instead of free chaining.",
        ],
        "monitor_route": {
            "skill": "/Users/joshuaeisenhart/.codex/skills/thread-run-monitor/SKILL.md",
            "owner_surface": "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/THREAD_RUN_DIAGNOSIS_AND_STOP_RULES__v1.md",
            "allowed_decisions": [
                "STOP",
                "CONTINUE_ONE_BOUNDED_STEP",
                "CORRECT_LANE_LATER",
            ],
        },
        "closeout_route": {
            "skill": "/Users/joshuaeisenhart/.codex/skills/thread-closeout-auditor/SKILL.md",
            "closeout_prompt": "/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/zip_subagents/THREAD_CLOSEOUT_AUDIT_PROMPT__v1.md",
            "staging_text_path": closeout_text_path,
            "staging_json_path": closeout_json_path,
            "sink_path": "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_derived_indices_noncanonical/thread_closeout_packets.000.jsonl",
            "extract_command": f"python3 system_v3/tools/extract_thread_closeout_packet.py --reply-text '{closeout_text_path}' --source-thread-label '{dispatch_id}__{role}' --out-json '{closeout_json_path}'",
            "append_command": f"python3 system_v3/tools/append_thread_closeout_packet.py --packet-json '{closeout_json_path}'",
        },
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Build one operator-ready A1 worker launch handoff packet."
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
