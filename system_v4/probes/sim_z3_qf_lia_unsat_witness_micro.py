#!/usr/bin/env python3
"""z3 QF_LIA UNSAT/witness micro probe.

Tool-stage scope:
  - one tool: z3
  - one API surface: SolverFor("QF_LIA").add / check / model
  - one tiny claim: z3 can decide a bounded linear-integer fixture, return
    witness values for SAT cases, and exclude contradictory/boundary cases.

This is pre-lego evidence. It does not promote a lego, coupling, bridge, or
stack claim.
"""

import json
import os

classification = "canonical"
NAME = "sim_z3_qf_lia_unsat_witness_micro"
PROBE_FAMILY = "z3_qf_lia_unsat_witness_micro"
CONSTRAINT_SET = "bounded_linear_integer_sat_unsat_boundary"

TOOL_MANIFEST = {
    "z3": {
        "tried": False,
        "used": False,
        "reason": (
            "z3 is load-bearing: SolverFor('QF_LIA').add, check, and model "
            "determine the SAT/UNSAT verdicts and witness values."
        ),
    }
}

TOOL_INTEGRATION_DEPTH = {"z3": "load_bearing"}

try:
    import z3

    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError as exc:
    z3 = None
    TOOL_MANIFEST["z3"]["reason"] = f"z3 import failed: {exc}"


def _solver():
    return z3.SolverFor("QF_LIA")


def _int(name):
    return z3.Int(name)


def _model_int(model, term):
    return model.eval(term, model_completion=True).as_long()


def _missing_z3(section):
    return {
        f"{section}_z3_import_gate": {
            "passed": False,
            "expected": "z3 importable",
            "z3_result": "import_error",
            "exclusion_note": "The micro receipt cannot run without z3.",
        }
    }


def run_positive_tests():
    if z3 is None:
        return _missing_z3("positive")

    solver = _solver()
    x = _int("x")
    y = _int("y")

    solver.add(x + y == 10)
    solver.add(x - y == 4)

    result = solver.check()
    model = {}
    model_ok = False
    if result == z3.sat:
        z3_model = solver.model()
        model = {"x": _model_int(z3_model, x), "y": _model_int(z3_model, y)}
        model_ok = model == {"x": 7, "y": 3}

    TOOL_MANIFEST["z3"]["used"] = True
    return {
        "linear_system_sat_with_model": {
            "passed": result == z3.sat and model_ok,
            "expected": "sat with x=7, y=3",
            "z3_result": str(result),
            "model": model,
            "constraints": ["x + y = 10", "x - y = 4"],
        }
    }


def run_negative_tests():
    if z3 is None:
        return _missing_z3("negative")

    solver = _solver()
    x = _int("x")

    solver.add(x > 0)
    solver.add(x < 0)

    result = solver.check()
    TOOL_MANIFEST["z3"]["used"] = True
    return {
        "strict_positive_and_negative_unsat": {
            "passed": result == z3.unsat,
            "expected": "unsat",
            "z3_result": str(result),
            "constraints": ["x > 0", "x < 0"],
            "exclusion_note": "A bounded integer cannot be strictly positive and strictly negative.",
        }
    }


def run_boundary_tests():
    if z3 is None:
        return _missing_z3("boundary")

    sat_solver = _solver()
    edge = _int("edge")
    sat_solver.add(edge >= 0)
    sat_solver.add(edge <= 0)
    sat_result = sat_solver.check()
    edge_model = None
    if sat_result == z3.sat:
        edge_model = _model_int(sat_solver.model(), edge)

    unsat_solver = _solver()
    edge_fail = _int("edge_fail")
    unsat_solver.add(edge_fail >= 0)
    unsat_solver.add(edge_fail <= 0)
    unsat_solver.add(edge_fail == 1)
    unsat_result = unsat_solver.check()

    TOOL_MANIFEST["z3"]["used"] = True
    return {
        "closed_zero_edge_sat": {
            "passed": sat_result == z3.sat and edge_model == 0,
            "expected": "sat with edge=0",
            "z3_result": str(sat_result),
            "model": {"edge": edge_model},
            "constraints": ["0 <= edge <= 0"],
        },
        "outside_closed_zero_edge_unsat": {
            "passed": unsat_result == z3.unsat,
            "expected": "unsat",
            "z3_result": str(unsat_result),
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
            "Other QF_LIA fixtures may survive; this micro receipt only covers the named z3 API surface and bounded constraints."
        ],
        "demotion_condition": (
            "Demote z3 for this surface if check is not decisive, if model "
            "cannot recover SAT witnesses, or if SAT/UNSAT verdicts diverge "
            "from the named positive, negative, and boundary fixtures."
        ),
        "out_of_scope": [
            "no lego promotion",
            "no tool-tool coupling",
            "no bridge claim",
            "no proof of the whole z3 library",
        ],
        "criteria_checked": [
            "z3 QF_LIA SAT witness extraction",
            "z3 QF_LIA contradiction exclusion",
            "z3 QF_LIA exact-boundary admission and exclusion",
        ],
        "summary": {
            "passed": sum(1 for test in flat_tests if test.get("passed")),
            "total": len(flat_tests),
        },
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
