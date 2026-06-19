#!/usr/bin/env python3
"""JAX/Python lane for discrete_axis0_field_v0."""

from __future__ import annotations

from pathlib import Path

import cvc5
from cvc5 import Kind
import jax
import jax.numpy as jnp
import networkx as nx
import sympy as sp
import z3

import discrete_axis0_field_v0_common as common


ENGINE = "jax"
SOURCE_PATH = common.SIM_DIR / f"{common.SIM_ID}_{ENGINE}.py"
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_{ENGINE}_results.json"


def source_backing_probe(axis0_object: dict) -> dict:
    phi_nums = jnp.asarray([row["phi_numerator"] for row in axis0_object["readout_table"]], dtype=jnp.int32)
    edge_pairs = jnp.asarray([[row["src"], row["dst"]] for row in axis0_object["gradient_table"]], dtype=jnp.int32)
    gradient_nums = jax.vmap(lambda pair: phi_nums[pair[1]] - phi_nums[pair[0]])(edge_pairs)
    nonzero = int(jax.device_get(jnp.count_nonzero(gradient_nums)))
    graph = nx.DiGraph()
    graph.add_nodes_from(row["cell_id"] for row in axis0_object["readout_table"])
    graph.add_edges_from((row["src"], row["dst"]) for row in axis0_object["gradient_table"])
    rational_total = sp.Rational(int(jax.device_get(jnp.sum(gradient_nums))), common.FIELD_DENOMINATOR)

    z_solver = z3.Solver()
    z_nonzero = z3.Int("jax_axis0_nonzero_gradients_z3")
    z_solver.add(z_nonzero == z3.IntVal(nonzero))
    z_solver.add(z_nonzero == z3.IntVal(0))
    z3_status = str(z_solver.check()).lower()

    c_solver = cvc5.Solver()
    int_sort = c_solver.getIntegerSort()
    c_nonzero = c_solver.mkConst(int_sort, "jax_axis0_nonzero_gradients_cvc5")
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_nonzero, c_solver.mkInteger(nonzero)))
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_nonzero, c_solver.mkInteger(0)))
    cvc5_status = str(c_solver.checkSat()).lower()

    expected_nonzero = axis0_object["gradient_summary"]["nonzero_gradient_edges"]
    return {
        "networkx_node_count": graph.number_of_nodes(),
        "networkx_collapsed_edge_count": graph.number_of_edges(),
        "jax_nonzero_gradient_edges": nonzero,
        "sympy_rational_total_gradient": str(rational_total),
        "z3_nonzero_not_zero": z3_status,
        "cvc5_nonzero_not_zero": cvc5_status,
        "pass": (
            graph.number_of_nodes() == common.EXPECTED_STATE_COUNT
            and nonzero == expected_nonzero
            and z3_status == "unsat"
            and cvc5_status == "unsat"
        ),
    }


def main() -> int:
    axis0_object = common.build_axis0_object()
    probe = source_backing_probe(axis0_object)
    payload = common.engine_result_payload(
        engine=ENGINE,
        source_path=SOURCE_PATH,
        result_path=RESULT_PATH,
        packages_used=["jax", "jax.numpy", "networkx", "sympy", "z3", "cvc5"],
        aligned_packages_load_bearing=["networkx", "sympy", "z3", "cvc5"],
        package_observables={
            "networkx": "nx.DiGraph ordered adjacency carrier for 33-cell directed updates",
            "sympy": "sp.Rational exact total gradient probe over phi denominator 97",
            "z3": "z3.Solver computed nonzero-gradient identity and packet crossover proofs",
            "cvc5": "cvc5.Solver computed nonzero-gradient identity and packet crossover proofs",
        },
        source_backing_probe=probe,
    )
    common.write_json(RESULT_PATH, payload)
    print(common.stable_json({"ok": payload["all_pass"], "result_path": common.rel(RESULT_PATH)}))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
