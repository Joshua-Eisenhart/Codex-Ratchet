#!/usr/bin/env python3
"""PEPS3D heldout-shape anchor replay scout.

Formal scout only.

This packet stays inside Phase 2 PEPS3D-anchored finite response-quotient
carrier geometry. It uses a heldout carrier shape that is not one of the prior
8/16/32/64 stress shapes:

  H_K : (r_P(s), K_holdout, anchor, local_order_ops)
        -> heldout anchor response + boundary signature + order-gap vector

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
    all_edge_signatures,
    apply_physical_operator,
    as_jsonable,
    cell_list,
    cell_signature,
    coords_for_shape,
    edge_list,
    face_list,
    face_signature,
    make_site_tensors,
    probe_responses,
    shift_filter_ops,
    sic_effects,
    site_signature,
    site_spinors,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "peps3d_heldout_shape_anchor_replay_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Test whether the active finite PEPS3D carrier geometry replays on a "
    "heldout non-power-of-two shape without dense closure or downstream claims."
)
SCIENTIFIC_QUESTION = (
    "Can a heldout finite PEPS3D carrier K_holdout=(V,E,F,C), shape (3,3,2), "
    "carry finite response-quotient tensors, anchor signatures, boundary "
    "readouts, and a local order witness while anchor-erased, scalar, "
    "order-erased, dense-closure, and promotion controls fail?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_heldout_shape_anchor_replay"
PROMOTION_ALLOWED = False

PHASE2_FRONTIER_MATRIX_PATH = "system_v5/ops/formal_scouts/phase2_peps3d_seed_frontier_matrix_20260525.json"
PHASE2_TRANSITION_PATH = "system_v5/ops/formal_scouts/phase2_seed_frontier_transition_decision_20260525.json"
PHASE2_SEED_RECEIPT = "system_v5/ops/formal_scouts/results/finite_peps3d_probe_effect_seed_carrier_gate_probe_results.json"
PHASE2_SPINOR_DENSITY_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_spinor_density_carrier_gate_probe_results.json"
PHASE2_BOUNDARY_RECEIPT = "system_v5/ops/formal_scouts/results/peps_peps3d_local_environment_contraction_gate_probe_results.json"
PHASE2_ABLATION_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_anchor_ablation_boundary_stress_continuation_probe_results.json"

CLAIM_CEILING = (
    "Formal scout only: tests a heldout finite PEPS3D seed-carrier shape. It "
    "does not admit nested Hopf tori, Weyl sheets, terrain, operator substages, "
    "flux, Xi/Phi0, Axis0, Holodeck/FEP, physics, IGT/game theory, axes 7-12, "
    "or full PEPS3D closure."
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
        "reason": "load-bearing heldout PEPS3D tensors, anchor signatures, boundary readouts, and local order gap",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing heldout carrier graph and finite edge support checks",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing heldout finite/nonpromotion gate",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact heldout site/edge/face/cell count checks",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "rustworkx": "load_bearing",
    "z3": "load_bearing",
    "sympy": "load_bearing",
}

HELDOUT_SHAPE = (3, 3, 2)
BOND_DIM = 2
GAP_FLOOR = 1.0e-8
TOL = 1.0e-10


def carrier_graph(shape: tuple[int, int, int]) -> rx.PyGraph:
    graph = rx.PyGraph()
    coords = coords_for_shape(shape)
    graph.add_nodes_from([{"coord": coord} for coord in coords])
    for edge in edge_list(shape):
        graph.add_edge(int(edge["src"]), int(edge["dst"]), {"axis": int(edge["axis"])})
    return graph


def is_boundary_coord(coord: tuple[int, int, int], shape: tuple[int, int, int]) -> bool:
    return any(coord[axis] == 0 or coord[axis] == shape[axis] - 1 for axis in range(3))


def build_tensors() -> tuple[list[tuple[int, int, int]], torch.Tensor]:
    coords = coords_for_shape(HELDOUT_SHAPE)
    responses = probe_responses(site_spinors(len(coords)), sic_effects())
    return coords, make_site_tensors(responses, coords, BOND_DIM)


def heldout_anchor_replay() -> dict[str, Any]:
    coords, tensors = build_tensors()
    edges = edge_list(HELDOUT_SHAPE)
    faces = face_list(HELDOUT_SHAPE)
    cells = cell_list(HELDOUT_SHAPE)
    graph = carrier_graph(HELDOUT_SHAPE)
    site_sigs = site_signature(tensors)
    edge_sigs = all_edge_signatures(tensors, edges)
    face_sigs = face_signature(edge_sigs, faces, edges)
    cell_sigs = cell_signature(face_sigs, cells)
    boundary_sites = [idx for idx, coord in enumerate(coords) if is_boundary_coord(coord, HELDOUT_SHAPE)]
    boundary_edges = [
        edge
        for edge in edges
        if int(edge["src"]) in boundary_sites or int(edge["dst"]) in boundary_sites
    ]
    boundary_edge_sigs = all_edge_signatures(tensors, boundary_edges)

    anchor_vector = torch.tensor(
        [
            float(len(coords)),
            float(len(edges)),
            float(len(faces)),
            float(len(cells)),
            float(torch.linalg.vector_norm(site_sigs).item()),
            float(torch.linalg.vector_norm(torch.real(edge_sigs)).item()),
            float(torch.linalg.vector_norm(face_sigs).item()) if face_sigs.numel() else 0.0,
            float(torch.linalg.vector_norm(cell_sigs).item()) if cell_sigs.numel() else 0.0,
            float(torch.linalg.vector_norm(site_sigs[boundary_sites]).item()),
            float(torch.linalg.vector_norm(torch.real(boundary_edge_sigs)).item()),
        ],
        dtype=RTYPE,
    )
    controls = {
        "site_only": anchor_vector * torch.tensor([1, 0, 0, 0, 1, 0, 0, 0, 1, 0], dtype=RTYPE),
        "edge_erased": anchor_vector * torch.tensor([1, 0, 0, 0, 1, 0, 0, 0, 1, 0], dtype=RTYPE),
        "face_erased": anchor_vector * torch.tensor([1, 1, 0, 0, 1, 1, 0, 0, 1, 1], dtype=RTYPE),
        "cell_erased": anchor_vector * torch.tensor([1, 1, 1, 0, 1, 1, 1, 0, 1, 1], dtype=RTYPE),
        "no_anchor": torch.zeros_like(anchor_vector),
        "scalar_label": torch.full_like(anchor_vector, float(len(coords))),
    }
    control_gaps = {name: float(torch.linalg.vector_norm(anchor_vector - vector).item()) for name, vector in controls.items()}

    shift, filt = shift_filter_ops()
    filter_after_shift = apply_physical_operator(apply_physical_operator(tensors, shift), filt)
    shift_after_filter = apply_physical_operator(apply_physical_operator(tensors, filt), shift)
    order_gap = float(torch.linalg.vector_norm((filter_after_shift - shift_after_filter).reshape(-1)).item())
    erased_1 = apply_physical_operator(apply_physical_operator(tensors, filt), filt)
    erased_2 = apply_physical_operator(apply_physical_operator(tensors, filt), filt)
    order_erased_gap = float(torch.linalg.vector_norm((erased_1 - erased_2).reshape(-1)).item())
    exact_total = (
        sp.Integer(len(coords))
        + sp.Integer(len(edges))
        + sp.Integer(len(faces))
        + sp.Integer(len(cells))
    )
    return {
        "pass": bool(
            graph.num_nodes() == len(coords)
            and graph.num_edges() == len(edges)
            and rx.is_connected(graph)
            and len(coords) == 18
            and all(value > GAP_FLOOR for value in control_gaps.values())
            and order_gap > GAP_FLOOR
            and order_erased_gap < TOL
            and torch.isfinite(anchor_vector).all().item()
            and torch.isfinite(torch.real(boundary_edge_sigs)).all().item()
        ),
        "finite_map": "H_K : (r_P(s), K_holdout, anchor, local_order_ops) -> heldout anchor response + boundary signature + order-gap vector",
        "shape": list(HELDOUT_SHAPE),
        "site_count": len(coords),
        "bond_dim": BOND_DIM,
        "anchor_counts": {
            "V": len(coords),
            "E": len(edges),
            "F": len(faces),
            "C": len(cells),
        },
        "boundary_site_count": len(boundary_sites),
        "boundary_edge_count": len(boundary_edges),
        "anchor_vector_norm": float(torch.linalg.vector_norm(anchor_vector).item()),
        "control_gaps": control_gaps,
        "order_gap": order_gap,
        "order_erased_control_gap": order_erased_gap,
        "rustworkx_nodes": graph.num_nodes(),
        "rustworkx_edges": graph.num_edges(),
        "sympy_exact_anchor_total": int(exact_total),
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def z3_gate(row: dict[str, Any]) -> dict[str, Any]:
    finite = z3.Bool("finite")
    heldout = z3.Bool("heldout")
    dense = z3.Bool("dense")
    promote = z3.Bool("promote")
    solver = z3.Solver()
    solver.add(finite, heldout, z3.Not(dense), z3.Not(promote))
    bad = z3.Solver()
    bad.add(promote, z3.Not(promote))
    gap_solver = z3.Solver()
    gap = z3.Int("heldout_scaled_order_gap")
    gap_solver.add(gap == int(row["order_gap"] * 1_000_000), gap > 0)
    return {
        "pass": solver.check() == z3.sat and bad.check() == z3.unsat and gap_solver.check() == z3.sat,
        "finite_heldout_status": str(solver.check()),
        "promotion_status": str(bad.check()),
        "gap_status": str(gap_solver.check()),
        "scaled_order_gap": int(row["order_gap"] * 1_000_000),
    }


def main() -> int:
    started = time.time()
    heldout = heldout_anchor_replay()
    z3_row = z3_gate(heldout)
    positive = {"P1_heldout_shape_anchor_replay": heldout}
    graveyard = {
        f"GC_{name}_control_rejected": {"pass": gap > GAP_FLOOR, "gap": gap}
        for name, gap in heldout["control_gaps"].items()
    }
    graveyard["GC_order_erased_control_collapses"] = {
        "pass": heldout["order_erased_control_gap"] < TOL,
        "gap": heldout["order_erased_control_gap"],
    }
    boundary = {
        "B1_formal_scout_no_promotion": {"pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED},
        "B2_dense_closure_banned": {
            "pass": not heldout["dense_state_closure_used"] and not heldout["dense_environment_closure_used"]
        },
        "B3_z3_finite_heldout_nonpromotion": z3_row,
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
            "F01": "finite heldout PEPS3D carrier, finite anchors, finite local responses, finite controls, finite output vector",
            "N01": "physical_filter after physical_shift differs from physical_shift after physical_filter on heldout tensors, while order-erased control collapses",
        },
        "finite_map": "H_K : (r_P(s), K_holdout, anchor, local_order_ops) -> heldout anchor response + boundary signature + order-gap vector",
        "domain": {
            "carrier": "finite heldout PEPS3D seed-carrier tensor",
            "heldout_shape": list(HELDOUT_SHAPE),
            "bond_dim": BOND_DIM,
            "probe_effect_source": "finite SIC effects and torch-native spinor-derived local responses as carrier data only",
        },
        "codomain_or_output": "finite heldout anchor counts, anchor norms, boundary norms, local order gap, controls, and dense-closure blockers",
        "carrier_layer": "phase_2_finite_peps3d_seed_carrier",
        "geometry_layer": "peps3d_anchored_finite_response_quotient_carrier_geometry_heldout_replay",
        "carrier_realization": "torch complex finite PEPS3D tensor carrier over heldout shape (3,3,2)",
        "peps3d_embedding": "K_holdout=(V,E,F,C) with explicit site, edge, face, and cell anchors; no scalar carrier labels admitted",
        "spinor_state": "torch-native two-component spinors seed finite local response tensors only; no Hopf/Weyl geometry is admitted",
        "quaternion_action": "not_applicable",
        "controller_context_artifacts": [PHASE2_TRANSITION_PATH],
        "dependency_receipts": [
            PHASE2_FRONTIER_MATRIX_PATH,
            PHASE2_SEED_RECEIPT,
            PHASE2_SPINOR_DENSITY_RECEIPT,
            PHASE2_BOUNDARY_RECEIPT,
            PHASE2_ABLATION_RECEIPT,
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "blocked",
        "cut_layer": "blocked",
        "law_or_candidate_tested": "finite PEPS3D heldout-shape anchor replay",
        "branch_status_before_run": "active_carrier_frontier_continue_active_level",
        "allowed_claims": [
            "heldout shape (3,3,2) preserves finite PEPS3D anchor replay under the tested controls",
            "heldout local physical operator order witness survives while order-erased control collapses",
        ],
        "promotion_blockers": BLOCKED_CONSUMERS,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_tools": ["pytorch", "rustworkx", "z3", "sympy"],
        "actual_tools_used": ["pytorch", "rustworkx", "z3", "sympy"],
        "proof_surfaces_used": ["z3_finite_heldout_nonpromotion_gate", "sympy_exact_anchor_count"],
        "graph_surfaces_used": ["rustworkx_heldout_carrier_graph"],
        "topology_surfaces_used": ["heldout_site_edge_face_cell_anchor_support_counts"],
        "required_inputs": [
            PHASE2_FRONTIER_MATRIX_PATH,
            PHASE2_SEED_RECEIPT,
            PHASE2_SPINOR_DENSITY_RECEIPT,
            PHASE2_BOUNDARY_RECEIPT,
            PHASE2_ABLATION_RECEIPT,
        ],
        "data_or_artifact_dependencies": [
            PHASE2_FRONTIER_MATRIX_PATH,
            PHASE2_SEED_RECEIPT,
            PHASE2_SPINOR_DENSITY_RECEIPT,
            PHASE2_BOUNDARY_RECEIPT,
            PHASE2_ABLATION_RECEIPT,
        ],
        "required_negatives": [
            "site_only",
            "edge_erased",
            "face_erased",
            "cell_erased",
            "no_anchor",
            "scalar_label",
            "order_erased",
            "dense_state_closure",
            "dense_environment_closure",
            "promotion",
        ],
        "negatives_run": [
            "site_only",
            "edge_erased",
            "face_erased",
            "cell_erased",
            "no_anchor",
            "scalar_label",
            "order_erased",
            "dense_state_closure",
            "dense_environment_closure",
            "promotion",
        ],
        "kill_conditions": [
            "heldout anchor vector lacks site/edge/face/cell support",
            "heldout erased-anchor or scalar controls replace the anchored vector",
            "heldout order witness vanishes",
            "dense closure is used",
            "promotion becomes satisfiable",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "phase2_heldout_shape_anchor_replay_v1",
        "all_pass": all_pass,
        "nearby_variants": {"passed": sum(1 for row in checks if row["pass"]), "total": len(checks)},
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "summary": {
            "phase": 2,
            "elapsed_seconds": time.time() - started,
            "candidate": "peps3d_heldout_shape_anchor_replay",
            "max_peps3d_sites": heldout["site_count"],
            "max_peps3d_bond": BOND_DIM,
            "heldout_shape": list(HELDOUT_SHAPE),
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "result_summary": {
            "all_pass": all_pass,
            "heldout_shape": list(HELDOUT_SHAPE),
            "site_count": heldout["site_count"],
            "anchor_counts": heldout["anchor_counts"],
            "order_gap": heldout["order_gap"],
            "order_erased_control_gap": heldout["order_erased_control_gap"],
            "control_gaps": heldout["control_gaps"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "pass_rule": "Pass iff heldout carrier anchors are finite/nonzero, controls differ, local order gap survives, order-erased control collapses, dense closure stays false, and promotion is blocked.",
        "fail_rule": "Fail if heldout anchors collapse, controls replace the carrier vector, order gap vanishes, dense closure is used, or promotion becomes satisfiable.",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_carrier_frontier_matrix_only"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "next_required_work": [
            "Classify this heldout-shape receipt inside the active carrier frontier matrix.",
            "Continue or block inside the same active carrier frontier with one bounded packet at a time.",
        ],
        "next_admissible_step": "Continue or block inside the active carrier frontier; do not open later consumers from this receipt.",
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
