#!/usr/bin/env python3
"""Python/JAX-role exact lane for axis0_cosurvivor_heavy_v0."""

from __future__ import annotations

import json

import cvc5
import networkx as nx
import sympy as sp
import z3

import axis0_cosurvivor_heavy_v0_common as common


SOURCE_PATH = common.SIM_DIR / f"{common.SIM_ID}_jax.py"
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_jax_results.json"


def tool_probe() -> dict[str, object]:
    graph = nx.DiGraph()
    graph.add_edges_from([(0, 1), (1, 2)])
    rational = sp.Rational(33, 97)
    solver = z3.Solver()
    value = z3.Int("axis0_cosurvivor_jax_probe")
    solver.add(value == graph.number_of_edges())
    z3_status = str(solver.check()).lower()
    csolver = cvc5.Solver()
    csolver.setLogic("QF_LIA")
    int_sort = csolver.getIntegerSort()
    var = csolver.mkConst(int_sort, "axis0_cosurvivor_jax_cvc5_probe")
    csolver.assertFormula(csolver.mkTerm(cvc5.Kind.EQUAL, var, csolver.mkInteger(graph.number_of_edges())))
    cvc5_status = str(csolver.checkSat()).lower()
    return {
        "networkx_edge_count": graph.number_of_edges(),
        "sympy_rational": str(rational),
        "z3_probe": z3_status,
        "cvc5_probe": cvc5_status,
    }


def build_result() -> dict[str, object]:
    probe = tool_probe()
    return common.lane_result(
        engine="jax",
        role_id="jax_exact_axis0_cosurvivor_heavy_builder",
        source_path=SOURCE_PATH,
        result_path=RESULT_PATH,
        packages_used=["networkx", "sympy", "z3", "cvc5", "json", "hashlib"],
        load_bearing=["networkx", "sympy", "z3", "cvc5"],
        package_observables={
            "networkx": "DiGraph carries committed generator adjacency and multi-step generator-walk profiles",
            "sympy": "Rational support binds finite 33-cell carrier scale and exact anchor controls",
            "z3": "Solver binds CP.11/CP.14 heavy-tooth counts with SAT flip control",
            "cvc5": "independent Solver binds the same heavy-tooth counts with SAT flip control",
        },
        engine_role_note=(
            "Python/JAX-role exact lane recomputes CP.11/CP.14 formulas from the committed carrier, "
            "then computes full disagreement, one-step stability, multi-step stability, boundary, and controls. "
            "No JAX array claim is made."
        ),
        extra={
            "tool_probe": probe,
            "tool_calls": [
                {
                    "tool": "networkx",
                    "qualified_api": "networkx.DiGraph.add_edges_from",
                    "input_object": "finite committed generator adjacency",
                    "output_object": "generator maps and multi-step stability profiles",
                    "positive_case": "all ordered depth-2 and depth-3 generator walks are counted",
                    "negative/erased_control": "prior CP.1/CP.2/CP.10 controls remain excluded",
                    "boundary_case": "graph support does not promote Axis-0 admission",
                    "gates": ["multi_step_stability_extension", "control_verdicts"],
                },
                {
                    "tool": "z3",
                    "qualified_api": "z3.Solver.check",
                    "input_object": "computed CP.11/CP.14 heavy tooth bindings",
                    "output_object": "UNSAT positive binding and SAT mutation",
                    "positive_case": "negating computed heavy rows is UNSAT",
                    "negative/erased_control": "mutating CP.11 hamming by one is SAT",
                    "boundary_case": "SMT binds the finite table, not formula ontology",
                    "gates": ["crossover_proofs"],
                },
                {
                    "tool": "cvc5",
                    "qualified_api": "cvc5.Solver.checkSat",
                    "input_object": "same computed CP.11/CP.14 heavy tooth bindings as z3",
                    "output_object": "matching UNSAT/SAT polarity",
                    "positive_case": "negating computed heavy rows is UNSAT",
                    "negative/erased_control": "mutating CP.11 hamming by one is SAT",
                    "boundary_case": "SMT binds the finite table, not formula ontology",
                    "gates": ["crossover_proofs"],
                },
            ],
        },
    )


def main() -> int:
    common.RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    common.write_json(RESULT_PATH, result)
    print(json.dumps({"ok": result["all_pass"], "result_path": common.rel(RESULT_PATH)}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
