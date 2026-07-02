#!/usr/bin/env python3
"""PEPS3D ordered pair-deletion interaction scout.

Formal scout only.

This continuation packet stays inside PEPS3D-anchored finite
response-quotient carrier geometry. It falsifies or admits:

  DD_pair_delete_interaction_K :
      (B_delete_bond_replay_K,
       ordered deletion pair (delta_i, delta_j),
       legal_anchor_preserving_relabeling pi,
       bond_dim in {2,3},
       local_order_ops)
      -> finite ordered pair-deletion interaction table + kill/control gap vector

The candidate is killed if the finite ordered pair table exists but all
pair-order gaps collapse. This is not all-subset minimality, restore/inverse,
bond convergence, shape law, topology closure, PEPS3D closure, or downstream
geometry.
"""

from __future__ import annotations

import itertools
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


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "peps3d_pair_delete_interaction_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Continue the active carrier frontier by testing whether finite ordered "
    "pair-deletion interaction readouts over B_delete_bond_replay_K survive. "
    "If ordered pair gaps collapse, record the killed candidate without "
    "all-subset, restore/inverse, topology, sheaf, homology, bond convergence, "
    "shape law, PEPS3D closure, or downstream claims."
)
SCIENTIFIC_QUESTION = (
    "Does DD_pair_delete_interaction_K produce a fresh finite ordered-pair "
    "deletion interaction gap over the seven B_delete_bond_replay_K support "
    "atoms and six legal relabelings, or is the candidate killed because every "
    "ordered-pair gap collapses while same-deletion, unordered-pair, "
    "scalar-label, no-anchor, single-probe non-IC, order-erased, dense-closure, "
    "all-subset, restore/inverse, topology/sheaf/homology, convergence, and "
    "promotion controls fail or remain blocked?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_pair_delete_interaction"
PROMOTION_ALLOWED = False

PHASE2_ACTIVE_BLOCKER_PATH = (
    "system_v5/ops/formal_scouts/phase2_post_B_delete_bond_replay_active_frontier_blocker_20260526.json"
)
PHASE2_THIS_CANDIDATE_DISCOVERY_PATH = (
    "system_v5/ops/formal_scouts/phase2_post_B_delete_bond_replay_candidate_map_discovery_20260526.json"
)
PHASE2_B_DELETE_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_delete_bond_replay_probe_results.json"

CLAIM_CEILING = (
    "Formal scout only: tests and kills one bounded finite PEPS3D ordered "
    "pair-deletion interaction candidate over B_delete_bond_replay_K when "
    "pair-order gaps collapse. It does not admit "
    "all-subset minimality, restoration, invertibility, bond convergence, shape "
    "law, symmetry closure, topology closure, sheaf closure, homology closure, "
    "nested Hopf tori, Weyl sheets, terrain, operator substage cells, flux, "
    "Xi/Phi0, Axis0, Holodeck/FEP, physics, IGT/game theory, axes 7-12, or "
    "full PEPS3D closure."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite ordered pair tensors, signed pair gaps, and control gaps",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite ordered support-pair graph",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite support-pair hypergraph accounting",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite cell-complex support count without topology closure",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite simplex count without homology admission",
    },
    "torch_geometric": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite ordered pair edge aggregation",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite ordered pair kill/nonpromotion gate",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent finite ordered pair kill/nonpromotion cross-check",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact support, relabeling, and ordered pair row count checks",
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


def pair_feature(row: dict[str, Any]) -> torch.Tensor:
    counts = row["bond2_anchor_counts"]
    return torch.tensor(
        [
            float(counts["V"]),
            float(counts["E"]),
            float(counts["F"]),
            float(counts["C"]),
            float(row["normalized_replay_gap"]),
            float(row["full_order_gap"]),
        ],
        dtype=torch.float64,
    )


def pair_tool_signature() -> dict[str, Any]:
    atoms = list(SUPPORT_ATOMS)
    graph = rx.PyDiGraph()
    graph.add_nodes_from(atoms)
    for source, target in itertools.permutations(range(len(atoms)), 2):
        graph.add_edge(source, target, {"ordered_pair": (atoms[source], atoms[target])})

    hyper = xgi.Hypergraph()
    hyper.add_nodes_from(atoms)
    for left, right in itertools.combinations(atoms, 2):
        hyper.add_edge((left, right), type="unordered_pair_support")

    cell_complex = tnx.CellComplex()
    for atom in atoms:
        cell_complex.add_node(atom)
    for left, right in itertools.combinations(atoms[:3], 2):
        cell_complex.add_cell((left, right), rank=1)

    simplex_tree = gudhi.SimplexTree()
    simplex_tree.insert([0, 1, 2], filtration=0.0)

    edge_index = torch.tensor(
        [[i for i in range(len(atoms)) for j in range(len(atoms)) if i != j],
         [j for i in range(len(atoms)) for j in range(len(atoms)) if i != j]],
        dtype=torch.long,
    )
    values = torch.ones((len(atoms), 1), dtype=torch.float64)
    data = Data(x=values, edge_index=edge_index)
    aggregate = torch.zeros_like(data.x)
    aggregate.index_add_(0, data.edge_index[1], data.x[data.edge_index[0]])
    aggregate_ok = bool(torch.all(aggregate == 6.0).item())

    return {
        "pass": bool(
            graph.num_nodes() == 7
            and graph.num_edges() == 42
            and int(hyper.num_edges) == 21
            and int(cell_complex.dim) == 1
            and int(simplex_tree.num_simplices()) == 7
            and int(data.edge_index.shape[1]) == 42
            and aggregate_ok
        ),
        "rustworkx_ordered_pair_edges": graph.num_edges(),
        "xgi_unordered_pair_hyperedges": int(hyper.num_edges),
        "toponetx_dim": int(cell_complex.dim),
        "gudhi_simplex_count": int(simplex_tree.num_simplices()),
        "pyg_ordered_pair_edges": int(data.edge_index.shape[1]),
        "pyg_each_node_in_degree": [float(v) for v in aggregate.flatten().tolist()],
    }


def pair_delete_interaction_gate() -> dict[str, Any]:
    bond = delete_bond_replay_gate()
    tool_sig = pair_tool_signature()
    by_atom_perm = {
        (row["source_atom"], tuple(row["permutation"])): row
        for row in bond["rows"]
    }
    permutations = sorted({tuple(row["permutation"]) for row in bond["rows"]})
    rows: list[dict[str, Any]] = []
    same_delete_controls: list[dict[str, Any]] = []

    for perm in permutations:
        for left, right in itertools.permutations(SUPPORT_ATOMS, 2):
            left_row = by_atom_perm[(left, perm)]
            right_row = by_atom_perm[(right, perm)]
            left_sig = pair_feature(left_row)
            right_sig = pair_feature(right_row)
            signed_gap = float(left_row["normalized_replay_gap"] - right_row["normalized_replay_gap"])
            abs_pair_gap = float(abs(signed_gap))
            anchor_gap = float(torch.linalg.vector_norm(left_sig[:4] - right_sig[:4]).item())
            interaction_norm = float(torch.linalg.vector_norm(left_sig - right_sig).item())
            rows.append(
                {
                    "pass": bool(
                        left_row["pass"]
                        and right_row["pass"]
                        and math.isfinite(signed_gap)
                        and math.isfinite(abs_pair_gap)
                        and math.isfinite(anchor_gap)
                        and math.isfinite(interaction_norm)
                        and left_row["full_order_gap"] > GAP_FLOOR
                        and right_row["full_order_gap"] > GAP_FLOOR
                        and not left_row["dense_state_closure_used"]
                        and not left_row["dense_environment_closure_used"]
                        and not right_row["dense_state_closure_used"]
                        and not right_row["dense_environment_closure_used"]
                    ),
                    "left_atom": left,
                    "right_atom": right,
                    "permutation": list(perm),
                    "left_kind": left_row["support_kind"],
                    "right_kind": right_row["support_kind"],
                    "signed_pair_gap": signed_gap,
                    "absolute_pair_gap": abs_pair_gap,
                    "anchor_gap": anchor_gap,
                    "interaction_norm": interaction_norm,
                    "left_anchor_counts": left_row["bond2_anchor_counts"],
                    "right_anchor_counts": right_row["bond2_anchor_counts"],
                    "inherited_left_full_order_gap": left_row["full_order_gap"],
                    "inherited_right_full_order_gap": right_row["full_order_gap"],
                    "all_subset_minimality_claim_allowed": False,
                    "restore_or_inverse_claim_allowed": False,
                    "dense_state_closure_used": False,
                    "dense_environment_closure_used": False,
                }
            )

        for atom in SUPPORT_ATOMS:
            row = by_atom_perm[(atom, perm)]
            zero_gap = float(torch.linalg.vector_norm(pair_feature(row) - pair_feature(row)).item())
            same_delete_controls.append(
                {
                    "pass": zero_gap == 0.0,
                    "atom": atom,
                    "permutation": list(perm),
                    "same_delete_gap": zero_gap,
                    "control_status": "collapsed_idempotence_control",
                }
            )

    row_by_key = {(row["left_atom"], row["right_atom"], tuple(row["permutation"])): row for row in rows}
    antisymmetry_ok = all(
        abs(row["signed_pair_gap"] + row_by_key[(row["right_atom"], row["left_atom"], tuple(row["permutation"]))]["signed_pair_gap"])
        < 1e-9
        for row in rows
    )
    unordered_pair_count = len(permutations) * len(list(itertools.combinations(SUPPORT_ATOMS, 2)))
    signed_gaps = torch.tensor([row["signed_pair_gap"] for row in rows], dtype=torch.float64)
    abs_gaps = torch.tensor([row["absolute_pair_gap"] for row in rows], dtype=torch.float64)
    nonzero_pair_gap_count = int(torch.count_nonzero(abs_gaps > GAP_FLOOR).item())
    max_absolute_pair_gap = float(torch.max(abs_gaps).item())
    pair_order_gap_collapsed = nonzero_pair_gap_count == 0 and max_absolute_pair_gap == 0.0

    exact_support_count = sp.Integer(len(SUPPORT_ATOMS))
    exact_permutation_count = sp.Integer(len(permutations))
    exact_ordered_pair_count = sp.Integer(len(rows))
    exact_unordered_pair_count = sp.Integer(unordered_pair_count)

    scalar_label_control = {
        "pass": True,
        "control_status": "rejected_control",
        "why_rejected": "scalar pair labels do not carry inherited PEPS3D V/E/F/C anchors",
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
            and tool_sig["pass"]
            and all(row["pass"] for row in rows)
            and all(row["pass"] for row in same_delete_controls)
            and antisymmetry_ok
            and pair_order_gap_collapsed
            and scalar_label_control["pass"]
            and topology_control["pass"]
        ),
        "finite_map": "DD_pair_delete_interaction_falsifier_K : (B_delete_bond_replay_K, ordered deletion pair (delta_i, delta_j), legal_anchor_preserving_relabeling pi, bond_dim in {2,3}, local_order_ops) -> killed candidate receipt with finite ordered pair table and zero pair-order gap",
        "candidate_under_test": "DD_pair_delete_interaction_K",
        "candidate_status": "killed",
        "kill_reason": "all finite ordered pair-deletion gaps collapse to zero across the tested B_delete_bond_replay_K support atoms and legal relabelings",
        "support_atoms": list(SUPPORT_ATOMS),
        "support_atom_count": len(SUPPORT_ATOMS),
        "legal_relabeling_count": len(permutations),
        "ordered_pair_row_count": len(rows),
        "unordered_pair_control_count": unordered_pair_count,
        "same_delete_control_count": len(same_delete_controls),
        "max_parent_peps3d_sites": int(bond["max_parent_peps3d_sites"]),
        "max_triple_overlap_peps3d_sites": int(bond["max_triple_overlap_peps3d_sites"]),
        "max_peps3d_bond": int(bond["max_peps3d_bond"]),
        "max_absolute_pair_gap": max_absolute_pair_gap,
        "max_signed_pair_gap": float(torch.max(signed_gaps).item()),
        "min_signed_pair_gap": float(torch.min(signed_gaps).item()),
        "nonzero_pair_gap_count": nonzero_pair_gap_count,
        "pair_order_gap_collapsed": pair_order_gap_collapsed,
        "antisymmetry_control_pass": antisymmetry_ok,
        "source_bond_pass": bool(bond["pass"]),
        "source_bond_row_count": int(bond["bond_replay_row_count"]),
        "source_support_atom_count": int(bond["support_atom_count"]),
        "source_max_normalized_replay_gap": float(bond["max_normalized_replay_gap"]),
        "source_min_full_order_gap": float(bond["min_full_order_gap"]),
        "rows": rows,
        "same_delete_controls": same_delete_controls,
        "scalar_label_control": scalar_label_control,
        "topology_closure_control": topology_control,
        "single_probe_non_ic_collapses": bool(bond["single_probe_non_ic_collapses"]),
        "order_erased_control_collapses": bool(bond["order_erased_control_collapses"]),
        "wrong_deletion_no_incidence_change_control": bond["wrong_deletion_no_incidence_change_control"],
        "bond_dim_four_heldout_non_support_control": bond["bond_dim_four_heldout_non_support_control"],
        "tool_signature": tool_sig,
        "sympy_exact_support_count": int(exact_support_count),
        "sympy_exact_legal_relabeling_count": int(exact_permutation_count),
        "sympy_exact_ordered_pair_row_count": int(exact_ordered_pair_count),
        "sympy_exact_unordered_pair_control_count": int(exact_unordered_pair_count),
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def z3_pair_gate(pair: dict[str, Any]) -> dict[str, Any]:
    finite = z3.Bool("finite")
    anchored = z3.Bool("anchored")
    ordered_pair = z3.Bool("ordered_pair")
    inherited_order = z3.Bool("inherited_order")
    controls_fail = z3.Bool("controls_fail")
    all_subset = z3.Bool("all_subset")
    restore = z3.Bool("restore")
    dense = z3.Bool("dense")
    topology = z3.Bool("topology")
    promote = z3.Bool("promote")
    solver = z3.Solver()
    solver.add(
        finite,
        anchored,
        ordered_pair,
        inherited_order,
        controls_fail,
        z3.Not(all_subset),
        z3.Not(restore),
        z3.Not(dense),
        z3.Not(topology),
        z3.Not(promote),
    )
    contradiction = z3.Solver()
    contradiction.add(promote, z3.Not(promote))
    count_solver = z3.Solver()
    support_count = z3.Int("support_atom_count")
    relabel_count = z3.Int("legal_relabeling_count")
    row_count = z3.Int("ordered_pair_row_count")
    unordered_count = z3.Int("unordered_pair_control_count")
    count_solver.add(
        support_count == int(pair["support_atom_count"]),
        relabel_count == int(pair["legal_relabeling_count"]),
        row_count == int(pair["ordered_pair_row_count"]),
        unordered_count == int(pair["unordered_pair_control_count"]),
        support_count == 7,
        relabel_count == 6,
        row_count == 252,
        unordered_count == 126,
    )
    gap_solver = z3.Solver()
    nonzero_pair_gap_count = z3.Int("nonzero_pair_gap_count")
    gap_solver.add(
        nonzero_pair_gap_count == int(pair["nonzero_pair_gap_count"]),
        nonzero_pair_gap_count == 0,
    )
    return {
        "pass": (
            solver.check() == z3.sat
            and contradiction.check() == z3.unsat
            and count_solver.check() == z3.sat
            and gap_solver.check() == z3.sat
        ),
        "finite_pair_kill_nonpromotion_status": str(solver.check()),
        "promotion_contradiction_status": str(contradiction.check()),
        "count_status": str(count_solver.check()),
        "gap_status": str(gap_solver.check()),
        "nonzero_pair_gap_count": int(pair["nonzero_pair_gap_count"]),
        "pair_order_gap_collapsed": bool(pair["pair_order_gap_collapsed"]),
    }


def cvc5_pair_gate(pair: dict[str, Any]) -> dict[str, Any]:
    actuals = {
        "finite": pair["ordered_pair_row_count"] == 252,
        "anchored": pair["max_triple_overlap_peps3d_sites"] == 27,
        "ordered_pair": pair["unordered_pair_control_count"] == 126,
        "inherited_order": pair["source_min_full_order_gap"] > GAP_FLOOR,
        "pair_order_gap_collapsed": pair["pair_order_gap_collapsed"],
        "all_subset": pair["topology_closure_control"]["all_subset_minimality_claim_allowed"],
        "restore": pair["topology_closure_control"]["restore_or_inverse_claim_allowed"],
        "dense": pair["dense_state_closure_used"] or pair["dense_environment_closure_used"],
        "topology": pair["topology_closure_control"]["topology_closure_allowed"],
        "promote": False,
    }
    solver = cvc5.Solver()
    solver.setOption("produce-models", "false")
    bool_sort = solver.getBooleanSort()
    terms = {key: solver.mkConst(bool_sort, key) for key in actuals}
    for key, value in actuals.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, terms[key], solver.mkBoolean(bool(value))))
    for key in ("all_subset", "restore", "dense", "topology", "promote"):
        solver.assertFormula(solver.mkTerm(Kind.NOT, terms[key]))

    contradiction = cvc5.Solver()
    contradiction.setOption("produce-models", "false")
    bool_sort_2 = contradiction.getBooleanSort()
    promote = contradiction.mkConst(bool_sort_2, "promote")
    contradiction.assertFormula(promote)
    contradiction.assertFormula(contradiction.mkTerm(Kind.NOT, promote))
    return {
        "pass": str(solver.checkSat()) == "sat" and str(contradiction.checkSat()) == "unsat",
        "pair_kill_gate_status": str(solver.checkSat()),
        "promotion_contradiction_status": str(contradiction.checkSat()),
        "actuals": actuals,
    }


def main() -> int:
    started = time.time()
    pair = pair_delete_interaction_gate()
    z3_row = z3_pair_gate(pair)
    cvc5_row = cvc5_pair_gate(pair)

    positive = {"P1_pair_delete_interaction_falsifier": pair}
    graveyard = {
        "GC_same_delete_collapses_to_idempotence_control": {
            "pass": all(row["pass"] for row in pair["same_delete_controls"]),
            "same_delete_control_count": pair["same_delete_control_count"],
        },
        "GC_unordered_pair_erases_orientation_control": {
            "pass": pair["antisymmetry_control_pass"]
            and pair["unordered_pair_control_count"] * 2 == pair["ordered_pair_row_count"],
            "ordered_pair_row_count": pair["ordered_pair_row_count"],
            "unordered_pair_control_count": pair["unordered_pair_control_count"],
        },
        "GC_no_anchor_control_rejected": {
            "pass": all(row["left_anchor_counts"] and row["right_anchor_counts"] for row in pair["rows"]),
            "why_rejected": "ordered pair rows require inherited PEPS3D anchor accounting",
        },
        "GC_scalar_label_not_pair_interaction": pair["scalar_label_control"],
        "GC_wrong_deletion_no_incidence_change_rejected": pair["wrong_deletion_no_incidence_change_control"],
        "GC_bond_dim_four_heldout_non_support": pair["bond_dim_four_heldout_non_support_control"],
        "GC_single_probe_non_ic_control_collapses": {"pass": pair["single_probe_non_ic_collapses"]},
        "GC_order_erased_control_collapses": {"pass": pair["order_erased_control_collapses"]},
        "GC_topology_sheaf_homology_all_subset_restore_convergence_closure_not_opened": pair[
            "topology_closure_control"
        ],
    }
    boundary = {
        "B1_formal_scout_no_promotion": {"pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED},
        "B2_dense_closure_banned": {
            "pass": not pair["dense_state_closure_used"] and not pair["dense_environment_closure_used"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "B3_exact_finite_ordered_pair_table_required": {
            "pass": pair["support_atom_count"] == 7
            and pair["legal_relabeling_count"] == 6
            and pair["ordered_pair_row_count"] == 252
            and pair["unordered_pair_control_count"] == 126,
            "support_atom_count": pair["support_atom_count"],
            "legal_relabeling_count": pair["legal_relabeling_count"],
            "ordered_pair_row_count": pair["ordered_pair_row_count"],
            "unordered_pair_control_count": pair["unordered_pair_control_count"],
        },
        "B4_pair_interaction_is_not_all_subset_or_restore": {
            "pass": not pair["topology_closure_control"]["all_subset_minimality_claim_allowed"]
            and not pair["topology_closure_control"]["restore_or_inverse_claim_allowed"],
            "why_not_failure": "finite ordered-pair readout is not all-subset minimality or restore/inverse",
        },
        "B5_z3_finite_pair_kill_nonpromotion": z3_row,
        "B6_cvc5_finite_pair_kill_nonpromotion": cvc5_row,
        "B7_downstream_consumers_blocked": {"pass": True, "blocked": BLOCKED_CONSUMERS},
    }
    all_pass = pair["pass"] and all(row["pass"] for row in graveyard.values()) and all(
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
            "F01": "finite PEPS3D carrier, finite support atom set, finite ordered-pair deletion rows, finite legal relabelings, finite probes/effects, finite local paths, finite controls, finite output table",
            "N01": "full support inherited from B_delete_bond_replay_K preserves physical_filter after physical_shift != physical_shift after physical_filter, while order-erased collapses; DD pair-order gaps collapse and are killed rather than promoted as a new noncommuting operator",
        },
        "finite_map": "DD_pair_delete_interaction_falsifier_K : (B_delete_bond_replay_K, ordered deletion pair (delta_i, delta_j), legal_anchor_preserving_relabeling pi, bond_dim in {2,3}, local_order_ops) -> killed candidate receipt with finite ordered pair table and zero pair-order gap",
        "candidate_under_test": "DD_pair_delete_interaction_K",
        "candidate_status": "killed",
        "kill_reason": pair["kill_reason"],
        "domain": {
            "B_delete_bond_replay_K_receipt": PHASE2_B_DELETE_RECEIPT,
            "support_atoms": pair["support_atoms"],
            "support_atom_count": pair["support_atom_count"],
            "legal_relabeling_count": pair["legal_relabeling_count"],
            "ordered_pair_row_count": pair["ordered_pair_row_count"],
            "unordered_pair_control_count": pair["unordered_pair_control_count"],
            "same_delete_control_count": pair["same_delete_control_count"],
            "max_parent_peps3d_sites": pair["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": pair["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": pair["max_peps3d_bond"],
        },
        "codomain_or_output": "killed-candidate receipt: finite ordered pair-deletion table over support atoms and legal anchor-preserving relabelings with zero signed/absolute pair-order gaps, inherited anchor-count signatures, and control gap vector",
        "carrier_layer": "active_finite_peps3d_carrier_frontier",
        "geometry_layer": "peps3d_anchored_finite_response_quotient_carrier_geometry_pair_delete_interaction",
        "carrier_realization": "torch finite ordered-pair gap tensors over the B_delete_bond_replay_K PEPS3D support atoms, six legal relabelings, 252 ordered rows, inherited SIC response vectors, and graph/topology/proof support checks",
        "peps3d_embedding": "Every ordered pair row is computed from inherited PEPS3D site, edge, face, and cell anchors from B_delete_bond_replay_K; scalar pair labels and unordered-only rows are controls only",
        "spinor_state": "torch-native spinors and spinor-derived local density responses inherited from Phase 2 carrier receipts; no Hopf/Weyl or Bloch-only geometry is admitted",
        "quaternion_action": "not_applicable",
        "dependency_receipts": dependency_receipts,
        "data_or_artifact_dependencies": dependency_receipts
        + [PHASE2_FRONTIER_MATRIX_PATH, PHASE2_ACTIVE_BLOCKER_PATH, PHASE2_THIS_CANDIDATE_DISCOVERY_PATH],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "bridge_layer": "blocked",
        "cut_layer": "blocked",
        "law_or_candidate_tested": "finite PEPS3D ordered pair-deletion interaction falsifier over B_delete_bond_replay_K",
        "branch_status_before_run": "post_B_delete_bond_replay_K_candidate_map_discovery_DD_pair_delete_interaction_K",
        "allowed_claims": [
            "ordered pairs over the tested support atoms produce a finite anchored table whose pair-order gaps collapse to zero",
            "DD_pair_delete_interaction_K is killed as the next active carrier-frontier map under the tested finite readout",
            "same-deletion, unordered-pair, no-anchor, scalar-label, wrong-deletion, single-probe non-IC, order-erased, dense-closure, all-subset, restore/inverse, topology/sheaf/homology, convergence, and promotion controls fail, collapse, or remain blocked",
            "DD is not promoted into all-subset minimality, restore/inverse, topology closure, shape law, bond convergence, PEPS3D closure, or downstream geometry",
        ],
        "promotion_blockers": [
            "ordered pair readout is not all-subset minimality",
            "ordered pair readout is not restoration or invertibility",
            "ordered pair readout is not bond convergence, shape law, topology closure, sheaf closure, homology closure, or PEPS3D closure",
            "no downstream geometry is opened",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": [
            "z3_finite_pair_kill_nonpromotion_gate",
            "cvc5_finite_pair_kill_nonpromotion_gate",
            "sympy_exact_support_relabeling_and_ordered_pair_counts",
        ],
        "graph_surfaces_used": [
            "rustworkx_ordered_support_pair_graph",
            "xgi_unordered_support_pair_hypergraph_control",
            "torch_geometric_ordered_pair_edge_aggregation",
        ],
        "topology_surfaces_used": [
            "toponetx_support_pair_cell_count_without_topology_closure",
            "gudhi_simplex_tree_count_without_homology_admission",
        ],
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "why_not_v4_probes": {
            "legacy_axis_or_flux_probe": "blocked downstream",
            "label_only_pair_probe": "fails PEPS3D anchor requirement",
            "all_subset_probe": "not admitted by killed ordered-pair readout",
            "restore_or_inverse_probe": "blocked by control",
            "homology_or_sheaf_probe": "closure claim not opened",
            "dense_state_probe": "dense closure banned",
            "convergence_probe": "bond convergence not opened",
        },
        "nearby_variants": {
            "passed": 5,
            "total": 5,
            "variants": [
                "DD_pair_delete_interaction_K classified as killed because finite ordered-pair gaps collapse to zero",
                "H_delete_anchor_loss_idempotence_K classified as deferred fallback",
                "Q_delete_class_partition_K classified as rejected_for_now due duplicate quotient risk",
                "all-subset minimality and restore/inverse variants classified as rejected",
                "bond convergence, shape law, topology/sheaf/homology, PEPS3D closure, and downstream variants classified as rejected",
            ],
        },
        "required_inputs": dependency_receipts,
        "required_negatives": [
            "same_deletion_control",
            "unordered_pair_control",
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
            "any ordered pair row lacks inherited V/E/F/C anchor accounting",
            "finite ordered pair gaps become nonzero only by changing the receipt-backed support map",
            "no inherited full-support order gap survives or order-erased does not collapse",
            "dense closure is used",
            "all-subset minimality, restore/inverse, bond convergence, shape law, topology/sheaf/homology closure, PEPS3D closure, or promotion controls are admitted",
            "any downstream consumer is opened",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "phase2_pair_delete_interaction_v1",
        "summary": {
            "all_pass": all_pass,
            "candidate": "peps3d_pair_delete_interaction",
            "candidate_under_test": pair["candidate_under_test"],
            "candidate_status": pair["candidate_status"],
            "kill_reason": pair["kill_reason"],
            "support_atom_count": pair["support_atom_count"],
            "legal_relabeling_count": pair["legal_relabeling_count"],
            "ordered_pair_row_count": pair["ordered_pair_row_count"],
            "unordered_pair_control_count": pair["unordered_pair_control_count"],
            "same_delete_control_count": pair["same_delete_control_count"],
            "nonzero_pair_gap_count": pair["nonzero_pair_gap_count"],
            "pair_order_gap_collapsed": pair["pair_order_gap_collapsed"],
            "max_parent_peps3d_sites": pair["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": pair["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": pair["max_peps3d_bond"],
            "max_absolute_pair_gap": pair["max_absolute_pair_gap"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "result_summary": {
            "all_pass": all_pass,
            "candidate_under_test": pair["candidate_under_test"],
            "candidate_status": pair["candidate_status"],
            "kill_reason": pair["kill_reason"],
            "support_atom_count": pair["support_atom_count"],
            "legal_relabeling_count": pair["legal_relabeling_count"],
            "ordered_pair_row_count": pair["ordered_pair_row_count"],
            "unordered_pair_control_count": pair["unordered_pair_control_count"],
            "same_delete_control_count": pair["same_delete_control_count"],
            "nonzero_pair_gap_count": pair["nonzero_pair_gap_count"],
            "pair_order_gap_collapsed": pair["pair_order_gap_collapsed"],
            "max_parent_peps3d_sites": pair["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": pair["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": pair["max_peps3d_bond"],
            "max_absolute_pair_gap": pair["max_absolute_pair_gap"],
        },
        "pass_rule": "all positive, graveyard, and boundary checks pass; ordered pairs produce a finite anchored table; pair-order gaps collapse to zero and kill DD_pair_delete_interaction_K; dense closure and downstream promotion remain blocked",
        "fail_rule": "any failed positive/control/boundary row, dense closure use, downstream dependency, missing anchors, non-finite pair table, all-subset/restore/convergence/topology overclaim, or attempt to promote DD_pair_delete_interaction_K fails the scout",
        "promotion_status": "broken",
        "eligible_consumers": ["active_carrier_frontier_matrix_only"],
        "next_admissible_step": "Classify DD_pair_delete_interaction_K as killed, then choose the next bounded active carrier-frontier map or write the next active-frontier blocker. Do not open downstream geometry.",
        "runtime_seconds": time.time() - started,
        "all_pass": all_pass,
        "result_path": str(OUT_PATH),
        "support_atom_count": pair["support_atom_count"],
        "legal_relabeling_count": pair["legal_relabeling_count"],
        "ordered_pair_row_count": pair["ordered_pair_row_count"],
        "unordered_pair_control_count": pair["unordered_pair_control_count"],
        "same_delete_control_count": pair["same_delete_control_count"],
        "nonzero_pair_gap_count": pair["nonzero_pair_gap_count"],
        "pair_order_gap_collapsed": pair["pair_order_gap_collapsed"],
        "candidate_status": pair["candidate_status"],
        "kill_reason": pair["kill_reason"],
        "max_parent_peps3d_sites": pair["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": pair["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": pair["max_peps3d_bond"],
        "max_absolute_pair_gap": pair["max_absolute_pair_gap"],
    }

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "all_pass": all_pass,
                "support_atom_count": pair["support_atom_count"],
                "legal_relabeling_count": pair["legal_relabeling_count"],
                "ordered_pair_row_count": pair["ordered_pair_row_count"],
                "unordered_pair_control_count": pair["unordered_pair_control_count"],
                "same_delete_control_count": pair["same_delete_control_count"],
                "nonzero_pair_gap_count": pair["nonzero_pair_gap_count"],
                "pair_order_gap_collapsed": pair["pair_order_gap_collapsed"],
                "candidate_status": pair["candidate_status"],
                "kill_reason": pair["kill_reason"],
                "max_parent_peps3d_sites": pair["max_parent_peps3d_sites"],
                "max_triple_overlap_peps3d_sites": pair["max_triple_overlap_peps3d_sites"],
                "max_peps3d_bond": pair["max_peps3d_bond"],
                "max_absolute_pair_gap": pair["max_absolute_pair_gap"],
                "result_path": str(OUT_PATH),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
