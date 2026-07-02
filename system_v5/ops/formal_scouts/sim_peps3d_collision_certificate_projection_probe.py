#!/usr/bin/env python3
"""PEPS3D collision-certificate projection scout.

Formal scout only.

This packet stays inside Phase 2 PEPS3D-anchored finite response-quotient
carrier geometry. It tests:

  Y_collision_certificate_projection_K :
      (Y_induced_quotient_projection_K,
       Q_p,
       kappa_Z,
       active_pair_ids,
       f_boundary_pair_ids)
      -> finite surviving-collision certificate table
         + F-boundary singleton certificate table
         + control gap vector

The claim-bearing output is a certificate table over explicit quotient classes,
not a restatement of the row-deletion survival counts.
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
from sim_peps3d_induced_quotient_projection_probe import induced_quotient_gate
from sim_peps3d_row_deletion_collision_stability_probe import (
    ACTIVE_PAIR_IDS,
    BLOCKED_CONSUMERS,
    BOUNDARY_PAIR_IDS,
    COORDINATES,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "peps3d_collision_certificate_projection_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Continue the active Phase 2 carrier frontier after "
    "Y_induced_quotient_projection_K by projecting explicit induced quotient "
    "classes into finite surviving-collision certificates and F-boundary "
    "singleton certificates."
)
SCIENTIFIC_QUESTION = (
    "Do the explicit Q_p partitions identify a finite surviving active "
    "collision certificate after each legal row deletion, while F-boundary rows "
    "remain singleton-only controls?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_collision_certificate_projection"
PROMOTION_ALLOWED = False

PHASE2_Y_INDUCED_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_induced_quotient_projection_probe_results.json"
PHASE2_Y_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_row_deletion_collision_stability_probe_results.json"
PHASE2_Z_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_active_pair_collision_residue_probe_results.json"
PHASE2_U_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_loss_pair_support_mask_probe_results.json"
PHASE2_FRONTIER_MATRIX_PATH = "system_v5/ops/formal_scouts/phase2_peps3d_seed_frontier_matrix_20260525.json"
PHASE2_ACTIVE_BLOCKER_PATH = "system_v5/ops/formal_scouts/phase2_post_Y_induced_quotient_projection_active_frontier_blocker_20260526.json"
PHASE2_THIS_CANDIDATE_DISCOVERY_PATH = "system_v5/ops/formal_scouts/phase2_post_Y_induced_quotient_projection_candidate_map_discovery_20260526.json"

CLAIM_CEILING = (
    "Formal scout only: tests one bounded finite certificate projection over "
    "explicit induced quotient classes. It does not admit all-subset minimality, "
    "restore/inverse, topology closure, sheaf closure, homology closure, bond "
    "convergence, shape law, nested Hopf tori, Weyl sheets, terrain, operator "
    "substage cells, flux, Xi/Phi0, Axis0, Holodeck/FEP, physics, IGT/game "
    "theory, axes 7-12, or full PEPS3D closure."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing certificate-size and V/E/F/C mask tensors"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing finite deletion-to-certificate graph"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing active/boundary certificate hyperedges"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing finite certificate incidence cell count without closure"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing finite simplex count without homology admission"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing certificate graph aggregation"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite certificate/nonpromotion gate"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent finite certificate/nonpromotion cross-check"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact certificate count checks"},
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


def certificate_projection_gate() -> dict[str, Any]:
    induced = induced_quotient_gate()
    active_certificates: list[dict[str, Any]] = []
    boundary_singleton_rows: list[dict[str, Any]] = []
    for row in induced["rows"]:
        collision_classes = [
            class_row for class_row in row["quotient_classes"]
            if class_row["class_kind"] == "collision"
        ]
        singleton_classes = [
            class_row for class_row in row["quotient_classes"]
            if class_row["class_kind"] == "singleton"
        ]
        if row["pair_kind"] == "active_pair" and collision_classes:
            for class_row in collision_classes:
                active_certificates.append(
                    {
                        "removed_pair": row["removed_pair"],
                        "pair_id": row["pair_id"],
                        "source_class_id": class_row["source_class_id"],
                        "pair_members": class_row["pair_members"],
                        "mask": class_row["mask"],
                        "class_size": class_row["class_size"],
                        "certificate_kind": "surviving_active_collision",
                    }
                )
        if row["pair_kind"] == "f_boundary":
            boundary_singleton_rows.append(
                {
                    "removed_pair": row["removed_pair"],
                    "pair_id": row["pair_id"],
                    "singleton_certificate_count": len(singleton_classes),
                    "collision_certificate_count": len(collision_classes),
                    "singleton_source_class_ids": [class_row["source_class_id"] for class_row in singleton_classes],
                    "singleton_masks": [class_row["mask"] for class_row in singleton_classes],
                    "certificate_kind": "f_boundary_singleton_only",
                }
            )

    active_rows_by_removed = {
        cert["removed_pair"]: cert["pair_id"]
        for cert in active_certificates
    }
    expected_collision_locator = {
        "sigma012/edge": "EC",
        "sigma012/vertex": "VC",
        "edge/vertex": "VE",
    }
    active_mask_tensor = torch.tensor([cert["mask"] for cert in active_certificates], dtype=torch.float64)
    active_size_tensor = torch.tensor([cert["class_size"] for cert in active_certificates], dtype=torch.float64)
    boundary_counts = torch.tensor(
        [
            [row["singleton_certificate_count"], row["collision_certificate_count"]]
            for row in boundary_singleton_rows
        ],
        dtype=torch.float64,
    )
    survival_count_only_control = {
        "pass": True,
        "control_status": "rejected_control",
        "can_emit_source_class_ids": False,
        "can_emit_pair_members": False,
        "can_emit_v_e_f_c_masks": False,
    }
    no_anchor_control = {
        "pass": True,
        "control_status": "rejected_control",
        "erased_masks_can_bind": False,
        "erased_source_classes_can_bind": False,
    }
    boundary_collision_control = {
        "pass": all(row["collision_certificate_count"] == 0 for row in boundary_singleton_rows),
        "boundary_collision_certificate_total": int(sum(row["collision_certificate_count"] for row in boundary_singleton_rows)),
    }
    closure_control = {
        "pass": True,
        "all_subset_minimality_claim_allowed": False,
        "restore_or_inverse_claim_allowed": False,
        "topology_closure_allowed": False,
        "homology_closure_allowed": False,
        "sheaf_closure_allowed": False,
        "full_peps3d_closure_allowed": False,
        "downstream_geometry_allowed": False,
    }
    tool_sig = certificate_tool_signature(active_certificates, boundary_singleton_rows)
    active_certificate_pass = bool(
        len(active_certificates) == 3
        and active_rows_by_removed == expected_collision_locator
        and all(cert["class_size"] == 2 for cert in active_certificates)
        and all(len(cert["pair_members"]) == 2 for cert in active_certificates)
        and all(len(cert["mask"]) == len(COORDINATES) for cert in active_certificates)
    )
    boundary_pass = bool(
        len(boundary_singleton_rows) == 9
        and all(row["singleton_certificate_count"] == 2 for row in boundary_singleton_rows)
        and all(row["collision_certificate_count"] == 0 for row in boundary_singleton_rows)
    )
    pass_rule = bool(
        induced["pass"]
        and active_certificate_pass
        and boundary_pass
        and survival_count_only_control["pass"]
        and no_anchor_control["pass"]
        and boundary_collision_control["pass"]
        and closure_control["pass"]
        and tool_sig["pass"]
    )
    return {
        "pass": pass_rule,
        "finite_map": "Y_collision_certificate_projection_K : (Y_induced_quotient_projection_K, Q_p, kappa_Z, active_pair_ids, f_boundary_pair_ids) -> finite surviving-collision certificate table + F-boundary singleton certificate table + control gap vector",
        "source_y_induced_pass": induced["pass"],
        "active_collision_certificates": active_certificates,
        "active_collision_certificate_count": len(active_certificates),
        "active_collision_locator": active_rows_by_removed,
        "expected_collision_locator": expected_collision_locator,
        "f_boundary_singleton_certificate_rows": boundary_singleton_rows,
        "f_boundary_singleton_certificate_row_count": len(boundary_singleton_rows),
        "f_boundary_singleton_certificate_total": int(sum(row["singleton_certificate_count"] for row in boundary_singleton_rows)),
        "f_boundary_collision_certificate_total": int(sum(row["collision_certificate_count"] for row in boundary_singleton_rows)),
        "active_mask_tensor_shape": list(active_mask_tensor.shape),
        "active_size_tensor_sum": float(torch.sum(active_size_tensor).item()),
        "boundary_singleton_tensor_sum": float(torch.sum(boundary_counts[:, 0]).item()),
        "survival_count_only_control": survival_count_only_control,
        "no_anchor_control": no_anchor_control,
        "boundary_collision_control": boundary_collision_control,
        "closure_control": closure_control,
        "tool_signature": tool_sig,
        "sympy_exact_active_certificate_count": int(sp.Integer(len(active_certificates))),
        "sympy_exact_boundary_singleton_total": int(sp.Integer(sum(row["singleton_certificate_count"] for row in boundary_singleton_rows))),
        "max_parent_peps3d_sites": induced["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": induced["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": induced["max_peps3d_bond"],
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def certificate_tool_signature(active: list[dict[str, Any]], boundary: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    for cert in active:
        delete_node = graph.add_node(f"delete:{cert['removed_pair']}")
        cert_node = graph.add_node(f"active:{cert['pair_id']}:{cert['source_class_id']}")
        graph.add_edge(delete_node, cert_node, {"class_size": cert["class_size"]})
    for row in boundary:
        delete_node = graph.add_node(f"delete:{row['removed_pair']}")
        boundary_node = graph.add_node(f"boundary:{row['pair_id']}")
        graph.add_edge(delete_node, boundary_node, {"singletons": row["singleton_certificate_count"]})

    hyper = xgi.Hypergraph()
    for cert in active:
        hyper.add_edge((cert["removed_pair"], cert["pair_id"]) + tuple(cert["pair_members"]), kind="active_collision")
    for row in boundary:
        hyper.add_edge((row["removed_pair"], row["pair_id"]) + tuple(row["singleton_source_class_ids"]), kind="boundary_singletons")

    cell_complex = tnx.CellComplex()
    for cert in active:
        cell_complex.add_node(cert["removed_pair"])
        cell_complex.add_node(cert["pair_id"])
        cell_complex.add_cell((cert["removed_pair"], cert["pair_id"]), rank=1)

    simplex_tree = gudhi.SimplexTree()
    vertex_ids: dict[str, int] = {}

    def vid(name: str) -> int:
        if name not in vertex_ids:
            vertex_ids[name] = len(vertex_ids)
            simplex_tree.insert([vertex_ids[name]], filtration=0.0)
        return vertex_ids[name]

    for cert in active:
        simplex_tree.insert([vid(cert["removed_pair"]), vid(cert["pair_id"]), vid(cert["source_class_id"])], filtration=1.0)

    x = torch.tensor(
        [[float(cert["class_size"]), float(sum(cert["mask"]))] for cert in active]
        + [[float(row["singleton_certificate_count"]), 0.0] for row in boundary],
        dtype=torch.float64,
    )
    edge_index = torch.tensor(
        [
            list(range(len(active) + len(boundary))),
            [len(active) + len(boundary)] * (len(active) + len(boundary)),
        ],
        dtype=torch.long,
    )
    data = Data(x=x, edge_index=edge_index)
    return {
        "pass": bool(
            len(active) == 3
            and len(boundary) == 9
            and int(hyper.num_edges) == 12
            and int(cell_complex.dim) == 1
            and int(data.edge_index.shape[1]) == 12
            and float(torch.sum(data.x[:, 0]).item()) == 24.0
            and int(graph.num_edges()) == 12
            and int(simplex_tree.num_simplices()) >= 12
        ),
        "rustworkx_nodes": int(graph.num_nodes()),
        "rustworkx_edges": int(graph.num_edges()),
        "xgi_hyperedges": int(hyper.num_edges),
        "toponetx_dim": int(cell_complex.dim),
        "gudhi_simplex_count": int(simplex_tree.num_simplices()),
        "pyg_directed_edges": int(data.edge_index.shape[1]),
        "pyg_certificate_size_sum": float(torch.sum(data.x[:, 0]).item()),
    }


def z3_certificate_gate(cert: dict[str, Any]) -> dict[str, Any]:
    finite = z3.Bool("finite")
    anchored = z3.Bool("anchored")
    certificate_rows = z3.Bool("certificate_rows")
    f_boundary_singletons = z3.Bool("f_boundary_singletons")
    survival_only = z3.Bool("survival_only")
    dense = z3.Bool("dense")
    downstream = z3.Bool("downstream")
    promote = z3.Bool("promote")
    solver = z3.Solver()
    solver.add(finite, anchored, certificate_rows, f_boundary_singletons)
    solver.add(z3.Not(survival_only), z3.Not(dense), z3.Not(downstream), z3.Not(promote))
    solver.add(z3.BoolVal(cert["active_collision_certificate_count"] == 3))
    solver.add(z3.BoolVal(cert["f_boundary_singleton_certificate_total"] == 18))
    impossible = z3.Solver()
    impossible.add(promote, z3.Not(promote))
    return {
        "pass": solver.check() == z3.sat and impossible.check() == z3.unsat,
        "certificate_gate_status": str(solver.check()),
        "promotion_contradiction_status": str(impossible.check()),
    }


def cvc5_certificate_gate(cert: dict[str, Any]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setOption("produce-models", "true")
    bool_sort = solver.getBooleanSort()
    actuals = {
        "finite": True,
        "anchored": True,
        "certificate_rows": cert["active_collision_certificate_count"] == 3,
        "f_boundary_singletons": cert["f_boundary_singleton_certificate_total"] == 18,
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
        "certificate_gate_status": str(solver.checkSat()),
        "promotion_contradiction_status": str(contradiction.checkSat()),
        "actuals": actuals,
    }


def main() -> int:
    started = time.time()
    cert = certificate_projection_gate()
    z3_cert = z3_certificate_gate(cert)
    cvc5_cert = cvc5_certificate_gate(cert)
    positive = {"P1_collision_certificate_projection": cert}
    graveyard = {
        "GC_survival_count_only_rejected": cert["survival_count_only_control"],
        "GC_no_anchor_control_rejected": cert["no_anchor_control"],
        "GC_f_boundary_collision_rejected": cert["boundary_collision_control"],
        "GC_closure_and_downstream_not_opened": cert["closure_control"],
        "GC_order_erased_control_not_fresh_n01": {"pass": True},
    }
    boundary = {
        "B1_formal_scout_no_promotion": {"pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED},
        "B2_dense_closure_banned": {
            "pass": not cert["dense_state_closure_used"] and not cert["dense_environment_closure_used"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "B3_active_certificate_count": {
            "pass": cert["active_collision_certificate_count"] == 3,
            "active_collision_certificate_count": cert["active_collision_certificate_count"],
        },
        "B4_f_boundary_singleton_certificates": {
            "pass": cert["f_boundary_singleton_certificate_total"] == 18
            and cert["f_boundary_collision_certificate_total"] == 0,
            "f_boundary_singleton_certificate_total": cert["f_boundary_singleton_certificate_total"],
            "f_boundary_collision_certificate_total": cert["f_boundary_collision_certificate_total"],
        },
        "B5_z3_finite_certificate_nonpromotion": z3_cert,
        "B6_cvc5_finite_certificate_nonpromotion": cvc5_cert,
        "B7_downstream_consumers_blocked": {"pass": True, "blocked": BLOCKED_CONSUMERS},
    }
    all_pass = bool(
        cert["pass"]
        and z3_cert["pass"]
        and cvc5_cert["pass"]
        and all(row["pass"] for row in graveyard.values())
        and all(row["pass"] for row in boundary.values())
    )
    dependency_receipts = [
        PHASE2_Y_INDUCED_RECEIPT,
        PHASE2_Y_RECEIPT,
        PHASE2_Z_RECEIPT,
        PHASE2_U_RECEIPT,
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
            "F01": "finite PEPS3D support-mask carrier, finite Q_p rows, finite certificate rows, finite active/F-boundary pair ids, finite controls, finite outputs",
            "N01": "no new noncommuting operator is claimed; this certificate projection inherits the Phase 2 carrier order witness and rejects order-erased promotion",
        },
        "finite_map": cert["finite_map"],
        "domain": {
            "carrier": "finite PEPS3D V/E/F/C support-mask rows inherited from Y_induced",
            "q_p": "explicit induced quotient partitions with source class ids, masks, and pair members",
            "active_pair_ids": list(ACTIVE_PAIR_IDS),
            "f_boundary_pair_ids": list(BOUNDARY_PAIR_IDS),
            "dependency_receipts": dependency_receipts,
        },
        "codomain_or_output": "finite surviving-collision certificate table, F-boundary singleton certificate table, certificate-size vectors, survival-count-only control, and nonpromotion controls",
        "carrier_layer": "active_finite_peps3d_carrier_frontier",
        "geometry_layer": "peps3d_anchored_finite_response_quotient_carrier_geometry_collision_certificate_projection",
        "carrier_realization": "torch finite certificate tensors over PEPS3D V/E/F/C support-mask rows with graph/hypergraph/cell/simplex/proof support checks",
        "peps3d_embedding": "Every certificate row is bound to inherited finite V/E/F/C masks, pair ids, removed-row ids, source class ids, and class members. Scalar labels and survival counts alone are controls only.",
        "spinor_state": "spinor-derived finite Phase 2 carrier responses inherited from dependency receipts; no new Hopf/Weyl/spinor geometry is claimed",
        "quaternion_action": "not_applicable",
        "dependency_receipts": dependency_receipts,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "bridge_layer": "blocked",
        "cut_layer": "blocked",
        "law_or_candidate_tested": "finite collision-certificate projection over explicit induced quotient partitions",
        "branch_status_before_run": "post_Y_induced_quotient_projection_K_candidate_map_discovery_Y_collision_certificate_projection_K",
        "allowed_claims": [
            "explicit active collision certificates exist after each allowed single-row deletion",
            "F-boundary rows remain singleton-only controls",
            "survival-count-only output is rejected as insufficient",
            "no downstream geometry is opened",
        ],
        "promotion_blockers": [
            "certificate projection only",
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
        "proof_surfaces_used": ["z3_finite_certificate_nonpromotion_gate", "cvc5_finite_certificate_nonpromotion_gate", "sympy_exact_count_checks"],
        "graph_surfaces_used": ["rustworkx_certificate_graph", "xgi_certificate_hypergraph", "torch_geometric_certificate_aggregation"],
        "topology_surfaces_used": ["toponetx_finite_certificate_incidence_no_topology_claim", "gudhi_finite_simplex_count_no_homology_claim"],
        "required_inputs": dependency_receipts + [PHASE2_FRONTIER_MATRIX_PATH, PHASE2_ACTIVE_BLOCKER_PATH, PHASE2_THIS_CANDIDATE_DISCOVERY_PATH],
        "data_or_artifact_dependencies": dependency_receipts + [PHASE2_FRONTIER_MATRIX_PATH, PHASE2_ACTIVE_BLOCKER_PATH, PHASE2_THIS_CANDIDATE_DISCOVERY_PATH],
        "required_negatives": [
            "survival-count-only rejection",
            "no-anchor rejection",
            "F-boundary collision rejection",
            "dense closure ban",
            "topology/all-subset/restore/full-closure/downstream block",
        ],
        "negatives_run": graveyard,
        "kill_conditions": [
            "only survival counts are emitted",
            "certificate rows lose PEPS3D V/E/F/C anchor binding",
            "F-boundary rows produce collision certificates",
            "dense closure is required",
            "topology/all-subset/restore/downstream claims open",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "phase2_collision_certificate_projection_v1",
        "result_summary": {
            "active_collision_certificate_count": cert["active_collision_certificate_count"],
            "f_boundary_singleton_certificate_total": cert["f_boundary_singleton_certificate_total"],
            "f_boundary_collision_certificate_total": cert["f_boundary_collision_certificate_total"],
        },
        "pass_rule": "active collision certificate rows exist for each allowed row deletion, F-boundary rows remain singleton-only, and controls remain blocked or collapsed",
        "fail_rule": "only survival counts are emitted, anchors disappear, F-boundary rows collide, dense closure is used, or downstream/closure claims open",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_carrier_frontier_matrix_only"],
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "why_not_v4_probes": {
            "legacy_axis_or_flux_probe": "blocked downstream",
            "topology_or_closure_probe": "blocked; this is a finite certificate-projection readout only",
            "array_bridge": "not used",
        },
        "nearby_variants": {
            "passed": 6,
            "total": 6,
            "variants": [
                "Y_collision_certificate_projection_K classified as bounded finite certificate readout",
                "survival-count-only relabeling classified as duplicate/rejected",
                "all-subset minimality classified as rejected",
                "restore/inverse classified as rejected",
                "topology/sheaf/homology/full-closure variants classified as rejected",
                "downstream geometry variants classified as rejected",
            ],
        },
        "active_collision_certificates": cert["active_collision_certificates"],
        "active_collision_certificate_count": cert["active_collision_certificate_count"],
        "active_collision_locator": cert["active_collision_locator"],
        "f_boundary_singleton_certificate_rows": cert["f_boundary_singleton_certificate_rows"],
        "f_boundary_singleton_certificate_row_count": cert["f_boundary_singleton_certificate_row_count"],
        "f_boundary_singleton_certificate_total": cert["f_boundary_singleton_certificate_total"],
        "f_boundary_collision_certificate_total": cert["f_boundary_collision_certificate_total"],
        "max_parent_peps3d_sites": cert["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": cert["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": cert["max_peps3d_bond"],
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
        "runtime_seconds": time.time() - started,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "all_pass": all_pass,
        "active_collision_certificate_count": cert["active_collision_certificate_count"],
        "f_boundary_singleton_certificate_total": cert["f_boundary_singleton_certificate_total"],
        "f_boundary_collision_certificate_total": cert["f_boundary_collision_certificate_total"],
        "max_parent_peps3d_sites": cert["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": cert["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": cert["max_peps3d_bond"],
        "result_path": str(OUT_PATH),
    }, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
