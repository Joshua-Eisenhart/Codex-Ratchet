#!/usr/bin/env python3
"""JAX/Python exact lane for render_layer_readout_v1."""

from __future__ import annotations

import json
from pathlib import Path

import cvc5
import jax
import jax.numpy as jnp
import networkx as nx
import sympy as sp
import z3

import render_layer_readout_v1_common as common


jax.config.update("jax_enable_x64", True)

SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_jax_results.json"
classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
TOOL_MANIFEST = {
    "networkx": {"tried": True, "used": True, "reason": "finite committed generator graph and v1 render cut-edge probe"},
    "sympy": {"tried": True, "used": True, "reason": "exact finite scalar smoke check"},
    "z3": {"tried": True, "used": True, "reason": "two-sided v1 reachability proof with erased old-pin control"},
    "cvc5": {"tried": True, "used": True, "reason": "independent two-sided v1 reachability proof with erased old-pin control"},
}
TOOL_INTEGRATION_DEPTH = {"networkx": "load_bearing", "sympy": "load_bearing", "z3": "load_bearing", "cvc5": "load_bearing"}


def package_smoke() -> dict[str, object]:
    graph = nx.DiGraph()
    graph.add_edge(0, 1)
    tensor_norm = float(jnp.linalg.norm(jnp.asarray([3.0, 4.0], dtype=jnp.float64)))
    solver = z3.Solver()
    solver.add(z3.Int("x") == 1)
    cvc = cvc5.Solver()
    cvc.setLogic("QF_LIA")
    return {
        "networkx_edges": graph.number_of_edges(),
        "sympy_rational": str(sp.Rational(1, 3) + sp.Rational(2, 3)),
        "jax_norm": tensor_norm,
        "z3_check": str(solver.check()),
        "cvc5_ready": True,
    }


def build_result() -> dict[str, object]:
    payload = common.engine_payload(
        "jax",
        SOURCE_PATH,
        RESULT_PATH,
        packages_used=["jax", "jax.numpy", "networkx", "sympy", "z3", "cvc5"],
        load_bearing=["networkx", "sympy", "z3", "cvc5"],
        observables={
            "networkx": "nx.MultiDiGraph finite committed generator graph and v1 render cut-edge probe",
            "sympy": "sp.Rational exact control smoke for finite scalar binding",
            "z3": "z3.Solver two-sided v1 reachability proof with erased old-pin control",
            "cvc5": "cvc5.Solver independent two-sided v1 reachability proof with erased old-pin control",
        },
        role_id="render_layer_readout_v1_jax_exact_builder",
    )
    payload["package_smoke"] = package_smoke()
    return payload


def main() -> int:
    result = build_result()
    common.write_json(RESULT_PATH, result)
    print(json.dumps({"result_path": common.rel(RESULT_PATH), "all_pass": result["all_pass"]}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
