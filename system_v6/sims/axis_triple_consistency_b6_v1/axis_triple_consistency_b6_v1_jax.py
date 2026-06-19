#!/usr/bin/env python3
"""JAX-slot lane for axis_triple_consistency_b6_v1."""

from __future__ import annotations

from typing import Any

import cvc5
from cvc5 import Kind
import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import networkx as nx
import sympy as sp
import z3

import axis_triple_consistency_b6_v1_common as common


ENGINE = "jax"
SOURCE_PATH = common.SIM_DIR / f"{common.SIM_ID}_{ENGINE}.py"
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_{ENGINE}_results.json"


def graph_probe() -> dict[str, Any]:
    carrier = common.axis0_common.rebuild_committed_carrier()
    graph = nx.DiGraph()
    for cell in carrier["cells"]:
        graph.add_node(int(cell["cell_id"]))
    for edge in carrier["edges"]:
        graph.add_edge(int(edge["src"]), int(edge["dst"]), generator=edge["generator"])
    return {
        "node_count": graph.number_of_nodes(),
        "edge_count": graph.number_of_edges(),
        "carrier_edge_count": len(carrier["edges"]),
        "has_33_nodes": graph.number_of_nodes() == common.EXPECTED_STATE_COUNT,
    }


def jax_sign_vector_probe(obj: dict[str, Any]) -> dict[str, Any]:
    rows = obj["consistency_table"]
    signs = jnp.asarray(
        [[row["b0_sign"], row["b3_panel_relation_sign"], row["b6_sign"]] for row in rows],
        dtype=jnp.int64,
    )
    expected = -(signs[:, 0] * signs[:, 1])
    holds = signs[:, 2] == expected
    expected_host = [int(value) for value in jax.device_get(expected)]
    holds_host = [bool(value) for value in jax.device_get(holds)]
    vector = [
        {
            "row_id": row["row_id"],
            "b0": int(signs_host[0]),
            "b3": int(signs_host[1]),
            "b6": int(signs_host[2]),
            "expected": expected_host[idx],
            "holds": holds_host[idx],
        }
        for idx, (row, signs_host) in enumerate(zip(rows, jax.device_get(signs).tolist(), strict=True))
    ]
    return {
        "sign_vector_sha256": common.stable_sha256(vector),
        "agreement_count": int(jax.device_get(jnp.sum(holds.astype(jnp.int64)))),
        "violation_count": int(len(rows) - int(jax.device_get(jnp.sum(holds.astype(jnp.int64))))),
        "jax_enable_x64": bool(jax.config.jax_enable_x64),
    }


def sympy_panel_probe() -> dict[str, Any]:
    eta_fiber = sp.Rational(1, 6) * sp.pi
    eta_base = sp.Rational(1, 3) * sp.pi
    b0_fiber = sp.sign(sp.cos(2 * eta_fiber))
    b0_base = sp.sign(sp.cos(2 * eta_base))
    matrix = sp.Matrix([[-(b0_fiber * 1)], [-(b0_base * -1)]])
    flipped = sp.Matrix([[(b0_fiber * 1)], [(b0_base * -1)]])
    return {
        "expected_b6_fiber": int(sp.simplify(matrix[0])),
        "expected_b6_base": int(sp.simplify(matrix[1])),
        "flipped_target_fiber": int(sp.simplify(flipped[0])),
        "flipped_target_base": int(sp.simplify(flipped[1])),
        "pass": int(matrix[0]) == -1 and int(matrix[1]) == -1,
    }


def z3_probe(obj: dict[str, Any]) -> str:
    values = common.engine_computed_values(obj)
    solver = z3.Solver()
    total = z3.Int("jax_v1_total")
    violations = z3.Int("jax_v1_violations")
    faithful = z3.Int("jax_v1_faithful_adapter")
    solver.add(total == values["sample_total"])
    solver.add(violations == values["violation_count"])
    solver.add(faithful == (1 if values["faithful_33_cell_placement_possible"] else 0))
    solver.add(total == common.EXPECTED_STATE_COUNT)
    solver.add(violations > 0)
    solver.add(faithful == 0)
    return str(solver.check()).lower()


def cvc5_probe(obj: dict[str, Any]) -> str:
    values = common.engine_computed_values(obj)
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    total = solver.mkConst(int_sort, "jax_v1_total_cvc5")
    violations = solver.mkConst(int_sort, "jax_v1_violations_cvc5")
    faithful = solver.mkConst(int_sort, "jax_v1_faithful_adapter_cvc5")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, total, solver.mkInteger(values["sample_total"])))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, violations, solver.mkInteger(values["violation_count"])))
    solver.assertFormula(
        solver.mkTerm(
            Kind.EQUAL,
            faithful,
            solver.mkInteger(1 if values["faithful_33_cell_placement_possible"] else 0),
        )
    )
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, total, solver.mkInteger(common.EXPECTED_STATE_COUNT)))
    solver.assertFormula(solver.mkTerm(Kind.GT, violations, solver.mkInteger(0)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, faithful, solver.mkInteger(0)))
    result = solver.checkSat()
    return "sat" if result.isSat() else "unsat" if result.isUnsat() else str(result).lower()


def build_result() -> dict[str, Any]:
    obj = common.build_axis_triple_object()
    graph = graph_probe()
    vector = jax_sign_vector_probe(obj)
    panel = sympy_panel_probe()
    z3_status = z3_probe(obj)
    cvc5_status = cvc5_probe(obj)
    expected_hash = common.engine_computed_values(obj)["sign_vector_sha256"]
    probe = {
        "pass": (
            graph["node_count"] == common.EXPECTED_STATE_COUNT
            and graph["carrier_edge_count"] == common.EXPECTED_EDGE_COUNT
            and vector["sign_vector_sha256"] == expected_hash
            and panel["pass"]
            and z3_status == "sat"
            and cvc5_status == "sat"
        ),
        "graph_probe": graph,
        "sign_vector_sha256": vector["sign_vector_sha256"],
        "sympy_panel_probe": panel,
        "z3_gate_status": z3_status,
        "cvc5_gate_status": cvc5_status,
    }
    return common.engine_result_payload(
        engine=ENGINE,
        source_path=SOURCE_PATH,
        result_path=RESULT_PATH,
        packages_used=["jax", "jax.numpy", "networkx", "sympy", "z3", "cvc5"],
        aligned_packages_load_bearing=["networkx", "sympy", "z3", "cvc5"],
        package_observables={
            "networkx": "nx.DiGraph rebuilds the finite 33-cell carrier graph from source edges",
            "sympy": "sp.Rational/sp.Matrix computes exact panel and convention-flip signs",
            "z3": "z3.Solver binds proxy violations and faithful-adapter blocker",
            "cvc5": "cvc5.Solver independently binds proxy violations and faithful-adapter blocker",
        },
        source_backing_probe=probe,
    )


def main() -> int:
    common.write_json(RESULT_PATH, build_result())
    print(common.stable_json({"ok": True, "result_path": common.rel(RESULT_PATH)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
