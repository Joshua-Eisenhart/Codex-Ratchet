#!/usr/bin/env python3
"""
tool_capability_z3.py

Tier A A0.1 tool-capability probe for z3.

This is a thin capability probe: z3 is the only tool in scope, and every test
is phrased so the result depends on the solver rather than on a fallback path.
The probe is canonical by process, but it is still a tool-capability sim rather
than a tool-lego-integration sim.
"""

import json
import os

classification = "canonical"
NAME = "tool_capability_z3"
SCOPE_NOTE = "Tier A z3 capability probe: isolated SAT, UNSAT, optimization, and boundary solver behavior only."

TOOL_MANIFEST = {
    "z3": {
        "tried": False,
        "used": False,
        "reason": "z3 is the sole solver used to check SAT and UNSAT instances for isolated capability coverage.",
    }
}

TOOL_INTEGRATION_DEPTH = {"z3": "load_bearing"}


def _row_passes(row):
    if row.get("status") == "skipped":
        return False
    if "expected" in row and "status" in row:
        return str(row["status"]) == str(row["expected"])
    return False


def _section_passes(section):
    return bool(section) and all(_row_passes(row) for row in section.values())

try:
    from z3 import And, Bool, If, Int, Not, Optimize, Or, Solver, Sum, sat, unsat

    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    And = Bool = If = Int = Not = Optimize = Or = Solver = Sum = None
    sat = unsat = None
    TOOL_MANIFEST["z3"]["reason"] = "z3 import failed on this machine; queue execution will show whether the solver is installed."


def _mark_z3_used() -> None:
    TOOL_MANIFEST["z3"]["used"] = True


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    if not TOOL_MANIFEST["z3"]["tried"]:
        results["z3_import_gate"] = {
            "status": "skipped",
            "reason": "z3 not importable",
        }
        return results

    # Positive 1: exact integer solution survives.
    solver = Solver()
    x = Int("x")
    y = Int("y")
    solver.add(x + y == 7, x - y == 1)
    status = solver.check()
    _mark_z3_used()
    positive_linear = {
        "status": str(status),
        "expected": "sat",
        "constraints": ["x + y = 7", "x - y = 1"],
    }
    if status == sat:
        model = solver.model()
        positive_linear["model"] = {"x": model[x].as_long(), "y": model[y].as_long()}
    results["exact_linear_system"] = positive_linear

    # Positive 2: maximize a bounded objective to show model search works.
    opt = Optimize()
    a = Int("a")
    b = Int("b")
    opt.add(a >= 0, b >= 0, a <= 6, b <= 6, a + 2 * b <= 8)
    opt.maximize(3 * a + b)
    opt_status = opt.check()
    _mark_z3_used()
    positive_opt = {
        "status": str(opt_status),
        "expected": "sat",
        "constraints": ["0 <= a,b <= 6", "a + 2b <= 8", "maximize 3a + b"],
    }
    if opt_status == sat:
        model = opt.model()
        positive_opt["model"] = {"a": model[a].as_long(), "b": model[b].as_long()}
        positive_opt["objective"] = model.eval(3 * a + b).as_long()
    results["bounded_optimization"] = positive_opt

    # Positive 3: small Boolean choice with exactly one admitted assignment.
    solver = Solver()
    p = Bool("p")
    q = Bool("q")
    r = Bool("r")
    solver.add(Or(p, q, r), Not(And(p, q)), Not(And(p, r)), Not(And(q, r)), q)
    status = solver.check()
    _mark_z3_used()
    positive_bool = {
        "status": str(status),
        "expected": "sat",
        "constraints": ["at least one of p,q,r", "at most one of p,q,r", "q required"],
    }
    if status == sat:
        model = solver.model()
        positive_bool["model"] = {
            "p": bool(model.eval(p, model_completion=True)),
            "q": bool(model.eval(q, model_completion=True)),
            "r": bool(model.eval(r, model_completion=True)),
        }
    results["boolean_single_choice"] = positive_bool

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    if not TOOL_MANIFEST["z3"]["tried"]:
        results["z3_import_gate"] = {
            "status": "skipped",
            "reason": "z3 not importable",
        }
        return results

    # Negative 1: conflicting equalities are UNSAT.
    solver = Solver()
    n = Int("n")
    solver.add(n == 2, n == 3)
    status = solver.check()
    _mark_z3_used()
    results["contradictory_equalities"] = {
        "status": str(status),
        "expected": "unsat",
        "constraints": ["n = 2", "n = 3"],
    }

    # Negative 2: impossible cardinality request is UNSAT.
    solver = Solver()
    u = Bool("u")
    v = Bool("v")
    w = Bool("w")
    solver.add(Sum([If(u, 1, 0), If(v, 1, 0), If(w, 1, 0)]) == 4)
    status = solver.check()
    _mark_z3_used()
    results["impossible_boolean_count"] = {
        "status": str(status),
        "expected": "unsat",
        "constraints": ["three booleans", "exactly four must be true"],
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    if not TOOL_MANIFEST["z3"]["tried"]:
        results["z3_import_gate"] = {
            "status": "skipped",
            "reason": "z3 not importable",
        }
        return results

    # Boundary 1: degenerate interval collapses to a single integer.
    solver = Solver()
    z = Int("z")
    solver.add(z >= 0, z <= 0)
    status = solver.check()
    _mark_z3_used()
    degenerate = {
        "status": str(status),
        "expected": "sat",
        "constraints": ["z >= 0", "z <= 0"],
    }
    if status == sat:
        model = solver.model()
        degenerate["model"] = {"z": model[z].as_long()}
    results["degenerate_interval"] = degenerate

    # Boundary 2: empty interval is UNSAT.
    solver = Solver()
    k = Int("k")
    solver.add(k >= 1, k <= 0)
    status = solver.check()
    _mark_z3_used()
    results["empty_interval"] = {
        "status": str(status),
        "expected": "unsat",
        "constraints": ["k >= 1", "k <= 0"],
    }

    # Boundary 3: a minimal feasible schedule with one slot survives.
    solver = Solver()
    slot = Int("slot")
    solver.add(slot >= 0, slot <= 0)
    status = solver.check()
    _mark_z3_used()
    singleton_schedule = {
        "status": str(status),
        "expected": "sat",
        "constraints": ["single available slot 0"],
    }
    if status == sat:
        model = solver.model()
        singleton_schedule["model"] = {"slot": model[slot].as_long()}
    results["singleton_schedule"] = singleton_schedule

    return results


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    summary = {
        "positive_all_pass": _section_passes(positive),
        "negative_all_pass": _section_passes(negative),
        "boundary_all_pass": _section_passes(boundary),
        "promotion_allowed": False,
        "claim_ceiling": "isolated_z3_capability_only",
        "scope_note": SCOPE_NOTE,
    }
    summary["all_pass"] = bool(summary["positive_all_pass"] and summary["negative_all_pass"] and summary["boundary_all_pass"])
    results = {
        "name": NAME,
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
        json.dump(results, handle, indent=2, sort_keys=True)
    print(f"Results written to {out_path}")
