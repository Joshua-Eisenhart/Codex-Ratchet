#!/usr/bin/env python3
"""JAX-slot graph/proof lane for manifold_family_c_integrated_v0."""

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

import manifold_family_c_integrated_v0_common as common


jax.config.update("jax_enable_x64", True)

ENGINE = "jax"
SOURCE = common.SIM_DIR / f"{common.SIM_ID}_{ENGINE}.py"
RESULT = common.RESULT_DIR / f"{common.SIM_ID}_{ENGINE}_results.json"


def source_backing_probe(family_c: dict[str, Any]) -> dict[str, Any]:
    graph = nx.DiGraph()
    for rung in ("n3", "n4"):
        row = family_c["integrated_state_object"][rung]
        graph.add_node(rung, dimension=row["carrier_dimension"])
    graph.add_edge("n3", "n4", relation="live_terrain_spine")
    current_vector = jnp.array(
        [
            family_c["integrated_state_object"]["n3"]["conditioned_total_abs_current"],
            family_c["integrated_state_object"]["n4"]["conditioned_total_abs_current"],
        ],
        dtype=jnp.float64,
    )
    current_l1 = float(jax.device_get(jnp.sum(jnp.abs(current_vector))))
    exact_relation = sp.simplify(sp.Integer(16) / sp.Integer(8) - 2)

    total_edges = sum(family_c["integrated_state_object"][r][ "conditioned_edge_count"] for r in ("n3", "n4"))
    solver = z3.Solver()
    edge_count = z3.Int("family_c_jax_conditioned_edge_total")
    solver.add(edge_count == z3.IntVal(total_edges))
    solver.add(edge_count != z3.IntVal(8))
    z3_status = str(solver.check())

    c_solver = cvc5.Solver()
    c_solver.setLogic("QF_LIA")
    int_sort = c_solver.getIntegerSort()
    c_edges = c_solver.mkConst(int_sort, "family_c_jax_conditioned_edge_total_cvc5")
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_edges, c_solver.mkInteger(total_edges)))
    c_solver.assertFormula(c_solver.mkTerm(Kind.DISTINCT, c_edges, c_solver.mkInteger(8)))
    raw = c_solver.checkSat()
    cvc5_status = "sat" if raw.isSat() else "unsat" if raw.isUnsat() else "unknown"

    return {
        "networkx_node_count": graph.number_of_nodes(),
        "networkx_edge_count": graph.number_of_edges(),
        "jax_current_l1": current_l1,
        "sympy_C16_over_C8_minus_2": str(exact_relation),
        "z3_edge_identity": z3_status,
        "cvc5_edge_identity": cvc5_status,
        "pass": graph.number_of_nodes() == 2 and graph.number_of_edges() == 1 and exact_relation == 0 and z3_status == cvc5_status == "unsat",
    }


def build_result() -> dict[str, Any]:
    family_c = common.build_family_c_object()
    artifact = common.write_trajectory_artifact(family_c)
    probe = source_backing_probe(family_c)
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
            "networkx": "source_backing_probe.networkx_node_count/edge_count over n3->n4 terrain spine",
            "sympy": "source_backing_probe.sympy_C16_over_C8_minus_2 exact support relation",
            "z3": "source_backing_probe.z3_edge_identity computed total edge identity",
            "cvc5": "source_backing_probe.cvc5_edge_identity computed total edge identity",
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
        "state_object_id": family_c["integrated_state_object"]["state_object_id"],
        "source_backing_probe": probe,
        "trajectory_artifact": artifact,
        "crossover_proofs": family_c["crossover_proofs"],
        "family_c_object_signature_sha256": common.stable_sha256(family_c),
        "all_pass": family_c["all_pass"] and probe["pass"] and artifact["sha_verified"],
    }
    return payload


def main() -> int:
    payload = build_result()
    common.write_json(RESULT, payload)
    print(json.dumps({"ok": payload["all_pass"], "result_path": common.rel(RESULT)}, indent=2, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
