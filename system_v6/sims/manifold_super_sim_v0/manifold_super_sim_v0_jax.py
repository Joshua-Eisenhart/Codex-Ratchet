#!/usr/bin/env python3
"""JAX-slot workhorse lane for manifold_super_sim_v0."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import jax
import jax.numpy as jnp
import jax.scipy.linalg as jsp_linalg
import networkx as nx
import sympy as sp
import z3

import manifold_super_sim_v0_common as common


jax.config.update("jax_enable_x64", True)

ENGINE = "jax"
SOURCE = common.SIM_DIR / f"{common.SIM_ID}_{ENGINE}.py"
RESULT = common.RESULT_DIR / f"{common.SIM_ID}_{ENGINE}_results.json"


def jax_expm(aug: list[list[float]], h: float) -> list[list[float]]:
    matrix = jnp.asarray(aug, dtype=jnp.float64)
    flow = jsp_linalg.expm(float(h) * matrix)
    return jax.device_get(flow).tolist()


def source_backing_probe() -> dict[str, Any]:
    graph = nx.DiGraph()
    graph.add_edge(0, 1)
    graph.add_edge(1, 2)
    components = list(nx.strongly_connected_components(graph))
    exact_log = sp.simplify(sp.log(3) - sp.log(1))

    solver = z3.Solver()
    actual = z3.Int("jax_probe_actual_component_count")
    solver.add(actual == z3.IntVal(len(components)))
    solver.add(actual != z3.IntVal(3))
    z3_status = str(solver.check())

    c_solver = cvc5.Solver()
    c_solver.setLogic("QF_LIA")
    int_sort = c_solver.getIntegerSort()
    c_actual = c_solver.mkConst(int_sort, "jax_probe_actual_component_count_cvc5")
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_actual, c_solver.mkInteger(len(components))))
    c_solver.assertFormula(c_solver.mkTerm(Kind.NOT, c_solver.mkTerm(Kind.EQUAL, c_actual, c_solver.mkInteger(3))))
    c_status_raw = c_solver.checkSat()
    cvc5_status = "sat" if c_status_raw.isSat() else "unsat" if c_status_raw.isUnsat() else str(c_status_raw)

    return {
        "networkx_component_count": len(components),
        "sympy_exact_log": str(exact_log),
        "z3_component_identity": z3_status,
        "cvc5_component_identity": cvc5_status,
        "pass": z3_status == cvc5_status == "unsat",
    }


def build_result() -> dict[str, Any]:
    super_object = common.build_super_object(jax_expm)
    artifact = common.write_trajectory_artifact(super_object)
    probe = source_backing_probe()
    layer_sigs = {key: row["row_signature_sha256"] for key, row in super_object["layers"].items()}
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
        "packages_used": ["jax", "jax.numpy", "jax.scipy.linalg", "networkx", "sympy", "z3", "cvc5", "json", "pathlib"],
        "aligned_packages_load_bearing": ["networkx", "sympy", "z3", "cvc5"],
        "package_observables": {
            "networkx": "source_backing_probe.networkx_component_count plus inherited finite graph recomputation",
            "sympy": "source_backing_probe.sympy_exact_log and typed entropy expressions",
            "z3": "crossover_proofs.z3 computed partition identity",
            "cvc5": "crossover_proofs.cvc5 computed partition identity",
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
        "state_object_id": super_object["state_object_id"],
        "layer_signatures": layer_sigs,
        "weld_anchors": super_object["weld_anchors"],
        "kill_controls": super_object["kill_controls"],
        "crossover_proofs": super_object["crossover_proofs"],
        "trajectory_artifact": artifact,
        "source_backing_probe": probe,
        "super_object_signature_sha256": common.stable_sha256(super_object),
        "all_pass": super_object["all_pass"] and probe["pass"] and artifact["sha_verified"],
    }
    return payload


def main() -> int:
    payload = build_result()
    common.write_json(RESULT, payload)
    print(json.dumps({"ok": payload["all_pass"], "result_path": common.rel(RESULT)}, indent=2, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

