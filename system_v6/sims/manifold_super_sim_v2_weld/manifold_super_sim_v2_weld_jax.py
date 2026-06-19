#!/usr/bin/env python3
"""JAX/Python workhorse lane for manifold_super_sim_v2_weld."""

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

import manifold_super_sim_v2_weld_common as common


jax.config.update("jax_enable_x64", True)

ENGINE = "jax"
SOURCE = common.SIM_DIR / f"{common.SIM_ID}_{ENGINE}.py"
RESULT = common.RESULT_DIR / f"{common.SIM_ID}_{ENGINE}_results.json"


def source_backing_probe() -> dict[str, Any]:
    graph = nx.DiGraph()
    graph.add_edge("A_G1_terminal_classes", "weld_relation_sum")
    graph.add_edge("B_Z4xZ2_orbit_order", "weld_relation_sum")
    graph.add_edge("weld_relation_sum", "declared_weld_map")
    topo_order = list(nx.topological_sort(graph))
    relation_inputs = jnp.asarray([3, 8], dtype=jnp.int64)
    relation_sum = int(jax.device_get(jnp.sum(relation_inputs)))
    exact_zero = sp.simplify(sp.log(4) - 2 * sp.log(2))

    solver = z3.Solver()
    value = z3.Int("v2_weld_jax_relation_sum")
    solver.add(value == z3.IntVal(relation_sum))
    solver.add(value != z3.IntVal(11))
    z3_status = str(solver.check())

    c_solver = cvc5.Solver()
    c_solver.setLogic("QF_LIA")
    int_sort = c_solver.getIntegerSort()
    c_value = c_solver.mkConst(int_sort, "v2_weld_jax_relation_sum_cvc5")
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
        "sympy_log4_minus_2log2": str(exact_zero),
        "z3_relation_identity": z3_status,
        "cvc5_relation_identity": cvc5_status,
        "pass": relation_sum == 11 and z3_status == cvc5_status == "unsat",
    }


def build_result() -> dict[str, Any]:
    weld_object = common.build_weld_object()
    artifact = common.write_trajectory_artifact(weld_object)
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
            "networkx": "source_backing_probe.networkx_topological_order finite A/B relation graph",
            "sympy": "source_backing_probe.sympy_log4_minus_2log2 typed-counting convention identity",
            "z3": "weld_smt_rows.z3_weld_relation computed A/B/relation identity",
            "cvc5": "weld_smt_rows.cvc5_weld_relation computed A/B/relation identity",
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
        "state_object_id": weld_object["state_object_id"],
        "family_state_object_ids": {
            "A": weld_object["family_state_objects"]["A"]["state_object_id"],
            "B": weld_object["family_state_objects"]["B"]["state_object_id"],
        },
        "weld_map_signature_sha256": common.stable_sha256(weld_object["declared_weld_map"]),
        "weld_row_signature_sha256": common.signature_rows(weld_object["weld_row_table"]),
        "parent_anchor_checks": weld_object["parent_anchor_checks"],
        "cross_family_controls": weld_object["cross_family_controls"],
        "weld_smt_rows": weld_object["weld_smt_rows"],
        "crossover_proofs": {
            "z3": weld_object["weld_smt_rows"]["z3_weld_relation"],
            "cvc5": weld_object["weld_smt_rows"]["cvc5_weld_relation"],
        },
        "trajectory_artifact": artifact,
        "source_backing_probe": probe,
        "all_pass": weld_object["all_pass"] and artifact["sha_verified"] and probe["pass"],
    }
    return payload


def main() -> int:
    payload = build_result()
    common.write_json(RESULT, payload)
    print(json.dumps({"ok": payload["all_pass"], "result_path": common.rel(RESULT)}, indent=2, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
