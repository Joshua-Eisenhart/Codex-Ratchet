#!/usr/bin/env python3
from __future__ import annotations

import argparse
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


def build_send_text(packet: dict) -> str:
    reload_artifacts = list(packet.get("a1_reload_artifacts", []))
    lines = [
        "Use Ratchet A2/A1.",
        "",
        "You are an A1 Codex thread.",
        "",
        "Read first:",
        f"- {packet['required_a1_boot']}",
        "",
        "Launch packet:",
        f"MODEL: {packet['model']}",
        f"THREAD_CLASS: {packet['thread_class']}",
        f"MODE: {packet['mode']}",
        f"A1_QUEUE_STATUS: {packet['queue_status']}",
        f"dispatch_id: {packet['dispatch_id']}",
        f"target_a1_role: {packet['target_a1_role']}",
        f"required_a1_boot: {packet['required_a1_boot']}",
    ]
    if reload_artifacts:
        lines.extend(
            [
                "a1_reload_artifacts:",
                *(f"- {path}" for path in reload_artifacts),
            ]
        )
    lines.append("source_a2_artifacts:")
    for path in packet["source_a2_artifacts"]:
        lines.append(f"- {path}")
    lines.extend(
        [
            f"bounded_scope: {packet['bounded_scope']}",
            f"stop_rule: {packet['stop_rule']}",
            f"go_on_count: {packet['go_on_count']}",
            f"go_on_budget: {packet['go_on_budget']}",
            "",
            "Prompt to execute:",
            packet["prompt_to_send"],
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Build operator-ready A1 worker send text from one validated launch packet."
    )
    parser.add_argument("--packet-json", required=True)
    parser.add_argument("--out-text", required=True)
    args = parser.parse_args(argv)

    packet_path = Path(args.packet_json)
    out_path = Path(args.out_text)
    if not packet_path.is_absolute():
        raise SystemExit("non_absolute_packet_json")
    if not out_path.is_absolute():
        raise SystemExit("non_absolute_out_text")

    packet = _load_json(packet_path)
    validation_result = validate_packet(packet)
    gate_result = build_gate_result(packet, validation_result)
    if gate_result.get("status") != "LAUNCH_READY":
        raise SystemExit(f"packet_not_launch_ready:{gate_result.get('status','UNKNOWN')}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(build_send_text(packet), encoding="utf-8")
    print(
        json.dumps(
            {
                "schema": "A1_WORKER_SEND_TEXT_RESULT_v1",
                "packet_json": str(packet_path),
                "out_text": str(out_path),
                "status": "CREATED",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
