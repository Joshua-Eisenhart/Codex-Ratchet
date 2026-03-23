#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from a1_queue_surface_models import A1QueueCandidateRegistry, A1QueueStatusPacket


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Emit local Pydantic schemas for A1 queue surfaces.")
    parser.add_argument("--registry-schema-out", required=True)
    parser.add_argument("--queue-packet-schema-out", required=True)
    args = parser.parse_args(argv)

    registry_out = Path(args.registry_schema_out)
    packet_out = Path(args.queue_packet_schema_out)
    if not registry_out.is_absolute():
        raise SystemExit("non_absolute_registry_schema_out")
    if not packet_out.is_absolute():
        raise SystemExit("non_absolute_queue_packet_schema_out")

    _write_json(registry_out, A1QueueCandidateRegistry.model_json_schema())
    _write_json(packet_out, A1QueueStatusPacket.model_json_schema())

    payload = {
        "schema": "A1_QUEUE_SURFACE_PYDANTIC_SCHEMA_EMIT_RESULT_v1",
        "registry_schema_out": str(registry_out),
        "queue_packet_schema_out": str(packet_out),
        "status": "CREATED",
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
