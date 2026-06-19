#!/usr/bin/env python3
"""JAX lane for the ECD.06 prediction-first inference discriminator."""

from __future__ import annotations

import json
from pathlib import Path

import cvc5
import jax
import jax.numpy as jnp
import networkx as nx
import sympy as sp
import z3

import ecd06_prediction_first_inference_v1_common as common


jax.config.update("jax_enable_x64", True)

SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_jax_results.json"


def package_smoke() -> dict[str, object]:
    graph = nx.DiGraph()
    graph.add_edges_from([(0, 1), (1, 2)])
    tensor = jnp.asarray([1.0, -2.0, 3.0], dtype=jnp.float64)
    solver = z3.Solver()
    solver.add(z3.Int("q") < z3.Int("b"))
    cvc = cvc5.Solver()
    cvc.setLogic("QF_LIA")
    return {
        "jax_enable_x64": bool(jax.config.jax_enable_x64),
        "jax_norm": float(jnp.linalg.norm(tensor)),
        "networkx_edges": graph.number_of_edges(),
        "sympy_rational": str(sp.Rational(1, 7) + sp.Rational(6, 7)),
        "z3_check": str(solver.check()),
        "cvc5_ready": True,
    }


def build_result() -> dict[str, object]:
    return common.engine_payload(
        "jax",
        SOURCE_PATH,
        RESULT_PATH,
        packages_used=["jax", "jax.numpy", "networkx", "sympy", "z3", "cvc5"],
        load_bearing=["networkx", "sympy", "z3", "cvc5"],
        observables={
            "networkx": "nx.DiGraph finite edge-family smoke for committed trajectory topology",
            "sympy": "sp.Rational exact scalar smoke for typed-error aggregation binding",
            "z3": "z3.Solver finite adjusted-error winner relation",
            "cvc5": "cvc5.Solver independent finite adjusted-error winner relation",
        },
        role_id="ecd06_prediction_first_inference_v1_jax_builder",
        package_smoke=package_smoke(),
    )


def main() -> int:
    result = build_result()
    common.write_json(RESULT_PATH, result)
    print(json.dumps({"result_path": common.rel(RESULT_PATH), "all_pass": result["all_pass"]}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
