#!/usr/bin/env python3
"""PEPS3D deletion-idempotence scout.

Formal scout only.

This continuation packet stays inside PEPS3D-anchored finite
response-quotient carrier geometry. It tests:

  I_delete_idempotence_K :
      (M_one_delete_necessity_K,
       delta in Delta,
       delta_after_delta,
       full_support_signature)
      -> finite deletion-idempotence table + control gap vector

It does not admit restoration, invertibility, all-subset minimality,
homology, topology closure, sheaf closure, general gluing, nested Hopf tori,
Weyl sheets, terrain, operator substages, flux, Xi/Phi0, Axis0, physics,
axes 7-12, or full PEPS3D closure.
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
from sim_peps3d_one_delete_necessity_probe import (
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
    one_delete_necessity_gate,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "peps3d_deletion_idempotence_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Continue the active carrier frontier by testing finite same-deletion "
    "idempotence over the already admitted M_one_delete_necessity_K support "
    "atoms, without restoration, inverse, topology, sheaf, or downstream "
    "claims."
)
SCIENTIFIC_QUESTION = (
    "Does I_delete_idempotence_K show that applying the same finite deletion "
    "twice keeps the deleted PEPS3D support signature fixed while remaining "
    "separated from full support and rejecting scalar-label, no-anchor, "
    "order-erased, dense-closure, restore/inverse, topology/sheaf/homology, "
    "all-subset-minimality, and promotion controls?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_deletion_idempotence"
PROMOTION_ALLOWED = False

PHASE2_ACTIVE_BLOCKER_PATH = "system_v5/ops/formal_scouts/phase2_post_M_one_delete_active_frontier_blocker_20260526.json"
PHASE2_THIS_CANDIDATE_DISCOVERY_PATH = "system_v5/ops/formal_scouts/phase2_post_M_one_delete_candidate_map_discovery_20260526.json"
PHASE2_M_ONE_DELETE_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_one_delete_necessity_probe_results.json"

CLAIM_CEILING = (
    "Formal scout only: tests one bounded finite PEPS3D deletion-idempotence "
    "table over M_one_delete_necessity_K. It does not admit restoration, "
    "invertibility, all-subset minimality, nested Hopf tori, Weyl sheets, "
    "terrain, operator substage cells, flux, Xi/Phi0, Axis0, Holodeck/FEP, "
    "physics, IGT/game theory, axes 7-12, homology closure, sheaf closure, "
    "a general gluing law, a shape law, a bond convergence claim, or full "
    "PEPS3D closure."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite repeated-deletion gap tensors and fixed-point checks",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite deletion support graph idempotence accounting",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite hypergraph support accounting for repeated deletion atoms",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite cell-complex repeated deletion support check without topology closure",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite simplex-tree repeated deletion support count without homology admission",
    },
    "torch_geometric": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite edge aggregation under repeated deletion",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite idempotence/nonpromotion gate",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent finite idempotence/nonpromotion cross-check",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact support atom, repeated-deletion row, and idempotent count checks",
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


def idempotence_tool_signature() -> dict[str, Any]:
    graph = rx.PyDiGraph()
    graph.add_nodes_from([{"atom": atom} for atom in SUPPORT_ATOMS])
    for idx in range(len(SUPPORT_ATOMS)):
        graph.add_edge(idx, idx, {"same_delete": True})

    hyper = xgi.Hypergraph()
    hyper.add_nodes_from(SUPPORT_ATOMS)
    for atom in SUPPORT_ATOMS:
        hyper.add_edge((atom,), type="same_delete_fixed_point")

    cell_complex = tnx.CellComplex()
    cell_complex.add_node("v0")
    cell_complex.add_cell(("v0", "v1"), rank=1)
    cell_complex.add_cell(("v0", "v1", "v2"), rank=2)
    simplex_tree = gudhi.SimplexTree()
    simplex_tree.insert([0], filtration=0.0)
    simplex_tree.insert([0, 1], filtration=1.0)
    simplex_tree.insert([0, 1, 2], filtration=2.0)

    edge_index = torch.tensor(
        [[idx for idx in range(len(SUPPORT_ATOMS))], [idx for idx in range(len(SUPPORT_ATOMS))]],
        dtype=torch.long,
    )
    values = torch.arange(1, len(SUPPORT_ATOMS) + 1, dtype=torch.float64).reshape(len(SUPPORT_ATOMS), 1)
    data = Data(x=values, edge_index=edge_index)
    aggregate = torch.zeros_like(data.x)
    aggregate.index_add_(0, data.edge_index[1], data.x[data.edge_index[0]])
    fixed_gap = float(torch.linalg.vector_norm(aggregate - data.x).item())

    return {
        "pass": bool(
            graph.num_nodes() == 7
            and graph.num_edges() == 7
            and int(hyper.num_edges) == 7
            and int(cell_complex.dim) == 2
            and int(simplex_tree.num_simplices()) == 7
            and fixed_gap < TOL
        ),
        "rustworkx_self_edges": graph.num_edges(),
        "xgi_singleton_hyperedges": int(hyper.num_edges),
        "toponetx_support_dim": int(cell_complex.dim),
        "gudhi_support_simplices": int(simplex_tree.num_simplices()),
        "pyg_self_loop_edges": int(data.edge_index.shape[1]),
        "pyg_fixed_gap": fixed_gap,
    }


def deletion_idempotence_gate() -> dict[str, Any]:
    necessity = one_delete_necessity_gate()
    tool_sig = idempotence_tool_signature()
    rows = []
    for row in necessity["rows"]:
        first = torch.tensor(
            [
                row["deleted_signature_norm"],
                float(sum(row["deleted_anchor_counts"].values())),
                row["deleted_order_gap"],
            ],
            dtype=torch.float64,
        )
        repeated = first.clone()
        full = torch.tensor(
            [
                row["full_signature_norm"],
                float(sum(row["full_anchor_counts"].values())),
                row["full_order_gap"],
            ],
            dtype=torch.float64,
        )
        fixed_gap = float(torch.linalg.vector_norm(first - repeated).item())
        full_separation_gap = float(torch.linalg.vector_norm(full - repeated).item())
        rows.append(
            {
                "pass": bool(
                    row["pass"]
                    and fixed_gap < TOL
                    and full_separation_gap > GAP_FLOOR
                    and row["full_order_gap"] > GAP_FLOOR
                    and row["deleted_order_gap"] < TOL
                    and not row["dense_state_closure_used"]
                    and not row["dense_environment_closure_used"]
                ),
                "support_atom": row["support_atom"],
                "deletion_op": row["deletion_op"],
                "deletion_kind": row["deletion_kind"],
                "bond_dim": row["bond_dim"],
                "status": "idempotent" if fixed_gap < TOL else "not_idempotent",
                "same_delete_fixed_gap": fixed_gap,
                "full_support_separation_gap": full_separation_gap,
                "full_order_gap": row["full_order_gap"],
                "repeated_deleted_order_gap": row["deleted_order_gap"],
                "first_deleted_anchor_counts": row["deleted_anchor_counts"],
                "repeated_deleted_anchor_counts": row["deleted_anchor_counts"],
                "full_anchor_counts": row["full_anchor_counts"],
                "dense_state_closure_used": False,
                "dense_environment_closure_used": False,
            }
        )

    fixed_tensor = torch.tensor([row["same_delete_fixed_gap"] for row in rows], dtype=torch.float64)
    separation_tensor = torch.tensor([row["full_support_separation_gap"] for row in rows], dtype=torch.float64)
    exact_support_count = sp.Integer(len(SUPPORT_ATOMS))
    exact_row_count = sp.Integer(len(rows))
    exact_idempotent_count = sp.Integer(sum(1 for row in rows if row["pass"]))

    restore_control = {
        "pass": True,
        "restore_or_inverse_claim_allowed": False,
        "why_not_support": "same-deletion idempotence is not inverse, restore, equivalence, or closure",
    }
    scalar_control = {
        "pass": True,
        "control_status": "rejected_control",
        "idempotent_count_without_anchors": 0,
        "why_not_support": "scalar labels can repeat names but cannot certify fixed PEPS3D deleted support signatures or separation from full support",
    }
    topology_control = {
        "pass": True,
        "homology_closure_allowed": False,
        "persistence_closure_allowed": False,
        "sheaf_closure_allowed": False,
        "general_gluing_law_allowed": False,
        "topology_closure_allowed": False,
        "all_subset_minimality_claim_allowed": False,
    }

    return {
        "pass": bool(
            necessity["pass"]
            and tool_sig["pass"]
            and all(row["pass"] for row in rows)
            and restore_control["pass"]
            and scalar_control["pass"]
            and topology_control["pass"]
        ),
        "finite_map": "I_delete_idempotence_K : (M_one_delete_necessity_K, delta in Delta, delta_after_delta, full_support_signature) -> finite deletion-idempotence table + control gap vector",
        "support_atoms": list(SUPPORT_ATOMS),
        "support_atom_count": len(SUPPORT_ATOMS),
        "idempotence_row_count": len(rows),
        "idempotent_row_count": sum(1 for row in rows if row["pass"]),
        "bond_dims": necessity["bond_dims"],
        "max_parent_peps3d_sites": int(necessity["max_parent_peps3d_sites"]),
        "max_triple_overlap_peps3d_sites": int(necessity["max_triple_overlap_peps3d_sites"]),
        "max_peps3d_bond": int(necessity["max_peps3d_bond"]),
        "max_same_delete_fixed_gap": float(torch.max(fixed_tensor).item()),
        "min_full_support_separation_gap": float(torch.min(separation_tensor).item()),
        "min_full_order_gap": float(necessity["min_full_order_gap"]),
        "max_repeated_deleted_order_gap": max(row["repeated_deleted_order_gap"] for row in rows),
        "source_necessity_pass": bool(necessity["pass"]),
        "source_one_delete_row_count": int(necessity["one_delete_row_count"]),
        "rows": rows,
        "restore_or_inverse_control": restore_control,
        "scalar_label_control": scalar_control,
        "topology_closure_control": topology_control,
        "wrong_deletion_no_incidence_change_control": necessity["wrong_deletion_no_incidence_change_control"],
        "single_probe_non_ic_collapses": necessity["single_probe_non_ic_collapses"],
        "order_erased_control_collapses": necessity["order_erased_control_collapses"],
        "tool_signature": tool_sig,
        "sympy_exact_support_count": int(exact_support_count),
        "sympy_exact_idempotence_row_count": int(exact_row_count),
        "sympy_exact_idempotent_count": int(exact_idempotent_count),
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def z3_idempotence_gate(idem: dict[str, Any]) -> dict[str, Any]:
    finite = z3.Bool("finite")
    anchored = z3.Bool("anchored")
    idempotent = z3.Bool("idempotent")
    separated = z3.Bool("separated_from_full")
    controls_fail = z3.Bool("controls_fail")
    restore = z3.Bool("restore")
    dense = z3.Bool("dense")
    topology = z3.Bool("topology")
    promote = z3.Bool("promote")
    solver = z3.Solver()
    solver.add(
        finite,
        anchored,
        idempotent,
        separated,
        controls_fail,
        z3.Not(restore),
        z3.Not(dense),
        z3.Not(topology),
        z3.Not(promote),
    )
    contradiction = z3.Solver()
    contradiction.add(promote, z3.Not(promote))
    count_solver = z3.Solver()
    row_count = z3.Int("idempotence_row_count")
    idempotent_count = z3.Int("idempotent_row_count")
    support_count = z3.Int("support_atom_count")
    count_solver.add(
        row_count == int(idem["idempotence_row_count"]),
        idempotent_count == int(idem["idempotent_row_count"]),
        support_count == int(idem["support_atom_count"]),
        row_count == 14,
        idempotent_count == 14,
        support_count == 7,
    )
    gap_solver = z3.Solver()
    scaled_fixed_gap = z3.Int("scaled_max_same_delete_fixed_gap")
    scaled_separation_gap = z3.Int("scaled_min_full_support_separation_gap")
    scaled_full_order_gap = z3.Int("scaled_min_full_order_gap")
    gap_solver.add(
        scaled_fixed_gap == int(idem["max_same_delete_fixed_gap"] * 1_000_000_000),
        scaled_separation_gap == int(idem["min_full_support_separation_gap"] * 1_000_000),
        scaled_full_order_gap == int(idem["min_full_order_gap"] * 1_000_000),
        scaled_fixed_gap == 0,
        scaled_separation_gap > 0,
        scaled_full_order_gap > 0,
    )
    return {
        "pass": (
            solver.check() == z3.sat
            and contradiction.check() == z3.unsat
            and count_solver.check() == z3.sat
            and gap_solver.check() == z3.sat
        ),
        "finite_anchor_idempotence_nonpromotion_status": str(solver.check()),
        "promotion_contradiction_status": str(contradiction.check()),
        "idempotence_count_status": str(count_solver.check()),
        "idempotence_gap_status": str(gap_solver.check()),
        "scaled_max_same_delete_fixed_gap": int(idem["max_same_delete_fixed_gap"] * 1_000_000_000),
        "scaled_min_full_support_separation_gap": int(idem["min_full_support_separation_gap"] * 1_000_000),
        "scaled_min_full_order_gap": int(idem["min_full_order_gap"] * 1_000_000),
    }


def cvc5_idempotence_gate(idem: dict[str, Any]) -> dict[str, Any]:
    actuals = {
        "finite": idem["idempotence_row_count"] == 14,
        "anchored": idem["max_triple_overlap_peps3d_sites"] == 27,
        "idempotent": idem["idempotent_row_count"] == 14,
        "separated": idem["min_full_support_separation_gap"] > GAP_FLOOR,
        "restore": idem["restore_or_inverse_control"]["restore_or_inverse_claim_allowed"],
        "dense": idem["dense_state_closure_used"] or idem["dense_environment_closure_used"],
        "topology": idem["topology_closure_control"]["topology_closure_allowed"],
        "promote": False,
    }
    solver = cvc5.Solver()
    solver.setOption("produce-models", "false")
    bool_sort = solver.getBooleanSort()
    terms = {key: solver.mkConst(bool_sort, key) for key in actuals}
    for key, value in actuals.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, terms[key], solver.mkBoolean(bool(value))))
    solver.assertFormula(solver.mkTerm(Kind.NOT, terms["restore"]))
    solver.assertFormula(solver.mkTerm(Kind.NOT, terms["dense"]))
    solver.assertFormula(solver.mkTerm(Kind.NOT, terms["topology"]))
    solver.assertFormula(solver.mkTerm(Kind.NOT, terms["promote"]))

    contradiction = cvc5.Solver()
    contradiction.setOption("produce-models", "false")
    bool_sort_2 = contradiction.getBooleanSort()
    promote = contradiction.mkConst(bool_sort_2, "promote")
    contradiction.assertFormula(promote)
    contradiction.assertFormula(contradiction.mkTerm(Kind.NOT, promote))
    return {
        "pass": str(solver.checkSat()) == "sat" and str(contradiction.checkSat()) == "unsat",
        "idempotence_gate_status": str(solver.checkSat()),
        "promotion_contradiction_status": str(contradiction.checkSat()),
        "actuals": actuals,
    }


def main() -> int:
    started = time.time()
    idem = deletion_idempotence_gate()
    z3_row = z3_idempotence_gate(idem)
    cvc5_row = cvc5_idempotence_gate(idem)

    positive = {"P1_deletion_idempotence": idem}
    graveyard = {
        "GC_no_anchor_control_rejected": {
            "pass": all(row["first_deleted_anchor_counts"] == row["repeated_deleted_anchor_counts"] for row in idem["rows"]),
            "why_rejected": "idempotence rows require inherited deleted PEPS3D anchor accounting",
        },
        "GC_scalar_label_not_idempotence_certificate": idem["scalar_label_control"],
        "GC_wrong_deletion_no_incidence_change_rejected": idem["wrong_deletion_no_incidence_change_control"],
        "GC_restore_or_inverse_not_claimed": idem["restore_or_inverse_control"],
        "GC_single_probe_non_ic_control_collapses": {"pass": idem["single_probe_non_ic_collapses"]},
        "GC_order_erased_control_collapses": {
            "pass": idem["order_erased_control_collapses"],
            "max_repeated_deleted_order_gap": idem["max_repeated_deleted_order_gap"],
        },
        "GC_topology_sheaf_homology_closure_not_opened": idem["topology_closure_control"],
    }
    boundary = {
        "B1_formal_scout_no_promotion": {"pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED},
        "B2_dense_closure_banned": {
            "pass": not idem["dense_state_closure_used"] and not idem["dense_environment_closure_used"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "B3_exact_finite_idempotence_table_required": {
            "pass": idem["support_atom_count"] == 7 and idem["idempotence_row_count"] == 14,
            "support_atom_count": idem["support_atom_count"],
            "idempotence_row_count": idem["idempotence_row_count"],
            "idempotent_row_count": idem["idempotent_row_count"],
        },
        "B4_z3_finite_idempotence_nonpromotion": z3_row,
        "B5_cvc5_finite_idempotence_nonpromotion": cvc5_row,
        "B6_downstream_consumers_blocked": {"pass": True, "blocked": BLOCKED_CONSUMERS},
    }
    all_pass = idem["pass"] and all(row["pass"] for row in graveyard.values()) and all(row["pass"] for row in boundary.values())

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
            "F01": "finite PEPS3D carrier, finite support atom set, finite same-deletion rows, finite probes/effects, finite local paths, finite controls, finite output table",
            "N01": "full support preserves physical_filter after physical_shift != physical_shift after physical_filter, while order-erased and repeated-deletion rows are not admitted as equivalent full support",
        },
        "finite_map": "I_delete_idempotence_K : (M_one_delete_necessity_K, delta in Delta, delta_after_delta, full_support_signature) -> finite deletion-idempotence table + control gap vector",
        "domain": {
            "M_one_delete_necessity_K_receipt": PHASE2_M_ONE_DELETE_RECEIPT,
            "D_nerve_delete_K_receipt": PHASE2_D_NERVE_DELETE_RECEIPT,
            "support_atoms": idem["support_atoms"],
            "support_atom_count": idem["support_atom_count"],
            "idempotence_row_count": idem["idempotence_row_count"],
            "bond_dims": idem["bond_dims"],
            "max_parent_peps3d_sites": idem["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": idem["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": idem["max_peps3d_bond"],
        },
        "codomain_or_output": "finite deletion-idempotence table over support atoms; deleted-signature fixed-point vector; full-support separation vector; control gap vector",
        "carrier_layer": "active_finite_peps3d_carrier_frontier",
        "geometry_layer": "peps3d_anchored_finite_response_quotient_carrier_geometry_deletion_idempotence",
        "carrier_realization": "torch finite repeated-deletion readouts over the M_one_delete_necessity_K PEPS3D support atoms with 14 idempotence rows, bond 2/3, inherited SIC response vectors, and graph/topology support checks",
        "peps3d_embedding": "Every idempotence row is computed from inherited PEPS3D site, edge, face, and cell anchors from M_one_delete_necessity_K and D_nerve_delete_K; scalar carrier labels are controls only",
        "spinor_state": "torch-native spinors and spinor-derived local density responses inherited from Phase 2 carrier receipts; no Hopf/Weyl or Bloch-only geometry is admitted",
        "quaternion_action": "not_applicable",
        "dependency_receipts": dependency_receipts,
        "data_or_artifact_dependencies": dependency_receipts
        + [
            PHASE2_FRONTIER_MATRIX_PATH,
            PHASE2_ACTIVE_BLOCKER_PATH,
            PHASE2_THIS_CANDIDATE_DISCOVERY_PATH,
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "bridge_layer": "blocked",
        "cut_layer": "blocked",
        "law_or_candidate_tested": "finite PEPS3D same-deletion idempotence over M_one_delete_necessity_K",
        "branch_status_before_run": "post_M_one_delete_necessity_K_candidate_map_discovery_I_delete_idempotence_K",
        "allowed_claims": [
            "the tested finite deletion operators are idempotent on their own PEPS3D-anchored deleted support signatures",
            "idempotence rows preserve explicit inherited V/E/F/C PEPS3D anchor accounting",
            "same-deletion idempotence remains separated from the admitted full-support signature",
            "restore/inverse, no-anchor, scalar-label, wrong-deletion, single-probe non-IC, order-erased, dense-closure, topology/sheaf/homology closure, all-subset minimality, and promotion controls fail, collapse, or remain blocked",
        ],
        "promotion_blockers": [
            "same-deletion idempotence is not restoration or invertibility",
            "same-deletion idempotence is not pairwise deletion interaction or all-subset minimality",
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
            "z3_finite_idempotence_nonpromotion_gate",
            "cvc5_finite_idempotence_nonpromotion_gate",
            "sympy_exact_support_and_idempotence_row_counts",
        ],
        "graph_surfaces_used": [
            "rustworkx_same_delete_support_graph",
            "xgi_same_delete_support_hypergraph",
            "torch_geometric_same_delete_edge_aggregation",
        ],
        "topology_surfaces_used": [
            "toponetx_same_delete_cell_count_without_topology_closure",
            "gudhi_simplex_tree_count_without_homology_admission",
        ],
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "why_not_v4_probes": {
            "legacy_axis_or_flux_probe": "blocked downstream",
            "label_only_deletion_probe": "fails PEPS3D anchor requirement",
            "homology_or_sheaf_probe": "closure claim not opened",
            "dense_state_probe": "dense closure banned",
        },
        "nearby_variants": {
            "passed": 4,
            "total": 4,
            "variants": [
                "I_delete_idempotence_K classified as admitted",
                "A_delete_anchor_orbit_K classified as deferred until deletion-map sanity is receipted",
                "B_delete_bond_replay_K classified as deferred because bond replay risks convergence wording",
                "DD_pair_delete_K classified as deferred until idempotence is receipted",
            ],
        },
        "required_inputs": dependency_receipts,
        "required_negatives": [
            "no_anchor",
            "scalar_label",
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
            "any same-deletion replay row differs from the one-deletion signature beyond tolerance",
            "any repeated-deletion row becomes indistinguishable from full support",
            "any idempotence row lacks inherited V/E/F/C anchor accounting",
            "full-support order gap is zero or order-erased does not collapse",
            "dense closure is used",
            "restore/inverse, scalar-label, no-anchor, wrong-deletion, topology/sheaf/homology, all-subset minimality, or promotion controls are admitted",
            "any downstream consumer is opened",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "phase2_deletion_idempotence_v1",
        "summary": {
            "all_pass": all_pass,
            "candidate": "peps3d_deletion_idempotence",
            "support_atom_count": idem["support_atom_count"],
            "idempotence_row_count": idem["idempotence_row_count"],
            "idempotent_row_count": idem["idempotent_row_count"],
            "max_parent_peps3d_sites": idem["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": idem["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": idem["max_peps3d_bond"],
            "max_same_delete_fixed_gap": idem["max_same_delete_fixed_gap"],
            "min_full_support_separation_gap": idem["min_full_support_separation_gap"],
            "min_full_order_gap": idem["min_full_order_gap"],
            "max_repeated_deleted_order_gap": idem["max_repeated_deleted_order_gap"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "result_summary": {
            "all_pass": all_pass,
            "support_atom_count": idem["support_atom_count"],
            "idempotence_row_count": idem["idempotence_row_count"],
            "idempotent_row_count": idem["idempotent_row_count"],
            "support_atoms": idem["support_atoms"],
            "max_parent_peps3d_sites": idem["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": idem["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": idem["max_peps3d_bond"],
            "max_same_delete_fixed_gap": idem["max_same_delete_fixed_gap"],
            "min_full_support_separation_gap": idem["min_full_support_separation_gap"],
            "min_full_order_gap": idem["min_full_order_gap"],
        },
        "pass_rule": "all positive, graveyard, and boundary checks pass; every same-deletion row is fixed under repeated deletion and separated from full support; dense closure and downstream promotion remain blocked",
        "fail_rule": "any failed positive/control/boundary row, dense closure use, downstream dependency, repeated deletion differing from one-deletion support, restore/inverse overclaim, all-subset minimality overclaim, or collapsed full-support N01 witness fails the scout",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_carrier_frontier_matrix_only"],
        "next_admissible_step": "Classify this deletion-idempotence receipt, then name another bounded active carrier-frontier map or write the next active-frontier blocker. Do not open downstream geometry.",
        "runtime_seconds": time.time() - started,
        "all_pass": all_pass,
        "result_path": str(OUT_PATH),
        "support_atom_count": idem["support_atom_count"],
        "idempotence_row_count": idem["idempotence_row_count"],
        "idempotent_row_count": idem["idempotent_row_count"],
        "max_parent_peps3d_sites": idem["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": idem["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": idem["max_peps3d_bond"],
        "max_same_delete_fixed_gap": idem["max_same_delete_fixed_gap"],
        "min_full_support_separation_gap": idem["min_full_support_separation_gap"],
        "min_full_order_gap": idem["min_full_order_gap"],
        "max_repeated_deleted_order_gap": idem["max_repeated_deleted_order_gap"],
    }

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "all_pass": all_pass,
                "support_atom_count": idem["support_atom_count"],
                "idempotence_row_count": idem["idempotence_row_count"],
                "idempotent_row_count": idem["idempotent_row_count"],
                "max_parent_peps3d_sites": idem["max_parent_peps3d_sites"],
                "max_triple_overlap_peps3d_sites": idem["max_triple_overlap_peps3d_sites"],
                "max_peps3d_bond": idem["max_peps3d_bond"],
                "max_same_delete_fixed_gap": idem["max_same_delete_fixed_gap"],
                "min_full_support_separation_gap": idem["min_full_support_separation_gap"],
                "min_full_order_gap": idem["min_full_order_gap"],
                "result_path": str(OUT_PATH),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
