#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import networkx as nx

from a1_queue_surface_models import load_queue_candidate_registry, load_queue_status_packet


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Export A1 queue registry or queue-status packet as GraphML through the local spec-object stack.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--registry-json")
    group.add_argument("--packet-json")
    parser.add_argument("--out-graphml", required=True)
    args = parser.parse_args(argv)

    out_path = Path(args.out_graphml)
    if not out_path.is_absolute():
        raise SystemExit("non_absolute_out_graphml")

    if args.registry_json:
        model = load_queue_candidate_registry(Path(args.registry_json))
        graph = model.to_graph()
        surface_kind = "candidate_registry"
    else:
        model = load_queue_status_packet(Path(args.packet_json))
        graph = model.to_graph()
        surface_kind = "queue_status_packet"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    nx.write_graphml(graph, out_path)
    payload = {
        "schema": "A1_QUEUE_SURFACE_GRAPH_EXPORT_RESULT_v1",
        "surface_kind": surface_kind,
        "out_graphml": str(out_path),
        "node_count": graph.number_of_nodes(),
        "edge_count": graph.number_of_edges(),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
