#!/usr/bin/env python3
"""
QIT Engine Graph Builder (v2)
==============================
Encodes the GeometricEngine's physical topology directly as a graph layer.

v2 changes (Codex P1/P2 audit fixes):
  - Every node carries a stable `public_id` (human-readable, joinable)
  - Every edge carries a stable `edge_id`
  - All nodes validated through Pydantic schemas before emission
  - 64 SUBCYCLE_STEP nodes for the full 16×4 runtime grain
  - Content hash for snapshot provenance
  - Cross-layer reconciliation map for joining to accumulation graph

Output: system_v4/a2_state/graphs/qit_engine_graph_v1.json
"""

from __future__ import annotations

import json
import hashlib
import time
from pathlib import Path
from typing import Any

# Import owner schemas for validation
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from qit_owner_schemas import (
    EngineType, EngineTypeEnum,
    MacroStage, LoopEnum, ModeEnum, BoundaryEnum,
    SubcycleOperator, OperatorEnum, SubcycleStep,
    TorusState, TorusEnum,
    AxisState, NegativeWitness, NegTargetEnum,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
GRAPH_DIR = REPO_ROOT / "system_v4" / "a2_state" / "graphs"
OUT_FILE = GRAPH_DIR / "qit_engine_graph_v1.json"
OWNER_LAYER = "QIT_ENGINE"


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
    ("axis_3", "Engine-family split (Type-1 / Type-2); chirality remains derived/noncanon here", True, None),
    ("axis_4", "Variance direction / information flow", True, None),
    ("axis_5", "Coupling strength / interaction weight", True, None),
    ("axis_6", "Polarity / torus latitude sign", True, "neg_axis6_shared_stage_matrix_sim.py"),
]

# Each negative witness carries: (id, description, target_class, specific_targets_or_None)
# When specific_targets is None, the sim proves something about the ENTIRE class.
# When specific_targets is a list, the sim only proves something about those specific members.
NEGATIVE_WITNESSES: list[tuple[str, str, str, list[str] | None]] = [
    ("neg_no_torus_transport", "Removing torus transport kills the engine", "TORUS", None),  # all tori
    ("neg_axis0_frozen", "Freezing Axis 0 kills entropy gradients", "AXIS", ["axis_0"]),
    ("neg_no_chirality", "Removing engine type distinction kills asymmetry", "CHIRALITY", None),  # both engines
    ("neg_torus_scrambled", "Scrambling torus assignment kills coherence", "TORUS", None),  # all tori
    ("neg_axis6_shared", "Sharing Axis 6 polarity across types kills separation", "AXIS", ["axis_6"]),
    ("neg_missing_fe", "Removing Fe operator kills the subcycle", "OPERATOR", ["Fe"]),
    ("neg_missing_operator", "Removing any single operator kills the subcycle", "OPERATOR", None),  # all operators
    ("neg_native_only", "Using only native operators kills type distinction", "OPERATOR", None),  # all operators
    ("neg_type_flatten", "Flattening engine types kills chirality separation", "CHIRALITY", None),  # both engines
]


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _hash_id(prefix: str, name: str) -> str:
    """Generate a short hash id. Used as dict key, NOT as public identity."""
    raw = f"{prefix}::{name}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _public_id(prefix: str, name: str) -> str:
    """Generate a stable, human-readable, joinable public id."""
    return f"qit::{prefix}::{name}"


def _edge_id(relation: str, source_pub: str, target_pub: str) -> str:
    """Generate a stable edge id from relation + endpoints."""
    raw = f"{relation}::{source_pub}::{target_pub}"
    return hashlib.sha256(raw.encode()).hexdigest()[:20]


def _content_hash(data: dict) -> str:
    """Compute a content hash over the entire graph for provenance."""
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def _make_node(
    prefix: str,
    name: str,
    node_type: str,
    attrs: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    """Create a node with both hash id (dict key) and public_id (joinable)."""
    hid = _hash_id(prefix, name)
    pub = _public_id(prefix, name)
    node = {
        "public_id": pub,
        "node_type": node_type,
        **attrs,
    }
    return hid, node


def _make_edge(
    relation: str,
    source_hid: str,
    target_hid: str,
    source_pub: str,
    target_pub: str,
    attrs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create an edge with stable edge_id and public endpoint refs."""
    return {
        "edge_id": _edge_id(relation, source_pub, target_pub),
        "source_id": source_hid,
        "target_id": target_hid,
        "source_public_id": source_pub,
        "target_public_id": target_pub,
        "relation": relation,
        "attributes": attrs or {},
    }


def build_qit_engine_graph() -> dict[str, Any]:
    """Construct the QIT Engine graph layer with Pydantic-validated nodes."""
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []
    validation_errors: list[str] = []

    # ── 1. ENGINE nodes (Pydantic-validated) ──
    for etype_id, etype_desc in ENGINE_TYPES:
        try:
            model = EngineType(
                engine_type=EngineTypeEnum(etype_id),
                description=etype_desc,
            )
        except Exception as e:
            validation_errors.append(f"ENGINE {etype_id}: {e}")
            continue
        hid, node = _make_node("ENGINE", etype_id, "ENGINE", {
            "label": model.engine_type.value,
            "description": model.description,
        })
        nodes[hid] = node

    # ── 2. MACRO_STAGE nodes (Pydantic-validated) ──
    for etype_id, _ in ENGINE_TYPES:
        for stage_idx, (terrain, loop, mode, boundary) in enumerate(TERRAINS):
            try:
                model = MacroStage(
                    terrain=terrain,
                    engine_type=EngineTypeEnum(etype_id),
                    stage_index=stage_idx,
                    loop=LoopEnum(loop),
                    mode=ModeEnum(mode),
                    boundary=BoundaryEnum(boundary),
                )
            except Exception as e:
                validation_errors.append(f"MACRO_STAGE {etype_id}_{terrain}: {e}")
                continue
            hid, node = _make_node(
                "MACRO_STAGE", f"{etype_id}_{terrain}", "MACRO_STAGE", {
                    "label": f"{etype_id}::{terrain}",
                    "engine_type": model.engine_type.value,
                    "terrain": model.terrain,
                    "loop": model.loop.value,
                    "mode": model.mode.value,
                    "boundary": model.boundary.value,
                    "stage_index": model.stage_index,
                })
            nodes[hid] = node

    # ── 3. OPERATOR nodes (Pydantic-validated) ──
    for op_name, op_action, op_desc in OPERATORS:
        try:
            model = SubcycleOperator(
                operator=OperatorEnum(op_name),
                action=op_action,
            )
        except Exception as e:
            validation_errors.append(f"OPERATOR {op_name}: {e}")
            continue
        hid, node = _make_node("OPERATOR", op_name, "OPERATOR", {
            "label": model.operator.value,
            "action": model.action,
            "description": op_desc,
        })
        nodes[hid] = node

    # ── 4. TORUS nodes (Pydantic-validated) ──
    for torus_name, torus_rank, torus_desc in TORI:
        try:
            model = TorusState(
                torus=TorusEnum(torus_name),
                nesting_rank=torus_rank,
                description=torus_desc,
            )
        except Exception as e:
            validation_errors.append(f"TORUS {torus_name}: {e}")
            continue
        hid, node = _make_node("TORUS", torus_name, "TORUS", {
            "label": model.torus.value,
            "nesting_rank": model.nesting_rank,
            "description": model.description,
        })
        nodes[hid] = node

    # ── 5. AXIS nodes (Pydantic-validated) ──
    for axis_id, axis_desc, axis_proven, axis_neg in PROVEN_AXES:
        try:
            model = AxisState(
                axis_id=axis_id,
                description=axis_desc,
                proven=axis_proven,
                negative_witness_sim=axis_neg,
            )
        except Exception as e:
            validation_errors.append(f"AXIS {axis_id}: {e}")
            continue
        hid, node = _make_node("AXIS", axis_id, "AXIS", {
            "label": model.axis_id,
            "description": model.description,
            "proven": model.proven,
            "negative_witness": model.negative_witness_sim,
        })
        nodes[hid] = node

    # ── 6. NEGATIVE_WITNESS nodes (Pydantic-validated) ──
    for neg_id, neg_desc, neg_target, specific_targets in NEGATIVE_WITNESSES:
        try:
            model = NegativeWitness(
                neg_id=neg_id,
                description=neg_desc,
                target_structure=NegTargetEnum(neg_target),
            )
        except Exception as e:
            validation_errors.append(f"NEG_WITNESS {neg_id}: {e}")
            continue
        hid, node = _make_node("NEG_WITNESS", neg_id, "NEG_WITNESS", {
            "label": model.neg_id,
            "description": model.description,
            "target_structure": model.target_structure.value,
        })
        nodes[hid] = node

    # ── 7. SUBCYCLE_STEP nodes — the 64 operator applications ──
    op_order = ["Ti", "Fe", "Te", "Fi"]
    for etype_id, _ in ENGINE_TYPES:
        for terrain, loop, mode, boundary in TERRAINS:
            for op_idx, op_name in enumerate(op_order):
                step_name = f"{etype_id}_{terrain}_{op_name}"
                try:
                    model = SubcycleStep(
                        operator=OperatorEnum(op_name),
                        stage_terrain=terrain,
                        engine_type=EngineTypeEnum(etype_id),
                        position_in_subcycle=op_idx,
                    )
                except Exception as e:
                    validation_errors.append(f"SUBCYCLE_STEP {step_name}: {e}")
                    continue
                hid, node = _make_node(
                    "SUBCYCLE_STEP", step_name, "SUBCYCLE_STEP", {
                        "label": f"{etype_id}::{terrain}::{op_name}",
                        "engine_type": model.engine_type.value,
                        "terrain": model.stage_terrain,
                        "operator": model.operator.value,
                        "position_in_subcycle": model.position_in_subcycle,
                    })
                nodes[hid] = node

    # ── EDGES ──

    def _h(pfx, nm):
        return _hash_id(pfx, nm)

    def _p(pfx, nm):
        return _public_id(pfx, nm)

    # 8a. SUBCYCLE_ORDER: Ti → Fe → Te → Fi → Ti
    for i in range(len(op_order)):
        src, tgt = op_order[i], op_order[(i + 1) % 4]
        edges.append(_make_edge(
            "SUBCYCLE_ORDER", _h("OPERATOR", src), _h("OPERATOR", tgt),
            _p("OPERATOR", src), _p("OPERATOR", tgt),
            {"position": i, "closes_cycle": i == 3, "proven": True},
        ))

    # 8b. STAGE_SEQUENCE: macro-stage n → n+1 within each engine type
    for etype_id, _ in ENGINE_TYPES:
        for i in range(len(TERRAINS)):
            src_t = TERRAINS[i][0]
            tgt_t = TERRAINS[(i + 1) % len(TERRAINS)][0]
            src_key = f"{etype_id}_{src_t}"
            tgt_key = f"{etype_id}_{tgt_t}"
            edges.append(_make_edge(
                "STAGE_SEQUENCE",
                _h("MACRO_STAGE", src_key), _h("MACRO_STAGE", tgt_key),
                _p("MACRO_STAGE", src_key), _p("MACRO_STAGE", tgt_key),
                {"engine_type": etype_id, "closes_cycle": i == len(TERRAINS) - 1},
            ))

    # 8c. TORUS_NESTING: inner → Clifford → outer
    for i in range(len(TORI) - 1):
        edges.append(_make_edge(
            "TORUS_NESTING",
            _h("TORUS", TORI[i][0]), _h("TORUS", TORI[i + 1][0]),
            _p("TORUS", TORI[i][0]), _p("TORUS", TORI[i + 1][0]),
            {"direction": "outward"},
        ))

    # 8d. ENGINE_OWNS_STAGE
    for etype_id, _ in ENGINE_TYPES:
        for terrain, _, _, _ in TERRAINS:
            stage_key = f"{etype_id}_{terrain}"
            edges.append(_make_edge(
                "ENGINE_OWNS_STAGE",
                _h("ENGINE", etype_id), _h("MACRO_STAGE", stage_key),
                _p("ENGINE", etype_id), _p("MACRO_STAGE", stage_key),
            ))

    # 8e. CHIRALITY_COUPLING
    edges.append(_make_edge(
        "CHIRALITY_COUPLING",
        _h("ENGINE", "type1_deductive"), _h("ENGINE", "type2_inductive"),
        _p("ENGINE", "type1_deductive"), _p("ENGINE", "type2_inductive"),
        {"coupling_type": "complementary_dominance"},
    ))

    # 8f. STEP_IN_STAGE: each SUBCYCLE_STEP belongs to its MACRO_STAGE
    for etype_id, _ in ENGINE_TYPES:
        for terrain, _, _, _ in TERRAINS:
            stage_key = f"{etype_id}_{terrain}"
            for op_name in op_order:
                step_key = f"{etype_id}_{terrain}_{op_name}"
                edges.append(_make_edge(
                    "STEP_IN_STAGE",
                    _h("SUBCYCLE_STEP", step_key), _h("MACRO_STAGE", stage_key),
                    _p("SUBCYCLE_STEP", step_key), _p("MACRO_STAGE", stage_key),
                    {"operator": op_name},
                ))

    # 8g. STEP_USES_OPERATOR: each SUBCYCLE_STEP uses its OPERATOR
    for etype_id, _ in ENGINE_TYPES:
        for terrain, _, _, _ in TERRAINS:
            for op_name in op_order:
                step_key = f"{etype_id}_{terrain}_{op_name}"
                edges.append(_make_edge(
                    "STEP_USES_OPERATOR",
                    _h("SUBCYCLE_STEP", step_key), _h("OPERATOR", op_name),
                    _p("SUBCYCLE_STEP", step_key), _p("OPERATOR", op_name),
                ))

    # 8h. STEP_SEQUENCE: within each stage, Ti→Fe→Te→Fi subcycle ordering
    for etype_id, _ in ENGINE_TYPES:
        for terrain, _, _, _ in TERRAINS:
            for i in range(len(op_order) - 1):
                src_step = f"{etype_id}_{terrain}_{op_order[i]}"
                tgt_step = f"{etype_id}_{terrain}_{op_order[i + 1]}"
                edges.append(_make_edge(
                    "STEP_SEQUENCE",
                    _h("SUBCYCLE_STEP", src_step), _h("SUBCYCLE_STEP", tgt_step),
                    _p("SUBCYCLE_STEP", src_step), _p("SUBCYCLE_STEP", tgt_step),
                    {"position": i},
                ))

    # 8i. STAGE_ON_TORUS: fiber → inner, base → outer, all → clifford
    for etype_id, _ in ENGINE_TYPES:
        for terrain, loop, _, _ in TERRAINS:
            stage_key = f"{etype_id}_{terrain}"
            primary_torus = "inner" if loop == "fiber" else "outer"
            edges.append(_make_edge(
                "STAGE_ON_TORUS",
                _h("MACRO_STAGE", stage_key), _h("TORUS", primary_torus),
                _p("MACRO_STAGE", stage_key), _p("TORUS", primary_torus),
                {"loop": loop, "primary": True},
            ))
            edges.append(_make_edge(
                "STAGE_ON_TORUS",
                _h("MACRO_STAGE", stage_key), _h("TORUS", "clifford"),
                _p("MACRO_STAGE", stage_key), _p("TORUS", "clifford"),
                {"shared": True, "primary": False},
            ))

    # 8j. AXIS_GOVERNS
    for axis_id, _, _, _ in PROVEN_AXES:
        for etype_id, _ in ENGINE_TYPES:
            edges.append(_make_edge(
                "AXIS_GOVERNS",
                _h("AXIS", axis_id), _h("ENGINE", etype_id),
                _p("AXIS", axis_id), _p("ENGINE", etype_id),
                {"axis": axis_id},
            ))

    # 8k. NEGATIVE_PROVES — scoped to specific targets when the sim only proves
    #     something about specific members, not the entire class.
    for neg_id, _, neg_target, specific_targets in NEGATIVE_WITNESSES:
        neg_h = _h("NEG_WITNESS", neg_id)
        neg_p = _p("NEG_WITNESS", neg_id)
        all_targets: list[tuple[str, str, str]] = []
        if neg_target == "TORUS":
            pool = [(t[0],) for t in TORI]
            all_targets = [(_h("TORUS", t[0]), _p("TORUS", t[0]), "structure_is_necessary") for t in pool]
        elif neg_target == "AXIS":
            pool = [(a[0],) for a in PROVEN_AXES]
            all_targets = [(_h("AXIS", a[0]), _p("AXIS", a[0]), "axis_is_load_bearing") for a in pool]
        elif neg_target == "OPERATOR":
            pool = [(o[0],) for o in OPERATORS]
            all_targets = [(_h("OPERATOR", o[0]), _p("OPERATOR", o[0]), "operator_is_necessary") for o in pool]
        elif neg_target == "CHIRALITY":
            all_targets = [
                (_h("ENGINE", "type1_deductive"), _p("ENGINE", "type1_deductive"), "chirality_separation_is_necessary"),
                (_h("ENGINE", "type2_inductive"), _p("ENGINE", "type2_inductive"), "chirality_separation_is_necessary"),
            ]

        # Filter to specific targets if the witness is scoped
        if specific_targets is not None:
            all_targets = [
                (h, p, proves) for h, p, proves in all_targets
                if any(st in p for st in specific_targets)
            ]

        for tgt_h, tgt_p, proves in all_targets:
            scope = "specific" if specific_targets else "class_wide"
            edges.append(_make_edge(
                "NEGATIVE_PROVES", neg_h, tgt_h, neg_p, tgt_p,
                {"proves": proves, "scope": scope},
            ))

    # ── Build public_id index for cross-layer reconciliation ──
    public_id_index = {}
    for hid, node in nodes.items():
        public_id_index[node["public_id"]] = hid

    if validation_errors:
        raise ValueError(
            "QIT owner graph validation failed:\n- " + "\n- ".join(validation_errors)
        )

    # ── Count node / relation types ──
    from collections import Counter
    type_counts = Counter(n["node_type"] for n in nodes.values())
    relation_counts = Counter(e["relation"] for e in edges)
    materialized = bool(nodes)
    build_status = "MATERIALIZED" if materialized else "FAIL_CLOSED"

    graph = {
        "schema": "QIT_ENGINE_GRAPH_v2",
        "generated_utc": _utc_iso(),
        "owner_layer": OWNER_LAYER,
        "materialized": materialized,
        "build_status": build_status,
        "derived_from": {
            "builder_program": str(Path(__file__).resolve()),
            "owner_schemas": str(REPO_ROOT / "system_v4" / "skills" / "qit_owner_schemas.py"),
        },
        "selection_contract": {
            "included_node_rule": (
                "Materialize only the explicit QIT owner structures enumerated in this "
                "builder: engine types, macro-stages, fixed operators, torus identities, "
                "proven axes, negative witnesses, and 64 subcycle steps. Do not infer "
                "runtime state, history/evidence, Weyl branches, or sidecar payloads."
            ),
            "edge_rule": (
                "Materialize only the explicitly constructed edges in this builder: "
                "structural topology edges between emitted owner nodes plus bounded "
                "NEGATIVE_PROVES witness edges. Do not infer extra relations from "
                "simulations, sidecars, or documentation."
            ),
            "validation_gate": (
                "Each emitted node must pass its owner-schema Pydantic model before the "
                "graph is materialized. Validation failures fail the build rather than "
                "emitting partial owner truth."
            ),
            "bridge_policy": (
                "public_id/public_id_index are stable join handles only. Cross-layer "
                "integration requires explicit bridge admission outside this owner builder."
            ),
        },
        "description": (
            "Owner graph encoding of the Geometric Engine's structural topology plus "
            "bounded negative-witness nodes/edges: "
            "8 macro-stages × 2 engine types, 4 fixed subcycle operators, "
            "64 subcycle steps (16×4 runtime grain), "
            "3 nested Hopf tori, 7 proven axes, and 9 negative witnesses. "
            "All nodes carry stable public_id for cross-layer joining."
        ),
        "nodes": nodes,
        "edges": edges,
        "public_id_index": public_id_index,
        "summary": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "node_types": dict(type_counts),
            "relation_types": dict(relation_counts),
            "validation_errors": [],
        },
    }

    # Compute content hash AFTER building (but before writing timestamp)
    content_for_hash = {k: v for k, v in graph.items() if k != "generated_utc"}
    graph["content_hash"] = _content_hash(content_for_hash)

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
        "content_hash": graph["content_hash"],
        "validation_errors": summary["validation_errors"],
    }


if __name__ == "__main__":
    result = write_qit_engine_graph()
    print(f"\n{'='*60}")
    print(f"QIT ENGINE GRAPH LAYER (v2)")
    print(f"{'='*60}")
    print(f"  Nodes: {result['node_count']}")
    print(f"  Edges: {result['edge_count']}")
    for ntype, count in result["node_types"].items():
        print(f"    {ntype}: {count}")
    print(f"  Content hash: {result['content_hash'][:16]}...")
    if result["validation_errors"]:
        print(f"  VALIDATION ERRORS: {len(result['validation_errors'])}")
        for err in result["validation_errors"]:
            print(f"    ⚠ {err}")
    else:
        print(f"  Pydantic validation: ALL PASSED ✓")
    print(f"  Written to: {result['path']}")
