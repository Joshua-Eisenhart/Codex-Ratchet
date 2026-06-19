#!/usr/bin/env python3
"""Python/JAX-role heavy lane for axis0_contender_heavy_v0."""

from __future__ import annotations

import json

import cvc5
import networkx as nx
import sympy as sp
import z3

import axis0_contender_heavy_v0_common as common


SOURCE_PATH = common.SIM_DIR / f"{common.SIM_ID}_jax.py"
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_jax_results.json"


def tool_probe() -> dict[str, object]:
    graph = nx.DiGraph()
    graph.add_edge(0, 1)
    rational = sp.Rational(33, 97)
    solver = z3.Solver()
    value = z3.Int("jax_tool_probe_value")
    solver.add(value == 33)
    z3_status = str(solver.check()).lower()
    csolver = cvc5.Solver()
    csolver.setLogic("QF_LIA")
    int_sort = csolver.getIntegerSort()
    var = csolver.mkConst(int_sort, "jax_cvc5_tool_probe_value")
    csolver.assertFormula(csolver.mkTerm(cvc5.Kind.EQUAL, var, csolver.mkInteger(33)))
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
        role_id="jax_exact_axis0_heavy_adapter_builder",
        source_path=SOURCE_PATH,
        result_path=RESULT_PATH,
        packages_used=["networkx", "sympy", "z3", "cvc5", "json", "hashlib"],
        load_bearing=["networkx", "sympy", "z3", "cvc5"],
        package_observables={
            "networkx": "networkx.DiGraph carries committed 33-cell edge/stability and light-regression graph rows",
            "sympy": "sp.Rational builds exact finite Lyapunov/field support rows",
            "z3": "z3.Solver binds row-local heavy verdict values with SAT flip control",
            "cvc5": "cvc5.Solver independently binds row-local heavy verdict values with SAT flip control",
        },
        engine_role_note=(
            "Python/JAX-role lane computes all CP.3-CP.9 33-cell adapters, exact alias forms, "
            "heavy teeth, controls, and z3/cvc5 bindings. No JAX array claim is made."
        ),
        extra={
            "tool_probe": probe,
            "tool_calls": [
                {
                    "tool": "networkx",
                    "qualified_api": "networkx.DiGraph.add_edge/number_of_edges",
                    "input_object": "finite probe graph and committed carrier graph in common builder",
                    "output_object": "edge and stability rows",
                    "positive_case": "33-cell carrier edges are read and grouped by generator",
                    "negative/erased_control": "degree-only and shuffled-adjacency controls remain excluded",
                    "boundary_case": "graph rows do not promote Axis-0 admission",
                    "gates": ["candidate_verdict_table", "control_verdicts"],
                },
                {
                    "tool": "sympy",
                    "qualified_api": "sp.Rational",
                    "input_object": "finite exact field/Lyapunov values",
                    "output_object": "exact rational support for CP.7 variants",
                    "positive_case": "rational values are converted back to exact Fractions",
                    "negative/erased_control": "functional-swap control runs across multiple Lyapunov candidates",
                    "boundary_case": "Lyapunov descent alone is not Axis-0 feedback polarity",
                    "gates": ["A0.CP.7_lyapunov_descent_direction"],
                },
                {
                    "tool": "z3",
                    "qualified_api": "z3.Solver.check",
                    "input_object": "computed row-local heavy bindings",
                    "output_object": "UNSAT positive binding and SAT mutation",
                    "positive_case": "negating computed values is UNSAT",
                    "negative/erased_control": "mutating CP.3 hamming is SAT",
                    "boundary_case": "SMT binds computed table rows only",
                    "gates": ["crossover_proofs"],
                },
                {
                    "tool": "cvc5",
                    "qualified_api": "cvc5.Solver.checkSat",
                    "input_object": "same computed row-local heavy bindings as z3",
                    "output_object": "matching UNSAT/SAT polarity",
                    "positive_case": "negating computed values is UNSAT",
                    "negative/erased_control": "mutating CP.3 hamming is SAT",
                    "boundary_case": "SMT binds computed table rows only",
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

