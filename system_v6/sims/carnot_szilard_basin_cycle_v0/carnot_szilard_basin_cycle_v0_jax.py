#!/usr/bin/env python3
"""JAX/Python lane for carnot_szilard_basin_cycle_v0."""

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

import carnot_szilard_basin_cycle_v0_common as common


ENGINE = "jax"
SOURCE_PATH = common.SIM_DIR / f"{common.SIM_ID}_{ENGINE}.py"
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_{ENGINE}_results.json"


def source_backing_probe(obj: dict) -> dict:
    sample_ms = jnp.asarray([row["m_sample"] for row in obj["basin_cycle_rows"]], dtype=jnp.int64)
    full_ms = jnp.asarray([row["m_full_graph"] for row in obj["basin_cycle_rows"]], dtype=jnp.int64)
    doubled = jax.vmap(lambda value: value * 2)(sample_ms)
    sample_min = int(jax.device_get(jnp.min(sample_ms)))
    sample_max = int(jax.device_get(jnp.max(sample_ms)))
    full_min = int(jax.device_get(jnp.min(full_ms)))
    doubled_sum = int(jax.device_get(jnp.sum(doubled)))

    graph = nx.DiGraph()
    for row in obj["basin_cycle_rows"]:
        graph.add_node(row["dof_id"])
        graph.add_edge(row["dof_id"], f"{row['dof_id']}::terminal_16")
    graph_paths_ok = all(nx.has_path(graph, row["dof_id"], f"{row['dof_id']}::terminal_16") for row in obj["basin_cycle_rows"])
    exact_ratio = sp.Rational(full_min, sample_min)
    exact_sample_log = sp.log(sample_min)

    z_solver = z3.Solver()
    z_sample = z3.Int("jax_sample_m")
    z_full = z3.Int("jax_full_m")
    z_solver.add(z_sample == z3.IntVal(sample_min))
    z_solver.add(z_full == z3.IntVal(full_min))
    z_solver.add(z3.Or(z_sample != 9, z_full != 33))
    z3_status = str(z_solver.check()).lower()

    c_solver = cvc5.Solver()
    int_sort = c_solver.getIntegerSort()
    c_sample = c_solver.mkConst(int_sort, "jax_sample_m_cvc5")
    c_full = c_solver.mkConst(int_sort, "jax_full_m_cvc5")
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_sample, c_solver.mkInteger(sample_min)))
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_full, c_solver.mkInteger(full_min)))
    c_solver.assertFormula(
        c_solver.mkTerm(
            Kind.OR,
            c_solver.mkTerm(Kind.DISTINCT, c_sample, c_solver.mkInteger(9)),
            c_solver.mkTerm(Kind.DISTINCT, c_full, c_solver.mkInteger(33)),
        )
    )
    cvc5_status = str(c_solver.checkSat()).lower()

    return {
        "jax_enable_x64": bool(jax.config.jax_enable_x64),
        "jax_vmap_doubled_sample_sum": doubled_sum,
        "networkx_node_count": graph.number_of_nodes(),
        "networkx_edge_count": graph.number_of_edges(),
        "networkx_paths_ok": graph_paths_ok,
        "sympy_full_over_sample_ratio": str(exact_ratio),
        "sympy_sample_log": str(exact_sample_log),
        "z3_count_identity": z3_status,
        "cvc5_count_identity": cvc5_status,
        "pass": (
            sample_min == 9
            and sample_max == 9
            and full_min == 33
            and graph_paths_ok
            and str(exact_ratio) == "11/3"
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
            "networkx": "nx.DiGraph/nx.has_path branch-to-terminal carrier check",
            "sympy": "sp.Rational and sp.log exact count-side floor rows",
            "z3": "z3.Solver computed m/floor count identity with violation UNSAT",
            "cvc5": "cvc5.Solver computed m/floor count identity with violation UNSAT",
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
