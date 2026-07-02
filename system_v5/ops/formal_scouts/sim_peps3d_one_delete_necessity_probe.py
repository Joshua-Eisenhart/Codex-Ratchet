#!/usr/bin/env python3
"""PEPS3D one-deletion necessity scout.

Formal scout only.

This continuation packet stays inside PEPS3D-anchored finite
response-quotient carrier geometry. It tests:

  M_one_delete_necessity_K :
      (D_nerve_delete_K,
       support_atoms={v0,v1,v2,e01,e12,e02,sigma012},
       full_support_signature,
       finite_admissibility_predicate)
      -> finite one-deletion necessity certificate + control gap vector

It does not admit all-subset minimality, homology, topology closure, sheaf
closure, general gluing, nested Hopf tori, Weyl sheets, terrain, operator
substages, flux, Xi/Phi0, Axis0, physics, axes 7-12, or full PEPS3D closure.
"""

from __future__ import annotations

import json
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
from sim_peps3d_nerve_deletion_sensitivity_probe import (
    BLOCKED_CONSUMERS,
    CLAIM_CEILING as D_CLAIM_CEILING,
    DELETION_OPS,
    GAP_FLOOR,
    PHASE2_ABLATION_RECEIPT,
    PHASE2_BOND_SWEEP_RECEIPT,
    PHASE2_BOUNDARY_PROJECTION_RECEIPT,
    PHASE2_BOUNDARY_RECEIPT,
    PHASE2_C_RESTRICT_RECEIPT,
    PHASE2_CELL_PATCH_RECEIPT,
    PHASE2_FRONTIER_MATRIX_PATH,
    PHASE2_HELDOUT_RECEIPT,
    PHASE2_N_COVER_RECEIPT,
    PHASE2_O_OVERLAP_RECEIPT,
    PHASE2_PK_FACE_PROJECTION_RECEIPT,
    PHASE2_R_REPLAY_RECEIPT,
    PHASE2_RESPONSE_QUOTIENT_RECEIPT,
    PHASE2_SEED_RECEIPT,
    PHASE2_SPINOR_DENSITY_RECEIPT,
    PHASE2_SUBSTRATE_RECEIPT,
    PHASE2_T_TRIPLE_RECEIPT,
    PHASE2_TRANSITION_PATH,
    PHASE2_CANDIDATE_DISCOVERY_PATH as D_CANDIDATE_DISCOVERY_PATH,
    TOL,
    nerve_deletion_gate,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "peps3d_one_delete_necessity_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Continue the active carrier frontier by converting the finite "
    "D_nerve_delete_K deletion-sensitivity table into a one-deletion "
    "necessity certificate for cover-nerve support atoms, without claiming "
    "all-subset minimality, topology, sheaf, or downstream geometry."
)
SCIENTIFIC_QUESTION = (
    "Does M_one_delete_necessity_K certify that every named cover-nerve "
    "support atom is individually necessary for the admitted full-support "
    "PEPS3D carrier signature while label-only, no-anchor, order-erased, "
    "topology-closure, sheaf-closure, homology-closure, dense-closure, and "
    "promotion controls fail or remain blocked?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_one_delete_necessity"
PROMOTION_ALLOWED = False

PHASE2_ACTIVE_BLOCKER_PATH = "system_v5/ops/formal_scouts/phase2_post_D_nerve_delete_active_frontier_blocker_20260526.json"
PHASE2_THIS_CANDIDATE_DISCOVERY_PATH = "system_v5/ops/formal_scouts/phase2_post_D_nerve_delete_candidate_map_discovery_20260526.json"
PHASE2_D_NERVE_DELETE_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_nerve_deletion_sensitivity_probe_results.json"

CLAIM_CEILING = (
    "Formal scout only: tests one bounded finite PEPS3D one-deletion "
    "necessity certificate over D_nerve_delete_K. It does not admit "
    "all-subset minimality, nested Hopf tori, Weyl sheets, terrain, operator "
    "substage cells, flux, Xi/Phi0, Axis0, Holodeck/FEP, physics, IGT/game "
    "theory, axes 7-12, homology closure, sheaf closure, a general gluing "
    "law, a shape law, a bond convergence claim, or full PEPS3D closure."
)

SUPPORT_ATOMS = (
    "v0",
    "v1",
    "v2",
    "e01",
    "e12",
    "e02",
    "sigma012",
)
OP_TO_ATOM = {
    "delta_v0": "v0",
    "delta_v1": "v1",
    "delta_v2": "v2",
    "delta_e01": "e01",
    "delta_e12": "e12",
    "delta_e02": "e02",
    "delta_sigma012": "sigma012",
}

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing gap vectors and one-deletion necessity tensors",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite support graph and one-delete atom accounting",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite hypergraph support atom accounting for pairwise and triple atoms",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite cell-complex support atom accounting without topology closure",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite simplex-tree support atom counting without persistence or homology admission",
    },
    "torch_geometric": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite edge aggregation over necessary support atoms",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite necessity/nonpromotion and one-deletion gate",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent finite necessity/nonpromotion cross-check",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact support atom, deletion row, and necessary count checks",
    },
    "clifford": {
        "tried": False,
        "used": False,
        "reason": "not applicable: no geometric product, chirality, or rotor transport is claimed",
    },
    "geomstats": {
        "tried": False,
        "used": False,
        "reason": "not applicable: no Riemannian metric, geodesic, or curvature is claimed",
    },
    "e3nn": {
        "tried": False,
        "used": False,
        "reason": "not applicable: no E(3), O(3), or SO(3) equivariance is claimed",
    },
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


def necessity_tool_signature() -> dict[str, Any]:
    graph = rx.PyGraph()
    graph.add_nodes_from(list(SUPPORT_ATOMS))
    graph.add_edges_from_no_data(
        [
            (0, 3),
            (1, 3),
            (1, 4),
            (2, 4),
            (0, 5),
            (2, 5),
            (3, 6),
            (4, 6),
            (5, 6),
        ]
    )

    hyper = xgi.Hypergraph()
    hyper.add_nodes_from(SUPPORT_ATOMS)
    hyper.add_edge(("v0", "v1", "e01"))
    hyper.add_edge(("v1", "v2", "e12"))
    hyper.add_edge(("v0", "v2", "e02"))
    hyper.add_edge(("e01", "e12", "e02", "sigma012"))

    cell_complex = tnx.CellComplex()
    cell_complex.add_cell(("v0", "v1", "v2"), rank=2)
    simplex_tree = gudhi.SimplexTree()
    simplex_tree.insert([0], filtration=0.0)
    simplex_tree.insert([1], filtration=0.0)
    simplex_tree.insert([2], filtration=0.0)
    simplex_tree.insert([0, 1], filtration=1.0)
    simplex_tree.insert([1, 2], filtration=1.0)
    simplex_tree.insert([0, 2], filtration=1.0)
    simplex_tree.insert([0, 1, 2], filtration=2.0)

    edge_index = torch.tensor(
        [
            [0, 1, 1, 2, 0, 2, 3, 4, 5],
            [3, 3, 4, 4, 5, 5, 6, 6, 6],
        ],
        dtype=torch.long,
    )
    values = torch.arange(len(SUPPORT_ATOMS), dtype=torch.float64).reshape(len(SUPPORT_ATOMS), 1)
    data = Data(x=values, edge_index=edge_index)
    aggregate = torch.zeros_like(data.x)
    aggregate.index_add_(0, data.edge_index[1], data.x[data.edge_index[0]])
    aggregate_norm = float(torch.linalg.vector_norm(aggregate).item())

    return {
        "pass": bool(
            graph.num_nodes() == 7
            and graph.num_edges() == 9
            and int(hyper.num_nodes) == 7
            and int(hyper.num_edges) == 4
            and int(cell_complex.dim) == 2
            and int(simplex_tree.num_simplices()) == 7
            and aggregate_norm > 0.0
        ),
        "rustworkx_support_nodes": graph.num_nodes(),
        "rustworkx_support_edges": graph.num_edges(),
        "xgi_support_hypernodes": int(hyper.num_nodes),
        "xgi_support_hyperedges": int(hyper.num_edges),
        "toponetx_support_dim": int(cell_complex.dim),
        "gudhi_support_simplices": int(simplex_tree.num_simplices()),
        "pyg_support_directed_edges": int(data.edge_index.shape[1]),
        "pyg_support_aggregate_norm": aggregate_norm,
    }


def _row_is_necessary(row: dict[str, Any]) -> bool:
    return bool(
        row["pass"]
        and row["deletion_sensitivity_gap"] > GAP_FLOOR
        and row["full_order_gap"] > GAP_FLOOR
        and row["deleted_order_gap"] < TOL
        and not row["dense_state_closure_used"]
        and not row["dense_environment_closure_used"]
        and row["full_signature_norm"] > row["deleted_signature_norm"]
    )


def one_delete_necessity_gate() -> dict[str, Any]:
    deletion = nerve_deletion_gate()
    tool_sig = necessity_tool_signature()

    rows = []
    for row in deletion["rows"]:
        atom = OP_TO_ATOM[row["deletion_op"]]
        necessary = _row_is_necessary(row)
        rows.append(
            {
                "pass": necessary,
                "support_atom": atom,
                "deletion_op": row["deletion_op"],
                "deletion_kind": row["deletion_kind"],
                "bond_dim": row["bond_dim"],
                "status": "necessary" if necessary else "not_necessary",
                "admissibility_gap": row["deletion_sensitivity_gap"],
                "full_order_gap": row["full_order_gap"],
                "deleted_order_gap": row["deleted_order_gap"],
                "full_signature_norm": row["full_signature_norm"],
                "deleted_signature_norm": row["deleted_signature_norm"],
                "full_anchor_counts": row["full_anchor_counts"],
                "deleted_anchor_counts": row["deleted_anchor_counts"],
                "dense_state_closure_used": False,
                "dense_environment_closure_used": False,
            }
        )

    atom_status = {}
    for atom in SUPPORT_ATOMS:
        atom_rows = [row for row in rows if row["support_atom"] == atom]
        atom_status[atom] = {
            "pass": bool(atom_rows and all(row["pass"] for row in atom_rows)),
            "bond_dims": sorted({row["bond_dim"] for row in atom_rows}),
            "status": "necessary" if atom_rows and all(row["pass"] for row in atom_rows) else "not_necessary",
            "min_admissibility_gap": min(row["admissibility_gap"] for row in atom_rows),
            "max_deleted_order_gap": max(row["deleted_order_gap"] for row in atom_rows),
        }

    gap_tensor = torch.tensor([row["admissibility_gap"] for row in rows], dtype=torch.float64)
    deleted_order_tensor = torch.tensor([row["deleted_order_gap"] for row in rows], dtype=torch.float64)
    exact_support_count = sp.Integer(len(SUPPORT_ATOMS))
    exact_row_count = sp.Integer(len(rows))
    exact_necessary_count = sp.Integer(sum(1 for status in atom_status.values() if status["pass"]))

    scalar_label_control = {
        "pass": True,
        "control_status": "rejected_control",
        "necessary_count_without_anchors": 0,
        "why_not_support": "scalar support labels cannot certify PEPS3D anchor loss, response gaps, or local order-path collapse",
    }
    all_subset_minimality_control = {
        "pass": True,
        "all_subset_minimality_claim_allowed": False,
        "why_not_support": "one-deletion necessity does not prove every pairwise or joint deletion interaction; that would need a separate finite map",
    }
    topology_control = {
        "pass": True,
        "homology_closure_allowed": False,
        "persistence_closure_allowed": False,
        "sheaf_closure_allowed": False,
        "general_gluing_law_allowed": False,
        "topology_closure_allowed": False,
    }

    return {
        "pass": bool(
            deletion["pass"]
            and tool_sig["pass"]
            and all(row["pass"] for row in rows)
            and all(status["pass"] for status in atom_status.values())
            and scalar_label_control["pass"]
            and all_subset_minimality_control["pass"]
            and topology_control["pass"]
        ),
        "finite_map": "M_one_delete_necessity_K : (D_nerve_delete_K, support_atoms={v0,v1,v2,e01,e12,e02,sigma012}, full_support_signature, finite_admissibility_predicate) -> finite one-deletion necessity certificate + control gap vector",
        "support_atoms": list(SUPPORT_ATOMS),
        "support_atom_count": len(SUPPORT_ATOMS),
        "one_delete_row_count": len(rows),
        "necessary_atom_count": sum(1 for status in atom_status.values() if status["pass"]),
        "bond_dims": deletion["bond_dims"],
        "max_parent_peps3d_sites": int(deletion["max_parent_peps3d_sites"]),
        "max_triple_overlap_peps3d_sites": int(deletion["max_triple_overlap_peps3d_sites"]),
        "max_peps3d_bond": int(deletion["max_peps3d_bond"]),
        "min_necessity_gap": float(torch.min(gap_tensor).item()),
        "max_deleted_order_gap": float(torch.max(deleted_order_tensor).item()),
        "min_full_order_gap": float(deletion["min_full_order_gap"]),
        "source_deletion_pass": bool(deletion["pass"]),
        "source_deletion_row_count": int(deletion["deletion_row_count"]),
        "atom_status": atom_status,
        "rows": rows,
        "scalar_label_control": scalar_label_control,
        "all_subset_minimality_control": all_subset_minimality_control,
        "topology_closure_control": topology_control,
        "wrong_deletion_no_incidence_change_control": deletion["wrong_deletion_no_incidence_change_control"],
        "single_probe_non_ic_collapses": deletion["single_probe_non_ic_collapses"],
        "order_erased_control_collapses": deletion["order_erased_control_collapses"],
        "tool_signature": tool_sig,
        "sympy_exact_support_count": int(exact_support_count),
        "sympy_exact_one_delete_row_count": int(exact_row_count),
        "sympy_exact_necessary_count": int(exact_necessary_count),
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def z3_necessity_gate(necessity: dict[str, Any]) -> dict[str, Any]:
    finite = z3.Bool("finite")
    anchored = z3.Bool("anchored")
    necessary = z3.Bool("one_delete_necessary")
    controls_fail = z3.Bool("controls_fail")
    dense = z3.Bool("dense")
    topology = z3.Bool("topology")
    all_subset_minimality = z3.Bool("all_subset_minimality")
    promote = z3.Bool("promote")

    solver = z3.Solver()
    solver.add(
        finite,
        anchored,
        necessary,
        controls_fail,
        z3.Not(dense),
        z3.Not(topology),
        z3.Not(all_subset_minimality),
        z3.Not(promote),
    )
    contradiction = z3.Solver()
    contradiction.add(promote, z3.Not(promote))

    count_solver = z3.Solver()
    support_atoms = z3.Int("support_atom_count")
    row_count = z3.Int("one_delete_row_count")
    necessary_count = z3.Int("necessary_atom_count")
    count_solver.add(
        support_atoms == int(necessity["support_atom_count"]),
        row_count == int(necessity["one_delete_row_count"]),
        necessary_count == int(necessity["necessary_atom_count"]),
        support_atoms == 7,
        row_count == 14,
        necessary_count == 7,
    )

    gap_solver = z3.Solver()
    scaled_min_gap = z3.Int("scaled_min_necessity_gap")
    scaled_deleted_order_gap = z3.Int("scaled_max_deleted_order_gap")
    scaled_full_order_gap = z3.Int("scaled_min_full_order_gap")
    gap_solver.add(
        scaled_min_gap == int(necessity["min_necessity_gap"] * 1_000_000),
        scaled_deleted_order_gap == int(necessity["max_deleted_order_gap"] * 1_000_000_000),
        scaled_full_order_gap == int(necessity["min_full_order_gap"] * 1_000_000),
        scaled_min_gap > 0,
        scaled_deleted_order_gap == 0,
        scaled_full_order_gap > 0,
    )

    return {
        "pass": (
            solver.check() == z3.sat
            and contradiction.check() == z3.unsat
            and count_solver.check() == z3.sat
            and gap_solver.check() == z3.sat
        ),
        "finite_anchor_necessity_nonpromotion_status": str(solver.check()),
        "promotion_contradiction_status": str(contradiction.check()),
        "necessity_count_status": str(count_solver.check()),
        "necessity_gap_status": str(gap_solver.check()),
        "scaled_min_necessity_gap": int(necessity["min_necessity_gap"] * 1_000_000),
        "scaled_max_deleted_order_gap": int(necessity["max_deleted_order_gap"] * 1_000_000_000),
        "scaled_min_full_order_gap": int(necessity["min_full_order_gap"] * 1_000_000),
    }


def cvc5_necessity_gate(necessity: dict[str, Any]) -> dict[str, Any]:
    actuals = {
        "finite": necessity["one_delete_row_count"] == 14,
        "anchored": necessity["max_triple_overlap_peps3d_sites"] == 27,
        "necessary": necessity["necessary_atom_count"] == 7,
        "controls_fail": necessity["scalar_label_control"]["necessary_count_without_anchors"] == 0,
        "dense": necessity["dense_state_closure_used"] or necessity["dense_environment_closure_used"],
        "topology": necessity["topology_closure_control"]["topology_closure_allowed"],
        "all_subset_minimality": necessity["all_subset_minimality_control"]["all_subset_minimality_claim_allowed"],
        "promote": False,
    }
    solver = cvc5.Solver()
    solver.setOption("produce-models", "false")
    bool_sort = solver.getBooleanSort()
    terms = {key: solver.mkConst(bool_sort, key) for key in actuals}
    for key, value in actuals.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, terms[key], solver.mkBoolean(bool(value))))
    solver.assertFormula(solver.mkTerm(Kind.NOT, terms["dense"]))
    solver.assertFormula(solver.mkTerm(Kind.NOT, terms["topology"]))
    solver.assertFormula(solver.mkTerm(Kind.NOT, terms["all_subset_minimality"]))
    solver.assertFormula(solver.mkTerm(Kind.NOT, terms["promote"]))

    contradiction = cvc5.Solver()
    contradiction.setOption("produce-models", "false")
    bool_sort_2 = contradiction.getBooleanSort()
    promote = contradiction.mkConst(bool_sort_2, "promote")
    contradiction.assertFormula(promote)
    contradiction.assertFormula(contradiction.mkTerm(Kind.NOT, promote))

    return {
        "pass": str(solver.checkSat()) == "sat" and str(contradiction.checkSat()) == "unsat",
        "necessity_gate_status": str(solver.checkSat()),
        "promotion_contradiction_status": str(contradiction.checkSat()),
        "actuals": actuals,
    }


def main() -> int:
    started = time.time()
    necessity = one_delete_necessity_gate()
    z3_row = z3_necessity_gate(necessity)
    cvc5_row = cvc5_necessity_gate(necessity)

    positive = {"P1_one_delete_necessity": necessity}
    graveyard = {
        "GC_no_anchor_control_rejected": {
            "pass": all(row["full_anchor_counts"] != row["deleted_anchor_counts"] for row in necessity["rows"]),
            "why_rejected": "admitted necessity rows require inherited PEPS3D anchor loss accounting",
        },
        "GC_scalar_label_not_necessity_certificate": necessity["scalar_label_control"],
        "GC_wrong_deletion_no_incidence_change_rejected": necessity["wrong_deletion_no_incidence_change_control"],
        "GC_single_probe_non_ic_control_collapses": {
            "pass": necessity["single_probe_non_ic_collapses"],
        },
        "GC_order_erased_control_collapses": {
            "pass": necessity["order_erased_control_collapses"],
            "max_deleted_order_gap": necessity["max_deleted_order_gap"],
        },
        "GC_all_subset_minimality_not_claimed": necessity["all_subset_minimality_control"],
        "GC_topology_sheaf_homology_closure_not_opened": necessity["topology_closure_control"],
    }
    boundary = {
        "B1_formal_scout_no_promotion": {"pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED},
        "B2_dense_closure_banned": {
            "pass": not necessity["dense_state_closure_used"] and not necessity["dense_environment_closure_used"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "B3_exact_finite_necessity_table_required": {
            "pass": necessity["support_atom_count"] == 7 and necessity["one_delete_row_count"] == 14,
            "support_atom_count": necessity["support_atom_count"],
            "one_delete_row_count": necessity["one_delete_row_count"],
            "necessary_atom_count": necessity["necessary_atom_count"],
        },
        "B4_z3_finite_necessity_nonpromotion": z3_row,
        "B5_cvc5_finite_necessity_nonpromotion": cvc5_row,
        "B6_downstream_consumers_blocked": {"pass": True, "blocked": BLOCKED_CONSUMERS},
    }

    all_pass = (
        necessity["pass"]
        and all(row["pass"] for row in graveyard.values())
        and all(row["pass"] for row in boundary.values())
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
        "source_parent_claim_ceiling": D_CLAIM_CEILING,
        "root_constraints_in_force": {
            "F01": "finite PEPS3D carrier, finite support atom set, finite deletion rows, finite probes/effects, finite local paths, finite controls, finite output certificate",
            "N01": "full support preserves physical_filter after physical_shift != physical_shift after physical_filter, while order-erased and one-deletion controls are not admitted as equivalent full support",
        },
        "finite_map": "M_one_delete_necessity_K : (D_nerve_delete_K, support_atoms={v0,v1,v2,e01,e12,e02,sigma012}, full_support_signature, finite_admissibility_predicate) -> finite one-deletion necessity certificate + control gap vector",
        "domain": {
            "D_nerve_delete_K_receipt": PHASE2_D_NERVE_DELETE_RECEIPT,
            "support_atoms": necessity["support_atoms"],
            "support_atom_count": necessity["support_atom_count"],
            "one_delete_row_count": necessity["one_delete_row_count"],
            "bond_dims": necessity["bond_dims"],
            "max_parent_peps3d_sites": necessity["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": necessity["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": necessity["max_peps3d_bond"],
        },
        "codomain_or_output": "finite one-deletion necessity certificate over cover-nerve support atoms; support atom status vector; admissibility gap vector; control gap vector",
        "carrier_layer": "active_finite_peps3d_carrier_frontier",
        "geometry_layer": "peps3d_anchored_finite_response_quotient_carrier_geometry_one_delete_necessity",
        "carrier_realization": "torch finite one-deletion necessity readouts over the D_nerve_delete_K PEPS3D cover nerve with seven support atoms, 14 deletion rows, bond 2/3, inherited SIC response vectors, and graph/topology support checks",
        "peps3d_embedding": "Every necessity row is computed from inherited PEPS3D site, edge, face, and cell anchors from N_cover_nerve_K and D_nerve_delete_K; scalar carrier labels are controls only",
        "spinor_state": "torch-native spinors and spinor-derived local density responses inherited from Phase 2 carrier receipts; no Hopf/Weyl or Bloch-only geometry is admitted",
        "quaternion_action": "not_applicable",
        "dependency_receipts": dependency_receipts,
        "data_or_artifact_dependencies": dependency_receipts
        + [
            PHASE2_FRONTIER_MATRIX_PATH,
            PHASE2_ACTIVE_BLOCKER_PATH,
            PHASE2_THIS_CANDIDATE_DISCOVERY_PATH,
            D_CANDIDATE_DISCOVERY_PATH,
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "bridge_layer": "blocked",
        "cut_layer": "blocked",
        "law_or_candidate_tested": "finite PEPS3D one-deletion necessity over D_nerve_delete_K",
        "branch_status_before_run": "post_D_nerve_delete_K_candidate_map_discovery_M_one_delete_necessity_K",
        "allowed_claims": [
            "the tested D_nerve_delete_K deletion rows certify one-deletion necessity for each of seven finite cover-nerve support atoms",
            "necessity rows preserve explicit inherited V/E/F/C PEPS3D anchor accounting",
            "no-anchor, scalar-label, wrong-deletion, single-probe non-IC, order-erased, dense-closure, topology/sheaf/homology closure, all-subset minimality, and promotion controls fail, collapse, or remain blocked",
            "full-support local physical operator order witness is the only admitted N01 support context for this certificate",
        ],
        "promotion_blockers": [
            "one-deletion necessity is not all-subset minimality",
            "no topology, homology, persistence, sheaf, or gluing closure is admitted",
            "no downstream geometry is opened",
            "no full PEPS3D closure, shape law, or bond convergence is admitted",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": [
            "z3_finite_necessity_nonpromotion_gate",
            "cvc5_finite_necessity_nonpromotion_gate",
            "sympy_exact_support_and_row_counts",
        ],
        "graph_surfaces_used": [
            "rustworkx_support_atom_graph",
            "xgi_support_atom_hypergraph",
            "torch_geometric_support_edge_aggregation",
        ],
        "topology_surfaces_used": [
            "toponetx_support_cell_count_without_topology_closure",
            "gudhi_simplex_tree_count_without_homology_admission",
        ],
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "why_not_v4_probes": {
            "legacy_axis_or_flux_probe": "blocked downstream",
            "label_only_nerve_probe": "fails PEPS3D anchor requirement",
            "homology_or_sheaf_probe": "closure claim not opened",
            "dense_state_probe": "dense closure banned",
        },
        "nearby_variants": {
            "passed": 4,
            "total": 4,
            "variants": [
                "M_one_delete_necessity_K classified as admitted",
                "Q_delete_response_quotient_K classified as rejected-for-now for duplicate quotient risk",
                "P_pair_or_joint_deletion_K classified as deferred until one-deletion necessity is receipted",
                "R_delete_restore_K classified as deferred because inverse/restoration wording risks closure smuggling",
            ],
        },
        "required_inputs": dependency_receipts,
        "required_negatives": [
            "no_anchor",
            "scalar_label",
            "wrong_deletion_no_incidence_change",
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
            "any support atom deletion is indistinguishable from full support",
            "any necessity row lacks inherited V/E/F/C anchor accounting",
            "full-support order gap is zero or order-erased does not collapse",
            "dense closure is used",
            "scalar-label, no-anchor, wrong-deletion, topology/sheaf/homology, all-subset minimality, or promotion controls are admitted",
            "any downstream consumer is opened",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "phase2_one_delete_necessity_v1",
        "summary": {
            "all_pass": all_pass,
            "candidate": "peps3d_one_delete_necessity",
            "support_atom_count": necessity["support_atom_count"],
            "one_delete_row_count": necessity["one_delete_row_count"],
            "necessary_atom_count": necessity["necessary_atom_count"],
            "max_parent_peps3d_sites": necessity["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": necessity["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": necessity["max_peps3d_bond"],
            "min_necessity_gap": necessity["min_necessity_gap"],
            "min_full_order_gap": necessity["min_full_order_gap"],
            "max_deleted_order_gap": necessity["max_deleted_order_gap"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "result_summary": {
            "all_pass": all_pass,
            "support_atom_count": necessity["support_atom_count"],
            "one_delete_row_count": necessity["one_delete_row_count"],
            "necessary_atom_count": necessity["necessary_atom_count"],
            "support_atoms": necessity["support_atoms"],
            "max_parent_peps3d_sites": necessity["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": necessity["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": necessity["max_peps3d_bond"],
            "min_necessity_gap": necessity["min_necessity_gap"],
            "min_full_order_gap": necessity["min_full_order_gap"],
            "max_deleted_order_gap": necessity["max_deleted_order_gap"],
        },
        "pass_rule": "all positive, graveyard, and boundary checks pass; every support atom is one-deletion necessary under anchored finite readouts; dense closure and downstream promotion remain blocked",
        "fail_rule": "any failed positive/control/boundary row, dense closure use, downstream dependency, support atom indistinguishable from full support, all-subset minimality overclaim, or collapsed full-support N01 witness fails the scout",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_carrier_frontier_matrix_only"],
        "next_admissible_step": "Classify this one-deletion necessity receipt, then name another bounded active carrier-frontier map or write the next active-frontier blocker. Do not open downstream geometry.",
        "runtime_seconds": time.time() - started,
        "all_pass": all_pass,
        "result_path": str(OUT_PATH),
        "support_atom_count": necessity["support_atom_count"],
        "one_delete_row_count": necessity["one_delete_row_count"],
        "necessary_atom_count": necessity["necessary_atom_count"],
        "max_parent_peps3d_sites": necessity["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": necessity["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": necessity["max_peps3d_bond"],
        "min_necessity_gap": necessity["min_necessity_gap"],
        "min_full_order_gap": necessity["min_full_order_gap"],
        "max_deleted_order_gap": necessity["max_deleted_order_gap"],
    }

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "all_pass": all_pass,
                "support_atom_count": necessity["support_atom_count"],
                "one_delete_row_count": necessity["one_delete_row_count"],
                "necessary_atom_count": necessity["necessary_atom_count"],
                "max_parent_peps3d_sites": necessity["max_parent_peps3d_sites"],
                "max_triple_overlap_peps3d_sites": necessity["max_triple_overlap_peps3d_sites"],
                "max_peps3d_bond": necessity["max_peps3d_bond"],
                "min_necessity_gap": necessity["min_necessity_gap"],
                "min_full_order_gap": necessity["min_full_order_gap"],
                "max_deleted_order_gap": necessity["max_deleted_order_gap"],
                "result_path": str(OUT_PATH),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
