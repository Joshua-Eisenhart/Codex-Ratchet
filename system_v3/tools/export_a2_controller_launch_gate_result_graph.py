#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import networkx as nx

from a2_controller_launch_gate_result_models import load_a2_controller_launch_gate_result


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Export one A2 controller launch gate result as GraphML through the local spec-object stack.")
    parser.add_argument("--gate-result-json", required=True)
    parser.add_argument("--out-graphml", required=True)
    args = parser.parse_args(argv)

    out_path = Path(args.out_graphml)
    if not out_path.is_absolute():
        raise SystemExit("non_absolute_out_graphml")

    result = load_a2_controller_launch_gate_result(Path(args.gate_result_json))
    graph = result.to_graph()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    nx.write_graphml(graph, out_path)
    payload = {
        "schema": "A2_CONTROLLER_LAUNCH_GATE_RESULT_GRAPH_EXPORT_RESULT_v1",
        "out_graphml": str(out_path),
        "node_count": graph.number_of_nodes(),
        "edge_count": graph.number_of_edges(),
        "status": "CREATED",
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
