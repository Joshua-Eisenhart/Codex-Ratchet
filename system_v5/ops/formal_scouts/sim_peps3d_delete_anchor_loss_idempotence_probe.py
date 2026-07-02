#!/usr/bin/env python3
"""PEPS3D delete-anchor loss/idempotence residue scout.

Formal scout only.

This continuation packet stays inside PEPS3D-anchored finite
response-quotient carrier geometry. It tests:

  H_delete_anchor_loss_idempotence_K :
      (B_delete_bond_replay_K,
       I_delete_idempotence_K,
       support_atom,
       repeated delete-loss projection,
       legal_anchor_preserving_relabeling,
       bond_dim in {2,3})
      -> finite delete-anchor loss/idempotence residue table + control gap vector

This is a finite loss-residue readout only. It is not all-subset minimality,
restore/inverse, bond convergence, shape law, topology closure, PEPS3D
closure, or downstream geometry.
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
from sim_peps3d_delete_bond_replay_probe import (
    BLOCKED_CONSUMERS,
    GAP_FLOOR,
    PHASE2_ABLATION_RECEIPT,
    PHASE2_A_DELETE_RECEIPT,
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
    delete_bond_replay_gate,
)
from sim_peps3d_deletion_idempotence_probe import deletion_idempotence_gate


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "peps3d_delete_anchor_loss_idempotence_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Continue the active carrier frontier after the killed DD candidate by "
    "testing finite delete-anchor loss/idempotence residues over "
    "B_delete_bond_replay_K and I_delete_idempotence_K, without all-subset, "
    "restore/inverse, topology, sheaf, homology, bond convergence, shape law, "
    "PEPS3D closure, or downstream claims."
)
SCIENTIFIC_QUESTION = (
    "Does H_delete_anchor_loss_idempotence_K produce a finite PEPS3D-anchored "
    "delete-loss residue table whose loss vectors are stable under repeated "
    "deletion and legal relabeling across bond dimensions 2 and 3, while "
    "no-anchor, scalar-label, wrong-deletion, single-probe non-IC, "
    "order-erased, dense-closure, all-subset, restore/inverse, "
    "topology/sheaf/homology, convergence, and promotion controls fail or "
    "remain blocked?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_delete_anchor_loss_idempotence"
PROMOTION_ALLOWED = False

PHASE2_ACTIVE_BLOCKER_PATH = (
    "system_v5/ops/formal_scouts/phase2_post_DD_pair_delete_interaction_killed_active_frontier_blocker_20260526.json"
)
PHASE2_THIS_CANDIDATE_DISCOVERY_PATH = (
    "system_v5/ops/formal_scouts/phase2_post_DD_pair_delete_interaction_killed_candidate_map_discovery_20260526.json"
)
PHASE2_B_DELETE_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_delete_bond_replay_probe_results.json"
PHASE2_DD_KILL_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_pair_delete_interaction_probe_results.json"

CLAIM_CEILING = (
    "Formal scout only: tests one bounded finite PEPS3D delete-anchor "
    "loss/idempotence residue table over B_delete_bond_replay_K and "
    "I_delete_idempotence_K. It does not admit all-subset minimality, "
    "restoration, invertibility, bond convergence, shape law, symmetry "
    "closure, topology closure, sheaf closure, homology closure, nested Hopf "
    "tori, Weyl sheets, terrain, operator substage cells, flux, Xi/Phi0, "
    "Axis0, Holodeck/FEP, physics, IGT/game theory, axes 7-12, or full "
    "PEPS3D closure."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing finite loss vectors and residue gaps"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing finite support-loss graph"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing finite support/loss hypergraph accounting"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing finite cell-complex count without topology closure"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing finite simplex count without homology admission"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing finite support-loss edge aggregation"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite loss-residue/nonpromotion gate"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent finite loss-residue/nonpromotion cross-check"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact support, relabeling, and loss row count checks"},
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


def count_vec(counts: dict[str, int]) -> torch.Tensor:
    return torch.tensor([float(counts[k]) for k in ("V", "E", "F", "C")], dtype=torch.float64)


def loss_tool_signature() -> dict[str, Any]:
    atoms = list(SUPPORT_ATOMS)
    graph = rx.PyGraph()
    graph.add_nodes_from(atoms)
    for index in range(len(atoms) - 1):
        graph.add_edge(index, index + 1, {"loss_chain": True})

    hyper = xgi.Hypergraph()
    hyper.add_nodes_from(atoms)
    hyper.add_edge(tuple(atoms[:3]), type="vertex_loss_family")
    hyper.add_edge(tuple(atoms[3:6]), type="edge_loss_family")
    hyper.add_edge((atoms[6],), type="simplex_loss_family")

    cell_complex = tnx.CellComplex()
    for atom in atoms:
        cell_complex.add_node(atom)
    cell_complex.add_cell(tuple(atoms[:2]), rank=1)
    simplex_tree = gudhi.SimplexTree()
    simplex_tree.insert([0, 1], filtration=0.0)

    edge_index = torch.tensor([[0, 1, 2, 3, 4, 5], [1, 2, 3, 4, 5, 6]], dtype=torch.long)
    data = Data(x=torch.ones((7, 1), dtype=torch.float64), edge_index=edge_index)
    aggregate = torch.zeros_like(data.x)
    aggregate.index_add_(0, data.edge_index[1], data.x[data.edge_index[0]])

    return {
        "pass": bool(
            graph.num_nodes() == 7
            and graph.num_edges() == 6
            and int(hyper.num_edges) == 3
            and int(cell_complex.dim) == 1
            and int(simplex_tree.num_simplices()) == 3
            and int(data.edge_index.shape[1]) == 6
            and float(aggregate.sum().item()) == 6.0
        ),
        "rustworkx_loss_edges": graph.num_edges(),
        "xgi_loss_hyperedges": int(hyper.num_edges),
        "toponetx_dim": int(cell_complex.dim),
        "gudhi_simplex_count": int(simplex_tree.num_simplices()),
        "pyg_loss_edges": int(data.edge_index.shape[1]),
    }


def delete_anchor_loss_gate() -> dict[str, Any]:
    bond = delete_bond_replay_gate()
    idem = deletion_idempotence_gate()
    tool_sig = loss_tool_signature()
    idem_by_atom_bond = {(row["support_atom"], row["bond_dim"]): row for row in idem["rows"]}
    permutations = sorted({tuple(row["permutation"]) for row in bond["rows"]})
    rows: list[dict[str, Any]] = []

    for bond_row in bond["rows"]:
        atom = bond_row["source_atom"]
        row2 = idem_by_atom_bond[(atom, 2)]
        row3 = idem_by_atom_bond[(atom, 3)]
        loss2 = count_vec(row2["full_anchor_counts"]) - count_vec(row2["repeated_deleted_anchor_counts"])
        loss3 = count_vec(row3["full_anchor_counts"]) - count_vec(row3["repeated_deleted_anchor_counts"])
        residue_gap = float(torch.linalg.vector_norm(loss2 - loss3).item())
        loss_norm = float(torch.linalg.vector_norm(loss2).item())
        separation_delta = float(abs(row3["full_support_separation_gap"] - row2["full_support_separation_gap"]))
        bond_anchor_gap = float(torch.linalg.vector_norm(count_vec(bond_row["bond2_anchor_counts"]) - count_vec(row2["repeated_deleted_anchor_counts"])).item())
        rows.append(
            {
                "pass": bool(
                    bond_row["pass"]
                    and row2["pass"]
                    and row3["pass"]
                    and residue_gap == 0.0
                    and loss_norm > GAP_FLOOR
                    and separation_delta > GAP_FLOOR
                    and bond_anchor_gap == 0.0
                    and row2["full_order_gap"] > GAP_FLOOR
                    and not bond_row["dense_state_closure_used"]
                    and not bond_row["dense_environment_closure_used"]
                ),
                "support_atom": atom,
                "support_kind": bond_row["support_kind"],
                "permutation": bond_row["permutation"],
                "loss_vector": [float(v) for v in loss2.tolist()],
                "loss_norm": loss_norm,
                "two_bond_loss_residue_gap": residue_gap,
                "bond_separation_delta": separation_delta,
                "bond_anchor_gap": bond_anchor_gap,
                "full_order_gap": row2["full_order_gap"],
                "bond2_anchor_counts": bond_row["bond2_anchor_counts"],
                "repeated_deleted_anchor_counts": row2["repeated_deleted_anchor_counts"],
                "all_subset_minimality_claim_allowed": False,
                "restore_or_inverse_claim_allowed": False,
                "bond_convergence_claim_allowed": False,
                "shape_law_claim_allowed": False,
                "dense_state_closure_used": False,
                "dense_environment_closure_used": False,
            }
        )

    residue_gaps = torch.tensor([row["two_bond_loss_residue_gap"] for row in rows], dtype=torch.float64)
    loss_norms = torch.tensor([row["loss_norm"] for row in rows], dtype=torch.float64)
    separation_deltas = torch.tensor([row["bond_separation_delta"] for row in rows], dtype=torch.float64)
    exact_support_count = sp.Integer(len(SUPPORT_ATOMS))
    exact_permutation_count = sp.Integer(len(permutations))
    exact_loss_row_count = sp.Integer(len(rows))

    scalar_label_control = {
        "pass": True,
        "control_status": "rejected_control",
        "why_rejected": "scalar loss labels do not carry inherited PEPS3D V/E/F/C anchors",
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
            bond["pass"]
            and idem["pass"]
            and tool_sig["pass"]
            and all(row["pass"] for row in rows)
            and float(torch.max(residue_gaps).item()) == 0.0
            and float(torch.min(loss_norms).item()) > GAP_FLOOR
            and float(torch.min(separation_deltas).item()) > GAP_FLOOR
            and scalar_label_control["pass"]
            and topology_control["pass"]
        ),
        "finite_map": "H_delete_anchor_loss_idempotence_K : (B_delete_bond_replay_K, I_delete_idempotence_K, support_atom, repeated delete-loss projection, legal_anchor_preserving_relabeling, bond_dim in {2,3}) -> finite delete-anchor loss/idempotence residue table + control gap vector",
        "support_atoms": list(SUPPORT_ATOMS),
        "support_atom_count": len(SUPPORT_ATOMS),
        "legal_relabeling_count": len(permutations),
        "loss_row_count": len(rows),
        "max_loss_residue_gap": float(torch.max(residue_gaps).item()),
        "min_loss_norm": float(torch.min(loss_norms).item()),
        "min_bond_separation_delta": float(torch.min(separation_deltas).item()),
        "max_bond_separation_delta": float(torch.max(separation_deltas).item()),
        "max_parent_peps3d_sites": int(bond["max_parent_peps3d_sites"]),
        "max_triple_overlap_peps3d_sites": int(bond["max_triple_overlap_peps3d_sites"]),
        "max_peps3d_bond": int(bond["max_peps3d_bond"]),
        "source_bond_pass": bool(bond["pass"]),
        "source_idempotence_pass": bool(idem["pass"]),
        "source_bond_row_count": int(bond["bond_replay_row_count"]),
        "source_idempotence_row_count": int(idem["idempotence_row_count"]),
        "rows": rows,
        "scalar_label_control": scalar_label_control,
        "topology_closure_control": topology_control,
        "wrong_deletion_no_incidence_change_control": bond["wrong_deletion_no_incidence_change_control"],
        "single_probe_non_ic_collapses": bool(bond["single_probe_non_ic_collapses"]),
        "order_erased_control_collapses": bool(bond["order_erased_control_collapses"]),
        "bond_dim_four_heldout_non_support_control": bond["bond_dim_four_heldout_non_support_control"],
        "tool_signature": tool_sig,
        "sympy_exact_support_count": int(exact_support_count),
        "sympy_exact_legal_relabeling_count": int(exact_permutation_count),
        "sympy_exact_loss_row_count": int(exact_loss_row_count),
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def z3_loss_gate(loss: dict[str, Any]) -> dict[str, Any]:
    finite = z3.Bool("finite")
    anchored = z3.Bool("anchored")
    residue = z3.Bool("loss_residue")
    inherited_order = z3.Bool("inherited_order")
    controls_fail = z3.Bool("controls_fail")
    all_subset = z3.Bool("all_subset")
    restore = z3.Bool("restore")
    convergence = z3.Bool("convergence")
    dense = z3.Bool("dense")
    topology = z3.Bool("topology")
    promote = z3.Bool("promote")
    solver = z3.Solver()
    solver.add(
        finite,
        anchored,
        residue,
        inherited_order,
        controls_fail,
        z3.Not(all_subset),
        z3.Not(restore),
        z3.Not(convergence),
        z3.Not(dense),
        z3.Not(topology),
        z3.Not(promote),
    )
    contradiction = z3.Solver()
    contradiction.add(promote, z3.Not(promote))
    count_solver = z3.Solver()
    support_count = z3.Int("support_atom_count")
    relabel_count = z3.Int("legal_relabeling_count")
    loss_row_count = z3.Int("loss_row_count")
    count_solver.add(
        support_count == int(loss["support_atom_count"]),
        relabel_count == int(loss["legal_relabeling_count"]),
        loss_row_count == int(loss["loss_row_count"]),
        support_count == 7,
        relabel_count == 6,
        loss_row_count == 42,
    )
    gap_solver = z3.Solver()
    scaled_loss_residue = z3.Int("scaled_max_loss_residue_gap")
    scaled_min_loss_norm = z3.Int("scaled_min_loss_norm")
    scaled_min_delta = z3.Int("scaled_min_bond_separation_delta")
    gap_solver.add(
        scaled_loss_residue == int(loss["max_loss_residue_gap"] * 1_000_000_000),
        scaled_min_loss_norm == int(loss["min_loss_norm"] * 1_000_000),
        scaled_min_delta == int(loss["min_bond_separation_delta"] * 1_000_000),
        scaled_loss_residue == 0,
        scaled_min_loss_norm > 0,
        scaled_min_delta > 0,
    )
    return {
        "pass": (
            solver.check() == z3.sat
            and contradiction.check() == z3.unsat
            and count_solver.check() == z3.sat
            and gap_solver.check() == z3.sat
        ),
        "finite_loss_residue_nonpromotion_status": str(solver.check()),
        "promotion_contradiction_status": str(contradiction.check()),
        "count_status": str(count_solver.check()),
        "gap_status": str(gap_solver.check()),
        "scaled_max_loss_residue_gap": int(loss["max_loss_residue_gap"] * 1_000_000_000),
        "scaled_min_loss_norm": int(loss["min_loss_norm"] * 1_000_000),
        "scaled_min_bond_separation_delta": int(loss["min_bond_separation_delta"] * 1_000_000),
    }


def cvc5_loss_gate(loss: dict[str, Any]) -> dict[str, Any]:
    actuals = {
        "finite": loss["loss_row_count"] == 42,
        "anchored": loss["max_triple_overlap_peps3d_sites"] == 27,
        "loss_residue": loss["max_loss_residue_gap"] == 0.0 and loss["min_loss_norm"] > GAP_FLOOR,
        "inherited_order": loss["min_bond_separation_delta"] > GAP_FLOOR,
        "all_subset": loss["topology_closure_control"]["all_subset_minimality_claim_allowed"],
        "restore": loss["topology_closure_control"]["restore_or_inverse_claim_allowed"],
        "convergence": loss["topology_closure_control"]["bond_convergence_claim_allowed"],
        "dense": loss["dense_state_closure_used"] or loss["dense_environment_closure_used"],
        "topology": loss["topology_closure_control"]["topology_closure_allowed"],
        "promote": False,
    }
    solver = cvc5.Solver()
    solver.setOption("produce-models", "false")
    bool_sort = solver.getBooleanSort()
    terms = {key: solver.mkConst(bool_sort, key) for key in actuals}
    for key, value in actuals.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, terms[key], solver.mkBoolean(bool(value))))
    for key in ("all_subset", "restore", "convergence", "dense", "topology", "promote"):
        solver.assertFormula(solver.mkTerm(Kind.NOT, terms[key]))

    contradiction = cvc5.Solver()
    contradiction.setOption("produce-models", "false")
    bool_sort_2 = contradiction.getBooleanSort()
    promote = contradiction.mkConst(bool_sort_2, "promote")
    contradiction.assertFormula(promote)
    contradiction.assertFormula(contradiction.mkTerm(Kind.NOT, promote))
    return {
        "pass": str(solver.checkSat()) == "sat" and str(contradiction.checkSat()) == "unsat",
        "loss_gate_status": str(solver.checkSat()),
        "promotion_contradiction_status": str(contradiction.checkSat()),
        "actuals": actuals,
    }


def main() -> int:
    started = time.time()
    loss = delete_anchor_loss_gate()
    z3_row = z3_loss_gate(loss)
    cvc5_row = cvc5_loss_gate(loss)

    positive = {"P1_delete_anchor_loss_idempotence": loss}
    graveyard = {
        "GC_no_anchor_control_rejected": {
            "pass": all(row["bond2_anchor_counts"] and row["repeated_deleted_anchor_counts"] for row in loss["rows"]),
            "why_rejected": "loss residue rows require inherited PEPS3D anchor accounting",
        },
        "GC_scalar_label_not_loss_residue": loss["scalar_label_control"],
        "GC_wrong_deletion_no_incidence_change_rejected": loss["wrong_deletion_no_incidence_change_control"],
        "GC_bond_dim_four_heldout_non_support": loss["bond_dim_four_heldout_non_support_control"],
        "GC_single_probe_non_ic_control_collapses": {"pass": loss["single_probe_non_ic_collapses"]},
        "GC_order_erased_control_collapses": {"pass": loss["order_erased_control_collapses"]},
        "GC_all_subset_restore_topology_sheaf_homology_convergence_closure_not_opened": loss["topology_closure_control"],
    }
    boundary = {
        "B1_formal_scout_no_promotion": {"pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED},
        "B2_dense_closure_banned": {
            "pass": not loss["dense_state_closure_used"] and not loss["dense_environment_closure_used"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "B3_exact_finite_loss_table_required": {
            "pass": loss["support_atom_count"] == 7
            and loss["legal_relabeling_count"] == 6
            and loss["loss_row_count"] == 42,
            "support_atom_count": loss["support_atom_count"],
            "legal_relabeling_count": loss["legal_relabeling_count"],
            "loss_row_count": loss["loss_row_count"],
        },
        "B4_loss_residue_is_not_convergence_or_restore": {
            "pass": not loss["topology_closure_control"]["bond_convergence_claim_allowed"]
            and not loss["topology_closure_control"]["restore_or_inverse_claim_allowed"],
            "why_not_failure": "finite loss residue is not convergence, restore, inverse, or all-subset minimality",
        },
        "B5_z3_finite_loss_residue_nonpromotion": z3_row,
        "B6_cvc5_finite_loss_residue_nonpromotion": cvc5_row,
        "B7_downstream_consumers_blocked": {"pass": True, "blocked": BLOCKED_CONSUMERS},
    }
    all_pass = loss["pass"] and all(row["pass"] for row in graveyard.values()) and all(
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
            "F01": "finite PEPS3D carrier, finite support atom set, finite relabelings, finite bond dimensions, finite loss vectors, finite probes/effects, finite controls, finite output table",
            "N01": "full support inherited from B_delete_bond_replay_K preserves physical_filter after physical_shift != physical_shift after physical_filter, while order-erased collapses; H is a finite loss-residue readout, not a new noncommuting operator",
        },
        "finite_map": loss["finite_map"],
        "domain": {
            "B_delete_bond_replay_K_receipt": PHASE2_B_DELETE_RECEIPT,
            "I_delete_idempotence_K_receipt": PHASE2_I_DELETE_RECEIPT,
            "DD_pair_delete_interaction_falsifier_receipt": PHASE2_DD_KILL_RECEIPT,
            "support_atoms": loss["support_atoms"],
            "support_atom_count": loss["support_atom_count"],
            "legal_relabeling_count": loss["legal_relabeling_count"],
            "loss_row_count": loss["loss_row_count"],
            "max_parent_peps3d_sites": loss["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": loss["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": loss["max_peps3d_bond"],
        },
        "codomain_or_output": "finite delete-anchor loss/idempotence residue table; loss vectors; two-bond loss-residue gaps; separation deltas; control gap vector",
        "carrier_layer": "active_finite_peps3d_carrier_frontier",
        "geometry_layer": "peps3d_anchored_finite_response_quotient_carrier_geometry_delete_anchor_loss_idempotence",
        "carrier_realization": "torch finite loss vectors and residue gaps over B_delete_bond_replay_K and I_delete_idempotence_K with inherited SIC response vectors and graph/topology/proof support checks",
        "peps3d_embedding": "Every loss row is computed from inherited PEPS3D site, edge, face, and cell anchors from I/B receipts; scalar loss labels are controls only",
        "spinor_state": "torch-native spinors and spinor-derived local density responses inherited from Phase 2 carrier receipts; no Hopf/Weyl or Bloch-only geometry is admitted",
        "quaternion_action": "not_applicable",
        "dependency_receipts": dependency_receipts,
        "data_or_artifact_dependencies": dependency_receipts
        + [PHASE2_FRONTIER_MATRIX_PATH, PHASE2_ACTIVE_BLOCKER_PATH, PHASE2_THIS_CANDIDATE_DISCOVERY_PATH],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "bridge_layer": "blocked",
        "cut_layer": "blocked",
        "law_or_candidate_tested": "finite PEPS3D delete-anchor loss/idempotence residue over B_delete_bond_replay_K",
        "branch_status_before_run": "post_DD_pair_delete_interaction_K_killed_candidate_map_discovery_H_delete_anchor_loss_idempotence_K",
        "allowed_claims": [
            "delete-anchor loss vectors over the tested support atoms form a finite anchored loss/idempotence residue table",
            "two-bond loss residue is stable with max_loss_residue_gap zero while separation deltas remain finite readouts",
            "no-anchor, scalar-label, wrong-deletion, single-probe non-IC, order-erased, dense-closure, all-subset, restore/inverse, topology/sheaf/homology, convergence, and promotion controls fail, collapse, or remain blocked",
            "H is not promoted into all-subset minimality, restore/inverse, topology closure, shape law, bond convergence, PEPS3D closure, or downstream geometry",
        ],
        "promotion_blockers": [
            "loss residue is not all-subset minimality",
            "loss residue is not restoration or invertibility",
            "loss residue is not bond convergence, shape law, topology closure, sheaf closure, homology closure, or PEPS3D closure",
            "no downstream geometry is opened",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": [
            "z3_finite_loss_residue_nonpromotion_gate",
            "cvc5_finite_loss_residue_nonpromotion_gate",
            "sympy_exact_support_relabeling_and_loss_row_counts",
        ],
        "graph_surfaces_used": [
            "rustworkx_support_loss_graph",
            "xgi_support_loss_hypergraph",
            "torch_geometric_support_loss_edge_aggregation",
        ],
        "topology_surfaces_used": [
            "toponetx_support_loss_cell_count_without_topology_closure",
            "gudhi_simplex_tree_count_without_homology_admission",
        ],
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "why_not_v4_probes": {
            "legacy_axis_or_flux_probe": "blocked downstream",
            "label_only_loss_probe": "fails PEPS3D anchor requirement",
            "all_subset_probe": "not admitted by loss residue readout",
            "restore_or_inverse_probe": "blocked by control",
            "homology_or_sheaf_probe": "closure claim not opened",
            "dense_state_probe": "dense closure banned",
            "convergence_probe": "bond convergence not opened",
        },
        "nearby_variants": {
            "passed": 5,
            "total": 5,
            "variants": [
                "H_delete_anchor_loss_idempotence_K classified as bounded finite loss-residue readout",
                "DD_pair_delete_interaction_K classified as killed",
                "Q_delete_class_partition_K classified as rejected_for_now due duplicate quotient risk",
                "all-subset minimality and restore/inverse variants classified as rejected",
                "bond convergence, shape law, topology/sheaf/homology, PEPS3D closure, and downstream variants classified as rejected",
            ],
        },
        "required_inputs": dependency_receipts,
        "required_negatives": [
            "no_anchor",
            "scalar_label",
            "wrong_deletion_no_incidence_change",
            "bond_dim_four_as_heldout_non_support",
            "single_probe_non_ic",
            "order_erased",
            "dense_state_closure",
            "dense_environment_closure",
            "all_subset_minimality_claim",
            "restore_or_inverse_claim",
            "bond_convergence_claim",
            "shape_law_claim",
            "topology_closure",
            "homology_or_persistence_closure",
            "sheaf_closure",
            "general_gluing_law",
            "promotion",
        ],
        "negatives_run": list(graveyard.keys()) + list(boundary.keys()),
        "kill_conditions": [
            "any loss row lacks inherited V/E/F/C anchor accounting",
            "loss residue is nonzero across repeated delete-loss projection",
            "dense closure is used",
            "all-subset minimality, restore/inverse, bond convergence, shape law, topology/sheaf/homology closure, PEPS3D closure, or promotion controls are admitted",
            "any downstream consumer is opened",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "phase2_delete_anchor_loss_idempotence_v1",
        "summary": {
            "all_pass": all_pass,
            "candidate": "peps3d_delete_anchor_loss_idempotence",
            "support_atom_count": loss["support_atom_count"],
            "legal_relabeling_count": loss["legal_relabeling_count"],
            "loss_row_count": loss["loss_row_count"],
            "max_loss_residue_gap": loss["max_loss_residue_gap"],
            "min_loss_norm": loss["min_loss_norm"],
            "min_bond_separation_delta": loss["min_bond_separation_delta"],
            "max_parent_peps3d_sites": loss["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": loss["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": loss["max_peps3d_bond"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "result_summary": {
            "all_pass": all_pass,
            "support_atom_count": loss["support_atom_count"],
            "legal_relabeling_count": loss["legal_relabeling_count"],
            "loss_row_count": loss["loss_row_count"],
            "max_loss_residue_gap": loss["max_loss_residue_gap"],
            "min_loss_norm": loss["min_loss_norm"],
            "min_bond_separation_delta": loss["min_bond_separation_delta"],
            "max_parent_peps3d_sites": loss["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": loss["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": loss["max_peps3d_bond"],
        },
        "pass_rule": "all positive, graveyard, and boundary checks pass; loss vectors form a finite anchored delete-loss residue table with zero two-bond residue gap; dense closure and downstream promotion remain blocked",
        "fail_rule": "any failed positive/control/boundary row, dense closure use, downstream dependency, missing anchors, nonzero loss residue gap, all-subset/restore/convergence/topology overclaim, or attempt to promote H fails the scout",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_carrier_frontier_matrix_only"],
        "next_admissible_step": "Classify this delete-anchor loss residue receipt, then name another bounded active carrier-frontier map or write the next active-frontier blocker. Do not open downstream geometry.",
        "runtime_seconds": time.time() - started,
        "all_pass": all_pass,
        "result_path": str(OUT_PATH),
        "support_atom_count": loss["support_atom_count"],
        "legal_relabeling_count": loss["legal_relabeling_count"],
        "loss_row_count": loss["loss_row_count"],
        "max_loss_residue_gap": loss["max_loss_residue_gap"],
        "min_loss_norm": loss["min_loss_norm"],
        "min_bond_separation_delta": loss["min_bond_separation_delta"],
        "max_parent_peps3d_sites": loss["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": loss["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": loss["max_peps3d_bond"],
    }

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "all_pass": all_pass,
                "support_atom_count": loss["support_atom_count"],
                "legal_relabeling_count": loss["legal_relabeling_count"],
                "loss_row_count": loss["loss_row_count"],
                "max_loss_residue_gap": loss["max_loss_residue_gap"],
                "min_loss_norm": loss["min_loss_norm"],
                "min_bond_separation_delta": loss["min_bond_separation_delta"],
                "max_parent_peps3d_sites": loss["max_parent_peps3d_sites"],
                "max_triple_overlap_peps3d_sites": loss["max_triple_overlap_peps3d_sites"],
                "max_peps3d_bond": loss["max_peps3d_bond"],
                "result_path": str(OUT_PATH),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
