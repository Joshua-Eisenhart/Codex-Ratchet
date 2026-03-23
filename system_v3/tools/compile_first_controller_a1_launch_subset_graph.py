#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import networkx as nx


def _require_abs_existing_path(raw: str, key: str) -> Path:
    path = Path(raw)
    if not path.is_absolute():
        raise SystemExit(f"non_absolute_{key}")
    if not path.exists():
        raise SystemExit(f"missing_{key}:{path}")
    return path


def _queue_status_value(node_data: dict[str, object]) -> str:
    queue_status = str(node_data.get("queue_status", "")).strip()
    if queue_status:
        return queue_status
    label = str(node_data.get("label", "")).strip()
    if label.startswith("A1_QUEUE_STATUS:"):
        return label.split(":", 1)[1].strip()
    return ""


def _compose_with_source_tag(compiled: nx.DiGraph, graph: nx.DiGraph, source_graphml: Path) -> None:
    for node_id, attrs in graph.nodes(data=True):
        merged = dict(attrs)
        merged["source_graphml"] = str(source_graphml)
        if compiled.has_node(node_id):
            compiled.nodes[node_id].update(merged)
        else:
            compiled.add_node(node_id, **merged)
    for source, target, attrs in graph.edges(data=True):
        compiled.add_edge(source, target, **dict(attrs))


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Compile one bounded controller/A1 launch graph subset from existing GraphML surfaces."
    )
    parser.add_argument("--family-slice-graphml", required=True)
    parser.add_argument("--queue-status-graphml", required=True)
    parser.add_argument("--a1-launch-packet-graphml", required=True)
    parser.add_argument("--a1-send-text-companion-graphml", required=True)
    parser.add_argument("--a1-launch-handoff-graphml", required=True)
    parser.add_argument("--a1-launch-spine-graphml", required=True)
    parser.add_argument("--a2-controller-launch-packet-graphml", required=True)
    parser.add_argument("--a2-controller-launch-handoff-graphml", required=True)
    parser.add_argument("--a2-controller-launch-spine-graphml", required=True)
    parser.add_argument("--out-graphml", required=True)
    args = parser.parse_args(argv)

    graph_paths = [
        _require_abs_existing_path(args.family_slice_graphml, "family_slice_graphml"),
        _require_abs_existing_path(args.queue_status_graphml, "queue_status_graphml"),
        _require_abs_existing_path(args.a1_launch_packet_graphml, "a1_launch_packet_graphml"),
        _require_abs_existing_path(args.a1_send_text_companion_graphml, "a1_send_text_companion_graphml"),
        _require_abs_existing_path(args.a1_launch_handoff_graphml, "a1_launch_handoff_graphml"),
        _require_abs_existing_path(args.a1_launch_spine_graphml, "a1_launch_spine_graphml"),
        _require_abs_existing_path(
            args.a2_controller_launch_packet_graphml, "a2_controller_launch_packet_graphml"
        ),
        _require_abs_existing_path(
            args.a2_controller_launch_handoff_graphml, "a2_controller_launch_handoff_graphml"
        ),
        _require_abs_existing_path(args.a2_controller_launch_spine_graphml, "a2_controller_launch_spine_graphml"),
    ]
    out_graphml = Path(args.out_graphml)
    if not out_graphml.is_absolute():
        raise SystemExit("non_absolute_out_graphml")

    compiled = nx.DiGraph()
    subset_root = "first_controller_a1_launch_subset"
    compiled.add_node(
        subset_root,
        kind="compiled_graph_subset",
        subset_kind="first_controller_a1_launch_subset",
        graph_count=len(graph_paths),
    )

    artifact_bridge_count = 0
    queue_status_bridge_count = 0

    for graph_path in graph_paths:
        graph = nx.read_graphml(graph_path)
        _compose_with_source_tag(compiled, graph, graph_path)
        source_node = f"graphml:{graph_path}"
        compiled.add_node(source_node, kind="source_graphml", path=str(graph_path))
        compiled.add_edge(subset_root, source_node, relation="compiled_from")

    for node_id, attrs in list(compiled.nodes(data=True)):
        path_value = str(attrs.get("path", "")).strip()
        if not path_value:
            continue
        artifact_node = f"artifact_path:{path_value}"
        if not compiled.has_node(artifact_node):
            compiled.add_node(artifact_node, kind="artifact_path", path=path_value)
        if not compiled.has_edge(node_id, artifact_node):
            compiled.add_edge(node_id, artifact_node, relation="references_artifact")
            artifact_bridge_count += 1

    for node_id, attrs in list(compiled.nodes(data=True)):
        status_value = _queue_status_value(attrs)
        if not status_value:
            continue
        queue_node = f"queue_status_value:{status_value}"
        if not compiled.has_node(queue_node):
            compiled.add_node(queue_node, kind="queue_status_value", queue_status=status_value)
        if not compiled.has_edge(node_id, queue_node):
            compiled.add_edge(node_id, queue_node, relation="normalizes_queue_status")
            queue_status_bridge_count += 1

    out_graphml.parent.mkdir(parents=True, exist_ok=True)
    nx.write_graphml(compiled, out_graphml)
    payload = {
        "schema": "FIRST_CONTROLLER_A1_LAUNCH_SUBSET_GRAPH_RESULT_v1",
        "out_graphml": str(out_graphml),
        "graph_count": len(graph_paths),
        "node_count": compiled.number_of_nodes(),
        "edge_count": compiled.number_of_edges(),
        "artifact_bridge_count": artifact_bridge_count,
        "queue_status_bridge_count": queue_status_bridge_count,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
