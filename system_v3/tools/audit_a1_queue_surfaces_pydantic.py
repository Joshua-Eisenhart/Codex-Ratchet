#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from a1_queue_surface_models import load_queue_candidate_registry, load_queue_status_packet


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Audit A1 queue registry or queue-status packet through the local Pydantic stack.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--registry-json")
    group.add_argument("--packet-json")
    args = parser.parse_args(argv)

    if args.registry_json:
        model = load_queue_candidate_registry(Path(args.registry_json))
        payload = {
            "schema": "A1_QUEUE_SURFACE_PYDANTIC_AUDIT_RESULT_v1",
            "surface_kind": "candidate_registry",
            "candidate_count": len(model.candidate_family_slice_jsons),
            "has_selected_family_slice": bool(model.selected_family_slice_json),
            "graph": {
                "node_count": model.to_graph().number_of_nodes(),
                "edge_count": model.to_graph().number_of_edges(),
            },
        }
    else:
        model = load_queue_status_packet(Path(args.packet_json))
        payload = {
            "schema": "A1_QUEUE_SURFACE_PYDANTIC_AUDIT_RESULT_v1",
            "surface_kind": "queue_status_packet",
            "queue_status": model.queue_status,
            "has_ready_surface": bool(model.ready_packet_json),
            "has_ready_send_text_companion": bool(model.ready_send_text_companion_json),
            "has_ready_launch_spine": bool(model.ready_launch_spine_json),
            "ready_artifact_integrity_verified": model.queue_status.startswith("READY_FROM_"),
            "graph": {
                "node_count": model.to_graph().number_of_nodes(),
                "edge_count": model.to_graph().number_of_edges(),
            },
        }

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
