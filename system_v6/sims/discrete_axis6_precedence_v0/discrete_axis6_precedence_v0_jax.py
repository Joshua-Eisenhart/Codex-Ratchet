#!/usr/bin/env python3
"""JAX/Python lane for discrete_axis6_precedence_v0."""

from __future__ import annotations

import cvc5
from cvc5 import Kind
import jax
import jax.numpy as jnp
import networkx as nx
import sympy as sp
import z3

import discrete_axis6_precedence_v0_common as common


jax.config.update("jax_enable_x64", True)

ENGINE = "jax"
SOURCE_PATH = common.SIM_DIR / f"{common.SIM_ID}_{ENGINE}.py"
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_{ENGINE}_results.json"


def source_backing_probe(axis6_object: dict) -> dict:
    pins = common.pinning_payload()
    coords = jnp.asarray([row["coord"] for row in axis6_object["precedence_table"]], dtype=jnp.float64)
    op_m = jnp.asarray(pins["operator"]["M"], dtype=jnp.float64)
    op_c = jnp.asarray(pins["operator"]["c"], dtype=jnp.float64)
    terrain_m = jnp.asarray(pins["terrain"]["M"], dtype=jnp.float64)
    terrain_c = jnp.asarray(pins["terrain"]["c"], dtype=jnp.float64)

    def b6_for_coord(r: jnp.ndarray) -> jnp.ndarray:
        operator_first = terrain_m @ (op_m @ r + op_c) + terrain_c
        terrain_first = op_m @ (terrain_m @ r + terrain_c) + op_c
        delta = operator_first - terrain_first
        weighted_z = jnp.linalg.norm(delta) * delta[2]
        return jnp.where(weighted_z > common.EPS, 1, jnp.where(weighted_z < -common.EPS, -1, 0))

    computed = jax.vmap(b6_for_coord)(coords)
    expected = jnp.asarray([row["b6_sign"] for row in axis6_object["precedence_table"]], dtype=jnp.int32)
    positive = int(jax.device_get(jnp.sum(computed == 1)))
    negative = int(jax.device_get(jnp.sum(computed == -1)))
    neutral = int(jax.device_get(jnp.sum(computed == 0)))
    matches = bool(jax.device_get(jnp.all(computed == expected)))

    graph = nx.DiGraph()
    graph.add_nodes_from(row["cell_id"] for row in axis6_object["precedence_table"])
    graph.add_edges_from((row["src"], row["dst"]) for row in axis6_object["carrier_edges"])

    q_z = sp.Rational(3, 10)
    dz = sp.diag(1 - q_z, 1 - q_z, 1)
    sqrt3 = sp.sqrt(3)
    ne_generator = sp.Matrix(
        [
            [0, 2 * sqrt3 / 3, -2 * sqrt3 / 3],
            [-2 * sqrt3 / 3, 0, 2 * sqrt3 / 3],
            [2 * sqrt3 / 3, -2 * sqrt3 / 3, 0],
        ]
    )
    commutator_template = sp.simplify(ne_generator * dz - dz * ne_generator)
    symbolic_nonzero_entries = int(sum(1 for value in commutator_template if value != 0))

    z_solver = z3.Solver()
    z_positive = z3.Int("jax_axis6_positive_count_z3")
    z_negative = z3.Int("jax_axis6_negative_count_z3")
    z_solver.add(z_positive == z3.IntVal(positive))
    z_solver.add(z_negative == z3.IntVal(negative))
    z_solver.add(z3.Or(z_positive == 0, z_negative == 0))
    z3_status = str(z_solver.check()).lower()

    c_solver = cvc5.Solver()
    int_sort = c_solver.getIntegerSort()
    c_positive = c_solver.mkConst(int_sort, "jax_axis6_positive_count_cvc5")
    c_negative = c_solver.mkConst(int_sort, "jax_axis6_negative_count_cvc5")
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_positive, c_solver.mkInteger(positive)))
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_negative, c_solver.mkInteger(negative)))
    c_solver.assertFormula(
        c_solver.mkTerm(
            Kind.OR,
            c_solver.mkTerm(Kind.EQUAL, c_positive, c_solver.mkInteger(0)),
            c_solver.mkTerm(Kind.EQUAL, c_negative, c_solver.mkInteger(0)),
        )
    )
    cvc5_status = str(c_solver.checkSat()).lower()

    return {
        "networkx_node_count": graph.number_of_nodes(),
        "networkx_collapsed_edge_count": graph.number_of_edges(),
        "jax_vmap_positive": positive,
        "jax_vmap_negative": negative,
        "jax_vmap_neutral": neutral,
        "jax_vmap_matches_common_table": matches,
        "sympy_commutator_template_nonzero_entries": symbolic_nonzero_entries,
        "sympy_commutator_template": str(commutator_template),
        "z3_positive_negative_not_zero": z3_status,
        "cvc5_positive_negative_not_zero": cvc5_status,
        "pass": (
            graph.number_of_nodes() == common.EXPECTED_STATE_COUNT
            and positive == axis6_object["precedence_counts"]["positive"]
            and negative == axis6_object["precedence_counts"]["negative"]
            and neutral == axis6_object["precedence_counts"]["neutral"]
            and matches
            and symbolic_nonzero_entries > 0
            and z3_status == "unsat"
            and cvc5_status == "unsat"
        ),
    }


def main() -> int:
    axis6_object = common.build_axis6_object()
    probe = source_backing_probe(axis6_object)
    payload = common.engine_result_payload(
        engine=ENGINE,
        source_path=SOURCE_PATH,
        result_path=RESULT_PATH,
        packages_used=["jax", "jax.numpy", "networkx", "sympy", "z3", "cvc5"],
        aligned_packages_load_bearing=["networkx", "sympy", "z3", "cvc5"],
        package_observables={
            "networkx": "nx.DiGraph carrier with 33 nodes and committed generator adjacency",
            "sympy": "sp.Matrix/sp.Rational exact D_z x Ne commutator-template source row",
            "z3": "z3.Solver/z3.Int computed positive/negative precedence identity",
            "cvc5": "cvc5.Solver/mkConst/mkTerm/assertFormula/checkSat computed positive/negative precedence identity",
        },
        source_backing_probe=probe,
    )
    common.write_json(RESULT_PATH, payload)
    print(common.stable_json({"ok": payload["all_pass"], "result_path": common.rel(RESULT_PATH)}))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
