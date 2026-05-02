#!/usr/bin/env python3
"""cvc5 QF_LIA model-extraction micro probe.

Tool-stage scope:
  - one tool: cvc5
  - one API surface: Solver.assertFormula / checkSat / getValue over QF_LIA
  - one tiny claim: cvc5 can decide a bounded integer fixture and return
    witness values for SAT cases.

This is pre-lego evidence. It does not promote a lego, coupling, bridge, or
stack claim.
"""

import json
import os

import cvc5
from cvc5 import Kind

classification = "canonical"
NAME = "sim_cvc5_qf_lia_model_extraction_micro"
PROBE_FAMILY = "cvc5_qf_lia_model_extraction_micro"
CONSTRAINT_SET = "bounded_linear_integer_sat_unsat_boundary"

TOOL_MANIFEST = {
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": (
            "cvc5 is load-bearing: Solver.assertFormula, checkSat, and "
            "getValue determine the SAT/UNSAT verdicts and witness values."
        ),
    }
}

TOOL_INTEGRATION_DEPTH = {"cvc5": "load_bearing"}


def _solver():
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    solver.setOption("produce-models", "true")
    return solver


def _int(solver, name):
    return solver.mkConst(solver.getIntegerSort(), name)


def _term_int(term):
    return int(term.getIntegerValue())


def _eq(solver, left, right):
    return solver.mkTerm(Kind.EQUAL, left, right)


def _add(solver, *terms):
    return solver.mkTerm(Kind.ADD, *terms)


def _sub(solver, left, right):
    return solver.mkTerm(Kind.SUB, left, right)


def _geq(solver, left, right):
    return solver.mkTerm(Kind.GEQ, left, right)


def _leq(solver, left, right):
    return solver.mkTerm(Kind.LEQ, left, right)


def _gt(solver, left, right):
    return solver.mkTerm(Kind.GT, left, right)


def _lt(solver, left, right):
    return solver.mkTerm(Kind.LT, left, right)


def run_positive_tests():
    solver = _solver()
    x = _int(solver, "x")
    y = _int(solver, "y")

    solver.assertFormula(_eq(solver, _add(solver, x, y), solver.mkInteger(10)))
    solver.assertFormula(_eq(solver, _sub(solver, x, y), solver.mkInteger(4)))

    result = solver.checkSat()
    model = {}
    model_ok = False
    if result.isSat():
        model = {"x": _term_int(solver.getValue(x)), "y": _term_int(solver.getValue(y))}
        model_ok = model == {"x": 7, "y": 3}

    return {
        "linear_system_sat_with_model": {
            "passed": result.isSat() and model_ok,
            "expected": "sat with x=7, y=3",
            "cvc5_result": str(result),
            "model": model,
            "constraints": ["x + y = 10", "x - y = 4"],
        }
    }


def run_negative_tests():
    solver = _solver()
    x = _int(solver, "x")
    zero = solver.mkInteger(0)

    solver.assertFormula(_gt(solver, x, zero))
    solver.assertFormula(_lt(solver, x, zero))

    result = solver.checkSat()
    return {
        "strict_positive_and_negative_unsat": {
            "passed": result.isUnsat(),
            "expected": "unsat",
            "cvc5_result": str(result),
            "constraints": ["x > 0", "x < 0"],
            "exclusion_note": "A bounded integer cannot be strictly positive and strictly negative.",
        }
    }


def run_boundary_tests():
    sat_solver = _solver()
    edge = _int(sat_solver, "edge")
    zero = sat_solver.mkInteger(0)
    one = sat_solver.mkInteger(1)

    sat_solver.assertFormula(_geq(sat_solver, edge, zero))
    sat_solver.assertFormula(_leq(sat_solver, edge, zero))
    sat_result = sat_solver.checkSat()
    edge_model = None
    if sat_result.isSat():
        edge_model = _term_int(sat_solver.getValue(edge))

    unsat_solver = _solver()
    edge_fail = _int(unsat_solver, "edge_fail")
    unsat_solver.assertFormula(_geq(unsat_solver, edge_fail, zero))
    unsat_solver.assertFormula(_leq(unsat_solver, edge_fail, zero))
    unsat_solver.assertFormula(_eq(unsat_solver, edge_fail, one))
    unsat_result = unsat_solver.checkSat()

    return {
        "closed_zero_edge_sat": {
            "passed": sat_result.isSat() and edge_model == 0,
            "expected": "sat with edge=0",
            "cvc5_result": str(sat_result),
            "model": {"edge": edge_model},
            "constraints": ["0 <= edge <= 0"],
        },
        "outside_closed_zero_edge_unsat": {
            "passed": unsat_result.isUnsat(),
            "expected": "unsat",
            "cvc5_result": str(unsat_result),
            "constraints": ["0 <= edge_fail <= 0", "edge_fail = 1"],
            "exclusion_note": "The exact boundary admits zero and excludes one.",
        },
    }


def _flatten_sections(*sections):
    flat = []
    for section in sections:
        for value in section.values():
            if isinstance(value, dict) and "passed" in value:
                flat.append(value)
    return flat


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    flat_tests = _flatten_sections(positive, negative, boundary)
    all_pass = all(test.get("passed") for test in flat_tests)

    results = {
        "name": NAME,
        "probe_family": PROBE_FAMILY,
        "constraint_set": CONSTRAINT_SET,
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "surviving_alternatives": [
            "Other QF_LIA fixtures may survive; this micro receipt only covers the named API surface and bounded constraints."
        ],
        "demotion_condition": (
            "Demote cvc5 for this surface if checkSat is not decisive, if getValue "
            "cannot recover SAT witnesses, or if SAT/UNSAT verdicts diverge from "
            "the named positive, negative, and boundary fixtures."
        ),
        "out_of_scope": [
            "no lego promotion",
            "no tool-tool coupling",
            "no bridge claim",
            "no proof of the whole cvc5 library",
        ],
        "criteria_checked": [
            "cvc5 QF_LIA SAT witness extraction",
            "cvc5 QF_LIA contradiction exclusion",
            "cvc5 QF_LIA exact-boundary admission and exclusion",
        ],
        "summary": {"passed": sum(1 for test in flat_tests if test.get("passed")), "total": len(flat_tests)},
        "all_pass": all_pass,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Summary: {results['summary']['passed']}/{results['summary']['total']} passed")

    if not all_pass:
        raise SystemExit(1)
