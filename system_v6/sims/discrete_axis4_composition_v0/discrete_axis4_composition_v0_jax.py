#!/usr/bin/env python3
"""JAX/Python lane for discrete_axis4_composition_v0."""

from __future__ import annotations

import cvc5
from cvc5 import Kind
import jax
import jax.numpy as jnp
import networkx as nx
import sympy as sp
import z3

import discrete_axis4_composition_v0_common as common


jax.config.update("jax_enable_x64", True)

ENGINE = "jax"
SOURCE_PATH = common.SIM_DIR / f"{common.SIM_ID}_{ENGINE}.py"
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_{ENGINE}_results.json"


def source_backing_probe(axis4_object: dict) -> dict:
    pins = common.pinning_payload()
    coords = jnp.asarray([row["coord"] for row in axis4_object["axis4_readout_table"]], dtype=jnp.float64)
    r_map = jnp.asarray(pins["R"]["M"], dtype=jnp.float64)
    c_map = jnp.asarray(pins["C"]["M"], dtype=jnp.float64)

    def axis4_for_coord(r: jnp.ndarray) -> jnp.ndarray:
        phi_d = r_map @ (c_map @ r)
        phi_i = c_map @ (r_map @ r)
        delta = phi_d - phi_i
        norm = jnp.linalg.norm(delta)
        yz_sign = jnp.where(
            jnp.abs(delta[1]) > common.EPS,
            jnp.where(delta[1] > common.EPS, 1, -1),
            jnp.where(
                jnp.abs(delta[2]) > common.EPS,
                jnp.where(delta[2] > common.EPS, 1, -1),
                jnp.where(delta[0] > common.EPS, 1, jnp.where(delta[0] < -common.EPS, -1, 0)),
            ),
        )
        return jnp.where(norm <= common.EPS, 0, yz_sign)

    computed = jax.vmap(axis4_for_coord)(coords)
    expected = jnp.asarray([row["axis4_sign"] for row in axis4_object["axis4_readout_table"]], dtype=jnp.int32)
    positive = int(jax.device_get(jnp.sum(computed == 1)))
    negative = int(jax.device_get(jnp.sum(computed == -1)))
    neutral = int(jax.device_get(jnp.sum(computed == 0)))
    matches = bool(jax.device_get(jnp.all(computed == expected)))

    graph = nx.DiGraph()
    graph.add_nodes_from(row["cell_id"] for row in axis4_object["axis4_readout_table"])
    graph.add_edges_from((row["src"], row["dst"]) for row in axis4_object["carrier_edges"])

    theta = sp.pi / 2
    l_r = sp.Matrix([[0, 0, 0], [0, 0, -theta], [0, theta, 0]])
    l_c = sp.diag(sp.log(sp.Rational(7, 10)), sp.log(sp.Rational(7, 10)), 0)
    commutator = sp.simplify(l_r * l_c - l_c * l_r)
    leading = sp.simplify(2 * sp.Rational(1, 1000) * sp.Rational(1, 1000) * commutator)
    symbolic_nonzero_entries = int(sum(1 for value in commutator if value != 0))

    z_solver = z3.Solver()
    z_positive = z3.Int("jax_axis4_positive_count_z3")
    z_negative = z3.Int("jax_axis4_negative_count_z3")
    z_solver.add(z_positive == z3.IntVal(positive))
    z_solver.add(z_negative == z3.IntVal(negative))
    z_solver.add(z3.Or(z_positive == 0, z_negative == 0))
    z3_status = str(z_solver.check()).lower()

    c_solver = cvc5.Solver()
    int_sort = c_solver.getIntegerSort()
    c_positive = c_solver.mkConst(int_sort, "jax_axis4_positive_count_cvc5")
    c_negative = c_solver.mkConst(int_sort, "jax_axis4_negative_count_cvc5")
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
        "sympy_commutator_nonzero_entries": symbolic_nonzero_entries,
        "sympy_commutator": str(commutator),
        "sympy_leading_order_2ue_commutator": str(leading),
        "z3_positive_negative_not_zero": z3_status,
        "cvc5_positive_negative_not_zero": cvc5_status,
        "pass": (
            graph.number_of_nodes() == common.EXPECTED_STATE_COUNT
            and positive == axis4_object["axis4_counts"]["positive"]
            and negative == axis4_object["axis4_counts"]["negative"]
            and neutral == axis4_object["axis4_counts"]["neutral"]
            and matches
            and symbolic_nonzero_entries > 0
            and z3_status == "unsat"
            and cvc5_status == "unsat"
        ),
    }


def main() -> int:
    axis4_object = common.build_axis4_object()
    probe = source_backing_probe(axis4_object)
    payload = common.engine_result_payload(
        engine=ENGINE,
        source_path=SOURCE_PATH,
        result_path=RESULT_PATH,
        packages_used=["jax", "jax.numpy", "networkx", "sympy", "z3", "cvc5"],
        aligned_packages_load_bearing=["networkx", "sympy", "z3", "cvc5"],
        package_observables={
            "networkx": "nx.DiGraph carrier with 33 nodes and committed generator adjacency",
            "sympy": "sp.Matrix/sp.log exact R_x/D_z generator commutator and 2ue[A,B] source row",
            "z3": "z3.Solver/z3.Int computed positive/negative Axis-4 identity",
            "cvc5": "cvc5.Solver/mkConst/mkTerm/assertFormula/checkSat computed positive/negative Axis-4 identity",
        },
        source_backing_probe=probe,
    )
    common.write_json(RESULT_PATH, payload)
    print(common.stable_json({"ok": payload["all_pass"], "result_path": common.rel(RESULT_PATH)}))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
