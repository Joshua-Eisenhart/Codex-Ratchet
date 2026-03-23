#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from a2_controller_launch_packet_models import load_a2_controller_launch_packet


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Audit one A2 controller launch packet through the local Pydantic stack.")
    parser.add_argument("--packet-json", required=True)
    args = parser.parse_args(argv)

    packet = load_a2_controller_launch_packet(Path(args.packet_json))
    payload = {
        "schema": "A2_CONTROLLER_LAUNCH_PACKET_PYDANTIC_AUDIT_RESULT_v1",
        "model": packet.model,
        "thread_class": packet.thread_class,
        "mode": packet.mode,
        "queue_status": packet.current_a1_queue_status,
        "graph": packet.graph_summary(),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
