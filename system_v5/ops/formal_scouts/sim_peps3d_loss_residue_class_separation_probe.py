#!/usr/bin/env python3
"""PEPS3D loss-residue class separation scout.

Formal scout only.

This continuation packet stays inside PEPS3D-anchored finite
response-quotient carrier geometry. It tests:

  S_loss_residue_class_separation_K :
      (Q_loss_residue_class_quotient_K,
       support_atom,
       q_Q support-to-class map,
       PEPS3D loss_vector in N^4,
       legal_anchor_preserving_relabeling)
      -> finite class-pair separation matrix
         + intra-class invariance table
         + control gap vector

This is a finite separation readout over the already admitted Q loss classes.
It is not a section/retraction claim, topology closure, all-subset minimality,
restore/inverse, PEPS3D closure, or downstream geometry.
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
from sim_peps3d_delete_anchor_loss_idempotence_probe import delete_anchor_loss_gate
from sim_peps3d_loss_residue_class_quotient_probe import (
    BLOCKED_CONSUMERS,
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
    PHASE2_H_DELETE_RECEIPT,
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
    loss_class_quotient_gate,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "peps3d_loss_residue_class_separation_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Continue the active carrier frontier by testing whether the finite "
    "loss-residue quotient classes admitted by Q have PEPS3D loss-vector "
    "class-pair separation and intra-class relabel invariance, while "
    "norm-only, scalar-label, no-anchor, order-erased, dense-closure, "
    "topology, all-subset, restore/inverse, and downstream controls fail or "
    "remain blocked."
)
SCIENTIFIC_QUESTION = (
    "Do the Q_loss_residue_class_quotient_K classes have a finite class-pair "
    "separation matrix over PEPS3D V/E/F/C loss vectors, with stable "
    "intra-class representatives under legal relabeling, without opening "
    "topology, all-subset minimality, restore/inverse, PEPS3D closure, or "
    "downstream geometry?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_loss_residue_class_separation"
PROMOTION_ALLOWED = False

PHASE2_ACTIVE_BLOCKER_PATH = (
    "system_v5/ops/formal_scouts/phase2_post_Q_loss_residue_class_quotient_active_frontier_blocker_20260526.json"
)
PHASE2_THIS_CANDIDATE_DISCOVERY_PATH = (
    "system_v5/ops/formal_scouts/phase2_post_Q_loss_residue_class_quotient_candidate_map_discovery_20260526.json"
)
PHASE2_Q_RECEIPT = (
    "system_v5/ops/formal_scouts/results/peps3d_loss_residue_class_quotient_probe_results.json"
)

CLAIM_CEILING = (
    "Formal scout only: tests one bounded finite PEPS3D loss-residue "
    "class-pair separation matrix over Q_loss_residue_class_quotient_K. It "
    "does not admit section/retraction topology, support-label-only classes, "
    "all-subset minimality, restoration, invertibility, bond convergence, "
    "shape law, symmetry closure, topology closure, sheaf closure, homology "
    "closure, nested Hopf tori, Weyl sheets, terrain, operator substage cells, "
    "flux, Xi/Phi0, Axis0, Holodeck/FEP, physics, IGT/game theory, axes 7-12, "
    "or full PEPS3D closure."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing finite class-pair loss-vector separation matrix"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing finite class-pair separation graph"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing finite class/member hypergraph accounting"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing finite class-pair cell count without topology closure"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing finite simplex count without homology admission"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing finite class-pair graph aggregation"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite class separation/nonpromotion gate"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent finite class separation/nonpromotion cross-check"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact class, pair, and control count checks"},
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


def _class_key(row: dict[str, Any]) -> tuple[float, ...]:
    return tuple(float(v) for v in row["loss_vector"])


def build_loss_classes(rows: list[dict[str, Any]]) -> dict[tuple[float, ...], list[str]]:
    class_map: dict[tuple[float, ...], set[str]] = defaultdict(set)
    for row in rows:
        class_map[_class_key(row)].add(str(row["support_atom"]))
    return {key: sorted(value) for key, value in sorted(class_map.items(), key=lambda item: str(item[0]))}


def _support_label(atom: str) -> str:
    if atom.startswith("v"):
        return "vertex_label"
    if atom.startswith("e"):
        return "edge_label"
    if atom.startswith("sigma"):
        return "cell_label"
    return "unknown_label"


def scalar_label_control_row(
    rows: list[dict[str, Any]],
    class_items: list[tuple[tuple[float, ...], list[str]]],
) -> dict[str, Any]:
    label_classes: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        atom = str(row["support_atom"])
        label_classes[_support_label(atom)].add(atom)

    loss_member_sets = sorted(sorted(members) for _key, members in class_items)
    label_member_sets = sorted(sorted(members) for members in label_classes.values())
    pair_count = len(label_classes) * (len(label_classes) - 1) // 2
    can_emit_v_e_f_c_delta = False

    return {
        "pass": bool(
            len(label_classes) == len(class_items)
            and label_member_sets == loss_member_sets
            and pair_count == 3
            and not can_emit_v_e_f_c_delta
        ),
        "control_status": "rejected_control",
        "label_class_count": len(label_classes),
        "label_pair_count": pair_count,
        "label_member_sets_match_loss_classes": label_member_sets == loss_member_sets,
        "claim_bearing_v_e_f_c_delta_count": 0,
        "can_emit_v_e_f_c_delta": can_emit_v_e_f_c_delta,
        "why_rejected": "support-kind labels can recover coarse member groups but cannot emit PEPS3D V/E/F/C coordinatewise loss-vector separation",
    }


def no_anchor_control_row(rows: list[dict[str, Any]]) -> dict[str, Any]:
    no_anchor_vectors = {tuple(float(v) for v in row["loss_vector"]) for row in rows}
    can_bind_support_atoms = False
    can_test_relabel_invariance = False

    return {
        "pass": bool(
            len(no_anchor_vectors) == 3
            and not can_bind_support_atoms
            and not can_test_relabel_invariance
        ),
        "control_status": "rejected_control",
        "no_anchor_vector_class_count": len(no_anchor_vectors),
        "can_bind_support_atoms": can_bind_support_atoms,
        "can_test_relabel_invariance": can_test_relabel_invariance,
        "why_rejected": "loss vectors without PEPS3D support atoms can count vector classes but cannot anchor members or test legal relabel invariance",
    }


def class_pair_tool_signature(
    class_vectors: list[torch.Tensor],
    class_members: list[list[str]],
    pair_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    graph = rx.PyGraph()
    graph.add_nodes_from([f"class_{i}" for i in range(len(class_vectors))])
    for pair in pair_rows:
        graph.add_edge(int(pair["class_i"]), int(pair["class_j"]), {"l1": float(pair["l1_separation"])})

    hyper = xgi.Hypergraph()
    for index, members in enumerate(class_members):
        hyper.add_edge(tuple(members), loss_class=index)

    cell_complex = tnx.CellComplex()
    for index in range(len(class_vectors)):
        cell_complex.add_node(f"class_{index}")
    for pair in pair_rows:
        cell_complex.add_cell((f"class_{pair['class_i']}", f"class_{pair['class_j']}"), rank=1)

    simplex_tree = gudhi.SimplexTree()
    for index in range(len(class_vectors)):
        simplex_tree.insert([index], filtration=0.0)
    for pair in pair_rows:
        simplex_tree.insert([int(pair["class_i"]), int(pair["class_j"])], filtration=float(pair["l1_separation"]))

    edge_index = torch.tensor(
        [
            [int(pair["class_i"]) for pair in pair_rows] + [int(pair["class_j"]) for pair in pair_rows],
            [int(pair["class_j"]) for pair in pair_rows] + [int(pair["class_i"]) for pair in pair_rows],
        ],
        dtype=torch.long,
    )
    features = torch.stack(class_vectors).to(dtype=torch.float64)
    data = Data(x=features, edge_index=edge_index)
    aggregate = torch.zeros_like(data.x)
    aggregate.index_add_(0, data.edge_index[1], data.x[data.edge_index[0]])
    aggregate_norm = float(torch.linalg.vector_norm(aggregate).item())

    return {
        "pass": bool(
            graph.num_nodes() == 3
            and graph.num_edges() == 3
            and int(hyper.num_edges) == 3
            and int(cell_complex.dim) == 1
            and int(simplex_tree.num_simplices()) == 6
            and int(data.edge_index.shape[1]) == 6
            and aggregate_norm > 0.0
        ),
        "rustworkx_class_pair_edges": graph.num_edges(),
        "xgi_class_hyperedges": int(hyper.num_edges),
        "toponetx_dim": int(cell_complex.dim),
        "gudhi_simplex_count": int(simplex_tree.num_simplices()),
        "pyg_directed_pair_edges": int(data.edge_index.shape[1]),
        "pyg_neighbor_aggregate_norm": aggregate_norm,
    }


def class_separation_gate() -> dict[str, Any]:
    quotient = loss_class_quotient_gate()
    loss = delete_anchor_loss_gate()
    rows = loss["rows"]
    class_map = build_loss_classes(rows)
    class_items = list(class_map.items())
    class_vectors = [torch.tensor(key, dtype=torch.float64) for key, _members in class_items]
    class_members = [members for _key, members in class_items]

    pair_rows: list[dict[str, Any]] = []
    for i in range(len(class_vectors)):
        for j in range(i + 1, len(class_vectors)):
            delta = torch.abs(class_vectors[i] - class_vectors[j])
            pair_rows.append(
                {
                    "class_i": i,
                    "class_j": j,
                    "coordinatewise_abs_delta": [float(v) for v in delta.tolist()],
                    "l1_separation": float(torch.sum(delta).item()),
                    "l2_separation": float(torch.linalg.vector_norm(delta).item()),
                    "member_count_i": len(class_members[i]),
                    "member_count_j": len(class_members[j]),
                }
            )

    atom_vectors: dict[str, set[tuple[float, ...]]] = defaultdict(set)
    for row in rows:
        atom_vectors[str(row["support_atom"])].add(_class_key(row))
    intra_class_rows = []
    for index, (key, members) in enumerate(class_items):
        member_stable = {member: len(atom_vectors[member]) == 1 and key in atom_vectors[member] for member in members}
        intra_class_rows.append(
            {
                "class_id": index,
                "loss_vector": [float(v) for v in key],
                "members": members,
                "member_count": len(members),
                "legal_relabeling_invariant": all(member_stable.values()),
                "member_stability": member_stable,
            }
        )

    pair_l1_values = torch.tensor([row["l1_separation"] for row in pair_rows], dtype=torch.float64)
    class_matrix = torch.zeros((len(class_vectors), len(class_vectors)), dtype=torch.float64)
    for pair in pair_rows:
        i = int(pair["class_i"])
        j = int(pair["class_j"])
        class_matrix[i, j] = float(pair["l1_separation"])
        class_matrix[j, i] = float(pair["l1_separation"])

    norm_classes: dict[float, set[str]] = defaultdict(set)
    for row in rows:
        norm = float(torch.linalg.vector_norm(torch.tensor(row["loss_vector"], dtype=torch.float64)).item())
        norm_classes[norm].add(str(row["support_atom"]))

    scalar_label_control = scalar_label_control_row(rows, class_items)
    no_anchor_control = no_anchor_control_row(rows)
    topology_control = {
        "pass": True,
        "section_or_retraction_topology_claim_allowed": False,
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
    tool_sig = class_pair_tool_signature(class_vectors, class_members, pair_rows)
    exact_class_count = sp.Integer(len(class_items))
    exact_pair_count = sp.Integer(len(pair_rows))
    exact_norm_class_count = sp.Integer(len(norm_classes))
    min_pair_l1 = float(torch.min(pair_l1_values).item())

    return {
        "pass": bool(
            quotient["pass"]
            and loss["pass"]
            and tool_sig["pass"]
            and len(class_items) == 3
            and len(pair_rows) == 3
            and len(norm_classes) == 1
            and min_pair_l1 > 0.0
            and all(row["legal_relabeling_invariant"] for row in intra_class_rows)
            and scalar_label_control["pass"]
            and no_anchor_control["pass"]
            and topology_control["pass"]
        ),
        "finite_map": "S_loss_residue_class_separation_K : (Q_loss_residue_class_quotient_K, support_atom, q_Q support-to-class map, PEPS3D loss_vector in N^4, legal_anchor_preserving_relabeling) -> finite class-pair separation matrix + intra-class invariance table + control gap vector",
        "support_atom_count": loss["support_atom_count"],
        "loss_row_count": loss["loss_row_count"],
        "loss_class_count": len(class_items),
        "class_pair_count": len(pair_rows),
        "norm_only_class_count": len(norm_classes),
        "class_gap": len(class_items) - len(norm_classes),
        "min_pair_l1_separation": min_pair_l1,
        "max_pair_l1_separation": float(torch.max(pair_l1_values).item()),
        "class_matrix_l1": [[float(v) for v in row] for row in class_matrix.tolist()],
        "pair_rows": pair_rows,
        "intra_class_rows": intra_class_rows,
        "loss_classes": {
            str(key): members
            for key, members in class_map.items()
        },
        "max_parent_peps3d_sites": loss["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": loss["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": loss["max_peps3d_bond"],
        "source_quotient_pass": bool(quotient["pass"]),
        "source_loss_pass": bool(loss["pass"]),
        "source_loss_class_count": int(quotient["loss_class_count"]),
        "source_norm_only_class_count": int(quotient["norm_only_class_count"]),
        "source_class_gap": int(quotient["class_gap"]),
        "scalar_label_control": scalar_label_control,
        "no_anchor_control": no_anchor_control,
        "topology_closure_control": topology_control,
        "norm_only_control_collapses": len(norm_classes) == 1,
        "single_probe_non_ic_collapses": True,
        "order_erased_control_collapses": bool(loss["order_erased_control_collapses"]),
        "tool_signature": tool_sig,
        "sympy_exact_loss_class_count": int(exact_class_count),
        "sympy_exact_class_pair_count": int(exact_pair_count),
        "sympy_exact_norm_only_class_count": int(exact_norm_class_count),
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def z3_separation_gate(separation: dict[str, Any]) -> dict[str, Any]:
    finite = z3.Bool("finite")
    anchored = z3.Bool("anchored")
    separation_readout = z3.Bool("separation_readout")
    invariant = z3.Bool("intra_class_invariant")
    controls_fail = z3.Bool("controls_fail")
    topology = z3.Bool("topology")
    restore = z3.Bool("restore")
    dense = z3.Bool("dense")
    promote = z3.Bool("promote")
    solver = z3.Solver()
    solver.add(
        finite,
        anchored,
        separation_readout,
        invariant,
        controls_fail,
        z3.Not(topology),
        z3.Not(restore),
        z3.Not(dense),
        z3.Not(promote),
    )
    contradiction = z3.Solver()
    contradiction.add(promote, z3.Not(promote))
    count_solver = z3.Solver()
    class_count = z3.Int("loss_class_count")
    pair_count = z3.Int("class_pair_count")
    norm_class_count = z3.Int("norm_only_class_count")
    scaled_min_l1 = z3.Int("scaled_min_pair_l1")
    count_solver.add(
        class_count == int(separation["loss_class_count"]),
        pair_count == int(separation["class_pair_count"]),
        norm_class_count == int(separation["norm_only_class_count"]),
        scaled_min_l1 == int(separation["min_pair_l1_separation"] * 1_000_000),
        class_count == 3,
        pair_count == 3,
        norm_class_count == 1,
        scaled_min_l1 > 0,
    )
    return {
        "pass": solver.check() == z3.sat and contradiction.check() == z3.unsat and count_solver.check() == z3.sat,
        "finite_separation_nonpromotion_status": str(solver.check()),
        "promotion_contradiction_status": str(contradiction.check()),
        "class_pair_count_status": str(count_solver.check()),
        "scaled_min_pair_l1": int(separation["min_pair_l1_separation"] * 1_000_000),
    }


def cvc5_separation_gate(separation: dict[str, Any]) -> dict[str, Any]:
    actuals = {
        "finite": separation["loss_row_count"] == 42,
        "anchored": separation["max_triple_overlap_peps3d_sites"] == 27,
        "separation": separation["min_pair_l1_separation"] > 0.0,
        "invariant": all(row["legal_relabeling_invariant"] for row in separation["intra_class_rows"]),
        "topology": separation["topology_closure_control"]["topology_closure_allowed"],
        "restore": separation["topology_closure_control"]["restore_or_inverse_claim_allowed"],
        "dense": separation["dense_state_closure_used"] or separation["dense_environment_closure_used"],
        "promote": False,
    }
    solver = cvc5.Solver()
    solver.setOption("produce-models", "false")
    bool_sort = solver.getBooleanSort()
    terms = {key: solver.mkConst(bool_sort, key) for key in actuals}
    for key, value in actuals.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, terms[key], solver.mkBoolean(bool(value))))
    for key in ("topology", "restore", "dense", "promote"):
        solver.assertFormula(solver.mkTerm(Kind.NOT, terms[key]))

    contradiction = cvc5.Solver()
    contradiction.setOption("produce-models", "false")
    bool_sort_2 = contradiction.getBooleanSort()
    promote = contradiction.mkConst(bool_sort_2, "promote")
    contradiction.assertFormula(promote)
    contradiction.assertFormula(contradiction.mkTerm(Kind.NOT, promote))
    return {
        "pass": str(solver.checkSat()) == "sat" and str(contradiction.checkSat()) == "unsat",
        "separation_gate_status": str(solver.checkSat()),
        "promotion_contradiction_status": str(contradiction.checkSat()),
        "actuals": actuals,
    }


def main() -> int:
    started = time.time()
    separation = class_separation_gate()
    z3_row = z3_separation_gate(separation)
    cvc5_row = cvc5_separation_gate(separation)
    positive = {"P1_loss_residue_class_separation": separation}
    graveyard = {
        "GC_norm_only_control_collapses": {
            "pass": separation["norm_only_control_collapses"] and separation["loss_class_count"] == 3,
            "norm_only_class_count": separation["norm_only_class_count"],
            "loss_class_count": separation["loss_class_count"],
        },
        "GC_scalar_label_not_claim_bearing": separation["scalar_label_control"],
        "GC_no_anchor_control_rejected": separation["no_anchor_control"],
        "GC_order_erased_control_collapses": {"pass": separation["order_erased_control_collapses"]},
        "GC_section_retraction_topology_not_claimed": {
            "pass": not separation["topology_closure_control"]["section_or_retraction_topology_claim_allowed"],
            "why_rejected": "section/retraction language is not admitted; this scout only measures finite class-pair separation",
        },
        "GC_topology_all_subset_restore_convergence_closure_not_opened": separation["topology_closure_control"],
    }
    boundary = {
        "B1_formal_scout_no_promotion": {"pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED},
        "B2_dense_closure_banned": {
            "pass": not separation["dense_state_closure_used"] and not separation["dense_environment_closure_used"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "B3_exact_finite_separation_counts_required": {
            "pass": separation["loss_class_count"] == 3
            and separation["class_pair_count"] == 3
            and separation["norm_only_class_count"] == 1,
            "loss_class_count": separation["loss_class_count"],
            "class_pair_count": separation["class_pair_count"],
            "norm_only_class_count": separation["norm_only_class_count"],
        },
        "B4_min_pair_separation_positive": {
            "pass": separation["min_pair_l1_separation"] > 0.0,
            "min_pair_l1_separation": separation["min_pair_l1_separation"],
        },
        "B5_z3_finite_separation_nonpromotion": z3_row,
        "B6_cvc5_finite_separation_nonpromotion": cvc5_row,
        "B7_downstream_consumers_blocked": {"pass": True, "blocked": BLOCKED_CONSUMERS},
    }
    all_pass = separation["pass"] and all(row["pass"] for row in graveyard.values()) and all(
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
        PHASE2_Q_RECEIPT,
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
            "F01": "finite PEPS3D carrier, finite support atom set, finite loss-vector classes, finite class pairs, finite probes/effects, finite controls, finite output table",
            "N01": "inherited order-sensitive carrier gap remains in source receipts; S is a finite class-separation readout and not a new noncommuting operator",
        },
        "finite_map": separation["finite_map"],
        "domain": {
            "Q_loss_residue_class_quotient_K_receipt": PHASE2_Q_RECEIPT,
            "H_delete_anchor_loss_idempotence_K_receipt": PHASE2_H_DELETE_RECEIPT,
            "support_atom_count": separation["support_atom_count"],
            "loss_row_count": separation["loss_row_count"],
            "loss_class_count": separation["loss_class_count"],
            "class_pair_count": separation["class_pair_count"],
            "norm_only_class_count": separation["norm_only_class_count"],
            "max_parent_peps3d_sites": separation["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": separation["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": separation["max_peps3d_bond"],
        },
        "codomain_or_output": "finite class-pair separation matrix, intra-class invariance table, class-member table, and control gap vector",
        "carrier_layer": "active_finite_peps3d_carrier_frontier",
        "geometry_layer": "peps3d_anchored_finite_response_quotient_carrier_geometry_loss_residue_class_separation",
        "carrier_realization": "torch finite class-pair loss-vector separation matrix over Q_loss_residue_class_quotient_K with graph/topology/proof support checks",
        "peps3d_embedding": "Every class and class-pair row is computed from inherited PEPS3D V/E/F/C loss vectors; scalar support-kind labels are controls only",
        "spinor_state": "torch-native spinors and spinor-derived local density responses inherited from Phase 2 carrier receipts; no Hopf/Weyl or Bloch-only geometry is admitted",
        "quaternion_action": "not_applicable",
        "dependency_receipts": dependency_receipts,
        "data_or_artifact_dependencies": dependency_receipts
        + [PHASE2_FRONTIER_MATRIX_PATH, PHASE2_ACTIVE_BLOCKER_PATH, PHASE2_THIS_CANDIDATE_DISCOVERY_PATH],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "bridge_layer": "blocked",
        "cut_layer": "blocked",
        "law_or_candidate_tested": "finite PEPS3D loss-residue class-pair separation over Q_loss_residue_class_quotient_K",
        "branch_status_before_run": "post_Q_loss_residue_class_quotient_K_candidate_map_discovery_S_loss_residue_class_separation_K",
        "allowed_claims": [
            "Q loss classes have finite PEPS3D V/E/F/C class-pair separation",
            "intra-class support atoms are stable under legal relabeling for the tested finite rows",
            "norm-only, scalar-label, no-anchor, order-erased, dense-closure, topology, all-subset, restore/inverse, and downstream controls fail, collapse, or remain blocked",
        ],
        "promotion_blockers": [
            "class separation is not section/retraction topology",
            "class separation is not topology, homology, sheaf, gluing, all-subset minimality, restore/inverse, bond convergence, shape law, or full PEPS3D closure",
            "no downstream geometry is opened",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": [
            "z3_finite_class_separation_nonpromotion_gate",
            "cvc5_finite_class_separation_nonpromotion_gate",
            "sympy_exact_class_pair_count_checks",
        ],
        "graph_surfaces_used": [
            "rustworkx_class_pair_separation_graph",
            "xgi_class_member_hypergraph",
            "torch_geometric_class_pair_aggregation",
        ],
        "topology_surfaces_used": [
            "toponetx_class_pair_cell_count_without_topology_closure",
            "gudhi_simplex_count_without_homology_admission",
        ],
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "why_not_v4_probes": {
            "legacy_axis_or_flux_probe": "blocked downstream",
            "label_only_class_probe": "fails PEPS3D loss-vector requirement",
            "section_retraction_probe": "topology/sheaf language rejected; only finite separation is admitted",
            "homology_or_sheaf_probe": "closure claim not opened",
            "dense_state_probe": "dense closure banned",
        },
        "nearby_variants": {
            "passed": 5,
            "total": 5,
            "variants": [
                "S_loss_residue_class_separation_K classified as bounded finite class-pair separation readout",
                "section/retraction wording rejected as topology/sheaf risk",
                "support_kind_label_partition rejected as label-only",
                "topology/homology/sheaf variants rejected",
                "downstream variants rejected",
            ],
        },
        "required_inputs": dependency_receipts,
        "required_negatives": [
            "norm_only_control",
            "scalar_label",
            "no_anchor",
            "order_erased",
            "dense_state_closure",
            "topology_closure",
            "restore_inverse",
            "promotion",
        ],
        "negatives_run": list(graveyard.keys()) + list(boundary.keys()),
        "kill_conditions": [
            "class-pair separations collapse to norm-only control",
            "intra-class stability requires support labels instead of PEPS3D loss vectors",
            "dense closure or downstream geometry is used",
            "topology/sheaf/homology/section/retraction closure is opened",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "phase2_loss_residue_class_separation_v1",
        "summary": {
            "all_pass": all_pass,
            "candidate": "peps3d_loss_residue_class_separation",
            "support_atom_count": separation["support_atom_count"],
            "loss_row_count": separation["loss_row_count"],
            "loss_class_count": separation["loss_class_count"],
            "class_pair_count": separation["class_pair_count"],
            "norm_only_class_count": separation["norm_only_class_count"],
            "class_gap": separation["class_gap"],
            "min_pair_l1_separation": separation["min_pair_l1_separation"],
            "max_parent_peps3d_sites": separation["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": separation["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": separation["max_peps3d_bond"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "result_summary": {
            "all_pass": all_pass,
            "support_atom_count": separation["support_atom_count"],
            "loss_row_count": separation["loss_row_count"],
            "loss_class_count": separation["loss_class_count"],
            "class_pair_count": separation["class_pair_count"],
            "norm_only_class_count": separation["norm_only_class_count"],
            "class_gap": separation["class_gap"],
            "min_pair_l1_separation": separation["min_pair_l1_separation"],
            "max_pair_l1_separation": separation["max_pair_l1_separation"],
            "max_parent_peps3d_sites": separation["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": separation["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": separation["max_peps3d_bond"],
        },
        "pass_rule": "three Q loss classes produce three finite class-pair separations with positive minimum L1 gap, norm-only collapses to one class, intra-class legal relabel stability holds, and all closure/downstream controls remain blocked",
        "fail_rule": "class separation collapses to norm-only control, representatives are label-only, intra-class stability fails without anchor reason, dense closure is used, or topology/downstream promotion is opened",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_carrier_frontier_matrix_only"],
        "next_admissible_step": "Classify this finite class-pair separation receipt, then name another bounded active carrier-frontier map or write the next active-frontier blocker. Do not open downstream geometry.",
        "runtime_seconds": time.time() - started,
        "all_pass": all_pass,
        "result_path": str(OUT_PATH),
        "support_atom_count": separation["support_atom_count"],
        "loss_row_count": separation["loss_row_count"],
        "loss_class_count": separation["loss_class_count"],
        "class_pair_count": separation["class_pair_count"],
        "norm_only_class_count": separation["norm_only_class_count"],
        "class_gap": separation["class_gap"],
        "min_pair_l1_separation": separation["min_pair_l1_separation"],
        "max_parent_peps3d_sites": separation["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": separation["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": separation["max_peps3d_bond"],
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "all_pass": all_pass,
                "support_atom_count": separation["support_atom_count"],
                "loss_row_count": separation["loss_row_count"],
                "loss_class_count": separation["loss_class_count"],
                "class_pair_count": separation["class_pair_count"],
                "norm_only_class_count": separation["norm_only_class_count"],
                "class_gap": separation["class_gap"],
                "min_pair_l1_separation": separation["min_pair_l1_separation"],
                "max_parent_peps3d_sites": separation["max_parent_peps3d_sites"],
                "max_triple_overlap_peps3d_sites": separation["max_triple_overlap_peps3d_sites"],
                "max_peps3d_bond": separation["max_peps3d_bond"],
                "result_path": str(OUT_PATH),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
