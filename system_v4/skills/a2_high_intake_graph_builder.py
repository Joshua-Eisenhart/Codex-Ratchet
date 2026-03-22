"""
a2_high_intake_graph_builder.py

Materialize the A2 high-intake owner graph as a bounded subset of the live
master graph after the identity registry scaffold exists.
"""

from __future__ import annotations

import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


MASTER_GRAPH = "system_v4/a2_state/graphs/system_graph_a2_refinery.json"
IDENTITY_REGISTRY = "system_v4/a2_state/graphs/identity_registry_v1.json"
OUTPUT_JSON = "system_v4/a2_state/graphs/a2_high_intake_graph_v1.json"
AUDIT_NOTE = "system_v4/a2_state/audit_logs/A2_HIGH_INTAKE_GRAPH_AUDIT__2026_03_20__v1.md"


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _resolve(root: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    return path if path.is_absolute() else (root / path)


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _clean_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _include_node(node: dict[str, Any]) -> bool:
    node_type = _clean_str(node.get("node_type", ""))
    declared_layer = _clean_str(node.get("layer", ""))
    trust_zone = _clean_str(node.get("trust_zone", ""))

    if node_type == "EXTRACTED_CONCEPT" and (declared_layer == "A2_HIGH_INTAKE" or trust_zone in {"A2_3_INTAKE", "A2_HIGH_INTAKE"}):
        return True
    return False


def _build_projection_diagnostics(
    selected_nodes: dict[str, Any],
    selected_edges: list[dict[str, Any]],
    master_edges: list[dict[str, Any]],
) -> dict[str, Any]:
    selected_ids = set(selected_nodes)
    boundary_edge_count = sum(
        1
        for edge in master_edges
        if (edge.get("source_id") in selected_ids) ^ (edge.get("target_id") in selected_ids)
    )
    selected_node_counts_by_trust_zone = Counter(
        _clean_str(node.get("trust_zone", "")) for node in selected_nodes.values()
    )
    selected_node_counts_by_status = Counter(
        _clean_str(node.get("status", "")) for node in selected_nodes.values()
    )
    return {
        "selected_node_count": len(selected_nodes),
        "attempted_internal_edge_count": len(selected_edges),
        "selected_boundary_edge_count": boundary_edge_count,
        "internal_edge_retention_ratio": (
            round(len(selected_edges) / (len(selected_edges) + boundary_edge_count), 6)
            if (len(selected_edges) + boundary_edge_count)
            else 0.0
        ),
        "selected_node_counts_by_trust_zone": dict(selected_node_counts_by_trust_zone),
        "selected_node_counts_by_status": dict(selected_node_counts_by_status),
    }


def build_a2_high_intake_graph(workspace_root: str) -> dict[str, Any]:
    root = Path(workspace_root).resolve()
    master_path = _resolve(root, MASTER_GRAPH)
    identity_path = _resolve(root, IDENTITY_REGISTRY)

    if not identity_path.exists():
        raise FileNotFoundError(f"Identity registry prerequisite missing: {identity_path}")

    master = _load_json(master_path)
    nodes = master.get("nodes", {})
    edges = master.get("edges", [])

    selected_extracted = {
        node_id: node
        for node_id, node in nodes.items()
        if _include_node(node)
    }

    source_anchor_relations = {
        "SOURCE_MAP_PASS",
        "ENGINE_PATTERN_PASS",
        "MATH_CLASS_PASS",
        "QIT_BRIDGE_PASS",
    }
    anchored_source_ids: set[str] = set()
    extracted_ids = set(selected_extracted)
    for edge in edges:
        source_id = edge.get("source_id")
        target_id = edge.get("target_id")
        relation = _clean_str(edge.get("relation", ""))
        if relation not in source_anchor_relations:
            continue
        if target_id not in extracted_ids or source_id not in nodes:
            continue
        source_node = nodes[source_id]
        if _clean_str(source_node.get("node_type", "")) != "SOURCE_DOCUMENT":
            continue
        anchored_source_ids.add(source_id)

    selected_nodes = dict(selected_extracted)
    for node_id in anchored_source_ids:
        selected_nodes[node_id] = nodes[node_id]

    selected_ids = set(selected_nodes)

    selected_edges = [
        edge for edge in edges
        if edge.get("source_id") in selected_ids and edge.get("target_id") in selected_ids
    ]

    node_counts_by_type = Counter(_clean_str(node.get("node_type", "")) for node in selected_nodes.values())
    edge_counts_by_relation = Counter(_clean_str(edge.get("relation", "")) for edge in selected_edges)
    projection_diagnostics = _build_projection_diagnostics(selected_nodes, selected_edges, edges)

    excluded_node_types = Counter(
        _clean_str(node.get("node_type", ""))
        for node_id, node in nodes.items()
        if node_id not in selected_ids
    )

    return {
        "schema": "A2_HIGH_INTAKE_GRAPH_v1",
        "generated_utc": _utc_iso(),
        "owner_layer": "A2_HIGH_INTAKE",
        "materialized": bool(selected_nodes),
        "build_status": "MATERIALIZED" if selected_nodes else "FAIL_CLOSED",
        "derived_from": {
            "master_graph": str(master_path),
            "identity_registry": str(identity_path),
        },
        "selection_contract": {
            "included_node_types": ["SOURCE_DOCUMENT", "EXTRACTED_CONCEPT"],
            "included_if": [
                "EXTRACTED_CONCEPT with layer A2_HIGH_INTAKE or trust_zone A2_3_INTAKE/A2_HIGH_INTAKE",
                "SOURCE_DOCUMENT only when it directly anchors an included EXTRACTED_CONCEPT through SOURCE_MAP_PASS / ENGINE_PATTERN_PASS / MATH_CLASS_PASS / QIT_BRIDGE_PASS",
            ],
            "edge_rule": "include all existing master-graph edges whose endpoints are both selected",
        },
        "summary": {
            "node_count": len(selected_nodes),
            "edge_count": len(selected_edges),
            "node_counts_by_type": dict(node_counts_by_type),
            "edge_counts_by_relation": dict(edge_counts_by_relation),
            "anchored_source_document_count": len(anchored_source_ids),
            "included_extracted_concept_count": len(selected_extracted),
            "excluded_node_types": dict(excluded_node_types),
        },
        "projection_diagnostics": projection_diagnostics,
        "nodes": dict(sorted(selected_nodes.items())),
        "edges": selected_edges,
    }


def render_audit_note(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# A2_HIGH_INTAKE_GRAPH_AUDIT__2026_03_20__v1",
        "",
        f"generated_utc: {report['generated_utc']}",
        f"build_status: {report['build_status']}",
        f"materialized: {report['materialized']}",
        f"node_count: {summary['node_count']}",
        f"edge_count: {summary['edge_count']}",
        f"derived_from.master_graph: {report['derived_from']['master_graph']}",
        f"derived_from.identity_registry: {report['derived_from']['identity_registry']}",
        "",
        "## Projection Diagnostics",
        f"- attempted_internal_edge_count: {report.get('projection_diagnostics', {}).get('attempted_internal_edge_count', 0)}",
        f"- selected_boundary_edge_count: {report.get('projection_diagnostics', {}).get('selected_boundary_edge_count', 0)}",
        f"- internal_edge_retention_ratio: {report.get('projection_diagnostics', {}).get('internal_edge_retention_ratio', 0.0)}",
        f"- selected_node_counts_by_trust_zone: {report.get('projection_diagnostics', {}).get('selected_node_counts_by_trust_zone', {})}",
        f"- selected_node_counts_by_status: {report.get('projection_diagnostics', {}).get('selected_node_counts_by_status', {})}",
        "",
        "## Included Node Types",
    ]
    for key, value in sorted(summary["node_counts_by_type"].items()):
        lines.append(f"- {key}: {value}")
    lines.extend([
        "",
        "## Included Edge Relations",
    ])
    for key, value in sorted(summary["edge_counts_by_relation"].items()):
        lines.append(f"- {key}: {value}")
    lines.extend([
        "",
        "## Excluded Node Types",
    ])
    for key, value in sorted(summary["excluded_node_types"].items()):
        lines.append(f"- {key}: {value}")
    lines.extend([
        "",
        "## Non-Claims",
        "- This owner graph is a bounded A2 high-intake materialization, not a full nested graph stack.",
        "- This pass does not materialize contradiction, kernel, Rosetta, stripped, or cartridge owner graphs.",
        "- This pass does not promote projection artifacts to authority.",
        "",
    ])
    return "\n".join(lines)


def write_a2_high_intake_graph(workspace_root: str) -> dict[str, str]:
    root = Path(workspace_root).resolve()
    report = build_a2_high_intake_graph(str(root))

    json_path = _resolve(root, OUTPUT_JSON)
    audit_note_path = _resolve(root, AUDIT_NOTE)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    audit_note_path.parent.mkdir(parents=True, exist_ok=True)

    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    audit_note_path.write_text(render_audit_note(report), encoding="utf-8")

    return {
        "json_path": str(json_path),
        "audit_note_path": str(audit_note_path),
    }


if __name__ == "__main__":
    result = write_a2_high_intake_graph(str(REPO_ROOT))
    print(json.dumps(result, indent=2, sort_keys=True))
