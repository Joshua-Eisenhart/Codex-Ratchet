#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from run_auto_go_on_cycle import main as run_cycle_main


def _load_packet(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"missing_packet:{path}")
    try:
        packet = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid_json:{path}:{exc.lineno}:{exc.colno}") from exc
    if packet.get("schema") != "AUTO_GO_ON_CYCLE_PACKET_v1":
        raise SystemExit("invalid_schema")
    return packet


def _require_absolute(path_value: str, field: str) -> None:
    if not path_value or not Path(path_value).is_absolute():
        raise SystemExit(f"non_absolute_path:{field}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Run one full auto-go-on cycle from an AUTO_GO_ON_CYCLE_PACKET_v1 packet."
    )
    parser.add_argument("--packet-json", required=True, help="Path to one AUTO_GO_ON_CYCLE_PACKET_v1 JSON file.")
    args = parser.parse_args(argv)

    packet = _load_packet(Path(args.packet_json))

    for field in ("reply_text", "boot_surface", "source_decision_record", "out_dir"):
        _require_absolute(packet.get(field, ""), field)

    cycle_args = [
        "--reply-text",
        packet["reply_text"],
        "--target-thread-id",
        packet["target_thread_id"],
        "--thread-class",
        packet["thread_class"],
        "--boot-surface",
        packet["boot_surface"],
        "--source-decision-record",
        packet["source_decision_record"],
        "--expected-return-shape",
        packet["expected_return_shape"],
        "--out-dir",
        packet["out_dir"],
    ]

    if packet.get("fallback_role"):
        cycle_args.extend(["--fallback-role", packet["fallback_role"]])
    if packet.get("fallback_scope"):
        cycle_args.extend(["--fallback-scope", packet["fallback_scope"]])
    cycle_args.extend(["--continuation-count", str(packet.get("continuation_count", 0))])

    return run_cycle_main(cycle_args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
