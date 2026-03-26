#!/usr/bin/env python3
"""
QIT Engine Graph Builder
========================
Encodes the GeometricEngine's physical topology directly as a graph layer.

This makes the graphs themselves mirror the QIT engine structure:
  - 8 macro-stages as MACRO_STAGE nodes (per engine type)
  - 4 operators (Ti, Fe, Te, Fi) as OPERATOR nodes
  - 3 nested tori (inner, Clifford, outer) as TORUS nodes
  - 2 engine types (Deductive, Inductive) as ENGINE nodes
  - 7 proven axes as AXIS nodes (Axis 0–6)

Edges encode:
  - SUBCYCLE_ORDER: Ti → Fe → Te → Fi (the fixed internal operator cycle)
  - STAGE_SEQUENCE: macro-stage n → macro-stage n+1
  - TORUS_NESTING: inner → Clifford → outer (Hopf fibration hierarchy)
  - CHIRALITY_COUPLING: Type 1 ↔ Type 2 (complementary dominance)
  - OPERATOR_ACTS_ON: which operator dominates which macro-stage
  - AXIS_GOVERNS: which axis is load-bearing for which macro-stage
  - NEGATIVE_WITNESS: edges to graveyard kills proving each structure is necessary

Output: system_v4/a2_state/graphs/qit_engine_graph_v1.json
"""

from __future__ import annotations

import json
import hashlib
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
GRAPH_DIR = REPO_ROOT / "system_v4" / "a2_state" / "graphs"
OUT_FILE = GRAPH_DIR / "qit_engine_graph_v1.json"


# ── Physical Constants ──

TERRAINS = [
    ("Se_f", "fiber", "expand", "open"),
    ("Si_f", "fiber", "compress", "closed"),
    ("Ne_f", "fiber", "expand", "closed"),
    ("Ni_f", "fiber", "compress", "open"),
    ("Se_b", "base", "expand", "open"),
    ("Si_b", "base", "compress", "closed"),
    ("Ne_b", "base", "expand", "closed"),
    ("Ni_b", "base", "compress", "open"),
]

OPERATORS = [
    ("Ti", "constrain", "Thinking introvert"),
    ("Fe", "release", "Feeling extrovert"),
    ("Te", "explore", "Thinking extrovert"),
    ("Fi", "filter", "Feeling introvert"),
]

TORI = [
    ("inner", 0, "Innermost torus — highest curvature"),
    ("clifford", 1, "Clifford torus — equal radii, flat"),
    ("outer", 2, "Outermost torus — lowest curvature"),
]

ENGINE_TYPES = [
    ("type1_deductive", "Fe/Ti dominant on base, Te/Fi on fiber"),
    ("type2_inductive", "Te/Fi dominant on base, Fe/Ti on fiber"),
]

PROVEN_AXES = [
    ("axis_0", "Identity / entropy gradient", True, "sim_neg_axis0_frozen.py"),
    ("axis_1", "Parity / expansion-compression", True, None),
    ("axis_2", "Scale / dimension-dependent shift", True, None),
    ("axis_3", "Chirality / engine type split", True, None),
    ("axis_4", "Variance direction / information flow", True, None),
    ("axis_5", "Coupling strength / interaction weight", True, None),
    ("axis_6", "Polarity / torus latitude sign", True, "neg_axis6_shared_stage_matrix_sim.py"),
]

NEGATIVE_WITNESSES = [
    ("neg_no_torus_transport", "Removing torus transport kills the engine", "TORUS"),
    ("neg_axis0_frozen", "Freezing Axis 0 kills entropy gradients", "AXIS"),
    ("neg_no_chirality", "Removing engine type distinction kills asymmetry", "CHIRALITY"),
    ("neg_torus_scrambled", "Scrambling torus assignment kills coherence", "TORUS"),
    ("neg_axis6_shared", "Sharing Axis 6 polarity across types kills separation", "AXIS"),
    ("neg_missing_fe", "Removing Fe operator kills the subcycle", "OPERATOR"),
    ("neg_missing_operator", "Removing any single operator kills the subcycle", "OPERATOR"),
    ("neg_native_only", "Using only native operators kills type distinction", "OPERATOR"),
    ("neg_type_flatten", "Flattening engine types kills chirality separation", "CHIRALITY"),
]


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _node_id(prefix: str, name: str) -> str:
    raw = f"{prefix}::{name}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def build_qit_engine_graph() -> dict[str, Any]:
    """Construct the QIT Engine graph layer."""
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []

    # ── 1. MACRO_STAGE nodes (8 per engine type = 16 total) ──
    for etype_id, etype_desc in ENGINE_TYPES:
        for stage_idx, (terrain, loop, mode, boundary) in enumerate(TERRAINS):
            nid = _node_id("MACRO_STAGE", f"{etype_id}_{terrain}")
            nodes[nid] = {
                "node_type": "MACRO_STAGE",
                "label": f"{etype_id}::{terrain}",
                "engine_type": etype_id,
                "terrain": terrain,
                "loop": loop,
                "mode": mode,
                "boundary": boundary,
                "stage_index": stage_idx,
            }

    # ── 2. OPERATOR nodes ──
    for op_name, op_action, op_desc in OPERATORS:
        nid = _node_id("OPERATOR", op_name)
        nodes[nid] = {
            "node_type": "OPERATOR",
            "label": op_name,
            "action": op_action,
            "description": op_desc,
        }

    # ── 3. TORUS nodes ──
    for torus_name, torus_rank, torus_desc in TORI:
        nid = _node_id("TORUS", torus_name)
        nodes[nid] = {
            "node_type": "TORUS",
            "label": torus_name,
            "nesting_rank": torus_rank,
            "description": torus_desc,
        }

    # ── 4. ENGINE nodes ──
    for etype_id, etype_desc in ENGINE_TYPES:
        nid = _node_id("ENGINE", etype_id)
        nodes[nid] = {
            "node_type": "ENGINE",
            "label": etype_id,
            "description": etype_desc,
        }

    # ── 5. AXIS nodes ──
    for axis_id, axis_desc, axis_proven, axis_neg in PROVEN_AXES:
        nid = _node_id("AXIS", axis_id)
        nodes[nid] = {
            "node_type": "AXIS",
            "label": axis_id,
            "description": axis_desc,
            "proven": axis_proven,
            "negative_witness": axis_neg,
        }

    # ── 6. NEGATIVE_WITNESS nodes ──
    for neg_id, neg_desc, neg_target in NEGATIVE_WITNESSES:
        nid = _node_id("NEG_WITNESS", neg_id)
        nodes[nid] = {
            "node_type": "NEG_WITNESS",
            "label": neg_id,
            "description": neg_desc,
            "target_structure": neg_target,
        }

    # ── EDGES ──

    # 6a. SUBCYCLE_ORDER: Ti → Fe → Te → Fi (fixed operator cycle)
    op_order = ["Ti", "Fe", "Te", "Fi"]
    for i in range(len(op_order) - 1):
        edges.append({
            "source_id": _node_id("OPERATOR", op_order[i]),
            "target_id": _node_id("OPERATOR", op_order[i + 1]),
            "relation": "SUBCYCLE_ORDER",
            "attributes": {"position": i, "proven": True},
        })
    # Close the cycle: Fi → Ti
    edges.append({
        "source_id": _node_id("OPERATOR", "Fi"),
        "target_id": _node_id("OPERATOR", "Ti"),
        "relation": "SUBCYCLE_ORDER",
        "attributes": {"position": 3, "closes_cycle": True, "proven": True},
    })

    # 6b. STAGE_SEQUENCE: macro-stage n → n+1 within each engine type
    for etype_id, _ in ENGINE_TYPES:
        for i in range(len(TERRAINS) - 1):
            edges.append({
                "source_id": _node_id("MACRO_STAGE", f"{etype_id}_{TERRAINS[i][0]}"),
                "target_id": _node_id("MACRO_STAGE", f"{etype_id}_{TERRAINS[i+1][0]}"),
                "relation": "STAGE_SEQUENCE",
                "attributes": {"engine_type": etype_id},
            })
        # Close the cycle
        edges.append({
            "source_id": _node_id("MACRO_STAGE", f"{etype_id}_{TERRAINS[-1][0]}"),
            "target_id": _node_id("MACRO_STAGE", f"{etype_id}_{TERRAINS[0][0]}"),
            "relation": "STAGE_SEQUENCE",
            "attributes": {"engine_type": etype_id, "closes_cycle": True},
        })

    # 6c. TORUS_NESTING: inner → Clifford → outer
    for i in range(len(TORI) - 1):
        edges.append({
            "source_id": _node_id("TORUS", TORI[i][0]),
            "target_id": _node_id("TORUS", TORI[i+1][0]),
            "relation": "TORUS_NESTING",
            "attributes": {"direction": "outward"},
        })

    # 6d. ENGINE_OWNS_STAGE: engine → its 8 macro-stages
    for etype_id, _ in ENGINE_TYPES:
        engine_nid = _node_id("ENGINE", etype_id)
        for terrain, _, _, _ in TERRAINS:
            stage_nid = _node_id("MACRO_STAGE", f"{etype_id}_{terrain}")
            edges.append({
                "source_id": engine_nid,
                "target_id": stage_nid,
                "relation": "ENGINE_OWNS_STAGE",
            })

    # 6e. CHIRALITY_COUPLING: Type 1 ↔ Type 2
    edges.append({
        "source_id": _node_id("ENGINE", "type1_deductive"),
        "target_id": _node_id("ENGINE", "type2_inductive"),
        "relation": "CHIRALITY_COUPLING",
        "attributes": {"coupling_type": "complementary_dominance"},
    })

    # 6f. OPERATOR_ACTS_ON: each operator acts on every macro-stage
    for etype_id, _ in ENGINE_TYPES:
        for terrain, _, _, _ in TERRAINS:
            stage_nid = _node_id("MACRO_STAGE", f"{etype_id}_{terrain}")
            for op_name, _, _ in OPERATORS:
                op_nid = _node_id("OPERATOR", op_name)
                edges.append({
                    "source_id": op_nid,
                    "target_id": stage_nid,
                    "relation": "OPERATOR_ACTS_ON",
                    "attributes": {"engine_type": etype_id, "terrain": terrain},
                })

    # 6g. STAGE_ON_TORUS: fiber stages on inner/clifford, base stages on clifford/outer
    for etype_id, _ in ENGINE_TYPES:
        for terrain, loop, _, _ in TERRAINS:
            stage_nid = _node_id("MACRO_STAGE", f"{etype_id}_{terrain}")
            if loop == "fiber":
                torus_nid = _node_id("TORUS", "inner")
            else:
                torus_nid = _node_id("TORUS", "outer")
            edges.append({
                "source_id": stage_nid,
                "target_id": torus_nid,
                "relation": "STAGE_ON_TORUS",
                "attributes": {"loop": loop},
            })
        # Both loops share the Clifford torus
        for terrain, _, _, _ in TERRAINS:
            stage_nid = _node_id("MACRO_STAGE", f"{etype_id}_{terrain}")
            edges.append({
                "source_id": stage_nid,
                "target_id": _node_id("TORUS", "clifford"),
                "relation": "STAGE_ON_TORUS",
                "attributes": {"shared": True},
            })

    # 6h. AXIS_GOVERNS: connect each axis to the engine nodes
    for axis_id, _, _, _ in PROVEN_AXES:
        axis_nid = _node_id("AXIS", axis_id)
        for etype_id, _ in ENGINE_TYPES:
            engine_nid = _node_id("ENGINE", etype_id)
            edges.append({
                "source_id": axis_nid,
                "target_id": engine_nid,
                "relation": "AXIS_GOVERNS",
                "attributes": {"axis": axis_id},
            })

    # 6i. NEGATIVE_PROVES: connect negative witnesses to what they prove
    for neg_id, _, neg_target in NEGATIVE_WITNESSES:
        neg_nid = _node_id("NEG_WITNESS", neg_id)
        if neg_target == "TORUS":
            for torus_name, _, _ in TORI:
                edges.append({
                    "source_id": neg_nid,
                    "target_id": _node_id("TORUS", torus_name),
                    "relation": "NEGATIVE_PROVES",
                    "attributes": {"proves": "structure_is_necessary"},
                })
        elif neg_target == "AXIS":
            for axis_id, _, _, _ in PROVEN_AXES:
                edges.append({
                    "source_id": neg_nid,
                    "target_id": _node_id("AXIS", axis_id),
                    "relation": "NEGATIVE_PROVES",
                    "attributes": {"proves": "axis_is_load_bearing"},
                })
        elif neg_target == "OPERATOR":
            for op_name, _, _ in OPERATORS:
                edges.append({
                    "source_id": neg_nid,
                    "target_id": _node_id("OPERATOR", op_name),
                    "relation": "NEGATIVE_PROVES",
                    "attributes": {"proves": "operator_is_necessary"},
                })
        elif neg_target == "CHIRALITY":
            edges.append({
                "source_id": neg_nid,
                "target_id": _node_id("ENGINE", "type1_deductive"),
                "relation": "NEGATIVE_PROVES",
                "attributes": {"proves": "chirality_separation_is_necessary"},
            })
            edges.append({
                "source_id": neg_nid,
                "target_id": _node_id("ENGINE", "type2_inductive"),
                "relation": "NEGATIVE_PROVES",
                "attributes": {"proves": "chirality_separation_is_necessary"},
            })

    graph = {
        "schema": "QIT_ENGINE_GRAPH_v1",
        "generated_utc": _utc_iso(),
        "description": (
            "Graph encoding of the Geometric Engine's physical topology: "
            "8 macro-stages × 2 engine types, 4 fixed subcycle operators, "
            "3 nested Hopf tori, 7 proven axes, and 9 negative witnesses."
        ),
        "nodes": nodes,
        "edges": edges,
        "summary": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "node_types": {
                "MACRO_STAGE": sum(1 for n in nodes.values() if n["node_type"] == "MACRO_STAGE"),
                "OPERATOR": sum(1 for n in nodes.values() if n["node_type"] == "OPERATOR"),
                "TORUS": sum(1 for n in nodes.values() if n["node_type"] == "TORUS"),
                "ENGINE": sum(1 for n in nodes.values() if n["node_type"] == "ENGINE"),
                "AXIS": sum(1 for n in nodes.values() if n["node_type"] == "AXIS"),
                "NEG_WITNESS": sum(1 for n in nodes.values() if n["node_type"] == "NEG_WITNESS"),
            },
        },
    }

    return graph


def write_qit_engine_graph() -> dict[str, Any]:
    """Build and write the QIT Engine graph layer."""
    graph = build_qit_engine_graph()
    GRAPH_DIR.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
    summary = graph["summary"]
    return {
        "path": str(OUT_FILE),
        "node_count": summary["node_count"],
        "edge_count": summary["edge_count"],
        "node_types": summary["node_types"],
    }


if __name__ == "__main__":
    result = write_qit_engine_graph()
    print(f"\n{'='*60}")
    print(f"QIT ENGINE GRAPH LAYER")
    print(f"{'='*60}")
    print(f"  Nodes: {result['node_count']}")
    print(f"  Edges: {result['edge_count']}")
    for ntype, count in result["node_types"].items():
        print(f"    {ntype}: {count}")
    print(f"  Written to: {result['path']}")
