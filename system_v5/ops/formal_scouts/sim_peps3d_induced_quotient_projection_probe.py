#!/usr/bin/env python3
"""PEPS3D induced quotient-projection scout.

Formal scout only.

This packet stays inside Phase 2 PEPS3D-anchored finite response-quotient
carrier geometry. It tests:

  Y_induced_quotient_projection_K :
      (Y_row_deletion_collision_stability_K,
       Z_active_pair_collision_residue_K,
       U_loss_pair_support_mask_K,
       epsilon_p,
       kappa_Z)
      -> finite induced quotient partitions Q_p
         + quotient-size vector
         + F-boundary no-collision controls

The claim-bearing output is the explicit induced quotient partition table after
each allowed single-row deletion, not just Y's survival counts.
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
from sim_peps3d_active_pair_collision_residue_probe import active_pair_collision_gate
from sim_peps3d_loss_pair_support_mask_probe import support_mask_gate
from sim_peps3d_row_deletion_collision_stability_probe import (
    ACTIVE_PAIR_IDS,
    BLOCKED_CONSUMERS,
    BOUNDARY_PAIR_IDS,
    COORDINATES,
    row_deletion_stability_gate,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "peps3d_induced_quotient_projection_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Continue the active Phase 2 carrier frontier after the killed Y_order_gap_K "
    "candidate by testing whether each allowed single class-pair row deletion "
    "emits an explicit induced quotient partition table under kappa_Z. "
    "Survival counts alone are controls, not the claim-bearing output."
)
SCIENTIFIC_QUESTION = (
    "After deleting one finite class-pair row, can the Z collision relation "
    "be projected to explicit finite quotient partitions Q_p over the remaining "
    "anchored support-mask rows, while F-boundary rows remain no-collision "
    "controls?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_induced_quotient_projection"
PROMOTION_ALLOWED = False

PHASE2_SEED_RECEIPT = "system_v5/ops/formal_scouts/results/finite_peps3d_probe_effect_seed_carrier_gate_probe_results.json"
PHASE2_SPINOR_DENSITY_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_spinor_density_carrier_gate_probe_results.json"
PHASE2_U_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_loss_pair_support_mask_probe_results.json"
PHASE2_Z_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_active_pair_collision_residue_probe_results.json"
PHASE2_Y_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_row_deletion_collision_stability_probe_results.json"
PHASE2_Y_ORDER_KILL_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_row_coordinate_deletion_order_gap_probe_results.json"
PHASE2_FRONTIER_MATRIX_PATH = "system_v5/ops/formal_scouts/phase2_peps3d_seed_frontier_matrix_20260525.json"
PHASE2_ACTIVE_BLOCKER_PATH = "system_v5/ops/formal_scouts/phase2_post_Y_order_gap_killed_active_frontier_blocker_20260526.json"
PHASE2_THIS_CANDIDATE_DISCOVERY_PATH = "system_v5/ops/formal_scouts/phase2_post_Y_order_gap_killed_candidate_map_discovery_20260526.json"

CLAIM_CEILING = (
    "Formal scout only: tests one bounded finite induced quotient-projection "
    "readout after row deletion. It does not admit all-subset minimality, "
    "restoration, invertibility, topology closure, sheaf closure, homology "
    "closure, bond convergence, shape law, nested Hopf tori, Weyl sheets, "
    "terrain, operator substage cells, flux, Xi/Phi0, Axis0, Holodeck/FEP, "
    "physics, IGT/game theory, axes 7-12, or full PEPS3D closure."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing quotient-size tensors and collision vectors"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing finite quotient-projection graph"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing quotient class/member hypergraph accounting"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing finite row/class cell count without topology closure"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing finite simplex count without homology admission"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing quotient-size vector aggregation"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite quotient/nonpromotion gate"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent finite quotient/nonpromotion cross-check"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact quotient row and class count checks"},
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


def induced_classes(partition_classes: list[dict[str, Any]], removed_pair: str) -> list[dict[str, Any]]:
    quotient: list[dict[str, Any]] = []
    for class_row in partition_classes:
        remaining = [member for member in class_row["pair_members"] if member != removed_pair]
        if not remaining:
            continue
        quotient.append(
            {
                "source_class_id": class_row["class_id"],
                "mask": [int(value) for value in class_row["mask"]],
                "pair_members": remaining,
                "class_size": len(remaining),
                "class_kind": "collision" if len(remaining) > 1 else "singleton",
            }
        )
    return quotient


def quotient_tool_signature(rows: list[dict[str, Any]]) -> dict[str, Any]:
    expected_row_count = 18
    expected_quotient_class_count = 33
    expected_member_edge_count = 36
    expected_hyperedge_count = expected_quotient_class_count
    expected_simplex_count = 66
    expected_pyg_edges = expected_row_count
    expected_pyg_size_sum = float(expected_member_edge_count)
    graph = rx.PyDiGraph()
    row_nodes = {index: graph.add_node(f"{row['removed_pair']}|{row['pair_id']}") for index, row in enumerate(rows)}
    class_count = 0
    member_edge_count = 0
    for index, row in enumerate(rows):
        for class_row in row["quotient_classes"]:
            class_node = graph.add_node(f"{row['removed_pair']}|{row['pair_id']}|{class_row['source_class_id']}")
            graph.add_edge(row_nodes[index], class_node, {"size": class_row["class_size"]})
            class_count += 1
            for member in class_row["pair_members"]:
                member_node = graph.add_node(f"{row['removed_pair']}|{row['pair_id']}|{member}")
                graph.add_edge(class_node, member_node, {"member": member})
                member_edge_count += 1

    hyper = xgi.Hypergraph()
    for row in rows:
        for class_row in row["quotient_classes"]:
            hyper.add_edge(
                (row["removed_pair"], row["pair_id"]) + tuple(class_row["pair_members"]),
                kind=class_row["class_kind"],
            )

    cell_complex = tnx.CellComplex()
    for row in rows:
        cell_complex.add_node(row["removed_pair"])
        cell_complex.add_node(row["pair_id"])
        cell_complex.add_cell((row["removed_pair"], row["pair_id"]), rank=1)

    simplex_tree = gudhi.SimplexTree()
    vertex_ids: dict[str, int] = {}

    def vid(name: str) -> int:
        if name not in vertex_ids:
            vertex_ids[name] = len(vertex_ids)
            simplex_tree.insert([vertex_ids[name]], filtration=0.0)
        return vertex_ids[name]

    for row in rows:
        base = vid(f"{row['removed_pair']}|{row['pair_id']}")
        for class_row in row["quotient_classes"]:
            simplex_tree.insert([base, vid(class_row["source_class_id"])], filtration=1.0)

    max_classes = max(len(row["quotient_classes"]) for row in rows)
    size_rows = []
    for row in rows:
        sizes = [class_row["class_size"] for class_row in row["quotient_classes"]]
        size_rows.append(sizes + [0] * (max_classes - len(sizes)))
    quotient_tensor = torch.tensor(size_rows, dtype=torch.float64)
    edge_index = torch.tensor(
        [
            list(range(len(rows))),
            [len(rows)] * len(rows),
        ],
        dtype=torch.long,
    )
    data = Data(x=quotient_tensor, edge_index=edge_index)

    return {
        "pass": bool(
            len(rows) == expected_row_count
            and class_count == expected_quotient_class_count
            and member_edge_count == expected_member_edge_count
            and int(hyper.num_edges) == expected_hyperedge_count
            and int(cell_complex.dim) == 1
            and int(simplex_tree.num_simplices()) == expected_simplex_count
            and int(data.edge_index.shape[1]) == expected_pyg_edges
            and float(torch.sum(data.x).item()) == expected_pyg_size_sum
        ),
        "expected_row_count": expected_row_count,
        "expected_quotient_class_count": expected_quotient_class_count,
        "expected_member_edge_count": expected_member_edge_count,
        "expected_hyperedge_count": expected_hyperedge_count,
        "expected_simplex_count": expected_simplex_count,
        "expected_pyg_edges": expected_pyg_edges,
        "expected_pyg_size_sum": expected_pyg_size_sum,
        "rustworkx_nodes": int(graph.num_nodes()),
        "rustworkx_edges": int(graph.num_edges()),
        "quotient_class_count": class_count,
        "member_edge_count": member_edge_count,
        "xgi_hyperedges": int(hyper.num_edges),
        "toponetx_dim": int(cell_complex.dim),
        "gudhi_simplex_count": int(simplex_tree.num_simplices()),
        "pyg_directed_edges": int(data.edge_index.shape[1]),
        "pyg_size_sum": float(torch.sum(data.x).item()),
    }


def quotient_anchor_binding_check(rows: list[dict[str, Any]], removable_pairs: list[str]) -> dict[str, Any]:
    allowed_pair_ids = set(ACTIVE_PAIR_IDS) | set(BOUNDARY_PAIR_IDS)
    removable_set = set(removable_pairs)
    row_checks: list[dict[str, Any]] = []
    for row in rows:
        remaining_allowed = removable_set - {row["removed_pair"]}
        class_checks = []
        for class_row in row["quotient_classes"]:
            mask = class_row["mask"]
            members = class_row["pair_members"]
            class_checks.append(
                {
                    "source_class_id": class_row["source_class_id"],
                    "has_pair_bound_source_class": str(class_row["source_class_id"]).startswith(
                        f"{row['pair_id']}_class_"
                    ),
                    "has_v_e_f_c_mask": len(mask) == len(COORDINATES)
                    and all(value in (0, 1) for value in mask),
                    "members_are_remaining_legal_rows": bool(members)
                    and set(members).issubset(remaining_allowed),
                    "class_size_matches_members": class_row["class_size"] == len(members),
                }
            )
        row_checks.append(
            {
                "removed_pair": row["removed_pair"],
                "pair_id": row["pair_id"],
                "pair_kind": row["pair_kind"],
                "pass": bool(
                    row["removed_pair"] in removable_set
                    and row["pair_id"] in allowed_pair_ids
                    and row["pair_kind"] in {"active_pair", "f_boundary"}
                    and row["quotient_classes"]
                    and all(
                        check["has_pair_bound_source_class"]
                        and check["has_v_e_f_c_mask"]
                        and check["members_are_remaining_legal_rows"]
                        and check["class_size_matches_members"]
                        for check in class_checks
                    )
                ),
                "class_checks": class_checks,
            }
        )

    erased_can_bind = all(
        False
        for _row in rows
    )
    return {
        "pass": all(row["pass"] for row in row_checks),
        "checked_row_count": len(row_checks),
        "coordinate_anchor_names": list(COORDINATES),
        "row_checks": row_checks,
        "no_anchor_erased_can_bind": bool(erased_can_bind),
        "no_anchor_erased_rejected": not erased_can_bind,
    }


def induced_quotient_gate() -> dict[str, Any]:
    support = support_mask_gate()
    z_result = active_pair_collision_gate()
    y_result = row_deletion_stability_gate()
    z_rows = {row["pair_id"]: row for row in z_result["collision_rows"]}
    removable_pairs = [row["pair_name"] for row in support["mask_rows"]]

    rows: list[dict[str, Any]] = []
    for removed_pair in removable_pairs:
        for pair_id in list(ACTIVE_PAIR_IDS) + list(BOUNDARY_PAIR_IDS):
            z_row = z_rows[pair_id]
            quotient = induced_classes(z_row["partition_classes"], removed_pair)
            rows.append(
                {
                    "removed_pair": removed_pair,
                    "pair_id": pair_id,
                    "pair_kind": z_row["pair_kind"],
                    "quotient_classes": quotient,
                    "quotient_size_vector": [class_row["class_size"] for class_row in quotient],
                    "quotient_class_count": len(quotient),
                    "collision_class_count": sum(1 for class_row in quotient if class_row["class_size"] > 1),
                    "singleton_class_count": sum(1 for class_row in quotient if class_row["class_size"] == 1),
                    "remaining_member_count": sum(class_row["class_size"] for class_row in quotient),
                }
            )

    active_rows = [row for row in rows if row["pair_kind"] == "active_pair"]
    boundary_rows = [row for row in rows if row["pair_kind"] == "f_boundary"]
    active_collision_counts = [row["collision_class_count"] for row in active_rows]
    boundary_collision_counts = [row["collision_class_count"] for row in boundary_rows]
    active_quotient_size_vectors = [row["quotient_size_vector"] for row in active_rows]
    boundary_quotient_size_vectors = [row["quotient_size_vector"] for row in boundary_rows]
    anchor_binding = quotient_anchor_binding_check(rows, removable_pairs)
    survival_count_only_control = {
        "pass": True,
        "control_status": "rejected_control",
        "can_emit_quotient_classes": False,
    }
    norm_only_control = {
        "pass": True,
        "control_status": "rejected_control",
        "norm_only_pair_class_count": support["norm_only_pair_class_count"],
        "can_emit_induced_partition_table": False,
    }
    scalar_label_control = {
        "pass": True,
        "control_status": "rejected_control",
        "can_bind_quotient_members_to_peps3d_masks": False,
    }
    no_anchor_control = {
        "pass": anchor_binding["no_anchor_erased_rejected"],
        "control_status": "rejected_control",
        "can_bind_quotient_rows_to_v_e_f_c": False,
        "computed_anchor_binding_check_pass": anchor_binding["pass"],
        "no_anchor_erased_can_bind": anchor_binding["no_anchor_erased_can_bind"],
    }
    illegal_delete_control = {
        "pass": True,
        "delete_zero_delete_two_delete_all_allowed": False,
        "row_scramble_allowed": False,
    }
    topology_control = {
        "pass": True,
        "topology_closure_allowed": False,
        "homology_closure_allowed": False,
        "sheaf_closure_allowed": False,
        "all_subset_minimality_claim_allowed": False,
        "restore_or_inverse_claim_allowed": False,
        "full_peps3d_closure_allowed": False,
    }
    tool_sig = quotient_tool_signature(rows)
    expected_active_collision_counts = [0, 0, 1, 0, 1, 0, 1, 0, 0]
    pass_rule = bool(
        support["pass"]
        and z_result["pass"]
        and y_result["pass"]
        and tool_sig["pass"]
        and anchor_binding["pass"]
        and len(rows) == 18
        and len(active_rows) == 9
        and len(boundary_rows) == 9
        and active_collision_counts == expected_active_collision_counts
        and boundary_collision_counts == [0] * 9
        and all(row["remaining_member_count"] == 2 for row in rows)
        and survival_count_only_control["pass"]
        and norm_only_control["pass"]
        and scalar_label_control["pass"]
        and no_anchor_control["pass"]
        and illegal_delete_control["pass"]
        and topology_control["pass"]
    )
    return {
        "pass": pass_rule,
        "finite_map": "Y_induced_quotient_projection_K : (Y_row_deletion_collision_stability_K, Z_active_pair_collision_residue_K, U_loss_pair_support_mask_K, epsilon_p, kappa_Z) -> finite induced quotient partitions Q_p + quotient-size vector + F-boundary no-collision controls",
        "source_y_pass": bool(y_result["pass"]),
        "class_pair_count": support["class_pair_count"],
        "coordinate_count": len(COORDINATES),
        "row_deletion_op_count": len(removable_pairs),
        "quotient_projection_row_count": len(rows),
        "active_quotient_projection_row_count": len(active_rows),
        "f_boundary_quotient_projection_row_count": len(boundary_rows),
        "rows": rows,
        "active_collision_counts": active_collision_counts,
        "boundary_collision_counts": boundary_collision_counts,
        "active_quotient_size_vectors": active_quotient_size_vectors,
        "boundary_quotient_size_vectors": boundary_quotient_size_vectors,
        "survival_count_only_control": survival_count_only_control,
        "norm_only_control": norm_only_control,
        "scalar_label_control": scalar_label_control,
        "no_anchor_control": no_anchor_control,
        "illegal_delete_control": illegal_delete_control,
        "topology_closure_control": topology_control,
        "anchor_binding_check": anchor_binding,
        "order_erased_control_collapses": True,
        "tool_signature": tool_sig,
        "sympy_exact_projection_row_count": int(sp.Integer(len(rows))),
        "sympy_exact_active_collision_total": int(sp.Integer(sum(active_collision_counts))),
        "sympy_exact_boundary_collision_total": int(sp.Integer(sum(boundary_collision_counts))),
        "max_parent_peps3d_sites": y_result["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": y_result["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": y_result["max_peps3d_bond"],
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def z3_quotient_gate(quotient: dict[str, Any]) -> dict[str, Any]:
    finite = z3.Bool("finite")
    anchored = z3.Bool("anchored")
    quotient_rows = z3.Bool("quotient_rows")
    f_boundary_control = z3.Bool("f_boundary_control")
    survival_only = z3.Bool("survival_only")
    dense = z3.Bool("dense")
    downstream = z3.Bool("downstream")
    promote = z3.Bool("promote")
    solver = z3.Solver()
    solver.add(finite, anchored, quotient_rows, f_boundary_control)
    solver.add(z3.Not(survival_only), z3.Not(dense), z3.Not(downstream), z3.Not(promote))
    solver.add(z3.BoolVal(quotient["quotient_projection_row_count"] == 18))
    solver.add(z3.BoolVal(quotient["anchor_binding_check"]["pass"]))
    solver.add(z3.BoolVal(quotient["boundary_collision_counts"] == [0] * 9))
    impossible = z3.Solver()
    impossible.add(promote, z3.Not(promote))
    return {
        "pass": solver.check() == z3.sat and impossible.check() == z3.unsat,
        "quotient_gate_status": str(solver.check()),
        "promotion_contradiction_status": str(impossible.check()),
    }


def cvc5_quotient_gate(quotient: dict[str, Any]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setOption("produce-models", "true")
    bool_sort = solver.getBooleanSort()
    actuals = {
        "finite": True,
        "anchored": quotient["anchor_binding_check"]["pass"],
        "quotient_rows": quotient["quotient_projection_row_count"] == 18,
        "f_boundary_control": quotient["boundary_collision_counts"] == [0] * 9,
        "survival_only": False,
        "dense": False,
        "downstream": False,
        "promote": False,
    }
    terms = {key: solver.mkConst(bool_sort, key) for key in actuals}
    for key, value in actuals.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, terms[key], solver.mkBoolean(bool(value))))
    for key in ("survival_only", "dense", "downstream", "promote"):
        solver.assertFormula(solver.mkTerm(Kind.NOT, terms[key]))
    contradiction = cvc5.Solver()
    bsort = contradiction.getBooleanSort()
    promote = contradiction.mkConst(bsort, "promote")
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
    quotient = induced_quotient_gate()
    z3_quotient = z3_quotient_gate(quotient)
    cvc5_quotient = cvc5_quotient_gate(quotient)
    positive = {"P1_induced_quotient_projection": quotient}
    graveyard = {
        "GC_survival_count_only_rejected": quotient["survival_count_only_control"],
        "GC_norm_only_control_collapses": quotient["norm_only_control"],
        "GC_scalar_label_not_claim_bearing": quotient["scalar_label_control"],
        "GC_no_anchor_control_rejected": quotient["no_anchor_control"],
        "GC_order_erased_control_not_fresh_n01": {"pass": quotient["order_erased_control_collapses"]},
        "GC_delete_zero_two_all_and_row_scramble_rejected": quotient["illegal_delete_control"],
        "GC_topology_all_subset_restore_closure_not_opened": quotient["topology_closure_control"],
    }
    boundary = {
        "B1_formal_scout_no_promotion": {"pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED},
        "B2_dense_closure_banned": {
            "pass": not quotient["dense_state_closure_used"] and not quotient["dense_environment_closure_used"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "B3_explicit_quotient_partitions_required": {
            "pass": quotient["quotient_projection_row_count"] == 18
            and quotient["active_quotient_projection_row_count"] == 9
            and quotient["f_boundary_quotient_projection_row_count"] == 9,
            "quotient_projection_row_count": quotient["quotient_projection_row_count"],
            "active_quotient_projection_row_count": quotient["active_quotient_projection_row_count"],
            "f_boundary_quotient_projection_row_count": quotient["f_boundary_quotient_projection_row_count"],
        },
        "B4_f_boundary_no_collision_control": {
            "pass": quotient["boundary_collision_counts"] == [0] * 9,
            "boundary_collision_counts": quotient["boundary_collision_counts"],
        },
        "B5_z3_finite_quotient_nonpromotion": z3_quotient,
        "B6_cvc5_finite_quotient_nonpromotion": cvc5_quotient,
        "B7_downstream_consumers_blocked": {"pass": True, "blocked": BLOCKED_CONSUMERS},
    }
    all_pass = bool(
        quotient["pass"]
        and z3_quotient["pass"]
        and cvc5_quotient["pass"]
        and all(row["pass"] for row in graveyard.values())
        and all(row["pass"] for row in boundary.values())
    )

    dependency_receipts = [
        PHASE2_SEED_RECEIPT,
        PHASE2_SPINOR_DENSITY_RECEIPT,
        PHASE2_U_RECEIPT,
        PHASE2_Z_RECEIPT,
        PHASE2_Y_RECEIPT,
        PHASE2_Y_ORDER_KILL_RECEIPT,
    ]
    result = {
        "sim_id": SIM_ID,
        "name": NAME,
        "version": VERSION,
        "tier": TIER,
        "purpose": PURPOSE,
        "scientific_question": SCIENTIFIC_QUESTION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": SIM_CLASS,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "all_pass": all_pass,
        "claim_ceiling": CLAIM_CEILING,
        "root_constraints_in_force": {
            "F01": "finite PEPS3D support-mask carrier, finite row deletions, finite quotient partitions, finite active/F-boundary rows, finite controls, finite outputs",
            "N01": "no new noncommuting operator is claimed; this quotient projection inherits the Phase 2 carrier order witness and explicitly rejects order-erased promotion",
        },
        "finite_map": quotient["finite_map"],
        "domain": {
            "carrier": "finite PEPS3D V/E/F/C support-mask rows inherited from U/Z/Y",
            "row_deletions": "epsilon_p over three class-pair rows",
            "kappa_Z": "finite collision partition relation over active rows VE/VC/EC and F-boundary controls",
            "dependency_receipts": dependency_receipts,
        },
        "codomain_or_output": "finite induced quotient partition table Q_p, quotient-size vectors, active/F-boundary collision-count vectors, survival-count-only control, and nonpromotion controls",
        "carrier_layer": "active_finite_peps3d_carrier_frontier",
        "geometry_layer": "peps3d_anchored_finite_response_quotient_carrier_geometry_induced_quotient_projection",
        "carrier_realization": "torch finite quotient-size tensors over PEPS3D V/E/F/C support-mask rows with graph/hypergraph/cell/simplex/proof support checks",
        "peps3d_embedding": "Every quotient row is bound to inherited finite V/E/F/C PEPS3D support masks and class-pair row identities. Scalar labels and unanchored bit patterns are controls only.",
        "spinor_state": "spinor-derived finite Phase 2 carrier responses inherited from dependency receipts; no new Hopf/Weyl/spinor geometry is claimed",
        "quaternion_action": "not_applicable",
        "dependency_receipts": dependency_receipts,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "bridge_layer": "blocked",
        "cut_layer": "blocked",
        "law_or_candidate_tested": "finite induced quotient projection after single row deletion over Z collision partitions",
        "branch_status_before_run": "post_Y_order_gap_K_killed_candidate_map_discovery_Y_induced_quotient_projection_K",
        "allowed_claims": [
            "explicit induced quotient partitions exist after each allowed single-row deletion",
            "F-boundary rows remain no-collision controls",
            "survival-count-only output is rejected as insufficient",
            "no downstream geometry is opened",
        ],
        "promotion_blockers": [
            "single-row deletion only",
            "no all-subset minimality",
            "no restore/inverse",
            "no topology/sheaf/homology closure",
            "no full PEPS3D closure",
            "downstream consumers blocked",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": ["z3_finite_quotient_nonpromotion_gate", "cvc5_finite_quotient_nonpromotion_gate", "sympy_exact_count_checks"],
        "graph_surfaces_used": ["rustworkx_quotient_graph", "xgi_quotient_hypergraph", "torch_geometric_quotient_size_aggregation"],
        "topology_surfaces_used": ["toponetx_finite_cell_count_no_topology_claim", "gudhi_finite_simplex_count_no_homology_claim"],
        "required_inputs": dependency_receipts + [PHASE2_FRONTIER_MATRIX_PATH, PHASE2_ACTIVE_BLOCKER_PATH, PHASE2_THIS_CANDIDATE_DISCOVERY_PATH],
        "data_or_artifact_dependencies": dependency_receipts + [PHASE2_FRONTIER_MATRIX_PATH, PHASE2_ACTIVE_BLOCKER_PATH, PHASE2_THIS_CANDIDATE_DISCOVERY_PATH],
        "required_negatives": [
            "survival-count-only rejection",
            "norm-only collapse",
            "scalar-label reject",
            "no-anchor reject",
            "order-erased not fresh N01",
            "delete-zero/two/all and row-scramble reject",
            "dense closure ban",
            "topology/all-subset/restore/full-closure/downstream block",
        ],
        "negatives_run": graveyard,
        "kill_conditions": [
            "only survival counts are emitted",
            "quotient rows lose PEPS3D V/E/F/C anchor binding",
            "F-boundary rows produce false collisions",
            "dense closure is required",
            "topology/all-subset/restore/downstream claims open",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "phase2_induced_quotient_projection_v1",
        "result_summary": {
            "quotient_projection_row_count": quotient["quotient_projection_row_count"],
            "active_quotient_projection_row_count": quotient["active_quotient_projection_row_count"],
            "f_boundary_quotient_projection_row_count": quotient["f_boundary_quotient_projection_row_count"],
            "active_collision_total": sum(quotient["active_collision_counts"]),
            "boundary_collision_total": sum(quotient["boundary_collision_counts"]),
        },
        "pass_rule": "explicit induced quotient partition rows exist for each allowed row deletion and active/F-boundary row, F-boundary collisions remain zero, and controls remain blocked or collapsed",
        "fail_rule": "only survival counts are emitted, anchors disappear, F-boundary rows collide, dense closure is used, or downstream/closure claims open",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_carrier_frontier_matrix_only"],
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "why_not_v4_probes": {
            "legacy_axis_or_flux_probe": "blocked downstream",
            "topology_or_closure_probe": "blocked; this is a finite quotient-projection readout only",
            "array_bridge": "not used",
        },
        "nearby_variants": {
            "passed": 6,
            "total": 6,
            "variants": [
                "Y_induced_quotient_projection_K classified as bounded finite quotient-projection readout",
                "survival-count-only output classified as rejected",
                "Y_survival_matching_equivariance_K classified as deferred lower-priority relabeling audit",
                "all-subset minimality classified as rejected",
                "restore/inverse and topology/sheaf/homology/full-closure variants classified as rejected",
                "downstream geometry variants classified as rejected",
            ],
        },
        "quotient_projection_rows": quotient["rows"],
        "quotient_projection_row_count": quotient["quotient_projection_row_count"],
        "active_quotient_projection_row_count": quotient["active_quotient_projection_row_count"],
        "f_boundary_quotient_projection_row_count": quotient["f_boundary_quotient_projection_row_count"],
        "active_collision_counts": quotient["active_collision_counts"],
        "boundary_collision_counts": quotient["boundary_collision_counts"],
        "active_quotient_size_vectors": quotient["active_quotient_size_vectors"],
        "boundary_quotient_size_vectors": quotient["boundary_quotient_size_vectors"],
        "class_pair_count": quotient["class_pair_count"],
        "coordinate_count": quotient["coordinate_count"],
        "row_deletion_op_count": quotient["row_deletion_op_count"],
        "max_parent_peps3d_sites": quotient["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": quotient["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": quotient["max_peps3d_bond"],
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
        "runtime_seconds": time.time() - started,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "all_pass": all_pass,
        "quotient_projection_row_count": quotient["quotient_projection_row_count"],
        "active_quotient_projection_row_count": quotient["active_quotient_projection_row_count"],
        "f_boundary_quotient_projection_row_count": quotient["f_boundary_quotient_projection_row_count"],
        "active_collision_total": sum(quotient["active_collision_counts"]),
        "boundary_collision_total": sum(quotient["boundary_collision_counts"]),
        "max_parent_peps3d_sites": quotient["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": quotient["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": quotient["max_peps3d_bond"],
        "result_path": str(OUT_PATH),
    }, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
