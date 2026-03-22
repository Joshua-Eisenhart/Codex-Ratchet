"""
a2_mid_refinement_graph_builder.py

Materialize the A2 mid-refinement owner graph as a bounded subset of the live
master graph after the identity registry and A2 high-intake owner graph exist.
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
A2_HIGH_INTAKE = "system_v4/a2_state/graphs/a2_high_intake_graph_v1.json"
OUTPUT_JSON = "system_v4/a2_state/graphs/a2_mid_refinement_graph_v1.json"
AUDIT_NOTE = "system_v4/a2_state/audit_logs/A2_MID_REFINEMENT_GRAPH_AUDIT__2026_03_20__v1.md"


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


def _should_preserve_existing(existing: dict[str, Any], report: dict[str, Any]) -> bool:
    existing_nodes = existing.get("nodes", {})
    existing_edges = existing.get("edges", [])
    report_nodes = report.get("nodes", {})
    report_edges = report.get("edges", [])
    if not isinstance(existing_nodes, dict) or not isinstance(existing_edges, list):
        return False
    if not isinstance(report_nodes, dict) or not isinstance(report_edges, list):
        return False
    return (
        len(existing_nodes) > len(report_nodes)
        or len(existing_edges) > len(report_edges)
    )


def _edge_signature(edge: dict[str, Any]) -> str:
    return json.dumps(edge, sort_keys=True)


def _include_node(node: dict[str, Any]) -> bool:
    return (
        _clean_str(node.get("node_type", "")) == "REFINED_CONCEPT"
        and _clean_str(node.get("trust_zone", "")) == "A2_2_CANDIDATE"
    )


def _build_summary(
    selected_nodes: dict[str, Any],
    selected_edges: list[dict[str, Any]],
    all_nodes: dict[str, Any],
) -> dict[str, Any]:
    node_counts_by_layer = Counter(_clean_str(node.get("layer", "")) for node in selected_nodes.values())
    edge_counts_by_relation = Counter(_clean_str(edge.get("relation", "")) for edge in selected_edges)
    selected_ids = set(selected_nodes)
    excluded_node_types = Counter(
        _clean_str(node.get("node_type", ""))
        for node_id, node in all_nodes.items()
        if node_id not in selected_ids
    )
    return {
        "node_count": len(selected_nodes),
        "edge_count": len(selected_edges),
        "node_counts_by_layer": dict(node_counts_by_layer),
        "edge_counts_by_relation": dict(edge_counts_by_relation),
        "excluded_node_types": dict(excluded_node_types),
    }


def _build_projection_diagnostics(
    selected_nodes: dict[str, Any],
    selected_edges: list[dict[str, Any]],
    master_edges: list[dict[str, Any]],
) -> dict[str, Any]:
    selected_ids = set(selected_nodes)
    boundary_edges = [
        edge
        for edge in master_edges
        if (edge.get("source_id") in selected_ids) ^ (edge.get("target_id") in selected_ids)
    ]
    internal_edges = len(selected_edges)
    boundary_edge_count = len(boundary_edges)
    attempted_total = internal_edges + boundary_edge_count
    source_map_origin_node_count = sum(
        1
        for node_id in selected_nodes
        if str(node_id).startswith("A2_3::SOURCE_MAP_PASS::")
    )
    selected_node_counts_by_trust_zone = Counter(
        _clean_str(node.get("trust_zone", "")) for node in selected_nodes.values()
    )
    selected_node_counts_by_status = Counter(
        _clean_str(node.get("status", "")) for node in selected_nodes.values()
    )
    selected_node_count_with_owner_declared_layer = sum(
        1 for node in selected_nodes.values() if _clean_str(node.get("layer", "")) == "A2_MID_REFINEMENT"
    )
    selected_node_count = len(selected_nodes)
    return {
        "selected_node_count": selected_node_count,
        "attempted_internal_edge_count": internal_edges,
        "selected_boundary_edge_count": boundary_edge_count,
        "internal_edge_retention_ratio": (
            round(internal_edges / attempted_total, 6) if attempted_total else 0.0
        ),
        "source_map_origin_node_count": source_map_origin_node_count,
        "source_map_origin_ratio": (
            round(source_map_origin_node_count / selected_node_count, 6)
            if selected_node_count
            else 0.0
        ),
        "selected_node_counts_by_trust_zone": dict(selected_node_counts_by_trust_zone),
        "selected_node_counts_by_status": dict(selected_node_counts_by_status),
        "selected_node_count_with_owner_declared_layer": selected_node_count_with_owner_declared_layer,
        "selected_node_count_with_non_owner_declared_layer": (
            selected_node_count - selected_node_count_with_owner_declared_layer
        ),
    }


def _build_preserve_diagnostics(
    existing: dict[str, Any],
    report: dict[str, Any],
    master_edges: list[dict[str, Any]],
) -> dict[str, Any]:
    existing_nodes = existing.get("nodes", {})
    existing_edges = existing.get("edges", [])
    attempted_edges = report.get("edges", [])
    master_edge_signatures = {_edge_signature(edge) for edge in master_edges}
    preserved_only_edges = [
        edge for edge in existing_edges if _edge_signature(edge) not in master_edge_signatures
    ]
    preserved_only_edge_count = len(preserved_only_edges)
    preserved_only_edge_counts_by_relation = Counter(
        _clean_str(edge.get("relation", "")) for edge in preserved_only_edges
    )
    overlap_edges = [
        edge for edge in preserved_only_edges if _clean_str(edge.get("relation", "")) == "OVERLAPS"
    ]
    existing_nodes = existing.get("nodes", {})
    overlap_layer_pairs = Counter()
    overlap_trust_zone_pairs = Counter()
    overlap_node_prefix_pairs = Counter()
    blank_link_type_count = 0
    zero_shared_count_count = 0
    for edge in overlap_edges:
        source_id = _clean_str(edge.get("source_id", ""))
        target_id = _clean_str(edge.get("target_id", ""))
        source_node = existing_nodes.get(source_id, {})
        target_node = existing_nodes.get(target_id, {})
        overlap_layer_pairs[(
            _clean_str(source_node.get("layer", "")),
            _clean_str(target_node.get("layer", "")),
        )] += 1
        overlap_trust_zone_pairs[(
            _clean_str(source_node.get("trust_zone", "")),
            _clean_str(target_node.get("trust_zone", "")),
        )] += 1
        source_parts = source_id.split("::")
        target_parts = target_id.split("::")
        source_prefix = "::".join(source_parts[:2]) if len(source_parts) >= 2 else source_id
        target_prefix = "::".join(target_parts[:2]) if len(target_parts) >= 2 else target_id
        overlap_node_prefix_pairs[(source_prefix, target_prefix)] += 1
        attributes = edge.get("attributes", {}) or {}
        if not _clean_str(attributes.get("link_type", "")):
            blank_link_type_count += 1
        if int(attributes.get("shared_count", 0) or 0) == 0:
            zero_shared_count_count += 1
    preserved_edge_count = len(existing_edges)
    overlap_attribute_contract_mismatch = (
        bool(overlap_edges)
        and (
            blank_link_type_count == len(overlap_edges)
            or zero_shared_count_count == len(overlap_edges)
        )
    )
    treatment_reason_flags = [
        "preserved_only_carryover_not_in_current_master_graph",
        "overlap_dominant_carryover",
    ]
    if overlap_attribute_contract_mismatch:
        treatment_reason_flags.append("overlap_attribute_contract_mismatch")
    treatment_reason_flags.append("no_direct_live_owner_edge_consumer_observed")
    return {
        "attempted_node_count": len(report.get("nodes", {})),
        "attempted_edge_count": len(attempted_edges),
        "preserved_node_count": len(existing_nodes),
        "preserved_edge_count": preserved_edge_count,
        "preserved_only_node_count": max(0, len(existing_nodes) - len(report.get("nodes", {}))),
        "attempted_only_node_count": max(0, len(report.get("nodes", {})) - len(existing_nodes)),
        "preserved_only_edge_count": preserved_only_edge_count,
        "preserved_only_edge_ratio": (
            round(preserved_only_edge_count / preserved_edge_count, 6)
            if preserved_edge_count
            else 0.0
        ),
        "attempted_only_edge_count": max(0, len(attempted_edges) - preserved_edge_count),
        "shared_live_edge_count": preserved_edge_count - preserved_only_edge_count,
        "preserved_only_edge_counts_by_relation": dict(preserved_only_edge_counts_by_relation),
        "preserved_only_overlaps_hygiene": {
            "preserved_only_overlap_edge_count": len(overlap_edges),
            "preserved_only_overlap_ratio_within_preserved_only_edges": (
                round(len(overlap_edges) / preserved_only_edge_count, 6)
                if preserved_only_edge_count
                else 0.0
            ),
            "preserved_only_overlap_layer_pairs": {
                f"{source}->{target}": count
                for (source, target), count in sorted(
                    overlap_layer_pairs.items(),
                    key=lambda item: (-item[1], item[0]),
                )
            },
            "preserved_only_overlap_trust_zone_pairs": {
                f"{source}->{target}": count
                for (source, target), count in sorted(
                    overlap_trust_zone_pairs.items(),
                    key=lambda item: (-item[1], item[0]),
                )
            },
            "preserved_only_overlap_node_prefix_pairs": {
                f"{source}->{target}": count
                for (source, target), count in sorted(
                    overlap_node_prefix_pairs.items(),
                    key=lambda item: (-item[1], item[0]),
                )[:5]
            },
            "blank_link_type_count": blank_link_type_count,
            "zero_shared_count_count": zero_shared_count_count,
        },
        "preserved_only_overlaps_treatment": {
            "current_runtime_effect": "none_observed_in_live_consumers",
            "equal_runtime_weight_admissible_now": False,
            "recommended_future_handling": "quarantine_or_downrank_before_equal_runtime_use",
            "reason_flags": treatment_reason_flags,
        },
    }


def _merge_preserved_payload(
    existing: dict[str, Any],
    report: dict[str, Any],
    all_nodes: dict[str, Any],
    master_edges: list[dict[str, Any]],
) -> dict[str, Any]:
    payload = dict(existing)
    payload["schema"] = report["schema"]
    payload["generated_utc"] = report["generated_utc"]
    payload["owner_layer"] = report["owner_layer"]
    payload["derived_from"] = report["derived_from"]
    payload["selection_contract"] = report["selection_contract"]
    payload["materialized"] = bool(existing.get("nodes", {}))
    payload["build_status"] = "MATERIALIZED" if payload["materialized"] else "FAIL_CLOSED"
    payload["projection_diagnostics"] = report["projection_diagnostics"]
    payload["preserve_diagnostics"] = _build_preserve_diagnostics(existing, report, master_edges)
    payload["summary"] = _build_summary(
        payload.get("nodes", {}),
        payload.get("edges", []),
        all_nodes,
    )
    return payload


def build_a2_mid_refinement_graph(workspace_root: str) -> dict[str, Any]:
    root = Path(workspace_root).resolve()
    master_path = _resolve(root, MASTER_GRAPH)
    identity_path = _resolve(root, IDENTITY_REGISTRY)
    a2_high_path = _resolve(root, A2_HIGH_INTAKE)

    for required in [identity_path, a2_high_path]:
        if not required.exists():
            raise FileNotFoundError(f"Prerequisite missing: {required}")

    master = _load_json(master_path)
    nodes = master.get("nodes", {})
    edges = master.get("edges", [])

    selected_nodes = {
        node_id: node
        for node_id, node in nodes.items()
        if _include_node(node)
    }
    selected_ids = set(selected_nodes)

    selected_edges = [
        edge for edge in edges
        if edge.get("source_id") in selected_ids and edge.get("target_id") in selected_ids
    ]

    summary = _build_summary(selected_nodes, selected_edges, nodes)
    projection_diagnostics = _build_projection_diagnostics(selected_nodes, selected_edges, edges)

    return {
        "schema": "A2_MID_REFINEMENT_GRAPH_v1",
        "generated_utc": _utc_iso(),
        "owner_layer": "A2_MID_REFINEMENT",
        "materialized": bool(selected_nodes),
        "build_status": "MATERIALIZED" if selected_nodes else "FAIL_CLOSED",
        "derived_from": {
            "master_graph": str(master_path),
            "identity_registry": str(identity_path),
            "a2_high_intake_graph": str(a2_high_path),
        },
        "selection_contract": {
            "included_node_types": ["REFINED_CONCEPT"],
            "included_if": [
                "REFINED_CONCEPT with trust_zone A2_2_CANDIDATE",
            ],
            "excluded_even_if_layer_matches": [
                "KERNEL_CONCEPT promoted into A2_1_KERNEL",
                "THREAD_SEAL graveyard markers",
                "REFINED_CONCEPT retired into GRAVEYARD",
            ],
            "edge_rule": "include all existing master-graph edges whose endpoints are both selected",
        },
        "summary": summary,
        "projection_diagnostics": projection_diagnostics,
        "nodes": dict(sorted(selected_nodes.items())),
        "edges": selected_edges,
    }


def render_audit_note(report: dict[str, Any]) -> str:
    summary = report["summary"]
    projection = report.get("projection_diagnostics", {})
    preserve = report.get("preserve_diagnostics")
    lines = [
        "# NON_REGRESSION_PRESERVE" if preserve else "# A2_MID_REFINEMENT_GRAPH_AUDIT__2026_03_20__v1",
    ]
    if preserve:
        lines.extend([
            "",
            "Preserved the existing richer A2 mid-refinement owner surface instead of overwriting it with a thinner projection pass.",
            f"- attempted_node_count: {preserve['attempted_node_count']}",
            f"- attempted_edge_count: {preserve['attempted_edge_count']}",
            f"- preserved_node_count: {preserve['preserved_node_count']}",
            f"- preserved_edge_count: {preserve['preserved_edge_count']}",
            f"- preserved_only_edge_count: {preserve['preserved_only_edge_count']}",
            f"- preserved_only_edge_ratio: {preserve['preserved_only_edge_ratio']}",
            "",
            "# A2_MID_REFINEMENT_GRAPH_AUDIT__2026_03_20__v1",
            "",
        ])
    else:
        lines.append("")
    lines.extend([
        f"generated_utc: {report['generated_utc']}",
        f"build_status: {report['build_status']}",
        f"materialized: {report['materialized']}",
        f"node_count: {summary['node_count']}",
        f"edge_count: {summary['edge_count']}",
        f"derived_from.master_graph: {report['derived_from']['master_graph']}",
        f"derived_from.identity_registry: {report['derived_from']['identity_registry']}",
        f"derived_from.a2_high_intake_graph: {report['derived_from']['a2_high_intake_graph']}",
        "",
        "## Projection Diagnostics",
        f"- attempted_internal_edge_count: {projection.get('attempted_internal_edge_count', 0)}",
        f"- selected_boundary_edge_count: {projection.get('selected_boundary_edge_count', 0)}",
        f"- internal_edge_retention_ratio: {projection.get('internal_edge_retention_ratio', 0.0)}",
        f"- source_map_origin_node_count: {projection.get('source_map_origin_node_count', 0)}",
        f"- source_map_origin_ratio: {projection.get('source_map_origin_ratio', 0.0)}",
        f"- selected_node_counts_by_trust_zone: {projection.get('selected_node_counts_by_trust_zone', {})}",
        f"- selected_node_counts_by_status: {projection.get('selected_node_counts_by_status', {})}",
        f"- selected_node_count_with_owner_declared_layer: {projection.get('selected_node_count_with_owner_declared_layer', 0)}",
        f"- selected_node_count_with_non_owner_declared_layer: {projection.get('selected_node_count_with_non_owner_declared_layer', 0)}",
        "",
        "## Included Node Layers",
    ])
    for key, value in sorted(summary["node_counts_by_layer"].items()):
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
    if preserve:
        lines.extend([
            "",
            "## Preserve Diagnostics",
            f"- preserved_only_node_count: {preserve.get('preserved_only_node_count', 0)}",
            f"- attempted_only_node_count: {preserve.get('attempted_only_node_count', 0)}",
            f"- preserved_only_edge_count: {preserve.get('preserved_only_edge_count', 0)}",
            f"- attempted_only_edge_count: {preserve.get('attempted_only_edge_count', 0)}",
            f"- shared_live_edge_count: {preserve.get('shared_live_edge_count', 0)}",
            "- preserved_only_edge_counts_by_relation:",
        ])
        preserved_only_relations = preserve.get("preserved_only_edge_counts_by_relation", {})
        if preserved_only_relations:
            for key, value in sorted(preserved_only_relations.items()):
                lines.append(f"  - {key}: {value}")
        else:
            lines.append("  - none")
        overlap_hygiene = preserve.get("preserved_only_overlaps_hygiene", {})
        if overlap_hygiene:
            lines.extend([
                "",
                "## Preserved-Only OVERLAPS Hygiene",
                f"- preserved_only_overlap_edge_count: {overlap_hygiene.get('preserved_only_overlap_edge_count', 0)}",
                (
                    "- preserved_only_overlap_ratio_within_preserved_only_edges: "
                    f"{overlap_hygiene.get('preserved_only_overlap_ratio_within_preserved_only_edges', 0.0)}"
                ),
                f"- blank_link_type_count: {overlap_hygiene.get('blank_link_type_count', 0)}",
                f"- zero_shared_count_count: {overlap_hygiene.get('zero_shared_count_count', 0)}",
                "- preserved_only_overlap_layer_pairs:",
            ])
            layer_pairs = overlap_hygiene.get("preserved_only_overlap_layer_pairs", {})
            if layer_pairs:
                for key, value in layer_pairs.items():
                    lines.append(f"  - {key}: {value}")
            else:
                lines.append("  - none")
            lines.append("- preserved_only_overlap_trust_zone_pairs:")
            trust_zone_pairs = overlap_hygiene.get("preserved_only_overlap_trust_zone_pairs", {})
            if trust_zone_pairs:
                for key, value in trust_zone_pairs.items():
                    lines.append(f"  - {key}: {value}")
            else:
                lines.append("  - none")
            lines.append("- preserved_only_overlap_node_prefix_pairs:")
            prefix_pairs = overlap_hygiene.get("preserved_only_overlap_node_prefix_pairs", {})
            if prefix_pairs:
                for key, value in prefix_pairs.items():
                    lines.append(f"  - {key}: {value}")
            else:
                lines.append("  - none")
        overlap_treatment = preserve.get("preserved_only_overlaps_treatment", {})
        if overlap_treatment:
            lines.extend([
                "",
                "## Preserved-Only OVERLAPS Treatment",
                f"- current_runtime_effect: {overlap_treatment.get('current_runtime_effect', '')}",
                f"- equal_runtime_weight_admissible_now: {overlap_treatment.get('equal_runtime_weight_admissible_now', False)}",
                f"- recommended_future_handling: {overlap_treatment.get('recommended_future_handling', '')}",
                f"- reason_flags: {overlap_treatment.get('reason_flags', [])}",
            ])
    lines.extend([
        "",
        "## Non-Claims",
        "- This owner graph is a bounded A2 mid-refinement materialization, not a full nested graph stack.",
        "- This pass does not materialize kernel, Rosetta, stripped, or cartridge owner graphs.",
        "- This pass does not treat promoted_subgraph or contradiction notes as authority for node membership.",
        "",
    ])
    return "\n".join(lines)


def write_a2_mid_refinement_graph(workspace_root: str) -> dict[str, str]:
    root = Path(workspace_root).resolve()
    report = build_a2_mid_refinement_graph(str(root))
    master = _load_json(_resolve(root, MASTER_GRAPH))

    json_path = _resolve(root, OUTPUT_JSON)
    audit_note_path = _resolve(root, AUDIT_NOTE)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    audit_note_path.parent.mkdir(parents=True, exist_ok=True)

    existing = _load_json(json_path)
    preserved_existing = _should_preserve_existing(existing, report)
    write_payload = (
        _merge_preserved_payload(
            existing,
            report,
            master.get("nodes", {}),
            master.get("edges", []),
        )
        if preserved_existing
        else report
    )

    json_path.write_text(json.dumps(write_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    audit_text = render_audit_note(write_payload)
    audit_note_path.write_text(audit_text, encoding="utf-8")

    return {
        "json_path": str(json_path),
        "audit_note_path": str(audit_note_path),
    }


if __name__ == "__main__":
    result = write_a2_mid_refinement_graph(str(REPO_ROOT))
    print(json.dumps(result, indent=2, sort_keys=True))
