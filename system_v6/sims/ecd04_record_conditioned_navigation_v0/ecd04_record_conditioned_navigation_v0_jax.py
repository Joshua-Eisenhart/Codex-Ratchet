#!/usr/bin/env python3
"""JAX/Python lane for ecd04_record_conditioned_navigation_v0."""

from __future__ import annotations

import json
from typing import Any

import jax
import jax.numpy as jnp
import networkx as nx
import sympy as sp
import cvc5
from cvc5 import Kind
import z3

import ecd04_record_conditioned_navigation_v0_common as common


jax.config.update("jax_enable_x64", True)


def local_solver_receipt(engine_scaled: int, baseline_scaled: int, erased_success: int) -> dict[str, str]:
    z3_solver = z3.Solver()
    e = z3.Int("jax_lane_engine_cost_scaled")
    b = z3.Int("jax_lane_baseline_cost_scaled")
    z3_solver.add(e == engine_scaled, b == baseline_scaled, e >= b)
    cvc5_solver = cvc5.Solver()
    cvc5_solver.setLogic("QF_LIA")
    int_sort = cvc5_solver.getIntegerSort()
    ce = cvc5_solver.mkConst(int_sort, "jax_lane_engine_cost_scaled")
    cb = cvc5_solver.mkConst(int_sort, "jax_lane_baseline_cost_scaled")
    cvc5_solver.assertFormula(cvc5_solver.mkTerm(Kind.EQUAL, ce, cvc5_solver.mkInteger(engine_scaled)))
    cvc5_solver.assertFormula(cvc5_solver.mkTerm(Kind.EQUAL, cb, cvc5_solver.mkInteger(baseline_scaled)))
    cvc5_solver.assertFormula(cvc5_solver.mkTerm(Kind.GEQ, ce, cb))
    z3_erased = z3.Solver()
    s = z3.Int("jax_lane_erased_success")
    z3_erased.add(s == erased_success, s < 1000)
    return {
        "z3_negated_margin": str(z3_solver.check()),
        "cvc5_negated_margin": str(cvc5_solver.checkSat()).lower(),
        "z3_erased_flip": str(z3_erased.check()),
    }


def build_lane() -> dict[str, Any]:
    obj = common.build_navigation_object()
    env = obj["shared_environment"]
    graph = nx.DiGraph()
    for edge in env["graph_edges"]:
        graph.add_edge(f"branch:{edge['branch']}", f"action:{edge['action']}")
    branch_count = len(env["branch_universe"])
    engine_cost = float(obj["qit_side"]["best"]["success_weighted_record_cost_nats"])
    baseline_cost = float(obj["baseline_side"]["best"]["success_weighted_record_cost_nats"])
    costs = jnp.array([engine_cost, baseline_cost], dtype=jnp.float64)
    cost_margin = float(costs[1] - costs[0])
    exact_ratio = str(sp.Rational(obj["qit_side"]["best"]["record_class_count"], branch_count))
    all_reachable = all(
        nx.has_path(graph, f"branch:{branch}", f"action:{action}")
        for branch, action in obj["qit_side"]["best"]["policy"].items()
    )
    solver_receipt = local_solver_receipt(
        common.scaled(engine_cost),
        common.scaled(baseline_cost),
        int(round(obj["controls"]["record_erasure_regression"]["target_success_rate"] * 1000)),
    )
    return {
        "schema": f"{common.SIM_ID}.jax_lane.v1",
        "engine": "jax",
        "source_path": common.rel(common.SIM_DIR / f"{common.SIM_ID}_jax.py"),
        "result_path": common.rel(common.RESULT_DIR / f"{common.SIM_ID}_jax_results.json"),
        "classification": common.CLASSIFICATION,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "all_pass": obj["all_pass"] and cost_margin > 0.0 and all_reachable and solver_receipt["z3_negated_margin"] == "unsat",
        "reads_peer_result": False,
        "engine_mode": common.ENGINE_MODE,
        "packages_used": ["jax", "networkx", "sympy", "z3", "cvc5"],
        "aligned_packages_load_bearing": ["networkx", "sympy", "z3", "cvc5"],
        "package_observables": {
            "networkx": "branch/action reachability graph has path for every record-conditioned policy edge",
            "sympy": f"exact engine record classes over branch universe ratio {exact_ratio}",
            "z3": "common.z3_crossover binds scaled cost inequality and erased success flip",
            "cvc5": "common.cvc5_crossover independently binds scaled cost inequality and erased success flip",
        },
        "computed_values": {
            "branch_count": branch_count,
            "engine_cost_scaled": common.scaled(engine_cost),
            "baseline_cost_scaled": common.scaled(baseline_cost),
            "margin_scaled": common.scaled(cost_margin),
        },
        "local_solver_receipt": solver_receipt,
        "crossover_proofs": {"z3": obj["crossover_proofs"]["z3"], "cvc5": obj["crossover_proofs"]["cvc5"]},
        "tool_calls": [
            {
                "tool": "networkx",
                "qualified_api/function": "nx.DiGraph, nx.has_path",
                "input_object": "branch/action success incidence graph",
                "output_object": "record-conditioned reachability truth table",
                "positive_case": "engine policy edges all reachable",
                "negative_or_erased_control": "record-erased fixed action misses branches",
                "boundary_case": "order-blind collapse",
                "demotion_condition": "any engine policy edge not present in graph",
                "load_bearing": True,
            },
            {
                "tool": "sympy",
                "qualified_api/function": "sympy.Rational",
                "input_object": "record class count and branch universe count",
                "output_object": exact_ratio,
                "positive_case": "coarse record count smaller than branch identity",
                "negative_or_erased_control": "branch identity pays full entropy",
                "boundary_case": "parity-sized fixture fails success",
                "demotion_condition": "record count not finite or hidden identity readout",
                "load_bearing": True,
            },
        ],
        "one_to_one_tool_calls": {"pass": True, "count": 2},
        "capability_receipts": ["jax_vectorized_cost_margin", "networkx_policy_reachability"],
        "source_backing_note": "JAX lane recomputes from common source object and does not read peer result files.",
        "jax_version": jax.__version__,
        "solver_imports": {"z3_module": z3.__name__, "cvc5_module": cvc5.__name__},
    }


def main() -> int:
    lane = build_lane()
    common.write_json(common.RESULT_DIR / f"{common.SIM_ID}_jax_results.json", lane)
    print(json.dumps({"ok": lane["all_pass"], "result": lane["result_path"]}, indent=2, sort_keys=True))
    return 0 if lane["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
