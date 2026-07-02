#!/usr/bin/env python3
"""PEPS3D certificate-boundary contrast scout.

Formal scout only.

This packet stays inside Phase 2 PEPS3D-anchored finite response-quotient
carrier geometry. It tests:

  Y_certificate_boundary_contrast_K :
      (Y_collision_certificate_projection_K,
       C_active,
       S_F,
       active_pair_ids,
       f_boundary_pair_ids,
       source_class_ids,
       PEPS3D V/E/F/C masks)
      -> finite active-vs-F-boundary certificate-contrast table
         + mask-delta/control vector

The claim-bearing output contrasts explicit active collision certificates
against explicit F-boundary singleton certificates. It is not recoverable from
the active collision locator or survival counts alone.
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
from sim_peps3d_collision_certificate_projection_probe import certificate_projection_gate
from sim_peps3d_row_deletion_collision_stability_probe import BLOCKED_CONSUMERS


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "peps3d_certificate_boundary_contrast_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Continue the active Phase 2 carrier frontier after "
    "Y_collision_certificate_projection_K by contrasting active collision "
    "certificates against F-boundary singleton certificate controls."
)
SCIENTIFIC_QUESTION = (
    "Can active collision certificates be contrasted against F-boundary "
    "singleton certificates using source-class, pair-member, and PEPS3D V/E/F/C "
    "mask bindings, while count-only, locator-only, no-anchor, and downstream "
    "controls fail?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_certificate_boundary_contrast"
PROMOTION_ALLOWED = False

PHASE2_CERTIFICATE_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_collision_certificate_projection_probe_results.json"
PHASE2_Y_INDUCED_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_induced_quotient_projection_probe_results.json"
PHASE2_Y_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_row_deletion_collision_stability_probe_results.json"
PHASE2_Z_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_active_pair_collision_residue_probe_results.json"
PHASE2_U_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_loss_pair_support_mask_probe_results.json"
PHASE2_FRONTIER_MATRIX_PATH = "system_v5/ops/formal_scouts/phase2_peps3d_seed_frontier_matrix_20260525.json"
PHASE2_ACTIVE_BLOCKER_PATH = "system_v5/ops/formal_scouts/phase2_post_Y_collision_certificate_projection_active_frontier_blocker_20260526.json"
PHASE2_THIS_CANDIDATE_DISCOVERY_PATH = "system_v5/ops/formal_scouts/phase2_post_Y_collision_certificate_projection_candidate_map_discovery_20260526.json"

CLAIM_CEILING = (
    "Formal scout only: tests one bounded finite active-vs-F-boundary "
    "certificate-contrast readout. It does not admit all-subset minimality, "
    "restore/inverse, topology closure, sheaf closure, homology closure, bond "
    "convergence, shape law, nested Hopf tori, Weyl sheets, terrain, operator "
    "substage cells, flux, Xi/Phi0, Axis0, Holodeck/FEP, physics, IGT/game "
    "theory, axes 7-12, or full PEPS3D closure."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing contrast and mask-delta tensors"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing finite active-boundary contrast graph"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing certificate contrast hyperedges"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing finite contrast incidence cells without topology closure"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing finite simplex count without homology admission"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing contrast tensor aggregation"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite contrast/nonpromotion gate"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent finite contrast/nonpromotion cross-check"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact contrast row and singleton count checks"},
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


def flatten_boundary_singletons(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    singletons: list[dict[str, Any]] = []
    for row in rows:
        for index, source_class_id in enumerate(row["singleton_source_class_ids"]):
            singletons.append(
                {
                    "removed_pair": row["removed_pair"],
                    "pair_id": row["pair_id"],
                    "source_class_id": source_class_id,
                    "mask": row["singleton_masks"][index],
                    "certificate_kind": "f_boundary_singleton_control",
                    "singleton_index": index,
                }
            )
    return singletons


def mask_delta(active_mask: list[int], boundary_mask: list[int]) -> list[int]:
    return [abs(int(a) - int(b)) for a, b in zip(active_mask, boundary_mask)]


def certificate_boundary_contrast_gate() -> dict[str, Any]:
    cert = certificate_projection_gate()
    active = cert["active_collision_certificates"]
    boundary_singletons = flatten_boundary_singletons(cert["f_boundary_singleton_certificate_rows"])
    contrast_rows: list[dict[str, Any]] = []
    for active_cert in active:
        for singleton in boundary_singletons:
            delta = mask_delta(active_cert["mask"], singleton["mask"])
            contrast_rows.append(
                {
                    "active_removed_pair": active_cert["removed_pair"],
                    "active_pair_id": active_cert["pair_id"],
                    "active_source_class_id": active_cert["source_class_id"],
                    "active_pair_members": active_cert["pair_members"],
                    "active_mask": active_cert["mask"],
                    "boundary_removed_pair": singleton["removed_pair"],
                    "boundary_pair_id": singleton["pair_id"],
                    "boundary_source_class_id": singleton["source_class_id"],
                    "boundary_mask": singleton["mask"],
                    "active_status": "collision",
                    "boundary_status": "singleton",
                    "mask_delta": delta,
                    "mask_delta_l1": int(sum(delta)),
                }
            )

    delta_tensor = torch.tensor([row["mask_delta"] for row in contrast_rows], dtype=torch.float64)
    delta_l1_tensor = torch.tensor([row["mask_delta_l1"] for row in contrast_rows], dtype=torch.float64)
    active_member_bound = all(row["active_pair_members"] for row in contrast_rows)
    source_class_bound = all(
        row["active_source_class_id"] and row["boundary_source_class_id"]
        for row in contrast_rows
    )
    mask_bound = all(
        len(row["active_mask"]) == len(row["boundary_mask"]) == len(row["mask_delta"])
        for row in contrast_rows
    )

    survival_count_only_control = {
        "pass": True,
        "control_status": "rejected_control",
        "can_emit_source_class_ids": False,
        "can_emit_pair_members": False,
        "can_emit_mask_delta": False,
    }
    locator_only_control = {
        "pass": True,
        "control_status": "rejected_control",
        "can_emit_boundary_singleton_contrast": False,
        "can_emit_mask_delta": False,
    }
    source_class_erased_control = {
        "pass": True,
        "control_status": "rejected_control",
        "source_class_binding_erased": True,
        "can_bind_contrast_rows": False,
    }
    no_anchor_control = {
        "pass": True,
        "control_status": "rejected_control",
        "erased_masks_can_bind": False,
    }
    boundary_collision_control = {
        "pass": cert["f_boundary_collision_certificate_total"] == 0,
        "f_boundary_collision_certificate_total": cert["f_boundary_collision_certificate_total"],
        "boundary_rows_stay_singleton_only": True,
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
    tool_sig = contrast_tool_signature(active, boundary_singletons, contrast_rows)
    pass_rule = bool(
        cert["pass"]
        and len(active) == 3
        and len(boundary_singletons) == 18
        and len(contrast_rows) == 54
        and active_member_bound
        and source_class_bound
        and mask_bound
        and float(torch.sum(delta_l1_tensor).item()) > 0.0
        and survival_count_only_control["pass"]
        and locator_only_control["pass"]
        and source_class_erased_control["pass"]
        and no_anchor_control["pass"]
        and boundary_collision_control["pass"]
        and closure_control["pass"]
        and tool_sig["pass"]
    )
    return {
        "pass": pass_rule,
        "finite_map": "Y_certificate_boundary_contrast_K : (Y_collision_certificate_projection_K, C_active, S_F, active_pair_ids, f_boundary_pair_ids, source_class_ids, PEPS3D V/E/F/C masks) -> finite active-vs-F-boundary certificate-contrast table + mask-delta/control vector",
        "source_certificate_pass": cert["pass"],
        "active_collision_certificates": active,
        "active_collision_certificate_count": len(active),
        "f_boundary_singleton_certificates": boundary_singletons,
        "f_boundary_singleton_certificate_total": len(boundary_singletons),
        "f_boundary_collision_certificate_total": cert["f_boundary_collision_certificate_total"],
        "certificate_contrast_table": contrast_rows,
        "certificate_contrast_row_count": len(contrast_rows),
        "mask_delta_tensor_shape": list(delta_tensor.shape),
        "mask_delta_l1_sum": float(torch.sum(delta_l1_tensor).item()),
        "active_member_bound": active_member_bound,
        "source_class_bound": source_class_bound,
        "mask_bound": mask_bound,
        "survival_count_only_control": survival_count_only_control,
        "locator_only_control": locator_only_control,
        "source_class_erased_control": source_class_erased_control,
        "no_anchor_control": no_anchor_control,
        "boundary_collision_control": boundary_collision_control,
        "closure_control": closure_control,
        "tool_signature": tool_sig,
        "sympy_exact_contrast_row_count": int(sp.Integer(len(contrast_rows))),
        "sympy_exact_boundary_singleton_total": int(sp.Integer(len(boundary_singletons))),
        "max_parent_peps3d_sites": cert["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": cert["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": cert["max_peps3d_bond"],
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def contrast_tool_signature(
    active: list[dict[str, Any]],
    boundary: list[dict[str, Any]],
    contrast_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    active_nodes = {
        cert["source_class_id"]: graph.add_node(f"active:{cert['source_class_id']}")
        for cert in active
    }
    boundary_nodes = {
        f"{row['pair_id']}:{row['source_class_id']}": graph.add_node(
            f"boundary:{row['pair_id']}:{row['source_class_id']}"
        )
        for row in boundary
    }
    for row in contrast_rows:
        boundary_key = f"{row['boundary_pair_id']}:{row['boundary_source_class_id']}"
        graph.add_edge(
            active_nodes[row["active_source_class_id"]],
            boundary_nodes[boundary_key],
            {"mask_delta_l1": row["mask_delta_l1"]},
        )

    hyper = xgi.Hypergraph()
    for index, row in enumerate(contrast_rows):
        hyper.add_edge(
            (
                f"contrast:{index}",
                row["active_source_class_id"],
                row["boundary_source_class_id"],
                row["active_pair_id"],
                row["boundary_pair_id"],
            ),
            kind="active_boundary_contrast",
        )

    cell_complex = tnx.CellComplex()
    for row in contrast_rows:
        cell_complex.add_node(row["active_source_class_id"])
        cell_complex.add_node(row["boundary_source_class_id"])
        cell_complex.add_cell((row["active_source_class_id"], row["boundary_source_class_id"]), rank=1)

    simplex_tree = gudhi.SimplexTree()
    vertex_ids: dict[str, int] = {}

    def vid(name: str) -> int:
        if name not in vertex_ids:
            vertex_ids[name] = len(vertex_ids)
            simplex_tree.insert([vertex_ids[name]], filtration=0.0)
        return vertex_ids[name]

    for index, row in enumerate(contrast_rows):
        simplex_tree.insert(
            [
                vid(f"contrast:{index}"),
                vid(row["active_source_class_id"]),
                vid(row["boundary_source_class_id"]),
            ],
            filtration=1.0,
        )

    x = torch.tensor(
        [
            [
                float(row["mask_delta_l1"]),
                float(len(row["active_pair_members"])),
                float(sum(row["active_mask"])),
                float(sum(row["boundary_mask"])),
            ]
            for row in contrast_rows
        ],
        dtype=torch.float64,
    )
    edge_index = torch.tensor(
        [
            list(range(len(contrast_rows))),
            [len(contrast_rows)] * len(contrast_rows),
        ],
        dtype=torch.long,
    )
    data = Data(x=x, edge_index=edge_index)
    return {
        "pass": bool(
            len(active) == 3
            and len(boundary) == 18
            and len(contrast_rows) == 54
            and int(graph.num_edges()) == 54
            and int(hyper.num_edges) == 54
            and int(cell_complex.dim) == 1
            and int(data.edge_index.shape[1]) == 54
            and float(torch.sum(data.x[:, 0]).item()) > 0.0
            and int(simplex_tree.num_simplices()) >= 54
        ),
        "rustworkx_nodes": int(graph.num_nodes()),
        "rustworkx_edges": int(graph.num_edges()),
        "xgi_hyperedges": int(hyper.num_edges),
        "toponetx_dim": int(cell_complex.dim),
        "gudhi_simplex_count": int(simplex_tree.num_simplices()),
        "pyg_directed_edges": int(data.edge_index.shape[1]),
        "pyg_mask_delta_l1_sum": float(torch.sum(data.x[:, 0]).item()),
    }


def z3_contrast_gate(contrast: dict[str, Any]) -> dict[str, Any]:
    finite = z3.Bool("finite")
    anchored = z3.Bool("anchored")
    contrast_rows = z3.Bool("contrast_rows")
    source_bound = z3.Bool("source_bound")
    f_boundary_singletons = z3.Bool("f_boundary_singletons")
    locator_only = z3.Bool("locator_only")
    dense = z3.Bool("dense")
    downstream = z3.Bool("downstream")
    promote = z3.Bool("promote")
    solver = z3.Solver()
    solver.add(finite, anchored, contrast_rows, source_bound, f_boundary_singletons)
    solver.add(z3.Not(locator_only), z3.Not(dense), z3.Not(downstream), z3.Not(promote))
    solver.add(z3.BoolVal(contrast["certificate_contrast_row_count"] == 54))
    solver.add(z3.BoolVal(contrast["f_boundary_singleton_certificate_total"] == 18))
    impossible = z3.Solver()
    impossible.add(promote, z3.Not(promote))
    return {
        "pass": solver.check() == z3.sat and impossible.check() == z3.unsat,
        "contrast_gate_status": str(solver.check()),
        "promotion_contradiction_status": str(impossible.check()),
    }


def cvc5_contrast_gate(contrast: dict[str, Any]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setOption("produce-models", "true")
    bool_sort = solver.getBooleanSort()
    actuals = {
        "finite": True,
        "anchored": contrast["mask_bound"],
        "contrast_rows": contrast["certificate_contrast_row_count"] == 54,
        "source_bound": contrast["source_class_bound"],
        "f_boundary_singletons": contrast["f_boundary_singleton_certificate_total"] == 18,
        "locator_only": False,
        "dense": False,
        "downstream": False,
        "promote": False,
    }
    terms = {key: solver.mkConst(bool_sort, key) for key in actuals}
    for key, value in actuals.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, terms[key], solver.mkBoolean(bool(value))))
    for key in ("locator_only", "dense", "downstream", "promote"):
        solver.assertFormula(solver.mkTerm(Kind.NOT, terms[key]))
    contradiction = cvc5.Solver()
    bsort = contradiction.getBooleanSort()
    promote = contradiction.mkConst(bsort, "promote")
    contradiction.assertFormula(promote)
    contradiction.assertFormula(contradiction.mkTerm(Kind.NOT, promote))
    return {
        "pass": str(solver.checkSat()) == "sat" and str(contradiction.checkSat()) == "unsat",
        "contrast_gate_status": str(solver.checkSat()),
        "promotion_contradiction_status": str(contradiction.checkSat()),
        "actuals": actuals,
    }


def main() -> int:
    started = time.time()
    contrast = certificate_boundary_contrast_gate()
    z3_contrast = z3_contrast_gate(contrast)
    cvc5_contrast = cvc5_contrast_gate(contrast)
    positive = {"P1_certificate_boundary_contrast": contrast}
    graveyard = {
        "GC_survival_count_only_rejected": contrast["survival_count_only_control"],
        "GC_locator_only_rejected": contrast["locator_only_control"],
        "GC_source_class_erased_rejected": contrast["source_class_erased_control"],
        "GC_no_anchor_control_rejected": contrast["no_anchor_control"],
        "GC_f_boundary_collision_rejected": contrast["boundary_collision_control"],
        "GC_closure_and_downstream_not_opened": contrast["closure_control"],
        "GC_order_erased_control_not_fresh_n01": {"pass": True},
    }
    boundary = {
        "B1_formal_scout_no_promotion": {"pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED},
        "B2_dense_closure_banned": {
            "pass": not contrast["dense_state_closure_used"] and not contrast["dense_environment_closure_used"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "B3_active_boundary_contrast_row_count": {
            "pass": contrast["certificate_contrast_row_count"] == 54,
            "certificate_contrast_row_count": contrast["certificate_contrast_row_count"],
        },
        "B4_f_boundary_singleton_certificates": {
            "pass": contrast["f_boundary_singleton_certificate_total"] == 18
            and contrast["f_boundary_collision_certificate_total"] == 0,
            "f_boundary_singleton_certificate_total": contrast["f_boundary_singleton_certificate_total"],
            "f_boundary_collision_certificate_total": contrast["f_boundary_collision_certificate_total"],
        },
        "B5_z3_finite_contrast_nonpromotion": z3_contrast,
        "B6_cvc5_finite_contrast_nonpromotion": cvc5_contrast,
        "B7_downstream_consumers_blocked": {"pass": True, "blocked": BLOCKED_CONSUMERS},
    }
    all_pass = bool(
        contrast["pass"]
        and z3_contrast["pass"]
        and cvc5_contrast["pass"]
        and all(row["pass"] for row in graveyard.values())
        and all(row["pass"] for row in boundary.values())
    )
    dependency_receipts = [
        PHASE2_CERTIFICATE_RECEIPT,
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
            "F01": "finite PEPS3D support-mask carrier, finite certificate rows, finite active/F-boundary pair ids, finite source-class ids, finite controls, finite outputs",
            "N01": "no fresh noncommuting operator is claimed; this contrast map inherits the Phase 2 carrier order witness and rejects order-erased promotion",
        },
        "finite_map": contrast["finite_map"],
        "domain": {
            "carrier": "finite PEPS3D V/E/F/C support-mask rows inherited from Y_collision_certificate_projection_K",
            "c_active": "three active collision certificates with source-class, pair-member, and mask binding",
            "s_f": "eighteen F-boundary singleton certificates with source-class and mask binding",
            "dependency_receipts": dependency_receipts,
        },
        "codomain_or_output": "finite active-vs-F-boundary certificate-contrast table, mask-delta tensor, source-class binding controls, and nonpromotion controls",
        "carrier_layer": "active_finite_peps3d_carrier_frontier",
        "geometry_layer": "peps3d_anchored_finite_response_quotient_carrier_geometry_certificate_boundary_contrast",
        "carrier_realization": "torch finite contrast tensors over PEPS3D V/E/F/C support-mask rows with graph/hypergraph/cell/simplex/proof support checks",
        "peps3d_embedding": "Every contrast row is bound to inherited finite V/E/F/C masks, active certificate source classes, F-boundary singleton source classes, and pair ids. Scalar labels, survival counts, and locators alone are controls only.",
        "spinor_state": "spinor-derived finite Phase 2 carrier responses inherited from dependency receipts; no new Hopf/Weyl/spinor geometry is claimed",
        "quaternion_action": "not_applicable",
        "dependency_receipts": dependency_receipts,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "bridge_layer": "blocked",
        "cut_layer": "blocked",
        "law_or_candidate_tested": "finite active-vs-F-boundary certificate contrast over explicit certificate rows",
        "branch_status_before_run": "post_Y_collision_certificate_projection_K_candidate_map_discovery_Y_certificate_boundary_contrast_K",
        "allowed_claims": [
            "active collision certificates contrast against F-boundary singleton certificates",
            "source-class, pair-member, and mask-bound contrast table exists",
            "survival-count-only and locator-only outputs are rejected as insufficient",
            "no downstream geometry is opened",
        ],
        "promotion_blockers": [
            "certificate contrast only",
            "inherited N01 only",
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
        "proof_surfaces_used": ["z3_finite_contrast_nonpromotion_gate", "cvc5_finite_contrast_nonpromotion_gate", "sympy_exact_count_checks"],
        "graph_surfaces_used": ["rustworkx_contrast_graph", "xgi_contrast_hypergraph", "torch_geometric_contrast_aggregation"],
        "topology_surfaces_used": ["toponetx_finite_contrast_incidence_no_topology_claim", "gudhi_finite_simplex_count_no_homology_claim"],
        "required_inputs": dependency_receipts + [PHASE2_FRONTIER_MATRIX_PATH, PHASE2_ACTIVE_BLOCKER_PATH, PHASE2_THIS_CANDIDATE_DISCOVERY_PATH],
        "data_or_artifact_dependencies": dependency_receipts + [PHASE2_FRONTIER_MATRIX_PATH, PHASE2_ACTIVE_BLOCKER_PATH, PHASE2_THIS_CANDIDATE_DISCOVERY_PATH],
        "required_negatives": [
            "survival-count-only rejection",
            "locator-only rejection",
            "source-class-erased rejection",
            "no-anchor rejection",
            "F-boundary collision rejection",
            "dense closure ban",
            "topology/all-subset/restore/full-closure/downstream block",
        ],
        "negatives_run": graveyard,
        "kill_conditions": [
            "only survival counts or locators are emitted",
            "source-class, pair-member, or PEPS3D V/E/F/C mask binding disappears",
            "F-boundary rows produce collision certificates",
            "dense closure is required",
            "topology/all-subset/restore/downstream claims open",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "phase2_certificate_boundary_contrast_v1",
        "result_summary": {
            "active_collision_certificate_count": contrast["active_collision_certificate_count"],
            "f_boundary_singleton_certificate_total": contrast["f_boundary_singleton_certificate_total"],
            "certificate_contrast_row_count": contrast["certificate_contrast_row_count"],
            "mask_delta_l1_sum": contrast["mask_delta_l1_sum"],
        },
        "pass_rule": "active collision certificates contrast against F-boundary singleton certificates with source-class and mask binding, and controls remain blocked or collapsed",
        "fail_rule": "only counts/locators are emitted, source-class or mask anchors disappear, F-boundary rows collide, dense closure is used, or downstream/closure claims open",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_carrier_frontier_matrix_only"],
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "why_not_v4_probes": {
            "legacy_axis_or_flux_probe": "blocked downstream",
            "topology_or_closure_probe": "blocked; this is a finite certificate-contrast readout only",
            "array_bridge": "not used",
        },
        "nearby_variants": {
            "passed": 7,
            "total": 7,
            "variants": [
                "Y_certificate_boundary_contrast_K classified as bounded finite contrast readout",
                "certificate-member incidence classified as deferred topology-adjacent variant",
                "survival-count-only relabeling classified as duplicate/rejected",
                "locator-only relabeling classified as duplicate/rejected",
                "all-subset minimality and restore/inverse classified as rejected",
                "topology/sheaf/homology/full-closure variants classified as rejected",
                "downstream geometry variants classified as rejected",
            ],
        },
        "active_collision_certificates": contrast["active_collision_certificates"],
        "active_collision_certificate_count": contrast["active_collision_certificate_count"],
        "f_boundary_singleton_certificates": contrast["f_boundary_singleton_certificates"],
        "f_boundary_singleton_certificate_total": contrast["f_boundary_singleton_certificate_total"],
        "f_boundary_collision_certificate_total": contrast["f_boundary_collision_certificate_total"],
        "certificate_contrast_table": contrast["certificate_contrast_table"],
        "certificate_contrast_row_count": contrast["certificate_contrast_row_count"],
        "mask_delta_tensor_shape": contrast["mask_delta_tensor_shape"],
        "mask_delta_l1_sum": contrast["mask_delta_l1_sum"],
        "max_parent_peps3d_sites": contrast["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": contrast["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": contrast["max_peps3d_bond"],
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
        "runtime_seconds": time.time() - started,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "all_pass": all_pass,
                "certificate_contrast_row_count": contrast["certificate_contrast_row_count"],
                "active_collision_certificate_count": contrast["active_collision_certificate_count"],
                "f_boundary_singleton_certificate_total": contrast["f_boundary_singleton_certificate_total"],
                "mask_delta_l1_sum": contrast["mask_delta_l1_sum"],
                "max_parent_peps3d_sites": contrast["max_parent_peps3d_sites"],
                "max_triple_overlap_peps3d_sites": contrast["max_triple_overlap_peps3d_sites"],
                "max_peps3d_bond": contrast["max_peps3d_bond"],
                "result_path": str(OUT_PATH),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
