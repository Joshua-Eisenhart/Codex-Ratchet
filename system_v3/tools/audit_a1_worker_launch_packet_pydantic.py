#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from a1_worker_launch_packet_models import load_a1_worker_launch_packet


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit one A1 worker launch packet through the local Pydantic stack.")
    parser.add_argument("--packet-json", required=True)
    args = parser.parse_args()

    packet = load_a1_worker_launch_packet(Path(args.packet_json))
    payload = {
        "schema": packet.schema_name,
        "thread_class": packet.thread_class,
        "mode": packet.mode,
        **packet.graph_summary(),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
