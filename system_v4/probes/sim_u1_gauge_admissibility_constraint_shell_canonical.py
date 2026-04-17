#!/usr/bin/env python3
"""
Canonical shell-local U(1) gauge admissibility constraint.

Constraint object: normalized endpoint gauge shift must be an integer winding.
This stays shell-local: admissible periodic gauges survive; fractional windings are excluded.
"""

import json
import os

classification = "canonical"
NAME = "sim_u1_gauge_admissibility_constraint_shell_canonical"
RESULTS_BASENAME = f"{NAME}_results.json"

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "tensor numerics are not needed for the winding admissibility proof"},
    "pyg": {"tried": False, "used": False, "reason": "graph tools are not needed for endpoint winding constraints"},
    "z3": {"tried": False, "used": False, "reason": "cvc5 is used as the load-bearing arithmetic prover for integer winding"},
    "cvc5": {"tried": False, "used": False, "reason": "cvc5 proves admissible normalized gauge shifts equal integer winding numbers and excludes fractional winding"},
    "sympy": {"tried": False, "used": False, "reason": "sympy checks exp(2*pi*i*n)=1 for admissible windings"},
    "clifford": {"tried": False, "used": False, "reason": "geometric algebra is not required for the scalar winding constraint"},
    "geomstats": {"tried": False, "used": False, "reason": "manifold geometry is not needed for the arithmetic admissibility check"},
    "e3nn": {"tried": False, "used": False, "reason": "equivariant networks are outside this shell-local constraint lane"},
    "rustworkx": {"tried": False, "used": False, "reason": "graphs are not needed for endpoint winding admissibility"},
    "xgi": {"tried": False, "used": False, "reason": "hypergraphs are not needed for integer winding constraints"},
    "toponetx": {"tried": False, "used": False, "reason": "cell complexes are not needed for this endpoint admissibility proof"},
    "gudhi": {"tried": False, "used": False, "reason": "persistent homology is not needed for gauge endpoint arithmetic"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["cvc5"] = "load_bearing"
TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"

for _name, _importer in [
    ("pytorch", lambda: __import__("torch")),
    ("pyg", lambda: __import__("torch_geometric")),
    ("z3", lambda: __import__("z3")),
    ("clifford", lambda: __import__("clifford")),
    ("geomstats", lambda: __import__("geomstats")),
    ("e3nn", lambda: __import__("e3nn")),
    ("rustworkx", lambda: __import__("rustworkx")),
    ("xgi", lambda: __import__("xgi")),
    ("toponetx", lambda: __import__("toponetx")),
    ("gudhi", lambda: __import__("gudhi")),
]:
    try:
        _importer()
        TOOL_MANIFEST[_name]["tried"] = True
    except Exception as exc:
        TOOL_MANIFEST[_name]["reason"] = f"not installed: {exc}"

import cvc5
TOOL_MANIFEST["cvc5"]["tried"] = True

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    sp = None
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"


def sat_for_shift(shift_num, shift_den=1):
    solver = cvc5.Solver()
    solver.setLogic("QF_LIRA")
    int_sort = solver.getIntegerSort()
    real_sort = solver.getRealSort()
    winding = solver.mkConst(int_sort, "winding")
    shift = solver.mkConst(real_sort, "shift")
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, shift, solver.mkTerm(cvc5.Kind.TO_REAL, winding)))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, shift, solver.mkReal(shift_num, shift_den)))
    return solver.checkSat().isSat()



def run_positive_tests():
    results = {
        "integer_winding_sat": {"pass": bool(sat_for_shift(3, 1))},
        "zero_winding_sat": {"pass": bool(sat_for_shift(0, 1))},
    }
    TOOL_MANIFEST["cvc5"]["used"] = True
    if sp is not None:
        n = sp.symbols("n", integer=True)
        results["sympy_periodic_gauge_closure"] = {"pass": bool(sp.simplify(sp.exp(2 * sp.pi * sp.I * n) - 1) == 0)}
        TOOL_MANIFEST["sympy"]["used"] = True
    else:
        results["sympy_periodic_gauge_closure"] = {"pass": False, "reason": "sympy unavailable"}
    return results



def run_negative_tests():
    return {
        "fractional_half_winding_excluded": {"pass": bool(not sat_for_shift(1, 2))},
        "fractional_third_winding_excluded": {"pass": bool(not sat_for_shift(1, 3))},
    }



def run_boundary_tests():
    return {
        "minus_one_winding_sat": {"pass": bool(sat_for_shift(-1, 1))},
        "unit_winding_sat": {"pass": bool(sat_for_shift(1, 1))},
    }


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    all_pass = all(item.get("pass", False) for group in (positive, negative, boundary) for item in group.values())
    results = {
        "name": NAME,
        "classification": classification,
        "scope_note": "shell-local U(1) admissibility: periodic gauge shifts are integer windings",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "passes_local_rerun": bool(all_pass),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, RESULTS_BASENAME)
    with open(out_path, "w") as handle:
        json.dump(results, handle, indent=2, default=str)
    print(f"{NAME}: {'PASS' if all_pass else 'FAIL'} -> {out_path}")
