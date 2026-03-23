#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from run_a2_worker_launch_from_packet import build_result as build_gate_result
from validate_a2_worker_launch_packet import validate as validate_packet


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"missing_input:{path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid_json:{path}:{exc.lineno}:{exc.colno}") from exc


def build_send_text(packet: dict) -> str:
    lines = [
        "Use Ratchet A2/A1.",
        "",
        "You are an A2 Codex worker thread.",
        "",
        "Read first:",
        f"- {packet['required_a2_boot']}",
        "",
        "Launch packet:",
        f"MODEL: {packet['model']}",
        f"THREAD_CLASS: {packet['thread_class']}",
        f"MODE: {packet['mode']}",
        f"dispatch_id: {packet['dispatch_id']}",
        f"ROLE_LABEL: {packet['role_label']}",
        f"ROLE_TYPE: {packet['role_type']}",
        f"ROLE_SCOPE: {packet['role_scope']}",
        f"required_a2_boot: {packet['required_a2_boot']}",
        "source_artifacts:",
    ]
    for path in packet["source_artifacts"]:
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
        description="Build operator-ready A2 worker send text from one validated launch packet."
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
                "schema": "A2_WORKER_SEND_TEXT_RESULT_v1",
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
