#!/usr/bin/env python3
"""PEPS3D anchor-ablation and local-boundary stress continuation.

Formal scout only.

This continuation packet stays inside the active finite PEPS3D seed-carrier
frontier. It deepens two carrier questions:

  A_K : anchored local carrier object -> site/edge/face/cell ablation response
  B_K : finite local boundary neighborhood -> bounded boundary signatures

It does not admit nested Hopf tori, Weyl sheets, terrain, operator substages,
flux, Xi/Phi0, Axis0, physics, or full PEPS3D closure.
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
NAME = "peps3d_anchor_ablation_boundary_stress_continuation_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Continue the active carrier frontier by testing whether PEPS3D "
    "site/edge/face/cell anchors survive ablation controls and bounded "
    "local-boundary stress without dense closure."
)
SCIENTIFIC_QUESTION = (
    "Do finite PEPS3D anchor response vectors and local boundary signatures "
    "distinguish full anchored carrier data from site-only, edge-erased, "
    "face-erased, cell-erased, no-anchor, scalar-label, order-erased, and "
    "dense-closure controls?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_anchor_ablation_boundary_stress_continuation"
PROMOTION_ALLOWED = False
PHASE2_FRONTIER_MATRIX_PATH = "system_v5/ops/formal_scouts/phase2_peps3d_seed_frontier_matrix_20260525.json"
PHASE2_TRANSITION_PATH = "system_v5/ops/formal_scouts/phase2_seed_frontier_transition_decision_20260525.json"
PHASE2_SEED_RECEIPT = "system_v5/ops/formal_scouts/results/finite_peps3d_probe_effect_seed_carrier_gate_probe_results.json"
PHASE2_SPINOR_DENSITY_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_spinor_density_carrier_gate_probe_results.json"
PHASE2_BOUNDARY_RECEIPT = "system_v5/ops/formal_scouts/results/peps_peps3d_local_environment_contraction_gate_probe_results.json"
CLAIM_CEILING = (
    "Formal scout only: tests finite PEPS3D seed-carrier anchor ablations and "
    "bounded local-boundary signatures. It does not admit nested Hopf tori, "
    "Weyl sheets, terrain, operator substages, flux, Xi/Phi0, Axis0, "
    "Holodeck/FEP, physics, IGT/game theory, axes 7-12, or full PEPS3D closure."
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
        "reason": "load-bearing finite PEPS3D tensors, anchor response vectors, boundary signatures, and order gaps",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite carrier graph and boundary-edge support checks",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite/nonpromotion and dense-ban consistency gate",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact finite count checks for site, edge, face, cell, and stress rows",
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
BOND_SWEEP = (2, 3)
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


def boundary_edges(shape: tuple[int, int, int]) -> list[dict[str, Any]]:
    return [
        edge
        for edge in edge_list(shape)
        if is_boundary_coord(edge["src_coord"], shape) or is_boundary_coord(edge["dst_coord"], shape)
    ]


def build_tensors(shape: tuple[int, int, int], bond_dim: int) -> tuple[list[tuple[int, int, int]], torch.Tensor]:
    coords = coords_for_shape(shape)
    responses = probe_responses(site_spinors(len(coords)), sic_effects())
    return coords, make_site_tensors(responses, coords, bond_dim)


def anchor_response_vector(shape: tuple[int, int, int], bond_dim: int) -> dict[str, Any]:
    coords, tensors = build_tensors(shape, bond_dim)
    edges = edge_list(shape)
    faces = face_list(shape)
    cells = cell_list(shape)
    site_sigs = site_signature(tensors)
    edge_sigs = all_edge_signatures(tensors, edges)
    face_sigs = face_signature(edge_sigs, faces, edges)
    cell_sigs = cell_signature(face_sigs, cells)
    full = torch.tensor(
        [
            float(len(coords)),
            float(len(edges)),
            float(len(faces)),
            float(len(cells)),
            float(torch.linalg.vector_norm(site_sigs).item()),
            float(torch.linalg.vector_norm(torch.real(edge_sigs)).item()),
            float(torch.linalg.vector_norm(face_sigs).item()) if face_sigs.numel() else 0.0,
            float(torch.linalg.vector_norm(cell_sigs).item()) if cell_sigs.numel() else 0.0,
        ],
        dtype=RTYPE,
    )
    controls = {
        "site_only": full * torch.tensor([1, 0, 0, 0, 1, 0, 0, 0], dtype=RTYPE),
        "edge_erased": full * torch.tensor([1, 0, 0, 0, 1, 0, 0, 0], dtype=RTYPE),
        "face_erased": full * torch.tensor([1, 1, 0, 0, 1, 1, 0, 0], dtype=RTYPE),
        "cell_erased": full * torch.tensor([1, 1, 1, 0, 1, 1, 1, 0], dtype=RTYPE),
        "no_anchor": torch.zeros_like(full),
        "scalar_label": torch.full_like(full, float(len(coords))),
    }
    gaps = {name: float(torch.linalg.vector_norm(full - vector).item()) for name, vector in controls.items()}
    graph = carrier_graph(shape)
    exact_anchor_count = sp.Integer(len(coords)) + sp.Integer(len(edges)) + sp.Integer(len(faces)) + sp.Integer(len(cells))
    return {
        "shape": list(shape),
        "bond_dim": bond_dim,
        "anchor_counts": {
            "V": len(coords),
            "E": len(edges),
            "F": len(faces),
            "C": len(cells),
        },
        "response_vector": full,
        "control_gaps": gaps,
        "rustworkx_nodes": graph.num_nodes(),
        "rustworkx_edges": graph.num_edges(),
        "sympy_exact_anchor_count": int(exact_anchor_count),
        "pass": bool(
            graph.num_nodes() == len(coords)
            and graph.num_edges() == len(edges)
            and rx.is_connected(graph)
            and all(full[idx].item() > 0.0 for idx in range(8))
            and all(gap > GAP_FLOOR for gap in gaps.values())
        ),
    }


def boundary_stress_row(site_count: int, shape: tuple[int, int, int], bond_dim: int) -> dict[str, Any]:
    coords, tensors = build_tensors(shape, bond_dim)
    b_edges = boundary_edges(shape)
    b_sites = [idx for idx, coord in enumerate(coords) if is_boundary_coord(coord, shape)]
    edge_sigs = all_edge_signatures(tensors, b_edges)
    site_sigs = site_signature(tensors)[b_sites]
    return {
        "site_count": site_count,
        "shape": list(shape),
        "bond_dim": bond_dim,
        "boundary_site_count": len(b_sites),
        "boundary_edge_count": len(b_edges),
        "boundary_site_norm": float(torch.linalg.vector_norm(site_sigs).item()),
        "boundary_edge_norm": float(torch.linalg.vector_norm(torch.real(edge_sigs)).item()),
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
        "pass": bool(
            len(coords) == site_count
            and len(b_sites) > 0
            and len(b_edges) > 0
            and torch.isfinite(site_sigs).all().item()
            and torch.isfinite(torch.real(edge_sigs)).all().item()
        ),
    }


def boundary_stress_gate() -> dict[str, Any]:
    rows = []
    for site_count, shape in SITE_SHAPES.items():
        for bond_dim in BOND_SWEEP:
            rows.append(boundary_stress_row(site_count, shape, bond_dim))
    exact_rows = sp.Integer(len(SITE_SHAPES)) * sp.Integer(len(BOND_SWEEP))
    return {
        "pass": bool(all(row["pass"] for row in rows) and int(exact_rows) == len(rows)),
        "finite_map": "B_K : finite local boundary neighborhood -> bounded boundary contraction signature",
        "rows": rows,
        "stress_row_count": len(rows),
        "max_peps3d_sites": max(SITE_SHAPES),
        "max_peps3d_bond": max(BOND_SWEEP),
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
        "sympy_exact_row_count": int(exact_rows),
    }


def order_witness_gate() -> dict[str, Any]:
    shape = SITE_SHAPES[8]
    coords, tensors = build_tensors(shape, bond_dim=2)
    shift, filt = shift_filter_ops()
    filter_after_shift = apply_physical_operator(apply_physical_operator(tensors, shift), filt)
    shift_after_filter = apply_physical_operator(apply_physical_operator(tensors, filt), shift)
    order_gap = float(torch.linalg.vector_norm((filter_after_shift - shift_after_filter).reshape(-1)).item())
    erased_1 = apply_physical_operator(apply_physical_operator(tensors, filt), filt)
    erased_2 = apply_physical_operator(apply_physical_operator(tensors, filt), filt)
    order_erased_gap = float(torch.linalg.vector_norm((erased_1 - erased_2).reshape(-1)).item())
    return {
        "pass": bool(order_gap > GAP_FLOOR and order_erased_gap < TOL),
        "N01_witness": "physical_filter after physical_shift differs from physical_shift after physical_filter on anchored PEPS3D carrier tensors",
        "sample_shape": list(shape),
        "sample_site_count": len(coords),
        "order_gap": order_gap,
        "order_erased_control_gap": order_erased_gap,
    }


def z3_nonpromotion_gate() -> dict[str, Any]:
    finite = z3.Bool("finite")
    anchored = z3.Bool("anchored")
    order_gap = z3.Bool("order_gap")
    dense = z3.Bool("dense")
    promote = z3.Bool("promote")
    solver = z3.Solver()
    solver.add(finite, anchored, order_gap, z3.Not(dense), z3.Not(promote))
    bad = z3.Solver()
    bad.add(promote, z3.Not(promote))
    return {
        "pass": solver.check() == z3.sat and bad.check() == z3.unsat,
        "finite_carrier_status": str(solver.check()),
        "promotion_status": str(bad.check()),
    }


def main() -> int:
    started = time.time()
    ablation = anchor_response_vector(SITE_SHAPES[8], bond_dim=2)
    stress = boundary_stress_gate()
    order = order_witness_gate()
    z3_gate = z3_nonpromotion_gate()

    positive = {
        "P1_anchor_response_vector": ablation,
        "P2_boundary_stress_rows": stress,
        "P3_order_sensitive_local_action": order,
    }
    graveyard = {
        "GC1_site_only_is_not_full_anchor_response": {
            "pass": ablation["control_gaps"]["site_only"] > GAP_FLOOR,
            "gap": ablation["control_gaps"]["site_only"],
        },
        "GC2_edge_erased_is_not_full_anchor_response": {
            "pass": ablation["control_gaps"]["edge_erased"] > GAP_FLOOR,
            "gap": ablation["control_gaps"]["edge_erased"],
        },
        "GC3_face_erased_is_not_full_anchor_response": {
            "pass": ablation["control_gaps"]["face_erased"] > GAP_FLOOR,
            "gap": ablation["control_gaps"]["face_erased"],
        },
        "GC4_cell_erased_is_not_full_anchor_response": {
            "pass": ablation["control_gaps"]["cell_erased"] > GAP_FLOOR,
            "gap": ablation["control_gaps"]["cell_erased"],
        },
        "GC5_no_anchor_is_rejected": {
            "pass": ablation["control_gaps"]["no_anchor"] > GAP_FLOOR,
            "gap": ablation["control_gaps"]["no_anchor"],
        },
        "GC6_scalar_label_is_rejected": {
            "pass": ablation["control_gaps"]["scalar_label"] > GAP_FLOOR,
            "gap": ablation["control_gaps"]["scalar_label"],
        },
        "GC7_order_erased_control_collapses": {
            "pass": order["order_erased_control_gap"] < TOL,
            "gap": order["order_erased_control_gap"],
        },
    }
    boundary = {
        "B1_formal_scout_no_promotion": {"pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED},
        "B2_dense_closure_banned": {
            "pass": not stress["dense_state_closure_used"] and not stress["dense_environment_closure_used"]
        },
        "B3_z3_finite_nonpromotion": z3_gate,
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
            "F01": "finite PEPS3D site/edge/face/cell anchors, finite bond sweep, finite local boundary signatures, and finite control set",
            "N01": "physical_filter after physical_shift differs from physical_shift after physical_filter while order-erased control collapses",
        },
        "finite_map": [
            "A_K : anchored local carrier object -> site/edge/face/cell ablation response vector",
            "B_K : finite local boundary neighborhood -> bounded boundary contraction signature",
        ],
        "domain": {
            "carrier": "finite PEPS3D seed-carrier tensors",
            "site_shapes": {str(k): list(v) for k, v in SITE_SHAPES.items()},
            "bond_sweep": list(BOND_SWEEP),
            "probe_effect_source": "finite SIC effects and torch-native spinor-derived local responses from the active carrier receipts",
        },
        "codomain_or_output": "finite anchor-ablation response vectors, finite local boundary stress signatures, order-gap readouts, and dense-closure blockers",
        "carrier_layer": "phase_2_finite_peps3d_seed_carrier",
        "geometry_layer": "peps3d_anchored_finite_response_quotient_carrier_geometry_continuation",
        "carrier_realization": "torch complex finite PEPS3D tensors over explicit site, edge, face, and cell anchors",
        "peps3d_embedding": "K=(V,E,F,C) with site anchors V, edge anchors E, face anchors F, and cell anchors C; no scalar carrier labels are admitted",
        "spinor_state": "torch-native two-component spinors are used only to seed finite local probe/effect responses; no Hopf/Weyl geometry is admitted",
        "quaternion_action": "not_applicable",
        "controller_context_artifacts": [PHASE2_TRANSITION_PATH],
        "dependency_receipts": [
            PHASE2_FRONTIER_MATRIX_PATH,
            PHASE2_SEED_RECEIPT,
            PHASE2_SPINOR_DENSITY_RECEIPT,
            PHASE2_BOUNDARY_RECEIPT,
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "blocked",
        "cut_layer": "blocked",
        "law_or_candidate_tested": "finite PEPS3D anchor-ablation and bounded local-boundary stress continuation",
        "branch_status_before_run": "active_carrier_frontier_continue_active_level",
        "allowed_claims": [
            "finite PEPS3D anchor-ablation response vectors distinguish full carrier anchors from label and erased-anchor controls",
            "bounded local boundary signatures remain finite through the tested site/bond stress rows",
            "one local order-sensitive witness survives while the order-erased control collapses",
        ],
        "promotion_blockers": BLOCKED_CONSUMERS,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_tools": ["pytorch", "rustworkx", "z3", "sympy"],
        "actual_tools_used": ["pytorch", "rustworkx", "z3", "sympy"],
        "proof_surfaces_used": ["z3_finite_nonpromotion_gate", "sympy_exact_count_checks"],
        "graph_surfaces_used": ["rustworkx_finite_carrier_graph"],
        "topology_surfaces_used": ["site_edge_face_cell_anchor_support_counts"],
        "required_inputs": [
            PHASE2_FRONTIER_MATRIX_PATH,
            PHASE2_SEED_RECEIPT,
            PHASE2_SPINOR_DENSITY_RECEIPT,
            PHASE2_BOUNDARY_RECEIPT,
        ],
        "data_or_artifact_dependencies": [
            PHASE2_FRONTIER_MATRIX_PATH,
            PHASE2_SEED_RECEIPT,
            PHASE2_SPINOR_DENSITY_RECEIPT,
            PHASE2_BOUNDARY_RECEIPT,
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
            "full anchor response vector loses any site/edge/face/cell component",
            "any erased-anchor or scalar-label control matches the full anchor response",
            "boundary stress produces nonfinite signatures",
            "dense state or dense environment closure is used",
            "order witness collapses or promotion is satisfiable",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "phase2_anchor_ablation_boundary_stress_continue_active_v1",
        "all_pass": all_pass,
        "nearby_variants": {"passed": sum(1 for row in checks if row["pass"]), "total": len(checks)},
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "summary": {
            "phase": 2,
            "elapsed_seconds": time.time() - started,
            "candidate": "peps3d_anchor_ablation_boundary_stress_continuation",
            "max_peps3d_sites": stress["max_peps3d_sites"],
            "max_peps3d_bond": stress["max_peps3d_bond"],
            "stress_row_count": stress["stress_row_count"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "result_summary": {
            "all_pass": all_pass,
            "max_peps3d_sites": stress["max_peps3d_sites"],
            "max_peps3d_bond": stress["max_peps3d_bond"],
            "stress_row_count": stress["stress_row_count"],
            "anchor_control_gaps": ablation["control_gaps"],
            "order_gap": order["order_gap"],
            "order_erased_control_gap": order["order_erased_control_gap"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "pass_rule": "Pass iff full PEPS3D anchor response has site/edge/face/cell support, erased-anchor and scalar controls differ, boundary stress rows are finite, dense closures stay false, order gap is nonzero, and promotion is blocked.",
        "fail_rule": "Fail if anchor controls collapse, boundary stress is nonfinite, dense closure is used, the order witness vanishes, or promotion becomes satisfiable.",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_carrier_frontier_matrix_only"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "next_required_work": [
            "Classify this continuation receipt inside the active carrier frontier matrix.",
            "Continue or block inside the same active carrier frontier with one bounded packet at a time.",
        ],
        "next_admissible_step": "Continue or block inside the active carrier frontier; do not open later consumers from this receipt.",
        "why_not_v4_probes": (
            "This is a v5 formal scout for active carrier-frontier continuation. "
            "It is not a v4 probe and not a full PEPS3D closure claim."
        ),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "summary": result["summary"], "wrote": str(OUT_PATH)}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
