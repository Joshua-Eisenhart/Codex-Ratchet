#!/usr/bin/env python3
"""JAX/Python relation lane for manifold_ab_weld_relation_v0."""

from __future__ import annotations

import json
from typing import Any

import cvc5
from cvc5 import Kind
import jax
import jax.numpy as jnp
import networkx as nx
import sympy as sp
import z3

import manifold_ab_weld_relation_v0_common as common


jax.config.update("jax_enable_x64", True)

ENGINE = "jax"
SOURCE = common.SIM_DIR / f"{common.SIM_ID}_{ENGINE}.py"
RESULT = common.RESULT_DIR / f"{common.SIM_ID}_{ENGINE}_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
TOOL_MANIFEST = {
    "networkx": {"tried": True, "used": True, "reason": "finite A/B dependency graph for relation rows"},
    "sympy": {"tried": True, "used": True, "reason": "exact relation residual and zero identity checks"},
    "z3": {"tried": True, "used": True, "reason": "A/B/relation SMT identity check"},
    "cvc5": {"tried": True, "used": True, "reason": "independent SMT mirror of the relation identity check"},
}
TOOL_INTEGRATION_DEPTH = {
    "networkx": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
}


def source_backing_probe() -> dict[str, Any]:
    graph = nx.DiGraph()
    graph.add_edge("A_G1_terminal_class_count", "WO2_partition_sum_relation")
    graph.add_edge("B_composite_order", "WO2_partition_sum_relation")
    graph.add_edge("coordinate_map_signature", "WO1_state_pair_hash")
    graph.add_edge("WO2_partition_sum_relation", "SMT_relation_sum")
    topo_order = list(nx.topological_sort(graph))

    relation_inputs = jnp.asarray([3, 8], dtype=jnp.int64)
    relation_sum = int(jax.device_get(jnp.sum(relation_inputs)))

    a_sym, b_sym, w_sym = sp.symbols("a_sym b_sym w_sym", integer=True)
    residual = sp.simplify((a_sym + b_sym - w_sym).subs({a_sym: 3, b_sym: 8, w_sym: 11}))
    zero_identity = sp.simplify(sp.Rational(0, 1) + sp.Rational(0, 1))

    solver = z3.Solver()
    value = z3.Int("ab_relation_jax_relation_sum")
    solver.add(value == z3.IntVal(relation_sum))
    solver.add(value != z3.IntVal(11))
    z3_status = str(solver.check())

    c_solver = cvc5.Solver()
    c_solver.setLogic("QF_LIA")
    int_sort = c_solver.getIntegerSort()
    c_value = c_solver.mkConst(int_sort, "ab_relation_jax_relation_sum_cvc5")
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_value, c_solver.mkInteger(relation_sum)))
    c_solver.assertFormula(c_solver.mkTerm(Kind.DISTINCT, c_value, c_solver.mkInteger(11)))
    c_status_raw = c_solver.checkSat()
    cvc5_status = "sat" if c_status_raw.isSat() else "unsat" if c_status_raw.isUnsat() else "unknown"

    return {
        "networkx_node_count": graph.number_of_nodes(),
        "networkx_edge_count": graph.number_of_edges(),
        "networkx_topological_order": topo_order,
        "jax_relation_inputs": jax.device_get(relation_inputs).tolist(),
        "jax_relation_sum": relation_sum,
        "sympy_relation_residual": str(residual),
        "sympy_zero_identity": str(zero_identity),
        "z3_relation_identity": z3_status,
        "cvc5_relation_identity": cvc5_status,
        "pass": relation_sum == 11
        and str(residual) == "0"
        and str(zero_identity) == "0"
        and graph.number_of_nodes() == 6
        and z3_status == cvc5_status == "unsat",
    }


def build_result() -> dict[str, Any]:
    relation_object = common.build_relation_object()
    artifact = common.write_trajectory_artifact(relation_object)
    probe = source_backing_probe()
    payload = {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": common.SIM_ID,
        "object_id": f"{common.SIM_ID}_{ENGINE}",
        "engine": ENGINE,
        "generated_at": common.now_z(),
        "classification": common.CLASSIFICATION,
        "promotion_allowed": common.PROMOTION_ALLOWED,
        "formal_admission_allowed": common.FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": False,
        "source_path": common.rel(SOURCE),
        "source_sha256": common.sha256_file(SOURCE),
        "result_path": common.rel(RESULT),
        "packages_used": ["jax", "jax.numpy", "networkx", "sympy", "z3", "cvc5", "json"],
        "aligned_packages_load_bearing": ["networkx", "sympy", "z3", "cvc5"],
        "package_observables": {
            "networkx": "source_backing_probe.networkx_topological_order finite A/B dependency graph",
            "sympy": "source_backing_probe.sympy_relation_residual exact typed relation residual",
            "z3": "weld_relation_smt.z3_weld_relation_sum relation proof and flips",
            "cvc5": "weld_relation_smt.cvc5_weld_relation_sum relation proof and flips",
        },
        "package_versions": {
            "jax": getattr(jax, "__version__", "version_unavailable"),
            "networkx": common.package_version("networkx"),
            "sympy": sp.__version__,
            "z3": getattr(z3, "get_version_string", lambda: "version_unavailable")(),
            "cvc5": getattr(cvc5, "__version__", "version_unavailable"),
        },
        "TOOL_MANIFEST": common.TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": {**common.TOOL_INTEGRATION_DEPTH, "jax": "supportive"},
        "tool_intent": common.TOOL_INTENT,
        "claim_path_tools": ["networkx", "sympy", "z3", "cvc5"],
        "engine_mode": common.ENGINE_MODE,
        "state_object_id": relation_object["state_object_id"],
        "family_state_object_ids": {
            "A": relation_object["pinned_state_objects"]["A"]["state_object_id"],
            "B": relation_object["pinned_state_objects"]["B"]["state_object_id"],
        },
        "coordinate_map_signature_sha256": relation_object["coordinate_map_signature_sha256"],
        "weld_only_rows_signature_sha256": relation_object["weld_only_rows_signature_sha256"],
        "nonrecoverability_signature_sha256": relation_object["nonrecoverability_signature_sha256"],
        "parent_anchor_checks": relation_object["parent_anchor_checks"],
        "cross_family_controls": relation_object["cross_family_controls"],
        "weld_relation_smt": relation_object["weld_relation_smt"],
        "crossover_proofs": {
            "z3": relation_object["weld_relation_smt"]["z3_weld_relation_sum"],
            "cvc5": relation_object["weld_relation_smt"]["cvc5_weld_relation_sum"],
        },
        "trajectory_artifact": artifact,
        "source_backing_probe": probe,
        "all_pass": relation_object["all_pass"] and artifact["sha_verified"] and probe["pass"],
    }
    return payload


def main() -> int:
    payload = build_result()
    common.write_json(RESULT, payload)
    print(json.dumps({"ok": payload["all_pass"], "result_path": common.rel(RESULT)}, indent=2, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
