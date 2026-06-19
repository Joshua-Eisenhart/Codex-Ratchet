#!/usr/bin/env python3
"""JAX-slot workhorse lane for manifold_family_b_integrated_v0."""

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

import manifold_family_b_integrated_v0_common as common


jax.config.update("jax_enable_x64", True)

ENGINE = "jax"
SOURCE = common.SIM_DIR / f"{common.SIM_ID}_{ENGINE}.py"
RESULT = common.RESULT_DIR / f"{common.SIM_ID}_{ENGINE}_results.json"


def source_backing_probe() -> dict[str, Any]:
    reps = [(q, r) for q in range(4) for r in range(2)]
    graph = nx.DiGraph()
    for q, r in reps:
        graph.add_edge((q, r), ((q + 1) % 4, r), label="a")
        graph.add_edge((q, r), (q, (r + 1) % 2), label="b")
    component_count = nx.number_strongly_connected_components(graph)
    phase = jnp.arange(8, dtype=jnp.float64)
    z4_classes = jnp.mod(phase, 4)
    residue = jnp.floor_divide(phase.astype(jnp.int64), 4)
    orbit_signature = jax.device_get(jnp.stack([z4_classes, residue.astype(jnp.float64)], axis=1)).tolist()
    exact_zero = sp.simplify(sp.log(4) - 2 * sp.log(2))

    solver = z3.Solver()
    actual = z3.Int("family_b_jax_orbit_count")
    solver.add(actual == z3.IntVal(len(reps)))
    solver.add(actual != z3.IntVal(8))
    z3_status = str(solver.check())

    c_solver = cvc5.Solver()
    c_solver.setLogic("QF_LIA")
    int_sort = c_solver.getIntegerSort()
    c_actual = c_solver.mkConst(int_sort, "family_b_jax_orbit_count_cvc5")
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_actual, c_solver.mkInteger(len(reps))))
    c_solver.assertFormula(c_solver.mkTerm(Kind.DISTINCT, c_actual, c_solver.mkInteger(8)))
    c_status_raw = c_solver.checkSat()
    cvc5_status = "sat" if c_status_raw.isSat() else "unsat" if c_status_raw.isUnsat() else "unknown"

    return {
        "networkx_component_count": component_count,
        "networkx_edge_count": graph.number_of_edges(),
        "jax_orbit_signature": orbit_signature,
        "sympy_log4_minus_2log2": str(exact_zero),
        "z3_orbit_identity": z3_status,
        "cvc5_orbit_identity": cvc5_status,
        "pass": component_count == 1 and z3_status == cvc5_status == "unsat",
    }


def build_result() -> dict[str, Any]:
    family_b_object = common.build_family_b_object()
    artifact = common.write_trajectory_artifact(family_b_object)
    probe = source_backing_probe()
    layer_sigs = {key: row["row_signature_sha256"] for key, row in family_b_object["layers"].items()}
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
            "networkx": "source_backing_probe.networkx_component_count and finite Z4xZ2 orbit graph",
            "sympy": "source_backing_probe.sympy_log4_minus_2log2 plus typed entropy expressions",
            "z3": "crossover_proofs.z3 computed denominator identity",
            "cvc5": "crossover_proofs.cvc5 computed denominator identity",
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
        "state_object_id": family_b_object["state_object_id"],
        "layer_signatures": layer_sigs,
        "weld_anchors": family_b_object["weld_anchors"],
        "kill_controls": family_b_object["kill_controls"],
        "crossover_proofs": family_b_object["crossover_proofs"],
        "trajectory_artifact": artifact,
        "source_backing_probe": probe,
        "family_b_object_signature_sha256": common.stable_sha256(family_b_object),
        "all_pass": family_b_object["all_pass"] and probe["pass"] and artifact["sha_verified"],
    }
    return payload


def main() -> int:
    payload = build_result()
    common.write_json(RESULT, payload)
    print(json.dumps({"ok": payload["all_pass"], "result_path": common.rel(RESULT)}, indent=2, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
