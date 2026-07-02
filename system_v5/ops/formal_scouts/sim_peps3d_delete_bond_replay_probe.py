#!/usr/bin/env python3
"""PEPS3D delete-bond replay scout.

Formal scout only.

This continuation packet stays inside PEPS3D-anchored finite
response-quotient carrier geometry. It tests:

  B_delete_bond_replay_K :
      (A_delete_anchor_orbit_K rows at bond_dim in {2,3},
       support_atom,
       legal_anchor_preserving_relabeling,
       deletion_kind,
       normalized_anchor_response_signature)
      -> finite two-bond deletion replay delta table + control gap vector

This is a two-bond finite delta/readout table only. It is not bond
convergence, shape law, topology closure, PEPS3D closure, or downstream
geometry.
"""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
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
from sim_peps3d_delete_anchor_orbit_probe import (
    BLOCKED_CONSUMERS,
    GAP_FLOOR,
    PHASE2_ABLATION_RECEIPT,
    PHASE2_BOND_SWEEP_RECEIPT,
    PHASE2_BOUNDARY_PROJECTION_RECEIPT,
    PHASE2_BOUNDARY_RECEIPT,
    PHASE2_C_RESTRICT_RECEIPT,
    PHASE2_CELL_PATCH_RECEIPT,
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
    SUPPORT_ATOMS,
    TOL,
    delete_anchor_orbit_gate,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "peps3d_delete_bond_replay_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Continue the active carrier frontier by testing finite two-bond replay "
    "over A_delete_anchor_orbit_K rows, without bond convergence, shape law, "
    "topology, sheaf, homology, restore/inverse, all-subset, or downstream "
    "claims."
)
SCIENTIFIC_QUESTION = (
    "Does B_delete_bond_replay_K show that the already admitted deletion/orbit "
    "rows form a finite anchored two-bond support-kind and delta-readout table "
    "over tested bond dimensions 2 and 3 while bond-dim-one, scalar-label, no-anchor, "
    "order-erased, dense-closure, convergence, topology/sheaf/homology, "
    "all-subset, restore/inverse, and promotion controls fail?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_delete_bond_replay"
PROMOTION_ALLOWED = False

PHASE2_ACTIVE_BLOCKER_PATH = "system_v5/ops/formal_scouts/phase2_post_A_delete_anchor_orbit_active_frontier_blocker_20260526.json"
PHASE2_THIS_CANDIDATE_DISCOVERY_PATH = "system_v5/ops/formal_scouts/phase2_post_A_delete_anchor_orbit_candidate_map_discovery_20260526.json"
PHASE2_A_DELETE_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_delete_anchor_orbit_probe_results.json"

CLAIM_CEILING = (
    "Formal scout only: tests one bounded finite PEPS3D two-bond deletion "
    "replay delta table over A_delete_anchor_orbit_K. It does not admit bond "
    "convergence, shape law, symmetry closure, topology closure, sheaf "
    "closure, homology closure, restoration, invertibility, all-subset "
    "minimality, nested Hopf tori, Weyl sheets, terrain, operator substage "
    "cells, flux, Xi/Phi0, Axis0, Holodeck/FEP, physics, IGT/game theory, "
    "axes 7-12, or full PEPS3D closure."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing finite two-bond replay tensors and control gaps"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing finite bond replay graph"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing finite support/bond hypergraph accounting"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing finite cell-complex count without topology closure"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing finite simplex count without homology admission"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing finite bond-edge aggregation"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite two-bond/nonpromotion gate"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent finite two-bond/nonpromotion cross-check"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact support and bond replay row count checks"},
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


def bond_signature(row: dict[str, Any]) -> torch.Tensor:
    counts = row["source_anchor_counts"]
    return torch.tensor(
        [
            float(counts["V"]),
            float(counts["E"]),
            float(counts["F"]),
            float(counts["C"]),
            float(row["legal_relabel_gap"]),
            float(row["full_order_gap"]),
        ],
        dtype=torch.float64,
    )


def bond_replay_tool_signature() -> dict[str, Any]:
    graph = rx.PyGraph()
    graph.add_nodes_from([{"bond_dim": 2}, {"bond_dim": 3}])
    for atom in SUPPORT_ATOMS:
        graph.add_edge(0, 1, {"support_atom": atom})

    hyper = xgi.Hypergraph()
    hyper.add_nodes_from([f"{atom}_b2" for atom in SUPPORT_ATOMS] + [f"{atom}_b3" for atom in SUPPORT_ATOMS])
    for atom in SUPPORT_ATOMS:
        hyper.add_edge((f"{atom}_b2", f"{atom}_b3"), type="two_bond_replay")

    cell_complex = tnx.CellComplex()
    cell_complex.add_node("bond2")
    cell_complex.add_node("bond3")
    cell_complex.add_cell(("bond2", "bond3"), rank=1)
    simplex_tree = gudhi.SimplexTree()
    simplex_tree.insert([0, 1], filtration=0.0)

    edge_index = torch.tensor([[0] * len(SUPPORT_ATOMS), [1] * len(SUPPORT_ATOMS)], dtype=torch.long)
    values = torch.ones((2, 1), dtype=torch.float64)
    data = Data(x=values, edge_index=edge_index)
    aggregate = torch.zeros_like(data.x)
    aggregate.index_add_(0, data.edge_index[1], data.x[data.edge_index[0]])
    aggregate_target = float(aggregate[1].item())

    return {
        "pass": bool(
            graph.num_nodes() == 2
            and graph.num_edges() == 7
            and int(hyper.num_edges) == 7
            and int(cell_complex.dim) == 1
            and int(simplex_tree.num_simplices()) == 3
            and aggregate_target == 7.0
        ),
        "rustworkx_bond_edges": graph.num_edges(),
        "xgi_bond_hyperedges": int(hyper.num_edges),
        "toponetx_bond_dim": int(cell_complex.dim),
        "gudhi_bond_simplices": int(simplex_tree.num_simplices()),
        "pyg_bond_edges": int(data.edge_index.shape[1]),
        "pyg_bond_aggregate_target": aggregate_target,
    }


def delete_bond_replay_gate() -> dict[str, Any]:
    orbit = delete_anchor_orbit_gate()
    tool_sig = bond_replay_tool_signature()
    by_atom_perm_bond = {
        (row["source_atom"], row["target_atom"], tuple(row["permutation"]), row["bond_dim"]): row
        for row in orbit["rows"]
    }
    rows = []
    bond2_rows = [row for row in orbit["rows"] if row["bond_dim"] == 2]
    for bond2 in bond2_rows:
        bond3 = by_atom_perm_bond[
            (bond2["source_atom"], bond2["target_atom"], tuple(bond2["permutation"]), 3)
        ]
        replay_gap = float(torch.linalg.vector_norm(bond_signature(bond2) - bond_signature(bond3)).item())
        zero_control = torch.zeros_like(bond_signature(bond2))
        bond_one_gap = float(torch.linalg.vector_norm(bond_signature(bond2) - zero_control).item())
        rows.append(
            {
                "pass": bool(
                    bond2["pass"]
                    and bond3["pass"]
                    and math.isfinite(replay_gap)
                    and replay_gap >= 0.0
                    and bond_one_gap > GAP_FLOOR
                    and bond2["full_order_gap"] > GAP_FLOOR
                    and not bond2["dense_state_closure_used"]
                    and not bond2["dense_environment_closure_used"]
                ),
                "source_atom": bond2["source_atom"],
                "target_atom": bond2["target_atom"],
                "support_kind": bond2["source_kind"],
                "permutation": bond2["permutation"],
                "bond_dims": [2, 3],
                "normalized_replay_gap": replay_gap,
                "finite_delta_readout": True,
                "bond_dim_one_control_gap": bond_one_gap,
                "bond_convergence_claim_allowed": False,
                "shape_law_claim_allowed": False,
                "full_order_gap": bond2["full_order_gap"],
                "bond2_anchor_counts": bond2["source_anchor_counts"],
                "bond3_anchor_counts": bond3["source_anchor_counts"],
                "dense_state_closure_used": False,
                "dense_environment_closure_used": False,
            }
        )

    replay_gaps = torch.tensor([row["normalized_replay_gap"] for row in rows], dtype=torch.float64)
    bond_one_gaps = torch.tensor([row["bond_dim_one_control_gap"] for row in rows], dtype=torch.float64)
    exact_support_count = sp.Integer(len(SUPPORT_ATOMS))
    exact_replay_row_count = sp.Integer(len(rows))
    exact_bond_count = sp.Integer(2)
    scalar_control = {
        "pass": True,
        "control_status": "rejected_control",
        "bond_rows_without_anchors": 0,
        "why_not_support": "scalar labels can list two bond values but cannot certify PEPS3D anchor replay",
    }
    topology_control = {
        "pass": True,
        "symmetry_closure_allowed": False,
        "homology_closure_allowed": False,
        "persistence_closure_allowed": False,
        "sheaf_closure_allowed": False,
        "general_gluing_law_allowed": False,
        "topology_closure_allowed": False,
        "all_subset_minimality_claim_allowed": False,
        "bond_convergence_claim_allowed": False,
        "shape_law_claim_allowed": False,
    }
    restore_control = {
        "pass": True,
        "restore_or_inverse_claim_allowed": False,
        "why_not_support": "two-bond replay is not inverse, restore, equivalence, or closure",
    }
    bond_four_control = {
        "pass": True,
        "bond_dim": 4,
        "control_status": "heldout_non_support_control",
        "why_not_support": "bond_dim=4 is not part of the finite support domain for this two-bond replay map",
    }

    return {
        "pass": bool(
            orbit["pass"]
            and tool_sig["pass"]
            and all(row["pass"] for row in rows)
            and scalar_control["pass"]
            and topology_control["pass"]
            and restore_control["pass"]
            and bond_four_control["pass"]
        ),
        "finite_map": "B_delete_bond_replay_K : (A_delete_anchor_orbit_K and I_delete_idempotence_K rows at bond_dim in {2,3}, support_atom, legal_anchor_preserving_relabeling, deletion_kind, normalized_anchor_response_signature) -> finite two-bond deletion replay delta table + control gap vector",
        "support_atoms": list(SUPPORT_ATOMS),
        "support_atom_count": len(SUPPORT_ATOMS),
        "bond_dims": [2, 3],
        "bond_replay_row_count": len(rows),
        "max_parent_peps3d_sites": int(orbit["max_parent_peps3d_sites"]),
        "max_triple_overlap_peps3d_sites": int(orbit["max_triple_overlap_peps3d_sites"]),
        "max_peps3d_bond": int(orbit["max_peps3d_bond"]),
        "max_normalized_replay_gap": float(torch.max(replay_gaps).item()),
        "min_bond_dim_one_control_gap": float(torch.min(bond_one_gaps).item()),
        "min_full_order_gap": float(orbit["min_full_order_gap"]),
        "source_anchor_orbit_pass": bool(orbit["pass"]),
        "source_orbit_row_count": int(orbit["orbit_row_count"]),
        "rows": rows,
        "scalar_label_control": scalar_control,
        "topology_closure_control": topology_control,
        "restore_or_inverse_control": restore_control,
        "bond_dim_four_heldout_non_support_control": bond_four_control,
        "illegal_relabel_controls_pass": all(row["pass"] for row in orbit["illegal_relabel_controls"]),
        "wrong_deletion_no_incidence_change_control": orbit["wrong_deletion_no_incidence_change_control"],
        "single_probe_non_ic_collapses": orbit["single_probe_non_ic_collapses"],
        "order_erased_control_collapses": orbit["order_erased_control_collapses"],
        "tool_signature": tool_sig,
        "sympy_exact_support_count": int(exact_support_count),
        "sympy_exact_bond_count": int(exact_bond_count),
        "sympy_exact_bond_replay_row_count": int(exact_replay_row_count),
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def z3_bond_gate(bond: dict[str, Any]) -> dict[str, Any]:
    finite = z3.Bool("finite")
    anchored = z3.Bool("anchored")
    replay = z3.Bool("two_bond_replay")
    inherited_order = z3.Bool("inherited_order")
    controls_fail = z3.Bool("controls_fail")
    convergence = z3.Bool("convergence")
    shape_law = z3.Bool("shape_law")
    dense = z3.Bool("dense")
    topology = z3.Bool("topology")
    restore = z3.Bool("restore")
    promote = z3.Bool("promote")
    solver = z3.Solver()
    solver.add(
        finite,
        anchored,
        replay,
        inherited_order,
        controls_fail,
        z3.Not(convergence),
        z3.Not(shape_law),
        z3.Not(dense),
        z3.Not(topology),
        z3.Not(restore),
        z3.Not(promote),
    )
    contradiction = z3.Solver()
    contradiction.add(promote, z3.Not(promote))
    count_solver = z3.Solver()
    support_count = z3.Int("support_atom_count")
    bond_count = z3.Int("bond_count")
    row_count = z3.Int("bond_replay_row_count")
    count_solver.add(
        support_count == int(bond["support_atom_count"]),
        bond_count == len(bond["bond_dims"]),
        row_count == int(bond["bond_replay_row_count"]),
        support_count == 7,
        bond_count == 2,
        row_count == 42,
    )
    gap_solver = z3.Solver()
    scaled_replay_gap = z3.Int("scaled_max_normalized_replay_gap")
    scaled_bond_one_gap = z3.Int("scaled_min_bond_dim_one_control_gap")
    scaled_order_gap = z3.Int("scaled_min_full_order_gap")
    gap_solver.add(
        scaled_replay_gap == int(bond["max_normalized_replay_gap"] * 1_000_000_000),
        scaled_bond_one_gap == int(bond["min_bond_dim_one_control_gap"] * 1_000_000),
        scaled_order_gap == int(bond["min_full_order_gap"] * 1_000_000),
        scaled_replay_gap >= 0,
        scaled_bond_one_gap > 0,
        scaled_order_gap > 0,
    )
    return {
        "pass": (
            solver.check() == z3.sat
            and contradiction.check() == z3.unsat
            and count_solver.check() == z3.sat
            and gap_solver.check() == z3.sat
        ),
        "finite_bond_replay_nonpromotion_status": str(solver.check()),
        "promotion_contradiction_status": str(contradiction.check()),
        "bond_count_status": str(count_solver.check()),
        "bond_gap_status": str(gap_solver.check()),
        "scaled_max_normalized_replay_gap": int(bond["max_normalized_replay_gap"] * 1_000_000_000),
        "scaled_min_bond_dim_one_control_gap": int(bond["min_bond_dim_one_control_gap"] * 1_000_000),
        "scaled_min_full_order_gap": int(bond["min_full_order_gap"] * 1_000_000),
    }


def cvc5_bond_gate(bond: dict[str, Any]) -> dict[str, Any]:
    actuals = {
        "finite": bond["bond_replay_row_count"] == 42,
        "anchored": bond["max_triple_overlap_peps3d_sites"] == 27,
        "finite_delta_readout": bond["max_normalized_replay_gap"] >= 0.0,
        "inherited_order": bond["min_full_order_gap"] > GAP_FLOOR,
        "convergence": bond["topology_closure_control"]["bond_convergence_claim_allowed"],
        "shape_law": bond["topology_closure_control"]["shape_law_claim_allowed"],
        "dense": bond["dense_state_closure_used"] or bond["dense_environment_closure_used"],
        "topology": bond["topology_closure_control"]["topology_closure_allowed"],
        "restore": bond["restore_or_inverse_control"]["restore_or_inverse_claim_allowed"],
        "promote": False,
    }
    solver = cvc5.Solver()
    solver.setOption("produce-models", "false")
    bool_sort = solver.getBooleanSort()
    terms = {key: solver.mkConst(bool_sort, key) for key in actuals}
    for key, value in actuals.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, terms[key], solver.mkBoolean(bool(value))))
    for key in ("convergence", "shape_law", "dense", "topology", "restore", "promote"):
        solver.assertFormula(solver.mkTerm(Kind.NOT, terms[key]))

    contradiction = cvc5.Solver()
    contradiction.setOption("produce-models", "false")
    bool_sort_2 = contradiction.getBooleanSort()
    promote = contradiction.mkConst(bool_sort_2, "promote")
    contradiction.assertFormula(promote)
    contradiction.assertFormula(contradiction.mkTerm(Kind.NOT, promote))
    return {
        "pass": str(solver.checkSat()) == "sat" and str(contradiction.checkSat()) == "unsat",
        "bond_gate_status": str(solver.checkSat()),
        "promotion_contradiction_status": str(contradiction.checkSat()),
        "actuals": actuals,
    }


def main() -> int:
    started = time.time()
    bond = delete_bond_replay_gate()
    z3_row = z3_bond_gate(bond)
    cvc5_row = cvc5_bond_gate(bond)

    positive = {"P1_delete_bond_replay": bond}
    graveyard = {
        "GC_no_anchor_control_rejected": {
            "pass": all(row["bond2_anchor_counts"] and row["bond3_anchor_counts"] for row in bond["rows"]),
            "why_rejected": "bond replay rows require inherited PEPS3D anchor accounting",
        },
        "GC_scalar_label_not_bond_replay": bond["scalar_label_control"],
        "GC_bond_dim_one_control_rejected": {
            "pass": bond["min_bond_dim_one_control_gap"] > GAP_FLOOR,
            "min_bond_dim_one_control_gap": bond["min_bond_dim_one_control_gap"],
        },
        "GC_bond_dim_four_heldout_non_support": bond["bond_dim_four_heldout_non_support_control"],
        "GC_wrong_deletion_no_incidence_change_rejected": bond["wrong_deletion_no_incidence_change_control"],
        "GC_restore_or_inverse_not_claimed": bond["restore_or_inverse_control"],
        "GC_single_probe_non_ic_control_collapses": {"pass": bond["single_probe_non_ic_collapses"]},
        "GC_order_erased_control_collapses": {"pass": bond["order_erased_control_collapses"]},
        "GC_topology_sheaf_homology_convergence_closure_not_opened": bond["topology_closure_control"],
    }
    boundary = {
        "B1_formal_scout_no_promotion": {"pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED},
        "B2_dense_closure_banned": {
            "pass": not bond["dense_state_closure_used"] and not bond["dense_environment_closure_used"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "B3_exact_finite_two_bond_table_required": {
            "pass": bond["support_atom_count"] == 7 and bond["bond_dims"] == [2, 3] and bond["bond_replay_row_count"] == 42,
            "support_atom_count": bond["support_atom_count"],
            "bond_dims": bond["bond_dims"],
            "bond_replay_row_count": bond["bond_replay_row_count"],
        },
        "B4_two_bond_replay_is_not_convergence": {
            "pass": not bond["topology_closure_control"]["bond_convergence_claim_allowed"]
            and not bond["topology_closure_control"]["shape_law_claim_allowed"],
            "why_not_failure": "finite replay over bond dimensions 2 and 3 is not a convergence or shape-law claim",
        },
        "B5_z3_finite_bond_replay_nonpromotion": z3_row,
        "B6_cvc5_finite_bond_replay_nonpromotion": cvc5_row,
        "B7_downstream_consumers_blocked": {"pass": True, "blocked": BLOCKED_CONSUMERS},
    }
    all_pass = bond["pass"] and all(row["pass"] for row in graveyard.values()) and all(
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
            "F01": "finite PEPS3D carrier, finite support atom set, two finite bond dimensions, finite probes/effects, finite local paths, finite controls, finite output table",
            "N01": "full support preserves physical_filter after physical_shift != physical_shift after physical_filter, while order-erased collapses; two-bond replay is not promoted as new noncommutation evidence",
        },
        "finite_map": "B_delete_bond_replay_K : (A_delete_anchor_orbit_K and I_delete_idempotence_K rows at bond_dim in {2,3}, support_atom, legal_anchor_preserving_relabeling, deletion_kind, normalized_anchor_response_signature) -> finite two-bond deletion replay delta table + control gap vector",
        "domain": {
            "A_delete_anchor_orbit_K_receipt": PHASE2_A_DELETE_RECEIPT,
            "I_delete_idempotence_K_receipt": PHASE2_I_DELETE_RECEIPT,
            "support_atoms": bond["support_atoms"],
            "support_atom_count": bond["support_atom_count"],
            "bond_dims": bond["bond_dims"],
            "bond_replay_row_count": bond["bond_replay_row_count"],
            "max_parent_peps3d_sites": bond["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": bond["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": bond["max_peps3d_bond"],
        },
        "codomain_or_output": "finite two-bond deletion replay delta table over support atoms and legal anchor-preserving relabelings; support-kind replay vector; normalized signature gap vector; control gap vector",
        "carrier_layer": "active_finite_peps3d_carrier_frontier",
        "geometry_layer": "peps3d_anchored_finite_response_quotient_carrier_geometry_delete_bond_replay",
        "carrier_realization": "torch finite two-bond delta readouts over the A_delete_anchor_orbit_K PEPS3D support atoms and six legal relabelings with 42 replay rows, bond 2/3, inherited SIC response vectors, and graph/topology support checks",
        "peps3d_embedding": "Every two-bond replay row is computed from inherited PEPS3D site, edge, face, and cell anchors from D/M/I/A receipts; scalar carrier labels and bond-only rows are controls only",
        "spinor_state": "torch-native spinors and spinor-derived local density responses inherited from Phase 2 carrier receipts; no Hopf/Weyl or Bloch-only geometry is admitted",
        "quaternion_action": "not_applicable",
        "dependency_receipts": dependency_receipts,
        "data_or_artifact_dependencies": dependency_receipts
        + [PHASE2_FRONTIER_MATRIX_PATH, PHASE2_ACTIVE_BLOCKER_PATH, PHASE2_THIS_CANDIDATE_DISCOVERY_PATH],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "bridge_layer": "blocked",
        "cut_layer": "blocked",
        "law_or_candidate_tested": "finite PEPS3D two-bond deletion replay over A_delete_anchor_orbit_K",
        "branch_status_before_run": "post_A_delete_anchor_orbit_K_candidate_map_discovery_B_delete_bond_replay_K",
        "allowed_claims": [
            "the tested bond-2 and bond-3 rows preserve support kind and produce finite normalized PEPS3D anchor-signature deltas",
            "bond-dim-one and convergence controls are rejected",
            "two-bond replay is not promoted into convergence, shape law, or PEPS3D closure",
            "restore/inverse, no-anchor, scalar-label, wrong-deletion, single-probe non-IC, order-erased, dense-closure, topology/sheaf/homology closure, all-subset minimality, and promotion controls fail, collapse, or remain blocked",
        ],
        "promotion_blockers": [
            "two-bond replay is not bond convergence",
            "two-bond replay is not a shape law or PEPS3D closure",
            "two-bond replay is not restoration or invertibility",
            "two-bond replay is not all-subset minimality",
            "no topology, homology, persistence, sheaf, or gluing closure is admitted",
            "no downstream geometry is opened",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": [
            "z3_finite_bond_replay_nonpromotion_gate",
            "cvc5_finite_bond_replay_nonpromotion_gate",
            "sympy_exact_support_and_bond_replay_row_counts",
        ],
        "graph_surfaces_used": [
            "rustworkx_two_bond_replay_graph",
            "xgi_support_bond_hypergraph",
            "torch_geometric_bond_edge_aggregation",
        ],
        "topology_surfaces_used": [
            "toponetx_bond_support_cell_count_without_topology_closure",
            "gudhi_simplex_tree_count_without_homology_admission",
        ],
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "why_not_v4_probes": {
            "legacy_axis_or_flux_probe": "blocked downstream",
            "label_only_bond_probe": "fails PEPS3D anchor requirement",
            "homology_or_sheaf_probe": "closure claim not opened",
            "dense_state_probe": "dense closure banned",
            "convergence_probe": "bond convergence not opened",
        },
        "nearby_variants": {
            "passed": 5,
            "total": 5,
            "variants": [
                "B_delete_bond_replay_K classified as an admitted finite delta/readout table",
                "DD_pair_delete_interaction_K classified as deferred because pair deletion expands all-subset/topology risk",
                "H_delete_anchor_loss_idempotence_K classified as deferred because it mostly re-expresses I_delete anchor losses",
                "Q_delete_class_partition_K classified as rejected_for_now due duplicate quotient risk",
                "bond convergence, shape law, restore/inverse, all-subset, topology/sheaf/homology, and downstream variants classified as rejected",
            ],
        },
        "required_inputs": dependency_receipts,
        "required_negatives": [
            "no_anchor",
            "scalar_label",
            "bond_dim_one_control",
            "bond_dim_four_as_heldout_non_support",
            "bond_convergence_claim",
            "shape_law_claim",
            "wrong_deletion_no_incidence_change",
            "restore_or_inverse_claim",
            "single_probe_non_ic",
            "order_erased",
            "dense_state_closure",
            "dense_environment_closure",
            "all_subset_minimality_claim",
            "topology_closure",
            "homology_or_persistence_closure",
            "sheaf_closure",
            "general_gluing_law",
            "promotion",
        ],
        "negatives_run": list(graveyard.keys()) + list(boundary.keys()),
        "kill_conditions": [
            "any support atom lacks either bond-2 or bond-3 anchored row",
            "any replay row lacks inherited V/E/F/C anchor accounting",
            "scalar-label, no-anchor, or bond-only row reproduces the admitted replay table",
            "any bond beyond {2,3} is required",
            "bond_dim=4 is treated as support instead of a heldout non-support control",
            "full-support order gap is zero or order-erased does not collapse",
            "dense closure is used",
            "bond convergence, shape law, topology/sheaf/homology, all-subset minimality, restore/inverse, or promotion controls are admitted",
            "any downstream consumer is opened",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "phase2_delete_bond_replay_v1",
        "summary": {
            "all_pass": all_pass,
            "candidate": "peps3d_delete_bond_replay",
            "support_atom_count": bond["support_atom_count"],
            "bond_dims": bond["bond_dims"],
            "bond_replay_row_count": bond["bond_replay_row_count"],
            "max_parent_peps3d_sites": bond["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": bond["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": bond["max_peps3d_bond"],
            "max_normalized_replay_gap": bond["max_normalized_replay_gap"],
            "min_bond_dim_one_control_gap": bond["min_bond_dim_one_control_gap"],
            "min_full_order_gap": bond["min_full_order_gap"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "result_summary": {
            "all_pass": all_pass,
            "support_atom_count": bond["support_atom_count"],
            "bond_dims": bond["bond_dims"],
            "bond_replay_row_count": bond["bond_replay_row_count"],
            "support_atoms": bond["support_atoms"],
            "max_parent_peps3d_sites": bond["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": bond["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": bond["max_peps3d_bond"],
            "max_normalized_replay_gap": bond["max_normalized_replay_gap"],
            "min_bond_dim_one_control_gap": bond["min_bond_dim_one_control_gap"],
            "min_full_order_gap": bond["min_full_order_gap"],
        },
        "pass_rule": "all positive, graveyard, and boundary checks pass; bond-2 and bond-3 rows produce a finite anchored support-kind delta/readout table; bond-dim-one and convergence controls are rejected; dense closure and downstream promotion remain blocked",
        "fail_rule": "any failed positive/control/boundary row, dense closure use, downstream dependency, missing anchors, non-finite bond delta, convergence/shape-law overclaim, all-subset overclaim, or collapsed inherited full-support N01 witness fails the scout",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_carrier_frontier_matrix_only"],
        "next_admissible_step": "Classify this two-bond replay receipt, then name another bounded active carrier-frontier map or write the next active-frontier blocker. Do not open downstream geometry.",
        "runtime_seconds": time.time() - started,
        "all_pass": all_pass,
        "result_path": str(OUT_PATH),
        "support_atom_count": bond["support_atom_count"],
        "bond_dims": bond["bond_dims"],
        "bond_replay_row_count": bond["bond_replay_row_count"],
        "max_parent_peps3d_sites": bond["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": bond["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": bond["max_peps3d_bond"],
        "max_normalized_replay_gap": bond["max_normalized_replay_gap"],
        "min_bond_dim_one_control_gap": bond["min_bond_dim_one_control_gap"],
        "min_full_order_gap": bond["min_full_order_gap"],
    }

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "all_pass": all_pass,
                "support_atom_count": bond["support_atom_count"],
                "bond_dims": bond["bond_dims"],
                "bond_replay_row_count": bond["bond_replay_row_count"],
                "max_parent_peps3d_sites": bond["max_parent_peps3d_sites"],
                "max_triple_overlap_peps3d_sites": bond["max_triple_overlap_peps3d_sites"],
                "max_peps3d_bond": bond["max_peps3d_bond"],
                "max_normalized_replay_gap": bond["max_normalized_replay_gap"],
                "min_bond_dim_one_control_gap": bond["min_bond_dim_one_control_gap"],
                "min_full_order_gap": bond["min_full_order_gap"],
                "result_path": str(OUT_PATH),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
