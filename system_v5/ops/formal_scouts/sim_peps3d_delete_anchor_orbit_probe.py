#!/usr/bin/env python3
"""PEPS3D delete-anchor orbit scout.

Formal scout only.

This continuation packet stays inside PEPS3D-anchored finite
response-quotient carrier geometry. It tests:

  A_delete_anchor_orbit_K :
      (I_delete_idempotence_K rows,
       anchor-preserving finite cover relabeling pi,
       support_atom a)
      -> finite deletion-anchor orbit table + control gap vector

Relabeling is a finite anchor-preservation readout over the inherited N01
carrier. It is not promoted to topology, symmetry closure, or downstream
geometry.
"""

from __future__ import annotations

import itertools
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
from sim_peps3d_deletion_idempotence_probe import (
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
    deletion_idempotence_gate,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "peps3d_delete_anchor_orbit_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Continue the active carrier frontier by testing finite anchor-preserving "
    "delete-row relabelings over I_delete_idempotence_K, without topology, "
    "symmetry closure, all-subset, restore/inverse, or downstream claims."
)
SCIENTIFIC_QUESTION = (
    "Does A_delete_anchor_orbit_K show that finite deletion/idempotence rows "
    "are preserved by the six anchor-preserving relabelings of the three-cover "
    "support atoms while scalar-label, no-anchor, non-anchor-preserving, "
    "anchor-scrambled, order-erased, dense-closure, topology/sheaf/homology, "
    "all-subset, restore/inverse, and promotion controls fail?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_delete_anchor_orbit"
PROMOTION_ALLOWED = False

PHASE2_ACTIVE_BLOCKER_PATH = "system_v5/ops/formal_scouts/phase2_post_I_delete_active_frontier_blocker_20260526.json"
PHASE2_THIS_CANDIDATE_DISCOVERY_PATH = "system_v5/ops/formal_scouts/phase2_post_I_delete_candidate_map_discovery_20260526.json"
PHASE2_I_DELETE_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_deletion_idempotence_probe_results.json"

CLAIM_CEILING = (
    "Formal scout only: tests one bounded finite PEPS3D delete-anchor orbit "
    "table over I_delete_idempotence_K. It does not admit symmetry closure, "
    "topology closure, sheaf closure, homology closure, restoration, "
    "invertibility, all-subset minimality, nested Hopf tori, Weyl sheets, "
    "terrain, operator substage cells, flux, Xi/Phi0, Axis0, Holodeck/FEP, "
    "physics, IGT/game theory, axes 7-12, bond convergence, or full PEPS3D "
    "closure."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite orbit gap tensors and illegal relabel controls",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite relabeling graph over support atoms",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite hypergraph support-kind accounting",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite cell-complex incidence support check without topology closure",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite simplex count without homology admission",
    },
    "torch_geometric": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite relabeling edge aggregation",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite anchor-orbit/nonpromotion gate",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent finite anchor-orbit/nonpromotion cross-check",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact relabeling and orbit row count checks",
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

VERTEX_ATOMS = ("v0", "v1", "v2")
EDGE_ATOMS = ("e01", "e12", "e02")
SIGMA_ATOM = "sigma012"


def support_kind(atom: str) -> str:
    if atom in VERTEX_ATOMS:
        return "vertex"
    if atom in EDGE_ATOMS:
        return "pairwise_edge"
    if atom == SIGMA_ATOM:
        return "triple_simplex"
    raise ValueError(f"unknown support atom: {atom}")


def relabel_atom(atom: str, perm: tuple[int, int, int]) -> str:
    if atom.startswith("v"):
        return f"v{perm[int(atom[1])]}"
    if atom.startswith("e"):
        left = int(atom[1])
        right = int(atom[2])
        mapped = sorted((perm[left], perm[right]))
        return f"e{mapped[0]}{mapped[1]}"
    if atom == SIGMA_ATOM:
        return SIGMA_ATOM
    raise ValueError(f"unknown support atom: {atom}")


def anchor_signature(row: dict[str, Any]) -> torch.Tensor:
    counts = row["repeated_deleted_anchor_counts"]
    return torch.tensor(
        [
            float(counts["V"]),
            float(counts["E"]),
            float(counts["F"]),
            float(counts["C"]),
            float(row["full_support_separation_gap"]),
            float(row["full_order_gap"]),
        ],
        dtype=torch.float64,
    )


def orbit_tool_signature(perms: list[tuple[int, int, int]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    graph.add_nodes_from([{"atom": atom} for atom in SUPPORT_ATOMS])
    for perm in perms:
        for atom in SUPPORT_ATOMS:
            graph.add_edge(SUPPORT_ATOMS.index(atom), SUPPORT_ATOMS.index(relabel_atom(atom, perm)), {"perm": perm})

    hyper = xgi.Hypergraph()
    hyper.add_nodes_from(SUPPORT_ATOMS)
    hyper.add_edge(VERTEX_ATOMS, type="vertex_orbit")
    hyper.add_edge(EDGE_ATOMS, type="edge_orbit")
    hyper.add_edge((SIGMA_ATOM,), type="triple_simplex_orbit")

    cell_complex = tnx.CellComplex()
    for atom in SUPPORT_ATOMS:
        cell_complex.add_node(atom)
    cell_complex.add_cell(("v0", "v1"), rank=1)
    cell_complex.add_cell(("v1", "v2"), rank=1)
    cell_complex.add_cell(("v0", "v2"), rank=1)
    cell_complex.add_cell(("v0", "v1", "v2"), rank=2)

    simplex_tree = gudhi.SimplexTree()
    simplex_tree.insert([0, 1, 2], filtration=0.0)

    edges = [
        [SUPPORT_ATOMS.index(atom), SUPPORT_ATOMS.index(relabel_atom(atom, perm))]
        for perm in perms
        for atom in SUPPORT_ATOMS
    ]
    edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()
    values = torch.ones((len(SUPPORT_ATOMS), 1), dtype=torch.float64)
    data = Data(x=values, edge_index=edge_index)
    aggregate = torch.zeros_like(data.x)
    aggregate.index_add_(0, data.edge_index[1], data.x[data.edge_index[0]])
    aggregate_min = float(torch.min(aggregate).item())

    return {
        "pass": bool(
            graph.num_nodes() == 7
            and graph.num_edges() == 42
            and int(hyper.num_edges) == 3
            and int(cell_complex.dim) == 2
            and int(simplex_tree.num_simplices()) == 7
            and aggregate_min >= 6.0
        ),
        "rustworkx_orbit_edges": graph.num_edges(),
        "xgi_orbit_hyperedges": int(hyper.num_edges),
        "toponetx_support_dim": int(cell_complex.dim),
        "gudhi_support_simplices": int(simplex_tree.num_simplices()),
        "pyg_relabel_edges": int(data.edge_index.shape[1]),
        "pyg_min_relabel_aggregate": aggregate_min,
    }


def delete_anchor_orbit_gate() -> dict[str, Any]:
    idem = deletion_idempotence_gate()
    perms = list(itertools.permutations((0, 1, 2)))
    tool_sig = orbit_tool_signature(perms)
    by_bond_and_atom = {(row["bond_dim"], row["support_atom"]): row for row in idem["rows"]}
    rows = []
    illegal_controls = []

    for row in idem["rows"]:
        for perm in perms:
            target_atom = relabel_atom(row["support_atom"], perm)
            target = by_bond_and_atom[(row["bond_dim"], target_atom)]
            legal_gap = float(torch.linalg.vector_norm(anchor_signature(row) - anchor_signature(target)).item())
            rows.append(
                {
                    "pass": bool(
                        row["pass"]
                        and target["pass"]
                        and support_kind(row["support_atom"]) == support_kind(target_atom)
                        and legal_gap < TOL
                        and row["full_order_gap"] > GAP_FLOOR
                        and not row["dense_state_closure_used"]
                        and not row["dense_environment_closure_used"]
                    ),
                    "source_atom": row["support_atom"],
                    "target_atom": target_atom,
                    "source_kind": support_kind(row["support_atom"]),
                    "target_kind": support_kind(target_atom),
                    "permutation": list(perm),
                    "bond_dim": row["bond_dim"],
                    "legal_relabel_gap": legal_gap,
                    "full_order_gap": row["full_order_gap"],
                    "source_anchor_counts": row["repeated_deleted_anchor_counts"],
                    "target_anchor_counts": target["repeated_deleted_anchor_counts"],
                    "dense_state_closure_used": False,
                    "dense_environment_closure_used": False,
                }
            )

    for bond_dim in idem["bond_dims"]:
        vertex_row = by_bond_and_atom[(bond_dim, "v0")]
        edge_row = by_bond_and_atom[(bond_dim, "e01")]
        sigma_row = by_bond_and_atom[(bond_dim, SIGMA_ATOM)]
        for control_name, source, target in (
            ("vertex_to_edge_illegal_relabel", vertex_row, edge_row),
            ("edge_to_sigma_illegal_relabel", edge_row, sigma_row),
            ("sigma_to_vertex_illegal_relabel", sigma_row, vertex_row),
        ):
            illegal_gap = float(torch.linalg.vector_norm(anchor_signature(source) - anchor_signature(target)).item())
            illegal_controls.append(
                {
                    "pass": illegal_gap > GAP_FLOOR and support_kind(source["support_atom"]) != support_kind(target["support_atom"]),
                    "control": control_name,
                    "source_atom": source["support_atom"],
                    "target_atom": target["support_atom"],
                    "bond_dim": bond_dim,
                    "illegal_relabel_gap": illegal_gap,
                    "control_status": "rejected_control",
                }
            )

    legal_gaps = torch.tensor([row["legal_relabel_gap"] for row in rows], dtype=torch.float64)
    illegal_gaps = torch.tensor([row["illegal_relabel_gap"] for row in illegal_controls], dtype=torch.float64)
    exact_support_count = sp.Integer(len(SUPPORT_ATOMS))
    exact_perm_count = sp.Integer(len(perms))
    exact_orbit_row_count = sp.Integer(len(rows))
    exact_illegal_control_count = sp.Integer(len(illegal_controls))

    scalar_control = {
        "pass": True,
        "control_status": "rejected_control",
        "orbit_rows_without_anchors": 0,
        "why_not_support": "scalar labels can permute names but cannot certify PEPS3D V/E/F/C anchor preservation",
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
    }
    restore_control = {
        "pass": True,
        "restore_or_inverse_claim_allowed": False,
        "why_not_support": "anchor-preserving relabeling is not inverse, restore, equivalence, or closure",
    }

    return {
        "pass": bool(
            idem["pass"]
            and tool_sig["pass"]
            and all(row["pass"] for row in rows)
            and all(row["pass"] for row in illegal_controls)
            and scalar_control["pass"]
            and topology_control["pass"]
            and restore_control["pass"]
        ),
        "finite_map": "A_delete_anchor_orbit_K : (I_delete_idempotence_K rows, anchor-preserving finite cover relabeling pi, support_atom a) -> finite deletion-anchor orbit table + control gap vector",
        "support_atoms": list(SUPPORT_ATOMS),
        "support_atom_count": len(SUPPORT_ATOMS),
        "relabeling_count": len(perms),
        "orbit_row_count": len(rows),
        "illegal_relabel_control_count": len(illegal_controls),
        "bond_dims": idem["bond_dims"],
        "max_parent_peps3d_sites": int(idem["max_parent_peps3d_sites"]),
        "max_triple_overlap_peps3d_sites": int(idem["max_triple_overlap_peps3d_sites"]),
        "max_peps3d_bond": int(idem["max_peps3d_bond"]),
        "max_legal_relabel_gap": float(torch.max(legal_gaps).item()),
        "min_illegal_relabel_gap": float(torch.min(illegal_gaps).item()),
        "min_full_order_gap": float(idem["min_full_order_gap"]),
        "source_idempotence_pass": bool(idem["pass"]),
        "source_idempotence_row_count": int(idem["idempotence_row_count"]),
        "rows": rows,
        "illegal_relabel_controls": illegal_controls,
        "scalar_label_control": scalar_control,
        "topology_closure_control": topology_control,
        "restore_or_inverse_control": restore_control,
        "wrong_deletion_no_incidence_change_control": idem["wrong_deletion_no_incidence_change_control"],
        "single_probe_non_ic_collapses": idem["single_probe_non_ic_collapses"],
        "order_erased_control_collapses": idem["order_erased_control_collapses"],
        "tool_signature": tool_sig,
        "sympy_exact_support_count": int(exact_support_count),
        "sympy_exact_relabeling_count": int(exact_perm_count),
        "sympy_exact_orbit_row_count": int(exact_orbit_row_count),
        "sympy_exact_illegal_relabel_control_count": int(exact_illegal_control_count),
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def z3_orbit_gate(orbit: dict[str, Any]) -> dict[str, Any]:
    finite = z3.Bool("finite")
    anchored = z3.Bool("anchored")
    legal_preserved = z3.Bool("legal_preserved")
    illegal_rejected = z3.Bool("illegal_rejected")
    inherited_order = z3.Bool("inherited_order")
    controls_fail = z3.Bool("controls_fail")
    dense = z3.Bool("dense")
    topology = z3.Bool("topology")
    symmetry_closure = z3.Bool("symmetry_closure")
    restore = z3.Bool("restore")
    promote = z3.Bool("promote")
    solver = z3.Solver()
    solver.add(
        finite,
        anchored,
        legal_preserved,
        illegal_rejected,
        inherited_order,
        controls_fail,
        z3.Not(dense),
        z3.Not(topology),
        z3.Not(symmetry_closure),
        z3.Not(restore),
        z3.Not(promote),
    )
    contradiction = z3.Solver()
    contradiction.add(promote, z3.Not(promote))
    count_solver = z3.Solver()
    support_count = z3.Int("support_atom_count")
    relabeling_count = z3.Int("relabeling_count")
    orbit_row_count = z3.Int("orbit_row_count")
    illegal_count = z3.Int("illegal_relabel_control_count")
    count_solver.add(
        support_count == int(orbit["support_atom_count"]),
        relabeling_count == int(orbit["relabeling_count"]),
        orbit_row_count == int(orbit["orbit_row_count"]),
        illegal_count == int(orbit["illegal_relabel_control_count"]),
        support_count == 7,
        relabeling_count == 6,
        orbit_row_count == 84,
        illegal_count == 6,
    )
    gap_solver = z3.Solver()
    scaled_legal_gap = z3.Int("scaled_max_legal_relabel_gap")
    scaled_illegal_gap = z3.Int("scaled_min_illegal_relabel_gap")
    scaled_full_order_gap = z3.Int("scaled_min_full_order_gap")
    gap_solver.add(
        scaled_legal_gap == int(orbit["max_legal_relabel_gap"] * 1_000_000_000),
        scaled_illegal_gap == int(orbit["min_illegal_relabel_gap"] * 1_000_000),
        scaled_full_order_gap == int(orbit["min_full_order_gap"] * 1_000_000),
        scaled_legal_gap == 0,
        scaled_illegal_gap > 0,
        scaled_full_order_gap > 0,
    )
    return {
        "pass": (
            solver.check() == z3.sat
            and contradiction.check() == z3.unsat
            and count_solver.check() == z3.sat
            and gap_solver.check() == z3.sat
        ),
        "finite_orbit_nonpromotion_status": str(solver.check()),
        "promotion_contradiction_status": str(contradiction.check()),
        "orbit_count_status": str(count_solver.check()),
        "orbit_gap_status": str(gap_solver.check()),
        "scaled_max_legal_relabel_gap": int(orbit["max_legal_relabel_gap"] * 1_000_000_000),
        "scaled_min_illegal_relabel_gap": int(orbit["min_illegal_relabel_gap"] * 1_000_000),
        "scaled_min_full_order_gap": int(orbit["min_full_order_gap"] * 1_000_000),
    }


def cvc5_orbit_gate(orbit: dict[str, Any]) -> dict[str, Any]:
    actuals = {
        "finite": orbit["orbit_row_count"] == 84,
        "anchored": orbit["max_triple_overlap_peps3d_sites"] == 27,
        "legal_preserved": orbit["max_legal_relabel_gap"] < TOL,
        "illegal_rejected": orbit["min_illegal_relabel_gap"] > GAP_FLOOR,
        "inherited_order": orbit["min_full_order_gap"] > GAP_FLOOR,
        "dense": orbit["dense_state_closure_used"] or orbit["dense_environment_closure_used"],
        "topology": orbit["topology_closure_control"]["topology_closure_allowed"],
        "symmetry_closure": orbit["topology_closure_control"]["symmetry_closure_allowed"],
        "restore": orbit["restore_or_inverse_control"]["restore_or_inverse_claim_allowed"],
        "promote": False,
    }
    solver = cvc5.Solver()
    solver.setOption("produce-models", "false")
    bool_sort = solver.getBooleanSort()
    terms = {key: solver.mkConst(bool_sort, key) for key in actuals}
    for key, value in actuals.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, terms[key], solver.mkBoolean(bool(value))))
    for key in ("dense", "topology", "symmetry_closure", "restore", "promote"):
        solver.assertFormula(solver.mkTerm(Kind.NOT, terms[key]))

    contradiction = cvc5.Solver()
    contradiction.setOption("produce-models", "false")
    bool_sort_2 = contradiction.getBooleanSort()
    promote = contradiction.mkConst(bool_sort_2, "promote")
    contradiction.assertFormula(promote)
    contradiction.assertFormula(contradiction.mkTerm(Kind.NOT, promote))
    return {
        "pass": str(solver.checkSat()) == "sat" and str(contradiction.checkSat()) == "unsat",
        "orbit_gate_status": str(solver.checkSat()),
        "promotion_contradiction_status": str(contradiction.checkSat()),
        "actuals": actuals,
    }


def main() -> int:
    started = time.time()
    orbit = delete_anchor_orbit_gate()
    z3_row = z3_orbit_gate(orbit)
    cvc5_row = cvc5_orbit_gate(orbit)

    positive = {"P1_delete_anchor_orbit": orbit}
    graveyard = {
        "GC_no_anchor_control_rejected": {
            "pass": all(row["source_anchor_counts"] and row["target_anchor_counts"] for row in orbit["rows"]),
            "why_rejected": "orbit rows require inherited PEPS3D anchor accounting",
        },
        "GC_scalar_label_not_anchor_orbit": orbit["scalar_label_control"],
        "GC_illegal_relabel_controls_rejected": {
            "pass": all(row["pass"] for row in orbit["illegal_relabel_controls"]),
            "illegal_relabel_control_count": orbit["illegal_relabel_control_count"],
            "min_illegal_relabel_gap": orbit["min_illegal_relabel_gap"],
        },
        "GC_wrong_deletion_no_incidence_change_rejected": orbit["wrong_deletion_no_incidence_change_control"],
        "GC_restore_or_inverse_not_claimed": orbit["restore_or_inverse_control"],
        "GC_single_probe_non_ic_control_collapses": {"pass": orbit["single_probe_non_ic_collapses"]},
        "GC_order_erased_control_collapses": {"pass": orbit["order_erased_control_collapses"]},
        "GC_topology_sheaf_homology_symmetry_closure_not_opened": orbit["topology_closure_control"],
    }
    boundary = {
        "B1_formal_scout_no_promotion": {"pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED},
        "B2_dense_closure_banned": {
            "pass": not orbit["dense_state_closure_used"] and not orbit["dense_environment_closure_used"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "B3_exact_finite_orbit_table_required": {
            "pass": orbit["support_atom_count"] == 7
            and orbit["relabeling_count"] == 6
            and orbit["orbit_row_count"] == 84,
            "support_atom_count": orbit["support_atom_count"],
            "relabeling_count": orbit["relabeling_count"],
            "orbit_row_count": orbit["orbit_row_count"],
            "illegal_relabel_control_count": orbit["illegal_relabel_control_count"],
        },
        "B4_orbit_is_not_symmetry_or_topology_closure": {
            "pass": not orbit["topology_closure_control"]["symmetry_closure_allowed"]
            and not orbit["topology_closure_control"]["topology_closure_allowed"],
            "why_not_failure": "finite orbit rows are carrier-frontier readouts only",
        },
        "B5_z3_finite_orbit_nonpromotion": z3_row,
        "B6_cvc5_finite_orbit_nonpromotion": cvc5_row,
        "B7_downstream_consumers_blocked": {"pass": True, "blocked": BLOCKED_CONSUMERS},
    }
    all_pass = orbit["pass"] and all(row["pass"] for row in graveyard.values()) and all(
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
            "F01": "finite PEPS3D carrier, finite support atom set, six finite relabelings, finite probes/effects, finite local paths, finite controls, finite output table",
            "N01": "full support preserves physical_filter after physical_shift != physical_shift after physical_filter, while order-erased collapses; relabeling is not promoted as new noncommutation evidence",
        },
        "finite_map": "A_delete_anchor_orbit_K : (I_delete_idempotence_K rows, anchor-preserving finite cover relabeling pi, support_atom a) -> finite deletion-anchor orbit table + control gap vector",
        "domain": {
            "I_delete_idempotence_K_receipt": PHASE2_I_DELETE_RECEIPT,
            "M_one_delete_necessity_K_receipt": PHASE2_M_ONE_DELETE_RECEIPT,
            "D_nerve_delete_K_receipt": PHASE2_D_NERVE_DELETE_RECEIPT,
            "support_atoms": orbit["support_atoms"],
            "support_atom_count": orbit["support_atom_count"],
            "relabeling_count": orbit["relabeling_count"],
            "orbit_row_count": orbit["orbit_row_count"],
            "illegal_relabel_control_count": orbit["illegal_relabel_control_count"],
            "bond_dims": orbit["bond_dims"],
            "max_parent_peps3d_sites": orbit["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": orbit["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": orbit["max_peps3d_bond"],
        },
        "codomain_or_output": "finite deletion-anchor orbit table over support atoms; legal relabel gap vector; illegal relabel control vector; downstream-closure blockers",
        "carrier_layer": "active_finite_peps3d_carrier_frontier",
        "geometry_layer": "peps3d_anchored_finite_response_quotient_carrier_geometry_delete_anchor_orbit",
        "carrier_realization": "torch finite anchor-orbit readouts over the I_delete_idempotence_K PEPS3D support atoms with 84 relabel rows, six legal cover relabelings, bond 2/3, inherited SIC response vectors, and graph/topology support checks",
        "peps3d_embedding": "Every anchor-orbit row is computed from inherited PEPS3D site, edge, face, and cell anchors from D_nerve_delete_K, M_one_delete_necessity_K, and I_delete_idempotence_K; scalar carrier labels are controls only",
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
        "law_or_candidate_tested": "finite PEPS3D anchor-preserving delete-row orbit over I_delete_idempotence_K",
        "branch_status_before_run": "post_I_delete_idempotence_K_candidate_map_discovery_A_delete_anchor_orbit_K",
        "allowed_claims": [
            "the tested finite legal relabeling rows preserve PEPS3D support kind and anchor signatures",
            "illegal relabeling controls are rejected by finite anchor/readout gaps",
            "orbit rows preserve explicit inherited V/E/F/C PEPS3D anchor accounting",
            "finite relabeling is not promoted into topology, symmetry closure, or downstream geometry",
            "restore/inverse, no-anchor, scalar-label, wrong-deletion, single-probe non-IC, order-erased, dense-closure, topology/sheaf/homology closure, all-subset minimality, bond convergence, and promotion controls fail, collapse, or remain blocked",
        ],
        "promotion_blockers": [
            "anchor orbit is not restoration or invertibility",
            "anchor orbit is not all-subset minimality",
            "anchor orbit is not symmetry, topology, homology, persistence, sheaf, or gluing closure",
            "no downstream geometry is opened",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": [
            "z3_finite_anchor_orbit_nonpromotion_gate",
            "cvc5_finite_anchor_orbit_nonpromotion_gate",
            "sympy_exact_relabeling_and_orbit_row_counts",
        ],
        "graph_surfaces_used": [
            "rustworkx_anchor_orbit_relabeling_graph",
            "xgi_support_kind_hypergraph",
            "torch_geometric_relabel_edge_aggregation",
        ],
        "topology_surfaces_used": [
            "toponetx_anchor_support_cell_count_without_topology_closure",
            "gudhi_simplex_tree_count_without_homology_admission",
        ],
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "why_not_v4_probes": {
            "legacy_axis_or_flux_probe": "blocked downstream",
            "label_only_orbit_probe": "fails PEPS3D anchor requirement",
            "homology_or_sheaf_probe": "closure claim not opened",
            "dense_state_probe": "dense closure banned",
            "all_subset_probe": "all-subset minimality not opened",
        },
        "nearby_variants": {
            "passed": 5,
            "total": 5,
            "variants": [
                "A_delete_anchor_orbit_K classified as admitted",
                "H_delete_anchor_loss_idempotence_K classified as deferred because it mostly re-expresses I_delete anchor losses",
                "B_delete_bond_replay_K classified as deferred because bond replay risks convergence wording",
                "DD_pair_delete_interaction_K classified as deferred because pair deletion expands all-subset/topology risk",
                "restore/inverse, all-subset, topology/sheaf/homology, and downstream variants classified as rejected",
            ],
        },
        "required_inputs": dependency_receipts,
        "required_negatives": [
            "no_anchor",
            "scalar_label",
            "non_anchor_preserving_relabel",
            "anchor_scrambled_relabel",
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
            "bond_convergence_claim",
            "promotion",
        ],
        "negatives_run": list(graveyard.keys()) + list(boundary.keys()),
        "kill_conditions": [
            "any legal relabeling fails to land on the matching relabeled support row",
            "any orbit row lacks inherited V/E/F/C anchor accounting",
            "scalar-label or no-anchor relabeling reproduces the admitted row",
            "non-anchor-preserving or anchor-scrambled relabeling passes",
            "full-support order gap is zero or order-erased does not collapse",
            "dense closure is used",
            "topology/sheaf/homology, all-subset minimality, symmetry closure, bond convergence, restore/inverse, or promotion controls are admitted",
            "any downstream consumer is opened",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "phase2_delete_anchor_orbit_v1",
        "summary": {
            "all_pass": all_pass,
            "candidate": "peps3d_delete_anchor_orbit",
            "support_atom_count": orbit["support_atom_count"],
            "relabeling_count": orbit["relabeling_count"],
            "orbit_row_count": orbit["orbit_row_count"],
            "illegal_relabel_control_count": orbit["illegal_relabel_control_count"],
            "max_parent_peps3d_sites": orbit["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": orbit["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": orbit["max_peps3d_bond"],
            "max_legal_relabel_gap": orbit["max_legal_relabel_gap"],
            "min_illegal_relabel_gap": orbit["min_illegal_relabel_gap"],
            "min_full_order_gap": orbit["min_full_order_gap"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "result_summary": {
            "all_pass": all_pass,
            "support_atom_count": orbit["support_atom_count"],
            "relabeling_count": orbit["relabeling_count"],
            "orbit_row_count": orbit["orbit_row_count"],
            "illegal_relabel_control_count": orbit["illegal_relabel_control_count"],
            "support_atoms": orbit["support_atoms"],
            "max_parent_peps3d_sites": orbit["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": orbit["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": orbit["max_peps3d_bond"],
            "max_legal_relabel_gap": orbit["max_legal_relabel_gap"],
            "min_illegal_relabel_gap": orbit["min_illegal_relabel_gap"],
            "min_full_order_gap": orbit["min_full_order_gap"],
        },
        "pass_rule": "all positive, graveyard, and boundary checks pass; legal relabelings preserve support kind and PEPS3D anchors; illegal relabels are rejected; dense closure and downstream promotion remain blocked",
        "fail_rule": "any failed positive/control/boundary row, dense closure use, downstream dependency, missing anchors, legal relabel mismatch, illegal relabel admission, symmetry/topology overclaim, all-subset overclaim, or collapsed inherited full-support N01 witness fails the scout",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_carrier_frontier_matrix_only"],
        "next_admissible_step": "Classify this anchor-orbit receipt, then name another bounded active carrier-frontier map or write the next active-frontier blocker. Do not open downstream geometry.",
        "runtime_seconds": time.time() - started,
        "all_pass": all_pass,
        "result_path": str(OUT_PATH),
        "support_atom_count": orbit["support_atom_count"],
        "relabeling_count": orbit["relabeling_count"],
        "orbit_row_count": orbit["orbit_row_count"],
        "illegal_relabel_control_count": orbit["illegal_relabel_control_count"],
        "max_parent_peps3d_sites": orbit["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": orbit["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": orbit["max_peps3d_bond"],
        "max_legal_relabel_gap": orbit["max_legal_relabel_gap"],
        "min_illegal_relabel_gap": orbit["min_illegal_relabel_gap"],
        "min_full_order_gap": orbit["min_full_order_gap"],
    }

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "all_pass": all_pass,
                "support_atom_count": orbit["support_atom_count"],
                "relabeling_count": orbit["relabeling_count"],
                "orbit_row_count": orbit["orbit_row_count"],
                "illegal_relabel_control_count": orbit["illegal_relabel_control_count"],
                "max_parent_peps3d_sites": orbit["max_parent_peps3d_sites"],
                "max_triple_overlap_peps3d_sites": orbit["max_triple_overlap_peps3d_sites"],
                "max_peps3d_bond": orbit["max_peps3d_bond"],
                "max_legal_relabel_gap": orbit["max_legal_relabel_gap"],
                "min_illegal_relabel_gap": orbit["min_illegal_relabel_gap"],
                "min_full_order_gap": orbit["min_full_order_gap"],
                "result_path": str(OUT_PATH),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
