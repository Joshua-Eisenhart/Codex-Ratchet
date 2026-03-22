"""
a1_jargoned_graph_builder.py

Materialize the A1 jargoned owner graph only from packet-backed Rosetta fuel
that is explicitly in scope for the queued A2->A1 handoff. This pass is
procedure-first and fail-closed: if the queue scope does not align with live
Rosetta packets, it writes an explicit blocked owner surface instead of
inventing a graph from projections or lexical heuristics.
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
QUEUE_PACKET = "system_v4/a2_state/NESTED_GRAPH_BUILD_QUEUE_STATUS_PACKET__CURRENT__2026_03_20__v1.json"
HANDOFF_PACKET = (
    "system_v4/a2_state/launch_bundles/nested_graph_build_a1_jargoned/"
    "NESTED_GRAPH_BUILD_WORKER_LAUNCH_HANDOFF__A1_JARGONED__2026_03_20__v1.json"
)
QUEUE_REGISTRY = "system_v3/a2_state/A1_QUEUE_CANDIDATE_REGISTRY__CURRENT__2026_03_15__v1.json"
ROSETTA_V2 = "system_v4/a1_state/rosetta_v2.json"
OUTPUT_JSON = "system_v4/a1_state/a1_jargoned_graph_v1.json"
AUDIT_NOTE = "system_v4/a2_state/audit_logs/A1_JARGONED_GRAPH_AUDIT__2026_03_20__v1.md"


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
    existing_materialized = existing.get("materialized") is True
    report_materialized = report.get("materialized") is True
    return (
        len(existing_nodes) > len(report_nodes)
        or len(existing_edges) > len(report_edges)
        or (existing_materialized and not report_materialized)
    )


def _source_terms_from_slice(data: dict[str, Any]) -> list[str]:
    terms: list[str] = []
    for key in [
        "primary_target_terms",
        "companion_terms",
        "deferred_terms",
        "graveyard_library_terms",
        "target_families",
    ]:
        value = data.get(key, [])
        if isinstance(value, list):
            for item in value:
                term = _clean_str(item)
                if term:
                    terms.append(term)
    # de-duplicate in stable order
    seen: set[str] = set()
    ordered: list[str] = []
    for term in terms:
        if term in seen:
            continue
        seen.add(term)
        ordered.append(term)
    return ordered


def _declared_family_slice_path(root: Path, handoff: dict[str, Any]) -> Path | None:
    for raw in handoff.get("source_artifacts", []):
        if "A2_TO_A1_FAMILY_SLICE" in raw:
            return _resolve(root, raw)
    return None


def build_a1_jargoned_graph(workspace_root: str) -> dict[str, Any]:
    root = Path(workspace_root).resolve()
    master = _load_json(_resolve(root, MASTER_GRAPH))
    queue_packet = _load_json(_resolve(root, QUEUE_PACKET))
    handoff = _load_json(_resolve(root, HANDOFF_PACKET))
    queue_registry = _load_json(_resolve(root, QUEUE_REGISTRY))
    rosetta = _load_json(_resolve(root, ROSETTA_V2))

    master_nodes = master.get("nodes", {})
    packets = rosetta.get("packets", {})

    selected_family_slice_name = _clean_str(queue_registry.get("selected_family_slice_json", ""))
    selected_family_slice_path = (
        root / "system_v3" / "a2_state" / selected_family_slice_name
        if selected_family_slice_name
        else None
    )
    selected_family_slice = (
        _load_json(selected_family_slice_path)
        if selected_family_slice_path and selected_family_slice_path.exists()
        else {}
    )
    declared_family_slice_path = _declared_family_slice_path(root, handoff)
    declared_family_slice = (
        _load_json(declared_family_slice_path)
        if declared_family_slice_path and declared_family_slice_path.exists()
        else {}
    )

    selected_scope_terms = _source_terms_from_slice(selected_family_slice)
    declared_scope_terms = _source_terms_from_slice(declared_family_slice)

    anchored_packets: dict[str, dict[str, Any]] = {}
    for packet_id, packet in packets.items():
        source_concept_id = _clean_str(packet.get("source_concept_id", ""))
        if source_concept_id and source_concept_id in master_nodes:
            anchored_packets[packet_id] = packet

    queue_scoped_packets = {
        packet_id: packet
        for packet_id, packet in anchored_packets.items()
        if _clean_str(packet.get("source_term", "")) in set(selected_scope_terms + declared_scope_terms)
    }

    block_reasons: list[str] = []
    if not selected_family_slice_name:
        block_reasons.append("queue candidate registry does not declare a selected_family_slice_json")
    if selected_family_slice_name and not selected_family_slice:
        block_reasons.append("selected family slice from queue registry is missing or unreadable")
    if declared_family_slice_path and not declared_family_slice:
        block_reasons.append("declared family slice in A1_JARGONED handoff is missing or unreadable")
    if declared_family_slice_path and selected_family_slice_name:
        if declared_family_slice_path.name != selected_family_slice_name:
            block_reasons.append(
                "queue registry selected family slice does not match A1_JARGONED handoff family slice"
            )
    if not selected_scope_terms and not declared_scope_terms:
        block_reasons.append("no explicit queue-scoped target terms are declared for A1_JARGONED")
    if not queue_scoped_packets:
        block_reasons.append("no packet-backed Rosetta nodes match the current queued A1 scope")

    build_status = "FAIL_CLOSED" if block_reasons else "MATERIALIZED"
    materialized = not block_reasons

    nodes: dict[str, Any] = {}
    if materialized:
        for packet_id, packet in sorted(queue_scoped_packets.items()):
            source_concept_id = _clean_str(packet.get("source_concept_id", ""))
            source_node = master_nodes.get(source_concept_id, {})
            nodes[packet_id] = {
                "id": packet_id,
                "node_type": _clean_str(packet.get("object_class", "ROSETTA_PACKET")),
                "layer": "A1_JARGONED",
                "trust_zone": "A1_JARGONED",
                "name": _clean_str(packet.get("source_term", packet_id)),
                "description": _clean_str(packet.get("source_context", "")),
                "status": _clean_str(packet.get("status", "PROPOSED")),
                "source_class": "OWNER_BOUND",
                "admissibility_state": "ROSETTA_DIVERTED",
                "lineage_refs": [source_concept_id] if source_concept_id else [],
                "witness_refs": [],
                "properties": {
                    "packet_id": packet_id,
                    "candidate_sense_id": _clean_str(packet.get("candidate_sense_id", "")),
                    "source_concept_id": source_concept_id,
                    "source_node_type": _clean_str(packet.get("source_node_type", "")),
                    "source_tags": list(packet.get("source_tags", [])),
                    "routing_reason": _clean_str(packet.get("routing_reason", "")),
                    "kernel_targets": list(packet.get("kernel_targets", [])),
                    "dependency_targets": list(packet.get("dependency_targets", [])),
                    "object_class": _clean_str(packet.get("object_class", "")),
                    "packet_status": _clean_str(packet.get("status", "")),
                    "source_anchor_name": _clean_str(source_node.get("name", "")),
                },
            }

    packet_classes = Counter(_clean_str(pkt.get("object_class", "")) for pkt in anchored_packets.values())
    packet_statuses = Counter(_clean_str(pkt.get("status", "")) for pkt in anchored_packets.values())

    return {
        "schema": "A1_JARGONED_GRAPH_v1",
        "generated_utc": _utc_iso(),
        "owner_layer": "A1_JARGONED",
        "materialized": materialized,
        "build_status": build_status,
        "derived_from": {
            "master_graph": str(_resolve(root, MASTER_GRAPH)),
            "queue_packet": str(_resolve(root, QUEUE_PACKET)),
            "handoff_packet": str(_resolve(root, HANDOFF_PACKET)),
            "queue_registry": str(_resolve(root, QUEUE_REGISTRY)),
            "rosetta_v2": str(_resolve(root, ROSETTA_V2)),
            "selected_family_slice": str(selected_family_slice_path) if selected_family_slice_path else "",
            "declared_family_slice": str(declared_family_slice_path) if declared_family_slice_path else "",
        },
        "selection_contract": {
            "included_node_rule": (
                "Include only Rosetta v2 packets with a non-empty source_concept_id "
                "that resolves in the live master graph and whose source_term falls "
                "inside the queued A1 scope."
            ),
            "edge_rule": (
                "No internal A1_JARGONED edges are materialized in this pass. "
                "ROSETTA_MAP and STRIPPED_FROM remain downstream explicit strip bridges."
            ),
            "projection_policy": "A1_GRAPH_PROJECTION is non-authoritative and cannot seed nodes.",
            "scope_terms_selected": selected_scope_terms,
            "scope_terms_declared": declared_scope_terms,
        },
        "blockers": block_reasons,
        "summary": {
            "node_count": len(nodes),
            "edge_count": 0,
            "anchored_rosetta_packet_count": len(anchored_packets),
            "queue_scoped_packet_count": len(queue_scoped_packets),
            "anchored_packet_classes": dict(packet_classes),
            "anchored_packet_statuses": dict(packet_statuses),
            "selected_family_slice_name": selected_family_slice_name,
            "selected_family_slice_term_count": len(selected_scope_terms),
            "declared_family_slice_term_count": len(declared_scope_terms),
        },
        "nodes": nodes,
        "edges": [],
    }


def render_audit_note(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# A1_JARGONED_GRAPH_AUDIT__2026_03_20__v1",
        "",
        f"generated_utc: {report['generated_utc']}",
        f"build_status: {report['build_status']}",
        f"materialized: {report['materialized']}",
        f"node_count: {summary['node_count']}",
        f"edge_count: {summary['edge_count']}",
        f"anchored_rosetta_packet_count: {summary['anchored_rosetta_packet_count']}",
        f"queue_scoped_packet_count: {summary['queue_scoped_packet_count']}",
        f"selected_family_slice_name: {summary['selected_family_slice_name']}",
        "",
        "## Selection Contract",
        f"- included_node_rule: {report['selection_contract']['included_node_rule']}",
        f"- edge_rule: {report['selection_contract']['edge_rule']}",
        f"- projection_policy: {report['selection_contract']['projection_policy']}",
        "",
        "## Scope Terms (Selected Family Slice)",
    ]
    if report["selection_contract"]["scope_terms_selected"]:
        for item in report["selection_contract"]["scope_terms_selected"]:
            lines.append(f"- {item}")
    else:
        lines.append("- none")
    lines.extend([
        "",
        "## Scope Terms (Declared Handoff Family Slice)",
    ])
    if report["selection_contract"]["scope_terms_declared"]:
        for item in report["selection_contract"]["scope_terms_declared"]:
            lines.append(f"- {item}")
    else:
        lines.append("- none")
    lines.extend([
        "",
        "## Anchored Packet Classes",
    ])
    for key, value in sorted(summary["anchored_packet_classes"].items()):
        lines.append(f"- {key}: {value}")
    lines.extend([
        "",
        "## Anchored Packet Statuses",
    ])
    for key, value in sorted(summary["anchored_packet_statuses"].items()):
        lines.append(f"- {key}: {value}")
    lines.extend([
        "",
        "## Blockers",
    ])
    if report["blockers"]:
        for blocker in report["blockers"]:
            lines.append(f"- {blocker}")
    else:
        lines.append("- none")
    lines.extend([
        "",
        "## Non-Claims",
        "- This pass does not promote A1_GRAPH_PROJECTION to owner authority.",
        "- This pass does not infer lexical or heuristic Rosetta graph edges.",
        "- This pass does not claim A1_STRIPPED or A1_CARTRIDGE already exist as owner graphs.",
        "",
    ])
    return "\n".join(lines)


def write_a1_jargoned_graph(workspace_root: str) -> dict[str, str]:
    root = Path(workspace_root).resolve()
    report = build_a1_jargoned_graph(str(root))

    json_path = _resolve(root, OUTPUT_JSON)
    audit_note_path = _resolve(root, AUDIT_NOTE)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    audit_note_path.parent.mkdir(parents=True, exist_ok=True)

    existing = _load_json(json_path)
    preserved_existing = _should_preserve_existing(existing, report)
    write_payload = existing if preserved_existing else report

    json_path.write_text(json.dumps(write_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    audit_text = render_audit_note(report)
    if preserved_existing:
        audit_text = "\n".join([
            "# NON_REGRESSION_PRESERVE",
            "",
            "Preserved the existing materialized A1 jargoned owner surface instead of overwriting it with a thinner or fail-closed rebuild.",
            f"- attempted_node_count: {len(report.get('nodes', {}))}",
            f"- attempted_edge_count: {len(report.get('edges', []))}",
            f"- attempted_build_status: {report.get('build_status', '')}",
            f"- preserved_node_count: {len(existing.get('nodes', {}))}",
            f"- preserved_edge_count: {len(existing.get('edges', []))}",
            f"- preserved_build_status: {existing.get('build_status', '')}",
            "",
            audit_text,
        ])
    audit_note_path.write_text(audit_text, encoding="utf-8")

    return {
        "json_path": str(json_path),
        "audit_note_path": str(audit_note_path),
    }


if __name__ == "__main__":
    result = write_a1_jargoned_graph(str(REPO_ROOT))
    print(json.dumps(result, indent=2, sort_keys=True))
