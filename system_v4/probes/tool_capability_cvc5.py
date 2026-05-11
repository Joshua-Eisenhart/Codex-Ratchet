#!/usr/bin/env python3
"""tool_capability_cvc5

Tier A A0.2 tool-capability probe for cvc5.
Thin capability scope only: show that cvc5 loads on this machine, admits
satisfiable integer constraints, excludes contradictory constraints, and stays
well-behaved at a tight boundary.
"""

import json
import os

import cvc5
from cvc5 import Kind

classification = "canonical"
NAME = "tool_capability_cvc5"
SCOPE_NOTE = "Tier A cvc5 capability probe: satisfiable arithmetic, contradictory exclusion, and edge-boundary behavior."

TOOL_MANIFEST = {
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "cvc5 is the sole solver used to check SAT and UNSAT behavior for this capability probe.",
    }
}

TOOL_INTEGRATION_DEPTH = {"cvc5": "load_bearing"}


def _row_passes(row):
    if row.get("status") == "skipped":
        return False
    if "pass" in row:
        return bool(row["pass"])
    if "expected" in row:
        observed = row.get("status") or row.get("z3_result")
        return str(observed) == str(row["expected"])
    return False


def _section_passes(section):
    return bool(section) and all(_row_passes(row) for row in section.values())


def _solver():
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    solver.setOption("produce-models", "true")
    return solver


def _int(solver, name):
    return solver.mkConst(solver.getIntegerSort(), name)


def _eq(solver, left, right):
    return solver.mkTerm(Kind.EQUAL, left, right)


def _geq(solver, left, right):
    return solver.mkTerm(Kind.GEQ, left, right)


def _leq(solver, left, right):
    return solver.mkTerm(Kind.LEQ, left, right)


def run_positive_tests():
    solver = _solver()
    x = _int(solver, "x")
    y = _int(solver, "y")

    solver.assertFormula(_eq(solver, solver.mkTerm(Kind.ADD, solver.mkTerm(Kind.MULT, solver.mkInteger(2), x), y), solver.mkInteger(8)))
    solver.assertFormula(_eq(solver, solver.mkTerm(Kind.SUB, x, y), solver.mkInteger(1)))

    result = solver.checkSat()
    x_val = solver.getValue(x) if result.isSat() else None
    y_val = solver.getValue(y) if result.isSat() else None

    return {
        "integer_system_sat": {
            "pass": result.isSat(),
            "expected": "sat",
            "model": {
                "x": str(x_val) if x_val is not None else None,
                "y": str(y_val) if y_val is not None else None,
            },
            "constraints": [
                "2*x + y = 8",
                "x - y = 1",
            ],
        }
    }


def run_negative_tests():
    solver = _solver()
    x = _int(solver, "x")
    y = _int(solver, "y")

    solver.assertFormula(_eq(solver, solver.mkTerm(Kind.ADD, solver.mkTerm(Kind.MULT, solver.mkInteger(2), x), y), solver.mkInteger(8)))
    solver.assertFormula(_eq(solver, solver.mkTerm(Kind.SUB, x, y), solver.mkInteger(1)))
    solver.assertFormula(_eq(solver, solver.mkTerm(Kind.ADD, x, y), solver.mkInteger(10)))

    result = solver.checkSat()
    return {
        "contradictory_extension_unsat": {
            "pass": result.isUnsat(),
            "expected": "unsat",
            "constraints": [
                "2*x + y = 8",
                "x - y = 1",
                "x + y = 10",
            ],
        }
    }


def run_boundary_tests():
    sat_solver = _solver()
    edge = _int(sat_solver, "edge")
    sat_solver.assertFormula(_geq(sat_solver, edge, sat_solver.mkInteger(0)))
    sat_solver.assertFormula(_leq(sat_solver, edge, sat_solver.mkInteger(0)))
    sat_result = sat_solver.checkSat()
    edge_val = sat_solver.getValue(edge) if sat_result.isSat() else None

    unsat_solver = _solver()
    edge_fail = _int(unsat_solver, "edge_fail")
    unsat_solver.assertFormula(_geq(unsat_solver, edge_fail, unsat_solver.mkInteger(0)))
    unsat_solver.assertFormula(_leq(unsat_solver, edge_fail, unsat_solver.mkInteger(0)))
    unsat_solver.assertFormula(_eq(unsat_solver, edge_fail, unsat_solver.mkInteger(1)))
    unsat_result = unsat_solver.checkSat()

    return {
        "exact_edge_sat": {
            "pass": sat_result.isSat(),
            "expected": "sat",
            "model": {"edge": str(edge_val) if edge_val is not None else None},
            "constraints": ["0 <= edge <= 0"],
        },
        "beyond_edge_unsat": {
            "pass": unsat_result.isUnsat(),
            "expected": "unsat",
            "constraints": ["0 <= edge_fail <= 0", "edge_fail = 1"],
        },
    }


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    summary = {
        "positive_all_pass": _section_passes(positive),
        "negative_all_pass": _section_passes(negative),
        "boundary_all_pass": _section_passes(boundary),
        "promotion_allowed": False,
        "claim_ceiling": "isolated_cvc5_capability_only",
        "scope_note": SCOPE_NOTE,
    }
    summary["all_pass"] = bool(summary["positive_all_pass"] and summary["negative_all_pass"] and summary["boundary_all_pass"])
    results = {
        "name": NAME,
        "scope_note": SCOPE_NOTE,
        "classification": classification,
        "classification_note": SCOPE_NOTE,
        "divergence_log": SCOPE_NOTE,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": summary,
        "all_pass": bool(summary["all_pass"]),
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=str)
    print(f"Results written to {out_path}")
