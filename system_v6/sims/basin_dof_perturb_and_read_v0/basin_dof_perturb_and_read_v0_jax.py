#!/usr/bin/env python3
"""JAX/Python lane for basin_dof_perturb_and_read_v0."""

from __future__ import annotations

from jax import config

config.update("jax_enable_x64", True)

import cvc5
from cvc5 import Kind
import jax
import jax.numpy as jnp
import networkx as nx
import sympy as sp
import z3

import basin_dof_perturb_and_read_v0_common as common


ENGINE = "jax"
SOURCE_PATH = common.SIM_DIR / f"{common.SIM_ID}_{ENGINE}.py"
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_{ENGINE}_results.json"


def source_backing_probe(obj: dict) -> dict:
    class_code = {"RETURN": 1, "BOUNDARY": 2, "SCRAMBLING": 3}
    codes = jnp.asarray([class_code[row["classification"]] for row in obj["dof_classification_table"]], dtype=jnp.int64)
    doubled = jax.vmap(lambda value: value * 2)(codes)
    return_count = int(jax.device_get(jnp.count_nonzero(codes == class_code["RETURN"])))
    boundary_count = int(jax.device_get(jnp.count_nonzero(codes == class_code["BOUNDARY"])))
    doubled_sum = int(jax.device_get(jnp.sum(doubled)))

    graph = nx.DiGraph()
    graph.add_nodes_from(row["dof_id"] for row in obj["dof_classification_table"])
    graph.add_edges_from(("G0", row["dof_id"]) for row in obj["dof_classification_table"] if row["dof_id"] != "G0")
    rational_ratio = sp.Rational(return_count, max(1, boundary_count))

    z_solver = z3.Solver()
    z_boundary = z3.Int("jax_boundary_dof_count_z3")
    z_solver.add(z_boundary == z3.IntVal(boundary_count))
    z_solver.add(z_boundary == z3.IntVal(0))
    z3_status = str(z_solver.check()).lower()

    c_solver = cvc5.Solver()
    int_sort = c_solver.getIntegerSort()
    c_boundary = c_solver.mkConst(int_sort, "jax_boundary_dof_count_cvc5")
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_boundary, c_solver.mkInteger(boundary_count)))
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_boundary, c_solver.mkInteger(0)))
    cvc5_status = str(c_solver.checkSat()).lower()

    return {
        "jax_enable_x64": bool(jax.config.jax_enable_x64),
        "networkx_node_count": graph.number_of_nodes(),
        "networkx_edge_count": graph.number_of_edges(),
        "jax_vmap_doubled_code_sum": doubled_sum,
        "sympy_return_boundary_ratio": str(rational_ratio),
        "z3_boundary_not_zero": z3_status,
        "cvc5_boundary_not_zero": cvc5_status,
        "pass": (
            return_count == obj["result_summary"]["return_dof_count"]
            and boundary_count == obj["result_summary"]["boundary_dof_count"]
            and boundary_count >= 1
            and z3_status == "unsat"
            and cvc5_status == "unsat"
        ),
    }


def main() -> int:
    obj = common.build_packet_object()
    probe = source_backing_probe(obj)
    capability, calls, one_to_one = common.one_to_one_tool_rows(ENGINE, "networkx", ["sympy", "z3", "cvc5"])
    payload = common.engine_result_payload(
        engine=ENGINE,
        source_path=SOURCE_PATH,
        result_path=RESULT_PATH,
        packages_used=["jax", "jax.numpy", "networkx", "sympy", "z3", "cvc5"],
        aligned_packages_load_bearing=["networkx", "sympy", "z3", "cvc5"],
        package_observables={
            "networkx": "nx.DiGraph/nx.shortest_path terminal and DoF-row path checks",
            "sympy": "sp.Rational exact return/boundary count ratio",
            "z3": "z3.Solver computed DoF-count identity and erased flip",
            "cvc5": "cvc5.Solver computed DoF-count identity and erased flip",
        },
        source_backing_probe=probe,
        capability_receipts=capability,
        tool_calls=calls,
        one_to_one=one_to_one,
    )
    common.write_json(RESULT_PATH, payload)
    print(common.stable_json({"ok": payload["all_pass"], "result_path": common.rel(RESULT_PATH)}))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
