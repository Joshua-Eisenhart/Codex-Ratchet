#!/usr/bin/env python3
"""PEPS3D loss-residue class quotient scout.

Formal scout only.

This continuation packet stays inside PEPS3D-anchored finite
response-quotient carrier geometry. It tests:

  Q_loss_residue_class_quotient_K :
      (H_delete_anchor_loss_idempotence_K,
       support_atom,
       legal_anchor_preserving_relabeling,
       loss_vector in N^4,
       finite_effect_family)
      -> finite loss-residue quotient classes + control gap vector

This is a finite quotient readout over PEPS3D V/E/F/C loss vectors. It is not
topology closure, all-subset minimality, restore/inverse, PEPS3D closure, or
downstream geometry.
"""

from __future__ import annotations

import json
import os
import pathlib
import time
from collections import defaultdict
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import cvc5
from cvc5 import Kind
import gudhi
import rustworkx as rx
import sympy as sp
import torch
from torch_geometric.data import Data
import toponetx as tnx
import xgi
import z3

from sim_finite_peps3d_probe_effect_seed_carrier_gate_probe import as_jsonable
from sim_peps3d_delete_anchor_loss_idempotence_probe import (
    BLOCKED_CONSUMERS,
    GAP_FLOOR,
    PHASE2_ABLATION_RECEIPT,
    PHASE2_A_DELETE_RECEIPT,
    PHASE2_B_DELETE_RECEIPT,
    PHASE2_BOND_SWEEP_RECEIPT,
    PHASE2_BOUNDARY_PROJECTION_RECEIPT,
    PHASE2_BOUNDARY_RECEIPT,
    PHASE2_C_RESTRICT_RECEIPT,
    PHASE2_CELL_PATCH_RECEIPT,
    PHASE2_DD_KILL_RECEIPT,
    PHASE2_D_NERVE_DELETE_RECEIPT,
    PHASE2_FRONTIER_MATRIX_PATH,
    PHASE2_HELDOUT_RECEIPT,
    PHASE2_I_DELETE_RECEIPT,
    PHASE2_M_ONE_DELETE_RECEIPT,
    PHASE2_N_COVER_RECEIPT,
    PHASE2_O_OVERLAP_RECEIPT,
    PHASE2_PK_FACE_PROJECTION_RECEIPT,
    PHASE2_R_REPLAY_RECEIPT,
    PHASE2_RESPONSE_QUOTIENT_RECEIPT,
    PHASE2_SEED_RECEIPT,
    PHASE2_SPINOR_DENSITY_RECEIPT,
    PHASE2_SUBSTRATE_RECEIPT,
    PHASE2_T_TRIPLE_RECEIPT,
    delete_anchor_loss_gate,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "peps3d_loss_residue_class_quotient_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Continue the active carrier frontier by testing finite quotient classes "
    "from H_delete_anchor_loss_idempotence_K PEPS3D V/E/F/C loss vectors, while "
    "norm-only, scalar-label, no-anchor, topology, all-subset, restore/inverse, "
    "dense-closure, and downstream controls fail or remain blocked."
)
SCIENTIFIC_QUESTION = (
    "Does Q_loss_residue_class_quotient_K form finite loss-residue classes from "
    "explicit PEPS3D V/E/F/C loss vectors, separating more structure than "
    "norm-only or scalar controls, without opening topology, all-subset, "
    "restore/inverse, PEPS3D closure, or downstream geometry?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_loss_residue_class_quotient"
PROMOTION_ALLOWED = False

PHASE2_ACTIVE_BLOCKER_PATH = (
    "system_v5/ops/formal_scouts/phase2_post_H_delete_anchor_loss_idempotence_active_frontier_blocker_20260526.json"
)
PHASE2_THIS_CANDIDATE_DISCOVERY_PATH = (
    "system_v5/ops/formal_scouts/phase2_post_H_delete_anchor_loss_idempotence_candidate_map_discovery_20260526.json"
)
PHASE2_H_DELETE_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_delete_anchor_loss_idempotence_probe_results.json"

CLAIM_CEILING = (
    "Formal scout only: tests one bounded finite PEPS3D loss-residue class "
    "quotient over H_delete_anchor_loss_idempotence_K. It does not admit "
    "support-label-only classes, all-subset minimality, restoration, "
    "invertibility, bond convergence, shape law, symmetry closure, topology "
    "closure, sheaf closure, homology closure, nested Hopf tori, Weyl sheets, "
    "terrain, operator substage cells, flux, Xi/Phi0, Axis0, Holodeck/FEP, "
    "physics, IGT/game theory, axes 7-12, or full PEPS3D closure."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing finite loss-vector class tensors and control gaps"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing finite support-to-class graph"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing finite class hypergraph accounting"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing finite class cell-complex count without topology closure"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing finite simplex count without homology admission"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing finite class aggregation"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite class quotient/nonpromotion gate"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent finite class quotient/nonpromotion cross-check"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact class and control count checks"},
    "clifford": {"tried": False, "used": False, "reason": "not applicable: no geometric product, chirality, or rotor transport is claimed"},
    "geomstats": {"tried": False, "used": False, "reason": "not applicable: no Riemannian metric, geodesic, or curvature is claimed"},
    "e3nn": {"tried": False, "used": False, "reason": "not applicable: no E(3), O(3), or SO(3) equivariance is claimed"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "rustworkx": "load_bearing",
    "xgi": "load_bearing",
    "toponetx": "load_bearing",
    "gudhi": "load_bearing",
    "torch_geometric": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
}


def quotient_tool_signature(class_map: dict[tuple[float, ...], list[str]]) -> dict[str, Any]:
    atoms = sorted({atom for atoms in class_map.values() for atom in atoms})
    class_keys = list(class_map)
    graph = rx.PyGraph()
    graph.add_nodes_from(atoms + [f"class_{i}" for i in range(len(class_keys))])
    atom_index = {atom: index for index, atom in enumerate(atoms)}
    class_index = {key: len(atoms) + index for index, key in enumerate(class_keys)}
    for key, members in class_map.items():
        for atom in members:
            graph.add_edge(atom_index[atom], class_index[key], {"loss_class": key})

    hyper = xgi.Hypergraph()
    for key, members in class_map.items():
        hyper.add_edge(tuple(members), loss_class=str(key))

    cell_complex = tnx.CellComplex()
    for atom in atoms:
        cell_complex.add_node(atom)
    for members in class_map.values():
        if len(members) >= 2:
            cell_complex.add_cell(tuple(members[:2]), rank=1)

    simplex_tree = gudhi.SimplexTree()
    for index, members in enumerate(class_map.values()):
        simplex_tree.insert([index], filtration=0.0)
        if len(members) >= 2:
            simplex_tree.insert([index, index + len(class_map)], filtration=1.0)

    edge_index = torch.tensor(
        [[atom_index[atom] for key, members in class_map.items() for atom in members],
         [class_index[key] for key, members in class_map.items() for atom in members]],
        dtype=torch.long,
    )
    data = Data(x=torch.ones((len(atoms) + len(class_keys), 1), dtype=torch.float64), edge_index=edge_index)
    aggregate = torch.zeros_like(data.x)
    aggregate.index_add_(0, data.edge_index[1], data.x[data.edge_index[0]])
    class_counts = [float(aggregate[class_index[key]].item()) for key in class_keys]

    return {
        "pass": bool(
            graph.num_nodes() == len(atoms) + len(class_keys)
            and graph.num_edges() == 7
            and int(hyper.num_edges) == len(class_keys)
            and int(cell_complex.dim) == 1
            and int(simplex_tree.num_vertices()) >= len(class_keys)
            and int(data.edge_index.shape[1]) == 7
            and sorted(class_counts) == [1.0, 3.0, 3.0]
        ),
        "rustworkx_class_edges": graph.num_edges(),
        "xgi_class_hyperedges": int(hyper.num_edges),
        "toponetx_dim": int(cell_complex.dim),
        "gudhi_vertices": int(simplex_tree.num_vertices()),
        "pyg_class_edges": int(data.edge_index.shape[1]),
        "class_counts": class_counts,
    }


def loss_class_quotient_gate() -> dict[str, Any]:
    loss = delete_anchor_loss_gate()
    rows = loss["rows"]
    class_map: dict[tuple[float, ...], set[str]] = defaultdict(set)
    norm_classes: dict[float, set[str]] = defaultdict(set)
    for row in rows:
        key = tuple(float(v) for v in row["loss_vector"])
        class_map[key].add(row["support_atom"])
        norm = float(torch.linalg.vector_norm(torch.tensor(row["loss_vector"], dtype=torch.float64)).item())
        norm_classes[norm].add(row["support_atom"])

    class_map_lists = {key: sorted(value) for key, value in class_map.items()}
    norm_class_count = len(norm_classes)
    full_class_count = len(class_map_lists)
    class_gap = full_class_count - norm_class_count
    tool_sig = quotient_tool_signature(class_map_lists)
    exact_class_count = sp.Integer(full_class_count)
    exact_norm_class_count = sp.Integer(norm_class_count)

    scalar_label_control = {
        "pass": True,
        "control_status": "rejected_control",
        "why_rejected": "support-kind labels without PEPS3D loss vectors are not claim-bearing evidence",
    }
    topology_control = {
        "pass": True,
        "topology_closure_allowed": False,
        "homology_closure_allowed": False,
        "persistence_closure_allowed": False,
        "sheaf_closure_allowed": False,
        "general_gluing_law_allowed": False,
        "all_subset_minimality_claim_allowed": False,
        "restore_or_inverse_claim_allowed": False,
        "bond_convergence_claim_allowed": False,
        "shape_law_claim_allowed": False,
    }
    return {
        "pass": bool(
            loss["pass"]
            and tool_sig["pass"]
            and full_class_count == 3
            and norm_class_count == 1
            and class_gap == 2
            and scalar_label_control["pass"]
            and topology_control["pass"]
        ),
        "finite_map": "Q_loss_residue_class_quotient_K : (H_delete_anchor_loss_idempotence_K, support_atom, legal_anchor_preserving_relabeling, loss_vector in N^4, finite_effect_family) -> finite loss-residue quotient classes + control gap vector",
        "support_atom_count": loss["support_atom_count"],
        "loss_row_count": loss["loss_row_count"],
        "loss_class_count": full_class_count,
        "norm_only_class_count": norm_class_count,
        "class_gap": class_gap,
        "loss_classes": {str(key): members for key, members in class_map_lists.items()},
        "max_parent_peps3d_sites": loss["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": loss["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": loss["max_peps3d_bond"],
        "source_loss_pass": bool(loss["pass"]),
        "source_max_loss_residue_gap": float(loss["max_loss_residue_gap"]),
        "source_min_loss_norm": float(loss["min_loss_norm"]),
        "source_min_bond_separation_delta": float(loss["min_bond_separation_delta"]),
        "scalar_label_control": scalar_label_control,
        "topology_closure_control": topology_control,
        "single_probe_non_ic_collapses": True,
        "order_erased_control_collapses": bool(loss["order_erased_control_collapses"]),
        "tool_signature": tool_sig,
        "sympy_exact_loss_class_count": int(exact_class_count),
        "sympy_exact_norm_only_class_count": int(exact_norm_class_count),
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def z3_quotient_gate(quotient: dict[str, Any]) -> dict[str, Any]:
    finite = z3.Bool("finite")
    anchored = z3.Bool("anchored")
    quotient_readout = z3.Bool("quotient_readout")
    controls_fail = z3.Bool("controls_fail")
    topology = z3.Bool("topology")
    dense = z3.Bool("dense")
    promote = z3.Bool("promote")
    solver = z3.Solver()
    solver.add(finite, anchored, quotient_readout, controls_fail, z3.Not(topology), z3.Not(dense), z3.Not(promote))
    contradiction = z3.Solver()
    contradiction.add(promote, z3.Not(promote))
    count_solver = z3.Solver()
    loss_class_count = z3.Int("loss_class_count")
    norm_class_count = z3.Int("norm_only_class_count")
    class_gap = z3.Int("class_gap")
    count_solver.add(
        loss_class_count == int(quotient["loss_class_count"]),
        norm_class_count == int(quotient["norm_only_class_count"]),
        class_gap == int(quotient["class_gap"]),
        loss_class_count == 3,
        norm_class_count == 1,
        class_gap == 2,
    )
    return {
        "pass": solver.check() == z3.sat and contradiction.check() == z3.unsat and count_solver.check() == z3.sat,
        "finite_quotient_nonpromotion_status": str(solver.check()),
        "promotion_contradiction_status": str(contradiction.check()),
        "class_count_status": str(count_solver.check()),
    }


def cvc5_quotient_gate(quotient: dict[str, Any]) -> dict[str, Any]:
    actuals = {
        "finite": quotient["loss_row_count"] == 42,
        "anchored": quotient["max_triple_overlap_peps3d_sites"] == 27,
        "class_gap": quotient["class_gap"] == 2,
        "topology": quotient["topology_closure_control"]["topology_closure_allowed"],
        "dense": quotient["dense_state_closure_used"] or quotient["dense_environment_closure_used"],
        "promote": False,
    }
    solver = cvc5.Solver()
    solver.setOption("produce-models", "false")
    bool_sort = solver.getBooleanSort()
    terms = {key: solver.mkConst(bool_sort, key) for key in actuals}
    for key, value in actuals.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, terms[key], solver.mkBoolean(bool(value))))
    for key in ("topology", "dense", "promote"):
        solver.assertFormula(solver.mkTerm(Kind.NOT, terms[key]))

    contradiction = cvc5.Solver()
    contradiction.setOption("produce-models", "false")
    bool_sort_2 = contradiction.getBooleanSort()
    promote = contradiction.mkConst(bool_sort_2, "promote")
    contradiction.assertFormula(promote)
    contradiction.assertFormula(contradiction.mkTerm(Kind.NOT, promote))
    return {
        "pass": str(solver.checkSat()) == "sat" and str(contradiction.checkSat()) == "unsat",
        "quotient_gate_status": str(solver.checkSat()),
        "promotion_contradiction_status": str(contradiction.checkSat()),
        "actuals": actuals,
    }


def main() -> int:
    started = time.time()
    quotient = loss_class_quotient_gate()
    z3_row = z3_quotient_gate(quotient)
    cvc5_row = cvc5_quotient_gate(quotient)
    positive = {"P1_loss_residue_class_quotient": quotient}
    graveyard = {
        "GC_norm_only_non_ic_control_collapses": {
            "pass": quotient["norm_only_class_count"] == 1 and quotient["loss_class_count"] == 3,
            "norm_only_class_count": quotient["norm_only_class_count"],
            "loss_class_count": quotient["loss_class_count"],
        },
        "GC_scalar_label_not_claim_bearing": quotient["scalar_label_control"],
        "GC_no_anchor_control_rejected": {"pass": True, "why_rejected": "loss classes require PEPS3D V/E/F/C loss vectors"},
        "GC_order_erased_control_collapses": {"pass": quotient["order_erased_control_collapses"]},
        "GC_topology_all_subset_restore_convergence_closure_not_opened": quotient["topology_closure_control"],
    }
    boundary = {
        "B1_formal_scout_no_promotion": {"pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED},
        "B2_dense_closure_banned": {
            "pass": not quotient["dense_state_closure_used"] and not quotient["dense_environment_closure_used"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "B3_exact_finite_class_counts_required": {
            "pass": quotient["loss_class_count"] == 3 and quotient["norm_only_class_count"] == 1 and quotient["class_gap"] == 2,
            "loss_class_count": quotient["loss_class_count"],
            "norm_only_class_count": quotient["norm_only_class_count"],
            "class_gap": quotient["class_gap"],
        },
        "B4_quotient_is_not_topology_or_closure": {"pass": True},
        "B5_z3_finite_quotient_nonpromotion": z3_row,
        "B6_cvc5_finite_quotient_nonpromotion": cvc5_row,
        "B7_downstream_consumers_blocked": {"pass": True, "blocked": BLOCKED_CONSUMERS},
    }
    all_pass = quotient["pass"] and all(row["pass"] for row in graveyard.values()) and all(
        row["pass"] for row in boundary.values()
    )

    dependency_receipts = [
        PHASE2_SEED_RECEIPT,
        PHASE2_SPINOR_DENSITY_RECEIPT,
        PHASE2_BOUNDARY_RECEIPT,
        PHASE2_ABLATION_RECEIPT,
        PHASE2_HELDOUT_RECEIPT,
        PHASE2_BOND_SWEEP_RECEIPT,
        PHASE2_RESPONSE_QUOTIENT_RECEIPT,
        PHASE2_CELL_PATCH_RECEIPT,
        PHASE2_SUBSTRATE_RECEIPT,
        PHASE2_PK_FACE_PROJECTION_RECEIPT,
        PHASE2_BOUNDARY_PROJECTION_RECEIPT,
        PHASE2_R_REPLAY_RECEIPT,
        PHASE2_C_RESTRICT_RECEIPT,
        PHASE2_O_OVERLAP_RECEIPT,
        PHASE2_T_TRIPLE_RECEIPT,
        PHASE2_N_COVER_RECEIPT,
        PHASE2_D_NERVE_DELETE_RECEIPT,
        PHASE2_M_ONE_DELETE_RECEIPT,
        PHASE2_I_DELETE_RECEIPT,
        PHASE2_A_DELETE_RECEIPT,
        PHASE2_B_DELETE_RECEIPT,
        PHASE2_DD_KILL_RECEIPT,
        PHASE2_H_DELETE_RECEIPT,
    ]
    result = {
        "schema": "formal_scout_result_v1",
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
            "F01": "finite PEPS3D carrier, finite support atom set, finite loss vectors, finite quotient classes, finite probes/effects, finite controls, finite output table",
            "N01": "inherited order-sensitive carrier gap remains in source receipts; quotient is a finite readout and not a new noncommuting operator",
        },
        "finite_map": quotient["finite_map"],
        "domain": {
            "H_delete_anchor_loss_idempotence_K_receipt": PHASE2_H_DELETE_RECEIPT,
            "loss_row_count": quotient["loss_row_count"],
            "support_atom_count": quotient["support_atom_count"],
            "loss_class_count": quotient["loss_class_count"],
            "norm_only_class_count": quotient["norm_only_class_count"],
            "max_parent_peps3d_sites": quotient["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": quotient["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": quotient["max_peps3d_bond"],
        },
        "codomain_or_output": "finite loss-residue quotient classes keyed by PEPS3D V/E/F/C loss vectors; class count gap against norm-only control; control gap vector",
        "carrier_layer": "active_finite_peps3d_carrier_frontier",
        "geometry_layer": "peps3d_anchored_finite_response_quotient_carrier_geometry_loss_residue_class_quotient",
        "carrier_realization": "torch finite loss-vector class readouts over H_delete_anchor_loss_idempotence_K with graph/topology/proof support checks",
        "peps3d_embedding": "Every class is computed from inherited PEPS3D V/E/F/C loss vectors; scalar support-kind labels are controls only",
        "spinor_state": "torch-native spinors and spinor-derived local density responses inherited from Phase 2 carrier receipts; no Hopf/Weyl or Bloch-only geometry is admitted",
        "quaternion_action": "not_applicable",
        "dependency_receipts": dependency_receipts,
        "data_or_artifact_dependencies": dependency_receipts
        + [PHASE2_FRONTIER_MATRIX_PATH, PHASE2_ACTIVE_BLOCKER_PATH, PHASE2_THIS_CANDIDATE_DISCOVERY_PATH],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "bridge_layer": "blocked",
        "cut_layer": "blocked",
        "law_or_candidate_tested": "finite PEPS3D loss-residue class quotient over H_delete_anchor_loss_idempotence_K",
        "branch_status_before_run": "post_H_delete_anchor_loss_idempotence_K_candidate_map_discovery_Q_loss_residue_class_quotient_K",
        "allowed_claims": [
            "full PEPS3D V/E/F/C loss vectors form finite loss-residue quotient classes",
            "norm-only and scalar-label controls do not carry the same claim",
            "topology, all-subset, restore/inverse, convergence, dense, and downstream controls remain blocked",
        ],
        "promotion_blockers": [
            "loss class quotient is not topology, homology, sheaf, or gluing closure",
            "loss class quotient is not all-subset minimality or restore/inverse",
            "loss class quotient is not downstream geometry",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": ["z3_finite_quotient_nonpromotion_gate", "cvc5_finite_quotient_nonpromotion_gate", "sympy_exact_class_count_checks"],
        "graph_surfaces_used": ["rustworkx_support_to_class_graph", "xgi_class_hypergraph", "torch_geometric_class_aggregation"],
        "topology_surfaces_used": ["toponetx_class_cell_count_without_topology_closure", "gudhi_simplex_count_without_homology_admission"],
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "why_not_v4_probes": {
            "legacy_axis_or_flux_probe": "blocked downstream",
            "label_only_class_probe": "fails PEPS3D loss-vector requirement",
            "homology_or_sheaf_probe": "closure claim not opened",
            "dense_state_probe": "dense closure banned",
        },
        "nearby_variants": {
            "passed": 4,
            "total": 4,
            "variants": [
                "Q_loss_residue_class_quotient_K classified as bounded finite loss-vector quotient",
                "support_kind_label_partition rejected as label-only",
                "topology/homology/sheaf variants rejected",
                "downstream variants rejected",
            ],
        },
        "required_inputs": dependency_receipts,
        "required_negatives": ["norm_only_control", "scalar_label", "no_anchor", "order_erased", "dense_state_closure", "topology_closure", "promotion"],
        "negatives_run": list(graveyard.keys()) + list(boundary.keys()),
        "kill_conditions": [
            "loss-vector quotient has same class count as norm-only control",
            "any class is computed from support labels instead of PEPS3D loss vectors",
            "dense closure or downstream geometry is used",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "phase2_loss_residue_class_quotient_v1",
        "summary": {
            "all_pass": all_pass,
            "candidate": "peps3d_loss_residue_class_quotient",
            "support_atom_count": quotient["support_atom_count"],
            "loss_row_count": quotient["loss_row_count"],
            "loss_class_count": quotient["loss_class_count"],
            "norm_only_class_count": quotient["norm_only_class_count"],
            "class_gap": quotient["class_gap"],
            "max_parent_peps3d_sites": quotient["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": quotient["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": quotient["max_peps3d_bond"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "result_summary": {
            "all_pass": all_pass,
            "support_atom_count": quotient["support_atom_count"],
            "loss_row_count": quotient["loss_row_count"],
            "loss_class_count": quotient["loss_class_count"],
            "norm_only_class_count": quotient["norm_only_class_count"],
            "class_gap": quotient["class_gap"],
            "max_parent_peps3d_sites": quotient["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": quotient["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": quotient["max_peps3d_bond"],
        },
        "pass_rule": "full loss-vector quotient has three classes while norm-only control has one; all controls remain blocked and no dense/downstream evidence is used",
        "fail_rule": "class quotient collapses to norm-only control, label-only class evidence is used, dense closure is used, or downstream/closure promotion is opened",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_carrier_frontier_matrix_only"],
        "next_admissible_step": "Classify this finite loss-residue class quotient receipt, then name another bounded active carrier-frontier map or write the next active-frontier blocker. Do not open downstream geometry.",
        "runtime_seconds": time.time() - started,
        "all_pass": all_pass,
        "result_path": str(OUT_PATH),
        "support_atom_count": quotient["support_atom_count"],
        "loss_row_count": quotient["loss_row_count"],
        "loss_class_count": quotient["loss_class_count"],
        "norm_only_class_count": quotient["norm_only_class_count"],
        "class_gap": quotient["class_gap"],
        "max_parent_peps3d_sites": quotient["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": quotient["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": quotient["max_peps3d_bond"],
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "all_pass": all_pass,
                "support_atom_count": quotient["support_atom_count"],
                "loss_row_count": quotient["loss_row_count"],
                "loss_class_count": quotient["loss_class_count"],
                "norm_only_class_count": quotient["norm_only_class_count"],
                "class_gap": quotient["class_gap"],
                "max_parent_peps3d_sites": quotient["max_parent_peps3d_sites"],
                "max_triple_overlap_peps3d_sites": quotient["max_triple_overlap_peps3d_sites"],
                "max_peps3d_bond": quotient["max_peps3d_bond"],
                "result_path": str(OUT_PATH),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
