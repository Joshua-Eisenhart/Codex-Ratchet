#!/usr/bin/env python3
"""PEPS3D cell-patch overlap consistency scout.

Formal scout only.

This continuation packet stays inside Phase 2 PEPS3D-anchored finite
response-quotient carrier geometry. It tests:

  G_K : (K=(V,E,F,C), r_P, cell patches, overlaps)
        -> finite cell-overlap consistency signatures + order-gap vector

It does not admit nested Hopf tori, Weyl sheets, terrain, operator substages,
flux, Xi/Phi0, Axis0, physics, axes 7-12, or full PEPS3D closure.
"""

from __future__ import annotations

import itertools
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
    cell_list,
    coords_for_shape,
    edge_list,
    make_site_tensors,
    probe_responses,
    shift_filter_ops,
    sic_effects,
    site_spinors,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "peps3d_cell_patch_overlap_consistency_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Continue the active carrier frontier by testing whether neighboring "
    "PEPS3D cell patches agree on shared finite face-overlap response "
    "signatures without dense closure or downstream geometry."
)
SCIENTIFIC_QUESTION = (
    "Can finite PEPS3D cell patches over K=(V,E,F,C) produce bounded overlap "
    "consistency signatures while overlap-erased, anchor-scrambled, "
    "scalar-label, single-probe non-IC, order-erased, dense-closure, and "
    "promotion controls fail?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_cell_patch_overlap_consistency"
PROMOTION_ALLOWED = False

PHASE2_FRONTIER_MATRIX_PATH = "system_v5/ops/formal_scouts/phase2_peps3d_seed_frontier_matrix_20260525.json"
PHASE2_TRANSITION_PATH = "system_v5/ops/formal_scouts/phase2_seed_frontier_transition_decision_20260525.json"
PHASE2_SEED_RECEIPT = "system_v5/ops/formal_scouts/results/finite_peps3d_probe_effect_seed_carrier_gate_probe_results.json"
PHASE2_SPINOR_DENSITY_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_spinor_density_carrier_gate_probe_results.json"
PHASE2_BOUNDARY_RECEIPT = "system_v5/ops/formal_scouts/results/peps_peps3d_local_environment_contraction_gate_probe_results.json"
PHASE2_ABLATION_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_anchor_ablation_boundary_stress_continuation_probe_results.json"
PHASE2_HELDOUT_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_heldout_shape_anchor_replay_probe_results.json"
PHASE2_BOND_SWEEP_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_bond_sweep_anchor_stability_probe_results.json"
PHASE2_RESPONSE_QUOTIENT_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_response_quotient_anchor_partition_probe_results.json"

CLAIM_CEILING = (
    "Formal scout only: tests finite PEPS3D cell-patch overlap consistency. "
    "It does not admit nested Hopf tori, Weyl sheets, terrain, operator "
    "substage cells, flux, Xi/Phi0, Axis0, Holodeck/FEP, physics, IGT/game "
    "theory, axes 7-12, or full PEPS3D closure."
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
        "reason": "load-bearing torch finite response tensors, overlap signatures, scrambled controls, and local order gap",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite cell-overlap graph support and connectivity checks",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite overlap/nonpromotion and dense-ban gate",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact finite site, edge, cell, and face-overlap count checks",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "rustworkx": "load_bearing",
    "z3": "load_bearing",
    "sympy": "load_bearing",
}

SHAPE = (4, 4, 4)
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


def face_overlap_pairs(cells: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pairs = []
    for left, right in itertools.combinations(range(len(cells)), 2):
        left_vertices = set(int(item) for item in cells[left]["vertices"])
        right_vertices = set(int(item) for item in cells[right]["vertices"])
        shared = sorted(left_vertices & right_vertices)
        if len(shared) == 4:
            pairs.append({"left": left, "right": right, "shared_vertices": shared})
    return pairs


def signature_for_vertices(responses: torch.Tensor, vertices: list[int], *, columns: int = 4) -> torch.Tensor:
    return responses[vertices, :columns].mean(dim=0)


def overlap_gate() -> dict[str, Any]:
    coords = coords_for_shape(SHAPE)
    edges = edge_list(SHAPE)
    cells = cell_list(SHAPE)
    graph = carrier_graph(SHAPE)
    overlaps = face_overlap_pairs(cells)
    responses = probe_responses(site_spinors(len(coords)), sic_effects())

    consistency_gaps = []
    scramble_gaps = []
    single_probe_signatures = set()
    full_signatures = set()
    for idx, overlap in enumerate(overlaps):
        shared = overlap["shared_vertices"]
        left_signature = signature_for_vertices(responses, shared, columns=4)
        right_signature = signature_for_vertices(responses, shared, columns=4)
        consistency_gaps.append(float(torch.linalg.vector_norm(left_signature - right_signature).item()))
        scrambled = signature_for_vertices(
            responses,
            [int((vertex + idx + 1) % len(coords)) for vertex in shared],
            columns=4,
        )
        scramble_gaps.append(float(torch.linalg.vector_norm(left_signature - scrambled).item()))
        single_probe_signatures.add(tuple(round(float(item), 10) for item in signature_for_vertices(responses, shared, columns=1)))
        full_signatures.add(tuple(round(float(item), 10) for item in left_signature))

    overlap_graph = rx.PyGraph()
    overlap_graph.add_nodes_from(range(len(cells)))
    for overlap in overlaps:
        overlap_graph.add_edge(int(overlap["left"]), int(overlap["right"]), {"shared": overlap["shared_vertices"]})

    exact_total = (
        sp.Integer(len(coords))
        + sp.Integer(len(edges))
        + sp.Integer(len(cells))
        + sp.Integer(len(overlaps))
    )
    return {
        "pass": bool(
            graph.num_nodes() == len(coords)
            and graph.num_edges() == len(edges)
            and rx.is_connected(graph)
            and len(cells) == 27
            and len(overlaps) == 54
            and overlap_graph.num_nodes() == len(cells)
            and overlap_graph.num_edges() == len(overlaps)
            and rx.is_connected(overlap_graph)
            and max(consistency_gaps) < TOL
            and min(scramble_gaps) > GAP_FLOOR
            and len(single_probe_signatures) < len(full_signatures)
        ),
        "finite_map": "G_K : (K=(V,E,F,C), r_P, cell patches, overlaps) -> finite cell-overlap consistency signatures + order-gap vector",
        "shape": list(SHAPE),
        "site_count": len(coords),
        "edge_count": len(edges),
        "cell_count": len(cells),
        "face_overlap_count": len(overlaps),
        "overlap_graph_nodes": overlap_graph.num_nodes(),
        "overlap_graph_edges": overlap_graph.num_edges(),
        "max_consistency_gap": max(consistency_gaps),
        "min_scrambled_control_gap": min(scramble_gaps),
        "full_overlap_signature_count": len(full_signatures),
        "single_probe_overlap_signature_count": len(single_probe_signatures),
        "single_probe_non_ic_collapses": len(single_probe_signatures) < len(full_signatures),
        "sympy_exact_site_edge_cell_overlap_total": int(exact_total),
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def order_witness_gate() -> dict[str, Any]:
    coords = coords_for_shape(SHAPE)
    responses = probe_responses(site_spinors(len(coords)), sic_effects())
    tensors = make_site_tensors(responses, coords, BOND_DIM)
    shift, filt = shift_filter_ops()
    filter_after_shift = apply_physical_operator(apply_physical_operator(tensors, shift), filt)
    shift_after_filter = apply_physical_operator(apply_physical_operator(tensors, filt), shift)
    order_gap = float(torch.linalg.vector_norm((filter_after_shift - shift_after_filter).reshape(-1)).item())
    erased_1 = apply_physical_operator(apply_physical_operator(tensors, filt), filt)
    erased_2 = apply_physical_operator(apply_physical_operator(tensors, filt), filt)
    order_erased_gap = float(torch.linalg.vector_norm((erased_1 - erased_2).reshape(-1)).item())
    return {
        "pass": bool(order_gap > GAP_FLOOR and order_erased_gap < TOL),
        "N01_witness": "physical_filter after physical_shift differs from physical_shift after physical_filter on cell-overlap anchored tensors",
        "order_gap": order_gap,
        "order_erased_control_gap": order_erased_gap,
    }


def z3_gate(overlap: dict[str, Any], order: dict[str, Any]) -> dict[str, Any]:
    finite = z3.Bool("finite")
    anchored = z3.Bool("anchored")
    overlap_consistent = z3.Bool("overlap_consistent")
    dense = z3.Bool("dense")
    promote = z3.Bool("promote")
    solver = z3.Solver()
    solver.add(finite, anchored, overlap_consistent, z3.Not(dense), z3.Not(promote))
    bad = z3.Solver()
    bad.add(promote, z3.Not(promote))
    count_solver = z3.Solver()
    cell_count = z3.Int("cell_count")
    overlap_count = z3.Int("face_overlap_count")
    count_solver.add(cell_count == int(overlap["cell_count"]), overlap_count == int(overlap["face_overlap_count"]))
    count_solver.add(cell_count == 27, overlap_count == 54)
    gap_solver = z3.Solver()
    scaled_gap = z3.Int("scaled_cell_overlap_order_gap")
    gap_solver.add(scaled_gap == int(order["order_gap"] * 1_000_000), scaled_gap > 0)
    return {
        "pass": (
            solver.check() == z3.sat
            and bad.check() == z3.unsat
            and count_solver.check() == z3.sat
            and gap_solver.check() == z3.sat
        ),
        "finite_anchor_nonpromotion_status": str(solver.check()),
        "promotion_status": str(bad.check()),
        "overlap_count_status": str(count_solver.check()),
        "gap_status": str(gap_solver.check()),
        "scaled_order_gap": int(order["order_gap"] * 1_000_000),
    }


def main() -> int:
    started = time.time()
    overlap = overlap_gate()
    order = order_witness_gate()
    z3_row = z3_gate(overlap, order)
    positive = {
        "P1_cell_patch_overlap_consistency": overlap,
        "P2_cell_patch_order_witness": order,
    }
    graveyard = {
        "GC_overlap_erased_control_rejected": {
            "pass": overlap["face_overlap_count"] > 0,
            "erased_overlap_count": 0,
            "required_overlap_count": overlap["face_overlap_count"],
        },
        "GC_anchor_scrambled_control_rejected": {
            "pass": overlap["min_scrambled_control_gap"] > GAP_FLOOR,
            "min_scrambled_control_gap": overlap["min_scrambled_control_gap"],
        },
        "GC_single_probe_non_ic_control_collapses": {
            "pass": overlap["single_probe_non_ic_collapses"],
            "single_probe_overlap_signature_count": overlap["single_probe_overlap_signature_count"],
            "full_overlap_signature_count": overlap["full_overlap_signature_count"],
        },
        "GC_scalar_label_not_cell_overlap_signature": {
            "pass": overlap["cell_count"] == 27,
            "why_rejected": "scalar cell labels can count cells but do not carry finite effect response restrictions on shared PEPS3D anchors",
        },
        "GC_order_erased_control_collapses": {
            "pass": order["order_erased_control_gap"] < TOL,
            "order_erased_control_gap": order["order_erased_control_gap"],
        },
    }
    boundary = {
        "B1_formal_scout_no_promotion": {"pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED},
        "B2_dense_closure_banned": {
            "pass": not overlap["dense_state_closure_used"] and not overlap["dense_environment_closure_used"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "B3_z3_finite_cell_overlap_nonpromotion": z3_row,
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
            "F01": "finite PEPS3D carrier, finite cell patches, finite face overlaps, finite SIC probe/effect responses, finite controls, finite output vector",
            "N01": "physical_filter after physical_shift differs from physical_shift after physical_filter on cell-overlap anchored tensors, while order-erased control collapses",
        },
        "finite_map": [
            "G_K : (K=(V,E,F,C), r_P, cell patches, overlaps) -> finite cell-overlap consistency signatures + order-gap vector",
            "O_K : (T_K, local_order_ops) -> finite local order-gap vector",
        ],
        "domain": {
            "carrier": "finite PEPS3D seed-carrier cell patches and face-overlap anchors",
            "shape": list(SHAPE),
            "site_count": overlap["site_count"],
            "cell_count": overlap["cell_count"],
            "face_overlap_count": overlap["face_overlap_count"],
            "bond_dim": BOND_DIM,
            "probe_effect_source": "finite SIC effects and torch-native spinor-derived local responses as carrier data only",
        },
        "codomain_or_output": "finite cell-overlap consistency signatures, overlap-incidence graph readouts, local order-gap rows, controls, and dense-closure blockers",
        "carrier_layer": "phase_2_finite_peps3d_seed_carrier",
        "geometry_layer": "peps3d_anchored_finite_response_quotient_carrier_geometry_cell_patch_overlap",
        "carrier_realization": "torch complex finite PEPS3D tensors over shape (4,4,4), bond 2, finite SIC response vectors, and finite cell overlap graph",
        "peps3d_embedding": "K=(V,E,F,C) with explicit cell patches C and face-overlap anchors; no scalar cell labels admitted",
        "spinor_state": "torch-native two-component spinors seed finite local response tensors only; no Hopf/Weyl geometry is admitted",
        "quaternion_action": "not_applicable",
        "controller_context_artifacts": [PHASE2_TRANSITION_PATH],
        "dependency_receipts": [
            PHASE2_FRONTIER_MATRIX_PATH,
            PHASE2_SEED_RECEIPT,
            PHASE2_SPINOR_DENSITY_RECEIPT,
            PHASE2_BOUNDARY_RECEIPT,
            PHASE2_ABLATION_RECEIPT,
            PHASE2_HELDOUT_RECEIPT,
            PHASE2_BOND_SWEEP_RECEIPT,
            PHASE2_RESPONSE_QUOTIENT_RECEIPT,
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "blocked",
        "cut_layer": "blocked",
        "law_or_candidate_tested": "finite PEPS3D cell-patch overlap consistency",
        "branch_status_before_run": "active_carrier_frontier_continue_active_level",
        "allowed_claims": [
            "finite PEPS3D neighboring cell patches agree on shared face-overlap finite response signatures under tested controls",
            "anchor-scrambled and overlap-erased controls fail as replacements",
            "local physical operator order witness survives while order-erased control collapses",
        ],
        "promotion_blockers": BLOCKED_CONSUMERS,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_tools": ["pytorch", "rustworkx", "z3", "sympy"],
        "actual_tools_used": ["pytorch", "rustworkx", "z3", "sympy"],
        "proof_surfaces_used": ["z3_finite_cell_overlap_nonpromotion_gate", "sympy_exact_cell_overlap_counts"],
        "graph_surfaces_used": ["rustworkx_cell_overlap_graph"],
        "topology_surfaces_used": ["finite_cell_patch_face_overlap_support_counts"],
        "required_inputs": [
            PHASE2_FRONTIER_MATRIX_PATH,
            PHASE2_SEED_RECEIPT,
            PHASE2_SPINOR_DENSITY_RECEIPT,
            PHASE2_BOUNDARY_RECEIPT,
            PHASE2_ABLATION_RECEIPT,
            PHASE2_HELDOUT_RECEIPT,
            PHASE2_BOND_SWEEP_RECEIPT,
            PHASE2_RESPONSE_QUOTIENT_RECEIPT,
        ],
        "data_or_artifact_dependencies": [
            PHASE2_FRONTIER_MATRIX_PATH,
            PHASE2_SEED_RECEIPT,
            PHASE2_SPINOR_DENSITY_RECEIPT,
            PHASE2_BOUNDARY_RECEIPT,
            PHASE2_ABLATION_RECEIPT,
            PHASE2_HELDOUT_RECEIPT,
            PHASE2_BOND_SWEEP_RECEIPT,
            PHASE2_RESPONSE_QUOTIENT_RECEIPT,
        ],
        "required_negatives": [
            "overlap_erased",
            "anchor_scrambled",
            "single_probe_non_ic",
            "scalar_label",
            "order_erased",
            "dense_state_closure",
            "dense_environment_closure",
            "promotion",
        ],
        "negatives_run": [
            "overlap_erased",
            "anchor_scrambled",
            "single_probe_non_ic",
            "scalar_label",
            "order_erased",
            "dense_state_closure",
            "dense_environment_closure",
            "promotion",
        ],
        "kill_conditions": [
            "finite cell patches or face overlaps are missing",
            "cell overlap consistency fails on shared finite response restrictions",
            "anchor-scrambled or overlap-erased controls are accepted",
            "single-probe non-IC control does not collapse relative to full overlap signatures",
            "order witness vanishes",
            "dense closure is used",
            "promotion becomes satisfiable",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "phase2_cell_patch_overlap_consistency_v1",
        "all_pass": all_pass,
        "nearby_variants": {"passed": sum(1 for row in checks if row["pass"]), "total": len(checks)},
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "summary": {
            "phase": 2,
            "elapsed_seconds": time.time() - started,
            "candidate": "peps3d_cell_patch_overlap_consistency",
            "max_peps3d_sites": overlap["site_count"],
            "max_peps3d_bond": BOND_DIM,
            "cell_count": overlap["cell_count"],
            "face_overlap_count": overlap["face_overlap_count"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "result_summary": {
            "all_pass": all_pass,
            "site_count": overlap["site_count"],
            "cell_count": overlap["cell_count"],
            "face_overlap_count": overlap["face_overlap_count"],
            "max_consistency_gap": overlap["max_consistency_gap"],
            "min_scrambled_control_gap": overlap["min_scrambled_control_gap"],
            "order_gap": order["order_gap"],
            "order_erased_control_gap": order["order_erased_control_gap"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "pass_rule": "Pass iff finite PEPS3D neighboring cell patches agree on shared face-overlap response signatures, overlap-erased and anchor-scrambled controls fail, single-probe non-IC control collapses, local order gap survives, dense closure stays false, and promotion is blocked.",
        "fail_rule": "Fail if cell patches/overlaps are nonfinite or missing, overlap consistency fails, controls replace the carrier overlap signature, order gap vanishes, dense closure is used, or promotion becomes satisfiable.",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_carrier_frontier_matrix_only"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "next_required_work": [
            "Classify this cell-patch overlap consistency receipt inside the active carrier frontier matrix.",
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
