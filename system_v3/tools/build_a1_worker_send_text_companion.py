#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from build_a1_worker_send_text_from_packet import build_send_text
from run_a1_worker_launch_from_packet import build_result as build_gate_result
from validate_a1_worker_launch_packet import validate as validate_packet


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
    read_paths = [
        str(packet["required_a1_boot"]),
        *list(packet.get("a1_reload_artifacts", [])),
        *list(packet["source_a2_artifacts"]),
    ]
    return {
        "schema": "A1_WORKER_SEND_TEXT_COMPANION_v1",
        "source_packet_json": str(packet_path),
        "send_text_path": str(send_text_path),
        "send_text_sha256": _sha256_file(send_text_path),
        "model": packet["model"],
        "thread_class": packet["thread_class"],
        "mode": packet["mode"],
        "queue_status": packet["queue_status"],
        "dispatch_id": packet["dispatch_id"],
        "target_a1_role": packet["target_a1_role"],
        "required_a1_boot": packet["required_a1_boot"],
        "a1_reload_artifacts": list(packet.get("a1_reload_artifacts", [])),
        "source_a2_artifacts": list(packet["source_a2_artifacts"]),
        "bounded_scope": packet["bounded_scope"],
        "stop_rule": packet["stop_rule"],
        "go_on_count": packet["go_on_count"],
        "go_on_budget": packet["go_on_budget"],
        "read_paths": read_paths,
        "read_path_count": len(read_paths),
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Build one derived A1 worker send-text companion object from the launch packet and send text.")
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
