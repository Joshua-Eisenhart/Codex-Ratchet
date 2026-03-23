#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import networkx as nx

SUBSET_ROOT = "first_controller_a1_launch_subset"
EXPECTED_COMPILED_FROM_COUNT = 9
EXPECTED_ARTIFACT_BRIDGE_COUNT = 43
EXPECTED_QUEUE_STATUS_BRIDGE_COUNT = 5


def _count_relation(graph: nx.DiGraph, relation: str) -> int:
    return sum(1 for _, _, attrs in graph.edges(data=True) if attrs.get("relation") == relation)


def _graph_count_attr(graph: nx.DiGraph) -> int:
    raw = graph.nodes[SUBSET_ROOT].get("graph_count", 0)
    return int(str(raw))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit one compiled first controller/A1 launch subset GraphML for fixed roots and bridge counts."
    )
    parser.add_argument("--graphml", required=True)
    args = parser.parse_args()

    graph_path = Path(args.graphml)
    graph = nx.read_graphml(graph_path)

    if SUBSET_ROOT not in graph:
        raise SystemExit(f"missing_subset_root:{SUBSET_ROOT}")

    if _graph_count_attr(graph) != EXPECTED_COMPILED_FROM_COUNT:
        raise SystemExit(
            f"unexpected_graph_count:{_graph_count_attr(graph)}!= {EXPECTED_COMPILED_FROM_COUNT}"
        )

    compiled_from_count = _count_relation(graph, "compiled_from")
    if compiled_from_count != EXPECTED_COMPILED_FROM_COUNT:
        raise SystemExit(
            f"unexpected_compiled_from_count:{compiled_from_count}!={EXPECTED_COMPILED_FROM_COUNT}"
        )

    artifact_bridge_count = _count_relation(graph, "references_artifact")
    if artifact_bridge_count != EXPECTED_ARTIFACT_BRIDGE_COUNT:
        raise SystemExit(
            f"unexpected_artifact_bridge_count:{artifact_bridge_count}!={EXPECTED_ARTIFACT_BRIDGE_COUNT}"
        )

    queue_status_bridge_count = _count_relation(graph, "normalizes_queue_status")
    if queue_status_bridge_count != EXPECTED_QUEUE_STATUS_BRIDGE_COUNT:
        raise SystemExit(
            "unexpected_queue_status_bridge_count:"
            f"{queue_status_bridge_count}!={EXPECTED_QUEUE_STATUS_BRIDGE_COUNT}"
        )

    payload = {
        "schema": "FIRST_CONTROLLER_A1_LAUNCH_SUBSET_GRAPH_AUDIT_RESULT_v1",
        "graphml": str(graph_path),
        "subset_root": SUBSET_ROOT,
        "graph_count": _graph_count_attr(graph),
        "compiled_from_count": compiled_from_count,
        "artifact_bridge_count": artifact_bridge_count,
        "queue_status_bridge_count": queue_status_bridge_count,
        "node_count": graph.number_of_nodes(),
        "edge_count": graph.number_of_edges(),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
