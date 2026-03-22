"""
identity_registry_builder.py

Build the first additive identity-registry scaffold for the intended nested
graph stack. This is deliberately conservative: it only unifies records when
the current repo provides an explicit bridge signal.
"""

from __future__ import annotations

import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


MASTER_GRAPH = "system_v4/a2_state/graphs/system_graph_a2_refinery.json"
PROMOTED_SUBGRAPH = "system_v4/a2_state/graphs/promoted_subgraph.json"
A1_PROJECTION = "system_v4/a1_state/A1_GRAPH_PROJECTION.json"
ROSETTA_V2 = "system_v4/a1_state/rosetta_v2.json"
OUTPUT_JSON = "system_v4/a2_state/graphs/identity_registry_v1.json"
BRIDGE_NOTE = "system_v4/a2_state/graphs/identity_bridge_contracts__v1.md"
AUDIT_NOTE = "system_v4/a2_state/audit_logs/IDENTITY_REGISTRY_BUILD_AUDIT__2026_03_20__v1.md"


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _resolve(root: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    return path if path.is_absolute() else (root / path)


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _first_nonempty(values: list[str]) -> str:
    for value in values:
        if value:
            return value
    return ""


def _clean_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _should_preserve_existing(existing: dict[str, Any], registry: dict[str, Any]) -> bool:
    existing_nodes = existing.get("nodes", {})
    existing_edges = existing.get("edges", [])
    registry_entities = registry.get("entities", {})
    if not isinstance(existing_nodes, dict) or not isinstance(existing_edges, list):
        return False
    if existing_nodes:
        return True
    if not isinstance(registry_entities, dict):
        return False
    return False


def _follow_single_lineage(node_id: str, nodes: dict[str, dict[str, Any]]) -> str:
    seen: set[str] = set()
    current = node_id
    while current in nodes and current not in seen:
        seen.add(current)
        lineage_refs = [ref for ref in nodes[current].get("lineage_refs", []) if ref in nodes]
        if len(lineage_refs) != 1:
            break
        current = lineage_refs[0]
    return current


def _derive_entity_id(node_id: str, node: dict[str, Any], nodes: dict[str, dict[str, Any]]) -> tuple[str, str]:
    props = node.get("properties", {}) or {}
    source_concept_id = _clean_str(props.get("source_concept_id", ""))
    if source_concept_id:
        return source_concept_id, "source_concept_id"

    lineage_refs = [ref for ref in node.get("lineage_refs", []) if ref in nodes]
    if len(lineage_refs) == 1:
        return _follow_single_lineage(node_id, nodes), "single_lineage_root"

    original_path = _clean_str(node.get("original_path", ""))
    if node.get("node_type") == "SOURCE_DOCUMENT" and original_path:
        return f"DOC::{original_path}", "source_document_path"

    return node_id, "self"


def _new_entity(entity_id: str, mode: str) -> dict[str, Any]:
    return {
        "entity_id": entity_id,
        "identity_bases": [mode],
        "derivation_modes": [mode],
        "primary_name": "",
        "primary_node_type": "",
        "member_node_ids": [],
        "surface_memberships": [],
        "graph_memberships": [],
        "projection_memberships": [],
        "rosetta_packet_ids": [],
        "authorities": [],
        "statuses": [],
        "admissibility_states": [],
        "object_families": [],
        "source_classes": [],
        "declared_layers": [],
        "trust_zones": [],
        "original_paths": [],
        "lineage_refs": [],
        "witness_refs": [],
        "bridge_hints": {
            "source_concept_ids": [],
            "primary_candidate_ids": [],
            "candidate_ids": [],
            "target_ids": [],
            "target_refs": [],
        },
    }


def build_identity_registry(workspace_root: str) -> dict[str, Any]:
    root = Path(workspace_root).resolve()
    master = _load_json(_resolve(root, MASTER_GRAPH))
    promoted_subgraph = _load_json(_resolve(root, PROMOTED_SUBGRAPH))
    a1_projection = _load_json(_resolve(root, A1_PROJECTION))
    rosetta = _load_json(_resolve(root, ROSETTA_V2))

    nodes = master.get("nodes", {})
    entities: dict[str, dict[str, Any]] = {}
    derivation_counts: Counter[str] = Counter()
    unresolved_nodes: list[str] = []
    rosetta_pair_index: dict[tuple[str, str], dict[str, Any]] = {}
    wrapper_links: list[dict[str, Any]] = []

    for node_id, node in nodes.items():
        entity_id, mode = _derive_entity_id(node_id, node, nodes)
        derivation_counts[mode] += 1
        entity = entities.setdefault(entity_id, _new_entity(entity_id, mode))
        if mode not in entity["derivation_modes"]:
            entity["derivation_modes"].append(mode)
        if mode not in entity["identity_bases"]:
            entity["identity_bases"].append(mode)

        entity["member_node_ids"].append(node_id)
        membership = {
            "surface": "system_graph_a2_refinery",
            "node_id": node_id,
            "node_type": node.get("node_type", ""),
            "declared_layer": node.get("layer", ""),
            "trust_zone": node.get("trust_zone", ""),
        }
        entity["graph_memberships"].append(membership)
        entity["surface_memberships"].append(membership)

        entity["primary_name"] = _first_nonempty([entity["primary_name"], _clean_str(node.get("name", ""))])
        entity["primary_node_type"] = _first_nonempty(
            [entity["primary_node_type"], _clean_str(node.get("node_type", ""))]
        )

        for field, target in [
            ("authority", "authorities"),
            ("status", "statuses"),
            ("admissibility_state", "admissibility_states"),
            ("object_family", "object_families"),
            ("source_class", "source_classes"),
            ("layer", "declared_layers"),
            ("trust_zone", "trust_zones"),
        ]:
            value = _clean_str(node.get(field, ""))
            if value and value not in entity[target]:
                entity[target].append(value)

        original_path = _clean_str(node.get("original_path", ""))
        if original_path and original_path not in entity["original_paths"]:
            entity["original_paths"].append(original_path)

        for ref in node.get("lineage_refs", []):
            if ref not in entity["lineage_refs"]:
                entity["lineage_refs"].append(ref)
        for ref in node.get("witness_refs", []):
            if ref not in entity["witness_refs"]:
                entity["witness_refs"].append(ref)

        props = node.get("properties", {}) or {}
        for key, hint_key in [
            ("source_concept_id", "source_concept_ids"),
            ("primary_candidate_id", "primary_candidate_ids"),
            ("candidate_id", "candidate_ids"),
            ("target_id", "target_ids"),
            ("target_ref", "target_refs"),
        ]:
            value = _clean_str(props.get(key, ""))
            if value and value not in entity["bridge_hints"][hint_key]:
                entity["bridge_hints"][hint_key].append(value)

        if mode == "self" and not original_path and not node.get("lineage_refs") and not props.get("source_concept_id"):
            unresolved_nodes.append(node_id)

    promoted_nodes = promoted_subgraph.get("nodes", {})
    for node_id, node in promoted_nodes.items():
        if node_id not in nodes:
            continue
        entity_id, _ = _derive_entity_id(node_id, nodes[node_id], nodes)
        entity = entities.setdefault(entity_id, _new_entity(entity_id, "promoted_exact_id"))
        membership = {
            "surface": "promoted_subgraph",
            "node_id": node_id,
            "node_type": node.get("node_type", ""),
            "declared_layer": node.get("layer", ""),
            "trust_zone": node.get("trust_zone", ""),
        }
        entity["surface_memberships"].append(membership)

    projection_nodes = a1_projection.get("nodes", {})
    for node_id, node in projection_nodes.items():
        if node_id in nodes:
            entity_id, _ = _derive_entity_id(node_id, nodes[node_id], nodes)
        else:
            entity_id, _ = _derive_entity_id(node_id, node, projection_nodes)
        entity = entities.setdefault(entity_id, _new_entity(entity_id, "projection_only"))
        membership = {
            "surface": "A1_GRAPH_PROJECTION",
            "node_id": node_id,
            "declared_layer": node.get("layer", ""),
            "trust_zone": node.get("trust_zone", ""),
            "node_type": node.get("node_type", ""),
        }
        entity["projection_memberships"].append(membership)
        entity["surface_memberships"].append(membership)

    anchored_rosetta = 0
    unanchored_rosetta: list[str] = []
    packets = rosetta.get("packets", {}) or {}
    for packet_id, packet in packets.items():
        source_concept_id = _clean_str(packet.get("source_concept_id", ""))
        if source_concept_id:
            entity = entities.setdefault(source_concept_id, _new_entity(source_concept_id, "rosetta_source_concept"))
            entity["rosetta_packet_ids"].append(packet_id)
            anchored_rosetta += 1
            continue
        unanchored_rosetta.append(packet_id)

    for edge in master.get("edges", []):
        source_id = _clean_str(edge.get("source_id", ""))
        target_id = _clean_str(edge.get("target_id", ""))
        relation = _clean_str(edge.get("relation", ""))
        if not source_id or not target_id or source_id not in nodes or target_id not in nodes:
            continue

        source_zone = _clean_str(nodes[source_id].get("trust_zone", ""))
        target_zone = _clean_str(nodes[target_id].get("trust_zone", ""))

        if relation in {"ROSETTA_MAP", "STRIPPED_FROM"} and {source_zone, target_zone} == {"A1_JARGONED", "A1_STRIPPED"}:
            pair_key = tuple(sorted([source_id, target_id]))
            record = rosetta_pair_index.setdefault(
                pair_key,
                {
                    "kind": "A1_ROSETTA_CORRESPONDENCE",
                    "node_ids": list(pair_key),
                    "relations": [],
                    "trust_zones": sorted([source_zone, target_zone]),
                },
            )
            if relation not in record["relations"]:
                record["relations"].append(relation)
            continue

        if relation == "PACKAGED_FROM":
            wrapper_links.append(
                {
                    "kind": "A1_CARTRIDGE_WRAPPER",
                    "wrapper_node_id": source_id,
                    "wrapped_node_id": target_id,
                    "wrapper_trust_zone": source_zone,
                    "wrapped_trust_zone": target_zone,
                }
            )

    summary = {
        "master_graph_nodes": len(nodes),
        "registry_entities": len(entities),
        "projection_nodes": len(projection_nodes),
        "anchored_rosetta_packets": anchored_rosetta,
        "unanchored_rosetta_packets": len(unanchored_rosetta),
        "a1_rosetta_correspondence_count": len(rosetta_pair_index),
        "a1_cartridge_wrapper_count": len(wrapper_links),
        "derivation_mode_counts": dict(derivation_counts),
        "unresolved_node_count": len(unresolved_nodes),
    }

    return {
        "schema": "IDENTITY_REGISTRY_v1",
        "generated_utc": _utc_iso(),
        "source_surfaces": {
            "master_graph": str(_resolve(root, MASTER_GRAPH)),
            "promoted_subgraph": str(_resolve(root, PROMOTED_SUBGRAPH)),
            "a1_projection": str(_resolve(root, A1_PROJECTION)),
            "rosetta_v2": str(_resolve(root, ROSETTA_V2)),
        },
        "summary": summary,
        "cross_surface_correspondences": list(sorted(rosetta_pair_index.values(), key=lambda item: tuple(item["node_ids"]))),
        "wrapper_links": wrapper_links,
        "unanchored_rosetta_packets": unanchored_rosetta,
        "entities": dict(sorted(entities.items())),
    }


def render_bridge_contracts(registry: dict[str, Any]) -> str:
    summary = registry["summary"]
    return "\n".join([
        "# identity_bridge_contracts__v1",
        "",
        "This note records only the bridge signals that are trustworthy enough for the first identity-registry scaffold.",
        "",
        "## Reliable Now",
        "- `canonical_concept_id`: use the A2 graph node id as the canonical anchor when a record descends from graph material.",
        "- `carrier_layer` plus local `carrier_id`: use this pair for per-surface binding instead of overloading lexical fields.",
        "- `properties.source_concept_id`: primary lower-loop bridge for B/graveyard/runtime records.",
        "- exact graph node id reuse across `A1_GRAPH_PROJECTION`: treat as projection membership only, not a fresh identity key.",
        "- `rosetta_v2.source_concept_id` plus `packet_id`: usable Rosetta bridge only when `source_concept_id` is populated.",
        "- `candidate_id`, `primary_candidate_id`, `target_id`, `sim_id`, and `failure_mode_id`: runtime-local bridge handles only within their declared carrier layers.",
        "",
        "## Allowed Strong Bridge Signals",
        "- `properties.source_concept_id`: primary lower-loop bridge for B/graveyard/runtime records.",
        "- single resolvable `lineage_refs` chain: allowed for conservative ancestor-root grouping.",
        "- `SOURCE_DOCUMENT.original_path`: allowed to stabilize document-root identities.",
        "- exact graph node id reuse across projection surfaces: allowed as a projection membership, not a new entity.",
        "",
        "## Weak Or External-Only Signals",
        "- `name`, `description`, `tags`, and heuristic cross-links are not identity proofs.",
        "- Rosetta packets without `source_concept_id` remain external references only.",
        "- Multiple `lineage_refs` are preserved as ambiguity, not auto-merged into one entity.",
        "- `target_ref` and `target_id` are bridge hints only; they do not create canonical identity on their own.",
        "- `source_term`, `candidate_sense_id`, and export text are lexical or reporting surfaces, not canonical identity.",
        "",
        "## Minimal Bridge Contract Fields",
        "- `canonical_concept_id`",
        "- `carrier_layer`",
        "- `carrier_id`",
        "- `dispatch_batch_id`",
        "- `kernel_batch_id`",
        "- `primary_candidate_id`",
        "- `target_candidate_id`",
        "- `failure_mode_id`",
        "- `bridge_relation`",
        "- `legacy_target_ref` (deprecated, non-canonical)",
        "",
        "## Current Scaffold Counts",
        f"- registry_entities: {summary['registry_entities']}",
        f"- anchored_rosetta_packets: {summary['anchored_rosetta_packets']}",
        f"- unanchored_rosetta_packets: {summary['unanchored_rosetta_packets']}",
        f"- a1_rosetta_correspondence_count: {summary['a1_rosetta_correspondence_count']}",
        f"- a1_cartridge_wrapper_count: {summary['a1_cartridge_wrapper_count']}",
        f"- unresolved_node_count: {summary['unresolved_node_count']}",
        "",
        "## Explicit Non-Claims",
        "- This scaffold does not claim the six intended layer stores already exist.",
        "- This scaffold does not flatten topology, axis, basin, or Rosetta semantics into a false canonical ontology.",
        "- This scaffold does not treat projections as authoritative owner stores.",
        "",
    ]) + "\n"


def render_audit_note(registry: dict[str, Any]) -> str:
    summary = registry["summary"]
    lines = [
        "# IDENTITY_REGISTRY_BUILD_AUDIT__2026_03_20__v1",
        "",
        f"generated_utc: {registry['generated_utc']}",
        f"master_graph_nodes: {summary['master_graph_nodes']}",
        f"registry_entities: {summary['registry_entities']}",
        f"projection_nodes: {summary['projection_nodes']}",
        f"anchored_rosetta_packets: {summary['anchored_rosetta_packets']}",
        f"unanchored_rosetta_packets: {summary['unanchored_rosetta_packets']}",
        f"a1_rosetta_correspondence_count: {summary['a1_rosetta_correspondence_count']}",
        f"a1_cartridge_wrapper_count: {summary['a1_cartridge_wrapper_count']}",
        f"unresolved_node_count: {summary['unresolved_node_count']}",
        "",
        "## Derivation Mode Counts",
    ]
    for key, value in sorted(summary["derivation_mode_counts"].items()):
        lines.append(f"- {key}: {value}")
    lines.extend([
        "",
        "## Pass Result",
        "- emitted one additive identity-registry scaffold",
        "- emitted one bridge-contract note",
        "- preserved ambiguous identity cases instead of auto-merging them",
        "- kept unanchored Rosetta packets external instead of inventing graph membership",
        "",
        "## Remaining Limits",
        "- separate A2/A1 owner graphs are still not materialized",
        "- multi-lineage cases remain unresolved by design",
        "- topology/axes/attractor semantics are still concept-rich but structurally thin",
        "",
    ])
    return "\n".join(lines)


def write_identity_registry(workspace_root: str) -> dict[str, str]:
    root = Path(workspace_root).resolve()
    registry = build_identity_registry(str(root))

    json_path = _resolve(root, OUTPUT_JSON)
    bridge_note_path = _resolve(root, BRIDGE_NOTE)
    audit_note_path = _resolve(root, AUDIT_NOTE)

    json_path.parent.mkdir(parents=True, exist_ok=True)
    bridge_note_path.parent.mkdir(parents=True, exist_ok=True)
    audit_note_path.parent.mkdir(parents=True, exist_ok=True)

    existing = _load_json(json_path)
    preserved_existing = _should_preserve_existing(existing, registry)
    write_payload = existing if preserved_existing else registry

    json_path.write_text(json.dumps(write_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    bridge_note_path.write_text(render_bridge_contracts(registry), encoding="utf-8")
    audit_text = render_audit_note(registry)
    if preserved_existing:
        audit_text = "\n".join([
            "# NON_REGRESSION_PRESERVE",
            "",
            "Preserved the existing populated identity owner surface instead of overwriting it with the older scaffold builder output.",
            f"- attempted_registry_entities: {len(registry.get('entities', {}))}",
            f"- preserved_node_count: {len(existing.get('nodes', {}))}",
            f"- preserved_edge_count: {len(existing.get('edges', []))}",
            "",
            audit_text,
        ])
    audit_note_path.write_text(audit_text, encoding="utf-8")

    return {
        "json_path": str(json_path),
        "bridge_note_path": str(bridge_note_path),
        "audit_note_path": str(audit_note_path),
    }


if __name__ == "__main__":
    result = write_identity_registry(str(REPO_ROOT))
    print(json.dumps(result, indent=2, sort_keys=True))
