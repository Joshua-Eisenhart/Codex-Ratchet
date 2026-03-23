#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from validate_a2_worker_launch_packet import validate as validate_packet


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"missing_input:{path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid_json:{path}:{exc.lineno}:{exc.colno}") from exc


def build_result(packet: dict, validation_result: dict) -> dict:
    is_valid = bool(validation_result.get("valid"))
    go_on_count = packet.get("go_on_count", 0)
    go_on_budget = packet.get("go_on_budget", 0)

    if not is_valid:
        status = "FAIL_CLOSED"
    elif go_on_count >= go_on_budget:
        status = "STOP_RELOAD_REQUIRED"
    else:
        status = "LAUNCH_READY"

    return {
        "schema": "A2_WORKER_LAUNCH_GATE_RESULT_v1",
        "status": status,
        "valid": is_valid,
        "errors": list(validation_result.get("errors", [])),
        "model": packet.get("model", ""),
        "thread_class": packet.get("thread_class", ""),
        "mode": packet.get("mode", ""),
        "dispatch_id": packet.get("dispatch_id", ""),
        "role_label": packet.get("role_label", ""),
        "role_type": packet.get("role_type", ""),
        "role_scope": packet.get("role_scope", ""),
        "required_a2_boot": packet.get("required_a2_boot", ""),
        "source_artifacts": list(packet.get("source_artifacts", [])),
        "bounded_scope": packet.get("bounded_scope", ""),
        "prompt_to_send": packet.get("prompt_to_send", ""),
        "stop_rule": packet.get("stop_rule", ""),
        "go_on_count": go_on_count,
        "go_on_budget": go_on_budget,
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Run the fail-closed A2 worker launch gate from one A2 worker launch packet."
    )
    parser.add_argument("--packet-json", required=True)
    parser.add_argument("--out-json", required=True)
    args = parser.parse_args(argv)

    packet_path = Path(args.packet_json)
    out_path = Path(args.out_json)
    if not packet_path.is_absolute():
        raise SystemExit("non_absolute_packet_json")
    if not out_path.is_absolute():
        raise SystemExit("non_absolute_out_json")

    packet = _load_json(packet_path)
    validation_result = validate_packet(packet)
    result = build_result(packet, validation_result)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "LAUNCH_READY" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
