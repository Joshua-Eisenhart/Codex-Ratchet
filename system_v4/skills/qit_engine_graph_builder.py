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
    SpinorEnum, TerrainFamilyEnum, TerrainNameEnum,
    SubcycleOperator, OperatorEnum, SubcycleStep,
    TorusState, TorusEnum,
    WeylBranch, WeylEnum,
    AxisState, NegativeWitness, NegTargetEnum,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
GRAPH_DIR = REPO_ROOT / "system_v4" / "a2_state" / "graphs"
OUT_FILE = GRAPH_DIR / "qit_engine_graph_v1.json"
OWNER_LAYER = "QIT_ENGINE"


# ── Physical Constants ──

# Terrain ordering is engine-type-dependent (loop-order class, Axis-4).
# Source of truth: TERRAIN_MATH_LEDGER_v1.md Section 6 (Loop Order Definitions).
#
# O_ded = (Se, Ne, Ni, Si)   O_ind = (Se, Si, Ni, Ne)
# Type-1 inner = IND → Se, Si, Ni, Ne   (stage_index 0–3)
# Type-1 outer = DED → Se, Ne, Ni, Si   (stage_index 4–7)
# Type-2 inner = DED → Se, Ne, Ni, Si   (stage_index 0–3)
# Type-2 outer = IND → Se, Si, Ni, Ne   (stage_index 4–7)
#
# Each entry: (code, loop, mode, boundary, terrain_family, loop_order, loop_label)
TERRAINS_BY_ENGINE: dict[str, list] = {
    "type1": [
        # Inductive inner (γ_f^L): Se, Si, Ni, Ne
        ("Se_f", "fiber", "expand",   "open",   "Se", "inductive", "Type-1 Engine Inductive Inner Loop"),
        ("Si_f", "fiber", "compress", "closed", "Si", "inductive", "Type-1 Engine Inductive Inner Loop"),
        ("Ni_f", "fiber", "compress", "open",   "Ni", "inductive", "Type-1 Engine Inductive Inner Loop"),
        ("Ne_f", "fiber", "expand",   "closed", "Ne", "inductive", "Type-1 Engine Inductive Inner Loop"),
        # Deductive outer (γ_b^L): Se, Ne, Ni, Si
        ("Se_b", "base",  "expand",   "open",   "Se", "deductive", "Type-1 Engine Deductive Outer Loop"),
        ("Ne_b", "base",  "expand",   "closed", "Ne", "deductive", "Type-1 Engine Deductive Outer Loop"),
        ("Ni_b", "base",  "compress", "open",   "Ni", "deductive", "Type-1 Engine Deductive Outer Loop"),
        ("Si_b", "base",  "compress", "closed", "Si", "deductive", "Type-1 Engine Deductive Outer Loop"),
    ],
    "type2": [
        # Deductive inner (γ_f^R): Se, Ne, Ni, Si
        ("Se_f", "fiber", "expand",   "open",   "Se", "deductive", "Type-2 Engine Deductive Inner Loop"),
        ("Ne_f", "fiber", "expand",   "closed", "Ne", "deductive", "Type-2 Engine Deductive Inner Loop"),
        ("Ni_f", "fiber", "compress", "open",   "Ni", "deductive", "Type-2 Engine Deductive Inner Loop"),
        ("Si_f", "fiber", "compress", "closed", "Si", "deductive", "Type-2 Engine Deductive Inner Loop"),
        # Inductive outer (γ_b^R): Se, Si, Ni, Ne
        ("Se_b", "base",  "expand",   "open",   "Se", "inductive", "Type-2 Engine Inductive Outer Loop"),
        ("Si_b", "base",  "compress", "closed", "Si", "inductive", "Type-2 Engine Inductive Outer Loop"),
        ("Ni_b", "base",  "compress", "open",   "Ni", "inductive", "Type-2 Engine Inductive Outer Loop"),
        ("Ne_b", "base",  "expand",   "closed", "Ne", "inductive", "Type-2 Engine Inductive Outer Loop"),
    ],
}

# Terrain name and generator by (engine_type, terrain_family).
# Source of truth: TERRAIN_MATH_LEDGER_v1.md Section 5 (Structural Lock).
_TERRAIN_NAME_BY_ENGINE: dict[tuple, str] = {
    ("type1", "Se"): "Funnel",  ("type1", "Ne"): "Vortex",
    ("type1", "Ni"): "Pit",     ("type1", "Si"): "Hill",
    ("type2", "Se"): "Cannon",  ("type2", "Ne"): "Spiral",
    ("type2", "Ni"): "Source",  ("type2", "Si"): "Citadel",
}
_GENERATOR_BY_ENGINE: dict[tuple, str] = {
    ("type1", "Se"): "X_F^L",    ("type1", "Ne"): "X_V^L",
    ("type1", "Ni"): "X_P^L",    ("type1", "Si"): "X_H^L",
    ("type2", "Se"): "X_C^R",    ("type2", "Ne"): "X_S^R",
    ("type2", "Ni"): "X_{So}^R", ("type2", "Si"): "X_{Ci}^R",
}

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

# Engine types match EngineTypeEnum.TYPE1 / TYPE2 values.
# Spinor assignment: type1 → Left Weyl (H_L = +n·σ), type2 → Right Weyl (H_R = −n·σ).
ENGINE_TYPES = [
    ("type1", "Type-1: Left Weyl spinor, H_L = +n·σ, Bloch law ṙ_L = +2n×r_L"),
    ("type2", "Type-2: Right Weyl spinor, H_R = −n·σ, Bloch law ṙ_R = −2n×r_R"),
]

PROVEN_AXES = [
    # Descriptions aligned to AXES_0_12_MASTER.md (DATE: 2026-03-25, AUTHORITY: CANON OVERLAY)
    # and AXES_MASTER_SPEC_v0.2.md (DATE: 2026-02-02, AUTHORITY: CANON).
    ("axis_0", "Polarity: base state moderator — admissible/non-admissible subsets (gradient_up / gradient_down)", True, "sim_neg_axis0_frozen.py"),
    ("axis_1", "Topology4 boundary openness: open system (CPTP/Lindblad families) vs closed system (unitary families)", True, None),
    ("axis_2", "Topology4 radial accessibility: expand (larger equivalence classes) vs compress (smaller equivalence classes)", True, None),
    ("axis_3", "Engine-family split: Type-1 (inward, Left Weyl H_L=+n·σ) vs Type-2 (outward, Right Weyl H_R=−n·σ). Physical chirality overlays noncanon — see AXIS3_HYPOTHESES.md", True, None),
    ("axis_4", "Thermodynamic path: Deductive (FeTi — S→0, sequence constraint) vs Inductive (TeFi — ΔW→max, sequence drive)", True, None),
    ("axis_5", "Generator algebra: Line/TeTi (differentiation, Gradient+DiracDelta, discrete boundary) vs Wave/FeFi (integration, Laplacian+Fourier, continuous field)", True, None),
    ("axis_6", "Precedence / composition sidedness: UP vs DOWN (left-action Aρ vs right-action ρA)", True, "neg_axis6_shared_stage_matrix_sim.py"),
]

# Each negative witness carries:
#   (id, description, target_class, specific_targets, owner_edge_emission, proves_label)
# We only emit owner proof edges when there is a faithful owner-level target.
NEGATIVE_WITNESSES: list[tuple[str, str, str, list[str], str, str]] = [
    (
        "neg_no_torus_transport",
        "Removing torus transport kills the engine",
        "TORUS",
        [],
        "suppressed_pending_owner_concept",
        "torus_transport_regime_is_necessary",
    ),
    (
        "neg_axis0_frozen",
        "Freezing Axis 0 kills entropy gradients",
        "AXIS",
        ["axis_0"],
        "specific_targets",
        "axis_0_entropy_gradient_is_load_bearing",
    ),
    (
        "neg_no_chirality",
        "Removing engine type distinction kills asymmetry",
        "CHIRALITY",
        ["type1", "type2"],
        "specific_targets",
        "engine_type_asymmetry_is_necessary",
    ),
    (
        "neg_torus_scrambled",
        "Scrambling torus assignment kills coherence",
        "TORUS",
        [],
        "suppressed_pending_owner_concept",
        "torus_assignment_coherence_is_necessary",
    ),
    (
        "neg_axis6_shared",
        "Sharing Axis 6 polarity across types kills separation",
        "AXIS",
        ["axis_6"],
        "specific_targets",
        "axis_6_polarity_is_load_bearing",
    ),
    (
        "neg_missing_fe",
        "Removing Fe operator kills the subcycle",
        "OPERATOR",
        ["Fe"],
        "specific_targets",
        "fe_member_is_load_bearing",
    ),
    (
        "neg_missing_operator",
        "Removing any single operator kills the subcycle",
        "OPERATOR",
        ["Ti", "Fe", "Te", "Fi"],
        "per_member_sweep",
        "operator_member_is_load_bearing",
    ),
    (
        "neg_native_only",
        "Using only native operators kills type distinction",
        "OPERATOR",
        [],
        "suppressed_pending_owner_concept",
        "mixed_operator_regime_is_necessary",
    ),
    (
        "neg_type_flatten",
        "Flattening engine types kills chirality separation",
        "CHIRALITY",
        ["type1", "type2"],
        "specific_targets",
        "type_specific_weighting_is_necessary",
    ),
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
    # Stage ordering is engine-type-dependent (see TERRAINS_BY_ENGINE).
    _SPINOR = {"type1": SpinorEnum.LEFT, "type2": SpinorEnum.RIGHT}
    _HAMSIGN = {"type1": +1, "type2": -1}
    for etype_id, _ in ENGINE_TYPES:
        spinor = _SPINOR[etype_id]
        ham_sign = _HAMSIGN[etype_id]
        for stage_idx, (terrain, loop, mode, boundary, tfamily, loop_order, loop_label) in enumerate(TERRAINS_BY_ENGINE[etype_id]):
            key = (etype_id, tfamily)
            tname = _TERRAIN_NAME_BY_ENGINE[key]
            gen = _GENERATOR_BY_ENGINE[key]
            try:
                model = MacroStage(
                    terrain=terrain,
                    engine_type=EngineTypeEnum(etype_id),
                    stage_index=stage_idx,
                    loop=LoopEnum(loop),
                    mode=ModeEnum(mode),
                    boundary=BoundaryEnum(boundary),
                    spinor_type=spinor,
                    terrain_family=TerrainFamilyEnum(tfamily),
                    terrain_name=TerrainNameEnum(tname),
                    hamiltonian_sign=ham_sign,
                    generator=gen,
                )
            except Exception as e:
                validation_errors.append(f"MACRO_STAGE {etype_id}_{terrain}: {e}")
                continue
            hid, node = _make_node(
                "MACRO_STAGE", f"{etype_id}_{terrain}", "MACRO_STAGE", {
                    "label": f"{etype_id}::{terrain}",
                    "engine_type": model.engine_type.value,
                    "terrain": model.terrain,
                    "terrain_family": model.terrain_family.value,
                    "terrain_name": model.terrain_name.value,
                    "loop": model.loop.value,
                    "loop_order": loop_order,
                    "loop_label": loop_label,
                    "mode": model.mode.value,
                    "boundary": model.boundary.value,
                    "stage_index": model.stage_index,
                    "spinor_type": model.spinor_type.value,
                    "hamiltonian_sign": model.hamiltonian_sign,
                    "generator": model.generator,
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

    # ── 5. WEYL_BRANCH nodes (Pydantic-validated) ──
    for branch_id, branch_desc, engine_type, spinor_type, ham_sign in [
        ("left", "Left Weyl spinor branch carried by the Type-1 engine family.", "type1", "L", +1),
        ("right", "Right Weyl spinor branch carried by the Type-2 engine family.", "type2", "R", -1),
    ]:
        try:
            model = WeylBranch(
                branch=WeylEnum(branch_id),
                description=branch_desc,
            )
        except Exception as e:
            validation_errors.append(f"WEYL_BRANCH {branch_id}: {e}")
            continue
        hid, node = _make_node("WEYL_BRANCH", branch_id, "WEYL_BRANCH", {
            "label": model.branch.value,
            "description": model.description,
            "engine_type": engine_type,
            "spinor_type": spinor_type,
            "hamiltonian_sign": ham_sign,
        })
        nodes[hid] = node

    # ── 6. AXIS nodes (Pydantic-validated) ──
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

    # ── 7. NEGATIVE_WITNESS nodes (Pydantic-validated) ──
    for neg_id, neg_desc, neg_target, specific_targets, owner_edge_emission, proves_label in NEGATIVE_WITNESSES:
        try:
            model = NegativeWitness(
                neg_id=neg_id,
                description=neg_desc,
                target_structure=NegTargetEnum(neg_target),
                specific_targets=list(specific_targets),
                owner_edge_emission=owner_edge_emission,
                proves_label=proves_label,
            )
        except Exception as e:
            validation_errors.append(f"NEG_WITNESS {neg_id}: {e}")
            continue
        hid, node = _make_node("NEG_WITNESS", neg_id, "NEG_WITNESS", {
            "label": model.neg_id,
            "description": model.description,
            "target_structure": model.target_structure.value,
            "specific_targets": model.specific_targets,
            "owner_edge_emission": model.owner_edge_emission,
            "proves_label": model.proves_label,
        })
        nodes[hid] = node

    # ── 8. SUBCYCLE_STEP nodes — the 64 operator applications ──
    op_order = ["Ti", "Fe", "Te", "Fi"]
    for etype_id, _ in ENGINE_TYPES:
        for terrain, loop, mode, boundary, *_ in TERRAINS_BY_ENGINE[etype_id]:
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

    # 8a. ENGINE_REALIZES_WEYL_BRANCH
    for engine_id, branch_id in [("type1", "left"), ("type2", "right")]:
        edges.append(_make_edge(
            "ENGINE_REALIZES_WEYL_BRANCH",
            _h("ENGINE", engine_id), _h("WEYL_BRANCH", branch_id),
            _p("ENGINE", engine_id), _p("WEYL_BRANCH", branch_id),
            {"engine_type": engine_id, "branch": branch_id},
        ))

    # 8b. SUBCYCLE_ORDER: Ti → Fe → Te → Fi → Ti
    for i in range(len(op_order)):
        src, tgt = op_order[i], op_order[(i + 1) % 4]
        edges.append(_make_edge(
            "SUBCYCLE_ORDER", _h("OPERATOR", src), _h("OPERATOR", tgt),
            _p("OPERATOR", src), _p("OPERATOR", tgt),
            {"position": i, "closes_cycle": i == 3, "proven": True},
        ))

    # 8c. STAGE_SEQUENCE: macro-stage n → n+1 within each engine type
    for etype_id, _ in ENGINE_TYPES:
        terrains_e = TERRAINS_BY_ENGINE[etype_id]
        for i in range(len(terrains_e)):
            src_t = terrains_e[i][0]
            tgt_t = terrains_e[(i + 1) % len(terrains_e)][0]
            src_key = f"{etype_id}_{src_t}"
            tgt_key = f"{etype_id}_{tgt_t}"
            edges.append(_make_edge(
                "STAGE_SEQUENCE",
                _h("MACRO_STAGE", src_key), _h("MACRO_STAGE", tgt_key),
                _p("MACRO_STAGE", src_key), _p("MACRO_STAGE", tgt_key),
                {"engine_type": etype_id, "closes_cycle": i == len(terrains_e) - 1},
            ))

    # 8d. TORUS_NESTING: inner → Clifford → outer
    for i in range(len(TORI) - 1):
        edges.append(_make_edge(
            "TORUS_NESTING",
            _h("TORUS", TORI[i][0]), _h("TORUS", TORI[i + 1][0]),
            _p("TORUS", TORI[i][0]), _p("TORUS", TORI[i + 1][0]),
            {"direction": "outward"},
        ))

    # 8e. ENGINE_OWNS_STAGE
    for etype_id, _ in ENGINE_TYPES:
        for terrain, *_ in TERRAINS_BY_ENGINE[etype_id]:
            stage_key = f"{etype_id}_{terrain}"
            edges.append(_make_edge(
                "ENGINE_OWNS_STAGE",
                _h("ENGINE", etype_id), _h("MACRO_STAGE", stage_key),
                _p("ENGINE", etype_id), _p("MACRO_STAGE", stage_key),
            ))

    # 8f. CHIRALITY_COUPLING
    edges.append(_make_edge(
        "CHIRALITY_COUPLING",
        _h("ENGINE", "type1"), _h("ENGINE", "type2"),
        _p("ENGINE", "type1"), _p("ENGINE", "type2"),
        {"coupling_type": "complementary_dominance"},
    ))

    # 8g. STEP_IN_STAGE: each SUBCYCLE_STEP belongs to its MACRO_STAGE
    for etype_id, _ in ENGINE_TYPES:
        for terrain, *_ in TERRAINS_BY_ENGINE[etype_id]:
            stage_key = f"{etype_id}_{terrain}"
            for op_name in op_order:
                step_key = f"{etype_id}_{terrain}_{op_name}"
                edges.append(_make_edge(
                    "STEP_IN_STAGE",
                    _h("SUBCYCLE_STEP", step_key), _h("MACRO_STAGE", stage_key),
                    _p("SUBCYCLE_STEP", step_key), _p("MACRO_STAGE", stage_key),
                    {"operator": op_name},
                ))

    # 8h. STEP_USES_OPERATOR: each SUBCYCLE_STEP uses its OPERATOR
    for etype_id, _ in ENGINE_TYPES:
        for terrain, *_ in TERRAINS_BY_ENGINE[etype_id]:
            for op_name in op_order:
                step_key = f"{etype_id}_{terrain}_{op_name}"
                edges.append(_make_edge(
                    "STEP_USES_OPERATOR",
                    _h("SUBCYCLE_STEP", step_key), _h("OPERATOR", op_name),
                    _p("SUBCYCLE_STEP", step_key), _p("OPERATOR", op_name),
                ))

    # 8i. STEP_SEQUENCE: within each stage, Ti→Fe→Te→Fi subcycle ordering
    for etype_id, _ in ENGINE_TYPES:
        terrains_e = TERRAINS_BY_ENGINE[etype_id]
        for t_idx, (terrain, *_) in enumerate(terrains_e):
            for i in range(len(op_order) - 1):
                src_step = f"{etype_id}_{terrain}_{op_order[i]}"
                tgt_step = f"{etype_id}_{terrain}_{op_order[i + 1]}"
                edges.append(_make_edge(
                    "STEP_SEQUENCE",
                    _h("SUBCYCLE_STEP", src_step), _h("SUBCYCLE_STEP", tgt_step),
                    _p("SUBCYCLE_STEP", src_step), _p("SUBCYCLE_STEP", tgt_step),
                    {"position": i},
                ))
            # Cross-boundary sequence link: Fi of current stage to Ti of next stage
            next_terrain = terrains_e[(t_idx + 1) % len(terrains_e)][0]
            src_boundary = f"{etype_id}_{terrain}_{op_order[-1]}"
            tgt_boundary = f"{etype_id}_{next_terrain}_{op_order[0]}"
            edges.append(_make_edge(
                "STEP_SEQUENCE",
                _h("SUBCYCLE_STEP", src_boundary), _h("SUBCYCLE_STEP", tgt_boundary),
                _p("SUBCYCLE_STEP", src_boundary), _p("SUBCYCLE_STEP", tgt_boundary),
                {"position": 3, "boundary_transition": True},
            ))

    # 8j. STAGE_ON_TORUS: fiber → inner, base → outer, all → clifford
    for etype_id, _ in ENGINE_TYPES:
        for terrain, loop, *_ in TERRAINS_BY_ENGINE[etype_id]:
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

    # 8k. AXIS_GOVERNS
    for axis_id, _, _, _ in PROVEN_AXES:
        for etype_id, _ in ENGINE_TYPES:
            edges.append(_make_edge(
                "AXIS_GOVERNS",
                _h("AXIS", axis_id), _h("ENGINE", etype_id),
                _p("AXIS", axis_id), _p("ENGINE", etype_id),
                {"axis": axis_id},
            ))

    # 8l. NEGATIVE_PROVES — only emit owner proof edges when the witness names
    #     a faithful owner-level target. Relation/transport witnesses remain
    #     represented by the NEG_WITNESS node until a better owner concept exists.
    for neg_id, _, neg_target, specific_targets, owner_edge_emission, proves_label in NEGATIVE_WITNESSES:
        neg_h = _h("NEG_WITNESS", neg_id)
        neg_p = _p("NEG_WITNESS", neg_id)
        if owner_edge_emission == "suppressed_pending_owner_concept":
            continue

        targets: list[tuple[str, str]] = []
        if neg_target == "TORUS":
            targets = [(_h("TORUS", torus_id), _p("TORUS", torus_id)) for torus_id in specific_targets]
        elif neg_target == "AXIS":
            targets = [(_h("AXIS", axis_id), _p("AXIS", axis_id)) for axis_id in specific_targets]
        elif neg_target == "OPERATOR":
            targets = [(_h("OPERATOR", operator_id), _p("OPERATOR", operator_id)) for operator_id in specific_targets]
        elif neg_target == "CHIRALITY":
            targets = [(_h("ENGINE", engine_id), _p("ENGINE", engine_id)) for engine_id in specific_targets]

        for tgt_h, tgt_p in targets:
            edges.append(_make_edge(
                "NEGATIVE_PROVES", neg_h, tgt_h, neg_p, tgt_p,
                {
                    "proves": proves_label,
                    "scope": owner_edge_emission,
                },
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
                "Weyl branches, proven axes, negative witnesses, and 64 subcycle steps. "
                "Do not infer runtime state, history/evidence, or sidecar payloads."
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
            "3 nested Hopf tori, 2 Weyl branches, 7 proven axes, and 9 negative witnesses. "
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
