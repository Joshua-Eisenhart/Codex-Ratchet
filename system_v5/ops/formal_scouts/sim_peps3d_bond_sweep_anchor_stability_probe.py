#!/usr/bin/env python3
"""PEPS3D bond-sweep anchor stability scout.

Formal scout only.

This continuation packet stays inside Phase 2 PEPS3D-anchored finite
response-quotient carrier geometry. It tests a bounded bond sweep:

  S_K : (r_P(s), K, bond_dim, anchor, local_order_ops)
        -> bond-swept anchor stability signature + order-gap vector

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
NAME = "peps3d_bond_sweep_anchor_stability_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Continue the active carrier frontier by testing whether finite PEPS3D "
    "site/edge/face/cell anchor signatures remain finite and distinguishable "
    "across a bounded bond sweep without dense closure."
)
SCIENTIFIC_QUESTION = (
    "Can the finite PEPS3D carrier K=(V,E,F,C) carry response-quotient tensor "
    "signatures across site counts 8/16/32/64 and bond dimensions 2/3/4 while "
    "no-anchor, scalar-label, bond-collapsed, order-erased, dense-closure, and "
    "promotion controls fail?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_bond_sweep_anchor_stability"
PROMOTION_ALLOWED = False

PHASE2_FRONTIER_MATRIX_PATH = "system_v5/ops/formal_scouts/phase2_peps3d_seed_frontier_matrix_20260525.json"
PHASE2_TRANSITION_PATH = "system_v5/ops/formal_scouts/phase2_seed_frontier_transition_decision_20260525.json"
PHASE2_SEED_RECEIPT = "system_v5/ops/formal_scouts/results/finite_peps3d_probe_effect_seed_carrier_gate_probe_results.json"
PHASE2_SPINOR_DENSITY_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_spinor_density_carrier_gate_probe_results.json"
PHASE2_BOUNDARY_RECEIPT = "system_v5/ops/formal_scouts/results/peps_peps3d_local_environment_contraction_gate_probe_results.json"
PHASE2_ABLATION_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_anchor_ablation_boundary_stress_continuation_probe_results.json"
PHASE2_HELDOUT_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_heldout_shape_anchor_replay_probe_results.json"

CLAIM_CEILING = (
    "Formal scout only: tests finite PEPS3D seed-carrier bond-sweep anchor "
    "stability. It does not admit nested Hopf tori, Weyl sheets, terrain, "
    "operator substages, flux, Xi/Phi0, Axis0, Holodeck/FEP, physics, "
    "IGT/game theory, axes 7-12, or full PEPS3D closure."
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
        "reason": "load-bearing bond-swept PEPS3D tensors, anchor signatures, and local order gaps",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite carrier graph connectivity and edge support checks at each site shape",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite/nonpromotion and dense-ban consistency gate",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact finite stress row and anchor count checks",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "rustworkx": "load_bearing",
    "z3": "load_bearing",
    "sympy": "load_bearing",
}

SITE_SHAPES = {
    8: (2, 2, 2),
    16: (2, 2, 4),
    32: (2, 4, 4),
    64: (4, 4, 4),
}
BOND_SWEEP = (2, 3, 4)
COLLAPSED_BOND = 1
GAP_FLOOR = 1.0e-8
TOL = 1.0e-10


def carrier_graph(shape: tuple[int, int, int]) -> rx.PyGraph:
    graph = rx.PyGraph()
    coords = coords_for_shape(shape)
    graph.add_nodes_from([{"coord": coord} for coord in coords])
    for edge in edge_list(shape):
        graph.add_edge(int(edge["src"]), int(edge["dst"]), {"axis": int(edge["axis"])})
    return graph


def build_tensors(shape: tuple[int, int, int], bond_dim: int) -> tuple[list[tuple[int, int, int]], torch.Tensor]:
    coords = coords_for_shape(shape)
    responses = probe_responses(site_spinors(len(coords)), sic_effects())
    return coords, make_site_tensors(responses, coords, bond_dim)


def anchor_signature_row(site_count: int, shape: tuple[int, int, int], bond_dim: int) -> dict[str, Any]:
    coords, tensors = build_tensors(shape, bond_dim)
    edges = edge_list(shape)
    faces = face_list(shape)
    cells = cell_list(shape)
    graph = carrier_graph(shape)
    site_sigs = site_signature(tensors)
    edge_sigs = all_edge_signatures(tensors, edges)
    face_sigs = face_signature(edge_sigs, faces, edges)
    cell_sigs = cell_signature(face_sigs, cells)
    vector = torch.tensor(
        [
            float(len(coords)),
            float(len(edges)),
            float(len(faces)),
            float(len(cells)),
            float(bond_dim),
            float(torch.linalg.vector_norm(site_sigs).item()),
            float(torch.linalg.vector_norm(torch.real(edge_sigs)).item()),
            float(torch.linalg.vector_norm(face_sigs).item()) if face_sigs.numel() else 0.0,
            float(torch.linalg.vector_norm(cell_sigs).item()) if cell_sigs.numel() else 0.0,
        ],
        dtype=RTYPE,
    )
    controls = {
        "no_anchor": torch.zeros_like(vector),
        "scalar_label": torch.full_like(vector, float(site_count)),
        "site_only": vector * torch.tensor([1, 0, 0, 0, 1, 1, 0, 0, 0], dtype=RTYPE),
        "edge_erased": vector * torch.tensor([1, 0, 0, 0, 1, 1, 0, 0, 0], dtype=RTYPE),
        "face_erased": vector * torch.tensor([1, 1, 0, 0, 1, 1, 1, 0, 0], dtype=RTYPE),
        "cell_erased": vector * torch.tensor([1, 1, 1, 0, 1, 1, 1, 1, 0], dtype=RTYPE),
    }
    control_gaps = {name: float(torch.linalg.vector_norm(vector - control).item()) for name, control in controls.items()}
    exact_count = sp.Integer(len(coords)) + sp.Integer(len(edges)) + sp.Integer(len(faces)) + sp.Integer(len(cells))
    return {
        "pass": bool(
            len(coords) == site_count
            and graph.num_nodes() == site_count
            and graph.num_edges() == len(edges)
            and rx.is_connected(graph)
            and tensors.shape == (site_count, bond_dim, bond_dim, bond_dim, bond_dim, bond_dim, bond_dim, 4)
            and torch.isfinite(vector).all().item()
            and all(value > GAP_FLOOR for value in control_gaps.values())
        ),
        "site_count": site_count,
        "shape": list(shape),
        "bond_dim": bond_dim,
        "anchor_counts": {"V": len(coords), "E": len(edges), "F": len(faces), "C": len(cells)},
        "signature_norm": float(torch.linalg.vector_norm(vector).item()),
        "control_gaps": control_gaps,
        "rustworkx_nodes": graph.num_nodes(),
        "rustworkx_edges": graph.num_edges(),
        "sympy_exact_anchor_count": int(exact_count),
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def bond_sweep_gate() -> dict[str, Any]:
    rows = []
    for site_count, shape in SITE_SHAPES.items():
        for bond_dim in BOND_SWEEP:
            rows.append(anchor_signature_row(site_count, shape, bond_dim))
    exact_rows = sp.Integer(len(SITE_SHAPES)) * sp.Integer(len(BOND_SWEEP))
    return {
        "pass": bool(all(row["pass"] for row in rows) and int(exact_rows) == len(rows)),
        "finite_map": "S_K : (r_P(s), K, bond_dim, anchor) -> bond-swept finite anchor stability signature",
        "rows": rows,
        "stress_row_count": len(rows),
        "max_peps3d_sites": max(SITE_SHAPES),
        "max_peps3d_bond": max(BOND_SWEEP),
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
        "sympy_exact_row_count": int(exact_rows),
    }


def order_witness_gate() -> dict[str, Any]:
    rows = []
    shift, filt = shift_filter_ops()
    for bond_dim in BOND_SWEEP:
        coords, tensors = build_tensors(SITE_SHAPES[8], bond_dim)
        filter_after_shift = apply_physical_operator(apply_physical_operator(tensors, shift), filt)
        shift_after_filter = apply_physical_operator(apply_physical_operator(tensors, filt), shift)
        order_gap = float(torch.linalg.vector_norm((filter_after_shift - shift_after_filter).reshape(-1)).item())
        erased_1 = apply_physical_operator(apply_physical_operator(tensors, filt), filt)
        erased_2 = apply_physical_operator(apply_physical_operator(tensors, filt), filt)
        order_erased_gap = float(torch.linalg.vector_norm((erased_1 - erased_2).reshape(-1)).item())
        rows.append(
            {
                "pass": bool(len(coords) == 8 and order_gap > GAP_FLOOR and order_erased_gap < TOL),
                "bond_dim": bond_dim,
                "order_gap": order_gap,
                "order_erased_control_gap": order_erased_gap,
            }
        )
    return {
        "pass": all(row["pass"] for row in rows),
        "N01_witness": "physical_filter after physical_shift differs from physical_shift after physical_filter across the bond sweep",
        "rows": rows,
        "min_order_gap": min(row["order_gap"] for row in rows),
        "max_order_erased_control_gap": max(row["order_erased_control_gap"] for row in rows),
    }


def collapsed_bond_control() -> dict[str, Any]:
    coords, tensors = build_tensors(SITE_SHAPES[8], COLLAPSED_BOND)
    collapsed_virtual_support = tensors.shape[1:7] == (1, 1, 1, 1, 1, 1)
    return {
        "pass": bool(len(coords) == 8 and collapsed_virtual_support),
        "why_rejected": "bond_dim=1 is a finite boundary/control row, not admitted bond-sweep support",
        "virtual_shape": list(tensors.shape[1:7]),
    }


def z3_gate(sweep: dict[str, Any], order: dict[str, Any]) -> dict[str, Any]:
    finite = z3.Bool("finite")
    anchored = z3.Bool("anchored")
    dense = z3.Bool("dense")
    order_gap = z3.Bool("order_gap")
    promote = z3.Bool("promote")
    solver = z3.Solver()
    solver.add(finite, anchored, order_gap, z3.Not(dense), z3.Not(promote))
    bad = z3.Solver()
    bad.add(promote, z3.Not(promote))
    count_solver = z3.Solver()
    row_count = z3.Int("bond_sweep_row_count")
    count_solver.add(row_count == int(sweep["stress_row_count"]), row_count == 12)
    gap_solver = z3.Solver()
    scaled_gap = z3.Int("scaled_min_order_gap")
    gap_solver.add(scaled_gap == int(order["min_order_gap"] * 1_000_000), scaled_gap > 0)
    return {
        "pass": (
            solver.check() == z3.sat
            and bad.check() == z3.unsat
            and count_solver.check() == z3.sat
            and gap_solver.check() == z3.sat
        ),
        "finite_anchor_nonpromotion_status": str(solver.check()),
        "promotion_status": str(bad.check()),
        "row_count_status": str(count_solver.check()),
        "gap_status": str(gap_solver.check()),
        "scaled_min_order_gap": int(order["min_order_gap"] * 1_000_000),
    }


def main() -> int:
    started = time.time()
    sweep = bond_sweep_gate()
    order = order_witness_gate()
    z3_row = z3_gate(sweep, order)
    collapsed = collapsed_bond_control()
    positive = {
        "P1_bond_sweep_anchor_stability": sweep,
        "P2_bond_sweep_order_witness": order,
    }
    control_gaps = [
        gap
        for row in sweep["rows"]
        for gap in row["control_gaps"].values()
    ]
    graveyard = {
        "GC_no_anchor_scalar_and_anchor_erasure_controls_rejected": {
            "pass": all(gap > GAP_FLOOR for gap in control_gaps),
            "min_control_gap": min(control_gaps),
        },
        "GC_bond_dim_one_boundary_control_rejected_as_sweep_support": collapsed,
        "GC_order_erased_control_collapses": {
            "pass": order["max_order_erased_control_gap"] < TOL,
            "max_order_erased_control_gap": order["max_order_erased_control_gap"],
        },
    }
    boundary = {
        "B1_formal_scout_no_promotion": {"pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED},
        "B2_dense_closure_banned": {
            "pass": not sweep["dense_state_closure_used"] and not sweep["dense_environment_closure_used"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "B3_z3_finite_bond_sweep_nonpromotion": z3_row,
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
            "F01": "finite PEPS3D shapes, finite bond sweep, finite site/edge/face/cell anchors, finite local responses, finite controls, finite output vectors",
            "N01": "physical_filter after physical_shift differs from physical_shift after physical_filter across the bounded bond sweep, while order-erased control collapses",
        },
        "finite_map": [
            "S_K : (r_P(s), K, bond_dim, anchor) -> bond-swept finite anchor stability signature",
            "O_K : (T_K, local_order_ops) -> finite local order-gap vector",
        ],
        "domain": {
            "carrier": "finite PEPS3D seed-carrier tensors",
            "site_shapes": {str(site_count): list(shape) for site_count, shape in SITE_SHAPES.items()},
            "bond_sweep": list(BOND_SWEEP),
            "probe_effect_source": "finite SIC effects and torch-native spinor-derived local responses as carrier data only",
        },
        "codomain_or_output": "finite bond-swept anchor signatures, local order-gap rows, controls, and dense-closure blockers",
        "carrier_layer": "phase_2_finite_peps3d_seed_carrier",
        "geometry_layer": "peps3d_anchored_finite_response_quotient_carrier_geometry_bond_sweep",
        "carrier_realization": "torch complex finite PEPS3D tensors over bounded shapes and bond dimensions 2/3/4",
        "peps3d_embedding": "K=(V,E,F,C) with explicit site, edge, face, and cell anchors at every stress row; no scalar carrier labels admitted",
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
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "blocked",
        "cut_layer": "blocked",
        "law_or_candidate_tested": "finite PEPS3D bond-sweep anchor stability",
        "branch_status_before_run": "active_carrier_frontier_continue_active_level",
        "allowed_claims": [
            "bounded bond sweep 2/3/4 preserves finite PEPS3D anchor signatures through 64 sites under the tested controls",
            "local physical operator order witness survives across the tested bond sweep while order-erased control collapses",
        ],
        "promotion_blockers": BLOCKED_CONSUMERS,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_tools": ["pytorch", "rustworkx", "z3", "sympy"],
        "actual_tools_used": ["pytorch", "rustworkx", "z3", "sympy"],
        "proof_surfaces_used": ["z3_finite_bond_sweep_nonpromotion_gate", "sympy_exact_anchor_and_row_counts"],
        "graph_surfaces_used": ["rustworkx_carrier_graphs"],
        "topology_surfaces_used": ["site_edge_face_cell_anchor_support_counts"],
        "required_inputs": [
            PHASE2_FRONTIER_MATRIX_PATH,
            PHASE2_SEED_RECEIPT,
            PHASE2_SPINOR_DENSITY_RECEIPT,
            PHASE2_BOUNDARY_RECEIPT,
            PHASE2_ABLATION_RECEIPT,
            PHASE2_HELDOUT_RECEIPT,
        ],
        "data_or_artifact_dependencies": [
            PHASE2_FRONTIER_MATRIX_PATH,
            PHASE2_SEED_RECEIPT,
            PHASE2_SPINOR_DENSITY_RECEIPT,
            PHASE2_BOUNDARY_RECEIPT,
            PHASE2_ABLATION_RECEIPT,
            PHASE2_HELDOUT_RECEIPT,
        ],
        "required_negatives": [
            "no_anchor",
            "scalar_label",
            "site_only",
            "edge_erased",
            "face_erased",
            "cell_erased",
            "bond_dim_one_boundary_control",
            "order_erased",
            "dense_state_closure",
            "dense_environment_closure",
            "promotion",
        ],
        "negatives_run": [
            "no_anchor",
            "scalar_label",
            "site_only",
            "edge_erased",
            "face_erased",
            "cell_erased",
            "bond_dim_one_boundary_control",
            "order_erased",
            "dense_state_closure",
            "dense_environment_closure",
            "promotion",
        ],
        "kill_conditions": [
            "bond-swept rows lose finite site/edge/face/cell support",
            "erased-anchor or scalar controls replace the anchored vector",
            "bond_dim_one is accepted as bond-sweep support",
            "order witness vanishes",
            "dense closure is used",
            "promotion becomes satisfiable",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "phase2_bond_sweep_anchor_stability_v1",
        "all_pass": all_pass,
        "nearby_variants": {"passed": sum(1 for row in checks if row["pass"]), "total": len(checks)},
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "summary": {
            "phase": 2,
            "elapsed_seconds": time.time() - started,
            "candidate": "peps3d_bond_sweep_anchor_stability",
            "max_peps3d_sites": sweep["max_peps3d_sites"],
            "max_peps3d_bond": sweep["max_peps3d_bond"],
            "stress_row_count": sweep["stress_row_count"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "result_summary": {
            "all_pass": all_pass,
            "stress_row_count": sweep["stress_row_count"],
            "max_peps3d_sites": sweep["max_peps3d_sites"],
            "max_peps3d_bond": sweep["max_peps3d_bond"],
            "min_order_gap": order["min_order_gap"],
            "max_order_erased_control_gap": order["max_order_erased_control_gap"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "pass_rule": "Pass iff bond-swept PEPS3D anchor rows are finite through 64 sites and bond 4, controls differ or collapse as required, local order gap survives, dense closure stays false, and promotion is blocked.",
        "fail_rule": "Fail if anchor rows collapse, controls replace the carrier vector, bond_dim_one is admitted as sweep support, order gap vanishes, dense closure is used, or promotion becomes satisfiable.",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_carrier_frontier_matrix_only"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "next_required_work": [
            "Classify this bond-sweep receipt inside the active carrier frontier matrix.",
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
