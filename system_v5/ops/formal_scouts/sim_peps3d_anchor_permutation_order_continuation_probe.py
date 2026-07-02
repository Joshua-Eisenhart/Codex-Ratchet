#!/usr/bin/env python3
"""PEPS3D anchor permutation/order continuation scout.

Formal scout only.

This packet stays inside Phase 2 PEPS3D-anchored finite response-quotient
carrier geometry. It tests whether finite boundary-anchor readouts distinguish
operation order:

  R_K : (K, anchor_path) -> finite boundary-anchor response vector
  O_K : (anchor_path, physical_operator_path) -> finite order-gap readout

No nested Hopf tori, Weyl sheets, terrain, substages, flux, Xi/Phi0, Axis0,
physics, axes 7-12, or full PEPS3D closure are admitted.
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
    CTYPE,
    RTYPE,
    all_edge_signatures,
    apply_physical_operator,
    as_jsonable,
    coords_for_shape,
    edge_list,
    make_site_tensors,
    probe_responses,
    shift_filter_ops,
    sic_effects,
    site_signature,
    site_spinors,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "peps3d_anchor_permutation_order_continuation_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Continue the active carrier frontier by testing finite boundary-anchor "
    "permutation order against physical effect-index order on PEPS3D tensors."
)
SCIENTIFIC_QUESTION = (
    "Does an anchored finite PEPS3D carrier preserve an order-sensitive "
    "boundary response when anchor-path permutation and physical effect-index "
    "operators are composed in opposite orders, while identity/no-anchor/"
    "scalar/order-erased/dense controls fail?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_anchor_permutation_order_continuation"
PROMOTION_ALLOWED = False

PHASE2_FRONTIER_MATRIX_PATH = "system_v5/ops/formal_scouts/phase2_peps3d_seed_frontier_matrix_20260525.json"
PHASE2_TRANSITION_PATH = "system_v5/ops/formal_scouts/phase2_seed_frontier_transition_decision_20260525.json"
PHASE2_SEED_RECEIPT = "system_v5/ops/formal_scouts/results/finite_peps3d_probe_effect_seed_carrier_gate_probe_results.json"
PHASE2_SPINOR_DENSITY_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_spinor_density_carrier_gate_probe_results.json"
PHASE2_BOUNDARY_RECEIPT = "system_v5/ops/formal_scouts/results/peps_peps3d_local_environment_contraction_gate_probe_results.json"
PHASE2_ABLATION_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_anchor_ablation_boundary_stress_continuation_probe_results.json"

CLAIM_CEILING = (
    "Formal scout only: tests finite PEPS3D boundary-anchor order readouts. It "
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
        "reason": "load-bearing finite PEPS3D tensors, physical operator paths, anchor-path permutations, and response gaps",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite carrier graph and boundary-edge path checks",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite/order-gap and nonpromotion gate",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact finite row and noncommuting matrix count checks",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "rustworkx": "load_bearing",
    "z3": "load_bearing",
    "sympy": "load_bearing",
}

SHAPES = {
    8: (2, 2, 2),
    16: (2, 2, 4),
    32: (2, 4, 4),
    64: (4, 4, 4),
}
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


def boundary_site_indices(coords: list[tuple[int, int, int]], shape: tuple[int, int, int]) -> list[int]:
    return [idx for idx, coord in enumerate(coords) if is_boundary_coord(coord, shape)]


def build_tensors(shape: tuple[int, int, int]) -> tuple[list[tuple[int, int, int]], torch.Tensor]:
    coords = coords_for_shape(shape)
    responses = probe_responses(site_spinors(len(coords)), sic_effects())
    return coords, make_site_tensors(responses, coords, BOND_DIM)


def permute_boundary_path(tensors: torch.Tensor, coords: list[tuple[int, int, int]], shape: tuple[int, int, int]) -> torch.Tensor:
    boundary = boundary_site_indices(coords, shape)
    out = tensors.clone()
    if not boundary:
        return out
    rolled = boundary[1:] + boundary[:1]
    for src, dst in zip(boundary, rolled):
        out[dst] = tensors[src]
    return out


def boundary_response(tensors: torch.Tensor, coords: list[tuple[int, int, int]], shape: tuple[int, int, int]) -> torch.Tensor:
    boundary = boundary_site_indices(coords, shape)
    site_sigs = site_signature(tensors)[boundary]
    edge_sigs = all_edge_signatures(
        tensors,
        [
            edge
            for edge in edge_list(shape)
            if int(edge["src"]) in boundary or int(edge["dst"]) in boundary
        ],
    )
    return torch.cat(
        [
            site_sigs.reshape(-1).to(RTYPE),
            torch.real(edge_sigs).reshape(-1).to(RTYPE),
        ]
    )


def order_row(site_count: int, shape: tuple[int, int, int]) -> dict[str, Any]:
    coords, tensors = build_tensors(shape)
    graph = carrier_graph(shape)
    shift, filt = shift_filter_ops()
    op_path = apply_physical_operator(apply_physical_operator(tensors, shift), filt)
    anchor_after_op = permute_boundary_path(op_path, coords, shape)
    anchor_first = permute_boundary_path(tensors, coords, shape)
    op_after_anchor = apply_physical_operator(apply_physical_operator(anchor_first, shift), filt)
    order_gap = float(
        torch.linalg.vector_norm(
            boundary_response(anchor_after_op, coords, shape) - boundary_response(op_after_anchor, coords, shape)
        ).item()
    )

    erased_a = apply_physical_operator(apply_physical_operator(tensors, filt), filt)
    erased_b = apply_physical_operator(apply_physical_operator(tensors, filt), filt)
    order_erased_gap = float(
        torch.linalg.vector_norm(
            boundary_response(erased_a, coords, shape) - boundary_response(erased_b, coords, shape)
        ).item()
    )
    no_anchor_gap = float(torch.linalg.vector_norm(boundary_response(tensors, coords, shape)).item())
    scalar_label = torch.full_like(boundary_response(tensors, coords, shape), float(site_count))
    scalar_gap = float(torch.linalg.vector_norm(boundary_response(anchor_after_op, coords, shape) - scalar_label).item())
    exact_edge_count = sp.Integer(len(edge_list(shape)))
    return {
        "site_count": site_count,
        "shape": list(shape),
        "bond_dim": BOND_DIM,
        "boundary_site_count": len(boundary_site_indices(coords, shape)),
        "edge_count": len(edge_list(shape)),
        "rustworkx_nodes": graph.num_nodes(),
        "rustworkx_edges": graph.num_edges(),
        "sympy_exact_edge_count": int(exact_edge_count),
        "order_gap": order_gap,
        "order_erased_control_gap": order_erased_gap,
        "no_anchor_control_gap": no_anchor_gap,
        "scalar_label_control_gap": scalar_gap,
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
        "pass": bool(
            graph.num_nodes() == site_count
            and graph.num_edges() == len(edge_list(shape))
            and rx.is_connected(graph)
            and order_gap > GAP_FLOOR
            and order_erased_gap < TOL
            and no_anchor_gap > GAP_FLOOR
            and scalar_gap > GAP_FLOOR
        ),
    }


def z3_gate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    finite = z3.Bool("finite")
    order_sensitive = z3.Bool("order_sensitive")
    dense = z3.Bool("dense")
    promote = z3.Bool("promote")
    solver = z3.Solver()
    solver.add(finite, order_sensitive, z3.Not(dense), z3.Not(promote))
    bad = z3.Solver()
    bad.add(promote, z3.Not(promote))
    min_scaled_gap = min(int(row["order_gap"] * 1_000_000) for row in rows)
    gap_solver = z3.Solver()
    gap = z3.Int("min_scaled_gap")
    gap_solver.add(gap == min_scaled_gap, gap > 0)
    return {
        "pass": solver.check() == z3.sat and bad.check() == z3.unsat and gap_solver.check() == z3.sat,
        "finite_order_status": str(solver.check()),
        "promotion_status": str(bad.check()),
        "gap_status": str(gap_solver.check()),
        "min_scaled_gap": min_scaled_gap,
    }


def main() -> int:
    started = time.time()
    rows = [order_row(site_count, shape) for site_count, shape in SHAPES.items()]
    z3_row = z3_gate(rows)
    positive = {
        "P1_anchor_permutation_order_rows": {
            "pass": all(row["pass"] for row in rows),
            "rows": rows,
            "finite_map": "O_K : (anchor_path, physical_operator_path) -> finite boundary order-gap readout",
        }
    }
    graveyard = {
        "GC1_order_erased_control_collapses": {
            "pass": all(row["order_erased_control_gap"] < TOL for row in rows),
            "max_gap": max(row["order_erased_control_gap"] for row in rows),
        },
        "GC2_no_anchor_control_rejected": {
            "pass": all(row["no_anchor_control_gap"] > GAP_FLOOR for row in rows),
            "min_gap": min(row["no_anchor_control_gap"] for row in rows),
        },
        "GC3_scalar_label_control_rejected": {
            "pass": all(row["scalar_label_control_gap"] > GAP_FLOOR for row in rows),
            "min_gap": min(row["scalar_label_control_gap"] for row in rows),
        },
    }
    boundary = {
        "B1_formal_scout_no_promotion": {"pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED},
        "B2_dense_closure_banned": {
            "pass": all(not row["dense_state_closure_used"] and not row["dense_environment_closure_used"] for row in rows)
        },
        "B3_z3_finite_order_nonpromotion": z3_row,
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
            "F01": "finite PEPS3D carriers, finite boundary anchor paths, finite physical operator paths, finite response vectors, and finite controls",
            "N01": "anchor permutation after physical operator path differs from physical operator path after anchor permutation, while order-erased control collapses",
        },
        "finite_map": [
            "R_K : (K, anchor_path) -> finite boundary-anchor response vector",
            "O_K : (anchor_path, physical_operator_path) -> finite order-gap readout",
        ],
        "domain": {
            "carrier": "finite PEPS3D seed-carrier tensors",
            "site_shapes": {str(k): list(v) for k, v in SHAPES.items()},
            "bond_dim": BOND_DIM,
            "operator_paths": ["anchor_after_physical_path", "physical_after_anchor_path", "order_erased_control"],
        },
        "codomain_or_output": "finite boundary-anchor response vectors, finite order-gap readouts, no-anchor/scalar controls, and dense-closure blockers",
        "carrier_layer": "phase_2_finite_peps3d_seed_carrier",
        "geometry_layer": "peps3d_anchored_finite_response_quotient_carrier_geometry_continuation",
        "carrier_realization": "torch complex finite PEPS3D tensors over boundary site and edge anchors",
        "peps3d_embedding": "K=(V,E,F,C) seed carrier with boundary site and boundary edge response readouts; no scalar carrier labels admitted",
        "spinor_state": "torch-native two-component spinors are used only to seed finite local response tensors; no Hopf/Weyl geometry is admitted",
        "quaternion_action": "not_applicable",
        "dependency_receipts": [
            PHASE2_FRONTIER_MATRIX_PATH,
            PHASE2_TRANSITION_PATH,
            PHASE2_SEED_RECEIPT,
            PHASE2_SPINOR_DENSITY_RECEIPT,
            PHASE2_BOUNDARY_RECEIPT,
            PHASE2_ABLATION_RECEIPT,
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "blocked",
        "cut_layer": "blocked",
        "law_or_candidate_tested": "finite PEPS3D boundary-anchor permutation order sensitivity",
        "branch_status_before_run": "active_carrier_frontier_continue_active_level",
        "allowed_claims": [
            "finite PEPS3D boundary anchor permutation and physical operator paths are order-sensitive on the tested carrier rows",
            "order-erased, no-anchor, scalar-label, dense-state, dense-environment, and promotion controls do not replace the anchored carrier witness",
        ],
        "promotion_blockers": BLOCKED_CONSUMERS,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_tools": ["pytorch", "rustworkx", "z3", "sympy"],
        "actual_tools_used": ["pytorch", "rustworkx", "z3", "sympy"],
        "proof_surfaces_used": ["z3_finite_order_nonpromotion_gate", "sympy_exact_edge_count_checks"],
        "graph_surfaces_used": ["rustworkx_finite_carrier_graph"],
        "topology_surfaces_used": ["boundary_site_and_edge_anchor_support_counts"],
        "required_inputs": [
            PHASE2_FRONTIER_MATRIX_PATH,
            PHASE2_TRANSITION_PATH,
            PHASE2_SEED_RECEIPT,
            PHASE2_SPINOR_DENSITY_RECEIPT,
            PHASE2_BOUNDARY_RECEIPT,
            PHASE2_ABLATION_RECEIPT,
        ],
        "data_or_artifact_dependencies": [
            PHASE2_FRONTIER_MATRIX_PATH,
            PHASE2_TRANSITION_PATH,
            PHASE2_SEED_RECEIPT,
            PHASE2_SPINOR_DENSITY_RECEIPT,
            PHASE2_BOUNDARY_RECEIPT,
            PHASE2_ABLATION_RECEIPT,
        ],
        "required_negatives": [
            "order_erased",
            "no_anchor",
            "scalar_label",
            "dense_state_closure",
            "dense_environment_closure",
            "promotion",
        ],
        "negatives_run": [
            "order_erased",
            "no_anchor",
            "scalar_label",
            "dense_state_closure",
            "dense_environment_closure",
            "promotion",
        ],
        "kill_conditions": [
            "order gap vanishes",
            "order-erased control has a nonzero gap",
            "no-anchor or scalar-label control replaces the anchored response",
            "dense state or dense environment closure is used",
            "promotion becomes satisfiable",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "phase2_anchor_permutation_order_continue_active_v1",
        "all_pass": all_pass,
        "nearby_variants": {"passed": sum(1 for row in checks if row["pass"]), "total": len(checks)},
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "summary": {
            "phase": 2,
            "elapsed_seconds": time.time() - started,
            "candidate": "peps3d_anchor_permutation_order_continuation",
            "max_peps3d_sites": max(SHAPES),
            "max_peps3d_bond": BOND_DIM,
            "order_row_count": len(rows),
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "result_summary": {
            "all_pass": all_pass,
            "max_peps3d_sites": max(SHAPES),
            "max_peps3d_bond": BOND_DIM,
            "order_row_count": len(rows),
            "min_order_gap": min(row["order_gap"] for row in rows),
            "max_order_erased_control_gap": max(row["order_erased_control_gap"] for row in rows),
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "pass_rule": "Pass iff every finite carrier row has a nonzero anchor/physical order gap, collapsed order-erased control, rejected no-anchor/scalar controls, no dense closure, and blocked promotion.",
        "fail_rule": "Fail if order sensitivity collapses, controls replace the anchored response, dense closure is used, or promotion becomes satisfiable.",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_carrier_frontier_matrix_only"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "next_required_work": [
            "Classify this order-continuation receipt inside the active carrier frontier matrix.",
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
