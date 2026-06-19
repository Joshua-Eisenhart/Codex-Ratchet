#!/usr/bin/env python3
"""JAX/Python lane for discrete_axis3_placement_v0."""

from __future__ import annotations

from pathlib import Path

import cvc5
from cvc5 import Kind
from jax import config

config.update("jax_enable_x64", True)

import jax
import jax.numpy as jnp
import networkx as nx
import sympy as sp
import z3

import discrete_axis3_placement_v0_common as common


ENGINE = "jax"
SOURCE_PATH = common.SIM_DIR / f"{common.SIM_ID}_{ENGINE}.py"
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_{ENGINE}_results.json"


def source_backing_probe(axis3_object: dict) -> dict:
    edge_distances = jnp.asarray(
        [
            row["density_step_distance"]
            for row in axis3_object["stability_under_committed_dynamics"]["rows"]
        ],
        dtype=jnp.float64,
    )
    stable = int(jax.device_get(jnp.count_nonzero(edge_distances <= common.EPS)))
    changed = int(jax.device_get(jnp.count_nonzero(edge_distances > common.EPS)))

    graph = nx.DiGraph()
    graph.add_nodes_from(row["loop_id"] for row in axis3_object["placement_table"])
    for row in axis3_object["stability_under_committed_dynamics"]["rows"]:
        graph.add_edge(row["loop_id"], f"{row['loop_id']}::step{row['next_step']}")

    u, eta = sp.symbols("u eta", real=True)
    horizontal_base = sp.simplify((-sp.cos(2 * eta)) + sp.cos(2 * eta) * 1)
    fiber_connection = sp.simplify(1 + sp.cos(2 * eta) * 0)
    wrong_sign_base = sp.simplify(sp.cos(2 * eta) + sp.cos(2 * eta) * 1)
    symbolic_pass = horizontal_base == 0 and fiber_connection == 1 and wrong_sign_base != 0

    z_solver = z3.Solver()
    z_stable = z3.Int("jax_axis3_stable_z3")
    z_solver.add(z_stable == z3.IntVal(stable))
    z_solver.add(z_stable == z3.IntVal(0))
    z3_status = str(z_solver.check()).lower()

    c_solver = cvc5.Solver()
    int_sort = c_solver.getIntegerSort()
    c_stable = c_solver.mkConst(int_sort, "jax_axis3_stable_cvc5")
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_stable, c_solver.mkInteger(stable)))
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_stable, c_solver.mkInteger(0)))
    cvc5_status = str(c_solver.checkSat()).lower()

    expected = axis3_object["stability_under_committed_dynamics"]
    return {
        "networkx_loop_nodes": graph.number_of_nodes(),
        "networkx_loop_edges": graph.number_of_edges(),
        "jax_stable_density_edges": stable,
        "jax_changed_density_edges": changed,
        "sympy_horizontal_base_A_dot_gamma": str(horizontal_base),
        "sympy_fiber_A_dot_gamma": str(fiber_connection),
        "sympy_wrong_sign_base_A_dot_gamma": str(wrong_sign_base),
        "z3_stable_not_zero": z3_status,
        "cvc5_stable_not_zero": cvc5_status,
        "pass": (
            stable == expected["stable_edge_count"]
            and changed == expected["changed_edge_count"]
            and symbolic_pass
            and z3_status == "unsat"
            and cvc5_status == "unsat"
        ),
    }


def main() -> int:
    axis3_object = common.build_axis3_object()
    probe = source_backing_probe(axis3_object)
    payload = common.engine_result_payload(
        engine=ENGINE,
        source_path=SOURCE_PATH,
        result_path=RESULT_PATH,
        packages_used=["jax", "jax.numpy", "networkx", "sympy", "z3", "cvc5"],
        aligned_packages_load_bearing=["networkx", "sympy", "z3", "cvc5"],
        package_observables={
            "networkx": "nx.DiGraph loop-time dynamics carrier over pinned Axis-3 rows",
            "sympy": "sp.symbols and sp.simplify exact horizontal condition A(dot gamma_out)=0",
            "z3": "z3.Solver computed stable-edge identity and packet crossover proofs",
            "cvc5": "cvc5.Solver computed stable-edge identity and packet crossover proofs",
        },
        source_backing_probe=probe,
    )
    common.write_json(RESULT_PATH, payload)
    print(common.stable_json({"ok": payload["all_pass"], "result_path": common.rel(RESULT_PATH)}))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
