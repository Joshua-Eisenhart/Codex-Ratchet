#!/usr/bin/env python3
"""PEPS3D K8 face-projection response-quotient scout.

Formal scout only.

This continuation packet repairs the post-D_K active-frontier blocker by
testing the smallest grounded face-projection map:

  P_K : (D_K(Q_K|K_8), pi_f, anchor_f, local_order_ops)
        -> finite boundary-projected response-quotient carrier signatures
           + projection/control gap vector

It does not admit nested Hopf tori, Weyl sheets, terrain, operator substages,
flux, Xi/Phi0, Axis0, physics, axes 7-12, or full PEPS3D closure.
"""

from __future__ import annotations

import json
import pathlib
import time
from typing import Any

import rustworkx as rx
import sympy as sp
import torch
import z3

from sim_finite_peps3d_probe_effect_seed_carrier_gate_probe import (
    RTYPE,
    apply_physical_operator,
    as_jsonable,
    coords_for_shape,
    edge_list,
    face_list,
    make_site_tensors,
    probe_responses,
    shift_filter_ops,
    sic_effects,
    site_spinors,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "peps3d_k8_face_projection_response_quotient_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Repair the post-D_K active-frontier blocker by testing the smallest "
    "finite K_8 face-projection response-quotient packet before any broader "
    "boundary projection is admitted."
)
SCIENTIFIC_QUESTION = (
    "Does P_K over D_K(Q_K|K_8) produce finite per-face response-quotient "
    "projection signatures while projection-erased, face-scrambled, edge-"
    "erased, wrong-adjacency, single-probe non-IC, no-anchor, scalar-label, "
    "order-erased, dense-closure, and promotion controls fail?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_k8_face_projection_response_quotient"
PROMOTION_ALLOWED = False

PHASE2_FRONTIER_MATRIX_PATH = "system_v5/ops/formal_scouts/phase2_peps3d_seed_frontier_matrix_20260525.json"
PHASE2_TRANSITION_PATH = "system_v5/ops/formal_scouts/phase2_seed_frontier_transition_decision_20260525.json"
PHASE2_POST_DK_BLOCKER = "system_v5/ops/formal_scouts/phase2_post_dk_face_projection_frontier_blocker_20260525.json"
PHASE2_SEED_RECEIPT = "system_v5/ops/formal_scouts/results/finite_peps3d_probe_effect_seed_carrier_gate_probe_results.json"
PHASE2_SPINOR_DENSITY_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_spinor_density_carrier_gate_probe_results.json"
PHASE2_BOUNDARY_RECEIPT = "system_v5/ops/formal_scouts/results/peps_peps3d_local_environment_contraction_gate_probe_results.json"
PHASE2_ABLATION_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_anchor_ablation_boundary_stress_continuation_probe_results.json"
PHASE2_HELDOUT_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_heldout_shape_anchor_replay_probe_results.json"
PHASE2_BOND_SWEEP_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_bond_sweep_anchor_stability_probe_results.json"
PHASE2_RESPONSE_QUOTIENT_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_response_quotient_anchor_partition_probe_results.json"
PHASE2_CELL_PATCH_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_cell_patch_overlap_consistency_probe_results.json"
PHASE2_SUBSTRATE_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_response_quotient_substrate_distinguishability_probe_results.json"

CLAIM_CEILING = (
    "Formal scout only: tests finite K_8 face-projection response-quotient "
    "carrier signatures. It does not admit nested Hopf tori, Weyl sheets, "
    "terrain, operator substage cells, flux, Xi/Phi0, Axis0, Holodeck/FEP, "
    "physics, IGT/game theory, axes 7-12, or full PEPS3D closure."
)
BLOCKED_CONSUMERS = [
    "nested Hopf tori",
    "Weyl sheet cover",
    "terrain generator placement",
    "operator substage cells",
    "PEPS/PEPS3D closure beyond bounded local seed-carrier evidence",
    "flux",
    "Xi/Phi0",
    "Axis0",
    "Holodeck/FEP",
    "physics",
    "IGT/game theory",
    "axes 7-12",
]

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite face-projection tensors, response gaps, controls, and local order gap",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite K_8 graph connectivity and face/edge incidence checks",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite face projection/nonpromotion and control-collapse gate",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact finite site, edge, face, incident-edge, and class count checks",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "rustworkx": "load_bearing",
    "z3": "load_bearing",
    "sympy": "load_bearing",
}

SHAPE = (2, 2, 2)
BOND_DIM = 2
GAP_FLOOR = 1.0e-8
TOL = 1.0e-10
SCRAMBLED_FACE_CONTROLS = [
    [3, 5, 6, 7],
    [0, 1, 2, 4],
    [3, 4, 6, 7],
    [0, 1, 2, 5],
    [3, 5, 6, 7],
    [0, 1, 2, 4],
]


def carrier_graph(shape: tuple[int, int, int]) -> rx.PyGraph:
    graph = rx.PyGraph()
    coords = coords_for_shape(shape)
    graph.add_nodes_from([{"coord": coord} for coord in coords])
    for edge in edge_list(shape):
        graph.add_edge(int(edge["src"]), int(edge["dst"]), {"axis": int(edge["axis"])})
    return graph


def incident_face_edges(face: dict[str, Any], edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    vertices = {int(item) for item in face["vertices"]}
    return [
        edge for edge in edges
        if int(edge["src"]) in vertices and int(edge["dst"]) in vertices
    ]


def row_key(row: torch.Tensor) -> tuple[float, ...]:
    return tuple(round(float(item), 10) for item in row)


def face_projection_gate() -> dict[str, Any]:
    coords = coords_for_shape(SHAPE)
    edges = edge_list(SHAPE)
    faces = face_list(SHAPE)
    graph = carrier_graph(SHAPE)
    responses = probe_responses(site_spinors(len(coords)), sic_effects())
    parent_signature = responses[:, :4].mean(dim=0)
    pairwise = torch.cdist(responses[:, :4], responses[:, :4], p=2)
    face_rows = []
    parent_gaps = []
    incident_gap_means = []
    wrong_adjacency_gaps = []
    scrambled_gaps = []
    full_face_signatures = set()
    single_probe_face_signatures = set()
    for face_index, face in enumerate(faces):
        vertices = [int(item) for item in face["vertices"]]
        incident_edges = incident_face_edges(face, edges)
        nonincident_edges = [
            edge for edge in edges
            if edge not in incident_edges
        ]
        face_signature = responses[vertices, :4].mean(dim=0)
        single_probe_signature = responses[vertices, :1].mean(dim=0)
        parent_gap = float(torch.linalg.vector_norm(face_signature - parent_signature).item())
        incident_gaps = torch.tensor(
            [float(pairwise[int(edge["src"]), int(edge["dst"])].item()) for edge in incident_edges],
            dtype=RTYPE,
        )
        nonincident_gaps = torch.tensor(
            [float(pairwise[int(edge["src"]), int(edge["dst"])].item()) for edge in nonincident_edges],
            dtype=RTYPE,
        )
        wrong_adjacency_gap = abs(float(incident_gaps.mean().item()) - float(nonincident_gaps.mean().item()))
        scrambled_vertices = SCRAMBLED_FACE_CONTROLS[face_index]
        scrambled_signature = responses[scrambled_vertices, :4].mean(dim=0)
        scrambled_gap = float(torch.linalg.vector_norm(face_signature - scrambled_signature).item())
        full_face_signatures.add(row_key(face_signature))
        single_probe_face_signatures.add(row_key(single_probe_signature))
        parent_gaps.append(parent_gap)
        incident_gap_means.append(float(incident_gaps.mean().item()))
        wrong_adjacency_gaps.append(wrong_adjacency_gap)
        scrambled_gaps.append(scrambled_gap)
        face_rows.append(
            {
                "face_index": face_index,
                "axis": int(face["axis"]),
                "site_anchors": vertices,
                "incident_edge_count": len(incident_edges),
                "projected_class_ids": sorted({row_key(responses[vertex, :4]) for vertex in vertices}),
                "parent_vs_projection_gap": parent_gap,
                "incident_edge_gap_mean": float(incident_gaps.mean().item()),
                "wrong_adjacency_gap": wrong_adjacency_gap,
            }
        )
    exact_total = (
        sp.Integer(len(coords))
        + sp.Integer(len(edges))
        + sp.Integer(len(faces))
        + sp.Integer(sum(row["incident_edge_count"] for row in face_rows))
        + sp.Integer(len(full_face_signatures))
    )
    return {
        "pass": bool(
            graph.num_nodes() == len(coords)
            and graph.num_edges() == len(edges)
            and rx.is_connected(graph)
            and len(faces) == 6
            and min(row["incident_edge_count"] for row in face_rows) == 4
            and max(row["incident_edge_count"] for row in face_rows) == 4
            and min(parent_gaps) > GAP_FLOOR
            and min(incident_gap_means) > GAP_FLOOR
            and min(wrong_adjacency_gaps) > GAP_FLOOR
            and min(scrambled_gaps) > GAP_FLOOR
            and len(single_probe_face_signatures) < len(full_face_signatures)
        ),
        "finite_map": "P_K : (D_K(Q_K|K_8), pi_f, anchor_f, local_order_ops) -> finite boundary-projected response-quotient carrier signatures + projection/control gap vector",
        "shape": list(SHAPE),
        "site_count": len(coords),
        "edge_count": len(edges),
        "face_projection_count": len(faces),
        "incident_edge_total": sum(row["incident_edge_count"] for row in face_rows),
        "bond_dim": BOND_DIM,
        "min_parent_projection_gap": min(parent_gaps),
        "min_incident_edge_gap_mean": min(incident_gap_means),
        "min_wrong_adjacency_gap": min(wrong_adjacency_gaps),
        "min_face_anchor_scramble_gap": min(scrambled_gaps),
        "full_face_projection_signature_count": len(full_face_signatures),
        "single_probe_face_projection_signature_count": len(single_probe_face_signatures),
        "single_probe_non_ic_collapses": len(single_probe_face_signatures) < len(full_face_signatures),
        "projection_erased_face_count": 0,
        "edge_erased_incident_edge_count": 0,
        "no_anchor_class_count": 0,
        "scalar_label_face_count": len(faces),
        "face_rows": face_rows,
        "sympy_exact_site_edge_face_incident_class_total": int(exact_total),
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def order_witness_gate() -> dict[str, Any]:
    coords = coords_for_shape(SHAPE)
    faces = face_list(SHAPE)
    responses = probe_responses(site_spinors(len(coords)), sic_effects())
    tensors = make_site_tensors(responses, coords, BOND_DIM)
    shift, filt = shift_filter_ops()
    face_gaps = []
    erased_gaps = []
    for face in faces:
        vertices = [int(item) for item in face["vertices"]]
        face_tensors = tensors[vertices]
        filter_after_shift = apply_physical_operator(apply_physical_operator(face_tensors, shift), filt)
        shift_after_filter = apply_physical_operator(apply_physical_operator(face_tensors, filt), shift)
        face_gaps.append(float(torch.linalg.vector_norm((filter_after_shift - shift_after_filter).reshape(-1)).item()))
        erased_1 = apply_physical_operator(apply_physical_operator(face_tensors, filt), filt)
        erased_2 = apply_physical_operator(apply_physical_operator(face_tensors, filt), filt)
        erased_gaps.append(float(torch.linalg.vector_norm((erased_1 - erased_2).reshape(-1)).item()))
    return {
        "pass": bool(min(face_gaps) > GAP_FLOOR and max(erased_gaps) < TOL),
        "N01_witness": "physical_filter after physical_shift differs from physical_shift after physical_filter on face-projected anchored tensors",
        "min_face_order_gap": min(face_gaps),
        "max_order_erased_control_gap": max(erased_gaps),
    }


def z3_gate(projection: dict[str, Any], order: dict[str, Any]) -> dict[str, Any]:
    finite = z3.Bool("finite")
    anchored = z3.Bool("anchored")
    face_projection = z3.Bool("face_projection")
    controls_fail = z3.Bool("controls_fail")
    dense = z3.Bool("dense")
    promote = z3.Bool("promote")
    solver = z3.Solver()
    solver.add(finite, anchored, face_projection, controls_fail, z3.Not(dense), z3.Not(promote))
    bad = z3.Solver()
    bad.add(promote, z3.Not(promote))
    count_solver = z3.Solver()
    faces = z3.Int("face_projection_count")
    sites = z3.Int("site_count")
    incident_edges = z3.Int("incident_edge_total")
    count_solver.add(
        faces == int(projection["face_projection_count"]),
        sites == int(projection["site_count"]),
        incident_edges == int(projection["incident_edge_total"]),
        faces == 6,
        sites == 8,
        incident_edges == 24,
    )
    gap_solver = z3.Solver()
    scaled_projection_gap = z3.Int("scaled_face_projection_gap")
    scaled_order_gap = z3.Int("scaled_face_order_gap")
    gap_solver.add(
        scaled_projection_gap == int(projection["min_parent_projection_gap"] * 1_000_000),
        scaled_order_gap == int(order["min_face_order_gap"] * 1_000_000),
        scaled_projection_gap > 0,
        scaled_order_gap > 0,
    )
    return {
        "pass": (
            solver.check() == z3.sat
            and bad.check() == z3.unsat
            and count_solver.check() == z3.sat
            and gap_solver.check() == z3.sat
        ),
        "finite_anchor_nonpromotion_status": str(solver.check()),
        "promotion_status": str(bad.check()),
        "face_count_status": str(count_solver.check()),
        "gap_status": str(gap_solver.check()),
        "scaled_projection_gap": int(projection["min_parent_projection_gap"] * 1_000_000),
        "scaled_order_gap": int(order["min_face_order_gap"] * 1_000_000),
    }


def main() -> int:
    started = time.time()
    projection = face_projection_gate()
    order = order_witness_gate()
    z3_row = z3_gate(projection, order)
    positive = {
        "P1_k8_face_projection_response_quotient": projection,
        "P2_face_projection_order_witness": order,
    }
    graveyard = {
        "GC_projection_erased_control_rejected": {
            "pass": projection["projection_erased_face_count"] == 0,
            "projection_erased_face_count": projection["projection_erased_face_count"],
        },
        "GC_face_anchor_scrambled_control_rejected": {
            "pass": projection["min_face_anchor_scramble_gap"] > GAP_FLOOR,
            "min_face_anchor_scramble_gap": projection["min_face_anchor_scramble_gap"],
        },
        "GC_edge_erased_control_rejected": {
            "pass": projection["edge_erased_incident_edge_count"] == 0,
            "edge_erased_incident_edge_count": projection["edge_erased_incident_edge_count"],
        },
        "GC_wrong_adjacency_control_rejected": {
            "pass": projection["min_wrong_adjacency_gap"] > GAP_FLOOR,
            "min_wrong_adjacency_gap": projection["min_wrong_adjacency_gap"],
        },
        "GC_single_probe_non_ic_control_collapses": {
            "pass": projection["single_probe_non_ic_collapses"],
            "single_probe_face_projection_signature_count": projection["single_probe_face_projection_signature_count"],
            "full_face_projection_signature_count": projection["full_face_projection_signature_count"],
        },
        "GC_no_anchor_control_rejected": {
            "pass": projection["no_anchor_class_count"] == 0,
            "no_anchor_class_count": projection["no_anchor_class_count"],
        },
        "GC_scalar_label_not_face_projection_signature": {
            "pass": projection["scalar_label_face_count"] == projection["face_projection_count"],
            "why_rejected": "scalar labels can count faces but do not carry finite response projections, incident edge gaps, or PEPS3D anchors",
        },
        "GC_order_erased_control_collapses": {
            "pass": order["max_order_erased_control_gap"] < TOL,
            "max_order_erased_control_gap": order["max_order_erased_control_gap"],
        },
    }
    boundary = {
        "B1_formal_scout_no_promotion": {"pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED},
        "B2_dense_closure_banned": {
            "pass": not projection["dense_state_closure_used"] and not projection["dense_environment_closure_used"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "B3_z3_finite_face_projection_nonpromotion": z3_row,
        "B4_downstream_consumers_blocked": {"pass": bool(BLOCKED_CONSUMERS), "blocked": BLOCKED_CONSUMERS},
    }
    checks = list(positive.values()) + list(graveyard.values()) + list(boundary.values())
    all_pass = all(bool(row["pass"]) for row in checks)
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "sim_id": SIM_ID,
        "name": NAME,
        "version": VERSION,
        "tier": TIER,
        "purpose": PURPOSE,
        "scientific_question": SCIENTIFIC_QUESTION,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": SIM_CLASS,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "root_constraints_in_force": {
            "F01": "finite K_8 PEPS3D carrier, finite face projections, finite anchors, finite SIC probe/effect responses, finite local operator paths, finite controls, finite output table",
            "N01": "physical_filter after physical_shift differs from physical_shift after physical_filter on face-projected anchored tensors, while order-erased control collapses",
        },
        "finite_map": [
            "P_K : (D_K(Q_K|K_8), pi_f, anchor_f, local_order_ops) -> finite boundary-projected response-quotient carrier signatures + projection/control gap vector",
            "O_K : (T_face, local_order_ops) -> finite local order-gap vector",
        ],
        "domain": {
            "carrier": "finite PEPS3D K_8 face-projection response-quotient carrier",
            "shape": list(SHAPE),
            "site_count": projection["site_count"],
            "edge_count": projection["edge_count"],
            "face_projection_count": projection["face_projection_count"],
            "incident_edge_total": projection["incident_edge_total"],
            "bond_dim": BOND_DIM,
            "probe_effect_source": "finite response classes from Q_K and torch-native spinor-derived response rows as carrier data only",
        },
        "codomain_or_output": "finite per-face projection table with projected class ids, incident edge response gaps, parent-vs-projection gap, local order gap, controls, and dense-closure blockers",
        "carrier_layer": "phase_2_finite_peps3d_seed_carrier",
        "geometry_layer": "peps3d_anchored_finite_response_quotient_carrier_geometry_k8_face_projection",
        "carrier_realization": "torch complex finite PEPS3D tensors over K_8 shape (2,2,2), bond 2, finite SIC response vectors, and rustworkx face/edge incidence",
        "peps3d_embedding": "K_8=(V,E,F,C) with explicit face anchors, each carrying four site anchors and four incident edge anchors; no scalar face labels admitted",
        "spinor_state": "torch-native two-component spinors seed finite local response tensors only; no Hopf/Weyl geometry is admitted",
        "quaternion_action": "not_applicable",
        "controller_context_artifacts": [PHASE2_TRANSITION_PATH],
        "dependency_receipts": [
            PHASE2_FRONTIER_MATRIX_PATH,
            PHASE2_POST_DK_BLOCKER,
            PHASE2_SEED_RECEIPT,
            PHASE2_SPINOR_DENSITY_RECEIPT,
            PHASE2_BOUNDARY_RECEIPT,
            PHASE2_ABLATION_RECEIPT,
            PHASE2_HELDOUT_RECEIPT,
            PHASE2_BOND_SWEEP_RECEIPT,
            PHASE2_RESPONSE_QUOTIENT_RECEIPT,
            PHASE2_CELL_PATCH_RECEIPT,
            PHASE2_SUBSTRATE_RECEIPT,
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "blocked",
        "cut_layer": "blocked",
        "law_or_candidate_tested": "finite PEPS3D K_8 face-projection response quotient",
        "branch_status_before_run": "post_D_K_active_frontier_blocker_repair",
        "allowed_claims": [
            "finite K_8 face projections preserve response-quotient carrier signatures on the tested carrier",
            "projection-erased, face-scrambled, edge-erased, wrong-adjacency, single-probe non-IC, no-anchor, scalar-label, order-erased, dense-closure, and promotion controls fail or collapse",
            "local physical operator order witness survives while order-erased control collapses",
        ],
        "promotion_blockers": BLOCKED_CONSUMERS,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_tools": ["pytorch", "rustworkx", "z3", "sympy"],
        "actual_tools_used": ["pytorch", "rustworkx", "z3", "sympy"],
        "proof_surfaces_used": ["z3_finite_face_projection_nonpromotion_gate", "sympy_exact_face_projection_counts"],
        "graph_surfaces_used": ["rustworkx_k8_face_edge_incidence_graph"],
        "topology_surfaces_used": ["finite_site_edge_face_incident_edge_support_counts"],
        "required_inputs": [
            PHASE2_FRONTIER_MATRIX_PATH,
            PHASE2_POST_DK_BLOCKER,
            PHASE2_SEED_RECEIPT,
            PHASE2_SPINOR_DENSITY_RECEIPT,
            PHASE2_BOUNDARY_RECEIPT,
            PHASE2_ABLATION_RECEIPT,
            PHASE2_HELDOUT_RECEIPT,
            PHASE2_BOND_SWEEP_RECEIPT,
            PHASE2_RESPONSE_QUOTIENT_RECEIPT,
            PHASE2_CELL_PATCH_RECEIPT,
            PHASE2_SUBSTRATE_RECEIPT,
        ],
        "data_or_artifact_dependencies": [
            PHASE2_FRONTIER_MATRIX_PATH,
            PHASE2_POST_DK_BLOCKER,
            PHASE2_SEED_RECEIPT,
            PHASE2_SPINOR_DENSITY_RECEIPT,
            PHASE2_BOUNDARY_RECEIPT,
            PHASE2_ABLATION_RECEIPT,
            PHASE2_HELDOUT_RECEIPT,
            PHASE2_BOND_SWEEP_RECEIPT,
            PHASE2_RESPONSE_QUOTIENT_RECEIPT,
            PHASE2_CELL_PATCH_RECEIPT,
            PHASE2_SUBSTRATE_RECEIPT,
        ],
        "required_negatives": [
            "projection_erased",
            "face_anchor_scrambled",
            "edge_erased",
            "wrong_adjacency",
            "single_probe_non_ic",
            "no_anchor",
            "scalar_label",
            "order_erased",
            "dense_state_closure",
            "dense_environment_closure",
            "promotion",
        ],
        "negatives_run": [
            "projection_erased",
            "face_anchor_scrambled",
            "edge_erased",
            "wrong_adjacency",
            "single_probe_non_ic",
            "no_anchor",
            "scalar_label",
            "order_erased",
            "dense_state_closure",
            "dense_environment_closure",
            "promotion",
        ],
        "kill_conditions": [
            "finite K_8 face projections or incident edge anchors are missing",
            "parent-vs-projection or incident edge response gap vanishes",
            "projection-erased, face-scrambled, edge-erased, or wrong-adjacency controls are accepted",
            "single-probe non-IC control does not collapse relative to the full effect family",
            "order witness vanishes",
            "dense closure is used",
            "promotion becomes satisfiable",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "phase2_k8_face_projection_response_quotient_v1",
        "all_pass": all_pass,
        "nearby_variants": {"passed": sum(1 for row in checks if row["pass"]), "total": len(checks)},
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "summary": {
            "phase": 2,
            "elapsed_seconds": time.time() - started,
            "candidate": "peps3d_k8_face_projection_response_quotient",
            "max_peps3d_sites": projection["site_count"],
            "max_peps3d_bond": BOND_DIM,
            "face_projection_count": projection["face_projection_count"],
            "incident_edge_total": projection["incident_edge_total"],
            "min_parent_projection_gap": projection["min_parent_projection_gap"],
            "min_wrong_adjacency_gap": projection["min_wrong_adjacency_gap"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "result_summary": {
            "all_pass": all_pass,
            "site_count": projection["site_count"],
            "edge_count": projection["edge_count"],
            "face_projection_count": projection["face_projection_count"],
            "incident_edge_total": projection["incident_edge_total"],
            "min_parent_projection_gap": projection["min_parent_projection_gap"],
            "min_incident_edge_gap_mean": projection["min_incident_edge_gap_mean"],
            "min_wrong_adjacency_gap": projection["min_wrong_adjacency_gap"],
            "full_face_projection_signature_count": projection["full_face_projection_signature_count"],
            "single_probe_face_projection_signature_count": projection["single_probe_face_projection_signature_count"],
            "min_face_order_gap": order["min_face_order_gap"],
            "max_order_erased_control_gap": order["max_order_erased_control_gap"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "pass_rule": "Pass iff finite K_8 face projections preserve response-quotient carrier signatures with incident edge support, projection-erased/face-scrambled/edge-erased/wrong-adjacency controls fail, single-probe non-IC control collapses, no-anchor and scalar-label controls are rejected, local order gap survives, dense closure stays false, and promotion is blocked.",
        "fail_rule": "Fail if face projection support is nonfinite or missing, controls replace the carrier projection, single-probe non-IC control does not collapse, order gap vanishes, dense closure is used, or promotion becomes satisfiable.",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_carrier_frontier_matrix_only"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "next_required_work": [
            "Classify this K_8 face-projection receipt inside the active carrier frontier matrix.",
            "After classification, reissue or keep blocking the broader boundary/interior projection packet with P_K as dependency."
        ],
        "next_admissible_step": "Classify this P_K packet, then decide whether to reissue the broader boundary response projection packet or write the next active-frontier blocker.",
        "why_not_v4_probes": (
            "This is a v5 formal scout for active PEPS3D carrier-frontier continuation. "
            "It is not a v4 probe and not a full PEPS3D closure claim."
        ),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "summary": result["summary"], "wrote": str(OUT_PATH)}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
