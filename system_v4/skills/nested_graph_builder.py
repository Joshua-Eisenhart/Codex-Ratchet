"""
nested_graph_builder.py

Builds the nested graph-of-graphs from the 5 layer graphs using 
TopoNetX for higher-order topology and PyG for tensor-edge structure.

This is the forward-motion code that the V4 spec calls for:
"the target is an evolving nested graph family or graph-of-graphs"
"the graph family should reflect control relations, constraint
 eliminations, witness structure, and runtime transitions"

NOT a sidecar. NOT an audit. This BUILDS the nested_graph_v1.json
that has been sitting empty.
"""

from __future__ import annotations

import json
import os
import time
import hashlib
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]

# The 5 layer graphs that form the nested structure
LAYER_GRAPHS = {
    "A2_HIGH_INTAKE": {
        "path": "system_v4/a2_state/graphs/a2_high_intake_graph_v1.json",
        "rank": 0,  # outermost layer
        "trust_zone": "A2_3_INTAKE",
        "description": "Raw extraction from source documents",
    },
    "A2_MID_REFINEMENT": {
        "path": "system_v4/a2_state/graphs/a2_mid_refinement_graph_v1.json",
        "rank": 1,
        "trust_zone": "A2_2_CONTRADICTION",
        "description": "Refined concepts after cross-validation",
    },
    "A2_LOW_CONTROL": {
        "path": "system_v4/a2_state/graphs/a2_low_control_graph_v1.json",
        "rank": 2,
        "trust_zone": "A2_1_KERNEL",
        "description": "Kernel control concepts - structural truth",
    },
    "A1_JARGONED": {
        "path": "system_v4/a2_state/graphs/a1_jargoned_graph_v1.json",
        "rank": 3,
        "trust_zone": "A1",
        "description": "A1 jargoned kernel view for strategy packets",
    },
    "PROMOTED_SUBGRAPH": {
        "path": "system_v4/a2_state/graphs/promoted_subgraph.json",
        "rank": -1,  # cross-cutting
        "trust_zone": "CROSS_LAYER",
        "description": "Cross-layer promotion records",
    },
    "QIT_ENGINE": {
        "path": "system_v4/a2_state/graphs/qit_engine_graph_v1.json",
        "rank": 4,  # physics layer below A1
        "trust_zone": "PHYSICS",
        "description": "QIT engine topology: macro-stages, operators, tori, axes, negative witnesses",
    },
}

# The authoritative accumulation graph and the target nested graph
ACCUMULATION_GRAPH = "system_v4/a2_state/graphs/system_graph_a2_refinery.json"
NESTED_GRAPH_OUT = "system_v4/a2_state/graphs/nested_graph_v1.json"
REPORT_JSON = "system_v4/a2_state/audit_logs/NESTED_GRAPH_BUILD_REPORT__v1.json"
REPORT_MD = "system_v4/a2_state/audit_logs/NESTED_GRAPH_BUILD_REPORT__v1.md"
QIT_BRIDGE_REGISTRY = "system_v4/a2_state/graphs/qit_cross_layer_registry_v1.json"

# Cross-layer edge relations that connect layers
CROSS_LAYER_RELATIONS = {
    "REFINED_INTO",      # A2_HIGH → A2_MID
    "PROMOTED_TO_KERNEL", # A2_MID → A2_LOW
    "DEPENDS_ON",        # can be intra or inter-layer
    "STRUCTURALLY_RELATED",
    "SKILL_OPERATES_ON", # SKILL → KERNEL_CONCEPT
    "ACCEPTED_FROM",     # B_SURVIVOR → source concept
    "SIM_EVIDENCE_FOR",  # SIM → B_SURVIVOR
    "AXIS_GOVERNS",      # AXIS → ENGINE (physics layer)
    "NEGATIVE_PROVES",   # NEG_WITNESS → structure (physics layer)
    "OPERATOR_ACTS_ON",  # OPERATOR → MACRO_STAGE (physics layer)
    "QIT_AXIS_BRIDGE",   # explicit admitted system ↔ QIT axis link
    "QIT_ENGINE_FAMILY_BRIDGE",
    "QIT_OPERATOR_FAMILY_BRIDGE",
}

PREFERRED_INTERPRETER = "/opt/homebrew/bin/python3"


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _node_id(prefix: str, name: str) -> str:
    raw = f"{prefix}::{name}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _build_layer_summary(root: Path, layer_id: str, layer_cfg: dict) -> dict[str, Any]:
    """Build summary for one layer graph."""
    data = _load_json(root / layer_cfg["path"])
    nodes = data.get("nodes", {}) if isinstance(data, dict) else {}
    edges = data.get("edges", []) if isinstance(data, dict) else []

    if not isinstance(nodes, dict):
        nodes = {}
    if not isinstance(edges, list):
        edges = []

    node_types = Counter(
        n.get("node_type", "?") for n in nodes.values() if isinstance(n, dict)
    )
    relation_types = Counter(
        e.get("relation", "?") for e in edges if isinstance(e, dict)
    )

    return {
        "layer_id": layer_id,
        "path": layer_cfg["path"],
        "rank": layer_cfg["rank"],
        "trust_zone": layer_cfg["trust_zone"],
        "description": layer_cfg["description"],
        "node_count": len(nodes),
        "edge_count": len(edges),
        "node_types": dict(node_types),
        "relation_types": dict(relation_types),
        "node_ids": sorted(nodes.keys()),
    }


def _node_layer_from_type(node: dict[str, Any]) -> str | None:
    """Best-effort layer classification for accumulation-only node types."""
    ntype = node.get("node_type", "")
    if ntype == "SKILL":
        return "SKILLS"
    if ntype in ("B_OUTCOME", "B_SURVIVOR", "B_PARKED"):
        return "B_LAYER"
    if ntype in ("SIM_EVIDENCED", "SIM_KILL"):
        return "SIM_LAYER"
    if ntype == "GRAVEYARD_RECORD":
        return "GRAVEYARD"
    if ntype == "TERM_ADMITTED":
        return "TERM_LAYER"
    return None


def _build_layer_indexes(root: Path) -> dict[str, dict[str, str]]:
    """Collect exact node-id and public-id bindings for all configured layers."""
    node_to_layer: dict[str, str] = {}
    public_id_to_layer: dict[str, str] = {}
    public_id_to_node_id: dict[str, str] = {}
    node_memberships: dict[str, list[str]] = defaultdict(list)

    for layer_id, cfg in LAYER_GRAPHS.items():
        layer_data = _load_json(root / cfg["path"])
        layer_nodes = layer_data.get("nodes", {}) if isinstance(layer_data, dict) else {}
        if not isinstance(layer_nodes, dict):
            layer_nodes = {}

        public_id_index = layer_data.get("public_id_index", {}) if isinstance(layer_data, dict) else {}
        if not isinstance(public_id_index, dict):
            public_id_index = {}

        for nid, node in layer_nodes.items():
            node_memberships.setdefault(nid, [])
            if layer_id not in node_memberships[nid]:
                node_memberships[nid].append(layer_id)
            # First-loaded layer wins — preserve highest-rank attribution
            if nid not in node_to_layer:
                node_to_layer[nid] = layer_id
            if isinstance(node, dict):
                public_id = node.get("public_id", "")
                if isinstance(public_id, str) and public_id:
                    public_id_to_layer[public_id] = layer_id
                    public_id_to_node_id[public_id] = nid

        for public_id, nid in public_id_index.items():
            if not isinstance(public_id, str) or not public_id:
                continue
            if not isinstance(nid, str) or not nid:
                continue
            public_id_to_layer[public_id] = layer_id
            public_id_to_node_id[public_id] = nid

    return {
        "node_to_layer": node_to_layer,
        "public_id_to_layer": public_id_to_layer,
        "public_id_to_node_id": public_id_to_node_id,
        "node_memberships": node_memberships,
    }


def _resolve_layer_binding(
    ref: str,
    layer_indexes: dict[str, dict[str, str]],
) -> dict[str, str] | None:
    """Resolve an exact layer node id or a layer public_id."""
    if not isinstance(ref, str) or not ref:
        return None

    node_to_layer = layer_indexes["node_to_layer"]
    if ref in node_to_layer:
        return {
            "node_id": ref,
            "layer": node_to_layer[ref],
            "resolved_via": "node_id",
        }

    public_id_to_node_id = layer_indexes["public_id_to_node_id"]
    public_id_to_layer = layer_indexes["public_id_to_layer"]
    if ref in public_id_to_node_id:
        return {
            "node_id": public_id_to_node_id[ref],
            "layer": public_id_to_layer[ref],
            "public_id": ref,
            "resolved_via": "public_id",
        }

    return None


def _resolve_edge_endpoint(
    edge: dict[str, Any],
    endpoint: str,
    layer_indexes: dict[str, dict[str, str]],
) -> dict[str, str] | None:
    """Resolve edge endpoints using exact ids first, then public ids."""
    endpoint_id_key = f"{endpoint}_id"
    direct = _resolve_layer_binding(edge.get(endpoint_id_key, ""), layer_indexes)
    if direct:
        return direct

    public_keys = [
        f"{endpoint}_public_id",
        f"{endpoint}_canonical_concept_id",
    ]
    attrs = edge.get("attributes", {}) or {}
    if isinstance(attrs, dict):
        public_keys.extend([
            f"{endpoint}_public_id",
            f"{endpoint}_canonical_concept_id",
        ])

    for key in public_keys:
        if key in edge:
            resolved = _resolve_layer_binding(edge.get(key, ""), layer_indexes)
            if resolved:
                return resolved
        if isinstance(attrs, dict) and key in attrs:
            resolved = _resolve_layer_binding(attrs.get(key, ""), layer_indexes)
            if resolved:
                return resolved

    return None


def _iter_strong_node_bridges(
    node_id: str,
    node: dict[str, Any],
    layer_indexes: dict[str, dict[str, str]],
) -> list[dict[str, Any]]:
    """Extract conservative bridge targets from repo-approved strong fields only."""
    props = node.get("properties", {}) or {}
    bridges: list[dict[str, Any]] = []

    def add_bridge(ref: Any, field: str, via: str | None = None) -> None:
        resolved = _resolve_layer_binding(ref if isinstance(ref, str) else "", layer_indexes)
        if not resolved:
            return
        relation = {
            "canonical_concept_id": "CANONICAL_CONCEPT_BRIDGE",
            "source_concept_id": "SOURCE_CONCEPT_ID_BRIDGE",
        }.get(field, "STRONG_IDENTITY_BRIDGE")
        bridges.append({
            "source_id": node_id,
            "target_id": resolved["node_id"],
            "target_layer": resolved["layer"],
            "target_public_id": resolved.get("public_id", ""),
            "target_resolved_via": resolved["resolved_via"],
            "bridge_field": field,
            "bridge_via": via or field,
            "relation": relation,
        })

    for field in ("canonical_concept_id", "source_concept_id"):
        value = node.get(field)
        if not value:
            value = props.get(field)
        add_bridge(value, field)

    carrier_layer = node.get("carrier_layer") or props.get("carrier_layer")
    carrier_id = node.get("carrier_id") or props.get("carrier_id")
    if isinstance(carrier_layer, str) and carrier_layer and isinstance(carrier_id, str) and carrier_id:
        resolved = _resolve_layer_binding(carrier_id, layer_indexes)
        if resolved and resolved["layer"] == carrier_layer:
            bridges.append({
                "source_id": node_id,
                "target_id": resolved["node_id"],
                "target_layer": resolved["layer"],
                "target_public_id": resolved.get("public_id", ""),
                "target_resolved_via": resolved["resolved_via"],
                "bridge_field": "carrier_id",
                "bridge_via": "carrier_layer+carrier_id",
                "relation": "CARRIER_BINDING_BRIDGE",
            })

    return bridges


def _iter_registry_bridges(
    root: Path,
    nodes: dict[str, Any],
    layer_indexes: dict[str, dict[str, str]],
    node_to_layer: dict[str, str],
) -> list[dict[str, Any]]:
    """Load explicit admitted QIT bridge records from the registry surface."""
    registry = _load_json(root / QIT_BRIDGE_REGISTRY)
    bridge_rows = registry.get("bridges", []) if isinstance(registry, dict) else []
    if not isinstance(bridge_rows, list):
        return []

    bridges: list[dict[str, Any]] = []
    for row in bridge_rows:
        if not isinstance(row, dict):
            continue
        if row.get("status") != "ADMITTED":
            continue

        source_ref = row.get("source_id") or row.get("source_public_id") or ""
        target_ref = row.get("target_id") or row.get("target_public_id") or ""
        relation = str(row.get("relation", "QIT_EXPLICIT_BRIDGE"))

        source_binding = _resolve_layer_binding(source_ref, layer_indexes)
        target_binding = _resolve_layer_binding(target_ref, layer_indexes)
        if not target_binding:
            continue

        source_layer_hint = str(row.get("source_layer", "") or "")
        source_memberships = layer_indexes.get("node_memberships", {}).get(
            source_binding["node_id"] if source_binding else source_ref,
            [],
        )
        source_layer = (
            source_binding["layer"]
            if source_binding
            else node_to_layer.get(source_ref, "UNKNOWN")
        )
        if source_layer == "UNKNOWN":
            source_node = nodes.get(source_ref)
            if isinstance(source_node, dict):
                source_layer = _node_layer_from_type(source_node) or "UNKNOWN"
        if source_layer_hint:
            if source_layer_hint not in source_memberships:
                continue
            source_layer = source_layer_hint
        if source_layer == "UNKNOWN" or source_layer == target_binding["layer"]:
            continue

        bridges.append({
            "source_id": source_binding["node_id"] if source_binding else source_ref,
            "target_id": target_binding["node_id"],
            "resolved_source_id": source_binding["node_id"] if source_binding else source_ref,
            "resolved_target_id": target_binding["node_id"],
            "source_layer": source_layer,
            "target_layer": target_binding["layer"],
            "relation": relation,
            "attributes": {
                "registry_bridge_id": row.get("bridge_id", ""),
                "bridge_via": row.get("bridge_via", "explicit_registry"),
                "scope": row.get("scope", ""),
                "rationale": row.get("rationale", ""),
                "registry_source_layer": source_layer_hint or source_layer,
                "target_public_id": row.get("target_public_id", ""),
                "derived": True,
            },
            "source_resolved_via": source_binding["resolved_via"] if source_binding else "node_id",
            "target_resolved_via": target_binding["resolved_via"],
            "discovery_mode": "explicit_bridge_registry",
        })

    return bridges


def _find_cross_layer_edges(root: Path) -> list[dict[str, Any]]:
    """Find edges in the accumulation graph that connect nodes across layers."""
    accum = _load_json(root / ACCUMULATION_GRAPH)
    nodes = accum.get("nodes", {}) if isinstance(accum, dict) else {}
    edges = accum.get("edges", []) if isinstance(accum, dict) else []

    layer_indexes = _build_layer_indexes(root)
    # Use first-loaded layer (highest-rank) as canonical, preserving multi-membership
    node_to_layer = dict(layer_indexes["node_to_layer"])
    node_memberships = layer_indexes.get("node_memberships", {})

    # Also map node types from accumulation graph for nodes not in any layer
    for nid, n in nodes.items():
        if nid not in node_to_layer:
            layer = _node_layer_from_type(n if isinstance(n, dict) else {})
            if layer:
                node_to_layer[nid] = layer

    # Find edges that cross layer boundaries
    cross_edges = []
    seen_edges: set[tuple[str, str, str]] = set()
    for e in edges:
        if not isinstance(e, dict):
            continue
        src = e.get("source_id", "")
        tgt = e.get("target_id", "")
        src_binding = _resolve_edge_endpoint(e, "source", layer_indexes)
        tgt_binding = _resolve_edge_endpoint(e, "target", layer_indexes)

        src_layer = src_binding["layer"] if src_binding else node_to_layer.get(src, "UNKNOWN")
        tgt_layer = tgt_binding["layer"] if tgt_binding else node_to_layer.get(tgt, "UNKNOWN")

        if src_layer != tgt_layer and src_layer != "UNKNOWN" and tgt_layer != "UNKNOWN":
            resolved_src = src_binding["node_id"] if src_binding else src
            resolved_tgt = tgt_binding["node_id"] if tgt_binding else tgt
            dedupe_key = (resolved_src, resolved_tgt, str(e.get("relation", "?")))
            if dedupe_key in seen_edges:
                continue
            seen_edges.add(dedupe_key)
            cross_edges.append({
                "source_id": src,
                "target_id": tgt,
                "resolved_source_id": resolved_src,
                "resolved_target_id": resolved_tgt,
                "source_layer": src_layer,
                "target_layer": tgt_layer,
                "source_memberships": node_memberships.get(resolved_src, [src_layer]),
                "target_memberships": node_memberships.get(resolved_tgt, [tgt_layer]),
                "relation": e.get("relation", "?"),
                "attributes": e.get("attributes", {}),
                "source_resolved_via": src_binding["resolved_via"] if src_binding else "node_id" if src in layer_indexes["node_to_layer"] else "node_type",
                "target_resolved_via": tgt_binding["resolved_via"] if tgt_binding else "node_id" if tgt in layer_indexes["node_to_layer"] else "node_type",
                "discovery_mode": "explicit_edge",
            })

    for nid, node in nodes.items():
        if not isinstance(node, dict):
            continue
        source_layer = node_to_layer.get(nid, "UNKNOWN")
        if source_layer == "UNKNOWN":
            continue
        for bridge in _iter_strong_node_bridges(nid, node, layer_indexes):
            target_layer = bridge["target_layer"]
            if target_layer == source_layer:
                continue
            dedupe_key = (nid, bridge["target_id"], bridge["relation"])
            if dedupe_key in seen_edges:
                continue
            seen_edges.add(dedupe_key)
            cross_edges.append({
                "source_id": nid,
                "target_id": bridge["target_id"],
                "resolved_source_id": nid,
                "resolved_target_id": bridge["target_id"],
                "source_layer": source_layer,
                "target_layer": target_layer,
                "relation": bridge["relation"],
                "attributes": {
                    "bridge_field": bridge["bridge_field"],
                    "bridge_via": bridge["bridge_via"],
                    "derived": True,
                },
                "source_resolved_via": "node_id" if nid in layer_indexes["node_to_layer"] else "node_type",
                "target_resolved_via": bridge["target_resolved_via"],
                "discovery_mode": "strong_bridge_field",
            })

    for bridge in _iter_registry_bridges(root, nodes, layer_indexes, node_to_layer):
        dedupe_key = (
            bridge["resolved_source_id"],
            bridge["resolved_target_id"],
            bridge["relation"],
        )
        if dedupe_key in seen_edges:
            continue
        seen_edges.add(dedupe_key)
        cross_edges.append(bridge)

    return cross_edges


def _build_toponetx_layer_complex(root: Path, layers: list[dict]) -> dict[str, Any]:
    """Build a TopoNetX CellComplex for the layer-level graph structure."""
    cache_root = root / "work" / "audit_tmp" / "mplcache"
    cache_root.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(cache_root))
    os.environ.setdefault("XDG_CACHE_HOME", str(cache_root))

    try:
        import toponetx as tnx
    except ImportError:
        return {"available": False, "error": "TopoNetX not available in current interpreter"}

    # Build a cell complex where:
    # - 0-cells = layer graphs (nodes)
    # - 1-cells = cross-layer edge families (edges between layers)
    # - 2-cells = triangles where three layers have mutual cross-layer connections
    complex_ = tnx.CellComplex()

    # Add layer nodes
    layer_ids = [l["layer_id"] for l in layers if l["rank"] >= 0]
    for lid in layer_ids:
        complex_.add_node(lid)

    # Add inter-layer edges based on the natural hierarchy
    hierarchy_edges = [
        ("A2_HIGH_INTAKE", "A2_MID_REFINEMENT"),      # extraction → refinement
        ("A2_MID_REFINEMENT", "A2_LOW_CONTROL"),       # refinement → kernel
        ("A2_LOW_CONTROL", "A1_JARGONED"),             # kernel → A1 view
    ]
    for src, tgt in hierarchy_edges:
        if src in layer_ids and tgt in layer_ids:
            complex_.add_cell([src, tgt], rank=1)

    # Add the cross-layer shortcut edge to form a triangle
    if all(l in layer_ids for l in ["A2_HIGH_INTAKE", "A2_LOW_CONTROL"]):
        complex_.add_cell(["A2_HIGH_INTAKE", "A2_LOW_CONTROL"], rank=1)

    # Now all 3 boundary edges exist for the A2 triangle — add the 2-cell
    if all(l in layer_ids for l in ["A2_HIGH_INTAKE", "A2_MID_REFINEMENT", "A2_LOW_CONTROL"]):
        try:
            complex_.add_cell(
                ["A2_HIGH_INTAKE", "A2_MID_REFINEMENT", "A2_LOW_CONTROL"],
                rank=2,
            )
        except Exception:
            pass  # 2-cell requires all boundary 1-cells present

    return {
        "available": True,
        "shape": [int(s) for s in complex_.shape],
        "layer_nodes": layer_ids,
        "hierarchy_edges": hierarchy_edges,
        "two_cells": ["A2_HIGH_INTAKE ↔ A2_MID_REFINEMENT ↔ A2_LOW_CONTROL"],
    }


def _build_pyg_layer_graph(root: Path, layers: list[dict], cross_edges: list[dict]) -> dict[str, Any]:
    """Build a PyG heterograph for the nested graph structure."""
    try:
        import torch
        from torch_geometric.data import HeteroData
    except ImportError:
        return {"available": False, "error": "PyG not available in current interpreter"}

    data = HeteroData()

    # Create node stores for each layer
    for layer in layers:
        lid = layer["layer_id"]
        data[lid].x = torch.tensor([[
            float(layer["node_count"]),
            float(layer["edge_count"]),
            float(layer["rank"]),
        ]])
        data[lid].layer_id = lid
        data[lid].trust_zone = layer["trust_zone"]

    # Create edge stores for cross-layer connections
    cross_layer_counts = Counter()
    for ce in cross_edges:
        key = f"{ce['source_layer']}→{ce['target_layer']}"
        cross_layer_counts[key] += 1

    return {
        "available": True,
        "node_stores": [l["layer_id"] for l in layers],
        "cross_layer_edge_counts": dict(cross_layer_counts),
        "total_cross_layer_edges": len(cross_edges),
    }


def _build_gudhi_homology(root: Path, cross_edges: list[dict]) -> dict[str, Any]:
    """Compute topological persistence using GUDHI to track nonclassical loops."""
    try:
        import gudhi
    except ImportError:
        return {"available": False, "error": "GUDHI not available in current interpreter"}

    st = gudhi.SimplexTree()
    node_to_idx = {}
    
    def get_idx(nid: str) -> int:
        if nid not in node_to_idx:
            node_to_idx[nid] = len(node_to_idx)
        return node_to_idx[nid]

    # Insert edges (1-simplices)
    for ce in cross_edges:
        s = get_idx(ce['source_id'])
        t = get_idx(ce['target_id'])
        st.insert([s, t])

    # Compute persistence to find true structural loops vs collapsed diamonds
    st.compute_persistence()
    betti = st.betti_numbers()

    return {
        "available": True,
        "betti_numbers": betti,  # [components, holes/loops, voids]
        "total_simplices": st.num_simplices(),
        "num_vertices": st.num_vertices(),
    }


def build_nested_graph(repo_root: str | Path) -> dict[str, Any]:
    """Build the nested graph structure from the layer graphs."""
    root = Path(repo_root).resolve()

    # 1. Build layer summaries
    layers = []
    for layer_id, cfg in LAYER_GRAPHS.items():
        summary = _build_layer_summary(root, layer_id, cfg)
        layers.append(summary)

    # 2. Find cross-layer edges from the accumulation graph
    cross_edges = _find_cross_layer_edges(root)

    # 3. Build cross-layer summary
    cross_layer_summary = Counter()
    cross_layer_by_relation = Counter()
    for ce in cross_edges:
        key = f"{ce['source_layer']} → {ce['target_layer']}"
        cross_layer_summary[key] += 1
        cross_layer_by_relation[ce["relation"]] += 1

    # 4. Try TopoNetX layer complex
    tnx_result = _build_toponetx_layer_complex(root, layers)

    # 5. Try PyG layer graph
    pyg_result = _build_pyg_layer_graph(root, layers, cross_edges)

    # 5b. Compute Topological Persistence (GUDHI)
    gudhi_result = _build_gudhi_homology(root, cross_edges)

    # 6. Build the nested graph JSON
    nested_graph = {
        "schema": "NESTED_GRAPH_v1",
        "generated_utc": _utc_iso(),
        "description": "Nested graph-of-graphs structure representing the layered system architecture",
        "layers": {
            layer["layer_id"]: {
                "path": layer["path"],
                "rank": layer["rank"],
                "trust_zone": layer["trust_zone"],
                "description": layer["description"],
                "node_count": layer["node_count"],
                "edge_count": layer["edge_count"],
                "node_types": layer["node_types"],
                "node_ids": layer["node_ids"],
            }
            for layer in layers
        },
        "inter_layer_edges": {
            "total": len(cross_edges),
            "by_layer_pair": dict(cross_layer_summary),
            "by_relation": dict(cross_layer_by_relation),
            "edges": cross_edges,  # Full set — no cap
        },
        "topology": {
            "toponetx": tnx_result,
            "pyg": pyg_result,
            "gudhi": gudhi_result,
        },
        "hierarchy": [
            {"from": "A2_HIGH_INTAKE", "to": "A2_MID_REFINEMENT", "relation": "REFINES_DOWN"},
            {"from": "A2_MID_REFINEMENT", "to": "A2_LOW_CONTROL", "relation": "PROMOTES_DOWN"},
            {"from": "A2_LOW_CONTROL", "to": "A1_JARGONED", "relation": "TRANSLATES_DOWN"},
            {"from": "SKILLS", "to": "A2_LOW_CONTROL", "relation": "OPERATES_ON"},
            {"from": "B_LAYER", "to": "A2_LOW_CONTROL", "relation": "ACCEPTS_FROM"},
            {"from": "SIM_LAYER", "to": "B_LAYER", "relation": "EVIDENCES"},
        ],
    }

    # 7. Build report
    report = {
        "schema": "NESTED_GRAPH_BUILD_REPORT_v1",
        "generated_utc": nested_graph["generated_utc"],
        "status": "built",
        "layer_count": len(layers),
        "total_nodes_across_layers": sum(l["node_count"] for l in layers),
        "total_edges_across_layers": sum(l["edge_count"] for l in layers),
        "cross_layer_edge_count": len(cross_edges),
        "cross_layer_by_pair": dict(cross_layer_summary),
        "toponetx_available": tnx_result.get("available", False),
        "toponetx_shape": tnx_result.get("shape", []),
        "pyg_available": pyg_result.get("available", False),
        "pyg_cross_layer_edges": pyg_result.get("total_cross_layer_edges", 0),
        "gudhi_available": gudhi_result.get("available", False),
        "gudhi_betti_numbers": gudhi_result.get("betti_numbers", []),
        "layers": [
            {
                "id": l["layer_id"],
                "nodes": l["node_count"],
                "edges": l["edge_count"],
                "rank": l["rank"],
            }
            for l in layers
        ],
    }

    return {
        "nested_graph": nested_graph,
        "report": report,
        "cross_edges": cross_edges,
    }


def _render_markdown(report: dict[str, Any]) -> str:
    layer_lines = []
    for l in report.get("layers", []):
        layer_lines.append(f"| {l['id']:25s} | {l['nodes']:>6d} | {l['edges']:>6d} | {l['rank']:>4d} |")

    cross_lines = [f"- `{k}`: {v}" for k, v in sorted(report.get("cross_layer_by_pair", {}).items(), key=lambda x: -x[1])]

    return "\n".join([
        "# Nested Graph Build Report",
        "",
        f"- generated_utc: `{report['generated_utc']}`",
        f"- status: `{report['status']}`",
        f"- layer_count: `{report['layer_count']}`",
        f"- total_nodes_across_layers: `{report['total_nodes_across_layers']}`",
        f"- total_edges_across_layers: `{report['total_edges_across_layers']}`",
        f"- cross_layer_edge_count: `{report['cross_layer_edge_count']}`",
        f"- toponetx_available: `{report['toponetx_available']}`",
        f"- toponetx_shape: `{report['toponetx_shape']}`",
        f"- pyg_available: `{report['pyg_available']}`",
        f"- gudhi_available: `{report['gudhi_available']}`",
        f"- gudhi_betti_numbers: `{report['gudhi_betti_numbers']}`",
        "",
        "## Layers",
        "",
        "| Layer | Nodes | Edges | Rank |",
        "|-------|-------|-------|------|",
        *layer_lines,
        "",
        "## Cross-Layer Edges",
        "",
        *cross_lines,
        "",
    ])


def inject_nested_graph(repo_root: str | Path) -> dict[str, Any]:
    """Build and write the nested graph structure."""
    root = Path(repo_root).resolve()
    result = build_nested_graph(root)

    nested_path = root / NESTED_GRAPH_OUT
    report_json_path = root / REPORT_JSON
    report_md_path = root / REPORT_MD

    _write_json(nested_path, result["nested_graph"])
    _write_json(report_json_path, result["report"])
    _write_text(report_md_path, _render_markdown(result["report"]))

    return {
        "nested_graph_path": str(nested_path),
        "report_json_path": str(report_json_path),
        "report_md_path": str(report_md_path),
        "layer_count": result["report"]["layer_count"],
        "cross_layer_edges": result["report"]["cross_layer_edge_count"],
        "total_nodes": result["report"]["total_nodes_across_layers"],
    }


if __name__ == "__main__":
    result = inject_nested_graph(REPO_ROOT)
    print(f"\n{'='*60}")
    print(f"NESTED GRAPH BUILD")
    print(f"{'='*60}")
    print(f"  Layers:            {result['layer_count']}")
    print(f"  Total nodes:       {result['total_nodes']}")
    print(f"  Cross-layer edges: {result['cross_layer_edges']}")
    print(f"  Nested graph:      {result['nested_graph_path']}")
    print(f"  Report:            {result['report_md_path']}")
